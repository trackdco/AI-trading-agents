#!/usr/bin/env python3
"""VWAP bands paired with FVG / IFVG — Angus's model.

WHY VWAP. Every level this project has tested so far was drawn: a swing someone decided was
significant, a session extreme, a gap someone eyeballed. VWAP is arithmetic. Volume-weighted
mean price and the volume-weighted standard deviation around it are the same numbers for
everyone holding the same tape, which means the band is not a matter of taste and cannot be
quietly refitted. If price reverts to a statistical mean, this is where it shows up.

THE TWO SETUPS, as Angus specified them (longs at the lower band; shorts mirror at the upper):

  RECLAIM   price trades below -1sigma, then closes back ABOVE it with displacement, and that
            displacement leaves a bullish fair value gap. Enter on the retrace into the gap.
            Stop below the low that was set before it broke the band. Target the middle band
            (VWAP), then +1sigma, then the external draw on liquidity.

  REJECT    price tags -1sigma and refuses it -- a bearish gap in the approach leg gets INVERTED
            (price closes back above it). Enter on that inversion. Same stop, same targets.

MULTI-TIMEFRAME, which is the point. Gaps are searched 15m -> 10m -> 5m -> 3m -> 2m -> 1m and
the HIGHEST timeframe present in the leg wins. A 3m floor was rejecting 3.57 setups per day in
the NY AM funnel -- by far the largest single leak -- and that floor was one trader's preference,
not a property of the market.

CAUSALITY. VWAP and its bands at bar i use bars up to and including i, so they are known at that
bar's CLOSE and never earlier; every entry fills at the next bar's open. A fair value gap is not
visible until its third bar has closed, so a 15m gap is unusable for up to 14 minutes after it
forms. Both rules exist because this project has manufactured an edge out of exactly these two
head starts before.

    python -m scripts.vwap_fvg [--grid] [--from 2023-01-01] [--to 2026-07-31]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
BARS = ("data/reference/nq_1m_master.parquet", "data/reference/nq_1m_feb_jul2026.parquet")
TICK = 0.25
FVG_TFS = (15, 10, 5, 3, 2, 1)        # highest-first; 1m only when nothing larger is in the leg
RTH = (9 * 60 + 30, 16 * 60)
WINDOWS = ((9 * 60 + 30, 11 * 60 + 10), (13 * 60, 15 * 60))
ANCHORS = {"session": 18 * 60, "rth": 9 * 60 + 30}
MIN_STOP_PTS = 2.0
MAX_STOP_PTS = 60.0
RETRACE_WAIT = 30                     # bars a resting limit at the gap stays live
FIT0, FIT1 = "2025-06-01", "2026-07-31"


def load() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
                   for p in BARS], ignore_index=True)
    b = b.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    t = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b["day"] = t.dt.strftime("%Y-%m-%d")
    b["hm"] = t.dt.hour * 60 + t.dt.minute
    # session day: the 18:00 block belongs to the NEXT trading day
    sd = pd.to_datetime(b.day).to_numpy()
    b["sday"] = pd.to_datetime(np.where(b.hm.to_numpy() >= 18 * 60,
                                        sd + np.timedelta64(1, "D"), sd)).strftime("%Y-%m-%d")
    return b


def vwap_bands(tp: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Volume-weighted mean and volume-weighted standard deviation, cumulative from the anchor.

    sd^2 = E[p^2] - E[p]^2 under the volume measure. Clipped at zero for float error only."""
    cv = np.cumsum(v)
    cv[cv == 0] = 1.0
    m = np.cumsum(tp * v) / cv
    m2 = np.cumsum(tp * tp * v) / cv
    return m, np.sqrt(np.maximum(m2 - m * m, 0.0))


def tf_fvgs(h: np.ndarray, lo: np.ndarray, tf: int) -> list[dict]:
    n = len(h) // tf * tf
    if n < tf * 3:
        return []
    H = h[:n].reshape(-1, tf).max(1)
    L = lo[:n].reshape(-1, tf).min(1)
    out = []
    for i in range(2, len(H)):
        ready = (i + 1) * tf - 1                      # known only at the third bar's CLOSE
        if L[i] > H[i - 2]:
            out.append({"tf": tf, "dir": "bull", "top": float(L[i]),
                        "bottom": float(H[i - 2]), "ready": ready})
        if H[i] < L[i - 2]:
            out.append({"tf": tf, "dir": "bear", "top": float(L[i - 2]),
                        "bottom": float(H[i]), "ready": ready})
    return out


def in_window(m: int) -> bool:
    return any(a <= m < b for a, b in WINDOWS)


