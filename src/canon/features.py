"""Shared canon feature library (LIVE-STACK punch-list #2 — feature-library parity).

The SAME feature definitions must serve the backtest matrix builders
(`scripts/trade_matrix.py`, and the London depth path) AND the live ingestor, so a live
feature can never silently drift from the value the frozen thresholds were fit against.
These functions are the single source of truth for those definitions; both sides import
them rather than each carrying its own copy.

Copied expression-for-expression from `scripts/trade_matrix.py` (the definitions the
+$106k book was scored on). Three families so far:
  * depth      — path_eff, crosses, load_depth_day, depth_at
  * tape / CVD — tape_features (pm/op-so-far CVD+eff, d5/d15/d30, pathpos, fill_delta)
  * VWAP geom  — vwap_geometry (entry vs VWAP band, ON-range position, London sweep)

Validation: `tests/test_canon_features_parity.py` reproduces the stored
`output/trade_matrix.parquet` DEPTH columns to the decimal from the raw depth CSVs
(922/922 trades). `tests/test_canon_features_unit.py` covers tape/VWAP with hand-computed
synthetic frames; their backtest-parity check activates once `output/fp_minutes.parquet`
is restored (it is currently absent from this machine — see the ingestor build notes).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

NY = "America/New_York"


def path_eff(p: pd.Series) -> float:
    """Path efficiency of a price/VWAP series: |net move| / sum(|per-step move|).
    NaN until at least 5 non-null points (matches the backtest's min-length guard)."""
    p = p.dropna()
    if len(p) < 5:
        return np.nan
    return float(abs(p.iloc[-1] - p.iloc[0]) / max(p.diff().abs().sum(), 1e-9))


def crosses(p: pd.Series) -> float:
    """Number of mean-crossings of a series (chop proxy). NaN until >= 5 points."""
    p = p.dropna()
    if len(p) < 5:
        return np.nan
    s = np.sign(p - p.mean())
    return float((s.diff().abs() > 0).sum())


def load_depth_day(day: str) -> pd.DataFrame | None:
    """Load one NY session's long-form book snapshots (bid/ask levels per timestamp) from
    the reference depth archives, ts converted to America/New_York. None if absent."""
    for folder in ("depth_2025", "depth_2026", "depth_apr2026"):
        p = Path(f"data/reference/{folder}/nq_depth_{day}_ny.csv")
        if p.exists():
            d = pd.read_csv(p)
            d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY)
            return d
    return None


def depth_at(dep: pd.DataFrame, minute: pd.Timestamp, entry: float,
             direction: str) -> dict:
    """Order-book features as of the last snapshot at/before `minute`: thickness,
    imbalance, spread, direction-aware support/resist, nearest wall above/below
    (distance + size), and the 5-minute thickness delta. Empty dict if no snapshot.

    This is the definition the canon's depth signals (`WALLSZ`, `dep_wall_*`, thickness,
    imbalance) were validated on — the live ingestor MUST call this exact function."""
    sub = dep[dep.ts <= minute]
    if sub.empty:
        return {}
    b = sub[sub.ts == sub.ts.max()]
    bid, ask = b[b.side == "bid"], b[b.side == "ask"]
    if bid.empty or ask.empty:
        return {}
    tb, ta = bid["size"].sum(), ask["size"].sum()
    f = {"dep_thick": tb + ta, "dep_imb": (tb - ta) / max(tb + ta, 1),
         "dep_spread": ask.price.min() - bid.price.max(),
         "dep_support": tb if direction == "long" else ta,
         "dep_resist": ta if direction == "long" else tb}
    f["dep_sup_m_res"] = f["dep_support"] - f["dep_resist"]
    above, below = b[b.price > entry], b[b.price < entry]
    if len(above):
        w = above.loc[above["size"].idxmax()]
        f["dep_wall_above_d"] = float(w.price - entry)
        f["dep_wall_above_sz"] = float(w["size"])
    if len(below):
        w = below.loc[below["size"].idxmax()]
        f["dep_wall_below_d"] = float(entry - w.price)
        f["dep_wall_below_sz"] = float(w["size"])
    b5 = dep[dep.ts <= minute - pd.Timedelta(minutes=5)]
    if not b5.empty:
        f["dep_thick_d5m"] = f["dep_thick"] - b5[b5.ts == b5.ts.max()]["size"].sum()
    return f


# --------------------------------------------------------------------------- tape / CVD
# The minute tape ("footprint minutes") carries, per closed minute of a session day:
#   sday (session-date str), delta (signed volume = CVD increment), vol (total volume),
#   vwp (per-minute VWAP proxy for path features), hm (minute-of-day = hour*60+minute),
#   and the running cum / runmin / runmax of cumulative delta over the day (no lookahead).
# `tape_features` reads the slice STRICTLY BEFORE the fill (`upto`), so it can never see
# the fill minute or later — identical truncation to scripts/trade_matrix.py.

