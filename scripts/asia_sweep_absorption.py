#!/usr/bin/env python3
"""Asia sweep of a NY PM extreme, confirmed by footprint absorption.
Rules frozen in docs/PREREG-asia-sweep-absorption.md. delta = B - A (B is the buy aggressor).
Exits scanned from the bar AFTER entry."""
import argparse, glob, gzip, json, numpy as np, pandas as pd
TICK = 0.25

def to_et(s):
    s = pd.to_datetime(s)
    s = s.dt.tz_convert("America/New_York") if s.dt.tz is not None else s.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    return s.dt.tz_localize(None)

def load_all():
    fp = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob("data/reference/cvd/footprint_*.parquet"))])
    fp["ts"] = to_et(fp.ts_minute)
    fp = fp[["ts","price","side","volume"]].sort_values("ts")
    bars = []
    for f in ("data/reference/nq_1m_master.parquet","data/reference/nq_1m_jul_sep2026.parquet"):
        b = pd.read_parquet(f); b.index = to_et(b.ts_event); bars.append(b[["open","high","low","close","volume"]])
    b = pd.concat(bars); b = b[~b.index.duplicated()].sort_index()
    return fp, b

def run(fp, bars, mode, tmode='EXT', cost=0.5):
    """mode: 'absorb' (full), 'nodelta' (volume test dropped), 'plain' (no footprint test at all)"""
    bars = bars.copy(); bars["sess"] = (bars.index - pd.Timedelta(hours=18)).normalize()
    dmin = fp.groupby(["ts","side"]).volume.sum().unstack("side").fillna(0)
    for c in ("A","B"):
        if c not in dmin: dmin[c] = 0.0
    dmin["delta"] = dmin.B - dmin.A; dmin["vol"] = dmin.A + dmin.B
    fp_days = set(pd.DatetimeIndex(fp.ts).normalize().unique())
    out = []
    for day, s in bars.groupby("sess"):
        pm_day = pd.Timestamp(day)
        pm = bars[(bars.index >= pm_day + pd.Timedelta(hours=12)) & (bars.index < pm_day + pd.Timedelta(hours=16))]
        if len(pm) < 120: continue
        hi, lo = float(pm.high.max()), float(pm.low.min())
        asia = s[(s.index >= pm_day + pd.Timedelta(hours=18)) & (s.index < pm_day + pd.Timedelta(hours=27))]
        if len(asia) < 300: continue
        if pm_day not in fp_days and mode != "plain": continue
        H, L, C = asia.high.values, asia.low.values, asia.close.values; ts = asia.index
        up = np.where(H >= hi + TICK)[0]; dn = np.where(L <= lo - TICK)[0]
        i_up = up[0] if len(up) else 10**9; i_dn = dn[0] if len(dn) else 10**9
        if min(i_up, i_dn) == 10**9: continue
        if i_up <= i_dn: i, d, lvl, tgt, ext = i_up, -1, hi, lo, float(H[i_up])
        else:            i, d, lvl, tgt, ext = i_dn, +1, lo, hi, float(L[i_dn])
        j = min(i + 4, len(asia) - 1)
        ext = float(H[i:j+1].max()) if d == -1 else float(L[i:j+1].min())
        rejected = (C[j] < lvl) if d == -1 else (C[j] > lvl)
        if not rejected: continue
        if mode != "plain":
            w = fp[(fp.ts >= ts[i]) & (fp.ts <= ts[j]) & (abs(fp.price - lvl) <= 5*TICK)]
            if w.empty: continue
            vol = float(w.volume.sum())
            delta = float(w[w.side=="B"].volume.sum() - w[w.side=="A"].volume.sum())
            pre = dmin[(dmin.index >= pm_day + pd.Timedelta(hours=18)) & (dmin.index < ts[i])]
            if len(pre) < 30: continue
            med = float(pre.vol.median())
            if med <= 0: continue
            if not ((delta > 0) if d == -1 else (delta < 0)): continue   # aggressors pushed through
            if mode == "absorb" and vol < 3.0 * med: continue
        E = float(C[j]); stop = ext + TICK*(1 if d == -1 else -1); risk = abs(E - stop)
        if risk <= 0: continue
        if tmode != "EXT": tgt = E + d*float(tmode[1:])*risk
        if (d*(tgt - E)) <= 0: continue
        fwd = s[s.index > ts[j]]
        if len(fwd) < 2: continue
        FH, FL, FC = fwd.high.values, fwd.low.values, fwd.close.values
        r = None; res = "FLAT"
        for q in range(len(fwd)):
            if (FH[q] >= stop) if d == -1 else (FL[q] <= stop): r, res = -1.0, "STOP"; break
            if (FL[q] <= tgt) if d == -1 else (FH[q] >= tgt): r, res = abs(tgt-E)/risk, "TARGET"; break
        if r is None: r = d*(FC[-1]-E)/risk
        out.append(dict(day=str(pm_day.date()), dir=int(d), entry=E, stop=float(stop), risk=float(risk),
                        target=float(tgt), res=res, r=float(r), hold_min=int(q+1), fill_hrs=0.0,
                        target_r=float(abs(tgt-E)/risk), depth=0.0))
    return pd.DataFrame(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    fp, bars = load_all()
    print(f"footprint: {len(fp):,} rows, {pd.DatetimeIndex(fp.ts).normalize().nunique()} days | bars: {len(bars):,}")
    print(f"\n  {'variant':<28}{'trades':>8}{'R/trade':>10}{'net R':>8}{'win':>7}{'medRR':>7}{'maxDD':>8}{'2023-24':>10}{'2025-26':>10}")
    for mode, tm in [("plain", t) for t in ("R1","R1.5","R2","R3","R4","R5","R8","EXT")]:
        lab = f"target {tm}"
        tr = run(fp, bars, mode, tm)
        if len(tr) == 0: print(f"  {lab:<28}   no trades"); continue
        tr["netr"] = tr.r - 0.5/tr.risk
        day = tr.groupby("day").netr.sum(); cum = day.cumsum(); dd = (cum-cum.cummax()).min()
        e1 = tr[tr.day < "2025-01-01"].netr; e2 = tr[tr.day >= "2025-01-01"].netr
        wn = tr[tr.res=="TARGET"]
        print(f"  {lab:<28}{len(tr):>8}{tr.netr.mean():>+10.4f}{tr.netr.sum():>+8.0f}{(tr.res=='TARGET').mean():>7.1%}"
              f"{(wn.r.median() if len(wn) else float('nan')):>7.2f}{dd:>+8.1f}"
              f"{(e1.mean() if len(e1) else float('nan')):>+10.4f}{(e2.mean() if len(e2) else float('nan')):>+10.4f}")
        with gzip.open(f"{a.out}_{mode}_{tm}.jsonl.gz","wt") as fh:
            for _,t in tr.iterrows(): fh.write(json.dumps({q:(v.item() if hasattr(v,'item') else v) for q,v in t.items()})+"\n")
