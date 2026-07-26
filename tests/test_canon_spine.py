"""Safety-spine executor tests (docs/SAFETY-SPINE.md, decision 1). A MockBroker stands in
for DTC — no network, no real orders. Covers every deterministic rule, the yes-only +
arming gate, and broker read-back verification.
"""
from __future__ import annotations

import math

import pytest

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
    def __init__(self, status_override=None, position=0):
        self.submitted, self.flattened, self.cancelled = [], [], []
        self._override, self._position = status_override, position

    def submit_bracket(self, i):
        self.submitted.append(i)
        return f"ref-{len(self.submitted)}"

    def order_status(self, ref):
        if self._override is not None:
            return self._override
        i = self.submitted[-1]
        return {"side": i.side, "size": i.size, "account": i.account, "entry": i.entry_ref,
                "stop": i.stop, "target": i.target, "stop_resting": True}

    def position(self, account):
        return self._position

    def flatten(self, account):
        self.flattened.append(account)

    def cancel_all(self, account):
        self.cancelled.append(account)


def _exe(broker=None, kill=False, **cfg):
    return SpineExecutor(SpineConfig(**cfg), broker or MockBroker(),
                         kill_file_present=lambda: kill)


# ---- arming / yes-only ------------------------------------------------------
def test_disarmed_by_default_is_shadow_no_broker_call():
    b = MockBroker()
    e = _exe(b)
    d = e.place(intent(), GOOD_ACCT, GOOD_FEED, now=0.0)
    assert d.action == "place" and d.rule == "shadow"
    assert b.submitted == []                      # disarmed: nothing sent


def test_arm_requires_exact_token():
    e = _exe()
    assert e.arm("nope") is False and e.armed is False
    assert e.arm(ARM) is True and e.armed is True


def test_market_order_rejected():
    d = _exe().check(intent(order_type="market"), GOOD_ACCT, GOOD_FEED, 0.0)
    assert d.action == "reject" and d.rule == "limit_only"


# ---- Tier 1 -----------------------------------------------------------------
def test_dd_proximity_halt():
    acct = AccountState(equity=50_200, trailing_floor=50_000, day_pnl=0, open_positions=0)
    d = _exe().check(intent(), acct, GOOD_FEED, 0.0)              # 200 <= 250 buffer
    assert d.action == "halt" and d.rule == "dd_proximity"


def test_daily_loss_halt():
    acct = AccountState(equity=52_000, trailing_floor=50_000, day_pnl=-800, open_positions=0)
    d = _exe().check(intent(), acct, GOOD_FEED, 0.0)
    assert d.action == "halt" and d.rule == "daily_loss"


def test_contract_clamp_shrinks_not_rejects():
    b = MockBroker()
    e = _exe(b, max_contracts=2)
    e.arm(ARM)
    d = e.place(intent(size=5), GOOD_ACCT, GOOD_FEED, 0.0)
    assert d.action == "place" and d.clamped_size == 2
    assert b.submitted[-1].size == 2                              # broker got the clamped size


# ---- Tier 2 -----------------------------------------------------------------
def test_feed_and_spread_guards():
    e = _exe()
    stale = FeedHealth(4000, False, True, 1.0)
    assert e.check(intent(), GOOD_ACCT, stale, 0.0).rule == "feed_stale"
    crossed = FeedHealth(100, True, True, 1.0)
    assert e.check(intent(), GOOD_ACCT, crossed, 0.0).rule == "book_crossed"
    noctx = FeedHealth(100, False, False, 1.0)
    assert e.check(intent(), GOOD_ACCT, noctx, 0.0).rule == "context_incomplete"
    wide = FeedHealth(100, False, True, 9.0)
    assert e.check(intent(), GOOD_ACCT, wide, 0.0).rule == "spread"


