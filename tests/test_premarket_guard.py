"""PremarketGuard — corrections 2+3 live + the sentinel's fail-closed snapshot contract.

The batch applies these as size->0 inside build_canon; live they veto verdicts at emit
time. Every branch is pinned: the 09:55–10:00 dead zone (half-open), the pre-open
blackout, snapshot-missing fail-closed, calendar-stale fail-closed, NY-only scope."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

import src.canon.news_gate as ng
from src.canon.news_gate import NewsGate
from src.canon.premarket_guard import PremarketGuard

NY = "America/New_York"


def _gate(releases=None, stale="2026-12-31"):
    return NewsGate(releases=releases or {}, promoted=frozenset(),
                    stale_after=pd.Timestamp(stale))


def _v(hm: str, day="2026-07-27", session="NY"):
    ts = pd.Timestamp(f"{day} {hm}", tz=NY)
    return {"session": session, "day": day, "fill": ts.tz_convert("UTC").isoformat()}


@pytest.fixture
def snapshot_today(tmp_path, monkeypatch):
    monkeypatch.setattr(ng, "DAILY_DIR", tmp_path)
    (tmp_path / "news_2026-07-27.csv").write_text("datetime_ET,event,impact\n")
    return tmp_path


def test_dead_zone_vetoes_0955_to_0959_half_open(snapshot_today):
    g = PremarketGuard(gate=_gate())
    assert g.veto(_v("09:55")) == "dead_zone"
    assert g.veto(_v("09:59")) == "dead_zone"
    assert g.veto(_v("09:54")) is None
    assert g.veto(_v("10:00")) is None


def test_pre_open_release_blocks_before_the_print_only(snapshot_today):
    rel = pd.Timestamp("2026-07-27 08:30")
    g = PremarketGuard(gate=_gate(releases={date(2026, 7, 27): rel}))
    assert g.veto(_v("08:15")) == "news_blackout"
    assert g.veto(_v("08:35")) is None                     # after the print: allowed


def test_missing_snapshot_fails_closed_for_all_pre_open(tmp_path, monkeypatch):
    monkeypatch.setattr(ng, "DAILY_DIR", tmp_path)          # empty dir: no board today
    g = PremarketGuard(gate=_gate())
    assert g.veto(_v("08:15")) == "news_snapshot_missing"
    assert g.veto(_v("09:45")) is None                     # post-open: not the sentinel's scope


def test_stale_calendar_fails_closed(snapshot_today):
    g = PremarketGuard(gate=_gate(stale="2026-07-01"))      # calendar ran out weeks ago
    assert g.veto(_v("08:15")) == "news_calendar_stale"


def test_london_verdicts_are_out_of_scope(tmp_path, monkeypatch):
    monkeypatch.setattr(ng, "DAILY_DIR", tmp_path)          # even with no snapshot
    g = PremarketGuard(gate=_gate())
    assert g.veto(_v("04:15", session="LONDON")) is None


def test_unparseable_fill_fails_closed(snapshot_today):
    g = PremarketGuard(gate=_gate())
    assert g.veto({"session": "NY", "day": "2026-07-27", "fill": "not-a-time"}) \
        == "unparseable_fill_ts"


def test_route_b_veto_never_reaches_journal_spine_or_lifecycle(tmp_path):
    """Loop wiring: a vetoed verdict is journaled as a veto in decisions.jsonl and does
    NOT reach verdicts.jsonl / the spine / the lifecycle."""
    import json

    from tests.test_route_b import FixtureVerdictSource, _bar, _live, _tape, _ts, _verdict

    class VetoAll:
        def veto(self, v):
            return "dead_zone"

    fill = _ts("08:01")
    src = FixtureVerdictSource({"2026-03-17": [_verdict(fill)]})
    live = _live(tmp_path, src)
    live.premarket_guard = VetoAll()
    live.dispatch([
        {"kind": "minute", "ts": _ts("08:00"), "bar": _bar(_ts("08:00")), "tape": _tape()},
        {"kind": "minute", "ts": _ts("08:01"), "bar": _bar(_ts("08:01")), "tape": _tape()},
    ], now=_ts("08:01"))
    assert not (tmp_path / "verdicts.jsonl").exists()
    assert not (tmp_path / "sizing.jsonl").exists()
    decs = [json.loads(x) for x in (tmp_path / "decisions.jsonl").read_text().splitlines()]
    veto = next(d for d in decs if d.get("type") == "verdict_veto")
    assert veto["reason"] == "dead_zone"
