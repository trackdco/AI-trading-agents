#!/usr/bin/env python3
"""THE CANON MECHANICAL BOOK (Angus 25-Jul ruling: ship as default; do not divert unless
explicitly asked).

Layer 0  HARD GATES : stop >= 7pts (pre) / engine post-open floor (gold); stop <= 60pts
                      (ANGUS 25-Jul ruling: 29 trades carried 60-136pt stops, 0/12 wins ever
                      reached 2R — structurally sub-doctrine, banned); universe = both books,
                      every day, no book choosing, no day forecasting.
Layer 1  VALIDATION : 5 checks at fill —
                      W wall-behind absent (no visible depth behind entry)
                      F fill-bar delta confirms direction
                      T last-15-min tape not heavily against (dir-signed d15 >= 2025-q25)
                      G geometry aligned (dir-signed VWAP-side >= 2025-q25)
                      C window-correct CVD (PM conf if pre-fill, LON conf if gold-fill)
Layer 2  SIZING     : score<=2 -> 0 | 3 -> 0.5 | 4 -> 1.0 | 5 -> 1.5
Layer 2b ESCALATION : trade #2+ of the day requires score >= 4 (ANGUS 25-Jul ruling: the
                      follow-up entry needs full conviction; strict upgrade +$1.1k, never worse)
Layer 2c ESCALATION : within-day ladder (ANGUS 25-Jul ruling, results-based, no forecasting):
                      day running P&L < 0  -> entries require BOTH structure checks (W+T),
                      A-setups exempt (reversals thrive in bad tape);
                      day running P&L <= -$400 -> sit out the rest of the day.
Layer 3  GOVERNOR   : trailing-15 confirmed-trade (score>=4) win rate < 0.35 -> all sizes x0.5
                      (results-based; uses only past trades)

Validated 2025/2026 out-of-fit (full stack): +$18,171 / +$29,716, worst month -$789.
Writes output/canon_book.parquet (one row per trade with score/size/governor/final P&L).

    python -m scripts.canon_mechanical
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def build_canon(T):
    """T = trade_matrix rows. Returns the canon book with score, size, governor, pl."""
    T = T.copy()
    long = T.direction == "long"
    T["W"] = np.where(long, T.dep_wall_below_d.isna(), T.dep_wall_above_d.isna()).astype(float)
    T["W"] = T["W"].where(T.dep_thick.notna())
    T["F"] = (T.fill_delta_conf == 1).astype(float)
    d15dir = T.d15 * np.where(long, 1, -1)
    T["Tp"] = (d15dir >= d15dir[T.yr == 2025].quantile(0.25)).astype(float)
    T["G"] = (T.ent_vs_vwap_sd_dir >= T[T.yr == 2025].ent_vs_vwap_sd_dir.quantile(0.25)).astype(float)
    T["C"] = np.where(T.win_ == "pre", (T.conf_PM == 1), (T.conf_LON == 1)).astype(float)
    T = T[(T.risk >= 7) & (T.risk <= 60)].sort_values("fill").reset_index(drop=True)
    T["score"] = T[["W", "F", "Tp", "G", "C"]].sum(axis=1)
    T["size"] = np.select([T.score <= 2, T.score == 3, T.score == 4, T.score == 5], [0, .5, 1, 1.5])
    hi = T[T.score >= 4].reset_index()
    hi["trailWR"] = hi.dollars.gt(0).rolling(15).mean().shift(1)
    trail = dict(zip(hi["index"], hi.trailWR))
    cur = np.nan
    gov = []
    twr = pd.Series(T.index.map(trail))
    for i in range(len(T)):
        if not np.isnan(twr[i]):
            cur = twr[i]
        gov.append(0.5 if (not np.isnan(cur) and cur < 0.35) else 1.0)
    T["governor"] = gov
    # Layer 2b: second-and-later trades of the day require score >= 4
    taken = T[T["size"] > 0]
    nth = taken.groupby("day").cumcount() + 1
    T["nth"] = nth.reindex(T.index)
    esc = (T["nth"] >= 2) & (T.score < 4)
    T.loc[esc.fillna(False), "size"] = 0.0
    T["pl"] = T.dollars * T["size"] * T.governor
    # Layer 2c: within-day escalation ladder (react to realized losses only)
    T["struct"] = T.W + T.Tp
    live = T[T["size"] > 0].sort_values("fill")
    drop = []
    for d, g in live.groupby("day"):
        daypl = 0.0; out = False
        for r in g.itertuples():
            if out or (daypl < 0 and r.struct < 2 and r.pattern != "A"):
                drop.append(r.Index)
            else:
                daypl += r.pl
            if daypl <= -400:
                out = True
    T.loc[drop, "size"] = 0.0
    T["pl"] = T.dollars * T["size"] * T.governor
    return T


def main():
    T = pd.read_parquet("output/trade_matrix.parquet")
    C = build_canon(T)
    C.to_parquet("output/canon_book.parquet")
    for yr in (2025, 2026):
        d = C[C.yr == yr]
        t = d[d["size"] > 0]
        cum = t.groupby("day").pl.sum().cumsum()
        dd = (cum.cummax() - cum).max() if len(cum) else 0
        print(f"{yr}: ${d.pl.sum():+9,.0f}  ({len(t)} trades, {t.day.nunique()} days, "
              f"WR {(t.dollars>0).mean()*100:.0f}%, maxDD ${dd:,.0f})")
    print(f"\nwrote output/canon_book.parquet ({len(C)} rows)")


if __name__ == "__main__":
    main()
