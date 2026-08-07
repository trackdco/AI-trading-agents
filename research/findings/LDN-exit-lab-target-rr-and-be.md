---
date: 2026-08-07
status: FINDING — there is no best target RR (the curve is flat: −3.13 to −3.73 from
  nearest to 3R). Straight BE-at-1R makes London WORSE, −4.06 vs −3.67, by scratching
  winners faster than it saves losers. The best-looking arm on net, runner-to-EOD at −0.52,
  is the WORST arm on Angus's actual objective (19% green days, median day −19.1, worst-10d
  −551) and its T is −0.36. No arm is net-positive in both eras.
tags: [london, exits, target-rr, break-even, prop-objective, era-consistency, burn-list]
sources: ["output/london_exit_sweep.md", "output/london_exit_sweep/",
          "scripts/l2_london_exit_sweep.py"]
---

# The exit lab: no best target RR, BE-at-1R hurts, and the winner on net is the loser on the objective

ANGUS: *"Can you run variables test to see what target RR is the best, and maybe test having
it go to BE after 1 RR or sum shit."*

12 arms, displacement-only, 264 sessions, deduped per arm, every trade through the real
`simulate()`. Control = `min 2R` (the shipped configuration).

## Q1 — what target RR is best? There isn't one.

| target | N | net pt | vs 2R | green | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|---:|
| nearest | 852 | −3.47 | +0.20 | 28% | −2.10 | −5.71 |
| **min 1R** | 927 | **−3.13** | **+0.54** | 27% | −2.35 | −4.51 |
| min 1.5R | 920 | −3.48 | +0.19 | 27% | −2.75 | −4.75 |
| min 2R *(shipped)* | 913 | −3.67 | — | 27% | −2.78 | −5.23 |
| min 2.5R | 903 | −3.72 | −0.05 | 27% | −2.66 | −5.55 |
| min 3R | 896 | −3.73 | −0.06 | 27% | −2.63 | −5.65 |

**The whole range from "nearest" to "3R" spans 0.6 points.** There is no optimum to find —
the curve is flat and very slightly favours nearer targets. Green days are 27–28% across
every single arm. Both eras negative everywhere.

This is the sixth independent angle to say the same thing: **the target is not what is wrong
with London.**

## Q2 — BE after 1R? It makes it worse.

| management (all on the 2R target) | N | net pt | vs 2R | green | med day | worst10d | flat stop |
|---|---:|---:|---:|---:|---:|---:|---:|
| **BE@1R, no partial** | 912 | **−4.06** | **−0.39** | 25% | −12.5 | −432 | **53%** |
| partial@1R | 913 | −3.45 | +0.22 | 33% | −5.4 | −340 | 54% |
| **partial@1R + BE** | 913 | **−3.42** | **+0.25** | **34%** | **−4.9** | **−341** | 54% |
| partial at 1st structure + BE | 913 | −3.66 | +0.01 | 26% | −8.4 | −396 | 47% |
| runner holds (no trail) | 911 | −3.88 | −0.21 | 26% | −10.1 | −427 | 47% |
| runner to EOD | 911 | −0.52 | +3.15 | 19% | −19.1 | −551 | 47% |

**Straight break-even at 1R is the worst arm in the target-comparable set.** Flat stop-outs
rise from 47% to **53%** — moving the stop to entry converts trades that would have come
back into scratches faster than it rescues trades that would have died. Six points of extra
flat exits, and −0.39 pt/trade for it.

**But BE with a partial is the best arm for the objective.** `partial@1R + BE` gives the
highest green-day rate in the sweep (**34% vs 27%**), the best median day (**−4.9 vs −7.9**)
and a materially better worst 10-day stretch (**−341 vs −446**). It is still not profitable
— but of everything tested, it is the one that moves the numbers Angus actually trades for.
The difference from the losing BE arm is banking half the position first: the scratch is
then a scratch on half, with the other half already paid.

## The trap: the best net in the sweep is the worst book for the objective

