#!/usr/bin/env python3
"""DIAGNOSTIC (for Angus, not a locked change): compare champion arm/config variants under the
FIXED engine, reported in R (the strategy's real sizing currency) as well as 1-contract $.
Variants: current mixed (E3 non-WAR + E4 WAR) vs E3-only vs E4-only vs mixed+09:15-09:45 stand-out.
    python3 scripts/_champion_variants.py"""
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


def load_triggers():
    out = []
    for p in ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def run(mode, gate=False):
    allt = load_triggers()
    V = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    upd = {"win_start": dtime(8, 0), "win_end": dtime(10, 15), "max_trades_per_day": 2}
    if gate:
        upd["no_trade_start"] = dtime(9, 15); upd["no_trade_end"] = dtime(9, 45)
    base = load_backtest_config().model_copy(update=upd)
    E3 = base.model_copy(update={"mgmt_variant": "V8"})
    E4 = base.model_copy(update={"entry_variant": "E4"})
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                           .tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        if mode == "mixed":
            arms = [([t for t in trigs if t.ts[:10] not in war], E3),
                    ([t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0], E4)]
        elif mode == "e3_only":
            arms = [(trigs, E3)]
        elif mode == "e4_only":
            arms = [([t for t in trigs if abs(t.close - t.stop_ref) <= 15.0], E4)]
        for tt, cfg in arms:
            tr, _, _ = simulate(seg, tt, cfg)
            rows += [dict(r=x.r_multiple, d=x.dollars) for x in tr]
    J = pd.DataFrame(rows)
    return J


if __name__ == "__main__":
    print(f"{'variant':22s} {'n':>4} {'win%':>5} {'net$':>9} {'netR':>7} {'expR':>7}")
    for label, mode, gate in [("mixed (champion)", "mixed", False),
                              ("mixed + 0915-0945 out", "mixed", True),
                              ("E3-only (limit)", "e3_only", False),
                              ("E3-only + 0915-0945", "e3_only", True),
                              ("E4-only (market)", "e4_only", False)]:
        J = run(mode, gate)
        w = (J.r > 0).mean() * 100
        print(f"{label:22s} {len(J):4d} {w:5.1f} {J.d.sum():+9,.0f} {J.r.sum():+7.1f} {J.r.mean():+7.3f}")
