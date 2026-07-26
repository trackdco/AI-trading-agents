#!/usr/bin/env python3
"""TREND PULLBACK x HTF DRAW — final locked protocol. NET of costs. NQ 2023 -> 2026-07-15.

PRE-REGISTERED (before test is touched):
  PRIMARY  = "+draw target" (no filter): target = nearest UNTAPPED pool locked AT ENTRY;
             no pool in direction -> fallback 3R (fallback share logged). Verdict judged HERE.
  SECONDARY (exploratory): "+draw filter" (3R), "+draw filter + draw target".
  CONTROL  = base (fixed 3R).
  TIMEFRAME RULE: M15 train filtered-N >= 60 -> M15 only; else M5 added BEFORE scoring test.
  COSTS: 1 tick adverse slip each side + $5 RT commission -> all figures NET (R after cost).
  POOLS (a priori, <=-now): prior-day RTH H/L, prior-week RTH H/L, premarket H/L (00:00-09:40),
  overnight H/L (prior 16:00 -> 09:30). Untapped = not traded through since 09:30 up to trigger.
  Target locked at entry; never re-selected. Report % of draw targets < 1R.
  Split: train 2023-24 / test 2025->now ONCE; folds 25H1/25H2/26H1; counter-baseline; placebo.
  User sub-window report: 2026-02-01 -> 2026-07-15.
"""
import json
import math
from datetime import time as dtime, timedelta

import numpy as np
import pandas as pd

import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
NY = "America/New_York"
TRAIN_END = "2024-12-31"
TICK, PV, COMM = 0.25, 20.0, 5.0
rng = np.random.default_rng(42)

print("=" * 80 + "\nTREND PULLBACK x HTF DRAW — locked protocol, NET of costs\n" + "=" * 80)
bars = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts").reset_index(drop=True)
bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")
bars["t"] = bars["ts"].dt.time

# ---------------- per-day pool sets (all completed / frozen <= 09:40) ----------------
rthhl = {}
for d, g in bars.groupby("day"):
    r = g[(g.t >= dtime(9, 30)) & (g.t < dtime(16, 0))]
    if len(r) >= 100:
        rthhl[d] = (float(r.high.max()), float(r.low.min()))
allday = sorted(set(bars.day))
POOLS = {}
last_rth, last_week_hl, cur_week, cur_hi, cur_lo = None, None, None, -1e18, 1e18
prev_day_bars = {d: g for d, g in bars.groupby("day")}
for d in allday:
    iso = pd.Timestamp(d).isocalendar()
    wk = (iso.year, iso.week)
    if cur_week is not None and wk != cur_week and cur_hi > -1e17:
        last_week_hl = (cur_hi, cur_lo); cur_hi, cur_lo = -1e18, 1e18
    if cur_week != wk:
        cur_week = wk
    pools = {}
    if last_rth is not None:
        pools["PDH"], pools["PDL"] = rthhl[last_rth]
    if last_week_hl is not None:
        pools["PWH"], pools["PWL"] = last_week_hl
    g = prev_day_bars[d]
    pm = g[g.t < dtime(9, 40)]
    if len(pm):
        pools["PMH"], pools["PML"] = float(pm.high.max()), float(pm.low.min())
    # overnight: prior day >=16:00 + today <09:30
    dprev = (pd.Timestamp(d) - timedelta(days=1)).strftime("%Y-%m-%d")
    on_h, on_l = -1e18, 1e18
    if dprev in prev_day_bars:
        pg = prev_day_bars[dprev]; pgn = pg[pg.t >= dtime(16, 0)]
        if len(pgn):
            on_h, on_l = max(on_h, float(pgn.high.max())), min(on_l, float(pgn.low.min()))
    tg = g[g.t < dtime(9, 30)]
    if len(tg):
        on_h, on_l = max(on_h, float(tg.high.max())), min(on_l, float(tg.low.min()))
    if on_h > -1e17:
        pools["ONH"], pools["ONL"] = on_h, on_l
    POOLS[d] = pools
    if d in rthhl:
        last_rth = d
        cur_hi, cur_lo = max(cur_hi, rthhl[d][0]), min(cur_lo, rthhl[d][1])

