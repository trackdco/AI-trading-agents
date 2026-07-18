"""Tests for src/live/vault.py — the streaming champion loop (Phase 4 Stage 2, hardened).

Loop logic is tested fast with a stub simulate. Real-data streaming==batch parity is the
Stage-7 harness (scripts/parity_check.py).
"""

from types import SimpleNamespace

import pandas as pd
import pytest

from src.live.feed import Bar
from src.live.vault import TradeEvent, Vault

NY = "America/New_York"


def _bar(ts, c=25000.0):
    t = pd.Timestamp(ts, tz=NY)
    return Bar(ts_event=t, open=c, high=c + 1, low=c - 1, close=c, volume=100.0)


def _trig(ts, pattern="A", close=25000.0, stop_ref=24990.0):
    return SimpleNamespace(ts=ts, tf="1m", direction="long", pattern=pattern,
                           close=close, stop_ref=stop_ref)


def _rec(trade_date, fill_ts, dollars=100.0, pattern="A"):
    # minimal stand-in for engine TradeRecord (only fields TradeEvent reads)
    return SimpleNamespace(trade_date=trade_date, trigger_ts=fill_ts, direction="long",
                           pattern=pattern, fill_ts=fill_ts, entry=25000.0, stop_initial=24990.0,
                           target_level=25020.0, exit_ts=fill_ts, exit_price=25010.0,
                           exit_reason="target", points=10.0, dollars=dollars, r_multiple=1.0,
                           size=1.0)


def _noop_sim(df, trigs, cfg, day_gate=None):
    return [], [], None


def test_requires_cfg_or_policy():
    with pytest.raises(ValueError):
        Vault()


def test_emits_each_trade_once_as_it_completes():
    # stub simulate: trade for 02-10 appears once its fill bar is in the buffer
    def sim(df, trigs, cfg, day_gate=None):
        out = []
        if any(b == "2026-02-10 09:00" for b in df["ts_event"].astype(str).str[:16]):
            out.append(_rec("2026-02-10", "2026-02-10T09:00"))
        return out, [], None

    seen = []
    v = Vault(cfg="static", triggers=[_trig("2026-02-10T08:31:00-05:00")], sim_fn=sim)
    v.add_sink(seen.append)
    v.on_bar(_bar("2026-02-10 08:31"))          # trigger present, trade not yet
    assert seen == []
    got1 = v.on_bar(_bar("2026-02-10 09:00"))   # fill bar arrives -> emit once
    got2 = v.on_bar(_bar("2026-02-10 09:01"))   # still present -> NOT re-emitted
    assert len(got1) == 1 and got2 == []
    assert len(seen) == 1 and isinstance(seen[0], TradeEvent)
    assert seen[0].trade_date == "2026-02-10" and seen[0].dollars == 100.0


def test_no_causal_trigger_means_no_simulation():
    calls = {"n": 0}

    def sim(df, trigs, cfg, day_gate=None):
        calls["n"] += 1
        return [], [], None
    v = Vault(cfg="static", triggers=[_trig("2026-02-10T09:30:00-05:00")], sim_fn=sim)
    v.on_bar(_bar("2026-02-10 08:00"))          # before the trigger's ts -> skip sim
    assert calls["n"] == 0


def test_causal_and_session_scoped_trigger_filter():
    captured = {}

    def sim(df, trigs, cfg, day_gate=None):
        captured["n"] = len(trigs)
        return [], [], None
    v = Vault(cfg="static", sim_fn=sim,
              triggers=[_trig("2026-02-10T08:30:00-05:00"),      # causal, this session
                        _trig("2026-02-10T09:30:00-05:00"),      # this session, future
                        _trig("2026-02-09T09:00:00-05:00")])     # PRIOR session — excluded
    v.on_bar(_bar("2026-02-10 08:45"))
    assert captured["n"] == 1                    # only the causal same-session trigger


def test_day_gate_is_passed_through():
    got = {}

    def sim(df, trigs, cfg, day_gate=None):
        got["gate"] = day_gate
        return [], [], None

    def gate(d):
        return {"stand_down": True}
    v = Vault(cfg="static", triggers=[_trig("2026-02-10T08:30:00-05:00")],
              day_gate=gate, sim_fn=sim)
    v.on_bar(_bar("2026-02-10 08:45"))
    assert got["gate"] is gate                   # the seam reaches simulate untouched


