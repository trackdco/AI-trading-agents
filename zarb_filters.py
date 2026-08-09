#!/usr/bin/env python3
"""
zarb_filters.py
===============

Conditional-lift measurement for three Zarb-derived bias filters, applied to an
existing NY trade population, with proximity-matched placebo controls.

WHAT THIS MEASURES
------------------
F1  GOLDEN RULE      Entry above previous-day POC -> long only; below -> short only.
                     Measured as conditional lift on the NY trade population.

F2  MIDNIGHT OPEN    Entry below the 00:00 ET open  -> discount -> long only;
                     above -> premium -> short only.
                     Measured as conditional lift on the NY trade population.

F3  80% RULE         Session-level base rate, NOT a trade filter. Two variants:
                       (a) CANONICAL: price trades outside the prior day's value
                           area, then trades inside for two consecutive 30-minute
                           periods -> does it traverse the full value area?
                       (b) ZARB VARIANT: session opens without engaging the prior
                           day's POC -> does it engage the POC intraday?
                     Reported separately, as pipeline validation. The canonical
                     variant has a published independent range of roughly 60-70%
                     on ES, so if this script returns something wildly outside
                     that band on NQ, suspect the pipeline before the finding.

PROFILE CONSTRUCTION
--------------------
Previous-day volume profile over an 18:00 -> 16:30 ET session window, value area
at 68%, built from 30-MINUTE bars. The 30-minute resample is deliberate and not
a performance shortcut: profile levels shift with the timeframe they are read
from, and Zarb's stated levels come off a 30-minute chart. Building from 1-minute
bars produces a different (finer) POC and would not be the level he trades.

Volume is distributed uniformly across each bar's high-low range at tick
resolution. This is an approximation -- true volume-at-price needs trade prints,
which OHLCV does not carry. It is the same approximation charting packages make.

PLACEBO CONTROLS (non-negotiable, and the reason this script exists)
-------------------------------------------------------------------
The last level-based claim tested on this book had both placebos fire at roughly
5x the real effect. So every lift statistic here is compared against a null built
from synthetic levels, two independent ways:

  NULL A  offset-preserving:  keep |POC - session open| per day (proximity
          matched), randomise the sign, apply multiplicative jitter. The
          synthetic level sits as close to price as the real one but in an
          arbitrary location.

  NULL B  day-shuffled:       permute real levels across trading days. Preserves
          the marginal distribution of levels, breaks the day-specific link.

A filter passes only if its real lift exceeds the 95th percentile of BOTH nulls.
Pre-registration is enforced: the hypothesis set and decision rule are written to
disk and hashed BEFORE any result is computed.

UNITS
-----
R is the primary unit throughout; points are reported alongside. If the trade
file carries no stop price, R cannot be computed and the script falls back to
points, says so loudly, and marks every R field as unavailable rather than
silently substituting a dollar-derived proxy.

USAGE
-----
    # verify the script runs end to end on synthetic data first
    python zarb_filters.py --selfcheck

    # then point it at real data
    python zarb_filters.py \
        --bars    /path/to/nq_ohlcv_1m.csv \
        --trades  /path/to/ny_trades.csv \
        --outdir  ./zarb_out \
        --bars-tz UTC --trades-tz UTC

Requires: pandas, numpy (no other dependencies).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------

ET = ZoneInfo("America/New_York")

TICK_SIZE = 0.25          # NQ
POINT_VALUE = 20.0        # $ per NQ point, 1 contract

SESSION_OPEN = time(18, 0)    # profile window open, ET  (Zarb's stated window)
SESSION_CLOSE = time(16, 30)  # profile window close, ET
# NOTE: CME's actual NQ close is 17:00 ET. 16:30 is what Zarb states and what was
# selected. SESSION_CLOSE is exposed as a CLI arg -- worth a 17:00 sensitivity run.

VALUE_AREA_PCT = 0.68     # Zarb's stated setting (70% is the other convention)
PROFILE_TF_MIN = 30       # read levels off the 30-minute chart

NY_OPEN = time(9, 30)
NY_CLOSE = time(16, 0)

PLACEBO_DRAWS = 200
PLACEBO_PCTILE = 95.0
JITTER_LO, JITTER_HI = 0.80, 1.20

MIN_BUCKET_N = 30         # below this, descriptive only -- no verdict
BOOTSTRAP_DRAWS = 5000
SEED = 20260810


# ----------------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------------

BAR_ALIASES = {
    "timestamp": ["timestamp", "time", "datetime", "date", "ts", "bar_time", "open_time"],
    "open":      ["open", "o", "Open"],
    "high":      ["high", "h", "High"],
    "low":       ["low", "l", "Low"],
    "close":     ["close", "c", "Close"],
    "volume":    ["volume", "v", "Volume", "vol"],
}

TRADE_ALIASES = {
    "entry_ts":    ["entry_ts", "dateStart", "entry_time", "entry_timestamp",
                    "entrytime", "open_time", "timestamp"],
    "exit_ts":     ["exit_ts", "dateEnd", "exit_time", "exit_timestamp", "close_time"],
    "side":        ["side", "direction", "dir", "trade_side", "type"],
    "entry_price": ["entry_price", "entryPrice", "entry", "price_in"],
    "exit_price":  ["exit_price", "avgClosePrice", "exit", "price_out", "close_price"],
    # FXReplay ships this misspelled as "initalSL" -- both spellings accepted.
    "stop_price":  ["stop_price", "initalSL", "initialSL", "stop", "sl", "stop_loss"],
    "r_multiple":  ["r_multiple", "r", "R", "rMultiple", "r_mult"],
    "tags":        ["tags", "tag", "notes", "label"],
}


def _to_et(s: pd.Series, tz: str, label: str) -> pd.Series:
    """
    Parse a timestamp column to tz-aware ET.

    Handles the case that bit us in testing and will bite on any real multi-month
    NQ file: once a span crosses a DST boundary, an offset-bearing CSV contains
    BOTH -05:00 and -04:00, and pandas refuses to parse the mixed offsets without
    being told to normalise. Naive timestamps are localised to `tz`; offset-bearing
    ones are normalised through UTC and then converted, so both paths land in ET.
    """
    try:
        ts = pd.to_datetime(s, errors="coerce")
    except (ValueError, TypeError):
        ts = pd.to_datetime(s, errors="coerce", utc=True)
    if ts.isna().any():
        raise ValueError(
            f"{int(ts.isna().sum())} {label} timestamps failed to parse. "
            "Check the timestamp format."
        )
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize(ZoneInfo(tz))
    return ts.dt.tz_convert(ET)


def _resolve(cols: List[str], aliases: List[str]) -> Optional[str]:
    lower = {c.lower(): c for c in cols}
    for a in aliases:
        if a in cols:
            return a
        if a.lower() in lower:
            return lower[a.lower()]
    return None


def load_bars(path: Path, tz: str) -> pd.DataFrame:
    """Load OHLCV bars, return tz-aware ET-indexed frame."""
    df = pd.read_csv(path)
    mapping = {}
    for canon, aliases in BAR_ALIASES.items():
        found = _resolve(list(df.columns), aliases)
        if found is None:
            raise ValueError(
                f"Bar file is missing a column for '{canon}'. "
                f"Looked for any of: {aliases}. Found columns: {list(df.columns)}"
            )
        mapping[found] = canon
    df = df.rename(columns=mapping)[list(BAR_ALIASES.keys())]

    df["timestamp"] = _to_et(df["timestamp"], tz, "bar")

    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"]).sort_values("timestamp")
    df = df.set_index("timestamp")
    df["volume"] = df["volume"].fillna(0.0)
    return df


def load_trades(path: Path, tz: str) -> Tuple[pd.DataFrame, bool]:
    """
    Load the trade population. Returns (frame, r_available).

    Required: entry_ts, side, entry_price, exit_price.
    Optional: exit_ts, stop_price, r_multiple, tags.
    """
    df = pd.read_csv(path)
    cols = list(df.columns)
    out = pd.DataFrame(index=df.index)

    for canon in ("entry_ts", "side", "entry_price", "exit_price"):
        found = _resolve(cols, TRADE_ALIASES[canon])
        if found is None:
            raise ValueError(
                f"Trade file is missing a column for '{canon}'. "
                f"Looked for any of: {TRADE_ALIASES[canon]}. Found: {cols}"
            )
        out[canon] = df[found]

    for canon in ("exit_ts", "stop_price", "r_multiple", "tags"):
        found = _resolve(cols, TRADE_ALIASES[canon])
        out[canon] = df[found] if found is not None else np.nan

    out["entry_ts"] = _to_et(out["entry_ts"], tz, "entry")

    if out["exit_ts"].notna().any():
        try:
            out["exit_ts"] = _to_et(out["exit_ts"], tz, "exit")
        except ValueError:
            # exit timestamps are optional and unused by the analysis; a partial or
            # malformed exit column must not block the run
            out["exit_ts"] = pd.NaT

    # direction: +1 long, -1 short
    def _side(v) -> float:
        if pd.isna(v):
            return np.nan
        s = str(v).strip().lower()
        if s in ("1", "+1", "buy", "long", "b", "l", "bull"):
            return 1.0
        if s in ("-1", "sell", "short", "s", "bear"):
            return -1.0
        return np.nan

    out["dir"] = out["side"].map(_side)
    if out["dir"].isna().any():
        vals = sorted(set(out.loc[out["dir"].isna(), "side"].astype(str)))
        raise ValueError(f"Unrecognised side values: {vals}")

    for c in ("entry_price", "exit_price", "stop_price", "r_multiple"):
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out = out.dropna(subset=["entry_price", "exit_price"]).copy()

    # points is always computable
    out["points"] = out["dir"] * (out["exit_price"] - out["entry_price"])
    out["dollars"] = out["points"] * POINT_VALUE

    # R: use supplied r_multiple if present, else derive from stop
    if out["r_multiple"].notna().sum() >= max(1, int(0.8 * len(out))):
        out["R"] = out["r_multiple"]
        r_available = True
        r_source = "supplied r_multiple column"
    elif out["stop_price"].notna().sum() >= max(1, int(0.8 * len(out))):
        risk = (out["entry_price"] - out["stop_price"]).abs()
        risk = risk.where(risk > 0)
        out["R"] = out["points"] / risk
        r_available = True
        r_source = "derived from entry_price and stop_price"
    else:
        out["R"] = np.nan
        r_available = False
        r_source = "UNAVAILABLE"

    out.attrs["r_source"] = r_source
    return out.reset_index(drop=True), r_available


# ----------------------------------------------------------------------------
# PROFILE CONSTRUCTION
# ----------------------------------------------------------------------------

def assign_session(ts: pd.Timestamp,
                   s_open: time = SESSION_OPEN,
                   s_close: time = SESSION_CLOSE) -> Optional[date]:
    """
    Label each bar with the DATE ITS SESSION CLOSES ON.

    A session runs s_open on day X through s_close on day X+1, so the session that
    closes 16:30 Tuesday is "Tuesday's profile" -- which is how a trader names it,
    and what "previous day's profile" then refers to. Bars in the maintenance gap
    (between s_close and s_open) return None and are excluded.
    """
    t = ts.time()
    if t >= s_open:
        return (ts + timedelta(days=1)).date()
    if t <= s_close:
        return ts.date()
    return None


def profile_bins(df: pd.DataFrame, tick: float) -> pd.Series:
    """Distribute each bar's volume uniformly across its high-low range at tick
    resolution. Returns volume-at-price indexed by price, ascending."""
    acc: Dict[int, float] = defaultdict(float)
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    vols = df["volume"].to_numpy()
    for h, l, v in zip(highs, lows, vols):
        if not np.isfinite(v) or v <= 0 or not np.isfinite(h) or not np.isfinite(l):
            continue
        lo_t = int(round(l / tick))
        hi_t = int(round(h / tick))
        if hi_t < lo_t:
            lo_t, hi_t = hi_t, lo_t
        n = hi_t - lo_t + 1
        share = v / n
        for t_ in range(lo_t, hi_t + 1):
            acc[t_] += share
    if not acc:
        return pd.Series(dtype=float)
    s = pd.Series(acc, dtype=float)
    s.index = s.index.astype(float) * tick
    return s.sort_index()


def value_area(bins: pd.Series, target_frac: float) -> Tuple[float, float, float]:
    """
    Standard Market Profile value-area expansion: start at the POC, then compare
    the two bins above against the two bins below and take the larger side, until
    cumulative volume reaches target_frac of the session total.

    Returns (poc, val, vah).
    """
    prices = bins.index.to_numpy()
    vols = bins.to_numpy()
    total = float(vols.sum())
    if total <= 0 or len(vols) == 0:
        return (np.nan, np.nan, np.nan)

    poc_i = int(np.argmax(vols))
    included = np.zeros(len(vols), dtype=bool)
    included[poc_i] = True
    acc = float(vols[poc_i])
    lo, hi = poc_i, poc_i
    target = total * target_frac

    while acc < target:
        up_idx = [i for i in (hi + 1, hi + 2) if i < len(vols)]
        dn_idx = [i for i in (lo - 1, lo - 2) if i >= 0]
        if not up_idx and not dn_idx:
            break
        up_vol = float(vols[up_idx].sum()) if up_idx else -1.0
        dn_vol = float(vols[dn_idx].sum()) if dn_idx else -1.0
        if up_vol >= dn_vol and up_idx:
            for i in up_idx:
                if not included[i]:
                    included[i] = True
                    acc += float(vols[i])
            hi = max(up_idx)
        elif dn_idx:
            for i in dn_idx:
                if not included[i]:
                    included[i] = True
                    acc += float(vols[i])
            lo = min(dn_idx)
        else:
            break

    sel = prices[included]
    return (float(prices[poc_i]), float(sel.min()), float(sel.max()))


def build_daily_levels(bars: pd.DataFrame,
                       s_open: time,
                       s_close: time,
                       va_pct: float,
                       tf_min: int) -> pd.DataFrame:
    """
    Per trading day, compute: the PREVIOUS session's POC/VAH/VAL/high/low, and the
    current day's midnight open. Indexed by trading date.
    """
    labels = [assign_session(ts, s_open, s_close) for ts in bars.index]
    b = bars.copy()
    b["session"] = labels
    b = b[b["session"].notna()]

    # resample to the profile timeframe within each session
    rows = []
    for sess, grp in b.groupby("session", sort=True):
        agg = grp.resample(f"{tf_min}min").agg(
            {"open": "first", "high": "max", "low": "min",
             "close": "last", "volume": "sum"}
        ).dropna(subset=["high", "low"])
        if agg.empty:
            continue
        bins = profile_bins(agg, TICK_SIZE)
        if bins.empty:
            continue
        poc, val, vah = value_area(bins, va_pct)
        rows.append({
            "session": sess,
            "poc": poc, "val": val, "vah": vah,
            "sess_high": float(agg["high"].max()),
            "sess_low": float(agg["low"].min()),
            "sess_open": float(agg["open"].iloc[0]),
            "n_bars": int(len(agg)),
            "total_volume": float(bins.sum()),
        })

    prof = pd.DataFrame(rows).sort_values("session").reset_index(drop=True)
    if prof.empty:
        raise ValueError("No sessions could be profiled. Check bar coverage and session window.")

    # shift so each row carries the PREVIOUS session's levels
    prev = prof.shift(1)
    out = pd.DataFrame({
        "trading_date": prof["session"],
        "prev_poc": prev["poc"],
        "prev_val": prev["val"],
        "prev_vah": prev["vah"],
        "prev_high": prev["sess_high"],
        "prev_low": prev["sess_low"],
        "prev_session": prev["session"],
        # CURRENT session's 18:00 open. Used only as the proximity-matching anchor
        # for the placebo engine. It must be independent of every level under test,
        # otherwise a placebo built from it collapses onto the real level and can
        # never fire -- which is exactly what happened when the midnight open was
        # used as the anchor while F2 was testing the midnight open.
        "day_open": prof["sess_open"],
    })

    # midnight open: first bar at or after 00:00 ET on the trading date
    mid = {}
    for d in out["trading_date"]:
        start = pd.Timestamp(datetime.combine(d, time(0, 0)), tz=ET)
        end = start + timedelta(hours=2)
        win = bars.loc[(bars.index >= start) & (bars.index < end)]
        mid[d] = float(win["open"].iloc[0]) if not win.empty else np.nan
    out["midnight_open"] = out["trading_date"].map(mid)

    return out.set_index("trading_date")


# ----------------------------------------------------------------------------
# STATISTICS
# ----------------------------------------------------------------------------

def describe(vals: np.ndarray) -> Dict[str, Optional[float]]:
    v = vals[np.isfinite(vals)]
    if len(v) == 0:
        return {"n": 0, "mean": None, "median": None, "win_rate": None,
                "sum": None, "std": None}
    return {
        "n": int(len(v)),
        "mean": float(np.mean(v)),
        "median": float(np.median(v)),
        "win_rate": float(np.mean(v > 0)),
        "sum": float(np.sum(v)),
        "std": float(np.std(v, ddof=1)) if len(v) > 1 else 0.0,
    }


def bootstrap_ci(vals: np.ndarray, rng: np.random.Generator,
                 draws: int = BOOTSTRAP_DRAWS,
                 lo: float = 2.5, hi: float = 97.5) -> Tuple[Optional[float], Optional[float]]:
    v = vals[np.isfinite(vals)]
    if len(v) < 3:
        return (None, None)
    idx = rng.integers(0, len(v), size=(draws, len(v)))
    means = v[idx].mean(axis=1)
    return (float(np.percentile(means, lo)), float(np.percentile(means, hi)))


def lift_stat(metric: np.ndarray, aligned: np.ndarray) -> Optional[float]:
    """
    Primary statistic: mean(aligned) - mean(all).

    Deliberately measured against the unfiltered baseline rather than against the
    opposed bucket, because the decision the filter actually informs is "take this
    trade or don't", not "flip it".
    """
    m = np.asarray(metric, dtype=float)
    a = np.asarray(aligned, dtype=bool)
    ok = np.isfinite(m)
    if ok.sum() == 0 or (a & ok).sum() == 0:
        return None
    return float(m[a & ok].mean() - m[ok].mean())


# ----------------------------------------------------------------------------
# FILTERS
# ----------------------------------------------------------------------------

def align_golden_rule(entry_price: np.ndarray, direction: np.ndarray,
                      level: np.ndarray) -> np.ndarray:
    """Above the level -> longs only. Below -> shorts only."""
    above = entry_price > level
    return np.where(direction > 0, above, ~above)


def align_midnight(entry_price: np.ndarray, direction: np.ndarray,
                   level: np.ndarray) -> np.ndarray:
    """Below the midnight open (discount) -> longs. Above (premium) -> shorts."""
    below = entry_price < level
    return np.where(direction > 0, below, ~below)


FILTERS = {
    "F1_golden_rule":   {"level_col": "prev_poc",      "fn": align_golden_rule,
                         "desc": "entry vs previous-day POC (18:00-16:30 ET profile, 68% VA)"},
    "F2_midnight_open": {"level_col": "midnight_open", "fn": align_midnight,
                         "desc": "entry vs 00:00 ET open (premium/discount)"},
}


# ----------------------------------------------------------------------------
# PLACEBO ENGINE
# ----------------------------------------------------------------------------

def placebo_offset_preserving(real_level: np.ndarray, ref: np.ndarray,
                              rng: np.random.Generator) -> np.ndarray:
    """
    NULL A. Keep the level's absolute distance from the session reference price
    (proximity matched), randomise the sign, apply multiplicative jitter. The
    synthetic level is as close to price as the real one but arbitrarily placed.
    """
    d = np.abs(real_level - ref)
    sign = rng.choice(np.array([-1.0, 1.0]), size=len(d))
    jitter = rng.uniform(JITTER_LO, JITTER_HI, size=len(d))
    return ref + sign * d * jitter


def placebo_day_shuffled(real_level: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """NULL B. Permute real levels across days. Preserves the marginal
    distribution of levels, destroys the day-specific link."""
    out = real_level.copy()
    finite = np.isfinite(out)
    vals = out[finite]
    rng.shuffle(vals)
    out[finite] = vals
    return out


def run_placebos(metric: np.ndarray, entry_price: np.ndarray, direction: np.ndarray,
                 real_level: np.ndarray, ref: np.ndarray, align_fn,
                 rng: np.random.Generator, draws: int) -> Dict[str, dict]:
    results = {}
    for name, gen in (
        ("null_A_offset_preserving", lambda: placebo_offset_preserving(real_level, ref, rng)),
        ("null_B_day_shuffled",      lambda: placebo_day_shuffled(real_level, rng)),
    ):
        stats = []
        for _ in range(draws):
            fake = gen()
            al = align_fn(entry_price, direction, fake)
            s = lift_stat(metric, al)
            if s is not None:
                stats.append(s)
        arr = np.array(stats, dtype=float)
        results[name] = {
            "draws": int(len(arr)),
            "mean": float(arr.mean()) if len(arr) else None,
            "p95": float(np.percentile(arr, PLACEBO_PCTILE)) if len(arr) else None,
            "p99": float(np.percentile(arr, 99)) if len(arr) else None,
            "max": float(arr.max()) if len(arr) else None,
        }
    return results


# ----------------------------------------------------------------------------
# F3 -- 80% RULE BASE RATES (session level, not a trade filter)
# ----------------------------------------------------------------------------

def eighty_percent_rule(bars: pd.DataFrame, levels: pd.DataFrame,
                        s_open: time, s_close: time) -> Dict[str, dict]:
    """
    Canonical: during the trading day, price trades outside the previous day's
    value area, then records two CONSECUTIVE 30-minute periods entirely inside it.
    Outcome: does price subsequently traverse the full value area (touch both VAL
    and VAH) before the session closes?

    Zarb variant: the session opens without engaging the previous day's POC.
    Outcome: does price engage the POC before the session closes?
    """
    canon_trig = canon_hit = 0
    zarb_trig = zarb_hit = 0

    for d, row in levels.iterrows():
        val, vah, poc = row["prev_val"], row["prev_vah"], row["prev_poc"]
        if not np.isfinite(val) or not np.isfinite(vah) or not np.isfinite(poc):
            continue

        start = pd.Timestamp(datetime.combine(d - timedelta(days=1), s_open), tz=ET)
        end = pd.Timestamp(datetime.combine(d, s_close), tz=ET)
        sess = bars.loc[(bars.index >= start) & (bars.index <= end)]
        if sess.empty:
            continue

        # ---- canonical ----
        p30 = sess.resample("30min").agg({"high": "max", "low": "min", "open": "first"}).dropna(subset=["high", "low"])
        if len(p30) >= 3:
            outside_seen = False
            inside_run = 0
            trigger_i = None
            for i, (_, p) in enumerate(p30.iterrows()):
                if p["high"] > vah or p["low"] < val:
                    outside_seen = True
                fully_inside = (p["low"] >= val) and (p["high"] <= vah)
                inside_run = inside_run + 1 if fully_inside else 0
                if outside_seen and inside_run >= 2:
                    trigger_i = i
                    break
            if trigger_i is not None:
                canon_trig += 1
                after = p30.iloc[trigger_i + 1:]
                if not after.empty:
                    touched_low = bool((after["low"] <= val).any())
                    touched_high = bool((after["high"] >= vah).any())
                    if touched_low and touched_high:
                        canon_hit += 1

        # ---- Zarb variant ----
        open_px = float(sess["open"].iloc[0])
        first = sess.iloc[0]
        engaged_at_open = (first["low"] <= poc <= first["high"])
        if not engaged_at_open and np.isfinite(open_px):
            zarb_trig += 1
            rest = sess.iloc[1:]
            if not rest.empty and bool(((rest["low"] <= poc) & (rest["high"] >= poc)).any()):
                zarb_hit += 1

    def _pack(trig, hit, note):
        return {"triggers": int(trig), "hits": int(hit),
                "rate": (float(hit / trig) if trig else None), "note": note}

    return {
        "canonical_80pct_rule": _pack(
            canon_trig, canon_hit,
            "Independent tests on ES cluster at 60-70%, not 80%. A result far "
            "outside that band on NQ is more likely a pipeline fault than a finding."),
        "zarb_poc_engagement_variant": _pack(
            zarb_trig, zarb_hit,
            "No published base rate exists for this variant. It does not inherit "
            "the canonical rule's evidence."),
    }


# ----------------------------------------------------------------------------
# BARS-ONLY MODE -- measure the filters as directional bias, no trades required
# ----------------------------------------------------------------------------

def build_bar_population(bars: pd.DataFrame, levels: pd.DataFrame,
                         cfg: dict) -> pd.DataFrame:
    """
    One observation per trading day: enter at the 09:30 ET open, hold to 16:00 ET,
    with a declared fixed stop.

    Both directional outcomes are precomputed per session. A filter (or a placebo)
    then only SELECTS which of the two it would have taken, so a 200-draw placebo
    sweep costs two bar-walks per session in total rather than 200. Because the
    outcome set is fixed before any level is consulted, no placebo draw can alter
    the underlying data -- only which side of it gets picked.

    Intrabar ambiguity: if a single 1-minute bar contains both the stop and a
    larger favourable excursion, the stop is assumed first. Conservative, and it
    applies identically to real and placebo directions, so it cannot bias the
    comparison.
    """
    S = float(cfg["declared_stop"])
    rows = []
    for d, row in levels.iterrows():
        if not (np.isfinite(row["prev_poc"]) and np.isfinite(row["midnight_open"])
                and np.isfinite(row["day_open"])):
            continue
        start = pd.Timestamp(datetime.combine(d, NY_OPEN), tz=ET)
        end = pd.Timestamp(datetime.combine(d, NY_CLOSE), tz=ET)
        w = bars.loc[(bars.index >= start) & (bars.index <= end)]
        if len(w) < 30:
            continue

        entry = float(w["open"].iloc[0])
        hi = w["high"].to_numpy(dtype=float)
        lo = w["low"].to_numpy(dtype=float)
        cl = float(w["close"].iloc[-1])

        rec = {
            "trading_date": d, "entry_price": entry, "n_bars": int(len(w)),
            "prev_poc": float(row["prev_poc"]),
            "midnight_open": float(row["midnight_open"]),
            "day_open": float(row["day_open"]),
            "prev_val": row["prev_val"], "prev_vah": row["prev_vah"],
        }

        for dname, ds in (("long", 1.0), ("short", -1.0)):
            stop_px = entry - ds * S
            hit = np.nonzero(lo <= stop_px)[0] if ds > 0 else np.nonzero(hi >= stop_px)[0]
            stopped = len(hit) > 0
            fav_arr = hi if ds > 0 else lo
            adv_arr = lo if ds > 0 else hi
            if stopped:
                k = int(hit[0])
                r = -1.0
                mfe = float(np.max(ds * (fav_arr[:k + 1] - entry)))
                mae = S
            else:
                r = ds * (cl - entry) / S
                mfe = float(np.max(ds * (fav_arr - entry)))
                mae = float(max(0.0, -np.min(ds * (adv_arr - entry))))
            rec[f"R_{dname}"] = r
            rec[f"MFE_{dname}"] = mfe
            rec[f"MAE_{dname}"] = mae
            rec[f"pts_{dname}"] = ds * (cl - entry)
            rec[f"stopped_{dname}"] = bool(stopped)
        rows.append(rec)

    pop = pd.DataFrame(rows)
    if pop.empty:
        raise ValueError("No sessions produced a usable NY window. Check bar coverage.")
    return pop


def select_by_dir(pop: pd.DataFrame, dirs: np.ndarray, field: str) -> np.ndarray:
    return np.where(dirs > 0,
                    pop[f"{field}_long"].to_numpy(dtype=float),
                    pop[f"{field}_short"].to_numpy(dtype=float))


BAR_FILTERS = {
    "F1_golden_rule": {
        "level_col": "prev_poc",
        "dir_fn": lambda px, lvl: np.where(px > lvl, 1.0, -1.0),
        "desc": "long above previous-day POC, short below (18:00-16:30 ET, 68% VA)",
    },
    "F2_midnight_open": {
        "level_col": "midnight_open",
        "dir_fn": lambda px, lvl: np.where(px < lvl, 1.0, -1.0),
        "desc": "long below the 00:00 ET open (discount), short above (premium)",
    },
}


def analyse_bars(bars: pd.DataFrame, outdir: Path, cfg: dict) -> dict:
    rng = np.random.default_rng(cfg["seed"])
    levels = build_daily_levels(bars, cfg["session_open"], cfg["session_close"],
                               cfg["va_pct"], cfg["profile_tf"])
    pop = build_bar_population(bars, levels, cfg)

    entry_px = pop["entry_price"].to_numpy(dtype=float)
    ref = pop["day_open"].to_numpy(dtype=float)
    n = len(pop)

    always_long = pop["R_long"].to_numpy(dtype=float)
    always_short = pop["R_short"].to_numpy(dtype=float)

    results = {
        "mode": "bars",
        "metric": "R at declared stop",
        "declared_stop_points": cfg["declared_stop"],
        "counts": {"sessions_analysed": int(n),
                   "date_min": str(pop["trading_date"].min()),
                   "date_max": str(pop["trading_date"].max())},
        "drift_baselines": {
            "always_long": describe(always_long),
            "always_short": describe(always_short),
            "note": ("If one of these is strongly positive, the span has directional "
                     "drift and any filter that leans that way will look good for "
                     "reasons unrelated to its level. Null C is what controls for it."),
        },
        "filters": {},
    }

    for fname, spec in BAR_FILTERS.items():
        lvl = pop[spec["level_col"]].to_numpy(dtype=float)
        dirs = spec["dir_fn"](entry_px, lvl)
        R = select_by_dir(pop, dirs, "R")
        real = float(np.nanmean(R))
        frac_long = float(np.mean(dirs > 0))

        ci_lo, ci_hi = bootstrap_ci(R, rng)

        nulls: Dict[str, dict] = {}

        # NULL A -- proximity-matched synthetic level
        stats = [float(np.nanmean(select_by_dir(
            pop, spec["dir_fn"](entry_px, placebo_offset_preserving(lvl, ref, rng)), "R")))
            for _ in range(cfg["placebo_draws"])]
        nulls["null_A_offset_preserving"] = _null_pack(stats)

        # NULL B -- levels permuted across days
        stats = [float(np.nanmean(select_by_dir(
            pop, spec["dir_fn"](entry_px, placebo_day_shuffled(lvl, rng)), "R")))
            for _ in range(cfg["placebo_draws"])]
        nulls["null_B_day_shuffled"] = _null_pack(stats)

        # NULL C -- random directions matched to this filter's own long/short mix.
        # This is the null that matters most: it holds the filter's directional
        # imbalance fixed and destroys only the level information, so beating it
        # means the LEVEL carried signal rather than the filter merely leaning the
        # way the market drifted.
        stats = []
        for _ in range(cfg["placebo_draws"]):
            fake_dirs = np.where(rng.random(n) < frac_long, 1.0, -1.0)
            stats.append(float(np.nanmean(select_by_dir(pop, fake_dirs, "R"))))
        nulls["null_C_direction_matched"] = _null_pack(stats)

        if n < 100:
            verdict = f"DESCRIPTIVE ONLY - only {n} sessions, need 100+"
        else:
            p95s = [v["p95"] for v in nulls.values() if v["p95"] is not None]
            verdict = ("LIFT SHOWN (beats all three nulls)"
                       if p95s and all(real > p for p in p95s)
                       else "NO LIFT (fails at least one null)")

        results["filters"][fname] = {
            "description": spec["desc"],
            "level_column": spec["level_col"],
            "mean_R": real,
            "mean_R_ci95": [ci_lo, ci_hi],
            "fraction_long": frac_long,
            "MFE_points": describe(select_by_dir(pop, dirs, "MFE")),
            "MAE_points": describe(select_by_dir(pop, dirs, "MAE")),
            "close_points": describe(select_by_dir(pop, dirs, "pts")),
            "stopped_rate": float(np.mean(select_by_dir(
                pop, dirs, "stopped").astype(bool))),
            "nulls": nulls,
            "verdict": verdict,
        }

    results["f3_base_rates"] = eighty_percent_rule(
        bars, levels, cfg["session_open"], cfg["session_close"])

    pop.to_csv(outdir / "bar_population.csv", index=False)
    levels.to_csv(outdir / "daily_levels.csv")
    (outdir / "RESULTS.json").write_text(json.dumps(results, indent=2, default=str))
    return results


def _null_pack(stats: List[float]) -> dict:
    arr = np.array([s for s in stats if np.isfinite(s)], dtype=float)
    if not len(arr):
        return {"draws": 0, "mean": None, "p95": None, "p99": None, "max": None}
    return {"draws": int(len(arr)), "mean": float(arr.mean()),
            "p95": float(np.percentile(arr, PLACEBO_PCTILE)),
            "p99": float(np.percentile(arr, 99)), "max": float(arr.max())}


def report_bars(res: dict, digest: str) -> str:
    L: List[str] = []
    add = L.append
    add("=" * 78)
    add("ZARB BIAS FILTERS - DIRECTIONAL TEST ON BARS (no trade population needed)")
    add("=" * 78)
    add(f"PREREG sha256 : {digest}")
    add(f"Metric        : R at a declared {res['declared_stop_points']:.0f}-point stop, "
        f"09:30 entry -> 16:00 ET exit")
    add("                The stop is DECLARED, not a real one. R here is a common")
    add("                yardstick for comparing directions, not a tradeable result.")
    c = res["counts"]
    add(f"Sessions      : {c['sessions_analysed']}  ({c['date_min']} -> {c['date_max']})")

    add("")
    add("DRIFT BASELINES (what you get with no filter at all)")
    for k in ("always_long", "always_short"):
        d = res["drift_baselines"][k]
        add(f"  {k:<13} n={d['n']:<5} mean R={d['mean']:+.4f}  "
            f"median={d['median']:+.4f}  win={d['win_rate']*100:.1f}%")

    for fname, f in res["filters"].items():
        add("")
        add("-" * 78)
        add(f"{fname}  --  {f['description']}")
        add("-" * 78)
        add(f"  mean R        : {f['mean_R']:+.4f}   "
            f"CI95 [{f['mean_R_ci95'][0]:+.4f}, {f['mean_R_ci95'][1]:+.4f}]")
        add(f"  long/short    : {f['fraction_long']*100:.1f}% long   "
            f"(stopped out {f['stopped_rate']*100:.1f}% of sessions)")
        for label, key in (("MFE", "MFE_points"), ("MAE", "MAE_points"),
                           ("close", "close_points")):
            d = f[key]
            add(f"  {label:<13} : mean {d['mean']:+.2f} pts   median {d['median']:+.2f} pts")
        for nn, nv in f["nulls"].items():
            if nv["p95"] is not None:
                add(f"  {nn:<28} draws={nv['draws']:<4} mean={nv['mean']:+.4f}  "
                    f"p95={nv['p95']:+.4f}  max={nv['max']:+.4f}")
        add(f"  VERDICT: {f['verdict']}")

    add("")
    add("-" * 78)
    add("F3  80% RULE BASE RATES (pipeline validation)")
    add("-" * 78)
    for k, v in res["f3_base_rates"].items():
        rate = f"{v['rate']*100:.1f}%" if v["rate"] is not None else "n/a"
        add(f"  {k}: {v['hits']}/{v['triggers']} = {rate}")
        add(f"      {v['note']}")

    add("")
    add("=" * 78)
    add("NULL C IS THE ONE THAT MATTERS. Nulls A and B only randomise WHERE the")
    add("level sits. Null C holds the filter's own long/short mix fixed and destroys")
    add("only the level information -- so a filter that beats A and B but fails C is")
    add("capturing directional drift, not reading the level.")
    add("Fit-side measurement only. No holdout was touched.")
    add("=" * 78)
    return "\n".join(L)


# ----------------------------------------------------------------------------
# PRE-REGISTRATION
# ----------------------------------------------------------------------------

def preregister(outdir: Path, cfg: dict, n_trades: int, r_available: bool,
                mode: str = "trades") -> str:
    if mode == "bars":
        prereg = {
            "written_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "bars (directional test, no trade population)",
            "primary_metric": f"R at a declared {cfg.get('declared_stop')}-point stop",
            "primary_statistic": "mean R of the filter-directed session population",
            "hypotheses": {
                "F1_golden_rule": "Taking the direction implied by price vs the "
                                  "previous-day POC at 09:30 produces positive mean R.",
                "F2_midnight_open": "Taking the direction implied by price vs the "
                                    "00:00 ET open at 09:30 produces positive mean R.",
            },
            "decision_rule": (
                f"A filter is declared to show lift ONLY IF its mean R exceeds the "
                f"{PLACEBO_PCTILE:.0f}th percentile of ALL THREE nulls "
                f"(A offset-preserving level, B day-shuffled level, "
                f"C direction-frequency-matched), each from "
                f"{cfg['placebo_draws']} draws. Failing any null = no lift. "
                f"Null C is decisive: passing A and B while failing C means the "
                f"filter captured directional drift, not level information. "
                f"Fewer than 100 sessions = descriptive only, no verdict."
            ),
            "secondary_reported": ["MFE points", "MAE points", "close points",
                                   "stopped-out rate", "always-long and "
                                   "always-short drift baselines"],
            "config": cfg,
        }
    else:
        prereg = {
            "written_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "trades (conditional lift on an existing population)",
            "primary_metric": "R per trade" if r_available else "POINTS per trade (R unavailable)",
            "primary_statistic": "mean(filter-aligned) - mean(all trades)",
            "hypotheses": {
                "F1_golden_rule": "Restricting NY trades to those aligned with the "
                                  "previous-day-POC bias raises mean R per trade.",
                "F2_midnight_open": "Restricting NY trades to those aligned with "
                                    "midnight-open premium/discount raises mean R per trade.",
            },
            "decision_rule": (
                f"A filter is declared to show lift ONLY IF its real statistic exceeds "
                f"the {PLACEBO_PCTILE:.0f}th percentile of BOTH null distributions "
                f"(offset-preserving and day-shuffled), each built from "
                f"{cfg['placebo_draws']} draws. Failing either null = no lift. "
                f"Buckets with n < {MIN_BUCKET_N} are reported descriptively with no verdict."
            ),
            "secondary_reported": ["median R", "win rate", "mean points", "bootstrap 95% CI"],
            "config": cfg,
            "n_trades": n_trades,
            "r_available": r_available,
        }
    prereg["f3_status"] = ("F3 is a session-level base rate, reported for pipeline "
                          "validation only. It is not part of the lift hypotheses.")
    blob = json.dumps(prereg, sort_keys=True, indent=2)
    digest = hashlib.sha256(blob.encode()).hexdigest()
    prereg["sha256"] = digest
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "PREREG.json").write_text(json.dumps(prereg, sort_keys=True, indent=2))
    return digest


# ----------------------------------------------------------------------------
# MAIN ANALYSIS
# ----------------------------------------------------------------------------

def analyse(bars: pd.DataFrame, trades: pd.DataFrame, r_available: bool,
            outdir: Path, cfg: dict) -> dict:
    rng = np.random.default_rng(cfg["seed"])

    levels = build_daily_levels(bars, cfg["session_open"], cfg["session_close"],
                                cfg["va_pct"], cfg["profile_tf"])

    # restrict to the NY window and attach levels
    t = trades.copy()
    t["trading_date"] = [ts.date() for ts in t["entry_ts"]]
    t["entry_time"] = [ts.time() for ts in t["entry_ts"]]
    in_ny = t["entry_time"].apply(lambda x: NY_OPEN <= x <= NY_CLOSE)
    n_all = len(t)
    t = t[in_ny].copy()
    n_ny = len(t)

    t = t.join(levels, on="trading_date")
    before = len(t)
    t = t[t["prev_poc"].notna() & t["midnight_open"].notna()
          & t["day_open"].notna()].copy()
    dropped = before - len(t)

    if t.empty:
        raise ValueError("No NY trades survived level attachment. Check date overlap "
                         "between the bar file and the trade file.")

    metric_name = "R" if r_available else "points"
    metric = t[metric_name].to_numpy(dtype=float)
    entry_px = t["entry_price"].to_numpy(dtype=float)
    direction = t["dir"].to_numpy(dtype=float)
    # Proximity-matching anchor: the current session's 18:00 open. Chosen because
    # it is independent of BOTH tested levels. Anchoring on a price that is itself
    # under test makes the placebo identical to the real level.
    ref = t["day_open"].to_numpy(dtype=float)

    results = {
        "metric": metric_name,
        "r_available": r_available,
        "r_source": trades.attrs.get("r_source", "unknown"),
        "counts": {
            "trades_in_file": n_all,
            "trades_in_ny_window": n_ny,
            "dropped_no_levels": int(dropped),
            "trades_analysed": int(len(t)),
        },
        "baseline": {
            "R": describe(t["R"].to_numpy(dtype=float)),
            "points": describe(t["points"].to_numpy(dtype=float)),
        },
        "filters": {},
    }

    for fname, spec in FILTERS.items():
        lvl = t[spec["level_col"]].to_numpy(dtype=float)
        aligned = spec["fn"](entry_px, direction, lvl)
        real = lift_stat(metric, aligned)

        a_R = t["R"].to_numpy(dtype=float)[aligned]
        o_R = t["R"].to_numpy(dtype=float)[~aligned]
        a_P = t["points"].to_numpy(dtype=float)[aligned]
        o_P = t["points"].to_numpy(dtype=float)[~aligned]

        ci_lo, ci_hi = bootstrap_ci(metric[aligned], rng)
        nulls = run_placebos(metric, entry_px, direction, lvl, ref,
                             spec["fn"], rng, cfg["placebo_draws"])

        n_aligned = int(aligned.sum())
        n_opposed = int((~aligned).sum())
        underpowered = (n_aligned < MIN_BUCKET_N) or (n_opposed < MIN_BUCKET_N)

        if real is None:
            verdict = "NO RESULT (statistic not computable)"
        elif underpowered:
            verdict = (f"DESCRIPTIVE ONLY - underpowered "
                       f"(aligned n={n_aligned}, opposed n={n_opposed}, "
                       f"need {MIN_BUCKET_N} each)")
        else:
            p95s = [v["p95"] for v in nulls.values() if v["p95"] is not None]
            beats_all = bool(p95s) and all(real > p for p in p95s)
            verdict = "LIFT SHOWN (beats both nulls)" if beats_all else "NO LIFT (fails a null)"

        results["filters"][fname] = {
            "description": spec["desc"],
            "level_column": spec["level_col"],
            "real_lift": real,
            "aligned_bootstrap_ci95": [ci_lo, ci_hi],
            "aligned": {"R": describe(a_R), "points": describe(a_P)},
            "opposed": {"R": describe(o_R), "points": describe(o_P)},
            "nulls": nulls,
            "verdict": verdict,
        }

    results["f3_base_rates"] = eighty_percent_rule(
        bars, levels, cfg["session_open"], cfg["session_close"])

    t.to_csv(outdir / "trades_with_levels.csv", index=False)
    levels.to_csv(outdir / "daily_levels.csv")
    (outdir / "RESULTS.json").write_text(json.dumps(results, indent=2, default=str))
    return results


def report(res: dict, digest: str) -> str:
    L: List[str] = []
    add = L.append
    unit = res["metric"]

    add("=" * 78)
    add("ZARB BIAS FILTERS - CONDITIONAL LIFT ON THE NY POPULATION")
    add("=" * 78)
    add(f"PREREG sha256 : {digest}")
    add(f"Primary unit  : {unit.upper()}   (R source: {res['r_source']})")
    if not res["r_available"]:
        add("")
        add("  !! R IS UNAVAILABLE IN THIS TRADE FILE.")
        add("  !! No stop price and no r_multiple column, so every figure below is")
        add("  !! in POINTS. Points are size-invariant but not risk-normalised, so")
        add("  !! these numbers are NOT comparable to any R figure on the board.")
        add("  !! Fix the stop capture before treating any verdict here as final.")
    c = res["counts"]
    add("")
    add(f"Trades in file {c['trades_in_file']} -> NY window {c['trades_in_ny_window']} "
        f"-> analysed {c['trades_analysed']} (dropped for missing levels: {c['dropped_no_levels']})")

    b = res["baseline"]
    add("")
    add("BASELINE (all analysed NY trades)")
    for k in ("R", "points"):
        d = b[k]
        if d["n"]:
            add(f"  {k:<7} n={d['n']:<5} mean={d['mean']:+.4f}  median={d['median']:+.4f}  "
                f"win={d['win_rate']*100:.1f}%")
        else:
            add(f"  {k:<7} unavailable")

    for fname, f in res["filters"].items():
        add("")
        add("-" * 78)
        add(f"{fname}  --  {f['description']}")
        add("-" * 78)
        for bucket in ("aligned", "opposed"):
            for k in ("R", "points"):
                d = f[bucket][k]
                if d["n"]:
                    add(f"  {bucket:<8} {k:<7} n={d['n']:<5} mean={d['mean']:+.4f}  "
                        f"median={d['median']:+.4f}  win={d['win_rate']*100:.1f}%")
                else:
                    add(f"  {bucket:<8} {k:<7} unavailable")
        rl = f["real_lift"]
        add(f"  REAL LIFT ({unit}, aligned mean - all mean): "
            f"{rl:+.4f}" if rl is not None else "  REAL LIFT: not computable")
        ci = f["aligned_bootstrap_ci95"]
        if ci[0] is not None:
            add(f"  aligned mean 95% CI: [{ci[0]:+.4f}, {ci[1]:+.4f}]")
        for nname, n in f["nulls"].items():
            if n["p95"] is not None:
                add(f"  {nname:<26} draws={n['draws']:<4} "
                    f"mean={n['mean']:+.4f}  p95={n['p95']:+.4f}  max={n['max']:+.4f}")
        add(f"  VERDICT: {f['verdict']}")

    add("")
    add("-" * 78)
    add("F3  80% RULE BASE RATES (session level - pipeline validation, not a filter)")
    add("-" * 78)
    for k, v in res["f3_base_rates"].items():
        rate = f"{v['rate']*100:.1f}%" if v["rate"] is not None else "n/a"
        add(f"  {k}: {v['hits']}/{v['triggers']} = {rate}")
        add(f"      {v['note']}")

    add("")
    add("=" * 78)
    add("A verdict of LIFT SHOWN means the filter beat proximity-matched random")
    add("levels on both nulls. It does NOT mean the filter is validated out of")
    add("sample - this is fit-side measurement only. No holdout was touched.")
    add("=" * 78)
    return "\n".join(L)


# ----------------------------------------------------------------------------
# SELF-CHECK
# ----------------------------------------------------------------------------

def selfcheck(outdir: Path) -> None:
    """Generate synthetic bars and trades, run the full pipeline, prove it works.

    The synthetic trades carry NO real edge, so the correct outcome is 'NO LIFT'
    on both filters. If this self-check reports lift, the placebo engine is broken
    and nothing downstream should be trusted.
    """
    rng = np.random.default_rng(7)
    idx = pd.date_range("2026-01-01 18:00", "2026-03-31 16:00", freq="1min", tz=ET)
    idx = idx[[(t.time() >= SESSION_OPEN) or (t.time() <= SESSION_CLOSE) for t in idx]]
    n = len(idx)
    px = 21000 + np.cumsum(rng.normal(0, 1.1, n))
    bars = pd.DataFrame({
        "open": px,
        "high": px + np.abs(rng.normal(0, 1.6, n)),
        "low": px - np.abs(rng.normal(0, 1.6, n)),
        "close": px + rng.normal(0, 0.6, n),
        "volume": rng.integers(40, 900, n).astype(float),
    }, index=idx)
    bars.index.name = "timestamp"

    ny = bars[[NY_OPEN <= t.time() <= NY_CLOSE for t in bars.index]]
    pick = rng.choice(len(ny), size=260, replace=False)
    pick.sort()
    ent = ny.iloc[pick]
    dirs = rng.choice([1, -1], size=len(ent))
    ep = ent["close"].to_numpy()
    stop = ep - dirs * 30.0
    xp = ep + dirs * rng.normal(2.0, 22.0, len(ent))
    tr = pd.DataFrame({
        "dateStart": [t.tz_convert("UTC").strftime("%Y-%m-%d %H:%M:%S") for t in ent.index],
        "side": ["buy" if d > 0 else "sell" for d in dirs],
        "entryPrice": ep,
        "avgClosePrice": xp,
        "initalSL": stop,
    })

    outdir.mkdir(parents=True, exist_ok=True)
    bp, tp = outdir / "_selfcheck_bars.csv", outdir / "_selfcheck_trades.csv"
    bars.to_csv(bp)
    tr.to_csv(tp, index=False)

    b = load_bars(bp, "UTC")
    t_, r_ok = load_trades(tp, "UTC")
    cfg = {"session_open": SESSION_OPEN, "session_close": SESSION_CLOSE,
           "va_pct": VALUE_AREA_PCT, "profile_tf": PROFILE_TF_MIN,
           "placebo_draws": 60, "seed": SEED, "declared_stop": 30.0}
    cfg_ser = dict(cfg, session_open=str(SESSION_OPEN), session_close=str(SESSION_CLOSE))

    d1 = preregister(outdir, cfg_ser, 0, True, mode="bars")
    res1 = analyse_bars(b, outdir, cfg)
    print(report_bars(res1, d1))

    print("\n\n" + "#" * 78 + "\n# TRADES MODE\n" + "#" * 78 + "\n")
    d2 = preregister(outdir, cfg_ser, len(t_), r_ok, mode="trades")
    res2 = analyse(b, t_, r_ok, outdir, cfg)
    print(report(res2, d2))

    print("\n[selfcheck] Both modes ran end to end on a random walk.")
    print("[selfcheck] TRADES mode: R is i.i.d. and independent of direction and")
    print("[selfcheck] price by construction, so NO LIFT is provably correct.")
    print("[selfcheck] BARS mode: a driftless random walk carries no directional")
    print("[selfcheck] edge, so NO LIFT is the expected result there too.")
    print("[selfcheck] Every null p95 must be NON-ZERO. A null of exactly 0.0000")
    print("[selfcheck] means the placebo collapsed onto the real level and can")
    print("[selfcheck] never fire -- stop and report it rather than trusting a verdict.")
    print("[selfcheck] IGNORE the F3 percentages: random walks are not auctions, so")
    print("[selfcheck] value-area traversal has no reason to land in the 60-70% band.")


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def _parse_time(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bars", type=Path, help="OHLCV CSV (1-minute or finer)")
    ap.add_argument("--trades", type=Path, help="NY trade population CSV")
    ap.add_argument("--outdir", type=Path, default=Path("./zarb_out"))
    ap.add_argument("--bars-tz", default="UTC", help="timezone of bar timestamps if naive")
    ap.add_argument("--trades-tz", default="UTC", help="timezone of trade timestamps if naive")
    ap.add_argument("--session-open", default="18:00", help="profile window open, ET")
    ap.add_argument("--session-close", default="16:30", help="profile window close, ET")
    ap.add_argument("--va-pct", type=float, default=VALUE_AREA_PCT)
    ap.add_argument("--profile-tf", type=int, default=PROFILE_TF_MIN,
                    help="minutes; 30 matches the chart Zarb reads levels from")
    ap.add_argument("--placebo-draws", type=int, default=PLACEBO_DRAWS)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--mode", choices=["bars", "trades"], default="bars",
                    help="bars: directional test, needs ONLY --bars (default). "
                         "trades: conditional lift, needs a trade population with R.")
    ap.add_argument("--declared-stop", type=float, default=30.0,
                    help="bars mode only: declared stop in points, for the R yardstick")
    ap.add_argument("--selfcheck", action="store_true",
                    help="run on synthetic data to validate the pipeline")
    a = ap.parse_args(argv)

    if a.selfcheck:
        selfcheck(a.outdir)
        return 0
    if not a.bars:
        ap.error("--bars is required (or use --selfcheck)")
    if a.mode == "trades" and not a.trades:
        ap.error("--mode trades requires --trades")

    cfg = {"session_open": _parse_time(a.session_open),
           "session_close": _parse_time(a.session_close),
           "va_pct": a.va_pct, "profile_tf": a.profile_tf,
           "placebo_draws": a.placebo_draws, "seed": a.seed,
           "declared_stop": a.declared_stop}
    cfg_ser = dict(cfg, session_open=a.session_open, session_close=a.session_close)

    bars = load_bars(a.bars, a.bars_tz)

    if a.mode == "bars":
        digest = preregister(a.outdir, cfg_ser, 0, True, mode="bars")
        print(f"[prereg] {a.outdir/'PREREG.json'}  sha256={digest[:16]}...\n")
        res = analyse_bars(bars, a.outdir, cfg)
        text = report_bars(res, digest)
    else:
        trades, r_ok = load_trades(a.trades, a.trades_tz)
        digest = preregister(a.outdir, cfg_ser, len(trades), r_ok, mode="trades")
        print(f"[prereg] {a.outdir/'PREREG.json'}  sha256={digest[:16]}...\n")
        res = analyse(bars, trades, r_ok, a.outdir, cfg)
        text = report(res, digest)

    print(text)
    (a.outdir / "REPORT.txt").write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
