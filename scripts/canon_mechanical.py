#!/usr/bin/env python3
"""THE CANON MECHANICAL BOOK — window-native edition (Angus rulings 25-27 Jul).

Two windows, two books of confluences, one shared skeleton. Pre-market is frozen as
originally shipped; the golden window runs its own checks re-derived from the raw gold
trade data (27-Jul campaign: 8 screen->adversarial-verify families, gold-only).

Layer 0  HARD GATES : stop 7-60pts; universe = both books, every day, no book choosing,
                      no day forecasting.

Layer 1  VALIDATION (5 binary checks -> score, per window):
  PRE  (unchanged) : W wall-behind absent | F fill-bar delta confirms | T d15 tape
                     >= 2025-q25 | G vwap-side geometry >= 2025-q25 | C PM-window CVD conf
  GOLD (native)    : D wall exists AHEAD (magnet to trade into; the toxic state is
                     "only wall on the book is behind you" — WR 14%/12%)
                     Tc d15_conf tape aligned
                     X vol expanding (bbw_state >= 2025-GOLD q75)
                     AGE overnight extreme old (>= 2025-GOLD q50 minutes)
                     PAQ efficient 30m approach (netpath_30 >= 2025-GOLD q25)

Layer 2  SIZING     : score<=2 -> 0 | 3 -> 0.5 | 4 -> 1.0 | 5 -> 1.5

Layer 2q GOLD QUALITY TIER (27-Jul ruling): Q = count of 6 quality bits —
                      WALLSZ  wall ahead >= 7 contracts (absolute size, 2025-GOLD q50)
                      BIGFD   |fill-minute delta| >= 173 (2025-GOLD q75)
                      T2      fill-minute delta aligned OR >=3 of last 5 min opposed
                              (absorption fill into counter-flow)
                      TRIG    >11 engine triggers last 30m (busy tape GOOD in gold)
                      VWAPD   entry >= 0.107 SD beyond vwap in trade direction
                      LONSLOPE London cum-delta OLS slope dir-signed >= -0.0961
                      Q <= 1 -> NO TRADE (structure without quality; 12/16 losers incl.
                                every 53-56pt-stop monster; WATCH ITEM: cell is only 16
                                trades over 2 yrs — first thing to re-test on 2023/24)
                      Q >= 3 -> one ladder step up (cap 1.5). Boost cell WR 83%/82%.

Layer 2b ESCALATION : trade #2+ of the day requires score >= 4 (window-native score)
Layer 2c ESCALATION : day P&L < 0 -> require both structure checks (pre W+T / gold D+Tc),
                      A-setups exempt; day P&L <= -$400 -> done for the day
Layer 2d IN-TRADE   : 3-min cut (r_3 <= -0.1106 AND fw_3 <= -13 -> exit at r_3).
                      NOTE (gold autopsy): in gold this cut is EV-neutral — gold losers
                      already scratch near -0.5R; kept for pre where it earns.
Layer 2e SIZING MODS: R1 cold-grind cut (trail-20 WR<0.40 & churn_flow_30>0.0292 -> x0.5)
                      R2 good-PA boost (netpath_30 >= 0.3328 -> x1.5, not R1-flagged)
Layer 3  GOVERNOR   : trailing-15 confirmed-trade (score>=4) WR < 0.35 -> all sizes x0.5

All gold thresholds are frozen 2025-GOLDEN-WINDOW quantiles (2026 = out-of-fit).
Validated full stack: 2025 +$31,175 / 2026 +$40,189, Jul-Sep +$2,034/-$98,
12/13 green months, worst month -$98, maxDD $2,492/$1,872.
Holdout list for 2023/24: Q-tier mapping (esp. the Q<=1 cut), gold 5-min time-stop,
DOM_EARLY calendar effect, dead-tape W-weighting, 0.8x stops.

Inputs: output/trade_matrix.parquet, badpa_matrix.parquet, intrade_matrix.parquet,
gold_quality.parquet (python -m scripts.gold_quality). Writes output/canon_book.parquet.

    python -m scripts.canon_mechanical
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def build_canon(T):
    """T = trade_matrix rows. Returns the canon book with score, Q, size, governor, pl."""
    T = T.copy()
    long = T.direction == "long"
    # --- pre-market checks (frozen as originally shipped; thresholds pooled-2025) ---
    T["W"] = np.where(long, T.dep_wall_below_d.isna(), T.dep_wall_above_d.isna()).astype(float)
    T["W"] = T["W"].where(T.dep_thick.notna())
    T["F"] = (T.fill_delta_conf == 1).astype(float)
    d15dir = T.d15 * np.where(long, 1, -1)
    T["Tp"] = (d15dir >= d15dir[T.yr == 2025].quantile(0.25)).astype(float)
    T["G"] = (T.ent_vs_vwap_sd_dir >= T[T.yr == 2025].ent_vs_vwap_sd_dir.quantile(0.25)).astype(float)
    T["C"] = np.where(T.win_ == "pre", (T.conf_PM == 1), (T.conf_LON == 1)).astype(float)
    # --- golden-native checks (thresholds = frozen 2025-GOLD quantiles) ---
    BP = pd.read_parquet("output/badpa_matrix.parquet")[
        ["day", "book", "fill", "netpath_30", "bbw_state", "churn_flow_30", "trigdens_30"]]
    T = T.merge(BP, on=["day", "book", "fill"], how="left")
    g25 = T[(T.win_ == "gold") & (T.yr == 2025)]
    T["D"] = pd.Series(np.where(long, T.dep_wall_above_d.notna(), T.dep_wall_below_d.notna()),
                       index=T.index).astype(float).where(T.dep_thick.notna())
    T["Tc"] = (T.d15_conf == 1).astype(float)
    T["X"] = (T.bbw_state >= g25.bbw_state.quantile(0.75)).astype(float).where(T.bbw_state.notna())
    T["AGE"] = (T.on_extreme_age >= g25.on_extreme_age.quantile(0.50)).astype(float).where(T.on_extreme_age.notna())
    T["PAQ"] = (T.netpath_30 >= g25.netpath_30.quantile(0.25)).astype(float).where(T.netpath_30.notna())

    T = T[(T.risk >= 7) & (T.risk <= 60)].sort_values("fill").reset_index(drop=True)
    pre_score = T[["W", "F", "Tp", "G", "C"]].sum(axis=1)
    gold_score = T[["D", "Tc", "X", "AGE", "PAQ"]].sum(axis=1)
    T["score"] = np.where(T.win_ == "pre", pre_score, gold_score)

    # Layer 2d: 3-minute in-trade cut -> effective realized dollars downstream
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

    # Layer 2q: golden quality tier
    long2 = T.direction == "long"
    wall_ahead_sz = np.where(long2, T.dep_wall_above_sz, T.dep_wall_below_sz)
    T["WALLSZ"] = ((T.D == 1) & (pd.Series(wall_ahead_sz, index=T.index) >= 7)).astype(float)
    T["BIGFD"] = (T.fill_delta.abs() >= 173).astype(float)
    try:
        GQ = pd.read_parquet("output/gold_quality.parquet")
        T = T.merge(GQ, on=["day", "book", "fill"], how="left")
        T["T2"] = ((T.fill_delta_conf == 1) | (T.bp5opp == 1)).astype(float)
        T["LONSLOPE"] = (T.lon_slope_d >= -0.0961).astype(float)
    except FileNotFoundError:
        T["T2"] = (T.fill_delta_conf == 1).astype(float)
        T["LONSLOPE"] = np.nan
    T["TRIG"] = (T.trigdens_30 > 11).astype(float)
    T["VWAPD"] = (T.ent_vs_vwap_sd_dir >= 0.107).astype(float)
    T["Q"] = T[["WALLSZ", "BIGFD", "T2", "TRIG", "VWAPD", "LONSLOPE"]].sum(axis=1)
    gold_live = (T.win_ == "gold") & (T["size"] > 0)
    T.loc[gold_live & (T.Q <= 1), "size"] = 0.0          # structure without quality: no trade
    bq = gold_live & (T.Q >= 3) & (T["size"] > 0)
    T.loc[bq, "size"] = np.minimum(T.loc[bq, "size"] + 0.5, 1.5)   # quality stack: step up

    # Layer 3 governor (window-native confirmed trades)
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
    T["pl"] = T.eff_dollars * T["size"] * T.governor
    # Layer 2c: within-day escalation ladder (react to realized losses only)
    T["struct"] = np.where(T.win_ == "pre", T.W + T.Tp, T.D.fillna(0) + T.Tc)
    live = T[T["size"] > 0].sort_values("fill")
    drop = []
    for d, g in live.groupby("day"):
        daypl = 0.0
        out = False
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
        pre = d[d.win_ == "pre"].pl.sum()
        gld = d[d.win_ == "gold"].pl.sum()
        print(f"{yr}: ${d.pl.sum():+9,.0f}  (pre ${pre:+,.0f} gold ${gld:+,.0f}; {len(t)} trades, "
              f"{t.day.nunique()} days, WR {(t.dollars>0).mean()*100:.0f}%, maxDD ${dd:,.0f})")
    print(f"\nwrote output/canon_book.parquet ({len(C)} rows)")


if __name__ == "__main__":
    main()
