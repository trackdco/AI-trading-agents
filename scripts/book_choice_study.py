#!/usr/bin/env python3
"""BOOK-CHOICE STUDY. The gap from champion (+$14k) to the book-oracle (+$30k) is picking the
right book (E3 rotation vs E4 momentum) each day. This grades BOTH books on EVERY day, measures
how badly the WAR heuristic mis-picks, and tests whether any pre-open feature predicts the
better book -- because an oracle you can't predict is worthless.

    python -m scripts.book_choice_study
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
SP = "/tmp/claude-0/-home-user-AI-trading-agents/8f4cdd65-f942-532a-87f2-c9c07c27272a/scratchpad"


def load_triggers():
    out = []
    for p in ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def preopen_cvd():
    """Net aggressive delta in the pre-open window 08:00-09:30, per session day (ET)."""
    frames = [pd.read_parquet(f"data/reference/cvd/{f}.parquet", columns=["ts_minute", "side", "volume"])
              for f in CVD]
    d = pd.concat(frames, ignore_index=True)
    d["signed"] = np.where(d["side"] == "A", d["volume"], -d["volume"])
    d["ts"] = d["ts_minute"].dt.tz_convert(NY)
    d = d[(d.ts.dt.time >= dtime(8, 0)) & (d.ts.dt.time < dtime(9, 30))]
    d["day"] = d.ts.dt.strftime("%Y-%m-%d")
    return d.groupby("day")["signed"].sum().rename("preopen_cvd")


def grade_all(allt, df, cfg):
    """Per-day P&L for a book run over ALL days at the realistic 2-cap."""
    per = {}
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                           .tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        tr, _, _ = simulate(seg, trigs, cfg)
        for r in tr:
            per[r.trade_date] = per.get(r.trade_date, 0.0) + r.dollars
    return per


def main():
    allt = load_triggers()
    V = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)

    base = load_backtest_config().model_copy(
        update={"win_start": dtime(8, 0), "win_end": dtime(10, 15), "max_trades_per_day": 2})
    e3 = grade_all(allt, df, base.model_copy(update={"mgmt_variant": "V8"}))
    # E4 book: momentum entry, tight-stop filter applied like the champion (<=15pt)
    e4t = [t for t in allt if abs(t.close - t.stop_ref) <= 15.0]
    e4 = grade_all(e4t, df, base.model_copy(update={"entry_variant": "E4"}))

    days = sorted(set(e3) | set(e4))
    rows = []
    for d in days:
        a, b = e3.get(d, 0.0), e4.get(d, 0.0)
        rows.append(dict(day=d, e3=a, e4=b, better="e3" if a >= b else "e4",
                         best=max(a, b), iswar=d in war,
                         champ=(b if d in war else a)))
    D = pd.DataFrame(rows)

    champ = D.champ.sum()
    always_e3, always_e4 = D.e3.sum(), D.e4.sum()
    oracle = D.best.clip(lower=0).sum()          # best book, stand down if it still loses
    print(f"\n== BOOK CHOICE, 2026 Feb-Jul ({len(D)} trading days) ==")
    print(f"  always E3            ${always_e3:+8,.0f}")
    print(f"  always E4            ${always_e4:+8,.0f}")
    print(f"  champion (WAR switch)${champ:+8,.0f}   <- current")
    print(f"  ORACLE best+standdown${oracle:+8,.0f}   = 100%   (champ = {champ/oracle*100:.0f}%)")
    print(f"  60% target           ${oracle*0.6:+8,.0f}")

    # how good is the WAR heuristic at picking the book?
    D["war_pick"] = np.where(D.iswar, "e4", "e3")
    D["correct"] = D.war_pick == D.better
    cost = (D.best - D.champ).sum()
    print(f"\n  WAR heuristic picks the better book {D.correct.mean()*100:.0f}% of days")
    print(f"  cost of wrong book picks (vs oracle): ${cost:+,.0f}")

    # is the better book PREDICTABLE from pre-open features?
    feats = ["imbal_share_20", "imbal_share_10", "trap_rate_10", "range_pctl_20",
             "gap_open_pts", "streak_imbal", "inventory_pts", "on_nr_rank", "gap_vs_value"]
    Vd = V.set_index("day")
    D = D.set_index("day")
    D = D.join(Vd[feats]).join(preopen_cvd())
    print(f"\n== which pre-open features separate E3-better vs E4-better days? ==")
    print(f"  (mean feature value on days each book won; gap = signal strength)")
    for f in feats + ["preopen_cvd"]:
        if f not in D.columns:
            continue
        e3w, e4w = D[D.better == "e3"][f].dropna(), D[D.better == "e4"][f].dropna()
        if len(e3w) < 5 or len(e4w) < 5:
            continue
        print(f"    {f:16s} E3-day {e3w.mean():+9.2f}   E4-day {e4w.mean():+9.2f}   Δ {e4w.mean()-e3w.mean():+9.2f}")
    D.reset_index().to_csv(f"{SP}/book_choice.csv", index=False)


if __name__ == "__main__":
    main()
