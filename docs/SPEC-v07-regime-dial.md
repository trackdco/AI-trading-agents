# v0.7 — THE REGIME DIAL (Angus discovery, 19 Jul night)

## The finding that produced this (Rung 1 override analysis, floored 2026, 106 days)

The agent's per-day STAND-DOWN is the entire loss; its BOOK SELECTION is a small
real edge. Measured against the mechanical champion baseline:

| deviation from champion | days | value |
|---|--:|--:|
| stand FLAT (champion traded) | 74 | **−$10,002** |
| pick a different book | 8 | **+$1,361** |
| net agent override | — | **−$8,642** |

Kill the daily stand-down, keep the book edge, trade full size:

| 2026 config | capture |
|---|--:|
| agent v0.6.3 (daily stand-down ON) | 10% |
| mechanical champion + floor | 29% |
| **REGIME DIAL (champ default + agent book edge, full size)** | **32%** ← first agent config to beat the champion |
| regime dial but keep agent half-sizing | 27% |

## The design

The agent stops answering "should I trade today?" (a daily coin-flip it loses on)
and starts answering "what regime are we in, and how should the desk be dialed?"

1. **Never flat by default.** Baseline action = the champion's imbalance-switch
   book pick, always in the market.
2. **Book override:** the agent may switch rotation↔momentum with cited evidence.
   (Proven +$1,361 / 8 days in 2026.)
3. **Size:** {0.5, 1.0}. Full size unless the agent states a reason to halve —
   its caution half-sized winners and cost 5 points of capture (32%→27%).
4. **Stand-down is a persistent STANCE, not a daily vote.** The agent can only pull
   the desk flat by declaring a `risk_off` regime that CARRIES FORWARD across days
   until it explicitly declares `risk_on` again. It cannot re-flip each morning.
   This is the only defensible form of stand-down: v0.6.1's daily version cost
   $10k in green 2026; a stance that engages only across genuine risk-off stretches
   should protect the red years at a fraction of the green-year cost.

## Why this REQUIRES the chained run (the Long Walk)

A persistent regime stance is stateful — the agent must see its own carried-forward
stance to maintain or revoke it. Fresh-eyes (stateless, each day independent) CANNOT
express "stand down across a stretch." So v0.7 is inherently the chained/journaled
run Angus flagged: emit→verdict→ingest one day at a time, regime stance + notes
carried forward. This is the same "full 2023→2026 simulation" idea — now with a
concrete reason to be chained rather than a nice-to-have.

## The bars it must clear (floored books, per year)

| year | champion+floor | ceiling | the dial must… |
|---|--:|--:|---|
| 2023 | −$10,214 (−14%) | $71,490 | protect: get ≥ $0 where champ bleeds |
| 2024 | −$3,579 (−5%) | $78,282 | protect |
| 2025 | −$15,962 (−25%) | $62,610 | protect (the hardest red year) |
| 2026 | +$8,878 (+18%) | $48,110 | add: beat champion (dial already = 32% > 29%) |

PROMOTE criteria (pre-registered): every year ≥ $0 at as-verdicted sizing; beats
champion+floor on 4-year total; beats it in ≥3 of 4 years individually.

## Cost & sequencing (honest)

The chained 886-day run is ~886 verdicts single-arm — ~2.5× tonight's volume, and
tonight hit the Max-20x monthly spend limit at ~350 verdicts. So:

1. **Build now (free):** this spec, the v0.7 agent file, the persistence mechanism
   in the sequential driver (stance carry-forward + revoke), checkpoint/resume so a
   long run survives interruption.
2. **Validate cheap first:** a single red-era quarter (a 2024 quarter, ~64 verdicts)
   proves the persistent stand-down protects before spending on the full 886.
3. **The full Long Walk:** staged + checkpointed background job, run after the spend
   resets and on the successor model (Opus 4.8 — record the model in the ledger;
   re-sit June 2026 regression under it first to calibrate the model delta).

## Model-transition note

All verdicts to date were produced by the current model. Before any cross-model
comparison, re-sit one spent regression paper (June 2026) under the new model to
measure the model's own delta — the trader changed, not just the config.

## AMT features wired (v0.7) + PREDICTION P11 (2026, filed pre-run)

Wired: value_position / open_vs_value / inventory_pts into regime_vector.csv
(agent sees them as facts) + today's value_position & inventory base-rate slices
into the briefing. NOT wired into the analog distance metric — MEASURED to hurt
the 2026 analog read (49%->45%, equal-weighting diluted the imbalance signal);
kept out of matching, surfaced to the agent directly instead.

Measured signal (2026, mechanical, no agent):
- value_position swings the momentum-lean 15% (overlap_dn) -> 37% (overlap_up)
- as a BOOK-CHOICE rule it beats the champion imbalance rule: 62% vs 55% right,
  +$4,794 on 58 tradeable days; on the 16 disagreement days $12,594 vs $7,800
- as the dial's book baseline (all days, full size): 24% vs 18% capture, +$2,544

