"""Indicators (Spec 1, Step 4): Bollinger Bands, anchored VWAPs, volume profile.

Pure functions over the validated 1-minute frame from ``data.py`` (and the close-labeled
resampled frames from ``sessions.resample_ohlcv``). Formulas match TradingView so the
Step-4 parity gate against Angus's reference charts is meaningful:

  * ``bollinger`` — BB(length, SMA of close, mult·σ), POPULATION stdev (ddof=0, matching
    TradingView ``ta.stdev``). Basis = the SMA ("BB MA", core cluster level §2/§3).
  * ``daily_vwap`` — anchored at the CME daily session open 18:00 ET (§2 CONFIRMED),
    grouped via ``_anchor_session_date`` (bars at/after the CONFIGURED anchor belong to
    the NEXT session — the anchor argument is honored, not silently pinned to 17:00).
  * ``ny_vwap`` — anchored 09:30 ET cash open (§2); DOES NOT EXIST pre-anchor: NaN for
    every bar before 09:30 and at/after the 17:00 ET session end (architecture invariant 1).
  * VWAP formula (TradingView): source = hlc3 = (high+low+close)/3 per bar;
    vwap = Σ(volume·src)/Σ(volume) from the anchor; band stdev is VOLUME-WEIGHTED:
    var = Σ(volume·src²)/Σ(volume) − vwap² (clipped at 0), bands = vwap ± k·√var.
    NOT a simple rolling stdev (spec-1 §3).
  * ``volume_profile`` — from 1m bars, each bar's volume spread UNIFORMLY across the
    0.25-pt price bins its [low, high] range touches (inclusive) — approximate vs tick
    data, documented as acceptable (spec-1 §3). POC / VAH / VAL / HVN / LVN.
  * ``profile_asof`` / ``weekly_profile_asof`` — developing profiles using ONLY bars
    fully closed at ``ts`` (no lookahead, structurally). Weekly is gated behind
    ``indicators.volume_profile.weekly_enabled`` (§2 TOURNAMENT).
  * ``indicators_asof`` — the parity-gate / future-snapshot entry point: one plain dict
    of every indicator value as of a timestamp, per entry TF.

Closed-bar semantics (spec-1 §3 "no lookahead, structurally"):
  * The 1m base frame is START-labeled (ts_event = interval open): a 1m bar stamped
    09:48 is still forming at 09:48 and closes at 09:49, so the last CLOSED 1m bar at
    time T is the last bar with ts_event <= T − 1min.
  * Resampled frames from ``sessions.resample_ohlcv`` are CLOSE-labeled: the last
    closed bar at T is the last bar with ts_event <= T. ``indicators_asof`` resamples
    from already-closed 1m bars and then drops any trailing partial bin, so lookahead
    is impossible by construction.

Flagged conventions (documented for Angus sign-off, per progress-tracker practice):
  * HVN/LVN = STRICT local maxima/minima of the bin-volume histogram (a bin whose
    volume is greater/less than BOTH immediate neighbours; edge bins excluded).
  * Value area: standard 70% algorithm — start at the POC bin, greedily add whichever
    adjacent bin (above vs below) holds more volume until >= value_area_pct of total
    volume is covered; ties go UP. POC tie -> lowest-price bin (numpy argmax).
"""
from __future__ import annotations

from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel

from src.engine.data import _MAINT_START
from src.engine.sessions import _parse_hhmm, resample_ohlcv

_ONE_MIN = pd.Timedelta(minutes=1)
_ONE_HOUR = pd.Timedelta(hours=1)  # wall-clock alignment unit for the resample-rule guard
_BIN_EPS = 1e-9        # float guard for price/bin_points division (prices are tick multiples)
_VA_EPS = 1e-9         # float guard for the >= value-area coverage comparison
_HLC3_SOURCE = "hlc3"  # §2 — the only implemented VWAP source (TradingView standard)


# ---------------------------------------------------------------- config

