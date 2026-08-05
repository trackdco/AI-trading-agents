#!/usr/bin/env python3
"""NYA-IB50-01 trial 4 — winner-vs-loser diagnosis on the fit span (ANGUS:
"there has to be something that distinguishes winners from losers... see if
we can see losers before they happen"). Three parts:
(A) full fit-span stat pack; (B) discriminant table — every at-entry and
early-in-trade variable, winner mean vs loser mean, Welch t, rank AUC;
(C) causal early-cut policy arms (exit at t's close on a dying/flow-against
read) scored against the baseline walk — the agents-defense question run
mechanically first.

    python -m scripts.nya_ib50_diagnosis
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0


def auc(x, y):
    m = x.notna()
    if m.sum() < 10 or y[m].nunique() < 2:
        return np.nan
    xv, yv = x[m].to_numpy(float), y[m].to_numpy(int)
    ranks = pd.Series(xv).rank().to_numpy()
    n1, n0 = int(yv.sum()), int((1 - yv).sum())
    u = ranks[yv == 1].sum() - n1 * (n1 + 1) / 2
    return float(u / (n1 * n0))


def main() -> None:
    A = pd.read_parquet(ROOT / "output/nya_ib50_deep.parquet")
    Wn, Lo = A[A.win == 1], A[A.win == 0]
    net = A.pts - FR
    r_ = A.net_r

    print("=" * 30, "A. FIT-SPAN STAT PACK (IB50 continuation, default no-BE)", "=" * 10)
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    print(f"n={len(A)} | WR {(net>0).mean():.1%} | {net.sum():+.0f}pts | "
          f"${160*r_.sum():+,.0f} @$160-risk | PF {gw/max(gl,1e-9):.2f}")
    print(f"payoff {net[net>0].mean()/max(-net[net<=0].mean(),1e-9):.2f} | "
          f"median win {net[net>0].median():+.1f}pts / loss {net[net<=0].median():+.1f}pts | "
          f"mean risk {A.risk.mean():.1f}pts (IB/2)")
    seq = (160 * r_).cumsum()
    dd = float((seq.cummax() - seq).max())
    sgn = (net > 0).astype(int)
    streak = max((len(list(g)) for k, g in __import__("itertools").groupby(sgn) if k == 0),
                 default=0)
    print(f"trade-seq maxDD ${dd:,.0f} | max losing streak {streak}")
    for h, g in A.groupby(A.day.str[:7].map(lambda m: m[:4] + ("H1" if m[5:7] < "07" else "H2"))):
        gn = g.pts - FR
        hw, hl = gn[gn > 0].sum(), -gn[gn <= 0].sum()
        print(f"  {h}: n={len(g)} WR {(gn>0).mean():.0%} {gn.sum():+.0f}pts "
              f"PF {hw/max(hl,1e-9):.2f}")

    print("\n" + "=" * 30, "B. WINNER-vs-LOSER DISCRIMINANT TABLE", "=" * 24)
    VARS = [
        ("risk (IB size/2, pts)", "risk"), ("frontrun entry", "frontrun"),
        ("weekday trailing rate", "roll_wd"), ("entry delta (signed)", "e_delta"),
        ("entry dz (signed)", "e_dz"), ("book imb (signed)", "e_imb"),
        ("conviction score", "score"),
        ("r at t+5 (close R)", "r5"), ("MFE by t+5", "mf5"), ("MAE by t+5", "ma5"),
        ("cvd since entry t+5", "cvd5"), ("r at t+15", "r15"), ("MFE by t+15", "mf15"),
        ("MAE by t+15", "ma15"), ("cvd since entry t+15", "cvd15"),
    ]
    print(f"{'variable':28s} {'win-mean':>9s} {'lose-mean':>9s} {'t':>6s} {'AUC':>5s}  n")
    for lbl, c in VARS:
        if c not in A.columns:
            continue
        w, l = Wn[c].dropna(), Lo[c].dropna()
        if len(w) < 8 or len(l) < 8:
            print(f"{lbl:28s} — thin (n={len(w)}/{len(l)})")
            continue
        t = (w.mean() - l.mean()) / np.sqrt(w.var(ddof=1)/len(w) + l.var(ddof=1)/len(l))
        a = auc(A[c], A.win)
        print(f"{lbl:28s} {w.mean():+9.2f} {l.mean():+9.2f} {t:+6.2f} {a:5.2f}  {len(w)+len(l)}")

    print("\n" + "=" * 30, "C. EARLY-CUT POLICY ARMS (causal, exit at t's close)", "=" * 12)
    base_total = 160 * r_.sum()
    print(f"baseline (no policy): ${base_total:+,.0f}")
    POLS = [
        ("cut t+5 if MAE<=-0.5R", 5, lambda g, t: g[f"ma{t}"] <= -0.5),
        ("cut t+15 if MAE<=-0.5R", 15, lambda g, t: g[f"ma{t}"] <= -0.5),
        ("cut t+15 if cvd against", 15, lambda g, t: g[f"cvd{t}"] <= 0),
        ("cut t+15 if dying OR cvd against", 15,
         lambda g, t: (g[f"ma{t}"] <= -0.5) | (g[f"cvd{t}"] <= 0)),
        ("cut t+30 if cvd against", 30, lambda g, t: g[f"cvd{t}"] <= 0),
        ("cut t+15 red AND cvd against", 15,
         lambda g, t: (g[f"r{t}"] < 0) & (g[f"cvd{t}"] <= 0)),
    ]
    for lbl, t, cond in POLS:
        open_t = A[f"open{t}"] == 1
        c = cond(A, t).fillna(False) & open_t & A[f"r{t}"].notna()
        new_r = np.where(c, A[f"r{t}"] - FR / A.risk, r_)
        cut = A[c]
        saved = 160 * (new_r.sum() - r_.sum())
        # what the cut trades would have done (their baseline outcome)
        print(f"  {lbl:34s}: cuts {c.sum():3d} (of {int(open_t.sum())} open) | "
              f"cut-cohort baseline WR {cut.win.mean() if len(cut) else 0:.0%} | "
              f"total ${160*new_r.sum():+,.0f} (delta {saved:+,.0f})")


if __name__ == "__main__":
    main()
