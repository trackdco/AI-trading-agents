"""Signal layer — build the per-TF indicator context (no lookahead) and detect the three
setups with a full confluence count.

Setups (spec §Setups):
  A  Reversal   — entry candle is a REJECTION of a strong level (VWAP band / VAH / VAL /
                  POC), wick through + close back; entry off the rejection close.
                  Alt path: closed OUTSIDE a Bollinger band then reclaimed INSIDE (bb_reclaim).
                  Counter-impulse but only WITH HTF bias.
  B  Continuation— rejection off a MIDLINE (BB basis / VWAP / POC) in the HTF-bias direction.
  B2 POC-limit  — resting limit at POC in the HTF-bias direction (fill on touch), taken only
                  where prior reaction at POC exists (a prior pivot near POC).

Every candidate carries the SET of confluence factors present, so the executor can filter on
min-confluence (3/4/5) and the reporter can break down by factor. HTF bias is mandatory.
Signals fire only on CLOSED candles (no anticipation).
"""
from __future__ import annotations

from datetime import time as dtime

import numpy as np
import pandas as pd

from . import indicators as ind


# ------------------------------------------------------------------ context

class Context:
    """All precomputed, no-lookahead indicator state the detector reads."""

    def __init__(self, bars: pd.DataFrame, cfg: dict):
        self.cfg = cfg
        self.bars = bars
        tz = cfg["data"]["tz"]
        self.tz = tz
        self.idx = bars.set_index("ts_event")
        # 1-min close series (for CVD divergence price reads)
        self.close_1m = self.idx["close"].astype("float64")
        # per-day 1m slices (small frames) so execution never re-scans the full 161k index
        self.day_bars = {d: g for d, g in self.idx.groupby(self.idx.index.normalize())}

        # --- session-anchored VWAP (18:00 CME open) on 1m, sampled per-minute ---
        bands = cfg["indicators"]["vwap"]["bands_sigma"]
        anchor = _t(cfg["indicators"]["vwap"]["anchor"])
        dv = ind.daily_vwap(bars, bands, anchor)
        cols = ["vwap"] + [f"upper_{k}" for k in bands] + [f"lower_{k}" for k in bands]
        for c in cols:
            bars[c] = dv[c].values
        self.vwl = bars.set_index("ts_event")[cols]
        self.vwap_bands = bands

        # --- developing daily volume profile snapshot at each minute (POC/VAH/VAL) ---
        self.prof_at = self._build_profiles(bars, cfg)

        # --- HTF bias series (per-minute, as-of last closed HTF bar) ---
        self.bias_at = self._build_htf_bias(bars, cfg)

        # --- prior-day liquidity levels ---
        self.liq_pdhl = self._prior_day_levels(bars)

    # .......................................................... profiles
    def _build_profiles(self, bars, cfg):
        binp = cfg["indicators"]["volume_profile"]["bin_points"]
        va = cfg["indicators"]["volume_profile"]["value_area_pct"]
        cme = _t(cfg["indicators"]["vwap"]["anchor"])
        sd = ind.anchor_session_date(bars["ts_event"], cme)
        bars = bars.assign(_sd=sd.values)
        # snapshot the developing profile for every minute in [09:29, 15:55] so the entry
        # candle at ts (close-labeled) can read the profile of bars closed at ts.
        prof_at = {}
        for _, g in bars.groupby("_sd"):
            hist = {}
            for row in g.itertuples():
                lo_i = int(np.floor(row.low / binp + 1e-9)); hi_i = int(np.floor(row.high / binp + 1e-9))
                share = row.volume / (hi_i - lo_i + 1)
                for bi in range(lo_i, hi_i + 1):
                    hist[bi] = hist.get(bi, 0.0) + share
                t = row.ts_event.time()
                if dtime(9, 29) <= t <= dtime(15, 55):
                    prof_at[row.ts_event + pd.Timedelta(minutes=1)] = _snap(hist, binp, va)
        return prof_at

    # .......................................................... HTF bias
    def _build_htf_bias(self, bars, cfg):
        vtf = cfg["indicators"]["htf_bias"]["vwap_tf"]
        stf = cfg["indicators"]["htf_bias"]["structure_tf"]
        k = cfg["indicators"]["htf_bias"]["swing_lookback"]
        cme = _t(cfg["indicators"]["vwap"]["anchor"])
        # 1H session-anchored VWAP built from 1m then resampled read is complex; instead use
        # the 1m session VWAP value sampled at the HTF bar close (same anchored VWAP, read at HTF).
        vwap_1m = self.vwl["vwap"]
        # structure on the 15m frame: HH&HL (long) / LH&LL (short) over last two confirmed pivots
        s = ind.resample_ohlcv(bars[["ts_event", "open", "high", "low", "close", "volume"]], stf)
        s = ind.pivots(s, k)
        sh = s[s["piv_high"]][["ts_event", "high"]].reset_index(drop=True)
        sl = s[s["piv_low"]][["ts_event", "low"]].reset_index(drop=True)
        # For each 15m bar close, structure known only from pivots CONFIRMED k bars earlier.
        conf_delay = pd.Timedelta(stf) * k
        bias_rows = []
        for row in s.itertuples():
            ts = row.ts_event
            # pivots confirmed as of ts
            ph = sh[sh["ts_event"] <= ts - conf_delay]
            pl = sl[sl["ts_event"] <= ts - conf_delay]
            struct = "neutral"
            if len(ph) >= 2 and len(pl) >= 2:
                hh = ph["high"].iloc[-1] > ph["high"].iloc[-2]
                hl = pl["low"].iloc[-1] > pl["low"].iloc[-2]
                lh = ph["high"].iloc[-1] < ph["high"].iloc[-2]
                ll = pl["low"].iloc[-1] < pl["low"].iloc[-2]
                if hh and hl:
                    struct = "long"
                elif lh and ll:
                    struct = "short"
            # session VWAP as of this HTF close (last closed 1m bar)
            v = vwap_1m.reindex([ts - pd.Timedelta(minutes=1)]).iloc[0]
            price = row.close
            bias = "neutral"
            if not pd.isna(v):
                if price > v and struct == "long":
                    bias = "long"
                elif price < v and struct == "short":
                    bias = "short"
            bias_rows.append((ts, bias))
        bs = pd.DataFrame(bias_rows, columns=["ts_event", "bias"]).set_index("ts_event")["bias"]
        return bs

    def bias_asof(self, ts):
        """HTF bias as of ts = the bias stamped on the last HTF bar closed at/before ts."""
        b = self.bias_at.loc[self.bias_at.index <= ts]
        return b.iloc[-1] if len(b) else "neutral"

    # .......................................................... liquidity
    def _prior_day_levels(self, bars):
        cme = _t(bars_cme_anchor(self.cfg))
        sd = ind.anchor_session_date(bars["ts_event"], cme)
        g = bars.assign(_sd=sd.values).groupby("_sd")
        hl = pd.DataFrame({"high": g["high"].max(), "low": g["low"].min()})
        prior = hl.shift(1)
        return {str(k): (prior.loc[k, "high"], prior.loc[k, "low"])
                for k in prior.index if not pd.isna(prior.loc[k, "high"])}, sd


