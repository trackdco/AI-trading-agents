# BRIEF — VWAP ROTATION FADE, RTH (NYA-VWR-01)

Date: 2026-08-05. Owner: THIS chat (program law: one strategy per chat;
Angus operates every stage gate; plain language always — he is not a
quant). Read docs/VALIDATION-PROCESS.md IN FULL before touching data —
it is the constitution (§5.9 rulings, §5.9.1 no-bin-off-raw, §5.10 data
cards, §5.11 checklist incl. -8 baseline sign-off and -9 deep-testing
standard, §5.12(+.1) canon map, §6.0 promotion law).

## What this strategy is (source + spec)

Orochi Trading's VWAP standard-deviation rotation fade — his most
mechanical VWAP teaching. FULL corrected as-taught specs:
research/transcripts/orochi/RESPEC-as-taught-2026-08-05.md, SPEC 1
(regime-gated sd2 fade) and SPEC 3 (the retest + compound-add grammar —
the most mechanical single sequence in his corpus). Credibility:
research/findings/orochi-credibility.md (anonymous, unverified — test
mechanics, ignore claims). HISTORY WARNING: this family's OVERNIGHT
cousin was tested and parked today (research/candidates/nyo-rotation.md,
trials 3-4: corrected grammar ran WORSE than a strawman overnight). THIS
chat tests the RTH version — his actual primary session — which is
untested. The overnight failure is context, not fate; but read it.

Plain-language thesis: when a session is rotating inside its own value
(no acceptance beyond the value area), a stretch to the second standard
deviation band of the session VWAP is an over-extension — the chasers
who bought the stretch are offside against a mean the whole session's
volume agrees on, and price tends to travel back.

THE INSTRUMENT (his exact definition, IMs472GOwnY): session-anchored
VWAP (RTH anchor 09:30 for this chat — DECLARE it; his NQ examples used
the Globex daily anchor, an 18:00-anchor variant is a declared arm),
volume-weighted sigma bands: +/-1 sigma = the value area, +/-2 sigma =
the rotational extreme. Bands DEVELOP (move) through the session. Skip
the first 10-15 minutes (his warm-up exclusion — declare exact).

AS-TAUGHT MECHANICS (all census arms, never silently pick one):
- EVENT: price reaches the +/-2 sigma band while the session is
  "rotational within value" — his hard gate, stated three ways in SPEC 1
  §5: no acceptance established beyond either +/-1 sigma edge this
  session. Acceptance definition is HIS gap — declared arms: 1 close
  beyond edge does NOT kill / N=2-3 consecutive closes = acceptance
  (kills the gate) / time-based.
- ENTRY arms (D1): (a) fade the first sd2 touch; (b) wick beyond sd2 +
  close back inside; (c) his sweep-case literal: re-entry into the
  +/-1 sigma band. PLUS the SPEC-3 grammar as its own arm: first
  rejection -> RETEST entry (1/3 risk) -> add remaining 2/3 on
  acceptance-back-inside after a shallow poke out.
- STOP: NEVER TAUGHT anywhere in the corpus (SPEC 1 §3 flag) — house
  declared arms only, and per Angus's standing rule: NO oversized stops;
  declare capped arms (sigma-fraction and fixed-point caps) from birth.
- TARGETS (taught, both arms): (a) the mean (developing VWAP);
  (b) opposite +/-1 sigma edge. POC/VWAP-interrupt scratch declared.
- Uncapped (standing convention): every qualifying sd2 reach, sequential
  re-entries, no per-day caps. Time-of-day recorded, not filtered.

## Stage 1 order from Angus: BUILD THE RAW TRIGGER SET

- Span: FIT = 2025-06 -> 2026-07 ONLY (§5.11-9a; full flow 24h + depth
  08:00-10:29 ET coverage; OOF = the six sealed 2023/24 months, single
  look, later). RTH sessions 09:30-16:00.
- Expect ~1-3 qualifying touches/day ungated (more uncapped) — a few
  hundred to ~800 events. Record per event: side, sd2 distance, regime
  state (which acceptance arm), VWAP slope, session clock, tap number,
  MFE/MAE + t+5/15/30 checkpoints (§5.12-5 from birth), gap context,
  outcome per declared exit arm.
- Raw card per §5.10 to research/FUNNEL.md: counts, WR, pts, $, PF per
  arm per year-half. UGLY IS FINE (§5.9.1) — no bin off raw.
- PREREG FIRST: docs/PREREG-vwap-rotation.md declaring everything above
  BEFORE any data touch. Then census. Then STOP — hand Angus the card;
  stage 2 (flow/depth/conviction/in-trade per §5.11-9c) is his call.

## Logistics
- SEPARATE git branch, push often; merge output/trial_ledger.parquet at
  sync points (shared DSR denominator, 237 trials at writing) — every
  arm gets a ledger row.
- Parallel chats live: chat 1 = IB Complex (NYA-IBC-01), chat 2 =
  level-interaction/London 50 (NYA-LVL-01). Redundancy gates at book
  stage; no shared files except ledger/FUNNEL merges.
- Machinery to adapt (committed): scripts/nyo_rotation_respec.py (VWAP
  band computation + the V-A/V-B grammars — overnight version),
  scripts/nya_ibc_census_uncapped.py (uncapped sequential pattern),
  scripts/nya_ib50_deep.py + nya_ib50_diagnosis.py (deep round +
  winner/loser discriminant + early-cut arms),
  src/validation/{permnull,pbo,dsr,trial_ledger}.py (graders).
