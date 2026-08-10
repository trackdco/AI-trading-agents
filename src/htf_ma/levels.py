"""HTF BB MA mechanism census — level construction (SPEC §2).

Every level is AS-OF-BAR: the value at minute t is computable from bars with
timestamp <= t and nothing else. Gate G1 (lookahead) and G7 (as-of profile) in
scripts/htf_ma_gates.py assert this by perturbing bars after t and demanding
bit-identical levels. Convention notes:

* BB middle bands: BB(20) SMA of close per TF in {1,2,3,5,15,60}m. The
  DEVELOPING TF bar is included with its close-so-far at t — the chart
  convention (what the trader's eye sees), and strictly causal. Band width
  W_tf = upper - lower (2 sd of the same 20 closes) is stored per TF.
* Resample alignment (G8): label='right', closed='left' on the NY-tz index —
  15m bars end on :00/:15/:30/:45, 60m on the hour, independent of the frame's
  first row.
* VWAP: anchored 18:00 ET, cumulative vol-weighted price with +/-1/2/3 sd
  bands (sd of price about vwap, volume-weighted, cumulative).
* Developing session volume profile: anchored 18:00 ET, each bar's volume
  spread uniformly across its high-low range into fixed-width bins (canonical
  1.00pt; variants 0.25/2.00). POC and the 70% value area are recomputed at
  each requested minute from the accumulation SO FAR only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NY = "America/New_York"
TFS = [1, 2, 3, 5, 15, 60]
SESSION_ANCHOR_H = 18          # 18:00 ET


def session_key(ts: pd.Timestamp) -> str:
    """The 18:00-anchored session a minute belongs to (date of the anchor)."""
    t = ts.tz_convert(NY)
    d = t.normalize()
    return str((d if t.hour >= SESSION_ANCHOR_H else d - pd.Timedelta(days=1)).date())


def session_tag(ts: pd.Timestamp) -> str:
    """SPEC §1 session tags — tagged always, filtered never."""
    hm = ts.tz_convert(NY).hour * 60 + ts.tz_convert(NY).minute
    if hm >= 18 * 60 or hm < 3 * 60:
        return "asia"
    if hm < 8 * 60:
        return "london"
    if hm < 9 * 60 + 30:
        return "ny_pre"
    if hm < 12 * 60:
        return "ny_rth_am"
    if hm < 17 * 60:
        return "ny_pm"
    return "maintenance"


def bb_ma_asof(bars_1m: pd.DataFrame, tf: int, n: int = 20):
    """Per-1m-row BB(n) middle band and width for a TF, developing bar included.

    Returns two Series aligned to bars_1m.index: ma, width (upper-lower = 4 sd?
    no: width = 2*2*sd = upper-lower with 2-sd bands). Computation: for each 1m
    close at t, the TF close series is the closes of completed TF bars before
    t's TF bucket plus the developing bucket's close-so-far (= close at t)."""
    idx = bars_1m.index
    bucket_end = idx.floor(f"{tf}min") + pd.Timedelta(minutes=tf)
    close = bars_1m.close
    # completed TF closes, stamped at their end minute
    tfc = close.resample(f"{tf}min", label="right", closed="left").last().dropna()
    # for each 1m row: SMA over last n-1 completed TF closes strictly before
    # bucket_end, plus the developing close (close at t)
    # positions of the last completed TF bar strictly before each row's bucket.
    # ROW t IS THE LEVEL AT THE CLOSE OF 1m BAR t (bar-start stamping): usable
    # for decisions at t+1m and later, never at t itself.
    pos = np.searchsorted(tfc.index.values, (bucket_end - pd.Timedelta(minutes=tf)).values,
                          side="right") - 1
    vals = tfc.to_numpy()
    csum = np.concatenate([[0.0], np.cumsum(vals)])
    csum2 = np.concatenate([[0.0], np.cumsum(vals ** 2)])
    k = n - 1                       # completed bars used
    lo = pos - k + 1
    ok = lo >= 0
    s = np.where(ok, csum[np.clip(pos + 1, 0, len(vals))] - csum[np.clip(lo, 0, len(vals))], np.nan)
    s2 = np.where(ok, csum2[np.clip(pos + 1, 0, len(vals))] - csum2[np.clip(lo, 0, len(vals))], np.nan)
    dev = close.to_numpy()
    m = (s + dev) / n
    var = (s2 + dev ** 2) / n - m ** 2
    sd = np.sqrt(np.maximum(var, 0.0))
    ma = pd.Series(m, index=idx)
    width = pd.Series(4.0 * sd, index=idx)          # upper(+2sd) - lower(-2sd)
    ma[~ok] = np.nan
    width[~ok] = np.nan
    return ma, width


def vwap_bands(bars_1m: pd.DataFrame, source: str = "open") -> pd.DataFrame:
    """Session VWAP (18:00 anchor) with +/-1/2/3 sd bands, per 1m row, causal.

    source="open" is the calibrated default: the trader's TradingView VWAP is
    configured to `Session open`, bar-matched to 0.13pt on his 2026-01-07
    screenshot. The former hlc3 default sat ~0.5pt out — two NQ ticks, enough
    to flip a borderline "closed through the band" call. Parquet artifacts
    written before 2026-08-10 were built on hlc3; rebuild before comparing.
    """
    df = bars_1m.copy()
    if source == "open":
        tp = df.open.astype(float)
    elif source == "hlc3":
        tp = (df.high + df.low + df.close) / 3.0
    elif source == "ohlc4":
        tp = (df.open + df.high + df.low + df.close) / 4.0
    elif source == "close":
        tp = df.close.astype(float)
    else:
        raise ValueError(f"unknown vwap source: {source!r}")
    v = df.volume.astype(float).clip(lower=0)
    key = [session_key(t) for t in df.index]
    g = pd.Series(key, index=df.index)
    pv = (tp * v).groupby(g).cumsum()
    vv = v.groupby(g).cumsum().replace(0, np.nan)
    vwap = pv / vv
    p2v = (tp ** 2 * v).groupby(g).cumsum()
    var = p2v / vv - vwap ** 2
    sd = np.sqrt(var.clip(lower=0))
    out = pd.DataFrame({"vwap": vwap, "vwap_sd": sd}, index=df.index)
    for k in (1, 2, 3):
        out[f"vwap_p{k}"] = vwap + k * sd
        out[f"vwap_m{k}"] = vwap - k * sd
    return out


class DevelopingProfile:
    """18:00-anchored developing volume profile with as-of snapshots.

    add_bar() accumulates one 1m bar; snapshot() returns (poc, vah, val) from
    the accumulation so far — by construction it cannot see later bars (G7)."""

    def __init__(self, bin_width: float = 1.0):
        self.bw = float(bin_width)
        self.vol: dict[int, float] = {}

    def add_bar(self, high: float, low: float, volume: float) -> None:
        if volume <= 0 or not np.isfinite(high) or not np.isfinite(low):
            return
        b0 = int(np.floor(low / self.bw))
        b1 = int(np.floor(high / self.bw))
        nb = b1 - b0 + 1
        per = float(volume) / nb
        for b in range(b0, b1 + 1):
            self.vol[b] = self.vol.get(b, 0.0) + per

    def snapshot(self):
        if not self.vol:
            return np.nan, np.nan, np.nan
        bins = sorted(self.vol)
        v = np.array([self.vol[b] for b in bins])
        total = v.sum()
        pi = int(np.argmax(v))
        lo = hi = pi
        acc = v[pi]
        while acc < 0.70 * total and (lo > 0 or hi < len(v) - 1):
            nxt_lo = v[lo - 1] if lo > 0 else -1.0
            nxt_hi = v[hi + 1] if hi < len(v) - 1 else -1.0
            if nxt_hi >= nxt_lo:
                hi += 1
                acc += v[hi]
            else:
                lo -= 1
                acc += v[lo]
        c = self.bw / 2.0
        return (bins[pi] * self.bw + c,
                bins[hi] * self.bw + c,
                bins[lo] * self.bw + c)


def profile_at_minutes(bars_1m: pd.DataFrame, minutes: list[pd.Timestamp],
                       bin_width: float = 1.0) -> pd.DataFrame:
    """POC/VAH/VAL at each requested minute (as-of), efficiently in one pass.
    A bar stamped t covers [t, t+1); it is included for request minutes > t
    (i.e. only completed bars — a request AT t sees bars strictly before t)."""
    want = sorted(pd.Timestamp(m) for m in minutes)
    out = []
    by_sess: dict[str, list[pd.Timestamp]] = {}
    for m in want:
        by_sess.setdefault(session_key(m), []).append(m)
    skey = pd.Series([session_key(t) for t in bars_1m.index], index=bars_1m.index)
    for sess, ms in by_sess.items():
        seg = bars_1m[skey == sess]
        prof = DevelopingProfile(bin_width)
        i = 0
        rows = list(seg.itertuples())
        for m in ms:
            while i < len(rows) and rows[i].Index < m:
                prof.add_bar(rows[i].high, rows[i].low, rows[i].volume)
                i += 1
            poc, vah, val = prof.snapshot()
            out.append({"minute": m, "poc": poc, "vah": vah, "val": val})
    return pd.DataFrame(out).set_index("minute").sort_index()