def test_session_policy_picks_book_cfg_and_filter_per_session():
    picked = []

    def sim(df, trigs, cfg, day_gate=None):
        picked.append((cfg, len(trigs)))
        return [], [], None

    def policy(day):
        if day == "2026-02-10":
            return "E4", "cfg-E4", lambda t: abs(t.close - t.stop_ref) <= 15.0
        return "E3", "cfg-E3", lambda t: True

    v = Vault(session_policy=policy, sim_fn=sim, triggers=[
        _trig("2026-02-10T08:30:00-05:00", close=25000.0, stop_ref=24990.0),   # 10pt: E4-ok
        _trig("2026-02-10T08:35:00-05:00", close=25000.0, stop_ref=24950.0),   # 50pt: E4-cut
        _trig("2026-02-11T08:30:00-05:00", close=25000.0, stop_ref=24950.0)])  # E3 day: kept
    v.on_bar(_bar("2026-02-10 09:00"))
    assert v.book == "E4" and picked[-1] == ("cfg-E4", 1)     # wide-stop trigger filtered
    v.on_bar(_bar("2026-02-11 09:00"))
    assert v.book == "E3" and picked[-1] == ("cfg-E3", 1)     # E3 day keeps wide stops


def test_policy_none_sits_the_session_out():
    calls = {"n": 0}

    def sim(df, trigs, cfg, day_gate=None):
        calls["n"] += 1
        return [], [], None
    v = Vault(session_policy=lambda day: None, sim_fn=sim,
              triggers=[_trig("2026-02-10T08:30:00-05:00")])
    assert v.on_bar(_bar("2026-02-10 09:00")) == []
    assert calls["n"] == 0


def test_session_roll_cannot_mint_phantom_past_trades():
    # even if a day-2 re-sim returned a REVISED past-session trade, dedup by
    # (date, fill_ts) suppresses re-emission — the emitted record is final.
    def sim(df, trigs, cfg, day_gate=None):
        out = [_rec("2026-02-10", "2026-02-10T09:00")]
        if any(b.startswith("2026-02-11") for b in df["ts_event"].astype(str)):
            out.append(_rec("2026-02-10", "2026-02-10T09:00", dollars=999.0))
        return out, [], None
    v = Vault(cfg="static", sim_fn=sim,
              triggers=[_trig("2026-02-10T08:30:00-05:00"),
                        _trig("2026-02-11T08:30:00-05:00")])
    first = v.on_bar(_bar("2026-02-10 09:00"))
    second = v.on_bar(_bar("2026-02-11 09:00"))
    assert len(first) == 1 and first[0].dollars == 100.0
    assert second == []                          # past trade never re-emitted or revised


def test_sink_error_does_not_kill_loop_or_other_sinks():
    def sim(df, trigs, cfg, day_gate=None):
        return [_rec("2026-02-10", "2026-02-10T09:00")], [], None
    errors, delivered = [], []

    def bad_sink(ev):
        raise RuntimeError("telegram down")
    v = Vault(cfg="static", triggers=[_trig("2026-02-10T08:30:00-05:00")], sim_fn=sim,
              on_sink_error=lambda e, ev: errors.append(str(e)))
    v.add_sink(bad_sink).add_sink(delivered.append)
    out = v.on_bar(_bar("2026-02-10 09:00"))
    assert len(out) == 1                         # loop survived
    assert delivered and errors == ["telegram down"]   # later sink still served


def test_add_triggers_dedup_and_session_refresh():
    captured = {}

    def sim(df, trigs, cfg, day_gate=None):
        captured["n"] = len(trigs)
        return [], [], None
    v = Vault(cfg="static", triggers=[_trig("2026-02-10T08:30:00-05:00")], sim_fn=sim)
    v.on_bar(_bar("2026-02-10 08:45"))
    assert captured["n"] == 1
    v.add_triggers([_trig("2026-02-10T08:30:00-05:00")])       # same identity -> no-op
    v.on_bar(_bar("2026-02-10 08:46"))
    assert captured["n"] == 1
    v.add_triggers([_trig("2026-02-10T08:40:00-05:00")])       # genuinely new -> included
    v.on_bar(_bar("2026-02-10 08:47"))
    assert captured["n"] == 2


def test_session_trim_bounds_the_buffer():
    v = Vault(cfg="static", triggers=[_trig("2026-02-10T08:30:00-05:00")],
              warmup_sessions=1, sim_fn=_noop_sim)
    for d in ("2026-02-10", "2026-02-11", "2026-02-12", "2026-02-13"):
        v.on_bar(_bar(f"{d} 09:00"))
    kept_days = {b.ts_event.strftime("%Y-%m-%d") for b in v._bars}
    assert len(kept_days) <= 2                   # warmup_sessions=1 -> current + 1 prior