def tape_features(upto: pd.DataFrame, direction: str, fill_ts: pd.Timestamp,
                  day_med_vol: float) -> dict:
    """At-fill tape/CVD features from the minute tape truncated before the fill.

    `upto` = the day's minute rows with index < fill_ts (must carry columns delta, vol,
    vwp, hm, cum, runmin, runmax). `day_med_vol` = the session day's median minute volume
    (for `fill_vol_rel`). Copied expression-for-expression from trade_matrix.py so the
    live ingestor's numbers equal the backtest's."""
    f: dict = {}
    is_long = direction == "long"
    pm = upto[upto.hm >= 480]                     # 08:00+ ("pre-market so far")
    op = upto[upto.hm >= 570]                     # 09:30+ ("open so far")
    if len(pm):
        f["pm_sofar_cvd"] = pm.delta.sum()
        f["pm_sofar_abscvd"] = abs(f["pm_sofar_cvd"])
        f["pm_sofar_eff"] = f["pm_sofar_cvd"] / max(pm.vol.sum(), 1)
        f["pm_sofar_crosses"] = crosses(pm.vwp)
        f["pm_sofar_patheff"] = path_eff(pm.vwp)
        f["pm_sofar_conf"] = int((f["pm_sofar_cvd"] > 0) == is_long)
    if len(op):
        f["op_sofar_cvd"] = op.delta.sum()
        f["op_sofar_eff"] = f["op_sofar_cvd"] / max(op.vol.sum(), 1)
        f["op_sofar_conf"] = int((f["op_sofar_cvd"] > 0) == is_long)
    for k in (5, 15, 30):
        w = upto[upto.index >= fill_ts - pd.Timedelta(minutes=k)]
        f[f"d{k}"] = w.delta.sum() if len(w) else np.nan
        f[f"d{k}_conf"] = int((f[f"d{k}"] > 0) == is_long) if len(w) else np.nan
    if len(upto):
        last = upto.iloc[-1]
        rng = last.runmax - last.runmin
        f["pathpos"] = (last.cum - last.runmin) / rng if rng > 0 else np.nan
        f["fill_vol_rel"] = last.vol / max(day_med_vol, 1)
        f["fill_delta"] = last.delta
        f["fill_delta_conf"] = int((last.delta > 0) == is_long)
    return f


# --------------------------------------------------------------------------- VWAP geometry
# Bars carry per closed minute: mi (minute timestamp), hm, high, low, and daily-VWAP
# bands vw / up1 (lower_1 is symmetric). `vwap_geometry` reads only bars STRICTLY BEFORE
# the fill and measures entry position vs the VWAP band, vs the overnight range, and the
# London-sweep state — copied expression-for-expression from trade_matrix.py.

def vwap_geometry(pre: pd.DataFrame, entry: float, direction: str) -> dict:
    """At-fill geometry from the day's bars before the fill (`pre`, columns mi/hm/high/low/
    vw/up1). Returns {} if there is no prior bar or VWAP is not yet anchored (NaN)."""
    f: dict = {}
    if not len(pre):
        return f
    bar = pre.iloc[-1]
    if bar.vw != bar.vw:                          # VWAP NaN (pre-anchor) -> no geometry
        return f
    sgn = 1 if direction == "long" else -1
    bw = max(bar.up1 - bar.vw, 1e-9)              # one-sigma band width
    f["ent_vs_vwap_sd"] = (entry - bar.vw) / bw
    f["ent_vs_vwap_sd_dir"] = sgn * f["ent_vs_vwap_sd"]   # + = entering with-trend vs VWAP
    onr = pre[(pre.hm >= 1080) | (pre.hm < 480)]  # overnight: 18:00-24:00 or 00:00-08:00
    if len(onr):
        hi, lo = onr.high.max(), onr.low.min()
        f["ent_on_pos"] = (entry - lo) / max(hi - lo, 1e-9)
    lon = pre[(pre.hm >= 120) & (pre.hm < 480)]   # London 02:00-08:00 ET
    if len(lon):
        post = pre[pre.hm >= 480]
        if len(post):
            f["lon_hi_swept"] = int(post.high.max() > lon.high.max())
            f["lon_lo_swept"] = int(post.low.min() < lon.low.min())
        else:
            f["lon_hi_swept"] = 0
            f["lon_lo_swept"] = 0
    return f