class IndicatorsConfig(BaseModel):
    """Everything the indicator layer reads from config/strategy.yaml (no magic numbers)."""

    bb_length: int                # indicators.bollinger.length (§2)
    bb_mult: float                # indicators.bollinger.stdev_mult (§2)
    entry_tfs: list[str]          # timeframes.entry (§1)
    ny_anchor: dtime              # indicators.ny_vwap.anchor (§2)
    ny_bands: list[int]           # indicators.ny_vwap.bands_sigma (§2)
    daily_anchor: dtime           # indicators.daily_vwap.anchor (§2 CONFIRMED, 18:00 ET)
    daily_bands: list[int]        # indicators.daily_vwap.bands_sigma (§2)
    vwap_source: str              # indicators.vwap.source (§2 — hlc3)
    vp_bin_points: float          # indicators.volume_profile.bin_points (spec-1 §3)
    vp_value_area_pct: float      # indicators.volume_profile.value_area_pct (§2)
    vp_weekly_enabled: bool       # indicators.volume_profile.weekly_enabled (§2 TOURNAMENT)


def load_indicators_config(config_path: Path = Path("config/strategy.yaml")) -> IndicatorsConfig:
    """Read the indicators (+ entry-TF) section of config/strategy.yaml into a typed model."""
    cfg = yaml.safe_load(open(config_path))
    ind = cfg["indicators"]
    return IndicatorsConfig(
        bb_length=ind["bollinger"]["length"],
        bb_mult=ind["bollinger"]["stdev_mult"],
        entry_tfs=cfg["timeframes"]["entry"],
        ny_anchor=_parse_hhmm(ind["ny_vwap"]["anchor"]),
        ny_bands=ind["ny_vwap"]["bands_sigma"],
        daily_anchor=_parse_hhmm(ind["daily_vwap"]["anchor"]),
        daily_bands=ind["daily_vwap"]["bands_sigma"],
        vwap_source=ind["vwap"]["source"],
        vp_bin_points=ind["volume_profile"]["bin_points"],
        vp_value_area_pct=ind["volume_profile"]["value_area_pct"],
        vp_weekly_enabled=ind["volume_profile"]["weekly_enabled"],
    )


# ---------------------------------------------------------------- session grouping / resample guard

def _anchor_session_date(ts: pd.Series, session_open: dtime) -> pd.Series:
    """CME session (trade) date per bar, honoring the CONFIGURED anchor.

    Bars stamped at/after ``session_open`` (wall-clock ET) belong to the NEXT calendar
    day's session; earlier bars belong to the current day's. This is the indicator-layer
    replacement for ``data._session_date``, which is pinned to the 17:00 maintenance
    boundary for gap reporting and ignores its ``session_open`` argument — here the
    18:00 anchor from config (``indicators.daily_vwap.anchor``, §2 CONFIRMED) really is
    the grouping boundary, so any bar in [17:00, 18:00) stays in the OLD session and the
    first bar at/after 18:00 starts the new one.
    """
    roll_next = ts.dt.time >= session_open
    return (ts.dt.normalize() + pd.to_timedelta(roll_next.astype(int), unit="D")).dt.date


def _check_resample_rule(rule: str) -> None:
    """Raise unless ``rule`` evenly divides one hour (wall-clock-safe resampling).

    ``sessions.resample_ohlcv`` bins from midnight of the first bar's day (pandas
    default ``origin='start_day'``). For rules dividing 60 minutes the bin boundaries
    are wall-clock-anchored and DST-invariant — identical to TradingView's
    session-anchored bins, because both the 18:00->midnight offset (360 min) and the
    DST shift (60 min) are whole hours. For longer rules (e.g. the '4h' in
    ``timeframes.range_extreme_tfs``) the bins would be midnight-anchored and shift by
    an hour at DST — NOT TradingView's 18:00-ET-anchored futures bars — so such rules
    are rejected here; the session-anchored HTF resampler is deferred to Step 5
    (flagged in config/strategy.yaml).
    """
    td = pd.Timedelta(rule)
    if td <= pd.Timedelta(0):
        raise ValueError(f"resample rule must be a positive interval, got {rule!r}")
    if _ONE_HOUR % td != pd.Timedelta(0):
        raise ValueError(
            f"resample rule {rule!r} does not divide 60 minutes: sessions.resample_ohlcv "
            f"bins would be midnight-anchored and DST-shifting, not CME-session-anchored "
            f"(TradingView parity). HTF rules like '4h' need the session-anchored "
            f"resampler deferred to Step 5.")


