#!/usr/bin/env python3
"""L3 Stage B — every canon check on trial against the honest population.

Each of the ten window-native checks (pre: W F Tp G C · gold: D Tc X AGE PAQ) and six Q
bits is evaluated with its FROZEN shipped threshold (config/live_thresholds.json via
scripts/live_thresholds.TH) on the L3 feature matrix, and judged by lift tables:

  split          2025 months (the original fit era) vs 2026 months (out-of-era)
  population     sane risk band 7-60pt (Layer-0, massively vindicated by L2: sub-7pt is
                 14% WR / -0.201R and carries 3/4 of the raw loss), per session
  sessions       pre 08:00-09:30 · gold 09:40-10:30 (ANGUS 2026-07-30 extension)
  verdict basis  WR and mean R with the check ON vs OFF, on candidates where the check
                 could be evaluated (NaN = stood down, excluded from both sides)

A check earns survival by discriminating in BOTH eras. trigdens_30-based TRIG uses census
stamps (denser than the old v2 CSVs), so its frozen threshold >11 is re-examined rather
than trusted — flagged in the output.

    python -m scripts.l3_check_trial
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.live_thresholds import TH  # noqa: E402

PRE = (480, 570)
GOLD = (580, 630)          # ANGUS 2026-07-30: extended to 10:30


def load() -> pd.DataFrame:
    F = pd.read_parquet(ROOT / "output/l3_features_fit.parquet")
    F = F[(F.risk >= 7) & (F.risk <= 60)].copy()
    F["sess"] = np.select([F.fill_hm.between(*PRE, inclusive="left"),
                           F.fill_hm.between(*GOLD, inclusive="left")],
                          ["pre", "gold"], default="other")
    F["era"] = np.where(F.day.str[:4] == "2025", "2025", "2026")
    long = F.direction == "long"
    # --- the ten checks, frozen definitions (canon_mechanical.py / scorer.py) ---
    F["W"] = np.where(long, F.dep_wall_below_d.isna(), F.dep_wall_above_d.isna()).astype(float)
    F["W"] = F["W"].where(F.dep_thick.notna())
    F["F_"] = (F.fill_delta_conf == 1).astype(float)
    d15dir = F.d15 * np.where(long, 1, -1)
    F["Tp"] = (d15dir >= TH.pre_Tp_d15dir_min).astype(float)
    F["G"] = (F.ent_vs_vwap_sd_dir >= TH.pre_G_ent_vs_vwap_sd_dir_min).astype(float)
    F["C"] = np.where(F.sess == "pre", (F.pm_sofar_conf == 1), (F.conf_LON == 1)).astype(float)
    F["D"] = pd.Series(np.where(long, F.dep_wall_above_d.notna(), F.dep_wall_below_d.notna()),
                       index=F.index).astype(float).where(F.dep_thick.notna())
    F["Tc"] = (F.d15_conf == 1).astype(float)
    F["X"] = (F.bbw_state >= TH.gold_X_bbw_state_min).astype(float).where(F.bbw_state.notna())
    F["AGE"] = (F.on_extreme_age >= TH.gold_AGE_on_extreme_age_min).astype(float).where(
        F.on_extreme_age.notna())
    F["PAQ"] = (F.netpath_30 >= TH.gold_PAQ_netpath_30_min).astype(float).where(
        F.netpath_30.notna())
    # --- Q bits (gold quality tier) ---
    wall_ahead_sz = np.where(long, F.dep_wall_above_sz, F.dep_wall_below_sz)
    F["WALLSZ"] = ((F.D == 1) & (pd.Series(wall_ahead_sz, index=F.index) >= 7)).astype(float)
    F["BIGFD"] = (F.fill_delta.abs() >= 173).astype(float)
    F["T2"] = ((F.fill_delta_conf == 1) | (F.bp5opp == 1)).astype(float)
    F["TRIG"] = (F.trigdens_30 > 11).astype(float)
    F["VWAPD"] = (F.ent_vs_vwap_sd_dir >= 0.107).astype(float)
    F["LONSLOPE"] = (F.lon_slope_d >= -0.0961).astype(float)
    return F


def lift(F: pd.DataFrame, check: str, sess: str) -> list[dict]:
    rows = []
    for era in ("2025", "2026"):
        d = F[(F.sess == sess) & (F.era == era) & F[check].notna()]
        on, off = d[d[check] == 1], d[d[check] == 0]
        if len(on) < 15 or len(off) < 15:
            rows.append({"check": check, "sess": sess, "era": era, "n_on": len(on),
                         "n_off": len(off), "verdict": "thin"})
            continue
        rows.append({
            "check": check, "sess": sess, "era": era,
            "n_on": len(on), "n_off": len(off),
            "wr_on": round((on.dollars_1lot > 0).mean(), 3),
            "wr_off": round((off.dollars_1lot > 0).mean(), 3),
            "r_on": round(on.R.mean(), 3), "r_off": round(off.R.mean(), 3),
            "lift_r": round(on.R.mean() - off.R.mean(), 3),
            "fire_rate": round(len(on) / (len(on) + len(off)), 2)})
    return rows


def main() -> None:
    F = load()
    print(f"population: {len(F)} outcomes 7-60pt | "
          f"pre {len(F[F.sess == 'pre'])} | gold {len(F[F.sess == 'gold'])} "
          f"(gold window 09:40-10:30 per ruling) | eras "
          f"{F.era.value_counts().to_dict()}\n")

    out = []
    for check, sess in [("W", "pre"), ("F_", "pre"), ("Tp", "pre"), ("G", "pre"),
                        ("C", "pre"),
                        ("D", "gold"), ("Tc", "gold"), ("X", "gold"), ("AGE", "gold"),
                        ("PAQ", "gold"),
                        ("WALLSZ", "gold"), ("BIGFD", "gold"), ("T2", "gold"),
                        ("TRIG", "gold"), ("VWAPD", "gold"), ("LONSLOPE", "gold")]:
        out.extend(lift(F, check, sess))
    T = pd.DataFrame(out)
    T.to_parquet(ROOT / "output/l3_check_trial.parquet", index=False)

    print(f"{'check':<9}{'sess':<6}{'era':<6}{'fire':>5}{'n_on':>6}{'n_off':>6}"
          f"{'WR on/off':>12}{'R on/off':>15}{'liftR':>7}")
    for r in out:
        if r.get("verdict") == "thin":
            print(f"{r['check']:<9}{r['sess']:<6}{r['era']:<6}   -- thin "
                  f"(on {r['n_on']}, off {r['n_off']})")
            continue
        print(f"{r['check']:<9}{r['sess']:<6}{r['era']:<6}{r['fire_rate']:>5}"
              f"{r['n_on']:>6}{r['n_off']:>6}"
              f"{r['wr_on']:>6}/{r['wr_off']:<5}"
              f"{r['r_on']:>7}/{r['r_off']:<7}{r['lift_r']:>7}")
    print("\nNOTE TRIG uses census trigger stamps (denser than the v2 CSVs the >11 "
          "threshold was frozen on) — its lift is read as direction only, threshold refit "
          "pending.")


if __name__ == "__main__":
    main()
