#!/usr/bin/env python3
"""SIZE THE STAND-DOWN PRIZE (Angus 22 Jul). The entire 2025 loss is bleed from TRADING
both-books-red days; on genuinely tradeable days the agent already makes money. This measures
how much of that both-red bleed a mechanical pre-market-CVD stand-down gate actually catches
across 2025 H2 (the CVD-covered span), threshold trained OUT-OF-FIT on 2026.

Two gate framings, reported honestly:
  (A) low CONVICTION  -> stand down when |pre-market CVD| is in the bottom tail
      ("no one is committing before the open" -> chop / both-books-lose)
  (B) heavy SELLING   -> stand down when signed pre-market CVD is in the bottom tail

    python -m scripts.standdown_size_2025
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def load_premkt_cvd():
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
    pre = g[(hm >= 480) & (hm < 570)]                       # 08:00-09:30
    return pre.groupby(pre.index.strftime("%Y-%m-%d")).sum().rename("premkt_cvd")


def main():
    L = pd.read_csv("output/v07/walk_v07/ledger.csv")
    L["yr"] = L.day.str[:4].astype(int)
    L["both_red"] = (L.e3 <= 0) & (L.e4 <= 0)
    L["traded"] = L.act.isin(["MOMENTUM", "ROTATION"])
    pre = load_premkt_cvd()
    M = L.merge(pre, left_on="day", right_index=True, how="inner").copy()
    M["absc"] = M.premkt_cvd.abs()

    tr = M[M.yr == 2026]                                     # OUT-OF-FIT training year
    te = M[M.yr == 2025].copy()                              # 2025 H2 (CVD-covered)
    print(f"2025 CVD-covered days: {len(te)}   (both-red {int(te.both_red.sum())}, "
          f"agent traded {int(te.traded.sum())})")
    pool = te[te.both_red & te.traded].pl.sum()
    good = te[~te.both_red].pl.sum()
    print(f"  addressable both-red bleed (agent traded these): ${pool:+,.0f}")
    print(f"  P&L on genuinely tradeable days:                 ${good:+,.0f}")
    print(f"  agent actual 2025-covered P&L:                   ${te.pl.sum():+,.0f}\n")

    for col, name in (("absc", "(A) low CONVICTION  |CVD| bottom tail"),
                      ("premkt_cvd", "(B) heavy SELLING   signed CVD bottom tail")):
        print(f"### gate {name} — threshold from 2026, applied to 2025 ###")
        for q in (0.25, 0.33, 0.40):
            thr = tr[col].quantile(q)
            stood = te[col] < thr                            # gate fires -> force FLAT
            newpl = np.where(stood, 0.0, te.pl)
            delta = newpl.sum() - te.pl.sum()
            # diagnostics: of the days the gate stood down, how many were truly both-red?
            g = te[stood]
            br_caught = int((g.both_red).sum())
            good_killed = g[~g.both_red].pl.sum()            # money lost by gating good days
            bleed_saved = -g[g.both_red & g.traded].pl.sum()
            print(f"  q={q:.2f}: stood down {int(stood.sum()):3d} days "
                  f"({br_caught} both-red, {int(stood.sum())-br_caught} not)   "
                  f"2025 P&L ${te.pl.sum():+,.0f} -> ${newpl.sum():+,.0f}  ({delta:+,.0f})   "
                  f"[saved ${bleed_saved:+,.0f} bleed, gave back ${good_killed:+,.0f} on good days]")
        print()

    # precision/recall of framing (A) at q=0.33 as a both-red classifier
    thr = tr.absc.quantile(0.33)
    pred = te.absc < thr
    tp = int((pred & te.both_red).sum()); fp = int((pred & ~te.both_red).sum())
    fn = int((~pred & te.both_red).sum())
    prec = tp / max(tp + fp, 1) * 100
    rec = tp / max(tp + fn, 1) * 100
    base = te.both_red.mean() * 100
    print(f"framing (A) as a both-red detector @q=0.33: precision {prec:.0f}% "
          f"(base rate {base:.0f}%), recall {rec:.0f}%  [tp{tp} fp{fp} fn{fn}]")


if __name__ == "__main__":
    main()
