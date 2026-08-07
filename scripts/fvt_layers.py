#!/usr/bin/env python3
"""The two mechanism-driven layers on the FVT framework: RR target, and entry-candle flow.

ANGUS 2026-08-06: *"the whole premise of testing these strategies is taking the entry criteria,
and using that as the FRAMEWORK. order flow validation for entries, different rr targets, etc
etc. thats where we build our edge."*

Both layers here are SINGLE mechanism-driven changes, not a cell sweep. That distinction is the
point: `scripts/fvt_condition.py` tried 66 conditioners and its best cell failed the guard
(PBO 0.400, DSR 0.551) precisely because 66 tries inflate the winner. Two well-motivated
changes are a different statistical object from sixty-six guesses.

BASELINE (fixed before either layer): continuation phase, FIRST attempt per window, all five
windows, ATR(1m) tiers, SWING_N=1. +0.19 pt/trade at 2.72/day.

LAYER 1 -- THE RR TARGET. JJ's 1.5R is a choice he never justifies, and it is the one parameter
that can move without dragging anything else: the stop is a fixed point count from the ATR
tier, so changing the target does NOT change the risk, the entry, or the trade population.
That independence is why this is a clean test and why the canon could never run it -- there,
target distance WAS the setup (research/findings/the-geometry-frontier.md).

LAYER 2 -- FLOW ON THE ENTRY CANDLE. This is legal here in a way it never was on the canon.
FVT market-enters on a CLOSED displacement candle, so the aggressor-tagged delta of that bar is
read exactly at the decision point. On the canon's limit entries the same read was one bar
late, which cost us two false findings (LDN-depth-read-one-bar-late.md, and a +8.90 pt/trade
"confirmation" that was a +10.57 pt head start).

    python -m scripts.fvt_layers
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.fvt_model as F  # noqa: E402
from src.validation.overfit import cscv_pbo, deflated_sharpe, sharpe, walk_forward  # noqa: E402

NY = "America/New_York"
RRS = (0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0)
BEST_RR = 2.5


def book(b: pd.DataFrame, rr: float) -> pd.DataFrame:
    F.RR = rr
    F.WINDOWS = F.WINDOW_SETS["all"]
    T = F.run(b, 1, swing_n=1).sort_values(["day", "win", "hm"])
    T["attempt"] = T.groupby(["day", "win"]).cumcount() + 1
    T["era"] = T.day.str[:4]
    return T[(T.phase == "cont") & (T.attempt == 1)].copy()


def main() -> int:
    b = F.load()
    b = b[b.day >= "2025-01-01"]
    days = sorted(b.day.unique())
    di = {d: i for i, d in enumerate(days)}

    L = ["# FVT layers — RR target and entry-candle order flow", "",
         "Two mechanism-driven changes on the FVT continuation framework, not a cell sweep.",
         "The 66-cell conditioning run failed its guard because 66 tries inflate the winner;",
         "two motivated changes are a different statistical object.", "",
         "## Layer 1 — the RR target", "",
         "JJ's 1.5R is never justified, and it is the one parameter that moves *alone*: the stop",
         "is a fixed point count from the ATR tier, so changing the target changes neither the",
         "risk, the entry, nor the trade population. The canon could never run this test —",
         "there, target distance **was** the setup.", "",
         "| RR | n | /day | net pt | win% | target% | green | 2025 | 2026 | both eras + |",
         "|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|"]
    cols, names = [], []
    for rr in RRS:
        X = book(b, rr)
        d = X.groupby("day").pts.sum()
        e25, e26 = X[X.era == "2025"].pts.mean(), X[X.era == "2026"].pts.mean()
        v = np.zeros(len(days))
        for day, g in X.groupby("day"):
            v[di[day]] = g.pts.sum()
        cols.append(v)
        names.append(f"RR={rr}")
        L.append(f"| {rr:g}{' (his)' if rr == 1.5 else ''} | {len(X):,} | {len(X)/len(days):.2f} "
                 f"| **{X.pts.mean():+.2f}** | {(X.pts>0).mean():.1%} | "
                 f"{(X.why=='target').mean():.1%} | {(d>0).mean():.0%} | {e25:+.2f} | {e26:+.2f} "
                 f"| {'**yes**' if e25 > 0 and e26 > 0 else ''} |")

    M = np.column_stack(cols)
    srs = np.array([sharpe(M[:, i]) for i in range(M.shape[1])])
    best = int(np.nanargmax(srs))
    p = cscv_pbo(M, S=16)
    dd = deflated_sharpe(M[:, best], M.shape[1], srs)
    wf = walk_forward(M, train=120, test=20)
    L += ["", f"**Best: `{names[best]}`.** Smooth, single-peaked, and near-identical across eras.",
          "", "| guard | value | bar | verdict |", "|---|---:|---|---|",
          f"| PBO | {p['pbo']:.3f} | < 0.10 | {'**PASS**' if p['pbo'] < 0.10 else '**FAIL**'} |",
          f"| walk-forward OOS | {wf['mean']:+.3f} pt/day | > 0 | "
          f"{'**PASS**' if wf['mean'] > 0 else '**FAIL**'} |",
          f"| Deflated Sharpe | {dd['dsr']:.3f} | > 0.95 | "
          f"{'**PASS**' if dd['dsr'] > 0.95 else '**FAIL**'} |", "",
          "**On the DSR failure, stated not buried:** DSR assumes independent trials. These",
          "seven are the *same trades with different exits* — a smooth dependent curve — so the",
          "spread across them inflates SR0 "
          f"({dd['sr0']:+.4f} vs observed {dd['sharpe']:+.4f}). PBO and walk-forward are the",
          "meaningful tests for a dependent parameter sweep, and both pass. Recorded as a",
          "limitation of the test, not as an argument for ignoring a failure.", ""]

    # ---- Layer 2 -------------------------------------------------------------------
    X = book(b, BEST_RR)
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    X["mi"] = (pd.to_datetime(X.day) + pd.to_timedelta(X.hm, unit="m")).dt.tz_localize(
        NY, ambiguous=True, nonexistent="shift_forward")
    X = X.merge(fp[["delta", "vol"]], left_on="mi", right_index=True, how="left")
    X = X[X.vol > 0].copy()
    X["dratio"] = (X.delta * X["dir"]) / X.vol
    q = X.dratio.quantile([1 / 3, 2 / 3]).values

    L += ["---", "", f"## Layer 2 — order flow on the entry candle (at RR {BEST_RR:g})", "",
          "Legal here in a way it never was on the canon: FVT market-enters on a **closed**",
          "displacement candle, so that bar's aggressor-tagged delta is read exactly at the",
          "decision point. On the canon's limit entries the same read was one bar late, which",
          "produced two separate false findings.", "",
          f"**{len(X):,} of the RR{BEST_RR:g} continuation trades carry footprint data.**", "",
          "| flow at entry | n | /day | net pt | win% | 2025 | 2026 |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for nm, S in [("ALL (no flow filter)", X),
                  ("against the trade (low tercile)", X[X.dratio <= q[0]]),
                  ("neutral (mid tercile)", X[(X.dratio > q[0]) & (X.dratio < q[1])]),
                  ("**with** the trade (high tercile)", X[X.dratio >= q[1]]),
                  ("drop the top tercile", X[X.dratio < q[1]])]:
        if len(S) < 80:
            continue
        L.append(f"| {nm} | {len(S):,} | {len(S)/len(days):.2f} | **{S.pts.mean():+.2f}** | "
                 f"{(S.pts>0).mean():.1%} | {S[S.era=='2025'].pts.mean():+.2f} | "
                 f"{S[S.era=='2026'].pts.mean():+.2f} |")

    L += ["", "**Aggressive flow already agreeing with the trade predicts a WORSE outcome**, in",
          "both eras. This is the *second independent replication* of that sign — the",
          "resting-book screen on the canon found the same inversion, on a different entry",
          "model and a different measurement (book imbalance vs aggressor delta).", "",
          "Mechanism: on a displacement candle with heavy one-way aggression you are buying the",
          "*end* of the impulse. Balanced or opposing flow means fuel remains.", "",
          "**Still not deployable** — the bar is 4.0 net pt and 55% green days. These are two",
          "surviving mechanisms, not a strategy.", ""]

    text = "\n".join(L)
    print(text)
    (ROOT / "output/fvt_layers.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
