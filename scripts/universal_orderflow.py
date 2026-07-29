#!/usr/bin/env python3
"""UNIVERSAL order-flow-per-setup: BOTH books, EVERY footprint-covered day, no agent selection,
no book preference (Angus 23-Jul). Question: does a signal at entry universally lift a given
setup type (A/B/B2), out-of-fit across 2025 and 2026? If it holds regardless of book/day, it's a
real, pushable edge — independent of whether the agent decides to trade that day.

Universe = output/substrate_v2_signals.parquet (970 trades: E3+E4, all days, v2-tagged).
Signals recomputed fresh at entry (3 min ending at fill, within +-2pt of entry):
  cvd_conf    pre-market 08:00-09:30 CVD net delta agrees with trade direction
  absorption  LOOSENED: a minute >=1.5x median vol AND two-sided min(B,A)/max>=0.55
  delta_div   net delta OPPOSES the trade move
  stacked_imb >=2 stacked 300% diagonal imbalances on the trade side

    python -m scripts.universal_orderflow
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.orderflow_by_setup import load_fp_all, stacked_imb
from scripts.orderflow_combined import premkt_cvd
NY = "America/New_York"


def main():
    S = pd.read_parquet("output/substrate_v2_signals.parquet")[
        ["day", "book", "fill", "direction", "entry", "dollars", "pattern", "yr"]].copy()
    fp = load_fp_all()
    dmed = fp.groupby(fp.index.strftime("%Y-%m-%d %H:%M")).volume.sum()
    dmed = dmed.groupby(dmed.index.str[:10]).median()
    pcvd = premkt_cvd()
    S["fillmi"] = pd.to_datetime(S.fill, utc=True, format="mixed").dt.tz_convert(NY).dt.floor("min")
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
                a = 1
        net = wf.sd.sum()
        dd.append(int((net < 0 and t.direction == "long") or (net > 0 and t.direction == "short")))
        im.append(int(stacked_imb(wf, t.direction) >= 2)); ab.append(a)
    S["absorption"] = ab; S["delta_div"] = dd; S["stacked_imb"] = im
    S["cvd_conf"] = S.apply(lambda r: int((pcvd.get(r.day, 0) > 0 and r.direction == "long")
                                          or (pcvd.get(r.day, 0) < 0 and r.direction == "short")), axis=1)
    S = S.dropna(subset=["absorption"]); S["win"] = S.dollars > 0
    S["nsig"] = S.absorption + S.delta_div + S.stacked_imb
    S.to_parquet("output/universal_orderflow.parquet")
    print(f"UNIVERSE both books, all days, footprint-covered: {len(S)} trades "
          f"(2025 {int((S.yr==2025).sum())}, 2026 {int((S.yr==2026).sum())})")
    print(f"  book mix: {S.book.value_counts().to_dict()}   patterns: {S.pattern.value_counts().to_dict()}\n")

    for setup in ["A", "B", "B2"]:
        d = S[S.pattern == setup]
        print(f"===== SETUP {setup}  n={len(d)}  base win {d.win.mean()*100:.0f}%  ${d.dollars.mean():+.0f}/t  tot ${d.dollars.sum():+,.0f} =====")
        for s in ["cvd_conf", "absorption", "delta_div", "stacked_imb"]:
            line = f"  {s:11s}"
            for yr in (2025, 2026, "ALL"):
                dy = d if yr == "ALL" else d[d.yr == yr]
                on = dy[dy[s] == 1]; off = dy[dy[s] == 0]
                if len(on) < 3 or len(off) < 3:
                    line += f"   {str(yr):>4}: (few on{len(on)}/off{len(off)})        "
                else:
                    line += f"   {str(yr):>4}: on{len(on):3d} {on.win.mean()*100:2.0f}%/${on.dollars.mean():+5.0f}  off{len(off):3d} {off.win.mean()*100:2.0f}%/${off.dollars.mean():+5.0f}"
            print(line)
        print()


if __name__ == "__main__":
    main()
