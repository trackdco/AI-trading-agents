#!/usr/bin/env python3
"""Winner/loser optimisation under interleaved month-level cross-validation.

ANGUS 2026-08-06: *"the edge lies in having a higher rr target, and then cutting as many
losers as we can as possible without cutting winners. Take 3 random months from h2 2025, and
3 random months in the 2026 data we have. Calibrate and optimise, see if it holds across the
other months we have flow data for in 2025/2026."*

WHY HIS DESIGN IS THE RIGHT ONE. A chronological fit-then-test split confounds two different
failures: overfitting, and regime drift. Interleaving fit and test months inside the same
regime isolates the first. That matters here because the regime check
(research/findings/FVT-CORRECTED.md and the session log) showed the "Trump era" is not one
regime at all -- H1-2025 is the most volatile stretch in the sample (daily range 1.86%,
sd 1.90%) and H2-2025 is the calmest (1.12%, 0.93%). Chronological splits across that boundary
measure the weather, not the model.

THE ONE CHANGE: THE DRAW IS REPEATED. A single 3+3 month pick is one sample and can be lucky.
This repeats it N times and reports the DISTRIBUTION of out-of-fit results, plus the
in-fit-minus-out-of-fit gap, which is the direct measure of how much the optimisation is
fitting noise.

Universe: months where footprint/flow data exists (2025-06 → 2026-07).
Fit:  3 random months from H2-2025 + 3 random months from 2026.
Test: every remaining month in the universe.

    python -m scripts.fvt_monthcv [--draws 200]
"""

from __future__ import annotations

import argparse
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.fvt_model as F  # noqa: E402
from scripts.fvt_optimise import entries, evaluate  # noqa: E402

FRIC = 0.5
MIN_FIT = 60          # a config must have at least this many fit trades to be selectable
RRS = (1.5, 2.0, 2.5, 3.0, 4.0)
STOPS = (0.75, 1.0, 1.25)
FLOW = ("off", "drop_top", "keep_bottom")     # the loser-cutting lever Angus named
SESS = ("all", "PM", "AM", "E20", "LDN")


def base(b: pd.DataFrame) -> pd.DataFrame:
    """All continuation entries with flow attached, once. Configs are filters on this."""
    E = entries(b)
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    frames = []
    for sm, rr in product(STOPS, RRS):
        D = evaluate(E, sm, rr, 15, 1)
        if D.empty:
            continue
        D = D.assign(sm=sm, rr=rr)
        frames.append(D)
    A = pd.concat(frames, ignore_index=True)
    # entry-bar aggressor delta: legal because FVT market-enters on a CLOSED candle
    key = entries(b)
    K = pd.DataFrame([{"day": e["day"], "win": e["win"], "mins_in": e["mins_in"],
                       "dir": e["dir"]} for e in key])
    K = K.drop_duplicates(["day", "win"])
    A = A.merge(K[["day", "win", "dir"]], on=["day", "win"], how="left")
    mi = (pd.to_datetime(A.day) + pd.to_timedelta(
        A.win.map({"AM": 9 * 60 + 33, "PM": 14 * 60, "E18": 18 * 60,
                   "E20": 20 * 60, "LDN": 3 * 60}), unit="m"))
    A["mi"] = mi.dt.tz_localize("America/New_York", ambiguous=True, nonexistent="shift_forward")
    A = A.merge(fp[["delta", "vol"]], left_on="mi", right_index=True, how="left")
    A["dratio"] = np.where(A.vol > 0, (A.delta * A["dir"]) / A.vol.replace(0, np.nan), np.nan)
    A["net"] = A.pts + 2.0 - FRIC          # undo the 2.0 charged inside evaluate, apply 0.5
    A["month"] = A.day.str[:7]
    return A


def apply_cfg(A: pd.DataFrame, sm, rr, flow, sess, q_lo, q_hi) -> pd.DataFrame:
    S = A[(A.sm == sm) & (A.rr == rr)]
    if sess != "all":
        S = S[S.win == sess]
    if flow == "drop_top":
        S = S[S.dratio < q_hi]
    elif flow == "keep_bottom":
        S = S[S.dratio <= q_lo]
    return S


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()

    b = F.load()
    b = b[(b.day >= "2025-06-01")]
    A = base(b)
    A = A[A.dratio.notna()]
    months = sorted(A.month.unique())
    h2 = [m for m in months if "2025-07" <= m <= "2025-12"]
    y26 = [m for m in months if m.startswith("2026")]
    print(f"{len(A):,} config-trades over {len(months)} months: {months[0]}..{months[-1]}")
    print(f"  H2-2025 pool: {h2}\n  2026 pool:    {y26}", flush=True)

    q_lo, q_hi = A.dratio.quantile([1 / 3, 2 / 3])
    cfgs = list(product(STOPS, RRS, FLOW, SESS))
    print(f"{len(cfgs)} candidate configs; {a.draws} random 3+3 month draws", flush=True)

    rng = np.random.default_rng(20260806)
    recs = []
    for d in range(a.draws):
        fit_m = list(rng.choice(h2, 3, replace=False)) + list(rng.choice(y26, 3, replace=False))
        test_m = [m for m in months if m not in fit_m]
        Afit = A[A.month.isin(fit_m)]
        Atst = A[A.month.isin(test_m)]
        best, bn = None, -1e9
        for c in cfgs:
            S = apply_cfg(Afit, *c, q_lo, q_hi)
            if len(S) < MIN_FIT:
                continue
            m = S.net.mean()
            if m > bn:
                bn, best = m, c
        if best is None:
            continue
        T = apply_cfg(Atst, *best, q_lo, q_hi)
        if len(T) < 30:
            continue
        recs.append({"draw": d, "cfg": str(best), "sm": best[0], "rr": best[1],
                     "flow": best[2], "sess": best[3],
                     "fit": bn, "oos": T.net.mean(), "n_oos": len(T),
                     "oos_day": T.net.sum() / max(len(test_m) * 21, 1)})
    R = pd.DataFrame(recs)
    R.to_parquet(ROOT / "output/fvt_monthcv.parquet", index=False)

    print()
    print(f"=== {len(R)} completed draws ===")
    print(f"  in-fit  net/trade : median {R.fit.median():+.2f}   mean {R.fit.mean():+.2f}")
    print(f"  out-fit net/trade : median {R.oos.median():+.2f}   mean {R.oos.mean():+.2f}")
    print(f"  OPTIMISATION GAP  : {R.fit.mean()-R.oos.mean():+.2f} pt/trade lost from fit to test")
    print(f"  draws with OOS > 0: {(R.oos>0).mean():.0%}")
    print(f"  OOS 10th pct {R.oos.quantile(.1):+.2f} | 25th {R.oos.quantile(.25):+.2f} | "
          f"75th {R.oos.quantile(.75):+.2f} | 90th {R.oos.quantile(.9):+.2f}")
    print()
    print("  what the optimiser picked, across draws:")
    for c in ("rr", "sm", "flow", "sess"):
        vc = R[c].value_counts(normalize=True)
        print(f"    {c:5s} " + "  ".join(f"{k}={v:.0%}" for k, v in vc.head(5).items()))
    print()
    # benchmark: the fixed unoptimised base, same test months
    print("  BENCHMARK — no optimisation at all, on the same data:")
    for rr in RRS:
        S = A[(A.sm == 1.0) & (A.rr == rr)]
        print(f"    stop×1.0 RR{rr} all sessions, no flow filter: {S.net.mean():+.2f} pt "
              f"on {len(S):,} trades")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
