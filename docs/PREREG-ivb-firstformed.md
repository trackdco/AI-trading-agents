# PREREG — first-formed-extreme conditioning on nya-ivb-fadeB

Date: 2026-08-05. Filed BEFORE any data touch. Family: nya-ivb-fadeB
(validated sleeve, PSR 0.994). This is a §6.0 round-2 conditioning arm on the
already-open full-span event set — NOT a new holdout look, NOT a new family.

## Source + mechanism
MrZincx / Edgeful "IB by rejection" stat (research/transcripts/mrzincx/
SPEC-as-taught.md; credibility in research/findings/intake2-credibility.md):
the first-formed extreme of the NY initial balance holds and the
second-formed extreme breaks, ~72-79% of days (Edgeful, 6-month QQQ
lookbacks). Our fade WANTS the touched extreme to hold. Hypothesis: fades at
the FIRST-formed IB extreme are the aligned half of our event set; fades at
the second-formed extreme fight the break stat and should be the weak half.

## Test (declared)
- Data: nq_1m_master.parquet full span, existing default-spec trigger logic
  (30-min IB 09:30-10:00, touch window 10:00-10:30, stop 0.25xIB, target
  mid, no BE) — the exact geometry of the shipped-track spec, unchanged.
- Split variable: whether the touched extreme was the FIRST- or
  SECOND-formed extreme of the 09:30-10:00 IB. First-formed = the extreme
  whose final value was set at the earlier minute. Tie (both set same
  minute): excluded, count reported.
- Report per §5.10: n, WR, pts, $, PF per side, PER YEAR (no pooling), on
  both the 356 default trades and the 478 raw touches.
- Null: permutation of the first/second label within year cells (§5.12-9
  discipline, src/validation/permnull.py), 10k shuffles.
- Ledger: one trial row per split, merged machine ledger.

## Decision rule (declared)
- No bin decision off this split alone. If the first-formed side shows lift
  with year-level consistency AND permnull p < 0.05, the gated variant
  enters the round-2 tournament as a challenger alongside cap20-W120 and
  ib15 — displacement of the default only via §6.0 (PBO < 0.5 AND holdout).
- If the split shows nothing: banked as evidence, default untouched, no
  further first-formed arms without new prereg.

## Declared-but-not-run in this pass (round-2 tournament arms, need own runs)
- IB60 variant (his IB is 09:30-10:30; ours 09:30-10:00 — tournament had
  ib15, this adds ib60).
- Weekday-conditional base rates (his 8% deviation skip/invert rule) —
  computable from our own candles.
- SPY-QQQ alignment gate — DATA-BLOCKED (no SPY/QQQ feed in repo); noted,
  not testable now.
- Fixed-point BE+trail (his 35-50pt BE / 25-35pt trail) — exit-tournament
  arm only; BE already failed twice as R-based on this family, so this runs
  as a challenger with its own prereg line, not assumed.
