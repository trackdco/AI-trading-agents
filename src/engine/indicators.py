"""Indicators: Bollinger Bands, anchored VWAPs with sigma bands, volume profile.

Spec: spec-1-market-engine-backtester.md, Step 4. Strategy §2 indicator stack.

Formula choices are pinned to TradingView conventions because the Step 4
PARITY GATE compares against Angus's TradingView charts:
  - Bollinger: SMA of close, POPULATION std (ddof=0), ±2σ (§2: BB 20/SMA/close/2σ)
  - VWAP: hlc3 typical price, volume-weighted; bands are the volume-weighted
    std of typical price: sqrt(cum(v*tp²)/cum(v) − vwap²)
  - Daily VWAP anchors at the 18:00 ET session open (§2 CONFIRMED); NY VWAP
    anchors 09:30 ET and DOES NOT EXIST pre-anchor (§2, architecture inv. 1)
  - Volume profile: each 1m bar's volume split equally across the price bins
    its range touches (engineering approximation — TradingView's internal
    allocation is proprietary; the parity gate judges whether it's close
    enough). Value area expands greedily from POC toward the higher-volume
    neighbor until value_area_pct is covered.

All VWAP/profile computations run on the 1m table and are causal: the value
on a row is the value as of that bar's close. Higher-TF consumers sample by
timestamp (step 5). CLI: python -m src.engine.indicators --parity  writes
output/parity_report.md once real data exists (GATE: Angus sign-off).
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml

from src.engine.data import session_date

logger = logging.getLogger(__name__)

NY_TZ = ZoneInfo("America/New_York")
NY_OPEN_MINUTES = 9 * 60 + 30  # §2 — NY VWAP anchor 09:30 ET cash open


def load_indicator_config(path: Path = Path("config/strategy.yaml")) -> dict:
    """Indicator parameters from strategy.yaml (§2). No magic numbers."""
    with open(path) as f:
        cfg = yaml.safe_load(f)["indicators"]
    return {
        "bb_length": int(cfg["bollinger"]["length"]),
        "bb_mult": float(cfg["bollinger"]["stdev_mult"]),
        "band_sigmas": [int(s) for s in cfg["daily_vwap"]["bands_sigma"]],
        "value_area_pct": float(cfg["volume_profile"]["value_area_pct"]),
        "bin_ticks": int(cfg["volume_profile"]["profile_bin_ticks"]),
        "weekly_enabled": bool(cfg["volume_profile"]["weekly_enabled"]),
    }


# ---------------------------------------------------------------- Bollinger


def bollinger(df_tf: pd.DataFrame, length: int, mult: float) -> pd.DataFrame:
    """BB(length, SMA, close, mult·σ) on one TF frame. NaN until the window fills.

    Population std (ddof=0) to match TradingView's ta.stdev.
    """
    out = df_tf.copy()
    roll = out["close"].rolling(length)
    out["bb_basis"] = roll.mean()
    sd = roll.std(ddof=0)
    out["bb_upper"] = out["bb_basis"] + mult * sd
    out["bb_lower"] = out["bb_basis"] - mult * sd
    return out


# ------------------------------------------------------------------- VWAPs


def _typical_price(df: pd.DataFrame) -> pd.Series:
    return (df["high"] + df["low"] + df["close"]) / 3.0


def _anchored_vwap(df: pd.DataFrame, group: pd.Series, prefix: str, sigmas: list[int]) -> pd.DataFrame:
    """Cumulative volume-weighted TP and sigma bands within each group segment."""
    out = df.copy()
    tp = _typical_price(out)
    v = out["volume"].astype("float64")
    pv = (tp * v).groupby(group).cumsum()
    pv2 = (tp * tp * v).groupby(group).cumsum()
    cv = v.groupby(group).cumsum()
    vwap = pv / cv
    var = (pv2 / cv - vwap * vwap).clip(lower=0.0)
    sd = np.sqrt(var)
    out[prefix] = vwap
    for s in sigmas:
        out[f"{prefix}_up_{s}"] = vwap + s * sd
        out[f"{prefix}_dn_{s}"] = vwap - s * sd
    return out


def daily_vwap(df_1m: pd.DataFrame, sigmas: list[int]) -> pd.DataFrame:
    """Daily VWAP ±σ, anchored at the 18:00 ET session open (§2 CONFIRMED).

    The step-2 session_date already rolls 18:00+ bars into the next session,
    so grouping by it IS the 18:00 anchor.
    """
    df = df_1m.copy()
    if "session_date" not in df.columns:
        df["session_date"] = session_date(df["ts_event"])
    return _anchored_vwap(df, df["session_date"], "daily_vwap", sigmas)


def ny_vwap(df_1m: pd.DataFrame, sigmas: list[int]) -> pd.DataFrame:
    """NY VWAP ±σ anchored 09:30 ET; NaN for every bar before the anchor.

    §2 / architecture invariant 1: the NY VWAP does not exist pre-market.
    Pre-9:30 rows (including the prior evening) stay NaN — proven by the
    mandatory test_ny_vwap_absent_premarket.
    """
    df = df_1m.copy()
    if "session_date" not in df.columns:
        df["session_date"] = session_date(df["ts_event"])
    minutes = df["ts_event"].dt.hour * 60 + df["ts_event"].dt.minute
    # NY cash window on the session's calendar date: 09:30 <= t < 18:00
    in_ny = (minutes >= NY_OPEN_MINUTES) & (minutes < 18 * 60)
    cols_before = set(df.columns)
    computed = _anchored_vwap(df[in_ny], df.loc[in_ny, "session_date"], "ny_vwap", sigmas)
    for col in set(computed.columns) - cols_before:
        df[col] = np.nan
        df.loc[in_ny, col] = computed[col]
    return df


# ---------------------------------------------------------- Volume profile


@dataclass
class Profile:
    """POC/VAH/VAL + HVN/LVN for one price-volume histogram (§2)."""

    poc: float
    vah: float
    val: float
    hvn: list[float] = field(default_factory=list)
    lvn: list[float] = field(default_factory=list)
    total_volume: float = 0.0


def _histogram(df: pd.DataFrame, bin_size: float) -> tuple[np.ndarray, int]:
    """Volume histogram: each bar's volume split equally across bins its range touches."""
    lo_bin = np.floor(df["low"].to_numpy() / bin_size).astype(int)
    hi_bin = np.floor(df["high"].to_numpy() / bin_size).astype(int)
    base = int(lo_bin.min())
    hist = np.zeros(int(hi_bin.max()) - base + 1)
    vol = df["volume"].to_numpy(dtype=float)
    for lo, hi, v in zip(lo_bin - base, hi_bin - base, vol):
        hist[lo : hi + 1] += v / (hi - lo + 1)
    return hist, base


