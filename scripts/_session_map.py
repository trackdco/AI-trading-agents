#!/usr/bin/env python3
"""P1 roadmap: session-wide expectancy map on the FIXED engine. Runs the champion arms over the
FULL 08:00-11:00 trigger window (uncapped, no stand-out) and reports expectancy by 15-min entry
bucket, split IS (Feb-May) vs OOS (Jun-Jul) — to decide which windows to trade / kill / add."""
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


def main():
    allt = load_triggers()
    V = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    base = load_backtest_config().model_copy(
        update={"win_start": dtime(8, 0), "win_end": dtime(11, 0), "max_trades_per_day": 50})
    E3 = base.model_copy(update={"mgmt_variant": "V8"}); E4 = base.model_copy(update={"entry_variant": "E4"})
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        for tt, cfg in (([t for t in trigs if t.ts[:10] not in war], E3),
                        ([t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0], E4)):
            for x in simulate(seg, tt, cfg)[0]:
                ft = pd.Timestamp(x.fill_ts).tz_convert(NY)
                rows.append(dict(mo=m, b=ft.floor("15min").strftime("%H:%M"), r=x.r_multiple, d=x.dollars))
    J = pd.DataFrame(rows)
    J.to_csv(f"{S}/session_map.csv", index=False)
    print("SESSION-WIDE expectancy by 15-min entry bucket (fixed engine, 08:00-11:00, uncapped):")
    print(f"{'bucket':7s} | {'IS n':>4} {'IS win':>6} {'IS R':>6} {'IS exp':>7} | {'OOS n':>5} {'OOS win':>7} {'OOS R':>6} {'OOS exp':>7}")
    for b in sorted(J.b.unique()):
        s = J[J.b == b]; i = s[s.mo.isin(IS)]; o = s[~s.mo.isin(IS)]
        def f(x): return (len(x), (x.r > 0).mean()*100 if len(x) else 0, x.r.sum(), x.r.mean() if len(x) else 0)
        iN, iw, iR, ie = f(i); oN, ow, oR, oe = f(o)
        print(f"{b:7s} | {iN:4d} {iw:5.0f}% {iR:+6.1f} {ie:+7.3f} | {oN:5d} {ow:6.0f}% {oR:+6.1f} {oe:+7.3f}")
    print(f"\nTOTAL IS {len(J[J.mo.isin(IS)])}t R{J[J.mo.isin(IS)].r.sum():+.1f}  OOS {len(J[~J.mo.isin(IS)])}t R{J[~J.mo.isin(IS)].r.sum():+.1f}")


if __name__ == "__main__":
    main()
