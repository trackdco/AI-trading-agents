#!/usr/bin/env python3
"""Safety-spine FORCE TEST (SAFETY-SPINE.md) — deliberately trip every rule in sim and show
each behaves exactly as specified. No broker: a mock stands in. Complements the unit suite
(tests/test_canon_spine.py) with a single readable demonstration and real output.

    python -m scripts.spine_forcetest
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.agent_replay import size_book  # noqa: F401  (ensures src importable)
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


def _intent(**kw):
    base = {"side": "B", "order_type": "limit", "entry_ref": 100.0, "stop": 99.0,
            "target": 103.0, "size": 1, "setup_id": "s", "account": "ACC"}
    base.update(kw)
    return OrderIntent(**base)


class _Mock:
    """Faithful mock: order_status echoes the last submitted intent so read-back passes
    (lets the duplicate/order-rate cases reach their own rule instead of a read-back halt)."""
    def __init__(self):
        self.last = None

    def submit_bracket(self, i):
        self.last = i
        return "ref"

    def order_status(self, r):
        i = self.last
        # stop_resting is the key _verify_readback checks (B4). The old legs_resting name
        # made the spine flatten+halt the armed cases — correctly! — and report 'halted'
        # for duplicate/order-rate (on-box 2026-07-27).
        return {"side": i.side, "size": i.size, "account": i.account, "entry": i.entry_ref,
                "stop": i.stop, "target": i.target, "stop_resting": True}

    def position(self, a): return 0
    def flatten(self, a): pass
    def cancel_all(self, a): pass


def _exe(**cfg):
    return SpineExecutor(SpineConfig(**cfg), _Mock())


# each case: (label, expected action, expected rule, callable -> SpineDecision)
CASES = [
    ("Tier1 dd-proximity halt", "halt", "dd_proximity",
     lambda: _exe().check(_intent(),                       # $80 of room <= the $100 hard halt
              AccountState(50_080, 50_000, 0, 0), GOOD_FEED, 0.0)),   # under the DD ramp
    ("Tier1 daily-loss halt", "halt", "daily_loss",
     lambda: _exe().check(_intent(),
              AccountState(52_000, 50_000, -800, 0), GOOD_FEED, 0.0)),
    ("Tier1 contract clamp", "place", "contract_clamp",
     lambda: _exe(max_contracts=2).check(_intent(size=5), GOOD_ACCT, GOOD_FEED, 0.0)),
    ("Tier2 feed-stale reject", "reject", "feed_stale",
     lambda: _exe().check(_intent(), GOOD_ACCT,
              FeedHealth(9999, False, True, 1.0), 0.0)),
    ("Tier2 spread reject", "reject", "spread",
     lambda: _exe().check(_intent(), GOOD_ACCT,
              FeedHealth(100, False, True, 9.0), 0.0)),
    ("Tier2 limit-only (reject market)", "reject", "limit_only",
     lambda: _exe().check(_intent(order_type="market"), GOOD_ACCT, GOOD_FEED, 0.0)),
    ("Tier3 fail-closed (NaN stop)", "halt", "fail_closed",
     lambda: _exe().check(_intent(stop=math.nan), GOOD_ACCT, GOOD_FEED, 0.0)),
    ("Manual KILL", "halt", "manual_kill",
     lambda: SpineExecutor(SpineConfig(), _Mock(), kill_file_present=lambda: True)
              .check(_intent(), GOOD_ACCT, GOOD_FEED, 0.0)),
    ("Startup parity not green", "halt", "startup_parity",
     lambda: _exe().check(_intent(), GOOD_ACCT, GOOD_FEED, 0.0, parity_ok=False)),
]


def _rate_and_dup():
    """Order-rate + duplicate need state across calls; run them explicitly (armed)."""
    out = []
    e = _exe(max_orders_per_min=2)
    e.arm(ARM)
    e.place(_intent(setup_id="a"), GOOD_ACCT, GOOD_FEED, 0.0)
    d_dup = e.place(_intent(setup_id="a"), GOOD_ACCT, GOOD_FEED, 0.0)
    out.append(("Tier2 duplicate reject", "reject", "duplicate", d_dup))
    e.place(_intent(setup_id="b"), GOOD_ACCT, GOOD_FEED, 0.0)
    d_rate = e.place(_intent(setup_id="c"), GOOD_ACCT, GOOD_FEED, 1.0)
    out.append(("Tier2 order-rate reject", "reject", "order_rate", d_rate))
    return out


def main():
    rows = [(lbl, ea, er, fn()) for lbl, ea, er, fn in CASES] + \
           [(lbl, ea, er, d) for lbl, ea, er, d in _rate_and_dup()]
    ok = True
    print(f"{'rule forced':38s} {'action':9s} {'rule':16s} result")
    for lbl, exp_a, exp_r, d in rows:
        good = d.action == exp_a and d.rule == exp_r
        ok = ok and good
        extra = f" clamp->{d.clamped_size}" if d.clamped_size is not None else ""
        print(f"{lbl:38s} {d.action:9s} {d.rule:16s} {'✓' if good else '✗ EXPECTED '+exp_a+'/'+exp_r}{extra}")
    print(f"\nSPINE FORCE TEST: {'✓ every rule fired as specified' if ok else '✗ MISMATCH'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
