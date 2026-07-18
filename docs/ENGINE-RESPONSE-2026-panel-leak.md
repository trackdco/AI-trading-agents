# Engine response: the 2026 FreshEyes panel leak — analysis + v0.6 proposal

Companion to Pat's whole-2026 calibration (47% reads / 15% capture / $38,137
regret, 108 days in 6.4 min). Independent decomposition from output/fe/ledger.csv,
plus mechanical tests of candidate fixes BEFORE any prompt work.

## 1. The leak, decomposed (regret = $38,137 total)

| miss class | days | $ regret | share |
|---|--:|--:|--:|
| ALL wrong FLATs (agent hid, day paid) | 36 | $29,642 | **78%** |
| … of which event_risk wrong-FLATs | 24 | $19,999 | **52%** |
| war MOMENTUM-called-ROTATION | 4 | $2,294 | 6% |
| balance ROTATION on flat days | 7 | $3,664 | 10% |

One reflex — `event_risk → stand_down` — carries half of everything we leak.
Agent FLAT rate 70% vs oracle 50%.

## 2. Candidate fixes, tested mechanically on the same verdicts

| variant | 2026 capture | off-era (2023-25) |
|---|--:|---|
| as-run FreshEyes v0.5 | 15% ($6,811) | — |
| Pat's v0.6 draft: FLAT iff analog share_both_books_red ≥ T | ≤18% (best T=0.65) | untested — signal's FLAT precision is chance-level, rejected |
| event FLAT → analog majority | 17% | — |
| **event FLAT → momentum book** | **23% ($10,533)** | **FAILS: −$660 / −$2,080 / −$5,545 by year** |
| perfect event-day reads (upper bound) | **60% ($26,810)** | oracle makes $20–26k/yr on event days — ~half of every year's ceiling |

Conclusion: **no fixed replacement reflex works.** Every mechanical substitute
tops out at 17–23% in-era and the best one inverts off-era. The event-day prize
is huge and regime-dependent — it must be READ (or timed), not ruled.

## 3. Proposal: v0.6 = Angus's B1/B2, made concrete

The agent's fear is temporally correct and daily wrong: the danger of an 08:30
CPI is the release moment, not the date. Our window is 08:00–10:15; nearly all
red-folder drops are 08:30 or 10:00 — **most of the tradeable window exists
AFTER the information is out.**

1. **Event = timing modifier, not day-kill (B2/B3).** On event days the 08:00
   verdict picks which book gets ARMED and at what size; entries are held until
   release + N minutes (N≈10–15). stand_down remains available but must cite
   evidence beyond the calendar label alone (schema: `stand_down_reason ≠
   "calendar"` on its own).
2. **ENGINE TEST FIRST (no prompt change until this is measured):
   delayed-entry backtest** — both books, all four years, triggers on
   red-folder days gated to ts ≥ release + 10min. If post-release books are
   green off-era where full-day books bleed, the mechanical floor exists and
   the agent read rides on top. Queued in the engine lane immediately after the
   news-aware year suites finish (CPU contention only).
3. **Event-day briefing upgrade (A3, already proposed):** the analog block
   filtered to same-event-family mornings ("last 8 CPI days: what paid,
   post-release") + corrected base rates (event days: 54% FLAT, rotation is the
   poison book at −$84/day full-history, momentum −$24/day — NOT the +$60 the
   51-day 2026 sample suggested; that claim is withdrawn).

## 4. Sizing of the prize

Fixing event-day reads alone bridges as-run 15% → 60% capture upper bound in
2026, and the same class is worth $20–26k/yr off-era. Nothing else we have
measured — memory quarantine (June: reads 45% vs 38%), analog retrieval (3×
capture), sizing discipline — comes within an order of magnitude of this single
miss class. B1/B2 is the campaign.

## 5. MEASURED (Angus "run it", 18 Jul): the delayed-entry test, all four years

Blanket delay FAILED (sign-flips by year — another dead reflex). But splitting by
RELEASE TIME exposed two conditional rules:

| rule | 4-yr effect | by year |
|---|--:|---|
| **R1: release ≤ 09:30 → MOMENTUM entries wait for release+10min** | **+$9,765** | +335 / +7,305 / +2,030 / +95 — green ALL FOUR years |
| **R2: release at 10:00+ → no ROTATION entries pre-release** | **+$3,251** | +1,212 / +559 / +2,278 / −798 — green 3 of 4 |
| combined two-rule floor (event days, books unchanged otherwise) | **+$13,018** | +1,548 / +7,864 / +4,308 / −702 |

Tape logic: post-release displacement is momentum structure (wait for the number,
trade the reaction); pre-10:00 chop poisons rotation reclaims (don't fade a
market that's waiting). Caveats, stated plainly: R1's magnitude is concentrated
in 2024 (+$7.3k of $9.8k); 2026 is the weakest year for both rules (−$702
combined) — the floor is an off-era edge that roughly breaks even in-era. Do NOT
extend either rule beyond its bucket (rotation-early and momentum-late both
sign-flip).

**v0.6 shape:** engine enforces R1/R2 as the mechanical timing floor
(config-gated, split-testable); the agent's 08:00 verdict arms book/size on top
and may still stand down with non-calendar evidence. Event-day capture then has
three layers: timing floor (mechanical), book choice (agent), size (agent).