P11: because the regime dial's whole game is book choice (no daily FLAT), AMT
should help HERE more than it helped the 3-way read proxy. Estimate for 2026:
- 3-way read accuracy: ~flat (44-49%) — AMT informs book choice, not the FLAT
  call, and reads have been sticky regardless of inputs.
- regime-dial CAPTURE: 32% -> 35-40%, driven by better book overrides. The agent
  won't match the pure value_position rule but now sees the signal + base rates
  that produce it. Central estimate +$1,500-3,500 over the AMT-blind dial.
- Risk: the agent over-trusts value_position on inside/overlap days where it's
  weak (12-pt flat spread is modest); tell = book accuracy on 'inside' days.
Only a run confirms it. This is the last free build before the Long Walk.

## OVERNIGHT RUN (20 Jul, Angus authorized) — fresh-eyes full history + chained 2026 only

Scope decision (Angus, cost-conscious): fresh-eyes runs the FULL 2023-2026 walk
(912 days, walk-forward-clean --asof base rates per year, 8 parallel background
workflows). Chained (true day-to-day playbook_notes memory) is scoped to 2026 ONLY
(139 days) rather than the full 4 years — chaining is strictly serial (can't
parallelize; day N depends on day N-1's notes) and after tonight's spend-limit hit,
running it across 4 years unattended was judged too risky. 2026 alone gives a direct,
same-year chained-vs-fresh-eyes comparison, which is the point of the test.

Chained implementation: no CLI driver needed. A Workflow script holds `notes` in a
plain JS variable across a sequential for-loop (NOT parallel/pipeline — literally
await agent() one at a time). Each call: agent reads the v0.7 contract + the day's
pre-built briefing.json (reused from the fresh-eyes emit — same features, health
gate, base rates), receives the running notes inline in the prompt, and returns
structured output via a JSON schema (date/regime_stance/book/size_multiplier/
expected_value_usd/rationale/cited_evidence/playbook_notes) — schema-forced output
sidesteps free-text JSON parsing failures. The returned playbook_notes becomes next
iteration's carried notes. No file writes needed for the chain itself.

Grading plan on completion: pull fresh-eyes' own 2026 subset from the walk_v07 tag,
grade both arms on IDENTICAL 2026 floored books, and report reads/capture/FLAT-rate/
health-override-rate side by side — this is the real "does memory help or hurt"
answer promised since June's frame-lock-in finding, now on 139 days not ~20.

## RESULTS (20 Jul) — both arms complete, graded

Fresh-eyes: 912/912 answered, 884 gradeable days, 0 invalid. Chained: 139/139
answered, 127 gradeable days, 0 errors. Three overnight failure modes hit and fixed
live (stacked-workflow silent death, a hard session-usage limit that hit all three
arms simultaneously, a CronCreate watchdog that never fired once in ~8 hours) — see
the overnight-report artifacts for the full incident writeups.

**Fresh-eyes, full 4-year walk (vs champion+floor):**

| year | champion+floor | fresh-eyes v0.7 | Δ |
|---|--:|--:|--:|
| 2023 | −$10,214 (−14%) | −$440 (−1%) | +$9,774 |
| 2024 | −$3,579 (−5%) | +$2,391 (+3%) | +$5,970 |
| 2025 | −$15,962 (−25%) | −$13,783 (−22%) | +$2,179 |
| 2026 | +$8,878 (+18%) | +$10,913 (+23%) | +$2,035 |
| **4-year total** | **−$20,877** | **−$919 (−0%)** | **+$19,958** |

Graded against the pre-registered PROMOTE bars: beats champion+floor on the 4-year
total ✅, beats it in 4/4 years individually (bar was ≥3/4) ✅, but does NOT clear
"every year ≥ $0" ❌ — 2023 and 2025 are still net negative, just far less so. Real,
measured progress (the dial substantially shrinks the bleed in every single year),
not full promotion-grade performance. Say that plainly.

**Chained vs fresh-eyes, identical 127 days in 2026:**

| | fresh-eyes | chained |
|---|--:|--:|
| P&L | +$10,913 | +$14,465 |
| capture | 23% | 30% |
| reads | 35% | 39% |
| flat | 17% | 17% |
| book override | 28/127 (22%) | 25/127 (20%) |
| health-gate overrides | 0% | 0% |

Chained wins by +$3,552 / +7pp capture. Flat-rate and health-override-rate are
IDENTICAL between the two arms (both mechanically gated by the same precomputed
`regime_health` signal, present in both arms' briefings regardless of memory) — the
entire gap is book-choice accuracy (39% vs 35% reads), despite chained overriding
the champion pick slightly LESS often. Memory doesn't change WHEN the desk trades;
it changes WHICH book it picks when it does. Caveat: one run each, not multiple
seeds — the exact-match flat-rate/health-gate numbers make pure noise less likely
as the explanation, but a repeat chained run on a different year would firm this up
before treating "+7pp from memory" as load-bearing for design decisions.

Full writeup: artifact "The Long Walk — Final Results" (published 20 Jul).
