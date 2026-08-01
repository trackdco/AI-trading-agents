"""NYExecution + DryRunBroker — the R13 layer's own obligations.

The exit ENGINE (LiveExitExecutor/ExitDriver) is pinned elsewhere; what this file pins
is the routing: brackets reach the broker, cancels pull them, fills attribute to exact
refs, stops fire stop-first, close_now cancels the stop before closing, and realized
P&L reaches on_closed with the book's arithmetic ($2/pt-micro, $5 commission).
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.canon.spine import OrderIntent
from src.live.ny_execution import COMMISSION, DryRunBroker, NYExecution

NY = "America/New_York"


def _ts(hm):
    return pd.Timestamp(f"2026-04-20 {hm}", tz=NY)


def _intent(side="B", entry=18_000.0, stop=17_990.0, size=11, ref="ny:1"):
    return OrderIntent(side=side, order_type="limit", entry_ref=entry, stop=stop,
                       target=None, size=size, setup_id=ref, account="FUNDED")


def _bar(bk, hm, high, low, close):
    bk.on_bar(_ts(hm), high, low, close)


# ---------------------------------------------------------------- DryRunBroker
def test_entry_fills_on_touch_and_stop_fires_stop_first():
    bk = DryRunBroker()
    ref = bk.submit_bracket(_intent())
    _bar(bk, "09:45", 18_010, 18_002, 18_005)          # never trades down to the limit
    assert bk.take_fills() == [] and bk.position("FUNDED") == 0
    _bar(bk, "09:46", 18_006, 17_999, 18_004)          # trades through 18_000 -> fill
    fills = bk.take_fills()
    assert len(fills) == 1 and fills[0]["ref"] == ref and fills[0]["size"] == 11
    assert bk.position("FUNDED") == 11
    _bar(bk, "09:47", 18_001, 17_989, 17_995)          # trades through the stop
    assert bk.position("FUNDED") == 0
    assert bk.take_stop_fires()[0]["price"] == 17_990.0


def test_cancel_pulls_the_working_entry_and_its_stop():
    bk = DryRunBroker()
    ref = bk.submit_bracket(_intent())
    bk.cancel_order(ref)
    _bar(bk, "09:46", 18_006, 17_999, 18_004)
    assert bk.take_fills() == [] and bk.position("FUNDED") == 0
    assert bk.order_status(ref)["stop_resting"] is False


def test_close_partial_fills_with_one_tick_slip():
    bk = DryRunBroker()
    ref = bk.submit_bracket(_intent())
    _bar(bk, "09:46", 18_006, 17_999, 18_004)
    bk.take_fills()
    bk.close_partial("FUNDED", 11)                     # long -> close at close - tick
    f = bk.take_fills()
    assert f[0]["closing"] and f[0]["price"] == 18_004 - 0.25
    assert bk.position("FUNDED") == 0


# ---------------------------------------------------------------- NYExecution
class Sink(list):
    def __call__(self, row):
        self.append(row)


@pytest.fixture()
def ex():
    closed = []
    bk = DryRunBroker()
    e = NYExecution(mode="dryrun", broker=bk, journal=Sink(),
                    on_closed=lambda ref, pl: closed.append((ref, pl)))
    return e, bk, closed


def test_place_cancel_roundtrip(ex):
    e, bk, _ = ex
    assert e.place("ny:1", _intent(), trigger=None) is True
    assert len(bk._orders) == 1
    e.cancel("ny:1", "no_window_ahead")
    _bar(bk, "09:46", 18_006, 17_999, 18_004)
    assert e.poll_fills() == []                        # cancelled orders never fill


def test_fill_attribution_is_exact_with_two_resting_orders(ex):
    e, bk, _ = ex
    e.place("ny:1", _intent(entry=18_000.0, ref="ny:1"), None)
    e.place("ny:2", _intent(entry=17_980.0, ref="ny:2"), None)
    _bar(bk, "09:46", 18_006, 17_999, 18_004)          # only ny:1's level trades
    fills = e.poll_fills()
    assert [f["ref"] for f in fills] == ["ny:1"]


def test_close_now_cancels_stop_then_closes_and_reports_pl(ex):
    e, bk, closed = ex
    e.place("ny:1", _intent(), None)
    _bar(bk, "09:46", 18_006, 17_999, 18_004)
    e.poll_fills()
    e.confirm_fill("ny:1", {"entry": 18_000.0, "stop": 17_990.0, "direction": "long"},
                   11, pre=False)
    _bar(bk, "09:47", 18_012, 18_004, 18_010)          # +10pt
    pl = e.close_now("ny:1", "rule_k_flatten")
    # close at 18_010 - 0.25 slip... estimate uses last close (18_010): 10pt * $2 * 11 - $5
    assert closed and closed[0][0] == "ny:1"
    assert pl == pytest.approx(10 * 2.0 * 11 - COMMISSION)
    assert bk.position("FUNDED") == 0
    assert bk.order_status(bk._orders and list(bk._orders)[0])["stop_resting"] is False


def test_realized_pl_arithmetic_partial_plus_stop():
    """_realize: one partial leg + remainder at the (BE) stop, book arithmetic."""
    e = NYExecution(mode="dryrun", broker=DryRunBroker(), journal=Sink())
    got = []
    e.on_closed = lambda ref, pl: got.append(pl)
    p = {"exe": None, "entry": 18_000.0, "stop": 18_000.0, "side": "B",
         "size": 10, "pre": False, "legs": [(5, 18_010.0)]}
    e._positions["ny:9"] = p
    e._realize("ny:9", p, {"kind": "exit", "reason": "be_stop", "price": None})
    # 5 micros +10pt = $100; 5 micros at BE = $0; minus $5 commission
    assert got == [pytest.approx(5 * 10 * 2.0 - COMMISSION)]


def test_shadow_mode_touches_nothing():
    e = NYExecution(mode="shadow", broker=None, journal=Sink())
    assert e.place("ny:1", _intent(), None) is True    # journal-only placement
    assert e.poll_fills() == []
    e.cancel("ny:1", "x")
    assert e.close_now("ny:1", "x") == 0.0             # no such position, no crash


# ------------------------------------------------------------- cancel/fill race (ny:20)
def test_cancel_that_loses_the_race_to_a_fill_still_surfaces_the_fill(ex):
    """R13 practice day 3, ny:2026-07-31:20: the bar touched the limit and the runner's
    gate-cancel landed in the same minute. The old cancel popped the order record, so
    the queued fill could not attribute and was silently dropped — leaving a naked,
    stopless, unjournaled position in the broker. The graveyard keeps attribution:
    the racing fill surfaces, and the scratch path can flatten it."""
    e, bk, _ = ex
    e.place("ny:1", _intent(side="S", entry=18_020.0, stop=18_030.0), None)
    _bar(bk, "10:21", 18_022, 18_010, 18_015)          # trades through the short limit
    e.cancel("ny:1", "gold_wall_quality")              # cancel AFTER the broker filled
    fills = e.poll_fills()
    assert [f["ref"] for f in fills] == ["ny:1"]       # the racing fill is NOT dropped
    assert bk.position("FUNDED") == -11                # position exists and is known
    e.scratch_unconfirmed("ny:1", 11, "gate:gold_wall_quality")
    assert bk.position("FUNDED") == 0                  # flattened, not naked
    assert not bk.order_status("dry:1")["stop_resting"]


def test_cancel_with_no_fill_keeps_nothing_behind(ex):
    e, bk, _ = ex
    e.place("ny:1", _intent(side="S", entry=18_020.0, stop=18_030.0), None)
    _bar(bk, "10:21", 18_015, 18_010, 18_012)          # never reaches the limit
    e.cancel("ny:1", "no_window_ahead")
    assert e.poll_fills() == []
    assert e._graveyard == {} and "ny:1" not in e._orders
    _bar(bk, "10:22", 18_030, 18_010, 18_020)          # cancelled: can never fill later
    assert e.poll_fills() == [] and bk.position("FUNDED") == 0
