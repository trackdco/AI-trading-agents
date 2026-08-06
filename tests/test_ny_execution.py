"""NYExecution + DryRunBroker — the R13 layer's own obligations.

The exit ENGINE (LiveExitExecutor/ExitDriver) is pinned elsewhere; what this file pins
is the routing: brackets reach the broker, cancels pull them, fills attribute to exact
refs, stops fire stop-first, close_now cancels the stop before closing, and realized
P&L reaches on_closed with the book's arithmetic ($2/pt-micro, $5 commission).
"""
from __future__ import annotations

import socket

import pandas as pd
import pytest

from src.canon.spine import OrderIntent
from src.desk.dtc_broker import DTCBroker
from src.desk.dtc_client import DTCClient, DTCConfig
from src.live.ny_execution import COMMISSION, DryRunBroker, NYExecution
from tests.test_dtc_client import MockDTCServer

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


def test_close_now_is_leg_aware_after_a_prior_partial(ex):
    """2026-08-05 review: a position that already took a partial exit (V8's own partial
    action, or an agent's close_partial_qty) has fewer than p["size"] micros left.
    close_now() used to always close AND price the full original size -- close_partial's
    own broker-side clamp saves the ORDER from being wrong, but the REPORTED pl still
    double-counted the already-realized leg, corrupting the day's risk budget."""
    e, bk, closed = ex
    e.place("ny:1", _intent(size=10), None)
    _bar(bk, "09:46", 18_006, 17_999, 18_004)
    e.poll_fills()
    e.confirm_fill("ny:1", {"entry": 18_000.0, "stop": 17_990.0, "direction": "long"},
                   10, pre=False)
    # a partial: 5 micros already closed AT THE BROKER (as close_partial_qty/V8's own
    # partial action would have done) at +10pt (18_010), leaving 5 open
    bk._pos -= 5
    e._positions["ny:1"]["legs"].append((5, 18_010.0))
    _bar(bk, "09:47", 18_022, 18_014, 18_020)          # close 18_020, +20pt from entry
    pl = e.close_now("ny:1", "rule_k_flatten")
    # leg: 5 * (18_010-18_000) * $2 = $100. remainder: 5 * (18_020-0.25-18_000) * $2 - $5
    # close_now prices the remaining CLOSE against the broker's own last close (18_020,
    # no slip modeled in close_now's own pl estimate, unlike close_partial's fill price)
    expected = (5 * 10 * 2.0) + (5 * 20 * 2.0 - COMMISSION)
    assert pl == pytest.approx(expected)
    assert closed[0][1] == pytest.approx(expected)
    assert bk.position("FUNDED") == 0                  # only the REMAINING 5 were closed


def test_close_flipped_never_touches_the_broker_position(ex):
    """2026-08-05 incident: rule J's padded fill already nets the old position away in
    the SAME broker order that opens the new one. close_flipped() must NOT issue a
    close_partial (that would erode the brand-new reversal) -- only cancel the stale
    stop and do bookkeeping-only closure with the caller's own pl estimate."""
    e, bk, closed = ex
    e.place("ny:1", _intent(size=10), None)
    _bar(bk, "09:46", 18_006, 17_999, 18_004)
    e.poll_fills()
    e.confirm_fill("ny:1", {"entry": 18_000.0, "stop": 17_990.0, "direction": "long"},
                   10, pre=False)
    # simulate the flip: broker net is already whatever the padded reversal fill left
    # it at (e.g. -6 short after a 16-lot padded sell netted the +10 long away) --
    # close_flipped must not move this AT ALL
    bk._pos = -6
    pl = e.close_flipped("ny:1", "rule_j_flip", 123.45)
    assert pl is None                                   # bookkeeping-only, no broker return value
    assert bk.position("FUNDED") == -6                  # completely untouched
    assert closed == [("ny:1", 123.45)]                 # caller's own pl estimate, verbatim
    assert "ny:1" not in e._positions
    assert not bk.order_status("dry:1")["stop_resting"]  # the stale stop WAS pulled


def test_close_flipped_on_unknown_ref_is_a_safe_noop(ex):
    e, bk, closed = ex
    e.close_flipped("ny:ghost", "rule_j_flip", 0.0)
    assert closed == []


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


# ------------------------------------------------------------- cancel/fill race, DTC path
def _armed_exec(server):
    """A real DTCBroker (not DryRunBroker) against the mock Sierra -- poll_fills()'s
    DTC branch (order_status polling) is a completely different code path from the
    dry-run branch above and needs its own coverage."""
    cfg = DTCConfig(host="127.0.0.1", port=server.port, username="u", password="p",
                    trade_account="FUNDED")
    c = DTCClient(cfg=cfg, connector=lambda h, p: socket.create_connection(
        (h, server.port), timeout=2.0))
    assert c.connect()
    bk = DTCBroker(client=c, symbol="MNQU26-CME", account="FUNDED", pump_rounds=4)
    e = NYExecution(mode="armed", broker=bk, journal=Sink())
    return e, bk, c


def test_poll_fills_dtc_path_resurrects_a_cancel_that_lost_the_race_to_a_fill():
    """2026-08-05 review: the DTC branch of poll_fills() never consulted the graveyard
    (unlike the dry-run branch), so this exact race -- the one the graveyard mechanism
    was built for (R13 practice day 3, ny:20) -- orphaned the fill on the armed path.
    cancel()'s only_if_not_filled=True leaves a raced fill's real stop resting; that
    stop_resting is exactly the signal this branch needs to tell a genuine cancel
    (stop pulled, dead) from a lost race (stop still resting -> real fill)."""
    s = MockDTCServer(order_mode="fill_entry")     # entry fills immediately, stop rests
    try:
        e, bk, c = _armed_exec(s)
        assert e.place("ny:1", _intent(size=3), None) is True
        e.cancel("ny:1", "gate")                    # too late -- it already filled
        assert "ny:1" not in e._orders               # moved to the graveyard
        fills = e.poll_fills()
        assert [f["ref"] for f in fills] == ["ny:1"]  # resurrected, not orphaned
        assert e._graveyard == {}                     # checked once, then dropped
        assert "ny:1" in e._orders                     # resurrected for confirm_fill downstream
        c.close()
    finally:
        s.stop()


def test_poll_fills_dtc_path_drops_a_genuinely_cancelled_graveyard_entry():
    """The normal case: the cancel actually won the race (entry never filled). The
    graveyard entry must be checked once and dropped -- never reported as a fill,
    never re-checked forever."""
    s = MockDTCServer(order_mode="none")            # entry rests, never fills
    try:
        e, bk, c = _armed_exec(s)
        assert e.place("ny:1", _intent(size=3), None) is True
        e.cancel("ny:1", "gate")
        assert e.poll_fills() == []
        assert e._graveyard == {} and "ny:1" not in e._orders
        c.close()
    finally:
        s.stop()
