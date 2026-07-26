#!/usr/bin/env python3
"""Angus cross-validation, window 2: entries 10:00-13:00 UK (the edge-peak slot).
Depth (08:00-09:59 UK only) does NOT cover this window -> W/FAR NOT TESTABLE (no 1m proxies).
Computable checks: StopFloor>=9.5 (sub-7 kill), ROOM 2.5-9.6, ASIA opposition (cvd hole
Oct25-Jan26), NotEarlyTight (structurally vacuous here -- confirmed, not assumed).
Ladder therefore runs on FEWER checks than the 08:00-10:00 ladder: tiers NOT comparable."""
import json
from datetime import time as dtime
import numpy as np, pandas as pd
import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
WT = f"{S}/canon_wt"; TICK, PV, COMM = 0.25, 20.0, 5.0
MISM = [("2025-10-26", "2025-11-01"), ("2026-03-08", "2026-03-28")]
W_LO, W_HI = dtime(10, 0), dtime(13, 0)
print("load...", flush=True)
b = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b["ts_event"], utc=True); b["uk"] = b.ts.dt.tz_convert("Europe/London")
b = b.sort_values("ts").reset_index(drop=True); b["ukday"] = b.uk.dt.strftime("%Y-%m-%d")
b1 = {d: (g.ts.values.astype("int64"), g.low.values.astype(float), g.high.values.astype(float)) for d, g in b.groupby("ukday")}
# ASIA cvd + 3-min delta (lean, per file)
cvd_ASIA = {}; cvd_days = set(); dparts = []
for f in ["footprint_q3_2025", "footprint_feb_mar2026", "footprint_apr2026", "footprint_may_jul2026"]:
    d = pd.read_parquet(f"{WT}/data/reference/cvd/{f}.parquet", columns=["ts_minute", "side", "volume"])
    uk = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert("Europe/London")
    d["ukday"] = uk.dt.strftime("%Y-%m-%d"); cvd_days |= set(d.ukday.unique())
    d["s"] = np.where(d.side == "B", d.volume, -d.volume)
    g = d[uk.dt.time < dtime(8, 0)].groupby("ukday")["s"].sum()
    for k, v in g.items():
        cvd_ASIA[k] = cvd_ASIA.get(k, 0) + float(v)
    dm = d.groupby("ts_minute")["s"].sum(); dparts.append(dm); del d
