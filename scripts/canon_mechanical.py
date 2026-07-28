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
from scripts.live_thresholds import TH  # frozen thresholds (LIVE-STACK #1)  # noqa: E402


def build_canon(T, news_gate=None, dead_zones=None, escalation_keys=("day",)):
    """T = trade_matrix rows. Returns the canon book with score, Q, size, governor, pl.

    news_gate: optional object exposing `.blocks(ts_et) -> bool`, True where a PRE-OPEN
    HIGH-IMPACT RELEASE lands after the fill (ANGUS RULING 2026-07-26 — "it should not be
    trading from 8-8:30 when there is high impact news at 8:30"). Applied as size -> 0
    AFTER the ladder and BEFORE the Layer-2b nth escalation, which is the live-faithful
    ordering: the detector still fires the signal (so the Layer-3 governor's rolling state
    is unchanged), the order is simply never placed (so a vetoed trade does not consume
    the day's first-trade slot). Default None = pre-ruling behaviour, bit-identical.

    dead_zones: optional list of (start_hm, end_hm) minute-of-day ET intervals; fills
    inside any zone are vetoed (size -> 0) at the same stage as the news gate. ANGUS RULING
    2026-07-26: [(595, 600)] — "guess we're gonna cut trade entries from 9:55 till 10:00."
    Evidence: docs/GOLDEN-WINDOW-DISSECTION.md §4 (champion pop: −23.0R raw, 0% win under the
    refinement, negative both years) + the canon's own zone trades (3 taken, 0 wins, −$372).

    Deliberately a GATE OBJECT, not a precomputed mask: the merges below drop rows and
    reset the index, so any mask built against the caller's `T` silently misaligns here.
    The mask is derived from this frame's own `fill` column at the point of use.
    See src/canon/news_gate.py and docs/FINDING-canon-has-no-news-blackout.md.
    """
    T = T.copy()
    long = T.direction == "long"
    # --- pre-market checks (frozen as originally shipped; thresholds pooled-2025) ---
    T["W"] = np.where(long, T.dep_wall_below_d.isna(), T.dep_wall_above_d.isna()).astype(float)
    T["W"] = T["W"].where(T.dep_thick.notna())
    T["F"] = (T.fill_delta_conf == 1).astype(float)
    d15dir = T.d15 * np.where(long, 1, -1)
    T["Tp"] = (d15dir >= TH.pre_Tp_d15dir_min).astype(float)
    T["G"] = (T.ent_vs_vwap_sd_dir >= TH.pre_G_ent_vs_vwap_sd_dir_min).astype(float)
    T["C"] = np.where(T.win_ == "pre", (T.conf_PM == 1), (T.conf_LON == 1)).astype(float)
    # --- golden-native checks (thresholds = frozen 2025-GOLD quantiles) ---
    BP = pd.read_parquet("output/badpa_matrix.parquet")[
        ["day", "book", "fill", "netpath_30", "bbw_state", "churn_flow_30", "trigdens_30"]]
    T = T.merge(BP, on=["day", "book", "fill"], how="left")
    T["D"] = pd.Series(np.where(long, T.dep_wall_above_d.notna(), T.dep_wall_below_d.notna()),
                       index=T.index).astype(float).where(T.dep_thick.notna())
    T["Tc"] = (T.d15_conf == 1).astype(float)
    T["X"] = (T.bbw_state >= TH.gold_X_bbw_state_min).astype(float).where(T.bbw_state.notna())
    T["AGE"] = (T.on_extreme_age >= TH.gold_AGE_on_extreme_age_min).astype(float).where(T.on_extreme_age.notna())
    T["PAQ"] = (T.netpath_30 >= TH.gold_PAQ_netpath_30_min).astype(float).where(T.netpath_30.notna())

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

    # Dead-zone entry cut (ANGUS 2026-07-26) — same live-faithful ordering as the news veto.
    if dead_zones:
        for z0, z1 in dead_zones:
            T.loc[(T.fillhm >= z0) & (T.fillhm < z1), "size"] = 0.0

    # Pre-open news blackout (ANGUS 2026-07-26) — veto before the nth escalation counts.
    if news_gate is not None:
        _et = pd.to_datetime(T["fill"], utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
        T.loc[_et.map(news_gate.blocks).fillna(False).astype(bool), "size"] = 0.0

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
    # Layer 2b: second-and-later trades require score >= 4.
    # ANGUS 29-Jul: *"the trade cap i wanted to implement for live was 2 trades in london, 2 in
    # pre market, 2 in golden window. if it lost the first, the second needed extra conviction."*
    # Grouping on "day" alone makes pre-market and gold share one counter, and since pre fires
    # at 08:00 and gold at 09:40, gold's genuine FIRST trade is scored as the day's 3rd or 4th
    # and held to the score-4 bar. escalation_keys=("day","win_") is the per-session form he
    # asked for. Default stays ("day",) so the armed book is bit-identical.
    ek = list(escalation_keys)
    taken = T[T["size"] > 0]
    nth = taken.groupby(ek).cumcount() + 1
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
    for _, g in live.groupby(ek):
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
