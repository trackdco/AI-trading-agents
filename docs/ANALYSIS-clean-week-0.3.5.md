# The clean week on 0.3.5 — 2026-06-21 to 2026-06-25

Uncontaminated re-run of the full narrated week after the steered run was discarded.
Every briefing was FACT-ONLY: no doctrine quotes, no rulings, no ALL-CAPS attention
fields, no questions containing their own answer. This session read only
`docs/RUNBOOK-replay-scoring.md` and the agent contracts. It did not open
`TEACHING-LOOP.md`, the ANALYSIS docs, or anything under `data/narrated_days`.

All five days pass `audit_run_leak` with exit 0 on all six checks, including check D
(narrated-corpus answer-key markers) and check F (his 112 recorded quotes).

## Per-day result

| session-day | R (full-target) | R (blended) | fills | W | L | BE | takes that never filled |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-06-21 | +3.23 | +2.63 | 3 | 2 | 1 | 0 | 3 |
| 2026-06-22 | +5.89 | +2.19 | 4 | 2 | 2 | 0 | 1 |
| 2026-06-23 | −0.42 | −0.67 | 5 | 2 | 3 | 0 | 0 |
| 2026-06-24 | −1.96 | −2.10 | 4 | 1 | 3 | 0 | 0 |
| 2026-06-25 | −3.00 | −3.00 | 4 | 0 | 3 | 1 | 4 |
| **week** | **+3.74** | **−0.95** | **20** | **7** | **12** | **1** | **8** |

- **Win rate: 7/20 = 35.0%**
- **Average winner: +2.18R full-target, +1.51R blended**
- Average loser: −0.96R blended
- Expectancy per fill: −0.05R blended
- 28 takes → 20 fills (71% conversion); 17 passes; 32 candidates mechanically gated

The two numbers diverge because the full-target convention credits a runner with the
R of the furthest target it reached. Blended is the honest one and the one to compare
versions on.

## Escalation report

| session-day | candidate | granted | Tier 1 | result |
|---|---|---|---|---:|
| 2026-06-21 | C5-D21-NYA5-1018 | yes | accommodated | +2.17 full / +1.83 blended |
| 2026-06-22 | C5-D22-NYA3-0940 | yes | accommodated | +6.41 full / +2.95 blended |
| 2026-06-23 | C5-D23-NYP1-0816 | yes | accommodated | −1.00 |
| 2026-06-25 | C5-D25-NYA2-0942 | yes | accommodated | −1.00 |

**4 raised, 4 granted, 4 accommodated, 0 re-affirmed.**

Every escalation was raised by the trigger agent unprompted on a fact-only briefing,
and every one was granted by the orchestrator's gate rather than by me. Tier 1 never
once re-affirmed — it accommodated all four times, twice by widening a condition and
twice by relocating a stale level. On 2026-06-22 it flipped its bias outright.

The four escalation trades net **+6.58R full / +2.78R blended**. The other sixteen
fills net **−2.84R full / −3.73R blended**. The escalation rule is the only thing
keeping the week's full-target number positive — and 0-for-4 on re-affirmation is
itself a finding: a Tier 1 that always accommodates is not being tested by the rule,
it is being led by it.

## The three cases you asked me to check

**Tuesday ~03:24 London short** — taken, `take_full` short, and it worked: +1.48R
full / +1.24R blended. Note this is a *correction*. It was originally scored +2.59 /
+1.76; the T23 trail had never been applied by the scanner, and with the runner
trailed out at +0.5R rather than credited with reaching target 2, the honest number
is lower.

**Tuesday 09:36–09:40 long** — the week's best trade, +6.41R full / +2.95R blended,
and it only exists because of the escalation rule. The trigger first returned `pass`,
then escalated: the thesis licensed longs on reclaiming vwap_m1, which it had priced
at 29,773.09 at 09:30, but by 09:40 the live band read 29,718.96 and price at
29,780.75 had cleared it by 62 points. **A developing band had been quoted as a fixed
number.** Tier 1 accommodated, flipped short to long, and the re-adjudication took it.
Worth noting that the same window's earlier 09:36 short lost 1R — the agent was
short, then long, four minutes apart, and was right the second time.

