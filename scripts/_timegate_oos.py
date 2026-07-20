#!/usr/bin/env python3
"""OOS-clean test of the 09:15-09:45 stand-out on the fixed engine: mixed champion with vs
without the stand-out, split IN-SAMPLE (Feb-May) vs OUT-OF-SAMPLE (Jun-Jul)."""
import ast, sys
from datetime import time as dtime
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_backtest_config, simulate
from src.engine.triggers import Trigger

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
IS = {"2026-02", "2026-03", "2026-04", "2026-05"}
DATA = "data/reference/nq_1m_feb_jul2026.parquet"


def load_triggers():
    out = []
    for p in ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def champ(gate):
    allt = load_triggers()
    V = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    upd = {"win_start": dtime(8, 0), "win_end": dtime(10, 15), "max_trades_per_day": 2}
    if gate:
        upd["no_trade_start"] = dtime(9, 15); upd["no_trade_end"] = dtime(9, 45)
    base = load_backtest_config().model_copy(update=upd)
    E3 = base.model_copy(update={"mgmt_variant": "V8"}); E4 = base.model_copy(update={"entry_variant": "E4"})
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        for tt, cfg in (([t for t in trigs if t.ts[:10] not in war], E3),
                        ([t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0], E4)):
            for x in simulate(seg, tt, cfg)[0]:
                rows.append(dict(mo=m, r=x.r_multiple, d=x.dollars))
    return pd.DataFrame(rows)


def rep(J, label):
    for name, sub in [("IS Feb-May", J[J.mo.isin(IS)]), ("OOS Jun-Jul", J[~J.mo.isin(IS)])]:
        w = (sub.r > 0).mean() * 100 if len(sub) else 0
        print(f"  {label:18s} {name:12s} {len(sub):3d}t  win {w:4.1f}%  ${sub.d.sum():+8,.0f}  "
              f"R {sub.r.sum():+6.1f}  exp {sub.r.mean() if len(sub) else 0:+.3f}")


if __name__ == "__main__":
    base = champ(False); gated = champ(True)
    print("09:15-09:45 STAND-OUT — OOS-clean (fixed engine):")
    rep(base, "mixed (no gate)"); rep(gated, "mixed + standout")
