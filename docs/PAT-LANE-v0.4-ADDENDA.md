# Pat-lane addenda to the v0.4 proposal — for Angus review

Companion to docs/PROPOSED-AGENT-ADJUSTMENTS-v0.4.md. Everything below comes
from running 65 real verdicts across March/April/May 2026 (v0.2 → v0.3.1) and
reproducing the full-history oracle ledger from output/allyears_daily_books.csv
+ output/l2_analog_routing.csv. Agreement first: the regime read is the
single highest-leverage variable — reads scored before P&L, always (D1).

## The ledger, reproduced from source (definitions pinned)

Two oracle flavors exist in the codebase; keep them distinct in every report:
- **oracle** = better book per day, always trades: 2026 Feb–Jul **+$37,014**
- **oracle + stand-down** = better book or FLAT (max(E3,E4,0)) — the real
  target: 2026 Feb–Jul **+$45,159**; 2023 **+$73,014**; 2024 **+$76,049**;
  2025 **+$62,549**; ≈ **$259k** over the full history.

Champion Blend v1.1 by contrast: +$14,022 in 2026, and per the engine lane it
LOST ~$6k/$14k/$15k in 2023/24/25. The judgment layer is not garnish — over
the full history it is essentially all of the P&L.

## The headline structural fact: the oracle is FLAT ~half of all days

Stand-down share of the oracle+SD ceiling: **47% of 789 days** (2023–25) and
**50%** of 2026 Feb–Jul. Knowing *when not to trade* is half the entire prize.
This reframes our miss classes: the agent's defensive instinct is not wrong in
kind — it is wrong in *selection*. March over-called FLAT on tradeable
event days; May under-called FLAT on chop days it labeled war/momentum. Same
skill, both directions: **trade/no-trade discrimination**.

## Additional proposals (numbered to slot after Angus's A/B/C/D)

E1. **Fix the L1 vector before grading reads on it** (engine lane, upstream of
    everything). Across all 65 verdicts the agents independently and repeatedly
    documented the same three feature defects:
    - `red_folder_today` = 0 on mornings with listed high-impact releases
      (03-12, 03-19, 03-26, 04-21, 04-30, 05-04, 05-14, 05-27, 05-28 …)
    - `gap_open_pts` sign-conflicts with the overnight block (04-20, 04-23,
      04-28, 05-05, 05-12, 05-15, 05-19, 05-21, 05-26, 05-28 …)
    - `streak_imbal` / `day_type` contradicting the raw trailing sessions
      (9-day streak scored streak_imbal=1, etc.)
    Read accuracy is capped by feature quality; A1–A3 add features but these
    existing ones actively mislead. The agents burn rationale space every
    single day re-deriving "the vector is unreliable" — that alone argues the
    fix pays for itself.

E2. **Stabilize the shock-bar metric.** `threshold_pts` drifts day-to-day
    (observed 40.5 → 78), making `count` incomparable across days — the agents
    flagged this in nearly every May playbook note. Report BOTH a fixed-scale
    count (e.g. bars > 50pts) and a percentile vs the 20d norm, so "elevated"
    is a fact, not a guess. Directly serves the always-half-size fix: the
    agent can't calibrate "normal volatility" without a stable ruler.

E3. **Build the true sequential replay driver before v0.4 is graded.** Our
    month runs were parallel — every verdict was a "first entry" with no real
    playbook chaining (each month's agents all inherited only the prior
    month's last note). Angus's C1 (scorecard feedback) and C2 (regret ledger)
    are *learning* mechanisms; they only function day-by-day. Deliverable:
    emit→verdict→ingest one day at a time so notes, scorecard, and regret
    actually accumulate. Without this, C1/C2 cannot even be tested — and any
    v0.4 exam that skips it under-measures the design.

E4. **Make FLAT a first-class prediction target.** Given the 47–50% flat
    share, score a binary trade/no-trade read alongside the 3-way, with its
    own precision/recall in the scorecard (C1). B4's health-conditioned
    default and A1's analog conditionals are the natural inputs. Our May
    war-called-chop misses (6 days MOMENTUM vs oracle FLAT) were exactly
    failed no-trade detection — as were March's inverted event-day misses.

E5. **Name the day-vs-regime mismatch in the taxonomy split (B3).** Oracle
    labels are per-DAY best action; the agent reads a multi-day REGIME. May
    was genuinely a trend-up regime AND the momentum book lost on half its
    days — both true. B3's two axes help; additionally the briefing should
    show each book's rolling recent daily P&L shape (B4 provides the health
    number; show the per-book split) so "momentum regime, momentum book
    locally sick" is visible instead of inferable.

E6. **The fair exam should include a 2023–25 stretch** (agree with D1, making
    it concrete): score_regime_reads.py already accepts
    allyears_daily_books.csv; the champion is net-negative in all three of
    those years, so they are the payout-side exam March/April could never be.
    Propose: one 2025 quarter, reads scored first, then P&L.

## Status of already-filed items (so v0.4 doesn't re-do them)

- Rationale length cap: fixed in prompt v0.3.0 (0 length failures since).
- size_multiplier notch enumeration {0.0, 0.5, 1.0}: fixed in prompt v0.3.1
  (5 April verdicts died on 0.75 before the fix). If v0.4 wants graded sizing,
  widen the SCHEMA to {0, 0.25, 0.5, 0.75, 1.0} instead — April showed the
  agent reaches for 0.75 naturally, and the intermediate notch is judgment
  the current contract discards.
- Structure-exclusion rule (no label-only bans): in prompt v0.3.0; the 03-19
  class of veto has not recurred in 43 subsequent verdicts.
