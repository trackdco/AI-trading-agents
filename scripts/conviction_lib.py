#!/usr/bin/env python3
"""CONVICTION / STACKED-CONFIRMATION library — flow + depth at entry.

THE OBJECT UNDER TEST is not "does feature X split the book" (that is
settled: BR-94, chance-level at both evaluation timestamps). It is the
STACKED construct: at the moment the trigger candle closes and we market
in, how many independent flow/depth signals agree with the trade — and
does win rate / EV climb with that count?

ENTRY TIMING IS CAUSAL HERE: features are evaluated at the closure
minute the market order is sent on. The old canon's depth hindsight came
from limit fills timestamped inside later bars; that defect cannot arise
in this construction.

ORIENTATION DEFECT, FOUND 2026-08-08 AND FIXED HERE:
  `delta_z`       = (bar_delta - mu)/sd  -- RAW SIGNED in flow_features,
                    never multiplied by direction (longs mean +1.22,
                    shorts mean -1.17). The original CONCORD (BR-19)
                    scored `delta_z > 0` as agreement, i.e. it counted
                    BUYING pressure as confirmation for SHORT trades.
  `dep_imbalance` = (bid-ask)/total -- same defect, milder.
Both are oriented by `direction` below. Every prior CONCORD refutation
(BR-19/26/62) carried the unoriented version for these components.
`RAW_SIGNALS` reproduces the old (defective) orientation so the two can
be compared directly.

LAW-2: `closeloc` and `rangex` are risk-coupled (BR-43, risk ~= closeloc
x range). They are included but FLAGGED, and every count is also
provided in a `_clean` form with both dropped.

    from scripts.conviction_lib import load, signals, add_counts, \
        monotone_table, permute, calibrate
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WIDE = ROOT / "output/htf_ma_census/race_wide.parquet"
SEED, DRAWS = 20260807, 2000

# name -> (expression, family, law2)
# expression takes the frame and returns a boolean Series = "agrees"
FLOW_SIGNALS = {
    "s_flowconf":   (lambda B: B.flowconf >= 1, "flow", False),
    "s_thru_delta": (lambda B: B.thru_delta_conf >= 1, "flow", False),
    "s_d5":         (lambda B: B.d5_conf >= 1, "flow", False),
    "s_d15":        (lambda B: B.d15_conf >= 1, "flow", False),
    "s_d30":        (lambda B: B.d30_conf >= 1, "flow", False),
    "s_no_opp":     (lambda B: B.bp5opp <= 0, "flow", False),
    "s_cvd":        (lambda B: B.cvd_slope30 > 0, "flow", False),
    # FIXED: oriented by trade direction (was raw-signed in CONCORD)
    "s_deltaz":     (lambda B: B.delta_z * B.direction > 0, "flow", False),
    "s_volx":       (lambda B: B.volx >= B.volx.median(), "flow", False),
    "s_eff":        (lambda B: B.eff_result >= B.eff_result.median(),
                     "flow", False),
    "s_closeloc":   (lambda B: B.closeloc >= 0.5, "flow", True),
    "s_rangex":     (lambda B: B.rangex >= B.rangex.median(), "flow", True),
}
DEPTH_SIGNALS = {
    # FIXED: oriented by trade direction (was raw-signed)
    "s_dep_imb":    (lambda B: B.dep_imbalance * B.direction > 0,
                     "depth", False),
    "s_sup_res":    (lambda B: B.support_minus_resist > 0, "depth", False),
    "s_wall_sz":    (lambda B: B.support_wall_size
                     >= B.support_wall_size.median(), "depth", False),
    "s_wall_near":  (lambda B: B.support_wall_dist
                     <= B.support_wall_dist.median(), "depth", False),
    "s_thick":      (lambda B: B.dep_thickness_vs_day
                     >= B.dep_thickness_vs_day.median(), "depth", False),
    "s_thick_up":   (lambda B: B.dep_thickness_delta_5m > 0,
                     "depth", False),
}
ALL_SIGNALS = {**FLOW_SIGNALS, **DEPTH_SIGNALS}
# the OLD (defective) orientation, for direct comparison
RAW_SIGNALS = {
    "s_deltaz_raw": (lambda B: B.delta_z > 0, "flow", False),
    "s_dep_imb_raw": (lambda B: B.dep_imbalance > 0, "depth", False),
}
LAW2 = {k for k, v in ALL_SIGNALS.items() if v[2]}


def load() -> pd.DataFrame:
    B = pd.read_parquet(WIDE)
    B["t"] = pd.to_datetime(B.t)
    B["win"] = (B["out"] > 0).astype(float)
    return B


def signals(B: pd.DataFrame, include_raw: bool = True) -> pd.DataFrame:
    """Add s_* boolean columns + *_avail masks. Medians are taken WITHIN
    the frame passed in — pass a session/mech cell to make them local, or
    the whole book for global cuts. State which you used."""
    B = B.copy()
    src = {**ALL_SIGNALS, **(RAW_SIGNALS if include_raw else {})}
    for name, (fn, fam, _l2) in src.items():
        base = {"s_flowconf": "flowconf", "s_thru_delta": "thru_delta_conf",
                "s_d5": "d5_conf", "s_d15": "d15_conf", "s_d30": "d30_conf",
                "s_no_opp": "bp5opp", "s_cvd": "cvd_slope30",
                "s_deltaz": "delta_z", "s_deltaz_raw": "delta_z",
                "s_volx": "volx", "s_eff": "eff_result",
                "s_closeloc": "closeloc", "s_rangex": "rangex",
                "s_dep_imb": "dep_imbalance",
                "s_dep_imb_raw": "dep_imbalance",
                "s_sup_res": "support_minus_resist",
                "s_wall_sz": "support_wall_size",
                "s_wall_near": "support_wall_dist",
                "s_thick": "dep_thickness_vs_day",
                "s_thick_up": "dep_thickness_delta_5m"}[name]
        avail = B[base].notna()
        B[name] = fn(B).where(avail).astype("float")
        B[name + "_avail"] = avail.astype(float)
    return B


def add_counts(B: pd.DataFrame) -> pd.DataFrame:
    """Conviction counts. `_n` = how many of that family were available;
    `_frac` = agreements / available (the coverage-fair version, since
    depth exists on ~80% of fights and wall features on ~40%)."""
    B = B.copy()
    groups = {
        "flow": [k for k, v in FLOW_SIGNALS.items()],
        "flow_clean": [k for k, v in FLOW_SIGNALS.items() if not v[2]],
        "depth": list(DEPTH_SIGNALS),
        "all": list(ALL_SIGNALS),
        "all_clean": [k for k, v in ALL_SIGNALS.items() if not v[2]],
    }
    for g, cols in groups.items():
        cols = [c for c in cols if c in B.columns]
        B[f"cc_{g}"] = B[cols].sum(axis=1, min_count=1)
        B[f"cc_{g}_n"] = B[[c + "_avail" for c in cols]].sum(axis=1)
        B[f"cc_{g}_frac"] = B[f"cc_{g}"] / B[f"cc_{g}_n"].replace(0, np.nan)
    # the OLD defective flow count, for the comparison
    old = [k for k in FLOW_SIGNALS if k != "s_deltaz"] + ["s_deltaz_raw"]
    old = [c for c in old if c in B.columns]
    B["cc_flow_olddefect"] = B[old].sum(axis=1, min_count=1)
    return B


def dboot_mean(df: pd.DataFrame, col: str, draws: int = DRAWS):
    g = df.groupby("sess_day")[col].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    if len(s) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(s), (draws, len(s)))
    c = n[i].sum(1)
    st = np.divide(s[i].sum(1), c, out=np.full(draws, np.nan), where=c > 0)
    return (float(np.nanpercentile(st, 2.5)),
            float(np.nanpercentile(st, 97.5)))


def monotone_table(g: pd.DataFrame, count_col: str, min_n: int = 15):
    """Win rate AND EV by conviction level (dual currency, Law 3).
    Returns a DataFrame; levels with < min_n fights are kept but marked."""
    rows = []
    for lvl, gl in g[g[count_col].notna()].groupby(count_col):
        lo, hi = dboot_mean(gl, "out") if len(gl) >= min_n else (np.nan,
                                                                np.nan)
        rows.append({"level": lvl, "n": len(gl),
                     "days": gl.sess_day.nunique(),
                     "win_pct": 100 * gl["win"].mean(),
                     "ev": gl["out"].mean(), "lo": lo, "hi": hi,
                     "thin": len(gl) < min_n})
    return pd.DataFrame(rows).sort_values("level")


def spearman_trend(tab: pd.DataFrame, col: str = "ev") -> float:
    """Rank correlation of the count level vs the metric, n-weighted by
    inclusion only (thin levels dropped). The monotonicity question."""
    t = tab[~tab.thin]
    if len(t) < 3:
        return np.nan
    return float(pd.Series(t.level).corr(pd.Series(t[col]),
                                         method="spearman"))


def permute(B: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Null: shuffle the OUTCOME within each (session, mech) cell,
    preserving every signal, count, cell size and outcome distribution.
    THIS IS MANDATORY for any claim in this family — the last pass showed
    the survival machinery passes ~5% of pure noise (BR-97)."""
    rng = np.random.default_rng(seed)
    Bn = B.copy()
    for (s, m), idx in Bn.groupby(["session", "mech"]).groups.items():
        idx = np.asarray(idx)
        if len(idx) < 2:
            continue
        perm = rng.permutation(idx)
        for c in ("out", "win"):
            Bn.loc[idx, c] = Bn.loc[perm, c].to_numpy()
    return Bn


def calibrate(fn, B: pd.DataFrame, n_perm: int = 5, base: int = 90000):
    """Run `fn(frame) -> number` on the real frame and on n_perm
    permutations. Returns (real, null_array). Report both, always."""
    real = fn(B)
    null = np.array([fn(permute(B, base + i)) for i in range(n_perm)],
                    dtype=float)
    return real, null
