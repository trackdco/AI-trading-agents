# PREREG — failed-auction: balance-break fail/succeed event tree (dual-sourced)

Committed BEFORE any census or test touches data. Family: NYA-FA-01.
Sources: research/findings/orochi-diagnosis.md (F2+F3 — the flagship, "80%
rule"); research/findings/fabervaale-diagnosis.md (FAB-5, FAB-9 — his
failed-auction and double-absorption breakout anticipation); both extraction
files. The ONE setup both independent intakes teach, with the same
trapped-counterparty story. Program: NY-AM. Owner: Claude; verdicts to Angus.

## Thesis (plain language)

Price breaks out of an established balance (value area). Two futures exist:
the break gets ACCEPTED (trend; the balance's other side becomes the fade
crowd's graveyard) or it FAILS (price re-enters value; the breakout chasers
are trapped and their forced exit fuels a traverse to the other side of the
balance). Everyone teaches both trades; nobody defines the discriminator —
"time and space", "acceptance", vibes. Our program: measure the discriminator
mechanically, with order flow at the break as the main instrument. The
published record says the folklore number is fake (traverse 27-67%, not 80%)
and the geometry alone dies at costs — so the edge, if any, lives in the
discriminator, exactly where our data has an advantage nobody published.

## Declared universe and spans

- Balance definition (frozen for this prereg): a run of >= 2 consecutive
  sessions whose value areas (amt_days.parquet, 70% TPO) OVERLAP; the
  composite = union of those sessions' profiles; composite VAH/VAL = value
  area of the merged TPO stack. Computed by an extension to
  scripts/amt_substrate.py (committed before census).
- Break event: first 1-min close outside composite VAH/VAL during RTH,
  09:30-15:00, while a composite of age >= 2 days exists.
- Resolution windows (declared): 30/60/120 min post-break.
- FAIL event: 1-min close back inside the composite within the window.
  ACCEPT event: no re-entry close within the window.
- Spans: full 2023-2026 for candles; flow arms on flow span. Era discipline
  and sealed-holdout rules identical to PREREG-fab-ivb.

## L0 census

1. Break frequency, direction split, by composite age/size.
2. P(fail) vs P(accept) per resolution window — the base rates.
3. Post-FAIL: traverse completion rate to opposite edge (the "80%" measured
   honestly), time-to-traverse, POC-interrupt rate.
4. Post-ACCEPT: continuation distance vs the IB/trend stats.

## Kill classes

- K1 premise kill (L0): traverse-after-fail completion shows no edge over
  the unconditional base both eras.
- K2 era-flip kill per arm.
- K3 expectancy kill ONLY after the full discriminator search completes
  (§3.2). The discriminator search IS the family's core test.
- Cost stack: base + strict, same as fab-ivb.

## Declared discriminator variables (the search)

Candles: time spent outside before re-entry; extension distance beyond the
edge; bar count outside; poor/strong structure at the extreme (single-print
taper vs flat); session clock of the break.
Flow (flow span): delta of the break bar and the outside excursion;
absorption AT the composite edge on re-entry (P7 library); CVD divergence
during the outside excursion (his Dec-30 pattern generalized); trapped-volume
estimate (volume transacted outside that is now offside).
Depth (heatmap span): wall state at the broken edge; fresh-liquidity reload
behind the break (FAB-8) vs empty book.

## Entry expressions (declared, tested only on surviving branches)

FAIL side: enter on the re-entry close toward the opposite edge; retest-of-
edge entry variant. ACCEPT side: retest-of-broken-edge continuation entry.
Stops: beyond the failure extreme / beyond the reload wall; exit arms
declared at L1 and frozen after tournament.

## Redundancy gates

- vs nypre-gap-engine (shelved): different mechanism (gap fill vs balance
  traverse) but both mean-revert toward a reference — pairwise check when a
  book exists.
- vs Brake's NY candidates and london-level-trap-fade (sweep cousin) — via
  shared vault emissions.

## Promotion rule (declared 2026-08-05, BEFORE any exit tournament — §6.0 law)

- Fail-branch DEFAULT SPEC by mechanism prior: deep-excursion cohort (trapped
  mass), G2 excursion-delta gate (the chase wasn't paid — counterparty
  confirmation), S2 half-excursion stop (MAE-derived geometry), target
  min(POC, 0.5 width), time-stop 15:55. This default was fixed by mechanism
  reasoning at trial 3, before the tournament.
- The exit tournament may test declared arms; an alternative arm DISPLACES the
  default only if PBO (CSCV, day-level, all arms) < 0.5 AND the alternative
  survives the candidate's holdout adjudication. In-sample rank never
  promotes.
- Accept-branch default: A1 retest entry, 1.0-width target; same displacement
  rule.
- Family promotion to grading requires: era-consistent positive at base
  friction on the default spec, all trials recorded in the MERGED machine
  ledger (output/trial_ledger.parquet), correlation battery vs canon + all
  live emissions passed.

## Trial ledger

research/candidates/nya-failed-auction.md (narrative) AND
output/trial_ledger.parquet via src/validation/trial_ledger.py (the number
the gate reads — §6.0). All arms count; deflation merged with Brake's NY
program.
