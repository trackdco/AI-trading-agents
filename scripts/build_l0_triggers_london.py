#!/usr/bin/env python3
"""L0 LONDON — regenerate the London trigger universe from bars. Base of the London rebuild.

WHY (ANGUS 2026-08-05): *"what if we build a london strategy around my canon strategy.
vwap, bollinger bands, etc you should know. start top down. raw triggers, etc etc."*

That is the London canon rebuild specified in `docs/HANDOFF-london-rebuild.md`, which was
written and never run. This is its L0 rung, mirroring `scripts/build_l0_triggers.py` (NY)
with the two London specifics the handoff insists on:

  * the window is 08:00-10:00 **Europe/London** converted per-day to ET, never hardcoded ET
    hours -- `run_triggers_london.london_window_et` (burn-list item 1: mixed DST timestamps)
  * parity is gated against `output/triggers_london.csv`, the cached London stream

NO SELECTION HERE. No caps, no stop gates, no score, no order flow. Those are L4 policy,
applied post-hoc so changing them is a re-run and never a rebuild. This layer answers one
question: what does the canon's own detector -- BB / daily-VWAP band / POC confluence
clusters, rejection blocks and displacements -- actually fire on in the London window.

EVENT-UNIVERSE SENSITIVITY IS BUILT IN FROM STAGE ONE (5.11.2). `--band wide` detects over
07:30-10:30 London instead of 08:00-10:00. LDN-PO3-01 was killed twice before anyone ever
asked what widening the window did; that question is answerable here without a re-run.

    python -m scripts.build_l0_triggers_london --parity
    python -m scripts.build_l0_triggers_london --span fit [--band std|wide] [--procs N]
"""
from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_triggers_london import london_window_et  # noqa: E402
from src.engine.triggers import detect_triggers  # noqa: E402

NY = "America/New_York"
LON = "Europe/London"
LOOKBACK_DAYS = 30
BANDS = {"std": ("08:00", "10:00"), "wide": ("07:30", "10:30")}   # Europe/London

SEGMENTS = [
    ([f"2025-{m:02d}" for m in range(6, 13)], "data/reference/nq_1m_master.parquet"),
    ([f"2026-{m:02d}" for m in range(2, 8)], "data/reference/nq_1m_feb_jul2026.parquet"),
]

_BARS: pd.DataFrame | None = None
_BAND: tuple[str, str] = BANDS["std"]


def _force_prior_profile() -> None:
    """Force the §7 prior-session-profile flag ON in BOTH binding modules.

    `triggers` does `from ... import _include_prior_profile`, which binds the name in its
    own namespace, so patching only `snapshot` would leave detection reading the config
    default and silently produce the baseline census under an arm's filename. Same
    two-module patch `scripts/_detect_parallel.py` uses for OTE, and applied per worker so
    it survives a spawn start method.
    """
    import src.engine.snapshot as _snap
    import src.engine.triggers as _trg
    _snap._include_prior_profile = lambda: True
    _trg._include_prior_profile = lambda: True


def _init_pool(bars: pd.DataFrame, band: tuple[str, str], prior_profile: bool = False) -> None:
    """Pool initializer -- workers need their own globals under spawn (Pat's VPS, 2026-07-30)."""
    global _BARS, _BAND
    _BARS, _BAND = bars, band
    if prior_profile:
        _force_prior_profile()


def window_et(day: str, band: tuple[str, str]):
    """`band` in Europe/London -> ET, per day, so DST misalignment weeks shift correctly."""
    if band == BANDS["std"]:
        return london_window_et(day)
    return (pd.Timestamp(f"{day} {band[0]}", tz=LON).tz_convert(NY),
            pd.Timestamp(f"{day} {band[1]}", tz=LON).tz_convert(NY))


def _one_day(d: str) -> list[dict]:
    start, end = window_et(d, _BAND)
    seg = _BARS[(_BARS.ts_event >= start - pd.Timedelta(days=LOOKBACK_DAYS))
                & (_BARS.ts_event <= end)].reset_index(drop=True)
    if seg[(seg.ts_event >= start) & (seg.ts_event <= end)].empty:
        return []
    rows = [t.model_dump() for t in detect_triggers(seg, start=start, end=end)]
    for r in rows:
        r["day"] = d
        r["et_hour_start"] = int(start.hour)      # 3 normally, 4 on DST-misaligned days
    return rows


