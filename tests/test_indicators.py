"""Step 4 checks: BB, anchored VWAPs (+bands), volume profile — hand-computed.

The full step-4 check is the PARITY GATE (Angus vs TradingView, real data);
these tests pin the formulas so the gate is testing conventions, not bugs.
"""

from __future__ import annotations

import math
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from src.engine import indicators as ind

NY = ZoneInfo("America/New_York")


def mk_bars(start_ny: str, rows: list[tuple[float, float, float, float, int]]) -> pd.DataFrame:
    start = pd.Timestamp(start_ny, tz=NY)
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])
    df.insert(0, "ts_event", [start + pd.Timedelta(minutes=i) for i in range(len(rows))])
    df["symbol"] = "NQH6"
    return df


def test_bollinger_hand_computed() -> None:
    df = pd.DataFrame({"close": [1.0, 2.0, 3.0, 4.0, 5.0]})
    out = ind.bollinger(df, length=3, mult=2.0)
    assert pd.isna(out.loc[1, "bb_basis"])  # window not filled
    assert out.loc[2, "bb_basis"] == pytest.approx(2.0)
    sd = math.sqrt(2.0 / 3.0)  # POPULATION std of [1,2,3]
    assert out.loc[2, "bb_upper"] == pytest.approx(2.0 + 2.0 * sd)
    assert out.loc[2, "bb_lower"] == pytest.approx(2.0 - 2.0 * sd)
    assert out.loc[4, "bb_basis"] == pytest.approx(4.0)


def test_daily_vwap_hand_computed() -> None:
    # tp1 = (102+98+100)/3 = 100 @ v=10 ; tp2 = (112+104+108)/3 = 108 @ v=30
    df = mk_bars("2026-02-10 09:30", [(99, 102, 98, 100, 10), (101, 112, 104, 108, 30)])
    out = ind.daily_vwap(df, sigmas=[1])
    assert out.loc[0, "daily_vwap"] == pytest.approx(100.0)
    assert out.loc[1, "daily_vwap"] == pytest.approx(106.0)  # (100·10+108·30)/40
    # var = (100²·10 + 108²·30)/40 − 106² = 12
    assert out.loc[1, "daily_vwap_up_1"] == pytest.approx(106.0 + math.sqrt(12.0))
    assert out.loc[1, "daily_vwap_dn_1"] == pytest.approx(106.0 - math.sqrt(12.0))


def test_daily_vwap_resets_at_1800_anchor() -> None:
    late = mk_bars("2026-02-10 17:59", [(99, 102, 98, 100, 10)])   # Feb 10 session
    even = mk_bars("2026-02-10 18:00", [(200, 212, 204, 208, 30)])  # Feb 11 session
    out = ind.daily_vwap(pd.concat([late, even], ignore_index=True), sigmas=[1])
    assert out.loc[0, "daily_vwap"] == pytest.approx(100.0)
    assert out.loc[1, "daily_vwap"] == pytest.approx(208.0)  # fresh anchor, own tp only


def test_ny_vwap_absent_premarket() -> None:
    """Mandatory (code-standards): NY VWAP returns NO values before 09:30 ET."""
    df = pd.concat(
        [
            mk_bars("2026-02-10 09:28", [(99, 102, 98, 100, 10)] * 2),  # 09:28, 09:29
            mk_bars("2026-02-10 09:30", [(101, 112, 104, 108, 30)]),
            mk_bars("2026-02-10 18:05", [(1, 2, 0.5, 1.5, 5)]),  # evening: also NaN
        ],
        ignore_index=True,
    )
    out = ind.ny_vwap(df, sigmas=[1, 2, 3])
    assert pd.isna(out.loc[0, "ny_vwap"]) and pd.isna(out.loc[1, "ny_vwap"])
    assert pd.isna(out.loc[3, "ny_vwap"])
    assert pd.isna(out.loc[0, "ny_vwap_up_2"])
    assert out.loc[2, "ny_vwap"] == pytest.approx(108.0)  # anchor bar = its own tp


def test_ny_vwap_cumulative_after_anchor() -> None:
    df = mk_bars("2026-02-10 09:30", [(99, 102, 98, 100, 10), (101, 112, 104, 108, 30)])
    out = ind.ny_vwap(df, sigmas=[1])
    assert out.loc[1, "ny_vwap"] == pytest.approx(106.0)


