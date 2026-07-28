# PLAN — how the agent-owned run is scaffolded so a broken harness costs minutes, not a night

**ANGUS, 29-Jul:** *"i want to make sure its scaffolded properly instead of rinsing all my
usage on some shit that doesnt work."*

Fair, and earned. The 29-Jul chained run burned half a night producing **zero verdicts**
because `agentType` pointed at a name that does not resolve as a spawnable type. A two-week
smoke run would have caught it in ten minutes. Everything below is built so that each stage is
cheap to verify and the expensive stage runs only after the cheap ones pass.

---

## Part 1 — what the run actually does

### Stage A: candidate assembly (no agents)

Every trigger the detector produces in the session windows, run through the engine to the
point of a fill — **including the 449 the ladder currently rejects**. 713 candidates per span
instead of the canon's 383, because the selection decision lives in the rejected set.

### Stage B: entry decision, one per candidate

The agent sees the setup *as it stood at the trigger*: the level being traded and how price
arrived at it, what sits overhead and underneath (VWAP bands, POC, session extremes,
prior-day levels), the book, the flow, the clock, what the day has done so far.

It answers: **take or skip**, with a conviction that drives size through the frozen schedule,
and a thesis.

### Stage C: exit management, event-driven, for the life of each taken trade

Woken when something happens — new high-water mark, flow flipping against, a new swing forming,
a stall, the mechanical target being reached (as information, not instruction), or a heartbeat
so a quiet trade is never abandoned.

It answers: **hold or exit**, optionally moving the stop, optionally taking a partial. No hard
targets — a target ends the trade and an ended trade cannot be managed.

### Stage D: guardrails, mechanical, every decision

Proposals that violate the envelope are rejected fail-closed and the candidate is skipped. The
envelope is unchanged: original stop, trades per window, conviction sizing, 40-micro clamp,
−4R day halt, DD ramp, session windows, 15:55 flatten, news blackout.

### Stage E: journal and chain

Every decision written with its state and, once resolved, its outcome. The digest carried into
the next period is matched to the situation at hand, and only ever contains trades that closed
before the current period began.

---

## Part 2 — what we get out of it

### Five questions it answers

| question | how it is measured | what "good" looks like |
|---|---|---|
| **Does agent selection beat the ladder?** | its taken set vs the canon's 264, and what it skipped vs the ladder's 449 | beats 46% WR / +0.46R on a comparable trade count |
| **Does event-driven exit capture more R?** | capture ratio: realised R ÷ R available while alive | above the canon's ~2.15R median exit |
| **Does the journal actually teach?** | first third vs last third of the chain, on comparable setups | later periods better; the 29-Jul run went *backwards* |
| **What does caution cost?** | veto regret — every skip scored against what it went on to do | small; this is the known failure mode |
| **Which half carries the value?** | selection and exit contributions separated | tells us where to spend next |

### What it produces regardless of the verdict

Even if the agent loses to the canon, the run leaves three assets:

1. **A reasoned decision record over ~3,100 decisions** — every take, skip, hold and exit with
   the flow, book and geometry that prompted it. That is the substrate for everything after,
   and it is what you and Brake were reading off TradingView by hand.
2. **Veto regret data** — the first direct measurement of what over-caution costs. No
   mechanical study can produce this, because the ladder has no counterfactual.
3. **Capture ratios by setup type** — which patterns give back their move and which run,
   independent of who is managing them.

### What it does NOT settle

- Whether it generalises. That needs the holdout, which is a separate run.
- Whether it works live. Replay has no slippage beyond the modelled tick, no partial fills,
  no feed gaps.

---

## Part 3 — the scaffolding

Five stages, each with a **kill criterion**. Usage is spent only after the previous stage
passes.

### Stage 0 — reproduce a known answer. **No agents. Free.**

The pipeline replays the canon's own decisions and must reproduce the arming book to the cent,
exactly as `run_intrade_replay check` does today (383/383).

> **KILL if it does not reproduce.** This is the gate that caught the V8 partial leg, the
> canon-exit ordering bug and the stop-touch bounding this week. A harness that cannot
> reproduce a known answer cannot be trusted on an unknown one.

### Stage 1 — smoke. **~10 agents, ~15 minutes.**

Two weeks. Both decision types. Verifies the plumbing, not the strategy:

- verdicts actually land in the file (the 29-Jul failure)
- the schema validates and rejects malformed output
- guardrails reject an out-of-envelope proposal
- journal rows form with outcomes attached
- the agent type resolves and has the tools it needs

> **KILL on any zero-verdict round.**

### Stage 2 — one month, chained. **~40 agents, ~1 hour.**

Verifies the *thinking*, not just the plumbing:

- the cohort digest populates and is matched to the situation
- capture ratio computes and is sane
- veto regret computes
- **I read twenty rationales by hand.** Tonight's most valuable findings — the median-anchoring
  trap, the journal grading itself — came from reading reasoning, not from a P&L table.

> **KILL if the reasoning shows a structural trap** (anchoring on a statistic that caps it,
> citing its own record against the cohort, treating any decision as final).

### Stage 3 — full fit span, month-chained. **~8-10 hours.** The experiment.

> **Bar to clear:** beats the canon on total, on mean R, and on months green — or loses in a
> way that is diagnosable rather than diffuse.

### Stage 4 — holdout. **Only if Stage 3 clears.**

Same code, sealed 2023/24 days, the benchmark being whatever the canon does out of sample.

---

## Part 4 — failure modes and where each is caught

| failure | caught at | cost |
|---|---|---|
| agent type does not resolve | Stage 1 | 15 min |
| schema mismatch, malformed verdicts | Stage 1 | 15 min |
| guardrail not enforced | Stage 1 | 15 min |
| journal not populating | Stage 2 | 1 hour |
| a lever that terminates the decision loop | Stage 2, by reading | 1 hour |
| self-referential learning | Stage 2, by reading | 1 hour |
| over-caution / vetoing everything | Stage 2, veto rate | 1 hour |
| lookahead leak | Stage 0, structurally | free |
| strategy simply does not work | Stage 3 | 8-10 hours |

Only the last one costs real usage, and it is the only one that is a genuine result.

---

## Part 5 — cost

| chaining | run | learning granularity |
|---|---|---|
| week | ~24-36h | finest |
| fortnight | ~14-18h | good |
| **month** | **~10-12h** | 13 updates — recommended for the first full run |

Scoped first cut — **NY only, fit span, month-chained: ~8 hours** including all gates. Both
sessions roughly doubles it.

---

## Part 6 — decisions still needed

1. **Both sessions, or NY first?** London is the cleaner test (its book carries exit stamps and
   reasons); NY is where the money is. This roughly doubles the cost.
2. **Does the agent see the canon's verdict on a candidate?** Showing it anchors; hiding it
   discards information the live system would have.
3. **Fit first, or straight to 2023/24?** Fit is checkable against a known answer.

Recommendation: NY, fit, month-chained, canon verdict hidden at entry and shown at the exit
decision. Cheapest configuration that still answers all five questions.
