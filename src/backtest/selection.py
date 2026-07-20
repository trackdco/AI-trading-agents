"""Selection-layer gate: the SHIPPED "don't-trade" filter (docs/FINDING-dont-trade-filter.md).

Applied AFTER the deterministic engine produces candidate trades — it decides which
*validated* trades to keep, so it lives OUTSIDE src/engine and never touches fill/stop/
target logic. Two tells, both causal (known at or before entry, no lookahead):

  - below-value opens : skip trades on days whose open printed below the prior value area
                        (open_vs_value == "below_value") — 0% win / -$2,355 in-sample.
  - hollow rejections : skip trades without CVD absorption (cvd > cvd_absorption_max) — the
                        #1 loser/winner separator (winners cvd ~ -74, losers ~ -10).

Reproduced on the 2026 champion journal (IN-SAMPLE): 132t -> 78t, +$14,009 -> +$14,351,
win 33% -> 41%, 5/6 months green. Cross-year OOS is OPEN (docs/FINDING-oracle-is-hindsight...);
this ships as a 2026-regime selection gate, not a proven cross-year edge.
"""
from pathlib import Path

import pandas as pd
import yaml

CONFIG = Path(__file__).resolve().parents[2] / "config" / "strategy.yaml"


def load_selection_filters(path: Path = CONFIG) -> dict:
    """Read the shipped selection-gate parameters from config/strategy.yaml -> filters."""
    f = yaml.safe_load(Path(path).read_text())["filters"]
    return {
        "cut_below_value_open": bool(f.get("cut_below_value_open", False)),
        "require_cvd_absorption": bool(f.get("require_cvd_absorption", False)),
        "cvd_absorption_max": float(f.get("cvd_absorption_max", 0.0)),
    }


def apply_selection_gate(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Return the subset of candidate trades `df` that passes the shipped selection gate.

    Requires columns:
      - open_vs_value : str per-day auction location (only read if cut_below_value_open)
      - cvd           : signed pre-entry aggressive flow, oriented so <=0 = absorption
                        (only read if require_cvd_absorption)

    Non-mutating. NaN semantics match the validated reproduction: a NaN cvd fails the
    absorption test (dropped); a NaN open_vs_value is not "below_value" (kept).
    """
    keep = pd.Series(True, index=df.index)
    if filters.get("cut_below_value_open"):
        keep &= df["open_vs_value"] != "below_value"
    if filters.get("require_cvd_absorption"):
        keep &= df["cvd"] <= filters.get("cvd_absorption_max", 0.0)
    return df[keep].copy()
