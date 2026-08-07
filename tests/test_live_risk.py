"""Tests for src/live/risk.py — the Vault's safety rails (Phase 4 Stage 4)."""

from types import SimpleNamespace

import pandas as pd

from src.live.feed import Bar
from src.live.risk import RiskGuard, RiskLimits
from src.live.vault import TradeEvent, Vault

NY = "America/New_York"


def _ev(date="2026-02-10", fill="2026-02-10T09:35:00-05:00", dollars=100.0):
    return TradeEvent(trade_date=date, trigger_ts=fill, direction="long", pattern="A",
                      fill_ts=fill, entry=25000.0, stop_initial=24990.0, target_level=None,
                      exit_ts=fill, exit_price=25010.0, exit_reason="target", points=5.0,
                      dollars=dollars, r_multiple=1.0, size=1.0, book="E3")


def _limits(tmp_path, **kw):
    kw.setdefault("kill_file", tmp_path / "KILL")
    return RiskLimits(**kw)


def test_no_restriction_by_default(tmp_path):
    g = RiskGuard(_limits(tmp_path))
    assert g.gate("2026-02-10") is None


def test_kill_switch_blocks_everything_until_reset(tmp_path):
    g = RiskGuard(_limits(tmp_path))
    g.trip()
    for d in ("2026-02-10", "2026-02-11"):
        out = g.gate(d)
        assert out["stand_down"] and out["risk_reason"] == "kill_switch"
    g.reset()
    assert g.gate("2026-02-10") is None


def test_daily_loss_limit_trips_that_day_only(tmp_path):
    g = RiskGuard(_limits(tmp_path, daily_loss_dollars=500.0, max_trades_per_day=99))
    g.on_trade(_ev(dollars=-200.0))
    assert g.gate("2026-02-10") is None                      # -200 > -500: fine
    g.on_trade(_ev(fill="2026-02-10T10:00:00-05:00", dollars=-350.0))
    out = g.gate("2026-02-10")                               # -550 <= -500: halt today
    assert out["stand_down"] and out["risk_reason"] == "daily_loss_limit"
    assert g.gate("2026-02-11") is None                      # tomorrow unaffected


def test_max_trades_backstop(tmp_path):
    g = RiskGuard(_limits(tmp_path, max_trades_per_day=2, daily_loss_dollars=1e9))
    g.on_trade(_ev(dollars=50.0))
    assert g.gate("2026-02-10") is None
    g.on_trade(_ev(fill="2026-02-10T10:00:00-05:00", dollars=50.0))
    assert g.gate("2026-02-10")["risk_reason"] == "max_trades"


def test_equity_floor_is_permanent_until_human_reset(tmp_path):
    g = RiskGuard(_limits(tmp_path, equity_floor_dollars=-1000.0,
                          daily_loss_dollars=1e9, max_trades_per_day=99))
    g.on_trade(_ev(dollars=-600.0))
    g.on_trade(_ev(date="2026-02-11", fill="2026-02-11T09:35:00-05:00", dollars=-500.0))
    for d in ("2026-02-11", "2026-02-12", "2026-03-01"):     # every session, forever
        assert g.gate(d)["risk_reason"] == "equity_floor"
    g.reset_floor()
    assert g.gate("2026-03-01") is None


def test_on_halt_fires_once_per_date_reason(tmp_path):
    halts = []
    g = RiskGuard(_limits(tmp_path, daily_loss_dollars=100.0, max_trades_per_day=99),
                  on_halt=lambda d, r: halts.append((d, r)))
    g.on_trade(_ev(dollars=-150.0))                          # trips + announces
    g.gate("2026-02-10")
    g.gate("2026-02-10")                                     # repeated checks: no re-announce
    assert halts == [("2026-02-10", "daily_loss_limit")]


def test_wrap_composes_with_strategy_gate(tmp_path):
    g = RiskGuard(_limits(tmp_path))
    inner = {"2026-02-10": {"stand_down": False, "size_multiplier": 0.5}}
    gate = g.wrap(lambda d: inner.get(d))
    assert gate("2026-02-10") == inner["2026-02-10"]         # guard clear -> inner rules
    assert gate("2026-02-11") is None
    g.trip()
    assert gate("2026-02-10")["risk_reason"] == "kill_switch"  # guard overrides inner


def test_status_snapshot(tmp_path):
    g = RiskGuard(_limits(tmp_path))
    g.on_trade(_ev(dollars=250.0))
    s = g.status()
    assert s["killed"] is False and s["cum_dollars"] == 250.0
    assert s["days"]["2026-02-10"] == {"dollars": 250.0, "trades": 1}


