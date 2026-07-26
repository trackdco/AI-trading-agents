#!/usr/bin/env python3
"""LONDON-session Trend Pullback (stacked MA), raw price only. NQ M15, 2023 -> Jul 2026.

Setup (long; mirror for short):
  - clear trend: 20MA > 50MA > 200MA AND price above all three (M15 close)
  - trigger: bar WICKS the 50MA (low<=50ma) and CLOSES back above, with FADING volume
    (bar vol < mean(prior 10 bars))
  - bracket: stop = min(swing-low-5, 50ma) - 1 tick, clamp 5-70pt; target = 3R
  - entry: next M15 bar open + 1 tick slip; flatten unresolved at 09:25 ET (before NY open)
London trading window = fills in [03:00, 07:45) ET. NET of costs (2 ticks slip + $5 RT commission).
Split train 2023-24 / test 2025->now. Counter-baseline = same triggers, mirror direction.
Reports per year: net E[R], win rate (Wilson CI), PF, net $, maxDD, N. N<30 flagged.
"""
from datetime import time as dtime
import math
import numpy as np
import pandas as pd

NY = "America/New_York"
TICK, PV, COMM = 0.25, 20.0, 5.0
TRAIN_END = "2024-12-31"
LON_START, LON_END, FLAT = dtime(3, 0), dtime(7, 45), dtime(9, 25)
TG = 3.0

bars = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts").reset_index(drop=True)
m = bars.set_index("ts").resample("15min", label="right", closed="right").agg(
    open=("open", "first"), high=("high", "max"), low=("low", "min"),
    close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"])
m["day"] = m.index.strftime("%Y-%m-%d"); m["t"] = m.index.time
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["vol_maN"] = m.volume.rolling(10).mean().shift(1)
m["swing_lo5"] = m.low.rolling(5).min(); m["swing_hi5"] = m.high.rolling(5).max()
M = m.reset_index().rename(columns={"index": "ts"}).dropna(subset=["ma200"]).reset_index(drop=True)
a = {c: M[c].values for c in ["open", "high", "low", "close", "ma20", "ma50", "ma200",
                              "vol_maN", "volume", "swing_lo5", "swing_hi5"]}
day_a = M.day.values; t_a = M.t.values

trg = np.array([LON_START <= t < LON_END for t in t_a])
trigs = []
for i in range(1, len(M)):
    if not trg[i] or np.isnan(a["vol_maN"][i]) or a["vol_maN"][i] <= 0:
        continue
    if a["volume"][i] >= a["vol_maN"][i]:                   # require fading volume
        continue
    up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
    dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
    if up and a["low"][i] <= a["ma50"][i] and a["close"][i] > a["ma50"][i]:
        trigs.append((i, 1))
    elif dn and a["high"][i] >= a["ma50"][i] and a["close"][i] < a["ma50"][i]:
        trigs.append((i, -1))

def resolve(i, dr, invert=False):
    """returns (net_dollars, netR, risk) for 1 NQ; costs = 2 ticks slip + $5 RT."""
    if i + 1 >= len(M) or day_a[i + 1] != day_a[i]:
        return None
    ed = -dr if invert else dr
    entry = a["open"][i + 1] + ed * TICK                    # 1 tick entry slip
    if invert:
        ref = a["swing_hi5"][i] if dr > 0 else a["swing_lo5"][i]; risk = abs(ref - entry)
    else:
        ref = min(a["swing_lo5"][i], a["ma50"][i]) if dr > 0 else max(a["swing_hi5"][i], a["ma50"][i])
        risk = abs(entry - ref) + TICK
    if risk < 5 or risk > 70:
        return None
    stop = entry - ed * risk; tgt = entry + ed * TG * risk
    gross = None
    j = i + 1
    while j < len(M) and day_a[j] == day_a[i]:
        if t_a[j] >= FLAT:
            gross = ed * (a["close"][j] - entry); break
        hit_stop = (a["low"][j] <= stop) if ed > 0 else (a["high"][j] >= stop)
        hit_tgt = (a["high"][j] >= tgt) if ed > 0 else (a["low"][j] <= tgt)
        if hit_stop:
            gross = -risk - TICK; break                     # 1 tick exit slip
        if hit_tgt:
            gross = TG * risk - TICK; break
        j += 1
    if gross is None:
        gross = ed * (a["close"][min(j, len(M) - 1)] - entry)
    net = gross * PV - COMM                                  # $ (slip already in gross via ticks)
    return net, net / (risk * PV), risk

rec = []
for i, dr in trigs:
    r = resolve(i, dr); rc = resolve(i, dr, invert=True)
    if r is None:
        continue
    rec.append(dict(day=day_a[i], t=str(t_a[i]), dir=dr, net=r[0], R=r[1], risk=r[2],
                    train=day_a[i] <= TRAIN_END, ctrR=rc[1] if rc else np.nan,
                    ctr_net=rc[0] if rc else np.nan))
RC = pd.DataFrame(rec)
print("=" * 96)
print(f"LONDON Trend Pullback (M15, 03:00-07:45 ET fills)  |  {len(RC)} trades, "
      f"{RC.day.nunique()} days, {int(RC.train.sum())} train / {int((~RC.train).sum())} test")
print("=" * 96)

def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0)
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d; h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (round(100*(c-h)), round(100*(c+h)))

