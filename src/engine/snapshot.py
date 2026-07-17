"""Snapshot builder — one validated picture per timestamp (Spec 1, Step 5).

`build_snapshot(df_1m, ts, ...)` composes the Step-4 indicators with cluster detection,
the HTF regime flag, session context, data levels, and target-menu distances into a single
pydantic `Snapshot` (the Engine→Desk contract; JSON via `.model_dump_json()`). Everything is
computed as of the CLOSE of the named bar using only closed bars — lookahead is structurally
impossible because it all flows through `indicators_asof` / `_closed_1m` semantics.

Documented conventions (flagged in progress-tracker for Angus):
  * Confluence cluster (§3): candidate levels are {BB basis per entry TF (type "bb"),
    daily VWAP mid/±1/±2/±3σ + (post-09:30 only) NY VWAP mid/±1σ (type "vwap"), daily POC
    (type "poc")}. Single-linkage grouping within `cluster.tolerance_points`; a cluster needs
    ≥2 DISTINCT types (per §3 "confluence count = distinct level types"). Pre-09:30 the VWAP
    family is daily-only (NY VWAP is None upstream), so the pre-market rule is automatic.
  * HTF regime (§4 flag): on 15m closed bars, fractal swings with lookback k=2 (a swing high
    is a bar strictly higher than the 2 bars each side; swing low symmetric). Using the last
    two confirmed swing highs (SH) and lows (SL): uptrend if SH↑ and SL↑; downtrend if SH↓ and
    SL↓; else range; "unknown" if <2 of either. This exact rule is the chosen definition.
  * Target menu (§6): daily VWAP mid/±1σ/±2σ, NY VWAP mid (post-09:30), POC/VAH/VAL,
    prior-day H/L, prior-week H/L, current-session Asia/London/NY extremes, and recent data
    extremes. HTF 1h/4h range extremes are deferred with the session-anchored HTF resampler
    (flagged Step-4); pullback-origin is trade-specific (Step 6/7), not a snapshot level.
"""
from __future__ import annotations

from datetime import time as dtime

import pandas as pd
from pydantic import BaseModel

from src.engine.data import _session_date
from src.engine.indicators import (
    IndicatorsConfig,
    _closed_1m,
    indicators_asof,
    load_indicators_config,
)
from src.engine.sessions import (
    SessionBox,
    data_levels,
    load_data_level_window,
    load_news_calendar,
    load_session_boxes,
    prior_day_levels,
    prior_week_levels,
    resample_ohlcv,
    session_of,
)

_HTF_TF = "15min"
_SWING_K = 2  # fractal lookback each side


# ---------------------------------------------------------------- schema

class Level(BaseModel):
    name: str
    price: float
    type: str                 # "bb" | "vwap" | "poc" | "structural" | "data"
    distance: float           # price - ref_price (signed; + is above current price)


class Cluster(BaseModel):
    center: float
    confluence_count: int     # distinct level TYPES in the cluster (§3)
    types: list[str]
    members: list[str]        # level names


class Snapshot(BaseModel):
    ts: str                                   # ISO ET
    ref_price: float | None                   # last closed 1m close as of ts
    session: str                              # asia|london|ny|"" (outside boxes)
    htf_regime: str                           # uptrend|downtrend|range|unknown
    indicators: dict                          # indicators_asof output (timestamps -> ISO)
    session_high: float | None
    session_low: float | None
    prior_day_high: float | None
    prior_day_low: float | None
    prior_week_high: float | None
    prior_week_low: float | None
    clusters: list[Cluster]
    data_levels: list[dict]
    target_menu: list[Level]


# ---------------------------------------------------------------- helpers

def _isoify(obj):
    """Recursively convert pandas/py timestamps to ISO strings for JSON-stable output."""
    if isinstance(obj, dict):
        return {k: _isoify(v) for k, v in obj.items()}
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return obj


