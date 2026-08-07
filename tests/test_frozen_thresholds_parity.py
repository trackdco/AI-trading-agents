"""Parity: freezing the canon's thresholds must change NOTHING.

The refactor replaced five live `.quantile()` calls in canon_mechanical.build_canon
with constants loaded from config/live_thresholds.json. Since the frozen constants
equal the live recompute (freeze_thresholds --check), every `x >= frozen` must be
bit-identical to the old `x >= live_quantile`, so all downstream scoring/sizing is
unchanged.

Run from the repo root: `python -m pytest tests/test_frozen_thresholds_parity.py`
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # build_canon reads relative "output/..." paths

from scripts.live_thresholds import TH  # noqa: E402

BASELINE_ROWS = 713  # unmodified build_canon on the current trade_matrix


def _merged():
    T = pd.read_parquet("output/trade_matrix.parquet")
    BP = pd.read_parquet("output/badpa_matrix.parquet")[
        ["day", "book", "fill", "netpath_30", "bbw_state", "churn_flow_30", "trigdens_30"]]
    return T.merge(BP, on=["day", "book", "fill"], how="left")


def test_frozen_equals_live_for_all_five_checks():
    T = _merged()
    long = T.direction == "long"
    d15dir = T.d15 * np.where(long, 1, -1)
    g25 = T[(T.win_ == "gold") & (T.yr == 2025)]
    live = {
        "Tp": d15dir >= d15dir[T.yr == 2025].quantile(0.25),
        "G": T.ent_vs_vwap_sd_dir >= T[T.yr == 2025].ent_vs_vwap_sd_dir.quantile(0.25),
        "X": T.bbw_state >= g25.bbw_state.quantile(0.75),
        "AGE": T.on_extreme_age >= g25.on_extreme_age.quantile(0.50),
        "PAQ": T.netpath_30 >= g25.netpath_30.quantile(0.25),
    }
    frozen = {
        "Tp": d15dir >= TH.pre_Tp_d15dir_min,
        "G": T.ent_vs_vwap_sd_dir >= TH.pre_G_ent_vs_vwap_sd_dir_min,
        "X": T.bbw_state >= TH.gold_X_bbw_state_min,
        "AGE": T.on_extreme_age >= TH.gold_AGE_on_extreme_age_min,
        "PAQ": T.netpath_30 >= TH.gold_PAQ_netpath_30_min,
    }
    for k in live:
        assert live[k].equals(frozen[k]), f"{k}: frozen threshold differs from live quantile"


def test_build_canon_runs_and_is_deterministic():
    from scripts.canon_mechanical import build_canon
    T = pd.read_parquet("output/trade_matrix.parquet")
    C = build_canon(T)
    assert len(C) == BASELINE_ROWS, f"row count {len(C)} != baseline {BASELINE_ROWS}"
    pd.testing.assert_frame_equal(C, build_canon(T))  # deterministic


if __name__ == "__main__":
    test_frozen_equals_live_for_all_five_checks()
    print("PASS test_frozen_equals_live_for_all_five_checks")
    test_build_canon_runs_and_is_deterministic()
    print("PASS test_build_canon_runs_and_is_deterministic")
    print("\nparity OK")
