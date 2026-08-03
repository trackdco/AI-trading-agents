#!/usr/bin/env python3
"""L0 — LONDON trigger census. The base of the London canon rebuild.

Mirrors `scripts/build_l0_triggers.py` (the NY L0) with the London window rule. Same
discipline, same guarantee: this PRODUCES the trigger universe from `detect_triggers` — the
same code the live detector runs — so there is exactly one London trigger universe and it is
derived, not chosen. The cached `output/triggers_london.csv` becomes a parity reference, not
an input.

NO SELECTION HERE. No caps, no risk gate (LON_RISK_MIN is Layer 0 of the *scorer*, applied at
L4 policy), no escalation, no score minimum. Those are post-hoc so changing them is a re-run,
never a rebuild.

WINDOW. 08:00-10:00 Europe/London via `run_triggers_london.london_window_et`, never hardcoded
ET hours — the ~5 weeks/year when UK and US clocks disagree land the window on 04:00-06:00 ET
instead of 03:00-05:00. Verified against the depth-file pull, whose UTC start hour flips on
2025-10-27 and 2026-03-30 (the UK DST dates, not the US ones).

SCHEMA. Two additive Trigger fields the cached stream predates, populated from state the
detector always had and used to throw away:
  cluster_members  the crossed cluster's component levels [[name, price, type], ...]
  level_stack      the full level stack at trigger time, sorted by price
Both feed the L1 structural-cancel rule. They are additive — identity columns are unaffected,
which is what makes the parity gate below meaningful.

LOOKBACK. 30 days before each day. `holdout_london_triggers.py` verified London
lookback-invariance directly (60d/30d/20d byte-identical on sampled days), and the cached
fit-span run handed the detector everything from 2025-05-20 — so its earliest days had ~13
days of history and its latest had over a year. --parity re-tests that across both regimes.

JANUARY 2026 IS INCLUDED, and this is a deliberate departure from the cached stream.
`run_triggers_london.py` skipped it (`bdate_range` 2025-06-02..2025-12-31 then
2026-02-02..2026-07-10) and the NY L0 skips it too (`range(2, 8)`). The reason is documented
in docs/FINDING-late-window-orderflow.md:105 — "2026-01 has no trades in any sub-window table
(trigger-cache seam month)" — i.e. it is an artifact of where the two trigger CACHES were
seamed, not a data gap. Master carries 21 Jan-2026 sessions with full London-window bars, and
Jan-2026 sits inside the handoff's declared fit span (2025-06 -> 2026-07). Dropping a month
of valid bars would be selection, which L0 does not do. The month is counted separately in
the summary so any comparison against the cached stream stays apples-to-apples.

BARS. Master alone covers the whole fit span. Verified byte-identical to
nq_1m_feb_jul2026.parquet across all 161,525 overlapping 2026 rows (open/high/low/close/
volume, zero mismatches), so the two-segment split the NY L0 needs is unnecessary here and
one source removes a dedup-order confound: the cached London stream concatenated master-first
and deduped, meaning its 2026 bars came from master anyway.

    python -m scripts.build_l0_triggers_london --parity        # gate: run BEFORE building
    python -m scripts.build_l0_triggers_london --span fit
    python -m scripts.build_l0_triggers_london --span holdout
"""
from __future__ import annotations

import argparse
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zoneinfo import ZoneInfo  # noqa: E402

from scripts.run_triggers_london import london_window_et  # noqa: E402
from src.engine.triggers import detect_triggers  # noqa: E402

NY = "America/New_York"
LON = ZoneInfo("Europe/London")

# The London window, in LONDON LOCAL time. Default 08:00-10:00 is the canon window and is
# asserted below to be bit-identical to run_triggers_london.london_window_et. Set via --win to
# census a different slice (e.g. 10:00-12:00, the second two hours) — module-level so Pool
# workers inherit it across the fork.
WINDOW = ("08:00", "10:00")


def window_et(day: str):
    """Resolve WINDOW for `day` into ET. Same DST discipline as london_window_et: the window
    is defined in Europe/London and converted per day, never hardcoded to ET hours."""
    s = pd.Timestamp(f"{day} {WINDOW[0]}", tz=LON).tz_convert(NY)
    e = pd.Timestamp(f"{day} {WINDOW[1]}", tz=LON).tz_convert(NY)
    if WINDOW == ("08:00", "10:00"):        # self-check: default must match the shipped fn
        assert (s, e) == london_window_et(day), f"window drift on {day}"
    return s, e
MASTER = ROOT / "data/reference/nq_1m_master.parquet"
SEALED = ROOT / "data/reference/holdout_2023_24_days.csv"
CACHED = ROOT / "output/triggers_london.csv"
LOOKBACK_DAYS = 30

FIT_MONTHS = [f"2025-{m:02d}" for m in range(6, 13)] + [f"2026-{m:02d}" for m in range(1, 8)]
SEAM_MONTH = "2026-01"          # included here, absent from the cached stream — see docstring

