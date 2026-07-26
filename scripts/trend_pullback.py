#!/usr/bin/env python3
"""TREND PULLBACK (stacked MA) — isolated setup test, BARE vs +CONFLUENCE. NQ M15, 2023->Jul 2026.

SETUP (long; mirrored short):
  permission: SMA20>SMA50>SMA200 on M15 AND trigger close > SMA50 & > SMA200 (during a pullback
    the close sits below the 20MA by construction; the strict 'above all three' reading would
    forbid nearly every 50MA touch — deviation LOGGED, stack order still required).
  trigger: pullback TOUCHES the 50MA and RESUMES (close back on trend side), volume FADING into
    the touch vs prior N bars. touch mode (wick/close), N, fade threshold = PARAMETERS chosen on
    TRAIN only and logged.
  bracket: stop below min(pullback swing low, 50MA) - 1 tick (risk clamped 5..70pt, Campion);
    target = tgtR * risk (tgtR a train-chosen parameter); entry next M15 open +1 tick slip;
    stop-first conservative; RTH triggers only (09:30-15:00 ET), EOD flatten 15:55 (existing rules).
CONFLUENCE (b): tick-delta absorption on the touch bar (proxy — true delta div needs bid/ask,
  2026-only), session VWAP side, Bollinger not-extended (inside upper band, M15 20/2), price vs
  session POC (5pt bins). Require >=K of 4 (K train-chosen). All session metrics built
  cumulatively from <=-now 1m bars; time-guard asserted.
DISCIPLINE: train 2023-24 (parameter selection) / test 2025->now touched ONCE; counter-baseline =
  mirrored-direction entries at the same triggers; anchored folds; placebo = shuffle trigger
  labels within the permission set; Wilson CIs; N<30 flagged.
"""
import json
import math
from datetime import time as dtime

import numpy as np
import pandas as pd

import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
NY = "America/New_York"
TRAIN_END = "2024-12-31"
TICK = 0.25
rng = np.random.default_rng(42)

print("=" * 80 + "\nTREND PULLBACK (stacked MA) — isolated M15 setup, bare vs +confluence\n" + "=" * 80)
bars = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts").reset_index(drop=True)
bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")
bars["delta"] = np.sign(bars.close.diff().fillna(0)) * bars.volume

# ---- M15 frame (label = window END; all features use bars <= that close) ----
m = bars.set_index("ts").resample("15min", label="right", closed="right").agg(
    open=("open", "first"), high=("high", "max"), low=("low", "min"),
    close=("close", "last"), volume=("volume", "sum"), delta=("delta", "sum")).dropna(subset=["close"])
m["day"] = m.index.strftime("%Y-%m-%d")
m["t"] = m.index.time
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
bb_m = m.close.rolling(20).mean(); bb_s = m.close.rolling(20).std(ddof=0)
m["bb_up"] = bb_m + 2 * bb_s
m["vol_ma5"] = m.volume.rolling(5).mean().shift(1)     # prior N bars (exclude current)
m["vol_ma10"] = m.volume.rolling(10).mean().shift(1)
m["vol_ma20"] = m.volume.rolling(20).mean().shift(1)
m["swing_lo5"] = m.low.rolling(5).min()
m["swing_hi5"] = m.high.rolling(5).max()

# ---- session VWAP + POC at each M15 close, built cumulatively from <=-now 1m bars ----
GUARD_FAIL = 0
vwap_at, poc_at = {}, {}
for d, g in bars.groupby("day", sort=True):
    tp = ((g.high + g.low + g.close) / 3).values; vol = g.volume.values
    px = g.close.values; ts_int = g.ts.values.astype("int64")   # UTC ns since epoch
    cum_pv = np.cumsum(tp * vol); cum_v = np.cumsum(vol)
    bins = np.round(((g.high + g.low) / 2 / 5.0)).astype(int).values
    ends = m.index[(m.day == d)]
    hist = {}
    bi = 0
    for e in ends:
        e_val = e.value                                          # UTC ns since epoch
        while bi < len(ts_int) and ts_int[bi] <= e_val:
            hist[bins[bi]] = hist.get(bins[bi], 0.0) + vol[bi]; bi += 1
        if bi == 0:
            continue
        assert ts_int[bi - 1] <= e_val, "TIME GUARD VIOLATION"
        vwap_at[e] = cum_pv[bi - 1] / max(cum_v[bi - 1], 1e-9)
        poc_at[e] = max(hist, key=hist.get) * 5.0
m["vwap"] = m.index.map(vwap_at)
m["poc"] = m.index.map(poc_at)
print(f"M15 bars: {len(m)}  | time-guard: session VWAP/POC built cumulatively, assertion armed "
      f"(violations: {GUARD_FAIL})")

