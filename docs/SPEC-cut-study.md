# SPEC — THE CUT STUDY (Phase 3, declared before compute)

Nothing in this programme has ever REMOVED a trade and measured the
remaining book. Every prior test was a base rate, a correlation, a binned
readout, or a sizing weight. This study is the first gate test (eighth law:
gates convert lift ~1:1; weights bleed it).

## Population

M-TABLE fit rows, POST entry-price fix (PHASE0-verification.md item 1),
arm-separated from the first line of code:

- **Reject book:** arm == "reject", valid geometry (risk > 0). The bet: the
  level holds.
- **Break-retest book:** arm == "break", retested == True, valid geometry.
  The bet: the level flipped.

Different bets, different validators, never a shared denominator. Outcome
column: `out_ship` (the adopted exit). Collapse: structural clusters
(X=0.5W); intervals: day-level bootstrap (D4).

## Design — seeded split-half on fit

- Split unit: session-day. Seed **20260807**, stratified by era (H2-2025 /
  H1-2026) so both halves carry both eras. Half 1 = EXPLORATION (labelled
  as such in every output); Half 2 = CONFIRMATION, untouched until
  survivors are pre-registered in the appendix below with declared signs
  and bars.
- After confirmation: the three gates on the full fit span —
  cluster-collapse (structural), period folds (LODO by month), dual
  currency (hit AND R). All three, every survivor.
- The sealed holdout is NOT part of this study. Survivors that also pass
  the three gates queue for the D2/D3 holdout looks under the frozen
  aggregation rule.

## Operation — declared cuts, never swept

A cut removes the declared-worst bin of ONE variable and reports the
REMAINING book. Cut definitions are fixed by the existing bin structure:

- Binary/tri-state features (flowconf, thru_delta_conf, d5/d15/d30_conf,
  bp5opp): cut the disconfirming bin (value 0; ties 0.5 stay).
- Continuous features (volx, delta_z, eff_result, cvd_slope30): cut the
  bottom quartile, quartile edges computed on Half 1 only and FROZEN for
  Half 2 (declared direction: low = bad; a Half-1 readout showing the
  opposite monotonicity disqualifies the variable rather than flipping the
  cut — no sign shopping).
- Bar variables: cnt_ahead_1w (cut the TOP bin — obstacles hurt, H2's
  declared sign), cnt_beyond_3r (top bin), fresh-permission admissibility
  (cut UNBROKEN-ceiling rows at K=1), pen_bw (bottom quartile),
  n_attempts (no cut — item 11 read first; only if a monotone break
  appears at n>=5 does a declared cut enter), session (cut ny_pm — the
  truncation-confounded stratum — recorded as an operational cut, not an
  edge claim).

No cut is swept across thresholds. One declared cut per variable, one
readout per half.

## Metric — the book, not the bin

Per cut, report the remaining book: expectancy (out_ship, structural
cluster-collapsed), trade count, green-day rate, max drawdown of the
day-P&L path, and the score:

**P(5 qualifying days AND profit target BEFORE an EOD trailing-DD breach)**
— estimated by day-level bootstrap over the remaining book's day-P&L
vectors through the funded-account mechanics (`scripts/funded_book.py`
parameters for the Lucid Flex account), 2,000 draws, seed 20260807.

**Executable-book convention (declared; BR-10 makes this mandatory):** the
book sim takes the FIRST trigger of each structural fight that survives the
cut, in time order; ALL fights are taken (overlapping exposure allowed —
each fight is an independent, separately-sized trade, matching desk
practice). Day P&L = sum of fight R x $160 risk. AMENDED 2026-08-07 BEFORE
any Half-1 readout: the original one-position-at-a-time wording is not
computable from the table (exit minutes are not recorded); the
one-at-a-time variant is deferred to the assembly stage. Baseline to beat,
from the Phase 0 restatement: +0.139R / +0.162R per fight by era (BR-9).
Law-7 arithmetic runs against THIS baseline, not against −0.047R.

