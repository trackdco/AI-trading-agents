"""End-to-end DTC client tests against a mock DTC server (item 7). No real Sierra — the
mock speaks the same JSON-compact DTC protocol over a localhost socket, so we exercise
logon, market data + MBP-10 depth, account/position, order fill/partial/reject, heartbeat,
reconnect + re-subscribe, and stale-heartbeat detection.
"""
from __future__ import annotations

import json
import socket
import struct
import threading


from src.desk import dtc_client as D
from src.desk.dtc_client import DTCClient, DTCConfig


# The fields a real Sierra s_SubmitNewSingleOrder actually reads. Anything else (e.g. "Stop",
# "Target") is an UNKNOWN key that Sierra's JSON decoder DROPS silently — so the mock models
# that by keeping only these, exposing the naked-entry bug the old permissive mock hid.
_VALID_SUBMIT_FIELDS = {
    "Symbol", "TradeAccount", "ClientOrderID", "OrderType", "BuySell", "Price1", "Price2",
    "Quantity", "TimeInForce", "GoodTillDateTime", "IsAutomated", "OpenOrClose",
    "ParentTriggerClientOrderID", "FreeFormText", "IsParentOrder",
}


class MockDTCServer:
    def __init__(self, order_mode: str = "fill"):
        self.order_mode = order_mode
        self.orders: list[dict] = []      # single orders received, DTC-valid fields only
        self.ocos: list[dict] = []        # SUBMIT_NEW_OCO_ORDER messages received
        self.cancelled: list[str] = []    # ClientOrderIDs cancelled (incl. bracket children)
        self.cancel_rejects: list[str] = []   # cancels of unknown/filled orders
        self.replaced: list[dict] = []    # CANCEL_REPLACE messages applied
        self._sid = 7000                  # ServerOrderIDs, echoed like real Sierra
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind(("127.0.0.1", 0))
        self._srv.listen(4)
        self.port = self._srv.getsockname()[1]
        self._stop = threading.Event()
        self.drop_next = False
        self._t = threading.Thread(target=self._serve, daemon=True)
        self._t.start()

    def _serve(self):
        self._srv.settimeout(0.3)
        while not self._stop.is_set():
            try:
                conn, _ = self._srv.accept()
            except TimeoutError:
                continue
            except OSError:
                break                       # server socket closed by stop() — exit cleanly
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _send(self, conn, mtype, **f):
        conn.sendall(json.dumps({"Type": mtype, **f}).encode() + b"\x00")

    def _handle(self, conn):
        conn.settimeout(0.3)
        buf = b""
        # DTC binary handshake first: read the 16-byte ENCODING_REQUEST, reply with a binary
        # ENCODING_RESPONSE, then switch to the JSON (\0-terminated) protocol.
        while len(buf) < 16 and not self._stop.is_set():
            try:
                data = conn.recv(65536)
            except TimeoutError:
                continue
            except OSError:
                return
            if not data:
                return
            buf += data
        conn.sendall(struct.pack("<HHii4s", 16, D.ENCODING_RESPONSE, 8, D.JSON_ENCODING, b"DTC\x00"))
        buf = buf[16:]
        while not self._stop.is_set():
            while b"\x00" in buf:
                raw, buf = buf.split(b"\x00", 1)
                if raw:
                    try:
                        self._respond(conn, json.loads(raw.decode()))
                    except OSError:
                        return          # client disconnected mid-response (Windows: WinError 10053)
            try:
                data = conn.recv(65536)
            except TimeoutError:
                continue
            except OSError:
                return
            if not data:
                return
            buf += data

    def _respond(self, conn, m):
        t = m["Type"]
        if t == D.ENCODING_REQUEST:
            self._send(conn, D.ENCODING_RESPONSE, Encoding=D.JSON_ENCODING)
        elif t == D.LOGON_REQUEST:
            if self.drop_next:                       # simulate a link drop right after logon
                self.drop_next = False
                conn.close()
                return
            self._send(conn, D.LOGON_RESPONSE, Result=1, ResultText="ok")
        elif t == D.HEARTBEAT:
            self._send(conn, D.HEARTBEAT, CurrentDateTime=0)
        elif t == D.MARKET_DATA_REQUEST:
            self._send(conn, D.MARKET_DATA_SNAPSHOT, Symbol=m["Symbol"], LastTradePrice=100.0)
            self._send(conn, D.MARKET_DATA_UPDATE_TRADE, Symbol=m["Symbol"], Price=100.25, Volume=3)
        elif t == D.MARKET_DEPTH_REQUEST:
            for i in range(3):
                self._send(conn, D.MARKET_DEPTH_SNAPSHOT_LEVEL, Side=1, Price=100.0 - i * 0.25,
                           Quantity=10 + i, NumOrders=1 + i, Level=i + 1)
        elif t == D.SUBMIT_NEW_OCO_ORDER:
            self.ocos.append({k: v for k, v in m.items() if k != "Type"})
            return
        elif t == D.SUBMIT_NEW_SINGLE_ORDER:
            # model Sierra: keep only DTC-valid fields; unknown keys (Stop/Target) are DROPPED.
            kept = {k: v for k, v in m.items() if k in _VALID_SUBMIT_FIELDS}
            self._sid += 1
            kept["ServerOrderID"] = self._sid
            self.orders.append(kept)
            oid = m["ClientOrderID"]
            # Real Sierra sends FilledQuantity/AverageFillPrice PRESENT with JSON null on a
            # resting order (found on-box 2026-07-27: int(None) crash in order_status).
            # dict.get's default only covers ABSENT keys — model the nulls faithfully.
            # And a bracket CHILD (ParentTriggerClientOrderID) is HELD server-side until
            # its parent fills: it acks as PENDING_CHILD, never OPEN (on-box 2026-07-27).
            ack = (D.ORDER_STATUS_PENDING_CHILD if m.get("ParentTriggerClientOrderID")
                   else D.ORDER_STATUS_OPEN)
            self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid, ServerOrderID=self._sid,
                       OrderStatus=ack,
                       FilledQuantity=None, AverageFillPrice=None,
                       Price1=kept.get("Price1"), Quantity=kept.get("Quantity"))
            # market orders always fill regardless of mode (a reducing close must not
            # depend on the scenario knob). "fill_entry" is the Sierra-faithful bracket
            # fill: the entry fills but the protective STOP child stays WORKING — the
            # state the B4/B8 stop_resting read-back is defined over.
            fills = (m.get("OrderType") == D.ORDER_TYPE_MARKET
                     or self.order_mode == "fill"
                     or (self.order_mode in ("fill_entry", "fill_entry_stop_errors")
                         and m.get("OrderType") != D.ORDER_TYPE_STOP))
            if fills:
                self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid, OrderStatus=D.ORDER_STATUS_FILLED,
                           FilledQuantity=m["Quantity"], AverageFillPrice=m.get("Price1", 100.0))
            elif self.order_mode == "partial":
                self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid,
                           OrderStatus=D.ORDER_STATUS_PARTIALLY_FILLED,
                           FilledQuantity=max(1, m["Quantity"] // 2), RemainingQuantity=1)
            elif self.order_mode == "reject":
                self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid,
                           OrderStatus=D.ORDER_STATUS_REJECTED, InfoText="risk rejected")
            elif (self.order_mode in ("stop_errors", "fill_entry_stop_errors")
                  and m.get("OrderType") == D.ORDER_TYPE_STOP):
                # 2026-08-05 incident, reproduced: Sierra's Trade Orders window showed a
                # stop leg as "Error", a label the DTC OrderStatusEnum has no distinct
                # numeric code for. 99 stands in for whatever that real status turns out
                # to be -- not REJECTED(9), not any code DTCBroker._working()/FILLED
                # already recognizes. "stop_errors": entry stays resting (no fill race).
                # "fill_entry_stop_errors": entry fills normally (the fill-race case).
                # The two legs are independent orders (v4 design, dtc_client.py's own
                # submit_bracket docstring) -- ParentTriggerClientOrderID is never sent,
                # so OrderType is the only reliable entry-vs-stop signal here.
                self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid,
                           OrderStatus=99, InfoText="Error")
        elif t == D.CANCEL_ORDER:
            # model Sierra: a cancel of an unknown/never-seen order is REJECTED with text,
            # not silently absorbed; cancelling a working parent cancels its bracket
            # children too (Sierra tears the linked stop down with the entry).
            oid = m.get("ClientOrderID")
            order = self.order_by_oid(oid)
            if order is None or oid in self.cancelled:
                self.cancel_rejects.append(oid)
                self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid,
                           InfoText="cancel rejected: no working order")
                return
            for victim in [order, *self.children_of(oid)]:
                voi = victim["ClientOrderID"]
                if voi not in self.cancelled:
                    self.cancelled.append(voi)
                    self._send(conn, D.ORDER_UPDATE, ClientOrderID=voi,
                               ServerOrderID=victim.get("ServerOrderID"),
                               OrderStatus=D.ORDER_STATUS_CANCELED)
        elif t == D.CANCEL_REPLACE_ORDER:
            oid = m.get("ClientOrderID")
            order = self.order_by_oid(oid)
            if order is None or oid in self.cancelled:
                self.cancel_rejects.append(oid)
                self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid,
                           InfoText="cancel/replace rejected: no working order")
                return
            order["Price1"] = m["Price1"]
            self.replaced.append({k: v for k, v in m.items() if k != "Type"})
            self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid,
                       ServerOrderID=order.get("ServerOrderID"),
                       OrderStatus=D.ORDER_STATUS_OPEN, Price1=m["Price1"])
        elif t == D.CURRENT_POSITIONS_REQUEST:
            self._send(conn, D.POSITION_UPDATE, Symbol="NQ", Quantity=2, AveragePrice=100.0)
        elif t == D.ACCOUNT_BALANCE_REQUEST:
            self._send(conn, D.ACCOUNT_BALANCE_UPDATE, CashBalance=52000.0, AccountCurrency="USD")

    def stop(self):
        self._stop.set()
        self._srv.close()

    # ---- bracket-structure inspection (models real Sierra) ---------------------------
    def order_by_oid(self, oid):
        return next((o for o in self.orders if o.get("ClientOrderID") == oid), None)

    def children_of(self, oid):
        return [o for o in self.orders if o.get("ParentTriggerClientOrderID") == oid]

    def has_protective_stop(self, entry_oid) -> bool:
        """True iff a resting protective STOP is attached to the entry — a child order linked
        by ParentTriggerClientOrderID, or a SUBMIT_NEW_OCO_ORDER referencing the entry. A single
        SUBMIT_NEW_SINGLE_ORDER carrying `Stop`/`Target` fields does NOT qualify (Sierra drops
        them), which is exactly the naked-entry bug."""
        child_stop = any(o.get("OrderType") == D.ORDER_TYPE_STOP for o in self.children_of(entry_oid))
        oco_stop = any(o.get("ParentTriggerClientOrderID") == entry_oid for o in self.ocos)
        return child_stop or oco_stop


