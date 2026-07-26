"""TradeLifecycle — the assembly between a spine placement and the broker, per closed bar.

`SpineExecutor.place()` ends at the read-back-verified resting bracket. Everything AFTER
that — the part of the arming reference the backtest engine produced with its working-order
block and V8 management — is owned here:

  * the RESTING ENTRY:  `OrderWatch` mirrors engine.py's cancel decisions
    (t_cancel / window-end / EOD) boundary-for-boundary; armed, each decision executes as
    `broker.cancel_order`; every decision (and the fill-vs-cancel race) is journaled.
  * FILL DETECTION:     position read-back (one-position-at-a-time — the canon never holds
    two). Armed only: the disarmed loop places nothing, so there is nothing to detect and
    the broker (a `_NoBroker`) must never be touched.
  * the MANAGED EXIT:   a `LiveExitExecutor` built by the injected `exit_factory` at fill
    time and driven every closed bar; its own fail-closed semantics (drive death, pin
    break, prefix divergence -> flatten) stay in charge of the open position.
  * the 3-MIN CUT:      `cut_inputs()` computes r_3 / fw_3 live, mirrored line-for-line
    from scripts/intrade_matrix.py, and `maybe_cut` fires the frozen condition once at
    t+3min, taking precedence over the driven stream.

`exit_factory(ref, side, entry, stop, size) -> LiveExitExecutor` is a SEAM: binding the
driver needs the live trigger object + book config (the remaining live-assembly work). The
lifecycle FAILS CLOSED on an armed fill with no factory — an armed position that cannot be
managed is flattened immediately, never left to run on the resting stop alone (C7).

Shadow mode (armed=False): entries register with the watch under synthetic refs and every
would-be cancel is journaled with executed=False — the §D evidence for the B7 rule — with
zero broker calls, same pattern as the disarmed spine and the shadow exit executor.
"""
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from src.canon.exit_driver import CUT_AFTER_MIN
from src.canon.order_watch import OrderWatch

NY = "America/New_York"


def cut_inputs(bars_df: pd.DataFrame, tape_df: pd.DataFrame, *, entry: float, risk: float,
               direction: str, fill_ts) -> tuple[float, float]:
    """(r_3, fw_3) at t+3min, mirrored from scripts/intrade_matrix.py: fw_3 = direction-
    signed net tape delta over (fill, fill+3]; r_3 = position P&L in R at the fill+3min
    close. Insufficient minutes -> (nan, nan), and the frozen cut condition treats nan as
    'does not fire' — identical to the batch's alive-at-h guard."""
    f = pd.Timestamp(fill_ts).tz_convert(NY).floor("min")
    hi = f + pd.Timedelta(minutes=CUT_AFTER_MIN)
    if bars_df is None or tape_df is None or bars_df.empty or tape_df.empty:
        return math.nan, math.nan
    sgn = 1.0 if direction == "long" else -1.0
    seg = tape_df.sort_index().loc[f + pd.Timedelta(minutes=1): hi]
    bt = pd.to_datetime(bars_df["ts_event"]).dt.tz_convert(NY).dt.floor("min")
    pseg = bars_df.assign(_mi=bt).set_index("_mi").sort_index().loc[f: hi]
    if len(seg) < 2 or len(pseg) < 2:
        return math.nan, math.nan
    fw_3 = float((seg["delta"].to_numpy() * sgn).sum())
    r_3 = float((pseg["close"].iloc[-1] - entry) * sgn / risk)
    return r_3, fw_3


