#!/usr/bin/env python3
"""Build the NY candidate substrate for the 2023/24 holdout — SAME engine, SAME config.

The canon's universe is "both books, every day, no book choosing, no day forecasting"
(`docs/CANON-MECHANICAL.md`). This reproduces exactly that for the sealed holdout days:
both books simulated on every day, every resulting fill kept, nothing selected.

ANGUS'S CONSTRAINT, which is the whole point: *"to see if our mechanical strategy fits out
of fit you have to trade exactly the same as our mechanical canon."* So nothing here is
re-derived. The engine is `src.backtest.engine.simulate`, the config is
`load_backtest_config()` with the same three overrides the fit-window substrate used
(`win_start` 08:00, `win_end` 10:15, `max_trades_per_day` 2 — PER BOOK, which is why up to
four fills a day can survive), and the books are the same `mgmt_variant=V8` / `entry_variant=E4`
pair. Triggers come from the same detector, reclassified by the same `reclassify_triggers`.

    python -m scripts.build_holdout_substrate --validate    # FIT window, must match trade_matrix
    python -m scripts.build_holdout_substrate               # the holdout

--validate is not optional ceremony. It rebuilds the FIT window through this exact code and
compares against `output/trade_matrix.parquet`. If the rebuild cannot reproduce the known
substrate on known days, nothing it produces on 2023/24 is worth reading — the numbers would
look plausible and mean nothing.
"""
from __future__ import annotations

import argparse
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.grade_window_cap import books, load
from src.backtest.engine import load_backtest_config, simulate

NY = "America/New_York"
MASTER = ROOT / "data/reference/nq_1m_master.parquet"
TRIGS_HIST = ROOT / "output/triggers_hist2326_ob_v2.csv"
SEALED = ROOT / "data/reference/holdout_2023_24_days.csv"
OUT = ROOT / "output/holdout_substrate.parquet"


def canon_config():
    """The fit-window substrate's config, unchanged. max_trades_per_day is PER BOOK."""
    return load_backtest_config().model_copy(update={
        "win_start": dtime(8, 0), "win_end": dtime(10, 15), "max_trades_per_day": 2})


# Bars fed to simulate() for a month start LOOKBACK_DAYS before it, not at the beginning of
# the master. Every management indicator is intraday or daily-anchored, so a generous lookback
# is result-identical — the same reasoning (and the same practice) as the fit-window builder,
# which pre-filtered its master to three months before the span. Passing the FULL master makes
# each month re-simulate from 2023 (~1M bars x2 books) and turns minutes into hours.
LOOKBACK_DAYS = 120


def run_months(months, trigs, bars, base) -> pd.DataFrame:
    """Both books, every day, nothing selected — the canon universe."""
    cfg_e3, cfg_e4 = books(base)
    rows = []
    for m in sorted(months):
        seg_trigs = [t for t in trigs if t.ts[:7] == m]
        if not seg_trigs:
            print(f"  {m}: no triggers", flush=True)
            continue
        end = pd.Timestamp(
            (pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        start = pd.Timestamp(m + "-01", tz=NY) - pd.Timedelta(days=LOOKBACK_DAYS)
        seg = bars[(bars.ts_event >= start) & (bars.ts_event <= end)].reset_index(drop=True)
        n0 = len(rows)
        for book, cfg in (("E3", cfg_e3), ("E4", cfg_e4)):
            tr, _, _ = simulate(seg, seg_trigs, cfg)
            for r in tr:
                rows.append({
                    "day": r.trade_date, "book": book, "fill": str(r.fill_ts),
                    "exit": str(r.exit_ts), "direction": r.direction, "entry": r.entry,
                    "stop": r.stop_initial, "exit_price": r.exit_price,
                    "dollars": r.dollars, "pattern": r.pattern, "tf": getattr(r, "tf", "")})
        print(f"  {m}: {len(seg_trigs):>5} triggers -> {len(rows) - n0:>4} fills", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--validate", action="store_true",
                    help="rebuild the FIT window and compare against output/trade_matrix.parquet")
    a = ap.parse_args()

    base = canon_config()
    print(f"config: win {base.win_start}-{base.win_end}, "
          f"max_trades_per_day {base.max_trades_per_day} (per book), "
          f"lookback {LOOKBACK_DAYS}d\n", flush=True)
    bars = pd.read_parquet(MASTER)
    trigs = load([str(TRIGS_HIST)])
    print(f"bars {len(bars):,} | triggers {len(trigs):,}\n", flush=True)

    if a.validate:
        tm = pd.read_parquet(ROOT / "output/trade_matrix.parquet")
        months = sorted({d[:7] for d in tm.day.astype(str)})
        # the fit substrate's 2026 half came from a different bar file; validate the 2025
        # half, which triggers_hist2326_ob_v2 + nq_1m_master cover end to end.
        months = [m for m in months if m.startswith("2025")]
        print(f"VALIDATE — rebuilding fit months {months[0]}..{months[-1]}")
        S = run_months(months, trigs, bars, base)
        ref = tm[tm.day.astype(str).str[:7].isin(months)]
        mine = {(str(r.day), str(pd.Timestamp(r.fill).tz_convert(NY)), r.direction)
                for r in S.itertuples()}
        theirs = {(str(r.day)[:10], str(pd.Timestamp(r.fill).tz_convert(NY)), r.direction)
                  for r in ref.itertuples()}
        inter = mine & theirs
        print(f"\n  rebuilt fills : {len(mine)}")
        print(f"  trade_matrix  : {len(theirs)}")
        print(f"  exact matches : {len(inter)}  "
              f"({len(inter) / max(len(theirs), 1) * 100:.1f}% of reference)")
        missing = sorted(theirs - mine)[:5]
        extra = sorted(mine - theirs)[:5]
        if missing:
            print(f"  in reference, NOT rebuilt ({len(theirs - mine)}): {missing}")
        if extra:
            print(f"  rebuilt, NOT in reference ({len(mine - theirs)}): {extra}")
        ok = len(inter) / max(len(theirs), 1) >= 0.98
        print(f"\n  {'PASS' if ok else 'FAIL'} — "
              f"{'pipeline reproduces the known substrate' if ok else 'DO NOT TRUST THIS ON 2023/24'}")
        raise SystemExit(0 if ok else 1)

    days = set(pd.read_csv(SEALED, dtype=str)["day"])
    months = sorted({d[:7] for d in days})
    print(f"HOLDOUT — {len(days)} sealed days across {len(months)} months: {', '.join(months)}\n")
    S = run_months(months, trigs, bars, base)
    S = S[S.day.astype(str).isin(days)].reset_index(drop=True)   # sealed days ONLY
    S["yr"] = S.day.astype(str).str[:4].astype(int)
    S.to_parquet(OUT, index=False)

    print(f"\nwrote {OUT.relative_to(ROOT)}  —  {len(S)} candidate fills "
          f"on {S.day.nunique()} of {len(days)} sealed days")
    print(f"\nby year x book:\n{pd.crosstab(S.yr, S.book)}")
    print(f"\nby pattern: {S.pattern.value_counts().to_dict()}")
    print(f"raw 1-lot P&L (NOT the canon — this is the unfiltered universe): "
          f"${S.dollars.sum():+,.0f}")


if __name__ == "__main__":
    main()
