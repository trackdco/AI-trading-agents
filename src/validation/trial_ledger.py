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
    "series_path",   # per-day outcome vector for this arm — unlocks ONC / CSCV / SPA
    "verdict",
]

SERIES_DIR = LEDGER.parent / "trials"


def series_file(family: str, arm: str) -> Path:
    """One series per (family, arm) over the WHOLE fit span.

    Deliberately not per era: the era split is a validation device, not a separate
    strategy. For CSCV the N is the number of distinct configurations tried, and both
    era rows of an arm point at the same series.
    """
    slug = f"{family}_{arm}".replace("/", "-").replace(":", "-").replace(" ", "")
    return SERIES_DIR / f"{slug}.parquet"


def write_series(family: str, arm: str, day_ret: "pd.Series") -> Path:
    """Persist an arm's per-day outcome vector. Days the arm did not fire are 0 —
    a strategy that does not trade earns nothing that day, which is what CSCV needs."""
    p = series_file(family, arm)
    p.parent.mkdir(parents=True, exist_ok=True)
    s = pd.Series(day_ret).astype(float).sort_index()
    s.index.name = "day"
    s.rename("ret").to_frame().to_parquet(p)
    return p


def load_matrix() -> "pd.DataFrame":
    """T x N matrix of every recorded arm's day series, aligned on the union of days.

    This is the artifact PBO/CSCV, ONC clustering and SPA all need and none of which
    could run before it existed.
    """
    d = load()
    paths = sorted({p for p in d.series_path.dropna().unique() if p})
    cols = {}
    for p in paths:
        fp = Path(p)
        if not fp.exists():
            continue
        cols[fp.stem] = pd.read_parquet(fp)["ret"]
    if not cols:
        raise FileNotFoundError(
            "no trial series on disk — run scripts/backfill_trial_series.py")
    return pd.DataFrame(cols).fillna(0.0).sort_index()

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


# Columns added after the ledger was already in use by both researchers. They are
# BACKFILLED, never required — a caller written against the original 10-column schema
# must keep working, or the merged ledger §6.0 depends on silently stops being merged.
_OPTIONAL = {
    "programme": "UNSPECIFIED",
    "researcher": "UNSPECIFIED",
    "cluster": None,          # falls back to `family`
    "series_path": None,
}
_REQUIRED = [c for c in COLUMNS if c not in _OPTIONAL]


def _conform(d: pd.DataFrame) -> pd.DataFrame:
    """Bring any ledger vintage up to the current schema without losing rows."""
    d = d.copy()
    for c, default in _OPTIONAL.items():
        if c not in d.columns:
            d[c] = default
    if "cluster" in d.columns and "family" in d.columns:
        d["cluster"] = d["cluster"].fillna(d["family"])
    for c in COLUMNS:
        if c not in d.columns:
            d[c] = None
    return d[COLUMNS]


def load() -> pd.DataFrame:
    if not LEDGER.exists():
        return pd.DataFrame(columns=COLUMNS)
    return _conform(pd.read_parquet(LEDGER))


def record(rows: list[dict]) -> pd.DataFrame:
    """Append trials. Never rewrites existing rows.

    Only the original 10 columns are required. `programme`, `researcher`, `cluster` and
    `series_path` are optional and default — supply them where you can, because §6.0's
    merged denominator is more useful when scope is tagged, but a caller that omits them
    still records a valid trial rather than raising.
    """
    if not rows:
        return load()
    new = pd.DataFrame(rows)
    missing = [c for c in _REQUIRED if c not in new.columns]
    if missing:
        raise ValueError(f"trial rows missing required columns: {missing}")
    out = pd.concat([load(), _conform(new)], ignore_index=True)
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
    try:
        return effective_trials_from_series()
    except (FileNotFoundError, ValueError):
        return int(d["cluster"].fillna(d["family"]).nunique())


def effective_trials_from_series(threshold: float = 0.5) -> int:
    """Effective independent trials by clustering the arms' RETURN SERIES (§2.4).

    ONC-lite: correlate every pair of arm day-series, join arms whose |rho| >= threshold
    into the same cluster (connected components), and count clusters. This is the
    specified *kind* of correction — cluster on realised co-movement, not on which
    prereg an arm happened to be declared in — though it is a simpler linkage than
    López de Prado's ONC.

    Correlated configurations are not independent draws, so effective N < nominal N and
    the bar drops. That makes this correction dangerous if applied loosely: report it
    alongside the nominal bar, never instead of it.
    """
    m = load_matrix()
    if m.shape[1] < 2:
        raise ValueError("need at least 2 arm series to cluster")
    c = m.corr().abs().fillna(0.0).to_numpy()
    n = c.shape[0]
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if c[i, j] >= threshold:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    return len({find(i) for i in range(n)})


V_N_FLOOR = 30          # matches the desk's own n>=30 event floor


def trial_effect_variance(df: pd.DataFrame | None = None,
                          n_floor: int = V_N_FLOOR) -> float:
    """Variance of the standardised effect across recorded trials — DSR's other input.

    N-FLOOR ON THE VARIANCE ONLY. `effect = t/sqrt(n)` is a per-observation standardised
    effect, and its ESTIMATE is noisy at small n — noise that scales as 1/sqrt(n) and
    lands directly in V. Measured on the merged ledger 2026-08-05:

        n   3-10   :  3 trials, mean |effect| 0.626, max 1.704
        n  10-30   :  5 trials, mean |effect| 0.229
        n  30-100  : 22 trials, mean |effect| 0.189
        n 100+     : 14 trials, mean |effect| 0.088

    The monotone decline is estimation noise, not signal. Including the three n<10 arms
    inflated the bar from +0.5519 to +0.8026 at N=52 — a 45% rise driven by 3 of 44
    trials, one of them n=3.

    An inflated V is not "safely conservative": per §2.4 both under- and over-correction
    are errors, and a bar set by an artifact rejects real edges. So trials below the
    floor are still COUNTED in N (they were lottery tickets) but excluded from V.

    Set n_floor=0 to reproduce the unfiltered figure.
    """
    d = load() if df is None else df
    e = pd.to_numeric(d["effect"], errors="coerce")
    n = pd.to_numeric(d["n"], errors="coerce")
    keep = e.notna() & (n.fillna(0) >= n_floor)
    e = e[keep]
    if len(e) < 2:
        raise ValueError(
            f"trial ledger holds {len(e)} usable effects at n>={n_floor}; variance needs "
            "at least 2. Record more trials before deflating — do not substitute a guess.")
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
        f"  by programme: {d.programme.value_counts().to_dict()}",
        f"  by researcher: {d.researcher.value_counts().to_dict()}",
        f"effective trials (clusters): {eff}   <- approximation, see n_effective()",
        f"programmes             : {', '.join(sorted(d.programme.dropna().unique()))}",
        f"researchers            : {', '.join(sorted(d.researcher.dropna().unique()))}",
        f"effect sd across trials: {math.sqrt(var):.4f}  (var {var:.6f})"
        f"   [V over n>={V_N_FLOOR} only; all {len(d)} counted in N]",
        f"best effect observed   : {d.effect.max():+.4f}"
        f"  ({best['family']} {best['era']})",
        f"deflation bar @ nominal {len(d)}: {deflation_bar(df=d):+.4f}",
        f"deflation bar @ effective {eff}: {deflation_bar(n=eff, df=d):+.4f}"
        "   <- LOWER bar; do not use to promote until series-based clustering exists",
    ]
    return "\n".join(lines)
