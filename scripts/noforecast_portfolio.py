#!/usr/bin/env python3
"""NO-FORECAST portfolio + CVD-aware ceiling (Angus 23-Jul autonomous deep-dive).

Premise from the screens: the day does not announce itself pre-market (best day-level AUC
~0.58), but the TAPE AT ENTRY does (per-trade survivors). So: trade BOTH books EVERY day —
no day prediction, no book prediction — and let the OOF-surviving trade rules do the work:

  B2: pre-market CVD agrees with direction AND |cvd_PM| above the 2025 Q1 cut
      AND session-CVD path NOT at the day's lows (path_lo == 0)
  B : last-15-min tape delta agrees with direction AND no 15-min divergence (div15 == 0)
  A : pre-market CVD agrees with direction

All numeric thresholds fitted on 2025 ONLY. Report 2025 / 2026 P&L, per book, daily
drawdown, vs the oracle+SD ceiling. Also: CEILING v2 = per-day oracle+SD computed on the
FILTERED books (same sim universe), i.e. what the ceiling becomes once CVD lives inside
the books. Plus the post-open (9:50) book-read test on late trades.

    python -m scripts.noforecast_portfolio
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def main():
    S = pd.read_parquet("output/trade_angles.parquet")
    S["win"] = S.dollars > 0

    q1 = S[(S.pattern == "B2") & (S.yr == 2025) & (S.conf_PM == 1)].cvd_PM.abs().quantile(0.25)
    print(f"B2 |cvd_PM| floor (2025 Q1 fit): {q1:.0f}\n")
    keep = pd.Series(False, index=S.index)
    b2 = (S.pattern == "B2") & (S.conf_PM == 1) & (S.cvd_PM.abs() >= q1) & (S.path_lo == 0)
    bb = (S.pattern == "B") & (S.conf_last15 == 1) & (S.div15 == 0)
    aa = (S.pattern == "A") & (S.conf_PM == 1)
    keep = b2 | bb | aa
    K = S[keep]

    B = pd.read_parquet("output/dayflow_features.parquet")[["oracle_sd", "E3", "E4", "yr"]]
    for yr in (2025, 2026):
        d = K[K.yr == yr]; a = S[S.yr == yr]
        ceil = B[B.yr == yr].oracle_sd.sum()
        days = a.day.nunique()
        daily = d.groupby("day").dollars.sum()
        cum = daily.cumsum(); dd = (cum.cummax() - cum).max() if len(cum) else 0
        print(f"=== {yr} ===")
        print(f"  universe (both books, no rules): {len(a):4d} trades  ${a.dollars.sum():+8,.0f}")
        print(f"  NO-FORECAST portfolio          : {len(d):4d} trades  ${d.dollars.sum():+8,.0f}   "
              f"win {d.win.mean()*100:.0f}%  {len(d)/days:.1f} tr/day  maxDD ${dd:,.0f}")
        print(f"    by setup: " + "  ".join(f"{p} n{len(g)} ${g.dollars.sum():+,.0f}" for p, g in d.groupby("pattern")))
        print(f"    by book : " + "  ".join(f"{b} n{len(g)} ${g.dollars.sum():+,.0f}" for b, g in d.groupby("book")))
        print(f"  oracle+SD ceiling (raw books)  : ${ceil:+,.0f}   portfolio capture {d.dollars.sum()/ceil*100:.0f}%")

    # ---- CEILING v2: oracle+SD on FILTERED books (same sim universe, like-for-like) ----
    print("\n=== CEILING v2: what the ceiling becomes with the trade rules INSIDE the books ===")
    raw_day = S.groupby(["day", "book"]).dollars.sum().unstack(fill_value=0.0)
    fil_day = K.groupby(["day", "book"]).dollars.sum().unstack(fill_value=0.0)
    fil_day = fil_day.reindex(raw_day.index).fillna(0.0)
    for lbl, dd_ in [("raw sim books ", raw_day), ("filtered books", fil_day)]:
        dd_ = dd_.copy(); dd_["yr"] = dd_.index.str[:4]
        for yr in ("2025", "2026"):
            x = dd_[dd_.yr == yr]
            orc = np.maximum(np.maximum(x.get("E3", 0.0), x.get("E4", 0.0)), 0.0).sum()
            print(f"  {lbl} {yr}: oracle+SD ${orc:+,.0f}")

    # ---- post-open book read: among trades filling after 9:50, does the first-20-min
    #      move direction/size pick the better book for the rest of the morning? ----
    print("\n=== post-open (9:50) read gating LATE trades only ===")
    D = pd.read_parquet("output/dayflow_features.parquet")[["px_chg_OP", "cvd_OP"]]
    L = S.join(D, on="day")
    L["t"] = L.fillmi.dt.hour * 60 + L.fillmi.dt.minute
    late = L[L.t >= 9 * 60 + 50]
    thr = abs(late[late.yr == 2025].px_chg_OP).median()
    for yr in (2025, 2026):
        d = late[late.yr == yr]
        pick = np.where(d.px_chg_OP.abs() >= thr, "E4", "E3")     # big open move -> momentum book
        sel = d[d.book == pick]
        print(f"  {yr}: late trades both books ${d.dollars.sum():+8,.0f} (n={len(d)})   "
              f"OP-picked book only ${sel.dollars.sum():+8,.0f} (n={len(sel)})")


if __name__ == "__main__":
    main()
