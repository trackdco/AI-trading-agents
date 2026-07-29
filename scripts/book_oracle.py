#!/usr/bin/env python3
"""BOOK-SELECTION SCOREBOARD (Angus 21 Jul). The oracle ceiling = pick the more profitable
book (E3 retest vs E4 displacement) every day. Not achievable, but a real daily read at
60-70% correct = green. This establishes the board:
  * per-day E3-book P&L vs E4-book P&L (pre+golden, CVD gate, 20pt pre cap) — the canon pipeline
  * ORACLE (always right book)  vs  always-E3  vs  always-E4  vs  the current WAR-day heuristic
  * WAR-day book-selection ACCURACY — the baseline any daily read must beat

Books are canon: E3 = mgmt V8 limit-retest on all triggers; E4 = market entry on
displacement-eligible triggers (|close-stop_ref| <= 15). 2026 book (Feb-Jul).

    python -m scripts.book_oracle
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


def book_trades(seg, trigs, cfg_e3, cfg_e4, delta, book):
    """All that book's gated trades (pre+golden), run ONCE over the full period."""
    rows = []
    tt = trigs if book == "E3" else [t for t in trigs if abs(t.close - t.stop_ref) <= 15.0]
    cfg = cfg_e3 if book == "E3" else cfg_e4
    for wname, win in (("pre", PRE), ("golden", GOLD)):
        upd = {"win_start": win[0], "win_end": win[1], "max_trades_per_day": 2}
        if wname == "pre":
            upd["max_stop_points"] = 20.0
        tr, _, _ = simulate(seg, tt, cfg.model_copy(update=upd))
        for r in tr:
            ft = pd.Timestamp(r.fill_ts).time()
            if not (win[0] <= ft < win[1]):
                continue
            rows.append(dict(date=r.trade_date, window=wname, direction=r.direction,
                             dollars=r.dollars,
                             cvd=-conviction(delta, r.fill_ts, r.direction)))
    return rows


def main():
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    filt = load_selection_filters()
    V = vec[["day", "open_vs_value"]].rename(columns={"day": "date"})
    print("loading CVD ...", flush=True)
    delta = load_cvd_delta()
    base = load_backtest_config().model_copy(update={"no_trade_start": None, "no_trade_end": None})
    cfg_e3, cfg_e4 = books(base)

    trigs = [t for t in allt if t.ts[:7] in MONTHS]
    seg = df.reset_index(drop=True)                    # full period; indicators are causal
    print(f"{len(trigs)} triggers, {len(seg)} bars; simulating books ...", flush=True)
    recs = []
    for book in ("E3", "E4"):
        print(f"  book {book} ...", flush=True)
        r = book_trades(seg, trigs, cfg_e3, cfg_e4, delta, book)
        if not r:
            continue
        J = pd.DataFrame(r).merge(V, on="date", how="left")
        G = apply_selection_gate(J, filt)              # canon CVD gate
        for date, s in G.groupby("date"):
            recs.append(dict(date=date, book=book, pnl=s.dollars.sum(), n=len(s)))
    P = pd.DataFrame(recs)
    piv = P.pivot_table(index="date", columns="book", values="pnl", aggfunc="sum").fillna(0.0)
    for b in ("E3", "E4"):
        if b not in piv:
            piv[b] = 0.0
    piv["war"] = [d in war for d in piv.index]
    piv["winner"] = piv.apply(lambda r: "E3" if r.E3 > r.E4 else ("E4" if r.E4 > r.E3 else "tie"), axis=1)
    piv["war_pick"] = piv.war.map({True: "E4", False: "E3"})

    days = len(piv)
    oracle = piv[["E3", "E4"]].max(axis=1).sum()
    a_e3, a_e4 = piv.E3.sum(), piv.E4.sum()
    war_pnl = piv.apply(lambda r: r.E4 if r.war else r.E3, axis=1).sum()
    dec = piv[piv.winner != "tie"]
    war_acc = (dec.war_pick == dec.winner).mean() * 100 if len(dec) else 0
    floor = min(a_e3, a_e4)
    green = floor + 0.60 * (oracle - floor)       # ~"60% of the way to oracle" reference

    print(f"\n### BOOK-SELECTION SCOREBOARD — 2026 (Feb-Jul), {days} trading days ###\n")
    print(f"  ORACLE (right book every day)   ${oracle:+9,.0f}")
    print(f"  always E3 (retest)              ${a_e3:+9,.0f}")
    print(f"  always E4 (displacement)        ${a_e4:+9,.0f}")
    print(f"  WAR-day heuristic (current)     ${war_pnl:+9,.0f}")
    print(f"\n  decisive days (books differ):   {len(dec)} of {days}")
    print(f"  WAR-day book ACCURACY:          {war_acc:.0f}%   <- number to beat")
    print(f"  (always-E3 accuracy {(dec.winner=='E3').mean()*100:.0f}%, always-E4 {(dec.winner=='E4').mean()*100:.0f}%)")
    print(f"\n  reference: ~60% of the way to oracle ~= ${green:+,.0f}")
    P.to_csv("output/book_oracle_daily.csv", index=False)
    piv.reset_index().to_csv("output/book_oracle_pivot.csv", index=False)
    print("\n  wrote output/book_oracle_daily.csv + output/book_oracle_pivot.csv")
    print("\n  per-month oracle vs war-heuristic:")
    piv["mo"] = piv.index.str[:7]
    for mo, s in piv.groupby("mo"):
        orc = s[["E3", "E4"]].max(axis=1).sum()
        wp = s.apply(lambda r: r.E4 if r.war else r.E3, axis=1).sum()
        d2 = s[s.winner != "tie"]
        acc = (d2.war_pick == d2.winner).mean() * 100 if len(d2) else 0
        print(f"    {mo}  oracle ${orc:+7,.0f}   war ${wp:+7,.0f}   war-acc {acc:3.0f}%  ({len(d2)} decisive)")


if __name__ == "__main__":
    main()
