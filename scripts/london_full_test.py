#!/usr/bin/env python3
"""LONDON FULL TEST — Jul 2025 -> Jul 2026, UK-anchored, two segments never blended.

Segments by ENTRY time (Europe/London local):  LDN 08:00-14:30 UK | OVL 14:30-16:30 UK.
Force-flat at 16:30 UK (flat-rule cost logged vs a 21:00-UK counterfactual resolution).
DST-mismatch weeks (UK-ET offset 4h: 2025-10-26..11-01, 2026-03-08..03-28) flagged on every trade.
Half-days excluded from entries: 2025-11-28, 2026-04-03 (thin data; logged).

Baseline A: M15 SMA 20>50>200 stack (mirror short), entry on 50SMA wick-touch with declining
pullback volume (bar vol < 1.0x mean prior 10), structural stop = swing5-low/50MA clamp 5-70pt,
target 3R, entry next-bar open +1 tick, costs 2 ticks + $5 RT. Variants = ONE change each:
  B touch-reclaim trigger | C no volume filter | D target 2R | E prev-day-range>=20d median gate
  F close beyond 20MA too | G limit@50MA entry | H REAL-CVD 3-min confirm (footprint days only,
  reported vs A on the SAME covered subset) | I all-combined.
MAE/MFE per trade from the 1m path. Monthly x segment x variant reporting; rejected-trade
outcome analysis per filter; 30-min time-of-day buckets; winner-MAE stop caps per segment.
NO LOOKAHEAD anywhere: gates use prior-day stats; CVD window ends strictly before entry minute.
"""
import json
from datetime import time as dtime

import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
WT = f"{S}/canon_wt"
TICK, PV, COMM = 0.25, 20.0, 5.0
W0, W1, W2 = dtime(8, 0), dtime(14, 30), dtime(16, 30)      # UK segment bounds
FLAT_CF = dtime(21, 0)                                       # counterfactual backstop (UK)
EXCLUDE = {"2025-11-28", "2026-04-03"}
MISM = [("2025-10-26", "2025-11-01"), ("2026-03-08", "2026-03-28")]

print("loading 1m + footprint ...", flush=True)
b = pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b["ts_event"], utc=True)
b["uk"] = b.ts.dt.tz_convert("Europe/London")
b = b.sort_values("ts").reset_index(drop=True)
b["ukday"] = b.uk.dt.strftime("%Y-%m-%d")

# real CVD: per-minute signed delta (B=buy verified) from Databento footprint parquets
fp = []
for f in ["footprint_q3_2025", "footprint_feb_mar2026", "footprint_apr2026", "footprint_may_jul2026"]:
    d = pd.read_parquet(f"{WT}/data/reference/cvd/{f}.parquet", columns=["ts_minute", "side", "volume"])
    fp.append(d)
fp = pd.concat(fp, ignore_index=True)
fp["signed"] = np.where(fp["side"] == "B", fp["volume"], -fp["volume"])
delta = fp.groupby("ts_minute")["signed"].sum().sort_index()
delta.index = pd.to_datetime(delta.index, utc=True)
delta3 = delta.rolling(3).sum()                              # 3-min sum ending AT index minute
cvd_days = set(pd.Series(delta.index.tz_convert("Europe/London")).dt.strftime("%Y-%m-%d"))
del fp

