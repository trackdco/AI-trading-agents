"""Tests for src/live/feed.py — the replay bar feed (Phase 4 Stage 1)."""

import pandas as pd
import pytest

from src.live.feed import Bar, ReplayFeed

NY = "America/New_York"


def _df(start="2026-02-10 09:30", n=5, base=25000.0):
    idx = pd.date_range(pd.Timestamp(start, tz=NY), periods=n, freq="1min")
    return pd.DataFrame({"ts_event": idx, "open": [base + i for i in range(n)],
                         "high": [base + i + 2 for i in range(n)],
                         "low": [base + i - 2 for i in range(n)],
                         "close": [base + i + 1 for i in range(n)],
                         "volume": [100] * n})


def test_streams_all_bars_in_order_and_closed():
    feed = ReplayFeed(_df(n=5))
    bars = list(feed.stream())
    assert len(bars) == 5 and len(feed) == 5
    ts = [b.ts_event for b in bars]
    assert ts == sorted(ts)                       # chronological
    assert all(isinstance(b, Bar) for b in bars)
    with pytest.raises(Exception):                # frozen — delivered bar can't mutate
        bars[0].close = 1.0


def test_date_window_inclusive_of_end_day():
    df = pd.concat([_df("2026-02-10 09:30", 3), _df("2026-02-11 09:30", 3),
                    _df("2026-02-12 09:30", 3)], ignore_index=True)
    days = {b.ts_event.strftime("%Y-%m-%d") for b in
            ReplayFeed(df, start="2026-02-11", end="2026-02-11").stream()}
    assert days == {"2026-02-11"}                 # end day fully included, others excluded


def test_warmup_prepends_lead_in():
    df = pd.concat([_df("2026-02-10 09:30", 3), _df("2026-02-11 09:30", 3)],
                   ignore_index=True)
    days = {b.ts_event.strftime("%Y-%m-%d") for b in
            ReplayFeed(df, start="2026-02-11", end="2026-02-11", warmup_days=1).stream()}
    assert days == {"2026-02-10", "2026-02-11"}   # warmup pulled the prior day in


def test_bars_df_roundtrips_for_parity_checks():
    df = _df(n=4)
    out = ReplayFeed(df).bars_df()
    assert list(out.columns) == ["ts_event", "open", "high", "low", "close", "volume"]
    assert len(out) == 4


def test_missing_columns_rejected():
    with pytest.raises(ValueError):
        ReplayFeed(pd.DataFrame({"ts_event": [pd.Timestamp("2026-02-10", tz=NY)]}))


def test_source_is_sorted_even_if_input_unordered():
    df = _df(n=4).iloc[::-1].reset_index(drop=True)      # reversed input
    ts = [b.ts_event for b in ReplayFeed(df).stream()]
    assert ts == sorted(ts)
