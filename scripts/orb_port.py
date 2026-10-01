#!/usr/bin/env python3
"""15-min Opening Range Breakout ported from johnamcruz/algoTraderBot strategies/orb.py.
Rules frozen in docs/PREREG-orb-algotrader.md. Exits scanned from the bar AFTER entry."""
import argparse, gzip, json, numpy as np, pandas as pd

TICKS = {"NQ":0.25,"ES":0.25,"RTY":0.10,"YM":1.0,"GC":0.10}
ORB_BARS, OPEN_MIN, ADX_GATE, CLOSE_MIN, ATR_P, ADX_P, STOP_ATR = 5, 570, 18.0, 960, 20, 14, 0.5
ACTIVATE_R, GIVEBACK_R = 2.0, 0.75

def wilder(x, n):
    a = np.full(len(x), np.nan)
    if len(x) < n: return a
    a[n-1] = np.nanmean(x[:n])
    for i in range(n, len(x)): a[i] = (a[i-1]*(n-1)+x[i])/n
    return a

def atr_adx(h, l, c):
    pc = np.roll(c,1); pc[0]=c[0]
    tr = np.maximum(h-l, np.maximum(abs(h-pc), abs(l-pc)))
    at = wilder(tr, ATR_P); a14 = wilder(tr, ADX_P)
    up = h-np.roll(h,1); dn = np.roll(l,1)-l; up[0]=dn[0]=0.0
    pdm = np.where((up>dn)&(up>0), up, 0.0); ndm = np.where((dn>up)&(dn>0), dn, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        pdi = 100*wilder(pdm,ADX_P)/a14; ndi = 100*wilder(ndm,ADX_P)/a14
        dx = 100*np.abs(pdi-ndi)/(pdi+ndi)
    return at, wilder(np.nan_to_num(dx), ADX_P)

def opening_range(idx, h, l):
    """Causal: at bar i, the high/low of the first ORB_BARS bars at/after 09:30 ET of i's day.
    Active only from the bar AFTER that window closes."""
    day = idx.normalize().values
    tmin = (idx.hour*60 + idx.minute).values
    n = len(h); oh = np.full(n,np.nan); ol = np.full(n,np.nan)
    cur=None; H=L=np.nan; cnt=0; done=False
    for i in range(n):
        if day[i] != cur: cur, H, L, cnt, done = day[i], np.nan, np.nan, 0, False
        if (not done) and tmin[i] >= OPEN_MIN:
            H = h[i] if cnt==0 else max(H,h[i]); L = l[i] if cnt==0 else min(L,l[i]); cnt += 1
            if cnt >= ORB_BARS: done = True
        elif done:
            oh[i], ol[i] = H, L
    return oh, ol, tmin, day

def run(b, exit_mode, tick, cost_ticks=2.0):
    o,h,l,c = (b[x].values.astype(float) for x in ("open","high","low","close"))
    idx = b.index
    at, ad = atr_adx(h,l,c)
    oh, ol, tmin, day = opening_range(idx, h, l)
    n = len(c); out=[]; i=1
    while i < n-1:
        if not (np.isfinite(oh[i]) and np.isfinite(oh[i-1]) and np.isfinite(at[i]) and at[i]>0
                and np.isfinite(ad[i])):
            i += 1; continue
        if tmin[i] >= CLOSE_MIN or ad[i] < ADX_GATE: i += 1; continue
        d = 0
        if c[i-1] <= oh[i-1] and c[i] > oh[i]: d = 1
        elif c[i-1] >= ol[i-1] and c[i] < ol[i]: d = -1
        if d == 0: i += 1; continue
        E = c[i]; risk = STOP_ATR*at[i]
        if risk <= 0: i += 1; continue
        stop = E - d*risk; peak = 0.0; r=None; res="FLAT"; k=i+1
        while k < n and day[k] == day[i]:
            fav = (h[k]-E)/risk if d==1 else (E-l[k])/risk
            adv = (l[k]-E)/risk if d==1 else (E-h[k])/risk
            if exit_mode == "GIVEBACK":
                if adv <= -1.0 and peak < ACTIVATE_R: r,res = -1.0,"STOP"; break
                peak = max(peak, fav)
                if peak >= ACTIVATE_R:
                    floor_r = peak - GIVEBACK_R
                    if adv <= floor_r: r,res = floor_r,"TRAIL"; break
                elif adv <= -1.0: r,res = -1.0,"STOP"; break
            else:
                T = float(exit_mode[1:])
                if adv <= -1.0: r,res = -1.0,"STOP"; break
                if fav >= T: r,res = T,"TARGET"; break
            k += 1
        if r is None:
            k = min(k, n-1); r = d*(c[k]-E)/risk; res = "FLAT"
        out.append(dict(day=str(pd.Timestamp(idx[i]).date()), dir=d, entry=float(E), stop=float(stop),
                        risk=float(risk), res=res, r=float(r),
                        hold_min=int((idx[k]-idx[i]).total_seconds()//60), fill_hrs=0.0,
                        target_r=1.0, depth=0.0))
        i = k+1
    df = pd.DataFrame(out)
    if len(df): df["netr"] = df.r - (cost_ticks*tick)/df.risk
    return df

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    D = "/home/user/AI-trading-agents/data/reference/algotrader_3min"
    print(f"  {'sym':<5}{'exit':<10}{'trades':>8}{'/sess':>7}{'R/trade':>10}{'net R':>9}{'win':>7}"
          f"{'medHold':>9}{'maxDD':>9}{'@5tick':>9}{'H1':>9}{'H2':>9}")
    for sym in ("NQ","ES","RTY","YM","GC"):
        b = pd.read_parquet(f"{D}/{sym}_3min.parquet")
        nd = b.index.normalize().nunique(); tk = TICKS[sym]
        for em in ("GIVEBACK","R1","R2","R3"):
            tr = run(b, em, tk)
            if len(tr)==0: print(f"  {sym:<5}{em:<10}   no trades"); continue
            day = tr.groupby("day").netr.sum(); cum = day.cumsum(); dd = (cum-cum.cummax()).min()
            h1 = tr[tr.day < "2024-01-01"].netr; h2 = tr[tr.day >= "2024-01-01"].netr
            c5 = (tr.r - (5.0*tk)/tr.risk).mean()
            print(f"  {sym:<5}{em:<10}{len(tr):>8}{len(tr)/nd:>7.2f}{tr.netr.mean():>+10.4f}{tr.netr.sum():>+9.0f}"
                  f"{(tr.res.isin(['TARGET','TRAIL'])).mean():>7.1%}{tr.hold_min.median():>9.0f}{dd:>+9.1f}"
                  f"{c5:>+9.4f}{h1.mean():>+9.4f}{h2.mean():>+9.4f}")
            with gzip.open(f"{a.out}_{sym}_{em}.jsonl.gz","wt") as fh:
                for _,t in tr.iterrows(): fh.write(json.dumps({q:(v.item() if hasattr(v,'item') else v) for q,v in t.items()})+"\n")
