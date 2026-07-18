"""Tests for src/live/vault.py — the streaming champion loop (Phase 4 Stage 2).

Loop logic (dedup, sinks, causal triggers, session trim) is tested fast with a stub
simulate. Real-data streaming==batch parity is the Stage-7 harness (scripts/parity_check.py).
"""

from types import SimpleNamespace

import pandas as pd

from src.live.feed import Bar
from src.live.vault import TradeEvent, Vault

NY = "America/New_York"


def _bar(ts, c=25000.0):
    t = pd.Timestamp(ts, tz=NY)
    return Bar(ts_event=t, open=c, high=c + 1, low=c - 1, close=c, volume=100.0)


def _trig(ts):
    return SimpleNamespace(ts=ts)


def _rec(trade_date, fill_ts, dollars=100.0, pattern="A"):
    # minimal stand-in for engine TradeRecord (only fields TradeEvent reads)
    return SimpleNamespace(trade_date=trade_date, trigger_ts=fill_ts, direction="long",
                           pattern=pattern, fill_ts=fill_ts, entry=25000.0, stop_initial=24990.0,
                           target_level=25020.0, exit_ts=fill_ts, exit_price=25010.0,
                           exit_reason="target", points=10.0, dollars=dollars, r_multiple=1.0,
                           size=1.0)


def test_emits_each_trade_once_as_it_completes():
    # stub simulate: trade for 02-10 appears once its fill bar is in the buffer
    def sim(df, trigs, cfg, day_gate=None):
        out = []
        if any(b == "2026-02-10 09:00" for b in df["ts_event"].astype(str).str[:16]):
            out.append(_rec("2026-02-10", "2026-02-10T09:00"))
        return out, [], None

    seen = []
    v = Vault(cfg=None, triggers=[_trig("2026-02-10T08:31:00-05:00")], sim_fn=sim)
    v.add_sink(seen.append)
    v.on_bar(_bar("2026-02-10 08:31"))          # trigger present, trade not yet
    assert seen == []
    got1 = v.on_bar(_bar("2026-02-10 09:00"))   # fill bar arrives → emit once
    got2 = v.on_bar(_bar("2026-02-10 09:01"))   # still present → NOT re-emitted
    assert len(got1) == 1 and got2 == []
    assert len(seen) == 1 and isinstance(seen[0], TradeEvent)
    assert seen[0].trade_date == "2026-02-10" and seen[0].dollars == 100.0


def test_no_trigger_yet_means_no_simulation():
    calls = {"n": 0}
    def sim(df, trigs, cfg, day_gate=None):
        calls["n"] += 1
        return [], [], None
    v = Vault(cfg=None, triggers=[_trig("2026-02-10T09:30:00-05:00")], sim_fn=sim)
    v.on_bar(_bar("2026-02-10 08:00"))          # before the trigger's ts → skip sim entirely
    assert calls["n"] == 0


def test_causal_trigger_filter_hides_future_triggers():
    captured = {}
    def sim(df, trigs, cfg, day_gate=None):
        captured["n"] = len(trigs)
        return [], [], None
    v = Vault(cfg=None, triggers=[_trig("2026-02-10T08:30:00-05:00"),
                                  _trig("2026-02-10T09:30:00-05:00")], sim_fn=sim)
    v.on_bar(_bar("2026-02-10 08:45"))          # only the 08:30 trigger is causal
    assert captured["n"] == 1


def test_day_gate_is_passed_through():
    got = {}
    def sim(df, trigs, cfg, day_gate=None):
        got["gate"] = day_gate
        return [], [], None

    def gate(d):
        return {"stand_down": True}
    v = Vault(cfg=None, triggers=[_trig("2026-02-10T08:30:00-05:00")], day_gate=gate, sim_fn=sim)
    v.on_bar(_bar("2026-02-10 08:45"))
    assert got["gate"] is gate                  # the seam reaches simulate untouched


def test_session_trim_bounds_the_buffer():
    def sim(df, trigs, cfg, day_gate=None):
        return [], [], None
    v = Vault(cfg=None, triggers=[_trig("2026-02-10T08:30:00-05:00")], warmup_sessions=1, sim_fn=sim)
    # feed 4 distinct session days of one bar each (09:00 ET each day)
    for d in ("2026-02-10", "2026-02-11", "2026-02-12", "2026-02-13"):
        v.on_bar(_bar(f"{d} 09:00"))
    kept_days = {b.ts_event.strftime("%Y-%m-%d") for b in v._bars}
    assert len(kept_days) <= 2                   # warmup_sessions=1 → current + 1 prior at most
