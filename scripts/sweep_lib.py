#!/usr/bin/env python3
"""SHARED SURVIVAL TEST for the agent sweep.

Every agent imports THIS — the five declared tests
(docs/DECLARATIONS-agent-sweep.md) implemented once so results are
comparable across agents. Do not reimplement the statistics.

    from scripts.sweep_lib import load_wide, test_split, quintiles
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WIDE = ROOT / "output/htf_ma_census/race_wide.parquet"
SEED, DRAWS = 20260807, 2000
MECHANICAL = {"risk", "w15", "w15_pts", "risk_over_w", "tf_won",
              "closeloc", "rangex", "risk_over_atr30", "entry", "stop",
              "ma15"}
# columns that ARE outcomes or outcome-derived — never use as predictors
OUTCOME_COLS = {"out", "out_pts", "hit", "mfe_r", "near_hit", "near_out",
                "near_dist_r", "far_hit", "far_out", "far_dist_r",
                "m1_hit", "m1_out", "m1_dist_r"}
# NOTE 2026-08-08: `out_pts` (= out x risk) was missing from this set in
# the first sweep build — it is the outcome itself re-scaled, so it
# "survived" tautologically in every cell it was tested in. Caught by the
# NY_PRE sweep agent, not by me. Any survivor list containing `out_pts`
# is void for that row only; all other rows are unaffected.


def load_wide() -> pd.DataFrame:
    B = pd.read_parquet(WIDE)
    B["t"] = pd.to_datetime(B.t)
    B["out_pts"] = B["out"] * B["risk"]
    return B


def _dayboot_diff(g: pd.DataFrame, mask: pd.Series, col: str,
                  draws: int = DRAWS):
    """Day-clustered bootstrap CI on the DIFFERENCE of arm means.
    Same day draws for both arms (paired)."""
    a, b = g[mask], g[~mask]
    if len(a) < 10 or len(b) < 10:
        return np.nan, np.nan, np.nan
    if a.sess_day.nunique() < 3 or b.sess_day.nunique() < 3:
        return np.nan, np.nan, np.nan
    days = sorted(g.sess_day.unique())
    di = {d: i for i, d in enumerate(days)}
    n = len(days)

    def sums(x):
        s = np.zeros(n)
        c = np.zeros(n)
        agg = x.groupby("sess_day")[col].agg(["sum", "count"])
        for d, r in agg.iterrows():
            s[di[d]], c[di[d]] = r["sum"], r["count"]
        return s, c

    sa, ca = sums(a)
    sb, cb = sums(b)
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, n, (draws, n))
    csa, csb = ca[i].sum(1), cb[i].sum(1)
    ea = np.divide(sa[i].sum(1), csa, out=np.full(draws, np.nan),
                   where=csa > 0)
    eb = np.divide(sb[i].sum(1), csb, out=np.full(draws, np.nan),
                   where=csb > 0)
    dd = ea - eb
    return (float(a[col].mean() - b[col].mean()),
            float(np.nanpercentile(dd, 2.5)),
            float(np.nanpercentile(dd, 97.5)))


def test_split(g: pd.DataFrame, var: str, mask=None, label: str = "",
               col: str = "out") -> dict:
    """Run all five declared tests on one split of one cell.

    g    : the cell (already filtered to session x mech [x dir])
    var  : variable name (for the mechanical check and rho)
    mask : boolean Series aligned to g. Default = above-median split.
    Returns a dict with every test's result and `survives`.
    """
    g = g[g[var].notna()].copy() if var in g.columns else g.copy()
    if mask is None:
        if var not in g.columns or g[var].nunique() < 2:
            return {"var": var, "label": label, "n": len(g),
                    "survives": False, "why": "constant/missing"}
        if g[var].dtype == bool or set(g[var].dropna().unique()) <= {0, 1}:
            mask = g[var].astype(bool)
        else:
            mask = g[var] > g[var].median()
    else:
        mask = mask.reindex(g.index).fillna(False).astype(bool)

    out = {"var": var, "label": label or var, "n": len(g),
           "n_a": int(mask.sum()), "n_b": int((~mask).sum()),
           "survives": False, "why": ""}
    # T5 power
    if len(g) < 40 or out["n_a"] < 10 or out["n_b"] < 10:
        out["why"] = "power"
        return out
    if g[mask].sess_day.nunique() < 3 or g[~mask].sess_day.nunique() < 3:
        out["why"] = "power(days)"
        return out
    # T1 full-cell CI
    d_, lo_, hi_ = _dayboot_diff(g, mask, col)
    out.update(dev=d_, lo=lo_, hi=hi_,
               ev_a=float(g[mask][col].mean()),
               ev_b=float(g[~mask][col].mean()))
    if not np.isfinite(lo_):
        out["why"] = "thin(boot)"
        return out
    clears = (lo_ > 0) or (hi_ < 0)
    out["clears"] = bool(clears)
    if not clears:
        out["why"] = "CI spans zero"
        return out
    # T3 points control
    dp = (g[mask]["out_pts"].mean() - g[~mask]["out_pts"].mean())
    out["d_pts"] = float(dp)
    if np.sign(dp) != np.sign(d_):
        out["why"] = "points-control disagrees (R denominator)"
        return out
    # T4 mechanical
    rho = (g[var].astype(float).corr(g["risk"])
           if var in g.columns else np.nan)
    out["rho_risk"] = float(rho) if np.isfinite(rho) else np.nan
    if var in MECHANICAL or (np.isfinite(rho) and abs(rho) > 0.4):
        out["why"] = "LAW2 mechanical"
        return out
    # T2 both halves
    ha, hb = g[g.half == 0], g[g.half == 1]
    dh = []
    for h in (ha, hb):
        m = mask.reindex(h.index).fillna(False).astype(bool)
        if m.sum() < 5 or (~m).sum() < 5:
            dh.append(np.nan)
        else:
            dh.append(float(h[m][col].mean() - h[~m][col].mean()))
    out["d_half_a"], out["d_half_b"] = dh
    if not all(np.isfinite(x) for x in dh):
        out["why"] = "half too thin"
        return out
    same = np.sign(dh[0]) == np.sign(dh[1]) == np.sign(d_)
    mag = all(abs(x) >= abs(d_) / 3 for x in dh)
    if not same:
        out["why"] = "halves disagree in sign"
        return out
    if not mag:
        out["why"] = "a half is <1/3 the effect"
        return out
    out["survives"] = True
    out["why"] = "SURVIVES all five"
    return out


def quintiles(g: pd.DataFrame, var: str, col: str = "out") -> str:
    """Mean of `var` by realized-R quintile — monotonicity evidence."""
    g = g[g[var].notna()]
    if len(g) < 25:
        return "thin"
    q = pd.qcut(g[col].rank(method="first"), 5, labels=False) + 1
    m = g.groupby(q)[var].mean()
    return " ".join(f"Q{i}:{m.get(i, float('nan')):.2f}" for i in range(1, 6))


def cells(B: pd.DataFrame, session: str):
    """Yield (label, frame) for each mechanism cell in a session, plus
    the direction splits where they have power."""
    for mech in ("M1", "M2", "M3"):
        g = B[(B.session == session) & (B.mech == mech)]
        if len(g) >= 40:
            yield f"{session}/{mech}", g
        for dr in ("long", "short"):
            gd = g[g.dir == dr]
            if len(gd) >= 40:
                yield f"{session}/{mech}/{dr}", gd


def predictors(B: pd.DataFrame):
    """All usable predictor columns (numeric/bool, not outcomes)."""
    bad = OUTCOME_COLS | {"direction", "half", "sess_day", "scid"}
    return [c for c in B.columns
            if c not in bad and B[c].dtype.kind in "fbi"
            and B[c].notna().sum() >= 100 and B[c].nunique() > 1]
