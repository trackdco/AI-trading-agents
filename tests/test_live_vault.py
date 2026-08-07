"""Tests for src/live/vault.py — the streaming champion loop (Phase 4 Stage 2, hardened).

Loop logic is tested fast with a stub simulate. Real-data streaming==batch parity is the
Stage-7 harness (scripts/parity_check.py).
"""

from types import SimpleNamespace

import pandas as pd
import pytest

from src.live.ambient import vault_ambient
from src.live.feed import Bar
from src.live.spread_guard import SpreadGuard
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


def test_record_sink_gets_full_record_book_and_cfg_and_is_isolated():
    def sim(df, trigs, cfg, day_gate=None):
        return [_rec("2026-02-10", "2026-02-10T09:00")], [], None
    records, errors = [], []

    def bad_record_sink(tr, book, cfg):
        raise RuntimeError("journal disk full")
    v = Vault(cfg="static", book="E3", triggers=[_trig("2026-02-10T08:30:00-05:00")],
              sim_fn=sim, on_sink_error=lambda e, ev: errors.append(str(e)))
    v.add_record_sink(bad_record_sink)
    v.add_record_sink(lambda tr, book, cfg: records.append((tr, book, cfg)))
    out = v.on_bar(_bar("2026-02-10 09:00"))
    assert len(out) == 1 and errors == ["journal disk full"]   # loop + later sink survive
    tr, book, cfg = records[0]
    assert tr.trade_date == "2026-02-10" and book == "E3" and cfg == "static"
    v.on_bar(_bar("2026-02-10 09:01"))
    assert len(records) == 1                     # emit-once semantics shared with sinks


def test_pending_policy_retried_per_bar_then_applied():
    """Stage-8: a policy may answer PENDING until the day's overnight completes —
    the Vault must stay inactive, retry each bar, then trade the eventual pick."""
    from src.live.vault import PENDING
    asked, sims = [], {"n": 0}

    def policy(day):
        asked.append(day)
        return PENDING if len(asked) < 3 else ("E4", "warcfg", lambda t: True)

    def sim(df, trigs, cfg, day_gate=None):
        sims["n"] += 1
        return [_rec("2026-02-10", "2026-02-10T09:00")], [], None
    v = Vault(session_policy=policy, sim_fn=sim,
              triggers=[_trig("2026-02-10T08:30:00-05:00")])
    assert v.on_bar(_bar("2026-02-10 08:31")) == [] and sims["n"] == 0   # pending
    assert v.on_bar(_bar("2026-02-10 08:32")) == [] and sims["n"] == 0   # still
    out = v.on_bar(_bar("2026-02-10 09:00"))                             # decided now
    assert len(out) == 1 and out[0].book == "E4" and v.cfg == "warcfg"
    assert asked == ["2026-02-10"] * 3                # retried once per bar
    v.on_bar(_bar("2026-02-10 09:01"))
    assert asked == ["2026-02-10"] * 3                # settled: no more retries


def test_pending_policy_can_resolve_to_stand_down():
    from src.live.vault import PENDING
    calls = {"n": 0}

    def policy(day):
        calls["n"] += 1
        return PENDING if calls["n"] < 2 else None
    v = Vault(session_policy=policy, sim_fn=_noop_sim,
              triggers=[_trig("2026-02-10T08:30:00-05:00")])
    v.on_bar(_bar("2026-02-10 08:31"))
    v.on_bar(_bar("2026-02-10 08:32"))                # resolves to sit-out
    assert not v._sess_active and not v._sess_pending
    v.on_bar(_bar("2026-02-10 08:33"))
    assert calls["n"] == 2                            # no retry after resolution


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


# ---- CANON ruling: ambient instrumentation + order-time spread guard ---------

def _wide_bar(ts, c=25000.0, half=10.0):
    t = pd.Timestamp(ts, tz=NY)
    return Bar(ts_event=t, open=c, high=c + half, low=c - half, close=c, volume=100.0)


def _sim_fill_at_0900(df, trigs, cfg, day_gate=None, target_resolver=None):
    if any(b == "2026-02-10 09:00" for b in df["ts_event"].astype(str).str[:16]):
        return [_rec("2026-02-10", "2026-02-10T09:00")], [], None
    return [], [], None


def _feed_tight_session(v, n=6):
    """A trigger plus n tight (2pt) pre-fill bars, so the guard has a real baseline."""
    for i in range(n):
        v.on_bar(_bar(f"2026-02-10 08:{50 + i:02d}"))   # spread 2.0 each


def test_spread_guard_trip_blocks_order_and_journals_reason():
    trips, records, emitted = [], [], []
    v = Vault(cfg="static", triggers=[_trig("2026-02-10T08:30:00-05:00")],
              sim_fn=_sim_fill_at_0900, ambient_fn=vault_ambient,
              spread_guard=SpreadGuard(mult=3.0, window=30, min_obs=5),
              on_guard_trip=lambda tr, book, cfg, amb, res: trips.append((tr, amb, res)))
    v.add_sink(emitted.append)
    v.add_record_sink(lambda tr, book, cfg, amb: records.append((tr, amb)))
    _feed_tight_session(v)                              # baseline = 2pt spreads
    out = v.on_bar(_wide_bar("2026-02-10 09:00"))       # fill bar spread = 20pt -> TRIP

    assert out == [] and emitted == [] and records == []   # no order placed anywhere
    assert len(trips) == 1                                  # journaled once
    _, amb, res = trips[0]
    assert not res.ok and res.observed == 20.0 and res.baseline == 2.0
    assert amb["spread_at_fill"] == 20.0                    # ambient still computed for audit
    # decided once: a re-cover of the same bar does not re-trip
    v.on_bar(_wide_bar("2026-02-10 09:01"))
    assert len(trips) == 1


def test_spread_guard_passes_normal_spread_and_passes_ambient_to_record_sink():
    records, emitted = [], []
    v = Vault(cfg="static", triggers=[_trig("2026-02-10T08:30:00-05:00")],
              sim_fn=_sim_fill_at_0900, ambient_fn=vault_ambient,
              spread_guard=SpreadGuard(mult=3.0, window=30, min_obs=5))
    v.add_sink(emitted.append)
    v.add_record_sink(lambda tr, book, cfg, amb: records.append((tr, amb)))
    _feed_tight_session(v)
    out = v.on_bar(_bar("2026-02-10 09:00"))            # fill bar spread = 2pt -> PASS
    assert len(out) == 1 and len(emitted) == 1 and len(records) == 1
    _, amb = records[0]
    assert amb["spread_at_fill"] == 2.0                 # ambient reached the journal sink


def test_ambient_without_guard_still_journals_context():
    records = []
    v = Vault(cfg="static", triggers=[_trig("2026-02-10T08:30:00-05:00")],
              sim_fn=_sim_fill_at_0900, ambient_fn=vault_ambient)  # no guard
    v.add_record_sink(lambda tr, book, cfg, amb: records.append(amb))
    v.on_bar(_bar("2026-02-10 09:00"))
    assert len(records) == 1 and "sweep_state" in records[0]


def test_session_trim_bounds_the_buffer():
    v = Vault(cfg="static", triggers=[_trig("2026-02-10T08:30:00-05:00")],
              warmup_sessions=1, sim_fn=_noop_sim)
    for d in ("2026-02-10", "2026-02-11", "2026-02-12", "2026-02-13"):
        v.on_bar(_bar(f"{d} 09:00"))
    kept_days = {b.ts_event.strftime("%Y-%m-%d") for b in v._bars}
    assert len(kept_days) <= 2                   # warmup_sessions=1 -> current + 1 prior
