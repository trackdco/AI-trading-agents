# NYA-DS-01 — JadeCap Daily Sweep (1H swing raid + SFP + reversal)

Prereg: docs/PREREG-jadecap-sweep.md. Source: verified trader (Kyle Ng /
JadeCap — $2.55M Apex single payout, industry-corroborated; see
intake2-credibility.md). Card: research/FUNNEL.md.

### Trial 1 — census (2026-08-05, as-taught default expression)
scripts/nya_ds_census.py: bias-gated (prior close vs close before), prior
1-2 day 1H fractal levels untapped at 09:00, raid + same-bar close back
inside during AM (09-11h bars) or PM (13-15h) windows, entry at
confirmation close, stop at SFP-bar extreme, 2R target, time exits
(12:00 AM-entries / 16:00 PM), first signal per day.
RAW: n=381 (~2.3/wk, matches teaching), WR 38%, -1,132pts, $-454, PF 0.90
— ugly raw per the law. YEARS: 2023 PF 1.11 / 2024 1.15 / 2025 0.87 /
2026 0.64 — DECAY SHAPE (worked 23-24, dying 25-26; inverse of the
canon's regime profile).
DECLARED SPLITS (first pass):
- AM PF 0.80 vs PM PF 1.56; PM-vs-AM permnull p=0.030 (significant lift)
  BUT PM 2025 is PF 0.32 (n=26) — era-flip inside the cell; evidence, not
  a gate. PM years: 3.67/4.70/0.32/2.24.
- Raid penetration terciles: shallow PF 1.42 / mid 0.79 / DEEP 0.75 with
  deep NEGATIVE ALL FOUR YEARS (-146/-157/-270/-723) — a legal
  every-era-bad cut candidate (canon wall-cut precedent) for L1, declared
  variable, to be taken only with the full search context.
NEXT: remaining declared search (SFP close strength, level age, distance
from open, gap context; flow at the raid bar on flow span; depth at level
on morning overlap), then L1 with any legal cuts. NO BIN off raw (§5.9.1).
Ledger rows 102-104.

### Trial 2 — declared search + L1 (2026-08-05) — GAP CONTEXT IS THE VARIABLE
Full declared candle search (scripts/nya_ds_census.py enriched; analysis in
ledger context):
- SFP close strength: strong tercile PF 1.15 (2025 mildly neg) — weak signal.
- Level age: fresh PF 1.17 (2023 neg) — weak. Distance-from-open: nothing.
- GAP CONTEXT (the find): raids AGAINST the overnight gap (>20pts) are
  negative ALL FOUR YEARS (PF 0.68, n=227: -311/-626/-462/-1252) — an
  every-era-bad cohort, legal cut class (canon wall-cut precedent). Flat-gap
  days PF 1.77 positive all four years (n=54); gap-with PF 1.46 (3/4).
  Mechanism-coherent: raiding into a day that gapped against the bias =
  fighting the overnight repricing, not fading a stop-hunt.
- COMBO shallow-pen + strong-close: PF 2.19 n=33 permnull p=0.108 — noted,
  not claimed.
L1 EXPRESSIONS (both cuts are declared-variable every-era-bad cohorts):
- L1a cut gap-against: n=154, WR 42%, +1,520pts, $+3,561, PF 1.56;
  years 2.00/2.69/1.00/1.11 (no negative year); permnull p=0.006.
- L1b cut gap-against + deep-pen: n=117, WR 46%, +1,514pts, $+3,556,
  PF 1.89; years 1.76/2.47/1.54/1.63 — EVERY YEAR POSITIVE; permnull
  p=0.008; ~0.69/wk (sleeve-cadence). 2026 cell n=7 — THIN, flagged.
The decay concern from trial 1 largely lives in the gap-against cohort;
the L1b expression holds 2025-26. CANON SHAPE: raw 0.90 → legal cuts →
1.89 era-consistent is the textbook arc.
NEXT (owed before any grading): flow-at-raid on flow span (declared),
depth-at-level (morning overlap), strict-cost stack, §3.2 loser autopsy +
MFE/MAE + time-segment schema, exit/stop arms under §6.0, redundancy gate
vs Brake's sweep-reclaim. Ledger rows 105-107.

### Trial 3 — strict costs + flow-at-raid round (2026-08-05)
- STRICT-COST STACK (§5.11-3 declared arm): L1b holds — PF 1.79 strict
  (vs 1.89 base), $+2,952, EVERY year positive (1.66/2.35/1.46/1.56). PASS.
- FLOW-AT-RAID (declared): flow span covers 117 census trades — but that
  span is the raw family's weak era, and no flow feature rescues the
  UNGATED population (heavy-delta PF 0.66, absorb-flagged 0.36 — the
  gap-against cohort dominates). On L1b ∩ flow-span: n=30 — cells n=9-11,
  TOO THIN to claim (absorb-flagged PF 3.40 n=11 recorded as evidence
  only, the §5.12-9 shape). The stop-run-absorption discriminator stays
  OPEN, decidable as flow history accumulates (~monthly growth).
- Ledger row 108. NEXT RUNGS before grading: §3.2 loser autopsy + MFE/MAE
  + time-segment schema (checkpoints adapted to the hourly clock:
  t+5/15/30/60/120min, declared here); exit/stop arms under §6.0;
  redundancy vs Brake's sweep-reclaim; then DSR/PBO grading vs the
  sleeve floor.

### Trial 4 — §3.2 loser autopsy + MFE/MAE + time segments on L1b (2026-08-05)
scripts/nya_ds_autopsy.py (checkpoints t+5/15/30/60/120, hourly-clock
adaptation declared; still-open-at-t conditioning per §5.12-5).
- EXIT MIX: time 67 / stop 30 / target 20 — the 2R target hits only 17%;
  the clock, not the bracket, resolves most trades (time-exit trades mean
  +0.21R). Exit design is where this family's tournament will matter.
- LOSERS (n=63): median MFE 0.11R — losers never really go green (only
  27% ever saw +0.5R, 13% saw +1R); they ride to the stop (median MAE
  0.91R). Half die at the stop, half at the clock.
- WINNERS (n=54): median MAE 0.28R; worst survived 0.96R (a near-stop
  save); p25 endured 0.51R; median time-to-target 60 min.
- CANON GRAMMAR TRANSFERS, with one family-specific twist:
  PRESS at t+15 wins 100% (n=12), t+60 88% (n=16) vs base 46%;
  DYING (MAE<=-0.5R) wins 35-43% — the coin-flip degradation, matches
  canon. TWIST: GIVEBACK IS STRONG HERE (t+30 76% n=21, t+60 100% n=13)
  unlike the canon's ambiguous giveback — on an hourly mean-reversion
  trade, pulling back off peak is rotation, not death. This goes in the
  agent-rung playbook with the sign FLIPPED from canon.
- BE note for the tournament: only 27% of losers ever reached +0.5R — a
  BE@0.5R arm has limited material; §5.12-6 null stands until defeated.
- Ledger row 109. NEXT: exit/stop arms under §6.0 (time-exit variants,
  partial-at-1R, BE null, stop-cap class), redundancy vs sweep-reclaim,
  then grading.

### Trial 5 — exit/stop tournament (2026-08-05, prereg amendment b) — DEFAULT STANDS, challengers banked
scripts/nya_ds_exitlab.py, 10 declared arms, day-level PBO CSCV (S=8, 70
splits, 104 days). Population note: 19 of 117 trades have a degenerate
zero-length management window under the taught 12:00 exit (signals on the
11:00 bar enter at the cutoff) — dropped by the lab, rescued only by the
hold1555 arm (n=110); spec wart recorded.
- Autopsy prediction CONFIRMED: deeper/no targets win in-sample —
  no_target +35.0R ($5,599), cap30 +35.2R ($5,628), t3r +34.2R ($5,474)
  vs default +23.2R ($3,705, every year positive).
- BE NULL DEFEATED AGAIN (§5.12-6 holds): be05 wrecks it (+5.6R, WR 33%);
  be10 +17.0R < default. Third family where BE hurts a mean-reversion book.
- Stop-cap class delivers again (fade cap20 precedent): cap30 top-2 with
  2025 +17.8R.
- PBO = 0.50, slope -0.81 — the displacement bar (PBO < 0.5) is NOT met,
  and no holdout is declared for this family. Per §6.0: DEFAULT STANDS;
  no_target / cap30 / t3r / hold1555 BANKED as challengers for a round-2
  tournament under a declared holdout.
- REDUNDANCY GATE: blocked on Brake — sweep-reclaim has no trade file in
  the repo yet; London sweep families have zero clock overlap (different
  sessions). Owed before book admission, not before grading.
- Ledger rows 110-113 (default, no_target, cap30, be05-null).
NEXT: grading vs the 0.75 sleeve floor (PSR on the default), correlation
battery vs canon + live emissions, then Angus's book decision.

### Trial 6 — grading pack (2026-08-05, scripts/nya_ds_grade.py) — SLEEVE FLOOR PASS
Default spec (tournament survivor), $160-risk, 98 trade-days / 915 sessions:
- PSR(0) 0.986 vs the 0.75 sleeve floor — PASS. MTRL 512d vs 915 held —
  certifiable on its own track.
- DSR 0.000 under the merged ledger (113 trials) — carries the KNOWN
  ledger-denominator inflation caveat (Brake fix pending); per standing
  rule the PSR floor governs sleeve verdicts meanwhile.
- Funded MC (12mo, 50K shell, 2K trail): P(bust) 0.1%, median +$1,032 —
  small additive sleeve, not a solo account.
- CORRELATIONS: canon union -0.017 (both-active -0.092, 19 days); IB fade
  union -0.013 (35 both-active days) — independent-to-slightly-negative
  vs everything live, AND the regime profile (23-24 strong) inverts the
  canon's. Genuine diversifier.
STATUS: sleeve-certified pending (a) redundancy gate vs Brake's
sweep-reclaim trade file (BLOCKED on Brake), (b) Angus's book decision.
2026 cell n=7 stays on the label. Ledger row 114.
