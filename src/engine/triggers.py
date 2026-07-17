"""Trigger detection — rejection blocks & displacements per entry TF (Spec 1, Step 6).

For each entry-TF candle (evaluated at its CLOSE, using only closed bars via
``indicators_asof``), we detect the two mechanical triggers of §3 against the confluence
cluster levels of §3, classify the pattern A/B/B2 (§4) with the HTF flag, and resolve
simultaneous multi-TF triggers by "highest TF wins" (§1 MTF arbitration).

Definitions (strategy-definition §3/§4; interpretive choices flagged in progress-tracker):
  * Rejection block (long): candle trades INTO the cluster (low ≤ top cluster level), CLOSES
    back above ALL cluster levels (close > top level), and leaves a lower wick through them.
    Short is the mirror. Tradeable zone = wick: body edge → wick extreme (§3).
  * Displacement (long): body closes UP through ≥2 cluster levels, body/range ≥ B_min, close
    in the top quartile of the candle range; optional range ≥ k·ATR(20). Short mirrors.
  * Pattern (§4): displacement → B (reclaim). Rejection block → A (reversal) if over-extended
    (candle reached NY VWAP ±2σ) or counter-trend; else B2 (continuation) when with-trend.
  * HTF flag: with_trend / counter_trend / range, from the 15m regime vs trade direction.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import BaseModel

from src.engine.indicators import IndicatorsConfig, indicators_asof, load_indicators_config
from src.engine.sessions import resample_ohlcv
from src.engine.snapshot import _gather_levels

_TF_RANK = {"1min": 1, "2min": 2, "3min": 3, "5min": 5, "15min": 15}


class Trigger(BaseModel):
    ts: str                     # ISO ET — candle close time
    tf: str
    direction: str              # long | short
    kind: str                   # rejection_block | displacement
    pattern: str                # A | B | B2
    htf_flag: str               # with_trend | counter_trend | range
    entry_ref: float            # BB MA / cluster reference for the limit (Step 7 uses per E1/E2/E3)
    stop_ref: float             # beyond the wick extreme / displacement origin (§5.4)
    wick_low: float
    wick_high: float
    cluster_center: float
    confluence_count: int
    close: float


def _level_groups(levels: list[tuple[str, float, str]], tol: float) -> list[list[tuple[str, float, str]]]:
    """Single-linkage groups within tol that span ≥2 distinct level types (§3)."""
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
    return [g for g in groups if len({t for _, _, t in g}) >= 2]


def _htf_flag(regime: str, direction: str) -> str:
    if regime == "range":
        return "range"
    trend_dir = "long" if regime == "uptrend" else "short"
    return "with_trend" if direction == trend_dir else "counter_trend"


def _over_extended(candle, ind: dict) -> bool:
    nv = ind.get("ny_vwap") or {}
    up2, lo2 = nv.get("upper_2"), nv.get("lower_2")
    return ((up2 is not None and candle["high"] >= up2)
            or (lo2 is not None and candle["low"] <= lo2))


def _test_candle(candle, groups, all_levels, disp, atr) -> dict | None:
    o, h, lo, c = candle["open"], candle["high"], candle["low"], candle["close"]
    rng = h - lo
    if rng <= 0:
        return None
    prices = [p for _, p, _ in all_levels]

    # --- displacement first (more specific): body through ≥2 levels, body/range ≥ B_min,
    #     close in the extreme quartile; optional range ≥ k·ATR(20) ---
    body = abs(c - o)
    if body / rng >= disp["body_range_min"] and not (disp["atr_floor_enabled"] and rng < disp["atr_floor_k"] * atr):
        up_through = [p for p in prices if o < p <= c]
        dn_through = [p for p in prices if c <= p < o]
        if c > o and len(up_through) >= 2 and (c - lo) / rng >= 0.75:
            return dict(direction="long", kind="displacement", entry_ref=min(up_through),
                        stop_ref=lo, wick_low=lo, wick_high=o, cluster=None, count=2)
        if c < o and len(dn_through) >= 2 and (h - c) / rng >= 0.75:
            return dict(direction="short", kind="displacement", entry_ref=max(dn_through),
                        stop_ref=h, wick_low=o, wick_high=h, cluster=None, count=2)

    # --- rejection block: wick INTO a cluster, body CLOSES back on the trade side of ALL its
    #     levels (body does not engulf through — that would be a displacement above) ---
    for g in groups:
        gp = [p for _, p, _ in g]
        top, bot = max(gp), min(gp)
        # long: lower wick into cluster, body above all levels, close above all
        if lo <= top and c > top and min(o, c) >= bot and min(o, c) - lo > 0:
            return dict(direction="long", kind="rejection_block", entry_ref=top,
                        stop_ref=lo, wick_low=lo, wick_high=min(o, c),
                        cluster=g, count=len({t for _, _, t in g}))
        # short: upper wick into cluster, body below all levels, close below all
        if h >= bot and c < bot and max(o, c) <= top and h - max(o, c) > 0:
            return dict(direction="short", kind="rejection_block", entry_ref=bot,
                        stop_ref=h, wick_low=max(o, c), wick_high=h,
                        cluster=g, count=len({t for _, _, t in g}))
    return None


def _load_disp(config_path="config/strategy.yaml"):
    import yaml
    d = yaml.safe_load(open(config_path))["triggers"]["displacement"]
    return {"body_range_min": d["body_range_min"], "atr_floor_enabled": d["atr_floor_enabled"],
            "atr_floor_k": d["atr_floor_k"], "atr_length": d["atr_length"]}


def _atr(frame: pd.DataFrame, length: int) -> pd.Series:
    h, lo, c = frame["high"], frame["low"], frame["close"]
    pc = c.shift()
    tr = pd.concat([h - lo, (h - pc).abs(), (lo - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(length).mean()


def detect_triggers(df_1m: pd.DataFrame, cfg: IndicatorsConfig | None = None,
                    start=None, end=None, tol: float | None = None) -> list[Trigger]:
    """Detect triggers across [start, end] (ET). Returns MTF-arbitrated Trigger list."""
    cfg = cfg or load_indicators_config()
    disp = _load_disp()
    if tol is None:
        import yaml
        tol = float(yaml.safe_load(open("config/strategy.yaml"))["cluster"]["tolerance_points"])

    frames = {tf: resample_ohlcv(df_1m, tf) for tf in cfg.entry_tfs}
    atrs = {tf: _atr(frames[tf], disp["atr_length"]) for tf in cfg.entry_tfs}
    raw: list[Trigger] = []
    for tf in cfg.entry_tfs:
        fr = frames[tf].reset_index(drop=True)
        mask = pd.Series(True, index=fr.index)
        if start is not None:
            mask &= fr["ts_event"] >= start
        if end is not None:
            mask &= fr["ts_event"] <= end
        for i in fr.index[mask]:
            t = fr["ts_event"].iloc[i]
            ind = indicators_asof(df_1m, t, cfg)
            levels = _gather_levels(ind, ind.get("daily_profile") or {})
            if len(levels) < 2:
                continue
            groups = _level_groups(levels, tol)
            res = _test_candle(fr.iloc[i], groups, levels, disp,
                               atrs[tf].iloc[i] if not np.isnan(atrs[tf].iloc[i]) else 0.0)
            if res is None:
                continue
            regime = _regime_from_ind(df_1m, t)
            htf = _htf_flag(regime, res["direction"])
            if res["kind"] == "displacement":
                pattern = "B"
            else:
                oe = _over_extended(fr.iloc[i], ind)
                pattern = "A" if (oe or htf == "counter_trend") else ("B2" if htf == "with_trend" else "A")
            g = res.get("cluster")
            center = round(sum(p for _, p, _ in g) / len(g), 4) if g else res["entry_ref"]
            raw.append(Trigger(ts=t.isoformat(), tf=tf, direction=res["direction"],
                               kind=res["kind"], pattern=pattern, htf_flag=htf,
                               entry_ref=round(float(res["entry_ref"]), 4),
                               stop_ref=round(float(res["stop_ref"]), 4),
                               wick_low=round(float(res["wick_low"]), 4),
                               wick_high=round(float(res["wick_high"]), 4),
                               cluster_center=round(float(center), 4),
                               confluence_count=res["count"], close=round(float(fr["close"].iloc[i]), 4)))
    return _mtf_arbitrate(raw)


def _regime_from_ind(df_1m, t) -> str:
    from src.engine.snapshot import _htf_regime
    from src.engine.indicators import _closed_1m
    return _htf_regime(_closed_1m(df_1m, t).reset_index(drop=True), t)


def _mtf_arbitrate(triggers: list[Trigger]) -> list[Trigger]:
    """On a shared close time, the highest TF wins (§1)."""
    best: dict[str, Trigger] = {}
    for tr in triggers:
        cur = best.get(tr.ts)
        if cur is None or _TF_RANK[tr.tf] > _TF_RANK[cur.tf]:
            best[tr.ts] = tr
    return sorted(best.values(), key=lambda x: x.ts)