def _client(server, **kw):
    cfg = DTCConfig(host="127.0.0.1", port=server.port, username="u", password="p",
                    trade_account="ACC")
    return DTCClient(cfg=cfg, connector=lambda h, p: socket.create_connection((h, server.port),
                                                                              timeout=2.0), **kw)


def test_logon():
    s = MockDTCServer()
    try:
        c = _client(s)
        assert c.connect() is True and c.logged_on is True
        c.close()
    finally:
        s.stop()


def test_market_data_and_depth():
    s = MockDTCServer()
    trades, depth = [], []
    try:
        c = _client(s, on_trade=trades.append, on_depth=depth.append)
        c.connect()
        c.subscribe_market_data("NQ")
        c.subscribe_depth("NQ")
        for _ in range(10):
            c.pump(timeout=0.2)
        assert any(t.get("Price") == 100.25 for t in trades)
        assert len(depth) >= 3 and depth[0]["Quantity"] == 10        # MBP-10 levels
        c.close()
    finally:
        s.stop()


def test_positions_and_balance():
    s = MockDTCServer()
    try:
        c = _client(s)
        c.connect()
        pos = c.positions()
        bal = c.account_balance()
        assert pos and pos[0]["Quantity"] == 2
        assert bal and bal["CashBalance"] == 52000.0
        c.close()
    finally:
        s.stop()


