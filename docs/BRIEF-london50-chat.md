# BRIEF — THE LEVEL-INTERACTION FAMILY, seeded with LONDON 50 (NYA-LVL-01)

Date: 2026-08-05. Owner: THIS chat (program law: one strategy per chat;
Angus operates every stage gate; plain language always — he is not a
quant). Read docs/VALIDATION-PROCESS.md IN FULL before touching data —
it is the constitution (§5.9 rulings, §5.9.1 no-bin-off-raw, §5.10 data
cards, §5.11 checklist incl. -8 baseline sign-off and -9 deep-testing
standard, §5.12(+.1) canon map, §6.0 promotion law).

FAMILY IDENTITY (Angus 2026-08-05): this is ONE family with two layers —
the LEVEL-INTERACTION substrate (the general idea: the tape's behavior at
pre-known reference levels, the canon-frequency trigger universe,
~10-15/day) SEEDED by MrZincx's London 50 (the concrete taught mechanics
and the exact six-level core below). They are basically the same thing:
London 50 is a taught, specific instance of level interaction. Census the
taught six-level core FIRST (it is the as-taught anchor, §5.9.1); the
substrate GENERALIZATION is a declared extension — same event grammar
applied to additional lookahead-clean reference levels (overnight
18:00-04:00 high/low, prior RTH close, prior-week high/low; declare the
exact extension list in the prereg, run it AFTER Angus reads the core
card). Level TYPE is expected to be the first great discriminator —
record it on every event from birth.

## What this strategy is (source + spec)

MrZincx's "London 50" / Power of 50 — the highest-frequency raw trigger
set in the vault. FULL as-taught spec: research/transcripts/mrzincx/
SPEC-as-taught.md, MODEL 3 (read every word; quotes carry video IDs +
timestamps). Credibility: research/findings/intake2-credibility.md (small
anonymous channel, Edgeful + Lucid affiliate; his claimed 71-82% WR is
self-reported and unverified — test the mechanics, ignore the marketing).

Plain-language thesis: the premarket range's midpoint and extremes, and
the prior day's midpoint and extremes, act as the day's reference levels;
breakout chasers without a retest are trapped, and level touches are
fade-the-stop-hunt scalps.

THE SIX LEVELS (compute lookahead-clean):
- Premarket ("London") range: 04:00 -> 09:15 ET session high / low / 50%
  (fixed from 09:15; he draws with a Gann box on 15-min).
- Prior day range: 04:00 -> 20:00 ET prior-day high / low / 50% (fixed
  from prior 20:00).
He charts QQQ ext-hours and executes NQ — we compute levels on NQ candles
directly; DECLARE this as a spec translation in the prereg (a QQQ-derived
variant is a future arm, we hold no QQQ data).

AS-TAUGHT MECHANICS (both taught versions are census arms — never pick
one silently):
- Version A (original): break of level, then RETEST entry on a 15-min
  body close back at the level.
- Version B (current): raw TOUCH = entry, any of the six levels, 15-min
  wick touch.
- Stops, two taught readings (both arms): (a) 15-min close beyond the
  traded LEVEL (current teaching, ~16pt scale); (b) 15-min close beyond
  the range's far extreme (original, 3-5x bigger — Angus considers
  oversized stops disqualifying; flag sizes honestly).
- Targets: HE NEVER DEFINES ONE ("$50 profit... whatever tickles your
  fancy"). House declared exit arms at census: (i) next-level ladder (his
  stated ladder: hit London 50 -> target London high/low; hit PD 50 ->
  target PD high/low); (ii) fixed-point scalp equivalent; (iii) time exit.
  Declare exact parameters in the prereg BEFORE running.
- His v2 filters — census as ARMS, not assumptions: skip opening 15-min
  candle (his "45% of losses" claim — VERIFY it), skip closing candle,
  three-tap invalidation (a level dies directionally after 3 reactions;
  tap-counting timeframe is ambiguous — declare arms), 80/20 trend-side
  bias, usual stop ~11:00 (but census ALL RTH touches with time-of-day
  as a variable).

## Stage 1 order from Angus: BUILD THE RAW TRIGGER SET

- Span: FIT = 2025-06 -> 2026-07 ONLY (§5.11-9a; full flow + depth
  coverage; OOF = the six sealed 2023/24 months, single look, later).
- UNCAPPED (standing convention, Angus 2026-08-05): every touch of every
  level, sequential re-entries, no per-day caps, no trading-window cap —
  time-of-day is a recorded variable, not a filter. Expect THOUSANDS of
  events (~10-15/day is the design intent).
- Per event record at minimum: level type (6), touch direction, tap
  number at that level, clock, 15m-vs-1m touch granularity, distance
  from open, level age, gap context, outcome under each declared exit
  arm, MFE/MAE + t+5/15/30 checkpoints (§5.12-5 schema from birth —
  cheap to record now, mandatory later anyway).
- Raw card per §5.10 to research/FUNNEL.md: counts by level type, WR,
  pts, $, PF per exit arm per year-half — UGLY IS FINE AND EXPECTED
  (§5.9.1: no bin decisions off raw; the canon started ugly).
- PREREG FIRST: write docs/PREREG-level-interaction.md declaring all of the above
  BEFORE any data touch. Then census. Then STOP and hand Angus the card —
  he reads raw before any optimization begins (stage 2 is his call:
  flow/depth/conviction per §5.11-9c; note the depth archive covers
  08:00-10:29 ET, which overlaps his prime trading window beautifully,
  including level formation during premarket).

## Logistics
- Work a SEPARATE git branch (Brake precedent), push often; merge
  output/trial_ledger.parquet at sync points (shared DSR denominator,
  237 trials at time of writing) — every arm you run gets a ledger row.
- Known cousins for LATER redundancy gates (do not test now): Brake's
  london-level-trap-fade + sweep-reclaim; the NY-AM Daily Sweep family
  (1H swing raids). Different level sets/sessions, but the book must not
  double-count one edge twice.
- Machinery you may adapt (committed): scripts/nya_ibc_census_uncapped.py
  (uncapped sequential census pattern), scripts/nya_ib50_deep.py (deep
  round: in-trade flow/checkpoints/conviction), scripts/
  nya_ib50_diagnosis.py (winner-vs-loser discriminant + early-cut arms),
  src/validation/{permnull,pbo,dsr,trial_ledger}.py (the graders).