# M15 frame (UTC resample; bar labels = right/close time)
m = b.set_index("ts").resample("15min", label="right", closed="right").agg(
    open=("open", "first"), high=("high", "max"), low=("low", "min"),
    close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"])
m["uk"] = m.index.tz_convert("Europe/London")
m["ukday"] = m.uk.dt.strftime("%Y-%m-%d"); m["ukt"] = m.uk.dt.time
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["vol_ma10"] = m.volume.rolling(10).mean().shift(1)
m["swing_lo5"] = m.low.rolling(5).min(); m["swing_hi5"] = m.high.rolling(5).max()
M = m.reset_index().rename(columns={"ts": "uts"}) if "ts" in m.index.names else m.reset_index()
M = M.rename(columns={M.columns[0]: "uts"}).dropna(subset=["ma200"]).reset_index(drop=True)
a = {c: M[c].values for c in ["open", "high", "low", "close", "volume", "ma20", "ma50", "ma200",
                              "vol_ma10", "swing_lo5", "swing_hi5"]}
ukday = M.ukday.values; ukt = M.ukt.values; uts = M.uts.values

# prior-day range map (completed UK days) for gate E
dr = b.groupby("ukday").agg(hi=("high", "max"), lo=("low", "min"))
dr["rng"] = dr.hi - dr.lo
days_sorted = dr.index.tolist()
rng_med20, prev_rng = {}, {}
for i, d in enumerate(days_sorted):
    if i >= 1:
        prev_rng[d] = dr.rng.iloc[i - 1]
    if i >= 21:
        rng_med20[d] = dr.rng.iloc[i - 21:i - 1].median()

# 1m arrays per UK day for MAE/MFE + counterfactual
b1 = {d: g.reset_index(drop=True) for d, g in b.groupby("ukday")}

WIN_START, WIN_END = "2025-07-01", "2026-07-15"
in_win = (M.ukday >= WIN_START) & (M.ukday <= WIN_END)
mismset = set()
for lo, hi in MISM:
    mismset |= {d for d in days_sorted if lo <= d <= hi}

def seg_of(t):
    if W0 <= t < W1:
        return "LDN"
    if W1 <= t < W2:
        return "OVL"
    return None

# ---------------- trigger universe (superset, flags per filter) ----------------
U = []
for i in range(1, len(M)):
    if not in_win.iloc[i] or ukday[i] in EXCLUDE:
        continue
    seg = seg_of(ukt[i])
    if seg is None:
        continue
    up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
    dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
    dr_ = 0
    if up and a["low"][i] <= a["ma50"][i]:
        dr_ = 1
    elif dn and a["high"][i] >= a["ma50"][i]:
        dr_ = -1
    if dr_ == 0 or i + 1 >= len(M) or ukday[i + 1] != ukday[i]:
        continue
    volfade = (not np.isnan(a["vol_ma10"][i])) and a["vol_ma10"][i] > 0 and a["volume"][i] < a["vol_ma10"][i]
    reclaim = (a["close"][i - 1] < a["ma50"][i - 1]) if dr_ > 0 else (a["close"][i - 1] > a["ma50"][i - 1])
    d = ukday[i]
    gateE = (d in rng_med20) and (d in prev_rng) and (prev_rng[d] >= rng_med20[d])
    deepF = (a["close"][i] > a["ma20"][i]) if dr_ > 0 else (a["close"][i] < a["ma20"][i])
    # real CVD 3-min confirm, window ends strictly BEFORE the entry minute (next bar open)
    ent_min = pd.Timestamp(uts[i + 1])                       # entry occurs at open of bar i+1
    if ent_min.tzinfo is None:
        ent_min = ent_min.tz_localize("UTC")
    cvd_ok, cvd_cov = None, False
    key = ent_min - pd.Timedelta(minutes=1)
    if d in cvd_days:
        v = delta3.get(key, np.nan)
        if not np.isnan(v):
            cvd_cov = True
            cvd_ok = (v > 0) if dr_ > 0 else (v < 0)
    U.append(dict(i=i, dir=dr_, seg=seg, day=d, month=d[:7], mism=d in mismset,
                  volfade=volfade, reclaim=reclaim, gateE=gateE, deepF=deepF,
                  cvd_cov=cvd_cov, cvd_ok=bool(cvd_ok) if cvd_ok is not None else False))
print(f"trigger universe: {len(U)} touches  ({sum(1 for u in U if u['seg']=='LDN')} LDN / "
      f"{sum(1 for u in U if u['seg']=='OVL')} OVL)")

def resolve(i, dr_, tg=3.0, limit_entry=False, stop_cap=None):
    """Returns trade dict or None. Force-flat 16:30 UK; counterfactual to 21:00 UK."""
    if limit_entry:
        # limit at 50MA of trigger bar: filled next bar only if touched
        j = i + 1
        lm = a["ma50"][i]
        touched = (a["low"][j] <= lm) if dr_ > 0 else (a["high"][j] >= lm)
        if not touched:
            return None
        entry = lm + dr_ * TICK
    else:
        entry = a["open"][i + 1] + dr_ * TICK
    ref = min(a["swing_lo5"][i], a["ma50"][i]) if dr_ > 0 else max(a["swing_hi5"][i], a["ma50"][i])
    risk = abs(entry - ref) + TICK
    if risk < 5 or risk > 70:
        return None
    if stop_cap is not None:
        risk = min(risk, stop_cap)
    stop = entry - dr_ * risk; tgt = entry + dr_ * tg * risk
    gross, exit_reason, jexit = None, None, None
    j = i + 1
    while j < len(M) and ukday[j] == ukday[i]:
        if ukt[j] >= W2:                                     # force-flat 16:30 UK
            gross = dr_ * (a["close"][j] - entry); exit_reason = "flat"; jexit = j; break
        hs = (a["low"][j] <= stop) if dr_ > 0 else (a["high"][j] >= stop)
        ht = (a["high"][j] >= tgt) if dr_ > 0 else (a["low"][j] <= tgt)
        if hs:
            gross = -risk - TICK; exit_reason = "stop"; jexit = j; break
        if ht:
            gross = tg * risk - TICK; exit_reason = "target"; jexit = j; break
        j += 1
    if gross is None:
        jexit = min(j, len(M) - 1) - (0 if j < len(M) else 1)
        gross = dr_ * (a["close"][jexit] - entry); exit_reason = "eod"
    net = gross * PV - COMM
    # counterfactual for flat-closed trades: continue race to 21:00 UK
    cf_net = None
    if exit_reason == "flat":
        g2 = None; k = jexit
        while k < len(M) and ukday[k] == ukday[i] and ukt[k] < FLAT_CF:
            hs = (a["low"][k] <= stop) if dr_ > 0 else (a["high"][k] >= stop)
            ht = (a["high"][k] >= tgt) if dr_ > 0 else (a["low"][k] <= tgt)
            if hs:
                g2 = -risk - TICK; break
            if ht:
                g2 = tg * risk - TICK; break
            k += 1
        if g2 is None:
            kk = min(k, len(M) - 1)
            g2 = dr_ * (a["close"][kk] - entry)
        cf_net = g2 * PV - COMM
    # MAE/MFE from 1m path entry->exit
    g1 = b1[ukday[i]]
    t0, t1 = pd.Timestamp(uts[i]).value, pd.Timestamp(uts[jexit]).value
    seg1 = g1[(g1.ts.values.astype("int64") > t0) & (g1.ts.values.astype("int64") <= t1)]
    if len(seg1):
        if dr_ > 0:
            mae = max(0.0, entry - float(seg1.low.min())); mfe = max(0.0, float(seg1.high.max()) - entry)
        else:
            mae = max(0.0, float(seg1.high.max()) - entry); mfe = max(0.0, entry - float(seg1.low.min()))
    else:
        mae = mfe = 0.0
    return dict(entry=entry, risk=risk, net=net, R=net / (risk * PV), exit=exit_reason,
                cf_net=cf_net, mae_pts=mae, mae_R=mae / risk, mfe_R=mfe / risk)

def run_variant(name, sel_fn, tg=3.0, limit_entry=False, trigger="wick", subset_days=None):
    rows = []
    for u in U:
        if subset_days is not None and u["day"] not in subset_days:
            continue
        if trigger == "wick":
            trig_ok = True
        else:
            trig_ok = u["reclaim"]
        if not (trig_ok and sel_fn(u)):
            continue
        r = resolve(u["i"], u["dir"], tg=tg, limit_entry=limit_entry)
        if r is None:
            continue
        rows.append({**u, **r, "variant": name})
    return pd.DataFrame(rows)

def stats(df):
    if not len(df):
        return None
    v = df.R.values; net = df.net.sum()
    eq = df.sort_values("day").net.cumsum().values
    dd = float((np.maximum.accumulate(eq) - eq).max())
    gp = v[v > 0].sum(); gl = -v[v < 0].sum()
    return dict(n=len(df), wr=round(100 * (v > 0).mean(), 1), eR=round(float(v.mean()), 3),
                pf=round(float(gp / gl), 2) if gl > 0 else 99.0, net=round(float(net), 0),
                dd=round(dd, 0), mae=round(float(df.mae_R.mean()), 2), mfe=round(float(df.mfe_R.mean()), 2))

VAR = {
    "A_base": dict(sel=lambda u: u["volfade"], tg=3.0),
    "B_touch_reclaim": dict(sel=lambda u: u["volfade"], tg=3.0, trigger="reclaim"),
    "C_no_volfilter": dict(sel=lambda u: True, tg=3.0),
    "D_target_2R": dict(sel=lambda u: u["volfade"], tg=2.0),
    "E_prevday_range_gate": dict(sel=lambda u: u["volfade"] and u["gateE"], tg=3.0),
    "F_deep_trend_20MA": dict(sel=lambda u: u["volfade"] and u["deepF"], tg=3.0),
    "G_limit_at_50MA": dict(sel=lambda u: u["volfade"], tg=3.0, limit=True),
    "H_real_CVD_confirm": dict(sel=lambda u: u["volfade"] and u["cvd_cov"] and u["cvd_ok"], tg=3.0, cvd_subset=True),
    "I_all_combined": dict(sel=lambda u: u["gateE"] and u["deepF"] and (not u["cvd_cov"] or u["cvd_ok"]),
                           tg=2.0, trigger="reclaim", limit=True),
}
res, frames = {}, {}
covered = {u["day"] for u in U if u["cvd_cov"]}
for name, cfg in VAR.items():
    sub = covered if cfg.get("cvd_subset") else None
    df = run_variant(name, cfg["sel"], tg=cfg.get("tg", 3.0),
                     limit_entry=cfg.get("limit", False), trigger=cfg.get("trigger", "wick"),
                     subset_days=sub)
    frames[name] = df
    res[name] = {seg: (stats(df[df.seg == seg]) if len(df) else None) for seg in ("LDN", "OVL")}
# A on the CVD-covered subset (apples-to-apples for H)
frames["A_on_CVD_days"] = run_variant("A_on_CVD_days", lambda u: u["volfade"], subset_days=covered)
_f = frames["A_on_CVD_days"]
res["A_on_CVD_days"] = {seg: (stats(_f[_f.seg == seg]) if len(_f) else None) for seg in ("LDN", "OVL")}

print("\n" + "=" * 118)
print("VARIANT x SEGMENT (Jul-2025 -> Jul-2026, entries UK-anchored, force-flat 16:30 UK, NET of costs)")
print("=" * 118)
for name in list(VAR) + ["A_on_CVD_days"]:
    for seg in ("LDN", "OVL"):
        s = res[name][seg]
        if s:
            low = "  LOW-N!" if s["n"] < 30 else ""
            print(f"  {name:22s} {seg}  n={s['n']:4d}{low}  WR {s['wr']:4.1f}%  E[R] {s['eR']:+.3f}  "
                  f"PF {s['pf']:5.2f}  net ${s['net']:+9,.0f}  maxDD ${s['dd']:7,.0f}  "
                  f"MAE {s['mae']:.2f}R  MFE {s['mfe']:.2f}R")

# ---------------- rejected-trade analysis (pure filters vs A) ----------------
print("\n--- what each PURE filter rejects (from A's trades): removed losers or winners? ---")
A = frames["A_base"]
for name, flag in [("E_prevday_range_gate", "gateE"), ("F_deep_trend_20MA", "deepF")]:
    rej = A[~A[flag]]
    print(f"  {name:22s} rejects {len(rej):3d} A-trades: their net ${rej.net.sum():+8,.0f}  "
          f"WR {100*(rej.R>0).mean() if len(rej) else 0:.0f}%  (negative = filter removes losers = good)")
Acov = frames["A_on_CVD_days"]
rej = Acov[~(Acov.cvd_ok)] if len(Acov) else Acov
if len(rej):
    print(f"  H_real_CVD_confirm     rejects {len(rej):3d} A-trades (covered days): net ${rej.net.sum():+8,.0f}  "
          f"WR {100*(rej.R>0).mean():.0f}%")
else:
    print("  H_real_CVD_confirm     NO COVERAGE (bug or no matching minutes) -> investigate")
for name in ("B_touch_reclaim", "C_no_volfilter", "G_limit_at_50MA", "D_target_2R"):
    print(f"  {name:22s} changes the trade universe/exits (not a subset filter) -> compared head-to-head above")

# ---------------- flat-rule cost ----------------
print("\n--- force-flat 16:30 UK: rule cost (baseline A) ---")
fl = A[A.exit == "flat"]
if len(fl):
    print(f"  trades flat-closed: {len(fl)}  their net ${fl.net.sum():+,.0f}  "
          f"counterfactual (held to 21:00 UK): ${fl.cf_net.sum():+,.0f}  "
          f"-> rule cost ${fl.net.sum()-fl.cf_net.sum():+,.0f}")
else:
    print("  no trades reached 16:30 UK open")

# ---------------- time-of-day buckets ----------------
print("\n--- 30-min entry buckets (baseline A, both segments) ---")
A2 = A.copy()
A2["slot"] = [f"{t.hour:02d}:{(t.minute//30)*30:02d}" for t in
              [M.ukt.iloc[i] for i in A2.i]]
tod = []
for slot, g in sorted(A2.groupby("slot")):
    tod.append(dict(slot=slot, n=len(g), net=round(g.net.sum()), eR=round(g.R.mean(), 3),
                    wr=round(100 * (g.R > 0).mean())))
    print(f"  {slot} UK  n={len(g):3d}  net ${g.net.sum():+8,.0f}  E[R] {g.R.mean():+.3f}  WR {100*(g.R>0).mean():3.0f}%")
first_ldn = A2[A2.slot == "08:00"]; first_ovl = A2[A2.slot == "14:30"]
print(f"\n  ANGUS CLAIM CHECK — 08:00-08:30 UK: n={len(first_ldn)}, net ${first_ldn.net.sum():+,.0f}"
      f"  |  14:30-15:00 UK: n={len(first_ovl)}, net ${first_ovl.net.sum():+,.0f}")

# 08:30-start re-run if the open bleeds
if len(first_ldn) and first_ldn.net.sum() < 0:
    lateA = A2[A2.slot != "08:00"]
    print("  -> 08:30-start baseline A: " + str({s: stats(lateA[lateA.seg == s]) for s in ("LDN", "OVL")}))

# ---------------- winner-MAE stop caps per segment ----------------
print("\n--- winner MAE distribution & p90 stop caps (baseline A) ---")
caps = {}
for seg in ("LDN", "OVL"):
    wn = A[(A.seg == seg) & (A.R > 0)]
    if len(wn) < 10:
        print(f"  {seg}: only {len(wn)} winners  LOW-N, no cap proposed"); continue
    p90 = float(np.percentile(wn.mae_pts, 90))
    clip = 100 * (wn.mae_pts > p90).mean()
    caps[seg] = round(p90, 1)
    print(f"  {seg}: winners n={len(wn)}  MAE_pts p50/p75/p90 = "
          f"{np.percentile(wn.mae_pts,50):.1f}/{np.percentile(wn.mae_pts,75):.1f}/{p90:.1f}  "
          f"cap@p90 clips {clip:.0f}% of winners")
# re-run A with per-segment caps
if caps:
    rows = []
    for u in U:
        if not u["volfade"] or u["seg"] not in caps:
            continue
        r = resolve(u["i"], u["dir"], tg=3.0, stop_cap=caps[u["seg"]])
        if r is not None:
            rows.append({**u, **r})
    Ac = pd.DataFrame(rows)
    for seg in caps:
        s0, s1 = stats(A[A.seg == seg]), stats(Ac[Ac.seg == seg])
        print(f"  {seg} capped@{caps[seg]}pt: E[R] {s0['eR']:+.3f} -> {s1['eR']:+.3f}   "
              f"net ${s0['net']:+,.0f} -> ${s1['net']:+,.0f}   n {s0['n']} -> {s1['n']}")

# ---------------- monthly grid for A and best variant ----------------
def monthly(df, label):
    print(f"\n--- monthly x segment: {label} ---")
    for seg in ("LDN", "OVL"):
        g = df[df.seg == seg]
        line = []
        for mo, gg in sorted(g.groupby("month")):
            line.append(f"{mo[2:]} {'+' if gg.net.sum()>=0 else ''}{gg.net.sum()/1000:.1f}k/{len(gg)}")
        print(f"  {seg}: " + "  ".join(line))
monthly(A, "A_base")
mism_n = int(A.mism.sum())
print(f"\nDST-mismatch-week trades in A: {mism_n} ({100*A.mism.mean():.0f}%) — OVL in those weeks = 10:30-12:30 ET, NOT the NY open")

# persist
ALL = pd.concat([f.assign(variant=k) for k, f in frames.items()], ignore_index=True)
ALL.to_csv(f"{S}/london_full_trades.csv", index=False)
json.dump(dict(res={k: v for k, v in res.items()}, tod=tod, caps=caps,
               covered_days=len(covered), universe=len(U)),
          open(f"{S}/london_full_summary.json", "w"), default=str)
print(f"\nsaved london_full_trades.csv ({len(ALL)} rows), london_full_summary.json")
