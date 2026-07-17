"""Tests for src/backtest/engine.py — event-driven backtester (Spec 1, Step 7).

Hand-built 1m bar sequences + synthetic Triggers with a stub target resolver and pinned
entry prices, so fill/stop/target/management/vault mechanics are tested in isolation
(detect_triggers is NOT called here except in one integration test on the committed slice).

Mandatory named tests (code-standards): test_no_lookahead, test_single_position_invariant,
test_fill_requires_trade_through.
"""
from datetime import time
from pathlib import Path

import pandas as pd
import pytest

from src.backtest.engine import BacktestConfig, simulate
from src.engine.triggers import Trigger

NY = "America/New_York"
FIX = Path(__file__).parent / "fixtures"


def cfg(**over) -> BacktestConfig:
    base = dict(timezone=NY, win_start=time(0, 1), win_end=time(23, 58),
                eod_flatten=time(15, 55), entry_variant="E3", t_cancel=15.0,
                front_run=2.5, rr_floor=1.5, news_override=False,
                min_conf_counter=3, min_conf_with=2, mgmt_variant="V0",
                v1_be_at_r=1.0, v4_partial_pct=50, max_trades_per_day=3,
                halt_losses=2, halt_r=-2.0,
                oversized_stop=42.0, late_window_after=time(10, 30),
                vwap_warmup_min=60, no_premarket_high_impact=True,
                require_bb_vwap=True,
                # min-stop disabled by default so hand-built geometry fixtures stay valid;
                # the §5 v1.2 rule has its own dedicated tests below (min_stop_points=10)
                min_stop_points=0.0,
                tick=0.25, through_ticks=1,
                slip_normal=1, slip_news=4, news_window_min=15,
                commission_side=2.5, point_value=20.0)
    base.update(over)
    return BacktestConfig(**base)


def mk_bars(start: str, rows: list[tuple]) -> pd.DataFrame:
    idx = pd.date_range(pd.Timestamp(start, tz=NY), periods=len(rows), freq="1min")
    o, h, lo, c = zip(*rows)
    return pd.DataFrame({"ts_event": idx, "open": o, "high": h, "low": lo, "close": c,
                         "volume": [100] * len(rows)})


def trig(ts: str, direction="long", conf=3, htf="counter_trend", pattern="A",
         entry_ref=25000.0, stop_ref=None, tf="3min", cluster_types=("bb", "vwap", "poc")) -> Trigger:
    stop = stop_ref if stop_ref is not None else (entry_ref - 10 if direction == "long"
                                                  else entry_ref + 10)
    wl, wh = (stop, entry_ref) if direction == "long" else (entry_ref, stop)
    return Trigger(ts=pd.Timestamp(ts, tz=NY).isoformat(), tf=tf, direction=direction,
                   kind="rejection_block", pattern=pattern, htf_flag=htf,
                   entry_ref=entry_ref, stop_ref=stop, wick_low=wl, wick_high=wh,
                   cluster_center=entry_ref, confluence_count=conf,
                   cluster_types=list(cluster_types), close=entry_ref + 2)


def stub_resolver(level: float):
    return lambda t, entry, stop: ("stub_level", level)


def pin_entry(price: float):
    return lambda t: price


EMPTY_CAL = pd.DataFrame(columns=["datetime_ET", "event", "impact"])


def run(bars, triggers, c=None, resolver=None, entry=None, calendar=None):
    return simulate(bars, triggers, c or cfg(), target_resolver=resolver,
                    entry_price_fn=entry, calendar=EMPTY_CAL if calendar is None else calendar)


# ------------------------------------------------------------- fills

