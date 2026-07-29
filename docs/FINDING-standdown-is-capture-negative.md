# FINDING — the stand-down layer is capture-NEGATIVE; "read accuracy" is a misleading target

After three prompt iterations (v0.5 → v0.6 → v0.6.1) and a mechanical threshold sweep,
the 2026 fresh-eyes data forces a conclusion that reframes the campaign. Reported straight.

## The numbers (2026, same days, capture = follow-the-reads $ / oracle+SD ceiling)

| strategy | FLAT rate | reads (3-way) | capture |
|---|--:|--:|--:|
| **always-trade CHAMPION** (imbal E3/E4 switch, never flat) | 0% | **25%** | **21%** |
| always-trade ANALOG-MAJORITY book | 0% | 49% | 7% |
| agent v0.5 | 70% | 47% | 15% |
| agent v0.6 | 35% | 36% | 19% |
| agent v0.6.1 | 78% | 49% | 11% |

## Two hard conclusions

**1. Every agent version captures LESS than just always-trading the champion (21%).**
The best agent config (v0.6, 19%) still trails the dumb always-trade champion. The
regime-read + stand-down layer, as built, SUBTRACTS value versus running the books
straight. The more the agent stands down, the less it captures (v0.6.1 at 78% flat →
11%; v0.6 at 35% flat → 19%) — because on this book pair the winners it forfeits by
standing down outweigh the losers it avoids.

**2. "Read accuracy" and capture are ANTI-correlated — reads is the wrong target.**
- always-trade-analog-majority: **49% reads, 7% capture** (best reads, near-worst money).
- always-trade-champion: **25% reads, 21% capture** (worst reads, best money).

3-way "read accuracy" is dominated by correct FLAT-calls, and every correct FLAT forfeits
that day's winner. So optimizing reads drives standing-down, which destroys capture. The
champion's imbal switch reads the regime WORSE than random (25%) yet captures the most,
because it never forfeits a winner and its book still often pays even when the 3-way label
is "wrong." Chasing Angus's read metric via the stand-down channel actively hurt the P&L.

## Why the stand-down can't be fixed by tuning

The available stand-down signal — the analog cohort — is FLAT-dominant on ~80% of days
(flat_share ≥ 0.4 on 84% of them). Any rule anchored to it over-flats to 78–84% and
caps capture at 7–11% (mechanical threshold sweep confirms: every T gives ~80% flat).
The oracle's 50% flat rate is a HINDSIGHT luxury (it knows which days both books lost);
no pre-open signal we have identifies those days (best confluence 63%, established
earlier). Trying to replicate the oracle's stand-down forfeits winners on the ~half of
"flat-looking" days that actually paid.

## What this means for the campaign (the pivot)

- **Stop optimizing the stand-down.** It is capture-negative; the target "bring the flat
  rate to the oracle's 50%" was wrong-headed. The capture-maximizing posture is to trade
  nearly ALWAYS and stand down only on the rare, cited both-red day.
- **The agent's job is BOOK SELECTION, not gating.** To add value it must beat the imbal
  switch's book pick (25% reads / 21% capture) while trading always. We have NOT shown it
  can — the reads aren't good enough, which the feature analysis (docs/VERDICT-standdown-
  variable.md §2) attributed to input poverty, not prompt wording. This needs the richer
  features (AMT / order-book / event-family analogs), not another prompt version.
- **The proven positive levers are mechanical:** the R1/R2 timing floor (+$13k/4yr, Angus)
  and sizing. The LLM regime-read layer is, on current features, not yet earning its keep.

## Caveat

"capture" is a full-notional read-quality proxy, not the deployed arm-B P&L (which carries
the 0.25/0.5 sizing and the champion's C1–C3 cuts). The deployed number may differ in
magnitude, but the RANKING — agent selection below always-trade-champion, and reads
anti-correlated with capture — is robust across all three versions and both baselines.

## TESTED (2026-07-18): the "book selection, always-trade" fork does NOT work on current features

Ran the fork mechanically (no new verdicts): took the v0.6 verdicts' book lean, forced
ALWAYS-TRADE (stand-downs removed), graded vs the champion imbal switch on the same 108 days.

| always-trade strategy | capture |
|---|--:|
| champion imbal E3/E4 switch | **30% ($13,720)** |
| agent book lean (v0.6) | 13% ($5,972) |

On the 36 days they disagree, the agent's book made **−$1,619** vs the champion's **+$6,129**.
So the agent's BOOK SELECTION is also worse than the mechanical switch — not just its
stand-downs. Freeing it to always-trade does not rescue it. Confirmed: the LLM read layer
cannot beat the champion on current features, in ANY posture. Improvement is gated on new
FEATURES (AMT / order-book / event-family analogs), not prompt/logic — a real build, not a
quick tweak.

## SHIP DECISION (Pat, urgency): build the bot on the CHAMPION now, swap the strategy later

Because the agent is value-negative in every tested posture, the shippable strategy today is
the frozen champion (Blend v1.1, +$14k 2026). The engine already supports a hot swap:
`simulate(day_gate=None)` runs the pure champion byte-identical; the agent/refined strategy
plugs in later as a `day_gate` callable with ZERO engine changes. So Phase 4-5 (live loop,
Telegram, paper trading, risk guards) can be built now on the champion, decoupled from the
agent research. CAVEAT: champion is profitable only in 2026 (lost 2023-25) — build + PAPER
trade now; hold live money until the champion is validated wider or the adaptive layer works.

## Recommendation (for Angus)

Do NOT ship a v0.6.2 stand-down tweak. Two real forks:
1. **Near-always-trade agent** whose only job is book choice + size, stand-down deleted
   except on cited both-red; then pour effort into the features that could make book
   selection beat the imbal switch. Grade against the 21% always-trade-champion bar, not
   the oracle.
2. **Concede the LLM read layer for now** and bank the mechanical wins (timing floor +
   sizing), revisiting the agent when AMT/order-book features exist.

The four-year 2023-25 validation is on hold until this fork is decided — running 770
verdicts to confirm a capture-negative layer across more years would only re-prove the
finding.