# Parity days: two ordinary days at opposite ends of the fit span (cached lookback ~3 weeks
# vs >1 year), plus one day inside EACH DST-misalignment gap, where the window shifts to
# 04:00-06:00 ET. A parity set without the shifted days would not test the window rule at all.
PARITY_DAYS = [
    "2025-06-10",   # early fit — cached run had only ~3 weeks of history here
    "2025-09-17",   # ordinary mid-span day
    "2025-10-28",   # UK on GMT, US still EDT -> 04:00-06:00 ET
    "2026-03-11",   # US on EDT, UK still GMT -> 04:00-06:00 ET
    "2026-07-01",   # late fit — cached run had >1 year of history here
]

IDENT = ["tf", "direction", "kind", "entry_ref", "stop_ref"]     # + normalized ts, handled apart

_BARS: pd.DataFrame | None = None       # per-process cache for the Pool path


def _one_day(d: str) -> list[dict]:
    start, end = window_et(d)
    seg = _BARS[(_BARS.ts_event >= start - pd.Timedelta(days=LOOKBACK_DAYS))
                & (_BARS.ts_event <= end)].reset_index(drop=True)
    if seg.empty or seg[(seg.ts_event >= start) & (seg.ts_event <= end)].empty:
        return []
    return [t.model_dump() for t in detect_triggers(seg, start=start, end=end)]


def run_days(bars: pd.DataFrame, days: list[str], procs: int = 1) -> pd.DataFrame:
    """Days are independent (each reads its own lookback slice, writes its own rows), so the
    Pool changes wall-clock only — per-day output is bit-identical to procs=1."""
    global _BARS
    _BARS = bars
    rows: list[dict] = []
    if procs <= 1:
        for d in days:
            got = _one_day(d)
            rows.extend(got)
            print(f"  {d}: {len(got):>3} triggers", flush=True)
    else:
        with Pool(procs) as p:                      # fork inherits _BARS read-only
            for d, got in zip(days, p.imap(_one_day, days)):
                rows.extend(got)
                print(f"  {d}: {len(got):>3} triggers", flush=True)
    return pd.DataFrame(rows)


def weekdays(months: list[str], bars: pd.DataFrame) -> list[str]:
    """Trading days derived from bar presence, not from a calendar — holidays drop out for
    free. The London window (03:00-06:00 ET) never crosses an ET date boundary, so the ET
    calendar date equals the UK calendar date `london_window_et` expects."""
    d = bars.ts_event.dt.tz_convert(NY)
    days = sorted(set(d.dt.strftime("%Y-%m-%d")))
    return [x for x in days if x[:7] in months and pd.Timestamp(x).weekday() < 5]


