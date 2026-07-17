"""Databento 1-minute NQ ingest + validation (Spec 1, Step 2).

Loads a Databento ``ohlcv-1m`` export (CSV; DBN support is a documented TODO) into a
validated, timezone-aware parquet at ``data/nq_1m.parquet`` with the canonical columns

    ts_event (America/New_York, tz-aware) | open | high | low | close | volume | roll

Validation performed (per strategy-definition-v1.1.md §12 and spec-1 Step 2):
  * timestamps strictly monotonic increasing with NO duplicates — a violation RAISES
    (code-standards: validation errors raise, never warn);
  * gap report — unexpected missing 1-minute bars per CME daily session, written to
    ``output/gap_report.csv`` (expected closures — the 17:00–18:00 ET daily maintenance
    break and the weekend close — are excluded, so only real holes are reported);
  * roll tags — the ``roll`` column marks the first bar after the continuous contract's
    underlying ``instrument_id`` changes (Databento volume-based roll, unspliced; spec-1 §3).

All timestamps are tz-aware ``America/New_York`` via zoneinfo; DST is handled by the tz
library, never by offset arithmetic (architecture invariant 2).

Run on the real dataset once Databento data lands in ``data/raw/``:

    python -m src.engine.data data/raw/nq_ohlcv_1m.csv
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path

import pandas as pd
import yaml
from pydantic import BaseModel

CANONICAL_COLUMNS = ["ts_event", "open", "high", "low", "close", "volume", "roll"]
_PRICE_COLS = ["open", "high", "low", "close"]
# CME Globex daily maintenance break (no bars expected). §1 / Design decisions.
_MAINT_START = time(17, 0)
_MAINT_END = time(18, 0)


class IngestConfig(BaseModel):
    """Configuration for one ingest run (cross-boundary object -> pydantic, per code-standards)."""

    input_path: Path
    output_parquet: Path = Path("data/nq_1m.parquet")
    gap_report_path: Path = Path("output/gap_report.csv")
    timezone: str = "America/New_York"          # from config/strategy.yaml session.timezone
    session_open: time = time(18, 0)            # CME daily session open; daily VWAP anchor (§2)
    price_scale: float | None = None            # None = auto-detect Databento 1e-9 fixed precision
    tick_size: float = 0.25                     # spec-1 §3

    model_config = {"arbitrary_types_allowed": True}


@dataclass
class IngestResult:
    n_bars: int
    start: pd.Timestamp
    end: pd.Timestamp
    n_rolls: int
    roll_dates: list[str]
    unexpected_missing_minutes: int
    n_gap_sessions: int
    output_parquet: Path
    gap_report_path: Path
    frame: pd.DataFrame = field(repr=False, default=None)


def load_strategy_timezone(config_path: Path = Path("config/strategy.yaml")) -> str:
    """Read the project timezone from config so it is never a magic string here."""
    cfg = yaml.safe_load(open(config_path))
    return cfg["session"]["timezone"]


# ---------------------------------------------------------------- read / normalize

def read_databento_csv(path: Path, timezone: str, price_scale: float | None,
                       session_open: time = time(18, 0)) -> pd.DataFrame:
    """Read a Databento ohlcv-1m CSV into a normalized, tz-aware single-series frame.

    Handles Databento's native encoding: ``ts_event`` as integer nanoseconds since the
    UNIX epoch (UTC) or an ISO string, and fixed-precision 1e-9 integer prices. Returns
    columns ts_event(tz-aware NY), open, high, low, close, volume, instrument_id(if present).

    If the export is a Databento "parent" pull (all NQ outright contracts + calendar
    spreads, i.e. many rows per minute), it is collapsed to a single volume-based,
    unspliced continuous front-month series here (see ``to_continuous_front_month``).
    """
    raw = pd.read_csv(path)
    missing = {"ts_event", "open", "high", "low", "close", "volume"} - set(raw.columns)
    if missing:
        raise ValueError(f"{path}: missing required Databento columns {sorted(missing)}")

    ts = raw["ts_event"]
    if pd.api.types.is_numeric_dtype(ts):
        ts = pd.to_datetime(ts, unit="ns", utc=True)      # ns since epoch, UTC
    else:
        ts = pd.to_datetime(ts, utc=True)                 # ISO string (--pretty-ts export)
    ts = ts.dt.tz_convert(timezone)                        # DST-aware, never offset math

    out = pd.DataFrame({"ts_event": ts})
    scale = _resolve_price_scale(raw[_PRICE_COLS], price_scale)
    for c in _PRICE_COLS:
        out[c] = raw[c].astype("float64") / scale
    out["volume"] = raw["volume"].astype("int64")
    if "instrument_id" in raw.columns:
        out["instrument_id"] = raw["instrument_id"].astype("int64")
    if "symbol" in raw.columns:
        out["symbol"] = raw["symbol"].astype("string")

    if _is_parent_export(out):
        out = to_continuous_front_month(out, session_open)
    return out.drop(columns=[c for c in ("symbol",) if c in out.columns])


def _is_parent_export(df: pd.DataFrame) -> bool:
    """True if the frame holds many contracts (parent pull) rather than one clean series."""
    if "symbol" not in df.columns:
        return False
    s = df["symbol"]
    is_spread = s.str.contains("-", na=False)
    return bool(is_spread.any() or s[~is_spread].nunique() > 1)


def to_continuous_front_month(df: pd.DataFrame, session_open: time = time(18, 0)) -> pd.DataFrame:
    """Collapse a Databento parent export into one volume-based, unspliced continuous series.

    Rule (documented per spec-1 §3 Design Decisions: "continuous NQ,
    volume-based roll, unspliced"):
      * calendar spreads (symbols containing '-') are dropped — outright contracts only;
      * the front month for each CME trade date (18:00 ET session boundary) is the outright
        contract with the greatest total volume that session;
      * the continuous series takes that contract's 1-minute bars for the whole session and
        rolls at the session boundary when the front contract changes;
      * prices are NOT back-adjusted (unspliced), so a price gap appears at each roll — the
        roll is tagged downstream via the ``instrument_id`` change and surfaced in diagnostics.

    This reproduces Databento's NQ.v.0 continuous from the raw parent pull, transparently.
    """
    outr = df[~df["symbol"].str.contains("-", na=False)].copy()
    outr["_sd"] = _session_date(outr["ts_event"], session_open)
    daily_vol = outr.groupby(["_sd", "symbol"], observed=True)["volume"].sum().reset_index()
    front = (daily_vol.loc[daily_vol.groupby("_sd")["volume"].idxmax(), ["_sd", "symbol"]]
             .rename(columns={"symbol": "_front"}))
    merged = outr.merge(front, on="_sd")
    cont = merged[merged["symbol"] == merged["_front"]].copy()
    return (cont.drop(columns=["_sd", "_front"])
            .sort_values("ts_event", kind="stable").reset_index(drop=True))


def _resolve_price_scale(prices: pd.DataFrame, price_scale: float | None) -> float:
    """Databento stores prices as int * 1e-9. Auto-detect vs already-decimal exports."""
    if price_scale is not None:
        return price_scale
    med = float(pd.concat([prices[c] for c in _PRICE_COLS]).astype("float64").median())
    # NQ trades ~15k–25k; a fixed-precision value is ~1e13, a decimal value ~2e4.
    return 1e9 if med > 1e7 else 1.0


# ---------------------------------------------------------------- validate

def check_monotonic_unique(df: pd.DataFrame) -> None:
    """Raise if timestamps are duplicated or not strictly increasing."""
    ts = df["ts_event"]
    dup = ts[ts.duplicated(keep=False)]
    if not dup.empty:
        raise ValueError(f"duplicate timestamps ({dup.nunique()} distinct), e.g. {dup.iloc[0]}")
    if not ts.is_monotonic_increasing:
        bad = ts[ts.diff() <= pd.Timedelta(0)].iloc[0]
        raise ValueError(f"timestamps not strictly increasing at {bad}")


def tag_rolls(df: pd.DataFrame) -> pd.Series:
    """Boolean series: True on the first bar after ``instrument_id`` changes (contract roll)."""
    if "instrument_id" not in df.columns:
        return pd.Series(False, index=df.index)
    changed = df["instrument_id"].ne(df["instrument_id"].shift())
    changed.iloc[0] = False  # first bar is not a roll
    return changed


# ---------------------------------------------------------------- gap report

def _is_closed(idx: pd.DatetimeIndex) -> pd.Series:
    """Vectorized CME equity-index closed-session mask (maintenance break + weekend).

    Closed when: Mon–Thu 17:00–17:59 ET (daily maintenance); Fri >= 17:00; all Saturday;
    Sunday < 18:00. Holidays are NOT modeled here (they surface as gaps; cross-reference
    config/news_calendar.csv 'holiday' rows).
    """
    dow = idx.dayofweek            # Mon=0 .. Sun=6
    tmin = idx.hour * 60 + idx.minute
    maint = (tmin >= _MAINT_START.hour * 60) & (tmin < _MAINT_END.hour * 60)
    weekday_maint = (dow <= 3) & maint
    fri_close = (dow == 4) & (tmin >= _MAINT_START.hour * 60)
    sat = dow == 5
    sun_pre = (dow == 6) & (tmin < _MAINT_END.hour * 60)
    return pd.Series(weekday_maint | fri_close | sat | sun_pre, index=idx)


def _session_date(ts: pd.Series, session_open: time) -> pd.Series:
    """CME trade-date: bars at/after the maintenance break roll into the next day's session."""
    roll_next = ts.dt.time >= _MAINT_START
    return (ts.dt.normalize() + pd.to_timedelta(roll_next.astype(int), unit="D")).dt.date


def build_gap_report(df: pd.DataFrame, session_open: time) -> pd.DataFrame:
    """Per-session count of UNEXPECTED missing 1-minute bars (expected closures excluded)."""
    ts = df["ts_event"].reset_index(drop=True)
    records: list[dict] = []
    for i in range(len(ts) - 1):
        prev, nxt = ts[i], ts[i + 1]
        step = nxt - prev
        if step <= pd.Timedelta(minutes=1):
            continue
        # minutes strictly between prev and nxt that SHOULD have had a bar
        grid = pd.date_range(prev + pd.Timedelta(minutes=1), nxt - pd.Timedelta(minutes=1),
                             freq="1min")
        if len(grid) == 0:
            continue
        open_minutes = grid[~_is_closed(grid).to_numpy()]
        if len(open_minutes) == 0:
            continue
        records.append({
            "session_date": _session_date(pd.Series([prev]), session_open).iloc[0],
            "gap_start": prev,
            "gap_end": nxt,
            "missing_minutes": int(len(open_minutes)),
        })
    if not records:
        return pd.DataFrame(columns=["session_date", "missing_minutes", "n_gaps",
                                     "largest_gap_start", "largest_gap_end"])
    g = pd.DataFrame(records)
    agg = (g.groupby("session_date")
             .apply(lambda s: pd.Series({
                 "missing_minutes": int(s["missing_minutes"].sum()),
                 "n_gaps": len(s),
                 "largest_gap_start": s.loc[s["missing_minutes"].idxmax(), "gap_start"],
                 "largest_gap_end": s.loc[s["missing_minutes"].idxmax(), "gap_end"],
             }), include_groups=False)
             .reset_index())
    return agg


# ---------------------------------------------------------------- orchestrate

def ingest(cfg: IngestConfig) -> IngestResult:
    """Full pipeline: read -> validate -> tag rolls -> gap report -> write parquet."""
    df = read_databento_csv(cfg.input_path, cfg.timezone, cfg.price_scale, cfg.session_open)
    df = df.sort_values("ts_event", kind="stable").reset_index(drop=True)
    check_monotonic_unique(df)
    df["roll"] = tag_rolls(df)

    gaps = build_gap_report(df, cfg.session_open)
    roll_dates = sorted({str(d) for d in df.loc[df["roll"], "ts_event"].dt.date})

    out = df[CANONICAL_COLUMNS].copy()
    cfg.output_parquet.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(cfg.output_parquet, index=False)
    cfg.gap_report_path.parent.mkdir(parents=True, exist_ok=True)
    gaps.to_csv(cfg.gap_report_path, index=False)

    return IngestResult(
        n_bars=len(out),
        start=df["ts_event"].iloc[0],
        end=df["ts_event"].iloc[-1],
        n_rolls=int(df["roll"].sum()),
        roll_dates=roll_dates,
        unexpected_missing_minutes=int(gaps["missing_minutes"].sum()) if not gaps.empty else 0,
        n_gap_sessions=len(gaps),
        output_parquet=cfg.output_parquet,
        gap_report_path=cfg.gap_report_path,
        frame=out,
    )


def main(argv: list[str]) -> None:
    if not argv:
        sys.exit("usage: python -m src.engine.data <databento_csv> [out.parquet]")
    tz = load_strategy_timezone()
    cfg = IngestConfig(input_path=Path(argv[0]), timezone=tz,
                       **({"output_parquet": Path(argv[1])} if len(argv) > 1 else {}))
    r = ingest(cfg)
    print(f"ingested {r.n_bars} bars  {r.start} -> {r.end}")
    print(f"rolls: {r.n_rolls} {r.roll_dates}")
    print(f"unexpected missing minutes: {r.unexpected_missing_minutes} "
          f"across {r.n_gap_sessions} session(s) -> {r.gap_report_path}")
    print(f"wrote {r.output_parquet}")


if __name__ == "__main__":
    main(sys.argv[1:])