def stat(sub, col="R", ncol="net"):
    v = sub[col].values; n = len(v)
    if n == 0:
        return None
    net = sub[ncol].sum() if ncol in sub else v.sum()
    k = int((v > 0).sum())
    eq = np.cumsum(sub.sort_values("day")[ncol].values if ncol in sub else v)
    dd = float((np.maximum.accumulate(eq) - eq).max())
    gp = sub[sub[col] > 0][col].sum() if False else v[v > 0].sum(); gl = -v[v < 0].sum()
    return dict(n=n, eR=round(float(v.mean()), 3), wr=round(100*k/n, 1), wci=wilson(k, n),
                pf=round(float(gp/gl), 2) if gl > 0 else 999, net=round(float(net), 0), dd=round(dd, 0))

def show(label, sub):
    for split, mask in [("ALL", np.ones(len(sub), bool)), ("TRAIN 23-24", sub.train.values), ("TEST 25-26", ~sub.train.values)]:
        s = stat(sub[mask])
        if s:
            flag = "  LOW-N!" if s["n"] < 30 else ""
            print(f"  {label:16s} {split:11s} n={s['n']:4d}{flag}  netE[R] {s['eR']:+.3f}  "
                  f"WR {s['wr']}% CI{s['wci']}  PF {s['pf']}  net ${s['net']:+,.0f}  maxDD ${s['dd']:,.0f}")

print("\n-- ALL London trades --"); show("all", RC)
print("\n-- LONG only (uptrend pullback) --"); show("long", RC[RC.dir == 1])
print("\n-- SHORT only (downtrend) --"); show("short", RC[RC.dir == -1])

# counter-baseline (mirror direction, same triggers) on TEST
te = RC[~RC.train]
cb = stat(te.assign(R=te.ctrR, net=te.ctr_net).dropna(subset=["R"]))
mn = stat(te)
print("\n-- direction check (TEST) --")
print(f"  strategy net E[R] {mn['eR']:+.3f} (net ${mn['net']:+,.0f})  vs  counter-baseline "
      f"E[R] {cb['eR']:+.3f} (net ${cb['net']:+,.0f})")

# per-year net $ and vs the earlier RTH version for context
print("\n-- net $ by year --")
for yr in ("2023", "2024", "2025", "2026"):
    sub = RC[RC.day.str[:4] == yr]
    if len(sub):
        print(f"  {yr}: {len(sub):3d} trades  net ${sub.net.sum():+,.0f}  WR {100*(sub.R>0).mean():.0f}%")
RC.to_csv(f"{S}/london_tp_trades.csv", index=False)
print("\nNOTE: raw price-only test (no depth/heatmap in London). Costs net. Exploratory -> "
      "any edge needs the same holdout discipline as the desk's canon.")
