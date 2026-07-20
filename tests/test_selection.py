"""Lock the SHIPPED selection gate to its validated in-sample numbers.

The gate (below-value cut + CVD absorption) is docs/FINDING-dont-trade-filter.md. If a
future change moves these numbers, that is a strategy change and must be intentional —
this test makes it impossible to do silently.
"""
from pathlib import Path

import pandas as pd

from src.backtest.selection import apply_selection_gate, load_selection_filters

ROOT = Path(__file__).resolve().parents[1]


def _champion_journal_with_value():
    """The committed 2026 champion journal joined to per-day auction location."""
    j = pd.read_csv(ROOT / "output/handoff/champ_journal_cvd.csv")
    v = (pd.read_csv(ROOT / "output/regime_vector.csv")[["day", "open_vs_value"]]
         .rename(columns={"day": "date"}))
    return j.merge(v, on="date", how="left")


def test_config_default_ships_the_gate_on():
    f = load_selection_filters()
    assert f["cut_below_value_open"] is True
    assert f["require_cvd_absorption"] is True
    assert f["cvd_absorption_max"] == 0.0


def test_shipped_gate_reproduces_finding():
    j = _champion_journal_with_value()
    assert len(j) == 132  # baseline substrate
    gated = apply_selection_gate(j, load_selection_filters())
    assert len(gated) == 78                              # 132 -> 78 trades
    assert abs(gated.dollars.sum() - 14351) < 1.0        # +$14,351 (kept the money)
    assert round(gated.win.mean() * 100) == 41           # 33% -> 41% win
    by_month = gated.groupby(gated.date.str[:7]).dollars.sum()
    assert len(by_month) == 6 and (by_month > 0).sum() == 5  # 5/6 months green


def test_gate_is_non_mutating_and_subsetting():
    j = _champion_journal_with_value()
    n_before = len(j)
    gated = apply_selection_gate(j, load_selection_filters())
    assert len(j) == n_before          # input untouched
    assert set(gated.index) <= set(j.index)  # strict subset of the candidates
