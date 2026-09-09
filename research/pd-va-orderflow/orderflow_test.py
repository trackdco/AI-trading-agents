#!/usr/bin/env python3
"""
PREREGISTRATION-4 engine: the video's order-flow entry sequence at prior-day value-area levels,
on the NQ footprint tape 2025-06 → 2026-07, eight readings plus the unfiltered baseline.
All definitions are in PREREGISTRATION-4.md; this file implements them and nothing else.
"""
import json
import statistics as st
import sys
from bisect import bisect_left, bisect_right
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ET = ZoneInfo("America/New_York")
HERE = __file__.rsplit("/", 1)[0]
BARS = f"{HERE}/data/nq_raw_1m_2025-05-26_2026-07-19.csv"
FP = [f"{HERE}/data/footprint/footprint_{n}.parquet" for n in ("q3_2025", "q4_2025", "jan2026", "feb_mar2026", "apr2026", "may_jul2026")]
TICK = 0.25; PT = 20.0; SLIP = 0.5; COMM_RT = 5.0
SEED = 20260909

# ── load bars ──────────────────────────────────────────────────────────────────────────────
b = pd.read_csv(BARS)
b["ts"] = pd.to_datetime(b["ts_event"], utc=True)
b = b.sort_values("ts").reset_index(drop=True)
et = b["ts"].dt.tz_convert(ET)
b["hm"] = et.dt.hour * 60 + et.dt.minute
b["cd"] = et.dt.date                       # calendar ET date
b["td"] = [(t + timedelta(days=1)).date() if t.hour >= 18 else t.date() for t in et]   # CME trading day
O, H, L, C = b["open"].values, b["high"].values, b["low"].values, b["close"].values
TS = b["ts"].values.astype("datetime64[ns]").astype(np.int64)
print(f"bars {len(b):,}  {b['ts'].iloc[0]} -> {b['ts'].iloc[-1]}", flush=True)

# ── load footprint ─────────────────────────────────────────────────────────────────────────
fp = pd.concat([pd.read_parquet(p) for p in FP], ignore_index=True)
fp["ts"] = pd.to_datetime(fp["ts_minute"], utc=True)
fp = fp.sort_values(["ts", "price"]).reset_index(drop=True)
FTS = fp["ts"].values.astype("datetime64[ns]").astype(np.int64)
FPR = fp["price"].values.astype(float); FSD = (fp["side"].values == "B"); FV = fp["volume"].values.astype(np.int64)
print(f"footprint cells {len(fp):,}  {fp['ts'].iloc[0]} -> {fp['ts'].iloc[-1]}", flush=True)
del fp


def cells(t0, t1):
    """index range of footprint cells with t0 <= ts < t1 (int64 ns)"""
    return bisect_left(FTS, t0), bisect_left(FTS, t1)


def profile(t0, t1):
    a, z = cells(t0, t1)
    if z <= a:
        return None
    pr = FPR[a:z]; v = FV[a:z]
    lo = int(round(pr.min() / TICK)); hi = int(round(pr.max() / TICK))
    prof = np.zeros(hi - lo + 1)
    np.add.at(prof, np.round(pr / TICK).astype(int) - lo, v)
    if prof.sum() <= 0:
        return None
    poc = int(np.argmax(prof)); target = 0.7 * prof.sum(); acc = prof[poc]; up = poc + 1; dn = poc - 1
    while acc < target and (up < len(prof) or dn >= 0):
        vu = prof[up] if up < len(prof) else -1; vd = prof[dn] if dn >= 0 else -1
        if vu >= vd: acc += vu; up += 1
        else: acc += vd; dn -= 1
    return {"poc": (poc + lo) * TICK, "val": (dn + 1 + lo) * TICK, "vah": (up - 1 + lo) * TICK}


def ns(dt):
    return int(pd.Timestamp(dt).value)


def minute_cells(i):
    """cells of bar i: (prices, is_buy, volumes)"""
    a, z = cells(TS[i], TS[i] + 60_000_000_000)
    return FPR[a:z], FSD[a:z], FV[a:z]


# ── sessions ───────────────────────────────────────────────────────────────────────────────
rth = (b["hm"] >= 570) & (b["hm"] < 960)
cash_days = sorted(b.loc[rth, "cd"].unique())
first_idx = {d: i for i, d in zip(b.index[rth], b.loc[rth, "cd"]) if d not in {}}  # first RTH bar per day (dict comp keeps last; fix below)
first_idx = {}
for i in b.index[rth]:
    d = b.at[i, "cd"]
    if d not in first_idx:
        first_idx[d] = i
