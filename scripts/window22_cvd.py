#!/usr/bin/env python3
"""Angus ask (2026-07): per-window 2+2 caps (pre-market 08:00-09:30 cap 2 + golden
09:40-10:15 cap 2), WITH CVD absorption as a selection criterion, Feb-Jul 2026. Shows what
the golden window looks like once un-starved AND filtered to CVD-confirmed trades only.
2026-by-design (the book Angus trades). Reports; ships nothing.

    python -m scripts.window22_cvd
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load                       # noqa: E402
from scripts.champion_journal_cvd import conviction, load_cvd_delta     # noqa: E402
from src.backtest.engine import load_backtest_config, simulate          # noqa: E402
from src.backtest.selection import apply_selection_gate, load_selection_filters  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
PRE = (dtime(8, 0), dtime(9, 30))
GOLD = (dtime(9, 40), dtime(10, 15))


def build(allt, war, df, delta, vec):
    cfg0 = load_backtest_config()
    base = cfg0.model_copy(update={"no_trade_start": None, "no_trade_end": None})
    windows = [("pre", base.model_copy(update={"win_start": PRE[0], "win_end": PRE[1], "max_trades_per_day": 2}), PRE),
               ("golden", base.model_copy(update={"win_start": GOLD[0], "win_end": GOLD[1], "max_trades_per_day": 2}), GOLD)]
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        for _wname, wcfg, wwin in windows:
            cfg_e3, cfg_e4 = books(wcfg)
            for tt, cfg in ((e3in, cfg_e3), (e4in, cfg_e4)):
                tr, _, _ = simulate(seg, tt, cfg)
                for r in tr:
                    ft = pd.Timestamp(r.fill_ts).time()
                    if not (wwin[0] <= ft < wwin[1]):
                        continue
                    rows.append(dict(month=m, date=r.trade_date, window=_wname, fill_t=ft.strftime("%H:%M"),
                                     direction=r.direction, dollars=r.dollars, win=r.dollars > 0,
                                     risk_pts=round(abs(r.entry - r.stop_initial), 2),
                                     # NEGATED: the repo's conviction() sign is inverted vs the
                                     # validated gate / committed journal (cvd<=0 == absorption).
                                     # Verified: negating reproduces 78t/+$14,351/41% exactly.
                                     cvd=-conviction(delta, r.fill_ts, r.direction)))
    J = pd.DataFrame(rows)
    V = vec[["day", "open_vs_value"]].rename(columns={"day": "date"})
    return J.merge(V, on="date", how="left")


def rep(J, label):
    if not len(J):
        print(f"  {label:30s}   (0 trades)")
        return
    mg = J.groupby("month").dollars.sum()
    g = (mg > 0).sum()
    print(f"  {label:30s} {len(J):3d}t  ${J.dollars.sum():+8,.0f}  win {J.win.mean() * 100:2.0f}%  green {g}/{len(mg)}")
    for m in MONTHS:
        s = J[J.month == m]
        if len(s):
            print(f"      {m}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean() * 100:2.0f}%  {'GREEN' if s.dollars.sum() > 0 else 'red'}")


def main():
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    print("loading CVD ...", flush=True)
    delta = load_cvd_delta()
    J = build(allt, war, df, delta, vec)
    filt = load_selection_filters()
    J["weekday"] = pd.to_datetime(J.date).dt.day_name()
    J["gated_kept"] = J.index.isin(apply_selection_gate(J, filt).index)
    J.to_csv("output/window22_trades.csv", index=False)
    print("\n### PER-WINDOW 2+2 CAPS, Feb-Jul 2026 ###")
    print("\n== ALL (pre-market 2 + golden 2), months-green ==")
    rep(J, "raw (no gate)")
    rep(J[J.cvd <= 0], "CVD absorption only (cvd<=0)")
    G = apply_selection_gate(J, filt)
    rep(G, "shipped gate (below-val + cvd)")

    # ANGUS 2026-07 (verbatim): "we should not be taking fucking trades with over a
    # hundred points stop ... cut that from our dataset entirely." Structural stop only;
    # this is an exclusion of the pathological wide stops, NOT a hard risk cap.
    print("\n== >100pt STOP EXCLUSION (on the shipped gate) ==")
    over = G[G.risk_pts > 100.0]
    print(f"  cut {len(over)} trade(s) with stop >100pt  "
          f"(${over.dollars.sum():+,.0f} removed)  stops: "
          f"{sorted(over.risk_pts.round(0).astype(int).tolist(), reverse=True)}")
    rep(G[G.risk_pts <= 100.0], "shipped gate + cut >100pt stops")
    print("\n== GOLDEN WINDOW 9:40-10:15 ONLY ==")
    g = J[J.window == "golden"]
    rep(g, "raw")
    rep(g[g.cvd <= 0], "CVD absorption only")
    rep(apply_selection_gate(g, filt), "shipped gate")

    def dow(frame, title):
        print(f"\n== DAY-OF-WEEK — {title} ==")
        for wd in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            s = frame[frame.weekday == wd]
            if len(s):
                print(f"  {wd:9s} {len(s):3d}t  ${s.dollars.sum():+8,.0f}  win {s.win.mean() * 100:2.0f}%  "
                      f"${s.dollars.mean():+5.0f}/t")
    dow(G, "shipped gate, ALL (pre+golden)")
    dow(G[G.window == "golden"], "shipped gate, GOLDEN 9:40-10:15 only")
    dow(G[G.window == "pre"], "shipped gate, PRE-MARKET only")


if __name__ == "__main__":
    main()
