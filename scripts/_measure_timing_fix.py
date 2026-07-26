#!/usr/bin/env python3
"""Reproduce the champion (E3+V8 non-WAR / E4 WAR, win 08:00-10:15, max 2/day, per-month)
and dump every trade, so the entry-timing fix can be measured before/after.
Usage: python3 scripts/_measure_timing_fix.py <tag>   -> writes champ_<tag>.csv to scratchpad."""
import ast, sys
from datetime import time as dtime
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_backtest_config, simulate
from src.engine.triggers import Trigger

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = "data/reference/nq_1m_feb_jul2026.parquet"
SCRATCH = f"{S}"


def load_triggers():
    out = []
    for p in ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def champion():
    allt = load_triggers()
    V = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    base = load_backtest_config().model_copy(
        update={"win_start": dtime(8, 0), "win_end": dtime(10, 15), "max_trades_per_day": cap})
    E3 = base.model_copy(update={"mgmt_variant": "V8"})
    E4 = base.model_copy(update={"entry_variant": "E4"})
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                           .tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3 = [t for t in trigs if t.ts[:10] not in war]
        e4 = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        for tt, cfg, arm in ((e3, E3, "E3"), (e4, E4, "E4")):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                rows.append(dict(date=r.trade_date, fill_ts=r.fill_ts, arm=arm,
                                 dir=r.direction, entry=r.entry, exit=r.exit_price,
                                 reason=r.exit_reason, r=round(r.r_multiple, 4),
                                 dollars=r.dollars, risk=round(abs(r.entry - r.stop_initial), 2),
                                 mo=m))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "run"
    J = champion()
    J.to_csv(f"{SCRATCH}/champ_{tag}.csv", index=False)
    w = (J.r > 0).mean() * 100
    print(f"{tag}: {len(J)}t  ${J.dollars.sum():+,.0f}  win {w:.1f}%  "
          f"netR {J.r.sum():+.1f}  exp {J.r.mean():+.3f}R", flush=True)