# --------------------------------------------------------------------------- gold + London
# The families the golden-window and London scorers read that the three above do not cover.
# Same contract as everything else here: copied expression-for-expression from the scripts
# that produced the signed-off book, so live and backtest cannot drift.
#   badpa      (scripts/badpa_matrix.py)  -> netpath_30, bbw_state, churn_flow_30, trigdens_30
#   gold qual  (scripts/gold_quality.py)  -> bp5opp, lon_slope_d
#   London     (scripts/london_canon.py)  -> opp5   (+ ASIA/ON day features below)
# Every window here ends STRICTLY BEFORE the fill minute, so none of them can look ahead.


def opposed_last5(fp_upto: pd.DataFrame, direction: str, fill_ts: pd.Timestamp,
                  *, require_exactly_5: bool) -> float:
    """Count of the last 5 completed pre-fill 1-minute deltas that ran OPPOSED to the trade
    (a limit filling into counter-flow = absorption at the level).

    ONE primitive for two callers that slice the identical window but guard it differently —
    keeping them in one place is the point, since two copies of "last five minutes" is exactly
    how live drifts from backtest:
      * gold `bp5opp`  = int(count >= 3), guard len(seg) >= 5   (scripts/gold_quality.py)
      * London `opp5`  = the raw count,   guard len(seg) == 5   (scripts/london_canon.py)
    `require_exactly_5` selects the guard; NaN when the guard is not met (never 0 — an
    unmeasurable window must not read as "no opposition")."""
    f = pd.Timestamp(fill_ts).floor("min")
    seg = fp_upto.loc[f - pd.Timedelta(minutes=5): f - pd.Timedelta(minutes=1)]
    ok = (len(seg) == 5) if require_exactly_5 else (len(seg) >= 5)
    if not ok:
        return np.nan
    sgn = 1 if direction == "long" else -1
    return float((np.sign(seg.delta.values * sgn) < 0).sum())


def bp5opp(fp_upto: pd.DataFrame, direction: str, fill_ts: pd.Timestamp) -> float:
    """Gold `bp5opp`: 1 when >= 3 of the last 5 pre-fill minutes opposed the trade."""
    n = opposed_last5(fp_upto, direction, fill_ts, require_exactly_5=False)
    return np.nan if n != n else float(n >= 3)


def opp5(fp_upto: pd.DataFrame, direction: str, fill_ts: pd.Timestamp) -> float:
    """London `opp5`: the raw opposed count, requiring a complete 5-minute window."""
    return opposed_last5(fp_upto, direction, fill_ts, require_exactly_5=True)


def london_slope(fp_session: pd.DataFrame) -> float:
    """UNSIGNED OLS slope of London-session (02:00-05:00 ET) cumulative delta for one session
    day. London closes hours before any golden-window fill, so this is complete-session
    context, not lookahead. NaN under 60 minutes. The caller multiplies by the trade's
    direction sign to get `lon_slope_d` (scripts/gold_quality.py)."""
    hm = fp_session.index.hour * 60 + fp_session.index.minute
    lon = fp_session[(hm >= 120) & (hm < 300)]
    if len(lon) < 60:
        return np.nan
    y = lon.delta.cumsum().values
    x = np.arange(len(y), dtype=float)
    return float(np.polyfit(x, y, 1)[0])


def lon_slope_d(fp_session: pd.DataFrame, direction: str) -> float:
    """Direction-signed London slope — the `LONSLOPE` gold-quality input."""
    s = london_slope(fp_session)
    return np.nan if s != s else s * (1 if direction == "long" else -1)


def badpa_features(bars: pd.DataFrame, fp_upto: pd.DataFrame, entry: float,
                   fill_ts: pd.Timestamp, trigger_times=None) -> dict:
    """Bad-price-action features over windows ending one minute BEFORE the fill.

    `bars`  — the day's 1-minute bars indexed by timestamp (columns close, high, low, open,
              vw); must extend back at least 60 minutes before the fill AND to 02:00 of the
              fill's date for `bbw_state`'s day-median baseline.
    `fp_upto` — minute tape (delta, vol) covering at least the prior 30 minutes.
    `trigger_times` — engine trigger timestamps for the day (np.datetime64 array or None).

    Only the four columns the gold path actually scores on are ported here (X <- bbw_state,
    PAQ <- netpath_30, TRIG <- trigdens_30, and churn_flow_30 for the Layer-2e R1 cold-grind
    cut). badpa_matrix.py computes ~20 columns; the rest are research, not canon inputs, and
    porting unused definitions would be surface area that can silently drift."""
    f: dict = {}
    fill = pd.Timestamp(fill_ts)
    w60 = bars.loc[fill - pd.Timedelta(minutes=60): fill - pd.Timedelta(minutes=1)]
    w30 = w60.loc[fill - pd.Timedelta(minutes=30):]
    if len(w30) >= 15:
        c = w30.close
        f["netpath_30"] = abs(c.iloc[-1] - c.iloc[0]) / max(c.diff().abs().sum(), 1e-9)
        std20 = c.rolling(20).std().iloc[-1]
        day_c = bars.loc[fill.normalize() + pd.Timedelta(hours=2):
                         fill - pd.Timedelta(minutes=1)].close
        if len(day_c) > 40:
            f["bbw_state"] = float(std20 / max(day_c.rolling(20).std().median(), 1e-9))
        else:
            f["bbw_state"] = np.nan
    g = fp_upto.loc[fill - pd.Timedelta(minutes=30): fill - pd.Timedelta(minutes=1)]
    if len(g) >= 10:
        f["churn_flow_30"] = abs(g.delta.sum()) / max(g.vol.sum(), 1)   # low = two-sided grind
    if trigger_times is not None:
        arr = np.asarray(trigger_times)
        f["trigdens_30"] = int(((arr >= (fill - pd.Timedelta(minutes=30)).to_datetime64())
                                & (arr < fill.to_datetime64())).sum())
    return f