def _htf_regime(closed_1m: pd.DataFrame, ts: pd.Timestamp) -> str:
    bars = resample_ohlcv(closed_1m, _HTF_TF)
    bars = bars[bars["ts_event"] <= ts].reset_index(drop=True)
    k = _SWING_K
    if len(bars) < 2 * k + 1:
        return "unknown"
    hi, lo = bars["high"].to_numpy(), bars["low"].to_numpy()
    sh, sl = [], []
    for i in range(k, len(bars) - k):
        if hi[i] == max(hi[i - k:i + k + 1]) and hi[i] > max(hi[i - k:i]) and hi[i] > max(hi[i + 1:i + k + 1]):
            sh.append(hi[i])
        if lo[i] == min(lo[i - k:i + k + 1]) and lo[i] < min(lo[i - k:i]) and lo[i] < min(lo[i + 1:i + k + 1]):
            sl.append(lo[i])
    if len(sh) < 2 or len(sl) < 2:
        return "unknown"
    up = sh[-1] > sh[-2] and sl[-1] > sl[-2]
    down = sh[-1] < sh[-2] and sl[-1] < sl[-2]
    return "uptrend" if up else "downtrend" if down else "range"


def _gather_levels(ind: dict, poc_vah_val: dict) -> list[tuple[str, float, str]]:
    """Candidate cluster levels: (name, price, type). NY VWAP already None pre-09:30 upstream."""
    out: list[tuple[str, float, str]] = []
    for tf, d in ind["tfs"].items():
        if d.get("bb_basis") is not None:
            out.append((f"bb_basis_{tf}", d["bb_basis"], "bb"))
    for fam, tag in (("daily_vwap", "dvwap"), ("ny_vwap", "nyvwap")):
        v = ind.get(fam) or {}
        if v.get("mid") is not None:
            out.append((f"{tag}_mid", v["mid"], "vwap"))
        for key, val in v.items():
            if key != "mid" and val is not None:
                out.append((f"{tag}_{key}", val, "vwap"))
    if poc_vah_val.get("poc") is not None:
        out.append(("poc", poc_vah_val["poc"], "poc"))
    return out


def _clusters(levels: list[tuple[str, float, str]], tol: float) -> list[Cluster]:
    """Single-linkage groups within `tol`; keep groups spanning >=2 distinct types (§3)."""
    if not levels:
        return []
    ordered = sorted(levels, key=lambda x: x[1])
    groups, cur = [], [ordered[0]]
    for lv in ordered[1:]:
        if lv[1] - cur[-1][1] <= tol:
            cur.append(lv)
        else:
            groups.append(cur)
            cur = [lv]
    groups.append(cur)
    clusters = []
    for g in groups:
        types = sorted({t for _, _, t in g})
        if len(types) >= 2:
            clusters.append(Cluster(center=round(sum(p for _, p, _ in g) / len(g), 4),
                                    confluence_count=len(types), types=types,
                                    members=[n for n, _, _ in g]))
    return clusters


def _session_extremes(cur_session_bars: pd.DataFrame,
                      boxes: list[SessionBox]) -> dict[str, tuple[float, float]]:
    """High/low per session box within the current CME session, as of ts."""
    if cur_session_bars.empty:
        return {}
    box = session_of(cur_session_bars["ts_event"], boxes)
    out = {}
    seen = set()
    for b in boxes:                       # iterate in box order (deterministic, not a set)
        if b.name in seen:
            continue
        seen.add(b.name)
        sel = cur_session_bars[(box == b.name).to_numpy()]
        if not sel.empty:
            out[b.name] = (float(sel["high"].max()), float(sel["low"].min()))
    return out


# ---------------------------------------------------------------- builder

