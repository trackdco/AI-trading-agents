#!/usr/bin/env python3
"""POST-OPEN full-2026 (Feb-Jul) + CAP SWEEP. The winning post-open shapes from postopen_e6 on the
STANDARD re-detected triggers (full-year coverage), window 09:40-10:15, caps {2,3,4}. Answers
Angus: how does the post-open fix look across the whole year, and what's the right trade cap.

    python -m scripts.postopen_full
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
POST_S, POST_E = dtime(9, 40), dtime(10, 15)


def load():
    out = []
    for p in ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def run(allt, df, cfg, tight):
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        if tight:
            trigs = [t for t in trigs if abs(t.close - t.stop_ref) <= 15.0]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                           .tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        tr, _, _ = simulate(seg, trigs, cfg)
        for r in tr:
            ft = pd.Timestamp(r.fill_ts).tz_convert(NY).time()
            if POST_S <= ft <= POST_E:
                rows.append(dict(month=m, dollars=r.dollars, win=r.dollars > 0))
    return pd.DataFrame(rows)


def report(J, label):
    if not len(J):
        print(f"  {label:32s} (none)"); return
    by = J.groupby("month").dollars.sum()
    mo = " ".join(f"{m[-2:]}:{by.get(m,0):+.0f}" for m in MONTHS)
    green = (by > 0).sum()
    print(f"  {label:32s} {len(J):3d}t ${J.dollars.sum():+8,.0f} win {J.win.mean()*100:2.0f}% "
          f"{green}/{len(by)}mo+ | {mo}")


def main():
    allt = load()
    df = pd.read_parquet(DATA)
    print(f"POST-OPEN 09:40-10:15, FULL 2026 (Feb-Jul), standard triggers\n")
    for cap in (2, 3, 4):
        base = load_backtest_config().model_copy(
            update={"win_start": POST_S, "win_end": POST_E, "max_trades_per_day": cap})
        print(f"--- cap {cap}/day ---")
        report(run(allt, df, base.model_copy(update={"entry_variant": "E3", "mgmt_variant": "V0"}), False), "champion E3/V0")
        report(run(allt, df, base.model_copy(update={"entry_variant": "E3", "mgmt_variant": "V8"}), False), "E3 + V8")
        report(run(allt, df, base.model_copy(update={"entry_variant": "E4", "mgmt_variant": "V8", "oversized_stop": 15.0}), False), "E4 + V8 + guard15")
        report(run(allt, df, base.model_copy(update={"entry_variant": "E4", "mgmt_variant": "V8", "oversized_stop": 15.0}), True), "E4+V8+guard15 tight-trig")
        print()


if __name__ == "__main__":
    main()
