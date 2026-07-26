"""Promotion-gate evidence primitives (src/canon/gate_evidence.py) + the two spine-side
evidence additions (SpineExecutor.guard_report, SpineExecutor.reconcile).

These close the four journal gaps the gate audit found: rejection reason codes (one ledger),
per-trade micros-vs-schedule, per-guard fired/not-fired, and naked-position detection."""
from __future__ import annotations

import pytest

from src.canon.gate_evidence import (
    RejectLedger,
    base_dollar,
    check_sizing,
    expected_micros,
    normalize_dtc_reject,
    normalize_spine_reject,
)
from src.canon.spine import (
    AccountState,
    FeedHealth,
    OrderIntent,
    SpineConfig,
    SpineExecutor,
)

ARM = "ANGUS-SIGNOFF"
GOOD_ACCT = AccountState(equity=52_000, trailing_floor=50_000, day_pnl=-100, open_positions=0)
GOOD_FEED = FeedHealth(last_tick_age_ms=100, crossed_or_locked=False,
                       context_complete=True, spread_rel=1.0)


def intent(**kw) -> OrderIntent:
    base = {"side": "B", "order_type": "limit", "entry_ref": 100.0, "stop": 99.0,
            "target": 103.0, "size": 1, "setup_id": "s1", "account": "ACC"}
    base.update(kw)
    return OrderIntent(**base)


class MockBroker:
    def __init__(self, position=0):
        self.submitted, self.flattened, self.cancelled = [], [], []
        self._position = position
        self.stop_resting = True

    def submit_bracket(self, i):
        self.submitted.append(i)
        return f"ref-{len(self.submitted)}"

    def order_status(self, ref):
        i = self.submitted[-1]
        return {"side": i.side, "size": i.size, "account": i.account, "entry": i.entry_ref,
                "stop": i.stop, "target": i.target, "stop_resting": self.stop_resting}

    def position(self, account):
        return self._position

    def flatten(self, account):
        self.flattened.append(account)

    def cancel_all(self, account):
        self.cancelled.append(account)


# --------------------------------------------------------------------------- sizing (gap c)
def test_base_dollar_floor_and_scaling():
    assert base_dollar(None) == 200.0 and base_dollar(3000) == 200.0
    assert base_dollar(5000) == 350.0            # +$75 per $1k past $3k: 200 + 75*2
    assert base_dollar(6000) == 425.0


def test_expected_micros_floor_schedule():
    # SAFETY-SPINE anchor: 1.0=$200, 1.5=$300, 2.25=$400 at the floor; /(stop*2), clamp 40
    assert expected_micros(1.0, 10.0) == 10       # 200 / (10*2)
    assert expected_micros(1.5, 10.0) == 15       # 300 / 20
    assert expected_micros(2.25, 10.0) == 20      # 400 / 20  (2.25 caps at 2x base)
    assert expected_micros(1.0, 2.0) == 40        # 200/(2*2)=50 -> clamped to 40


def test_expected_micros_dd_scaled():
    assert expected_micros(1.0, 10.0, available_dd=5000) == 18   # 350/20 = 17.5 -> 18


def test_check_sizing_pass_and_fail():
    ok = check_sizing(1.0, 10.0, actual_micros=10)
    assert ok["ok"] and ok["expected"] == 10 and ok["delta"] == 0
    bad = check_sizing(1.0, 10.0, actual_micros=15)
    assert not bad["ok"] and bad["expected"] == 10 and bad["delta"] == 5


def test_expected_micros_rejects_bad_stop():
    with pytest.raises(ValueError):
        expected_micros(1.0, 0.0)


# --------------------------------------------------------------------------- reject ledger (gap a)
def test_reject_ledger_unifies_sources(tmp_path):
    led = RejectLedger(path=tmp_path / "rejects.jsonl")
    led.record(normalize_spine_reject({"event": "decision", "action": "reject",
                                       "rule": "feed_stale", "detail": "tick age 9000ms",
                                       "setup": "s1"}), ts="2026-09-01T08:00:00")
    led.record(normalize_dtc_reject({"Type": 103, "RejectText": "Market data not allowed",
                                     "Symbol": "NQU26"}), ts="2026-09-01T08:00:01")
    led.record(normalize_dtc_reject({"Type": 301, "InfoText": "insufficient margin",
                                     "OrderStatus": 8}), ts="2026-09-01T08:00:02")
    rows = led.rows()
    assert len(rows) == 3
    assert led.code_counts() == {"feed_stale": 1, "market_data_reject": 1, "order_rejected": 1}
    assert rows[1]["source"] == "dtc" and rows[1]["reason"] == "Market data not allowed"


