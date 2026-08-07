"""Tests for src/engine/snapshot.py — the snapshot builder (Spec 1, Step 5).

Golden-file test on a self-contained 1m slice (tests/fixtures/snapshot_slice.csv, Feb 9 18:00
-> Feb 11 10:00 ET) with PINNED inputs, so the golden is immune to config edits by other
sessions. Plus a no-lookahead test and the pre-09:30 daily-VWAP-only cluster rule.
"""
import json
from datetime import time
from pathlib import Path

import pandas as pd

from src.engine.indicators import IndicatorsConfig
from src.engine.sessions import SessionBox
from src.engine.snapshot import build_snapshot

NY = "America/New_York"
FIX = Path(__file__).parent / "fixtures"
GOLDEN = FIX / "snapshot_golden.json"
GATE_TS = pd.Timestamp("2026-02-11 09:48", tz=NY)


def _slice() -> pd.DataFrame:
    df = pd.read_csv(FIX / "snapshot_slice.csv")
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(NY)
    return df


def _params() -> dict:
    """Fully pinned inputs so the snapshot depends only on the slice, not on config files."""
    return dict(
        ind_cfg=IndicatorsConfig(
            bb_length=20, bb_mult=2.0, entry_tfs=["1min", "2min", "3min", "5min"],
            ny_anchor=time(9, 30), ny_bands=[1, 2, 3], daily_anchor=time(18, 0),
            daily_bands=[1, 2, 3], vwap_source="hlc3", vp_bin_points=0.25,
            vp_value_area_pct=70, vp_weekly_enabled=False),
        boxes=[SessionBox(name="asia", start=time(18, 0), end=time(3, 0)),
               SessionBox(name="london", start=time(3, 0), end=time(9, 30)),
               SessionBox(name="ny", start=time(9, 30), end=time(16, 0))],
        calendar=pd.DataFrame({
            "datetime_ET": [pd.Timestamp("2026-02-10 08:30", tz=NY),
                            pd.Timestamp("2026-02-11 08:30", tz=NY)],
            "event": ["Core Retail Sales", "Non-Farm Employment Change"],
            "impact": ["high", "high"]}),
        cluster_tol=10.0, data_window_min=15, cluster_min_types=2)


def _build(df=None):
    return build_snapshot(df if df is not None else _slice(), GATE_TS, **_params())


# ------------------------------------------------------------------ golden file

def test_golden_snapshot_matches_fixture():
    snap = _build()
    got = json.loads(snap.model_dump_json())
    expected = json.loads(GOLDEN.read_text())
    assert got == expected, "snapshot drifted from golden — review, and if intended, regen the golden"


def test_snapshot_pydantic_validates_and_json_roundtrips():
    snap = _build()
    assert snap.ref_price is not None
    assert snap.session == "ny"
    assert snap.htf_regime in ("uptrend", "downtrend", "range", "unknown")
    # every cluster spans >=2 distinct level types (§3)
    for c in snap.clusters:
        assert c.confluence_count >= 2 and len(set(c.types)) == c.confluence_count


# ------------------------------------------------------------------ no lookahead

def test_snapshot_no_lookahead():
    df = _slice()
    base = _build(df).model_dump_json()
    # perturb every bar stamped AT/after the gate ts: 1m bars are START-labeled, so the bar
    # stamped GATE_TS is still FORMING at GATE_TS — a lookahead bug would include exactly
    # that bar, so it must be perturbed too. The snapshot must be identical.
    future = df["ts_event"] >= GATE_TS
    df2 = df.copy()
    df2.loc[future, ["open", "high", "low", "close"]] += 500.0
    df2.loc[future, "volume"] *= 7
    assert _build(df2).model_dump_json() == base


# ------------------------------------------------------------------ pre-09:30 rule

def test_cluster_premarket_uses_daily_vwap_only():
    # at 09:15 ET, NY VWAP does not exist yet -> no cluster member may be an ny vwap level
    snap = build_snapshot(_slice(), pd.Timestamp("2026-02-11 09:15", tz=NY), **_params())
    assert (snap.indicators["ny_vwap"]["mid"]) is None
    for c in snap.clusters:
        assert not any(m.startswith("nyvwap") for m in c.members)


# ------------------------------------------------------------------ §3 cluster-set rules

