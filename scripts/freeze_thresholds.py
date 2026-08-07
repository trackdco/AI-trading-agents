#!/usr/bin/env python3
"""Freeze the canon's live-derived thresholds into config/live_thresholds.json.

LIVE-STACK.md punch-list #1. The scorers (`canon_mechanical.py`, `london_canon.py`)
currently derive five quantiles from the 2025 slice of the trade matrix *at load
time*. In production the thresholds must be baked constants — a value that drifts
with the data is not a frozen threshold. This script computes those five values
ONCE from the matrices (exactly as build_canon does — same merge, same
pre-risk-filter population) and writes them, alongside the already-hardcoded
literals, into a single config file the scorers load.

    python -m scripts.freeze_thresholds            # (re)generate the config
    python -m scripts.freeze_thresholds --check     # assert config == live recompute

Proposals-only: the *values* here are exactly what the validated canon already
uses — freezing changes nothing behaviourally (proven by tests/test_frozen_
thresholds_parity.py). Changing any value is a rule change and needs Angus.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CONFIG = ROOT / "config" / "live_thresholds.json"


def compute_derived() -> dict:
    """The five live-derived quantiles, computed exactly as build_canon does."""
    T = pd.read_parquet(ROOT / "output/trade_matrix.parquet")
    BP = pd.read_parquet(ROOT / "output/badpa_matrix.parquet")[
        ["day", "book", "fill", "netpath_30", "bbw_state", "churn_flow_30", "trigdens_30"]]
    T = T.merge(BP, on=["day", "book", "fill"], how="left")  # same as build_canon
    long = T.direction == "long"
    d15dir = T.d15 * np.where(long, 1, -1)
    g25 = T[(T.win_ == "gold") & (T.yr == 2025)]
    return {
        "pre.Tp_d15dir_min": float(d15dir[T.yr == 2025].quantile(0.25)),
        "pre.G_ent_vs_vwap_sd_dir_min": float(T[T.yr == 2025].ent_vs_vwap_sd_dir.quantile(0.25)),
        "gold.X_bbw_state_min": float(g25.bbw_state.quantile(0.75)),
        "gold.AGE_on_extreme_age_min": float(g25.on_extreme_age.quantile(0.50)),
        "gold.PAQ_netpath_30_min": float(g25.netpath_30.quantile(0.25)),
    }


def build_config() -> dict:
    d = compute_derived()
    return {
        "_meta": {
            "purpose": "Frozen production thresholds for the mechanical canon "
                       "(canon_mechanical.py NY pre/gold + london_canon.py).",
            "derived_from": "2025 slice of output/trade_matrix.parquet merged with "
                            "badpa_matrix.parquet (pre-risk-filter population, as build_canon).",
            "generated_by": "scripts/freeze_thresholds.py",
            "warning": "Do NOT hand-edit `derived`; regenerate with freeze_thresholds.py. "
                       "Changing any threshold is a rule change — Angus sign-off required "
                       "(proposals-only). Literals below are lifted verbatim from the "
                       "validated scorers; parity is enforced by tests.",
        },
        # The five values that used to be computed live (frozen quantiles).
        "derived": {
            "pre": {
                "Tp_d15dir_min": d["pre.Tp_d15dir_min"],
                "G_ent_vs_vwap_sd_dir_min": d["pre.G_ent_vs_vwap_sd_dir_min"],
            },
            "gold": {
                "X_bbw_state_min": d["gold.X_bbw_state_min"],
                "AGE_on_extreme_age_min": d["gold.AGE_on_extreme_age_min"],
                "PAQ_netpath_30_min": d["gold.PAQ_netpath_30_min"],
            },
        },
        # Already-hardcoded literals, lifted here verbatim for a single source of truth.
        "hard_gates": {"ny_stop_min": 7, "ny_stop_max": 60, "london_stop_min": 9.5},
        "gold_quality": {
            "WALLSZ_min_contracts": 7, "BIGFD_fill_delta_abs_min": 173,
            "TRIG_trigdens_30_min_exclusive": 11, "VWAPD_ent_vs_vwap_sd_dir_min": 0.107,
            "LONSLOPE_lon_slope_d_min": -0.0961, "Q_no_trade_max": 1, "Q_boost_min": 3,
        },
        "sizing": {
            "pre_gold_ladder": {"le2": 0.0, "s3": 0.5, "s4": 1.0, "s5": 1.5},
            "london_ladder": {"le1": 0.0, "s2": 0.5, "s3": 1.0, "s4": 1.5},
            "size_cap": 1.5,
        },
        "escalation": {
            "second_trade_min_score_ny": 4, "second_trade_min_score_london": 3,
            "day_loss_stop_dollars": -400,
        },
        "intrade": {"cut3_r3_max": -0.1106, "cut3_fw3_max": -13},
        "sizing_mods": {
            "R1_churn_flow_30_min_exclusive": 0.0292, "R2_netpath_30_min": 0.3328,
            "cold_trail20_wr_max": 0.40,
        },
        "governor": {"trail15_confirmed_wr_min": 0.35},
        "london": {
            "FAR_wall_ahead_d_min_exclusive": 4.5,
            "ROOM_room_R_low_exclusive": 2.48, "ROOM_room_R_high": 9.56,
            "ASIA_dir_cvd_min": -748, "OF_opp5_max_exclusive": 2,
            "B_continuation_min_score": 3,
        },
    }


def write() -> dict:
    cfg = build_config()
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, indent=2) + "\n")
    return cfg


def check() -> int:
    if not CONFIG.exists():
        print(f"MISSING {CONFIG} — run `python -m scripts.freeze_thresholds` first")
        return 1
    cfg = json.loads(CONFIG.read_text())
    live = compute_derived()
    flat = {
        "pre.Tp_d15dir_min": cfg["derived"]["pre"]["Tp_d15dir_min"],
        "pre.G_ent_vs_vwap_sd_dir_min": cfg["derived"]["pre"]["G_ent_vs_vwap_sd_dir_min"],
        "gold.X_bbw_state_min": cfg["derived"]["gold"]["X_bbw_state_min"],
        "gold.AGE_on_extreme_age_min": cfg["derived"]["gold"]["AGE_on_extreme_age_min"],
        "gold.PAQ_netpath_30_min": cfg["derived"]["gold"]["PAQ_netpath_30_min"],
    }
    bad = {k: (flat[k], live[k]) for k in live if flat[k] != live[k]}
    if bad:
        print("DRIFT — config != live recompute:")
        for k, (c, l) in bad.items():
            print(f"  {k}: config={c!r} live={l!r}")
        return 1
    print("OK — config matches live recompute for all 5 derived thresholds.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="assert config == live recompute (don't rewrite)")
    args = ap.parse_args()
    if args.check:
        return check()
    cfg = write()
    print(f"wrote {CONFIG.relative_to(ROOT)}")
    for k, v in cfg["derived"]["pre"].items():
        print(f"  pre.{k} = {v:.6g}")
    for k, v in cfg["derived"]["gold"].items():
        print(f"  gold.{k} = {v:.6g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