def run_days(bars: pd.DataFrame, days: list[str], band: tuple[str, str],
             procs: int = 1, quiet: bool = False,
             prior_profile: bool = False) -> pd.DataFrame:
    """Days are independent, so the Pool changes wall-clock only -- output is identical."""
    global _BARS, _BAND
    _BARS, _BAND = bars, band
    rows = []
    if procs <= 1:
        if prior_profile:
            _force_prior_profile()
        for d in days:
            got = _one_day(d)
            rows.extend(got)
            if not quiet:
                print(f"  {d}: {len(got):>3} triggers", flush=True)
    else:
        with Pool(procs, initializer=_init_pool,
                  initargs=(bars, band, prior_profile)) as p:
            for i, (d, got) in enumerate(zip(days, p.imap(_one_day, days))):
                rows.extend(got)
                if not quiet and (i % 20 == 0 or i == len(days) - 1):
                    print(f"  [{i+1}/{len(days)}] {d}: {len(got):>3} triggers "
                          f"(running {len(rows):,})", flush=True)
    return pd.DataFrame(rows)


def load_bars() -> pd.DataFrame:
    frames = [pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
              for _, p in SEGMENTS]
    b = (pd.concat(frames, ignore_index=True)
         .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))
    b["ts_event"] = pd.to_datetime(b["ts_event"], utc=True).dt.tz_convert(NY)
    return b


def span_days(bars: pd.DataFrame) -> list[str]:
    months = {m for ms, _ in SEGMENTS for m in ms}
    d = bars.ts_event
    days = sorted(set(d.dt.strftime("%Y-%m-%d")))
    return [x for x in days if x[:7] in months and pd.Timestamp(x).weekday() < 5]


def parity(procs: int) -> bool:
    """GATE: on overlap days the regenerated stream must match the cached London stream on
    the identity columns. Pattern labels may differ -- the cache predates the current
    classifier, which the handoff records as known and fine."""
    cached = pd.read_csv(ROOT / "output/triggers_london.csv")
    cts = pd.to_datetime(cached.ts, utc=True, format="mixed").dt.tz_convert(NY)
    cached["day"] = cts.dt.strftime("%Y-%m-%d")
    counts = cached.groupby("day").size()
    # three days spread across the span, each with real trigger volume; the middle one is
    # deliberately a DST-misaligned day so the window conversion is gated too
    days = ["2025-06-10", "2025-11-05", "2026-05-13"]
    bars = load_bars()
    new = run_days(bars, days, BANDS["std"], procs=procs, quiet=True)
    ident = ["ts", "tf", "direction", "kind", "entry_ref", "stop_ref"]
    ok = True
    for d in days:
        a = new[new.day == d] if len(new) else new
        b = cached[cached.day == d]
        an = a[ident].sort_values(["ts", "tf", "entry_ref"]).reset_index(drop=True)
        bn = b[ident].copy()
        bn["ts"] = pd.to_datetime(bn.ts, utc=True, format="mixed").dt.tz_convert(NY).apply(
            lambda x: x.isoformat())
        bn = bn.sort_values(["ts", "tf", "entry_ref"]).reset_index(drop=True)
        same = len(an) == len(bn) and an.equals(bn)
        ok &= same
        print(f"  {d} (cached day-count {counts.get(d, 0)}): regenerated {len(an):>3} vs "
              f"cached {len(bn):>3}  {'IDENTICAL' if same else 'MISMATCH'}")
        if not same and len(an) == len(bn):
            diff = (an != bn).any(axis=0)
            print(f"    differing columns: {list(diff[diff].index)}")
    print("parity OK -- the regenerated stream reproduces the cached London stream"
          if ok else "PARITY FAILED -- do not build L1 on this until explained")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prior-profile", action="store_true",
                    help="§7 arm: add the PREVIOUS session's POC/VAH/VAL to the level menu. "
                         "Changes the census, so it writes its own file and must re-gate "
                         "L0 parity as a new arm.")
    ap.add_argument("--span", choices=["fit"])
    ap.add_argument("--band", choices=sorted(BANDS), default="std")
    ap.add_argument("--parity", action="store_true")
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()

    if a.parity:
        return 0 if parity(a.procs) else 1
    if not a.span:
        ap.error("--span fit or --parity")

    bars = load_bars()
    days = span_days(bars)
    print(f"L0 London, band {a.band} {BANDS[a.band]} Europe/London, "
          f"{len(days)} weekdays {days[0]} -> {days[-1]}"
          + (" | +PRIOR-SESSION PROFILE (§7 arm)" if a.prior_profile else ""), flush=True)
    T = run_days(bars, days, BANDS[a.band], procs=a.procs,
                 prior_profile=a.prior_profile)
    # a different level menu is a different census: its own file, never overwriting the
    # baseline the shipped L0 gate was run against
    suffix = a.band + ("_pp" if a.prior_profile else "")
    out = ROOT / f"output/l0_triggers_london_fit_{suffix}.parquet"
    T.to_parquet(out, index=False)
    print(f"\nwrote {out.relative_to(ROOT)}: {len(T):,} triggers over "
          f"{T['day'].nunique()} days ({len(T)/max(T['day'].nunique(),1):.1f}/day)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
