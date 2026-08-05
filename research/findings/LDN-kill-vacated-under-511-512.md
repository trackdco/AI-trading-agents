---
date: 2026-08-05
status: STATUS CORRECTION — both London-open kills vacated
tags: [london, process, self-correction, canon-map]
sources: ["docs/VALIDATION-PROCESS.md#5.11", "docs/VALIDATION-PROCESS.md#5.12", "research/findings/DISCOVERY-raw-triggers-to-canon.md", "output/london_obk_flow.md", "output/london_obk_autopsy.md"]
---

# The London-open kills do not survive §5.11/§5.12 — vacated, not restarted

The canon rebuild landed §5.11 (pre-ship checklist) and §5.12 (canon map) after
`LDN-OBK-01` and `LDN-PO3-01` were killed. Re-reading my own run against them: **the
kill verdict is not earned. It is withdrawn.**

This is not "the strategies are alive". It is "I did not run the search I claimed to
have completed", and under §5.9.2 an expectancy kill is only legal *after* a complete
search.

## What still stands (do NOT re-run)

- **The census.** 881 events, 396 sessions. Break frequency 92/93%, fail rate 85/84%,
  **+12/+14pp over the declared placebo range**, era-consistent. §5.11 and §5.12 change
  nothing about counting events, and the placebo control is exactly the kind of thing
  the new law wants more of. **Keep.**
- **L1 mechanics.** The tight-stop claim failing 0/4 is a clean, correctly-run result
  against a pre-committed reading. **Keep.**
- **The conditioning search.** Predictions declared before the run, opposite directions
  per branch. Method is sound. **Keep** — but see gap 4, it was pooled.
- **The NYA-FA transfer negative.** Unaffected. **Keep.**
- **The trial ledger.** All 141 London rows stay. A vacated verdict does not un-charge
  the search — the deflation denominator is honest precisely because it never shrinks.

## What does not stand — six gaps, each with a rule and a precedent

### 1. I tested the weakest variable class at the weakest moment (§5.12.10)

This is the one that actually matters, and it is embarrassing in a useful way.

The canon dissection's class priors, measured on the shipped canon:

> **depth carried the entire canon edge (+0.5 to +1.3R); flow was near-worthless AT
> entry and decisive INSIDE the trade; context died almost everywhere; structure
> generates population, not edge.**

> *"Not one flow check exceeds +0.34R in any era... Against depth's +0.5 to +1.3R,
> order flow is a rounding error on entries."*

My L3 pass was **four tape features at entry** and two thin book features. I then wrote
"zero of six confirmed" and killed the family. **I ran the class the canon says is a
rounding error, at the moment the canon says it is worthless, and treated the null as
decisive.** The canon's actual edge carriers — `W` (no wall behind), `D` (wall ahead),
`WALLSZ` — are depth constructions I never built.

`wall_ratio_opp` is not `W`. `W` is `isna(behind_d)` — a *presence* test on the wall
behind the trade, direction-resolved. Different object.

### 2. Pooled flow nulls do not close a gate question (§5.11.4)

> *"every flow/context gate re-tested inside states: strategy drawdown vs profit, day
> regime at entry (no-lookahead), post-loss entries. **Pooled nulls DO NOT close a gate
> question.** (Pooling masked a real drawdown-state flow gate.)"*

Every table in `output/london_obk_flow.md` is a pooled tercile. The NY lane found a real
flow gate that pooling hid, on this exact rule, days ago. My flow null is the pooled
kind, which the law now says cannot close the question.

### 3. No event-universe sensitivity (§5.11.2)

> *"all-occurrences vs first-occurrence, window widening, re-entry rules... (356→478 was
> found only on challenge.)"*

My prereg froze **first break per side per day** and listed re-break behaviour as a
known limit. The NY lane got **+34% more events** from exactly this challenge. Never run
here.

### 4. No stop-cap arm class (§5.11.3)

> *"absolute stop caps and fixed-dollar-sizing interaction tested as standard arms, not
> ad hoc. (cap20 found the family's best expression and rescued 2024.)"*

I tested trigger-candle vs structural stop at a fixed 2R target. **No absolute stop
cap.** On the NY lane a cap was the difference between a losing year and no losing year.
This is directly on point for a branch whose average risk was ~5 points with a
fat right tail.

### 5. No time-segment / MFE-MAE pack (§5.12.5, §5.11.1)

> *"Every sim records open/r/mfe/mae at t+2/3/5/8/10 from day one — the in-trade
> winner/loser signatures are where the management edge lives."*

I have exit reasons and final P&L. I have no in-trade path at all — so I cannot see the
press-state / dying-trade / giving-back signatures, and critically **I cannot test flow
where the canon says flow actually works: inside the trade.** My autopsy was run without
the pack §5.11.1 makes mandatory.

### 6. The carried interaction was never permutation-tested (§5.12.4)

V1×V3 beat both its components. §5.12.4 flags a variable entering via combination rather
than standalone survival and requires a permutation null (the LONSLOPE lesson). Not run.

## The precedent says vacate, and it is explicit

§5.9.1 as tightened:

> *"the IVB breakout's kill became legal only AFTER the flow+wall search failed to save
> it; **the IVB range fade survived only BECAUSE the raw-set kill was vacated and the
> search ran**."*

That candidate was killed twice on incomplete searches and is now the healthiest thing
in the programme (PF 1.56/1.57/1.20, positive every era, PSR 0.994). The failure mode
this rule exists to prevent is exactly the one I just committed.

## What I am NOT claiming

**I am not claiming these strategies work.** The L1 economics are genuinely poor, the
tight-stop claim genuinely failed 0/4, and a completed search may well kill them again.
Three of the six gaps (depth family, stop caps, event expansion) are the ones that
rescued candidates on the NY lane, so there is real reason to run them — but "the kill
was premature" and "the strategy is good" are different sentences and only the first is
being asserted.

## Status change

| | was | now |
|---|---|---|
| `LDN-OBK-01` | KILLED (expectancy) | **kill VACATED — search incomplete under §5.11/§5.12** |
| `LDN-PO3-01` | KILLED (expectancy) | **kill VACATED — search incomplete under §5.11/§5.12** |

## The work to close it, in priority order

1. **Depth family, properly** — port `dep_wall_below/above_d/sz`, `dep_thick`,
   `dep_imb`, direction-resolve to behind/ahead, build `W`/`D`/`WALLSZ` analogues on the
   London window. Highest prior by a distance. `data/reference/depth_london/` already
   holds 295 days and covers the open hour on every day.
2. **Time-segment schema + MFE/MAE pack**, then re-run the §3.2 autopsy properly and
   test flow *inside* the trade.
3. **State-conditional re-tests** of every flow feature — drawdown state, post-loss,
   day regime (lookahead-audited).
4. **Event-universe sensitivity** — all touches vs first, window widening, re-entry.
5. **Stop-cap arm class.**
6. **Permutation null** on the V1×V3 combination.

Steps 1 and 2 are the ones that can change the verdict. 3–6 are required before any
verdict — kill or ship — is legal again.

## Not spent

No 2023/24 look and no sealed-flow look was spent by the vacated run, so nothing is lost
by re-opening. That is the one piece of luck here, and it is not luck — it is the
holdout discipline doing its job.
