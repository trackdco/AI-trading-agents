"""Exit driver — the on_manage hook must reproduce engine.py's own exits, exactly.

The driver's whole claim is correctness BY CONSTRUCTION: it does not re-implement exit
management, it surfaces engine.py's decisions through the `on_manage` callback. These
tests hold that claim to real historical bars rather than synthetic fixtures, because the
champion-vs-canon lesson was precisely that a faithful-to-spec re-write shared 14% of its
trades with the thing it re-wrote — only running the SAME code proves sameness.

Three properties, in order of how badly a regression would hurt:

  1. the hook is ADDITIVE — `on_manage=None` is byte-identical to no hook at all, so
     wiring a live driver can never perturb the backtest that signed off the book;
  2. the emitted events RECONSTRUCT each TradeRecord (entry/stop/fill_ts, the final exit
     price/ts, and the "partial+" reason composition) — i.e. a consumer acting on the
     event stream acts on engine.py's actual exit, not an approximation;
  3. entry-pinning FAILS LOUD — a fill that isn't the canon's position must refuse to
     translate into broker actions, since managing an exit for a position we did not
     reproduce is the one failure that silently trades the wrong thing.

Slice: 2026-03-01..06 on the committed Feb–Jul parquet + committed trigger cache, chosen
because it exercises every event kind (fill / stop_move / partial / exit) in ~5s.
"""
from __future__ import annotations

from datetime import time as dtime
from pathlib import Path

import pandas as pd
import pytest

from src.backtest.engine import load_backtest_config, simulate
from src.canon.exit_driver import (
    CUT_FW3_MAX,
    CUT_R3_MAX,
    ExitDriver,
    three_min_cut,
    to_broker_actions,
)

NY = "America/New_York"
DATA = "data/reference/nq_1m_feb_jul2026.parquet"
TRIGS = "output/triggers_marjul_ob.csv"
LO, HI = "2026-03-01", "2026-03-06"
WARMUP_DAYS = 25            # indicator/level history ahead of the traded window


def _group_by_position(events: list[dict]) -> list[list[dict]]:
    """Segment the flat event stream into one group per position: fill … exit."""
    groups: list[list[dict]] = []
    cur: list[dict] | None = None
    for e in events:
        if e["kind"] == "fill":
            cur = [e]
        elif cur is not None:
            cur.append(e)
            if e["kind"] == "exit":
                groups.append(cur)
                cur = None
    return groups


@pytest.fixture(scope="module")
def sim():
    """Run the real slice ONCE: (bars, triggers, cfg, trades, events, groups)."""
    if not Path(DATA).exists() or not Path(TRIGS).exists():
        pytest.skip(f"{DATA} or {TRIGS} not present — this gate runs where the data lives")
    from scripts.grade_window_cap import books, load

    df = pd.read_parquet(DATA)
    trigs = load([TRIGS])
    base = load_backtest_config().model_copy(
        update={"win_start": dtime(8, 0), "win_end": dtime(10, 15),
                "max_trades_per_day": 2})
    cfg, _e4 = books(base)
    lo = pd.Timestamp(LO, tz=NY) - pd.Timedelta(days=WARMUP_DAYS)
    bars = df[(df.ts_event >= lo)
              & (df.ts_event <= pd.Timestamp(HI, tz=NY))].reset_index(drop=True)
    window = [t for t in trigs if LO <= t.ts[:10] <= HI]
    events: list[dict] = []
    trades, _v, _e = simulate(bars, window, cfg, on_manage=events.append)
    if not trades:
        pytest.skip("slice produced no trades — trigger cache or data changed")
    return bars, window, cfg, trades, events, _group_by_position(events)


# ---- 1. the hook is additive -------------------------------------------------------

def test_hook_never_changes_the_backtest(sim):
    """The load-bearing safety property: attaching the live driver's hook must not move a
    single backtest number, or the signed-off book stops meaning what it says."""
    bars, window, cfg, trades, _events, _groups = sim
    plain, _v, _e = simulate(bars, window, cfg)                     # no hook at all
    assert [t.model_dump() for t in plain] == [t.model_dump() for t in trades]


# ---- 2. events reconstruct the TradeRecords ----------------------------------------

