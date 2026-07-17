"""Data ingest: Databento 1-minute NQ -> validated parquet + gap report.

Spec: spec-1-market-engine-backtester.md, Step 2.

Reads Databento OHLCV-1m files (CSV natively; DBN via the optional `databento`
package), normalizes to a single tz-aware table, validates it, tags roll
sessions, and writes:
  - data/nq_1m.parquet  (columns: ts_event [America/New_York], open, high,
    low, close, volume, symbol, session_date, is_roll_session)
  - output/gap_report.csv  (missing minutes per session)

Run: python -m src.engine.data --raw data/raw --out data/nq_1m.parquet \
        --report output/gap_report.csv
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

logger = logging.getLogger(__name__)

NY_TZ = ZoneInfo("America/New_York")
REQUIRED_COLUMNS = ("ts_event", "open", "high", "low", "close", "volume")
PRICE_COLUMNS = ("open", "high", "low", "close")
# Databento stores prices as fixed-precision ints (price * 1e9). NQ trades in
# the 1e4 range, so anything above this threshold must be a scaled int.
PRICE_SCALE_THRESHOLD = 1e7
PRICE_SCALE = 1e9
# CME Globex equity-index session: 18:00 ET -> 17:00 ET next day (strategy §2:
# daily anchor 18:00 ET / Asia open). 23h = 1380 expected minutes per session.
SESSION_OPEN_HOUR_ET = 18
EXPECTED_SESSION_MINUTES = 23 * 60


class DataValidationError(ValueError):
    """Raised when ingested data violates a hard invariant."""


def _read_one(path: Path) -> pd.DataFrame:
    """Read a single Databento OHLCV-1m file (CSV, or DBN if `databento` is installed)."""
    suffixes = "".join(path.suffixes)
    if ".dbn" in suffixes:
        try:
            from databento import DBNStore
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise DataValidationError(
                f"{path} is a DBN file but the optional `databento` package is not "
                "installed; install it or export CSV from Databento instead"
            ) from exc
        df = DBNStore.from_file(path).to_df().reset_index()
        if "ts_event" not in df.columns and "ts_recv" in df.columns:
            df = df.rename(columns={"ts_recv": "ts_event"})
        return df
    return pd.read_csv(path)


def load_raw(paths: list[Path]) -> pd.DataFrame:
    """Load and concatenate raw Databento files."""
    if not paths:
        raise DataValidationError("no raw data files found")
    frames = [_read_one(p) for p in sorted(paths)]
    df = pd.concat(frames, ignore_index=True)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(f"raw data missing required columns: {missing}")
    return df


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Parse timestamps to tz-aware America/New_York, unscale prices, sort, validate.

    Databento ts_event is UTC (ISO string or integer nanoseconds); naive
    datetimes are a bug by definition (code-standards), so everything is parsed
    as UTC then converted.
    """
    df = df.copy()
    ts = df["ts_event"]
    if pd.api.types.is_integer_dtype(ts):
        parsed = pd.to_datetime(ts, unit="ns", utc=True)
    else:
        parsed = pd.to_datetime(ts, utc=True, format="ISO8601")
    df["ts_event"] = parsed.dt.tz_convert(NY_TZ)

    for col in PRICE_COLUMNS:
        series = pd.to_numeric(df[col])
        if series.abs().median() > PRICE_SCALE_THRESHOLD:
            series = series / PRICE_SCALE
        df[col] = series.astype("float64")
    df["volume"] = pd.to_numeric(df["volume"]).astype("int64")

    if "symbol" not in df.columns:
        df["symbol"] = "NQ"

    keep = [*REQUIRED_COLUMNS, "symbol"]
    df = df[keep].sort_values(["ts_event", "symbol"], kind="stable").reset_index(drop=True)
    _validate(df)
    return df


