# FINDING — agent discretion capped the winners it was built to capture

**Run:** 53 weeks chronological, 383 arming trades (NY 247 + London 136), 422 verdicts,
293 agents, 4h52m, zero agent errors. Entries frozen — every arm replays the identical fills
on the identical original stops, only the management differs. `scripts/run_intrade_replay`.

## The result

| arm | total | mean R | median R | WR | held | green | maxDD |
|---|---|---|---|---|---|---|---|
| **canon** | **+$88,290** | **0.61** | 0.13 | 52% | 10m | 13/13 | $2,121 |
| trail_1r | +$62,139 | 0.46 | 0.33 | 64% | 8m | 12/13 | $1,252 |
| lock1r_2r | +$61,630 | 0.38 | 0.33 | 55% | 10m | 11/13 | $2,110 |
| **agent** | **+$58,210** | **0.37** | **0.51** | **66%** | 6m | 13/13 | $1,432 |
| be1r | +$54,087 | 0.42 | −0.04 | 23% | 13m | 8/13 | $4,889 |

Agent vs canon: **−$30,081**, better on 181 trades, worse on 197.

## It solved the wrong problem, and it solved it well

Angus's hypothesis was explicit: *"im far more worried about taking 50% win rate 2rr to 50%
win rate average 3rr then taking it from 50 to 70% at the same average r."*

The agent delivered **52% → 66% win rate at 0.61 → 0.37 mean R**. That is precisely the trade
he did not want. It is not incompetence — the agent is *better* than canon on the metrics it
optimised: highest win rate of any arm, highest median R, 13/13 green months, second-lowest
drawdown. It built a smoother, more reliable, smaller book.

## The mechanism: it capped its own tail

Median `target_r` was **1.60R**, on a book whose winners run past 7R. The five worst trades
against canon are all `exit_reason == agent_target`:

| trade | agent R | canon R | cost |
|---|---|---|---|
| 2025-11-19 NY | 1.40 | **7.31** | −$4,697 |
| 2025-12-29 NY | 1.54 | **5.15** | −$3,853 |
| 2026-03-17 NY | 1.18 | **10.75** | −$3,446 |
| 2025-11-06 LON | 1.38 | **9.85** | −$2,921 |
| 2026-04-30 NY | 0.49 | 1.57 | −$2,070 |

Naming a target converts an open-ended runner into a capped one. The canon's expectancy lives
in a thin tail; the agent sold the tail for a higher hit rate.

Scaling out did the same thing in miniature: 120 trades, better on 68 of them, **net −$8,712**.
More wins, smaller wins, and the losses that survive are the ones that mattered.

## What DID work — and it is the thing that was asked for

Holding through the mechanical exit: **25 trades, mean R +0.97, +$1,282 against canon, better
on 15 of 25.** The Angus rule — *"if the orderflow is heavily favouring the trade still, hold
it for longer"* — is positive where it was applied.

It was applied on **7% of trades**. The agent almost never did the thing the experiment
existed to test.

## The journal did not teach it

| quarter | Δ vs canon | agent mean R | canon mean R | beat canon |
|---|---|---|---|---|
| Q1 2025-06→09 | −$2,734 | +0.11 | +0.19 | 43/96 |
| Q2 2025-09→12 | −$6,882 | +0.55 | +0.71 | 52/96 |
| Q3 2025-12→2026-04 | −$12,505 | +0.31 | +0.75 | 46/96 |
| Q4 2026-04→07 | −$7,959 | +0.50 | +0.80 | 40/95 |

No learning curve. The gap widens, and the beat rate falls from 52/96 at its best to 40/95.
The agent's own mean R does rise (0.11 → 0.50) but canon's rises faster (0.19 → 0.80) — the
second half was a better tape for holding, and the agent captured less of the improvement than
the mechanical rule did. Chronological chaining, a matched-cohort digest and a scored thesis
were all in place; none of it changed the behaviour.

## The most likely cause is the doctrine, not the agent

`.claude/agents/trade-manager.md` opens with the headroom (2.14R realised vs 7.28R available)
and then immediately warns that **78% of winners stop out if simply held** and that **every
mechanical trail loses to canon**. Both are true. Both are framed as reasons for caution, and
they are the first thing the agent reads. Its judgement section then says *"when the flow says
nothing in particular, the mechanical plan is better than a coin flip — take the exit."*

The result is an agent primed to protect. Its median target sits below the median forward run
its own journal reported. The instruction to build targets from the cohort distribution was
present; the framing around it pulled harder.

## What this does not settle

- **Whether discretion can beat canon.** This tests one doctrine, one action space, one
  53-week chain. The positive signal on held-through trades (+0.97R mean) is real but n=25.
- **Whether a learning curve is achievable.** It did not emerge here. Whether that is the
  journal design, the 400-decision sample, or the doctrine is untested.

## Next experiment, if it is run

Invert the framing: lead with the cohort distribution, require a target at or above its
median when the cohort is strong, and make capping the tail the thing that needs justifying.
Keep every control arm — the mechanical arms are what made this readable, and one of them
(`trail_1r`, +$62,139 at 64% WR and the lowest drawdown of any arm) quietly beat the agent.
