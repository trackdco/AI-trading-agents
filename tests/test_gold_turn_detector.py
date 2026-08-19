"""Constructed-bar self-tests for the second-derivative turn detector, mandatory before
any run touches data per this repo's convention (`tests/test_orb_engine.py`).

`ema_span=1` makes the EMA equal to raw close exactly (alpha = 2/(1+1) = 1), which lets
several tests control the sign of the second derivative directly through hand-picked
closing prices rather than through an opaque smoother — the crossing/hold/direction/stop
logic is exercised deterministically without also depending on EMA convergence.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.research.orb.engine import Config, daily_context, prep, run
from src.research.gold.turn_detector import _bars5, build_signal, turn_candidates_all

NY = "America/New_York"

# A hand-computed sequence: d2 is a constant -2 through index 4, flips to a constant +2
# at index 5 (t0), holds +2 through indices 6 and 7 (confirmation at 7), so the crossing
# is unambiguous and reproduced by hand in the docstring test above.
DOWN_UP = [100, 97, 92, 85, 76, 69, 64, 61, 60, 61]
# The mirror: concave-up decelerating into a top, flips to concave-down and holds -> short.
UP_DOWN = [100, 103, 108, 115, 124, 131, 136, 139, 140, 139]


def bars5_from(closes, start="2024-01-03 10:00", vol=100.0) -> pd.DataFrame:
    ts = pd.date_range(start, periods=len(closes), freq="5min", tz=NY)
    b = pd.DataFrame({"open": closes, "high": closes, "low": closes, "close": closes,
                      "volume": [vol] * len(closes), "ts": ts})
    b["tmin"] = b.ts.dt.hour * 60 + b.ts.dt.minute
    b["cal"] = b.ts.dt.normalize()
    return b


# --------------------------------------------------------------------------
# the crossing / hold / direction / stop logic, isolated from resampling
# --------------------------------------------------------------------------

def test_down_up_curvature_flip_is_a_long_after_holding_two_bars():
    b5 = bars5_from(DOWN_UP)
    c = turn_candidates_all(b5, ema_span=1, hold_bars=2, cooldown_bars=0, stop_lookback=2)
    assert len(c) == 1
    r = c.iloc[0]
    assert r.t0 == 5 and r.direction == 1
    assert r.signal_tmin == int(b5.tmin.iloc[7])     # confirmation = t0 + hold_bars
    assert r.fill_tmin == int(b5.tmin.iloc[8])        # fill = the NEXT bar's open
    assert r.stop_ref == pytest.approx(61 - 0.10)     # min low over [t0-2, t0+2]


def test_up_down_curvature_flip_is_a_short():
    b5 = bars5_from(UP_DOWN)
    c = turn_candidates_all(b5, ema_span=1, hold_bars=2, cooldown_bars=0, stop_lookback=2)
    assert len(c) == 1
    r = c.iloc[0]
    assert r.direction == -1
    assert r.stop_ref == pytest.approx(139 + 0.10)    # max high over the same window


def test_hold_must_be_the_SAME_sign_for_BOTH_subsequent_bars():
    """A flip that reverses again one bar later never confirms — it is noise, not a turn."""
    closes = [100, 97, 92, 85, 76, 69, 68, 61, 60, 61]  # d2 flips at 5 but breaks at 6
    b5 = bars5_from(closes)
    c = turn_candidates_all(b5, ema_span=1, hold_bars=2, cooldown_bars=0, stop_lookback=2)
    assert c.empty


def test_no_signal_from_pure_linear_price():
    """A straight line has zero curvature everywhere: no crossing is possible."""
    b5 = bars5_from(list(range(100, 100 + 40)))
    c = turn_candidates_all(b5, ema_span=1, hold_bars=2, cooldown_bars=0)
    assert c.empty


def test_no_false_crossing_at_the_very_start_of_the_series():
    """d2 is undefined (NaN -> sign 0) for the first two bars of any series. Reading that
    placeholder zero as a real prior sign would register a false crossing at bar index 2
    on every run — a warm-up artifact, not a signal."""
    b5 = bars5_from(DOWN_UP)
    c = turn_candidates_all(b5, ema_span=1, hold_bars=2, cooldown_bars=0, stop_lookback=2)
    assert (c.t0 == 2).sum() == 0
    assert len(c) == 1                                # only the real crossing at t0=5


# --------------------------------------------------------------------------
# cooldown — BR-9/BR-10, one signal per fight
# --------------------------------------------------------------------------

def test_cooldown_suppresses_a_second_same_direction_signal():
    closes = DOWN_UP + [58, 55, 50, 41, 30, 17, 12, 9, 8, 9]   # a second down-up flip soon after
    b5 = bars5_from(closes)
    loose = turn_candidates_all(b5, ema_span=1, hold_bars=2, cooldown_bars=0)
    tight = turn_candidates_all(b5, ema_span=1, hold_bars=2, cooldown_bars=100)
    assert len(loose) == 2 and len(tight) == 1
    assert tight.iloc[0].t0 == loose.iloc[0].t0       # the FIRST of the pair survives


def test_cooldown_does_not_block_the_opposite_direction():
    """A down-up flip immediately followed by an up-down flip is a legitimate whipsaw,
    not noise to be suppressed — cooldown is keyed per direction."""
    closes = DOWN_UP + UP_DOWN
    b5 = bars5_from(closes)
    c = turn_candidates_all(b5, ema_span=1, hold_bars=2, cooldown_bars=100)
    assert len(c) == 2 and set(c.direction) == {1, -1}


# --------------------------------------------------------------------------
# volume confirmation
# --------------------------------------------------------------------------

def test_volume_gate_blocks_a_quiet_confirmation_bar():
    b5 = bars5_from(DOWN_UP, vol=100.0)
    b5.loc[7, "volume"] = 50.0                        # the confirmation bar itself is quiet
    assert turn_candidates_all(b5, ema_span=1, cooldown_bars=0, vol_mult=1.5,
                               vol_lookback=5).empty
    b5.loc[7, "volume"] = 500.0
    assert len(turn_candidates_all(b5, ema_span=1, cooldown_bars=0, vol_mult=1.5,
                                   vol_lookback=5)) == 1


def test_volume_baseline_excludes_the_bar_it_judges():
    """The confirmation bar's own volume must not inflate the baseline it is compared to."""
    b5 = bars5_from(DOWN_UP, vol=100.0)
    b5.loc[7, "volume"] = 1e6                          # a spike ON the judged bar
    assert turn_candidates_all(b5, ema_span=1, cooldown_bars=0, vol_mult=1.5,
                               vol_lookback=5).iloc[0] is not None  # still fires: 1e6 >= 1.5x prior mean(100)
    # a spike the bar BEFORE would corrupt the baseline if the shift were missing
    b5b = bars5_from(DOWN_UP, vol=100.0)
    b5b.loc[6, "volume"] = 1e6
    b5b.loc[7, "volume"] = 140.0                        # 1.4x a plain 100-baseline -> should FAIL 1.5x
    assert turn_candidates_all(b5b, ema_span=1, cooldown_bars=0, vol_mult=1.5,
                               vol_lookback=5).empty


