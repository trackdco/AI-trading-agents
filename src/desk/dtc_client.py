"""DTC client for Sierra Chart (LIVE-STACK Step 3/6) — the execution+data transport.

Speaks DTC (Data and Trading Communications, Sierra Chart's open TCP protocol) in the
**JSON-compact** encoding: each message is a JSON object with an integer `Type`, terminated
by a NUL byte. Covers what the desk needs:

  * logon + heartbeat (with server-heartbeat staleness detection)
  * market-data subscription (trades) + MBP-10 market-depth subscription
  * account balance + current positions queries
  * LIMIT-bracket order submission (entry limit + stop + target)
  * reconnect (re-logon + re-subscribe) on a dropped connection

Host/port/credentials are CONFIG (`DTCConfig`), so pointing at the real Sierra box is a
config change, not a code change. The socket connector is injectable, so the whole client
is tested end-to-end against a mock DTC server (tests/test_dtc_client.py) with no real
Sierra: reconnect, stale heartbeat, partial fill, and rejected order.
"""
from __future__ import annotations

import json
import socket
import struct
from collections.abc import Callable
from dataclasses import dataclass, field

# --- DTC message types (subset; standard DTC numbering) ---------------------
ENCODING_REQUEST = 6
ENCODING_RESPONSE = 7
LOGON_REQUEST = 1
LOGON_RESPONSE = 2
HEARTBEAT = 3
LOGOFF = 5
MARKET_DATA_REQUEST = 101
MARKET_DATA_REJECT = 103
MARKET_DATA_SNAPSHOT = 104
MARKET_DATA_UPDATE_TRADE = 107
MARKET_DEPTH_REQUEST = 102
MARKET_DEPTH_SNAPSHOT_LEVEL = 122
MARKET_DEPTH_UPDATE_LEVEL = 123
SUBMIT_NEW_SINGLE_ORDER = 208
SUBMIT_NEW_OCO_ORDER = 201          # the two exit legs as a linked OCO pair (DTC bracket path)
CANCEL_ORDER = 203                  # s_CancelOrder — pull ONE working order (B7)
CANCEL_REPLACE_ORDER = 204          # s_CancelReplaceOrder — modify a working order in place (B8)
ORDER_UPDATE = 301
CURRENT_POSITIONS_REQUEST = 305
POSITION_UPDATE = 306
ACCOUNT_BALANCE_REQUEST = 601
ACCOUNT_BALANCE_UPDATE = 600

# DTC OrderStatusEnum — the REAL protocol numbering (DTCProtocol.h). Pinned 2026-07-27
# pre-London after the on-box forcetest read an entry cancel as status 8 while our guessed
# CANCELED was 6 — the depth Command-enum bug's twin. PENDING_CHILD is the state a bracket's
# protective-stop child is HELD in at the server until its parent fills; it counts as
# resting (the server releases it on fill), and the old constants had no such state at all.
ORDER_STATUS_ORDER_SENT = 1
ORDER_STATUS_PENDING_OPEN = 2
ORDER_STATUS_PENDING_CHILD = 3
ORDER_STATUS_OPEN = 4
ORDER_STATUS_PENDING_CANCEL_REPLACE = 5
ORDER_STATUS_PENDING_CANCEL = 6
ORDER_STATUS_FILLED = 7
ORDER_STATUS_CANCELED = 8
ORDER_STATUS_REJECTED = 9
ORDER_STATUS_PARTIALLY_FILLED = 10
#: statuses meaning the order EXISTS at (or is en route to) the broker — the set the
#: stop_resting read-back and every "still working?" check is defined over. Filled,
#: canceled, rejected and pending-cancel are OUT (gone or deliberately dying).
ORDER_ALIVE_STATUSES = frozenset({
    ORDER_STATUS_ORDER_SENT, ORDER_STATUS_PENDING_OPEN, ORDER_STATUS_PENDING_CHILD,
    ORDER_STATUS_OPEN, ORDER_STATUS_PENDING_CANCEL_REPLACE, ORDER_STATUS_PARTIALLY_FILLED,
})
ORDER_TYPE_MARKET = 1
ORDER_TYPE_LIMIT = 2
ORDER_TYPE_STOP = 3                 # protective stop child (attached via ParentTriggerClientOrderID)
JSON_ENCODING = 2


@dataclass
class DTCConfig:
    host: str = "127.0.0.1"
    port: int = 11099
    username: str = ""
    password: str = ""
    trade_account: str = ""
    heartbeat_s: int = 10


