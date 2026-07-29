#!/usr/bin/env python3
"""B1/B2 ENGINE TEST — delayed entry on red-folder days (v0.6 floor candidate).

The 2026 FreshEyes panel leak: event_risk -> auto-FLAT = 52% of all regret, yet
no fixed replacement book survives off-era. Hypothesis (Angus B1/B2): the danger
is the RELEASE MOMENT, not the day — on event days, hold entries until
release + N minutes and let the post-release tape trade.

For each year: on days with a high-impact release scheduled at or before 10:15 ET,
run both books (E3+V8, E4tight15) twice —
  baseline: all triggers (what the current books do)
  delayed:  only triggers timestamped >= last such release + N minutes
Days with no pre-10:15 release (e.g. 14:00 FOMC) are untouched by the rule and
excluded from the comparison. Reports per-year event-day P&L, both modes, both
books, plus the day-oracle of each mode. No normalization (s=1.0) — this isolates
the timing effect.

    python -m scripts.delayed_entry_test --year 2023 [--delay 10]
"""
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

NY = "America/New_York"
_ctx = {}


def _init(year, daydir, delay_min):
    import ast

    from src.backtest.engine import load_backtest_config, load_news_calendar
    from src.engine.triggers import Trigger
    _ctx["df"] = pd.read_parquet("data/reference/nq_1m_master.parquet")

    cal = load_news_calendar()
    hi = cal[(cal.impact == "high") & (cal.datetime_ET.dt.time <= dtime(10, 15))]
    gates = {}                       # day -> entries allowed from this ts
    for _, e in hi.iterrows():
        d = e.datetime_ET.strftime("%Y-%m-%d")
        g = e.datetime_ET + pd.Timedelta(minutes=delay_min)
        gates[d] = max(gates.get(d, g), g)
    _ctx["GATES"] = {d: g for d, g in gates.items() if d.startswith(year)}

    trigs = []
    for p in sorted(Path(daydir).glob(f"{year}-*.csv")):
        if p.stat().st_size == 0:
            continue
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            trigs.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    # event days with a gate only — the rest of the year is irrelevant to this test
    _ctx["TRIGS"] = [t for t in trigs if t.pattern != "unclassified"
                     and t.ts[:10] in _ctx["GATES"]]
    base = load_backtest_config().model_copy(
        update={"win_end": dtime(10, 15), "max_trades_per_day": 2})
    _ctx["E3"] = base.model_copy(update={"mgmt_variant": "V8"})
    _ctx["E4"] = base.model_copy(update={"entry_variant": "E4"})


def run_task(task):
    from src.backtest.engine import simulate
    arm, month = task                              # arm in {e3,e4} x {base,delay}
    book, mode = arm.split("_")
    trigs = [t for t in _ctx["TRIGS"] if t.ts[:7] == month]
    if mode == "delay":
        trigs = [t for t in trigs
                 if pd.Timestamp(t.ts) >= _ctx["GATES"][t.ts[:10]]]
    if book == "e4":
        trigs = [t for t in trigs if abs(t.close - t.stop_ref) <= 15.0]
    if not trigs:
        return arm, month, {}
    df = _ctx["df"]
    end = pd.Timestamp((pd.Timestamp(month + "-01", tz=NY)
                        + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
    start = pd.Timestamp(month + "-01", tz=NY) - pd.Timedelta(days=12)
    seg = df[(df.ts_event <= end) & (df.ts_event >= start)].reset_index(drop=True)
    cfg = _ctx["E3"] if book == "e3" else _ctx["E4"]
    tr, _, _ = simulate(seg, trigs, cfg)
    per_day = {}
    for r in tr:
        per_day[r.trade_date] = per_day.get(r.trade_date, 0.0) + r.dollars
    return arm, month, per_day


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", required=True)
    ap.add_argument("--daydir", default="output/triggers_hist2326_days")
    ap.add_argument("--delay", type=int, default=10)
    a = ap.parse_args()
    _init(a.year, a.daydir, a.delay)
    months = sorted({t.ts[:7] for t in _ctx["TRIGS"]})
    tasks = [(f"{b}_{m}", mo) for mo in months for b in ("e3", "e4")
             for m in ("base", "delay")]
    daily = {}                                     # arm -> {day: $}
    with ProcessPoolExecutor(max_workers=4, initializer=_init,
                             initargs=(a.year, a.daydir, a.delay)) as ex:
        for arm, mo, per_day in ex.map(run_task, tasks):
            for d, v in per_day.items():
                daily.setdefault(arm, {})[d] = daily.setdefault(arm, {}).get(d, 0) + v

    days = sorted(_ctx["GATES"])
    rows = []
    for d in days:
        rows.append({"day": d,
                     "e3_base": daily.get("e3_base", {}).get(d, 0.0),
                     "e3_delay": daily.get("e3_delay", {}).get(d, 0.0),
                     "e4_base": daily.get("e4_base", {}).get(d, 0.0),
                     "e4_delay": daily.get("e4_delay", {}).get(d, 0.0)})
    R = pd.DataFrame(rows)
    R["oracle_base"] = R[["e3_base", "e4_base"]].max(axis=1).clip(lower=0)
    R["oracle_delay"] = R[["e3_delay", "e4_delay"]].max(axis=1).clip(lower=0)
    out = Path(f"output/delayed_entry_{a.year}.csv")
    R.to_csv(out, index=False)
    print(f"{a.year}: {len(R)} gated event days (delay {a.delay}min) -> {out}")
    t = R[["e3_base", "e3_delay", "e4_base", "e4_delay",
           "oracle_base", "oracle_delay"]].sum().round(0)
    print(t.to_string())
    print(f"  rotation book delta: {t.e3_delay - t.e3_base:+,.0f}$"
          f" | momentum book delta: {t.e4_delay - t.e4_base:+,.0f}$"
          f" | oracle delta: {t.oracle_delay - t.oracle_base:+,.0f}$")


if __name__ == "__main__":
    main()
