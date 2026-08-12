"""L1 — the behaviour census. Every event, no selection.

Per event (all prices from NQ 1m bars, ET clock):
  ref            last 1m close BEFORE the release minute (T-1 close) —
                 the realistic pre-positioning price
  drift_Wm       ref − close(T−W)  for W in DRIFT_WINDOWS (pre-release drift)
  rel_*          release bar open/high/low/close/range/volume
  move_Hm        close(T+H) − ref  for H in HORIZONS
  mfe/mae up/dn  extremes vs ref over (T .. T+120]
  gapfill        for each stop distance S and both directions:
                   stopped?  adverse extreme over bars [T, T+1] ≥ S
                   realized loss BOUNDS: best = S (fill at stop — never true
                   through a print), worst = adverse extreme (fill at the
                   hole). Truth is bracketed, reported as a range.

Timezone doctrine (repo history: 3 DST bugs): parse UTC → tz_convert(ET).
Never localize naive timestamps.

Units: points AND R (R = points / stop), R printed first. NQ $20/pt.
"""
from __future__ import annotations
import glob
import pandas as pd
import numpy as np

from .config import (TZ_ET, STOP_GRID_PTS, HORIZONS_MIN, DRIFT_WINDOWS_MIN,
                     DEFAULT_STOP_PTS, SEAL_FROM, unsealed,
                     SURPRISE_TO_NQ_SIGN)


# ---------------------------------------------------------------------------
# Bars
# ---------------------------------------------------------------------------
def load_bars(paths_glob: str) -> pd.DataFrame:
    """Load Databento OHLCV-1m csv(.zst). Schema pinned to the repo's files:
    ts_event ISO-UTC-ns, human-unit prices, raw contract symbols (NQZ5...).
    Front month = per-ET-day dominant symbol by volume (matches Databento's
    volume roll within a day's tolerance; plug docs/CONTRACT-ROLL-DATES.md
    here if exact roll-day behaviour ever matters to an event)."""
    frames = []
    for p in sorted(glob.glob(paths_glob)):
        df = pd.read_csv(p, usecols=["ts_event", "open", "high", "low",
                                     "close", "volume", "symbol"])
        frames.append(df)
    if not frames:
        raise FileNotFoundError(paths_glob)
    bars = pd.concat(frames, ignore_index=True)
    ts = pd.to_datetime(bars["ts_event"], utc=True)
    bars["ts_et"] = ts.dt.tz_convert(TZ_ET)
    bars["et_date"] = bars["ts_et"].dt.date
    # keep outright NQ contracts only (NQH5/M/U/Z + digit), drop spreads
    bars = bars[bars["symbol"].str.fullmatch(r"NQ[HMUZ]\d")]
    dom = (bars.groupby(["et_date", "symbol"])["volume"].sum()
               .reset_index()
               .sort_values(["et_date", "volume"], ascending=[True, False])
               .drop_duplicates("et_date")
               .set_index("et_date")["symbol"])
    bars = bars[bars["symbol"] == bars["et_date"].map(dom)]
    bars = (bars.drop_duplicates("ts_et")
                .set_index("ts_et").sort_index())
    return bars[["open", "high", "low", "close", "volume", "symbol"]]


# ---------------------------------------------------------------------------
# Per-event measurement
# ---------------------------------------------------------------------------
def _close_at(bars: pd.DataFrame, t: pd.Timestamp):
    """Close of the bar stamped exactly t; falls back to last bar ≤ t within
    3 minutes (thin tape), else None."""
    if t in bars.index:
        return float(bars.at[t, "close"])
    w = bars.loc[:t]
    if len(w) and (t - w.index[-1]) <= pd.Timedelta(minutes=3):
        return float(w["close"].iloc[-1])
    return None