def run_day(g: pd.DataFrame, anchor: str, k: float, setup: str,
            pools: dict) -> list[dict]:
    o = g.open.to_numpy(float)
    h = g.high.to_numpy(float)
    lo = g.low.to_numpy(float)
    c = g.close.to_numpy(float)
    v = g.volume.to_numpy(float)
    hm = g.hm.to_numpy(int)
    n = len(h)
    if n < 120:
        return []

    tp = (h + lo + c) / 3.0
    mid, sd = vwap_bands(tp, v)
    up, dn = mid + k * sd, mid - k * sd

    gaps = [x for t_ in FVG_TFS for x in tf_fvgs(h, lo, t_)]
    gaps.sort(key=lambda x: x["ready"])

    out: list[dict] = []
    armed: dict[str, int] = {}

    for i in range(30, n - 5):
        if not in_window(hm[i]):
            continue
        for side in ("long", "short"):
            band = dn if side == "long" else up
            # ---- the band has to have been TAGGED recently, and price now back on our side ----
            look = slice(max(0, i - 60), i + 1)
            tagged = (lo[look] <= band[look]).any() if side == "long" \
                else (h[look] >= band[look]).any()
            if not tagged:
                continue
            if armed.get(f"{side}{i // 30}"):
                continue
            back = c[i] > band[i] if side == "long" else c[i] < band[i]
            if not back:
                continue

            # the leg = from the extreme made at/after the band tag, to now
            seg = np.arange(max(0, i - 60), i + 1)
            ext_i = int(seg[np.argmin(lo[seg])] if side == "long" else seg[np.argmax(h[seg])])
            ext = lo[ext_i] if side == "long" else h[ext_i]
            if ext_i >= i:
                continue

            want = "bull" if side == "long" else "bear"
            if setup == "reject":
                want = "bear" if side == "long" else "bull"   # the gap we INVERT

            cand = None
            for tf in FVG_TFS:                                # highest timeframe first
                m = [x for x in gaps if x["tf"] == tf and x["dir"] == want
                     and ext_i - 30 <= x["ready"] <= i]
                if m:
                    cand = m[-1]
                    break
            if cand is None:
                continue

            if setup == "reclaim":
                # displacement gap in OUR direction -> rest a limit at the gap edge
                lim = cand["top"] if side == "long" else cand["bottom"]
                ent_i = None
                for u in range(i + 1, min(i + RETRACE_WAIT, n - 1)):
                    if (lo[u] <= lim) if side == "long" else (h[u] >= lim):
                        ent_i = u
                        break
                if ent_i is None:
                    continue
                entry = lim
            else:
                # inversion: a close back through the opposing gap, fill at the NEXT open
                edge = cand["top"] if side == "long" else cand["bottom"]
                if not ((c[i] > edge) if side == "long" else (c[i] < edge)):
                    continue
                ent_i = i + 1
                entry = o[ent_i]
            if ent_i >= n - 2 or not in_window(hm[ent_i]):
                continue

            lo_ref = min(ext, cand["bottom"]) if side == "long" else max(ext, cand["top"])
            stop = lo_ref - TICK if side == "long" else lo_ref + TICK
            risk = abs(entry - stop)
            if not (MIN_STOP_PTS <= risk <= MAX_STOP_PTS):
                continue

            t_mid = mid[ent_i]
            t_band = up[ent_i] if side == "long" else dn[ent_i]
            beyond = [x for x in pools.values()
                      if (x > entry if side == "long" else x < entry)]
            dol = (min(beyond) if side == "long" else max(beyond)) if beyond else np.nan
            if (t_mid <= entry) if side == "long" else (t_mid >= entry):
                continue                                    # already past the mean

            # ---- resolve the path in order ----
            r = {"day": g.day.iloc[0], "side": side, "setup": setup, "anchor": anchor,
                 "k": k, "tf": cand["tf"], "hm": int(hm[ent_i]), "risk": risk,
                 "r_mid": abs(t_mid - entry) / risk,
                 "r_band": abs(t_band - entry) / risk,
                 "r_dol": abs(dol - entry) / risk if dol == dol else np.nan,
                 "window": "AM" if hm[ent_i] < 12 * 60 else "PM"}
            hit_mid = hit_band = False
            rmax = 0.0
            # MFE BEFORE THE STOP, with no target in the way. This is the whole payoff curve in
            # one number: P(reach kR) == P(mfe >= k) for every k at once, so every possible
            # target can be priced afterwards without re-running the path and without anyone
            # choosing a target first and reporting it as if it had been chosen last.
            mfe = 0.0
            for u in range(ent_i, n):
                fav = (h[u] - entry) / risk if side == "long" else (entry - lo[u]) / risk
                mfe = max(mfe, fav)
                if ((lo[u] <= stop) if side == "long" else (h[u] >= stop)):
                    break
            for u in range(ent_i, n):
                fav = (h[u] - entry) / risk if side == "long" else (entry - lo[u]) / risk
                rmax = max(rmax, fav)
                if ((lo[u] <= stop) if side == "long" else (h[u] >= stop)) and not hit_mid:
                    break
                if not hit_mid and ((h[u] >= t_mid) if side == "long" else (lo[u] <= t_mid)):
                    hit_mid = True
                if hit_mid and ((h[u] >= t_band) if side == "long" else (lo[u] <= t_band)):
                    hit_band = True
                    break
                if hit_mid and ((lo[u] <= entry) if side == "long" else (h[u] >= entry)):
                    break                                   # runner stopped at break even
            r["hit_mid"], r["hit_band"], r["r_max"] = hit_mid, hit_band, rmax
            r["mfe"] = mfe
            # half off at the mean, rest to the opposite band, break even behind it
            r["R"] = (-1.0 if not hit_mid else
                      0.5 * r["r_mid"] + (0.5 * r["r_band"] if hit_band else 0.0))
            out.append(r)
            armed[f"{side}{i // 30}"] = 1
    return out


