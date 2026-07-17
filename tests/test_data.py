"""Step 2 checks: ingest, validation, session tagging, rolls, gap report.

Fixture: tests/fixtures/nq_1m_2day_sample.csv — two sessions (2026-02-10,
2026-02-11), NY-morning bars plus three 18:00-ET bars that must land in the
NEXT session.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.engine import data as d

FIXTURE = Path(__file__).parent / "fixtures" / "nq_1m_2day_sample.csv"


@pytest.fixture()
def fixture_df() -> pd.DataFrame:
    return d.normalize(d.load_raw([FIXTURE]))


def test_fixture_loads_normalized(fixture_df: pd.DataFrame) -> None:
    assert list(fixture_df.columns) == ["ts_event", "open", "high", "low", "close", "volume", "symbol"]
    assert str(fixture_df["ts_event"].dt.tz) == "America/New_York"
    assert fixture_df["ts_event"].is_monotonic_increasing
    assert fixture_df["open"].dtype == "float64"
    # 14:30 UTC on a February (EST, UTC-5) date is 09:30 ET
    assert fixture_df["ts_event"].iloc[0].strftime("%H:%M") == "09:30"


def test_bars_at_1800_et_belong_to_next_session(fixture_df: pd.DataFrame) -> None:
    tagged = d.tag_sessions_and_rolls(fixture_df)
    evening = tagged[tagged["ts_event"].dt.hour == 18]
    assert len(evening) == 3
    assert (evening["ts_event"].dt.date == pd.Timestamp("2026-02-10").date()).all()
    assert (evening["session_date"] == pd.Timestamp("2026-02-11").date()).all()


def test_duplicate_timestamps_raise(fixture_df: pd.DataFrame) -> None:
    dup = pd.concat([fixture_df, fixture_df.iloc[[3]]], ignore_index=True)
    with pytest.raises(d.DataValidationError, match="duplicate"):
        d._validate(dup.sort_values(["ts_event", "symbol"]).reset_index(drop=True))


def test_ohlc_bounds_violation_raises(fixture_df: pd.DataFrame) -> None:
    bad = fixture_df.copy()
    bad.loc[5, "high"] = bad.loc[5, "low"] - 1.0
    with pytest.raises(d.DataValidationError, match="OHLC"):
        d._validate(bad)


def test_scaled_int_prices_normalized() -> None:
    raw = pd.read_csv(FIXTURE)
    for col in ("open", "high", "low", "close"):
        raw[col] = (raw[col] * 1e9).round().astype("int64")
    df = d.normalize(raw)
    assert 15000 < df["close"].median() < 30000
    assert df["close"].iloc[0] == pytest.approx(21852.50)


def test_gap_report_counts_missing_minute(fixture_df: pd.DataFrame) -> None:
    tagged = d.tag_sessions_and_rolls(fixture_df)
    full = d.gap_report(tagged).set_index("session_date")
    # Feb 10 session has exactly the 10 morning bars
    assert full.loc[pd.Timestamp("2026-02-10").date(), "present_minutes"] == 10
    assert (
        full.loc[pd.Timestamp("2026-02-10").date(), "missing_minutes"]
        == d.EXPECTED_SESSION_MINUTES - 10
    )
    # dropping 09:33 shows up as exactly one more missing minute
    dropped = tagged[tagged["ts_event"].dt.strftime("%Y-%m-%d %H:%M") != "2026-02-10 09:33"]
    rerun = d.gap_report(dropped).set_index("session_date")
    assert rerun.loc[pd.Timestamp("2026-02-10").date(), "present_minutes"] == 9


def test_roll_session_tagged_on_lead_change(fixture_df: pd.DataFrame) -> None:
    df = fixture_df.copy()
    # second session trades the June contract at 10x volume -> lead flips
    june = df[df["ts_event"].dt.date >= pd.Timestamp("2026-02-10").date()].copy()
    june = june[june["ts_event"].dt.hour != 9]  # evening + Feb 11 bars only
    june["symbol"] = "NQM6"
    june["volume"] = june["volume"] * 10
    tagged = d.tag_sessions_and_rolls(
        pd.concat([df, june], ignore_index=True)
        .sort_values(["ts_event", "symbol"], kind="stable")
        .reset_index(drop=True)
    )
    by_session = tagged.groupby("session_date").agg(
        lead=("symbol", "first"), roll=("is_roll_session", "first")
    )
    feb10 = pd.Timestamp("2026-02-10").date()
    feb11 = pd.Timestamp("2026-02-11").date()
    assert by_session.loc[feb10, "lead"] == "NQH6" and not by_session.loc[feb10, "roll"]
    assert by_session.loc[feb11, "lead"] == "NQM6" and by_session.loc[feb11, "roll"]
    # non-lead rows are dropped: every Feb 11 row is the lead contract
    assert (tagged[tagged["session_date"] == feb11]["symbol"] == "NQM6").all()


def test_ingest_writes_parquet_and_report(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "sample.csv").write_bytes(FIXTURE.read_bytes())
    out = tmp_path / "nq_1m.parquet"
    report = tmp_path / "gap_report.csv"
    df = d.ingest(raw_dir, out, report)
    assert out.exists() and report.exists()
    roundtrip = pd.read_parquet(out)
    assert len(roundtrip) == len(df) == 23
    assert str(roundtrip["ts_event"].dt.tz) == "America/New_York"
    assert pd.read_csv(report).shape[0] == 2  # two sessions