last_idx = {}
for i in b.index[rth]:
    last_idx[b.at[i, "cd"]] = i


def cash_window_ns(d):
    t0 = datetime(d.year, d.month, d.day, 9, 30, tzinfo=ET); t1 = datetime(d.year, d.month, d.day, 16, 0, tzinfo=ET)
    return ns(t0), ns(t1)


def overnight_window_ns(d):
    t1 = datetime(d.year, d.month, d.day, 9, 30, tzinfo=ET); t0 = t1 - timedelta(hours=15, minutes=30)   # 18:00 previous evening
    return ns(t0), ns(t1)


def threshold(prev_days, pct):
    vals = []
    for d in prev_days:
        a, z = cells(*cash_window_ns(d))
        vals.append(FV[a:z])
    if not vals:
        return None
    v = np.concatenate(vals)
    return float(np.percentile(v, pct)) if len(v) else None


# ── simulation helpers ─────────────────────────────────────────────────────────────────────
def simulate(direction, entry, stop, target, start_i, end_i, entry_slip_paid):
    """walk bars start_i..end_i: stop first on ties; time exit at end_i close. returns (exit_px, reason, exit_i, net$)"""
    s = 1 if direction == "long" else -1
    for i in range(start_i, end_i + 1):
        if (s == 1 and L[i] <= stop) or (s == -1 and H[i] >= stop):
            px = stop - s * SLIP; reason = "stop"; break
        if target is not None and ((s == 1 and H[i] >= target) or (s == -1 and L[i] <= target)):
            px = target; reason = "target"; break
    else:
        i = end_i; px = C[end_i] - s * SLIP; reason = "time"
    gross = s * (px - entry) * PT
    net = gross - COMM_RT
    return px, reason, i, net


def first_on_target(direction, entry, stop, on):
    s = 1 if direction == "long" else -1
    r = abs(entry - stop)
    levels = sorted([on["val"], on["poc"], on["vah"]], reverse=(s == -1))
    for lv in levels:
        if s * (lv - entry) >= r:
            return lv, "on"
    return entry + s * 2 * r, "2R-fallback"


READINGS = [(t, e, x) for t in ("T-a", "T-b") for e in ("E-market", "E-limit") for x in ("X-on", "X-2R")]
trades = {rd: [] for rd in READINGS}
baseline = {"X-on": [], "X-2R": []}
counts = defaultdict(int)

