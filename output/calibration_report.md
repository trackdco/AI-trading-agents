# Spec 1 — February 2026 calibration report

Engine run: **W1 (08:00–11:00) / E1 (limit at BB basis) / V0 (set-and-forget)**, Feb 2–27 2026, strategy-definition-v1.1.

Match key: (date, direction, entry time ±15 min), OPEN-clock (engine trigger_ts − TF vs hand entry time). **No tuning** — divergences are reported, not fixed (spec-1 Step 8 / code-standards §5).

| bucket | count |
|---|---|
| reference (hand) trades | 28 |
| engine trades | 44 |
| **MATCHED** | 6 |
| **MISSED** (hand took, engine didn't) | 22 |
| **EXTRA** (engine took, hand didn't) | 38 |

## Headline patterns (observations, not fixes)

Nearest gate on each MISSED reference trade (what stopped the engine from taking a trade Angus took):

- **vetoed_rr_floor** × 7
- **cancelled_tcancel** × 4
- **vetoed_min_stop** × 3
- **vetoed_halt** × 2
- **vetoed_bb_vwap** × 2
- **skipped_position_open** × 2
- **vetoed_vault_max** × 1
- **vetoed_news_preopen** × 1

Reading (v1.2 run — for Angus to rule, not for the engine to self-correct):

- **The v1.1 confluence blocker is resolved** (P5.15 ruled: BB+VWAP gate, POC bonus, no 3-count minimum). The MISSED mix is now spread across execution/risk gates rather than one dominant selection rule.
- **`vetoed_halt` is a cascade, not an independent problem.** The engine takes EXTRA early losers, trips the §10 2-loss / −2R daily halt, then misses Angus's later winners the same day. Fewer bad EXTRA entries would clear most of these.
- **`vetoed_rr_floor`** now ties for the top MISSED gate: on these setups the engine's target menu offers < 2R to the actual level where Angus saw ≥ 2R — target-selection divergence (menu contents / level choice), not a sizing question.
- **`cancelled_tcancel`** kills several of Angus's winners: price ran > T_cancel (22) beyond the limit before filling. His fills chase further than the current band.
- **`vetoed_news_preopen` × Feb 20 08:06** is the tightened news rule vetoing Angus's own pre-PCE entry (open item P5.14 — strict FF-red vs named-list ruling decides it).

## MATCHED

| date | dir | Δopen | hand (TF/pat, R, exit) | engine (TF/pat, entry/stop/tgt, R, exit) |
|---|---|---|---|---|
| 2026-02-02 | short | 7m | 2M A, +0.00R, BE stopped | 5min B | entry 25864.25 stop 25875.25 target 25648.25 | -1.02R stop |
| 2026-02-04 | short | 8m | 5M B2, +3.30R, target hit | 1min B | entry 25336.50 stop 25353.75 target 25221.50 | -0.57R stop |
| 2026-02-06 | short | 10m | 5M A, -1.00R, stop hit | 5min B2 | entry 24885.50 stop 24905.00 target 24703.25 | -0.35R stop |
| 2026-02-09 | long | 12m | 1M A, +3.31R, target hit | 3min B | entry 25063.50 stop 25044.00 target 25118.25 | -1.01R stop |
| 2026-02-11 | short | 2m | 3M A, +5.98R, target hit | 1min B | entry 25397.00 stop 25436.75 target 25241.25 | +3.92R target |
| 2026-02-24 | long | 8m | 5M B2, +4.28R, target hit | 2min A | entry 24840.50 stop 24835.25 target 24870.50 | +2.86R target |

## MISSED — reference trades the engine did not take

For each: the nearest rejected trigger (same date+direction) and which gate stopped it. `window_gates` tallies every verdict within ±15 min.

- **2026-02-03 long 2M 10:52** (A, -1.00R, stop hit; news=No)
  - nearest trigger: 10:52 1min unclassified → **vetoed_halt** (daily halt active (§10)) — 0m away
  - gates within ±15m: vetoed_halt×9

- **2026-02-04 short 5M 10:30** (B2, +3.57R, target hit; news=Yes)
  - nearest trigger: 10:30 1min B → **vetoed_vault_max** (max trades/day reached (§10)) — 0m away
  - gates within ±15m: vetoed_vault_max×11

- **2026-02-05 long 2M 09:36** (A, +2.15R, target hit; news=Yes)
  - nearest trigger: 09:36 2min A → **cancelled_tcancel** (price ran 22.0 pts beyond limit unfilled) — 0m away
  - gates within ±15m: cancelled_tcancel×3, vetoed_rr_floor×1

- **2026-02-06 long 5M 10:20** (B2, +2.62R, target hit; news=Yes)
  - nearest trigger: 10:20 2min A → **vetoed_rr_floor** (RR 1.44 < 2.0 (target data_high_UoM Consumer Sen_10:00)) — 0m away
  - gates within ±15m: vetoed_rr_floor×5, vetoed_bb_vwap×4, vetoed_min_stop×2

- **2026-02-10 long 2M 10:34** (B2, -1.00R, stop hit; news=Yes)
  - nearest trigger: 10:36 1min unclassified → **vetoed_bb_vwap** (cluster ['poc', 'vwap'] lacks BB+VWAP (§9 v1.1 no-trade)) — 2m away
  - gates within ±15m: vetoed_bb_vwap×6, cancelled_tcancel×2, vetoed_rr_floor×2, vetoed_min_stop×1

- **2026-02-12 short 2M 09:40** (A, +3.37R, target hit; news=Yes)
  - nearest trigger: 09:40 5min B → **vetoed_rr_floor** (RR 0.86 < 2.0 (target london_session_low)) — 0m away
  - gates within ±15m: vetoed_rr_floor×3, cancelled_tcancel×2, vetoed_bb_vwap×2, vetoed_min_stop×1

- **2026-02-13 long 3M 09:33** (B2, -1.00R, stop hit; news=Yes)
  - nearest trigger: 09:30 1min A → **vetoed_rr_floor** (RR 1.55 < 2.0 (target data_extreme_CPI)) — 3m away
  - gates within ±15m: vetoed_rr_floor×5, vetoed_bb_vwap×1

- **2026-02-17 long 1M 09:32** (B, +3.69R, target hit; news=Yes)
  - nearest trigger: 09:32 2min unclassified → **vetoed_min_stop** (stop 4.25 pts < 6 minimum (§5 v1.2)) — 0m away
  - gates within ±15m: vetoed_min_stop×4, vetoed_bb_vwap×3, vetoed_rr_floor×2, skipped_position_open×1

- **2026-02-17 short 2M 09:50** (A, +3.88R, target hit; news=Yes)
  - nearest trigger: 09:50 2min unclassified → **cancelled_tcancel** (price ran 22.0 pts beyond limit unfilled) — 0m away
  - gates within ±15m: cancelled_tcancel×6, vetoed_rr_floor×2, vetoed_min_stop×2

- **2026-02-18 short 5M 08:35** (B2, +4.17R, target hit; news=No)
  - nearest trigger: 08:35 5min unclassified → **vetoed_bb_vwap** (cluster ['bb', 'poc'] lacks BB+VWAP (§9 v1.1 no-trade)) — 0m away
  - gates within ±15m: vetoed_bb_vwap×5

- **2026-02-18 short 3M 09:42** (B2, -1.00R, stop hit; news=No)
  - nearest trigger: 09:48 2min B → **vetoed_rr_floor** (RR -0.02 < 2.0 (target london_session_low)) — 6m away
  - gates within ±15m: vetoed_rr_floor×3, vetoed_min_stop×3, vetoed_bb_vwap×1

- **2026-02-18 long 1M 09:53** (B, +4.78R, target hit; news=No)
  - nearest trigger: 09:52 1min B → **vetoed_rr_floor** (RR 0.08 < 2.0 (target asia_session_high)) — 1m away
  - gates within ±15m: vetoed_rr_floor×10, cancelled_tcancel×1, vetoed_min_stop×1

- **2026-02-19 short 5M 09:00** (B, -0.35R, discretionary close; news=Yes)
  - nearest trigger: 09:00 3min unclassified → **vetoed_halt** (daily halt active (§10)) — 0m away
  - gates within ±15m: vetoed_halt×7

- **2026-02-20 long 3M 08:06** (A, +4.79R, target hit; news=Yes)
  - nearest trigger: 07:55 5min unclassified → **vetoed_news_preopen** (high-impact day (release 08:30:00) -> whole pre-market blocked until 09:30) — 11m away
  - gates within ±15m: vetoed_window×4, vetoed_news_preopen×1

- **2026-02-20 long 1M 09:31** (A, +3.18R, target hit; news=Yes)
  - nearest trigger: 09:30 1min A → **cancelled_tcancel** (price ran 22.0 pts beyond limit unfilled) — 1m away
  - gates within ±15m: vetoed_bb_vwap×4, cancelled_tcancel×2, vetoed_rr_floor×2

- **2026-02-20 long 3M 10:33** (B2, +3.22R, target hit; news=Yes)
  - nearest trigger: 10:35 5min B → **vetoed_rr_floor** (RR 0.15 < 2.0 (target london_session_high)) — 2m away
  - gates within ±15m: vetoed_rr_floor×9, vetoed_min_stop×3

- **2026-02-23 short 5M 10:20** (B, +2.74R, target hit; news=No)
  - nearest trigger: 10:20 2min unclassified → **cancelled_tcancel** (price ran 22.0 pts beyond limit unfilled) — 0m away
  - gates within ±15m: vetoed_vault_max×4, cancelled_tcancel×2, vetoed_min_stop×1, vetoed_bb_vwap×1

- **2026-02-24 long 5M 08:20** (B, +3.67R, target hit; news=No)
  - nearest trigger: 08:20 2min B2 → **skipped_position_open** (one position at a time (§5.6)) — 0m away
  - gates within ±15m: skipped_position_open×10

- **2026-02-25 long 5M 09:25** (B2, +12.98R, target hit; news=No)
  - nearest trigger: 09:25 5min B2 → **vetoed_min_stop** (stop 1.00 pts < 6 minimum (§5 v1.2)) — 0m away
  - gates within ±15m: vetoed_min_stop×2, cancelled_tcancel×2, skipped_order_working×1, vetoed_rr_floor×1

- **2026-02-26 short 3M 09:18** (A, +4.22R, target hit; news=Yes)
  - nearest trigger: 09:18 3min unclassified → **skipped_position_open** (one position at a time (§5.6)) — 0m away
  - gates within ±15m: skipped_position_open×11, vetoed_bb_vwap×5

- **2026-02-27 long 5M 09:40** (A, -1.00R, stop hit; news=Yes)
  - nearest trigger: 09:40 1min A → **vetoed_min_stop** (stop 0.75 pts < 6 minimum (§5 v1.2)) — 0m away
  - gates within ±15m: vetoed_rr_floor×7, vetoed_min_stop×5

- **2026-02-27 long 3M 09:54** (A, +4.62R, target hit; news=Yes)
  - nearest trigger: 09:55 5min A → **vetoed_rr_floor** (RR 1.77 < 2.0 (target daily_vwap_mid)) — 1m away
  - gates within ±15m: vetoed_rr_floor×5, vetoed_min_stop×4, cancelled_tcancel×2

## EXTRA — engine trades Angus did not take

| date | dir | open | engine (TF/pat, entry/stop/tgt, R, exit) |
|---|---|---|---|
| 2026-02-02 | short | 08:14 | 2min A | entry 25494.00 stop 25501.75 target 25402.50 | -1.03R stop |
| 2026-02-03 | short | 08:20 | 1min B | entry 25989.00 stop 25995.25 target 25952.00 | -1.04R stop |
| 2026-02-03 | long | 08:24 | 3min B | entry 25991.00 stop 25976.00 target 26021.50 | -1.02R stop |
| 2026-02-04 | long | 09:25 | 5min B | entry 25308.25 stop 25356.25 target 25507.00 | -0.01R stop |
| 2026-02-04 | long | 09:45 | 5min A | entry 25294.00 stop 25292.00 target 25378.25 | -0.11R stop |
| 2026-02-05 | short | 10:48 | 3min unclassified | entry 24623.25 stop 24620.00 target 24561.00 | -0.02R stop |
| 2026-02-05 | short | 10:52 | 1min B | entry 24616.75 stop 24625.50 target 24561.00 | -0.43R stop |
| 2026-02-05 | long | 10:52 | 2min unclassified | entry 24598.25 stop 24595.00 target 24705.00 | -0.27R stop |
| 2026-02-06 | short | 10:50 | 5min B | entry 24872.00 stop 24912.75 target 24616.25 | -0.78R stop |
| 2026-02-09 | short | 09:18 | 3min B | entry 25064.25 stop 25073.50 target 24971.00 | -1.03R stop |
| 2026-02-10 | short | 09:32 | 2min A | entry 25375.00 stop 25394.00 target 25304.00 | +3.74R target |
| 2026-02-10 | short | 10:36 | 2min unclassified | entry 25401.75 stop 25410.25 target 25294.75 | -0.52R stop |
| 2026-02-10 | short | 10:50 | 2min unclassified | entry 25394.50 stop 25404.50 target 25294.75 | +9.07R target |
| 2026-02-11 | long | 09:30 | 3min A | entry 25405.50 stop 25397.25 target 25438.75 | -1.03R stop |
| 2026-02-11 | long | 09:32 | 2min A | entry 25386.50 stop 25395.25 target 25434.00 | -0.02R stop |
| 2026-02-12 | long | 09:40 | 1min unclassified | entry 25361.50 stop 25355.75 target 25417.25 | -0.80R stop |
| 2026-02-12 | long | 10:22 | 1min B | entry 25223.25 stop 25194.00 target 25317.75 | -0.73R stop |
| 2026-02-13 | long | 09:54 | 2min B | entry 24692.25 stop 24728.50 target 24820.75 | -0.02R stop |
| 2026-02-13 | short | 10:48 | 2min unclassified | entry 24758.00 stop 24760.25 target 24724.00 | -0.42R stop |
| 2026-02-13 | short | 10:54 | 3min unclassified | entry 24818.25 stop 24846.00 target 24724.00 | -0.84R stop |
| 2026-02-16 | long | 09:51 | 3min B | entry 24754.25 stop 24734.25 target 24871.50 | -0.85R stop |
| 2026-02-16 | short | 10:40 | 5min B2 | entry 24703.25 stop 24711.75 target 24685.25 | -1.03R stop |
| 2026-02-17 | long | 08:33 | 3min A | entry 24583.00 stop 24577.00 target 24655.00 | +12.00R target |
| 2026-02-17 | short | 09:21 | 3min B2 | entry 24654.25 stop 24669.50 target 24583.00 | -1.02R stop |
| 2026-02-17 | short | 10:10 | 5min unclassified | entry 24517.75 stop 24543.50 target 24466.00 | -1.01R stop |
| 2026-02-19 | short | 07:55 | 5min B | entry 24869.50 stop 24875.50 target 24817.50 | -1.00R stop |
| 2026-02-19 | long | 08:36 | 1min B | entry 24861.50 stop 24849.50 target 24913.75 | -1.08R stop |
| 2026-02-20 | short | 09:30 | 2min A | entry 24782.00 stop 24755.25 target 24725.00 | -0.11R stop |
| 2026-02-23 | short | 08:00 | 2min unclassified | entry 24907.25 stop 24912.25 target 24880.00 | -0.81R stop |
| 2026-02-23 | long | 08:03 | 3min B | entry 24909.00 stop 24904.00 target 25001.50 | +13.70R target |
| 2026-02-23 | long | 10:24 | 2min unclassified | entry 24886.25 stop 24878.50 target 25001.50 | -1.03R stop |
| 2026-02-24 | long | 08:00 | 2min B | entry 24823.25 stop 24814.25 target 24885.75 | +3.79R target |
| 2026-02-24 | short | 10:06 | 2min B2 | entry 24884.50 stop 24896.50 target 24784.00 | -1.02R stop |
| 2026-02-25 | short | 10:06 | 1min A | entry 25331.50 stop 25344.00 target 25282.50 | +3.92R target |
| 2026-02-26 | short | 08:00 | 3min A | entry 25371.50 stop 25380.00 target 25341.25 | -1.12R stop |
| 2026-02-26 | short | 08:54 | 2min B | entry 25386.25 stop 25401.00 target 25345.75 | +2.49R target |
| 2026-02-27 | short | 09:42 | 3min B2 | entry 24856.50 stop 24864.00 target 24796.25 | -0.70R stop |
| 2026-02-27 | short | 10:30 | 3min B | entry 24962.75 stop 24977.25 target 24864.25 | -0.55R stop |

## For Angus — the GATE

Rule every MISSED and EXTRA: *"my setup, I missed it"* (accept the divergence) vs *"not my setup — detector too loose"* (tighten a rule, with an approved hypothesis + out-of-sample check + doc bump; never tuned to February).
