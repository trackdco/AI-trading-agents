#!/usr/bin/env python3
"""P6 — pre-market CVD pressure gate study (NYA-CVD-01). DECLARATION: this
header is the study's pre-registration, committed before the run.

CLAIM UNDER TEST (Fabervaale Dec-30 pattern, generalized): when the pre-market
tape shows strong one-sided aggressive flow while PRICE stays balanced, the
open tends to resolve in the flow's direction — pressure builds before price
moves, and the open releases it.

FROZEN DEFINITIONS:
  window        06:00-09:29 ET primary; 08:00-09:29 declared variant.
  cvd_press     sum of minute delta over the window / baseline (median of
                prior 20 sessions' |same-window sum|). |press| >= 1.5 = strong.
  balanced      |window net price change| <= 0.35 x window range.
  GATE ON       strong press AND balanced; direction = sign(press).
  outcome       09:30 open -> 10:30 close move sign and magnitude (pts);
                secondary: full-day close.
  KILL          gate-on directional hit rate < 55% on the 10:30 outcome in
                either flow-span half-year era (2025H2 / 2026H1) -> the gate
                is not adopted as a feature (study closes negative).
  NO STRATEGY   this is a feature study — no entries, no exits, no arms
                beyond the two declared windows. Both recorded in the ledger.

    python -m scripts.nya_cvd_gate_study
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run_window(FL, bars, w0: str, label: str):
    rows = []
    hist: list[float] = []
    for d, f in FL.groupby("gday"):
        win = f[(f.clock >= w0) & (f.clock < "09:30")]
        rth = bars[(bars.gday == d)]
        op = rth[rth.clock >= "09:30"]
        mid = rth[(rth.clock >= "10:30")]
        eod = rth[rth.clock >= "15:59"]
        w_minutes = (int("09:30"[:2]) * 60 + 30) - (int(w0[:2]) * 60 + int(w0[3:]))
        if len(win) < 0.8 * w_minutes or not len(op) or not len(mid):
            continue
        dsum = float(win.delta.sum())
        base = np.median(np.abs(hist[-20:])) if len(hist) >= 5 else np.nan
        hist.append(dsum)
        if base != base or base <= 0:
            continue
        press = dsum / base
        prange = float(win.high.max() - win.low.min())
        pnet = float(win.close.iloc[-1] - win.close.iloc[0])
        balanced = abs(pnet) <= 0.35 * max(prange, 1e-9)
        o = float(op.open.iloc[0])
        m = float(mid.close.iloc[0])
        e = float(eod.close.iloc[0]) if len(eod) else np.nan
        rows.append(dict(day=d, half=d[:4] + ("H1" if d[5:7] < "07" else "H2"),
                         press=press, balanced=balanced,
                         gate=int(abs(press) >= 1.5 and balanced),
                         gdir=int(np.sign(press)),
                         am=m - o, day_move=(e - o) if e == e else np.nan))
    T = pd.DataFrame(rows)
    if not len(T):
        print(f"== window {label}: 0 usable sessions ==")
        return T, T
    g = T[T.gate == 1]
    print(f"== window {label}: {len(T)} sessions, gate fires {len(g)} ({len(g)/max(len(T),1):.0%}) ==")
    base_up = (T.am > 0).mean()
    hit = (np.sign(g.am) == g.gdir).mean() if len(g) else float("nan")
    print(f"  base P(am up) {base_up:.0%} | gated directional hit (09:30->10:30): {hit:.0%}")
    for h, gg in g.groupby("half"):
        hh = (np.sign(gg.am) == gg.gdir).mean()
        mag = (gg.am * gg.gdir).mean()
        print(f"    {h}: n={len(gg)} hit {hh:.0%} avg move-with-gate {mag:+.1f} pts")
    if len(g):
        dd = g.dropna(subset=["day_move"])
        print(f"  full-day hit: {(np.sign(dd.day_move) == dd.gdir).mean():.0%} "
              f"avg {(dd.day_move * dd.gdir).mean():+.1f} pts")
    return T, g


def main() -> None:
    FL = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    for w0, label in (("06:00", "06:00-09:29 (primary)"), ("08:00", "08:00-09:29 (variant)")):
        run_window(FL, B, w0, label)


if __name__ == "__main__":
    main()
