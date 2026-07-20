#!/usr/bin/env python3
"""SELECTION STUDY (Angus's thesis: the leak is knowing when NOT to trade).
Establishes the oracle+stand-down benchmark for 2026 and measures how close each selection
policy gets to it. Target: >=60% of oracle+stand-down.

Method: grade both books UNCAPPED (cap 6 ~ uncapped in the 08:00-10:15 window) to get the full
per-day candidate set with CVD conviction, then reconstruct policies in pandas:
  benchmark: per day pick the better book at a realistic 2-cap; stand down if it still loses.
  P0 static-2   : first 2 candidates by time (= current champion)
  P1 fade-gate  : causal — take candidates in time order, only if CVD conviction is a fade, cap 2
  P2 best2-fade : rank day's candidates by fade strength, take top 2 (hindsight CEILING)
  P3 best1-fade : top 1 by fade strength

CVD conviction = signed aggressive delta (buy-sell) in the 3-min window BEFORE entry, oriented
to direction. FADE = flow against the trade (low/negative) -> the champion's rejection edge.

    python -m scripts.selection_study
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
KMIN = 3
SP = "/tmp/claude-0/-home-user-AI-trading-agents/8f4cdd65-f942-532a-87f2-c9c07c27272a/scratchpad"


def load_triggers():
    out = []
    for p in ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def load_cvd_delta():
    frames = [pd.read_parquet(f"data/reference/cvd/{f}.parquet", columns=["ts_minute", "side", "volume"])
              for f in CVD]
    d = pd.concat(frames, ignore_index=True)
    d["signed"] = np.where(d["side"] == "A", d["volume"], -d["volume"])
    g = d.groupby("ts_minute")["signed"].sum().rename("delta")
    g.index = g.index.tz_convert(NY)
    return g.sort_index()


def conviction(delta, fill_ts, direction):
    t = pd.Timestamp(fill_ts).tz_convert(NY).floor("min")
    win = delta.loc[t - pd.Timedelta(minutes=KMIN): t - pd.Timedelta(minutes=1)]
    if win.empty:
        return np.nan
    d = float(win.sum())
    return d if direction == "long" else -d


def grade_book(allt, df, cfg, war_only, war):
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        if war_only is True:
            trigs = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        elif war_only is False:
            trigs = [t for t in trigs if t.ts[:10] not in war]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                           .tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        tr, _, _ = simulate(seg, trigs, cfg)
        for r in tr:
            rows.append(dict(date=r.trade_date, fill_ts=r.fill_ts, direction=r.direction,
                             dollars=r.dollars))
    return rows


def first_n_by_time(g, n):
    return g.sort_values("fill_ts").head(n)


def summarize(J, label, denom=None):
    tot, n = J.dollars.sum(), len(J)
    wr = (J.dollars > 0).mean() * 100 if n else 0
    pct = f"  = {tot/denom*100:4.0f}% of oracle+SD" if denom else ""
    print(f"  {label:26s} {n:3d}t  ${tot:+8,.0f}  win {wr:2.0f}%{pct}")
    return tot


def main():
    allt = load_triggers()
    V = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    print("loading CVD ...", flush=True)
    delta = load_cvd_delta()

    cfg0 = load_backtest_config()
    UNCAP = cfg0.model_copy(update={"win_start": dtime(8, 0), "win_end": dtime(10, 15),
                                    "max_trades_per_day": 6})
    E3 = UNCAP.model_copy(update={"mgmt_variant": "V8"})
    E4 = UNCAP.model_copy(update={"entry_variant": "E4"})

    # full candidate sets, uncapped, per book (E3 over non-WAR days, E4 over WAR days = champion books)
    e3 = pd.DataFrame(grade_book(allt, df, E3, False, war))
    e4 = pd.DataFrame(grade_book(allt, df, E4, True, war))
    cand = pd.concat([e3, e4], ignore_index=True)
    cand["cvd"] = [conviction(delta, r.fill_ts, r.direction) for r in cand.itertuples()]
    cand["fillt"] = pd.to_datetime(cand.fill_ts, utc=True).dt.tz_convert(NY).dt.time
    cand.to_csv(f"{SP}/selection_candidates.csv", index=False)

    # ---- benchmark: per-day better book at realistic 2-cap, stand down losers ----
    def day_pnl_2cap(bookdf):
        return bookdf.groupby("date", group_keys=False).apply(lambda g: first_n_by_time(g, 2).dollars.sum())
    e3d, e4d = day_pnl_2cap(e3), day_pnl_2cap(e4)
    days = sorted(set(e3d.index) | set(e4d.index))
    oracle = sum(max(e3d.get(d, 0.0), e4d.get(d, 0.0)) for d in days)
    oracle_sd = sum(max(e3d.get(d, 0.0), e4d.get(d, 0.0), 0.0) for d in days)
    print(f"\n== 2026 BENCHMARKS (Feb-Jul) ==")
    print(f"  oracle (perfect book/day)        ${oracle:+,.0f}")
    print(f"  oracle + stand-down (skip losers) ${oracle_sd:+,.0f}   <- the denominator")
    print(f"  60% target                        ${oracle_sd*0.6:+,.0f}")

    # ---- policies on the champion candidate set ----
    print(f"\n== SELECTION POLICIES (% of oracle+stand-down) ==")
    P0 = cand.groupby("date", group_keys=False).apply(lambda g: first_n_by_time(g, 2))
    summarize(P0, "P0 static-2 (current)", oracle_sd)

    for thr in (0.0, -200.0, -500.0):
        def gate(g, thr=thr):
            keep, out = 0, []
            for r in g.sort_values("fill_ts").itertuples():
                if keep >= 2:
                    break
                if pd.notna(r.cvd) and r.cvd <= thr:
                    out.append(r.Index); keep += 1
            return g.loc[out]
        P1 = cand.groupby("date", group_keys=False).apply(gate)
        summarize(P1, f"P1 fade-gate cvd<={thr:.0f} (causal)", oracle_sd)

    P2 = cand.groupby("date", group_keys=False).apply(lambda g: g.sort_values("cvd").head(2))
    summarize(P2, "P2 best-2-by-fade (ceiling)", oracle_sd)
    P3 = cand.groupby("date", group_keys=False).apply(lambda g: g.sort_values("cvd").head(1))
    summarize(P3, "P3 best-1-by-fade (ceiling)", oracle_sd)

    # ---- proxy check: is the fade edge just time-of-day or WAR? ----
    print(f"\n== PROXY CHECK: fade edge vs confounds (on P0 static-2 set) ==")
    P0 = P0.copy()
    P0["war"] = P0.date.isin(war)
    P0["fade"] = P0.cvd <= 0
    P0["preopen"] = P0.fillt.apply(lambda t: t < dtime(9, 30))
    for seg, mask in [("pre-open", P0.preopen), ("post-open", ~P0.preopen),
                      ("non-WAR", ~P0.war), ("WAR", P0.war)]:
        s = P0[mask]
        if len(s) < 5:
            continue
        f, nf = s[s.fade], s[~s.fade]
        print(f"  {seg:9s}: fade {len(f):3d}t win {(f.dollars>0).mean()*100:2.0f}% ${f.dollars.sum():+7,.0f}  |  "
              f"follow {len(nf):3d}t win {(nf.dollars>0).mean()*100:2.0f}% ${nf.dollars.sum():+7,.0f}")


if __name__ == "__main__":
    main()
