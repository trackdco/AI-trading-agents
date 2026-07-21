"""Data ingest → tz-aware 1-minute OHLCV frame.

Historical source: Databento glbx-mdp3 *.ohlcv-1m.csv.zst (the files in repo root).
Columns in raw: ts_event(UTC), rtype, publisher_id, instrument_id, open, high,
low, close, volume, symbol. We keep the front NQ contract per timestamp
(highest-volume symbol) and return OHLCV indexed by ET-localized timestamps.
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import zstandard


def _read_zst_csv(path: Path) -> pd.DataFrame:
    with open(path, "rb") as f:
        dctx = zstandard.ZstdDecompressor()
        with dctx.stream_reader(f) as r:
            text = io.TextIOWrapper(r, encoding="utf-8")
            return pd.read_csv(text)


def load_historical(paths: list[str | Path], tz: str) -> pd.DataFrame:
    """Load one or more zst OHLCV files → single OHLCV frame indexed by ET ts.

    Front-month selection: for each minute keep the symbol with the max volume
    (volume-based roll, unspliced per spec-1 §3). Returns columns
    [open, high, low, close, volume] with a tz-aware DatetimeIndex in ``tz``.
    """
    frames = [_read_zst_csv(Path(p)) for p in paths]
    df = pd.concat(frames, ignore_index=True)

    df = df[df["symbol"].str.startswith("NQ")].copy()          # drop spreads etc.
    df = df[~df["symbol"].str.contains("-")]                   # drop calendar spreads
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)

    # front month = highest-volume symbol per minute
    df.sort_values(["ts_event", "volume"], inplace=True)
    df = df.groupby("ts_event", as_index=False).last()

    df.set_index("ts_event", inplace=True)
    df.index = df.index.tz_convert(tz)
    df.index.name = "ts"

    out = df[["open", "high", "low", "close", "volume"]].astype(
        {"open": float, "high": float, "low": float, "close": float, "volume": float}
    )
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out


def validate(df: pd.DataFrame) -> dict:
    """Basic integrity report (monotonic, dup-free, gap count)."""
    idx = df.index
    return {
        "rows": int(len(df)),
        "monotonic": bool(idx.is_monotonic_increasing),
        "duplicates": int(idx.duplicated().sum()),
        "start": str(idx.min()),
        "end": str(idx.max()),
    }
