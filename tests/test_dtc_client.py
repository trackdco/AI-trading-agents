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


class MockDTCServer:
    def __init__(self, order_mode: str = "fill"):
        self.order_mode = order_mode
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
        elif t == D.SUBMIT_NEW_SINGLE_ORDER:
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
