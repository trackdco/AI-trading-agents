"""Pins the two footprint invariants that drifted, so they cannot drift again.

1. The aggressor-side sign: 'B' is the BUYER-aggressor, so signed delta is B - A.
   Two consumers had this inverted. Settled empirically (see src/engine/footprint):
   over 287 London sessions, B - A scores pearson r = +0.7293 against the realised
   open-to-close move from the independent 1m bar master, rising to +0.7754 on the 138
   sessions with |move| >= 40 pts and +0.7944 on the top 20 by |move|. A - B is the
   exact negative. There is no ambiguity to preserve.

2. No consumer reads data/reference/cvd directly. Every read goes through
   src/engine/footprint so the front-month band-clean and the sealed-holdout guard are
   applied once, not re-implemented eleven times.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from src.engine import footprint as fp

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- 1. the sign

def test_buy_aggressor_is_B():
    """The constant itself, so a flip is a one-line diff that fails here."""
    assert fp.BUY_AGGRESSOR == "B"
    assert fp.SELL_AGGRESSOR == "A"


def test_signed_delta_is_buy_positive():
    """A minute of pure buyer-aggression must produce a POSITIVE delta."""
    df = pd.DataFrame({
        "ts_minute": pd.to_datetime(["2025-06-02 08:00", "2025-06-02 08:00",
                                     "2025-06-02 08:01"], utc=True),
        "price": [21000.0, 21000.25, 21001.0],
        "side": ["B", "A", "B"],
        "volume": [100, 40, 7],
    })
    d = fp.signed_delta(df, by=("ts_minute",))
    assert d.iloc[0] == 60, "B=100 vs A=40 must give +60, not -60"
    assert d.iloc[1] == 7, "a pure-buy minute must be positive"


def test_signed_delta_rejects_hand_rolled_inverse():
    """Guard against the specific defect: A - B is the wrong sign, not a variant."""
    df = pd.DataFrame({
        "ts_minute": pd.to_datetime(["2025-06-02 08:00"] * 2, utc=True),
        "price": [21000.0, 21000.0], "side": ["B", "A"], "volume": [10, 3],
    })
    assert fp.signed_delta(df).iloc[0] > 0


# ------------------------------------------------- 2. the read chokepoint

_ALLOWED = {
    "src/engine/footprint.py",          # the chokepoint itself
    "scripts/sample_holdout_days.py",   # emits the path in generated prose, never reads
    "tests/test_footprint_convention.py",
}
_READ = re.compile(r"read_parquet\s*\(\s*[^)]*reference/cvd", re.S)


def _sources():
    for base in ("scripts", "src"):
        for p in sorted((ROOT / base).rglob("*.py")):
            rel = p.relative_to(ROOT).as_posix()
            if rel not in _ALLOWED:
                yield rel, p.read_text()


def test_no_direct_footprint_reads():
    """pd.read_parquet on data/reference/cvd outside the chokepoint is a defect."""
    offenders = [rel for rel, src in _sources() if _READ.search(src)]
    assert not offenders, (
        "these read the footprint directly instead of via src/engine/footprint, so they "
        "skip the front-month band-clean and the sealed-holdout guard: " + ", ".join(offenders)
    )


def test_sealed_holdout_is_guarded():
    """Passing a sealed file without an explicit declaration must raise, not warn."""
    with pytest.raises(PermissionError):
        fp.load_footprint(
            [fp.CVD_DIR / "footprint_holdout_2023-07.parquet"], bands={})


def test_band_clean_requires_price():
    """Dropping the price column is how the contamination became unobservable."""
    with pytest.raises(ValueError):
        fp.load_footprint([fp.CVD_DIR / "footprint_q3_2025.parquet"], bands={},
                          columns=("ts_minute", "side", "volume"))
