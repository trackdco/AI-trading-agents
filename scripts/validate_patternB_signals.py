#!/usr/bin/env python3
"""OUT-OF-FIT validation of the pattern-B signal-count edge (Angus 22 Jul). Reconstructs ALL
pattern-B trades (both books, engine-generated) for 2025 H2 (Q3+Q4, footprint-covered) AND 2026,
computes the three entry signals (absorption / delta-divergence / stacked-imbalance) with the
SAME fixed definitions, and breaks down win-rate + P&L by how many fire (0/1/2/3). If 2025 shows
the same 2+ threshold as 2026, the edge is real; if not, it was curve-fit to 2026.

    python -m scripts.validate_patternB_signals
"""
import sys
from datetime import time as dtime
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load
from src.backtest.engine import load_backtest_config, simulate
NY = "America/New_York"


def load_fp_all():
    fr = []
    for f in ("footprint_q3_2025","footprint_q4_2025","footprint_feb_mar2026","footprint_apr2026","footprint_may_jul2026"):
        p = Path(f"data/reference/cvd/{f}.parquet")
        if not p.exists(): continue
        d = pd.read_parquet(p, columns=["ts_minute","price","side","volume"])
        ny = d.ts_minute.dt.tz_convert(NY); hm = ny.dt.hour.values*60+ny.dt.minute.values
        keep = (hm>=475)&(hm<=620)                      # 07:55-10:20 only -> small
        d = d[keep].copy(); d["mi"] = ny[keep].dt.floor("min").values
        d["sd"] = np.where(d.side=="B", d.volume, -d.volume)
        fr.append(d[["mi","price","side","volume","sd"]])
    return pd.concat(fr, ignore_index=True).sort_values("mi").set_index("mi")


def stacked_imb(wf, direction):
    lv = wf.pivot_table(index="price", columns="side", values="volume", aggfunc="sum").fillna(0)
    lv.columns = [str(c) for c in lv.columns]
    if "A" not in lv or "B" not in lv or len(lv) < 2: return 0
    lv = lv.sort_index(); best = stack = 0
    for i in range(1, len(lv)):
        buy = lv["A"].iloc[i] >= 3*max(lv["B"].iloc[i-1],1)
        sell = lv["B"].iloc[i-1] >= 3*max(lv["A"].iloc[i],1)
        hit = buy if direction=="long" else sell
        stack = stack+1 if hit else 0; best = max(best,stack)
    return best


def reconstruct(months, trig_src, df):
    base = load_backtest_config().model_copy(update={"win_start": dtime(8,0), "win_end": dtime(10,15),
                                                     "max_trades_per_day": 2})
    cfg_e3, cfg_e4 = books(base)
    rows = []
    for m in months:
        trigs = [t for t in trig_src if t.ts[:7] == m]
        if not trigs: continue
        end = pd.Timestamp((pd.Timestamp(m+"-01", tz=NY)+pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        start = pd.Timestamp((pd.Timestamp(m+"-01")-pd.Timedelta(days=25)), tz=NY)
        seg = df[(df.ts_event>=start)&(df.ts_event<=end)].reset_index(drop=True)
        for book, cfg in (("E3",cfg_e3),("E4",cfg_e4)):
            tr,_,_ = simulate(seg, trigs, cfg)
            for r in tr:
                if r.pattern != "B": continue
                rows.append(dict(day=r.trade_date, book=book, fill=str(r.fill_ts),
                                 direction=r.direction, entry=r.entry, dollars=r.dollars))
    return pd.DataFrame(rows)


def add_signals(B, fp, dmed):
    B = B.copy(); B["fillmi"] = pd.to_datetime(B.fill, utc=True).dt.tz_convert(NY).dt.floor("min")
    ab,dd,im = [],[],[]
    for t in B.itertuples():
        w0 = t.fillmi - pd.Timedelta(minutes=2)
        try: sl = fp.loc[w0:t.fillmi]
        except KeyError: ab.append(np.nan);dd.append(np.nan);im.append(np.nan); continue
        wf = sl[(sl.price>=t.entry-2.0)&(sl.price<=t.entry+2.0)]
        if wf.empty: ab.append(np.nan);dd.append(np.nan);im.append(np.nan); continue
        med = dmed.get(t.fillmi.strftime("%Y-%m-%d"), np.nan)
        a = 0
        for _,g in wf.groupby(level=0):
            bb=g[g.side=="B"].volume.sum();aa=g[g.side=="A"].volume.sum()
            if med==med and (bb+aa)>=2.5*med and min(bb,aa)/max(max(bb,aa),1)>=0.7: a=1
        net = wf.sd.sum()
        d = int((net<0 and t.direction=="long") or (net>0 and t.direction=="short"))
        s = int(stacked_imb(wf,t.direction)>=2)
        ab.append(a);dd.append(d);im.append(s)
    B["absorption"]=ab;B["delta_div"]=dd;B["stacked_imb"]=im
    return B.dropna(subset=["absorption"])


def breakdown(B, label):
    B = B.copy(); B["win"]=B.dollars>0; B["nsig"]=B.absorption+B.delta_div+B.stacked_imb
    print(f"\n=== {label}: pattern-B win-rate by # signals firing ===")
    print(f"  all pattern B: n={len(B)}  win {B.win.mean()*100:.0f}%  ${B.dollars.mean():+.0f}/t  total ${B.dollars.sum():+,.0f}")
    print(f"  {'# firing':10s} {'n':>4s} {'win%':>6s} {'$/trade':>9s} {'total':>10s}")
    for k in [0,1,2,3]:
        s=B[B.nsig==k]
        if len(s)==0: print(f"  {k} of 3     {0:4d}"); continue
        print(f"  {k} of 3     {len(s):4d} {s.win.mean()*100:5.0f}% {s.dollars.mean():+8.0f} {s.dollars.sum():+9,.0f}")
    g2=B[B.nsig>=2]
    print(f"  >=2 firing  {len(g2):4d} {g2.win.mean()*100:5.0f}% {g2.dollars.mean():+8.0f} {g2.dollars.sum():+9,.0f}")


def main():
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    fp = load_fp_all()
    dmed = fp.groupby(fp.index.strftime("%Y-%m-%d %H:%M")).volume.sum()
    dmed = dmed.groupby(dmed.index.str[:10]).median()
    t2325 = load(["output/triggers_hist2326_ob.csv"])       # covers 2025
    t26 = load(["output/triggers_fullsession.csv"])          # 2026-02..07
    M25 = [f"2025-{mm:02d}" for mm in range(6,13)]
    M26 = [f"2026-{mm:02d}" for mm in range(2,8)]
    print("reconstructing 2025 H2 pattern-B trades...")
    B25 = add_signals(reconstruct(M25, t2325, df), fp, dmed)
    print("reconstructing 2026 pattern-B trades...")
    B26 = add_signals(reconstruct(M26, t26, df), fp, dmed)
    breakdown(B25, "2025 H2 (OUT-OF-FIT)")
    breakdown(B26, "2026 (in-sample reference)")


if __name__ == "__main__":
    main()
