#!/usr/bin/env python3
"""RE-RUN Champion v1.1 from the ENGINE (not the committed journal), Feb 2026 -> latest.

Pinned to the pass-29 tree (commit 90a91b2: engine/config/trigger CSVs as of the journal's
creation) because engine+config+triggers drifted afterward. Blend per CHAMPION-v1.1-FROZEN.md
and the committed pipeline in scripts/champion_journal_cvd.py:
  - window 08:00-10:15, max 2 trades/day
  - WAR days  (regime imbal_share_20 >= 0.5): E4 market-on-confirmation, tight-stop <=15pt, V0
  - BALANCE days: E3 reclaim limits + V8 management
  - v1.1 cuts: risk >= 5pt; no B-pattern fills in 09h; BALANCE book skips with_trend
Validates: totals + monthly vs the frozen reference, and trade-by-trade vs the committed
pre-cut journal (146 trades). Reports every discrepancy honestly.
"""
import ast
import os
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(f"{S}/gs29")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]


def load_triggers():
    """Feb-May triggers from the pinned pass-29 tree; Jun-Jul from the CURRENT checkout
    (the pass-29 tree has no Jun/Jul trigger coverage - committed later). Provenance is
    reported per month in the output."""
    out = []
    for p in ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv",
              "/home/user/gs/output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            r["_src"] = "pass29" if not p.startswith("/home/user") else "current"
            out.append((r.pop("_src"), Trigger(**{k: v for k, v in r.items() if k != "session_day"})))
    # pass-29 files own Feb-May; the current file supplies ONLY Jun-Jul
    keep = [t for src, t in out if t.pattern != "unclassified"
            and ((src == "pass29") or (t.ts[:7] in ("2026-06", "2026-07")))]
    return keep


allt = load_triggers()
V = pd.read_csv("/home/user/gs/output/regime_vector.csv")
war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
print(f"triggers: {len(allt)}   war days: {len(war)}")

df = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")

base = load_backtest_config().model_copy(
    update={"win_start": dtime(8, 0), "win_end": dtime(10, 15), "max_trades_per_day": 2})
CFG_E3 = base.model_copy(update={"mgmt_variant": "V8"})
CFG_E4 = base.model_copy(update={"entry_variant": "E4"})

rows = []
for m in MONTHS:
    trigs = [t for t in allt if t.ts[:7] == m]
    end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                       .tz_localize(None), tz=NY)
    seg = df[df.ts_event <= end].reset_index(drop=True)
    e3 = [t for t in trigs if t.ts[:10] not in war]
    e4 = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
    for name, tt, cfg in (("E3bal", e3, CFG_E3), ("E4war", e4, CFG_E4)):
        tr, _, _ = simulate(seg, tt, cfg)
        for r in tr:
            ts = pd.Timestamp(r.fill_ts).tz_convert(NY)
            rows.append(dict(month=r.trade_date[:7], day=r.trade_date,
                             fill=ts.strftime("%H:%M"), branch=name, dir=r.direction,
                             pattern=r.pattern, htf=r.htf_flag,
                             risk_pts=round(abs(r.entry - r.stop_initial), 2),
                             entry=r.entry, exit=r.exit_price, exit_reason=r.exit_reason,
                             points=r.points, dollars=r.dollars, win=r.dollars > 0))
J = pd.DataFrame(rows).sort_values(["day", "fill"]).reset_index(drop=True)
print(f"\nFRESH ENGINE RE-RUN, pre-cut superset: {len(J)} trades  "
      f"${J.dollars.sum():+,.0f}  win {J.win.mean()*100:.1f}%")

# ---- trade-by-trade diff vs the committed pre-cut journal --------------------
C = pd.read_csv("/home/user/gs/output/journal_champion.csv")
key = ["day", "fill", "branch"]
merged = J.merge(C[key + ["dollars", "pattern", "htf", "risk_pts"]], on=key, how="outer",
                 suffixes=("_new", "_frozen"), indicator=True)
only_new = merged[merged._merge == "left_only"]
only_old = merged[merged._merge == "right_only"]
both = merged[merged._merge == "both"]
dollar_mismatch = both[(both.dollars_new - both.dollars_frozen).abs() > 0.5]
print(f"vs committed journal ({len(C)}t): matched {len(both)}, "
      f"only-in-rerun {len(only_new)}, only-in-frozen {len(only_old)}, "
      f"$-mismatch among matched {len(dollar_mismatch)}")
if len(only_new):
    print("  only-in-rerun:\n", only_new[key + ["dollars_new"]].to_string(index=False))
if len(only_old):
    print("  only-in-frozen:\n", only_old[key + ["dollars_frozen"]].to_string(index=False))
if len(dollar_mismatch):
    print("  $ mismatches:\n", dollar_mismatch[key + ["dollars_new", "dollars_frozen"]].head(10).to_string(index=False))

# ---- apply the three v1.1 cuts ----------------------------------------------
fh = J.fill.str.slice(0, 2).astype(int)
c1 = J.risk_pts >= 5.0
c2 = ~((J.pattern == "B") & (fh == 9))
c3 = ~((J.branch == "E3bal") & (J.htf == "with_trend"))
V11 = J[c1 & c2 & c3]
print(f"\n=== CHAMPION v1.1 (fresh engine re-run + 3 cuts) ===")
print(f"trades {len(V11)} | win {V11.win.mean()*100:.1f}% | points {V11.points.sum():+.1f} | dollars {V11.dollars.sum():+,.0f}")
m = V11.groupby("month").dollars.sum().round(0)
print(m.to_string())
print(f"green months: {int((m > 0).sum())}/{len(m)}")
print("\nFROZEN REFERENCE: 100t | 45.0% | +915.7 pts | +$17,814 | +6599/+4250/+3705/+10/+3765/-515 | 5/6")
J.to_csv(f"{S}/champion_superset_rerun.csv", index=False)

# routing-disagreement report: journal-implied branch per day vs current-vector routing
jdays = C.groupby("day").branch.agg(lambda x: set(x)).to_dict()
dis = []
for dday, brs in jdays.items():
    in_war = dday in war
    implied_war = ("E4war" in brs)
    if len(brs) == 1 and implied_war != in_war:
        dis.append((dday, "journal=" + list(brs)[0], "vector=" + ("WAR" if in_war else "BAL")))
print(f"\nROUTING DRIFT (journal-implied book vs current regime vector): {len(dis)} day(s)")
for d_ in dis:
    print("  ", *d_)

V11.to_csv(f"{S}/champion_v11_rerun.csv", index=False)
print("saved champion_v11_rerun.csv")
