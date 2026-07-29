"""ExitBinder — the trigger binding must be unanimous or refused, and real on real data.

Unit tests use scripted simulate/driver fakes to pin every refusal path (no candidates,
no pin, disagreeing pins, engine errors). The real-data test binds an actual Mar-2026
trade end to end: cached triggers + the real simulate + the real ExitDriver, asserting
the binder recovers exactly the trigger that produced the trade in the batch.
"""
from __future__ import annotations

from datetime import time as dtime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from src.canon.exit_driver import DriveResult
from src.live.exit_binder import ExitBinder

NY = "America/New_York"
DATA = "data/reference/nq_1m_feb_jul2026.parquet"
TRIGS = "output/triggers_marjul_ob.csv"
DAY = "2026-03-02"


def _bars():
    return pd.DataFrame({"ts_event": [pd.Timestamp(f"{DAY} 09:00", tz=NY)],
                         "close": [100.0]})


def _trade(trigger_ts, entry=100.0, stop=99.0, direction="long"):
    return SimpleNamespace(trade_date=DAY, direction=direction, entry=entry,
                           stop_initial=stop, trigger_ts=trigger_ts, fill_ts="f")


class ScriptedDriver:
    """drive() answers from a {trigger_ts: (entry_ok, actions)} script."""
    tick = 0.25

    def __init__(self, script):
        self.script = script

    def drive(self, bars, trigger, cfg, *, canon_entry, canon_stop):
        ok, actions = self.script.get(trigger.ts, (False, []))
        return DriveResult(fill={"entry": canon_entry}, actions=actions,
                           entry_ok=ok, detail="" if ok else "not pinned")


def _binder(*, triggers, trades_by_call, driver_script, armed=False):
    calls = {"n": 0}

    def fake_sim(bars, cands, cfg):
        out = trades_by_call[min(calls["n"], len(trades_by_call) - 1)]
        calls["n"] += 1
        if isinstance(out, Exception):
            raise out
        return list(out), None, None

    return ExitBinder(broker=object(), account="FUNDED", armed=armed, session="NY",
                      bars_fn=_bars, detect_fn=lambda b, s, e: list(triggers),
                      driver=ScriptedDriver(driver_script), simulate_fn=fake_sim)


T1 = SimpleNamespace(ts=f"{DAY}T08:30:00-05:00", direction="long")
T2 = SimpleNamespace(ts=f"{DAY}T08:45:00-05:00", direction="long")
ACT_A = [{"kind": "exit", "reason": "eod", "price": 101.0, "frac": 1.0, "ts": "t9"}]
ACT_B = [{"kind": "exit", "reason": "stop", "price": 99.0, "frac": 1.0, "ts": "t5"}]


def test_unique_pin_binds_the_executor():
    b = _binder(triggers=[T1, T2], trades_by_call=[[_trade(T1.ts)], []],
                driver_script={T1.ts: (True, ACT_A)}, armed=True)
    exe = b.factory("ref1", "B", 100.0, 99.0, 3)
    assert exe.trigger is T1 and exe.armed is True and exe.size == 3
    assert exe.canon_entry == 100.0 and exe.canon_stop == 99.0


def test_no_matching_direction_candidates_refuses():
    b = _binder(triggers=[SimpleNamespace(ts="x", direction="short")],
                trades_by_call=[[]], driver_script={})
    with pytest.raises(LookupError, match="no long triggers"):
        b.factory("ref1", "B", 100.0, 99.0, 3)


def test_in_context_match_that_fails_the_isolated_pin_refuses():
    b = _binder(triggers=[T1], trades_by_call=[[_trade(T1.ts)], []],
                driver_script={T1.ts: (False, [])})
    with pytest.raises(LookupError, match="failed the isolated pin"):
        b.factory("ref1", "B", 100.0, 99.0, 3)


def test_disagreeing_pins_are_ambiguous_and_refused():
    b = _binder(triggers=[T1, T2],
                trades_by_call=[[_trade(T1.ts)], [_trade(T2.ts)]],
                driver_script={T1.ts: (True, ACT_A), T2.ts: (True, ACT_B)})
    with pytest.raises(LookupError, match="AMBIGUOUS"):
        b.factory("ref1", "B", 100.0, 99.0, 3)


def test_agreeing_pins_are_unanimous_and_accepted():
    b = _binder(triggers=[T1, T2],
                trades_by_call=[[_trade(T1.ts)], [_trade(T2.ts)]],
                driver_script={T1.ts: (True, ACT_A), T2.ts: (True, ACT_A)})
    exe = b.factory("ref1", "B", 100.0, 99.0, 3)
    assert exe.trigger in (T1, T2)


def test_one_config_erroring_does_not_block_a_pin_from_the_other():
    b = _binder(triggers=[T1],
                trades_by_call=[RuntimeError("cfg exploded"), [_trade(T1.ts)]],
                driver_script={T1.ts: (True, ACT_A)})
    assert b.factory("ref1", "B", 100.0, 99.0, 3).trigger is T1


def test_entry_mismatch_finds_no_trade_and_refuses():
    b = _binder(triggers=[T1], trades_by_call=[[_trade(T1.ts, entry=555.0)], []],
                driver_script={T1.ts: (True, ACT_A)})
    with pytest.raises(LookupError, match="no \\(trigger, cfg\\) reproduces"):
        b.factory("ref1", "B", 100.0, 99.0, 3)


def test_no_bars_refuses():
    b = ExitBinder(broker=object(), account="FUNDED", bars_fn=lambda: None)
    with pytest.raises(LookupError, match="no bars"):
        b.factory("ref1", "B", 100.0, 99.0, 3)


# --------------------------------------------------------------------------- real data
def test_binds_a_real_trade_to_its_real_trigger_on_real_bars():
    """End to end on the committed slice: the binder must recover the exact trigger the
    batch's own simulate attributed the trade to, and hand back a working executor."""
    if not Path(DATA).exists() or not Path(TRIGS).exists():
        pytest.skip("reference data not present")
    from scripts.grade_window_cap import books, load
    from src.backtest.engine import load_backtest_config, simulate

    df = pd.read_parquet(DATA)
    lo = pd.Timestamp(DAY, tz=NY) - pd.Timedelta(days=25)          # indicator warmup
    hi = pd.Timestamp(f"{DAY} 23:59", tz=NY)
    bars = df[(df.ts_event >= lo) & (df.ts_event <= hi)].reset_index(drop=True)
    day_trigs = [t for t in load([TRIGS]) if t.ts[:10] == DAY]
    assert day_trigs

    base = load_backtest_config().model_copy(
        update={"win_start": dtime(8, 0), "win_end": dtime(10, 15),
                "max_trades_per_day": 2})
    cfg_e3, _ = books(base)
    trades, _v, _e = simulate(bars, day_trigs, cfg_e3)             # the batch's own answer
    assert trades, "expected at least one trade on the slice"
    tr = trades[0]

    binder = ExitBinder(broker=object(), account="FUNDED", armed=False, session="NY",
                        bars_fn=lambda: bars,
                        detect_fn=lambda b, s, e: list(day_trigs))
    exe = binder.factory("ref1", "B" if tr.direction == "long" else "S",
                         float(tr.entry), float(tr.stop_initial), 2)
    assert exe.trigger.ts == tr.trigger_ts                         # the same trigger
    assert exe.canon_entry == float(tr.entry)
    # and the bound executor actually drives: replay to completion in shadow
    last = exe.on_bar(bars, bars["ts_event"].iloc[-1])
    assert exe.done and not exe.halted and last