def _profile_from_hist(hist: np.ndarray, base: int, bin_size: float, va_pct: float) -> Profile:
    poc_idx = int(hist.argmax())
    total = float(hist.sum())
    covered = hist[poc_idx]
    lo = hi = poc_idx
    while covered < va_pct * total:
        vol_below = hist[lo - 1] if lo > 0 else -1.0
        vol_above = hist[hi + 1] if hi < len(hist) - 1 else -1.0
        if vol_above >= vol_below:
            hi += 1
            covered += vol_above
        else:
            lo -= 1
            covered += vol_below

    def center(i: int) -> float:
        return (base + i + 0.5) * bin_size

    interior = range(1, len(hist) - 1)
    hvn = [center(i) for i in interior if hist[i] > hist[i - 1] and hist[i] > hist[i + 1]]
    lvn = [center(i) for i in interior if hist[i] < hist[i - 1] and hist[i] < hist[i + 1]]
    return Profile(
        poc=center(poc_idx), vah=center(hi), val=center(lo), hvn=hvn, lvn=lvn, total_volume=total
    )


def volume_profile(df_slice: pd.DataFrame, bin_size: float, va_pct: float) -> Profile:
    """Profile of any bar slice: a session box, a day, or (behind the §2
    flag, weekly_enabled) a week. The caller chooses the slice; this keeps
    the weekly variant config-gated without a separate code path."""
    if df_slice.empty:
        raise ValueError("cannot profile an empty slice")
    hist, base = _histogram(df_slice, bin_size)
    return _profile_from_hist(hist, base, bin_size, va_pct)


