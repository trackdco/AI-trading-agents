"""Tests for src/live/runner.py — the assembled paper bot (Phase 4 Stage 8).

Plumbing is tested fast with a stub sim + stub detector + injected session policy.
Real-data full-stack equivalence to the backtest is the drill (scripts/runner_drill.py).
"""

from types import SimpleNamespace

import pandas as pd

from src.backtest.engine import TradeRecord
from src.live.feed import Bar
from src.live.risk import RiskLimits
from src.live.runner import LiveRunner

NY = "America/New_York"


class _Cfg:
    win_end = None
    eod_flatten = None

    def model_dump_json(self):
        return '{"book":"E3"}'


class _Alerts:
    def __init__(self):
        self.trades, self.halts, self.summaries, self.said = 0, 0, [], []

    def on_trade(self, ev):
        self.trades += 1

    def on_halt(self, date, reason):
        self.halts += 1

    def daily_summary(self, broker, date):
        self.summaries.append(date)

    def say(self, text):
        self.said.append(text)


def _bar(ts, c=25000.0):
    t = pd.Timestamp(ts, tz=NY)
    return Bar(ts_event=t, open=c, high=c + 1, low=c - 1, close=c, volume=100.0)


def _rec(trade_date, fill_ts, dollars=200.0):
    return TradeRecord(
        trade_date=trade_date, trigger_ts=fill_ts, tf="2min", direction="long",
        kind="rejection_block", pattern="A", htf_flag="with_trend", confluence=2,
        entry_variant="E3", limit_price=25000.0, fill_ts=fill_ts, entry=25000.0,
        stop_initial=24990.0, target_name="pdh", target_level=25020.0,
        working_target=25019.0, exit_ts=fill_ts, exit_price=25010.0,
        exit_reason="target", points=10.0, r_multiple=1.0, size=1.0, dollars=dollars,
        slippage_ticks=0, mgmt_variant="V0")


class _StubDetector:
    """Emits one trigger the first in-band bar of each session (like real detection
    surfacing a setup), so the Vault has a causal trigger to run its sim against."""
    def __init__(self):
        self._seen = set()

    def wants(self, ts):
        return True

    def on_bar(self, df, bar):
        ts = pd.Timestamp(bar.ts_event)
        day = ts.strftime("%Y-%m-%d")
        if day in self._seen:
            return []
        self._seen.add(day)
        return [SimpleNamespace(ts=ts.isoformat(), tf="1m", direction="long",
                                pattern="A", close=25000.0, stop_ref=24990.0)]


def _policy(day):
    return ("E3", _Cfg(), lambda t: True)


def _fill_on(fill):
    """A stub sim that emits one trade once its fill bar is in the buffer."""
    want = fill.replace("T", " ")[:16]
    def sim(df, trigs, cfg, day_gate=None, target_resolver=None):
        stamps = df["ts_event"].astype(str).str.replace("T", " ").str[:16]
        if any(s == want for s in stamps):
            # honor a risk stand-down so guard composition is exercised
            if day_gate is not None and day_gate(fill[:10]) is not None:
                return [], [], None
            return [_rec(fill[:10], fill)], [], None
        return [], [], None
    return sim


def _runner(tmp, alerts=None, fill="2026-02-10T09:00", **kw):
    return LiveRunner(ledger_path=tmp / "ledger.csv", journal_dir=tmp / "j",
                      starting_equity=25_000.0, alerts=alerts,
                      detector=_StubDetector(), session_policy=_policy,
                      sim_fn=_fill_on(fill), **kw)


def test_trade_flows_to_broker_journal_and_alerts(tmp_path):
    alerts = _Alerts()
    r = _runner(tmp_path, alerts)
    r.on_bar(_bar("2026-02-10 08:31"))
    out = r.on_bar(_bar("2026-02-10 09:00"))
    assert len(out) == 1
    assert r.broker.total_dollars() == 200.0 and r.broker.equity() == 25_200.0
    assert len(r.journal.trades()) == 1 and r.journal.trades()[0].playbook == "E3"
    assert alerts.trades == 1
    # ledger persisted for restart
    assert (tmp_path / "ledger.csv").exists()


def test_session_roll_emits_daily_summary(tmp_path):
    alerts = _Alerts()
    r = _runner(tmp_path, alerts)
    r.on_bar(_bar("2026-02-10 09:00"))            # books a trade on the 10th
    r.on_bar(_bar("2026-02-11 08:30"))            # roll into the 11th -> summarize 10th
    assert alerts.summaries == ["2026-02-10"]
    r.finalize()                                  # flush the last session
    assert alerts.summaries == ["2026-02-10", "2026-02-11"]


def test_restart_restores_account_and_fires_no_duplicate_alerts(tmp_path):
    a1 = _Alerts()
    r1 = _runner(tmp_path, a1)
    r1.on_bar(_bar("2026-02-10 09:00"))
    assert a1.trades == 1 and r1.broker.total_dollars() == 200.0

    a2 = _Alerts()                                # --- restart: same ledger/journal ---
    r2 = _runner(tmp_path, a2)
    assert r2.broker.total_dollars() == 200.0     # account restored
    assert r2.broker.equity() == 25_200.0
    r2.on_bar(_bar("2026-02-10 09:00"))           # re-cover the SAME bar
    assert a2.trades == 0                         # no duplicate alert
    assert r2.broker.total_dollars() == 200.0     # no double-book
    assert len(r2.journal.trades()) == 1


def test_kill_switch_gate_blocks_new_trades(tmp_path):
    alerts = _Alerts()
    r = _runner(tmp_path, alerts, limits=RiskLimits(kill_file=tmp_path / "KILL"))
    r.guard.trip()                                # arm the kill switch
    r.on_bar(_bar("2026-02-10 08:31"))
    out = r.on_bar(_bar("2026-02-10 09:00"))      # sim honors the stand-down
    assert out == [] and alerts.trades == 0
    assert r.broker.total_dollars() == 0.0


def test_strategy_gate_composes_under_the_risk_guard(tmp_path):
    seen = {}

    def strat(date):
        seen[date] = True
        return None                               # permissive strategy
    r = _runner(tmp_path, strategy_gate=strat)
    r.on_bar(_bar("2026-02-10 08:31"))
    r.on_bar(_bar("2026-02-10 09:00"))
    assert seen.get("2026-02-10")                 # the seam was consulted
    assert r.broker.total_dollars() == 200.0      # permissive -> trade allowed


def test_history_is_bounded(tmp_path):
    r = _runner(tmp_path, history_days=2)
    for day in ("2026-02-02", "2026-02-05", "2026-02-06", "2026-02-09"):
        r.on_bar(_bar(f"{day} 09:00"))
    span = r._frame()["ts_event"]
    assert (span.max() - span.min()) <= pd.Timedelta(days=2)


def test_prime_loads_warmup_without_trading_or_summarizing(tmp_path):
    alerts = _Alerts()
    r = _runner(tmp_path, alerts)
    warm = pd.DataFrame([{"ts_event": pd.Timestamp(f"2026-02-09 {h:02d}:00", tz=NY),
                          "open": 25000.0, "high": 25001.0, "low": 24999.0,
                          "close": 25000.0, "volume": 100.0} for h in range(9, 16)])
    r.prime(warm)
    assert len(r._frame()) == 7 and alerts.trades == 0 and alerts.summaries == []
    assert r.broker.total_dollars() == 0.0            # primed bars are not traded
    # first live bar in a new session must NOT emit a summary for the primed day
    r.on_bar(_bar("2026-02-10 08:31"))
    assert alerts.summaries == []