def _tcp_connect(host: str, port: int, timeout: float = 5.0) -> socket.socket:
    return socket.create_connection((host, port), timeout=timeout)


@dataclass
class DTCClient:
    cfg: DTCConfig
    connector: Callable[[str, int], socket.socket] = _tcp_connect
    on_trade: Callable[[dict], None] | None = None
    on_depth: Callable[[dict], None] | None = None
    on_order_update: Callable[[dict], None] | None = None
    on_position: Callable[[dict], None] | None = None
    on_reject: Callable[[dict], None] | None = None      # MARKET_DATA_REJECT etc.

    _sock: socket.socket | None = field(default=None, init=False)
    _rxbuf: bytes = field(default=b"", init=False)
    logged_on: bool = field(default=False, init=False)
    server_hb: int = field(default=0, init=False)          # count of server heartbeats seen
    rejects: list[dict] = field(default_factory=list, init=False)   # MARKET_DATA_REJECT messages
    _subs: list[tuple[int, str]] = field(default_factory=list, init=False)
    _next_id: int = field(default=1, init=False)
    # last ORDER_UPDATE per ClientOrderID — the read-back surface (B4/A7) and the source of
    # ServerOrderID for cancel/modify (Sierra keys cancels on the SERVER id when it has one).
    order_state: dict = field(default_factory=dict, init=False)

    # ---- framing -----------------------------------------------------------
    def _send(self, mtype: int, fields: dict) -> None:
        msg = json.dumps({"Type": mtype, **fields}).encode() + b"\x00"
        self._sock.sendall(msg)

    def _recv_messages(self, timeout: float = 1.0) -> list[dict]:
        self._sock.settimeout(timeout)
        try:
            chunk = self._sock.recv(65536)
        except TimeoutError:
            return []
        if not chunk:
            raise ConnectionError("DTC connection closed by peer")
        self._rxbuf += chunk
        out = []
        while b"\x00" in self._rxbuf:
            raw, self._rxbuf = self._rxbuf.split(b"\x00", 1)
            if raw:
                out.append(json.loads(raw.decode()))
        return out

    def _recv_exact(self, n: int, timeout: float = 5.0) -> bytes:
        self._sock.settimeout(timeout)
        while len(self._rxbuf) < n:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise ConnectionError("DTC connection closed during handshake")
            self._rxbuf += chunk
        out, self._rxbuf = self._rxbuf[:n], self._rxbuf[n:]
        return out

    # ---- connect / logon ---------------------------------------------------
    def connect(self) -> bool:
        self._sock = self.connector(self.cfg.host, self.cfg.port)
        self._rxbuf = b""
        # The ENCODING_REQUEST/RESPONSE are ALWAYS binary in DTC; only after the encoding is
        # negotiated do subsequent messages use JSON. (Sierra drops the link if the encoding
        # request arrives as JSON.) Binary layout: <u16 Size><u16 Type><i32 ProtoVer><i32
        # Encoding><char[4] ProtocolType>.
        self._sock.sendall(struct.pack("<HHii4s", 16, ENCODING_REQUEST, 8,
                                       JSON_ENCODING, b"DTC\x00"))
        _size, rtype, _ver, _enc = struct.unpack("<HHii", self._recv_exact(16)[:12])
        if rtype != ENCODING_RESPONSE:
            raise ConnectionError(f"expected ENCODING_RESPONSE, got type {rtype}")
        # from here on, JSON:
        self._send(LOGON_REQUEST, {"ProtocolVersion": 8, "Username": self.cfg.username,
                                   "Password": self.cfg.password, "ClientName": "nqdesk",
                                   "HeartbeatIntervalInSeconds": self.cfg.heartbeat_s,
                                   "TradeAccount": self.cfg.trade_account})
        for msg in self._await(LOGON_RESPONSE, timeout=5.0):
            if msg["Type"] == LOGON_RESPONSE:
                self.logged_on = int(msg.get("Result", 0)) == 1
        return self.logged_on

    def _await(self, mtype: int, timeout: float = 3.0) -> list[dict]:
        """Pump until a message of `mtype` arrives (or timeout); dispatch the rest."""
        seen = []
        for _ in range(200):
            msgs = self._recv_messages(timeout=timeout)
            if not msgs:
                break
            for m in msgs:
                self._dispatch(m)
                seen.append(m)
            if any(m["Type"] == mtype for m in msgs):
                break
        return seen

    # ---- subscriptions -----------------------------------------------------
    def subscribe_market_data(self, symbol: str) -> None:
        sid = self._sym_id(MARKET_DATA_REQUEST, symbol)
        self._send(MARKET_DATA_REQUEST, {"RequestAction": 1, "SymbolID": sid, "Symbol": symbol})

    def subscribe_depth(self, symbol: str) -> None:
        sid = self._sym_id(MARKET_DEPTH_REQUEST, symbol)
        self._send(MARKET_DEPTH_REQUEST, {"RequestAction": 1, "SymbolID": sid, "Symbol": symbol})

    def _sym_id(self, kind: int, symbol: str) -> int:
        self._subs.append((kind, symbol))
        return len(self._subs)

    # ---- queries -----------------------------------------------------------
    def positions(self, timeout: float = 3.0) -> list[dict]:
        self._send(CURRENT_POSITIONS_REQUEST, {"TradeAccount": self.cfg.trade_account,
                                               "RequestID": self._rid()})
        return [m for m in self._await(POSITION_UPDATE, timeout) if m["Type"] == POSITION_UPDATE]

    def account_balance(self, timeout: float = 3.0) -> dict | None:
        self._send(ACCOUNT_BALANCE_REQUEST, {"TradeAccount": self.cfg.trade_account,
                                             "RequestID": self._rid()})
        got = [m for m in self._await(ACCOUNT_BALANCE_UPDATE, timeout)
               if m["Type"] == ACCOUNT_BALANCE_UPDATE]
        return got[-1] if got else None

    # ---- orders ------------------------------------------------------------
    def submit_bracket(self, *, symbol: str, buy: bool, entry: float, stop: float,
                       qty: int, target: float | None = None) -> str:
        """LIMIT entry + a SIMULTANEOUSLY-RESTING protective stop — two plain orders.

        HISTORY (all found on-box): v1 sent Stop/Target as fields Sierra silently dropped —
        naked entry. v2 linked a child via ParentTriggerClientOrderID — not a DTC single-order
        field; Sierra routed the stop INDEPENDENTLY. v3 added IsParentOrder=1 — Sierra held
        the parent forever (no ack) and still routed the stop independently. Sierra-side
        attach semantics over DTC are not usable on this path (2026-07-27, Rithmic).

        v4 (this): embrace the independent pair, whose safety is GEOMETRIC — the protective
        stop always sits on the LOSS side of the entry (buy: stop < entry; sell: stop >
        entry), so the market cannot reach the stop's trigger without first trading THROUGH
        the entry limit, filling it. The stop can never fire while flat. The one non-
        geometric hole — ONE leg rejected — is closed by the caller (DTCBroker.submit_bracket
        pumps and cancels the survivor). Uses only primitives PROVEN against live Rithmic
        paper: single limit, single stop, cancel, modify. `target` accepted but never rested
        (the canon's exit is managed). Returns the entry oid; pair on `self.last_bracket`."""
        entry_oid = f"desk-{self._next_id}"
        self._next_id += 1
        stop_oid = f"desk-{self._next_id}"
        self._next_id += 1
        self.last_bracket = (entry_oid, stop_oid)
        self._send(SUBMIT_NEW_SINGLE_ORDER, {                        # the limit entry
            "Symbol": symbol, "TradeAccount": self.cfg.trade_account,
            "ClientOrderID": entry_oid, "OrderType": ORDER_TYPE_LIMIT,
            "BuySell": 1 if buy else 2, "Price1": entry, "Quantity": qty, "IsAutomated": True})
        self._send(SUBMIT_NEW_SINGLE_ORDER, {                        # the protective stop (opp side)
            "Symbol": symbol, "TradeAccount": self.cfg.trade_account,
            "ClientOrderID": stop_oid, "OrderType": ORDER_TYPE_STOP,
            "BuySell": 2 if buy else 1, "Price1": stop, "Quantity": qty, "IsAutomated": True})
        return entry_oid

    def cancel_order(self, client_order_id: str) -> None:
        """Pull ONE working order (DTC CANCEL_ORDER) — the primitive gate B7 needs for the
        cancel-if-runs rule. Sends the ServerOrderID when a prior ORDER_UPDATE supplied one
        (Sierra keys cancels on it); the ClientOrderID rides along always. Confirmation is an
        ORDER_UPDATE with ORDER_STATUS_CANCELED — the caller VERIFIES via order_state, never
        trusts the send (same no-trust rule as submit)."""
        f = {"ClientOrderID": client_order_id, "TradeAccount": self.cfg.trade_account}
        srv = self.order_state.get(client_order_id, {}).get("ServerOrderID")
        if srv:                                  # "" from an early sparse update is missing
            f["ServerOrderID"] = srv
        self._send(CANCEL_ORDER, f)

    def modify_order_price(self, client_order_id: str, new_price: float, qty: int) -> None:
        """Modify a WORKING order in place (DTC CANCEL_REPLACE_ORDER) — the primitive gate B8
        needs so the managed exit can move the protective stop (BE move, V8 trail) without a
        cancel+resubmit gap during which the position would sit unprotected. `qty` must restate
        the working quantity (DTC requires it; a modify never changes size here)."""
        f = {"ClientOrderID": client_order_id, "TradeAccount": self.cfg.trade_account,
             "Price1": new_price, "Quantity": qty}
        srv = self.order_state.get(client_order_id, {}).get("ServerOrderID")
        if srv:                                  # "" from an early sparse update is missing
            f["ServerOrderID"] = srv
        self._send(CANCEL_REPLACE_ORDER, f)

    def submit_reduce(self, *, symbol: str, sell: bool, qty: int,
                      price: float | None = None) -> str:
        """A position-REDUCING order (OpenOrClose=close): market when `price` is None (3-min
        cut, EOD flatten, stop-outs — the exits the canon takes at market), else a limit (a
        target-style partial rests). This is the B8 partial-close / close primitive; it can
        only reduce, the spine never uses it to open risk."""
        oid = f"desk-{self._next_id}"
        self._next_id += 1
        f = {"Symbol": symbol, "TradeAccount": self.cfg.trade_account,
             "ClientOrderID": oid, "BuySell": 2 if sell else 1, "Quantity": qty,
             "IsAutomated": True, "OpenOrClose": 2,
             "OrderType": ORDER_TYPE_MARKET if price is None else ORDER_TYPE_LIMIT}
        if price is not None:
            f["Price1"] = price
        self._send(SUBMIT_NEW_SINGLE_ORDER, f)
        return oid

    # ---- heartbeat / liveness ---------------------------------------------
    def send_heartbeat(self) -> None:
        self._send(HEARTBEAT, {"CurrentDateTime": 0})

    def server_stale(self, expected_beats: int) -> bool:
        """True if the server has sent fewer heartbeats than expected (feed/link stalled)."""
        return self.server_hb < expected_beats

    # ---- pump / reconnect --------------------------------------------------
    def pump(self, timeout: float = 0.2) -> int:
        n = 0
        for m in self._recv_messages(timeout=timeout):
            self._dispatch(m)
            n += 1
        return n

    def ensure_connected(self) -> bool:
        """Reconnect + re-logon + re-subscribe after a drop. Idempotent."""
        try:
            self.send_heartbeat()
            return True
        except OSError:
            subs, self.logged_on = list(self._subs), False
            self._subs = []
            if not self.connect():
                return False
            for kind, sym in subs:
                (self.subscribe_market_data if kind == MARKET_DATA_REQUEST
                 else self.subscribe_depth)(sym)
            return True

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._send(LOGOFF, {"Reason": "client close"})
            except OSError:
                pass
            self._sock.close()
            self._sock = None

    # ---- dispatch ----------------------------------------------------------
    def _rid(self) -> int:
        self._next_id += 1
        return self._next_id

    def _dispatch(self, m: dict) -> None:
        t = m["Type"]
        if t == HEARTBEAT:
            self.server_hb += 1
        elif t == MARKET_DATA_REJECT:
            self.rejects.append(m)
            if self.on_reject:
                self.on_reject(m)
        elif t in (MARKET_DATA_SNAPSHOT, MARKET_DATA_UPDATE_TRADE) and self.on_trade:
            self.on_trade(m)
        elif t in (MARKET_DEPTH_SNAPSHOT_LEVEL, MARKET_DEPTH_UPDATE_LEVEL) and self.on_depth:
            self.on_depth(m)
        elif t == ORDER_UPDATE:
            oid = m.get("ClientOrderID")
            if oid is not None:
                # MERGE, skipping null/empty: real Sierra sends SPARSE updates — a later
                # update carrying Price1/ServerOrderID as JSON null (or "") must never
                # clobber a real value learned earlier (on-box 2026-07-27: Price1=None
                # after CANCEL_REPLACE, ServerOrderIDs read back as '').
                self.order_state.setdefault(oid, {}).update(
                    {k: v for k, v in m.items() if v is not None and v != ""})
            if self.on_order_update:
                self.on_order_update(m)
        elif t == POSITION_UPDATE and self.on_position:
            self.on_position(m)