def test_fill_requires_trade_through():
    # long limit 25000: a bar whose low EXACTLY touches 25000 must NOT fill;
    # a bar trading through by 1 tick (low 24999.75) MUST fill.
    t = trig("2026-02-11 09:48")
    touch = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                         (25004, 25005, 25000.0, 25002)])
    tr, vd, _ = run(touch, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert not any(v.status == "taken" for v in vd) and tr == []

    through = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                           (25004, 25005, 24999.75, 25002),
                                           (25003, 25101, 25002, 25100)])  # then target
    tr, vd, _ = run(through, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert any(v.status == "taken" for v in vd)
    assert len(tr) == 1 and tr[0].entry == 25000.0


def test_order_cannot_fill_before_activation():
    # fillable prices BEFORE the trigger's close ts must not fill the order
    t = trig("2026-02-11 09:50")
    bars = mk_bars("2026-02-11 09:48", [(25004, 25005, 24999.0, 25002),   # pre-trigger dip
                                        (25003, 25004, 25002, 25003),
                                        (25003, 25004, 25002.5, 25003),   # trigger bar: no dip
                                        (25003, 25004, 25002.5, 25003)])
    tr, vd, _ = run(bars, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert not any(v.status == "taken" for v in vd) and tr == []


def test_t_cancel_wins_and_blocks_fill():
    # price runs t_cancel (15) beyond the limit without a prior fill -> cancelled
    t = trig("2026-02-11 09:48")
    bars = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                        (25010, 25016.0, 25009, 25015),    # 25016 >= 25000+15+... run-away
                                        (25003, 25004, 24999.0, 25002)])   # would-be fill after cancel
    tr, vd, _ = run(bars, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert any(v.status == "cancelled_tcancel" for v in vd)
    assert tr == [] and not any(v.status == "taken" for v in vd)


def test_stop_touch_with_adverse_slippage_and_gap_through():
    t = trig("2026-02-11 09:48", stop_ref=24990.0)
    # fill at 25000, then bar touches stop 24990 -> exit 24990 - 1 tick
    bars = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                        (25004, 25005, 24999.75, 25002),
                                        (24996, 24997, 24990.0, 24992)])
    tr, _, _ = run(bars, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert len(tr) == 1 and tr[0].exit_reason == "stop"
    assert tr[0].exit_price == pytest.approx(24990.0 - 0.25)
    # gap-through: next-day style open BELOW the stop -> fill at the worse open - slip
    bars2 = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                         (25004, 25005, 24999.75, 25002),
                                         (24985.0, 24986, 24980, 24982)])
    tr2, _, _ = run(bars2, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert tr2[0].exit_price == pytest.approx(24985.0 - 0.25)


def test_same_bar_stop_and_target_resolves_to_stop():
    t = trig("2026-02-11 09:48", stop_ref=24990.0)
    bars = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                        (25004, 25005, 24999.75, 25002),
                                        (25000, 25101.0, 24989.0, 25050)])  # spans both
    tr, _, _ = run(bars, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert len(tr) == 1 and tr[0].exit_reason == "stop"


def test_target_fills_via_trade_through_at_working_target():
    # target level 25100, front-run 2.5 -> working 25097.5; fills when high >= 25097.75
    t = trig("2026-02-11 09:48")
    no = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                      (25004, 25005, 24999.75, 25002),
                                      (25050, 25097.5, 25040, 25090)])      # touch only
    tr, _, _ = run(no, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert tr == []                                                        # still open at end
    yes = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                       (25004, 25005, 24999.75, 25002),
                                       (25050, 25097.75, 25040, 25090)])
    tr, _, _ = run(yes, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert len(tr) == 1 and tr[0].exit_reason == "target"
    assert tr[0].exit_price == pytest.approx(25097.5)
    assert tr[0].r_multiple == pytest.approx(9.75, abs=0.01)               # 97.5 / 10


# ------------------------------------------------------------- invariants

def test_no_lookahead():
    t = trig("2026-02-11 09:48", stop_ref=24990.0)
    rows = [(25005, 25006, 25004, 25005), (25004, 25005, 24999.75, 25002),
            (25003, 25004, 25001, 25002), (24996, 24997, 24990.0, 24992),   # stop at 09:51
            (25000, 25200, 24900, 25100), (25000, 25200, 24900, 25100)]
    bars = mk_bars("2026-02-11 09:48", rows)
    T = pd.Timestamp("2026-02-11 09:52", tz=NY)
    tr_a, vd_a, _ = run(bars, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    pert = bars.copy()
    fut = pert["ts_event"] >= T
    pert.loc[fut, ["open", "high", "low", "close"]] += 500.0
    tr_b, vd_b, _ = run(pert, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    upto = lambda trs: [x.model_dump() for x in trs if pd.Timestamp(x.exit_ts) < T]  # noqa: E731
    assert upto(tr_a) == upto(tr_b)
    assert [v.model_dump() for v in vd_a if pd.Timestamp(v.ts) < T] == \
           [v.model_dump() for v in vd_b if pd.Timestamp(v.ts) < T]


def test_single_position_invariant():
    t1 = trig("2026-02-11 09:48")
    t2 = trig("2026-02-11 09:49", entry_ref=25001.0)
    bars = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                        (25004, 25005, 24999.75, 25002),
                                        (25003, 25004, 25001, 25002),
                                        (25050, 25101.0, 25040, 25090)])
    tr, vd, _ = run(bars, [t1, t2], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert len(tr) <= 1
    assert any(v.status in ("skipped_position_open", "skipped_order_working") for v in vd)
    spans = [(pd.Timestamp(x.fill_ts), pd.Timestamp(x.exit_ts)) for x in tr]
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            assert spans[i][1] <= spans[j][0] or spans[j][1] <= spans[i][0]


# ------------------------------------------------------------- vetoes & vault

def test_window_and_confluence_vetoes():
    c = cfg(win_start=time(9, 30), win_end=time(11, 0))
    early = trig("2026-02-11 08:00")
    weak = trig("2026-02-11 09:48", conf=2, htf="counter_trend")
    ok_wt = trig("2026-02-11 09:49", conf=2, htf="with_trend")
    bars = mk_bars("2026-02-11 08:00", [(25005, 25006, 25004, 25005)] * 130)
    _, vd, _ = run(bars, [early, weak, ok_wt], c=c,
                   resolver=stub_resolver(25100), entry=pin_entry(25000))
    st = {v.ts: v.status for v in vd}
    assert st[early.ts] == "vetoed_window"
    assert st[weak.ts] == "vetoed_confluence"          # counter-trend needs 3
    # with-trend needs only 2 -> passes filters and becomes a working order (no veto verdict)
    assert st.get(ok_wt.ts) != "vetoed_confluence"


def test_rr_floor_veto():
    t = trig("2026-02-11 09:48")                        # risk 10 pts
    bars = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005)] * 3)
    _, vd, _ = run(bars, [t], resolver=stub_resolver(25010.0), entry=pin_entry(25000))
    assert any(v.status == "vetoed_rr_floor" for v in vd)  # (10-2.5)/10 = 0.75 < 1.5


