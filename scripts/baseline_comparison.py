#!/usr/bin/env python3
"""RANKED COMPARISON — every baselined strategy, both traders, one table.

Reads the trade logs the baseline scripts wrote. Computes nothing new about any strategy: it
only puts already-scored books side by side on the SAME exit convention
(research/zxcked/strategies/EXIT-CONVENTION-LOCKED.md) so a difference between two rows is a
difference in edge, not in bookkeeping.

COSTS. $25 per NQ round-turn ($5 commission + one tick of slippage each way), NQ point value
$20. Cost in R = 25 / (median_risk_pts * 20), computed per card because each card's own stop
rule sets its R. Reported as a separate column; R itself is never net of costs.

STATISTICS. t = mean(R) / (sd(R)/sqrt(n)) on the GROSS R series; effect = t / sqrt(n) = the
standardised per-trade effect, which is the quantity the deflation bar is stated in.
Deflation bar at N = 293 trials = +0.6978.

    python -m scripts.baseline_comparison
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RT_COST_USD = 25.0        # $5 commission + 1 tick slippage, each way
NQ_POINT_USD = 20.0
DEFLATION_BAR = 0.6978    # N = 293 trials
MATCHED_SPAN_START = "2025-06-01"   # the zxck cards' span, for the fairness row only


def summarise(name: str, R: pd.Series, risk_pts: pd.Series | float, note: str = "") -> dict:
    R = pd.Series(R).astype(float).reset_index(drop=True)
    n = len(R)
    # PER-TRADE cost, then averaged. A card whose stop varies trade to trade pays a different
    # fraction of R on each one, and the mean of those fractions is the real drag. Using the
    # cost of the median stop instead understates it, because 1/x is convex.
    rp = (pd.Series(risk_pts).astype(float).reset_index(drop=True)
          if np.ndim(risk_pts) else pd.Series([float(risk_pts)] * n))
    per_trade_cost = RT_COST_USD / (rp * NQ_POINT_USD)
    cost = float(per_trade_cost.mean())
    net = R - per_trade_cost.to_numpy()
    eq = R.cumsum()
    sd = float(R.std(ddof=1))
    t = float(R.mean() / (sd / np.sqrt(n))) if sd > 0 else np.nan
    sdn = float(net.std(ddof=1))
    tn = float(net.mean() / (sdn / np.sqrt(n))) if sdn > 0 else np.nan
    return {"card": name, "n": n,
            "win%": 100 * float((R >= 2).mean()),
            "BE%": 100 * float((R == 0).mean()),
            "loss%": 100 * float((R <= -1).mean()),
            "avgR": float(R.mean()), "med_risk_pts": float(rp.median()), "cost": cost,
            "exp": float(R.mean()) - cost, "totR": float(R.sum()),
            "maxDD": float((eq.cummax() - eq).max()),
            "t": t, "effect": t / np.sqrt(n),
            "t_net": tn, "effect_net": tn / np.sqrt(n), "note": note}


def load() -> list[dict]:
    ash = pd.read_csv(ROOT / "research/ash10hazard/strategies/ash-unicorn-sb-raw-trades.csv")
    keyo = pd.read_csv(ROOT / "research/zxcked/strategies/zxck-10am-keyopen-bounded.csv")
    rem = pd.read_csv(ROOT / "research/zxcked/strategies/zxck-remaining-raw-trades.csv")
    wick = pd.read_csv(ROOT / "research/zxcked/strategies/zxck-wick-ce-raw-trades.csv")

    dec = keyo[(keyo.kind == "decidable") & keyo.R.notna()]
    ifvg = rem[rem.card == "zxck-ifvg-50"]
    cisd = rem[rem.card == "zxck-cisd"]
    m = ash[ash.date >= MATCHED_SPAN_START]

    return [
        summarise("ash-unicorn-sb (MATCHED span)", m.R, m.risk_pts,
                  "comparison fairness only — NOT the card's baseline"),
        summarise("ash-unicorn-sb (full log)", ash.R, ash.risk_pts, "the card's baseline"),
        summarise("zxck-cisd", cisd.R, cisd.risk_pts, ""),
        summarise("zxck-10am-keyopen", dec.R, 15.0,
                  "decidable sessions only; 73 ambiguous bounded separately"),
        summarise("zxck-ifvg-50", ifvg.R, ifvg.risk_pts, ""),
        summarise("zxck-wick-ce", wick.R, wick.risk_pts, ""),
    ]


def main() -> None:
    rows = [r for r in load()]
    d = pd.DataFrame(rows)
    rank = d[~d.card.str.contains("MATCHED")].sort_values("exp", ascending=False)

    print("RANKED COMPARISON — every baselined strategy, identical exit convention\n")
    print(f"costs ${RT_COST_USD:.0f}/round-turn, NQ ${NQ_POINT_USD:.0f}/pt  |  "
          f"deflation bar (N=293) {DEFLATION_BAR:+.4f}")
    print("random-walk null for a 2R target with break-even at 1R: 25.0 / 25.0 / 50.0\n")
    hdr = (f"{'card':<34}{'n':>5}{'win/BE/loss':>20}{'avgR':>9}{'cost':>7}"
           f"{'exp':>9}{'totR':>8}{'DD':>7}{'t':>8}{'effect':>9}{'eff_net':>9}")
    print(hdr); print("-" * len(hdr))
    for _, r in pd.concat([d[d.card.str.contains("MATCHED")], rank]).iterrows():
        mix = "%.1f/%.1f/%.1f" % (r["win%"], r["BE%"], r["loss%"])
        print(f"{r.card:<34}{r.n:>5}{mix:>20}"
              f"{r.avgR:>+9.3f}{r.cost:>7.3f}{r['exp']:>+9.3f}{r.totR:>+8.1f}"
              f"{r.maxDD:>7.1f}{r.t:>+8.3f}{r.effect:>+9.3f}{r.effect_net:>+9.3f}")
    print()
    best = rank.iloc[0]
    print(f"BEST BY EXPECTANCY: {best.card}  exp {best['exp']:+.3f}R")
    for lab, e in (("gross", best.effect), ("net of costs", best.effect_net)):
        print(f"  effect {e:+.3f} ({lab}) vs deflation bar {DEFLATION_BAR:+.4f} -> "
              f"{'CLEARS' if e >= DEFLATION_BAR else 'DOES NOT CLEAR'} "
              f"({100*e/DEFLATION_BAR:.0f}% of the bar)")

    out = ROOT / "research/_shared/baseline-comparison.csv"
    d.to_csv(out, index=False)
    print(f"\nwritten -> {out}")


if __name__ == "__main__":
    main()