`runner to EOD` returns **−0.52 pt/trade against the control's −3.67** — by far the biggest
improvement anything has produced for London. On profit factor or net-per-trade it wins
outright.

On the prop scoreboard it is the worst arm in the sweep:

- **green days 19%** — lowest of all 12
- **median day −19.1 pt** — worst of all 12
- **worst rolling 10 days −551 pt** — worst of all 12
- **T = −0.36** — the −0.52 is statistically indistinguishable from zero
- 2025 **−2.71**, 2026 **+3.27** — era-inconsistent, and the direction that flatters it is
  the validation era, which is how a lucky tail reads

Removing the target raises expectancy by raising variance. Most days get worse; a few get
much better. That is precisely the profile Angus ruled out in his own words — *"id rather
something that can do 50 points a day consistently year on year as opposed to something
that does 200 points once or twice a week"* … *"on a probability basis a streak could kill
everything … u can literally end up back in eval jail."*

**This is the clearest demonstration yet of why `prop_score` exists and profit factor
does not.** Ranked on net, runner-to-EOD is the answer. Ranked on what gets paid, it is the
one arm you would least want to run on ten copy-traded accounts.

## The consistent finding underneath all 12 arms

| arm | RAN net | RETRACED net |
|---|---:|---:|
| nearest | +3.62 | −4.72 |
| min 2R (control) | +7.02 | −5.43 |
| BE@1R | +12.58 | −6.81 |
| partial@1R | +13.80 | −6.29 |
| runner to EOD | **+19.10** | −3.73 |

`RAN` = price never retraced to the trigger level; `RETRACED` = it did.

**Exit policy is a lever on the winners and almost nothing else.** Across the sweep the RAN
population swings from +3.62 to +19.10 — a 5× range, purely from how you manage the trade.
RETRACED never escapes the −3.7 to −6.8 band no matter what you do.

Every arm is therefore the same trade-off in a different costume: how hard do you squeeze
128 good trades, and how much do you pay on 780 bad ones. Nothing in the exit toolkit
touches the ~47% that stop out flat, because those trades never get far enough for any exit
rule to apply.

## Verdict

**No arm is net-positive in both eras.** The best full-span number is −0.52 and it fails on
every consistency measure; the best objective-aligned arm is −3.42 at 34% green days. The
bar is +4 net, T ≥ 2, N ≥ 200, green ≥ 55%, both years green. Nothing is close.

Worth stating plainly because the sweep was cheap and the temptation is to combine winners:
stacking the best target (min 1R, +0.54) with the best management (partial@1R + BE, +0.25)
buys at most ~0.8 pt against a **7.6 pt** deficit. There is no combination of exit rules in
this space that reaches the bar, because exits do not create trades and do not reach the
losing half.

And the ceiling above all of it is unchanged: every arm here alters what happens after
entry, so none alters the ~3.2 setups/day London produces. Even a perfect exit policy on a
2-hour window tops out near 26 pt/day against a 50 pt/day objective.

## Method note — the dedup convention differs from earlier reports, deliberately

These arms filter to displacement and THEN group. Every London book shipped to date grouped
the full census and filtered after, which lets a rejection_block trigger — a B2, the pattern
§3.1 REMOVED — claim a setup and suppress the displacement trigger behind it. On the rr0
book: 667 setups / −3.64 the old way, **852 setups / −3.47** this way; 185 tradeable setups
suppressed by untradeable ones. That is handoff §4's own rule (*"do not group first and
filter after"*) violated on `kind` instead of on VWAP eligibility.

The control here is therefore −3.67, not the −3.69 quoted elsewhere for the same
configuration. Arms are comparable to each other and to that control; they are not
comparable to numbers in earlier reports. The shipped books are not re-derived here — that
is a separate change needing its own gate.

Sanity check that the control is faithful: `min 2R` reproduces the shipped book's outcome
count exactly (2,139), so the configuration is right and only the grouping differs.