# ---------------------------------------------------------------- Bollinger Bands

def bollinger(df: pd.DataFrame, length: int, mult: float) -> pd.DataFrame:
    """BB(length, SMA of close, mult·σ) aligned to the input bars (any TF frame).

    Population stdev (ddof=0) to match TradingView ``ta.stdev`` (§2). Rows with fewer
    than ``length`` bars of history are NaN. Works on the 1m base frame or any
    resampled TF frame — the caller owns the closed-bar semantics of the frame.
    """
    if length < 1:
        raise ValueError(f"bollinger length must be >= 1, got {length}")
    if mult < 0:
        raise ValueError(f"bollinger stdev mult must be >= 0, got {mult}")
    close = df["close"].astype("float64")
    basis = close.rolling(length).mean()
    sd = close.rolling(length).std(ddof=0)  # POPULATION stdev — TradingView ta.stdev
    return pd.DataFrame({"ts_event": df["ts_event"], "basis": basis,
                         "upper": basis + mult * sd, "lower": basis - mult * sd},
                        index=df.index)


# ---------------------------------------------------------------- anchored VWAP

def _band_columns(bands: list[int]) -> list[str]:
    return ["vwap"] + [f"upper_{k}" for k in bands] + [f"lower_{k}" for k in bands]


def _anchored_vwap(df: pd.DataFrame, group: pd.Series, bands: list[int]) -> pd.DataFrame:
    """Running TradingView VWAP ± k·σ per anchor group (spec-1 §3 formula).

    src = hlc3; vwap = cum(vol·src)/cum(vol); band stdev is VOLUME-WEIGHTED:
    var = cum(vol·src²)/cum(vol) − vwap² (negatives from float error clipped to 0).
    """
    src = (df["high"] + df["low"] + df["close"]).astype("float64") / 3.0  # hlc3 (§2)
    vol = df["volume"].astype("float64")
    cum_v = vol.groupby(group).cumsum()
    cum_pv = (vol * src).groupby(group).cumsum()
    cum_pv2 = (vol * src * src).groupby(group).cumsum()
    vwap = cum_pv / cum_v
    var = (cum_pv2 / cum_v - vwap * vwap).clip(lower=0.0)
    sd = np.sqrt(var)
    out = pd.DataFrame({"ts_event": df["ts_event"], "vwap": vwap}, index=df.index)
    for k in bands:
        out[f"upper_{k}"] = vwap + k * sd
        out[f"lower_{k}"] = vwap - k * sd
    return out


def daily_vwap(df_1m: pd.DataFrame, bands: list[int] = [1, 2, 3],
               session_open: dtime = dtime(18, 0)) -> pd.DataFrame:
    """Daily VWAP ± k·σ anchored at the CME daily session open, 18:00 ET (§2 CONFIRMED).

    Grouping uses ``_anchor_session_date`` with ``session_open`` (the configured anchor
    is HONORED): the session containing a bar starts at the prior ``session_open``, so
    the VWAP resets on the first bar at/after 18:00 ET — bars in [17:00, 18:00) belong
    to the OLD session — and exists for EVERY bar of the session (it is the only VWAP
    pre-9:30, §3).
    """
    group = _anchor_session_date(df_1m["ts_event"], session_open)
    return _anchored_vwap(df_1m, group, bands)


def ny_vwap(df_1m: pd.DataFrame, bands: list[int] = [1, 2, 3],
            anchor: dtime = dtime(9, 30), session_end: dtime = _MAINT_START) -> pd.DataFrame:
    """NY VWAP ± k·σ anchored at the 09:30 ET cash open (§2). Runs on 1m bars.

    DOES NOT EXIST outside its window (architecture invariant 1): every column is NaN
    for bars stamped before 09:30 ET and at/after ``session_end`` (17:00 ET, the CME
    maintenance break — the same boundary ``data.py`` uses). Anchored per calendar day.
    """
    ts = df_1m["ts_event"]
    t = ts.dt.time
    valid = ((t >= anchor) & (t < session_end)).to_numpy()
    cols = _band_columns(bands)
    out = pd.DataFrame({"ts_event": ts}, index=df_1m.index)
    for c in cols[:]:
        out[c] = np.nan
    sub = df_1m.loc[valid]
    if not sub.empty:
        vv = _anchored_vwap(sub, sub["ts_event"].dt.date, bands)
        out.loc[valid, cols] = vv[cols].to_numpy()
    return out