def test_slice_exercises_every_event_kind(sim):
    """Guard against a vacuous suite: if the engine stopped emitting (say) partials, the
    reconstruction test below would still 'pass' while covering nothing."""
    _b, _w, _c, _t, events, _g = sim
    kinds = {e["kind"] for e in events}
    assert kinds == {"fill", "stop_move", "partial", "exit"}, kinds


def test_one_event_group_per_trade(sim):
    _b, _w, _c, trades, _e, groups = sim
    assert len(groups) == len(trades)


def test_emitted_events_reproduce_every_trade_record(sim):
    """The core claim: a consumer of the event stream sees engine.py's ACTUAL exit —
    same entry, same stop, same fill/exit timestamps, same price, same reason (including
    how engine.py composes 'partial+<reason>' when a runner was scaled out of)."""
    _b, _w, _c, trades, _e, groups = sim
    for trade, group in zip(trades, groups):
        fill, last = group[0], group[-1]
        partials = [e for e in group if e["kind"] == "partial"]
        expected_reason = (f"partial+{last['reason']}" if partials else last["reason"])
        assert fill["entry"] == pytest.approx(trade.entry)
        assert fill["stop"] == pytest.approx(trade.stop_initial)
        assert fill["fill_ts"] == trade.fill_ts
        assert fill["direction"] == trade.direction
        assert last["price"] == pytest.approx(trade.exit_price)   # legs[-1] IS the exit
        assert last["ts"] == trade.exit_ts
        assert expected_reason == trade.exit_reason


# ---- 3. the driver: entry-pinning ---------------------------------------------------

def test_drive_pins_real_entries_and_reproduces_the_same_actions(sim):
    """drive() re-runs simulate() with ONLY the one trigger — the handoff's open question
    was whether that isolated re-run still reproduces the in-context position. It does:
    same entry+stop (pinned) AND a byte-identical action stream, including a trade that
    scales out over 8 actions."""
    bars, window, cfg, trades, _e, groups = sim
    driver = ExitDriver()
    for trade, group in zip(trades, groups):
        trigger = next(t for t in window if t.ts == trade.trigger_ts)
        res = driver.drive(bars, trigger, cfg,
                           canon_entry=trade.entry, canon_stop=trade.stop_initial)
        assert res.entry_ok, f"{trade.trigger_ts}: {res.detail}"
        assert res.detail == ""
        in_context = [e for e in group if e["kind"] != "fill"]
        assert res.actions == in_context, trade.trigger_ts


def test_drive_refuses_a_wrong_canon_entry(sim):
    """A one-tick-off canon entry is a DIFFERENT position — the driver must say so rather
    than manage an exit for a trade it did not reproduce."""
    bars, window, cfg, trades, _e, _g = sim
    trade = trades[0]
    trigger = next(t for t in window if t.ts == trade.trigger_ts)
    driver = ExitDriver()
    res = driver.drive(bars, trigger, cfg,
                       canon_entry=trade.entry + 0.25,          # exactly one tick off
                       canon_stop=trade.stop_initial)
    assert res.entry_ok is False
    assert "ENTRY MISMATCH" in res.detail
    assert res.fill is not None                                  # it DID fill, just not ours


def test_drive_refuses_a_wrong_canon_stop(sim):
    bars, window, cfg, trades, _e, _g = sim
    trade = trades[0]
    trigger = next(t for t in window if t.ts == trade.trigger_ts)
    res = ExitDriver().drive(bars, trigger, cfg, canon_entry=trade.entry,
                             canon_stop=trade.stop_initial + 0.25)
    assert res.entry_ok is False and "ENTRY MISMATCH" in res.detail


def test_sub_tick_drift_still_pins(sim):
    """Pinning is to the TICK, not to floating-point equality — a sub-half-tick rounding
    difference must not spuriously refuse a position that IS ours."""
    bars, window, cfg, trades, _e, _g = sim
    trade = trades[0]
    trigger = next(t for t in window if t.ts == trade.trigger_ts)
    res = ExitDriver().drive(bars, trigger, cfg, canon_entry=trade.entry + 0.05,
                             canon_stop=trade.stop_initial - 0.05)
    assert res.entry_ok is True


# ---- 3b. translation to broker actions ----------------------------------------------