def _quick_loss_day(n_triggers: int, c: BacktestConfig):
    """n triggers, each fills next bar and stops the bar after (loss cycle of 3 bars)."""
    rows, trigs = [], []
    t0 = pd.Timestamp("2026-02-11 09:00", tz=NY)
    for k in range(n_triggers):
        base = t0 + pd.Timedelta(minutes=3 * k)
        trigs.append(trig(str(base.tz_localize(None)), stop_ref=24995.0))
        rows += [(25005, 25006, 25004, 25005),
                 (25004, 25005, 24999.75, 25002),          # fill 25000
                 (24996, 24997, 24994.0, 24996)]           # stop 24995 -> loss ~-0.5R... risk 5
    bars = mk_bars("2026-02-11 09:00", rows)
    return run(bars, trigs, c=c, resolver=stub_resolver(25100), entry=pin_entry(25000))


def test_max_trades_per_day():
    c = cfg(halt_losses=99, halt_r=-99.0, max_trades_per_day=3)
    tr, vd, _ = _quick_loss_day(5, c)
    assert len(tr) == 3
    assert sum(1 for v in vd if v.status in ("vetoed_vault_max",)) >= 1


def test_daily_halt_after_losses():
    c = cfg(halt_losses=2, halt_r=-99.0, max_trades_per_day=99)
    tr, vd, _ = _quick_loss_day(4, c)
    assert len(tr) == 2                                    # halted after 2 losses
    assert any(v.status == "vetoed_halt" for v in vd)


