#!/usr/bin/env python3
"""The iFVG book split by session, on the CORRECTED detector.

Two reasons this exists.

1. The published session result (NY 09:30-11:00, pre-cost EV -0.026 -> -0.071) was
   measured on n=21,219 -- the population the CORRECTION withdrew -- and was never
   re-run. It has been cited since as though settled. It is not.
2. Everything measured so far ran with NO session filter, so 88.5% of the book sits in
   hours he tells students to avoid. A comparison that never enters his window is not a
   test of his model.

Also prices the three macro windows, which are narrower than the session and have never
been tested at all.

    python scripts/dodgy_session_split.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.dodgy_ifvg_test import load_nq, signals
from scripts.dodgy_structural_target import attach_target, draw_levels, row, simulate

# label -> (start_hour, end_hour) in NY clock, half-open
BOXES = {
    "ALL (no filter)":      None,
    "Asia 20:00-00:00":     (20.0, 24.0),
    "London 02:00-05:00":   (2.0, 5.0),
    "NY AM 08:30-11:00":    (8.5, 11.0),
    "NY 09:30-11:00":       (9.5, 11.0),
    "NY mid 11:00-16:00":   (11.0, 16.0),
    "macro 08:50-09:10":    (8 + 50 / 60, 9 + 10 / 60),
    "macro 09:50-10:10":    (9 + 50 / 60, 10 + 10 / 60),
    "macro 10:50-11:10":    (10 + 50 / 60, 11 + 10 / 60),
    "all 3 macros":         "MACROS",
}


def mask_for(ts: pd.DatetimeIndex, spec) -> np.ndarray:
    if spec is None:
        return np.ones(len(ts), bool)
    hh = ts.hour + ts.minute / 60.0
    if spec == "MACROS":
        m = np.zeros(len(ts), bool)
        for a, b in ((8 + 50 / 60, 9 + 10 / 60), (9 + 50 / 60, 10 + 10 / 60),
                     (10 + 50 / 60, 11 + 10 / 60)):
            m |= (hh >= a) & (hh < b)
        return m
    a, b = spec
    return (hh >= a) & (hh < b) if a < b else ((hh >= a) | (hh < b))


def main() -> None:
    bars = load_nq()
    lv = draw_levels(bars)
    sig = attach_target(signals(bars, require_sweep=False, require_revisit=True), bars, lv)
    ts = pd.DatetimeIndex(sig.ts)
    print(f"NQ {len(bars):,} bars · {len(sig):,} signals (corrected detector)\n", flush=True)

    res = []
    for label, spec in BOXES.items():
        s = sig[mask_for(ts, spec)]
        if len(s) < 200:
            print(f"  {label:22s} only {len(s)} signals — skipped")
            continue
        for mode, mrr, mlab in (("fixed2r", 0.0, "fixed 2R"),
                                ("structural", 0.0, "structural")):
            t = simulate(bars, s, mode, mrr)
            if len(t) < 200:
                continue
            r = row(t, f"{label:22s} · {mlab}")
            res.append(r)
        print(f"  {label:22s} {len(s):6,} signals", flush=True)

    d = pd.DataFrame([r for r in res if "ev" in r])
    d["ci"] = d.apply(lambda r: f"[{r.lo:+.3f},{r.hi:+.3f}]", axis=1)
    d["eras"] = np.where(d.both, "BOTH", "-")
    print("\n=== EV by session, corrected detector, dual currency ===")
    print(d[["variant", "n", "per_day", "win_pct", "ev", "ci", "h1", "h2", "eras"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print("\n=== Law 2 companion ===")
    print(d[["variant", "n", "med_stop", "cost_r", "med_rr", "usd", "usd_day"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    out = ROOT / "output/dodgy_session_split.csv"
    d.to_csv(out, index=False)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
