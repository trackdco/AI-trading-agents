"""Tests for src/live/ambient.py — the three CANON-ruling ambient journal fields.

Each field is a documented proxy (docs/ambient-instrumentation-choices.md); these pin the
mechanical definition so a later ruling change is a visible test change, not silent drift.
"""

from types import SimpleNamespace

import pandas as pd

from src.live import ambient

NY = "America/New_York"


def _bars(rows):
    """rows: (ts 'YYYY-MM-DD HH:MM', high, low)."""
    return pd.DataFrame([
        {"ts_event": pd.Timestamp(ts, tz=NY), "open": (h + l) / 2, "high": h, "low": l,
         "close": (h + l) / 2, "volume": 100.0}
        for ts, h, l in rows])


def _cal(rows):
    """rows: (ts 'YYYY-MM-DD HH:MM', event, impact)."""
    return pd.DataFrame([{"datetime_ET": pd.Timestamp(ts), "event": ev, "impact": imp}
                         for ts, ev, imp in rows])


# --------------------------------------------------------------------- spread proxy
def test_range_spread_is_fill_bar_high_low():
    bars = _bars([("2026-02-10 08:59", 25010, 25000), ("2026-02-10 09:00", 25012, 25004)])
    assert ambient.range_spread(bars, "2026-02-10T09:00") == 8.0     # 25012-25004


def test_range_spread_none_when_no_matching_bar():
    bars = _bars([("2026-02-10 08:59", 25010, 25000)])
    assert ambient.range_spread(bars, "2026-02-10T12:00") == 10.0    # falls back to <= bar
    assert ambient.range_spread(bars, "2026-02-10T06:00") is None    # nothing at/before


def test_recent_spreads_are_pre_fill_same_session_only():
    bars = _bars([
        ("2026-02-09 15:00", 25100, 25000),          # prior session — excluded
        ("2026-02-10 08:58", 25010, 25005),          # pre-fill  -> 5
        ("2026-02-10 08:59", 25010, 25004),          # pre-fill  -> 6
        ("2026-02-10 09:00", 25020, 25000),          # the fill bar itself — excluded
        ("2026-02-10 09:01", 25030, 25000)])         # post-fill — excluded
    got = ambient.recent_spreads(bars, "2026-02-10T09:00")
    assert got == [5.0, 6.0]


# --------------------------------------------------------------------- news calendar
def test_news_state_signed_minutes_to_nearest_high_impact():
    cal = _cal([("2026-02-04 08:30", "NFP", "high"), ("2026-02-04 10:00", "ISM", "high")])
    assert ambient.news_calendar_state(cal, "2026-02-04T08:38") == "NFP:T+8"   # 8m after
    assert ambient.news_calendar_state(cal, "2026-02-04T08:15") == "NFP:T-15"  # 15m before


def test_news_state_ignores_non_high_impact():
    cal = _cal([("2026-02-05 08:30", "Claims", "medium"), ("2026-02-05 10:00", "JOLTS", "medium")])
    assert ambient.news_calendar_state(cal, "2026-02-05T08:31") == "none"


def test_news_state_none_when_no_calendar():
    assert ambient.news_calendar_state(None, "2026-02-05T08:31") == "none"
    assert ambient.news_calendar_state(pd.DataFrame(), "2026-02-05T08:31") == "none"


# --------------------------------------------------------------------- sweep state
def _tr(direction, fill):
    return SimpleNamespace(direction=direction, fill_ts=fill)


def test_sweep_before_entry_long_pierces_prior_low():
    bars = _bars([
        ("2026-02-09 10:00", 25100, 25050),          # prior-session low = 25050 (pool)
        ("2026-02-10 08:40", 25060, 25040),          # pre-fill dips to 25040 < pool -> swept
        ("2026-02-10 09:00", 25070, 25060)])         # fill bar
    assert ambient.sweep_state(bars, _tr("long", "2026-02-10T09:00")) == "swept_before_entry"


def test_sweep_after_entry_long():
    bars = _bars([
        ("2026-02-09 10:00", 25100, 25050),          # pool low 25050
        ("2026-02-10 08:40", 25060, 25055),          # pre-fill stays above pool
        ("2026-02-10 09:00", 25070, 25060),          # fill bar
        ("2026-02-10 09:05", 25065, 25040)])         # AFTER: dips below pool
    assert ambient.sweep_state(bars, _tr("long", "2026-02-10T09:00")) == "swept_after_entry"


def test_no_sweep_when_pool_untouched():
    bars = _bars([
        ("2026-02-09 10:00", 25100, 25050),
        ("2026-02-10 08:40", 25060, 25055),
        ("2026-02-10 09:00", 25070, 25060)])
    assert ambient.sweep_state(bars, _tr("long", "2026-02-10T09:00")) == "no_sweep"


def test_sweep_short_pierces_prior_high():
    bars = _bars([
        ("2026-02-09 10:00", 25100, 25050),          # prior-session high 25100 (pool)
        ("2026-02-10 08:40", 25120, 25090),          # pre-fill pokes above 25100 -> swept
        ("2026-02-10 09:00", 25095, 25085)])
    assert ambient.sweep_state(bars, _tr("short", "2026-02-10T09:00")) == "swept_before_entry"


def test_sweep_unknown_without_prior_session():
    bars = _bars([("2026-02-10 08:40", 25060, 25055), ("2026-02-10 09:00", 25070, 25060)])
    assert ambient.sweep_state(bars, _tr("long", "2026-02-10T09:00")) == "unknown"


# --------------------------------------------------------------------- assembly + fail-soft
def test_compute_ambient_returns_all_three_fields():
    bars = _bars([
        ("2026-02-09 10:00", 25100, 25050),
        ("2026-02-10 08:40", 25060, 25040),
        ("2026-02-10 09:00", 25012, 25004)])
    cal = _cal([("2026-02-10 09:05", "CPI", "high")])
    tr = _tr("long", "2026-02-10T09:00")
    amb = ambient.compute_ambient(bars, cal, tr)
    assert amb == {"spread_at_fill": 8.0, "news_calendar_state": "CPI:T-5",
                   "sweep_state": "swept_before_entry"}


def test_compute_ambient_is_failsoft():
    # a broken bars frame must yield Nones, never raise
    amb = ambient.compute_ambient("not a frame", None, _tr("long", "2026-02-10T09:00"))
    assert amb["spread_at_fill"] is None and amb["news_calendar_state"] == "none"
    assert amb["sweep_state"] == "unknown"


def test_vault_ambient_adapter_signature():
    bars = _bars([("2026-02-10 09:00", 25012, 25004)])
    amb = ambient.vault_ambient(_tr("long", "2026-02-10T09:00"), bars, None)
    assert amb["spread_at_fill"] == 8.0