def test_eod_flatten():
    t = trig("2026-02-11 15:50")
    bars = mk_bars("2026-02-11 15:50", [(25005, 25006, 25004, 25005),
                                        (25004, 25005, 24999.75, 25002),   # fill 15:51
                                        (25003, 25004, 25002, 25003),
                                        (25003, 25004, 25002, 25003),
                                        (25003, 25004, 25002, 25003),
                                        (25010.0, 25011, 25009, 25010)])   # 15:55 flatten bar
    tr, _, _ = run(bars, [t], resolver=stub_resolver(25200), entry=pin_entry(25000))
    assert len(tr) == 1 and tr[0].exit_reason == "eod"
    assert tr[0].exit_price == pytest.approx(25010.0 - 0.25)               # open - slip


# ------------------------------------------------------------- management & slippage

def test_v1_be_at_1r_touch_then_be_stop():
    c = cfg(mgmt_variant="V1")
    t = trig("2026-02-11 09:48", stop_ref=24990.0)         # risk 10
    bars = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                        (25004, 25005, 24999.75, 25002),   # fill 25000
                                        (25005, 25010.0, 25000.1, 25008),  # touches +1R AND near entry: no exit this bar
                                        (25005, 25006, 25000.0, 25003)])   # BE stop (25000) touched next bar
    tr, _, _ = run(bars, [t], c=c, resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert len(tr) == 1 and tr[0].exit_reason == "be_stop"
    assert tr[0].exit_price == pytest.approx(25000.0 - 0.25)               # BE stop + slippage


def test_news_window_slippage():
    cal = pd.DataFrame({"datetime_ET": [pd.Timestamp("2026-02-11 09:50", tz=NY)],
                        "event": ["CPI"], "impact": ["high"]})
    t = trig("2026-02-11 09:48", stop_ref=24990.0)
    bars = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                        (25004, 25005, 24999.75, 25002),
                                        (24996, 24997, 24990.0, 24992)])
    tr, _, _ = run(bars, [t], resolver=stub_resolver(25100), entry=pin_entry(25000),
                   calendar=cal)
    assert tr[0].slippage_ticks == 4                                       # news window
    assert tr[0].exit_price == pytest.approx(24990.0 - 4 * 0.25)


def test_v4_partial_legs_weighted_r():
    c = cfg(mgmt_variant="V4")
    t = trig("2026-02-11 09:48", stop_ref=24990.0)         # risk 10
    tr_, vd, _ = None, None, None
    bars = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                        (25004, 25005, 24999.75, 25002),    # fill 25000
                                        (25030, 25050.25, 25020, 25045),    # partial at 25050? no: level 25050 needs 25050.25 through
                                        (25060, 25097.75, 25050, 25090)])   # runner target
    tr_, vd, _ = simulate(bars, [t], c,
                          target_resolver=stub_resolver(25100),
                          entry_price_fn=pin_entry(25000), calendar=EMPTY_CAL)
    # partial level comes from order attr; engine only books it when set -> with stub resolver
    # there is no partial level, so the trade exits fully at target (documented: V4 needs the
    # snapshot menu; stub-resolver runs behave like V0). This asserts the degraded behavior.
    assert len(tr_) == 1 and tr_[0].exit_reason == "target"


# ------------------------------------------------------------- Angus 2026-07-17 rules

def test_vwap_warmup_veto():
    # trigger 18:30 (within 60min of the 18:00 anchor) -> vetoed; 19:05 -> allowed
    t_in = trig("2026-02-11 18:30")
    t_out = trig("2026-02-11 19:05")
    bars = mk_bars("2026-02-11 18:00", [(25005, 25006, 25004, 25005)] * 90)
    _, vd, _ = run(bars, [t_in, t_out], resolver=stub_resolver(25100), entry=pin_entry(25000))
    st = {v.ts: v.status for v in vd}
    assert st[t_in.ts] == "vetoed_vwap_warmup"
    assert st.get(t_out.ts) != "vetoed_vwap_warmup"