def _norm_ts(s: pd.Series) -> pd.Series:
    """Compare timestamps as INSTANTS, not as strings. Trigger ts offsets flip -04:00/-05:00
    across DST, so '...T03:02:00-04:00' and '...T07:02:00+00:00' are the same moment and must
    compare equal. (Burn list #1 — this bit the NY rebuild three times.)"""
    return pd.to_datetime(s, utc=True, format="mixed").dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parity() -> None:
    """GATE — run before building anything on top of this.

    On overlap days the regenerated stream must match the cached London stream on the identity
    columns (ts/tf/direction/kind/entry_ref/stop_ref). The two new fields are additive and
    every other column byte-derives from the same detector code. Pattern labels are NOT
    compared: the cached stream predates the current classifier (known and accepted — handoff
    §4-L0). Any identity mismatch fails loudly and blocks L1.
    """
    cached = pd.read_csv(CACHED)
    cached["day"] = _norm_ts(cached.ts).str[:10]
    bars = pd.read_parquet(MASTER)

    days = [d for d in PARITY_DAYS if (cached.day == d).any()]
    missing = sorted(set(PARITY_DAYS) - set(days))
    if missing:
        print(f"NOTE: {missing} absent from the cached stream — parity runs on {len(days)} days")
    if len(days) < 3:
        raise SystemExit("parity needs >=3 overlap days")

    print(f"regenerating {len(days)} parity days (lookback {LOOKBACK_DAYS}d) "
          f"vs cached {CACHED.name}\n", flush=True)
    new = run_days(bars, days)
    new["day"] = _norm_ts(new.ts).str[:10]
    print()

    ok = True
    for d in days:
        start, _ = window_et(d)
        a = new[new.day == d].copy()
        b = cached[cached.day == d].copy()
        for f in (a, b):
            f["ts"] = _norm_ts(f.ts)
        cols = ["ts"] + IDENT
        an = a[cols].sort_values(cols).reset_index(drop=True)
        bn = b[cols].sort_values(cols).reset_index(drop=True)
        same = an.equals(bn)
        ok &= same
        shift = " [DST-shifted]" if start.hour != 3 else ""
        print(f"  {d} {start.strftime('%H:%M')} ET{shift}: regenerated {len(an):>3} vs "
              f"cached {len(bn):>3}  {'IDENTICAL' if same else 'MISMATCH'}")
        if not same:
            if len(an) != len(bn):
                ja = set(map(tuple, an.values))
                jb = set(map(tuple, bn.values))
                for row in sorted(ja - jb)[:5]:
                    print(f"    only in regenerated: {row}")
                for row in sorted(jb - ja)[:5]:
                    print(f"    only in cached:      {row}")
            else:
                diff = (an != bn).any(axis=0)
                print(f"    differing columns: {list(diff[diff].index)}")
    if not ok:
        raise SystemExit("PARITY FAILED — detector output drifted from the cached London "
                         "stream; do not build L1 on this until explained")
    print("\nparity OK — the regenerated stream is the cached stream + the two new fields")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=["fit", "holdout", "forward"])
    ap.add_argument("--days-file", default=None,
                    help="explicit day list, one YYYY-MM-DD per line (the forward shadow "
                         "log's mechanism). Overrides the span's own day derivation; --span "
                         "then only names the output artifact. Sealed 2023/24 days are "
                         "refused outright.")
    ap.add_argument("--parity", action="store_true")
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--win", default="08:00-10:00",
                    help="London-local window, HH:MM-HH:MM (default 08:00-10:00, the canon "
                         "window). Use e.g. 10:00-12:00 to census a different slice; the "
                         "output filename is suffixed so artifacts never collide.")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    global WINDOW
    WINDOW = tuple(a.win.split("-"))
    tag = "" if WINDOW == ("08:00", "10:00") else "_" + a.win.replace(":", "")
    if a.parity:
        return parity()
    if not a.span:
        raise SystemExit("--span or --parity required")

    bars = pd.read_parquet(MASTER)
    if a.days_file:
        days = sorted({x.strip() for x in Path(a.days_file).read_text().split() if x.strip()})
        sealed = set(pd.read_csv(SEALED, dtype=str)["day"])
        if bad := sorted(set(days) & sealed):
            raise SystemExit(f"SEALED DAY REFUSED: --days-file contains {len(bad)} holdout "
                             f"day(s), e.g. {bad[:3]}. The 2023/24 span was spent once.")
        have = set(weekdays([d[:7] for d in days], bars))
        if miss := sorted(set(days) - have):
            raise SystemExit(f"NO BARS: {len(miss)} requested day(s) absent from "
                             f"{MASTER.name}, e.g. {miss[:3]}. Extend the tape first — a "
                             "shadow log may not skip days silently.")
    elif a.span == "holdout":
        days = sorted(pd.read_csv(SEALED, dtype=str)["day"])
    else:
        days = weekdays(FIT_MONTHS, bars)
    print(f"{MASTER.name}: {len(bars):,} bars | {len(days)} days "
          f"{days[0]}..{days[-1]} | lookback {LOOKBACK_DAYS}d | procs {a.procs}\n"
          f"window {WINDOW[0]}-{WINDOW[1]} Europe/London", flush=True)

    T = run_days(bars, days, procs=a.procs)
    out = Path(a.out) if a.out else ROOT / f"output/l0_triggers_london{tag}_{a.span}.parquet"
    T.to_parquet(out, index=False)

    ts = pd.to_datetime(T.ts, format="mixed", utc=True).dt.tz_convert(NY)
    hm = ts.dt.hour + ts.dt.minute / 60
    shifted = sorted({d for d in days if window_et(d)[0].hour != 3})
    # os.path.relpath, not Path.relative_to: an --out outside the repo is legitimate
    # (scratch probes) and must not crash the run AFTER the artifact is already written.
    shown = os.path.relpath(out, ROOT)
    print(f"\nwrote {shown} — {len(T)} triggers on {ts.dt.date.nunique()} days")
    print(f"ET hour range: {hm.min():.2f} -> {hm.max():.2f}  "
          f"(DST-shifted days in span: {len(shifted)})")
    print(f"pattern: {T.pattern.value_counts().to_dict()}")
    print(f"kind:    {T.kind.value_counts().to_dict()}")
    print(f"tf:      {T.tf.value_counts().to_dict()}")
    if a.span == "fit":
        seam = int((ts.dt.strftime("%Y-%m") == SEAM_MONTH).sum())
        print(f"\n{SEAM_MONTH} (absent from the cached stream, included here): {seam} triggers "
              f"on {ts[ts.dt.strftime('%Y-%m') == SEAM_MONTH].dt.date.nunique()} days")
        print(f"fit total excluding {SEAM_MONTH}: {len(T) - seam} "
              f"(this is the number comparable to the cached stream)")
    print("\nby month:")
    print(ts.dt.strftime("%Y-%m").value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