**Wednesday 09:45 short** — this candidate does not exist in the clean run. The
scanner produced 09:34 (buffer-gated), 09:42, 09:54 and 09:57 for that window and no
09:45. The nearest, 09:42, was taken `take_full` short and is the one genuinely
ambiguous trade of the week: its limit, its first target and its stop were all touched
inside the single minute starting 09:42 (low 29,612.75, high 29,662.50). One-minute
bars are the finest data available, so the intrabar order is unknowable. **Scored
pessimistically as a full stop, −1.00R.** The optimistic reading is +1.50R full /
+1.25R blended — a 2.25R swing on one trade. It is recorded as the loss because
assuming the favourable ordering is how a replay flatters itself.

## What actually cost the week

**1. Limits that ask price to come back, on tape that doesn't.** Eight of 28 takes
never became positions. Friday is the clearest case: all four London candidates were
takes — the agents wanted every one — and three never filled. Twice the cancel sat
*closer to price than the entry did*, so the order could only ever be cancelled, never
filled. Once the cancel and the first target were 2 points apart, meaning the order
was pulled at almost exactly the price it was aiming to profit at. This is the T20/T12
collision and it is the single largest source of lost participation.

**2. Window caps spending the day's budget on the wrong trade.** On 2026-06-24 the
NY_PRE cap of one fill was used at 08:06 on a trade that stopped. The 08:33 candle
then ran 30,130 → 30,206 through five levels and was gated unadjudicated. Same shape
on 2026-06-23, where London's two fills were spent before his own setup appeared.

**3. Direction.** The agents were short-biased into two days that bottomed. On
2026-06-25 every fill was a short into a range that had already swept its low and
reclaimed.

## Defects found and fixed during the run

Four scoring or input defects were found *while* running, three of which were
inflating results:

- **T23 was never applied by the scanner.** The 25% runner rode the original stop, so
  a runner trailed out at +0.5R was credited with reaching target 2. Found by checking
  a 13.75pt MAE against a 14pt stop — too close to be luck. Re-scored every fill: day
  1 unchanged, two trades corrected downward. The trail now defaults ON.
- **A briefing carried the next minute's close as a 3m close.** It inverted the read
  and licensed a short that should not have existed. Voided; a fresh agent on correct
  data returned `pass`. Candles are now derived from bars, never typed, and the builder
  refuses to emit a briefing whose numbers disagree with the tape.
- **A trigger was served a dead thesis.** After Tier 1 was re-fired on a breached
  invalidation, the builder's lookup matched only rows typed `thesis` and skipped
  `thesis_refire`. Voided; on the correct thesis the verdict went `pass` →
  `take_full`, and the trade made +1.04R.
- **tscan reported its T13 block for trades that had already closed**, which reads as
  a breakeven on a position that no longer existed.

Two things were **not** smoothed over: the 10:44 verdict on 2026-06-24 put its first
target at 0.98R and the 09:42 pass-2 on 2026-06-25 at 0.93R — both outside the 1.0–2.5R
band. Both were scored exactly as specified rather than re-rolled, because discarding
a trade after seeing it lose is choosing which results to keep.

## Open questions for you

1. **T13 on a green carry.** "BE if green" admits two readings — book flat at the
   open, or move the stop to entry and let it run. Friday's carry was the week's first
   green one; both readings gave 0.00R because the 09:30 bar traded back through entry
   immediately. It is unresolved and will matter on a green carry that keeps running.
2. **The inverse escalation detector over-triggers.** It flags any pass that names a
   rejection behind a same-candle break, and cannot see that a co-present *non-thesis*
   constraint (headroom, HTF alignment) independently kills the trade. Twice the agent
   correctly declined to escalate on exactly that ground. Not changed mid-run, because
   altering enforcement between days would make the days incomparable.
3. **Zero re-affirmations in four escalations.** Either the triggers only escalate when
   they are right, or Tier 1 defers too readily. Worth a deliberate test.

## Scope

This rules out lookahead. It does **not** establish out-of-sample: the prompt doctrine
was distilled from these same narrated days. Out-of-sample requires post-corpus days,
and bars run to 2026-07-15.
