#!/usr/bin/env python3
"""PB Blake's mechanical inversion model — full rule set, NQ, NY session.

THE MODEL, from the transcript, stated as rules:

  1. Price sweeps a SIGNIFICANT liquidity pool. Not any swing -- a level visible on the higher
     timeframe: previous day high/low, overnight high/low, London high/low, or (for the
     afternoon window) the AM session high/low.
  2. After the sweep the market must REBALANCE, so the sweep leg has to have left a fair value
     gap behind it.
  3. Entry is the inversion of the HIGHEST-TIMEFRAME fair value gap in that leg. Check 15m, then
     10m, then 5m, then 3m -- take the highest that exists. 3m is the floor; below that, no trade.
  4. Stop goes at the swept extreme.
  5. First target is the nearest UNMITIGATED fair value gap beyond entry -- the internal draw,
     the imbalance the market has to rebalance. Break even there.
  6. Runner goes to external liquidity -- equal highs/lows, the session extreme, the previous
     day extreme.
  7. Windows only: 09:30-11:10 and 13:00-15:00. No lunch.

  Blake explicitly REMOVED the SMT rule on reflection ("I rarely see SMT fair value gaps... I'm
  just going to take that off"), and Angus has ruled SMT out separately. It is not in here.

WHAT "DRAW ON LIQUIDITY" MEANS MECHANICALLY, since that is the part he says you need to get:
the model has two draws and they are different objects. The INTERNAL draw is an unfilled FVG --
an inefficiency the market is obliged to rebalance, which is why it is a high-probability target
and why the win rate is high. The EXTERNAL draw is a resting pool of stops -- equal highs/lows,
old session extremes -- which only gets reached when the higher-timeframe bias agrees. That
split is the whole reason the model survives a wrong bias: you bank the internal draw at ~1R and
the runner to external is a free option.

CAUSALITY. Every level is fixed before the bar it is used on. Fair value gaps are only visible
once their third bar has CLOSED, so a 15m gap is not tradeable until the 15m bar completes --
the code holds them until then rather than at formation. Entries fill at the NEXT 1m open after
the inverting close, never at the closing price itself. Both are places this project has
previously manufactured an edge out of nothing.

    python -m scripts.pb_blake [--from 2023-01-01] [--to 2026-12-31] [--csv out.csv]
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
# Searched HIGHEST-FIRST, so a 15m gap still wins when one exists -- 1m/2m are only reached
# when nothing larger is present in the leg. Blake sets 3m as his floor, but that floor alone
# was rejecting 3.57 AM setups per day, by far the largest leak in the funnel, and Angus traded
# 1m/2m gaps directly. The floor is his preference, not a property of the market.
FVG_TFS = (15, 10, 5, 3, 2, 1)
RTH = (9 * 60 + 30, 16 * 60)
WINDOWS = ((9 * 60 + 30, 11 * 60 + 10), (13 * 60, 15 * 60))
LEG_LOOKBACK = 120                    # minutes back from the sweep to frame the leg
SCAN_START = 4 * 60                   # bars are built from 04:00, NOT 09:30 -- see below
MIN_STOP_PTS = 2.0                    # a stop tighter than this is noise, not a level
MAX_STOP_PTS = 60.0
MIN_TP1_R = 1.0                       # "if it's a one one" -- the internal draw must pay 1R
PIVOT_K = 5                           # fractal half-width for the swing-structure test


def load() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
                   for p in BARS], ignore_index=True)
    b = b.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    t = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b["day"] = t.dt.strftime("%Y-%m-%d")
    b["hm"] = t.dt.hour * 60 + t.dt.minute
    return b


def tf_fvgs(o: np.ndarray, h: np.ndarray, lo: np.ndarray, tf: int) -> list[dict]:
    """Fair value gaps on a tf-minute view of a 1m series anchored at SCAN_START.

    Anchoring at 09:30 instead meant no 15m gap could exist before 10:15, so the 09:30-11:10
    window -- Blake's primary one -- produced almost nothing and the earliest entry in the whole
    book was 10:04. 04:00 is divisible by 3/5/10/15, so the resampled bars stay clock-aligned.

    `ready` is the 1m index at which the gap becomes KNOWN -- the close of its third bar. Using
    the formation index instead would let the model trade a 15m gap up to 14 minutes before that
    gap exists, which is exactly the kind of head start that has faked an edge here before."""
    n = len(h) // tf * tf
    if n < tf * 3:
        return []
    H = h[:n].reshape(-1, tf).max(1)
    L = lo[:n].reshape(-1, tf).min(1)
    out = []
    for i in range(2, len(H)):
        ready = (i + 1) * tf - 1                       # last 1m bar of the third tf bar
        if L[i] > H[i - 2]:
            out.append({"tf": tf, "dir": "bull", "top": float(L[i]),
                        "bottom": float(H[i - 2]), "ready": ready})
        if H[i] < L[i - 2]:
            out.append({"tf": tf, "dir": "bear", "top": float(L[i - 2]),
                        "bottom": float(H[i]), "ready": ready})
    return out


def in_window(hm: int) -> bool:
    return any(a <= hm < b for a, b in WINDOWS)


def pivots(h: np.ndarray, lo: np.ndarray, k: int = PIVOT_K) -> tuple[np.ndarray, np.ndarray]:
    """Confirmed fractal pivots. Index i is only a pivot once k bars have printed AFTER it, so
    the arrays returned are 'known at bar i+k', and the caller must respect that."""
    n = len(h)
    ph = np.zeros(n, bool)
    pl = np.zeros(n, bool)
    for i in range(k, n - k):
        if h[i] == h[i - k:i + k + 1].max():
            ph[i] = True
        if lo[i] == lo[i - k:i + k + 1].min():
            pl[i] = True
    return ph, pl


def build_pools(b: pd.DataFrame, days: list[str]) -> dict[str, dict]:
    """Significant liquidity pools per day, all from bars strictly before 09:30 that day."""
    rth = b[(b.hm >= RTH[0]) & (b.hm < RTH[1])]
    S = rth.groupby("day").agg(h=("high", "max"), l=("low", "min"))
    prevh = S.h.shift(1)
    prevl = S.l.shift(1)
    on = b[(b.hm >= 18 * 60) | (b.hm < RTH[0])]
    # overnight belongs to the NEXT session when it is the evening block
    onday = np.where(on.hm.to_numpy() >= 18 * 60,
                     pd.to_datetime(on.day).to_numpy() + np.timedelta64(1, "D"),
                     pd.to_datetime(on.day).to_numpy())
    on = on.assign(sess=pd.to_datetime(onday).strftime("%Y-%m-%d"))
    ON = on.groupby("sess").agg(h=("high", "max"), l=("low", "min"))
    ldn = b[(b.hm >= 3 * 60) & (b.hm < RTH[0])]
    LD = ldn.groupby("day").agg(h=("high", "max"), l=("low", "min"))

    pools = {}
    for d in days:
        p = {}
        if d in prevh.index and not np.isnan(prevh.get(d, np.nan)):
            p["PDH"], p["PDL"] = float(prevh[d]), float(prevl[d])
        if d in ON.index:
            p["ONH"], p["ONL"] = float(ON.h[d]), float(ON.l[d])
        if d in LD.index:
            p["LDNH"], p["LDNL"] = float(LD.h[d]), float(LD.l[d])
        pools[d] = p
    return pools


FUNNEL: dict[str, int] = {}


def _f(k: str) -> None:
    FUNNEL[k] = FUNNEL.get(k, 0) + 1


def run_day(g: pd.DataFrame, pools: dict, stop_rule: str = "swept",
            min_tp1_r: float = MIN_TP1_R) -> list[dict]:
    o = g.open.to_numpy(float)
    h = g.high.to_numpy(float)
    lo = g.low.to_numpy(float)
    c = g.close.to_numpy(float)
    hm = g.hm.to_numpy(int)
    n = len(h)
    if n < 60:
        return []

    ph, pl = pivots(h, lo)
    gaps = [x for tf in FVG_TFS for x in tf_fvgs(o, h, lo, tf)]
    gaps.sort(key=lambda x: x["ready"])

    trades: list[dict] = []
    used_pool: set[str] = set()

    for t in range(20, n - 5):
        if not in_window(hm[t]):
            continue                                   # entries are window-bound; bars are not
        # AM extremes become a pool for the afternoon window only
        p = dict(pools)
        if hm[t] >= WINDOWS[1][0]:
            am = (hm >= WINDOWS[0][0]) & (hm < 11 * 60)
            if am.any():
                p["AMH"], p["AML"] = float(h[am].max()), float(lo[am].min())

        for side in ("long", "short"):
            # ---- 1. sweep of a significant pool: the FIRST bar to penetrate it ----
            # Requiring the sweep bar to also be the session extreme cut this to 25 trades in
            # four years. A sweep is a level being taken, not a record being set; price re-arms
            # the level by closing back inside it, which the `t-1` test enforces.
            hit = None
            for name, lvl in p.items():
                key = f"{name}{'L' if side == 'long' else 'S'}"
                if key in used_pool:
                    continue
                if side == "long" and name.endswith("L") and lo[t] < lvl <= lo[t - 1]:
                    hit = (name, lvl)
                if side == "short" and name.endswith("H") and h[t] > lvl >= h[t - 1]:
                    hit = (name, lvl)
                if hit:
                    break
            if hit is None:
                continue
            name, lvl = hit
            am = hm[t] < 12 * 60
            if am:
                _f("1. sweep of a pool detected")

            # ---- 1b. STRUCTURE: swing low -> swing high -> lower low ----
            # Blake's first stated requirement, and the one that separates his setup from a
            # plain breakdown: the sweep has to be the SECOND leg down, after the market has
            # already based and rallied. Without it the model catches first-leg breakdowns,
            # which simply continue -- that alone took the win rate from 28% territory.
            # Pivots are only used once confirmed (index + PIVOT_K <= t), so no lookahead.
            if side == "long":
                pl_i = np.flatnonzero(pl[:max(0, t - PIVOT_K)])
                ph_i = np.flatnonzero(ph[:max(0, t - PIVOT_K)])
                prior = [i for i in pl_i if lo[i] > lo[t]]        # a low we have now broken
                if not prior or not [j for j in ph_i if j > prior[-1]]:
                    if am:
                        _f("2. REJECTED no swing-low/high/lower-low structure")
                    continue
            else:
                ph_i = np.flatnonzero(ph[:max(0, t - PIVOT_K)])
                pl_i = np.flatnonzero(pl[:max(0, t - PIVOT_K)])
                prior = [i for i in ph_i if h[i] < h[t]]
                if not prior or not [j for j in pl_i if j > prior[-1]]:
                    if am:
                        _f("2. REJECTED no swing-low/high/lower-low structure")
                    continue

            # ---- 2/3. highest-timeframe gap in the sweep leg, re-checked each bar ----
            lg = max(0, t - LEG_LOOKBACK)
            leg_start = lg + int(np.argmax(h[lg:t + 1]) if side == "long"
                                 else np.argmin(lo[lg:t + 1]))
            want = "bear" if side == "long" else "bull"
            leg = [x for x in gaps if x["dir"] == want and x["ready"] >= leg_start]

            # ---- 4. wait for the inversion, fill at the NEXT open ----
            ext = lo[t] if side == "long" else h[t]
            ent_i, cand = None, None
            for u in range(t + 1, min(t + 90, n - 1)):
                if side == "long" and lo[u] < ext:
                    ext = lo[u]
                if side == "short" and h[u] > ext:
                    ext = h[u]
                if abs(ext - lvl) > MAX_STOP_PTS:         # ran away; this is not a sweep
                    break
                # the gap has to have CLOSED to be visible, so re-pick the highest tf each bar
                vis = [x for x in leg if x["ready"] <= u]
                cur = None
                for tf in FVG_TFS:                        # highest timeframe first, rule 3
                    m = [x for x in vis if x["tf"] == tf]
                    if m:
                        cur = m[-1]
                        break
                if cur is None:
                    continue
                edge = cur["top"] if side == "long" else cur["bottom"]
                if (side == "long" and c[u] > edge) or (side == "short" and c[u] < edge):
                    ent_i, cand = u + 1, cur
                    break
            if am:
                _f("3. structure ok")
            if ent_i is None:
                if am:
                    _f("4. REJECTED no inversion of a >=3m leg gap within 90min")
                continue
            if ent_i >= n - 2 or not in_window(hm[ent_i]):
                if am:
                    _f("5. REJECTED inversion landed outside the trade window")
                continue
            if am:
                _f("6. inversion found")

            entry = o[ent_i]
            # STOP RULE. "swept" is the literal reading -- stop at the swept extreme. But by the
            # time a 15m gap inverts, price has travelled a long way off that low, so the risk
            # balloons (median 23.5pt) and the target moves out of reach. Blake also says "I'll
            # put my stop loss probably at a closure above or whatever", i.e. a structural stop
            # local to the entry. Both are tested rather than assumed.
            if stop_rule == "swept":
                ref = ext
            elif stop_rule == "gap":                      # far edge of the gap being inverted
                ref = cand["bottom"] if side == "long" else cand["top"]
            else:                                          # local swing before entry
                w = slice(max(0, ent_i - 15), ent_i)
                ref = float(lo[w].min()) if side == "long" else float(h[w].max())
                ref = max(ref, ext) if side == "long" else min(ref, ext)
            stop = (ref - TICK) if side == "long" else (ref + TICK)
            risk = abs(entry - stop)
            if not (MIN_STOP_PTS <= risk <= MAX_STOP_PTS):
                if am:
                    _f("7. REJECTED risk outside 2-60pt")
                continue

            # ---- 5. internal draw: nearest UNMITIGATED gap beyond entry ----
            # The NEAREST unmitigated gap is usually a 3m sitting a few points away, which pays
            # 0.3R against 1R of risk and cannot win however high the hit rate is. Blake states
            # the rule himself: "you're not going to get that good of risk with a three minute...
            # usually going to be one to one with unfilled 15 minutes". So: nearest gap that is
            # at least MIN_TP1_R away. That is a stated rule of the model, not a fitted cut.
            live = sorted((x for x in gaps if x["ready"] <= ent_i),
                          key=lambda x: (x["bottom"] - entry) if side == "long"
                          else (entry - x["top"]))
            tgt = None
            for x in live:
                near = x["bottom"] if side == "long" else x["top"]
                if (near <= entry) if side == "long" else (near >= entry):
                    continue
                if abs(near - entry) / risk < min_tp1_r:
                    continue
                seg = slice(x["ready"] + 1, ent_i + 1)
                touched = (h[seg] >= near).any() if side == "long" else (lo[seg] <= near).any()
                if touched:
                    continue                              # already mitigated -- rule 5
                tgt = (near, x["top"] if side == "long" else x["bottom"], x["tf"])
                break
            if tgt is None:
                if am:
                    _f("8. REJECTED no unmitigated FVG target beyond entry")
                continue
            if am:
                _f("9. TRADE TAKEN")

            # ---- 6. external draw: the opposing significant pool ----
            cands = [v for k, v in p.items()
                     if (v > entry if side == "long" else v < entry)]
            extern = (min(cands) if side == "long" else max(cands)) if cands else None

            # ---- resolve the path, bar by bar, in order ----
            tp1 = tgt[0]
            r_tp1 = abs(tp1 - entry) / risk
            # ---- FEATURES, everything knowable at or before bar ent_i and nothing after ----
            atr = float(np.mean(h[max(0, ent_i - 60):ent_i] - lo[max(0, ent_i - 60):ent_i])) or 1.0
            gsz = abs(cand["top"] - cand["bottom"])
            sweep_depth = (lvl - ext) if side == "long" else (ext - lvl)
            pre = slice(max(0, ent_i - 20), ent_i)
            day_hi = float(h[:ent_i].max())
            day_lo = float(lo[:ent_i].min())
            rng = max(day_hi - day_lo, 1e-9)
            inv = ent_i - 1                                # the bar whose close inverted the gap
            confl = sum(1 for k, v in p.items()
                        if (k.endswith("L") if side == "long" else k.endswith("H"))
                        and abs(v - lvl) <= atr * 0.5)
            n_above = sum(1 for x in gaps if x["ready"] <= ent_i
                          and ((x["bottom"] > entry) if side == "long" else (x["top"] < entry)))
            res = {"day": g.day.iloc[0], "side": side, "pool": name, "tf": cand["tf"],
                   "tp_tf": tgt[2], "hm": int(hm[ent_i]), "entry": entry, "stop": stop,
                   "risk": risk, "tp1": tp1, "r_tp1": r_tp1,
                   "extern_R": (abs(extern - entry) / risk) if extern else np.nan,
                   "ent_i": ent_i, "sweep_i": t,
                   # -- setup geometry
                   "atr60": atr, "risk_atr": risk / atr,
                   "gap_pts": gsz, "gap_atr": gsz / atr,
                   "sweep_depth": sweep_depth, "sweep_depth_atr": sweep_depth / atr,
                   "bars_to_entry": ent_i - t,
                   "travel_atr": abs(entry - ext) / atr,
                   "travel_per_bar": abs(entry - ext) / max(ent_i - t, 1),
                   "confluence": confl, "n_gaps_ahead": n_above,
                   "window": "AM" if hm[ent_i] < 12 * 60 else "PM",
                   "trade_no": len(trades) + 1,
                   # -- where in the day's range the entry sits
                   "pos_in_day": (entry - day_lo) / rng,
                   "day_rng_atr": rng / atr,
                   # -- the inverting bar itself
                   "inv_body": abs(c[inv] - o[inv]) / max(h[inv] - lo[inv], 1e-9),
                   "inv_range_atr": (h[inv] - lo[inv]) / atr,
                   "inv_close_pos": (c[inv] - lo[inv]) / max(h[inv] - lo[inv], 1e-9),
                   # -- momentum into the entry
                   "mom5_atr": (c[ent_i - 1] - c[max(0, ent_i - 6)]) / atr *
                               (1 if side == "long" else -1),
                   "mom15_atr": (c[ent_i - 1] - c[max(0, ent_i - 16)]) / atr *
                                (1 if side == "long" else -1),
                   "pre_rng_atr": float(h[pre].max() - lo[pre].min()) / atr}
            hit_tp1 = stopped = False
            r_max = 0.0
            for u in range(ent_i, n):
                fav = (h[u] - entry) / risk if side == "long" else (entry - lo[u]) / risk
                adv = (entry - lo[u]) / risk if side == "long" else (h[u] - entry) / risk
                r_max = max(r_max, fav)
                tp_touch = (h[u] >= tp1) if side == "long" else (lo[u] <= tp1)
                st_touch = (lo[u] <= stop) if side == "long" else (h[u] >= stop)
                if st_touch and not hit_tp1:
                    stopped = True
                    break
                if tp_touch:
                    hit_tp1 = True
                    if extern is not None:
                        ex_touch = (h[u] >= extern) if side == "long" else (lo[u] <= extern)
                        if ex_touch:
                            res["exit"] = "external"
                            break
                    continue
                if hit_tp1 and adv >= 0.0:                # runner stopped at break even
                    res["exit"] = "be_after_tp1"
                    break
            else:
                res["exit"] = "eod"
            res.setdefault("exit", "external" if hit_tp1 else "stop")
            res["tp1_hit"] = bool(hit_tp1)
            res["stopped"] = bool(stopped)
            res["r_max"] = r_max
            # P&L: bank the internal draw, runner is the free option
            if stopped:
                res["R"] = -1.0
            elif res["exit"] == "external":
                res["R"] = 0.5 * r_tp1 + 0.5 * res["extern_R"]
            elif hit_tp1:
                res["R"] = 0.5 * r_tp1
            else:
                res["R"] = -1.0 if not hit_tp1 else 0.0
            trades.append(res)
            used_pool.add(f"{name}{'L' if side == 'long' else 'S'}")
    return trades


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="d0", default="2023-01-01")
    ap.add_argument("--to", dest="d1", default="2026-12-31")
    ap.add_argument("--csv", default="output/pb_blake_trades.csv")
    ap.add_argument("--stop", default="swept", choices=("swept", "gap", "local"))
    ap.add_argument("--min-tp1-r", dest="min_tp1_r", type=float, default=MIN_TP1_R)
    a = ap.parse_args()

    b = load()
    days = sorted(b.day.unique())
    pools = build_pools(b, days)
    scan = b[(b.hm >= SCAN_START) & (b.hm < RTH[1])]

    trades = []
    for d, g in scan.groupby("day", sort=True):
        if not (a.d0 <= d <= a.d1) or d not in pools or not pools[d]:
            continue
        trades += run_day(g.reset_index(drop=True), pools[d], a.stop, a.min_tp1_r)

    T = pd.DataFrame(trades)
    if T.empty:
        print("no trades")
        return 1
    T["year"] = T.day.str[:4]
    Path(ROOT / a.csv).parent.mkdir(parents=True, exist_ok=True)
    T.to_csv(ROOT / a.csv, index=False)

    def book(x: pd.DataFrame, label: str) -> None:
        w = (x.R > 0).mean()
        pf = x.R[x.R > 0].sum() / max(-x.R[x.R < 0].sum(), 1e-9)
        print(f"{label:14} n={len(x):5d}  win={w:5.1%}  PF={pf:5.2f}  "
              f"avgR={x.R.mean():+.3f}  tp1={x.tp1_hit.mean():5.1%}  "
              f"medR_tp1={x.r_tp1.median():4.2f}  ext={(x.exit == 'external').mean():5.1%}")

    print(f"\nPB BLAKE MECHANICAL MODEL — {len(T):,} trades, "
          f"{T.day.nunique()} days, {len(T)/T.day.nunique():.2f}/day\n")
    book(T, "ALL")
    print()
    for y, x in T.groupby("year"):
        book(x, y)
    print()
    for s, x in T.groupby("side"):
        book(x, s)
    print()
    for tf, x in T.groupby("tf"):
        book(x, f"entry {tf}m FVG")
    print()
    for p, x in T.groupby("pool"):
        book(x, f"pool {p}")
    print(f"\nwrote {a.csv}")
    nd = T.day.nunique()
    print(f"\nAM FUNNEL — where setups die, per trading day ({nd} days)")
    for k in sorted(FUNNEL):
        print(f"   {k:52} {FUNNEL[k]:6d}   {FUNNEL[k]/nd:5.2f}/day")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
