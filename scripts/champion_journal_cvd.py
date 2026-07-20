#!/usr/bin/env python3
"""One comprehensive champion journal (E-2 + Tier-2 shipped shape, 2026 Feb-Jul) with:
  - weekday, direction, htf, fill time, risk, dollars, win
  - CVD CONVICTION: signed aggressive-volume delta in the K-min window ending at entry,
    oriented to the trade's direction (long wants buyers, short wants sellers).

Answers Angus's selection thesis: (1) are Tue/Wed really best? (2) do high-conviction trades
win more -> can CVD tell a real setup from a hollow one, so we take fewer, better trades?

    python -m scripts.champion_journal_cvd
"""
import ast
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
CVD = ["footprint_feb_mar2026", "footprint_apr2026", "footprint_may_jul2026"]
KMIN = 3   # conviction window: entry minute + 2 prior


def load_triggers():
    out = []
    for p in ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def load_cvd_delta():
    """Per-minute signed aggressive delta (A=buy vol, B=sell vol) -> delta = buy - sell, in ET."""
    frames = []
    for f in CVD:
        d = pd.read_parquet(f"data/reference/cvd/{f}.parquet", columns=["ts_minute", "side", "volume"])
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d["signed"] = np.where(d["side"] == "A", d["volume"], -d["volume"])
    g = d.groupby("ts_minute")["signed"].sum().rename("delta")
    g.index = g.index.tz_convert(NY)
    return g.sort_index()


def conviction(delta_series, fill_ts, direction):
    """Signed delta over the KMIN-min window ending STRICTLY BEFORE the entry minute (no
    lookahead: the entry minute's volume partly occurs after our fill, so it's excluded),
    oriented to direction."""
    t = pd.Timestamp(fill_ts).tz_convert(NY).floor("min")
    win = delta_series.loc[t - pd.Timedelta(minutes=KMIN): t - pd.Timedelta(minutes=1)]
    if win.empty:
        return np.nan
    d = float(win.sum())
    return d if direction == "long" else -d


def main():
    allt = load_triggers()
    V = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    print("loading CVD delta ...", flush=True)
    delta = load_cvd_delta()

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
        for tt, cfg in ((e3, CFG_E3), (e4, CFG_E4)):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ts = pd.Timestamp(r.fill_ts).tz_convert(NY)
                rows.append(dict(
                    date=r.trade_date, weekday=ts.day_name(), fill_t=ts.time().strftime("%H:%M"),
                    direction=r.direction, htf=r.htf_flag, risk=abs(r.entry - r.stop_initial),
                    dollars=r.dollars, win=r.dollars > 0,
                    cvd=conviction(delta, r.fill_ts, r.direction)))
    J = pd.DataFrame(rows)
    J.to_csv("/tmp/claude-0/-home-user-AI-trading-agents/8f4cdd65-f942-532a-87f2-c9c07c27272a/scratchpad/champ_journal_cvd.csv", index=False)
    print(f"\nCHAMPION 2026 (E-2 + Tier-2): {len(J)}t  ${J.dollars.sum():+,.0f}  win {J.win.mean()*100:.0f}%")

    print("\n== BY WEEKDAY ==")
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    g = J.groupby("weekday")
    for wd in order:
        if wd not in g.groups:
            continue
        s = g.get_group(wd)
        print(f"  {wd:9s} {len(s):3d}t  ${s.dollars.sum():+8,.0f}  win {s.win.mean()*100:2.0f}%  (${s.dollars.mean():+.0f}/t)")

    print("\n== BY CVD CONVICTION (signed delta in dir, entry window) ==")
    JC = J.dropna(subset=["cvd"])
    print(f"  (CVD available for {len(JC)}/{len(J)} trades)")
    if len(JC):
        JC = JC.copy()
        JC["bucket"] = pd.qcut(JC["cvd"], 4, labels=["Q1 hollow/against", "Q2", "Q3", "Q4 strong support"])
        for b, s in JC.groupby("bucket", observed=True):
            print(f"  {b:20s} {len(s):3d}t  ${s.dollars.sum():+8,.0f}  win {s.win.mean()*100:2.0f}%  (${s.dollars.mean():+.0f}/t)")
        # simple gate: drop trades with conviction <= 0 (no directional volume behind them)
        pos = JC[JC.cvd > 0]; neg = JC[JC.cvd <= 0]
        print("\n== GATE: keep only positive-conviction trades ==")
        print(f"  kept (cvd>0)  {len(pos):3d}t  ${pos.dollars.sum():+8,.0f}  win {pos.win.mean()*100:2.0f}%")
        print(f"  dropped(cvd<=0){len(neg):3d}t ${neg.dollars.sum():+8,.0f}  win {neg.win.mean()*100:2.0f}%")


if __name__ == "__main__":
    main()