# --------------------------------------------------------------------------
# 1m -> 5m resampling
# --------------------------------------------------------------------------

def test_bars5_aggregates_ohlcv_correctly():
    ts = pd.date_range("2024-01-03 10:00", periods=10, freq="1min", tz=NY)
    b = pd.DataFrame({"ts_event": ts, "open": np.arange(10) + 100.0,
                      "high": np.arange(10) + 101.0, "low": np.arange(10) + 99.0,
                      "close": np.arange(10) + 100.5, "volume": [10.0] * 10})
    b5 = _bars5(b)
    assert len(b5) == 2
    first = b5.iloc[0]
    assert first.open == 100.0 and first.close == b.close.iloc[4]
    assert first.high == b.high.iloc[:5].max() and first.low == b.low.iloc[:5].min()
    assert first.volume == 50.0


def test_bars5_bins_on_absolute_time_not_per_day():
    """No anchor, no reset: bins are absolute 5-minute epoch buckets, so nothing about the
    binning depends on which calendar day a bar falls in. A whole-hour UTC offset (ET is
    always -4 or -5) means these epoch-aligned bins also land on ordinary clock 5-minute
    marks. Real data has a maintenance gap 17:00-18:00 ET most weekdays -- constructed here
    directly, rather than merged/misread as one bin spanning the closure."""
    before = pd.date_range("2024-01-03 16:55", periods=5, freq="1min", tz=NY)   # one full bin
    after = pd.date_range("2024-01-03 18:00", periods=5, freq="1min", tz=NY)    # next, post-gap
    ts = list(before) + list(after)
    b = pd.DataFrame({"ts_event": ts, "open": [1.0] * 10, "high": [1.0] * 10,
                      "low": [1.0] * 10, "close": [1.0] * 10, "volume": [1.0] * 10})
    b5 = _bars5(b)
    assert len(b5) == 2
    assert (b5.tmin % 5 == 0).all()                   # both bins land on a clock 5-mark
    assert b5.tmin.iloc[0] == 16 * 60 + 55 and b5.tmin.iloc[1] == 18 * 60
    assert b5.tmin.iloc[1] - b5.tmin.iloc[0] == 65     # the gap is preserved, not collapsed


# --------------------------------------------------------------------------
# full pipeline: build_signal() -> engine.run() -> a real trade
# --------------------------------------------------------------------------

