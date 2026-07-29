# VERDICT — the stand-down variable, and how to bring it to the oracle standard

Pat-lane verdict on Angus's 4-year delayed-entry test (docs/ENGINE-RESPONSE-2026-panel-
leak.md) + my whole-2026 FreshEyes calibration. Question: what do we ADD / REMOVE to move
the agent's stand-down toward the oracle's stand-down standard (oracle FLATs 50% of days,
correctly; the agent FLATs 70%, wrongly)?

Independently reproduced from output/fe/ledger.csv + regime_vector + analog_briefing.

## 1. The leak is the stand-down, confirmed

- Regret $38,137. **Wrong-FLATs = 78% ($29,642). event_risk wrong-FLATs = 52% ($19,999).**
- Agent FLAT rate 70% vs oracle 50% — over-flat by 20 points, concentrated on event days.

## 2. The decisive finding: the oracle stand-down is NOT out-filterable

I tested whether ANY pre-open feature/confluence identifies oracle-FLAT days precisely
enough to justify sitting out (you need ~80%+, because a wrong FLAT can cost +$3,485):

| stand-down signal | days | oracle-FLAT precision |
|---|--:|--:|
| base rate (no signal) | 108 | 50% |
| red_folder > 0 (the agent's current proxy) | 50 | 62% |
| range_pctl ≤ 0.35 | 33 | 55% |
| analog majority = FLAT | 85 | 53% |
| **majority FLAT AND red_folder > 0 (best found)** | 43 | **63%** |

Nothing clears 63%. range/trap/imbalance don't separate oracle-FLAT from tradeable at all
(means differ by <0.02). **The oracle's stand-down is P&L-defined ("both books lose") and
is essentially unpredictable from the features we have.** So a *smarter stand-down filter*
is a dead end — Angus proved it from the P&L side (every fixed replacement reflex 17–23%,
inverts off-era); this proves it from the feature side.

Corollary the corrected base rates make concrete (output/base_rates.json, 898 days): over
full history BOTH books lose on average (rotation −$44/day, momentum −$22/day) — the entire
edge is in *selection*, and selection on event days is the hardest, highest-stakes call.

## 3. Verdict: don't filter stand-down better — demote it, move risk to timing + size

Because you cannot match the oracle stand-down with a rule, the only way to converge the
70% FLAT rate toward 50% is to **stop using stand-down as the primary risk lever.**

### REMOVE
1. **`event_risk → stand_down` reflex.** 52% of all regret; 38% of event days are the
   month's biggest winners. event_risk must never, by itself, force FLAT. (Schema guard:
   `stand_down` requires a `stand_down_reason` other than the calendar label alone.)
2. **Binary stand-down as the default response to ambiguity.** 0-or-full is too blunt on
   days that are coin-flips; it turns "unsure" into "miss the winner."

### ADD
1. **Engine timing floor R1/R2 (CONCUR with Angus's B1/B2).** On event days, arm the book
   and let the engine gate entries: R1 (release ≤ 09:30 → momentum entries wait
   release+10min), R2 (release ≥ 10:00 → no pre-release rotation). This is what makes
   "don't stand down on event days" survivable. Build it engine-side, config-gated.
2. **A reduced-arm size tier (0.25) — schema widening.** Replace stand-down on ambiguous
   days with arm-minimal. The 36 wrong-FLATs leave $29,642; arming the right book at 0.5
   recovers ~$14.8k, at 0.25 ~$7.4k (upper bounds, correct-book). Even a quarter-size stake
   keeps the agent in the +$3,485 days it currently sits out entirely.
3. **Event-family analog block (A3).** Generic analogs don't lift event-day reads (feature
   analysis above). Same-event-type retrieval ("last 8 CPI mornings: what paid
   post-release, which book") is the one input that plausibly can — it's the only path to
   getting the event-day BOOK right, which is where the 2026 prize lives.
4. **Confluence-gated stand-down, demoted to rare.** The closest thing to a real signal is
   `majority FLAT AND red_folder>0` (63%). Reserve genuine stand-down for that confluence
   (low range + analog-majority-FLAT + no directional overnight gap) — and even then prefer
   0.25 over 0.0 unless conviction is high. This is the ONLY place stand-down earns its keep.

## 4. Honest caveat on the size of the win (do not oversell)

Angus's timing floor is **+$13k over 4 years but concentrated in 2024 (+$7.9k) and roughly
break-even in 2026 (−$702)** — it is an off-era robustness floor, not a 2026 bonanza. The
2026 event-day recovery (15% → 60% capture upper bound) requires *reading* event days
better, and §2 shows that may not be readable from current features. So:
- The timing floor + 0.25 tier are the **safe, mechanical** wins — build first, low risk.
- The A3 event-analog read is the **high-ceiling, unproven** win — build, but grade it hard
  against the fresh-eyes control before believing it.

## 5. Recommended v0.6 build order

1. Engine: R1/R2 timing floor (config-gated, split-testable) — Angus's test already sized it.
2. Schema: add 0.25 size notch; `stand_down` requires non-calendar reason.
3. Briefing: A3 event-family analog block.
4. Prompt v0.6: event_risk sets ARM (book+size+timing), not day-kill; stand-down only on the
   §3.4 confluence, prefer 0.25 on ambiguity.
5. Re-fire the whole-2026 (+ 2023-25, now that Brake's calendar is live) FreshEyes
   calibration; grade reads and capture vs this v0.5 baseline (47% / 15%). Fresh-eyes stays
   the control so we can't fool ourselves.

Bottom line: we can't teach the agent to stand down like the oracle — the signal isn't
there. We CAN stop it standing down when the oracle wouldn't, and catch those days with a
mechanical timing floor and a small stake instead of a full one. That is the move that
pulls the 70% FLAT rate down toward 50%.
