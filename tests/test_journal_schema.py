"""Tests for the frozen journal schema (src/desk/journal.py)."""

import pandas as pd
import pytest

from src.backtest.engine import TradeRecord
from src.desk.journal import JournalRecord, coverage_report, from_trade_record

MIN = {
    "trade_date": "2026-02-11", "trigger_ts": "2026-02-11T09:48:00-05:00", "tf": "3min",
    "direction": "short", "entry_variant": "E1", "mgmt_variant": "V0", "config_hash": "abc",
    "kind": "rejection_block", "pattern": "A", "htf_flag": "counter_trend",
    "confluence_count": 3, "entry": 25390.0, "stop_initial": 25405.0, "size": 1.0,
    "exit_ts": "2026-02-11T10:05:00-05:00", "exit_price": 25330.0, "exit_reason": "target",
    "points": 60.0, "r_multiple": 4.0, "dollars": 1200.0,
}


def test_minimal_record_valid():
    r = JournalRecord(**MIN)
    assert r.schema_version.endswith("proposed") and r.confluence_count == 3


def test_extra_field_forbidden():
    with pytest.raises(Exception):
        JournalRecord(**MIN, mig_liquidity=1)     # frozen: stray columns are loud errors


def test_win_must_match_r_sign():
    with pytest.raises(Exception, match="disagrees"):
        JournalRecord(**MIN, win=False)           # r=+4 but win=False
    assert JournalRecord(**MIN, win=True).win is True


def test_cluster_types_unique():
    with pytest.raises(Exception, match="unique"):
        JournalRecord(**MIN, cluster_types=["bb", "bb"])


def test_desk_context_optional_and_accepted():
    r = JournalRecord(**MIN, regime_verdict="war/short/0.5", htf_verdict="trend_down/segment/no_fade",
                      gates_applied=["regime_size_0.5", "htf_no_fade"], size_multiplier_applied=0.5)
    assert r.size_multiplier_applied == 0.5 and "htf_no_fade" in r.gates_applied


def test_from_trade_record_adapter():
    tr = TradeRecord(
        trade_date="2026-02-04", trigger_ts="2026-02-04T09:48:00-05:00", tf="3min",
        direction="short", kind="rejection_block", pattern="B2", htf_flag="with_trend",
        confluence=3, entry_variant="E1", limit_price=25361.25, fill_ts="2026-02-04T09:49:00-05:00",
        entry=25361.25, stop_initial=25376.5, target_name="prior_day_low", target_level=25200.0,
        working_target=25202.5, exit_ts="2026-02-04T10:20:00-05:00", exit_price=25329.0,
        exit_reason="target", points=32.25, r_multiple=2.1, size=1.0, dollars=645.0,
        slippage_ticks=1, mgmt_variant="V0",
    )
    r = from_trade_record(tr, config_hash="champion@deadbeef", regime_verdict="balance/neutral/0.5")
    assert r.confluence_count == 3 and r.risk_pts == pytest.approx(15.25)
    assert r.win is True and r.regime_verdict == "balance/neutral/0.5"


def test_coverage_report_flags_engine_gaps():
    rep = coverage_report(list(TradeRecord.model_fields))
    # TradeRecord lacks config_hash, cluster_types, day_type, path MFE/MAE, review fields, etc.
    miss = rep["missing_by_section"]
    assert "config_hash" in miss["identity"]
    assert "cluster_types" in miss["setup"] and "day_type" in miss["setup"]
    assert "mfe_r" in miss["path"] and "angus_verdict" in miss["review"]
    assert rep["unknown_emitted"] == []          # every TradeRecord field maps into the schema


def test_coverage_report_on_real_champion_journal():
    cols = list(pd.read_csv("output/journal_champion.csv", nrows=0).columns)
    rep = coverage_report(cols)
    # the condensed champion journal is missing execution/path detail the frozen schema wants
    assert rep["missing_by_section"]                       # something to add
    # ...but it legitimately carries fields the frozen schema also has (align_votes etc.)
    assert "align_votes" not in rep["unknown_emitted"]     # recognized, not foreign
