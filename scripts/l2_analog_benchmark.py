"""Pass-30: L2 HISTORICAL-ANALOG LOOKUP — mechanical benchmark (must beat the static switch
BEFORE any agent gets credit for it). Walk-forward: each day picks its branch (E3+V8 vs
E4tight15) from the K most similar PRIOR days' realized branch P&L. Similarity = normalized
regime-vector distance. No day ever sees its own or future outcomes.

Outputs per-day routing + the three-way score:
  static switch (champion) vs analog-routed vs single-branch baselines."""
import ast
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from datetime import time as dtime

from src.backtest.engine import load_backtest_config, simulate
from src.engine.triggers import Trigger

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
df = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")


def load(path):
    rows = pd.read_csv(path).to_dict("records")
    for r in rows:
        ct = r.get("cluster_types")
        r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
    ts = [Trigger(**{k: v for k, v in r.items() if k != "session_day"}) for r in rows]
    return [t for t in ts if t.pattern != "unclassified"]


allt = load("output/triggers_feb_ob.csv") + load("output/triggers_marjul_ob.csv") \
    + load("output/triggers_junjul_ob.csv")
base = load_backtest_config().model_copy(
    update={"win_end": dtime(10, 15), "max_trades_per_day": 2})
CFGS = {"E3": base.model_copy(update={"mgmt_variant": "V8"}),
        "E4": base.model_copy(update={"entry_variant": "E4"})}

# per-day P&L of EACH branch run on EVERY day (both books computed once)
daily = {}
for m in MONTHS:
    trigs = [t for t in allt if t.ts[:7] == m]
    tight = [t for t in trigs if abs(t.close - t.stop_ref) <= 15.0]
    end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY)
                        + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
    seg = df[df.ts_event <= end].reset_index(drop=True)
    for b, tt in (("E3", trigs), ("E4", tight)):
        tr, _, _ = simulate(seg, tt, CFGS[b])
        for r in tr:
            d = daily.setdefault(r.trade_date, {"E3": 0.0, "E4": 0.0})
            d[b] += r.dollars

V = pd.read_csv("output/regime_vector.csv")
V = V[V.day.str.startswith("2026")].reset_index(drop=True)
FEATS = ["imbal_share_20", "imbal_share_10", "trap_rate_10", "range_pctl_20",
         "gap_open_pts", "streak_imbal", "red_folder_today"]
V["is_imbal"] = (V.day_type == "imbalanced").astype(float)
FEATS.append("is_imbal")
K = 15
MIN_ANALOGS = 10

rows = []
for i, r in V.iterrows():
    d = r.day
    if d not in daily:
        continue
    static_branch = "E4" if (pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5) else "E3"
    prior = V.iloc[:i].dropna(subset=FEATS)
    prior = prior[prior.day.isin(daily)]
    if len(prior) < MIN_ANALOGS or pd.isna(r[FEATS]).any():
        pick = static_branch                        # cold start -> fall back to the switch
        n_an = 0
    else:
        # scale by prior-window std (no lookahead in normalization)
        mu, sd = prior[FEATS].mean(), prior[FEATS].std().replace(0, 1)
        dist = ((((prior[FEATS].astype(float) - r[FEATS].astype(float)) / sd) ** 2).sum(axis=1)) ** 0.5
        an = prior.assign(dist=dist).nsmallest(K, "dist")
        e3 = np.mean([daily[x]["E3"] for x in an.day])
        e4 = np.mean([daily[x]["E4"] for x in an.day])
        pick = "E3" if e3 >= e4 else "E4"
        n_an = len(an)
    rows.append(dict(day=d, month=d[:7], static=static_branch, analog=pick, n_analogs=n_an,
                     pl_static=daily[d][static_branch], pl_analog=daily[d][pick],
                     pl_e3=daily[d]["E3"], pl_e4=daily[d]["E4"],
                     pl_oracle=max(daily[d].values())))
R = pd.DataFrame(rows)
R.to_csv("output/l2_analog_routing.csv", index=False)

print(f"days routed: {len(R)} | analog agrees with static on "
      f"{(R.static == R.analog).mean() * 100:.0f}% of days\n")
print("=== monthly P&L: static switch vs analog-routed vs single branches vs oracle ===")
agg = R.groupby("month")[["pl_static", "pl_analog", "pl_e3", "pl_e4", "pl_oracle"]].sum()
agg.loc["TOTAL"] = agg.sum()
print(agg.round(0).to_string())
gm = (R.groupby("month")[["pl_static", "pl_analog"]].sum() > 0).sum()
print(f"\ngreen months: static {gm.pl_static}/6, analog {gm.pl_analog}/6")
