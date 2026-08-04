#!/usr/bin/env python3
"""FEASIBILITY COUNTS for the last three London candidates. NOT TESTS.

Counts only. No outcome, return, direction or P&L is computed anywhere in this file, so
no statistical power is spent and nothing here enters the DSR trial ledger. Per the
LDN-DRIVE-01 lesson, the n-floor is checked on each candidate's FULL gate stack — not its
trigger — before any prereg is written.

  1. london-value-traverse   — leg (b), the 80%-rule / value-traverse. Asia holds wholly
                               outside prior RTH value, London drives back inside.
  2. london-eu-macro-windows — how much of the EU release schedule even lands inside
                               08:00-10:00 London, and do we hold a calendar at all.
  3. london-level-defense-flow — absorption at a level; needs price-level footprint.

SEALED-SPAN GUARD: 2023/24 dropped via fit_only(). No holdout look.

    python -m scripts.ldn_remaining_feasibility
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_inv01_power import fit_only
from scripts.ldn_swp01_london_only import london_window_et

NY = "America/New_York"
LON = "Europe/London"
FLOOR = 30
HOLD_MIN = 45          # thesis: "VA re-entry held ~45-60 min"


def load():
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY))
    bars["day"] = bars.ts.dt.strftime("%Y-%m-%d")
    return sub, {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}


# ------------------------------------------------------------------ 1. value-traverse
def value_traverse(sub, by_day) -> pd.DataFrame:
    rows = []
    for r in sub.itertuples():
        g = by_day.get(r.day)
        if g is None or pd.isna(r.prior_va_hi) or pd.isna(r.prior_va_lo):
            continue
        start, end = london_window_et(r.day)
        w = g[(g.ts >= start) & (g.ts <= end)].reset_index(drop=True)
        if len(w) < 30:
            continue
        # gate 1: Asia held WHOLLY outside prior RTH value area, all night
        above = r.asia_lo > r.prior_va_hi
        below = r.asia_hi < r.prior_va_lo
        g1 = bool(above or below)
        g2 = g3 = False
        if g1:
            # gate 2: a London 1-min CLOSE back inside the value area
            inside = ((w.close <= r.prior_va_hi) & (w.close >= r.prior_va_lo))
            if inside.any():
                g2 = True
                # gate 3: and it HOLDS ~45 min (thesis: 45-60 min)
                i = int(inside.idxmax())
                seg = inside.iloc[i: i + HOLD_MIN]
                g3 = bool(len(seg) >= HOLD_MIN and seg.mean() >= 0.8)
        rows.append({"day": r.day, "era": r.day[:4], "g1": g1, "g2": g2, "g3": g3})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 2. eu-macro-windows
def macro_windows(sub) -> pd.DataFrame:
    """Where do the thesis's named release clock-times fall relative to our window?"""
    named = [("German prints", "07:00"), ("flash PMI (DE/FR)", "08:15"),
             ("flash PMI (EZ/UK)", "09:00"), ("EZ aggregates", "10:00")]
    rows = []
    for label, hhmm in named:
        inside = 0
        for r in sub.itertuples():
            start, end = london_window_et(r.day)
            t = pd.Timestamp(f"{r.day} {hhmm}", tz=LON).tz_convert(NY)
            if start <= t <= end:
                inside += 1
        rows.append({"release": label, "london_clock": hhmm,
                     "days_inside_window": inside, "days_total": len(sub)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 3. level-defense
def level_defense(sub) -> dict:
    fp_files = [f for f in glob.glob(str(ROOT / "data/reference/cvd/footprint_*.parquet"))
                if "holdout" not in f]
    depth_days = {f.split("mdp3-")[1][:8] for f in
                  glob.glob(str(ROOT / "data/reference/depth_london/*.csv"))}
    depth_days = {f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in depth_days}
    cov = sub[sub.day.isin(depth_days)]
    return {"footprint_files_excl_holdout": len(fp_files),
            "depth_days": len(depth_days),
            "session_days_with_depth": {e: int((cov.day.str[:4] == e).sum())
                                        for e in ("2025", "2026")}}


def main() -> None:
    sub, by_day = load()
    print("FEASIBILITY — last three London candidates. COUNTS ONLY, no outcomes.\n")
    print(f"session days after sealed-span guard: {len(sub)} "
          f"({', '.join(f'{e}: {int((sub.day.str[:4] == e).sum())}' for e in ('2025', '2026'))})")

    # 1
    v = value_traverse(sub, by_day)
    print("\n" + "=" * 78)
    print("1. london-value-traverse — leg (b), the 80% rule / value traverse")
    print("=" * 78)
    print(f"{'gate stack':<52}{'2025':>6}{'2026':>6}  floor n>={FLOOR}")
    print("-" * 78)
    for label, col in (("1. Asia held wholly outside prior RTH value", "g1"),
                       ("1+2. + a London close back inside the VA", "g2"),
                       (f"1+2+3. + held inside ~{HOLD_MIN} min (the thesis's rule)", "g3")):
        n25 = int(v[(v.era == "2025") & v[col]].shape[0])
        n26 = int(v[(v.era == "2026") & v[col]].shape[0])
        print(f"{label:<52}{n25:>6}{n26:>6}  "
              f"{'OK' if min(n25, n26) >= FLOOR else 'UNTESTABLE'}")

    # 2
    print("\n" + "=" * 78)
    print("2. london-eu-macro-windows — does the schedule even land in our window?")
    print("=" * 78)
    m = macro_windows(sub)
    print(f"{'release (thesis clock time)':<28}{'London':>8}{'days inside 08:00-10:00':>26}")
    print("-" * 78)
    for r in m.itertuples():
        print(f"{r.release:<28}{r.london_clock:>8}"
              f"{f'{r.days_inside_window} / {r.days_total}':>26}")

    # 3
    print("\n" + "=" * 78)
    print("3. london-level-defense-flow — data availability for absorption at price")
    print("=" * 78)
    d = level_defense(sub)
    print(f"  price-level footprint files (holdout excluded): "
          f"{d['footprint_files_excl_holdout']}")
    print(f"  depth days on disk: {d['depth_days']}")
    print(f"  session days with depth: {d['session_days_with_depth']}")

    print("\nTHESE ARE NOT VERDICTS. No outcome was measured; no trial is recorded.")


if __name__ == "__main__":
    main()
