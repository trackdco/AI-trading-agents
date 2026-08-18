"""Deterministic constructed-bar self-tests for the ORB v3 engine.

Mandated by references/tv-findings.md: every v3 mechanism gets a self-test on hand-built
bars before it is allowed near data. The cautionary example named there is the v2 Pine
consec-loss latch that reset only on a win and so halted the strategy permanently — so
the breaker tests below assert the RESET as hard as they assert the halt.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.research.orb.engine import (NY, Config, daily_context, prep, run)

FLAT, OPEN = 570, 570          # 09:30


def day_bars(date: str, path: dict[int, tuple], base: float = 2000.0,
             first: int = 570, last: int = 960, vol: float = 100.0) -> pd.DataFrame:
    """1m bars for one day. `path` maps minute-of-day -> (o,h,l,c); rest are flat."""
    rows = []
    for m in range(first, last + 1):
        o, h, l_, c = path.get(m, (base, base, base, base))
        rows.append({"ts_event": pd.Timestamp(f"{date} {m//60:02d}:{m%60:02d}", tz=NY),
                     "open": o, "high": h, "low": l_, "close": c, "volume": vol})
    return pd.DataFrame(rows)


def orday(date: str, hi: float, lo: float, after: dict[int, tuple],
          base: float = 2000.0) -> pd.DataFrame:
    """A day whose 09:30-09:44 range is exactly [lo, hi], then a given path."""
    path = {570: (base, hi, lo, base)}       # the whole OR in the first minute
    for m in range(571, 585):
        path[m] = (base, base, base, base)
    path.update(after)
    return day_bars(date, path, base=base)


def go(days, cfg: Config):
    b = prep(pd.concat(days, ignore_index=True))
    return run(b, cfg, daily_context(b, cfg.atr_days))


def step(mod: int, px: float, base: float = 2000.0) -> dict:
    """One minute that trades to `px` and closes there."""
    return {mod: (base, max(base, px), min(base, px), px)}


# --------------------------------------------------------------------------
# v1 core
# --------------------------------------------------------------------------

def test_long_breakout_hits_target():
    # OR [1990, 2010]; the 09:45-09:59 candle closes at 2012 -> fill at 10:00 open
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    after[601] = (2012, 2050, 2012, 2050)          # runs up
    t = go([orday("2024-01-03", 2010, 1990, after)], Config())
    assert len(t) == 1
    r = t.iloc[0]
    assert r["dir"] == 1 and r.entry == 2012 and r.stop == 1990
    assert r.risk_pts == pytest.approx(22.0)
    assert r.reason == "target"
    assert r.exit_px == pytest.approx(2012 + 1.5 * 22)
    assert r.r == pytest.approx(1.5)


def test_short_breakout_hits_stop():
    after = {**step(599, 1988), 600: (1988, 1988, 1988, 1988),
             601: (1988, 2010, 1988, 2010)}
    t = go([orday("2024-01-03", 2010, 1990, after)], Config())
    r = t.iloc[0]
    assert r["dir"] == -1 and r.stop == 2010 and r.reason == "stop"
    assert r.r == pytest.approx(-1.0)


def test_no_close_outside_means_no_trade():
    t = go([orday("2024-01-03", 2010, 1990, {})], Config())
    assert t.empty


def test_forced_flat_at_240_minutes():
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    t = go([orday("2024-01-03", 2010, 1990, after)], Config())
    r = t.iloc[0]
    assert r.reason == "flat" and r.exit_min == 600 + 240


def test_one_trade_per_day_cap():
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012),
             601: (2012, 2012, 1990, 1990)}       # stops out
    after.update({m: (1985, 1985, 1985, 1985) for m in range(602, 620)})
    t = go([orday("2024-01-03", 2010, 1990, after)], Config())
    assert len(t) == 1


def test_both_touched_bar_is_pessimistic_by_default():
    """One bar spans stop and target: the stop wins unless optimistic=True."""
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012),
             601: (2012, 2100, 1980, 2000)}
    base = orday("2024-01-03", 2010, 1990, after)
    assert go([base], Config()).iloc[0].reason == "stop"
    assert go([base], Config(optimistic=True)).iloc[0].reason == "target"


def test_slippage_costs_R_even_when_it_flatters_points():
    """A subtle one worth pinning: with an R-multiple target and an opposite-side stop,
    entry slippage widens the risk, which widens the target by 1.5x as much. The trade
    therefore banks MORE POINTS while earning LESS R. Judge slippage in R — which is
    exactly why the skill puts R first."""
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012),
             601: (2012, 2050, 2012, 2050)}
    d = orday("2024-01-03", 2010, 1990, after)
    a = go([d], Config()).iloc[0]
    b = go([d], Config(slip_ticks=1)).iloc[0]
    assert b.entry > a.entry                      # filled worse
    assert b.risk_pts > a.risk_pts                # so risk is wider
    assert b.pnl_pts > a.pnl_pts                  # and the 1.5R target is further away
    assert b.r < a.r                              # but the trade is worse in R


def test_slippage_is_unambiguously_adverse_on_a_loser():
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012),
             601: (2012, 2012, 1985, 1985)}
    d = orday("2024-01-03", 2010, 1990, after)
    a = go([d], Config()).iloc[0]
    b = go([d], Config(slip_ticks=1)).iloc[0]
    assert b.pnl_pts < a.pnl_pts and b.pnl_usd < a.pnl_usd


# --------------------------------------------------------------------------
# v3 (a) hard risk cap
# --------------------------------------------------------------------------

def test_risk_cap_pulls_the_stop_in():
    after = {**step(599, 2062), 600: (2062, 2062, 2062, 2062)}
    d = orday("2024-01-03", 2060, 1960, after)          # 100-pt OR
    assert go([d], Config()).iloc[0].risk_pts == pytest.approx(102.0)
    c = go([d], Config(risk_mode="cap", max_risk_pts=30)).iloc[0]
    assert c.risk_pts == pytest.approx(30.0) and c.stop == pytest.approx(2032.0)
    assert bool(c.capped)


def test_risk_cap_skip_mode_stands_aside():
    after = {**step(599, 2062), 600: (2062, 2062, 2062, 2062)}
    d = orday("2024-01-03", 2060, 1960, after)
    assert go([d], Config(risk_mode="skip", max_risk_pts=30)).empty


def test_risk_cap_leaves_a_narrow_range_alone():
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    d = orday("2024-01-03", 2010, 1990, after)
    c = go([d], Config(risk_mode="cap", max_risk_pts=30)).iloc[0]
    assert c.risk_pts == pytest.approx(22.0) and not bool(c.capped)


# --------------------------------------------------------------------------
# v3 (b) profit ratchet
# --------------------------------------------------------------------------

def test_ratchet_locks_in_a_quarter_R_after_one_R():
    """Touch +1R on bar A, give it all back on bar B -> exit at +0.25R, not the stop."""
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012),
             601: (2012, 2034, 2012, 2030),      # +1.0R = 2012+22 = 2034, touched
             602: (2030, 2030, 1985, 1985)}      # collapses through the old stop
    t = go([orday("2024-01-03", 2010, 1990, after)], Config(ratchet=True))
    r = t.iloc[0]
    assert r.reason == "ratchet"
    assert r.exit_px == pytest.approx(2012 + 0.25 * 22)
    assert r.r == pytest.approx(0.25)


def test_ratchet_cannot_fill_on_its_own_trigger_bar():
    """1m OHLC does not order its extremes, so the lock arms for LATER bars only."""
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012),
             601: (2012, 2034, 1985, 1990)}      # +1R and the stop in ONE bar
    r = go([orday("2024-01-03", 2010, 1990, after)], Config(ratchet=True)).iloc[0]
    assert r.reason == "stop" and r.r == pytest.approx(-1.0)


def test_ratchet_off_gives_the_loss_back():
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012),
             601: (2012, 2034, 2012, 2030), 602: (2030, 2030, 1985, 1985)}
    r = go([orday("2024-01-03", 2010, 1990, after)], Config()).iloc[0]
    assert r.reason == "stop" and r.r == pytest.approx(-1.0)


# --------------------------------------------------------------------------
# v3 (c) time stop
# --------------------------------------------------------------------------

def test_time_stop_scratches_a_stalled_trade():
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    after.update({m: (2013, 2013, 2013, 2013) for m in range(601, 760)})
    r = go([orday("2024-01-03", 2010, 1990, after)],
           Config(time_stop_min=90, time_stop_r=0.5)).iloc[0]
    assert r.reason == "time_stop" and r.exit_min == 690


def test_time_stop_spares_a_trade_already_past_the_threshold():
    up = 2012 + 0.6 * 22
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    after.update({m: (up, up, up, up) for m in range(601, 900)})
    r = go([orday("2024-01-03", 2010, 1990, after)],
           Config(time_stop_min=90, time_stop_r=0.5)).iloc[0]
    assert r.reason == "flat"


# --------------------------------------------------------------------------
# v3 (d)(e)(f) gates
# --------------------------------------------------------------------------

def test_vwap_gate_blocks_a_long_below_vwap():
    """Heavy overnight volume up at 2100 drags session VWAP above the breakout price.

    VWAP is anchored to the 18:00 ET CME open, so the prior evening's bars are part of
    the same session and must count — that is exactly what the anchor choice means.
    """
    evening = day_bars("2024-01-02", {}, base=2100.0, first=1080, last=1439, vol=1e5)
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    cur = orday("2024-01-03", 2010, 1990, after)
    assert go([evening, cur], Config(vwap_gate=True)).empty
    assert len(go([evening, cur], Config())) == 1


def test_pdc_gate_blocks_a_long_below_the_prior_close():
    prev = day_bars("2024-01-03", {960: (2200, 2200, 2200, 2200)})
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    cur = orday("2024-01-04", 2010, 1990, after)
    assert go([prev, cur], Config(pdc_gate=True)).empty
    assert len(go([prev, cur], Config())) == 1


def test_weekday_skip():
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    mon = orday("2024-01-08", 2010, 1990, after)      # a Monday
    assert mon.ts_event.dt.dayofweek.iloc[0] == 0
    assert go([mon], Config(skip_weekdays=(0,))).empty
    assert len(go([mon], Config())) == 1


# --------------------------------------------------------------------------
# v3 (g) breakers
# --------------------------------------------------------------------------

def _loser(date: str) -> pd.DataFrame:
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012),
             601: (2012, 2012, 1985, 1985)}
    after.update({m: (1985, 1985, 1985, 1985) for m in range(602, 700)})
    return orday(date, 2010, 1990, after)


def test_three_consecutive_losses_halt_trading():
    days = [_loser(d) for d in ("2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05")]
    assert len(go(days, Config())) == 4
    assert len(go(days, Config(consec_loss_halt=3))) == 3


def test_consecutive_loss_counter_RESETS_WEEKLY():
    """The v2 Pine bug: the latch reset only on a win, so a halt was permanent."""
    wk1 = [_loser(d) for d in ("2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05")]
    wk2 = [_loser(d) for d in ("2024-01-08", "2024-01-09")]
    t = go(wk1 + wk2, Config(consec_loss_halt=3))
    got = sorted(str(c)[:10] for c in t.cal)
    assert got == ["2024-01-02", "2024-01-03", "2024-01-04",
                   "2024-01-08", "2024-01-09"], got


def test_weekly_stop_halts_the_rest_of_the_week():
    wk1 = [_loser(d) for d in ("2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05")]
    wk2 = [_loser("2024-01-08")]
    t = go(wk1 + wk2, Config(weekly_stop_r=-2.0))
    got = sorted(str(c)[:10] for c in t.cal)
    assert got == ["2024-01-02", "2024-01-03", "2024-01-08"], got


# --------------------------------------------------------------------------
# no lookahead
# --------------------------------------------------------------------------

def test_daily_context_is_strictly_prior_day_shifted():
    a = day_bars("2024-01-03", {960: (2200, 2200, 2200, 2200)})
    b = day_bars("2024-01-04", {960: (2500, 2500, 2500, 2500)})
    ctx = daily_context(prep(pd.concat([a, b], ignore_index=True)), 14)
    assert np.isnan(ctx.iloc[0].pdc)                       # day 1 has no prior
    assert ctx.iloc[1].pdc == 2200                          # day 2 sees day 1, not itself


def test_truncating_the_future_cannot_change_a_closed_trade():
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012),
             601: (2012, 2050, 2012, 2050)}
    full = orday("2024-01-03", 2010, 1990, after)
    cut = full[full.ts_event.dt.hour * 60 + full.ts_event.dt.minute <= 601]
    a, b = go([full], Config()).iloc[0], go([cut], Config()).iloc[0]
    for k in ("entry", "stop", "exit_px", "r", "reason"):
        assert a[k] == b[k], k


# --------------------------------------------------------------------------
# scale-free risk cap  (points are not comparable across eras)
# --------------------------------------------------------------------------

def test_atr_risk_cap_scales_with_volatility():
    """The same ATR multiple must bind at a different POINT distance in a wider market."""
    from src.research.orb.engine import daily_context as dc
    prior = [day_bars(d, {570: (2000, 2000 + w, 2000 - w, 2000)})
             for d, w in zip(pd.bdate_range("2023-12-01", periods=20).strftime("%Y-%m-%d"),
                             [10] * 20)]
    after = {**step(599, 2062), 600: (2062, 2062, 2062, 2062)}
    cur = orday("2023-12-29", 2060, 1960, after)
    t = go(prior + [cur], Config(risk_mode="cap", max_risk_atr=1.0))
    atr = dc(prep(pd.concat(prior + [cur], ignore_index=True)), 14).iloc[-1].atr
    assert len(t) == 1
    assert t.iloc[0].risk_pts == pytest.approx(atr, rel=1e-6)
    assert bool(t.iloc[0].capped)


def test_pct_of_price_risk_cap():
    after = {**step(599, 2062), 600: (2062, 2062, 2062, 2062)}
    d = orday("2024-01-03", 2060, 1960, after)
    t = go([d], Config(risk_mode="cap", max_risk_pct=1.0))     # 1% of 2062
    assert t.iloc[0].risk_pts == pytest.approx(20.62)


def test_tightest_cap_binds_when_several_are_set():
    after = {**step(599, 2062), 600: (2062, 2062, 2062, 2062)}
    d = orday("2024-01-03", 2060, 1960, after)
    t = go([d], Config(risk_mode="cap", max_risk_pts=30, max_risk_pct=1.0))
    assert t.iloc[0].risk_pts == pytest.approx(20.62)          # 1% < 30pt


# --------------------------------------------------------------------------
# Crabel contraction gate
# --------------------------------------------------------------------------

def _wide(date, w=40.0):
    return day_bars(date, {570: (2000, 2000 + w, 2000 - w, 2000)})


def _narrow(date, w=2.0, after=None):
    p = {570: (2000, 2000 + w, 2000 - w, 2000)}
    if after:
        p.update(after)
    return day_bars(date, p)


def test_nr4_gate_fires_only_after_a_narrowest_of_four_day():
    """Widths are deliberately DISTINCT: with equal ranges every day ties the rolling
    minimum and NR4 is true everywhere, which silently makes the gate a no-op."""
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    base = [_wide("2024-01-02", 30), _wide("2024-01-03", 35), _wide("2024-01-04", 40)]
    cur = orday("2024-01-08", 2010, 1990, after)
    assert len(go(base + [_narrow("2024-01-05", 5)] + [cur], Config(crabel="nr4"))) == 1
    assert go(base + [_wide("2024-01-05", 50)] + [cur], Config(crabel="nr4")).empty


def test_inside_day_gate():
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    outer = day_bars("2024-01-03", {570: (2000, 2100, 1900, 2000)})
    ins = day_bars("2024-01-04", {570: (2000, 2050, 1950, 2000)})     # inside
    cur = orday("2024-01-05", 2010, 1990, after)
    assert len(go([outer, ins, cur], Config(crabel="inside"))) == 1
    notins = day_bars("2024-01-04", {570: (2000, 2200, 1800, 2000)})  # outside
    assert go([outer, notins, cur], Config(crabel="inside")).empty


def test_crabel_flags_are_prior_day_shifted():
    """Today's own range must never set today's gate — that would be lookahead."""
    from src.research.orb.engine import daily_context as dc
    days = [_wide("2024-01-02"), _wide("2024-01-03"), _wide("2024-01-04"),
            _narrow("2024-01-05")]
    ctx = dc(prep(pd.concat(days, ignore_index=True)), 14)
    assert not bool(ctx.iloc[3].nr4)      # the NR4 day itself is NOT gated on
    days.append(_wide("2024-01-08"))
    ctx = dc(prep(pd.concat(days, ignore_index=True)), 14)
    assert bool(ctx.iloc[4].nr4)          # the day AFTER it is


# --------------------------------------------------------------------------
# participation
# --------------------------------------------------------------------------

def test_relvol_gate_blocks_a_quiet_breakout_bar():
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012)}
    hist = [orday(d, 2010, 1990, {}) for d in
            pd.bdate_range("2023-12-01", periods=20).strftime("%Y-%m-%d")]
    cur = orday("2023-12-29", 2010, 1990, after)
    cur.loc[cur.ts_event.dt.hour * 60 + cur.ts_event.dt.minute >= 585, "volume"] = 1.0
    assert go(hist + [cur], Config(min_relvol=1.5)).empty
    loud = cur.copy()
    loud.loc[loud.ts_event.dt.hour * 60 + loud.ts_event.dt.minute >= 585, "volume"] = 1e5
    assert len(go(hist + [loud], Config(min_relvol=1.5))) == 1


def test_relvol_baseline_excludes_the_bar_it_judges():
    """A bar cannot be part of its own benchmark, or a lone spike gates itself in."""
    from src.research.orb.engine import entry_frame
    days = [orday(d, 2010, 1990, {}) for d in
            pd.bdate_range("2023-12-01", periods=20).strftime("%Y-%m-%d")]
    b = prep(pd.concat(days, ignore_index=True))
    ef = entry_frame(b, 585, 15)
    g = ef[ef.slot == 0].reset_index(drop=True)
    assert np.isnan(g.relvol.iloc[0])          # nothing to compare the first one to
    assert g.relvol.iloc[15] == pytest.approx(1.0)   # flat volume -> exactly the baseline


# --------------------------------------------------------------------------
# the signal interface — the harness must not care where candidates come from
# --------------------------------------------------------------------------

def test_a_custom_signal_drops_into_the_same_harness():
    """The ORB generator is retired; the harness is not. A replacement signal supplies
    (signal_tmin, fill_tmin, direction, stop_ref) and everything downstream still runs."""
    from src.research.orb.engine import Candidate

    def always_long_at_1000(day, cfg, row, feat, anchor, or_end):
        return [Candidate(585, 600, 1, 1990.0, {"why": "fixed-time probe"})]

    after = {600: (2012, 2012, 2012, 2012), 601: (2012, 2050, 2012, 2050)}
    t = go([orday("2024-01-03", 2010, 1990, after)], Config(), )
    t2 = run(prep(orday("2024-01-03", 2010, 1990, after)), Config(),
             signal_fn=always_long_at_1000)
    assert len(t2) == 1
    r = t2.iloc[0]
    assert r["dir"] == 1 and r.entry == 2012 and r.stop == 1990
    assert r.reason == "target" and r.r == pytest.approx(1.5)
    assert r.why == "fixed-time probe"          # meta is carried onto the trade row


def test_the_cap_ratchet_and_time_stop_apply_to_a_custom_signal_too():
    from src.research.orb.engine import Candidate

    def probe(day, cfg, row, feat, anchor, or_end):
        return [Candidate(585, 600, 1, 1960.0, {})]      # 102-pt raw risk

    after = {600: (2062, 2062, 2062, 2062)}
    b = prep(orday("2024-01-03", 2060, 1960, after, base=2000.0))
    t = run(b, Config(risk_mode="cap", max_risk_pts=30), signal_fn=probe)
    assert t.iloc[0].risk_pts == pytest.approx(30.0) and bool(t.iloc[0].capped)


def test_a_failed_bias_gate_does_not_kill_the_rest_of_the_day():
    """Regression: the VWAP/PDC gates used to `break`, so one blocked candidate silently
    discarded every later one. Pine re-evaluates each bar, and so must this."""
    prev = day_bars("2024-01-03", {960: (2200, 2200, 2200, 2200)})
    # 09:45 candle closes BELOW the prior close (gate blocks), 10:00 candle closes above it
    after = {**step(599, 2012), 600: (2012, 2012, 2012, 2012),
             **step(614, 2250), 615: (2250, 2250, 2250, 2250),
             616: (2250, 2400, 2250, 2400)}
    cur = orday("2024-01-04", 2010, 1990, after)
    t = go([prev, cur], Config(pdc_gate=True))
    assert len(t) == 1, "the second candidate must still be reachable"
    assert t.iloc[0].entry_min == 615
