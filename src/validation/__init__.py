"""The statistical gate — screening statistics for strategy validation.

Two questions every mined candidate must answer before it earns a holdout look:

  1. **DSR** (`src.validation.dsr`) — is the best Sharpe you found bigger than the best
     Sharpe pure noise would have handed you, given how many things you tried?
  2. **PBO** (`src.validation.pbo`) — does your *selection procedure itself* pick
     out-of-sample winners, or does it pick noise?

Both are SCREENING statistics: they decide which candidates deserve a holdout look. They
are NOT the shipping criterion — promotion still runs through funded-rules Monte Carlo and
maxDD (Sharpe is a volatility measure; the binding constraint is a trailing drawdown).

Calibration against a case with a known honest answer lives in
`scripts/validation_gate_calibrate.py` (the London stage-2 29k sweep / stage-3
selection-null shrinkage model).
"""
from src.validation.dsr import (
    DSRResult,
    deflated_sharpe_ratio,
    expected_max_sharpe,
    min_track_record_length,
    probabilistic_sharpe_ratio,
    sharpe_ratio,
)
from src.validation.pbo import PBOResult, pbo_cscv

__all__ = [
    "DSRResult",
    "PBOResult",
    "deflated_sharpe_ratio",
    "expected_max_sharpe",
    "min_track_record_length",
    "pbo_cscv",
    "probabilistic_sharpe_ratio",
    "sharpe_ratio",
]
