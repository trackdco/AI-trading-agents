"""LiveExitExecutor (gate B8) — the managed exit, actually running through the broker.

The canon has NO fixed target: the exit is engine.py's V8 management (BE move, partial,
trail) + the 3-min cut + EOD flatten. `ExitDriver` (src/canon/exit_driver.py) already
reproduces engine.py's decisions byte-for-byte from bars; until now nothing could EXECUTE
them, because the broker surface had no modify/partial/cancel. Item 1 added the surface
(DTCBroker); this executor is the loop between the two:

    per closed bar:  drive engine.py over bars-so-far  ->  the action stream so far
                     assert the already-executed actions are a PREFIX of that stream
                     execute the new suffix through the Broker protocol
                     journal every action (armed) or the would-have action (shadow)

FAIL-CLOSED, in every direction the design docs demand:
  * drive() raising, the entry pin breaking mid-trade, or the executed prefix diverging
    from the freshly-driven stream all mean the live position is no longer provably the
    backtest's position -> FLATTEN + halt (C7's "engine dead / can't manage -> do not
    leave it running on the resting stop alone", PROMOTION-GATE §D1).
  * a stop/be_stop exit is expected to have FIRED at the broker (the resting stop is
    real); if read-back shows the position still open, market-close it rather than trust.
  * cut/EOD/target exits cancel the resting stop FIRST, then close — the same ordering as
    DTCBroker.flatten, so a resting stop can never double-fill against the close. The
    seconds-long unprotected window that ordering creates is journaled, accepted, and
    identical to the kill path's.

The 3-MIN CUT (canon Layer 2d) takes precedence over the driven stream: `maybe_cut(r_3,
fw_3)` reuses the frozen `three_min_cut` condition; when it fires the position is closed
at market NOW and the remaining driven actions are abandoned (engine parity for the cut is
the canon scripts', not simulate()'s — it was never in simulate()).

Shadow mode (armed=False): every decision is computed and journaled with executed=False,
zero broker calls — the same evidence-first pattern as the disarmed spine.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.canon.exit_driver import DriveResult, ExitDriver, three_min_cut


def _due(action_ts, bar_ts) -> bool:
    """Engine actions stamp ISO-T strings ('2026-03-02T08:38:00-05:00') while live bar
    stamps render with a space — comparing the raw strings silently never matures a
    same-day action. Compare as timestamps; opaque labels (tests) fall back to string."""
    try:
        return pd.Timestamp(action_ts) <= pd.Timestamp(bar_ts)
    except (ValueError, TypeError):
        return str(action_ts) <= str(bar_ts)


@dataclass
class LiveExitExecutor:
    broker: object                       # src.canon.spine.Broker implementer (DTCBroker live)
    ref: str                             # the bracket's entry ref (order_status/modify key)
    account: str
    trigger: object                      # the canon trigger this position came from
    cfg: object                          # the book config that produced the canon exit
    canon_entry: float
    canon_stop: float
    size: int                            # micros filled
    armed: bool = False
    driver: ExitDriver = field(default_factory=ExitDriver)
    journal: object | None = None        # anything with .note(str); optional

    executed: list[dict] = field(default_factory=list, init=False)
    done: bool = field(default=False, init=False)
    halted: bool = field(default=False, init=False)

    # ---- journaling ---------------------------------------------------------
    def _note(self, text: str) -> None:
        if self.journal is not None:
            try:
                self.journal.note(text)
            except Exception:                      # journaling never breaks management
                pass

    # ---- fail-closed --------------------------------------------------------
    def _fail_closed(self, why: str) -> None:
        self.halted = True
        self.done = True
        self._note(f"exit_executor FAIL-CLOSED: {why} -> flatten")
        if self.armed:
            self.broker.flatten(self.account)

    # ---- the 3-min cut (Layer 2d) -------------------------------------------
    def maybe_cut(self, r_3: float | None, fw_3: float | None) -> bool:
        """Call once at t+3min with the live-computed r_3 / fw_3. Fires the frozen canon
        condition: close at market NOW, abandon the driven stream. Returns True if cut."""
        if self.done or not three_min_cut(r_3, fw_3):
            return False
        self._note(f"exit_executor 3-min cut fires (r_3={r_3}, fw_3={fw_3}) — market out")
        self.done = True
        if self.armed:
            self.broker.cancel_order(self.ref)     # tear the resting stop down first
            self.broker.close_partial(self.account, self.size)
        self.executed.append({"kind": "exit", "reason": "cut3", "executed": self.armed})
        return True

    # ---- per-bar step -------------------------------------------------------
    def on_bar(self, bars_df, bar_ts) -> list[dict]:
        """Drive engine.py over bars-so-far and execute the newly-due actions. Returns the
        actions performed this bar (each journaled). `bars_df` must be the same frame the
        canon runs on, through the just-closed bar."""
        if self.done:
            return []
        try:
            res: DriveResult = self.driver.drive(
                bars_df, self.trigger, self.cfg,
                canon_entry=self.canon_entry, canon_stop=self.canon_stop)
        except Exception as e:                     # the engine died mid-trade (C7)
            self._fail_closed(f"drive() raised {type(e).__name__}: {e}")
            return list(self.executed[-1:])
        if not res.entry_ok:
            self._fail_closed(f"entry pin broke mid-trade: {res.detail}")
            return list(self.executed[-1:])

        due = [a for a in res.actions if _due(a["ts"], bar_ts)]
        # the already-executed actions must be a PREFIX of the freshly-driven stream —
        # anything else means the re-derived management no longer matches what we did.
        keys = ("kind", "reason", "price", "frac", "ts")

        def _sig(a: dict) -> tuple:
            return tuple(a.get(k) for k in keys)
        prior = [a for a in self.executed if "ts" in a]     # driven actions (cut3 has none)
        if [_sig(a) for a in prior] != [_sig(a) for a in due[:len(prior)]]:
            self._fail_closed("executed actions diverged from the re-driven stream")
            return list(self.executed[-1:])

        out = []
        for action in due[len(prior):]:
            performed = self._execute(action)
            out.append(performed)
            self.executed.append(performed)
            if performed["kind"] == "exit":
                self.done = True
                break
        return out

    # ---- action translation (mirrors exit_driver.to_broker_actions) ---------
    def _execute(self, a: dict) -> dict:
        rec = {**a, "executed": self.armed}
        if a["kind"] == "stop_move":
            self._note(f"exit stop_move -> {a['price']} @ {a['ts']}")
            if self.armed:
                self.broker.modify_stop(self.ref, a["price"])
        elif a["kind"] == "partial":
            qty = max(1, round(float(a["frac"]) * self.size))
            rec["qty"] = qty
            self._note(f"exit partial {a['frac']:g} ({qty} micros) "
                       f"reason={a['reason']} @ {a['ts']}")
            if self.armed:
                price = a["price"] if a["reason"] == "target" else None
                self.broker.close_partial(self.account, qty, price=price)
        elif a["kind"] == "exit":
            self._note(f"exit close reason={a['reason']} @ {a['ts']}")
            if self.armed:
                if a["reason"] in ("stop", "be_stop"):
                    # the resting stop should have FIRED. Verify; never trust.
                    if self.broker.position(self.account) != 0:
                        self._note("exit_executor: stop exit but position still open "
                                   "at read-back — market-closing (fail-closed)")
                        self.broker.cancel_order(self.ref)
                        self.broker.close_partial(self.account, self.size)
                else:                              # cut/eod/target-style: we close it
                    self.broker.cancel_order(self.ref)     # stop down FIRST (no double-fill)
                    price = a["price"] if a["reason"] == "target" else None
                    self.broker.close_partial(self.account, self.size, price=price)
        return rec
