"""Permutation null for conditional (state x gate) findings — §5.12-9.

The problem: testing a gate INSIDE states multiplies the search space, and a
"the gate works when in drawdown" cell can be pure noise. The canon dissection
mandates a permutation null before any such finding ships.

The test: hold the state labels fixed; shuffle the GATE labels within each
state cell N times; the observed lift (mean outcome gated-on minus gated-off,
within-state) is compared to the shuffled distribution. p = fraction of
shuffles with lift >= observed. Shuffling within state preserves the state's
base rate, so only the gate's alignment is on trial.

    from src.validation.permnull import perm_pvalue
    p = perm_pvalue(outcomes, gate_on, states, n=10_000, seed=7)
"""
from __future__ import annotations

import numpy as np


def perm_pvalue(outcomes, gate_on, states, n: int = 10_000, seed: int = 7) -> dict:
    y = np.asarray(outcomes, dtype=float)
    g = np.asarray(gate_on, dtype=bool)
    s = np.asarray(states)
    if not (len(y) == len(g) == len(s)):
        raise ValueError("outcomes, gate_on, states must be same length")
    if g.all() or (~g).any() is False or g.sum() == 0:
        raise ValueError("gate must have both on and off rows")

    def lift(gv):
        tot, w = 0.0, 0
        for st in np.unique(s):
            m = s == st
            on, off = gv[m], ~gv[m] & m[m]
            a, b = y[m][gv[m]], y[m][~gv[m]]
            if len(a) < 3 or len(b) < 3:
                continue
            tot += (a.mean() - b.mean()) * m.sum()
            w += m.sum()
        return tot / w if w else np.nan

    obs = lift(g)
    rng = np.random.default_rng(seed)
    null = np.empty(n)
    for i in range(n):
        gp = g.copy()
        for st in np.unique(s):
            m = np.where(s == st)[0]
            gp[m] = rng.permutation(gp[m])
        null[i] = lift(gp)
    null = null[~np.isnan(null)]
    p = float((null >= obs).mean()) if obs == obs else 1.0
    return dict(observed_lift=float(obs), p_value=p, n_shuffles=int(len(null)),
                null_p95=float(np.percentile(null, 95)))