def test_to_broker_actions_refuses_when_not_pinned(sim):
    """The refusal must be an exception, not a falsy return — an unpinned exit silently
    translating into orders is the failure mode this whole check exists to prevent."""
    bars, window, cfg, trades, _e, _g = sim
    trade = trades[0]
    trigger = next(t for t in window if t.ts == trade.trigger_ts)
    res = ExitDriver().drive(bars, trigger, cfg, canon_entry=trade.entry + 5.0,
                             canon_stop=trade.stop_initial)
    with pytest.raises(ValueError, match="entry not pinned"):
        to_broker_actions(res)


def test_to_broker_actions_translates_a_real_scaled_out_trade(sim):
    """Translate the real multi-leg trade: stop moves become modifies, the partial becomes
    a partial-close, and the final exit closes — with `market` set so a stop-out/EOD goes
    marketable while a target rests as a limit (B2 is entries-only; exits may slip)."""
    bars, window, cfg, trades, _e, groups = sim
    idx = max(range(len(groups)), key=lambda i: len(groups[i]))   # the richest position
    trade = trades[idx]
    trigger = next(t for t in window if t.ts == trade.trigger_ts)
    res = ExitDriver().drive(bars, trigger, cfg,
                             canon_entry=trade.entry, canon_stop=trade.stop_initial)
    assert res.entry_ok
    orders = to_broker_actions(res)
    assert len(orders) == len(res.actions)
    for order, event in zip(orders, res.actions):
        if event["kind"] == "stop_move":
            assert order == {"action": "modify_stop", "price": event["price"],
                             "market": False}
        elif event["kind"] == "partial":
            assert order["action"] == "partial_close"
            assert order["frac"] == event["frac"] and order["price"] == event["price"]
            assert order["market"] is (event["reason"] != "target")
        else:
            assert order["action"] == "close" and order["price"] == event["price"]
            assert order["market"] is (event["reason"] != "target")
    assert [o["action"] for o in orders].count("close") == 1       # exactly one close


def test_target_exit_rests_as_a_limit_and_stop_exit_goes_market():
    """Pin the market/limit rule directly — it decides whether a live exit crosses the
    spread, so it must not drift with refactors even if the sampled slice has no target."""
    from src.canon.exit_driver import DriveResult
    res = DriveResult(fill={"entry": 1.0}, entry_ok=True, actions=[
        {"kind": "exit", "reason": "target", "price": 100.0, "frac": 1.0, "ts": "t"},
    ])
    assert to_broker_actions(res)[0]["market"] is False
    res.actions = [{"kind": "exit", "reason": "stop", "price": 90.0, "frac": 1.0,
                    "ts": "t"}]
    assert to_broker_actions(res)[0]["market"] is True


def test_drive_reports_no_fill_without_raising(sim):
    """A trigger that never fills is a normal outcome, not an error — but it must be
    reported as un-pinned so nothing downstream treats it as a live position."""
    bars, window, cfg, _t, _e, _g = sim
    driver = ExitDriver()
    for trigger in window:
        res = driver.drive(bars, trigger, cfg, canon_entry=1.0, canon_stop=0.5)
        if res.fill is None:
            assert res.entry_ok is False
            assert "no fill" in res.detail
            assert res.actions == []
            with pytest.raises(ValueError):
                to_broker_actions(res)
            return
    pytest.skip("every trigger in the slice filled — no-fill path not exercised here")


# ---- the 3-min cut overlay ----------------------------------------------------------

def test_three_min_cut_fires_only_when_both_frozen_conditions_hold():
    """Layer 2d is an AND of two frozen thresholds; either alone must NOT cut, and a
    missing input must never cut (absence of evidence is not evidence to exit)."""
    assert three_min_cut(CUT_R3_MAX, CUT_FW3_MAX) is True          # exactly at threshold
    assert three_min_cut(CUT_R3_MAX - 0.5, CUT_FW3_MAX - 5) is True
    assert three_min_cut(CUT_R3_MAX + 0.01, CUT_FW3_MAX) is False  # r_3 too healthy
    assert three_min_cut(CUT_R3_MAX, CUT_FW3_MAX + 1.0) is False   # fw_3 too healthy
    assert three_min_cut(None, CUT_FW3_MAX) is False
    assert three_min_cut(CUT_R3_MAX, None) is False
    assert three_min_cut(None, None) is False