def build_frame(tf):
    m = bars.set_index("ts").resample(tf, label="right", closed="right").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"])
    m["day"] = m.index.strftime("%Y-%m-%d"); m["t"] = m.index.time
    for p in (20, 50, 200):
        m[f"ma{p}"] = m.close.rolling(p).mean()
    m["vol_maN"] = m.volume.rolling(10).mean().shift(1)
    m["swing_lo5"] = m.low.rolling(5).min(); m["swing_hi5"] = m.high.rolling(5).max()
    rthm = (m.t >= dtime(9, 30))
    hi = m.high.where(rthm); lo = m.low.where(rthm)
    m["dev_hi"] = hi.groupby(m.day).cummax(); m["dev_lo"] = lo.groupby(m.day).cummin()
    return m.reset_index().rename(columns={"index": "ts"}).dropna(subset=["ma200"]).reset_index(drop=True)

def run_tf(tfname, tf):
    M = build_frame(tf)
    a = {c: M[c].values for c in ["open", "high", "low", "close", "ma20", "ma50", "ma200",
                                  "vol_maN", "swing_lo5", "swing_hi5", "dev_hi", "dev_lo", "volume"]}
    day_a = M.day.values; t_a = M.t.values
    rth = np.array([dtime(9, 30) <= t <= dtime(15, 0) for t in t_a])
    trigs = []
    for i in range(1, len(M)):
        if not rth[i] or np.isnan(a["vol_maN"][i]) or a["vol_maN"][i] <= 0:
            continue
        if a["volume"][i] >= 1.0 * a["vol_maN"][i]:
            continue
        up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
        dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
        if up and a["low"][i] <= a["ma50"][i] and a["close"][i] > a["ma50"][i]:
            trigs.append((i, 1))
        elif dn and a["high"][i] >= a["ma50"][i] and a["close"][i] < a["ma50"][i]:
            trigs.append((i, -1))

    def pick_target(i, dr, px):
        """nearest untapped pool beyond px in dir dr, locked at entry decision (bar i close)."""
        pl = POOLS.get(day_a[i], {})
        if dr > 0:
            c = [v for k, v in pl.items() if k in ("PDH", "PWH", "PMH", "ONH")
                 and v > px and (np.isnan(a["dev_hi"][i]) or a["dev_hi"][i] < v)]
            return min(c) if c else None
        c = [v for k, v in pl.items() if k in ("PDL", "PWL", "PML", "ONL")
             and v < px and (np.isnan(a["dev_lo"][i]) or a["dev_lo"][i] > v)]
        return max(c) if c else None

    def resolve(i, dr, mode, invert=False):
        """mode: '3r' or 'draw'. returns (netR, target_R, used_draw) or None."""
        if i + 1 >= len(M) or day_a[i + 1] != day_a[i]:
            return None
        ed = -dr if invert else dr
        entry = a["open"][i + 1] + ed * TICK
        if invert:
            ref = a["swing_hi5"][i] if dr > 0 else a["swing_lo5"][i]; risk = abs(ref - entry)
        else:
            ref = min(a["swing_lo5"][i], a["ma50"][i]) if dr > 0 else max(a["swing_hi5"][i], a["ma50"][i])
            risk = abs(entry - ref) + TICK
        if risk < 5 or risk > 70:
            return None
        used_draw = False
        if mode == "draw":
            tgt_px = pick_target(i, ed if not invert else ed, entry) if not invert else pick_target(i, ed, entry)
            if tgt_px is not None:
                used_draw = True
            else:
                tgt_px = entry + ed * 3 * risk
        else:
            tgt_px = entry + ed * 3 * risk
        tgtR = abs(tgt_px - entry) / risk
        stop = entry - ed * risk
        j = i + 1
        pts = None
        while j < len(M) and day_a[j] == day_a[i]:
            if t_a[j] >= dtime(15, 55):
                pts = ed * (a["close"][j] - entry) - TICK; break
            hs = (a["low"][j] <= stop) if ed > 0 else (a["high"][j] >= stop)
            ht = (a["high"][j] >= tgt_px) if ed > 0 else (a["low"][j] <= tgt_px)
            if hs:
                pts = -(risk + TICK); break
            if ht:
                pts = abs(tgt_px - entry) - TICK; break
            j += 1
        if pts is None:
            pts = ed * (a["close"][min(j, len(M) - 1) - (0 if j < len(M) else 1)] - entry) - TICK
        netR = (pts * PV - COMM) / (risk * PV)
        return netR, tgtR, used_draw

    recs = []
    for i, dr in trigs:
        has_draw = pick_target(i, dr, a["close"][i]) is not None
        r3 = resolve(i, dr, "3r")
        rdw = resolve(i, dr, "draw")
        rc = resolve(i, dr, "draw", invert=True)
        if r3 is None or rdw is None:
            continue
        recs.append(dict(tf=tfname, i=i, day=day_a[i], dir=dr, train=day_a[i] <= TRAIN_END,
                         has_draw=has_draw, base=r3[0], draw=rdw[0], drawR=rdw[1],
                         used_draw=rdw[2], ctr=rc[0] if rc else np.nan))
    return pd.DataFrame(recs), M, a, day_a, t_a, rth, resolve

