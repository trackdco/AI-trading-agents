#!/usr/bin/env python3
"""PHASE 2 — calibrate the engine against Angus's 116-trade TradingView export.

The export itself was NOT supplied — only the aggregates published in
`references/tv-findings.md`. A trade-for-trade diff is therefore impossible; what runs
here is the strongest check the available evidence supports: every published aggregate,
plus the two named landmark trades, against a v1-exact run of this engine on the same
window. That distinction is reported rather than papered over.

Both intrabar conventions are run, because it is the single largest expected divergence
class: TV resolves a both-touched bar optimistically on 15m candles, this engine resolves
pessimistically on 1m bars.

    python scripts/orb_calibrate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research.orb.engine import Config, daily_context, load_gc, run, summarise

WIN = ("2026-03-02", "2026-08-17")

TV = {                       # from references/tv-findings.md
    "n": 116, "win_pct": 52.6, "pf": 1.14, "usd": 15202.0, "ev_r": 0.07,
    "med_risk_pts": 21.0, "tgt": 24, "stop": 36, "flat": 56,
    "mfe_075": 56.0, "mfe_100": 47.0, "mfe_125": 35.0, "mfe_150": 14.0,
    "giveback": 7, "first_entry": "10:00", "last_entry": "11:45", "max_streak": 5,
}


def hhmm(m: int) -> str:
    return f"{int(m)//60:02d}:{int(m)%60:02d}"


def streak(r: pd.Series) -> int:
    best = cur = 0
    for x in r:
        cur = cur + 1 if x < 0 else 0
        best = max(best, cur)
    return best


def main() -> None:
    bars = load_gc(str(ROOT / "data/gc_1m.parquet"))
    ctx = daily_context(bars, 14)
    lo, hi = (pd.Timestamp(x, tz="America/New_York").normalize() for x in WIN)
    w = bars[(bars.cal >= lo) & (bars.cal <= hi)]
    days = w.cal.nunique()
    print(f"window {WIN[0]} -> {WIN[1]}")
    print(f"  calendar days with bars: {days}   last day present: {w.cal.max().date()}")
    if w.cal.max() < hi:
        miss = pd.bdate_range(w.cal.max() + pd.Timedelta(days=1), hi)
        print(f"  ** DATA SHORT: missing {len(miss)} business days to {WIN[1]} **")

    rows = []
    for opt in (False, True):
        t = run(w, Config(optimistic=opt), ctx)
        s = summarise(t, "TV-optimistic" if opt else "pessimistic (1m, stop wins)")
        mfe = t.mfe_r
        s.update({
            "mfe_075": 100 * (mfe >= 0.75).mean(), "mfe_100": 100 * (mfe >= 1.0).mean(),
            "mfe_125": 100 * (mfe >= 1.25).mean(), "mfe_150": 100 * (mfe >= 1.5).mean(),
            "giveback": int(((mfe >= 1.0) & (t.r < 0)).sum()),
            "first_entry": hhmm(t.entry_min.min()), "last_entry": hhmm(t.entry_min.max()),
            "max_streak": streak(t.r), "multi_day": int((t.groupby("cal").size() > 1).sum()),
        })
        rows.append(s)
        if not opt:
            trades_pess = t
            t.to_csv(ROOT / "output/orb_calib_trades.csv", index=False)

    out = pd.DataFrame(rows)
    pd.set_option("display.width", 250)

    print("\n=== engine, v1-exact, both intrabar conventions ===")
    print(out[["label", "n", "win_pct", "ev_r", "pf", "usd", "med_risk_pts",
               "tgt_pct", "stop_pct", "flat_pct"]].round(2).to_string(index=False))

    p = rows[0]
    o = rows[1]
    cmp_ = [
        ("trade count",        TV["n"],        p["n"],            o["n"],            "count"),
        ("win %",              TV["win_pct"],  p["win_pct"],      o["win_pct"],      "pct"),
        ("profit factor",      TV["pf"],       p["pf"],           o["pf"],           "num"),
        ("total $",            TV["usd"],      p["usd"],          o["usd"],          "usd"),
        ("EV R/trade",         TV["ev_r"],     p["ev_r"],         o["ev_r"],         "num"),
        ("median stop pts",    TV["med_risk_pts"], p["med_risk_pts"], o["med_risk_pts"], "num"),
        ("target exits %",     100*TV["tgt"]/TV["n"],  p["tgt_pct"],  o["tgt_pct"],  "pct"),
        ("stop exits %",       100*TV["stop"]/TV["n"], p["stop_pct"], o["stop_pct"], "pct"),
        ("flat exits %",       100*TV["flat"]/TV["n"], p["flat_pct"], o["flat_pct"], "pct"),
        ("MFE >=0.75R %",      TV["mfe_075"],  p["mfe_075"],      o["mfe_075"],      "pct"),
        ("MFE >=1.00R %",      TV["mfe_100"],  p["mfe_100"],      o["mfe_100"],      "pct"),
        ("MFE >=1.25R %",      TV["mfe_125"],  p["mfe_125"],      o["mfe_125"],      "pct"),
        ("MFE >=1.50R %",      TV["mfe_150"],  p["mfe_150"],      o["mfe_150"],      "pct"),
        ("giveback (>=1R, red)", TV["giveback"], p["giveback"],   o["giveback"],     "count"),
        ("max losing streak",  TV["max_streak"], p["max_streak"], o["max_streak"],   "count"),
    ]
    print("\n=== published TV aggregate vs this engine ===")
    print(f"{'metric':<22}{'TV':>10}{'pessimistic':>14}{'optimistic':>13}   verdict")
    for name, tv, pv, ov, kind in cmp_:
        best = min((pv, "pess"), (ov, "opt"), key=lambda z: abs(z[0] - tv))
        rel = abs(best[0] - tv) / (abs(tv) if tv else 1)
        mark = "OK" if rel <= 0.15 else ("near" if rel <= 0.35 else "MISS")
        print(f"{name:<22}{tv:>10.2f}{pv:>14.2f}{ov:>13.2f}   {mark} ({best[1]}, {100*rel:.0f}% off)")

    print(f"\nentry-time envelope   TV {TV['first_entry']}-{TV['last_entry']}"
          f"   engine {p['first_entry']}-{p['last_entry']}")
    print(f"multi-trade days      TV 0   engine {p['multi_day']}")

    t = trades_pess
    print("\n=== landmark trades named in the export ===")
    for day, want_or, want_usd in (("2026-03-03", 101, -9623), ("2026-06-24", 54, -5393)):
        g = t[t.cal.dt.strftime("%Y-%m-%d") == day]
        if g.empty:
            print(f"  {day}: TV OR ~{want_or}pt, ${want_usd} -> ENGINE TOOK NO TRADE")
            continue
        r = g.iloc[0]
        print(f"  {day}: TV OR ~{want_or}pt ${want_usd}  ->  engine OR {r.or_width:.1f}pt "
              f"{'long' if r['dir']>0 else 'short'} risk {r.risk_pts:.1f}pt "
              f"${r.pnl_usd:,.0f} ({r.reason})")

    dow = t.groupby(t.cal.dt.dayofweek).agg(n=("r", "size"), win=("r", lambda s: 100*(s > 0).mean()),
                                            usd=("pnl_usd", "sum"))
    dow.index = ["Mon", "Tue", "Wed", "Thu", "Fri"][:len(dow)]
    print("\n=== weekday, engine (TV: Mon 25/32%/-13,135 · Tue 65%/+10,771 · Fri 70%/+20,911) ===")
    print(dow.round(1).to_string())
    out.to_csv(ROOT / "output/orb_calibration.csv", index=False)


if __name__ == "__main__":
    main()
