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

STORAGE IS `scripts/ledger_io`, NOT PARQUET. This module wrote
`output/trial_ledger.parquet` directly until 2026-08-06, which had stopped being the
canonical store: the ledger had already forked into four divergent copies precisely
because parquet is a binary blob git cannot merge, and the fix was sorted JSONL with
`merge=union`. A second writer pointed at the derived artifact meant a script could
"record 1 trial" and leave the canonical file untouched — which is exactly what happened
when the corrected OBK/PO3 flow pass was re-run, and it took a row-count comparison to
notice. Every read and write here now goes through `scripts.ledger_io`; the parquet is a
build artifact regenerated from the JSONL and nothing writes it directly.
`tests/test_ledger_integrity.py` fails if anything does.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from statistics import NormalDist

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ledger_io  # noqa: E402

_PHI = NormalDist()
#: The canonical store. Kept as a name because callers and docs refer to it, but it is
#: now the JSONL, not the parquet.
LEDGER = ledger_io.LEDGER

#: The subset every caller must supply. `ledger_io.COLUMNS` is the full schema and
#: carries the provenance fields (`status`, `superseded_by`) that recording does not set.
COLUMNS = [
    "family",        # e.g. LDN-TRAP-01
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


def effect_from_t(t: float, n: int) -> float:
    return float(t) / math.sqrt(n)


def t_from_one_sided_p(p1: float) -> float:
    """Recover t from a published one-sided p under the z-approximation the verdicts used."""
    p1 = min(max(float(p1), 1e-12), 1.0 - 1e-12)
    return _PHI.inv_cdf(1.0 - p1)


def load() -> pd.DataFrame:
    return ledger_io.read()


def record(rows: list[dict]) -> pd.DataFrame:
    """Append trials to the canonical JSONL. Never rewrites an existing row's numbers.

    A key that already exists is left ALONE rather than overwritten. `ledger_io.append`
    overwrites on collision -- correct for a re-run of the same declared arm -- but this
    module's contract is append-only, and the two differ exactly when a re-run produces
    different numbers from the same key. That case is a supersession, not an update, and
    it is handled by appending under a distinguished trial key with `superseded_by` set
    on the original (ANGUS ruling 2026-08-06). Silently taking the new numbers would
    erase the fact that both passes ran.
    """
    if not rows:
        return load()
    new = pd.DataFrame(rows)
    missing = [c for c in COLUMNS if c not in new.columns]
    if missing:
        raise ValueError(f"trial rows missing required columns: {missing}")
    cur = load()
    seen = set(zip(cur.family, cur.trial, cur.era))
    fresh = [r for r in new[COLUMNS].to_dict("records")
             if (r["family"], r["trial"], r["era"]) not in seen]
    if not fresh:
        return cur
    ledger_io.write(pd.concat([cur, pd.DataFrame(fresh)], ignore_index=True))
    return load()


def n_trials(df: pd.DataFrame | None = None) -> int:
    return int(len(load() if df is None else df))


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
    lines = [
        f"trials recorded        : {len(d)}",
        f"families               : {d.family.nunique()}",
        f"effect sd across trials: {math.sqrt(var):.4f}  (var {var:.6f})",
        f"best effect observed   : {d.effect.max():+.4f}"
        f"  ({d.loc[d.effect.idxmax(), 'family']} {d.loc[d.effect.idxmax(), 'era']})",
        f"deflation bar @ {len(d)} trials: {deflation_bar(df=d):+.4f}",
    ]
    return "\n".join(lines)
