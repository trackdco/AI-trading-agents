# Candidate-strategy testing runbook

How to evaluate an externally-sourced trading strategy — a YouTube channel, a course, a
forum post, a mentor's method — without spending weeks discovering it was never viable.

Derived from the StarTrading branch, which produced a clean DEAD verdict after a full
acquisition-extraction-backtest cycle. **The check that killed it was five lines of
arithmetic available on day one.** PRE-FLIGHT exists so that never happens again.

Stages run in order. Any stage may terminate the study.

| Stage | What | Cost |
|---|---|---|
| 0 | Data audit — what do we actually hold | hours, once per dataset |
| **PRE-FLIGHT** | **Six gates, none requiring data work** | **~1 hour** |
| 1 | Build the corpus | days |
| 2 | Extraction into structured records | days |
| 3 | Model census | hours |
| 4 | Cheap-kill feasibility test | days |
| 5 | Verdict and closure | hours |

---

## Stage 0 — Data audit

Inspect the actual files. Never reason from your description of them. Print schemas, sample
rows, distinct values of any action/type column, event density per session, session coverage,
bar labelling convention, contract roll behaviour.

Output: an inventory of what is computable and what is not. PRE-FLIGHT gate 5 consumes it.

Do this once per dataset, not once per candidate.

---

## PRE-FLIGHT

**Gates 1–6 are answerable from arithmetic, a timezone conversion, a file listing, or a
careful read of the source. None requires data acquisition, backtesting, or transcript
extraction.**

**Gate 4b is the exception and is deliberately placed inside pre-flight anyway.** It needs the
detector built and run over the sample — but it needs no *outcomes*, only the distributions the
stated rules produce. Run it as soon as the detector fires, before any performance measurement.
Discovering that a rule means something other than its author intended is cheap before a
backtest and expensive after one, because by then the result has a number attached and the
number will be defended.

### The principle

> **Run every gate that requires no data work before doing any data work.**

A pre-flight that terminates is **not a failed study**. It is the cheapest possible correct
answer, and it is the outcome this stage is designed to produce. Treat termination as the
success case, not the disappointing one. The stage has done its job precisely when it stops
you from starting.

### Scope discipline — read before recording any verdict

**A gate firing scopes the claim narrowly. A pre-flight kill closes a *port*, not a
*strategy*, and the write-up must say which.**

Cluster α died on NQ inside a trailing-drawdown account, because futures are quantised at one
contract. It was **not** shown to fail on forex with fractional lot sizing, where position
scales continuously with the stop and the disqualifying geometry never arises. We did not
test it there and claimed nothing about it there.

Write the verdict as *"X on instrument Y under constraint Z"*, never as *"X doesn't work"*.
Overclaiming from a cheap gate is the failure mode this whole discipline exists to prevent,
and it is easy to commit precisely because the gate felt decisive.

---

### Gate 1 — SIZING. Does one loss fit in the account?

**Run this first. It is the cheapest gate and it has the highest historical hit rate.**

For any candidate with a fixed reward:risk and a level-based target, stop distance is not a
free parameter — it is forced:

```
stop distance = (1 / R) x target distance
```

At R = 0.2 that is a stop five times the distance to the target. Method:

1. Measure the target-distance distribution from bars alone — no strategy logic needed, just
   entry reference to level.
2. Derive the implied stop distribution.
3. Convert to dollars **at the smallest available contract**. That is the floor; there is
   nothing below it and futures do not fractionalise.
4. Compare to the account's drawdown allowance.

**TERMINATES IF:** a median loss exceeds a meaningful fraction of the allowance, or a p95
loss exceeds it outright.

**Evidence.** α's median loss on MNQ — the smallest listed contract in the family — was
**$848 against a $2,000 allowance (42%)**, and its p95 loss was **$4,002 (200%)**. Bust in
**2.4 median losses**. Entirely independent of win rate: not even a 100% win rate changes it,
because the disqualifier is the size of one loss, not the frequency of losses.

**Why it goes first:** it needs only a distribution of distances and a multiplication. No
entry rule, no exit rule, no win rate, no backtest.

