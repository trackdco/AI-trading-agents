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
    micros_for,
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
# REBUILT CANON schedule. These assertions and src/canon/scorer_ny.py must agree by
# construction — gate_evidence imports the profile rather than restating it — and the scorer
# is in turn conformance-tested against scripts/funded_book.py on both spans.
def test_base_dollar_is_the_lucid_base_by_default():
    assert base_dollar(None) == 150.0 and base_dollar(3000) == 150.0
    assert base_dollar(50_000) == 150.0, "lucid never scales with buffer"


def test_base_dollar_scaled_profile_steps_and_caps():
    assert base_dollar(3000, "scaled600") == 150.0
    assert base_dollar(4999, "scaled600") == 150.0    # first step lands at +$5k
    assert base_dollar(5000, "scaled600") == 225.0    # +$75 per $2k past $3k
    assert base_dollar(7000, "scaled600") == 300.0
    assert base_dollar(99_000, "scaled600") == 600.0  # hard cap


def test_expected_micros_ladder():
    # lucid ladder: 0.5=$75, 1.0=$150, 1.5=$225, 2.0=$300; micros = risk$/(stop x $2)
    assert expected_micros(0.5, 10.0) == 4        # 75 / 20 = 3.75 -> 4
    assert expected_micros(1.0, 10.0) == 8        # 150 / 20 = 7.5 -> 8
    assert expected_micros(1.5, 10.0) == 11       # 225 / 20 = 11.25 -> 11
    assert expected_micros(2.0, 10.0) == 15       # 300 / 20 = 15 (the elite tier)
    assert expected_micros(1.0, 1.0) == 40        # 150/2 = 75 -> clamped to 40


def test_micros_never_round_to_zero():
    """The canon takes a trade at >=1 micro or does not take it. A 0-micro 'trade' is a
    phantom fill in the journal and a divergence from the measured book."""
    assert micros_for(75.0, 60.0) == 1            # 75/120 = 0.625 -> 1, not 0
    assert expected_micros(0.5, 60.0) == 1


def test_dd_ramp_halves_the_base_below_1k_buffer():
    """ANGUS: half size below $1,000 of buffer. Dormant across all 19 months of history —
    pure insurance for a worse-than-history future, so it must actually be wired."""
    assert base_dollar(1000) == 150.0
    assert base_dollar(999) == 75.0
    assert expected_micros(1.0, 10.0, available_dd=999) == 4     # 75/20 = 3.75 -> 4


def test_check_sizing_pass_and_fail():
    ok = check_sizing(1.0, 10.0, actual_micros=8)
    assert ok["ok"] and ok["expected"] == 8 and ok["delta"] == 0
    bad = check_sizing(1.0, 10.0, actual_micros=15)
    assert not bad["ok"] and bad["expected"] == 8 and bad["delta"] == 7


def test_check_sizing_prefers_the_verdicts_own_risk_dollars():
    """The schedule cannot see the day's soft de-risk; the verdict's risk_dollars can. When
    supplied it is authoritative, so a correctly halved trade is not flagged as mis-sized."""
    halved = check_sizing(1.0, 10.0, actual_micros=4, risk_dollars=75.0)
    assert halved["ok"] and halved["expected"] == 4
    assert not check_sizing(1.0, 10.0, actual_micros=8, risk_dollars=75.0)["ok"]


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
