"""News sentinel feed-source tests (scripts/news_daily_agent.py).

The faireconomy JSON feed is the source that can run UNATTENDED on the VPS (the FF website
blocks datacenter IPs; the feed is a plain CDN JSON). The network fetch is proven by the
first on-box run — what is pinned here is the conversion into the snapshot schema the gate
consumes, so a live feed cannot silently produce rows the gate misreads.
"""
from __future__ import annotations

import pandas as pd

from scripts.news_daily_agent import rows_from_feed

FEED_SAMPLE = [
    # the documented feed shape: title/country/date(ISO w/ offset)/impact/forecast/previous
    {"title": "Unemployment Claims", "country": "USD",
     "date": "2026-07-30T08:30:00-04:00", "impact": "High",
     "forecast": "221K", "previous": "217K"},
    {"title": "CB Consumer Confidence", "country": "USD",
     "date": "2026-07-28T10:00:00-04:00", "impact": "Medium"},
    {"title": "German Prelim CPI m/m", "country": "EUR",              # non-USD: dropped
     "date": "2026-07-30T02:00:00-04:00", "impact": "High"},
    {"title": "Bank Holiday", "country": "USD",                       # not a release: dropped
     "date": "2026-07-27T00:00:00-04:00", "impact": "Holiday"},
    {"title": "FOMC Statement", "country": "USD",                     # UTC ts: converted to ET
     "date": "2026-07-29T18:00:00+00:00", "impact": "High"},
]


def test_rows_from_feed_schema_and_filters():
    rows = rows_from_feed(FEED_SAMPLE)
    assert [set(r) for r in rows] == [{"datetime_ET", "event", "impact"}] * 3
    by_name = {r["event"]: r for r in rows}
    assert set(by_name) == {"Unemployment Claims", "CB Consumer Confidence", "FOMC Statement"}
    assert by_name["Unemployment Claims"]["datetime_ET"] == "2026-07-30 08:30"
    assert by_name["Unemployment Claims"]["impact"] == "high"
    assert by_name["CB Consumer Confidence"]["impact"] == "medium"
    # 18:00 UTC on Jul 29 is 14:00 in New York (EDT) — the FOMC print, correctly localised
    assert by_name["FOMC Statement"]["datetime_ET"] == "2026-07-29 14:00"


def test_rows_parse_as_calendar_rows():
    """The snapshot must round-trip through the exact reads the gate performs."""
    d = pd.DataFrame(rows_from_feed(FEED_SAMPLE))
    ts = pd.to_datetime(d["datetime_ET"], errors="coerce")
    assert ts.notna().all() and ts.dt.tz is None                 # naive ET, like the calendars
    assert set(d["impact"]) <= {"high", "medium", "low"}


def test_empty_or_alien_feed_yields_no_rows_never_raises():
    assert rows_from_feed([]) == []
    assert rows_from_feed([{"unexpected": "shape"}]) == []       # missing keys -> just dropped