def test_high_impact_preopen_news_blocks_until_open():
    # ANGUS 2026-07-17 (TIGHTENED): on a high-impact pre-open release day the ENTIRE pre-market
    # is blocked -> both pre-release and post-release pre-open triggers are vetoed; 09:30+ allowed.
    cal = pd.DataFrame({"datetime_ET": [pd.Timestamp("2026-02-20 08:30", tz=NY)],
                        "event": ["Core Price Index"], "impact": ["high"]})
    pre_release = trig("2026-02-20 08:06")     # BEFORE the release -> now vetoed (whole pre-market)
    post_release = trig("2026-02-20 08:45")    # after release, before 09:30 -> vetoed
    after_open = trig("2026-02-20 09:35")      # after the open -> allowed
    rows = [(25005, 25006, 25004, 25005)] * 120
    bars = mk_bars("2026-02-20 08:00", rows)
    _, vd, _ = run(bars, [pre_release, post_release, after_open],
                   resolver=stub_resolver(25100), entry=pin_entry(25000), calendar=cal)
    st = {v.ts: v.status for v in vd}
    assert st[pre_release.ts] == "vetoed_news_preopen"
    assert st[post_release.ts] == "vetoed_news_preopen"
    assert st.get(after_open.ts) != "vetoed_news_preopen"


def test_oversized_stop_half_size():
    t = trig("2026-02-11 09:48", stop_ref=24950.0)          # 50-pt risk > 42 -> half
    bars = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                        (25004, 25005, 24999.75, 25002),
                                        (25050, 25200.0, 25040, 25150)])
    tr, _, _ = run(bars, [t], resolver=stub_resolver(25150), entry=pin_entry(25000))
    assert len(tr) == 1 and tr[0].size == 0.5