def running_daily_profile(df_1m: pd.DataFrame, bin_size: float, va_pct: float) -> pd.DataFrame:
    """Causal developing daily profile: POC/VAH/VAL as of each bar's close.

    The daily POC is a §3 core cluster level, so it must be available
    intraday without lookahead: row i reflects bars [session start .. i].
    """
    df = df_1m.reset_index(drop=True).copy()
    if "session_date" not in df.columns:
        df["session_date"] = session_date(df["ts_event"])
    poc = np.empty(len(df))
    vah = np.empty(len(df))
    val = np.empty(len(df))
    for _, day in df.groupby("session_date", sort=False):
        lo_bin = np.floor(day["low"].to_numpy() / bin_size).astype(int)
        hi_bin = np.floor(day["high"].to_numpy() / bin_size).astype(int)
        base = int(lo_bin.min())
        hist = np.zeros(int(hi_bin.max()) - base + 1)
        vol = day["volume"].to_numpy(dtype=float)
        for row, (lo, hi, v) in zip(day.index, zip(lo_bin - base, hi_bin - base, vol)):
            hist[lo : hi + 1] += v / (hi - lo + 1)
            prof = _profile_from_hist(hist, base, bin_size, va_pct)
            poc[row], vah[row], val[row] = prof.poc, prof.vah, prof.val
    df["daily_poc"], df["daily_vah"], df["daily_val"] = poc, vah, val
    return df


# ------------------------------------------------------------ Parity gate


PARITY_TIMESTAMPS = ["2026-02-11 09:48", "2026-02-17 09:50"]  # spec step 4, ET
ENTRY_TFS = [1, 2, 3, 5]


def parity_report(
    parquet_path: Path = Path("data/nq_1m.parquet"),
    out_path: Path = Path("output/parity_report.md"),
    config_path: Path = Path("config/strategy.yaml"),
) -> Path:
    """Computed vs chart values for the two spec timestamps (GATE — Angus).

    BB basis is reported on every entry TF (+15m) since the chart TF is
    Angus's; he matches whichever he trades from. Chart columns are blank for
    him to fill. Do not proceed past step 4 without his sign-off.
    """
    from src.engine.sessions import resample  # local import avoids cycle

    cfg = load_indicator_config(config_path)
    tick = 0.25
    df = pd.read_parquet(parquet_path)
    df = daily_vwap(df, cfg["band_sigmas"])
    df = ny_vwap(df, cfg["band_sigmas"])
    df = running_daily_profile(df, cfg["bin_ticks"] * tick, cfg["value_area_pct"])

    lines = [
        "# Parity Report — Spec 1 Step 4 GATE",
        "",
        "Tolerance: within **1.0 NQ point** of the reference chart (spec step 4).",
        "Angus: fill the `chart` column from TradingView and sign off below.",
        "",
    ]
    for ts_str in PARITY_TIMESTAMPS:
        ts = pd.Timestamp(ts_str, tz=NY_TZ)
        row = df[df["ts_event"] == ts]
        if row.empty:
            lines += [f"## {ts_str} ET — **NO DATA BAR AT THIS TIMESTAMP**", ""]
            continue
        r = row.iloc[0]
        lines += [f"## {ts_str} ET", "", "| value | computed | chart | Δ |", "|---|---|---|---|"]
        for tf in ENTRY_TFS + [15]:
            bars = bollinger(resample(df, tf), cfg["bb_length"], cfg["bb_mult"])
            asof = bars[bars["ts_close"] <= ts].iloc[-1]
            lines.append(f"| BB basis ({tf}m) | {asof['bb_basis']:.2f} | | |")
        for label, col in [
            ("daily VWAP", "daily_vwap"),
            ("daily VWAP +1σ", "daily_vwap_up_1"),
            ("daily VWAP −1σ", "daily_vwap_dn_1"),
            ("NY VWAP", "ny_vwap"),
            ("daily POC", "daily_poc"),
        ]:
            lines.append(f"| {label} | {r[col]:.2f} | | |")
        lines.append("")
    lines += ["---", "", "**Angus sign-off:** (date / PASS / FAIL + notes)", ""]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    logger.info("wrote %s", out_path)
    return out_path


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parity", action="store_true", help="write output/parity_report.md")
    args = parser.parse_args(argv)
    if args.parity:
        parity_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