**Cut rules pinned (before Half-1 contact):** binary confirms bad bin = 0
(bp5opp bad bin = 1 — it MEASURES opposing pressure); continuous
(volx, delta_z, eff_result, cvd_slope30, closeloc, rangex, pen_bw) bad =
bottom quartile, edges frozen from Half-1 books per arm; counts
(cnt_ahead_1w, cnt_beyond_3r) bad = above the Half-1 p75;
admissible_snapshot bad = BLOCKED (censusB rule as stored — the K=1-pure
refinement needs Census C's table and is recorded as deferred);
session bad = ny_pm; confluence (break arm) bad = 3+.
**Infeasibility rule:** a declared cut that removes 0%, removes >60%, or
leaves <50 book rows is recorded infeasible — never adjusted.
**Survivor rule:** implied lift >= +0.05R (Law-7 bar) AND eval score >=
the same half's baseline score. Survivors are appended to the appendix
with sign and bar, then Half 2 runs them UNCHANGED.

A cut that improves per-trade R but lowers the score FAILS — cuts cost
frequency and frequency produces qualifying days.

## Law 7 — feasibility arithmetic BEFORE any candidate runs

Gate mechanism: removing fraction q with removed-bin mean mu_cut moves the
book from EV to (EV − q·mu_cut)/(1 − q); lift = q·(EV − mu_cut)/(1 − q).

Worked at the restated book EV (see PHASE0 appendix; ~−0.05R/trade class):

- q = 0.25 (quartile cut): lift = (EV − mu_cut)/3. Closing a +0.10R gap
  needs mu_cut ≈ EV − 0.30R, i.e. the removed quartile must run ≈ −0.35R.
- q = 0.35-0.40 (binary disconfirm bin): lift ≈ 0.54-0.67·(EV − mu_cut).
  Closing +0.10R needs the disconfirm bin ≈ −0.20R.

**Feasibility bar (declared):** the implied full-book lift computed by the
formula above from the candidate's Half-1 removed-bin mean must be
>= +0.05R for the candidate to be eligible for pre-registration on Half 2.
Candidates below the bar are recorded (miss) and not advanced — no
"promising, rerun with a different bin".

## Candidate register (fixed BEFORE Half-1 contact)

Flow (sequenced last historically, never tested): flowconf, volx, bp5opp,
d5_conf, d15_conf, d30_conf, thru_delta_conf, eff_result, cvd_slope30,
delta_z — plus closeloc and rangex IF present in the table (verify: these
two are suspected unimplemented; if NaN they are recorded as absent, not
silently skipped).

Bar: cnt_ahead_1w, cnt_beyond_3r, fresh-permission (K=1) admissibility,
pen_bw, session(ny_pm operational).

AMENDMENT (2026-08-07, before any Half-1 readout existed): confluence_count
enters as a BREAK-ARM candidate (cut the TOP bin, 3+), motivated by Phase 2
item 10 (rho −0.126/−0.058 in R, declared-sign confirmed). Recorded
honestly: item 10 read the FULL fit span, so Half-2 "confirmation" for this
one variable is partially informed — its real confirmation is the D2
holdout. It runs in the study for book-impact measurement, flagged
`prior-full-fit-read`.

Anything not on this list does not run in this study.

## Appendix — pre-registered survivors (Half 1 run 2026-08-07; frozen
BEFORE any Half-2 contact)

Half-1 baselines: reject EV +0.120R, n 971, score 56.9% | break EV
+0.130R, n 686, score 63.7%. Full readout in the run log. 18 candidates
per arm; survivors below; notable recorded miss: delta_z's declared
low=bad direction INVERTED on both arms (the extreme-delta bin carries
+0.25/+0.33R) — recorded, not flipped, not advanced.

**Half-2 bar, declared now for every survivor:** same cut, same frozen
edges, sign unchanged (removed-bin mean below the Half-2 book EV), implied
lift >= +0.05R on Half 2, AND Half-2 score >= the Half-2 baseline score.
Then the three gates on full fit: (G1) per-fight units by construction —
asserted, plus no single day contributing >25% of the lift; (G2) LODO by
month, lift sign >= 0 in 14/14 folds for ADOPT, 12-13/14 recorded as
"weak, holdout decides", <=11 fails; (G3) dual currency — win-rate
(out_ship>0) before/after reported; a >3pp win-rate drop is flagged on
the record.

| # | arm | cut | H1 lift | H1 score | flag |
|---|-----|-----|---------|----------|------|
| S1 | reject | flowconf==0 removed | +0.053 | 72.1% | |
| S2 | reject | d30_conf==0 removed | +0.066 | 68.9% | |
| S3 | reject | volx<Q1 removed | +0.066 | 71.3% | |
| S4 | reject | session==ny_pm removed | +0.052 | 69.4% | operational |
| S5 | break | thru_delta_conf==0 removed | +0.057 | 80.6% | |
| S6 | break | d15_conf==0 removed | +0.086 | 80.2% | |
| S7 | break | volx<Q1 removed | +0.116 | 88.6% | |
| S8 | break | cvd_slope30<Q1 removed | +0.059 | 74.6% | |
| S9 | break | closeloc<Q1 removed | +0.062 | 78.3% | |
| S10 | break | confluence>=3 removed | +0.108 | 84.4% | prior-full-fit-read |