delta = pd.concat(dparts).sort_index(); delta.index = pd.to_datetime(delta.index, utc=True)
delta3 = delta.rolling(3).sum(); del dparts
print("  cvd loaded", flush=True)
onov = b[(b.uk.dt.time >= dtime(22, 0)) | (b.uk.dt.time < dtime(8, 0))].copy()
onov["sess"] = (onov.uk + pd.Timedelta(hours=2)).dt.strftime("%Y-%m-%d")
ONH = onov.groupby("sess").high.max().to_dict(); ONL = onov.groupby("sess").low.min().to_dict()
m = b.set_index("ts").resample("15min", label="right", closed="right").agg(
    open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"])
m["uk"] = m.index.tz_convert("Europe/London"); m["ukday"] = m.uk.dt.strftime("%Y-%m-%d"); m["ukt"] = m.uk.dt.time
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["vol10"] = m.volume.rolling(10).mean().shift(1); m["slo5"] = m.low.rolling(5).min(); m["shi5"] = m.high.rolling(5).max()
m["pclose"] = m.close.shift(1); m["pma50"] = m.ma50.shift(1)
M = m.reset_index(names="uts").dropna(subset=["ma200"])
M = M[(M.ukday >= "2025-04-01") & (M.ukday <= "2026-07-15")].reset_index(drop=True)
A = {c: M[c].values for c in ["uts", "open", "high", "low", "close", "volume", "ma20", "ma50", "ma200", "vol10", "slo5", "shi5", "pclose", "pma50"]}
ukday = M.ukday.values; ukt = M.ukt.values
def build(trig):
    R = []
    for i in range(1, len(M) - 1):
        d = ukday[i]
        if not ("2025-07-01" <= d <= "2026-07-15") or d in ("2025-11-28", "2026-04-03") or ukday[i + 1] != d:
            continue
        t = ukt[i]
        if not (W_LO <= t < W_HI):
            continue
        up = A["ma20"][i] > A["ma50"][i] > A["ma200"][i] and A["close"][i] > A["ma50"][i] and A["close"][i] > A["ma200"][i]
        dn = A["ma20"][i] < A["ma50"][i] < A["ma200"][i] and A["close"][i] < A["ma50"][i] and A["close"][i] < A["ma200"][i]
        dr = 1 if (up and A["low"][i] <= A["ma50"][i]) else (-1 if (dn and A["high"][i] >= A["ma50"][i]) else 0)
        if dr == 0:
            continue
        if trig == "volfade" and not (A["vol10"][i] > 0 and A["volume"][i] < A["vol10"][i]):
            continue
        if trig == "reclaim" and not ((A["pclose"][i] < A["pma50"][i]) if dr > 0 else (A["pclose"][i] > A["pma50"][i])):
            continue
        entry = A["open"][i + 1] + dr * TICK
        ref = min(A["slo5"][i], A["ma50"][i]) if dr > 0 else max(A["shi5"][i], A["ma50"][i])
        risk = abs(entry - ref) + TICK
        if risk < 5 or risk > 70:
            continue
        stop = entry - dr * risk; tgt = entry + dr * 3 * risk; g = None; jx = i + 1; j = i + 1
        while j < len(M) and ukday[j] == d:
            if ukt[j] >= dtime(16, 30):
                g = dr * (A["close"][j] - entry); jx = j; break
            hs = (A["low"][j] <= stop) if dr > 0 else (A["high"][j] >= stop)
            ht = (A["high"][j] >= tgt) if dr > 0 else (A["low"][j] <= tgt)
            if hs: g = -risk - TICK; jx = j; break
            if ht: g = 3 * risk - TICK; jx = j; break
            j += 1
        if g is None:
            jx = min(j, len(M) - 1); g = dr * (A["close"][jx] - entry)
        net = g * PV - COMM
        ti, lo1, hi1 = b1[d]; t0 = pd.Timestamp(A["uts"][i]).value; t1 = pd.Timestamp(A["uts"][jx]).value
        msk = (ti > t0) & (ti <= t1)
        mae = (entry - lo1[msk].min()) if (dr > 0 and msk.any()) else ((hi1[msk].max() - entry) if msk.any() else 0.0)
        onh = ONH.get(d, np.nan); onl = ONL.get(d, np.nan)
        room = ((onh - entry) if dr > 0 else (entry - onl)) / risk
        # real-CVD 3-min confirm at entry (strictly before entry minute)
        em = pd.Timestamp(A["uts"][i + 1])
        em = em.tz_localize("UTC") if em.tzinfo is None else em.tz_convert("UTC")
        v3 = delta3.get(em - pd.Timedelta(minutes=1), np.nan)
        cvd_cov = (d in cvd_days) and not np.isnan(v3)
        cvd_ok = bool((v3 > 0) if dr > 0 else (v3 < 0)) if cvd_cov else False
        R.append(dict(day=d, ent=str(t), dir=dr, entry=entry, risk=risk, net=net, R=net / (risk * PV), win=net > 0,
                      mae_R=max(0., mae) / risk, room=room, cvd_ASIA=cvd_ASIA.get(d, np.nan), asia_cov=d in cvd_days,
                      cvd_cov=cvd_cov, cvd_ok=cvd_ok, early_tight=(t < dtime(8, 30) and risk < 8), sub7=risk < 7,
                      mism=any(a_ <= d <= b_ for a_, b_ in MISM)))
    return pd.DataFrame(R)
AM = build("volfade"); BM = build("reclaim")
def L(df):
    if not len(df): return dict(n=0)
    v = df.R.values; eq = df.sort_values("day").net.cumsum().values
    dd = float((np.maximum.accumulate(eq) - eq).max()); gp = v[v > 0].sum(); gl = -v[v < 0].sum()
    return dict(n=len(df), wr=round(100 * (v > 0).mean()), eR=round(float(v.mean()), 3),
                pf=round(float(gp / gl), 2) if gl > 0 else 99., net=round(float(df.net.sum())), dd=round(dd))
print("\n=== 1. RESTRICTED 10:00-13:00 UK book ===")
print("  A_base      :", L(AM))
print("  B_reclaim   :", L(BM))
HM = AM[AM.cvd_cov & AM.cvd_ok]
print("  H_CVDconfirm:", L(HM), " (covered-days A ref:", L(AM[AM.cvd_cov]), ")")
AMk = AM[~AM.sub7].copy()
print(f"  sub-7 kill removed: {int(AM.sub7.sum())} trades")
print(f"\n=== 2/4. CHECKS (n={len(AMk)}; W/FAR NOT TESTABLE - depth is 08:00-09:59 UK only) ===")
ck = [("StopFloor>=9.5", AMk.risk >= 9.5), ("ROOM 2.5-9.6", (AMk.room >= 2.5) & (AMk.room <= 9.6)),
      ("ASIA_notopp", (~AMk.asia_cov) | (AMk.dir * AMk.cvd_ASIA >= -748)), ("NotEarlyTight", ~AMk.early_tight)]
verd = {}
print(f"  {'check':15}{'passN':>6}{'passNet':>10}{'failN':>6}{'failNet':>10}  verdict")
for nm, cond in ck:
    cond = cond.fillna(False); p = AMk[cond]; f = AMk[~cond]
    v = ("VETO(fail -$)" if (len(f) >= 5 and f.net.sum() < 0) else "score-check" if p.net.sum() > f.net.sum() else "no-transfer")
    if len(p) < 20 or len(f) < 20: v += "[directional-only]"
    if nm == "NotEarlyTight" and len(f) == 0: v = "VACUOUS (structurally: window >30min after open)"
    verd[nm] = v
    print(f"  {nm:15}{len(p):6}{p.net.sum():+10,.0f}{len(f):6}{f.net.sum():+10,.0f}  {v}")
AMk["score"] = sum([(c.fillna(False)).astype(int).loc[AMk.index] for _, c in ck])
print("\n=== 3. SCORE LADDER (max 4 computable checks; NOT tier-comparable to 08-10 ladder) ===")
for sc in sorted(AMk.score.unique()):
    print(f"  score {sc}: {L(AMk[AMk.score == sc])}")
print("\n=== 5. RECONCILE ===")
wn = AM[AM.win]
print(f"  (a) winners median MAE {wn.mae_R.median():+.2f}R vs Angus -0.4R -> "
      f"{'MATCH (run immediately)' if wn.mae_R.median() < 0.6 else 'DIFFERENT (deep-MAE pullback physics)'}")
print(f"  (b) early+tight cell n={int(AM.early_tight.sum())} (confirmed structurally vacuous: entries start 10:00 UK)")
print("  (c) clocks: entries 10:00<=t<13:00 Europe/London at M15 trigger-bar close; NY refs ET; DST weeks flagged")
print("\n=== 6. VERIFICATION (A_base restricted) ===")
for y in ("2025", "2026"):
    print(f"  {y}: {L(AM[AM.day.str[:4] == y])}")
for nm, lo, hi in [("25Q3", "2025-07", "2025-09"), ("25Q4", "2025-10", "2025-12"),
                   ("26Q1", "2026-01", "2026-03"), ("26Q2+", "2026-04", "2026-07")]:
    print(f"  {nm}: {L(AM[(AM.day.str[:7] >= lo) & (AM.day.str[:7] <= hi)])}")
print(f"  DST-mismatch trades: {int(AM.mism.sum())} ({100 * AM.mism.mean():.0f}%)")
json.dump(dict(A=L(AM), B=L(BM), H=L(HM), Href=L(AM[AM.cvd_cov]), verd=verd,
               ladder={int(s): L(AMk[AMk.score == s]) for s in AMk.score.unique()},
               yr={y: L(AM[AM.day.str[:4] == y]) for y in ("2025", "2026")},
               halves={nm: L(AM[(AM.day.str[:7] >= lo) & (AM.day.str[:7] <= hi)])
                       for nm, lo, hi in [("25Q3", "2025-07", "2025-09"), ("25Q4", "2025-10", "2025-12"),
                                          ("26Q1", "2026-01", "2026-03"), ("26Q2+", "2026-04", "2026-07")]},
               win_mae=float(wn.mae_R.median()), mism=int(AM.mism.sum())),
          open(f"{S}/london_xval_mid_summary.json", "w"), default=str)
AM.to_csv(f"{S}/london_xval_mid.csv", index=False)
print("\nSAVED.")