# --------------------------------------------------------------------------- guard_report (gap d)
def test_guard_report_all_pass():
    e = SpineExecutor(SpineConfig(), MockBroker(), kill_file_present=lambda: False)
    rep = e.guard_report(intent(), GOOD_ACCT, GOOD_FEED, now=0.0)
    assert rep["decision"] == "ok" and rep["n_fired"] == 0
    assert {g["rule"] for g in rep["guards"]} >= {"feed_stale", "spread", "dd_proximity"}
    assert all(g["fired"] is False for g in rep["guards"])


def test_guard_report_records_every_fired_not_just_first():
    # stale feed AND crossed book AND daily-loss breach: check() would stop at the first,
    # guard_report must show all three fired while the rest passed.
    # -2.5R at the eval-floor base_dollar ($200) = a -$500 halt threshold
    e = SpineExecutor(SpineConfig(daily_loss_halt_r=-2.5), MockBroker(),
                      kill_file_present=lambda: False)
    acct = AccountState(equity=52_000, trailing_floor=50_000, day_pnl=-900, open_positions=0)
    feed = FeedHealth(last_tick_age_ms=9000, crossed_or_locked=True,
                      context_complete=True, spread_rel=1.0)
    rep = e.guard_report(intent(), acct, feed, now=0.0)
    fired = {g["rule"] for g in rep["guards"] if g["fired"]}
    assert {"feed_stale", "book_crossed", "daily_loss"} <= fired
    assert rep["n_fired"] >= 3
    assert rep["decision"] in fired               # terminal decision is one of the fired rules


def test_guard_report_is_read_only():
    e = SpineExecutor(SpineConfig(), MockBroker(), kill_file_present=lambda: False)
    e.guard_report(intent(setup_id="dup"), GOOD_ACCT, GOOD_FEED, now=0.0)
    # no duplicate/rate state was mutated: a subsequent duplicate guard still shows not-fired
    rep = e.guard_report(intent(setup_id="dup"), GOOD_ACCT, GOOD_FEED, now=0.0)
    assert next(g for g in rep["guards"] if g["rule"] == "duplicate")["fired"] is False


# --------------------------------------------------------------------------- reconcile (gap b)
def _armed(broker):
    e = SpineExecutor(SpineConfig(), broker, kill_file_present=lambda: False)
    e.arm(ARM)
    e.place(intent(), GOOD_ACCT, GOOD_FEED, now=0.0)      # tracks the resting ref
    return e


def test_reconcile_flat_is_noop():
    b = MockBroker(position=0)
    e = _armed(b)
    assert e.reconcile("ACC", now=1.0) is None
    assert b.flattened == []


def test_reconcile_healthy_open_position_ok():
    b = MockBroker(position=1)
    e = _armed(b)
    b.stop_resting = True
    assert e.reconcile("ACC", now=1.0) is None
    assert b.flattened == []


def test_reconcile_naked_when_legs_not_resting_flattens_and_halts():
    b = MockBroker(position=1)
    e = _armed(b)
    b.stop_resting = False                                # bracket silently dropped
    d = e.reconcile("ACC", now=1.0)
    assert d is not None and d.action == "flatten" and d.rule == "naked_position"
    assert b.flattened == ["ACC"] and b.cancelled == ["ACC"]


def test_reconcile_naked_when_no_bracket_tracked():
    # position appeared with nothing placed by us (no tracked ref) -> naked, halt.
    b = MockBroker(position=-1)
    e = SpineExecutor(SpineConfig(), b, kill_file_present=lambda: False)
    d = e.reconcile("ACC", now=1.0)
    assert d is not None and d.rule == "naked_position" and b.flattened == ["ACC"]