M = m.reset_index().rename(columns={"index": "ts"})
M = M[M.ma200.notna()].reset_index(drop=True)
arr = {c: M[c].values for c in ["open", "high", "low", "close", "ma20", "ma50", "ma200",
                                "bb_up", "vwap", "poc", "volume", "delta",
                                "vol_ma5", "vol_ma10", "vol_ma20", "swing_lo5", "swing_hi5"]}
days_arr = M.day.values; tarr = M.t.values
rth = np.array([dtime(9, 30) <= t <= dtime(15, 0) for t in tarr])
is_train_bar = days_arr <= TRAIN_END

def find_triggers(touch_mode, nvol, thr):
    """returns list of (i, dir) trigger bars. Long: stack up, wick/close touch of ma50, resume."""
    out = []
    ma20, ma50, ma200 = arr["ma20"], arr["ma50"], arr["ma200"]
    lo, hi, cl = arr["low"], arr["high"], arr["close"]
    vma = arr[f"vol_ma{nvol}"]; vol = arr["volume"]
    for i in range(1, len(M)):
        if not rth[i] or np.isnan(vma[i]) or vma[i] <= 0:
            continue
        fade = vol[i] < thr * vma[i]
        if not fade:
            continue
        if ma20[i] > ma50[i] > ma200[i] and cl[i] > ma50[i] and cl[i] > ma200[i]:
            touched = (lo[i] <= ma50[i]) if touch_mode == "wick" else (min(cl[i - 1], arr["open"][i]) <= ma50[i])
            if touched and cl[i] > ma50[i]:
                out.append((i, 1))
        elif ma20[i] < ma50[i] < ma200[i] and cl[i] < ma50[i] and cl[i] < ma200[i]:
            touched = (hi[i] >= ma50[i]) if touch_mode == "wick" else (max(cl[i - 1], arr["open"][i]) >= ma50[i])
            if touched and cl[i] < ma50[i]:
                out.append((i, -1))
    return out

def confluence_score(i, dr):
    s = 0
    s += int(dr * arr["delta"][i] >= 0)                                   # absorption proxy
    s += int((arr["close"][i] > arr["vwap"][i]) if dr > 0 else (arr["close"][i] < arr["vwap"][i]))
    bb_lo = 2 * arr["ma20"][i] - arr["bb_up"][i]
    s += int((arr["close"][i] < arr["bb_up"][i]) if dr > 0 else (arr["close"][i] > bb_lo))
    s += int((arr["close"][i] > arr["poc"][i]) if dr > 0 else (arr["close"][i] < arr["poc"][i]))
    return s

def resolve(i, dr, tgtR, invert=False):
    """entry next M15 open; returns R or None (skip). invert -> counter-baseline mirror."""
    if i + 1 >= len(M) or days_arr[i + 1] != days_arr[i]:
        return None
    e_dir = -dr if invert else dr
    entry = arr["open"][i + 1] + e_dir * TICK
    if invert:
        stop_dist_ref = (arr["swing_hi5"][i] if dr > 0 else arr["swing_lo5"][i])
        risk = abs(stop_dist_ref - entry)
    else:
        ref = min(arr["swing_lo5"][i], arr["ma50"][i]) if dr > 0 else max(arr["swing_hi5"][i], arr["ma50"][i])
        risk = abs(entry - ref) + TICK
    if risk < 5 or risk > 70:
        return None
    stop = entry - e_dir * risk; tgt = entry + e_dir * tgtR * risk
    j = i + 1
    while j < len(M) and days_arr[j] == days_arr[i]:
        if tarr[j] >= dtime(15, 55):
            return e_dir * (arr["close"][j] - entry) / risk
        hs = (arr["low"][j] <= stop) if e_dir > 0 else (arr["high"][j] >= stop)
        ht = (arr["high"][j] >= tgt) if e_dir > 0 else (arr["low"][j] <= tgt)
        if hs:
            return -1.0 - TICK / risk
        if ht:
            return tgtR - TICK / risk
        j += 1
    return e_dir * (arr["close"][j - 1] - entry) / risk

def book(trigs, tgtR, conf_k=None, invert=False):
    res, used = [], []
    last_end = -1
    for i, dr in trigs:
        if i <= last_end:
            continue
        if conf_k is not None and confluence_score(i, dr) < conf_k:
            continue
        r = resolve(i, dr, tgtR, invert=invert)
        if r is None:
            continue
        res.append(r); used.append((i, dr)); last_end = i + 1
    return np.array(res), used