def test_duplicate_and_order_rate():
    b = MockBroker()
    e = _exe(b, max_orders_per_min=2)
    e.arm(ARM)
    assert e.place(intent(setup_id="a"), GOOD_ACCT, GOOD_FEED, 0.0).action == "place"
    # same setup again -> duplicate
    assert e.place(intent(setup_id="a"), GOOD_ACCT, GOOD_FEED, 0.0).rule == "duplicate"
    assert e.place(intent(setup_id="b"), GOOD_ACCT, GOOD_FEED, 0.0).action == "place"
    # third distinct within 60s -> rate cap (2 already sent)
    assert e.place(intent(setup_id="c"), GOOD_ACCT, GOOD_FEED, 1.0).rule == "order_rate"


# ---- Tier 3 / kill / parity -------------------------------------------------
def test_fail_closed_on_nan():
    d = _exe().check(intent(stop=math.nan), GOOD_ACCT, GOOD_FEED, 0.0)
    assert d.action == "halt" and d.rule == "fail_closed"


def test_manual_kill_and_parity_gate():
    assert _exe(kill=True).check(intent(), GOOD_ACCT, GOOD_FEED, 0.0).rule == "manual_kill"
    assert _exe().check(intent(), GOOD_ACCT, GOOD_FEED, 0.0, parity_ok=False).rule == "startup_parity"


# ---- read-back --------------------------------------------------------------
def test_armed_place_reads_back_ok():
    b = MockBroker()
    e = _exe(b)
    e.arm(ARM)
    d = e.place(intent(), GOOD_ACCT, GOOD_FEED, 0.0)
    assert d.action == "place" and d.rule == "ok"
    assert len(b.submitted) == 1 and b.flattened == []


def test_readback_mismatch_flattens_and_halts():
    # broker reports a different size than we sent -> flatten + halt
    bad = {"side": "B", "size": 9, "account": "ACC", "entry": 100.0, "stop": 99.0,
           "target": 103.0, "stop_resting": True}
    b = MockBroker(status_override=bad)
    e = _exe(b)
    e.arm(ARM)
    d = e.place(intent(), GOOD_ACCT, GOOD_FEED, 0.0)
    assert d.action == "flatten" and d.rule == "readback_mismatch"
    assert b.flattened == ["ACC"] and b.cancelled == ["ACC"]
    # halted: further checks refuse
    assert e.check(intent(setup_id="z"), GOOD_ACCT, GOOD_FEED, 0.0).rule == "halted"


def test_readback_missing_bracket_legs_halts():
    bad = {"side": "B", "size": 1, "account": "ACC", "entry": 100.0, "stop": 99.0,
           "target": 103.0, "stop_resting": False}
    b = MockBroker(status_override=bad)
    e = _exe(b)
    e.arm(ARM)
    assert e.place(intent(), GOOD_ACCT, GOOD_FEED, 0.0).rule == "readback_mismatch"


# ------------------------------------------------- PROMOTION-GATE §D2 blockers (regressions)

def test_contract_clamp_is_in_micros_and_matches_the_sizing_schedule():
    """§D2 blocker 2. `OrderIntent.size` carries MICROS (canon_lane/route_b both build it as
    `int(micros)`), so a clamp of 2 throttled every live order to 2 micros and gate B5 failed
    on trade one. The clamp must BE the sizing schedule's own cap, not a second literal that
    can drift away from it."""
    from src.canon.gate_evidence import MICRO_CLAMP
    assert SpineConfig().max_contracts == MICRO_CLAMP == 40
    e = _exe(MockBroker())
    e.arm(ARM)
    d = e.place(intent(size=40), GOOD_ACCT, GOOD_FEED, 0.0)   # a full-size order
    assert d.action == "place" and d.rule == "ok"             # passes through, NOT clamped
    assert d.clamped_size is None


def test_contract_clamp_still_shrinks_above_the_schedule_cap():
    b = MockBroker()
    e = _exe(b)
    e.arm(ARM)
    d = e.place(intent(size=99), GOOD_ACCT, GOOD_FEED, 0.0)
    assert d.action == "place" and d.clamped_size == 40       # shrink, never reject
    assert b.submitted[-1].size == 40


