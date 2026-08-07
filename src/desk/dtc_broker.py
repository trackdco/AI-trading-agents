"""DTCBroker — the spine's Broker protocol implemented over the DTC client (B7/B8 bridge).

This is the adapter that lets `SpineExecutor` drive a REAL Sierra DTC server: it maps the
spine's yes-only surface onto `DTCClient` calls and the client's `order_state` read-back.
Until it exists the protocol had mock implementers only — every armed-path primitive
(submit, cancel-one, modify-stop, partial close, flatten) now has a real transport.

Design rules, same as everywhere else in the trade path:

  * READ-BACK, NEVER TRUST. `order_status()` is built from ORDER_UPDATE messages the
    server actually sent (client.order_state), not from what we submitted. The spine's
    `_verify_readback` (B4: the resting protective stop) consumes exactly this.
  * RISK-REDUCING ONLY beyond submit_bracket: cancel/modify/close can never open or
    increase a position. `close_partial` clamps to the live position size.
  * PUMP AFTER EVERY SEND. DTC confirmations arrive as async ORDER_UPDATEs; each call
    pumps the socket so state is current before anyone reads it back.

The canon trades NQ data but routes MICROS (MNQ) — `symbol` here is the ORDER symbol
(e.g. "MNQU26-CME"), resolved by the caller (RollWatcher owns the contract month).

Verified end-to-end against the mock Sierra in tests/test_dtc_broker.py; the on-box A7/B7/B8
checks re-run the same sequences against the real server (docs/PROMOTION-GATE.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.desk import dtc_client as D
from src.desk.dtc_client import DTCClient


@dataclass
class DTCBroker:
    client: DTCClient
    symbol: str                                   # ORDER symbol (micros contract)
    account: str
    pump_rounds: int = 6                          # socket pumps after each send (mock+box safe)
    # ORDER price scale, service units per display point. Pat's VPS runs its Rithmic feed at
    # 100x display (first found in the .depth files, then confirmed on the ORDER path
    # 2026-07-27: DTC Price1=28690 landed at Sierra as 286.90 -> Rithmic 'bad price' on
    # every limit). All broker inputs/outputs are DISPLAY prices; this adapter multiplies
    # on the way out and divides on the way back. 1.0 = pass-through (mock, normal boxes).
    price_scale: float = 1.0

    # entry ref -> {stop_oid, intent-side/size/prices} — the bracket book this adapter placed
    _brackets: dict = field(default_factory=dict, init=False)

    # ---- helpers ------------------------------------------------------------
    def _pump(self) -> None:
        for _ in range(self.pump_rounds):
            self.client.pump(timeout=0.2)

    def ensure_connected(self) -> bool:
        """Idle keepalive — the fix for the 2026-08-02/03 armed-session incidents. Every
        `_pump()` above only fires from ORDER ACTIVITY (submit/cancel/status/position), so
        a quiet market leaves the socket completely untouched: no heartbeat out, nothing
        read back, for as long as nothing trades. Whatever reaps idle sockets on the box
        (Sierra's own idle timeout, a firewall, the OS) does so with nobody watching, and
        the NEXT real order discovers a corpse. `DTCClient.ensure_connected()` already
        exists and is already tested (test_reconnect_after_drop) — it was simply never
        called on a cadence independent of trading. The live loop calls THIS every few
        seconds regardless of activity; that's the entire fix. Returns False on a failed
        reconnect attempt (caller alerts; never raises — a dead socket must never crash
        the loop, only slow it down to journaled warnings)."""
        try:
            return self.client.ensure_connected()
        except Exception:                          # noqa: BLE001 — never crash the loop
            return False

    def _state(self, oid: str) -> dict:
        return self.client.order_state.get(oid, {})

    def _unscale(self, v, fallback):
        """Server price -> display price; None -> the tracked fallback (already display)."""
        return fallback if v is None else float(v) / self.price_scale

    @staticmethod
    def _coalesce(*vals):
        """First non-None value. Real Sierra sends fields PRESENT with JSON null on resting
        orders (FilledQuantity, AverageFillPrice — found on-box 2026-07-27, int(None)
        crash); dict.get's default only covers ABSENT keys, so nulls must be skipped
        explicitly."""
        for v in vals:
            if v is not None:
                return v
        return None

    @staticmethod
    def _working(st: dict) -> bool:
        """Alive at the broker — includes PENDING_CHILD: a bracket's protective-stop child
        is HELD server-side until its parent fills, and that held stop IS the resting
        protection B4 verifies (on-box 2026-07-27: it read False under the old two-status
        check and the spine would have flatten+halted a perfectly protected bracket)."""
        return st.get("OrderStatus") in D.ORDER_ALIVE_STATUSES

    @staticmethod
    def _dead(st: dict) -> bool:
        """Terminal-bad: the server reported SOME status, and it's neither alive nor a
        genuine fill. Deliberately NOT limited to ORDER_STATUS_REJECTED (2026-08-05
        incident): Sierra's own Trade Orders window showed two stop legs as "Error", a
        label the DTC protocol's OrderStatusEnum has no distinct numeric code for — the old
        REJECTED-only check never saw them, and the paired entry was left free to fill with
        no protection. Whitelisting "known good" (alive-or-filled) instead of blacklisting
        one specific "known bad" code catches this failure and any future one Sierra
        reports that hasn't been seen yet. `status is not None` guards a leg with no
        update at all yet — absence of news is not itself bad news."""
        status = st.get("OrderStatus")
        return status is not None and status not in D.ORDER_ALIVE_STATUSES \
            and status != D.ORDER_STATUS_FILLED

    # ---- Broker protocol ----------------------------------------------------
    def submit_bracket(self, intent) -> str:
        ref = self.client.submit_bracket(
            symbol=self.symbol, buy=(intent.side == "B"),
            entry=float(intent.entry_ref) * self.price_scale,
            stop=float(intent.stop) * self.price_scale, qty=int(intent.size))
        entry_oid, stop_oid = self.client.last_bracket
        self._brackets[ref] = {"stop_oid": stop_oid, "side": intent.side,
                               "size": int(intent.size), "entry": float(intent.entry_ref),
                               "stop": float(intent.stop), "account": intent.account}
        self._pump()
        # PAIRING ENFORCEMENT (the one hole in the independent-pair geometry): the pair is
        # only safe if BOTH legs live. A dead leg with a working partner is either a naked
        # entry (no protection) or a naked stop (can open a position from flat) — cancel
        # the survivor immediately. A dead ENTRY is never a reason to pull a working stop's
        # partner-check the other way: a FILLED entry is a healthy pair (position +
        # protective stop), never treated as dead here.
        entry_st, stop_st = self._state(ref), self._state(stop_oid)
        entry_dead, stop_dead = self._dead(entry_st), self._dead(stop_st)
        entry_filled = entry_st.get("OrderStatus") == D.ORDER_STATUS_FILLED
        if entry_dead and self._working(stop_st):
            self.client.cancel_order(stop_oid)
            self._pump()
        elif stop_dead and entry_filled:
            # the entry is ALREADY a real position with no protection — cancelling a fill
            # is not possible; the only safe response left is to flatten it now.
            self.flatten(intent.account)
        elif stop_dead and self._working(entry_st):
            self.client.cancel_order(ref)
            self._pump()
        return ref

    def order_status(self, ref: str) -> dict:
        """The spine's read-back shape, built from what the SERVER said (order_state):
        {entry, stop, size, side, account, stop_resting}. `stop_resting` is true only if
        the stop child's own ORDER_UPDATE shows it working — a dropped/naked stop reads
        False and _verify_readback flattens+halts (B4)."""
        b = self._brackets.get(ref)
        if b is None:
            return {}
        self._pump()
        entry_st, stop_st = self._state(ref), self._state(b["stop_oid"])
        return {
            # the readback verifies the ORDER AS PLACED (intent.entry_ref == the limit
            # price == Price1); AverageFillPrice is null while resting and can differ on
            # an IMPROVED fill, which must never read as a mismatch
            "entry": self._unscale(self._coalesce(entry_st.get("Price1"),
                                                  entry_st.get("AverageFillPrice")), b["entry"]),
            "stop": self._unscale(self._coalesce(stop_st.get("Price1"), stop_st.get("Price2")),
                                  b["stop"]),
            # order quantity, not filled quantity — a resting entry has FilledQuantity 0/null.
            # Real Sierra's ORDER_UPDATE names it OrderQuantity (observed 2026-07-27).
            "size": int(self._coalesce(entry_st.get("OrderQuantity"), entry_st.get("Quantity"),
                                       entry_st.get("FilledQuantity"), b["size"])),
            "side": b["side"], "account": b["account"],
            "stop_resting": self._working(stop_st),
        }

    def position(self, account: str) -> int:
        """Net position from a live CURRENT_POSITIONS query. The request is scoped to the
        configured TradeAccount, so this is the account's net — the one-position-at-a-time
        rule means account net == this symbol's net; the spine's reconcile keeps it honest."""
        return sum(int(self._coalesce(p.get("Quantity"), 0)) for p in self.client.positions())

    def cancel_order(self, ref: str) -> None:
        """B7: pull one working bracket. The server tears children down with the parent
        (verified against the mock; re-verified on box), but the tracked stop child is
        cancelled explicitly too — a cancel-reject on an already-dead child is harmless
        and journaled server-side, while a surviving naked stop child is not."""
        self.client.cancel_order(ref)
        b = self._brackets.get(ref)
        if b is not None:
            self._pump()
            if self._working(self._state(b["stop_oid"])):
                self.client.cancel_order(b["stop_oid"])
        self._pump()

    def modify_stop(self, ref: str, price: float) -> None:
        """B8: move the RESTING protective stop in place (CANCEL_REPLACE) — BE move and V8
        trail. Never cancel+resubmit: that gap is a naked position. Raises if the bracket
        is unknown (modifying an untracked stop would be acting on a position this adapter
        never placed — fail closed, the spine treats the raise as flatten+halt)."""
        b = self._brackets.get(ref)
        if b is None:
            raise KeyError(f"modify_stop: unknown bracket ref {ref!r}")
        st = self._state(b["stop_oid"])
        qty = int(self._coalesce(st.get("RemainingQuantity"), st.get("Quantity"), b["size"]))
        self.client.modify_order_price(b["stop_oid"], float(price) * self.price_scale, qty=qty)
        self._pump()

    def close_partial(self, account: str, qty: int, *, price: float | None = None) -> str:
        """B8: reduce the open position — V8 partial (limit at `price`) or cut/EOD (market).
        Clamped to the live position so it can NEVER flip or open risk; qty<=0 after the
        clamp is a no-op returning ''."""
        pos = self.position(account)
        if pos == 0:
            return ""
        q = min(int(qty), abs(pos))
        if q <= 0:
            return ""
        oid = self.client.submit_reduce(symbol=self.symbol, sell=(pos > 0), qty=q,
                                        price=(None if price is None
                                               else float(price) * self.price_scale))
        self._pump()
        return oid

    def cancel_all(self, account: str) -> None:
        for ref in list(self._brackets):
            b = self._brackets[ref]
            for oid in (ref, b["stop_oid"]):
                if self._working(self._state(oid)):
                    self.client.cancel_order(oid)
        self._pump()

    def flatten(self, account: str) -> None:
        """Kill-path: cancel every working order, then market-close the whole position.
        Order matters — cancelling first ensures a resting stop can't double-fill against
        the market close."""
        self.cancel_all(account)
        pos = self.position(account)
        if pos != 0:
            self.client.submit_reduce(symbol=self.symbol, sell=(pos > 0), qty=abs(pos))
        self._pump()