for di, d in enumerate(cash_days):
    if di < 6:
        continue
    prev = cash_days[di - 1]
    pd_va = profile(*cash_window_ns(prev))
    on = profile(*overnight_window_ns(d))
    if not pd_va or not on:
        counts["days_skipped_no_profile"] += 1; continue
    Ts = {"T-a": threshold(cash_days[di - 5:di], 98), "T-b": threshold(cash_days[di - 5:di], 95)}
    if not Ts["T-a"]:
        continue
    i0, i1 = first_idx[d], last_idx[d]
    open_px = O[i0]
    bias = "bullish" if open_px > pd_va["vah"] else ("bearish" if open_px < pd_va["val"] else "neutral")
    setups = {"bullish": [("long", pd_va["vah"])], "bearish": [("short", pd_va["val"])],
              "neutral": [("short", pd_va["vah"]), ("long", pd_va["val"])]}[bias]
    counts[f"days_{bias}"] += 1
    entry_last = i0 + (930 - 570)          # 15:30 ET
    # per reading: position-busy-until index; attempts per level
    busy = {rd: -1 for rd in READINGS}; busy_b = {x: -1 for x in baseline}
    attempts = {rd: defaultdict(int) for rd in READINGS}; attempts_b = {x: defaultdict(int) for x in baseline}
    seen_side = {lv: False for _, lv in setups}
    for i in range(i0 + 1, entry_last + 1):
        for direction, level in setups:
            s = 1 if direction == "long" else -1
            # approach from the trade's side: some earlier bar closed beyond the level in the trade direction
            if not seen_side[level]:
                if s * (C[i - 1] - level) > 0 or s * (open_px - level) > 0:
                    seen_side[level] = True
                else:
                    continue
            tapped = L[i] <= level <= H[i]
            if not tapped:
                continue
            counts["taps"] += 1
            # ---- baseline (unfiltered) at this tap ----
            for x in baseline:
                if i <= busy_b[x] or attempts_b[x][level] >= 2:
                    continue
                attempts_b[x][level] += 1
                entry = C[i] + s * SLIP; stop = (L[i] - TICK) if s == 1 else (H[i] + TICK)
                if s * (entry - stop) <= 0:
                    continue
                target, tk = first_on_target(direction, entry, stop, on) if x == "X-on" else (entry + s * 2 * abs(entry - stop), "2R")
                px, reason, ei, net = simulate(direction, entry, stop, target, i + 1, i1, True)
                busy_b[x] = ei
                baseline[x].append({"day": str(d), "bias": bias, "direction": direction, "level": level, "entry_ts": str(b["ts"].iloc[i]),
                                    "entry": entry, "stop": stop, "target": target, "target_kind": tk, "exit": px, "reason": reason,
                                    "net": net, "R": net / (abs(entry - stop) * PT)})
            # ---- confirmed sequence ----
            for rd in READINGS:
                tkey, ekey, xkey = rd
                if i <= busy[rd] or attempts[rd][level] >= 2:
                    continue
                T = Ts[tkey]
                # absorption in bars i..i+4
                absorbed = None
                for j in range(i, min(i + 5, i1 + 1)):
                    pr, isb, v = minute_cells(j)
                    body_lo, body_hi = min(O[j], C[j]), max(O[j], C[j])
                    if s == 1:
                        m = (~isb) & (pr < body_lo) & (v >= T); ok_close = C[j] >= level
                    else:
                        m = (isb) & (pr > body_hi) & (v >= T); ok_close = C[j] <= level
                    if m.any() and ok_close:
                        absorbed = (j, pr[m].max() if s == 1 else pr[m].min()); break
                if absorbed is None:
                    continue
                j, cluster_edge = absorbed
                # aggression + imbalance + inversion in bars j+1..j+3
                sig = None
                for k in range(j + 1, min(j + 4, i1 + 1)):
                    if s * (C[k] - O[k]) <= 0:
                        continue
                    pr, isb, v = minute_cells(k)
                    body_lo, body_hi = min(O[k], C[k]), max(O[k], C[k])
                    inbody = (pr >= body_lo) & (pr <= body_hi)
                    own = inbody & (isb if s == 1 else ~isb) & (v >= T)
                    if not own.any():
                        continue
                    # imbalance: own volume at p >= 3 x opposing volume at the adjacent tick (p - tick for buys, p + tick for sells)
                    own_vol = defaultdict(float); opp_vol = defaultdict(float)
                    for p_, ib_, v_ in zip(pr, isb, v):
                        (own_vol if ib_ == (s == 1) else opp_vol)[round(p_, 2)] += v_
                    imb_prices = []
                    for p_ in own_vol:
                        if not (body_lo <= p_ <= body_hi):
                            continue
                        adj = round(p_ - s * TICK, 2)
                        ov = opp_vol.get(adj, 0.0)
                        if (ov > 0 and own_vol[p_] >= 3 * ov) or (ov == 0 and own_vol[p_] >= T):
                            imb_prices.append(p_)
                    if not imb_prices:
                        continue
                    inversion = (C[k] > cluster_edge) if s == 1 else (C[k] < cluster_edge)
                    if not inversion:
                        continue
                    sig = (k, max(imb_prices) if s == 1 else min(imb_prices)); break
                if sig is None:
                    continue
                k, imb_px = sig
                attempts[rd][level] += 1
                counts[f"signals_{tkey}"] += 1
                stop = (min(L[j:k + 1]) - TICK) if s == 1 else (max(H[j:k + 1]) + TICK)
                if ekey == "E-market":
                    if k + 1 > i1:
                        continue
                    entry = O[k + 1] + s * SLIP; fi = k + 1
                else:
                    fi = None
                    for f in range(k + 1, min(k + 11, i1 + 1)):
                        if (s == 1 and L[f] <= imb_px) or (s == -1 and H[f] >= imb_px):
                            fi = f; break
                    if fi is None:
                        counts[f"limit_unfilled_{tkey}"] += 1; busy[rd] = min(k + 10, i1); continue
                    entry = imb_px
                if s * (entry - stop) <= 0:
                    continue
                target, tk = first_on_target(direction, entry, stop, on) if xkey == "X-on" else (entry + s * 2 * abs(entry - stop), "2R")
                px, reason, ei, net = simulate(direction, entry, stop, target, fi, i1, ekey == "E-market")
                busy[rd] = ei
                trades[rd].append({"day": str(d), "bias": bias, "direction": direction, "level": level, "tap_ts": str(b["ts"].iloc[i]),
                                   "absorb_i": int(j - i), "signal_i": int(k - i), "entry_ts": str(b["ts"].iloc[fi]), "entry": entry,
                                   "stop": stop, "target": target, "target_kind": tk, "exit": px, "reason": reason, "net": net,
                                   "R": net / (abs(entry - stop) * PT), "T": Ts[tkey]})
    if di % 40 == 0:
        print(f"  {d}: taps {counts['taps']}, signals T-a {counts['signals_T-a']}, trades so far {[len(v) for v in trades.values()]}", flush=True)