def five_min_1m_bars(closes, start="2024-01-03 09:30", base=2000.0) -> pd.DataFrame:
    """One 1-minute bar per 5-minute close, all flat within the block (open=high=low=close
    at every intermediate minute) so the 5m aggregation reproduces `closes` exactly."""
    ts0 = pd.Timestamp(start, tz=NY)
    rows = []
    for i, c in enumerate(closes):
        for m in range(5):
            t = ts0 + pd.Timedelta(minutes=5 * i + m)
            rows.append({"ts_event": t, "open": c, "high": c, "low": c, "close": c,
                        "volume": 100.0})
    return pd.DataFrame(rows)


def test_build_signal_produces_a_real_trade_through_the_full_harness():
    b1 = five_min_1m_bars(DOWN_UP)
    bars = prep(b1)
    ctx = daily_context(bars, 14)
    sig = build_signal(bars, ema_span=1, hold_bars=2, cooldown_bars=0, stop_lookback=2)
    t = run(bars, Config(cutoff=None, flat_minutes=600, max_trades_per_day=5,
                        target_r=1.5, risk_mode="off"), ctx, signal_fn=sig)
    # DOWN_UP is still declining at the fill bar (index 8 = 60, one below the computed
    # 60.9 stop) -- exactly the case the wrong-side-of-entry guard exists for, so THIS
    # candidate is correctly rejected below. For an end-to-end trade, the confirmation
    # (indices 0-7, unchanged) is identical, but the FILL bar itself (index 8) is raised
    # above the stop so the entry is valid -- appending data AFTER index 8 cannot do this,
    # since the fill price is fixed at index 8's own open the moment t0=5 is confirmed.
    UP_AT_FILL = DOWN_UP[:8] + [61.5, 65.0, 68.0, 70.0]
    b1b = five_min_1m_bars(UP_AT_FILL)
    barsb = prep(b1b)
    ctxb = daily_context(barsb, 14)
    sigb = build_signal(barsb, ema_span=1, hold_bars=2, cooldown_bars=0, stop_lookback=2)
    tb = run(barsb, Config(cutoff=None, flat_minutes=600, max_trades_per_day=5,
                          target_r=1.5, risk_mode="off"), ctxb, signal_fn=sigb)
    assert len(tb) == 1
    r = tb.iloc[0]
    assert r["dir"] == 1
    assert r.entry == 61.5            # the fill bar's open (index 8, raised above stop)
    assert r.stop == pytest.approx(60.9)
    assert r.sig_ema_span == 1


def test_a_stop_on_the_wrong_side_of_entry_is_rejected_not_mispriced():
    """If price keeps moving between the confirmation bar and the fill bar, a stop
    computed from bars strictly before the fill can end up on the WRONG side of the
    entry it is meant to protect. Taking that trade would let `_walk()` exit on bar one
    at a price the sign convention records as a WIN -- a "stop" that is arithmetically
    favourable. The harness must refuse the trade instead of mispricing it."""
    b1 = five_min_1m_bars(DOWN_UP)         # price is still falling at the fill bar
    bars = prep(b1)
    ctx = daily_context(bars, 14)
    sig = build_signal(bars, ema_span=1, hold_bars=2, cooldown_bars=0, stop_lookback=2)
    t = run(bars, Config(cutoff=None, flat_minutes=600, max_trades_per_day=5,
                        target_r=1.5, risk_mode="off"), ctx, signal_fn=sig)
    assert t.empty


def test_truncating_the_future_cannot_change_a_confirmed_candidate():
    """The mandatory no-lookahead pattern (`tests/test_orb_engine.py`), applied to the
    signal generator itself: nothing after the fill bar may change what was decided."""
    b1 = five_min_1m_bars(DOWN_UP[:8] + [61.5, 200, 200, 200, 200])  # entry above the
    full = prep(b1)                       # stop (see the fill-bar note above), + future bars
    cut = full[full.ts_event <= pd.Timestamp("2024-01-03 09:30", tz=NY)
              + pd.Timedelta(minutes=5 * 9 + 4)]                 # through the fill bar
    ctx_f, ctx_c = daily_context(full, 14), daily_context(cut, 14)
    sig_f = build_signal(full, ema_span=1, hold_bars=2, cooldown_bars=0, stop_lookback=2)
    sig_c = build_signal(cut, ema_span=1, hold_bars=2, cooldown_bars=0, stop_lookback=2)
    cfg = Config(cutoff=None, flat_minutes=600, max_trades_per_day=5, target_r=1.5,
                risk_mode="off")
    a = run(full, cfg, ctx_f, signal_fn=sig_f).iloc[0]
    b = run(cut, cfg, ctx_c, signal_fn=sig_c).iloc[0]
    for k in ("entry", "stop", "dir", "sig_t0_tmin"):
        assert a[k] == b[k], k
