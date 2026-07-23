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
Layer 2d IN-TRADE   : 3-minute cut (ANGUS 25-Jul ruling): if at fill+3min the trade is
                      >=0.11R underwater AND net delta since fill runs >=13 against the
                      position -> exit at market (realized = r_3). Thresholds = 2025 q40,
                      frozen. Flagged trades win 7%/11%; 47 losers vs 6 winners cut over 2yrs.
                      ONLY the 3-min horizon works — 5/10min exits lose money.
Layer 2e SIZING MODS: (ANGUS 26-Jul ruling, both shipped)
                      RULE 1 cold-grind cut: trailing-20 canon WR < 0.40 (past trades only)
                        AND one-sided 30m flow into fill (churn_flow_30 > 0.0292, 2025 median)
                        -> size x0.5. State-conditional; fires mostly in cold regimes.
                      RULE 2 good-PA boost: efficient 30m path into fill
                        (netpath_30 >= 0.3328, 2025 q90) and not Rule-1-flagged -> size x1.5.
Layer 3  GOVERNOR   : trailing-15 confirmed-trade (score>=4) win rate < 0.35 -> all sizes x0.5
                      (results-based; uses only past trades)

Validated 2025/2026 out-of-fit (full stack): +$22,532 / +$28,844, Jul-Sep +$754,
worst month -$312, maxDD $1.7k/$2.3k.
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
    # Layer 2d: 3-minute in-trade cut -> effective realized dollars for everything downstream
    try:
        I = pd.read_parquet("output/intrade_matrix.parquet")[["day", "book", "fill", "r_3", "fw_3"]]
        T = T.merge(I, on=["day", "book", "fill"], how="left")
        cut = (T.r_3 <= -0.1106) & (T.fw_3 <= -13)
        T["cut3"] = cut.fillna(False)
        T["eff_dollars"] = np.where(T.cut3, T.r_3 * T.risk * 20, T.dollars)
    except FileNotFoundError:
        T["cut3"] = False
        T["eff_dollars"] = T.dollars
    T["size"] = np.select([T.score <= 2, T.score == 3, T.score == 4, T.score == 5], [0, .5, 1, 1.5])
    hi = T[T.score >= 4].reset_index()
    hi["trailWR"] = hi.eff_dollars.gt(0).rolling(15).mean().shift(1)
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
    T["pl"] = T.eff_dollars * T["size"] * T.governor
    # Layer 2e: state-conditional sizing mods (Rules 1+2, thresholds 2025-frozen)
    try:
        BP = pd.read_parquet("output/badpa_matrix.parquet")[["day", "book", "fill",
                                                             "netpath_30", "churn_flow_30"]]
        T = T.merge(BP, on=["day", "book", "fill"], how="left")
        taken = T[T["size"] > 0].sort_values("fill")
        wins = (taken.eff_dollars > 0).astype(float)
        trail20 = wins.rolling(20).mean().shift(1)
        t20 = dict(zip(taken.index, trail20))
        cur = np.nan
        coldc = []
        for i in T.index:
            if i in t20 and t20[i] == t20[i]:
                cur = t20[i]
            coldc.append(bool(cur == cur and cur < 0.40))
        T["cold"] = coldc
        r1 = T["cold"] & (T.churn_flow_30 > 0.0292)
        r2 = (T.netpath_30 >= 0.3328) & ~r1
        T.loc[r1.fillna(False), "size"] *= 0.5
        T.loc[r2.fillna(False), "size"] *= 1.5
    except FileNotFoundError:
        pass
    T["pl"] = T.eff_dollars * T["size"] * T.governor
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
    T["pl"] = T.eff_dollars * T["size"] * T.governor
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
