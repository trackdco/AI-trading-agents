"""Databento ohlcv-1m ingest for the tomtrades research track (GC / 6J / DX).

Separate from ``src/engine/data.py`` on purpose. That module is the NQ engine's
validated ingest and is load-bearing for the live path; this one serves a research
question about a different instrument on a different venue, and must not be able to
disturb it. The two share conventions (tz-aware NY, volume-based front-month roll,
raising on out-of-order timestamps) but no code.

What it does, in order:
  * drops calendar spreads and FX-Link legs — symbols containing ``-`` or ``:``. On the
    gold export that is 1.79M of 4.39M rows (41%), and their prices are basis values
    (negative), not prices. Treating them as a price series would be silently wrong.
  * selects one front-month contract per NY session day: the highest-volume outright.
    This reproduces a volume roll rather than a calendar rule, matching the NQ engine's
    choice for the same reason (spec-1 §3).
  * tags the first bar after the contract changes in a ``roll`` column.
  * validates: strictly increasing timestamps, no duplicates, no non-positive prices.
    Violations RAISE (code-standards: validation errors raise, never warn). DX in
    particular ships negative closes, which is why the check is not optional.

Prices are already decimal in these exports (Databento ``pretty_px``), unlike the
fixed-precision integers the NQ CSV path auto-detects.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

CANONICAL_COLUMNS = ["ts_event", "open", "high", "low", "close", "volume", "symbol", "roll"]
_PRICE_COLS = ["open", "high", "low", "close"]
_SPREAD_MARKERS = r"[-:]"
_NY = "America/New_York"


@dataclass(frozen=True)
class IngestConfig:
    """One ingest run. ``allow_nonpositive`` exists only for diagnostics on DX."""

    input_path: Path
    output_parquet: Path
    timezone: str = _NY
    front_month_only: bool = True
    allow_nonpositive: bool = False


def read_databento_csv(path: Path, timezone: str = _NY) -> pd.DataFrame:
    """Read a Databento ohlcv-1m CSV into a tz-aware outright-only frame.

    Returns every outright contract (not yet collapsed to front month) so callers can
    inspect the contract set before the roll decision is applied.
    """
    raw = pd.read_csv(path)
    required = {"ts_event", "open", "high", "low", "close", "volume", "symbol"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"{path}: missing required Databento columns {sorted(missing)}")

    sym = raw["symbol"].astype(str)
    outright = raw.loc[~sym.str.contains(_SPREAD_MARKERS, regex=True, na=False)].copy()
    if outright.empty:
        raise ValueError(f"{path}: no outright rows after dropping spreads")

    out = pd.DataFrame(
        {
            "ts_event": pd.to_datetime(outright["ts_event"], format="ISO8601", utc=True)
            .dt.tz_convert(timezone),
            "symbol": outright["symbol"].astype(str),
            "volume": outright["volume"].astype("int64"),
        }
    )
    for col in _PRICE_COLS:
        out[col] = outright[col].astype("float64")
    if "instrument_id" in outright.columns:
        out["instrument_id"] = outright["instrument_id"].astype("int64")
    return out.sort_values(["ts_event", "symbol"], kind="mergesort").reset_index(drop=True)


def to_continuous_front_month(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse every outright to one series: the highest-volume contract per session day.

    A volume roll, unspliced — the price gap at the roll is left in and tagged rather
    than back-adjusted, so no synthetic prices enter the series. ``roll`` marks the first
    bar of each new contract.
    """
    if df.empty:
        raise ValueError("cannot build a continuous series from an empty frame")
    day = df["ts_event"].dt.tz_convert(_NY).dt.date
    totals = df.assign(_day=day).groupby(["_day", "symbol"], sort=False)["volume"].sum()
    front = totals.reset_index().sort_values("volume").groupby("_day").tail(1)
    front = front[["_day", "symbol"]]

    keep = df.assign(_day=day).merge(front, on=["_day", "symbol"], how="inner")
    keep = keep.drop(columns="_day").sort_values("ts_event", kind="mergesort")
    keep = keep.reset_index(drop=True)
    keep["roll"] = keep["symbol"].ne(keep["symbol"].shift()).fillna(False)
    keep.loc[keep.index[0], "roll"] = False
    return keep


def validate(df: pd.DataFrame, allow_nonpositive: bool = False) -> None:
    """Raise on anything that would silently corrupt downstream maths."""
    ts = df["ts_event"]
    if ts.dt.tz is None:
        raise ValueError("ts_event must be tz-aware (naive datetimes are a bug by definition)")
    if ts.duplicated().any():
        n = int(ts.duplicated().sum())
        raise ValueError(f"{n} duplicate timestamps in the continuous series")
    if not ts.is_monotonic_increasing:
        raise ValueError("ts_event is not strictly increasing after the front-month collapse")
    if not allow_nonpositive:
        bad = (df[_PRICE_COLS] <= 0).any(axis=1)
        if bad.any():
            raise ValueError(
                f"{int(bad.sum())} bars have a non-positive price — DX ships these; "
                "filter them or pass allow_nonpositive for a diagnostics-only read"
            )
    inverted = (df["high"] < df["low"]).sum()
    if inverted:
        raise ValueError(f"{int(inverted)} bars have high < low")


def ingest(cfg: IngestConfig) -> pd.DataFrame:
    """CSV -> validated, tz-aware, front-month parquet. Returns the frame it wrote."""
    df = read_databento_csv(cfg.input_path, cfg.timezone)
    if not cfg.allow_nonpositive:
        keep = (df[_PRICE_COLS] > 0).all(axis=1)
        df = df.loc[keep].reset_index(drop=True)
    df = to_continuous_front_month(df) if cfg.front_month_only else df.assign(roll=False)
    validate(df, cfg.allow_nonpositive)
    out = df[[c for c in CANONICAL_COLUMNS if c in df.columns]]
    cfg.output_parquet.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(cfg.output_parquet, index=False)
    return out


def load(path: Path) -> pd.DataFrame:
    """Read a parquet written by :func:`ingest`, restoring the NY timezone."""
    df = pd.read_parquet(path)
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(_NY)
    return df


if __name__ == "__main__":  # pragma: no cover - operator entry point
    import sys

    if len(sys.argv) < 3:
        sys.exit("usage: python -m src.research.tomtrades.data <csv> <out.parquet>")
    frame = ingest(IngestConfig(input_path=Path(sys.argv[1]), output_parquet=Path(sys.argv[2])))
    span = f"{frame['ts_event'].min()} -> {frame['ts_event'].max()}"
    print(f"wrote {len(frame):,} bars  {span}  rolls={int(frame['roll'].sum())}")
