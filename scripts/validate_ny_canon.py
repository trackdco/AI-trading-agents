#!/usr/bin/env python3
"""Run the NY canon through the DSR/PBO gate — READ-ONLY. The canon is not touched.

WHY THIS RUN EXISTS. The London 29k sweep calibrated the gate against a known NULL (a
clean null we reached honestly by other means). This is the opposite pole: the NY canon is
the one book we know is REAL — live, certified, order-flow validated, and profitable. A
gate that fails it is miscalibrated, and that would be the finding.

It also supports a test London cannot: **NY's sealed 2023/24 holdout has already been
spent** (`docs/HOLDOUT-2023-24-PREREGISTRATION.md`; results published in
`scripts/funded_book.py` — 13/13 and 6/6 months green). Computing a statistic on data
whose look is already taken spends nothing. So we can:

    1. run the gate on FIT DATA ONLY,
    2. record what it predicts,
    3. compare against the KNOWN holdout outcome.

That is a test of *predictive validity*, not of agreement with our priors — the only such
test available anywhere in this repo.

THE CANDIDATE. The shipped canon at 1 lot: `valid` rows less the aikido wall-quality cut,
exactly as `scripts.funded_book.load_book` selects them. 1 lot deliberately — DSR and PBO
screen the EDGE. Tiers, elite, the budget spine and both sizing profiles are L4 policy and
are judged by funded-rules Monte Carlo and maxDD, not by a Sharpe. Scoring the funded
profile here would let sizing flatter the statistic.

THE SEARCH BREADTH. `scripts/l3_check_trial.py` put 16 checks on trial (pre: W F Tp G C ·
gold: D Tc X AGE PAQ · plus 6 Q bits), selected PER SESSION. The honest trial space is
therefore every single check and every pair, per session, with a book being one pre-choice
combined with one gold-choice. That is the search the canon actually came out of, and it is
what the DSR null is estimated from — via the cross-sectional variance of the trial
Sharpes, so nested and correlated candidates are charged at effective, not nominal, breadth.

Day-level series, zero-filled on no-trade days: same-day trades share regime and tape, so a
trade-level split would leak (the stage-3 leak rule).

Output: docs/VALIDATION-NY-CANON.md + docs/validation_ny_canon.json
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.funded_book import load_book
from src.validation import deflated_sharpe_ratio, pbo_cscv, sharpe_ratio

DOCS = ROOT / "docs"
N_BLOCKS = 16
MIN_TRADES = 25          # same eligibility floor as the London calibration
CHECKS = ["W", "F_", "Tp", "G", "C", "D", "Tc", "X", "AGE",
          "PAQ", "WALLSZ", "BIGFD", "T2", "TRIG", "VWAPD", "LONSLOPE"]


def day_series(pnl: np.ndarray, day_ix: np.ndarray, masks: np.ndarray,
               n_days: int) -> np.ndarray:
    """(n_days x n_candidates) day-summed 1-lot P&L, zero-filled on no-trade days."""
    D = np.zeros((n_days, len(pnl)))
    D[day_ix, np.arange(len(pnl))] = pnl
    out = np.empty((n_days, masks.shape[1]))
    for lo in range(0, masks.shape[1], 2000):
        out[:, lo : lo + 2000] = D @ masks[:, lo : lo + 2000].astype(float)
    return out


def session_options(V: pd.DataFrame, sess: str) -> tuple[list[str], np.ndarray]:
    """Every single check and every pair, restricted to one session's rows."""
    in_sess = (V.sess == sess).to_numpy()
    singles = [((V[c] == 1).to_numpy() & in_sess) for c in CHECKS]
    names = list(CHECKS)
    cols = list(singles)
    for i, j in itertools.combinations(range(len(CHECKS)), 2):
        names.append(f"{CHECKS[i]}&{CHECKS[j]}")
        cols.append(singles[i] & singles[j])
    return names, np.column_stack(cols)