# NOTE — `on_extreme_age` is TWO DIFFERENT FEATURES sharing one column name. Both are
# below, deliberately named apart, because silently picking either one would put a wrong
# number into a live gate:
#   * gold (AGE)  — scripts/dayflow_v2.py: a per-DAY value over the COMPLETED 18:00-08:00
#                   overnight tape, measured in index positions back from the session end.
#   * London      — scripts/london_matrix.py: a per-TRADE value, wall-clock minutes from the
#                   fill back to the extreme, over session-so-far BARS (not the tape), with
#                   the extreme chosen by which side the entry sits nearer.
# They disagree numerically on the same day (verified: 60/60 days differ), so a live
# assembler must call the one its scorer was fit against.

def on_extreme_age_day(fp_on: pd.DataFrame) -> float:
    """GOLD's AGE input (scripts/dayflow_v2.py `extreme_age`). `fp_on` = the COMPLETED
    overnight tape for one session day (hm >= 1080 or hm < 480), needing `vwp`. Returns
    index-positions since the more recent of the ON high/low; NaN under 30 minutes. ON
    closes at 08:00, before any NY fill — complete-session context, not lookahead."""
    p = fp_on.vwp.dropna() if "vwp" in fp_on else pd.Series(dtype=float)
    if len(p) < 30:
        return np.nan
    n = len(p)
    return float(min(n - 1 - int(np.argmax(p.values)), n - 1 - int(np.argmin(p.values))))


def on_extreme_age_trade(bars_session: pd.DataFrame, entry: float,
                         fill_ts: pd.Timestamp) -> float:
    """LONDON's on_extreme_age (scripts/london_matrix.py). Wall-clock MINUTES from the fill
    back to the session-so-far extreme, where the extreme is the HIGH when the entry sits
    nearer the high side and the LOW otherwise. `bars_session` = 18:00-anchored bars up to
    fill-1min (needs high/low); NaN under 90 bars."""
    if len(bars_session) < 90:
        return np.nan
    hi, lo = bars_session.high.max(), bars_session.low.min()
    ext_t = (bars_session.high.idxmax() if (entry - lo) > (hi - entry)
             else bars_session.low.idxmin())
    return float((pd.Timestamp(fill_ts) - ext_t).total_seconds() / 60)


def london_session_features(fp_session: pd.DataFrame, bars_session: pd.DataFrame,
                            entry: float, sess_start: pd.Timestamp) -> dict:
    """London's ASIA + ROOM inputs, from the session slices truncated BEFORE the fill.

    `fp_session`   — minute tape from `sess_start` (18:00 prior evening) to fill-1min.
    `bars_session` — 1m bars over the same span (needs high/low).
    `sess_start`   — the 18:00 ET session anchor.

    Windows are the ones scripts/london_matrix.py uses, NOT the ON-session windows used
    elsewhere in this module — Asia here is the FIRST 8 HOURS from the 18:00 anchor
    (18:00-02:00 ET), guarded at >60 minutes, and the range is measured over everything
    seen so far this session rather than a fixed 18:00-08:00 block. They are deliberately
    different and must not be unified (a London fill happens mid-session, so its "so far"
    windows cannot be the completed-ON windows gold uses)."""
    f: dict = {}
    if len(fp_session):
        asia = fp_session.loc[: sess_start + pd.Timedelta(hours=8)]     # 18:00-02:00 ET
        f["cvd_ASIA"] = float(asia.delta.sum()) if len(asia) > 60 else np.nan
    if len(bars_session):
        hi, lo = bars_session.high.max(), bars_session.low.min()
        f["on_range"] = float(hi - lo)
        f["ent_on_pos"] = float((entry - lo) / max(hi - lo, 1e-9))
    return f