@dataclass
class TradeLifecycle:
    """Feed `on_placed` after each spine placement and `on_bar` for every guard-accepted
    closed bar. Decides nothing itself: the watch mirrors the engine, the executor drives
    the engine — this class only routes their decisions to the broker and the journal."""
    broker: object | None = None            # required when armed; never touched in shadow
    account: str = "FUNDED"
    armed: bool = False
    journal: Callable[[dict], None] | None = None
    watch: OrderWatch | None = None
    exit_factory: Callable | None = None    # (ref, side, entry, stop, size) -> executor
    cut_inputs_fn: Callable = cut_inputs    # injectable for tests

    _resting: dict = field(default_factory=dict, init=False)   # ref -> {side,entry,stop,size}
    _exe: object | None = field(default=None, init=False)
    _fill_ts: object | None = field(default=None, init=False)
    _fill_info: dict = field(default_factory=dict, init=False)
    _cut_checked: bool = field(default=False, init=False)
    halted: bool = field(default=False, init=False)

    def __post_init__(self):
        if self.watch is None:
            self.watch = OrderWatch()
        if self.armed and self.broker is None:
            raise ValueError("armed TradeLifecycle requires a broker")

    # ---- journaling ---------------------------------------------------------
    def _note(self, row: dict) -> None:
        if self.journal is not None:
            try:
                self.journal(row)
            except Exception:                      # journaling never breaks the loop
                pass

    # ---- fail-closed --------------------------------------------------------
    def _fail_closed(self, why: str) -> None:
        self.halted = True
        self._note({"event": "lifecycle_fail_closed", "why": why, "executed": self.armed})
        if self.armed:
            self.broker.flatten(self.account)

    # ---- placements ---------------------------------------------------------
    def on_placed(self, ref: str, *, side: str, entry: float, stop: float, size: int) -> None:
        """A LIMIT entry is now resting (armed: at the broker; shadow: hypothetically).
        Market entries never rest and must not be registered (B2: entries are limit-only,
        so in this lane everything placed rests)."""
        self._resting[ref] = {"side": side, "entry": float(entry), "stop": float(stop),
                              "size": int(size)}
        self.watch.register(ref, side, float(entry))
        self._note({"event": "entry_resting", "ref": ref, "side": side, "entry": entry,
                    "stop": stop, "size": size, "executed": self.armed})

    # ---- per closed bar -----------------------------------------------------
    def on_bar(self, bar: dict, *, bars_df=None, tape_df=None) -> None:
        """`bar` is one guard-accepted closed 1m bar (ts_event/high/low/close). `bars_df`
        is the engine-shaped frame THROUGH this bar (what the driver drives over) and
        `tape_df` the minute-tape frame — both from the canon ingestor."""
        if self.halted:
            return
        try:
            self._step(bar, bars_df, tape_df)
        except Exception as e:                     # noqa: BLE001 — any surprise: flatten
            self._fail_closed(f"lifecycle step raised {type(e).__name__}: {e}")

    def _step(self, bar: dict, bars_df, tape_df) -> None:
        ts = pd.Timestamp(bar["ts_event"])
        # 1) fill detection BEFORE the watch, so a filled entry is never cancelled.
        #    Armed only: shadow places nothing and must not touch the (_NoBroker) broker.
        if self.armed and self._exe is None and self._resting:
            pos = self.broker.position(self.account)
            if pos != 0:
                ref, info = next(iter(self._resting.items()))
                self.watch.mark_filled(ref)
                self._resting.pop(ref, None)
                self._fill_ts = ts
                self._fill_info = dict(info)
                self._cut_checked = False
                self._note({"event": "entry_filled", "ref": ref, "position": pos,
                            "executed": True})
                if self.exit_factory is None:      # armed position we cannot manage: C7
                    self._fail_closed("filled with no exit_factory bound — cannot manage")
                    return
                self._exe = self.exit_factory(ref, info["side"], info["entry"],
                                              info["stop"], abs(int(pos)))
        # 2) the engine-mirrored cancel decisions
        for d in self.watch.on_bar(ts, high=float(bar["high"]), low=float(bar["low"])):
            executed = self.armed and not d["raced_fill"]
            if executed:
                self.broker.cancel_order(d["ref"])
            self._resting.pop(d["ref"], None)
            self._note({"event": "order_watch", **d, "bar_ts": str(ts), "executed": executed})
        # 3) the managed exit
        if self._exe is None:
            return
        if not self._cut_checked and self._fill_ts is not None \
                and ts >= self._fill_ts + pd.Timedelta(minutes=CUT_AFTER_MIN):
            self._cut_checked = True
            fi = self._fill_info
            r_3, fw_3 = self.cut_inputs_fn(
                bars_df, tape_df, entry=fi["entry"],
                risk=abs(fi["entry"] - fi["stop"]),
                direction=("long" if fi["side"] == "B" else "short"),
                fill_ts=self._fill_ts)
            self._note({"event": "cut_check", "r_3": r_3, "fw_3": fw_3, "bar_ts": str(ts)})
            if self._exe.maybe_cut(r_3, fw_3):
                self._exe = None
                return
        self._exe.on_bar(bars_df, ts)
        if getattr(self._exe, "halted", False):
            self.halted = True                     # the executor already flattened
            self._note({"event": "lifecycle_halted_by_executor", "executed": self.armed})
        if getattr(self._exe, "done", False):
            self._exe = None
