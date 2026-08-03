"""DTCBroker adapter — the spine's Broker protocol over the mock Sierra, end to end.

This is the bridge the armed path will actually use, so every method is exercised against
the same mock server that models real Sierra's strictness (unknown-key drops, ServerOrderID
echo, bracket teardown, cancel rejects). The on-box A7/B7/B8 gates re-run these same
sequences against the real server — these tests are the offline half of that evidence.
"""
from __future__ import annotations

import socket

from src.canon.spine import OrderIntent
from src.desk import dtc_client as D
from src.desk.dtc_broker import DTCBroker
from src.desk.dtc_client import DTCClient, DTCConfig
from tests.test_dtc_client import MockDTCServer


def _broker(server, order_mode_client=None):
    cfg = DTCConfig(host="127.0.0.1", port=server.port, username="u", password="p",
                    trade_account="FUNDED")
    c = DTCClient(cfg=cfg, connector=lambda h, p: socket.create_connection(
        (h, server.port), timeout=2.0))
    assert c.connect()
    return DTCBroker(client=c, symbol="MNQU26-CME", account="FUNDED", pump_rounds=4), c


def _intent(**kw):
    base = {"side": "B", "order_type": "limit", "entry_ref": 100.0, "stop": 99.0,
            "target": None, "size": 3, "setup_id": "s1", "account": "FUNDED"}
    base.update(kw)
    return OrderIntent(**base)


def test_submit_and_readback_satisfies_the_spine_contract():
    """order_status must present exactly what _verify_readback consumes — and stop_resting
    must come from the CHILD's own server-side status, not from the submit having returned."""
    s = MockDTCServer(order_mode="none")               # entry rests OPEN
    try:
        b, c = _broker(s)
        ref = b.submit_bracket(_intent())
        st = b.order_status(ref)
        assert st["side"] == "B" and st["size"] == 3 and st["account"] == "FUNDED"
        assert st["entry"] == 100.0 and st["stop"] == 99.0
        assert st["stop_resting"] is True              # the child is genuinely working
        c.close()
    finally:
        s.stop()


def test_unknown_ref_reads_back_empty_which_fails_verify():
    s = MockDTCServer(order_mode="none")
    try:
        b, c = _broker(s)
        assert b.order_status("desk-ghost") == {}      # {} has no stop_resting -> B4 fails loud
        c.close()
    finally:
        s.stop()


def test_cancel_order_tears_down_entry_and_stop():
    """B7 through the adapter: after cancel, NOTHING of the bracket is working."""
    s = MockDTCServer(order_mode="none")
    try:
        b, c = _broker(s)
        ref = b.submit_bracket(_intent())
        stop_oid = b._brackets[ref]["stop_oid"]
        b.cancel_order(ref)
        assert ref in s.cancelled and stop_oid in s.cancelled
        assert b.order_status(ref)["stop_resting"] is False
        c.close()
    finally:
        s.stop()


def test_modify_stop_moves_the_child_in_place():
    """B8 trail/BE move: one CANCEL_REPLACE on the stop child; the entry is untouched and
    the read-back reflects the new stop price."""
    s = MockDTCServer(order_mode="none")
    try:
        b, c = _broker(s)
        ref = b.submit_bracket(_intent())
        b.modify_stop(ref, 99.75)
        st = b.order_status(ref)
        assert st["stop"] == 99.75 and st["stop_resting"] is True
        assert len(s.replaced) == 1                     # modified in place, never re-submitted
        assert ref not in s.cancelled                   # entry untouched
        c.close()
    finally:
        s.stop()


def test_modify_stop_on_unknown_ref_raises_fail_closed():
    s = MockDTCServer(order_mode="none")
    try:
        b, c = _broker(s)
        try:
            b.modify_stop("desk-ghost", 99.0)
            raise AssertionError("expected KeyError")
        except KeyError:
            pass
        c.close()
    finally:
        s.stop()


