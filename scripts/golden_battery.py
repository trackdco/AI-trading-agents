#!/usr/bin/env python3
"""GOLDEN-WINDOW battery on the real Layer-2e canon. Pre-market UNTOUCHED (asserted).

Faithful copy of canon_mechanical.build_canon (2e) with golden-only hooks:
  cut_hook(T)   -> may re-price eff_dollars for GOLD rows only (earlier in-trade cut)
  gate_hook(T)  -> may zero size for GOLD rows only (vetoes)   [applied after Layer 2b]
  boost_hook(T) -> may scale size for GOLD rows only (boosts)  [applied after Layer 2e]
Every variant reports gold $/n/WR per year + total book, delta vs baseline, and asserts the
pre-market P&L vector is IDENTICAL to baseline. Ends with a golden LOSER autopsy.
Honesty: ~61 taken golden trades/2yrs; 2025 quantiles are in-sample; anything positive is a
2023/24-holdout candidate, not a ship."""
import numpy as np
import pandas as pd

def build(T, cut_hook=None, gate_hook=None, boost_hook=None):
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
    I = pd.read_parquet("output/intrade_matrix.parquet")[["day", "book", "fill", "r_3", "fw_3"]]
    T = T.merge(I, on=["day", "book", "fill"], how="left")
    cut = (T.r_3 <= -0.1106) & (T.fw_3 <= -13)
    T["cut3"] = cut.fillna(False)
    T["eff_dollars"] = np.where(T.cut3, T.r_3 * T.risk * 20, T.dollars)
    if cut_hook is not None:
        cut_hook(T)                                   # gold-only re-pricing
    T["size"] = np.select([T.score <= 2, T.score == 3, T.score == 4, T.score == 5], [0, .5, 1, 1.5])
    hi = T[T.score >= 4].reset_index()
    hi["trailWR"] = hi.eff_dollars.gt(0).rolling(15).mean().shift(1)
    trail = dict(zip(hi["index"], hi.trailWR))
    cur = np.nan; gov = []; twr = pd.Series(T.index.map(trail))
    for i in range(len(T)):
        if not np.isnan(twr[i]):
            cur = twr[i]
        gov.append(0.5 if (not np.isnan(cur) and cur < 0.35) else 1.0)
    T["governor"] = gov
    taken = T[T["size"] > 0]
    nth = taken.groupby("day").cumcount() + 1
    T["nth"] = nth.reindex(T.index)
    esc = (T["nth"] >= 2) & (T.score < 4)
    T.loc[esc.fillna(False), "size"] = 0.0
    if gate_hook is not None:
        gate_hook(T)                                  # gold-only vetoes
    T["pl"] = T.eff_dollars * T["size"] * T.governor
    BP = pd.read_parquet("output/badpa_matrix.parquet")[["day", "book", "fill", "netpath_30", "churn_flow_30"]]
    T = T.merge(BP, on=["day", "book", "fill"], how="left")
    taken = T[T["size"] > 0].sort_values("fill")
    wins = (taken.eff_dollars > 0).astype(float)
    trail20 = wins.rolling(20).mean().shift(1)
    t20 = dict(zip(taken.index, trail20))
    cur = np.nan; coldc = []
    for i in T.index:
        if i in t20 and t20[i] == t20[i]:
            cur = t20[i]
        coldc.append(bool(cur == cur and cur < 0.40))
    T["cold"] = coldc
    r1 = T["cold"] & (T.churn_flow_30 > 0.0292)
    r2 = (T.netpath_30 >= 0.3328) & ~r1
    T.loc[r1.fillna(False), "size"] *= 0.5
    T.loc[r2.fillna(False), "size"] *= 1.5
    if boost_hook is not None:
        boost_hook(T)                                 # gold-only boosts
    T["pl"] = T.eff_dollars * T["size"] * T.governor
    T["struct"] = T.W + T.Tp
    live = T[T["size"] > 0].sort_values("fill"); drop = []
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

TM = pd.read_parquet("output/trade_matrix.parquet")
BASE = build(TM)
base_pre = BASE[(BASE["size"] > 0) & (BASE.win_ == "pre")]
base_pre_key = base_pre.groupby("yr").pl.sum().round(0).to_dict()

def gold_stats(T):
    out = {}
    for yr in (2025, 2026):
        g = T[(T.yr == yr) & (T["size"] > 0) & (T.win_ == "gold")]
        out[yr] = (g.pl.sum(), len(g), 100 * (g.pl > 0).mean() if len(g) else 0)
    js = T[(T.yr == 2025) & (T.day >= "2025-07-01") & (T.day <= "2025-09-30") & (T["size"] > 0) & (T.win_ == "gold")]
    out["js"] = js.pl.sum()
    out["tot"] = {yr: T[(T.yr == yr) & (T["size"] > 0)].pl.sum() for yr in (2025, 2026)}
    return out

