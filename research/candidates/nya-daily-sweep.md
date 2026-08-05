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
