# PREREG — FLOW CONCORDANCE, DEPTH, IN-TRADE (one declaration, one run)

Written 2026-08-07 BEFORE any number in sections B or C exists. Section A
is audit queries against already-committed artefacts, not new tests.
Fit-only; runs in parallel with holdout look #1; **no sealed row is
touched.** ONE candidate set, ONE family-wise correction, ONE split-half,
ONE findings file.

## Framing, recorded

Two canon findings were voided by contamination and **never refuted**: the
wall-quality cut and the graded flow-confluence conviction system. The
current entry model — market entry at the next bar's open, features from
bars ≤ t, entry-price gate enforced — removes the contamination mechanism,
so both are measurable for the first time.

Separately: every flow test in this programme has evaluated features **one
at a time**. The trader's system counted how many features AGREED. That is
a different object and has never been measured.

---

## B — CANDIDATE SET (declared, closed)

### B1 — FLOW CONCORDANCE COUNT (headline)

For each trigger bar, reduce every flow feature to a binary "does it agree
with the trade direction", and **count the agreements, unweighted**.

- Binary reduction, declared per feature: direction-conditioned features
  (`flowconf`, `thru_delta_conf`, `d5_conf`, `d15_conf`, `d30_conf`) agree
  iff == 1; `bp5opp` agrees iff == 0 (it MEASURES opposing pressure);
  `cvd_slope30` and `delta_z` agree iff > 0 (already direction-signed);
  `volx`, `eff_result`, `rangex` agree iff ≥ their fit median (magnitude
  features — "is there conviction behind it"); `closeloc` agrees iff ≥ 0.5
  (closed in the trade-favourable half of the bar).
- **CONCORD = the unweighted sum**, range 0–12. Ties (0.5) count 0.
- **Zero free parameters. No weights. No combo search.** The canon's
  version was a weighted score with hand-set weights over 339 searched
  combinations — that is where the overfitting lived.
- **This is ONE candidate, not twelve.** Twelve features tested
  individually is twelve trials; their concordance count is one statistic.
  That is the multiplicity problem *solved*, not *paid*.

Tested: monotone relationship of EV vs CONCORD, **both arms separately,
both eras, day-boot CIs, the X ∈ {0.25,0.5,1.0,2.0}W sensitivity**.

**Law 8 order, declared: monotone first, gate second.** A gate is placed
only at a threshold whose monotone relationship already cleared. A sizing
weight is considered **only** if the gate clears AND the Law-7 arithmetic
supports it — A-2 died because a ladder bled a 0.12 rho down to 0.01R, and
that failure mode is assumed until disproved.

### B2 — WALL-QUALITY CUT (highest-prior untested candidate)

`dep_wall_below_d < 2.75 OR WALLSZ == 0`, computed **as-of the decision
bar** (book snapshot at the last minute ≤ decision close), entry-price
gate applied, on the composite, **both arms separately**.

Prior on the record: 37–41% win rate on the cut set in all three canon
eras, +7pp book win rate, maxDD −37/−45%, never refuted.

### B3 — REMAINING BOOK-BASED DEPTH FEATURES, individually

`dep_thickness_vs_day`, `dep_imbalance`, `support_minus_resist`,
`support_wall_dist`, `support_wall_size`, `dep_thickness_delta_5m` — six
candidates, bottom-quartile cut (edges frozen on half 1), declared
direction low=bad.

### B — LAW 7 ARITHMETIC, PUBLISHED BEFORE ANY OF B RUNS

Composite book: 3,336 fights, EV **+0.186R**. Gate lift =
q·(EV − μ_cut)/(1 − q).

**Depth coverage is the binding constraint on B2/B3 and is stated up
front.** Depth files cover NY 08:00–10:29 (494 fights) and, from the raw
MBP-10 condensed files, NY 03:00–04:59 (305 fights): **799 of 3,336 =
24.0% of the book.** Depth-eligible fights are a better-than-average
subpopulation (EV +0.286 vs +0.186), which is itself a confound to
declare, not discover.

Whole-composite lift achievable by B2/B3, bounded by that coverage:

| cut share of eligible | = share of book | μ_cut −0.20R | μ_cut −0.40R |
|---|---|---|---|
| 25% | 6.0% | +0.025 | +0.037 |
| 40% | 9.6% | +0.041 | **+0.062** |
| 60% | 14.4% | **+0.065** | **+0.098** |
| 100% | 24.0% | **+0.121** | **+0.184** |

**Ruling: B2/B3 are NOT dead on Law 7** — they clear +0.05R if the cut
removes ≥40% of eligible at μ_cut ≤ −0.40R, or ≥60% at −0.20R. Both are
within the range the canon prior claims. They run.

**But the primary B2/B3 readout is the depth-eligible subpopulation's own
base rate**, with the whole-book lift reported as a coverage-bounded
secondary. A cut measured on 24% of a book cannot be shipped as a
whole-book rule without stating that bound, and it is stated here.

B1 has no coverage constraint (flow is 99–100% covered), so its Law 7 is
the ordinary one: at q = 0.30, μ_cut must be ≤ −0.10R to clear +0.05R; at
q = 0.50, ≤ +0.086R.

---

## C — IN-TRADE CENSUS (same table walk, no separate run)

In-trade flow measured at **t+1, t+2, t+3, t+5, t+10 minutes from entry**.
**No lookahead: each point uses only footprint minutes ≤ that minute.**

Four in-trade flow signals, declared (flow only — never price, since price
is the conditioning variable):

1. cumulative delta over [entry, entry+N] agrees with direction
2. the final minute's delta agrees
3. the OLS slope of cumulative delta over the window agrees (N ≥ 3)
4. the window's buy/sell volume ratio agrees

**IN-CONCORD = their unweighted sum, 0–4** — the same object as B1, applied
in-trade.

### C1 — the load-bearing measurement

For trades **underwater at t+N** (adverse vs entry at that minute), does
in-trade flow separate recoverers (out_ship > 0) from non-recoverers?

**Reported as PRECISION and RECALL of a sign-based flag, not correlation.**
Base rate P(recover | underwater at t+N) is reported alongside so precision
is readable against it. Then: does IN-CONCORD ≥ k beat the best single
signal on the same population?

### C2 — the +2R-then-stopped tell (prior: expect little)

Trades with mfe_r ≥ 2 that finished negative, vs mfe_r ≥ 2 that finished
positive: in-trade flow at t+5 and t+10. Declared prior AGAINST finding
anything — 85% of retraces resume and the shipped exit already banks 75%
at 3R, so most of the loss window is already closed. Approximation
declared: the peak minute is not recorded in the table, so the comparison
is at fixed horizons, not at the peak.

---

## Multiplicity, split-half, and bars

**Candidate count: 10** — B1 (1) + B2 (1) + B3 (6) + C1 recovery flag (1)
+ C2 tell (1). **Bonferroni ×10 applied to every claim**, declared now.
C's descriptive tables (base rates, precision/recall curves) are reported
without a gate claim and do not consume additional multiplicity.

**Split-half:** the SAME frozen day-split used by the cut study
(`output/htf_ma_census/cutstudy_split.csv`, seed 20260807). Explore on
half 1, pre-register survivors with declared signs and thresholds, confirm
on half 2 unchanged. Then the three gates (cluster-collapse, period folds,
dual currency) on full fit.

**Bar for a survivor:** implied whole-book lift ≥ +0.05R on half 1 (Law 7),
sign unchanged on half 2, ×10-corrected CI excluding zero, and — for any
gate — the qualifying-day/frequency axis reported alongside R (D4).

**Nothing from this prereg goes to a holdout.** Survivors ship on fit +
forward validation via the seven-locus recorder, per R0 of the holdout
declaration.

## Efficiency contract (D)

One feature frame computed ONCE per session day — trigger flow, depth at
decision, in-trade flow at all five horizons — then every candidate scored
off that frame. Bootstrap draws batched. No per-candidate table walk, no
intermediate reports, no per-candidate notifications. A candidate dead on
Law 7 is not run and is recorded in one line.