def test_volume_profile_poc_value_area_hand_computed() -> None:
    # three bars, each inside one 1.0-wide bin: hist = {100: 50, 101: 30, 102: 20}
    df = mk_bars(
        "2026-02-10 09:30",
        [(100.1, 100.5, 100.0, 100.3, 50), (101.3, 101.8, 101.2, 101.5, 30), (102.2, 102.9, 102.1, 102.5, 20)],
    )
    p = ind.volume_profile(df, bin_size=1.0, va_pct=0.70)
    assert p.poc == pytest.approx(100.5)  # center of bin 100
    # VA: 50 (POC) then neighbor above (30) -> 80/100 >= 70%
    assert p.val == pytest.approx(100.5)
    assert p.vah == pytest.approx(101.5)
    assert p.total_volume == pytest.approx(100.0)
    assert p.hvn == [] and p.lvn == []  # middle bin is neither peak nor trough


def test_volume_profile_splits_bar_across_bins() -> None:
    # one bar spanning bins 100-102 -> 30 volume split 10/10/10
    df = mk_bars("2026-02-10 09:30", [(100.5, 102.9, 100.0, 102.0, 30)])
    p = ind.volume_profile(df, bin_size=1.0, va_pct=0.70)
    assert p.total_volume == pytest.approx(30.0)
    # flat histogram: argmax -> first bin
    assert p.poc == pytest.approx(100.5)


def test_volume_profile_hvn_lvn() -> None:
    # hist = {100:50, 101:10, 102:40}: bin 101 is an LVN valley
    df = mk_bars(
        "2026-02-10 09:30",
        [(100.1, 100.5, 100.0, 100.3, 50), (101.3, 101.8, 101.2, 101.5, 10), (102.2, 102.9, 102.1, 102.5, 40)],
    )
    p = ind.volume_profile(df, bin_size=1.0, va_pct=0.70)
    assert p.lvn == [pytest.approx(101.5)]


def test_running_daily_profile_is_causal() -> None:
    df = mk_bars(
        "2026-02-10 09:30",
        [(100.1, 100.5, 100.0, 100.3, 100), (105.2, 105.4, 105.1, 105.3, 300), (100.2, 100.4, 100.1, 100.3, 10)],
    )
    out = ind.running_daily_profile(df, bin_size=1.0, va_pct=0.70)
    assert out.loc[0, "daily_poc"] == pytest.approx(100.5)  # only bar 0 known
    assert out.loc[1, "daily_poc"] == pytest.approx(105.5)  # volume shifted up
    assert out.loc[2, "daily_poc"] == pytest.approx(105.5)  # 110 < 300, POC stays


def test_empty_profile_slice_raises() -> None:
    df = mk_bars("2026-02-10 09:30", [(1, 2, 0.5, 1.5, 5)])
    with pytest.raises(ValueError, match="empty"):
        ind.volume_profile(df.iloc[0:0], bin_size=1.0, va_pct=0.70)


def test_load_indicator_config() -> None:
    cfg = ind.load_indicator_config(Path(__file__).parents[1] / "config" / "strategy.yaml")
    assert cfg["bb_length"] == 20 and cfg["bb_mult"] == 2.0
    assert cfg["band_sigmas"] == [1, 2, 3]
    assert cfg["value_area_pct"] == 0.70
    assert cfg["weekly_enabled"] is False  # §2 weekly profile stays behind its flag


def test_parity_report_smoke(tmp_path: Path) -> None:
    """Report generates from a parquet, fills computed values, flags missing bars."""
    bars = mk_bars(
        "2026-02-11 09:20",  # 31 bars: BB(20) on 1m fills by 09:40, before 09:48
        [(21850 + i, 21856 + i, 21845 + i, 21852 + i, 100 + i) for i in range(31)],
    )
    pq = tmp_path / "nq.parquet"
    bars.to_parquet(pq, index=False)
    out = tmp_path / "parity_report.md"
    ind.parity_report(pq, out, Path(__file__).parents[1] / "config" / "strategy.yaml")
    text = out.read_text()
    assert "2026-02-11 09:48 ET" in text and "BB basis (1m)" in text
    assert "daily POC" in text
    assert "NO DATA BAR" in text  # 2026-02-17 not in the fixture
    assert "Angus sign-off" in text
    # a computed number is present for the 1m BB basis (window filled by 09:48)
    assert not np.isnan(float(text.split("| BB basis (1m) | ")[1].split(" |")[0]))
