#!/usr/bin/env python3
"""Combined order-flow-per-setup (Angus 22 Jul), OUT-OF-FIT across 2025 + 2026, on the actual
correctly-tagged agent trades:
  2025 = real fresh-eyes trades (output/fresheyes_trades_2025.parquet)
  2026 = chained trades re-tagged v2 (output/chained_trades.csv, MOMENTUM=E4/ROTATION=E3)

Signals at entry (3 min ending at fill, within ±2pt of entry):
  absorption  (LOOSENED: a minute >=1.5x median vol AND two-sided min(B,A)/max>=0.55)
  delta_div   (net delta OPPOSES the trade move -> fade/absorb)
  stacked_imb (>=2 stacked 300% diagonal imbalances on the trade side)
  cvd_conf    (pre-market 08:00-09:30 CVD net delta agrees with trade direction)

Per setup (A/B/B2), per year + combined: win% / $ with-vs-without each signal, PLUS the
1/3-2/3-3/3 signal-count breakdown over {absorption, delta_div, stacked_imb}.

    python -m scripts.orderflow_combined
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.orderflow_by_setup import load_fp_all, stacked_imb
NY = "America/New_York"


def premkt_cvd():
    fr = []
    for f in ("footprint_q3_2025", "footprint_q4_2025", "footprint_feb_mar2026",
              "footprint_apr2026", "footprint_may_jul2026"):
        p = Path(f"data/reference/cvd/{f}.parquet")
        if p.exists():
            d = pd.read_parquet(p, columns=["ts_minute", "side", "volume"])
            d["s"] = np.where(d.side == "B", d.volume, -d.volume)
            fr.append(d.groupby("ts_minute")["s"].sum())
    g = pd.concat(fr).groupby(level=0).sum(); g.index = g.index.tz_convert(NY)
    hm = g.index.hour * 60 + g.index.minute
    pre = g[(hm >= 480) & (hm < 570)]
    return pre.groupby(pre.index.strftime("%Y-%m-%d")).sum()


def load_trades():
    a = pd.read_parquet("output/fresheyes_trades_2025.parquet")[
        ["day", "fill", "direction", "entry", "dollars", "pattern"]].assign(yr=2025)
    c = pd.read_csv("output/chained_trades.csv")
    c = pd.DataFrame({"day": c.day, "fill": c.fill_ts, "direction": c.direction,
                      "entry": c.entry, "dollars": c.dollars, "pattern": c.pattern}).assign(yr=2026)
    return pd.concat([a, c], ignore_index=True)


def main():
    S = load_trades()
    fp = load_fp_all()
    dmed = fp.groupby(fp.index.strftime("%Y-%m-%d %H:%M")).volume.sum()
    dmed = dmed.groupby(dmed.index.str[:10]).median()
    pcvd = premkt_cvd()
    S["fillmi"] = pd.to_datetime(S.fill, utc=True).dt.tz_convert(NY).dt.floor("min")
    ab, dd, im = [], [], []
    for t in S.itertuples():
        try:
            sl = fp.loc[t.fillmi - pd.Timedelta(minutes=2):t.fillmi]
        except KeyError:
            ab.append(np.nan); dd.append(np.nan); im.append(np.nan); continue
        wf = sl[(sl.price >= t.entry - 2) & (sl.price <= t.entry + 2)]
        if wf.empty:
            ab.append(np.nan); dd.append(np.nan); im.append(np.nan); continue
        med = dmed.get(t.fillmi.strftime("%Y-%m-%d"), np.nan); a = 0
        for _, g in wf.groupby(level=0):
            b = g[g.side == "B"].volume.sum(); aa = g[g.side == "A"].volume.sum()
            if med == med and (b + aa) >= 1.5 * med and min(b, aa) / max(max(b, aa), 1) >= 0.55:
                a = 1                                       # LOOSENED absorption
        net = wf.sd.sum()
        dd.append(int((net < 0 and t.direction == "long") or (net > 0 and t.direction == "short")))
        im.append(int(stacked_imb(wf, t.direction) >= 2)); ab.append(a)
    S["absorption"] = ab; S["delta_div"] = dd; S["stacked_imb"] = im
    S["cvd_conf"] = S.apply(lambda r: int((pcvd.get(r.day, 0) > 0 and r.direction == "long")
                                          or (pcvd.get(r.day, 0) < 0 and r.direction == "short")), axis=1)
    S = S.dropna(subset=["absorption"]); S["win"] = S.dollars > 0
    S["nsig"] = S.absorption + S.delta_div + S.stacked_imb
    print(f"trades w/ footprint: {len(S)}  (2025 {int((S.yr==2025).sum())}, 2026 {int((S.yr==2026).sum())})")
    S.to_parquet("output/orderflow_combined.parquet")

    for setup in ["A", "B", "B2"]:
        d = S[S.pattern == setup]
        print(f"\n===== {setup}  n={len(d)}  base win {d.win.mean()*100:.0f}%  ${d.dollars.mean():+.0f}/t  tot ${d.dollars.sum():+,.0f} =====")
        for s in ["absorption", "delta_div", "stacked_imb", "cvd_conf"]:
            line = f"  {s:12s}"
            for yr in (2025, 2026, "ALL"):
                dy = d if yr == "ALL" else d[d.yr == yr]
                on = dy[dy[s] == 1]; off = dy[dy[s] == 0]
                if len(on) < 2 or len(off) < 2:
                    line += f"  {str(yr):>4}: on{len(on)} (few)      "
                else:
                    line += f"  {str(yr):>4}: on{len(on):2d} {on.win.mean()*100:2.0f}%/${on.dollars.mean():+5.0f}  off{len(off):2d} {off.win.mean()*100:2.0f}%/${off.dollars.mean():+5.0f}"
            print(line)
        print(f"  -- signal count (absorp+delta_div+stacked) --")
        for k in [0, 1, 2, 3]:
            s = d[d.nsig == k]
            if len(s):
                print(f"     {k}/3: n={len(s):3d}  win {s.win.mean()*100:3.0f}%  ${s.dollars.mean():+6.0f}/t  tot ${s.dollars.sum():+,.0f}")


if __name__ == "__main__":
    main()
