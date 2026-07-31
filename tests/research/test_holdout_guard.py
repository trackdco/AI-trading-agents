"""RESEARCH ONLY (claude/agent-exit-london-r1). Tests for src/research/holdout_guard.py
— the one gate every bar-loading path in the agent-exit experiment must call.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research.holdout_guard import (HoldoutTouchedError, assert_fit_only,
                                        assert_path_fit_only)


def test_sealed_year_in_frame_raises():
    bad = pd.DataFrame({"ts_event": pd.to_datetime(["2023-07-03", "2025-06-02"], utc=True)})
    with pytest.raises(HoldoutTouchedError, match="SEALED SPAN TOUCHED"):
        assert_fit_only(bad, "ts_event", "data/reference/nq_1m_master.parquet")


def test_2024_also_raises():
    bad = pd.DataFrame({"ts_event": pd.to_datetime(["2024-10-31"], utc=True)})
    with pytest.raises(HoldoutTouchedError):
        assert_fit_only(bad, "ts_event", "anything.parquet")


def test_fit_only_frame_passes_clean():
    good = pd.DataFrame({"ts_event": pd.to_datetime(["2025-06-02", "2026-07-15"], utc=True)})
    assert_fit_only(good, "ts_event", "data/reference/nq_1m_master.parquet")  # no raise


def test_holdout_named_path_raises_regardless_of_content():
    with pytest.raises(HoldoutTouchedError, match="HOLDOUT PATH REFUSED"):
        assert_path_fit_only("output/l2_outcomes_london_holdout_v1.parquet")


def test_missing_ts_column_raises_rather_than_skip():
    df = pd.DataFrame({"other_col": [1, 2, 3]})
    with pytest.raises(HoldoutTouchedError):
        assert_fit_only(df, "ts_event", "some_file.parquet")


def test_real_master_file_raises_when_loaded_raw():
    """The actual regression this guard exists to catch: a raw, unfiltered read of the
    master parquet physically contains sealed 2023/24 rows."""
    m = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    with pytest.raises(HoldoutTouchedError, match="SEALED SPAN TOUCHED"):
        assert_fit_only(m, "ts_event", "data/reference/nq_1m_master.parquet")


def test_guard_is_called_at_every_bar_loading_entry_point_in_research():
    """Grep-level check (per Stage 2 S2.6): every load_bars()-style function under
    scripts/research/ and src/research/ must call assert_fit_only or
    assert_path_fit_only somewhere in its body. Fails loudly (names the file) if a
    new loader is added without wiring the guard, rather than passing silently."""
    import ast

    guard_names = {"assert_fit_only", "assert_path_fit_only"}
    offenders = []
    for py in list((ROOT / "scripts" / "research").glob("*.py")) + \
              list((ROOT / "src" / "research").glob("*.py")):
        if py.name in ("holdout_guard.py", "__init__.py"):
            continue
        src = py.read_text()
        tree = ast.parse(src)
        defs_reading_bars = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
            and ("bar" in n.name.lower() or "load" in n.name.lower())
        ]
        for fn in defs_reading_bars:
            calls = {c.func.id for c in ast.walk(fn)
                     if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
            if not (calls & guard_names):
                offenders.append(f"{py.name}::{fn.name}")
    assert not offenders, (
        f"bar-loading function(s) without a holdout_guard call: {offenders}")
