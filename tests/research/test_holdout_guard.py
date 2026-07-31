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
                                        assert_path_fit_only, filter_to_fit_years)


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


def test_filter_to_fit_years_drops_sealed_rows_and_logs(capsys):
    """The one legitimate filter-and-continue: the raw master bars file is shared and
    unpartitioned (2023-2026) by design, so filtering it to fit years is correct — but
    must be loud, not silent."""
    mixed = pd.DataFrame({"ts_event": pd.to_datetime(
        ["2023-07-03", "2024-10-31", "2025-06-02", "2026-07-15"], utc=True)})
    out = filter_to_fit_years(mixed, "ts_event", "nq_1m_master.parquet")
    assert len(out) == 2
    assert set(pd.to_datetime(out.ts_event).dt.year) == {2025, 2026}
    printed = capsys.readouterr().out
    assert "dropping 2" in printed and "2023" in printed and "2024" in printed


def test_filter_to_fit_years_self_checks_with_assert_fit_only():
    """The filter's own output must pass assert_fit_only — if a future edit to
    filter_to_fit_years ever let a sealed row leak through, this self-check inside the
    function raises immediately rather than downstream."""
    clean = pd.DataFrame({"ts_event": pd.to_datetime(["2025-01-01", "2026-01-01"],
                                                      utc=True)})
    out = filter_to_fit_years(clean, "ts_event", "src")
    assert_fit_only(out, "ts_event", "src")  # no raise


def test_filter_to_fit_years_on_real_master_yields_only_fit_years():
    m = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    out = filter_to_fit_years(m, "ts_event", "data/reference/nq_1m_master.parquet")
    assert set(pd.to_datetime(out.ts_event).dt.year) <= {2025, 2026}
    assert len(out) < len(m)          # real sealed rows were actually present and cut


def test_guard_is_called_at_every_bar_loading_entry_point_in_research():
    """Grep-level check (per Stage 2 S2.6): every load_bars()-style function under
    scripts/research/ and src/research/ must call assert_fit_only, assert_path_fit_only,
    or filter_to_fit_years (which itself wraps assert_fit_only as a self-check) somewhere
    in its body. Fails loudly (names the file) if a new loader is added without wiring
    the guard, rather than passing silently."""
    import ast

    guard_names = {"assert_fit_only", "assert_path_fit_only", "filter_to_fit_years"}
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