# ---------------------------------------------------------------- volume profile

class VolumeProfile(BaseModel):
    """One developing/completed volume profile (POC/VAH/VAL/HVN/LVN, §2).

    HVN/LVN convention (FLAGGED for Angus): strict local maxima/minima of the
    bin-volume histogram — a bin whose volume is greater (HVN) / less (LVN) than BOTH
    immediate neighbours; the two edge bins are never HVN/LVN. Prices are bin CENTERS.
    """

    poc: float
    vah: float
    val: float
    hvn: list[float]
    lvn: list[float]
    total_volume: float
    bin_centers: list[float]
    bin_volumes: list[float]


def volume_profile(df_1m_slice: pd.DataFrame, bin_points: float,
                   value_area_pct: float) -> VolumeProfile:
    """Volume profile from 1m bars (spec-1 §3 — approximate vs tick data, documented).

    Each bar's volume is spread UNIFORMLY across the price bins its [low, high] range
    touches (inclusive). Bins are a fixed grid of width ``bin_points`` anchored at 0
    (bin i covers [i·w, (i+1)·w); reported prices are bin centers). The histogram is
    contiguous from the lowest to the highest touched bin (untouched bins hold 0).

    POC = center of the max-volume bin (tie -> lowest price). Value area = standard
    algorithm: start at POC, greedily add whichever adjacent bin (above vs below) has
    more volume (tie -> above) until covered volume >= value_area_pct% of total;
    VAH/VAL = centers of the top/bottom covered bins. Raises on empty input.
    """
    if df_1m_slice.empty:
        raise ValueError("volume_profile: empty bar slice — no profile exists")
    if bin_points <= 0:
        raise ValueError(f"volume_profile: bin_points must be > 0, got {bin_points}")
    if not 0 < value_area_pct <= 100:
        raise ValueError(f"volume_profile: value_area_pct must be in (0, 100], got {value_area_pct}")

    lo_i = np.floor(df_1m_slice["low"].to_numpy("float64") / bin_points + _BIN_EPS).astype(int)
    hi_i = np.floor(df_1m_slice["high"].to_numpy("float64") / bin_points + _BIN_EPS).astype(int)
    vol = df_1m_slice["volume"].to_numpy("float64")
    imin, imax = int(lo_i.min()), int(hi_i.max())
    hist = np.zeros(imax - imin + 1)
    for lo, hi, v in zip(lo_i, hi_i, vol):
        hist[lo - imin: hi - imin + 1] += v / (hi - lo + 1)  # uniform across touched bins
    centers = (np.arange(imin, imax + 1) + 0.5) * bin_points
    n = len(hist)
    total = float(hist.sum())

    poc_i = int(np.argmax(hist))  # tie -> lowest price
    lo_va = hi_va = poc_i
    covered = hist[poc_i]
    target = value_area_pct / 100.0 * total
    while covered + _VA_EPS < target and (lo_va > 0 or hi_va < n - 1):
        below = hist[lo_va - 1] if lo_va > 0 else -np.inf
        above = hist[hi_va + 1] if hi_va < n - 1 else -np.inf
        if above >= below:  # tie -> extend upward (documented convention)
            hi_va += 1
            covered += hist[hi_va]
        else:
            lo_va -= 1
            covered += hist[lo_va]

    hvn = [float(centers[i]) for i in range(1, n - 1)
           if hist[i] > hist[i - 1] and hist[i] > hist[i + 1]]
    lvn = [float(centers[i]) for i in range(1, n - 1)
           if hist[i] < hist[i - 1] and hist[i] < hist[i + 1]]
    return VolumeProfile(poc=float(centers[poc_i]), vah=float(centers[hi_va]),
                         val=float(centers[lo_va]), hvn=hvn, lvn=lvn, total_volume=total,
                         bin_centers=[float(c) for c in centers],
                         bin_volumes=[float(v) for v in hist])