def _validate(df: pd.DataFrame) -> None:
    if df.empty:
        raise DataValidationError("no rows after normalization")
    dupes = df.duplicated(subset=["ts_event", "symbol"])
    if dupes.any():
        first = df.loc[dupes.idxmax(), "ts_event"]
        raise DataValidationError(
            f"{int(dupes.sum())} duplicate (ts_event, symbol) rows; first at {first}"
        )
    if not df["ts_event"].is_monotonic_increasing:
        raise DataValidationError("timestamps not monotonic after sort (mixed tz parse?)")
    bad_ohlc = (df["high"] < df[["open", "close", "low"]].max(axis=1)) | (
        df["low"] > df[["open", "close", "high"]].min(axis=1)
    )
    if bad_ohlc.any():
        raise DataValidationError(f"{int(bad_ohlc.sum())} rows violate OHLC bounds")


def session_date(ts: pd.Series) -> pd.Series:
    """Trading-session date for each NY timestamp.

    Bars at/after 18:00 ET belong to the NEXT calendar day's session
    (strategy §2: CME daily session opens 18:00 ET). Sunday 18:00 -> Monday.
    """
    dates = ts.dt.normalize()
    after_open = ts.dt.hour >= SESSION_OPEN_HOUR_ET
    return (dates + pd.to_timedelta(after_open.astype(int), unit="D")).dt.date


def tag_sessions_and_rolls(df: pd.DataFrame) -> pd.DataFrame:
    """Add session_date; reduce to per-session lead contract; tag roll sessions.

    Lead contract per session = symbol with the highest session volume. A
    session whose lead differs from the previous session's lead is a roll
    session (spec step 2: roll-date tags).
    """
    df = df.copy()
    df["session_date"] = session_date(df["ts_event"])

    lead = (
        df.groupby(["session_date", "symbol"], sort=True)["volume"]
        .sum()
        .reset_index()
        .sort_values(["session_date", "volume"], ascending=[True, False], kind="stable")
        .drop_duplicates("session_date")
        .set_index("session_date")["symbol"]
    )
    df = df[df["symbol"] == df["session_date"].map(lead)].reset_index(drop=True)

    prev_lead = lead.shift(1)
    roll_sessions = lead[(prev_lead.notna()) & (lead != prev_lead)].index
    df["is_roll_session"] = df["session_date"].isin(set(roll_sessions))
    if len(roll_sessions):
        logger.info("roll sessions detected: %s", list(roll_sessions))
    return df


def gap_report(df: pd.DataFrame) -> pd.DataFrame:
    """Missing minutes per session vs the full 1380-minute Globex session.

    Holidays and early closes surface as large missing counts on purpose —
    this is a report for human review, not a gate.
    """
    rows = []
    for sess, grp in df.groupby("session_date", sort=True):
        present = grp["ts_event"].dt.floor("min").nunique()
        rows.append(
            {
                "session_date": sess,
                "expected_minutes": EXPECTED_SESSION_MINUTES,
                "present_minutes": int(present),
                "missing_minutes": int(EXPECTED_SESSION_MINUTES - present),
                "coverage_pct": round(100.0 * present / EXPECTED_SESSION_MINUTES, 2),
                "is_roll_session": bool(grp["is_roll_session"].iloc[0]),
            }
        )
    return pd.DataFrame(rows)


def ingest(raw_dir: Path, out_path: Path, report_path: Path) -> pd.DataFrame:
    """Full pipeline: raw files -> validated parquet + gap report. Returns the table."""
    paths = [
        p
        for p in raw_dir.iterdir()
        if p.is_file() and (p.suffix == ".csv" or ".dbn" in "".join(p.suffixes))
    ]
    df = tag_sessions_and_rolls(normalize(load_raw(paths)))
    report = gap_report(df)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    report.to_csv(report_path, index=False)
    logger.info(
        "wrote %s (%d rows, %d sessions) and %s",
        out_path,
        len(df),
        report.shape[0],
        report_path,
    )
    return df


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data/nq_1m.parquet"))
    parser.add_argument("--report", type=Path, default=Path("output/gap_report.csv"))
    args = parser.parse_args(argv)
    ingest(args.raw, args.out, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