def measure_event(bars: pd.DataFrame, ts_release_et: pd.Timestamp) -> dict | None:
    T = ts_release_et.floor("min")
    pre_need = max(DRIFT_WINDOWS_MIN)
    post_need = max(HORIZONS_MIN)
    win = bars.loc[T - pd.Timedelta(minutes=pre_need + 5):
                   T + pd.Timedelta(minutes=post_need + 1)]
    if len(win) < (pre_need + post_need) * 0.7:
        return dict(coverage_ok=False)
    ref = _close_at(bars, T - pd.Timedelta(minutes=1))
    if ref is None or T not in bars.index:
        return dict(coverage_ok=False)
    out = dict(coverage_ok=True, ref=ref)
    for w in DRIFT_WINDOWS_MIN:
        c = _close_at(bars, T - pd.Timedelta(minutes=w))
        out[f"drift_{w}m"] = None if c is None else ref - c
    rb = bars.loc[T]
    out.update(rel_open=float(rb["open"]), rel_high=float(rb["high"]),
               rel_low=float(rb["low"]), rel_close=float(rb["close"]),
               rel_range=float(rb["high"] - rb["low"]),
               rel_dir=float(np.sign(rb["close"] - ref)),
               rel_vol=float(rb["volume"]))
    for h in HORIZONS_MIN:
        c = _close_at(bars, T + pd.Timedelta(minutes=h))
        out[f"move_{h}m"] = None if c is None else c - ref
    post = bars.loc[T: T + pd.Timedelta(minutes=HORIZONS_MIN[-1])]
    out["max_up"] = float(post["high"].max() - ref)
    out["max_dn"] = float(ref - post["low"].min())
    # gap-fill bounds over the release bar + next bar
    two = bars.loc[T: T + pd.Timedelta(minutes=1)]
    adv_long = float(ref - two["low"].min())    # adverse for a LONG at ref
    adv_short = float(two["high"].max() - ref)  # adverse for a SHORT at ref
    for S in STOP_GRID_PTS:
        for d, adv in (("long", adv_long), ("short", adv_short)):
            stopped = adv >= S
            out[f"stop{S}_{d}_stopped"] = stopped
            out[f"stop{S}_{d}_loss_best"] = float(S) if stopped else None
            out[f"stop{S}_{d}_loss_worst"] = adv if stopped else None
    return out


def run_census(bars: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, ev in events.iterrows():
        m = measure_event(bars, ev["ts_release_et"])
        if m is None:
            m = dict(coverage_ok=False)
        rows.append({**ev.to_dict(), **m})
    df = pd.DataFrame(rows)
    df["sealed"] = df["date"] >= SEAL_FROM
    return df


# ---------------------------------------------------------------------------
# Aggregates — the census verdict tables (R first, then points)
# ---------------------------------------------------------------------------
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


Z_BUCKETS = [(-np.inf, -2, "z<-2"), (-2, -1, "-2..-1"), (-1, -0.25, "-1..-.25"),
             (-0.25, 0.25, "flat"), (0.25, 1, ".25..1"), (1, 2, "1..2"),
             (2, np.inf, "z>2")]


def continuation_table(census: pd.DataFrame, horizon: int = 30,
                       stop: int = DEFAULT_STOP_PTS,
                       respect_seal: bool = True) -> pd.DataFrame:
    """P(move at +H continues in the surprise-implied NQ direction),
    by family × surprise-z bucket. THE headline census output."""
    df = census[census["coverage_ok"] == True].copy()  # noqa: E712
    if respect_seal and not unsealed():
        df = df[~df["sealed"]]
    df = df.dropna(subset=["surprise_z", f"move_{horizon}m"])
    df["nq_expected"] = df["family"].map(SURPRISE_TO_NQ_SIGN) * np.sign(
        df["surprise_z"])
    df["hit"] = np.sign(df[f"move_{horizon}m"]) == df["nq_expected"]
    out = []
    for fam, g in df.groupby("family"):
        for lo, hi, lab in Z_BUCKETS:
            b = g[(g["surprise_z"] > lo) & (g["surprise_z"] <= hi)]
            if not len(b):
                continue
            k = int(b["hit"].sum())
            n = len(b)
            ci = wilson(k, n)
            med_pts = float(b[f"move_{horizon}m"].abs().median())
            out.append(dict(family=fam, z_bucket=lab, n=n,
                            cont_rate=round(k / n, 3),
                            ci_lo=round(ci[0], 3), ci_hi=round(ci[1], 3),
                            med_move_R=round(med_pts / stop, 2),
                            med_move_pts=round(med_pts, 1)))
    return pd.DataFrame(out)


def gapfill_table(census: pd.DataFrame, respect_seal: bool = True) -> pd.DataFrame:
    """Realized-loss bounds per family × stop — what a 1R stop ACTUALLY costs
    through the print. Bounds bracket the truth: best=stop price, worst=hole."""
    df = census[census["coverage_ok"] == True].copy()  # noqa: E712
    if respect_seal and not unsealed():
        df = df[~df["sealed"]]
    out = []
    for fam, g in df.groupby("family"):
        for S in STOP_GRID_PTS:
            for d in ("long", "short"):
                stopped = g[f"stop{S}_{d}_stopped"]
                n = int(stopped.notna().sum())
                if n == 0:
                    continue
                k = int(stopped.fillna(False).sum())
                worst = g.loc[stopped == True, f"stop{S}_{d}_loss_worst"]  # noqa: E712
                out.append(dict(
                    family=fam, stop_pts=S, side=d, n=n,
                    p_stopped=round(k / n, 3),
                    worst_med_R=round(float(worst.median()) / S, 2) if k else None,
                    worst_p90_R=round(float(worst.quantile(.9)) / S, 2) if k else None,
                    worst_med_pts=round(float(worst.median()), 1) if k else None))
    return pd.DataFrame(out)