def _closed_1m(df_1m: pd.DataFrame, ts: pd.Timestamp) -> pd.DataFrame:
    """1m bars fully CLOSED at ts. 1m bars are START-labeled: bar e closes at e+1min."""
    if ts.tzinfo is None:
        raise ValueError(f"ts must be tz-aware (America/New_York), got naive {ts}")
    return df_1m[df_1m["ts_event"] <= ts - _ONE_MIN]


def profile_asof(df_1m: pd.DataFrame, ts: pd.Timestamp, scope: str,
                 bin_points: float, value_area_pct: float,
                 session_open: dtime = dtime(18, 0), ny_anchor: dtime = dtime(9, 30),
                 ny_end: dtime = _MAINT_START) -> VolumeProfile | None:
    """DEVELOPING volume profile as of ``ts`` — only bars fully closed at ts (no lookahead).

    scope="daily": the current CME session (``session_open`` boundary — 18:00 ET — via
    ``_anchor_session_date``) containing ts. scope="ny": bars from 09:30 ET on ts's
    calendar day (NY box).
    Returns None when no closed bars exist yet in scope (profile does not exist yet —
    e.g. daily right at 18:00, NY pre-09:31).
    """
    closed = _closed_1m(df_1m, ts)
    bts = closed["ts_event"]
    if scope == "daily":
        sd = _anchor_session_date(bts, session_open)
        cur = _anchor_session_date(pd.Series([ts]), session_open).iloc[0]
        sl = closed[(sd == cur).to_numpy()]
    elif scope == "ny":
        t = bts.dt.time
        sl = closed[(bts.dt.date == ts.date()).to_numpy()
                    & (t >= ny_anchor).to_numpy() & (t < ny_end).to_numpy()]
    else:
        raise ValueError(f"profile_asof: unknown scope {scope!r} (use 'daily' or 'ny')")
    if sl.empty:
        return None
    return volume_profile(sl, bin_points, value_area_pct)


def weekly_profile_asof(df_1m: pd.DataFrame, ts: pd.Timestamp, bin_points: float,
                        value_area_pct: float, weekly_enabled: bool,
                        session_open: dtime = dtime(18, 0)) -> VolumeProfile | None:
    """Developing WEEKLY profile as of ts — gated (§2 TOURNAMENT variant).

    Raises unless ``indicators.volume_profile.weekly_enabled`` is passed True (the
    variant is off by default; calling it while disabled is a config error, and
    validation errors raise). Week = ISO week of the CME session date (the same
    convention as ``sessions.prior_week_levels``, flagged there).
    """
    if not weekly_enabled:
        raise ValueError("weekly volume profile is disabled "
                         "(indicators.volume_profile.weekly_enabled: false)")
    closed = _closed_1m(df_1m, ts)
    sd = _anchor_session_date(closed["ts_event"], session_open)
    cur = _anchor_session_date(pd.Series([ts]), session_open).iloc[0]
    iso = pd.DatetimeIndex(pd.to_datetime(sd.astype("string"))).isocalendar()
    wk = (iso["year"].astype(int) * 100 + iso["week"].astype(int)).to_numpy()
    cur_iso = pd.Timestamp(cur).isocalendar()
    sl = closed[wk == cur_iso.year * 100 + cur_iso.week]
    if sl.empty:
        return None
    return volume_profile(sl, bin_points, value_area_pct)


# ---------------------------------------------------------------- as-of entry point

def _none_if_nan(x: float) -> float | None:
    return None if pd.isna(x) else float(x)


def _vwap_row_dict(row: pd.Series, bands: list[int]) -> dict:
    d = {"mid": _none_if_nan(row["vwap"])}
    for k in bands:
        d[f"upper_{k}"] = _none_if_nan(row[f"upper_{k}"])
        d[f"lower_{k}"] = _none_if_nan(row[f"lower_{k}"])
    return d