def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; dd = 1 + z * z / n; c = (p + z * z / (2 * n)) / dd
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / dd
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))

def boot_ci(v):
    if len(v) == 0:
        return (0.0, 0.0)
    bm = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(2000)]
    return (round(float(np.percentile(bm, 2.5)), 3), round(float(np.percentile(bm, 97.5)), 3))

def stat_line(v):
    n = len(v)
    if n == 0:
        return dict(n=0)
    k = int((v > 0).sum())
    gp = v[v > 0].sum(); gl = -v[v < 0].sum()
    eq = np.cumsum(v); mdd = float((np.maximum.accumulate(eq) - eq).max())
    return dict(n=n, expR=round(float(v.mean()), 3), ci=boot_ci(v),
                win=round(100 * k / n, 1), win_ci=wilson(k, n),
                pf=round(float(gp / gl), 2) if gl > 0 else 999.0, mddR=round(mdd, 1))

# ---------------- timeframe rule (train only) ----------------
RC15, M15, a15, day15, t15, rth15, res15 = run_tf("M15", "15min")
train_filtered_n = int((RC15.train & RC15.has_draw).sum())
print(f"\nTIMEFRAME RULE: M15 train filtered-N (draw exists) = {train_filtered_n} "
      f"(threshold 60) -> {'M15 only' if train_filtered_n >= 60 else 'ADD M5 (pre-registered)'}")
frames = [("M15", RC15)]
if train_filtered_n < 60:
    RC5, *_ = run_tf("M5", "5min")
    frames.append(("M5", RC5))

VAR = [("base 3R (control)", "base", None),
       ("+draw target (PRIMARY)", "draw", None),
       ("+draw filter, 3R (secondary)", "base", "has_draw"),
       ("+draw filter+target (secondary)", "draw", "has_draw")]
