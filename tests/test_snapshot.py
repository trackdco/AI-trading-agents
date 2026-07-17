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
        cluster_tol=10.0, data_window_min=15)


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
    # perturb every bar strictly AFTER the gate ts; the snapshot must be identical
    future = df["ts_event"] > GATE_TS
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