def build_snapshot(df_1m: pd.DataFrame, ts: pd.Timestamp,
                   ind_cfg: IndicatorsConfig | None = None,
                   boxes: list[SessionBox] | None = None,
                   calendar: pd.DataFrame | None = None,
                   cluster_tol: float | None = None,
                   data_window_min: int | None = None) -> Snapshot:
    ind_cfg = ind_cfg or load_indicators_config()
    boxes = boxes if boxes is not None else load_session_boxes()
    if cluster_tol is None:
        import yaml
        cluster_tol = float(yaml.safe_load(open("config/strategy.yaml"))["cluster"]["tolerance_points"])
    data_window_min = data_window_min if data_window_min is not None else load_data_level_window()

    ind = indicators_asof(df_1m, ts, ind_cfg)
    closed = _closed_1m(df_1m, ts).reset_index(drop=True)
    ref_price = float(closed["close"].iloc[-1]) if not closed.empty else None

    # session context
    sess = session_of(pd.Series([ts]), boxes).iloc[0]
    cur_sd = _session_date(pd.Series([ts]), dtime(18, 0)).iloc[0]
    cur_bars = closed[(_session_date(closed["ts_event"], dtime(18, 0)) == cur_sd).to_numpy()]
    sess_hi = float(cur_bars["high"].max()) if not cur_bars.empty else None
    sess_lo = float(cur_bars["low"].min()) if not cur_bars.empty else None
    pdl = prior_day_levels(closed).iloc[-1] if not closed.empty else None
    pwl = prior_week_levels(closed).iloc[-1] if not closed.empty else None

    # developing daily profile VAH/VAL (indicators_asof gives poc/vah/val)
    prof = ind.get("daily_profile") or {}

    # clusters (§3)
    clusters = _clusters(_gather_levels(ind, prof), cluster_tol)

    # data levels near recent releases, as of ts
    if calendar is None:
        try:
            calendar = load_news_calendar()
        except Exception:
            calendar = pd.DataFrame(columns=["datetime_ET", "event", "impact"])
    past_cal = calendar[calendar["datetime_ET"] <= ts]
    dl = data_levels(closed, past_cal, data_window_min)
    dl_records = [{"event": r["event"], "impact": r["impact"],
                   "data_high": r["data_high"], "data_low": r["data_low"],
                   "event_time": r["event_time"].isoformat()} for _, r in dl.iterrows()]

    # target menu (§6) with signed distances
    def lvl(name, price, typ):
        if price is None:
            return None
        return Level(name=name, price=float(price), type=typ,
                     distance=round(float(price) - ref_price, 4) if ref_price is not None else 0.0)

    menu: list[Level] = []
    dv = ind.get("daily_vwap") or {}
    for key in ("mid", "upper_1", "lower_1", "upper_2", "lower_2"):
        menu.append(lvl(f"daily_vwap_{key}", dv.get(key), "vwap"))
    if (ind.get("ny_vwap") or {}).get("mid") is not None:
        menu.append(lvl("ny_vwap_mid", ind["ny_vwap"]["mid"], "vwap"))
    for key in ("poc", "vah", "val"):
        menu.append(lvl(f"profile_{key}", prof.get(key), "poc" if key == "poc" else "structural"))
    if pdl is not None:
        menu.append(lvl("prior_day_high", pdl["prior_day_high"], "structural"))
        menu.append(lvl("prior_day_low", pdl["prior_day_low"], "structural"))
    if pwl is not None:
        menu.append(lvl("prior_week_high", pwl["prior_week_high"], "structural"))
        menu.append(lvl("prior_week_low", pwl["prior_week_low"], "structural"))
    for name, (hi, lo) in _session_extremes(cur_bars, boxes).items():
        menu.append(lvl(f"{name}_session_high", hi, "structural"))
        menu.append(lvl(f"{name}_session_low", lo, "structural"))
    for r in dl_records:
        menu.append(lvl(f"data_high_{r['event'][:16]}", r["data_high"], "data"))
        menu.append(lvl(f"data_low_{r['event'][:16]}", r["data_low"], "data"))
    menu = [m for m in menu if m is not None]

    return Snapshot(
        ts=ts.isoformat(), ref_price=ref_price, session=sess,
        htf_regime=_htf_regime(closed, ts),
        indicators=_isoify(ind),
        session_high=sess_hi, session_low=sess_lo,
        prior_day_high=None if pdl is None or pd.isna(pdl["prior_day_high"]) else float(pdl["prior_day_high"]),
        prior_day_low=None if pdl is None or pd.isna(pdl["prior_day_low"]) else float(pdl["prior_day_low"]),
        prior_week_high=None if pwl is None or pd.isna(pwl["prior_week_high"]) else float(pwl["prior_week_high"]),
        prior_week_low=None if pwl is None or pd.isna(pwl["prior_week_low"]) else float(pwl["prior_week_low"]),
        clusters=clusters, data_levels=dl_records, target_menu=menu,
    )
