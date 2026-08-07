"""Tests for src/desk/regime_agent.py — L3 briefing, schema, gate (desk contract).

Mandatory properties: no-lookahead briefing (perturbing bars at/after the 08:00
cutoff changes nothing), strict fail-closed verdict validation, deterministic
prompts, stand-down consistency in the gate mapping.
"""

import json
from datetime import time
from pathlib import Path

import pandas as pd
import pytest

from src.desk.regime_agent import (
    RegimeVerdict,
    build_briefing,
    parse_verdict,
    render_prompt,
    verdict_to_gate,
)

NY = "America/New_York"


def _bars(start_ny: str, n: int, base: float = 25000.0) -> pd.DataFrame:
    idx = pd.date_range(pd.Timestamp(start_ny, tz=NY), periods=n, freq="1min")
    px = base + pd.Series(range(n), dtype=float).mul(0.25)
    return pd.DataFrame({"ts_event": idx, "open": px, "high": px + 2, "low": px - 2,
                         "close": px + 1, "volume": 100})


def _fixture_frame() -> pd.DataFrame:
    # three CME sessions: Feb 10, 11, 12 (each 18:00 prev -> ~10:00), enough for stats
    parts = [
        _bars("2026-02-09 18:00", 600, 25000),   # Feb 10 session
        _bars("2026-02-10 18:00", 600, 25100),   # Feb 11 session
        _bars("2026-02-11 18:00", 600, 25200),   # Feb 12 session (overnight for our date)
    ]
    return pd.concat(parts, ignore_index=True)


def _vector() -> pd.DataFrame:
    return pd.DataFrame([{
        "day": "2026-02-12", "day_type": "balanced", "imbal_share_20": 0.4,
        "imbal_share_10": 0.5, "trap_rate_10": 0.1, "range_pctl_20": 0.5,
        "gap_open_pts": 12.0, "streak_imbal": 0, "red_folder_today": 1,
    }])


def _calendar() -> pd.DataFrame:
    rows = [
        {"datetime_ET": pd.Timestamp("2026-02-12 08:30", tz=NY), "event": "CPI", "impact": "high"},
        {"datetime_ET": pd.Timestamp("2026-02-13 08:30", tz=NY), "event": "PPI", "impact": "high"},
        {"datetime_ET": pd.Timestamp("2026-02-10 10:00", tz=NY), "event": "X", "impact": "medium"},
    ]
    return pd.DataFrame(rows)


VALID = {
    "schema_version": "1.0", "agent_version": "abc123def456", "date": "2026-02-12",
    "regime": "event_risk", "directional_bias": "neutral",
    "permitted_structures": ["reversion"], "stand_down": False, "size_multiplier": 0.5,
    "confidence": "medium", "rationale": "CPI 08:30 today (calendar); mixed tape.",
    "cited_evidence": ["regime_vector.red_folder_today=1"],
    "playbook_notes": "CPI days: half size until release resolves.",
}


# ------------------------------------------------------------------ no-lookahead

def test_briefing_no_lookahead():
    df = _fixture_frame()
    b1 = build_briefing("2026-02-12", df, _vector(), _calendar())
    # append bars at/after the 08:00 cutoff with wild prices — briefing must not change
    poisoned = pd.concat([df, _bars("2026-02-12 08:00", 300, 99999.0)], ignore_index=True)
    b2 = build_briefing("2026-02-12", poisoned, _vector(), _calendar())
    assert json.dumps(b1, sort_keys=True, default=str) == json.dumps(b2, sort_keys=True, default=str)


def test_briefing_includes_today_schedule_but_never_tomorrow():
    b = build_briefing("2026-02-12", _fixture_frame(), _vector(), _calendar())
    events = [(c["event"], c["today"]) for c in b["calendar"]]
    assert ("CPI", True) in events            # today's schedule is ex-ante knowledge
    assert all(e != "PPI" for e, _ in events)  # tomorrow's never appears


def test_briefing_news_filtered_to_pre_cutoff():
    news = pd.DataFrame([
        {"published_ET": pd.Timestamp("2026-02-12 06:00", tz=NY), "headline": "early"},
        {"published_ET": pd.Timestamp("2026-02-12 09:00", tz=NY), "headline": "late"},
    ])
    b = build_briefing("2026-02-12", _fixture_frame(), _vector(), _calendar(), news=news)
    heads = [n["headline"] for n in b["news"]]
    assert heads == ["early"]                  # post-cutoff headline excluded by the builder


def test_briefing_requires_vector_row():
    with pytest.raises(ValueError, match="no row"):
        build_briefing("2026-02-13", _fixture_frame(), _vector(), _calendar())


# ------------------------------------------------------------------ verdict schema

def test_valid_verdict_parses():
    v = RegimeVerdict.model_validate(VALID)
    assert v.regime == "event_risk" and v.size_multiplier == 0.5


@pytest.mark.parametrize("mutation", [
    {"regime": "chaos"},                          # unknown regime
    {"size_multiplier": 0.7},                     # off-menu size
    {"stand_down": True},                         # stand_down but structures/size non-empty
    {"permitted_structures": ["breakout"]},       # unknown structure
    {"extra_field": 1},                           # extra='forbid'
    {"cited_evidence": []},                       # must cite something
    {"size_multiplier": 0.0},                     # size 0 without stand_down
])
def test_invalid_verdicts_fail_closed(mutation):
    bad = {**VALID, **mutation}
    with pytest.raises(Exception):
        RegimeVerdict.model_validate(bad)


def test_stand_down_consistent_form_passes():
    v = RegimeVerdict.model_validate({**VALID, "stand_down": True,
                                      "permitted_structures": [], "size_multiplier": 0.0})
    g = verdict_to_gate(v)
    assert not g.allow_reversion and not g.allow_continuation and g.size_multiplier == 0.0


def test_parse_verdict_checks_date_echo_and_fences():
    fenced = "```json\n" + json.dumps(VALID) + "\n```"
    assert parse_verdict(fenced, "2026-02-12").date == "2026-02-12"
    with pytest.raises(ValueError, match="!= briefing date"):
        parse_verdict(json.dumps(VALID), "2026-02-13")


# ------------------------------------------------------------------ determinism + gate

def test_prompt_deterministic(tmp_path: Path):
    agent = tmp_path / "agent.md"
    agent.write_text("---\nversion: 0.0.1\ntools: []\n---\nrole text")
    b = build_briefing("2026-02-12", _fixture_frame(), _vector(), _calendar())
    assert render_prompt(b, agent) == render_prompt(b, agent)


def test_agent_file_declares_zero_tools():
    text = Path(".claude/agents/regime-context.md").read_text()
    assert "tools: []" in text.split("---")[1]   # frontmatter, blueprint §6.1 rule


def test_gate_mapping_active_day():
    g = verdict_to_gate(RegimeVerdict.model_validate(VALID))
    assert g.allow_reversion and not g.allow_continuation
    assert g.size_multiplier == 0.5 and g.date == "2026-02-12"


def test_overnight_and_shocks_computed():
    b = build_briefing("2026-02-12", _fixture_frame(), _vector(), _calendar())
    assert b["overnight"] is not None and b["overnight"]["range_pts"] > 0
    assert b["shock_bars"]["count"] == 0       # calm synthetic tape: no shocks
    assert time.fromisoformat(b["cutoff_et"][11:19]) == time(8, 0)