def _order_result(mode):
    s = MockDTCServer(order_mode=mode)
    updates = []
    try:
        c = _client(s, on_order_update=updates.append)
        c.connect()
        c.submit_bracket(symbol="NQ", buy=True, entry=100.0, stop=99.0, target=103.0, qty=2)
        for _ in range(10):
            c.pump(timeout=0.2)
        c.close()
    finally:
        s.stop()
    return [u["OrderStatus"] for u in updates]


def test_order_filled():
    assert D.ORDER_STATUS_FILLED in _order_result("fill")


def test_order_partial_fill():
    assert D.ORDER_STATUS_PARTIALLY_FILLED in _order_result("partial")


def test_order_rejected():
    assert D.ORDER_STATUS_REJECTED in _order_result("reject")


def test_submit_bracket_drops_non_dtc_stop_target_fields():
    """Documents the mechanism: `Stop`/`Target` are NOT s_SubmitNewSingleOrder fields, so a real
    Sierra (and now the mock) drops them silently. This passes TODAY and proves the entry order
    carries no protective information on the wire."""
    s = MockDTCServer(order_mode="fill")
    try:
        c = _client(s)
        c.connect()
        oid = c.submit_bracket(symbol="NQ", buy=True, entry=100.0, stop=99.0, target=103.0, qty=2)
        for _ in range(10):
            c.pump(timeout=0.2)
        c.close()
        entry = s.order_by_oid(oid)
        assert entry is not None
        assert "Stop" not in entry and "Target" not in entry     # silently dropped by Sierra
    finally:
        s.stop()


