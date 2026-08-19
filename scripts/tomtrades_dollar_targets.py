#!/usr/bin/env python3
"""What if the target were a fixed dollar amount instead of 50% of the impulse?

The autopsy's finding was that the target is set by the hour's geometry while the entry
arrives late, so the reward shrinks exactly as the stop grows — median reward:risk 0.40,
and 72% of signals discarded because the 50% level was already gone before the fill.

A FIXED DOLLAR target breaks that coupling. It does not care where the impulse was, it
does not move as price retraces, and it is always ahead of the entry — so the 6,073
skipped signals come back into the book. That last point matters more than it sounds:
the impulse book is not just differently-targeted, it is a SELECTED SUBSET, and the
selection is "trades where a sliver of the move was left". Comparing a fixed target
against it on different populations would be comparing two different books.

So both are reported: the full signal set, and the 2,411-trade subset the impulse target
admitted, so the exit can be judged with the population held fixed.

Costs are charged, because a small fixed target is exactly where friction bites: at
GC's $10/tick a $100 target is ten ticks of gross profit.

    python scripts/tomtrades_dollar_targets.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research.tomtrades import autopsy as AU
from src.research.tomtrades import data as D
from src.research.tomtrades import detector as DT

PV = 100.0            # GC: $100 per point
TICK_DOLLARS = 10.0   # 0.10 pt x $100
MAX_HOLD = 240


def run(df: pd.DataFrame, sig: pd.DataFrame, dollars: float | None,
        cost_ticks: float) -> pd.DataFrame:
    """Walk each signal to a fixed-dollar target, or to the impulse target if None."""
    o, h, l_, c = (df[x].to_numpy() for x in ("open", "high", "low", "close"))
    ts = df["ts_event"].to_numpy()
    n = len(df)
    out = []
    for r in sig.itertuples(index=False):
        i0 = int(r.entry_idx)
        if i0 >= n:
            continue
        entry, d = o[i0], int(r.direction)
        stop = float(r.stop)
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        if dollars is None:
            continue
        target = entry + d * (dollars / PV)
        px, why = np.nan, "timeout"
        for j in range(i0, min(i0 + MAX_HOLD, n)):
            if (h[j] >= stop) if d < 0 else (l_[j] <= stop):
                px, why = stop, "stop"
                break
            if (l_[j] <= target) if d < 0 else (h[j] >= target):
                px, why = target, "target"
                break
        else:
            j = min(i0 + MAX_HOLD, n) - 1
            px = c[j]
        gross = d * (px - entry) * PV
        out.append({"signal_ts": r.signal_ts, "entry_ts": ts[i0], "risk_pts": risk,
                    "risk_usd": risk * PV, "gross": gross,
                    "net": gross - cost_ticks * TICK_DOLLARS, "reason": why})
    t = pd.DataFrame(out)
    if t.empty:
        return t
    t["sess_day"] = pd.to_datetime(t.entry_ts).dt.tz_convert("America/New_York").dt.date
    t["out"] = t.net / t.risk_usd          # R, for the day-clustered interval
    t["win"] = (t.net > 0).astype(float)
    return t


def summarise(t: pd.DataFrame, label: str, n_all: int) -> dict:
    if len(t) < 30:
        return {"target": label, "n": len(t)}
    lo, hi = AU.dboot_mean(t, "out")
    return {"target": label, "n": len(t), "pct_of_signals": 100 * len(t) / n_all,
            "win_pct": 100 * t.win.mean(), "mean_usd": t.net.mean(),
            "ev_r": t["out"].mean(), "lo": lo, "hi": hi,
            "total_usd": t.net.sum(), "target_hit_pct": 100 * (t.reason == "target").mean(),
            "median_risk_usd": t.risk_usd.median()}


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config/tomtrades.yaml").read_text())
    gc = D.load(str(ROOT / "data/gc_1m.parquet"))
    dx = D.load(str(ROOT / "data/dx_1m.parquet"))
    j6 = D.load(str(ROOT / "data/6j_1m.parquet"))
    ctx = DT.build_context(gc, cfg, dxy=dx, yen=j6)
    off = {k: np.ones(len(gc), dtype=bool)
           for k in ("session", "c1", "c2", "c3", "c4", "c5")}
    sig = DT.detect(ctx, cfg, off)
    print(f"{len(sig):,} trigger signals", flush=True)

    cfg_nc = {**cfg, "risk": {**cfg["risk"], "max_trades_per_day": 0}}
    imp = DT.simulate(gc, sig, cfg_nc)
    keep = set(imp["signal_ts"])
    sub = sig[sig.signal_ts.isin(keep)].reset_index(drop=True)
    print(f"impulse target admitted {len(imp):,} ({100*len(imp)/len(sig):.1f}%)", flush=True)

    rows = []
    for cost in (0.0, 1.0):
        base = imp.assign(
            risk_usd=imp.risk * PV,
            net=imp.pnl_r * imp.risk * PV - cost * TICK_DOLLARS,
            reason=imp.exit_reason,
            entry_ts=imp.entry_ts)
        base["sess_day"] = pd.to_datetime(base.entry_ts).dt.tz_convert(
            "America/New_York").dt.date
        base["out"] = base.net / base.risk_usd
        base["win"] = (base.net > 0).astype(float)
        rows.append({**summarise(base, "impulse 50% (his rule)", len(sig)),
                     "cost_ticks": cost})
        for dollars in (50, 100, 200, 300, 500):
            for pop, tag in ((sig, "all signals"), (sub, "impulse subset")):
                t = run(gc, pop, dollars, cost)
                s = summarise(t, f"${dollars} fixed · {tag}", len(sig))
                rows.append({**s, "cost_ticks": cost})
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 240)
    for cost in (0.0, 1.0):
        print(f"\n=== cost {cost:g} tick round turn (${cost*TICK_DOLLARS:.0f}) ===")
        print(out[out.cost_ticks == cost].drop(columns="cost_ticks")
                 .round(3).to_string(index=False), flush=True)
    out.to_csv(ROOT / "output/tomtrades_dollar_targets.csv", index=False)


if __name__ == "__main__":
    main()