def test_vault_integration_guard_gate_reaches_engine_and_sink_updates(tmp_path):
    # the guard rides the Vault's day_gate seam and its sink accounting feeds back in
    seen_gates = []

    def sim(df, trigs, cfg, day_gate=None):
        seen_gates.append(day_gate("2026-02-10") if day_gate else None)
        return [SimpleNamespace(trade_date="2026-02-10", trigger_ts="t",
                                direction="long", pattern="A",
                                fill_ts=f"2026-02-10T09:{30 + len(seen_gates)}:00-05:00",
                                entry=1.0, stop_initial=0.0, target_level=None,
                                exit_ts="x", exit_price=1.0, exit_reason="target",
                                points=-30.0, dollars=-600.0, r_multiple=-1.0,
                                size=1.0)], [], None

    guard = RiskGuard(_limits(tmp_path, daily_loss_dollars=500.0, max_trades_per_day=99))
    trig = SimpleNamespace(ts="2026-02-10T08:30:00-05:00", tf="1m", direction="long",
                           pattern="A", close=25000.0, stop_ref=24990.0)
    v = Vault(cfg="static", triggers=[trig], day_gate=guard.wrap(None), sim_fn=sim)
    v.add_sink(guard.on_trade)

    b1 = Bar(ts_event=pd.Timestamp("2026-02-10 09:31", tz=NY), open=1, high=2, low=0,
             close=1, volume=1)
    b2 = Bar(ts_event=pd.Timestamp("2026-02-10 09:32", tz=NY), open=1, high=2, low=0,
             close=1, volume=1)
    v.on_bar(b1)                                  # -$600 trade books -> guard trips
    v.on_bar(b2)
    assert seen_gates[0] is None                              # first sim: unrestricted
    assert seen_gates[1] is not None and seen_gates[1]["stand_down"]   # second sim: halted


def test_default_limits_are_silent_on_a_normal_two_trade_day(tmp_path):
    # engine cap is 2/day; the guard backstop must sit ABOVE it or every normal day
    # announces a false halt (alert noise). Two winning trades at defaults -> no halt.
    halts = []
    g = RiskGuard(_limits(tmp_path), on_halt=lambda d, r: halts.append((d, r)))
    g.on_trade(_ev(dollars=200.0))
    g.on_trade(_ev(fill="2026-02-10T10:00:00-05:00", dollars=150.0))
    assert g.gate("2026-02-10") is None and halts == []


def test_seed_restores_halt_state_without_reannouncing(tmp_path):
    halts = []
    g = RiskGuard(_limits(tmp_path, daily_loss_dollars=500.0, max_trades_per_day=99),
                  on_halt=lambda d, r: halts.append((d, r)))
    g.seed([_ev(dollars=-600.0)])                 # restart recovery from the ledger
    out = g.gate("2026-02-10")
    assert out is not None and out["risk_reason"] == "daily_loss_limit"
    assert halts == []                            # silent: the halt already fired pre-crash


def test_crash_restart_broker_plus_seed_keeps_the_day_halted(tmp_path):
    # end-to-end restart drill: trade books -> crash -> restore broker -> seed guard
    from src.live.paper_broker import PaperBroker
    led = tmp_path / "ledger.csv"
    broker = PaperBroker(ledger_path=led)
    guard = RiskGuard(_limits(tmp_path, daily_loss_dollars=500.0, max_trades_per_day=99))
    t = _ev(dollars=-600.0)
    guard.on_trade(t)
    broker.on_trade(t)
    assert guard.gate("2026-02-10") is not None   # halted pre-crash

    broker2 = PaperBroker.restore(led)            # --- restart ---
    guard2 = RiskGuard(_limits(tmp_path, daily_loss_dollars=500.0, max_trades_per_day=99))
    guard2.seed(broker2.trades)
    out = guard2.gate("2026-02-10")
    assert out is not None and out["risk_reason"] == "daily_loss_limit"


# ---- Stage-6 review regressions ---------------------------------------------

def test_raising_on_halt_hook_cannot_break_gate(tmp_path):
    """Review F4: gate() runs inside the engine's day_gate path — a broken alert hook
    must not kill the trading loop, and the stand-down must still be returned."""
    def bad_hook(date, reason):
        raise RuntimeError("alert pipeline down")
    g = RiskGuard(_limits(tmp_path, daily_loss_dollars=50.0, max_trades_per_day=99),
                  on_halt=bad_hook)
    g.on_trade(_ev(dollars=-100.0))
    out = g.gate("2026-02-10")                     # must not raise
    assert out is not None and out["risk_reason"] == "daily_loss_limit"


def test_fanout_calls_all_hooks_and_isolates_failures(tmp_path):
    from src.live.risk import fanout
    calls = []

    def bad(date, reason):
        raise RuntimeError("boom")
    hook = fanout(bad, lambda d, r: calls.append((d, r)))
    hook("2026-02-10", "kill_switch")              # must not raise
    assert calls == [("2026-02-10", "kill_switch")]