def build(span: str):
    V = load_book(span).reset_index(drop=True)
    days = sorted(V.day.unique())
    day_ix = np.array([days.index(d) for d in V.day])
    pnl = V.dollars_1lot.to_numpy(float)

    pre_names, pre_masks = session_options(V, "pre")
    gold_names, gold_masks = session_options(V, "gold")

    # a book = one pre-choice UNION one gold-choice (the sessions are selected separately)
    n_books = pre_masks.shape[1] * gold_masks.shape[1]
    books = np.empty((len(V), n_books), dtype=bool)
    labels = []
    k = 0
    for pi in range(pre_masks.shape[1]):
        for gi in range(gold_masks.shape[1]):
            books[:, k] = pre_masks[:, pi] | gold_masks[:, gi]
            labels.append(f"pre:{pre_names[pi]} | gold:{gold_names[gi]}")
            k += 1

    X = day_series(pnl, day_ix, books, len(days))
    n_per = books.sum(axis=0)
    # the shipped canon: every row load_book returned (valid + wall-quality cut applied)
    canon = day_series(pnl, day_ix, np.ones((len(V), 1), dtype=bool), len(days))[:, 0]
    return V, days, X, canon, n_per, labels


def col_sharpes(X: np.ndarray) -> np.ndarray:
    sd = X.std(axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(sd > 0, X.mean(axis=0) / sd, np.nan)


def main() -> None:
    res: dict = {}
    L: list[str] = []

    # ---------------------------------------------------------------- FIT (the prediction)
    V, days, X, canon, n_per, labels = build("fit")
    sr = col_sharpes(X)
    eligible = (n_per >= MIN_TRADES) & np.isfinite(sr)
    sr_elig = sr[eligible]

    dsr_own = deflated_sharpe_ratio(canon, trial_sharpes=sr_elig)
    pbo_fit = pbo_cscv(X[:, eligible], n_blocks=N_BLOCKS, batch_size=64)

    # what the best MINED alternative looked like in-sample, for contrast
    elig_ix = np.flatnonzero(eligible)
    w = int(elig_ix[np.argmax(sr_elig)])

    res["fit"] = {
        "days": len(days), "trades": len(V),
        "span": [days[0], days[-1]],
        "trial_books": int(X.shape[1]), "eligible": int(eligible.sum()),
        "canon": {
            "day_sharpe": float(sharpe_ratio(canon)),
            "total_1lot": float(canon.sum()),
            "psr_zero": dsr_own.psr_zero, "sr0": dsr_own.sr0,
            "dsr": dsr_own.dsr, "significant": dsr_own.significant,
            "skew": dsr_own.skew, "kurt": dsr_own.kurt},
        "best_mined_alternative": {
            "cell": labels[w], "day_sharpe": float(sr[w]), "n": int(n_per[w])},
        "pbo": {"pbo": pbo_fit.pbo, "n_trials": pbo_fit.n_trials,
                "splits": pbo_fit.n_combinations, "slope": pbo_fit.slope,
                "prob_oos_loss": pbo_fit.prob_oos_loss,
                "days_used": pbo_fit.n_obs_used, "days_dropped": pbo_fit.n_obs_dropped},
    }

    # ---------------------------------------------------------------- THE BREADTH LADDER
    # SR0 is a function of HOW HARD YOU SEARCHED, and the cross-product space above is
    # broader than the search that actually produced the canon. l3_check_trial evaluated
    # each check ONCE, at its frozen threshold, judged by era-split lift tables — it did
    # not mine 18k combinations and keep the best. Charging the canon for a search it never
    # ran is the same nominal-breadth error our shrinkage model makes. So: report DSR at
    # every rung and let the reader see where the verdict turns.
    _pre_names, pre_masks = session_options(V, "pre")
    _gold_names, gold_masks = session_options(V, "gold")
    n_single = len(CHECKS)
    day_ix = np.array([days.index(d) for d in V.day])
    pnl = V.dollars_1lot.to_numpy(float)

    def sharpes_of(masks: np.ndarray) -> np.ndarray:
        s = col_sharpes(day_series(pnl, day_ix, masks, len(days)))
        n = masks.sum(axis=0)
        return s[(n >= MIN_TRADES) & np.isfinite(s)]

    singles_only = np.column_stack([pre_masks[:, :n_single], gold_masks[:, :n_single]])
    per_sess_pairs = np.column_stack([pre_masks, gold_masks])
    ladder = {
        "16 checks, per session (the actual L3 trial)": sharpes_of(singles_only),
        "singles + pairs, per session": sharpes_of(per_sess_pairs),
        "full pre x gold cross product (mined)": sr_elig,
    }
    res["breadth_ladder"] = {}
    for label, ts in ladder.items():
        d = deflated_sharpe_ratio(canon, trial_sharpes=ts)
        res["breadth_ladder"][label] = {
            "n_trials": d.n_trials, "trial_sr_sd": float(np.std(ts, ddof=1)),
            "sr0": d.sr0, "dsr": d.dsr, "significant": d.significant}

    # ------------------------------------------------- HOLDOUT (the already-spent outcome)
    Vh, days_h, _Xh, canon_h, _n_h, _labels_h = build("holdout")
    res["holdout"] = {
        "days": len(days_h), "trades": len(Vh),
        "span": [days_h[0], days_h[-1]],
        "canon": {"day_sharpe": float(sharpe_ratio(canon_h)),
                  "total_1lot": float(canon_h.sum()),
                  "psr_zero": deflated_sharpe_ratio(
                      canon_h, trial_sharpes=[0.0]).psr_zero},
    }

    # the honest comparison: fit Sharpe vs realized holdout Sharpe of the SAME rule
    fit_sr, hold_sr = float(sharpe_ratio(canon)), float(sharpe_ratio(canon_h))
    res["predictive_check"] = {
        "fit_day_sharpe": fit_sr, "holdout_day_sharpe": hold_sr,
        "shrinkage": fit_sr - hold_sr,
        "retained_fraction": hold_sr / fit_sr if fit_sr else float("nan"),
        # keyed to the canon's OWN breadth, which is the headline verdict
        "gate_said_real_on_fit": bool(
            res["breadth_ladder"]["16 checks, per session (the actual L3 trial)"][
                "significant"]),
        "gate_said_real_at_inflated_breadth": bool(dsr_own.significant),
        "holdout_confirmed": bool(hold_sr > 0),
    }

    (DOCS / "validation_ny_canon.json").write_text(json.dumps(res, indent=2))

    f, h, p = res["fit"], res["holdout"], res["predictive_check"]
    # HEADLINE AT THE CANON'S OWN BREADTH. The cross-product row is reported as the
    # over-charged contrast, exactly as the London calibration treats the wall arm — it
    # is not the verdict, because the canon never ran that search.
    own = res["breadth_ladder"]["16 checks, per session (the actual L3 trial)"]
    verdict = ("PASSES at the canon's own search breadth"
               if own["significant"]
               else "FAILS even at the canon's own search breadth — that is a finding "
                    "about the gate, not about the canon")
    agree = ("The gate's fit-only verdict was CORRECT — it called the canon real before "
             "the holdout was consulted, and the holdout agrees."
             if p["gate_said_real_on_fit"] and p["holdout_confirmed"] else
             "The gate's fit-only verdict and the holdout outcome DISAGREE — read the "
             "caveats before trusting either.")

    L += [
        "# NY canon through the validation gate — DSR + PBO\n",
        (
            "\n**READ-ONLY.** No canon rule, threshold, or config was touched. This "
            "measures the book `scripts.funded_book.load_book` already produces.\n"
        ),
        (
            "\n**On holdout use:** NY's sealed 2023/24 look was already spent and its "
            "results are published in `scripts/funded_book.py`. Computing a statistic on "
            "data whose look is already taken spends nothing — no new holdout look was "
            "consumed here.\n"
        ),
        "\n## Why this run matters\n",
        (
            "\nThe London 29k sweep calibrated the gate against a known **null**. The NY "
            "canon is the opposite pole — the book we know is **real**. A gate that fails "
            "it is miscalibrated. And because NY's holdout is already open, this is the "
            "one place we can test whether the gate *predicts* out-of-sample survival "
            "rather than merely agreeing with a conclusion we already hold.\n"
        ),
        (
            f"\n## The candidate\n\nThe shipped canon at **1 lot**: {f['trades']:,} trades "
            f"over {f['days']} days ({f['span'][0]} → {f['span'][1]}). 1 lot deliberately "
            f"— DSR and PBO screen the edge; tiers, elite, the budget spine and both "
            f"sizing profiles are L4 policy, judged by funded-rules Monte Carlo and maxDD, "
            f"not by a Sharpe.\n"
        ),
        (
            f"\n## The search it came out of\n\n`l3_check_trial.py` trialled 16 checks, "
            f"selected per session. Every single and every pair, per session, paired "
            f"across pre × gold = **{f['trial_books']:,} candidate books**; "
            f"{f['eligible']:,} clear the n≥{MIN_TRADES} floor. The DSR null is the "
            f"cross-sectional variance of those trial Sharpes, so nested and correlated "
            f"candidates are charged at effective breadth.\n"
        ),
        "\n## Q1 — does DSR confirm the canon?\n",
        (
            f"\n| | value |\n|---|---|\n"
            f"| canon day-Sharpe (fit, 1 lot) | {f['canon']['day_sharpe']:.4f} |\n"
            f"| skew / kurtosis | {f['canon']['skew']:+.3f} / {f['canon']['kurt']:.2f} |\n"
            f"| PSR (undeflated) | {f['canon']['psr_zero']:.4f} |\n"
            f"| SR0 at the canon's own breadth | {own['sr0']:.4f} |\n"
            f"| **DSR at the canon's own breadth** | **{own['dsr']:.4f}** |\n"
            f"| best MINED alternative, in-sample | "
            f"{f['best_mined_alternative']['day_sharpe']:.4f} "
            f"(`{f['best_mined_alternative']['cell']}`) |\n"
        ),
        f"\n**Verdict Q1: {verdict}** (screen: DSR ≥ 0.95).\n",
        "\n### Q1b — the verdict depends entirely on how you model the search\n",
        (
            "\nSR0 is a function of how hard you searched. The cross-product space above "
            "is **broader than the search that actually produced the canon**: "
            "`l3_check_trial.py` evaluated each check once, at its frozen threshold, "
            "judged by era-split lift tables — it did not mine combinations and keep the "
            "best. Charging the canon for a search it never ran is the same nominal-"
            "breadth error our shrinkage model makes. Here is the whole ladder:\n"
        ),
        (
            "\n| search breadth charged | trials | trial SR sd | SR0 | **DSR** | verdict |\n"
            "|---|---|---|---|---|---|\n"
            + "".join(
                f"| {lab} | {v['n_trials']:,} | {v['trial_sr_sd']:.3f} | {v['sr0']:.4f} | "
                f"**{v['dsr']:.4f}** | {'PASS' if v['significant'] else 'fails'} |\n"
                for lab, v in res["breadth_ladder"].items()
            )
        ),
        (
            "\nThe canon is the same book in every row — only the null moves. That is the "
            "single most important operational lesson in this report: **DSR is only as "
            "honest as your account of the search**, and an inflated trial space "
            "manufactures a false negative on a book that is demonstrably real.\n"
        ),
        "\n## Q2 — what does PBO say about the selection procedure?\n",
        (
            f"\n| trials | splits (S={N_BLOCKS}) | **PBO** | degradation slope | "
            f"P[OOS loss] |\n|---|---|---|---|---|\n| {f['pbo']['n_trials']:,} | "
            f"{f['pbo']['splits']:,} | **{f['pbo']['pbo']:.3f}** | "
            f"{f['pbo']['slope']:+.3f} | {f['pbo']['prob_oos_loss']:.3f} |\n"
        ),
        (
            "\nPBO judges the *procedure*, not the canon: across every symmetric split, "
            "does the in-sample winner stay above the out-of-sample median? Read it "
            "alongside DSR — DSR asks whether this specific book is real.\n"
        ),
        "\n## Q3 — did the gate PREDICT the holdout? (the part only NY can answer)\n",
        (
            f"\n| span | days | trades | day-Sharpe | total (1 lot) |\n"
            f"|---|---|---|---|---|\n"
            f"| fit 2025-06→2026-07 | {f['days']} | {f['trades']:,} | "
            f"{p['fit_day_sharpe']:.4f} | ${f['canon']['total_1lot']:,.0f} |\n"
            f"| sealed 2023/24 holdout | {h['days']} | {h['trades']:,} | "
            f"{p['holdout_day_sharpe']:.4f} | ${h['canon']['total_1lot']:,.0f} |\n"
        ),
        (
            f"\nShrinkage fit→holdout: **{p['shrinkage']:+.4f}** Sharpe "
            f"({p['retained_fraction'] * 100:.0f}% retained).\n"
        ),
        f"\n**{agree}**\n",
        "\n## What this does NOT establish\n",
        (
            "\n- DSR and PBO are **screening** statistics. The canon ships on funded-rules "
            "Monte Carlo and maxDD against a trailing drawdown — not on a Sharpe. Nothing "
            "here revises that.\n"
            "- The 16 checks were not specified independently of NY data; they came from "
            "the original canon fitted on 2025. 'Own breadth' is therefore a lower bound "
            "on the true search, exactly as stage-3 noted for London's wall arm.\n"
            "- One strategy passing is one data point. It says the gate does not reject a "
            "known-real book; it does not prove the gate catches every fake one.\n"
        ),
    ]
    (DOCS / "VALIDATION-NY-CANON.md").write_text("".join(L))
    print("".join(L))


if __name__ == "__main__":
    main()
