"""The trial ledger — the DSR denominator, on the record instead of in someone's head.

WHY THIS EXISTS. `deflated_sharpe_ratio` needs two things: how many trials were run, and
how much the trial statistics VARIED. Until now the desk had neither on disk. Trial counts
lived in prose at the bottom of each verdict, and the variance had to be eyeballed — when
the London programme was graded, the trial-Sharpe variance was estimated from six cells
recovered by hand out of markdown tables. That is the weakest link in the whole gate: the
number that decides whether anything is real was itself a guess.

This module makes every trial an appended row, and makes the deflation bar a function of
recorded history rather than of memory.

THE COMMON SCALE. Trials in this programme come in two shapes: mean-of-outcome tests
(a mean in points, with an n and a standard error) and rank-correlation tests (a Spearman
rho). Mixing a Sharpe with a rho would be meaningless, so every trial is stored with a
single standardised effect:

    effect = t / sqrt(n)

For a mean test that is the per-observation Sharpe ratio. For a correlation test it is
approximately rho itself. Both are per-observation standardised effects, so they live on
the same scale and their variance is the quantity DSR actually wants.

APPEND-ONLY BY DESIGN. `record()` never rewrites a row. A trial that was run happened, and
a ledger you can quietly shrink is not a ledger — it is the thing DSR exists to defend
against.
"""
from __future__ import annotations

import math
from pathlib import Path
from statistics import NormalDist

import pandas as pd

_PHI = NormalDist()
LEDGER = Path(__file__).resolve().parents[2] / "output" / "trial_ledger.parquet"

COLUMNS = [
    "programme",     # LONDON | NY | ... — scope tag, NOT a separate denominator
    "researcher",    # brake | angus — both arms must be visible (ANGUS 2026-08-05)
    "family",        # e.g. LDN-TRAP-01
    "cluster",       # correlated-arm group for effective-N (§2.4); defaults to family
    "trial",         # short name of the specific statistic
    "era",           # 2025 / 2026
    "prereg",        # doc that declared it, or the commit
    "stat_type",     # "mean" | "rho"
    "estimate",      # the reported estimate in its own units
    "n",
    "t_stat",
    "effect",        # t / sqrt(n) — the common scale
    "verdict",
]

# ---------------------------------------------------------------------------
# WHY THERE IS NO PER-PROGRAMME DENOMINATOR
#
# It is tempting to deflate London against London's arms and NY against NY's. That is
# wrong for the decision the desk actually makes. Whatever goes live is selected from
# the pool of everything tested, so the go-live bar must see the whole pool. Same for
# two researchers on one session: "two people searching the same session doubles the
# search size — the deflation math has to see both our arm counts or we'll fool
# ourselves" (ANGUS 2026-08-05).
#
# `programme` and `researcher` are therefore SCOPE TAGS for slicing and reporting, never
# filters applied before deflation. `deflation_bar()` uses the merged ledger by default
# and any narrowing has to be passed explicitly and justified on the verdict.
# ---------------------------------------------------------------------------


def effect_from_t(t: float, n: int) -> float:
    return float(t) / math.sqrt(n)


def t_from_one_sided_p(p1: float) -> float:
    """Recover t from a published one-sided p under the z-approximation the verdicts used."""
    p1 = min(max(float(p1), 1e-12), 1.0 - 1e-12)
    return _PHI.inv_cdf(1.0 - p1)


def load() -> pd.DataFrame:
    if not LEDGER.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_parquet(LEDGER)


def record(rows: list[dict]) -> pd.DataFrame:
    """Append trials. Never rewrites existing rows."""
    if not rows:
        return load()
    new = pd.DataFrame(rows)
    missing = [c for c in COLUMNS if c not in new.columns]
    if missing:
        raise ValueError(f"trial rows missing required columns: {missing}")
    out = pd.concat([load(), new[COLUMNS]], ignore_index=True)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(LEDGER, index=False)
    return out


def n_trials(df: pd.DataFrame | None = None) -> int:
    """NOMINAL arm count — everything tried, including abandoned arms (§2.4: they were
    lottery tickets too)."""
    return int(len(load() if df is None else df))


def n_effective(df: pd.DataFrame | None = None) -> int:
    """EFFECTIVE independent trials — number of correlated-arm clusters (§2.4).

    LIMITATION, STATED RATHER THAN HIDDEN. López de Prado's method clusters the trial
    RETURN SERIES (ONC) and uses the cluster count as effective N, with V computed over
    cluster representatives. This ledger stores summary statistics only, so it cannot
    cluster on series. `cluster` is therefore a DECLARED grouping — by default the
    family, on the reasoning that arms inside one prereg are draws from a single search
    over correlated configurations.

    That approximation is defensible but it is not the specified method, and it errs
    toward FEWER effective trials, i.e. a LOWER bar. Treat any candidate that clears on
    effective-N but not on nominal-N as unresolved until the series are recorded.
    """
    d = load() if df is None else df
    if d.empty:
        return 0
    return int(d["cluster"].fillna(d["family"]).nunique())


def trial_effect_variance(df: pd.DataFrame | None = None) -> float:
    """Variance of the standardised effect across recorded trials — the DSR denominator's
    other half. Raises rather than guessing when there is too little history."""
    d = load() if df is None else df
    e = pd.to_numeric(d["effect"], errors="coerce").dropna()
    if len(e) < 2:
        raise ValueError(
            f"trial ledger holds {len(e)} usable effects; variance needs at least 2. "
            "Record more trials before deflating — do not substitute a guess.")
    return float(e.var(ddof=1))


def deflation_bar(n: int | None = None, df: pd.DataFrame | None = None) -> float:
    """Expected best standardised effect from luck alone, given the recorded history."""
    from src.validation.dsr import expected_max_sharpe
    d = load() if df is None else df
    return expected_max_sharpe(n_trials(d) if n is None else n, trial_effect_variance(d))


def summary(df: pd.DataFrame | None = None) -> str:
    d = load() if df is None else df
    if d.empty:
        return "trial ledger is empty"
    var = trial_effect_variance(d)
    eff = n_effective(d)
    best = d.loc[d.effect.idxmax()]
    lines = [
        f"trials recorded (nominal): {len(d)}",
        f"effective trials (clusters): {eff}   <- approximation, see n_effective()",
        f"programmes             : {', '.join(sorted(d.programme.dropna().unique()))}",
        f"researchers            : {', '.join(sorted(d.researcher.dropna().unique()))}",
        f"effect sd across trials: {math.sqrt(var):.4f}  (var {var:.6f})",
        f"best effect observed   : {d.effect.max():+.4f}"
        f"  ({best['family']} {best['era']})",
        f"deflation bar @ nominal {len(d)}: {deflation_bar(df=d):+.4f}",
        f"deflation bar @ effective {eff}: {deflation_bar(n=eff, df=d):+.4f}"
        "   <- LOWER bar; do not use to promote until series-based clustering exists",
    ]
    return "\n".join(lines)