def _vwap_none(bands: list[int]) -> dict:
    return {"mid": None, **{f"{side}_{k}": None for k in bands for side in ("upper", "lower")}}


def indicators_asof(df_1m: pd.DataFrame, ts: pd.Timestamp, cfg: IndicatorsConfig) -> dict:
    """Every indicator value as of ``ts``, from CLOSED bars only — parity/snapshot entry point.

    Per entry TF (1m base + close-labeled resamples): BB basis/upper/lower of the last
    CLOSED bar at ts, plus that bar's stamp (``bar_ts``). The resampled frames are built
    from already-closed 1m bars and any trailing partial bin (label > ts) is dropped, so
    lookahead is structurally impossible. Entry-TF rules must divide 60 minutes
    (``_check_resample_rule``) so bins stay wall-clock/CME-session aligned — '4h'-style
    HTF rules raise until the Step-5 session-anchored resampler exists.
    Plus: daily VWAP mid/±kσ, NY VWAP mid/±kσ
    (None pre-09:30 / outside the NY window), and the developing daily-profile
    POC/VAH/VAL. Missing values (insufficient history, pre-anchor) are None.
    """
    if cfg.vwap_source != _HLC3_SOURCE:
        raise ValueError(f"unsupported vwap source {cfg.vwap_source!r} (only {_HLC3_SOURCE!r})")
    closed = _closed_1m(df_1m, ts).reset_index(drop=True)

    out: dict = {"ts": ts, "tfs": {}}
    for tf in cfg.entry_tfs:
        _check_resample_rule(tf)  # reject midnight-anchored/DST-shifting bins (e.g. '4h')
        if pd.Timedelta(tf) == _ONE_MIN:
            frame = closed                                   # START-labeled base frame
        else:
            frame = resample_ohlcv(closed, tf)               # CLOSE-labeled by construction
            frame = frame[frame["ts_event"] <= ts]           # drop trailing partial bin
        if frame.empty:
            out["tfs"][tf] = {"bar_ts": None, "bb_basis": None, "bb_upper": None,
                              "bb_lower": None}
            continue
        bb = bollinger(frame, cfg.bb_length, cfg.bb_mult).iloc[-1]
        out["tfs"][tf] = {"bar_ts": frame["ts_event"].iloc[-1],
                          "bb_basis": _none_if_nan(bb["basis"]),
                          "bb_upper": _none_if_nan(bb["upper"]),
                          "bb_lower": _none_if_nan(bb["lower"])}

    # daily VWAP: last closed bar of the CURRENT CME session (18:00-ET boundary)
    cur_session = _anchor_session_date(pd.Series([ts]), cfg.daily_anchor).iloc[0]
    in_session = closed[(_anchor_session_date(closed["ts_event"], cfg.daily_anchor)
                         == cur_session).to_numpy()]
    if in_session.empty:
        out["daily_vwap"] = _vwap_none(cfg.daily_bands)
    else:
        dv = daily_vwap(in_session, cfg.daily_bands, cfg.daily_anchor)
        out["daily_vwap"] = _vwap_row_dict(dv.iloc[-1], cfg.daily_bands)

    # NY VWAP: None outside [09:30, 17:00) ET, and until the first NY bar has closed
    if not (cfg.ny_anchor <= ts.time() < _MAINT_START):
        out["ny_vwap"] = _vwap_none(cfg.ny_bands)
    else:
        nv = ny_vwap(closed, cfg.ny_bands, cfg.ny_anchor)
        today = nv[(closed["ts_event"].dt.date == ts.date()).to_numpy()].dropna(subset=["vwap"])
        out["ny_vwap"] = (_vwap_none(cfg.ny_bands) if today.empty
                          else _vwap_row_dict(today.iloc[-1], cfg.ny_bands))

    prof = profile_asof(df_1m, ts, "daily", cfg.vp_bin_points, cfg.vp_value_area_pct,
                        session_open=cfg.daily_anchor, ny_anchor=cfg.ny_anchor)
    out["daily_profile"] = (None if prof is None
                            else {"poc": prof.poc, "vah": prof.vah, "val": prof.val})
    return out