def book(x: pd.DataFrame, label: str, fr: float = 0.03) -> None:
    if len(x) < 5:
        print(f"  {label:34} n={len(x):4d}   --")
        return
    R = x.R - fr
    pf = R[R > 0].sum() / max(-R[R < 0].sum(), 1e-9)
    print(f"  {label:34} n={len(x):4d}  win={(R>0).mean():5.1%}  PF={pf:5.2f}  "
          f"avgR={R.mean():+.3f}  mid={x.hit_mid.mean():5.1%}  band={x.hit_band.mean():5.1%}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="d0", default="2023-01-01")
    ap.add_argument("--to", dest="d1", default="2026-07-31")
    ap.add_argument("--csv", default="output/vwap_fvg.csv")
    a = ap.parse_args()

    b = load()
    rth = b[(b.hm >= RTH[0]) & (b.hm < RTH[1])]
    S = rth.groupby("day").agg(h=("high", "max"), l=("low", "min"))
    ph, pl = S.h.shift(1), S.l.shift(1)
    on = b[b.hm >= 18 * 60].groupby("sday").agg(h=("high", "max"), l=("low", "min"))

    rows = []
    for anchor, a0 in ANCHORS.items():
        src = b[(b.hm >= a0) | (b.hm < RTH[1])] if anchor == "session" else rth
        key = "sday" if anchor == "session" else "day"
        for d, g in src.groupby(key, sort=True):
            if not (a.d0 <= d <= a.d1) or d not in ph.index or ph.get(d) != ph.get(d):
                continue
            pools = {"PDH": float(ph[d]), "PDL": float(pl[d])}
            if d in on.index:
                pools["ONH"], pools["ONL"] = float(on.h[d]), float(on.l[d])
            gg = g.sort_values("ts_event").reset_index(drop=True)
            for k in (1.0, 2.0):
                for setup in ("reclaim", "reject"):
                    rows += run_day(gg, anchor, k, setup, pools)

    T = pd.DataFrame(rows)
    if T.empty:
        print("no trades")
        return 1
    T["fit"] = (T.day >= FIT0) & (T.day <= FIT1)
    T.to_csv(ROOT / a.csv, index=False)
    nd_fit = T[T.fit].day.nunique() or 1
    nd_oos = T[~T.fit].day.nunique() or 1

    print(f"VWAP BANDS x FVG/IFVG — {len(T):,} trades over the full grid\n")
    print(f"{'':36}{'FIT 2025-06..2026-07':>52}")
    for anchor in ANCHORS:
        for k in (1.0, 2.0):
            for setup in ("reclaim", "reject"):
                for win in ("AM", "PM"):
                    m = ((T.anchor == anchor) & (T.k == k) & (T.setup == setup)
                         & (T.window == win))
                    f, s = T[m & T.fit], T[m & ~T.fit]
                    if len(f) < 8 and len(s) < 8:
                        continue
                    lbl = f"{anchor:7} {k:.0f}sd {setup:7} {win}"
                    print(f"\n  {lbl}   {len(f)/nd_fit:.2f}/day fit, {len(s)/nd_oos:.2f}/day oos")
                    book(f, "   fit")
                    book(s, "   out-of-fit")
    print(f"\nwrote {a.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
