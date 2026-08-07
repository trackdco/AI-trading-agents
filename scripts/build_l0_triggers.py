#!/usr/bin/env python3
"""L0 — regenerate the trigger universe from bars. The base of the canon rebuild.

WHY (ANGUS 30-Jul): *"we need to re run triggers from the beginning i think, and work back
from there. the base strategy before order flow, and make order flow confirm without any
trade caps or anything. we work from there, and build the trade caps after."*

The cached trigger sets were artifacts, not products: v1 (`triggers_hist2326_ob.csv`) carries
16,783 `unclassified` rows that load() silently drops, v2 reclassified them and flooded the
substrate, and choosing between the two was archaeology. L0 ends that by PRODUCING the set
from `detect_triggers` — the same code the live detector runs — so there is exactly one
trigger universe and it is derived, not chosen.

WHAT IS NEW IN THE SCHEMA (both are additive Trigger fields, populated from state the
detector always had and used to throw away):

  cluster_members  the crossed cluster's component levels [[name, price, type], ...].
                   `cluster_center` is their MEAN — useless for the structural-cancel rule,
                   whose whole point is that the components sit at different prices.
  level_stack      the FULL level stack at trigger time, sorted by price. Feeds the
                   entry-cancel rule ANGUS specified 30-Jul: cancel when price runs away,
                   TESTS a structural level (e.g. the VWAP mid) and REJECTS hard back into
                   the entry; hold when it drifts without touching structure — regardless
                   of distance. Measured on gold: the 22pt distance cancel keeps the worse
                   half (27% WR, -0.19R) and kills the better half (36% WR, +0.08R).

NO SELECTION HERE. No caps, no stop gates, no session windows beyond the detection band —
those are L4 policy, applied post-hoc so changing them is a re-run, never a rebuild. The
07:45-11:00 ET band matches the band the cached sets were detected over; downstream layers
label sessions, they do not filter here.

LOOKBACK. Bars handed to the detector start LOOKBACK_DAYS before each day. Every level the
detector gathers is intraday- or daily-anchored (BB on entry TFs, daily/NY VWAP, daily
profile POC, 10-day OTE fibs), so 30 days is result-identical to full history — verified
for this detector by scripts/verify_lookback.py and reconfirmed here by --parity.

    python -m scripts.build_l0_triggers --span fit
    python -m scripts.build_l0_triggers --span holdout
    python -m scripts.build_l0_triggers --parity          # gate: match cached v1 on 3 days
"""
from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine.triggers import detect_triggers  # noqa: E402

NY = "America/New_York"
SEALED = ROOT / "data/reference/holdout_2023_24_days.csv"
LOOKBACK_DAYS = 30
BAND = ("07:45", "11:00")            # detection band, ET — matches the cached sets

# Same segment map as build_ny_substrate: the fit window spans two bar files.
SEGMENTS = {
    "fit": [
        ([f"2025-{m:02d}" for m in range(6, 13)], "data/reference/nq_1m_master.parquet"),
        ([f"2026-{m:02d}" for m in range(2, 8)], "data/reference/nq_1m_feb_jul2026.parquet"),
    ],
    "holdout": [
        (None, "data/reference/nq_1m_master.parquet"),      # None = sealed days' months
    ],
}


_BARS: pd.DataFrame | None = None       # per-process cache for the Pool path


def _init_pool(bars: pd.DataFrame) -> None:
    """Pool initializer: hand each worker its own _BARS. REQUIRED on Windows, where
    multiprocessing SPAWNS (re-imports the module, module globals reset to None) instead of
    forking — the bare Pool crashed every worker with `'NoneType' has no attribute
    'ts_event'` on Pat's VPS (2026-07-30). Under Linux fork this is a no-op-equivalent."""
    global _BARS
    _BARS = bars


def _one_day(d: str) -> list[dict]:
    start = pd.Timestamp(f"{d} {BAND[0]}", tz=NY)
    end = pd.Timestamp(f"{d} {BAND[1]}", tz=NY)
    seg = _BARS[(_BARS.ts_event >= start - pd.Timedelta(days=LOOKBACK_DAYS))
                & (_BARS.ts_event <= end)].reset_index(drop=True)
    if seg[(seg.ts_event >= start) & (seg.ts_event <= end)].empty:
        return []
    return [t.model_dump() for t in detect_triggers(seg, start=start, end=end)]


