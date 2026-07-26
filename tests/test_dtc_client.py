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

import pytest

from src.desk import dtc_client as D
from src.desk.dtc_client import DTCClient, DTCConfig


# The fields a real Sierra s_SubmitNewSingleOrder actually reads. Anything else (e.g. "Stop",
# "Target") is an UNKNOWN key that Sierra's JSON decoder DROPS silently — so the mock models
# that by keeping only these, exposing the naked-entry bug the old permissive mock hid.
_VALID_SUBMIT_FIELDS = {
    "Symbol", "TradeAccount", "ClientOrderID", "OrderType", "BuySell", "Price1", "Price2",
    "Quantity", "TimeInForce", "GoodTillDateTime", "IsAutomated", "OpenOrClose",
    "ParentTriggerClientOrderID", "FreeFormText",
}


class MockDTCServer:
    def __init__(self, order_mode: str = "fill"):
        self.order_mode = order_mode
        self.orders: list[dict] = []      # single orders received, DTC-valid fields only
        self.ocos: list[dict] = []        # SUBMIT_NEW_OCO_ORDER messages received
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
            self.orders.append(kept)
            oid = m["ClientOrderID"]
            self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid, OrderStatus=D.ORDER_STATUS_OPEN)
            if self.order_mode == "fill":
                self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid, OrderStatus=D.ORDER_STATUS_FILLED,
                           FilledQuantity=m["Quantity"], AverageFillPrice=m["Price1"])
            elif self.order_mode == "partial":
                self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid,
                           OrderStatus=D.ORDER_STATUS_PARTIALLY_FILLED,
                           FilledQuantity=max(1, m["Quantity"] // 2), RemainingQuantity=1)
            elif self.order_mode == "reject":
                self._send(conn, D.ORDER_UPDATE, ClientOrderID=oid,
                           OrderStatus=D.ORDER_STATUS_REJECTED, InfoText="risk rejected")
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


def test_submit_bracket_attaches_a_resting_protective_stop():
    """THE INVARIANT (Angus B4): every entry has a resting protective stop attached at the broker.
    submit_bracket now sends a parent entry + a STOP child linked by ParentTriggerClientOrderID."""
    s = MockDTCServer(order_mode="fill")
    try:
        c = _client(s)
        c.connect()
        oid = c.submit_bracket(symbol="NQ", buy=True, entry=100.0, stop=99.0, qty=2)
        for _ in range(10):
            c.pump(timeout=0.2)
        c.close()
        assert s.has_protective_stop(oid), (
            "NAKED ENTRY: no resting protective stop attached to the entry order")
        # the stop child is on the opposite side (a long entry protects with a sell stop)
        stop = next(o for o in s.children_of(oid) if o["OrderType"] == D.ORDER_TYPE_STOP)
        assert stop["BuySell"] == 2 and stop["Price1"] == 99.0
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
