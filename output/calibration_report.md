# Spec 1 — February 2026 calibration report

Engine run: **W1 (08:00–11:00) / E1 (limit at BB basis) / V0 (set-and-forget)**, Feb 2–27 2026, strategy-definition-v1.1.

Match key: (date, direction, entry time ±15 min), OPEN-clock (engine trigger_ts − TF vs hand entry time). **No tuning** — divergences are reported, not fixed (spec-1 Step 8 / code-standards §5).

| bucket | count |
|---|---|
| reference (hand) trades | 28 |
| engine trades | 20 |
| **MATCHED** | 4 |
| **MISSED** (hand took, engine didn't) | 24 |
| **EXTRA** (engine took, hand didn't) | 16 |

## Headline patterns (observations, not fixes)

Nearest gate on each MISSED reference trade (what stopped the engine from taking a trade Angus took):

- **vetoed_confluence** × 13
- **vetoed_halt** × 4
- **vetoed_rr_floor** × 2
- **cancelled_tcancel** × 2
- **vetoed_bb_vwap** × 1
- **vetoed_news_preopen** × 1
- **skipped_position_open** × 1

Reading (for Angus to rule, not for the engine to self-correct):

- **`vetoed_confluence` dominates.** In several cases the engine detected the *same* trigger Angus took (same time/TF/pattern) but counted only 2 confluence types and the §7 minimum for counter-trend is 3. This collides with the v1.1 sizing ladder (§9), which treats a 2-type **BB+VWAP** cluster as *tradeable at half size*. **Do the type-ladder and the §7 count-minimum STACK (both must pass) or does the ladder SUPERSEDE the count for counter-trend?** Decision-log says the ladder "refines §7/§9" — needs an explicit ruling; it is the biggest single driver of MISSED.
- **`vetoed_halt` is a cascade.** The engine takes EXTRA early losers, trips the §10 2-loss / −2R daily halt, then MISSES Angus's later winners on the same day (Feb 12, 17). Fewer EXTRA entries would remove most halt-blocks — i.e. this is downstream of the confluence/selection question, not an independent halt problem.
- **`vetoed_news_preopen` × Feb 20 08:06** is the tightened news rule vetoing Angus's own pre-PCE entry (open item P5.14 — strict FF-red vs named-list ruling decides it).

## MATCHED

| date | dir | Δopen | hand (TF/pat, R, exit) | engine (TF/pat, entry/stop/tgt, R, exit) |
|---|---|---|---|---|
| 2026-02-02 | short | 1m | 2M A, +0.00R, BE stopped | 3min A | entry 25856.75 stop 25873.25 target 25735.50 | -0.87R stop |
| 2026-02-04 | short | 3m | 5M B2, +3.30R, target hit | 3min B2 | entry 25361.25 stop 25346.00 target 25329.00 | -0.40R stop |
| 2026-02-18 | short | 8m | 3M B2, -1.00R, stop hit | 2min B2 | entry 24849.75 stop 24826.25 target 24811.00 | -0.12R stop |
| 2026-02-19 | short | 0m | 5M B, -0.35R, discretionary close | 3min unclassified | entry 24849.75 stop 24866.00 target 24800.50 | -1.02R stop |

## MISSED — reference trades the engine did not take

For each: the nearest rejected trigger (same date+direction) and which gate stopped it. `window_gates` tallies every verdict within ±15 min.

- **2026-02-03 long 2M 10:52** (A, -1.00R, stop hit; news=No)
  - nearest trigger: 10:52 1min unclassified → **vetoed_halt** (daily halt active (§10)) — 0m away
  - gates within ±15m: vetoed_halt×9

- **2026-02-04 short 5M 10:30** (B2, +3.57R, target hit; news=Yes)
  - nearest trigger: 10:30 1min B → **vetoed_rr_floor** (RR 0.24 < 2.0 (target prior_day_low)) — 0m away
  - gates within ±15m: vetoed_rr_floor×4, vetoed_halt×3, cancelled_tcancel×2, vetoed_bad_geometry×2

- **2026-02-05 long 2M 09:36** (A, +2.15R, target hit; news=Yes)
  - nearest trigger: 09:36 2min A → **vetoed_confluence** (confluence 2 < 3 (counter_trend)) — 0m away
  - gates within ±15m: vetoed_confluence×4

- **2026-02-06 short 5M 10:10** (A, -1.00R, stop hit; news=Yes)
  - nearest trigger: 10:10 5min B2 → **vetoed_bb_vwap** (cluster ['poc', 'vwap'] lacks BB+VWAP (§9 v1.1 no-trade)) — 0m away
  - gates within ±15m: vetoed_confluence×10, vetoed_bb_vwap×2, vetoed_rr_floor×1, cancelled_tcancel×1

- **2026-02-06 long 5M 10:20** (B2, +2.62R, target hit; news=Yes)
  - nearest trigger: 10:20 2min A → **vetoed_confluence** (confluence 2 < 3 (counter_trend)) — 0m away
  - gates within ±15m: vetoed_confluence×11

- **2026-02-09 long 1M 09:36** (A, +3.31R, target hit; news=No)
  - nearest trigger: 09:36 1min unclassified → **cancelled_tcancel** (price ran 22.0 pts beyond limit unfilled) — 0m away
  - gates within ±15m: vetoed_confluence×6, cancelled_tcancel×1, vetoed_rr_floor×1

- **2026-02-10 long 2M 10:34** (B2, -1.00R, stop hit; news=Yes)
  - nearest trigger: 10:36 1min unclassified → **vetoed_confluence** (confluence 2 < 3 (range)) — 2m away
  - gates within ±15m: vetoed_confluence×8, vetoed_bad_geometry×2, vetoed_rr_floor×1

- **2026-02-11 short 3M 09:48** (A, +5.98R, target hit; news=Yes)
  - nearest trigger: 09:48 3min A → **vetoed_confluence** (confluence 2 < 3 (counter_trend)) — 0m away
  - gates within ±15m: vetoed_confluence×9, skipped_position_open×1, cancelled_tcancel×1

- **2026-02-12 short 2M 09:40** (A, +3.37R, target hit; news=Yes)
  - nearest trigger: 09:40 5min B → **vetoed_halt** (daily halt active (§10)) — 0m away
  - gates within ±15m: vetoed_halt×5, vetoed_confluence×3

- **2026-02-13 long 3M 09:33** (B2, -1.00R, stop hit; news=Yes)
  - nearest trigger: 09:30 1min A → **vetoed_rr_floor** (RR 1.61 < 2.0 (target data_extreme_CPI)) — 3m away
  - gates within ±15m: vetoed_rr_floor×3, vetoed_confluence×3

- **2026-02-17 long 1M 09:32** (B, +3.69R, target hit; news=Yes)
  - nearest trigger: 09:32 2min unclassified → **vetoed_halt** (daily halt active (§10)) — 0m away
  - gates within ±15m: vetoed_halt×10

- **2026-02-17 short 2M 09:50** (A, +3.88R, target hit; news=Yes)
  - nearest trigger: 09:50 2min unclassified → **vetoed_halt** (daily halt active (§10)) — 0m away
  - gates within ±15m: vetoed_halt×10

- **2026-02-18 short 5M 08:35** (B2, +4.17R, target hit; news=No)
  - nearest trigger: 08:35 5min unclassified → **vetoed_confluence** (confluence 2 < 3 (range)) — 0m away
  - gates within ±15m: vetoed_confluence×5

- **2026-02-18 long 1M 09:53** (B, +4.78R, target hit; news=No)
  - nearest trigger: 09:52 1min B → **vetoed_confluence** (confluence 2 < 3 (counter_trend)) — 1m away
  - gates within ±15m: vetoed_confluence×8, vetoed_bad_geometry×2, vetoed_rr_floor×2

- **2026-02-20 long 3M 08:06** (A, +4.79R, target hit; news=Yes)
  - nearest trigger: 07:55 5min unclassified → **vetoed_news_preopen** (high-impact day (release 08:30:00) -> whole pre-market blocked until 09:30) — 11m away
  - gates within ±15m: vetoed_window×4, vetoed_news_preopen×1

- **2026-02-20 long 1M 09:31** (A, +3.18R, target hit; news=Yes)
  - nearest trigger: 09:30 1min A → **vetoed_confluence** (confluence 2 < 3 (counter_trend)) — 1m away
  - gates within ±15m: vetoed_confluence×8

- **2026-02-20 long 3M 10:33** (B2, +3.22R, target hit; news=Yes)
  - nearest trigger: 10:35 5min B → **vetoed_confluence** (confluence 2 < 3 (counter_trend)) — 2m away
  - gates within ±15m: vetoed_confluence×12

- **2026-02-23 short 5M 10:20** (B, +2.74R, target hit; news=No)
  - nearest trigger: 10:20 2min unclassified → **vetoed_confluence** (confluence 2 < 3 (range)) — 0m away
  - gates within ±15m: vetoed_confluence×7, vetoed_bb_vwap×1

- **2026-02-24 long 5M 08:20** (B, +3.67R, target hit; news=No)
  - nearest trigger: 08:20 2min B2 → **skipped_position_open** (one position at a time (§5.6)) — 0m away
  - gates within ±15m: skipped_position_open×10

- **2026-02-24 long 5M 10:10** (B2, +4.28R, target hit; news=No)
  - nearest trigger: 10:09 3min A → **vetoed_confluence** (confluence 2 < 3 (counter_trend)) — 1m away
  - gates within ±15m: vetoed_confluence×12

- **2026-02-25 long 5M 09:25** (B2, +12.98R, target hit; news=No)
  - nearest trigger: 09:25 5min B2 → **cancelled_tcancel** (price ran 22.0 pts beyond limit unfilled) — 0m away
  - gates within ±15m: cancelled_tcancel×2, vetoed_rr_floor×2, vetoed_bad_geometry×2

- **2026-02-26 short 3M 09:18** (A, +4.22R, target hit; news=Yes)
  - nearest trigger: 09:18 3min unclassified → **vetoed_confluence** (confluence 2 < 3 (range)) — 0m away
  - gates within ±15m: vetoed_confluence×16

- **2026-02-27 long 5M 09:40** (A, -1.00R, stop hit; news=Yes)
  - nearest trigger: 09:40 1min A → **vetoed_confluence** (confluence 2 < 3 (counter_trend)) — 0m away
  - gates within ±15m: vetoed_confluence×12

- **2026-02-27 long 3M 09:54** (A, +4.62R, target hit; news=Yes)
  - nearest trigger: 09:55 5min A → **vetoed_confluence** (confluence 2 < 3 (counter_trend)) — 1m away
  - gates within ±15m: vetoed_confluence×11

## EXTRA — engine trades Angus did not take

| date | dir | open | engine (TF/pat, entry/stop/tgt, R, exit) |
|---|---|---|---|
| 2026-02-02 | short | 10:48 | 3min A | entry 25866.00 stop 25867.00 target 25735.50 | -0.07R stop |
| 2026-02-03 | short | 08:17 | 1min B | entry 25997.00 stop 25995.75 target 25952.00 | -0.05R stop |
| 2026-02-03 | short | 08:20 | 1min B | entry 25992.00 stop 25995.25 target 25952.00 | -1.08R stop |
| 2026-02-04 | long | 10:42 | 1min A | entry 25202.25 stop 25216.50 target 25245.25 | -0.33R stop |
| 2026-02-05 | long | 10:54 | 2min unclassified | entry 24607.00 stop 24595.50 target 24705.00 | -0.85R stop |
| 2026-02-09 | short | 09:56 | 2min unclassified | entry 25115.25 stop 25149.00 target 24971.00 | -0.61R stop |
| 2026-02-11 | long | 09:52 | 1min B2 | entry 25377.50 stop 25360.75 target 25444.75 | -0.78R stop |
| 2026-02-12 | short | 08:30 | 2min A | entry 25355.25 stop 25353.25 target 25318.25 | -0.10R stop |
| 2026-02-12 | long | 09:40 | 1min unclassified | entry 25361.50 stop 25355.75 target 25417.25 | -0.80R stop |
| 2026-02-17 | short | 08:30 | 5min B | entry 24603.50 stop 24610.50 target 24560.75 | -0.97R stop |
| 2026-02-17 | short | 08:45 | 5min B | entry 24624.25 stop 24610.25 target 24560.75 | -0.02R stop |
| 2026-02-19 | short | 09:25 | 5min B | entry 24857.50 stop 24872.00 target 24800.50 | -0.70R stop |
| 2026-02-24 | long | 08:00 | 2min B | entry 24823.25 stop 24814.25 target 24885.75 | +6.76R target |
| 2026-02-25 | long | 10:26 | 2min B2 | entry 25321.00 stop 25304.50 target 25359.25 | -1.02R stop |
| 2026-02-25 | short | 10:42 | 2min A | entry 25311.50 stop 25315.75 target 25293.75 | +4.18R target |
| 2026-02-27 | short | 09:42 | 3min B2 | entry 24856.50 stop 24864.00 target 24796.25 | -0.49R stop |

## For Angus — the GATE

Rule every MISSED and EXTRA: *"my setup, I missed it"* (accept the divergence) vs *"not my setup — detector too loose"* (tighten a rule, with an approved hypothesis + out-of-sample check + doc bump; never tuned to February).