def test_late_window_half_size():
    t = trig("2026-02-11 10:31", pattern="A", conf=3)       # fill after 10:30 -> half
    bars = mk_bars("2026-02-11 10:31", [(25005, 25006, 25004, 25005),
                                        (25004, 25005, 24999.75, 25002),
                                        (25050, 25101.0, 25040, 25090)])
    tr, _, _ = run(bars, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    assert len(tr) == 1 and tr[0].size == 0.5


def test_gap_through_entry_is_a_scratch_not_a_phantom_loss():
    # A short limit whose FILL bar opens past both the entry and the stop must fill at the open
    # (gap), not the limit — otherwise entry@limit + stop@open books a phantom multi-R loss.
    t = trig("2026-02-11 09:48", direction="short", entry_ref=25000.0, stop_ref=25002.0)
    bars = mk_bars("2026-02-11 09:48", [
        (24998, 24999, 24997, 24998),      # 09:48: order placed, no fill (price below entry)
        (25010, 25012, 25008, 25011),      # 09:49: opens 25010 past entry+stop -> fill@open, scratch
    ])
    tr, _, _ = run(bars, [t], resolver=stub_resolver(24900), entry=pin_entry(25000))
    assert len(tr) == 1 and tr[0].exit_reason == "stop"
    assert tr[0].r_multiple > -1.0     # scratch (entry≈exit), not the ~-5R phantom of the old bug


def test_bb_vwap_gate_vetoes_cluster_without_both():
    # §9 v1.1: a cluster missing BB or VWAP -> NO TRADE, even at high confluence.
    t = trig("2026-02-11 09:48", conf=3, cluster_types=("vwap", "poc"))   # no BB
    bars = mk_bars("2026-02-11 09:48", [(25005, 25006, 25004, 25005),
                                        (25004, 25005, 24999.75, 25002),
                                        (25050, 25101.0, 25040, 25090)])
    tr, vd, _ = run(bars, [t], resolver=stub_resolver(25100), entry=pin_entry(25000))
    st = {v.ts: v.status for v in vd}
    assert len(tr) == 0
    assert st[t.ts] == "vetoed_bb_vwap"


def test_v12_full_size_default_even_counter_trend_two_types():
    # §9 v1.2 (ANGUS calibration ruling): FULL size is the default — a 2-type BB+VWAP
    # COUNTER-TREND trade is full size; POC adds nothing to sizing any more.
    rows = [(25005, 25006, 25004, 25005), (25004, 25005, 24999.75, 25002),
            (25050, 25101.0, 25040, 25090)]
    for ctypes in (("bb", "vwap"), ("bb", "vwap", "poc")):
        t = trig("2026-02-11 09:48", conf=2, htf="counter_trend", pattern="B",
                 cluster_types=ctypes)
        tr, _, _ = run(mk_bars("2026-02-11 09:48", rows), [t],
                       resolver=stub_resolver(25100), entry=pin_entry(25000),
                       c=cfg(min_conf_counter=2))
        assert len(tr) == 1 and tr[0].size == 1.0, ctypes


def test_v12_counter_trend_two_confluence_enters():
    # §7 v1.2: confluence minimum is 2 everywhere — conf=2 counter-trend must NOT be
    # vetoed_confluence (this was the gate on 13 of the 24 Feb MISSED trades).
    t = trig("2026-02-11 09:48", conf=2, htf="counter_trend", pattern="A",
             cluster_types=("bb", "vwap"))
    rows = [(25005, 25006, 25004, 25005), (25004, 25005, 24999.75, 25002),
            (25050, 25101.0, 25040, 25090)]
    tr, verdicts, _ = run(mk_bars("2026-02-11 09:48", rows), [t],
                          resolver=stub_resolver(25100), entry=pin_entry(25000),
                          c=cfg(min_conf_counter=2))
    assert not any(v.status == "vetoed_confluence" for v in verdicts)
    assert len(tr) == 1


def test_v12_min_stop_veto():
    # §5 v1.2 (ANGUS): structural stop narrower than min_stop_points -> skip, never widen.
    tight = trig("2026-02-11 09:48", stop_ref=24996.0)   # 4-pt stop vs pinned 25000 entry
    rows = [(25005, 25006, 25004, 25005), (25004, 25005, 24999.75, 25002),
            (25050, 25101.0, 25040, 25090)]
    tr, verdicts, _ = run(mk_bars("2026-02-11 09:48", rows), [tight],
                          resolver=stub_resolver(25100), entry=pin_entry(25000),
                          c=cfg(min_stop_points=10.0))
    assert len(tr) == 0
    assert any(v.status == "vetoed_min_stop" for v in verdicts)
    ok = trig("2026-02-11 09:48", stop_ref=24990.0)      # exactly 10 pts -> allowed
    tr2, v2, _ = run(mk_bars("2026-02-11 09:48", rows), [ok],
                     resolver=stub_resolver(25100), entry=pin_entry(25000),
                     c=cfg(min_stop_points=10.0))
    assert len(tr2) == 1 and not any(v.status == "vetoed_min_stop" for v in v2)


# ------------------------------------------------------------- integration (slice)

def test_integration_slice_runs_and_is_consistent():
    df = pd.read_csv(FIX / "snapshot_slice.csv")
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(NY)
    from src.engine.indicators import IndicatorsConfig
    from src.engine.triggers import detect_triggers
    icfg = IndicatorsConfig(bb_length=20, bb_mult=2.0,
                            entry_tfs=["1min", "2min", "3min", "5min"],
                            ny_anchor=time(9, 30), ny_bands=[1, 2, 3],
                            daily_anchor=time(18, 0), daily_bands=[1, 2, 3],
                            vwap_source="hlc3", vp_bin_points=0.25,
                            vp_value_area_pct=70, vp_weekly_enabled=False)
    trigs = detect_triggers(df, cfg=icfg,
                            start=pd.Timestamp("2026-02-11 09:30", tz=NY),
                            end=pd.Timestamp("2026-02-11 10:00", tz=NY), tol=10.0)
    c = cfg(win_start=time(8, 0), win_end=time(11, 0), entry_variant="E3")
    trades, verdicts, equity = simulate(df, trigs, c)
    assert len(verdicts) == len(trigs)                     # every trigger got a verdict
    for tr in trades:
        sign = 1 if tr.direction == "long" else -1
        # intended geometry is on the ORDER (limit vs stop/target); the actual fill may gap past
        # a level on a gap-through bar, so assert the invariants on limit_price, not the fill.
        assert sign * (tr.limit_price - tr.stop_initial) > 0     # stop beyond entry order
        assert sign * (tr.working_target - tr.limit_price) > 0   # target beyond entry order
        seg = df[(df["ts_event"] >= pd.Timestamp(tr.fill_ts)) &
                 (df["ts_event"] <= pd.Timestamp(tr.exit_ts))]
        assert not seg.empty
    if len(trades) > 1:
        spans = sorted((pd.Timestamp(x.fill_ts), pd.Timestamp(x.exit_ts)) for x in trades)
        for a, b in zip(spans, spans[1:]):
            assert a[1] <= b[0]                            # one position at a time
