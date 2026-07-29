#!/usr/bin/env python3
"""PRE-MARKET CVD STAND-DOWN GATE — P&L test (Angus 22 Jul). The one signal that held
out-of-fit was pre-market CVD conviction for stand-down (~0.58). Does acting on it save real
money? Stand down (flat the day) when pre-market CVD sits in the low-conviction tail; threshold
set on the OTHER regime (out-of-fit). Tested on the fresh-eyes agent's own daily P&L and on a
fixed always-E4 book, 2025 H2 + 2026.

    python -m scripts.standdown_gate_pnl
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def load_cvd_premkt():
    fr = []
    for f in ("footprint_q3_2025", "footprint_q4_2025", "footprint_feb_mar2026",
              "footprint_apr2026", "footprint_may_jul2026"):
        p = Path(f"data/reference/cvd/{f}.parquet")
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["ts_minute", "side", "volume"])
        d["s"] = np.where(d.side == "B", d.volume, -d.volume)
        fr.append(d.groupby("ts_minute")["s"].sum())
    g = pd.concat(fr).groupby(level=0).sum()
    g.index = g.index.tz_convert(NY)
    g = g.sort_index()
    hm = g.index.hour * 60 + g.index.minute
    pre = g[(hm >= 480) & (hm < 570)]                      # 08:00-09:30
    day = pre.groupby(pre.index.strftime("%Y-%m-%d")).sum()
    return day.rename("premkt_cvd")


def main():
    L = pd.read_csv("output/v07/walk_v07/ledger.csv")[["day", "pl", "e3", "e4", "stance"]]
    pre = load_cvd_premkt()
    M = L.merge(pre.rename("premkt_cvd"), left_on="day", right_index=True, how="inner")
    M["yr"] = M.day.str[:4].astype(int)
    M = M[M.yr.isin([2025, 2026])].copy()
    print(f"{len(M)} days with agent P&L + pre-market CVD  (2025 {int((M.yr==2025).sum())}, 2026 {int((M.yr==2026).sum())})\n")

    for pnl_col, name in (("pl", "AGENT's own decisions"), ("e4", "fixed always-E4 book")):
        print(f"### stand-down gate on {name} ###")
        Q = 0.33                                            # FIXED rule: stand down bottom third by conviction
        for train, test in ((2026, 2025), (2025, 2026)):
            tr, te = M[M.yr == train], M[M.yr == test]
            base = te[pnl_col].sum()
            thr = tr.premkt_cvd.quantile(Q)                 # threshold from TRAIN only (out-of-fit)
            stood = te.premkt_cvd < thr
            gated = te[~stood][pnl_col].sum()
            cut = te[stood][pnl_col].sum()
            mark = "IMPROVES" if gated > base else "NO HELP"
            print(f"  train {train} -> test {test}: base ${base:+7,.0f}  ->  gated ${gated:+7,.0f}  "
                  f"({mark} {gated-base:+,.0f})   [stood down {int(stood.sum())}/{len(te)} low-conv days worth ${cut:+,.0f}]")
        print()

    # sanity: are low-pre-market-CVD days actually worse? (the premise)
    print("### premise check: agent daily P&L by pre-market CVD tercile ###")
    for yr in (2025, 2026):
        s = M[M.yr == yr].copy()
        s["terc"] = pd.qcut(s.premkt_cvd, 3, labels=["low", "mid", "high"])
        g = s.groupby("terc").pl.agg(["mean", "sum", "size"])
        print(f"  {yr}: " + "  ".join(f"{t} ${g.loc[t,'sum']:+6,.0f}(${g.loc[t,'mean']:+4.0f}/d,n{int(g.loc[t,'size'])})" for t in ["low","mid","high"]))


if __name__ == "__main__":
    main()