results = {}
for tfname, RC in frames:
    te = ~RC.train
    print(f"\n===== {tfname}: {len(RC)} triggers ({int(RC.train.sum())} train / {int(te.sum())} test) =====")
    dtr = RC[RC.used_draw & te]
    sub1r = 100 * float((dtr.drawR < 1).mean()) if len(dtr) else 0
    print(f"  draw targets <1R at entry (test): {sub1r:.0f}%   fallback-to-3R share (test): "
          f"{100 * float((~RC[te].used_draw).mean()):.0f}%")
    results[tfname] = {}
    for label, col, filt in VAR:
        for split, mask in [("TRAIN", RC.train), ("TEST", te)]:
            sub = RC[mask & (RC[filt] if filt else True)]
            st = stat_line(sub[col].values)
            ctr = stat_line(sub.ctr.dropna().values)
            fold_txt = ""
            if split == "TEST" and st["n"]:
                fp = fv = 0
                for b0, b1 in [("2025-01-01", "2025-07-01"), ("2025-07-01", "2026-01-01"), ("2026-01-01", "2026-07-16")]:
                    f_ = sub[(sub.day >= b0) & (sub.day < b1)]
                    if len(f_) >= 10:
                        fv += 1; fp += int(f_[col].mean() > 0)
                fold_txt = f"  folds {fp}/{fv}"
            if st["n"]:
                print(f"  {label:32s} {split:5s} n={st['n']:3d}{'  LOW-N!' if st['n'] < 30 else ''} "
                      f"netE[R] {st['expR']:+.3f} CI{st['ci']}  win {st['win']}% CI{st['win_ci']}  "
                      f"PF {st['pf']}  maxDD {st['mddR']}R  ctr {ctr.get('expR', 'na')}{fold_txt}")
            results[tfname][f"{label}|{split}"] = dict(st=st, ctr=ctr)
        # user sub-window Feb->Jul 2026
        subw = RC[(RC.day >= "2026-02-01") & (RC.day <= "2026-07-15") & (RC[filt] if filt else True)]
        stw = stat_line(subw[col].values)
        if stw["n"]:
            print(f"  {label:32s} FEB-JUL26 n={stw['n']:3d}{' LOW-N!' if stw['n'] < 30 else ''} "
                  f"netE[R] {stw['expR']:+.3f} CI{stw['ci']}  win {stw['win']}%  PF {stw['pf']}")
        results[tfname][f"{label}|FEBJUL26"] = stat_line(subw[col].values)

# ---------------- placebo on the PRIMARY (per timeframe) ----------------
print("\n--- placebo: PRIMARY (+draw target) vs random bars in same stacked-MA regime (test) ---")
for tfname, RC in frames:
    if tfname == "M15":
        M_, a_, day_, t_, rth_, res_ = M15, a15, day15, t15, rth15, res15
    else:
        continue   # placebo on M15 (primary frame); M5 placebo skipped for runtime, noted
    te = ~RC.train
    real = RC[te].draw.mean()
    permL = [i for i in range(len(M_)) if rth_[i] and day_[i] > TRAIN_END
             and a_["ma20"][i] > a_["ma50"][i] > a_["ma200"][i] and a_["close"][i] > a_["ma50"][i]]
    permS = [i for i in range(len(M_)) if rth_[i] and day_[i] > TRAIN_END
             and a_["ma20"][i] < a_["ma50"][i] < a_["ma200"][i] and a_["close"][i] < a_["ma50"][i]]
    nL = int((RC[te].dir == 1).sum()); nS = int((RC[te].dir == -1).sum())
    sims = []
    for _ in range(200):
        pick = ([(int(x), 1) for x in rng.choice(permL, min(nL, len(permL)), replace=False)] +
                [(int(x), -1) for x in rng.choice(permS, min(nS, len(permS)), replace=False)])
        rr = [res_(i, d, "draw") for i, d in pick]
        rr = [x[0] for x in rr if x is not None]
        if rr:
            sims.append(np.mean(rr))
    pp = float((np.array(sims) >= real).mean()) if sims else 1.0
    print(f"  {tfname}: real net {real:+.3f} vs placebo {np.mean(sims):+.3f}  p={pp:.3f}  "
          f"({'trigger adds signal' if pp < 0.05 else 'regime, not trigger'})")
    results[tfname]["placebo_primary"] = dict(real=round(float(real), 3),
                                              placebo=round(float(np.mean(sims)), 3), p=round(pp, 3))

json.dump(results, open(f"{S}/tp_draw_final.json", "w"), default=str)
pd.concat([rc.assign(tf=n) for n, rc in frames]).to_csv(f"{S}/tp_draw_final_trades.csv", index=False)
print("\nsaved tp_draw_final.json / tp_draw_final_trades.csv")