---

### Gate 2 — SESSION OVERLAP. Does it trade when you trade?

Convert every stated session anchor to your exchange's local time, **accounting for DST**.
Compare against your own trading window.

**TERMINATES IF:** no overlap. A model that trades at 19:00 ET cannot be tested inside an RTH
system without becoming a different strategy — and then you are testing your variant, not
the candidate.

**Evidence.** None of the three StarTrading clusters overlapped RTH 09:36–16:00 ET: α anchors
at 00:00 UTC (19:00/20:00 ET), γ at 08:30, β at an undefined broad window. Knowable from one
transcript plus a clock conversion.

**Watch for:** anchors stated without a timezone. That is itself a finding — record it as
UNKNOWN rather than assuming the obvious one.

---

### Gate 3 — BREAKEVEN VS CREDIBLE BAND. Does the claim clear its own costs?

```
p0 = (s + c) / (s x (R + 1))
```

`s` = stop distance, `c` = round-trip cost in the same units, `R` = reward:risk. Compute at
the candidate's stated RR and a plausible stop, at **three** cost levels bracketing
optimistic / realistic / stressed. Cost the *session actually traded* — overnight books are
thinner than RTH and RTH assumptions will flatter the result.

**TERMINATES IF:** the claimed win rate sits below cost-adjusted breakeven, or the margin
over breakeven is too thin to measure with the sample available.

**Note the asymptote:** as `s` grows, `p0 → 1/(1+R)`. At R = 0.2 that floor is 83.33%. A
model claiming 95% has ~12 points of headroom *before* anything else is considered.

**Watch for the inverse trap.** α *passed* this gate — worst case 87.43% against a 95%
threshold — but only because its stops were so enormous that costs rounded to nothing
against them. **It passed gate 3 by virtue of the same property that killed it at gate 1.**
A pass here is not reassurance if gate 1 has not run.

---

### Gate 4 — SPECIFIABILITY. Is there a stated rule for every trade state?

Read the source for an explicit rule covering: entry, stop, target, time-based exit, and —
the one that is almost always missing — **what happens when a trade reaches neither target
nor stop.**

**TERMINATES IF:** a state is unhandled *and* its treatment changes the sign of expectancy.

**Evidence.** α states no exit for the **~32%** of trades that do not resolve same-session.
Treating them as excluded gives **+0.076R**; treating them as losses gives **−0.337R**. The
missing rule was worth more than the entire margin over breakeven, and it straddled zero. α
was never a specifiable strategy — that is a documentation verdict, not a performance one.

**The general form:** when a result depends on a parameter the source never states, the
finding is not the result. The finding is that the strategy is underspecified. Test your own
assumptions before testing the strategy — the StarTrading study nearly reported a profitable
system that was an artefact of an arbitrary 20-day hold cap the analyst had introduced.

#### Gate 4b — LITERALISM. Do the STATED rules produce the intended behaviour?

**A stated rule frozen to its most literal reading can produce behaviour the author never
intended.** Seen three times on this strategy: the 1-tick stop buffer, the nearest-level target
rule, and the Vault cap acting as primary selector. Gate 4 tests for UNSTATED parameters. It
does not test whether STATED rules produce intended behaviour. Add that check: **for each
stated rule, compute what it actually does across the sample and compare against the author's
stated intent.**

**How to run it.** For every rule you implemented, produce the distribution of the quantity it
governs — not a spot check, the whole distribution — and hold it against the author's own
recorded behaviour or stated purpose. Median, tails, and the fraction where the rule is
degenerate.

**TERMINATES IF:** nothing. This gate does not kill a strategy; it kills an *implementation*
and sends it back for a spec amendment. Record each divergence as an amendment with a date and
a reason, tagged `[FIAT]`, and state explicitly that no outcome was compared.

**Evidence — all three from VWAP/BB, all three invisible to gate 4:**