def test_daily_loss_halt_reindexes_to_the_days_own_risk_unit():
    """§D2 blocker 1. The halt is an R multiple of the day's base_dollar, so it tracks the
    drawdown-scaled sizer instead of tightening as the account grows. The two reference
    points are PROMOTION-GATE's own: -$800 at the eval floor, -$1,700 at $6k available DD."""
    from src.canon.spine import daily_loss_halt_dollars
    cfg = SpineConfig()                                        # -4R
    at_floor = AccountState(equity=52_000, trailing_floor=50_000,   # $2k available DD
                            day_pnl=0, open_positions=0)
    grown = AccountState(equity=56_000, trailing_floor=50_000,      # $6k available DD
                         day_pnl=0, open_positions=0)
    assert daily_loss_halt_dollars(cfg, at_floor) == -800.0
    assert daily_loss_halt_dollars(cfg, grown) == -1_700.0

    # and the guard actually fires at the re-indexed level, not the old fixed -$800
    just_under = AccountState(equity=56_000, trailing_floor=50_000,
                              day_pnl=-1_699, open_positions=0)
    assert _exe().check(intent(), just_under, GOOD_FEED, 0.0).action == "place"
    breached = AccountState(equity=56_000, trailing_floor=50_000,
                            day_pnl=-1_700, open_positions=0)
    d = _exe().check(intent(), breached, GOOD_FEED, 0.0)
    assert d.action == "halt" and d.rule == "daily_loss"


def test_no_fixed_dollar_daily_loss_knob_remains():
    """The footgun itself: a fixed-dollar field would let the units regression be reintroduced
    by setting one value. It must not exist."""
    assert not hasattr(SpineConfig(), "daily_loss_halt")
    assert hasattr(SpineConfig(), "daily_loss_halt_r")


def test_tier1_config_loads_from_live_yaml_and_matches_the_pin():
    """§D2 blocker 3: the limits must come from config, not dataclass defaults, and the
    shipped config must agree with the signed-off set."""
    from src.canon.spine import load_spine_config
    cfg = load_spine_config("config/live.yaml")
    assert cfg.max_contracts == 40 and cfg.daily_loss_halt_r == -4.0


def test_boot_assertion_fails_closed_on_a_drifted_limit(tmp_path):
    import yaml

    from src.canon.spine import SpinePinError, load_spine_config
    raw = yaml.safe_load(open("config/live.yaml"))
    raw["spine"]["max_contracts"] = 2                    # the exact old defect
    p = tmp_path / "drifted.yaml"
    p.write_text(yaml.safe_dump(raw))
    with pytest.raises(SpinePinError, match="drifted"):
        load_spine_config(p)


def test_missing_spine_block_is_an_error_not_a_silent_default(tmp_path):
    """'The limits ride on defaults' IS the defect — an absent block must not quietly
    reproduce it."""
    import yaml

    from src.canon.spine import SpinePinError, load_spine_config
    raw = yaml.safe_load(open("config/live.yaml"))
    raw.pop("spine")
    p = tmp_path / "no_spine.yaml"
    p.write_text(yaml.safe_dump(raw))
    with pytest.raises(SpinePinError, match="no `spine:` block"):
        load_spine_config(p)


def test_unknown_spine_key_is_rejected(tmp_path):
    """A typo'd limit silently falling back to a default is the failure mode this stops."""
    import yaml

    from src.canon.spine import SpinePinError, load_spine_config
    raw = yaml.safe_load(open("config/live.yaml"))
    raw["spine"]["max_contract"] = 40                    # typo: missing the 's'
    p = tmp_path / "typo.yaml"
    p.write_text(yaml.safe_dump(raw))
    with pytest.raises(SpinePinError, match="unknown spine config key"):
        load_spine_config(p)