def _t(s):
    h, m = s.split(":"); return dtime(int(h), int(m))


def bars_cme_anchor(cfg):
    return cfg["indicators"]["vwap"]["anchor"]


def _snap(hist, binp, va):
    imin, imax = min(hist), max(hist)
    arr = np.array([hist.get(i, 0.0) for i in range(imin, imax + 1)])
    centers = (np.arange(imin, imax + 1) + 0.5) * binp
    total = arr.sum(); n = len(arr); poc = int(arr.argmax()); lo = hi = poc; cov = arr[poc]
    tgt = va / 100.0 * total
    while cov < tgt - 1e-9 and (lo > 0 or hi < n - 1):
        b = arr[lo - 1] if lo > 0 else -np.inf
        a = arr[hi + 1] if hi < n - 1 else -np.inf
        if a >= b: hi += 1; cov += arr[hi]
        else: lo -= 1; cov += arr[lo]
    return dict(poc=float(centers[poc]), vah=float(centers[hi]), val=float(centers[lo]))


# ------------------------------------------------------------------ per-TF frame

def build_tf_frame(bars, tf, cfg):
    """Resample to the entry TF and attach BB, Keltner, pivots, fib50, order blocks."""
    r = ind.resample_ohlcv(bars[["ts_event", "open", "high", "low", "close", "volume"]], tf)
    bb = ind.bollinger(r, cfg["indicators"]["bollinger"]["length"],
                       cfg["indicators"]["bollinger"]["stdev_mult"])
    r = r.assign(bb_basis=bb["basis"].values, bb_up=bb["upper"].values, bb_lo=bb["lower"].values)
    kc = ind.keltner(r, cfg["indicators"]["volatility_bands"]["ema_length"],
                     cfg["indicators"]["volatility_bands"]["atr_length"],
                     cfg["indicators"]["volatility_bands"]["mult"])
    r = r.assign(kc_up=kc["kc_upper"].values, kc_lo=kc["kc_lower"].values, kc_mid=kc["kc_mid"].values)
    r = ind.pivots(r, cfg["indicators"]["htf_bias"]["swing_lookback"])
    return r.reset_index(drop=True)


