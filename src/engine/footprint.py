"""Canonical loader for the aggressor-tagged footprint tape.

THE ONLY SUPPORTED PATH TO ``data/reference/cvd/footprint_*.parquet``.

Why this module exists
----------------------
Two defects were being re-created by every consumer that read the parquets directly.

**1. Roll contamination.** The raw Databento ``GLBX.MDP3`` trades pull carries
calendar-spread and back-month prints alongside the front-month outright.
``data/reference/cvd/README.md`` states the remedy -- "keeping only ticks inside each
day's ground-truth ``[low, high]`` band" -- but that cleaning was applied to SOME
committed files and not others, and no consumer re-applied it. Measured on the London
08:00-10:00 window, 2025-06-02 -> 2026-07-17:

    3.91% of window volume is off-band, in 121 of 292 sessions,
    clustered on the mid-Jun / mid-Sep / mid-Dec quarterly roll weeks.
    Uncleaned, the p95 one-minute traded range reads 94,700 ticks.

A percentage band does NOT work: the back-month's cost-of-carry (~0.5-1.5%) sits
inside a +/-2% band, and a +/-2% band still leaves a p90 minute range of 950 ticks.
The band must come from a front-month ground truth. Provenance of the defect:
programme verdict D5, "Roll contamination via day-level banding ... 2025-09-15's raw
VPOC was 239.90 -- a calendar-spread price."

**2. Inverted delta sign.** ``side='B'`` is the BUYER-aggressor (lifted the offer), so
signed delta is ``B - A``. Two consumers had it backwards. Settled empirically, not by
reading prose -- London-window session delta against the realised open-to-close move
from the independent 1m bar master, 287 sessions:

    B - A :  pearson r = +0.7293 (all 287), +0.7754 (|move|>=40pt, n=138), +0.7944 (top 20)
             sign agreement 78.4% / 89.9% / 95.0%
    A - B :  the exact negative of the above

Use :func:`signed_delta`; do not hand-roll the subtraction.

Sealed-span safety
------------------
:func:`load_footprint` refuses to read any ``*holdout*`` file unless the caller passes
``allow_holdout=True``, which only a declared look may do. The assertion lives here, at
the chokepoint, rather than being restated in every consumer.
"""
from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd

CVD_DIR = Path("data/reference/cvd")
DEPTH_LONDON = Path("data/reference/depth_london")
BAND_SLACK_PTS = 50.0

#: ``side`` value that denotes the BUYER-aggressor (lifted the offer). See module
#: docstring for the empirical audit that pins this.
BUY_AGGRESSOR = "B"
SELL_AGGRESSOR = "A"

_BID = [f"bid_px_{i:02d}" for i in range(10)]
_ASK = [f"ask_px_{i:02d}" for i in range(10)]


def fit_span_files(cvd_dir: Path = CVD_DIR) -> list[Path]:
    """Every non-sealed footprint parquet, sorted. Holdout files are excluded by name."""
    return [Path(p) for p in sorted(glob.glob(str(cvd_dir / "footprint_*.parquet")))
            if "holdout" not in Path(p).name]


def front_month_bands(depth_dir: Path = DEPTH_LONDON,
                      slack: float = BAND_SLACK_PTS) -> dict:
    """Per-session ``[lo, hi]`` price band from the depth book, which is front-month by
    construction (``NQ.v.0``). Returns ``{date: (lo, hi)}`` keyed on London-local dates.
    """
    bands: dict = {}
    for f in sorted(glob.glob(str(depth_dir / "*.csv"))):
        d = pd.read_csv(f, usecols=["ts_event"] + _BID + _ASK)
        day = (pd.to_datetime(d["ts_event"], utc=True)
                 .dt.tz_convert("Europe/London").dt.date.iloc[0])
        px = d[_BID + _ASK].to_numpy(dtype=float)
        px = px[np.isfinite(px)]
        if px.size:
            bands[day] = (float(px.min()) - slack, float(px.max()) + slack)
    return bands


_BANDS_CACHE: dict | None = None


def cached_front_month_bands(depth_dir: Path = DEPTH_LONDON) -> dict | None:
    """:func:`front_month_bands` memoised for the process, and None (not an error) when
    the depth directory is absent. Call sites use this so importing a consumer does not
    read 295 CSVs, and so a missing depth tree degrades to a loud warning rather than a
    crash."""
    global _BANDS_CACHE
    if _BANDS_CACHE is None:
        _BANDS_CACHE = front_month_bands(depth_dir) if Path(depth_dir).exists() else {}
    return _BANDS_CACHE or None


