#!/usr/bin/env python3
"""POST-OPEN (09:40-10:15) test — make Angus's window better (his directive: leave pre-market alone).
On the OTE confluence trigger set (Feb-Apr 2026), test his real execution — market-on-confirmation
(E4) — with the FEBRUARY-diagnosed geometry fix: cap fill-to-stop so we don't market-order after
monster candles (F3: E4 loser stop ballooned to 27pt vs 13pt tight). V8 trail = the proven exit.

Arms (all restricted to 09:40-10:15 fills):
  A champion E3/V0            (baseline post-open)
  B E3 + V8                   (add trail)
  C E4 + V8, oversized 42     (market-confirm, NO geometry guard = the Feb loser)
  D E4 + V8, oversized 15     (E6 GEOMETRY FIX: tight fill-to-stop)
  E E4 + V8, oversized 15, tight-trigger<=15  (full E6)

    python -m scripts.postopen_e6
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
MONTHS = ["2026-02", "2026-03", "2026-04"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
POST_S, POST_E = dtime(9, 40), dtime(10, 15)


def load_ote():
    out = []
    for r in pd.read_csv("output/triggers_febapr_ote.csv").to_dict("records"):
        ct = r.get("cluster_types")
        r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
        out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def run(allt, df, cfg, tight_trig):
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        if tight_trig:
            trigs = [t for t in trigs if abs(t.close - t.stop_ref) <= 15.0]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                           .tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        tr, _, _ = simulate(seg, trigs, cfg)
        for r in tr:
            ft = pd.Timestamp(r.fill_ts).tz_convert(NY).time()
            if POST_S <= ft <= POST_E:
                rows.append(dict(month=m, dollars=r.dollars, win=r.dollars > 0,
                                 risk=abs(r.entry - r.stop_initial)))
    return pd.DataFrame(rows)


def report(J, label):
    if not len(J):
        print(f"  {label:34s} (no post-open trades)"); return
    line = f"  {label:34s} {len(J):3d}t  ${J.dollars.sum():+8,.0f}  win {J.win.mean()*100:2.0f}%  " \
           f"medRisk {J.risk.median():4.1f}pt"
    by = J.groupby("month").dollars.agg(["count", "sum"])
    mo = "  ".join(f"{m[-2:]}:{int(by.loc[m,'count'])}t${by.loc[m,'sum']:+,.0f}" for m in MONTHS if m in by.index)
    print(f"{line}  | {mo}")


def main():
    allt = load_ote()
    df = pd.read_parquet(DATA)
    base = load_backtest_config().model_copy(
        update={"win_start": POST_S, "win_end": POST_E, "max_trades_per_day": 4})
    print(f"POST-OPEN (09:40-10:15) OTE test, Feb-Apr 2026  ({len(allt)} OTE triggers)\n")
    arms = [
        ("A champion E3/V0",            base.model_copy(update={"entry_variant": "E3", "mgmt_variant": "V0"}), False),
        ("B E3 + V8",                   base.model_copy(update={"entry_variant": "E3", "mgmt_variant": "V8"}), False),
        ("C E4 + V8  (oversized 42)",   base.model_copy(update={"entry_variant": "E4", "mgmt_variant": "V8", "oversized_stop": 42.0}), False),
        ("D E4 + V8  (oversized 15)",   base.model_copy(update={"entry_variant": "E4", "mgmt_variant": "V8", "oversized_stop": 15.0}), False),
        ("E E4+V8 ovsz15 tight-trig",   base.model_copy(update={"entry_variant": "E4", "mgmt_variant": "V8", "oversized_stop": 15.0}), True),
    ]
    for label, cfg, tt in arms:
        report(run(allt, df, cfg, tt), label)


if __name__ == "__main__":
    main()
