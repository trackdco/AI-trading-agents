"""Tests for src/desk/htf_agent.py — 4H/daily structure briefing, schema, gate.

Same desk-contract properties as the regime agent: no-lookahead, fail-closed
schema, deterministic prompts, zero-tools agent file — plus hand-computed
session-anchored 4H bins and fractal-swing fixtures.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.desk.htf_agent import (
    HTFStructureVerdict,
    build_structure_briefing,
    fractal_swings,
    mech_classify,
    parse_verdict,
    resample_h4,
    verdict_to_gate,
)

NY = "America/New_York"


def _bars(start_ny: str, n: int, base: float = 25000.0, step: float = 0.0) -> pd.DataFrame:
    idx = pd.date_range(pd.Timestamp(start_ny, tz=NY), periods=n, freq="1min")
    px = base + pd.Series(range(n), dtype=float).mul(step)
    return pd.DataFrame({"ts_event": idx, "open": px, "high": px + 2, "low": px - 2,
                         "close": px + 1, "volume": 100})


def _frame() -> pd.DataFrame:
    # five sessions so daily k=2 swings can confirm; overnight for the brief date
    parts = [_bars(f"2026-02-{d:02d} 18:00", 840, base) for d, base in
             [(9, 25000), (10, 25300), (11, 25100), (12, 25400), (15, 25200)]]
    parts.append(_bars("2026-02-16 18:00", 840, 25250))   # overnight into Feb 17, thru 07:59
    return pd.concat(parts, ignore_index=True)


VALID = {
    "schema_version": "1.0", "agent_version": "abc123def456", "date": "2026-02-17",
    "daily_context": "range", "h4_leg": "up", "h4_leg_nested_as": "rotation",
    "fade_permitted": True, "continuation_only": False, "confidence": "medium",
    "rationale": "Overlapping daily swings; leg inside range.",
    "cited_evidence": ["daily_swings_mechanical.classification=range"],
    "playbook_notes": "n",
}


# ------------------------------------------------------------------ 4H resampler

def test_h4_bins_session_anchored():
    df = _bars("2026-02-09 18:00", 8 * 60, 25000)   # 18:00 -> 02:00, two full 4H bins
    h4 = resample_h4(df)
    starts = [str(t)[11:16] for t in h4["ts_open"]]
    assert starts == ["18:00"]                       # 22:00 bin is the forming one, dropped
    df2 = _bars("2026-02-09 18:00", 12 * 60, 25000)  # through 06:00 -> bins 18,22 complete
    assert [str(t)[11:16] for t in resample_h4(df2)["ts_open"]] == ["18:00", "22:00"]


def test_h4_bin_edges_at_expected_wall_clock():
    df = _bars("2026-02-10 06:00", 10 * 60, 25000)   # 06:00 -> 16:00 spans 06,10,14 bins
    h4 = resample_h4(df)
    assert [str(t)[11:16] for t in h4["ts_open"]] == ["06:00", "10:00"]


def test_h4_aggregation_hand_computed():
    df = _bars("2026-02-09 18:00", 12 * 60, 25000, step=1.0)  # rising 1pt/min
    h4 = resample_h4(df)
    first = h4.iloc[0]
    assert first["open"] == 25000.0
    assert first["close"] == 25000.0 + 239 + 1     # last minute of the bin, close = px+1
    assert first["high"] == 25000.0 + 239 + 2


# ------------------------------------------------------------------ swings

def test_fractal_swings_hand_computed():
    bars = pd.DataFrame({
        "day": [f"d{i}" for i in range(7)],
        "high": [10, 12, 15, 12, 11, 13, 12],       # swing high at idx2 (15)
        "low":  [8, 9, 11, 9, 7, 9, 10],            # swing low  at idx4 (7)
    })
    s = fractal_swings(bars, "day", k=2)
    assert s["swing_highs"] == [("d2", 15.0)]
    assert s["swing_lows"] == [("d4", 7.0)]


def test_mech_classify_mapping():
    up = {"swing_highs": [("a", 10), ("b", 12)], "swing_lows": [("a", 8), ("b", 9)]}
    dn = {"swing_highs": [("a", 12), ("b", 10)], "swing_lows": [("a", 9), ("b", 8)]}
    mixed = {"swing_highs": [("a", 10), ("b", 12)], "swing_lows": [("a", 9), ("b", 8)]}
    short = {"swing_highs": [("a", 10)], "swing_lows": [("a", 8), ("b", 9)]}
    assert mech_classify(up) == "trend_up"
    assert mech_classify(dn) == "trend_down"
    assert mech_classify(mixed) == "range"
    assert mech_classify(short) == "unknown"


# ------------------------------------------------------------------ briefing

def test_structure_briefing_no_lookahead():
    df = _frame()
    b1 = build_structure_briefing("2026-02-17", df)
    poisoned = pd.concat([df, _bars("2026-02-17 08:00", 300, 99999.0)], ignore_index=True)
    b2 = build_structure_briefing("2026-02-17", poisoned)
    assert json.dumps(b1, sort_keys=True, default=str) == json.dumps(b2, sort_keys=True, default=str)


def test_briefing_includes_interlock_when_present():
    rv = pd.DataFrame([{"date": "2026-02-17", "regime": "war", "directional_bias": "short",
                        "stand_down": False, "size_multiplier": 0.5, "confidence": "high"}])
    b = build_structure_briefing("2026-02-17", _frame(), regime_verdicts=rv)
    assert b["regime_verdict_today"]["regime"] == "war"
    b2 = build_structure_briefing("2026-02-17", _frame(), regime_verdicts=None)
    assert isinstance(b2["regime_verdict_today"], str)   # absent -> explicit note


def test_briefing_has_no_forming_h4_bar():
    b = build_structure_briefing("2026-02-17", _frame())
    # cutoff 08:00 sits inside the 06:00-10:00 bin -> last briefed bin must start 02:00
    assert b["h4_bars"][-1]["t"][11:16] == "02:00"


# ------------------------------------------------------------------ schema fail-closed

def test_valid_verdict_parses():
    v = HTFStructureVerdict.model_validate(VALID)
    g = verdict_to_gate(v)
    assert g.fade_permitted and not g.continuation_only


@pytest.mark.parametrize("mutation", [
    {"daily_context": "sideways"},                       # unknown enum
    {"h4_leg_nested_as": "trend_segment"},               # trend segment but fade permitted
    {"fade_permitted": True, "continuation_only": True}, # mutually exclusive
    {"daily_context": "unknown"},                        # unknown context but fade permitted
    {"extra": 1},                                        # extra='forbid'
    {"cited_evidence": []},                              # must cite
])
def test_invalid_verdicts_fail_closed(mutation):
    with pytest.raises(Exception):
        HTFStructureVerdict.model_validate({**VALID, **mutation})


def test_parse_checks_date_echo():
    with pytest.raises(ValueError, match="!= briefing date"):
        parse_verdict(json.dumps(VALID), "2026-02-18")


def test_agent_file_declares_zero_tools():
    text = Path(".claude/agents/htf-structure.md").read_text()
    assert "tools: []" in text.split("---")[1]