def run_days(bars: pd.DataFrame, days: list[str], procs: int = 1) -> pd.DataFrame:
    """Days are independent (each reads its own lookback slice, writes its own rows), so
    the Pool changes wall-clock only — per-day output is bit-identical to procs=1."""
    global _BARS
    _BARS = bars
    rows = []
    if procs <= 1:
        for d in days:
            got = _one_day(d)
            rows.extend(got)
            print(f"  {d}: {len(got):>3} triggers", flush=True)
    else:
        with Pool(procs, initializer=_init_pool, initargs=(bars,)) as p:
            for d, got in zip(days, p.imap(_one_day, days)):
                rows.extend(got)
                print(f"  {d}: {len(got):>3} triggers", flush=True)
    return pd.DataFrame(rows)


def weekdays(months: list[str], bars: pd.DataFrame) -> list[str]:
    lo, hi = min(months) + "-01", max(months) + "-31"
    d = bars.ts_event.dt.tz_convert(NY)
    days = sorted(set(d.dt.strftime("%Y-%m-%d")[(d >= pd.Timestamp(lo, tz=NY))
                                                & (d <= pd.Timestamp(hi + " 23:59", tz=NY))]))
    return [x for x in days if x[:7] in months and pd.Timestamp(x).weekday() < 5]


def parity() -> None:
    """Gate: on overlap days the regenerated stream must match cached v1 on the identity
    columns (ts/tf/direction/kind/entry_ref/stop_ref) — the two new fields are additive and
    everything else byte-derives from the same code. Any mismatch fails loudly."""
    v1 = pd.read_csv(ROOT / "output/triggers_hist2326_ob.csv")
    v1ts = pd.to_datetime(v1.ts, utc=True, format="mixed").dt.tz_convert(NY)
    v1["day"] = v1ts.dt.strftime("%Y-%m-%d")
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet").drop(
        columns=["roll"], errors="ignore")
    days = ["2025-06-10", "2025-09-17", "2025-12-04"]
    new = run_days(bars, days)
    ident = ["ts", "tf", "direction", "kind", "entry_ref", "stop_ref"]
    ok = True
    for d in days:
        a = new[new.ts.str[:10] == d]
        b = v1[v1.day == d]
        an = a[ident].sort_values("ts").reset_index(drop=True)
        bn = b[ident].sort_values("ts").reset_index(drop=True)
        bn["ts"] = pd.to_datetime(bn.ts, format="mixed").apply(lambda x: x.isoformat())
        same = an.equals(bn)
        ok &= same
        print(f"  {d}: regenerated {len(a):>3} vs cached {len(b):>3}  "
              f"{'IDENTICAL' if same else 'MISMATCH'}")
        if not same and len(an) == len(bn):
            diff = (an != bn).any(axis=0)
            print(f"    differing columns: {list(diff[diff].index)}")
    if not ok:
        raise SystemExit("PARITY FAILED — detector output drifted from the cached set; "
                         "do not build L1 on this until explained")
    print("parity OK — the regenerated stream is the cached stream + the two new fields")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=sorted(SEGMENTS))
    ap.add_argument("--parity", action="store_true")
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.parity:
        return parity()
    if not a.span:
        raise SystemExit("--span or --parity required")

    sealed = sorted(pd.read_csv(SEALED, dtype=str)["day"]) if a.span == "holdout" else None
    parts = []
    for months, barfile in SEGMENTS[a.span]:
        bars = pd.read_parquet(ROOT / barfile).drop(columns=["roll"], errors="ignore")
        days = sealed if months is None else weekdays(months, bars)
        print(f"{barfile}: {len(bars):,} bars | {len(days)} days "
              f"{days[0]}..{days[-1]} | procs {a.procs}", flush=True)
        parts.append(run_days(bars, days, procs=a.procs))

    T = pd.concat(parts, ignore_index=True)
    out = Path(a.out) if a.out else ROOT / f"output/l0_triggers_{a.span}.parquet"
    T.to_parquet(out, index=False)
    d = pd.to_datetime(T.ts, format="mixed", utc=True).dt.tz_convert(NY)
    print(f"\nwrote {out.relative_to(ROOT)} — {len(T)} triggers on {d.dt.date.nunique()} days")
    print(f"pattern: {T.pattern.value_counts().to_dict()}")
    print(f"kind:    {T.kind.value_counts().to_dict()}")
    print(f"tf:      {T.tf.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
