# NY canon through the validation gate — DSR + PBO

**READ-ONLY.** No canon rule, threshold, or config was touched. This measures the book `scripts.funded_book.load_book` already produces.

**On holdout use:** NY's sealed 2023/24 look was already spent and its results are published in `scripts/funded_book.py`. Computing a statistic on data whose look is already taken spends nothing — no new holdout look was consumed here.

## Why this run matters

The London 29k sweep calibrated the gate against a known **null**. The NY canon is the opposite pole — the book we know is **real**. A gate that fails it is miscalibrated. And because NY's holdout is already open, this is the one place we can test whether the gate *predicts* out-of-sample survival rather than merely agreeing with a conclusion we already hold.

## The candidate

The shipped canon at **1 lot**: 956 trades over 230 days (2025-06-02 → 2026-07-08). 1 lot deliberately — DSR and PBO screen the edge; tiers, elite, the budget spine and both sizing profiles are L4 policy, judged by funded-rules Monte Carlo and maxDD, not by a Sharpe.

## The search it came out of

`l3_check_trial.py` trialled 16 checks, selected per session. Every single and every pair, per session, paired across pre × gold = **18,496 candidate books**; 18,488 clear the n≥25 floor. The DSR null is the cross-sectional variance of those trial Sharpes, so nested and correlated candidates are charged at effective breadth.

## Q1 — does DSR confirm the canon?

| | value |
|---|---|
| canon day-Sharpe (fit, 1 lot) | 0.4211 |
| skew / kurtosis | +2.823 / 15.67 |
| PSR (undeflated) | 1.0000 |
| SR0 at the canon's own breadth | 0.2304 |
| **DSR at the canon's own breadth** | **1.0000** |
| best MINED alternative, in-sample | 0.4841 (`pre:WALLSZ&T2 | gold:W&G`) |

**Verdict Q1: PASSES at the canon's own search breadth** (screen: DSR ≥ 0.95).

### Q1b — the verdict depends entirely on how you model the search

SR0 is a function of how hard you searched. The cross-product space above is **broader than the search that actually produced the canon**: `l3_check_trial.py` evaluated each check once, at its frozen threshold, judged by era-split lift tables — it did not mine combinations and keep the best. Charging the canon for a search it never ran is the same nominal-breadth error our shrinkage model makes. Here is the whole ladder:

| search breadth charged | trials | trial SR sd | SR0 | **DSR** | verdict |
|---|---|---|---|---|---|
| 16 checks, per session (the actual L3 trial) | 30 | 0.111 | 0.2304 | **1.0000** | PASS |
| singles + pairs, per session | 240 | 0.102 | 0.2885 | **0.9984** | PASS |
| full pre x gold cross product (mined) | 18,488 | 0.089 | 0.3564 | **0.9252** | fails |

The canon is the same book in every row — only the null moves. That is the single most important operational lesson in this report: **DSR is only as honest as your account of the search**, and an inflated trial space manufactures a false negative on a book that is demonstrably real.

## Q2 — what does PBO say about the selection procedure?

| trials | splits (S=16) | **PBO** | degradation slope | P[OOS loss] |
|---|---|---|---|---|
| 18,488 | 12,870 | **0.022** | -0.595 | 0.000 |

PBO judges the *procedure*, not the canon: across every symmetric split, does the in-sample winner stay above the out-of-sample median? Read it alongside DSR — DSR asks whether this specific book is real.

## Q3 — did the gate PREDICT the holdout? (the part only NY can answer)

| span | days | trades | day-Sharpe | total (1 lot) |
|---|---|---|---|---|
| fit 2025-06→2026-07 | 230 | 956 | 0.4211 | $148,766 |
| sealed 2023/24 holdout | 122 | 637 | 0.6029 | $86,324 |

Shrinkage fit→holdout: **-0.1817** Sharpe (143% retained).

**The gate's fit-only verdict was CORRECT — it called the canon real before the holdout was consulted, and the holdout agrees.**

## What this does NOT establish

- DSR and PBO are **screening** statistics. The canon ships on funded-rules Monte Carlo and maxDD against a trailing drawdown — not on a Sharpe. Nothing here revises that.
- The 16 checks were not specified independently of NY data; they came from the original canon fitted on 2025. 'Own breadth' is therefore a lower bound on the true search, exactly as stage-3 noted for London's wall arm.
- One strategy passing is one data point. It says the gate does not reject a known-real book; it does not prove the gate catches every fake one.