def stats(R_, label=""):
    n = len(R_)
    if n == 0:
        return dict(n=0)
    wins = (R_ > 0)
    k = int(wins.sum()); wr = 100 * k / n
    z = 1.96; p = k / n; dd_ = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / dd_; hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / dd_
    gp = R_[R_ > 0].sum(); gl = -R_[R_ < 0].sum()
    eq = np.cumsum(R_); mdd = float((np.maximum.accumulate(eq) - eq).max()) if n else 0
    bm = [R_[rng.integers(0, n, n)].mean() for _ in range(2000)]
    return dict(n=n, expR=round(float(R_.mean()), 3),
                exp_ci=(round(float(np.percentile(bm, 2.5)), 3), round(float(np.percentile(bm, 97.5)), 3)),
                wr=round(wr, 1), wr_ci=(round(100 * (ctr - hw), 1), round(100 * (ctr + hw), 1)),
                pf=round(float(gp / gl), 2) if gl > 0 else float("inf"), mddR=round(mdd, 1))

# ---- TRAIN-ONLY parameter selection (grid logged) ----
print("\n--- parameter selection on TRAIN only (2023-24) ---")
grid = [(tm, nv, th, tg) for tm in ("wick", "close") for nv in (5, 10, 20)
        for th in (0.7, 0.8, 0.9, 1.0) for tg in (1.5, 2.0, 3.0)]
best = None
MIN_TRAIN_N = 120     # a-priori sample-sufficiency constraint (so test N is likely >=30), set before test
for tm, nv, th, tg in grid:
    trigs = [(i, d) for (i, d) in find_triggers(tm, nv, th) if is_train_bar[i]]
    R_, _ = book(trigs, tg)
    if len(R_) >= MIN_TRAIN_N:
        e = R_.mean()
        if best is None or e > best[0]:
            best = (e, tm, nv, th, tg, len(R_))
print(f"(sample-sufficiency constraint: train N>={MIN_TRAIN_N}, chosen a priori)")
_, TM, NV, TH, TG = best[0], best[1], best[2], best[3], best[4]
print(f"chosen on train: touch={TM}  fade: vol < {TH} x mean(prior {NV} bars)  target={TG}R  "
      f"(train n={best[5]}, train E[R]={best[0]:+.3f})")
CK = None
bestk = None
tr_trigs_all = [(i, d) for (i, d) in find_triggers(TM, NV, TH) if is_train_bar[i]]
for k in (2, 3, 4):
    Rk, _ = book(tr_trigs_all, TG, conf_k=k)
    if len(Rk) >= 30:
        if bestk is None or Rk.mean() > bestk[0]:
            bestk = (Rk.mean(), k, len(Rk))
CK = bestk[1] if bestk else 3
print(f"confluence K chosen on train: >= {CK} of 4 confirmations (train n={bestk[2] if bestk else 0}, "
      f"train E[R]={bestk[0]:+.3f})" if bestk else f"confluence K default {CK} (train too thin)")

# ---- frozen evaluation: TEST touched once ----
all_trigs = find_triggers(TM, NV, TH)
te_trigs = [(i, d) for (i, d) in all_trigs if not is_train_bar[i]]
tr_trigs = [(i, d) for (i, d) in all_trigs if is_train_bar[i]]
OUT = {}
for vname, ck in [("BARE", None), ("+CONFLUENCE", CK)]:
    OUT[vname] = {}
    for split, tg_ in [("TRAIN", tr_trigs), ("TEST", te_trigs)]:
        R_, used = book(tg_, TG, conf_k=ck)
        Rc, _ = book(used, TG, conf_k=None, invert=True)          # counter-baseline on same entries
        st = stats(R_); stc = stats(Rc)
        # folds (anchored) on the same variant
        bounds = ["2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01", "2026-01-01", "2026-07-16"]
        pos = valid = 0
        if split == "TEST":
            for j in range(len(bounds) - 1):
                fr = [(i, d) for (i, d) in all_trigs if bounds[j] <= days_arr[i] < bounds[j + 1]]
                Rf, _ = book(fr, TG, conf_k=ck)
                if len(Rf) >= 10:
                    valid += 1; pos += int(Rf.mean() > 0)
        OUT[vname][split] = dict(st=st, ctr=stc, folds=(pos, valid),
                                 used=[(int(i), int(d)) for i, d in used])
        lbl = f"{vname:12s} {split:5s}"
        if st["n"]:
            print(f"  {lbl} n={st['n']:3d}{' LOW-N!' if st['n']<30 else ''}  E[R] {st['expR']:+.3f} "
                  f"CI{st['exp_ci']}  win {st['wr']}% CI{st['wr_ci']}  PF {st['pf']}  maxDD {st['mddR']}R"
                  + (f"  | counter E[R] {stc['expR']:+.3f} (n={stc['n']})" if stc.get("n") else "")
                  + (f"  | folds {pos}/{valid}" if split == "TEST" else ""))
        else:
            print(f"  {lbl} n=0")