def order_blocks(r, cfg):
    """Detect order blocks on TF frame r. Bullish OB = last DOWN candle before an up-impulse
    >= impulse_min_points; supply OB mirror. Returns list of dicts confirmed at the impulse
    candle's close (no lookahead). ob_mid = 50% of the OB candle range."""
    imp = cfg["indicators"]["order_block"]["impulse_min_points"]
    obs = []
    o = r["open"].to_numpy(); h = r["high"].to_numpy(); l = r["low"].to_numpy(); c = r["close"].to_numpy()
    ts = r["ts_event"].to_numpy()
    for i in range(1, len(r)):
        move = c[i] - c[i - 1]
        if move >= imp:  # up impulse -> demand OB = last down candle at/before i-1
            j = i - 1
            while j >= 0 and c[j] >= o[j]:
                j -= 1
            if j >= 0:
                obs.append(dict(confirm_ts=ts[i], dir="long", lo=l[j], hi=h[j],
                                mid=(h[j] + l[j]) / 2))
        elif move <= -imp:
            j = i - 1
            while j >= 0 and c[j] <= o[j]:
                j -= 1
            if j >= 0:
                obs.append(dict(confirm_ts=ts[i], dir="short", lo=l[j], hi=h[j],
                                mid=(h[j] + l[j]) / 2))
    return pd.DataFrame(obs)


def fib50_series(r, cfg):
    """Most-recent significant-swing 50% level, confirmed as-of each bar (no lookahead).
    Uses confirmed pivots (delayed by swing_lookback) spanning >= swing_min_points."""
    k = cfg["indicators"]["htf_bias"]["swing_lookback"]
    minpts = cfg["indicators"]["fib"]["swing_min_points"]
    conf_ns = int((pd.Timedelta(_tf_of(r)) * k).value)
    ph = r[r["piv_high"]]; pl = r[r["piv_low"]]
    out = np.full(len(r), np.nan)
    if len(ph) and len(pl):
        ph_ts = pd.DatetimeIndex(ph["ts_event"]).asi8; ph_v = ph["high"].to_numpy("float64")
        pl_ts = pd.DatetimeIndex(pl["ts_event"]).asi8; pl_v = pl["low"].to_numpy("float64")
        cutoff = pd.DatetimeIndex(r["ts_event"]).asi8 - conf_ns   # last confirmable pivot time per bar
        ih = np.searchsorted(ph_ts, cutoff, side="right") - 1     # index of last confirmed swing high
        il = np.searchsorted(pl_ts, cutoff, side="right") - 1
        valid = (ih >= 0) & (il >= 0)
        vh = ph_v[np.clip(ih, 0, len(ph_v) - 1)]
        vl = pl_v[np.clip(il, 0, len(pl_v) - 1)]
        fib = (vh + vl) / 2.0
        ok = valid & (np.abs(vh - vl) >= minpts)
        out[ok] = fib[ok]
    return pd.Series(out, index=r.index)