def test_ny_vwap_2_3_sigma_never_cluster_candidates():
    # §3: NY VWAP contributes mid/±1σ ONLY; ±2σ/±3σ are the over-extension detector
    from src.engine.snapshot import _gather_levels
    ind = {"tfs": {"1min": {"bb_basis": 100.0}},
           "daily_vwap": {"mid": 100.0, "upper_1": 101.0, "lower_1": 99.0,
                          "upper_2": 102.0, "lower_2": 98.0, "upper_3": 103.0, "lower_3": 97.0},
           "ny_vwap": {"mid": 100.5, "upper_1": 101.5, "lower_1": 99.5,
                       "upper_2": 102.5, "lower_2": 97.5, "upper_3": 103.5, "lower_3": 96.5}}
    names = {n for n, _, _ in _gather_levels(ind, {"poc": 100.2})}
    assert {"nyvwap_mid", "nyvwap_upper_1", "nyvwap_lower_1"} <= names
    assert not any(n.startswith(("nyvwap_upper_2", "nyvwap_lower_2",
                                 "nyvwap_upper_3", "nyvwap_lower_3")) for n in names)
    # daily VWAP keeps its FULL band set (§3)
    assert {"dvwap_upper_2", "dvwap_lower_3"} <= names


# ------------------------------------------------------------------ OTE / FIB levels (Angus pass 22)

def _flat_blocks(highs, lows, start="2026-02-11 07:00", block_min=15):
    """1m bars where each `block_min`-minute block is flat at (high, low) — so the resampled
    block bar equals the spec exactly and fractal swings land where the test intends."""
    rows = []
    t0 = pd.Timestamp(start, tz=NY)
    for b, (h, lo) in enumerate(zip(highs, lows)):
        for m in range(block_min):
            rows.append(dict(ts_event=t0 + pd.Timedelta(minutes=b * block_min + m),
                             open=(h + lo) / 2, high=h, low=lo, close=(h + lo) / 2,
                             volume=100))
    return pd.DataFrame(rows)


def test_ote15_fib_math_upleg():
    from src.engine.snapshot import _ote_levels
    # 12 15m blocks: fractal swing low 90 at block 5, fractal swing high 110 at block 8
    highs = [100, 101, 102, 101, 100, 99, 100, 101, 110, 105, 104, 103]
    lows = [95, 96, 97, 96, 95, 90, 95, 96, 105, 100, 99, 98]
    df = _flat_blocks(highs, lows)
    ts = df["ts_event"].iloc[-1] + pd.Timedelta(minutes=1)
    got = {n: p for n, p, typ in _ote_levels(df, ts) if n.startswith("ote15")}
    # upleg 90 -> 110: retracement measured from leg END (110) back toward origin
    assert got == {"ote15_382": 102.36, "ote15_500": 100.0, "ote15_618": 97.64,
                   "ote15_705": 95.9, "ote15_786": 94.28}
    # every candidate carries the "ote" cluster type
    assert all(typ == "ote" for _, _, typ in _ote_levels(df, ts))


def test_ote15_fib_math_downleg():
    from src.engine.snapshot import _ote_levels
    # mirror image: fractal swing HIGH first (block 5), swing LOW after (block 8)
    highs = [100, 99, 98, 99, 100, 110, 100, 99, 90, 95, 96, 97]
    lows = [95, 94, 93, 94, 95, 105, 95, 94, 85, 90, 91, 92]
    df = _flat_blocks(highs, lows)
    ts = df["ts_event"].iloc[-1] + pd.Timedelta(minutes=1)
    got = {n: p for n, p, _ in _ote_levels(df, ts) if n.startswith("ote15")}
    # downleg 110 -> 85: retracement from leg END (85) back UP toward origin
    assert got == {"ote15_382": 94.55, "ote15_500": 97.5, "ote15_618": 100.45,
                   "ote15_705": 102.625, "ote15_786": 104.65}


def test_ote_insufficient_history_returns_empty():
    from src.engine.snapshot import _ote_levels
    df = _flat_blocks([100, 101, 102], [95, 96, 97])          # 3 blocks < 7 bars minimum
    assert _ote_levels(df, df["ts_event"].iloc[-1] + pd.Timedelta(minutes=1)) == []


def test_ote_flag_off_by_default_and_golden_unaffected():
    from src.engine.snapshot import _include_ote
    assert _include_ote() is False        # config default — existing trigger caches stay valid
    snap = _build()
    assert not any("ote" in c.types for c in snap.clusters)


def test_ote_flag_on_no_lookahead(monkeypatch):
    import src.engine.snapshot as snap_mod
    monkeypatch.setattr(snap_mod, "_include_ote", lambda: True)
    df = _slice()
    base = _build(df).model_dump_json()
    future = df["ts_event"] >= GATE_TS
    df2 = df.copy()
    df2.loc[future, ["open", "high", "low", "close"]] += 500.0
    assert _build(df2).model_dump_json() == base
