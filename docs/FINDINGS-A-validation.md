# FINDINGS — PHASE A: validating the positive book (2026-08-07)

Context for a fresh reader: NQ futures, mechanical version of a hand-traded
15m-Bollinger-MA strategy. The M-TABLE is the master event table (4,716 fit
rows, 2025-06..2026-07, entry-price-verified). "The book" = executable
first-of-fight reject book under the adopted exit (75% out at 3R, remainder
trailed): take the first trigger of each structural fight, one trade each.
"S1" = the one confirmed selection cut: skip fights whose decision-bar
aggressive flow (delta) disagrees with the trade direction (flowconf==0).
Structural fight = same-side triggers with no intervening excursion
≥ X·W from the 15m MA between them (X = 0.5W by declared fallback; W =
Bollinger band width). All CIs are day-level bootstrap, seed 20260807.

## A1 — clustering sensitivity curve

The book and S1's lift at every fight-definition X, plus the X→0 limit
(every trigger its own fight):

| X | fights | /day | EV H2-2025 [CI] | EV H1-2026 [CI] | pooled | S1 lift | S1 EV-after |
|---|---|---|---|---|---|---|---|
| 0 (rows) | 3,111 | 10.7 | +0.057 [−0.026,+0.142] | +0.190 [+0.090,+0.300] | +0.120 | +0.051 | +0.171 |
| 0.25W | 2,485 | 8.5 | +0.070 [−0.023,+0.161] | +0.210 [+0.107,+0.323] | +0.136 | +0.092 | +0.228 |
| **0.50W** | 1,830 | 6.3 | **+0.139 [+0.028,+0.253]** | **+0.162 [+0.051,+0.280]** | +0.149 | **+0.107** | +0.257 |
| 1.00W | 1,214 | 4.2 | +0.111 [−0.003,+0.232] | +0.113 [−0.017,+0.252] | +0.112 | +0.107 | +0.219 |
| 2.00W | 760 | 2.6 | +0.070 [−0.075,+0.217] | +0.139 [−0.031,+0.305] | +0.102 | +0.163 | +0.265 |

**Verdict.** Two separate questions, two separate answers:

1. *Is the positive book an artifact of X=0.5W?* **No in sign, yes in
   precision.** The pooled point estimate is positive at every X including
   the convention-free row limit (+0.10..+0.15). But the claim "CIs clear
   zero in BOTH eras" holds ONLY at X=0.5W — H2-2025's CI includes zero at
   every other X. BR-9 must carry this qualifier: the book is
   point-positive everywhere, era-significant only at the declared X.
   H1-2026 does the heavy lifting; H2-2025 is ambiguous-positive.
2. *Was S1 measured against a moving baseline?* **No.** S1's lift is
   positive at every X and monotone-increasing with it (+0.051 → +0.163).
   Whatever fight definition you pick, the cut pays; coarser fights pay
   more. S1's EV-after sits +0.17..+0.27 across the whole curve.

## A2 — the re-entry check

**The documented pair is not in the table.** Session day 2026-06-02 (Wed 3
Jun pre-market) contains exactly ONE ny_pre trigger: a break-short at
08:45 that lost (−1.11R). The remembered two-attempt pre-market pair is
not a 15m-BB-MA-grammar event — the hand grammar (sweep levels) indexes
setups the M-TABLE does not. However, the pathology named is real and
present the same session: London fight `above:S4` — 04:45 attempt stopped
(−1.06R), 05:00 re-entry won (+2.94R, 8R MFE). First-of-fight takes that
loser and skips that winner.

**The declared A/B, book-wide** (B = keep entering the fight's next
trigger while the previous entered attempt was a full stop-out):

| convention | EV/fight pooled | n (/day) | eval score | notes |
|---|---|---|---|---|
| A first-of-fight | +0.149 | 1,830 (6.3) | 64.5% | H2 +0.139 [+0.028,+0.253], H1 +0.162 [+0.051,+0.280] |
| B re-enter-after-stop | +0.025 | 2,742 (9.4) | 33.9% | H2 −0.009 [−0.092,+0.078], H1 +0.063 [−0.025,+0.159] |
| A + S1 | **+0.257** | 832 (2.9) | **86.5%** | H2 +0.219 [+0.066,+0.379], H1 +0.298 [+0.145,+0.457] |
| B + S1 | +0.135 | 1,380 (4.7) | 66.0% | |

The 912 added re-entries average ≈ **−0.22R each**. Unconditional
re-entry-after-stop is strongly negative even flow-filtered.

**Verdict.** First-of-fight stands as the book convention. The trader's
demonstrated winning re-entry was *sweep-conditioned* — a structural
condition the table does not index. "Re-enter only after a liquidity
sweep" is a legitimate NEW variable if declared with a sweep definition
(Law 7 arithmetic first); plain re-entry is dead on the record.

## A3 — S1's multiplicity, true denominator

Premise correction first: **the study ran with all twelve flow features
live.** closeloc/rangex were found 100%-NaN in the RECORDED table during
Phase 0, wired at root, and the table rebuilt BEFORE Half-1 ran (both
appear in the Half-1 readout — closeloc was a candidate and later a
kill-illustration). The denominator was genuinely 18 candidates per arm.

Permutation test (flowconf shuffled across fights within session-day,
10,000 permutations):

| frame | observed lift | raw p | ×4 (pre-registered reject survivors) | ×10 (all pre-registered) | ×18 (flat reject family) | ×36 (both arms flat) |
|---|---|---|---|---|---|---|
| Half-2 (confirmation) | +0.175 | 0.0042 | **0.017** | **0.042** | 0.076 | 0.151 |
| full fit | +0.107 | 0.0037 | — | — | 0.067 | 0.133 |

**Verdict.** Under the design's own two-stage logic — 18 candidates spent
their multiplicity in exploration; Half 2 confirmed only the 4
pre-registered reject survivors — S1 clears family-wise 0.05 (p_fw
0.017–0.042). Under the flat ×18/×36 correction that ignores the
pre-registration structure, it is marginal (0.07–0.15) and does not
clear. Both frames are on the record. The three gates (LODO 14/14,
single-day ≤6.6%, win rate +4pp) and the A1 X-robustness are additional
independent checks, but the decisive validation is forward flow (Phase C
recorder) — the flow holdout cannot resolve a +4pp effect and stays
unspent.

## Standing corrections issued by Phase A

- BR-9 (BASE-RATES.md) gains the A1 qualifier: point-positive at all X,
  era-CIs clear zero at X=0.5W only.
- The break arm stays parked (unchanged by anything here).
- Neither holdout look was touched.
