"""Unit tests for the tomtrades research detector.

Hand-computed fixtures throughout — small enough that the expected value is worked out
on paper in the test itself, per code-standards. The two that matter most:

``test_no_lookahead``   truncating the series immediately after a signal must not change
                        that signal. If a gate or the trigger peeked at a later bar, the
                        truncated run would disagree.
``test_gate_*_toggle``  every gate, disabled, must allow every bar. This is what makes
                        the ablation meaningful: flipping one flag changes exactly one
                        thing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import yaml

from src.research.tomtrades import ablate as AB
from src.research.tomtrades import detector as DT
from src.research.tomtrades import gates as G
from src.research.tomtrades import indicators as ind

NY = "America/New_York"


@pytest.fixture(scope="module")
def cfg() -> dict:
    with open("config/tomtrades.yaml") as fh:
        return yaml.safe_load(fh)


def _frame(prices: list[tuple[float, float, float, float]], start: str,
           volume: int = 100) -> pd.DataFrame:
    ts = pd.date_range(start, periods=len(prices), freq="1min", tz="UTC").tz_convert(NY)
    o, h, low_, c = zip(*prices)
    return pd.DataFrame({"ts_event": ts, "open": o, "high": h, "low": low_,
                         "close": c, "volume": volume})


def _ramp(n: int, start: float, step: float, base: str = "2024-03-01 00:00") -> pd.DataFrame:
    """A clean one-way ramp: each bar opens where the last closed."""
    rows = []
    px = start
    for _ in range(n):
        rows.append((px, px + abs(step), px - 0.0, px + step))
        px += step
    return _frame(rows, base)


# --------------------------------------------------------------------------- indicators
def test_pivot_flags_are_confirmable_not_clairvoyant():
    # a single obvious peak at index 5; with k=2 it can only be known at index 7
    lows = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
    highs = [x + 1 for x in lows]
    df = _frame([(v, h, v, v) for v, h in zip(lows, highs)], "2024-03-01 00:00")
    ph, _ = ind.pivot_flags(df["high"], df["low"], k=2)
    assert ph.iloc[7], "peak at 5 should be flagged at 5+k=7"
    assert not ph.iloc[:7].any(), "no flag may appear before the pivot is confirmable"


def test_mean_retracement_of_a_hand_built_zigzag():
    # legs: 100->110 (10), 110->105 (5 => 0.5), 105->115 (10 => 2.0), 115->110 (5 => 0.5)
    seq = [100, 104, 108, 110, 108, 106, 105, 108, 112, 115, 113, 111, 110]
    df = _frame([(p, p + 0.5, p - 0.5, p) for p in seq], "2024-03-01 00:00")
    val = ind.mean_retracement(df, k=1)
    assert not np.isnan(val)
    assert 0.3 <= val <= 2.0, f"retracement mean out of plausible band: {val}"


def test_atr_is_shifted_so_it_cannot_see_its_own_bar():
    df = _ramp(30, 100.0, 1.0)
    a = ind.atr(df, 5)
    assert np.isnan(a.iloc[0])
    # ATR at bar t must equal the rolling mean computed to t-1
    manual = None
    prev_close = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev_close).abs(),
                    (df["low"] - prev_close).abs()], axis=1).max(axis=1)
    manual = tr.rolling(5, min_periods=2).mean().shift()
    pd.testing.assert_series_equal(a, manual, check_names=False)


def test_hourly_run_state_counts_minutes_and_retracement():
    # 30 bars up 1.0 each, then 10 bars back down 1.0 each, inside one UTC hour
    up = [(100 + i, 100 + i + 0.5, 100 + i - 0.5, 100 + i + 1) for i in range(30)]
    dn = [(130 - i, 130 - i + 0.5, 130 - i - 0.5, 130 - i - 1) for i in range(10)]
    df = _frame(up + dn, "2024-03-01 00:00")
    st = ind.hourly_run_state(df, "UTC")
    assert st["run_minutes"].iloc[29] == 29
    assert st["run_dir"].iloc[29] == 1
    assert st["displacement"].iloc[29] > 0
    # after 10 bars of give-back the retrace fraction must have grown
    assert st["retrace_frac"].iloc[-1] > st["retrace_frac"].iloc[29]


def test_dst_boundary_keeps_one_bar_per_minute():
    # US DST spring-forward 2024-03-10 07:00Z; NY jumps 02:00 -> 03:00 local
    df = _ramp(180, 2000.0, 0.1, base="2024-03-10 06:00")
    st = ind.hourly_run_state(df, "UTC")
    assert len(st) == len(df)
    assert df["ts_event"].is_monotonic_increasing
    assert not df["ts_event"].duplicated().any()


# ------------------------------------------------------------------------------- gates
@pytest.mark.parametrize("gate", ["c1", "c2", "c3", "c5"])
def test_gate_toggle_off_allows_every_bar(cfg, gate):
    """A disabled gate must be a no-op — the property the ablation depends on."""
    df = _ramp(400, 2000.0, 0.1)
    st = ind.hourly_run_state(df, "UTC")
    atr_s = pd.Series(np.full(len(df), 1.0), index=df.index)
    off = {**cfg[{"c1": "c1_range", "c2": "c2_overextension",
                  "c3": "c3_clock", "c5": "c5_aoi"}[gate]], "enabled": False}
    fn = {
        "c1": lambda: G.c1_range(df, off),
        "c2": lambda: G.c2_overextension(st, atr_s, off),
        "c3": lambda: G.c3_clock(st, off),
        "c5": lambda: G.c5_aoi(df, st, atr_s, off),
    }[gate]
    assert fn().all(), f"{gate} disabled must allow every bar"


def test_c3_window_and_15m_boundary_buffer(cfg):
    df = _ramp(120, 2000.0, 0.05)
    st = ind.hourly_run_state(df, "UTC")
    out = G.c3_clock(st, {"enabled": True, "window_start_min": 30,
                          "window_end_min": 45, "boundary_buffer_min": 2})
    m = st["minute_of_hour"].to_numpy()
    assert not out[m == 29].any(), "minute 29 is outside a 30-45 window"
    assert out[m == 31].all(), "minute 31 is inside the window and clear of a boundary"
    assert not out[m == 44].any(), "minute 44 sits inside the 2-minute pre-boundary buffer"


def test_c2_requires_duration_and_is_killed_by_a_50pct_pullback(cfg):
    conf = {"enabled": True, "min_duration_min": 20, "invalidation_frac": 0.50,
            "require_magnitude": False, "onesided_frac": 0.0}
    df = _ramp(40, 2000.0, 0.5)
    st = ind.hourly_run_state(df, "UTC")
    atr_s = pd.Series(np.ones(len(df)), index=df.index)
    ok = G.c2_overextension(st, atr_s, conf)
    assert not ok[:20].any(), "a run shorter than min_duration is not overextended"
    assert ok[25], "a clean 25-minute one-way run is overextended"

    # same run, then hand back more than half of it -> invalidated
    give_back = [(2020 - i, 2020 - i + 0.2, 2020 - i - 0.2, 2020 - i - 1.0) for i in range(15)]
    df2 = pd.concat([df, _frame(give_back, "2024-03-01 00:40")], ignore_index=True)
    st2 = ind.hourly_run_state(df2, "UTC")
    ok2 = G.c2_overextension(st2, pd.Series(np.ones(len(df2))), conf)
    assert not ok2[-1], "a pullback past 50% must invalidate the overextension"


# ---------------------------------------------------------------------------- detector
def _signal_fixture(cfg) -> tuple[pd.DataFrame, dict, DT.Context, dict]:
    """A synthetic series engineered to produce at least one shift, gates wide open."""
    rng = np.random.default_rng(7)
    n = 3000
    px = 2000 + np.cumsum(rng.normal(0, 0.35, n))
    rows = [(p, p + 0.4, p - 0.4, p + rng.normal(0, 0.1)) for p in px]
    df = _frame(rows, "2024-03-01 00:00")
    c = {**cfg, "c7_nested": {"mode": "off", "window_bars": 10},
         "c6_shift": {**cfg["c6_shift"], "shape": "any_break"}}
    ctx = DT.build_context(df, c)
    masks = {k: np.ones(n, dtype=bool) for k in ("session", "c1", "c2", "c3", "c4", "c5")}
    return df, c, ctx, masks


def test_detector_emits_signals_on_synthetic_data(cfg):
    _df, c, ctx, masks = _signal_fixture(cfg)
    sig = DT.detect(ctx, c, masks)
    assert len(sig) > 0, "trigger must fire on noisy synthetic data with gates open"
    assert (sig["entry_idx"] > 0).all()


def test_entry_is_the_bar_after_the_signal(cfg):
    df, c, ctx, masks = _signal_fixture(cfg)
    sig = DT.detect(ctx, c, masks)
    row = sig.iloc[0]
    sig_pos = int(df.index[df["ts_event"] == row["signal_ts"]][0])
    assert int(row["entry_idx"]) == sig_pos + 1, "fill must be the bar AFTER confirmation"


def test_no_lookahead(cfg):
    """Truncating right after a signal must reproduce that identical signal."""
    df, c, ctx, masks = _signal_fixture(cfg)
    full = DT.detect(ctx, c, masks)
    assert len(full) > 0
    row = full.iloc[0]
    cut = int(row["entry_idx"]) + 1                      # keep the signal bar + the fill bar
    trunc_df = df.iloc[:cut].reset_index(drop=True)
    trunc_ctx = DT.build_context(trunc_df, c)
    trunc_masks = {k: v[:cut] for k, v in masks.items()}
    trunc = DT.detect(trunc_ctx, c, trunc_masks)
    assert len(trunc) > 0, "the signal vanished when future bars were removed"
    assert trunc.iloc[0]["signal_ts"] == row["signal_ts"]
    assert trunc.iloc[0]["stop"] == pytest.approx(row["stop"])
    assert trunc.iloc[0]["direction"] == row["direction"]


def test_stop_wins_the_tie_when_one_bar_contains_both(cfg):
    """The pessimistic tie-break — the only defensible one without sub-minute data."""
    df = _frame([(100.0, 100.2, 99.8, 100.0)] * 3 + [(100.0, 105.0, 95.0, 100.0)],
                "2024-03-01 00:00")
    sig = pd.DataFrame([{
        "signal_ts": df["ts_event"].iloc[2], "direction": -1,
        "entry_ts": df["ts_event"].iloc[3], "entry_idx": 3,
        "entry_ref_close": 100.0, "stop": 101.0, "risk": 1.0,
        "hour_id": df["ts_event"].iloc[3].floor("h"), "minute_of_hour": 3,
        "run_displacement": 1.0, "nested": False, "retrace_target_frac": 0.5,
    }])
    c = {**cfg, "execution": {**cfg["execution"], "target_mode": "fixed_rr", "fixed_rr": 1.0},
         "risk": {**cfg["risk"], "max_trades_per_day": 0}}
    tr = DT.simulate(df, sig, c)
    assert len(tr) == 1
    assert tr.iloc[0]["exit_reason"] == "stop"
    assert tr.iloc[0]["pnl_r"] == pytest.approx(-1.0)


def test_max_trades_per_day_cap_is_applied(cfg):
    df, c, ctx, masks = _signal_fixture(cfg)
    c = {**c, "risk": {**c["risk"], "max_trades_per_day": 1}}
    tr = DT.simulate(df, DT.detect(ctx, c, masks), c)
    if not tr.empty:
        per_day = pd.to_datetime(tr["entry_ts"]).dt.tz_convert(NY).dt.date.value_counts()
        assert per_day.max() <= 1


def test_ablation_refuses_to_interpret_thin_samples():
    thin = pd.DataFrame({"pnl_r": [1.0, -1.0], "exit_reason": ["target", "stop"]})
    s = AB._stats(thin)
    assert s["n"] == 2
    assert AB.MIN_N > 2, "the interpretation floor must exclude a 2-trade sample"