def _tf_of(r):
    # infer the rule string from median spacing
    d = r["ts_event"].diff().dt.total_seconds().median()
    return f"{int(round(d/60))}min"


# ------------------------------------------------------------------ detection

def detect(ctx: Context, tf: str, cfg: dict) -> pd.DataFrame:
    """Return one row per candidate signal on `tf`, with confluence factor set."""
    tol = cfg["confluence"]["proximity_points"]
    # entry window: use the golden-window bounds if set, else the full session
    open_t = _t(cfg["session"].get("entry_start") or cfg["session"]["open"])
    flat_t = _t(cfg["session"].get("entry_end") or cfg["session"]["flat_time"])
    r = build_tf_frame(ctx.bars, tf, cfg)
    r["fib50"] = fib50_series(r, cfg)
    obs = order_blocks(r, cfg)
    rej_large_pts = cfg["indicators"]["rejection"]["large_range_points"]
    wick_frac = cfg["indicators"]["rejection"]["wick_frac"]
    # order blocks as sorted numpy arrays (avoid per-candle DataFrame filtering)
    if len(obs):
        _o = obs.sort_values("confirm_ts")
        ob_ts = pd.DatetimeIndex(_o["confirm_ts"]).asi8    # int64 ns (UTC), sorted
        ob_islong = (_o["dir"].to_numpy() == "long")
        ob_mid = _o["mid"].to_numpy("float64")
    else:
        ob_ts = np.array([], dtype="int64")
        ob_islong = np.array([], dtype=bool); ob_mid = np.array([], dtype="float64")

    # vectorized as-of lookups (avoid per-candle linear scans):
    #  * HTF bias stamped on the last HTF bar closed at/before each candle
    #  * session VWAP bands as of ts (= 1m VWAP at ts-1min)
    bias_df = pd.merge_asof(r[["ts_event"]], ctx.bias_at.reset_index().rename(
        columns={"index": "ts_event"}), on="ts_event", direction="backward")
    r["candbias"] = bias_df["bias"].fillna("neutral").values
    vw_asof = ctx.vwl.reindex(r["ts_event"] - pd.Timedelta(minutes=1)).reset_index(drop=True)
    vw_asof.index = r.index

    out = []
    prev = None
    for row in r.itertuples():
        ts = row.ts_event
        t = ts.time()
        if not (open_t <= t <= flat_t):
            prev = row; continue
        vw = vw_asof.loc[row.Index]
        prof = ctx.prof_at.get(ts)
        if prof is None or pd.isna(vw["vwap"]):
            prev = row; continue
        bias = row.candbias

        # named levels available at ts
        vwap_levels = {"vwap": vw["vwap"]}
        for k in ctx.vwap_bands:
            vwap_levels[f"vwap+{k}"] = vw[f"upper_{k}"]
            vwap_levels[f"vwap-{k}"] = vw[f"lower_{k}"]
        prof_levels = {"poc": prof["poc"], "vah": prof["vah"], "val": prof["val"]}
        o, h, l, c = row.open, row.high, row.low, row.close
        rng = h - l

        # recent OB mids (confirmed at/before ts) split by direction, as numpy arrays
        k = int(np.searchsorted(ob_ts, ts.value, side="right"))
        if k:
            mk = ob_mid[:k]; lk = ob_islong[:k]
            mids_long = mk[lk]; mids_short = mk[~lk]
        else:
            mids_long = mids_short = ob_mid[:0]
        fib = row.fib50
        pdhl = ctx.liq_pdhl[0].get(_sess_day(ctx, ts), (np.nan, np.nan))
        liq_levels = [x for x in pdhl if not pd.isna(x)]

        def near(a, b):
            return (a is not None) and (b is not None) and (not pd.isna(a)) and (not pd.isna(b)) \
                and abs(a - b) <= tol

        def confluence(level, direction, entry_px, setup):
            f = set()
            if bias == direction:
                f.add("htf_bias")
            # rejection candle of the level
            if ind.is_rejection(o, h, l, c, level, direction, wick_frac):
                f.add("rejection_candle")
            if near(level, row.bb_basis):
                f.add("bb_midline")
            if any(near(level, v) for v in vwap_levels.values()):
                f.add("vwap")
            if near(level, prof_levels["poc"]):
                f.add("poc")
            oms = mids_long if direction == "long" else mids_short
            if oms.size and (np.abs(oms - entry_px) <= tol).any():
                f.add("ob_mid_50")
            if near(level, fib):
                f.add("fib_50")
            # bb_reclaim: closed outside a BB band on prior bar, back inside now
            if prev is not None:
                if direction == "long" and prev.close < prev.bb_lo and c > row.bb_lo:
                    f.add("bb_reclaim")
                if direction == "short" and prev.close > prev.bb_up and c < row.bb_up:
                    f.add("bb_reclaim")
            if any(near(level, x) for x in liq_levels):
                f.add("liquidity")
            # 50% of a large rejection candle (this candle, if large)
            if rng >= rej_large_pts and "rejection_candle" in f and near(entry_px, (h + l) / 2):
                f.add("rejection_50")
            if near(level, row.kc_up) or near(level, row.kc_lo):
                f.add("volatility_band")
            return f

        # -------- Setup A: reversal off a strong level (VWAP band / VAH / VAL / POC / BB) --------
        if cfg["setups"]["A_reversal"]:
            strong = {**vwap_levels, **prof_levels}
            if cfg["setups"].get("A_include_bb"):
                strong = {**strong, "bb_up": row.bb_up, "bb_lo": row.bb_lo, "bb_basis": row.bb_basis}
            for lname, L in strong.items():
                if pd.isna(L):
                    continue
                d = "long" if (l < L and c > L) else "short" if (h > L and c < L) else None
                if d is None:
                    continue
                if not ind.is_rejection(o, h, l, c, L, d, wick_frac):
                    continue
                f = confluence(L, d, c, "A")
                out.append(_mk(ts, tf, "A", d, L, lname, c, o, h, l, bias, f, t, open_t, cfg))

        # -------- Setup B: continuation, rejection off a MIDLINE in bias direction --------
        if cfg["setups"]["B_continuation"] and bias in ("long", "short"):
            mids = {"bb_basis": row.bb_basis, "vwap": vw["vwap"], "poc": prof_levels["poc"]}
            for lname, L in mids.items():
                if pd.isna(L):
                    continue
                d = bias
                if not ind.is_rejection(o, h, l, c, L, d, wick_frac):
                    continue
                f = confluence(L, d, c, "B")
                out.append(_mk(ts, tf, "B", d, L, lname, c, o, h, l, bias, f, t, open_t, cfg))

        # -------- Setup B2: POC limit in bias direction (fill on touch) --------
        if cfg["setups"]["B2_poc_limit"] and bias in ("long", "short"):
            L = prof_levels["poc"]
            # prior reaction at POC: a confirmed pivot near POC earlier in the frame
            react = False
            if k:
                react = bool((np.abs(ob_mid[:k] - L) <= tol).any())
            d = bias
            f = confluence(L, d, L, "B2")
            f.add("poc")
            out.append(_mk(ts, tf, "B2", d, L, "poc", c, o, h, l, bias, f, t, open_t, cfg,
                           limit=True, prior_reaction=bool(react)))
        prev = row

    return pd.DataFrame(out)


def _sess_day(ctx, ts):
    cme = _t(bars_cme_anchor(ctx.cfg))
    return str(ind.session_date_scalar(ts, cme))


def _mk(ts, tf, setup, d, level, lname, c, o, h, l, bias, factors, t, open_t, cfg, limit=False,
        prior_reaction=True):
    focus = cfg["session"]["focus_minutes"]
    late = (pd.Timestamp.combine(pd.Timestamp("2000-01-01"), t)
            - pd.Timestamp.combine(pd.Timestamp("2000-01-01"), open_t)) > pd.Timedelta(minutes=focus)
    return dict(ts=ts, tf=tf, setup=setup, dir=d, level=float(level), lname=lname,
                c=float(c), o=float(o), h=float(h), l=float(l), bias=bias,
                factors=sorted(factors), n_conf=len(factors), late_session=bool(late),
                limit=limit, prior_reaction=prior_reaction)