def report(name, T):
    pre = T[(T["size"] > 0) & (T.win_ == "pre")].groupby("yr").pl.sum().round(0).to_dict()
    pre_ok = pre == base_pre_key
    s = gold_stats(T); b = gold_stats(BASE)
    d25 = s[2025][0] - b[2025][0]; d26 = s[2026][0] - b[2026][0]
    print(f"{name:34s} g25 ${s[2025][0]:+8,.0f} (n{s[2025][1]:2d},{s[2025][2]:3.0f}%) "
          f"g26 ${s[2026][0]:+8,.0f} (n{s[2026][1]:2d},{s[2026][2]:3.0f}%) "
          f"d25 {d25:+6,.0f} d26 {d26:+6,.0f}  JulSep {s['js']:+6,.0f}  "
          f"2yr {d25+d26:+7,.0f}  pre{'=' if pre_ok else '!!CHANGED!!'}")
    return d25, d26

print("=" * 132)
print("GOLDEN BATTERY (real 2e canon; hooks touch GOLD only; pre asserted unchanged)")
print("=" * 132)
b = gold_stats(BASE)
print(f"{'BASELINE 2e canon':34s} g25 ${b[2025][0]:+8,.0f} (n{b[2025][1]:2d},{b[2025][2]:3.0f}%) "
      f"g26 ${b[2026][0]:+8,.0f} (n{b[2026][1]:2d},{b[2026][2]:3.0f}%)                        JulSep {b['js']:+6,.0f}")

gold = lambda T: T.win_ == "gold"
def gate_wt(T):
    T.loc[gold(T) & ((T.W < 1) | (T.Tp < 1)), "size"] = 0.0
def gate_score4(T):
    T.loc[gold(T) & (T.score < 4), "size"] = 0.0
def gate_risk40(T):
    T.loc[gold(T) & (T.risk > 40), "size"] = 0.0
def gate_early(T):
    T.loc[gold(T) & (T.fillhm > 600), "size"] = 0.0   # keep 09:40-10:00 fills only (fillhm = min-of-day)
def cut_tight(T):
    m = gold(T) & (T.r_3 <= -0.02) & ~T.cut3          # underwater at 3min = 18% WR (autopsy)
    T.loc[m, "eff_dollars"] = T.loc[m, "r_3"] * T.loc[m, "risk"] * 20
    T.loc[m, "cut3"] = True
def boost_struct(T):
    T.loc[gold(T) & (T.W >= 1) & (T.Tp >= 1), "size"] *= 1.5
def combo_gate(T):
    gate_wt(T)
def combo_cut(T):
    cut_tight(T)

V = [
    ("V1 veto: golden needs W+Tp", dict(gate_hook=gate_wt)),
    ("V2 veto: golden needs score>=4", dict(gate_hook=gate_score4)),
    ("V3 veto: golden risk cap 40pt", dict(gate_hook=gate_risk40)),
    ("V4 gold cut if underwater@3min", dict(cut_hook=cut_tight)),
    ("V5 gold 09:40-10:00 fills only", dict(gate_hook=gate_early)),
    ("V6 boost: gold W+Tp size x1.5", dict(boost_hook=boost_struct)),
    ("V7 combo: W+Tp veto + early cut", dict(gate_hook=combo_gate, cut_hook=combo_cut)),
    ("V8 combo: boost + early cut", dict(boost_hook=boost_struct, cut_hook=cut_tight)),
]
res = {}
for name, kw in V:
    res[name] = report(name, build(TM, **kw))

# ---------------- golden loser autopsy (baseline) ----------------
print("\n--- GOLDEN LOSER AUTOPSY (baseline taken golds) ---")
g = BASE[(BASE["size"] > 0) & (BASE.win_ == "gold")].copy()
L = g[g.pl < 0]; Wn = g[g.pl > 0]
print(f"golds: {len(g)}  winners {len(Wn)} (${Wn.pl.sum():+,.0f})  losers {len(L)} (${L.pl.sum():+,.0f})")
for lab, m in [("failed W", L.W < 1), ("failed Tp", L.Tp < 1), ("failed W or Tp", (L.W < 1) | (L.Tp < 1)),
               ("score 3", L.score == 3), ("risk>40pt", L.risk > 40),
               ("r3-underwater(<=-0.05)", L.r_3 <= -0.05), ("10:00+ fills", L.fillhm > 600),
               ("pattern A", L.pattern == "A"), ("pattern B", L.pattern == "B"), ("pattern B2", L.pattern == "B2")]:
    sub = L[m.fillna(False)]
    print(f"   losers {lab:24s} n={len(sub):2d}  ${sub.pl.sum():+8,.0f}")
print("\nwinners profile: W+Tp both pass: "
      f"{100*((Wn.W>=1)&(Wn.Tp>=1)).mean():.0f}% of winners vs {100*((L.W>=1)&(L.Tp>=1)).mean():.0f}% of losers")
print("NOTE: ~61 golds/2yr, 2025-frozen thresholds in-sample, 8 variants tested (multiplicity!) ->")
print("anything here is a HOLDOUT CANDIDATE, not a ship. Vetoes risk clipping big winners (desk-verified failure mode).")
