"""Trigger detection — rejection blocks & displacements per entry TF (Spec 1, Step 6).

For each entry-TF candle (evaluated at its CLOSE, using only closed bars via
``indicators_asof``), we detect the two mechanical triggers of §3 against the confluence
cluster levels of §3, classify the pattern A/B/B2 (§4) with the HTF flag, and resolve
simultaneous multi-TF triggers by "highest TF wins" (§1 MTF arbitration).

Definitions (strategy-definition §3/§4; interpretive choices flagged in progress-tracker):
  * Rejection block (long): candle trades INTO the cluster (low ≤ top cluster level), CLOSES
    back above ALL cluster levels (close > top level), and leaves a lower wick through them.
    Short is the mirror. Tradeable zone = wick: body edge → wick extreme (§3).
  * Displacement (long): body closes UP through ≥ ``min_levels_through`` levels OF ONE
    DETECTED CLUSTER GROUP (§3 "body closes through ≥2 CLUSTER levels" — candidate levels
    that belong to no cluster group do not count; interpretation flagged for Angus), with
    body/range ≥ B_min and close in the extreme quartile of the range
    (``close_extreme_quartile``); optional range ≥ k·ATR(20). Short mirrors. When the ATR
    floor is ENABLED and ATR has insufficient history (NaN), the floor is unevaluable and
    the displacement is REJECTED (conservative) — never silently bypassed.
  * confluence_count = distinct level TYPES of the crossed cluster group (§3 "confluence
    count = distinct level types"), same rule as rejection blocks — never a constant.
  * entry_ref: rejection block → near cluster edge; displacement → the penetrated cluster
    level NEAREST the candle's close (§5 E3). E1's BB MA and E2's wick-50% are derived by
    Step 7 from indicators / the wick fields — entry_ref is the E3 reference only.
  * Pattern (§4, ANGUS 22-Jul taxonomy — NOT candle shape). Universal entry is a limit on the
    RETEST of the closest structural level (POC / daily-VWAP dev band / BB MA). The tag is the
    CONTEXT of the close-through, not rejection-vs-displacement:
      A  = REVERSAL: a close-through that reverses a recent ±2 DAILY-VWAP over-extension
           (counter-trend). See the ±2-touch logic in the classifier below.
      B  = CONTINUATION: a with-trend close-through/displacement off a stacked confluence.
      B2 = REJECTION / FADE: wick into a level, close back, fade off it (either HTF direction).
    Order blocks are NOT part of the strategy. See docs/STRATEGY-SETUP-TAXONOMY.md.
  * HTF flag: with_trend / counter_trend / range, from the 15m regime vs trade direction.
  * No forming bars: resampled frames drop any trailing bin not fully covered by closed 1m
    data, so prefix replays can never evaluate a partial candle as closed (spec-1 §3).

Labeling convention (bar stamps): engine bars are CLOSE-labeled; TradingView (and Angus's
hand log) label candles by OPEN time. A hand-logged TF-minute candle at t is the engine
bar stamped t+TF (e.g. Feb 11 "09:48 3M" = engine 3min bar 09:51). Any exact-candle
comparison against the hand log (Step-8 matcher, spot-checks) must apply this +TF shift.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from pydantic import BaseModel, field_validator

from src.engine.indicators import IndicatorsConfig, indicators_asof, load_indicators_config
from src.engine.sessions import resample_ohlcv
from src.engine.snapshot import _gather_levels, _include_ote, _level_groups, _ote_levels

__all__ = ["Trigger", "detect_triggers", "_level_groups"]  # _level_groups re-exported (shared rule)

_TF_RANK = {"1min": 1, "2min": 2, "3min": 3, "5min": 5, "15min": 15}
_ONE_MIN = pd.Timedelta(minutes=1)
_VWAP_TOUCH_TOL = 0.5   # ANGUS pass-6: 2-tick tolerance for "the wick reached the VWAP band"
_OB_LOOKBACK = 3        # ANGUS pass-22: bars scanned back for the opposite-colored OB partner
_EXT_LOOKBACK = 10      # ANGUS 22-Jul: entry-TF bars scanned back for the ±2 over-extension that
                        # a displacement must reverse to be tagged A (else B / continuation)


def _order_block(fr: pd.DataFrame, i: int, direction: str) -> tuple[float | None, float | None]:
    """ANGUS pass-22: two-candle order block = the most recent OPPOSITE-colored candle
    before the trigger candle ("a bearish candle and a bullish candle. Mark the range of
    those two, and enter at the 50%"). Long trigger -> partner is bearish; short -> bullish.
    Scan back <= _OB_LOOKBACK bars (dojis/same-color noise between are skipped).
    Returns (mid, stop_extreme): entry at the combined range's 50%, stop beyond the BLOCK
    (combined low for longs / high for shorts)."""
    for j in range(i - 1, max(i - 1 - _OB_LOOKBACK, -1), -1):
        o, c = float(fr["open"].iloc[j]), float(fr["close"].iloc[j])
        if (c < o) if direction == "long" else (c > o):
            hi = max(float(fr["high"].iloc[j]), float(fr["high"].iloc[i]))
            lo = min(float(fr["low"].iloc[j]), float(fr["low"].iloc[i]))
            return round((hi + lo) / 2, 4), round(lo if direction == "long" else hi, 4)
    return None, None


class Trigger(BaseModel):
    ts: str                     # ISO ET — candle close time
    tf: str
    direction: str              # long | short
    kind: str                   # rejection_block | displacement
    pattern: str                # A | B | B2 | unclassified (range regime, no over-extension — §4 silent)
    htf_flag: str               # with_trend | counter_trend | range
    entry_ref: float            # E3 reference: penetrated cluster level nearest the close (§5)
    stop_ref: float             # beyond the wick extreme / displacement origin (§5.4)
    wick_low: float
    wick_high: float
    cluster_center: float
    confluence_count: int
    cluster_types: list[str] = []   # distinct level types in the crossed cluster: bb | vwap | poc
                                    # (§9 ANGUS v1.1 sizing ladder: FULL=BB+VWAP+POC, HALF=2 incl
                                    #  BB+VWAP, NO TRADE without both BB+VWAP)
    vwap_touched: bool = False      # ANGUS pass-6: did the candle's range actually REACH a VWAP
                                    # band? (his "it actually rejected VWAP" standard). Distinct
                                    # from cluster_types having 'vwap' (that's level-proximity, not
                                    # a price touch — Brake's Feb-24 find). Gate: filters.require_vwap_touch.
    ob_mid: float | None = None     # ANGUS pass-22 ORDER BLOCK: midpoint of the two-candle block
                                    # (most recent OPPOSITE-colored candle before the trigger +
                                    # the trigger candle; combined high/low range, enter at 50%).
                                    # None when no opposite candle sits within the lookback —
                                    # E5 then falls back to E3's reclaim level in the engine.
    ob_stop: float | None = None    # the block's stop-side extreme (combined LOW for longs /
                                    # HIGH for shorts) — E5's structural stop sits beyond the
                                    # BLOCK, not just the trigger wick (can be wider than stop_ref)
    close: float
    cluster_members: str = ""       # ANGUS 30-Jul (L0 rebuild): the crossed cluster's MEMBER
                                    # levels as JSON [[name, price, type], ...]. cluster_center
                                    # is their MEAN, which destroys exactly the distinction his
                                    # structural-cancel rule needs ("limit at bb MA stacked on
                                    # vwap -1" — the components sit at DIFFERENT prices, and the
                                    # far one is what price tests first).
    level_stack: str = ""           # the FULL level stack at trigger time, JSON same shape,
                                    # sorted by price. Feeds "what did price touch while away
                                    # from the limit, and did it fail there" — the structural
                                    # cancel/confirm rule (vwap mid rejection etc.). Both fields
                                    # default "" so cached pre-L0 CSVs round-trip unchanged.

    @field_validator("ob_mid", "ob_stop", mode="before")
    @classmethod
    def _csv_nan_is_none(cls, v):
        """CSV cache round-trip: None -> NaN on read_csv; coerce back so `is not None`
        checks in the engine stay truthful for cached triggers."""
        return None if isinstance(v, float) and np.isnan(v) else v


def _htf_flag(regime: str, direction: str) -> str:
    # E-2 FIX (Angus ruling, 20 Jul): an UNKNOWN regime is NEUTRAL, not a silent downtrend.
    # The old `else "short"` defaulted unknown-regime shorts to "with_trend" (lenient) and longs
    # to "counter_trend" — manufacturing phantom "with-trend" shorts that bled (18% win) on a
    # long-biased instrument. Unknown now resolves to "range" (neutral); only genuine
    # uptrend/downtrend set a directional trend.
    if regime in ("range", "unknown"):
        return "range"
    trend_dir = "long" if regime == "uptrend" else "short"   # only uptrend/downtrend reach here
    return "with_trend" if direction == trend_dir else "counter_trend"


def _over_extended(candle, ind: dict, direction: str, sigma: int) -> bool:
    """§3/§4: over-extension relevant to a rejection is IN the rejected direction —
    short rejects an extension ABOVE (high ≥ NY VWAP +kσ), long an extension BELOW."""
    nv = ind.get("ny_vwap") or {}
    if direction == "short":
        up = nv.get(f"upper_{sigma}")
        return up is not None and candle["high"] >= up
    lo_b = nv.get(f"lower_{sigma}")
    return lo_b is not None and candle["low"] <= lo_b


def _test_candle(candle, groups, disp, atr) -> dict | None:
    o, h, lo, c = candle["open"], candle["high"], candle["low"], candle["close"]
    rng = h - lo
    if rng <= 0:
        return None

    # --- displacement first (more specific): body through ≥ min_levels_through levels of ONE
    #     cluster group (§3), body/range ≥ B_min, close in the extreme quartile; optional
    #     range ≥ k·ATR(20). ATR floor enabled + NaN ATR → unevaluable → reject (conservative).
    body = abs(c - o)
    atr_ok = True
    if disp["atr_floor_enabled"]:
        atr_ok = not np.isnan(atr) and rng >= disp["atr_floor_k"] * atr
    n_min = disp["min_levels_through"]
    q = 1.0 - disp["close_extreme_quartile"]      # e.g. 0.25 → close in top/bottom 25%
    if body / rng >= disp["body_range_min"] and atr_ok:
        if c > o and (c - lo) / rng >= q:
            cands = [(g, [p for _, p, _ in g if o < p <= c]) for g in groups]
            cands = [(g, xs) for g, xs in cands if len(xs) >= n_min]
            if cands:
                g, xs = max(cands, key=lambda gx: max(gx[1]))   # group reclaimed nearest close
                return dict(direction="long", kind="displacement", entry_ref=max(xs),
                            stop_ref=lo, wick_low=lo, wick_high=o,
                            cluster=g, count=len({t for _, _, t in g}))
        if c < o and (h - c) / rng >= q:
            cands = [(g, [p for _, p, _ in g if c <= p < o]) for g in groups]
            cands = [(g, xs) for g, xs in cands if len(xs) >= n_min]
            if cands:
                g, xs = min(cands, key=lambda gx: min(gx[1]))
                return dict(direction="short", kind="displacement", entry_ref=min(xs),
                            stop_ref=h, wick_low=o, wick_high=h,
                            cluster=g, count=len({t for _, _, t in g}))

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


def _load_trigger_cfg(config_path="config/strategy.yaml"):
    """All trigger thresholds from config — nothing hardcoded (spec-1 §3 config-driven)."""
    import yaml
    cfg = yaml.safe_load(open(config_path))
    d = cfg["triggers"]["displacement"]
    return {
        "disp": {"min_levels_through": int(d["min_levels_through"]),
                 "body_range_min": float(d["body_range_min"]),
                 "close_extreme_quartile": float(d["close_extreme_quartile"]),
                 "atr_floor_enabled": bool(d["atr_floor_enabled"]),
                 "atr_floor_k": float(d["atr_floor_k"]),
                 "atr_length": int(d["atr_length"])},
        "over_extension_sigma": int(cfg["triggers"]["over_extension_sigma"]),
        "cluster_tol": float(cfg["cluster"]["tolerance_points"]),
        "cluster_min_types": int(cfg["cluster"]["min_level_types"]),
    }


def _atr(frame: pd.DataFrame, length: int) -> pd.Series:
    h, lo, c = frame["high"], frame["low"], frame["close"]
    pc = c.shift()
    tr = pd.concat([h - lo, (h - pc).abs(), (lo - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(length).mean()


def detect_triggers(df_1m: pd.DataFrame, cfg: IndicatorsConfig | None = None,
                    start=None, end=None, tol: float | None = None) -> list[Trigger]:
    """Detect triggers across [start, end] (ET). Returns MTF-arbitrated Trigger list."""
    cfg = cfg or load_indicators_config()
    tcfg = _load_trigger_cfg()
    disp = tcfg["disp"]
    if tol is None:
        tol = tcfg["cluster_tol"]
    min_types = tcfg["cluster_min_types"]
    oe_sigma = tcfg["over_extension_sigma"]

    # last instant fully covered by 1m data (1m bars are START-labeled: last bar closes at
    # max ts + 1min); resampled bins whose CLOSE label lies beyond it are forming — drop
    # them so a prefix replay can never evaluate a partial candle as closed (spec-1 §3).
    last_closed = df_1m["ts_event"].max() + _ONE_MIN
    frames = {tf: resample_ohlcv(df_1m, tf) for tf in cfg.entry_tfs}
    frames = {tf: fr[fr["ts_event"] <= last_closed] for tf, fr in frames.items()}
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
            if _include_ote():                       # ANGUS pass-22 fib confluence (split arm)
                # 10-day lookback: fractal fibs use only the most RECENT swing pair, so a
                # trailing window is result-identical to full history (>= 60 4H blocks vs
                # the 7-bar minimum) and keeps per-candle resampling tractable.
                closed_now = df_1m[(df_1m["ts_event"] < t)
                                   & (df_1m["ts_event"] >= t - pd.Timedelta(days=10))]
                levels = levels + _ote_levels(closed_now, t)
            if len(levels) < 2:
                continue
            groups = _level_groups(levels, tol, min_types)
            res = _test_candle(fr.iloc[i], groups, disp,
                               float(atrs[tf].reset_index(drop=True).iloc[i]))
            if res is None:
                continue
            regime = _regime_from_ind(df_1m, t)
            htf = _htf_flag(regime, res["direction"])
            # ANGUS 22-Jul taxonomy. A/B is NOT rejection-vs-displacement (candle shape); it is
            # what price does at the structural level + the ±2 extension context:
            #   CLOSE-THROUGH (displacement): A = REVERSAL — the close-through reverses a recent
            #     ±2 over-extension (price reached the NY-VWAP ±2σ band in the OPPOSITE direction
            #     within the last _EXT_LOOKBACK entry-TF bars, then displaced back through);
            #     B = with-trend CONTINUATION otherwise. The ±2 extension is REQUIRED for A —
            #     counter-trend alone is not enough (Angus: "A would look like ±2 over extension,
            #     then ... candle closes through ... i enter on the retest").
            #   REJECTION (wick in, close back): B2 — fade off the level, either HTF direction.
            if res["kind"] == "displacement":
                # ANGUS 22-Jul: "±2" is the DAILY (session-anchored) VWAP band, and "extension"
                # just means price TOUCHED/wicked the ±2 band (within tolerance) before reversing
                # — not a strict close beyond it.
                dv = ind.get("daily_vwap") or {}
                lb = fr.iloc[max(0, i - _EXT_LOOKBACK):i + 1]
                if res["direction"] == "long":
                    band = dv.get(f"lower_{oe_sigma}")
                    reversed_ext = band is not None and float(lb["low"].min()) <= band + _VWAP_TOUCH_TOL
                else:
                    band = dv.get(f"upper_{oe_sigma}")
                    reversed_ext = band is not None and float(lb["high"].max()) >= band - _VWAP_TOUCH_TOL
                pattern = "A" if reversed_ext else "B"
            else:
                pattern = "B2"        # rejection at a level = fade (with- or counter-HTF)
            g = res.get("cluster")
            center = round(sum(p for _, p, _ in g) / len(g), 4) if g else res["entry_ref"]
            ctypes = sorted({typ for _, _, typ in g}) if g else []
            # ANGUS pass-6 VWAP-touch: did the bar's actual range reach a VWAP band level?
            # (a real price touch, not level-proximity). Tolerance = 2 ticks for rounding.
            bar_lo, bar_hi = float(fr["low"].iloc[i]), float(fr["high"].iloc[i])
            vwaps = [p for _, p, typ in levels if typ == "vwap"]
            vwap_touched = any(bar_lo - _VWAP_TOUCH_TOL <= p <= bar_hi + _VWAP_TOUCH_TOL
                               for p in vwaps)
            ob_mid, ob_stop = _order_block(fr, i, res["direction"])
            raw.append(Trigger(ts=t.isoformat(), tf=tf, direction=res["direction"],
                               kind=res["kind"], pattern=pattern, htf_flag=htf,
                               entry_ref=round(float(res["entry_ref"]), 4),
                               stop_ref=round(float(res["stop_ref"]), 4),
                               wick_low=round(float(res["wick_low"]), 4),
                               wick_high=round(float(res["wick_high"]), 4),
                               cluster_center=round(float(center), 4),
                               confluence_count=res["count"], cluster_types=ctypes,
                               vwap_touched=bool(vwap_touched),
                               ob_mid=ob_mid, ob_stop=ob_stop,
                               close=round(float(fr["close"].iloc[i]), 4),
                               cluster_members=json.dumps(
                                   [[n, round(float(p), 4), typ] for n, p, typ in (g or [])]),
                               level_stack=json.dumps(
                                   [[n, round(float(p), 4), typ] for n, p, typ
                                    in sorted(levels, key=lambda x: x[1])])))
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