def bands_from_bars(bars: pd.DataFrame, tz: str = "Europe/London",
                    slack: float = BAND_SLACK_PTS) -> dict:
    """Fallback band for sessions with no depth (anything before 2025-06-02): the 1m
    master's own daily ``[low, high]``. This is the method
    ``data/reference/cvd/README.md`` describes. ``bars`` needs ts_event/high/low.
    """
    b = bars.copy()
    b["_day"] = pd.to_datetime(b["ts_event"], utc=True).dt.tz_convert(tz).dt.date
    g = b.groupby("_day")
    return {d: (float(x["low"].min()) - slack, float(x["high"].max()) + slack)
            for d, x in g}


def load_footprint(paths, bands: dict | None, *, allow_holdout: bool = False,
                   columns=("ts_minute", "price", "side", "volume"),
                   tz: str = "Europe/London", report: bool = True) -> pd.DataFrame:
    """Load footprint parquets, band-cleaned to the front month.

    paths   : iterable of parquet paths
    bands   : ``{date: (lo, hi)}`` from :func:`front_month_bands` or :func:`bands_from_bars`
    returns : DataFrame with a ``day`` column (local date in *tz*), off-band rows removed

    Raises ``PermissionError`` if a sealed holdout file is passed without an explicit
    declaration. Sessions with no band are dropped and reported, never silently kept.
    """
    paths = [Path(p) for p in paths]
    sealed = [p for p in paths if "holdout" in p.name]
    if sealed and not allow_holdout:
        raise PermissionError(
            "sealed holdout footprint requested without allow_holdout=True: "
            + ", ".join(p.name for p in sealed)
            + " -- a declared look in the docs/VALIDATION-PROCESS.md section 4 ledger is required"
        )
    if bands is not None and "price" not in columns:
        raise ValueError("'price' is required to band-clean; add it to `columns`")
    if bands is None and report:
        print("[footprint] WARNING: bands=None — tape is NOT band-cleaned "
              "(calendar-spread and back-month prints are included)")
    frames, kept, dropped, unbanded = [], 0, 0, set()
    for p in paths:
        df = pd.read_parquet(p, columns=list(columns))
        df["ts_minute"] = pd.to_datetime(df["ts_minute"], utc=True)
        df["day"] = df["ts_minute"].dt.tz_convert(tz).dt.date
        if bands is None:
            frames.append(df)
            kept += int(df["volume"].sum())
            continue
        lo = df["day"].map(lambda d: bands.get(d, (np.nan, np.nan))[0])
        hi = df["day"].map(lambda d: bands.get(d, (np.nan, np.nan))[1])
        unbanded |= set(df.loc[lo.isna(), "day"].unique())
        ok = (df["price"] >= lo) & (df["price"] <= hi)
        kept += int(df.loc[ok, "volume"].sum())
        dropped += int(df.loc[~ok, "volume"].sum())
        frames.append(df.loc[ok])
    out = pd.concat(frames, ignore_index=True).sort_values("ts_minute")
    if report:
        tot = kept + dropped
        print(f"[footprint] {len(out):,} rows | dropped {dropped:,}/{tot:,} volume "
              f"({100 * dropped / max(tot, 1):.3f}%) as off-band")
        if unbanded:
            s = sorted(unbanded)
            print(f"[footprint] WARNING {len(s)} sessions had no band and were DROPPED "
                  f"ENTIRELY: {s[:5]}{' ...' if len(s) > 5 else ''}")
    return out


def band_filter(df: pd.DataFrame, bands: dict | None,
                tz: str = "Europe/London") -> pd.DataFrame:
    """Drop off-band (calendar-spread / back-month) rows from an already-loaded
    footprint frame. One-line migration path for consumers that keep their own read
    loop. ``bands=None`` is a no-op with a warning, so the omission is never silent.
    """
    if bands is None:
        print("[footprint] WARNING: no bands supplied — frame is NOT band-cleaned")
        return df
    day = pd.to_datetime(df["ts_minute"], utc=True).dt.tz_convert(tz).dt.date
    lo = day.map(lambda d: bands.get(d, (np.nan, np.nan))[0])
    hi = day.map(lambda d: bands.get(d, (np.nan, np.nan))[1])
    return df.loc[(df["price"] >= lo) & (df["price"] <= hi)]


def signed_delta(df: pd.DataFrame, by=("ts_minute",)) -> pd.Series:
    """Signed volume delta, BUY-aggressor positive: ``B - A``.

    The sign is not a convention we are free to choose -- see the module docstring for
    the empirical audit (r = +0.78 against realised move on large-move sessions). Every
    consumer must call this rather than subtracting by hand.
    """
    signed = np.where(df["side"] == BUY_AGGRESSOR, df["volume"], -df["volume"])
    return pd.Series(signed, index=df.index).groupby(
        [df[c] for c in by]).sum() if by else pd.Series(signed, index=df.index).sum()