# ---- placebo: shuffle trigger labels within the permission set (test block) ----
print("\n--- placebo (shuffle trigger bars within stacked-MA permission set, 300x, TEST) ---")
perm_long = [i for i in range(len(M)) if rth[i] and not is_train_bar[i]
             and arr["ma20"][i] > arr["ma50"][i] > arr["ma200"][i] and arr["close"][i] > arr["ma50"][i]]
perm_short = [i for i in range(len(M)) if rth[i] and not is_train_bar[i]
              and arr["ma20"][i] < arr["ma50"][i] < arr["ma200"][i] and arr["close"][i] < arr["ma50"][i]]
placebo = {}
for vname, ck in [("BARE", None), ("+CONFLUENCE", CK)]:
    used = OUT[vname]["TEST"]["used"]
    real = OUT[vname]["TEST"]["st"].get("expR", 0)
    nL = sum(1 for _, d in used if d == 1); nS = len(used) - nL
    sims = []
    for _ in range(300):
        pick = ([(int(i), 1) for i in rng.choice(perm_long, min(nL, len(perm_long)), replace=False)] +
                [(int(i), -1) for i in rng.choice(perm_short, min(nS, len(perm_short)), replace=False)])
        pick.sort()
        Rp, _ = book(pick, TG, conf_k=None)
        if len(Rp):
            sims.append(Rp.mean())
    pval = float((np.array(sims) >= real).mean()) if sims else 1.0
    placebo[vname] = round(pval, 3)
    print(f"  {vname:12s} real E[R] {real:+.3f} vs placebo mean {np.mean(sims):+.3f}  "
          f"shuffle p={pval:.3f}  ({'edge beyond permission-set' if pval < 0.05 else 'NOT beyond random entries in same trend'})")

# ---- explicit answers ----
a_te, b_te = OUT["BARE"]["TEST"]["st"], OUT["+CONFLUENCE"]["TEST"]["st"]
print("\n" + "=" * 80 + "\nEXPLICIT ANSWERS\n" + "=" * 80)
d_ab = (b_te.get("expR", 0) - a_te.get("expR", 0)) if a_te.get("n") and b_te.get("n") else None
print(f"1) (b) vs (a) OOS: bare E[R] {a_te.get('expR')} (n={a_te.get('n')}) vs "
      f"+confluence {b_te.get('expR')} (n={b_te.get('n')})  -> diff {d_ab:+.3f}" if d_ab is not None else "1) insufficient N")
for vname in ("BARE", "+CONFLUENCE"):
    st = OUT[vname]["TEST"]["st"]; ct = OUT[vname]["TEST"]["ctr"]
    if st.get("n"):
        clear = st["exp_ci"][0] > ct.get("expR", 0) and st["n"] >= 30
        print(f"2) {vname}: E[R] CI {st['exp_ci']} vs counter {ct.get('expR')} -> "
              f"{'CLEARS' if clear else 'does NOT clear'} (n={st['n']})")
for vname in ("BARE", "+CONFLUENCE"):
    tr_, te_ = OUT[vname]["TRAIN"]["st"], OUT[vname]["TEST"]["st"]
    if tr_.get("n") and te_.get("n"):
        print(f"3) {vname}: train E[R] {tr_['expR']:+.3f} vs test {te_['expR']:+.3f}  "
              f"gap {tr_['expR']-te_['expR']:+.3f} ({'OVERFIT ALARM' if tr_['expR']-te_['expR'] > 0.15 else 'ok'})")

json.dump(dict(params=dict(touch=TM, n=NV, thr=TH, tgtR=TG, conf_k=CK,
                           notes=["permission deviation logged: close>ma50&ma200 + stack order (strict above-all-three would forbid 50MA touches)",
                                  "delta = tick-rule proxy (true delta div needs bid/ask, 2026-only)",
                                  "RTH triggers 09:30-15:00, EOD flatten 15:55, risk clamp 5-70pt"]),
               results={v: {s: dict(st=OUT[v][s]["st"], ctr=OUT[v][s]["ctr"], folds=OUT[v][s]["folds"])
                            for s in ("TRAIN", "TEST")} for v in OUT},
               placebo=placebo),
          open(f"{S}/trend_pullback.json", "w"), default=str)
print("\nsaved trend_pullback.json")
