#!/usr/bin/env python3
"""Decompose the +14.4k chained-2026 baseline into per-trade fills, verified day-by-day.

The chained baseline (output/v07/chained2026/ledger.csv, +$14,465) is day-level: the agent
picked a book per day, pl = that day's E3/E4 total from the committed daily books. The
per-trade fills behind those totals were produced in a dead session. This script re-derives
them with the year_suite recipe (E3 = V8 mgmt, E4 = entry_variant E4 + tight<=15pt triggers,
12-day seg lookback, unclassified triggers dropped, R1/R2 event-timing floor per book) and
accepts a day ONLY if the trades sum to the ledger's own e3/e4 value (+-$1). Unmatched days
are never adjusted.

Then: B2 (v2 tag) requires pre-market CVD confirmation -> remove non-confirmed B2 trades on
verified chosen-book days, report the delta vs the +14,465 baseline.

    python -m scripts.decompose_chained26
"""
import sys
from datetime import time as dtime
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import load
from scripts.orderflow_combined import premkt_cvd
from src.backtest.engine import load_backtest_config, load_news_calendar, simulate
from src.backtest.event_timing import event_entry_floor
NY = "America/New_York"
MONTHS = [f"2026-{m:02d}" for m in range(2, 8)]


def sim_month_book(df, trigs, month, book):
    cal = load_news_calendar()
    floor = event_entry_floor(cal, "rotation" if book == "E3" else "momentum")
    keep = [t for t in trigs if t.ts[:7] == month and t.pattern != "unclassified"
            and (t.ts[:10] not in floor or pd.Timestamp(t.ts) >= floor[t.ts[:10]])]
    if book == "E4":
        keep = [t for t in keep if abs(t.close - t.stop_ref) <= 15.0]
    if not keep:
        return []
    base = load_backtest_config().model_copy(update={"win_end": dtime(10, 15), "max_trades_per_day": 2})
    cfg = base.model_copy(update={"mgmt_variant": "V8"} if book == "E3" else {"entry_variant": "E4"})
    end = pd.Timestamp((pd.Timestamp(month + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
    start = pd.Timestamp(month + "-01", tz=NY) - pd.Timedelta(days=12)
    seg = df[(df.ts_event >= start) & (df.ts_event <= end)].reset_index(drop=True)
    tr, _, _ = simulate(seg, keep, cfg)
    return list(tr)


def main():
    led = pd.read_csv("output/v07/chained2026/ledger.csv")
    df = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    orig = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    v2 = load(["output/triggers_feb_ob_v2.csv", "output/triggers_marjul_ob_v2.csv"])
    v2map = {(t.ts, t.tf, t.direction): t.pattern for t in v2}
    pcvd = premkt_cvd()

    rows = []
    for m in MONTHS:
        for book in ("E3", "E4"):
            for r in sim_month_book(df, orig, m, book):
                tag = v2map.get((r.trigger_ts, r.tf, r.direction), r.pattern)
                cvd = pcvd.get(r.trade_date, 0.0)
                conf = int((cvd > 0 and r.direction == "long") or (cvd < 0 and r.direction == "short"))
                rows.append(dict(day=r.trade_date, book=book, dollars=r.dollars,
                                 pattern=tag, direction=r.direction, cvd_conf=conf,
                                 fill=str(r.fill_ts), entry=r.entry))
        print(f"  {m} done", flush=True)
    T = pd.DataFrame(rows)
    T.to_parquet("output/chained26_decomposed.parquet")

    g = T.groupby(["day", "book"]).dollars.sum()
    traded = led[led.act.isin(["MOMENTUM", "ROTATION"])].copy()
    traded["bk"] = traded.act.map({"MOMENTUM": "E4", "ROTATION": "E3"})

    ok = bad = 0
    adj = 0.0
    cut_n = 0; cut_d = 0.0
    mism = []
    for r in traded.itertuples():
        ledval = r.e4 if r.bk == "E4" else r.e3
        simsum = g.get((r.day, r.bk), 0.0)
        if abs(simsum - ledval) <= 1.0:
            ok += 1
            sub = T[(T.day == r.day) & (T.book == r.bk)]
            cut = sub[(sub.pattern == "B2") & (sub.cvd_conf == 0)]
            adj += r.pl - cut.dollars.sum()
            cut_n += len(cut); cut_d += cut.dollars.sum()
        else:
            bad += 1
            adj += r.pl
            mism.append((r.day, r.bk, simsum, ledval))

    print(f"\nreconciliation vs ledger e3/e4: {ok}/{len(traded)} traded days verified, {bad} not")
    print(f"B2-without-CVD removed on verified days: {cut_n} trades, ${cut_d:+,.0f}")
    print(f"\nBASELINE chained 2026 : ${led.pl.sum():+,.0f}")
    print(f"B2-requires-CVD       : ${adj:+,.0f}   (delta ${adj - led.pl.sum():+,.0f})")
    if mism:
        print(f"\nunverified days (untouched), first 15:")
        for d, b, s, l in mism[:15]:
            print(f"   {d} {b}  sim {s:+8.0f}  ledger {l:+8.0f}")


if __name__ == "__main__":
    main()
