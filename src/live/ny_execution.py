"""NYExecution — the R13 execution layer: the rebuilt canon's actions, actually sent.

This is the piece the arming review found missing (2026-07-31): `ny_run` decided
correctly but cancels, scratch-closes and the rule-K flatten were journal-only. This
module routes every runner action to a Broker and manages each filled position with the
canon's own V8 exit engine (`LiveExitExecutor` driving `ExitDriver` under the l2 config —
the SAME simulate() path the book's exits were measured with; `apply_close_reverse`
re-simulates pre trades through it, so this is the certified reference's engine).

Multi-position by design. The old canon's `TradeLifecycle` assumes one resting order and
one position (fill attribution = "first resting ref when account position != 0") — the
rebuilt canon stacks same-direction positions and rests several orders, so this layer
keys every order and position by the runner's ref and never infers from account net.

ROW I BY CONSTRUCTION: the legacy 3-minute cut is `LiveExitExecutor.maybe_cut`, an
opt-in method. This layer NEVER calls it — the rebuilt book was measured without it.

Fill detection:
  * DryRunBroker exposes `take_fills()` — exact refs, no inference.
  * A DTC broker is polled per resting ref via `order_status`: an entry that stopped
    working which we did not cancel is a fill (journaled with the read-back). This is the
    piece Saturday's on-box certification exercises against real Sierra order updates.

P&L: realized from the executor's executed legs — partial legs at `frac x size` and the
final exit at the action's price (stop exits at the canon stop), $2/pt per micro,
commission $5/position — the same arithmetic as the book. Reported to
`on_closed(ref, pl)` (the runner's budget realization) when the position completes.

KNOWN LIMITATION (flagged for cert): `LiveExitExecutor`'s stop-exit verification checks
account-level position != 0, which with STACKED positions can read another position's
size as "still open" and market-close conservatively. Fails toward flat — never toward
unmanaged exposure. Journaled whenever it can trigger (>1 concurrent position).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from src.canon.exit_live import LiveExitExecutor
from src.canon.spine import OrderIntent

TICK = 0.25
PV_MICRO = 2.0                          # $/pt per micro
COMMISSION = 5.0                        # $/position, the book's convention


class _Notes:
    def __init__(self, sink: Callable[[dict], None] | None, ref: str):
        self._sink, self._ref = sink, ref

    def note(self, text: str) -> None:
        if self._sink is not None:
            self._sink({"type": "exit_note", "ref": self._ref, "note": text})


# ------------------------------------------------------------------ dry-run broker
@dataclass
class DryRunBroker:
    """In-memory Broker for the certification practice day: real feed, simulated fills.

    Entry limits fill when the bar trades through them (long: low <= limit; short:
    high >= limit); stop children fire on touch, stop-first within a bar (conservative);
    market closes fill at the current close -/+ one tick of slip. Every fill is queued
    for `take_fills()` so attribution is exact.
    """
    account: str = "FUNDED"
    _orders: dict = field(default_factory=dict)      # ref -> bracket state
    _seq: int = field(default=0)
    _pos: int = field(default=0)                     # net micros, signed
    _last: dict = field(default_factory=dict)        # latest bar {high, low, close, ts}
    _fills: list = field(default_factory=list)       # queued {ref, ts, size}
    _stop_fires: list = field(default_factory=list)  # queued {ref, price, ts}

    def on_bar(self, ts, high: float, low: float, close: float) -> None:
        self._last = {"ts": ts, "high": float(high), "low": float(low),
                      "close": float(close)}
        for ref, o in list(self._orders.items()):
            if o["state"] == "working":
                hit = (low <= o["entry"] if o["side"] == "B" else high >= o["entry"])
                if hit:
                    o["state"] = "filled"
                    self._pos += o["size"] if o["side"] == "B" else -o["size"]
                    self._fills.append({"ref": ref, "ts": ts, "size": o["size"]})
            elif o["state"] == "filled" and o["stop_resting"]:
                # protective stop: opposite side of the entry, stop-first on touch
                stop_hit = (low <= o["stop"] if o["side"] == "B" else high >= o["stop"])
                if stop_hit:
                    o["stop_resting"] = False
                    o["state"] = "stopped"
                    self._pos -= o["size"] if o["side"] == "B" else -o["size"]
                    self._stop_fires.append({"ref": ref, "price": o["stop"], "ts": ts})

    def take_fills(self) -> list[dict]:
        out, self._fills = self._fills, []
        return out

    def take_stop_fires(self) -> list[dict]:
        out, self._stop_fires = self._stop_fires, []
        return out

    # ---- Broker protocol ----------------------------------------------------
    def submit_bracket(self, intent: OrderIntent) -> str:
        self._seq += 1
        ref = f"dry:{self._seq}"
        self._orders[ref] = {"entry": float(intent.entry_ref), "stop": float(intent.stop),
                             "size": int(intent.size), "side": intent.side,
                             "account": intent.account, "state": "working",
                             "stop_resting": True}
        return ref

    def order_status(self, ref: str) -> dict:
        o = self._orders.get(ref)
        if o is None:
            return {}
        return {"entry": o["entry"], "stop": o["stop"], "size": o["size"],
                "side": o["side"], "account": o["account"],
                "stop_resting": o["stop_resting"] and o["state"] in ("working", "filled")}

    def position(self, account: str) -> int:
        return self._pos

    def cancel_order(self, ref: str) -> None:
        o = self._orders.get(ref)
        if o is None:
            return
        if o["state"] == "working":
            o["state"] = "cancelled"
        o["stop_resting"] = False

    def modify_stop(self, ref: str, price: float) -> None:
        o = self._orders.get(ref)
        if o is not None and o["stop_resting"]:
            o["stop"] = float(price)

    def close_partial(self, account: str, qty: int, *, price: float | None = None) -> str:
        px = self._last.get("close", 0.0)
        fill = float(price) if price is not None else (px - TICK if self._pos > 0
                                                       else px + TICK)
        self._pos += -qty if self._pos > 0 else qty
        self._seq += 1
        self._fills.append({"ref": f"close:{self._seq}", "ts": self._last.get("ts"),
                            "size": qty, "price": fill, "closing": True})
        return f"close:{self._seq}"

    def cancel_all(self, account: str) -> None:
        for ref in list(self._orders):
            self.cancel_order(ref)

    def flatten(self, account: str) -> None:
        self.cancel_all(account)
        if self._pos != 0:
            self.close_partial(account, abs(self._pos))


# ------------------------------------------------------------------ execution layer
@dataclass
class NYExecution:
    """Routes runner actions to the broker and manages fills with the canon exit engine.

    `mode`: 'shadow' (no broker, journal only — tonight's loop), 'dryrun' (DryRunBroker,
    real feed + simulated fills — the certification practice day), 'armed' (real broker
    via the spine's armed path — only reachable once the R13 gate in ny_run comes off).
    """
    mode: str = "shadow"
    broker: object | None = None
    account: str = "FUNDED"
    exit_cfg: object | None = None                  # l2_cfg() — the canon exit config
    journal: Callable[[dict], None] | None = None
    on_closed: Callable[[str, float], None] | None = None   # (ref, realized $)

    _orders: dict = field(default_factory=dict, init=False)     # ref -> order record
    _positions: dict = field(default_factory=dict, init=False)  # ref -> position record

    def _note(self, row: dict) -> None:
        if self.journal is not None:
            self.journal({"layer": "ny_execution", **row})

    @property
    def live(self) -> bool:
        return self.mode in ("dryrun", "armed") and self.broker is not None

    # ---- runner action routing ---------------------------------------------
    def place(self, ref: str, intent: OrderIntent, trigger) -> bool:
        """Submit the bracket. Returns False when the submission failed (the caller must
        un-rest the runner's candidate so it can re-place on a later bar)."""
        rec = {"intent": intent, "trigger": trigger, "broker_ref": None,
               "cancelled": False}
        if self.live:
            try:
                rec["broker_ref"] = self.broker.submit_bracket(intent)
            except Exception as e:                 # noqa: BLE001 — journal, fail the place
                self._note({"type": "place_failed", "ref": ref, "error": repr(e)})
                return False
        self._orders[ref] = rec
        self._note({"type": "placed", "ref": ref, "broker_ref": rec["broker_ref"],
                    "mode": self.mode})
        return True

    def cancel(self, ref: str, why: str) -> None:
        rec = self._orders.pop(ref, None)
        if rec is None:
            return
        rec["cancelled"] = True
        if self.live and rec["broker_ref"] is not None:
            try:
                self.broker.cancel_order(rec["broker_ref"])
            except Exception as e:                 # noqa: BLE001
                self._note({"type": "cancel_failed", "ref": ref, "error": repr(e)})
                return
        self._note({"type": "cancelled", "ref": ref, "why": why, "mode": self.mode})

    def modify_size(self, ref: str, intent: OrderIntent, trigger) -> bool:
        """Cancel-and-replace — the only size change a resting bracket safely supports."""
        self.cancel(ref, "resize")
        return self.place(ref, intent, trigger)

    # ---- fills --------------------------------------------------------------
    def poll_fills(self) -> list[dict]:
        """Fills since the last poll as [{ref, ts, size}] in RUNNER refs."""
        if not self.live:
            return []
        out = []
        if hasattr(self.broker, "take_fills"):     # dry-run: exact attribution
            by_broker = {r["broker_ref"]: ref for ref, r in self._orders.items()
                         if r["broker_ref"] is not None}
            for f in self.broker.take_fills():
                if f.get("closing"):
                    continue
                ref = by_broker.get(f["ref"])
                if ref is not None:
                    out.append({"ref": ref, "ts": f["ts"], "size": f["size"]})
            return out
        # DTC path: an entry that stopped working which we did not cancel is a fill.
        for ref, rec in list(self._orders.items()):
            if rec["broker_ref"] is None or rec["cancelled"]:
                continue
            try:
                st = self.broker.order_status(rec["broker_ref"])
            except Exception as e:                 # noqa: BLE001
                self._note({"type": "status_poll_failed", "ref": ref, "error": repr(e)})
                continue
            if st and st.get("stop_resting") and not self._entry_working(rec, st):
                out.append({"ref": ref, "ts": pd.Timestamp.now(tz="UTC"),
                            "size": int(st.get("size", rec["intent"].size))})
        return out

    def _entry_working(self, rec, st) -> bool:
        """DTC read-back heuristic, certified on the box: a working entry keeps its
        limit as Price1; once filled the entry order leaves the working set. DTCBroker
        has no direct 'filled' flag in order_status, so the certification run pins the
        exact field behavior before this path ever arms."""
        try:
            probe = getattr(self.broker, "entry_working", None)
            if probe is not None:
                return bool(probe(rec["broker_ref"]))
        except Exception:                          # noqa: BLE001
            pass
        return False                               # conservative: treat as filled; the
                                                   # runner's fill-minute gate re-checks

    def confirm_fill(self, ref: str, verdict: dict, filled_size: int, pre: bool) -> None:
        """The runner committed this fill — bind the canon exit engine to the position."""
        rec = self._orders.pop(ref, None)
        exe = None
        if self.live and rec is not None and self.exit_cfg is not None:
            exe = LiveExitExecutor(
                broker=self.broker, ref=rec["broker_ref"], account=self.account,
                trigger=rec["trigger"], cfg=self.exit_cfg,
                canon_entry=float(verdict["entry"]), canon_stop=float(verdict["stop"]),
                size=int(filled_size), armed=True, journal=_Notes(self.journal, ref))
        self._positions[ref] = {
            "exe": exe, "entry": float(verdict["entry"]), "stop": float(verdict["stop"]),
            "side": "B" if verdict["direction"] == "long" else "S",
            "size": int(filled_size), "pre": pre, "legs": [],
            "broker_ref": rec["broker_ref"] if rec is not None else None}
        if len(self._positions) > 1:
            self._note({"type": "stacked_positions",
                        "note": "stop-exit verification is account-level in "
                                "LiveExitExecutor — fails toward flat (known limitation)"})

    def scratch_unconfirmed(self, ref: str, filled_size: int, why: str) -> None:
        """A fill landed but the runner REFUSED it (fill-minute gate or rule L) before
        any exit engine was bound: pull the bracket's stop child and market-close the
        just-filled quantity NOW. The scratch is the book's honest live price for the
        gated-at-fill idealisation — it must never ride on the resting stop alone."""
        rec = self._orders.pop(ref, None)
        if self.live and rec is not None and rec["broker_ref"] is not None:
            try:
                self.broker.cancel_order(rec["broker_ref"])    # stop down FIRST
                self.broker.close_partial(self.account, int(filled_size))
            except Exception as e:                 # noqa: BLE001
                self._note({"type": "scratch_close_failed", "ref": ref,
                            "error": repr(e)})
        self._note({"type": "scratched", "ref": ref, "why": why, "mode": self.mode})

    def close_now(self, ref: str, why: str) -> float:
        """Market-close a position NOW (scratch / rule J flatten / rule K flatten).
        Cancels the protective stop first, then closes. Returns estimated realized $."""
        p = self._positions.pop(ref, None)
        if p is None:
            return 0.0
        rec_ref = p.get("broker_ref")
        if p["exe"] is not None:
            p["exe"].done = True                   # abandon the driven stream
        pl = 0.0
        if self.live:
            try:
                if rec_ref is not None:
                    self.broker.cancel_order(rec_ref)          # stop down FIRST
                self.broker.close_partial(self.account, p["size"])
                last = getattr(self.broker, "_last", {})
                px = float(last.get("close", p["entry"]))
                sgn = 1.0 if p["side"] == "B" else -1.0
                pl = (sgn * (px - p["entry"]) * PV_MICRO * p["size"]) - COMMISSION
            except Exception as e:                 # noqa: BLE001
                self._note({"type": "close_failed", "ref": ref, "why": why,
                            "error": repr(e)})
        self._note({"type": "closed_now", "ref": ref, "why": why,
                    "pl_estimated": round(pl, 2), "mode": self.mode})
        if self.on_closed is not None:
            self.on_closed(ref, pl)
        return pl

    # ---- per closed bar: drive every position's exit engine ------------------
    def on_bar(self, bars_df, ts) -> None:
        if not self.live:
            return
        if hasattr(self.broker, "take_stop_fires"):
            for s in self.broker.take_stop_fires():
                self._note({"type": "stop_fired", "broker_ref": s["ref"],
                            "price": s["price"], "ts": str(s["ts"])})
        for ref, p in list(self._positions.items()):
            exe = p["exe"]
            if exe is None or exe.done:
                continue
            acts = exe.on_bar(bars_df, ts)
            for a in acts:
                self._note({"type": "exit_action", "ref": ref,
                            **{k: a.get(k) for k in
                               ("kind", "reason", "price", "frac", "qty", "ts")}})
                if a["kind"] == "partial":
                    p["legs"].append((int(a.get("qty", 0)), float(a.get("price") or 0)))
                elif a["kind"] == "exit":
                    self._realize(ref, p, a)

    def _realize(self, ref: str, p: dict, a: dict) -> None:
        sgn = 1.0 if p["side"] == "B" else -1.0
        exit_px = float(a.get("price") or (p["stop"] if a.get("reason") in
                                           ("stop", "be_stop") else p["entry"]))
        closed = sum(q for q, _ in p["legs"])
        pl = sum(sgn * (px - p["entry"]) * PV_MICRO * q for q, px in p["legs"])
        pl += sgn * (exit_px - p["entry"]) * PV_MICRO * max(p["size"] - closed, 0)
        pl -= COMMISSION
        self._positions.pop(ref, None)
        self._note({"type": "position_closed", "ref": ref, "reason": a.get("reason"),
                    "pl": round(pl, 2), "mode": self.mode})
        if self.on_closed is not None:
            self.on_closed(ref, round(pl, 2))

    def open_refs(self) -> list[str]:
        return list(self._positions)