def test_submit_bracket_rests_a_protective_stop_alongside_the_entry():
    """THE INVARIANT (Angus B4): every entry has a resting protective stop at the broker.
    Contract v4 (on-box 2026-07-27): an INDEPENDENT pair — Sierra's DTC attach semantics are
    unusable on the live path, and the pair is geometrically safe (the stop sits on the loss
    side of the entry, so it cannot trigger without the entry filling first)."""
    s = MockDTCServer(order_mode="fill")
    try:
        c = _client(s)
        c.connect()
        oid = c.submit_bracket(symbol="NQ", buy=True, entry=100.0, stop=99.0, qty=2)
        entry_oid, stop_oid = c.last_bracket
        assert entry_oid == oid
        for _ in range(10):
            c.pump(timeout=0.2)
        c.close()
        stop = next(o for o in s.orders if o["ClientOrderID"] == stop_oid)
        assert stop["OrderType"] == D.ORDER_TYPE_STOP, (
            "NAKED ENTRY: no protective stop submitted alongside the entry order")
        # opposite side (a long entry protects with a sell stop), on the loss side
        assert stop["BuySell"] == 2 and stop["Price1"] == 99.0
        entry = next(o for o in s.orders if o["ClientOrderID"] == entry_oid)
        assert stop["Price1"] < entry["Price1"]        # the geometric-safety precondition
    finally:
        s.stop()


def test_heartbeat_roundtrip():
    s = MockDTCServer()
    try:
        c = _client(s)
        c.connect()
        c.send_heartbeat()
        for _ in range(5):
            c.pump(timeout=0.2)
        assert c.server_hb >= 1 and c.server_stale(expected_beats=1) is False
        c.close()
    finally:
        s.stop()


def test_reconnect_after_drop():
    s = MockDTCServer()
    try:
        c = _client(s)
        c.connect()
        c.subscribe_depth("NQ")
        # force a drop: close the client socket underneath, then ensure_connected reconnects
        c._sock.close()
        assert c.ensure_connected() is True and c.logged_on is True
        assert ("NQ" in [sym for _, sym in c._subs])                 # re-subscribed
        c.close()
    finally:
        s.stop()


# ---------------------------------------------------------------- B7/B8 order surface

def _pump(c, n=10):
    for _ in range(n):
        c.pump(timeout=0.2)


def test_broker_cancel_tears_down_the_whole_bracket():
    """B7: cancelling the unfilled entry must also cancel the protective stop. Under the
    independent-pair contract the teardown lives in DTCBroker.cancel_order (nothing at the
    server links the legs) — a cancel that left the stop resting would leave a naked stop
    that can open a position from flat."""
    from src.desk.dtc_broker import DTCBroker

    class _I:
        side, order_type, entry_ref, stop, target, size, setup_id, account = \
            "B", "limit", 100.0, 99.0, None, 2, "s1", "ACC"

    s = MockDTCServer(order_mode="none")           # stays OPEN, never fills
    try:
        c = _client(s)
        c.connect()
        b = DTCBroker(client=c, symbol="NQ", account="ACC")
        ref = b.submit_bracket(_I())
        stop_oid = c.last_bracket[1]
        b.cancel_order(ref)
        _pump(c)
        c.close()
        assert ref in s.cancelled and stop_oid in s.cancelled
        # the client's read-back surface saw both CANCELED updates
        assert c.order_state[ref]["OrderStatus"] == D.ORDER_STATUS_CANCELED
        assert c.order_state[stop_oid]["OrderStatus"] == D.ORDER_STATUS_CANCELED
    finally:
        s.stop()