| stated rule | literal reading produced | author's intent | ratio |
|---|---|---|---|
| §5.4 "beyond the wick extreme" | median stop **3.12 pt** | hand-log median **35.00 pt** | **11×** |
| §6.5 "nearest valid target" | median target **7.95 pt** | hand-log winners **155.2 pt** | **19.5×** |
| §10 "max 3 trades/day" | binding on 33–92% of sessions, discarding 43–86% of qualified candidates | a *risk cap*, not a selection rule | — |

Each rule was stated, implemented faithfully, and wrong. The stop and target defects also
**masked each other**: because both compressed by roughly the same factor, the R-multiple
looked healthy and three gates passed over them. What did not survive was the cost ratio —
31% of risk at a 3.12-point stop against 2.8% at 35.

**The trap this catches.** The literal reading is the *defensible* one — it is what the
document says — so it survives review by anyone checking implementation against spec. It only
fails against a check of implementation against *intent*, and intent lives in the author's
behaviour, not the document. If the author supplied a trade log, that log is the intent
reference. If they did not, this gate cannot be run and you should say so.

---

### Gate 5 — DATA FEASIBILITY. Are the required inputs computable from what you hold?

Consume Stage 0's inventory and ask the candidate-specific question: does this strategy need
anything we do not have? Inspect the **actual files** — schema, event density, distinct
action values, session coverage. Do not reason from your description of them.

**TERMINATES IF:** a load-bearing input is absent and no honest substitute exists. A
substitute that infers the missing quantity from something correlated is not a substitute —
it fabricates the variable under test.

**Evidence.** Three trade records across **67,419** order-book rows killed an entire
orderflow research stage in ten minutes. The files were named like MBP-10 event data and were
in fact 1-minute periodic snapshots. Nothing but opening them would have revealed it.

---

### Gate 6 — SAMPLE SUFFICIENCY. Does required n exceed available n?

From the claimed margin over breakeven and the estimated trade frequency, compute the
required sample and compare it to the length of history you hold.

**TERMINATES IF:** the question is not answerable on the data you have. **Record the n that
would be required, and stop.** That number is the finding — it tells whoever revisits this
exactly what would need to change.

Do not proceed hoping the effect is larger than claimed. If the design cannot detect the
claimed effect, a null result is uninformative and a positive result is noise.

---

### PRE-FLIGHT output

One page. For each gate: PASS, TERMINATE, or UNKNOWN-BLOCKING, with the number that decided
it. On any TERMINATE, write the verdict with its scope stated per the discipline above, and
**do not proceed to Stage 1**.

---

## Stage 1 — Build the corpus

Acquire source material. Manifest-driven and resumable: every result committed atomically so
a killed run loses at most the item in flight, per-run caps, backoff, and a hard stop after
consecutive failures.

Diagnose blocks rather than inferring them from symptoms — the StarTrading pull was refused
by IP reputation, not velocity, which slowing down could never have fixed.

## Stage 2 — Extraction into structured records

One record per source, fixed schema, no synthesis. Rules with timestamps, concepts, claimed
numbers with sample sizes, contradictions, discretion markers.

**`costs_included` is the decisive field.** Never infer it; UNKNOWN is a finding. Across
seven StarTrading records it returned NO once and UNKNOWN six times, and commission was never
mentioned in any video. That single field bounds how much weight any claimed number can
carry.

Premature synthesis produces a confident summary of an incomplete ruleset, which is worse
than no summary.

## Stage 3 — Model census

Tabulate a small set of hard fields across every record **before synthesising anything**:
instrument, session anchor, entry filter, RR sign, trade management.

Clusters, or scatter? Two models sharing a vocabulary is a different finding from one model
with contradictions. Do not merge clusters for tidiness. This caught **three distinct models**
hiding under one channel identity, which no amount of reading would have surfaced.

## Stage 4 — Cheap-kill feasibility test

See the kill sequence in [`CLOSURE.md`](CLOSURE.md). Sizing first, then costs, then the
empirical work.

## Stage 5 — Verdict and closure

Record the verdict with its scope. Keep the evidence trail, including superseded analysis —
the sensitivity work is usually the most reusable part. A closed branch with its evidence
intact is the deliverable.