def test_close_partial_clamps_to_live_position_and_reduces():
    """B8 partial: mock reports a net LONG 2 — closing 5 must clamp to 2, sell side,
    OpenOrClose=close. It can never flip the position."""
    s = MockDTCServer(order_mode="none")               # positions query returns Quantity=2
    try:
        b, c = _broker(s)
        oid = b.close_partial("FUNDED", qty=5, price=None)
        assert oid                                      # an order went out
        row = s.order_by_oid(oid)
        assert row["Quantity"] == 2                     # clamped to the live position
        assert row["BuySell"] == 2                      # long position -> SELL to reduce
        assert row["OpenOrClose"] == 2
        assert row["OrderType"] == D.ORDER_TYPE_MARKET
        c.close()
    finally:
        s.stop()


def test_close_partial_with_price_rests_a_limit():
    s = MockDTCServer(order_mode="none")
    try:
        b, c = _broker(s)
        oid = b.close_partial("FUNDED", qty=1, price=104.5)
        row = s.order_by_oid(oid)
        assert row["OrderType"] == D.ORDER_TYPE_LIMIT and row["Price1"] == 104.5
        c.close()
    finally:
        s.stop()


def test_flatten_cancels_working_orders_before_market_closing():
    """Kill path: the resting stop must be DEAD before the market close goes out, or it can
    double-fill against the flatten. Order of operations is the test."""
    s = MockDTCServer(order_mode="none")
    try:
        b, c = _broker(s)
        ref = b.submit_bracket(_intent())
        stop_oid = b._brackets[ref]["stop_oid"]
        b.flatten("FUNDED")
        assert ref in s.cancelled and stop_oid in s.cancelled
        closes = [o for o in s.orders if o.get("OpenOrClose") == 2]
        assert closes and closes[-1]["OrderType"] == D.ORDER_TYPE_MARKET
        # every cancel arrived before the close order did
        close_ix = s.orders.index(closes[-1])
        assert all(o.get("OpenOrClose") != 2 for o in s.orders[:close_ix]
                   if o["ClientOrderID"] in (ref, stop_oid))
        c.close()
    finally:
        s.stop()


def test_price_scale_multiplies_out_and_divides_back():
    """Pat's VPS: the Rithmic service runs at 100x display prices (depth files first, then
    the ORDER path — DTC Price1=28690 landed at Sierra as 286.90, 'bad price' on every
    limit, 2026-07-27). With price_scale=100 the broker sends service prices and reads
    back display prices; the spine and forcetest keep speaking display throughout."""
    s = MockDTCServer(order_mode="none")
    try:
        b, c = _broker(s)
        b.price_scale = 100.0
        ref = b.submit_bracket(_intent(entry_ref=28690.0, stop=28670.0, size=1))
        stop_oid = c.last_bracket[1]
        sent_entry = next(o for o in s.orders if o["ClientOrderID"] == ref)
        sent_stop = next(o for o in s.orders if o["ClientOrderID"] == stop_oid)
        assert sent_entry["Price1"] == 2869000.0 and sent_stop["Price1"] == 2867000.0
        st = b.order_status(ref)                       # read-back is DISPLAY prices again
        assert st["entry"] == 28690.0 and st["stop"] == 28670.0 and st["stop_resting"]
        b.modify_stop(ref, 28680.0)                    # outbound modify scales too
        assert s.order_by_oid(stop_oid)["Price1"] == 2868000.0
        c.close()
    finally:
        s.stop()


# --------------------------------------------------------------------------- keepalive
def test_ensure_connected_survives_a_true_idle_drop():
    """The 2026-08-02/03 incident, reproduced: a socket that dies during a QUIET stretch
    (nothing calls _pump — no submit/cancel/status) must still be caught. ensure_connected
    is the standalone entry point the live loop's idle-independent keepalive calls."""
    s = MockDTCServer(order_mode="none")
    try:
        b, c = _broker(s)
        assert b.ensure_connected() is True             # freshly connected: trivially alive
        c._sock.close()                                 # simulate the reaped idle socket
        assert b.ensure_connected() is True              # heals itself, no order needed
        assert c.logged_on is True
        c.close()
    finally:
        s.stop()


def test_ensure_connected_never_raises_when_the_server_is_gone():
    """A keepalive failure must degrade to False, never an exception — this runs on every
    poll cycle of the live loop and must never be the thing that crashes it."""
    s = MockDTCServer(order_mode="none")
    b, c = _broker(s)
    s.stop()                                            # server gone entirely
    c._sock.close()
    assert b.ensure_connected() is False                # no server to reconnect to: False
