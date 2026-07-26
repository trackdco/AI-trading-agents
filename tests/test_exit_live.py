"""LiveExitExecutor (gate B8) — the managed exit through the broker surface, fail-closed.

The driver's fidelity to engine.py is already proven on real bars (test_exit_driver). Here
the driver is a scripted fake so every EXECUTION path is pinned deterministically: prefix
consistency, shadow-vs-armed, stop-fired verification, cancel-before-close ordering, the
3-min cut's precedence, and every fail-closed flatten."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.canon.exit_driver import CUT_FW3_MAX, CUT_R3_MAX, DriveResult
from src.canon.exit_live import LiveExitExecutor


@dataclass
class ScriptedDriver:
    """Returns a scripted action stream, truncated nowhere — the executor's own `ts <=
    bar_ts` due-filter does the pacing, which is exactly what real drive() output does."""
    actions: list = field(default_factory=list)
    entry_ok: bool = True
    raise_exc: bool = False

    def drive(self, bars, trigger, cfg, *, canon_entry, canon_stop):
        if self.raise_exc:
            raise RuntimeError("engine died")
        return DriveResult(fill={"entry": canon_entry}, actions=list(self.actions),
                           entry_ok=self.entry_ok,
                           detail="" if self.entry_ok else "ENTRY MISMATCH: scripted")


class RecordingBroker:
    def __init__(self, position=3):
        self.calls: list[tuple] = []
        self._position = position

    def modify_stop(self, ref, price):
        self.calls.append(("modify_stop", ref, price))

    def close_partial(self, account, qty, *, price=None):
        self.calls.append(("close_partial", account, qty, price))
        return "close-ref"

    def cancel_order(self, ref):
        self.calls.append(("cancel_order", ref))

    def flatten(self, account):
        self.calls.append(("flatten", account))

    def position(self, account):
        return self._position


class Journal:
    def __init__(self):
        self.notes = []

    def note(self, text):
        self.notes.append(text)


A_STOPMOVE = {"kind": "stop_move", "price": 101.0, "ts": "t1"}
A_PARTIAL = {"kind": "partial", "reason": "structure", "price": 103.0, "frac": 0.5, "ts": "t2"}
A_EXIT_STOP = {"kind": "exit", "reason": "stop", "price": 99.0, "frac": 0.5, "ts": "t3"}
A_EXIT_EOD = {"kind": "exit", "reason": "eod", "price": 102.0, "frac": 0.5, "ts": "t3"}


def _exe(actions, *, armed=True, position=3, **kw):
    broker = RecordingBroker(position=position)
    j = Journal()
    e = LiveExitExecutor(broker=broker, ref="entry-1", account="FUNDED", trigger=object(),
                         cfg="cfg", canon_entry=100.0, canon_stop=99.0, size=3,
                         armed=armed, driver=ScriptedDriver(actions=actions), journal=j, **kw)
    return e, broker, j


def test_actions_execute_incrementally_as_they_become_due():
    e, b, _ = _exe([A_STOPMOVE, A_PARTIAL, A_EXIT_EOD])
    assert [a["kind"] for a in e.on_bar(None, "t1")] == ["stop_move"]
    assert b.calls == [("modify_stop", "entry-1", 101.0)]
    out = e.on_bar(None, "t2")
    assert [a["kind"] for a in out] == ["partial"]
    assert ("close_partial", "FUNDED", 2, None) in b.calls      # 0.5 * 3 micros -> 2, market
    out = e.on_bar(None, "t3")
    assert [a["kind"] for a in out] == ["exit"] and e.done
    assert e.on_bar(None, "t9") == []                            # done: no further calls


def test_shadow_mode_journals_everything_and_touches_nothing():
    e, b, j = _exe([A_STOPMOVE, A_EXIT_EOD], armed=False)
    e.on_bar(None, "t3")                                         # both actions due
    assert b.calls == []                                         # zero broker calls
    assert all(a["executed"] is False for a in e.executed)
    assert any("stop_move" in n for n in j.notes)                # but fully journaled


def test_eod_exit_cancels_the_resting_stop_before_closing():
    e, b, _ = _exe([A_EXIT_EOD])
    e.on_bar(None, "t3")
    kinds = [c[0] for c in b.calls]
    assert kinds.index("cancel_order") < kinds.index("close_partial")


def test_stop_exit_trusts_a_fired_stop_when_position_is_flat():
    e, b, _ = _exe([A_EXIT_STOP], position=0)                    # broker says flat: stop fired
    e.on_bar(None, "t3")
    assert all(c[0] not in ("close_partial", "cancel_order") for c in b.calls)
    assert e.done


def test_stop_exit_market_closes_when_position_is_still_open():
    """The resting stop 'should' have fired; read-back says it didn't. Never trust —
    tear it down and close at market."""
    e, b, _ = _exe([A_EXIT_STOP], position=3)
    e.on_bar(None, "t3")
    kinds = [c[0] for c in b.calls]
    assert "cancel_order" in kinds and "close_partial" in kinds


def test_drive_exception_flattens_and_halts():
    e, b, _ = _exe([])
    e.driver.raise_exc = True                                    # C7: the engine died
    e.on_bar(None, "t1")
    assert e.halted and e.done and ("flatten", "FUNDED") in b.calls


def test_pin_break_mid_trade_flattens():
    e, b, _ = _exe([A_STOPMOVE])
    e.driver.entry_ok = False
    e.on_bar(None, "t1")
    assert e.halted and ("flatten", "FUNDED") in b.calls


def test_prefix_divergence_flattens():
    """If the re-driven stream no longer starts with what we already executed, the live
    position is not provably the backtest's position any more — flatten, don't improvise."""
    e, b, _ = _exe([A_STOPMOVE, A_EXIT_EOD])
    e.on_bar(None, "t1")                                         # executes the stop_move
    e.driver.actions = [{**A_STOPMOVE, "price": 555.0}, A_EXIT_EOD]   # history changed
    e.on_bar(None, "t2")
    assert e.halted and ("flatten", "FUNDED") in b.calls


def test_shadow_fail_closed_journals_but_does_not_touch_broker():
    e, b, j = _exe([], armed=False)
    e.driver.raise_exc = True
    e.on_bar(None, "t1")
    assert e.halted and b.calls == []
    assert any("FAIL-CLOSED" in n for n in j.notes)


def test_three_min_cut_takes_precedence_and_abandons_the_stream():
    e, b, _ = _exe([A_STOPMOVE, A_EXIT_EOD])
    assert e.maybe_cut(CUT_R3_MAX, CUT_FW3_MAX) is True          # fires exactly at threshold
    kinds = [c[0] for c in b.calls]
    assert kinds.index("cancel_order") < kinds.index("close_partial")
    assert e.done
    assert e.on_bar(None, "t3") == []                            # stream abandoned


def test_three_min_cut_healthy_trade_does_not_fire():
    e, b, _ = _exe([A_STOPMOVE])
    assert e.maybe_cut(0.5, 10.0) is False
    assert b.calls == [] and not e.done


def test_partial_quantity_rounds_from_fraction_of_filled_size():
    e, b, _ = _exe([{**A_PARTIAL, "frac": 0.5}], position=5)
    e.size = 5
    e.on_bar(None, "t2")
    assert ("close_partial", "FUNDED", 2, None) in b.calls       # round(0.5*5)=2, never 0