# ── report ─────────────────────────────────────────────────────────────────────────────────
def boot_lb(tr):
    if len(tr) < 2:
        return None
    byday = defaultdict(list)
    for t in tr: byday[t["day"]].append(t["net"])
    days = list(byday); sums = np.array([sum(byday[d]) for d in days]); ns_ = np.array([len(byday[d]) for d in days])
    rng = np.random.Generator(np.random.PCG64(SEED)); m = []
    for _ in range(10000):
        ix = rng.integers(0, len(days), len(days)); m.append(sums[ix].sum() / ns_[ix].sum())
    return float(np.percentile(m, 5))


def summ(tr):
    if not tr:
        return "| 0 | | | | | | |"
    n = len(tr); net = [t["net"] for t in tr]; w = [x for x in net if x > 0]; l = [x for x in net if x < 0]
    cum = peak = dd = 0
    for x in net: cum += x; peak = max(peak, cum); dd = max(dd, peak - cum)
    lb = boot_lb(tr)
    return f"| {n} | {100*len(w)/n:.1f} | {st.mean(net):+.2f} | {st.mean(t['R'] for t in tr):+.3f} | {(sum(w)/-sum(l)) if l else float('inf'):.2f} | {lb:+.2f} | {dd:,.0f} |"


lines = ["# PREREGISTRATION-4 — results (footprint tape 2025-06 → 2026-07)\n",
         f"days: bullish {counts['days_bullish']}, bearish {counts['days_bearish']}, neutral {counts['days_neutral']}; level taps {counts['taps']}; "
         f"sequences found T-a {counts['signals_T-a']}, T-b {counts['signals_T-b']}; limit unfilled T-a {counts['limit_unfilled_T-a']}, T-b {counts['limit_unfilled_T-b']}\n",
         "| reading | n | WR% | mean net $ | mean R | PF | LB95 $ | max DD $ |", "|---|---|---|---|---|---|---|---|"]
for x in baseline:
    lines.append(f"| **baseline, unfiltered, {x}** " + summ(baseline[x]))
for rd in READINGS:
    lines.append(f"| {' / '.join(rd)} " + summ(trades[rd]))
lines.append("\n**By bias / direction (reading T-a / E-market / X-on and the X-on baseline)**\n\n| bias, direction | confirmed n | mean $ | WR% | baseline n | mean $ | WR% |\n|---|---|---|---|---|---|---|")
key = ("T-a", "E-market", "X-on")
for bias_, dir_ in (("bullish", "long"), ("bearish", "short"), ("neutral", "short"), ("neutral", "long")):
    c_ = [t for t in trades[key] if t["bias"] == bias_ and t["direction"] == dir_]; b_ = [t for t in baseline["X-on"] if t["bias"] == bias_ and t["direction"] == dir_]
    f_ = lambda x: (f"{len(x)} | {st.mean(t['net'] for t in x):+.2f} | {100*sum(1 for t in x if t['net']>0)/len(x):.0f}" if x else "0 | | ")
    lines.append(f"| {bias_}, {dir_} | {f_(c_)} | {f_(b_)} |")
ok_all = all(len(trades[rd]) and st.mean(t["net"] for t in trades[rd]) > 0 and (boot_lb(trades[rd]) or -1) > 0
             and st.mean(t["net"] for t in trades[rd]) > st.mean(t["net"] for t in baseline[rd[2]]) for rd in READINGS)
lines.append(f"\n**Verdict (§6, minimum across the eight readings): {'ORDER FLOW ADDS' if ok_all else 'NOT DEMONSTRATED'}**")
text = "\n".join(lines); print(text)
open(f"{HERE}/RESULTS-4.md", "w").write(text + "\n")
json.dump({"trades": {" / ".join(k): v for k, v in trades.items()}, "baseline": baseline, "counts": dict(counts)}, open(f"{HERE}/data/orderflow_trades.json", "w"), indent=1)
