"""Tests for src/engine/data.py — Databento ingest + validation (Spec 1, Step 2).

Fixture: tests/fixtures/nq_1m_2day.csv — a Databento ohlcv-1m export in native encoding
(nanosecond UTC timestamps, 1e-9 fixed-precision prices) covering two RTH days with a
deliberate missing minute (09:35 ET on 2026-02-02) and a contract roll (instrument_id
101 -> 102 on 2026-02-03).
"""
from datetime import time
from pathlib import Path

import pandas as pd
import pytest

from src.engine.data import (
    CANONICAL_COLUMNS,
    IngestConfig,
    build_gap_report,
    check_monotonic_unique,
    ingest,
    read_databento_csv,
    tag_rolls,
)

FIXTURE = Path(__file__).parent / "fixtures" / "nq_1m_2day.csv"
NY = "America/New_York"


# ----------------------------------------------------------------- fixture load

def test_read_columns_and_tz():
    df = read_databento_csv(FIXTURE, NY, price_scale=None)
    assert {"ts_event", "open", "high", "low", "close", "volume"} <= set(df.columns)
    assert str(df["ts_event"].dt.tz) == NY                    # tz-aware America/New_York
    # first fixture bar is 2026-02-02 09:30 ET
    assert df["ts_event"].iloc[0] == pd.Timestamp("2026-02-02 09:30", tz=NY)


def test_prices_scaled_to_nq_range():
    df = read_databento_csv(FIXTURE, NY, price_scale=None)
    # 1e-9 fixed precision must be decoded back to ~20000, not left at ~2e13
    assert 15_000 < df["close"].median() < 25_000
    assert df["open"].iloc[0] == pytest.approx(20000.0)


def test_price_scale_not_applied_to_decimal_input(tmp_path):
    csv = tmp_path / "dec.csv"
    csv.write_text(
        "ts_event,instrument_id,open,high,low,close,volume\n"
        "2026-02-02T14:30:00Z,101,20000.0,20002.0,19998.0,20001.0,100\n"
        "2026-02-02T14:31:00Z,101,20001.0,20003.0,19999.0,20002.0,101\n"
    )
    df = read_databento_csv(csv, NY, price_scale=None)
    assert df["open"].iloc[0] == pytest.approx(20000.0)       # decimal left untouched
    assert str(df["ts_event"].dt.tz) == NY


# ----------------------------------------------------------------- validation

def test_monotonic_unique_passes_on_fixture():
    df = read_databento_csv(FIXTURE, NY, price_scale=None).sort_values("ts_event").reset_index(drop=True)
    check_monotonic_unique(df)  # must not raise


def test_duplicate_timestamps_raise():
    df = read_databento_csv(FIXTURE, NY, price_scale=None)
    dup = pd.concat([df, df.iloc[[0]]], ignore_index=True).sort_values("ts_event").reset_index(drop=True)
    with pytest.raises(ValueError, match="duplicate"):
        check_monotonic_unique(dup)


def test_non_monotonic_raises():
    df = read_databento_csv(FIXTURE, NY, price_scale=None).reset_index(drop=True)
    swapped = df.iloc[[1, 0] + list(range(2, len(df)))].reset_index(drop=True)
    with pytest.raises(ValueError, match="not strictly increasing"):
        check_monotonic_unique(swapped)


# ----------------------------------------------------------------- roll tags

def test_roll_tagged_once_on_day2():
    df = read_databento_csv(FIXTURE, NY, price_scale=None).sort_values("ts_event").reset_index(drop=True)
    roll = tag_rolls(df)
    assert roll.sum() == 1
    assert not roll.iloc[0]                                    # first bar never a roll
    assert df.loc[roll, "ts_event"].iloc[0].date().isoformat() == "2026-02-03"


def test_no_instrument_id_means_no_rolls(tmp_path):
    csv = tmp_path / "noid.csv"
    csv.write_text(
        "ts_event,open,high,low,close,volume\n"
        "2026-02-02T14:30:00Z,20000,20002,19998,20001,100\n"
        "2026-02-02T14:31:00Z,20001,20003,19999,20002,101\n"
    )
    df = read_databento_csv(csv, NY, price_scale=1.0)
    assert tag_rolls(df).sum() == 0


# ----------------------------------------------------------------- gap report

def _minute_frame(start_ny: str, n: int, drop: list[int] | None = None) -> pd.DataFrame:
    """Continuous 1-minute NY frame of n bars starting at start_ny, optionally dropping indices."""
    idx = pd.date_range(pd.Timestamp(start_ny, tz=NY), periods=n, freq="1min")
    if drop:
        idx = idx.delete(drop)
    return pd.DataFrame({"ts_event": idx})


def test_gap_report_counts_rth_hole():
    # 09:30..09:39 ET with 09:35 removed -> exactly one unexpected missing minute
    df = _minute_frame("2026-02-02 09:30", 10, drop=[5])
    rep = build_gap_report(df, session_open=time(18, 0))
    assert int(rep["missing_minutes"].sum()) == 1
    assert str(rep["session_date"].iloc[0]) == "2026-02-02"


def test_gap_report_excludes_maintenance_break():
    # last bar 16:59 ET, next bar 18:00 ET -> the 17:00-17:59 break must NOT count
    df = pd.DataFrame({"ts_event": [pd.Timestamp("2026-02-02 16:59", tz=NY),
                                    pd.Timestamp("2026-02-02 18:00", tz=NY)]})
    rep = build_gap_report(df, session_open=time(18, 0))
    assert rep.empty or int(rep["missing_minutes"].sum()) == 0


def test_gap_report_excludes_weekend():
    # Fri 16:59 ET -> Sun 18:00 ET (2026-02-06 is a Friday) must count zero unexpected minutes
    df = pd.DataFrame({"ts_event": [pd.Timestamp("2026-02-06 16:59", tz=NY),
                                    pd.Timestamp("2026-02-08 18:00", tz=NY)]})
    rep = build_gap_report(df, session_open=time(18, 0))
    assert rep.empty or int(rep["missing_minutes"].sum()) == 0


# ----------------------------------------------------------------- end to end

def test_ingest_writes_canonical_parquet(tmp_path):
    cfg = IngestConfig(input_path=FIXTURE, timezone=NY,
                       output_parquet=tmp_path / "nq_1m.parquet",
                       gap_report_path=tmp_path / "gap_report.csv")
    res = ingest(cfg)

    assert res.n_bars == 17
    assert res.n_rolls == 1 and res.roll_dates == ["2026-02-03"]
    assert cfg.output_parquet.exists() and cfg.gap_report_path.exists()

    back = pd.read_parquet(cfg.output_parquet)
    assert list(back.columns) == CANONICAL_COLUMNS
    assert str(back["ts_event"].dt.tz) == NY                  # tz survives the parquet round-trip
    assert back["ts_event"].is_monotonic_increasing
    assert back["roll"].sum() == 1
