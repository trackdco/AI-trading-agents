#!/usr/bin/env python3
"""E-2 before/after: grade the 2026 champion on a trigger cache and break the P&L down by
direction x htf_flag, plus monthly. Run on the pre-fix and post-fix caches to see whether the
E-2 fix (unknown regime -> neutral) closes the long/short with-trend gap.

    python -m scripts.grade_e2_split output/triggers_feb_ob_prefix.csv output/triggers_marjul_ob_prefix.csv PREFIX
    python -m scripts.grade_e2_split output/triggers_feb_ob.csv        output/triggers_marjul_ob.csv        POSTFIX
"""
import ast
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")


def load(paths):
    out = []
    for p in paths:
        if not Path(p).exists():
            continue
        rows = pd.read_csv(p).to_dict("records")
        for r in rows:
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def main():
    # optional trailing token TIER2=off disables the Tier-2 config (cash-open veto + post-open stop)
    args = sys.argv[1:]
    tier2 = True
    if args and args[-1].upper() in ("TIER2=OFF", "TIER2=ON"):
        tier2 = args.pop().upper() == "TIER2=ON"
    caches = args[:-1]
    label = args[-1]
    allt = load(caches)

    V = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in V.iterrows()
           if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}

    df = pd.read_parquet(DATA)
    base = load_backtest_config().model_copy(
        update={"win_start": dtime(8, 0), "win_end": dtime(10, 15), "max_trades_per_day": 2})
    if not tier2:
        base = base.model_copy(update={"no_trade_start": None, "no_trade_end": None,
                                       "post_open_after": None, "post_open_min_stop": 0.0})
    label = f"{label}/{'T2on' if tier2 else 'T2off'}"
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
        for tt, cfg in ((e3, CFG_E3), (e4, CFG_E4)):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                rows.append(dict(month=m, day=r.trade_date, direction=r.direction,
                                 htf=r.htf_flag, dollars=r.dollars, win=r.dollars > 0))
    J = pd.DataFrame(rows)
    if not len(J):
        print(f"[{label}] no trades"); return

    print(f"\n===== {label}  ({len(J)}t  ${J.dollars.sum():+,.0f}  win {J.win.mean()*100:.0f}%) =====")

    print("\n  direction x htf_flag:")
    g = J.groupby(["direction", "htf"]).dollars.agg(["count", "sum", "mean"])
    g["win"] = J.groupby(["direction", "htf"]).win.mean() * 100
    for (d, h), r in g.iterrows():
        print(f"    {d:5s} {h:14s} {int(r['count']):3d}t  ${r['sum']:+8,.0f}  "
              f"win {r['win']:2.0f}%  (${r['mean']:+.0f}/t)")

    print("\n  by direction:")
    gd = J.groupby("direction").dollars.agg(["count", "sum"])
    gd["win"] = J.groupby("direction").win.mean() * 100
    for d, r in gd.iterrows():
        print(f"    {d:5s} {int(r['count']):3d}t  ${r['sum']:+8,.0f}  win {r['win']:2.0f}%")

    print("\n  by month:")
    gm = J.groupby("month").dollars.agg(["count", "sum"])
    gm["win"] = J.groupby("month").win.mean() * 100
    for mo, r in gm.iterrows():
        print(f"    {mo}  {int(r['count']):3d}t  ${r['sum']:+8,.0f}  win {r['win']:2.0f}%")

    # persist for the artifact (slash-safe label)
    safe = label.replace("/", "_")
    J.to_csv(f"/tmp/claude-0/-home-user-AI-trading-agents/8f4cdd65-f942-532a-87f2-c9c07c27272a/scratchpad/e2_{safe}.csv", index=False)


if __name__ == "__main__":
    main()