def test_cancel_sends_the_server_order_id_from_readback():
    """Sierra keys cancels on the ServerOrderID; the client must remember it from the
    ORDER_UPDATE and send it, not just the client id."""
    s = MockDTCServer(order_mode="none")
    try:
        c = _client(s)
        c.connect()
        oid = c.submit_bracket(symbol="NQ", buy=True, entry=100.0, stop=99.0, qty=2)
        _pump(c)
        assert c.order_state[oid].get("ServerOrderID") is not None
        c.cancel_order(oid)
        _pump(c)
        c.close()
        assert oid in s.cancelled
    finally:
        s.stop()


def test_cancel_of_unknown_order_is_rejected_loudly_not_absorbed():
    s = MockDTCServer(order_mode="none")
    updates = []
    try:
        c = _client(s, on_order_update=updates.append)
        c.connect()
        c.cancel_order("desk-does-not-exist")
        _pump(c)
        c.close()
        assert "desk-does-not-exist" in s.cancel_rejects
        assert any("cancel rejected" in u.get("InfoText", "") for u in updates)
    finally:
        s.stop()


def test_modify_order_price_moves_the_resting_stop_in_place():
    """B8: the managed exit's BE move / V8 trail = CANCEL_REPLACE on the stop child —
    modified in place, never cancel-then-resubmit (that gap would leave the position
    unprotected, violating B4)."""
    s = MockDTCServer(order_mode="none")
    try:
        c = _client(s)
        c.connect()
        c.submit_bracket(symbol="NQ", buy=True, entry=100.0, stop=99.0, qty=2)
        _pump(c)
        stop_oid = c.last_bracket[1]
        c.modify_order_price(stop_oid, 99.75, qty=2)      # BE-ward move
        _pump(c)
        c.close()
        assert s.order_by_oid(stop_oid)["Price1"] == 99.75
        assert s.replaced and s.replaced[0]["ClientOrderID"] == stop_oid
        assert c.order_state[stop_oid]["Price1"] == 99.75  # read-back confirms the move
    finally:
        s.stop()


def test_modify_of_unknown_order_is_rejected():
    s = MockDTCServer(order_mode="none")
    try:
        c = _client(s)
        c.connect()
        c.modify_order_price("desk-ghost", 101.0, qty=1)
        _pump(c)
        c.close()
        assert "desk-ghost" in s.cancel_rejects
    finally:
        s.stop()


def test_submit_reduce_market_closes_and_always_fills():
    """The 3-min cut / EOD flatten path: a MARKET reducing order (OpenOrClose=close) must
    fill regardless of the server's scenario mode — an exit can never depend on the same
    luck as an entry."""
    s = MockDTCServer(order_mode="reject")          # entries would reject in this mode...
    try:
        c = _client(s)
        c.connect()
        oid = c.submit_reduce(symbol="NQ", sell=True, qty=2)   # ...but the market close fills
        _pump(c)
        c.close()
        row = s.order_by_oid(oid)
        assert row["OrderType"] == D.ORDER_TYPE_MARKET and row["OpenOrClose"] == 2
        assert c.order_state[oid]["OrderStatus"] == D.ORDER_STATUS_FILLED
    finally:
        s.stop()


def test_submit_reduce_with_price_rests_as_a_limit():
    """A target-style partial rests as a limit (B2: entries limit-only; exits may rest)."""
    s = MockDTCServer(order_mode="none")
    try:
        c = _client(s)
        c.connect()
        oid = c.submit_reduce(symbol="NQ", sell=True, qty=1, price=104.5)
        _pump(c)
        c.close()
        row = s.order_by_oid(oid)
        assert row["OrderType"] == D.ORDER_TYPE_LIMIT and row["Price1"] == 104.5
        assert row["OpenOrClose"] == 2
    finally:
        s.stop()
