# SPEC — agent-owned trading, mechanical guardrails

**ANGUS, 29-Jul:** *"i want to present the agents in a condition at the entry of every trade,
and let IT decide where to exit, with the mechanical strat merely as a guideline, and let it
journal and become better at capture itself."* And: *"theres no world where mechanical performs
better than literal agents, i can out trade this mechanical baseline every day of the week...
sounds like US programming the agents wrong, not the agents underperforming."*

The record from the 29-Jul chained run supports that reading. Every failure was harness or
configuration, not judgement:

| observed failure | actual cause |
|---|---|
| 44% of its targets below `rr_floor = 2.0` | the floor was never in the doctrine or the schema |
| held through the mechanical exit on 7% of trades | doctrine opened with two cautions and told it to exit when unsure |
| **median 1 decision per trade** | naming a target closed the trade before any second look could happen |
| learning curve ran downhill (Q1 −$2.7k → Q4 −$8.0k) | journal graded it against its own record, which was bad *because of the above* |
| 53 weeks producing 0 verdicts | `agentType` pointed at a repo agent file, which does not resolve as a spawnable type |

Its reasoning was sound throughout — correctly reading `path_efficiency 0.008` as chop, a
5-lot wall as too thin to respect, absorption at the highs. It lifted win rate 52% → 66% and
saved **+$27,491** on the trades the canon loses. It was asked the wrong question, once.

---

## 1. Inversion

The canon stops being the spine and becomes the **benchmark**. The agent owns:

- **selection** — whether to take a candidate at all
- **exit** — where and when, revisable for the life of the trade
- **conviction** — which drives size through the existing frozen schedule

The mechanical stack owns the risk envelope, and nothing inside the agent can touch it.

---

## 2. The guardrail contract — mechanical, non-negotiable

Confirmed by Angus 29-Jul (*"trades per window, risk metrics we have all should still apply,
and also sizing per trade based off of conviction. this is optimised for funded accounts, and
i wont want to change that"*):

| guardrail | source |
|---|---|
| original structural stop | engine, at trigger resolution |
| trades per window (2 pre / 2 gold / 2 London) | `max_trades_per_day` per section |
| conviction-based sizing | `gate_evidence.expected_micros`: `risk_$ = base_dollar(avail_dd) × min(2.0, conviction)` |
| 40-micro clamp | `MICRO_CLAMP` |
| −4R account day halt | `SpineConfig.daily_loss_halt_r` |
| DD halt / ramp to zero | `base_dollar`, `dd_halt_buffer` |
| session windows | 08:00-09:30, 09:40-10:15, London 08:00-10:00 UK |
| 15:55 flatten | `eod_flatten` |
| pre-open news blackout | `src/canon/news_gate` |

The agent proposes; the spine disposes. Any verdict that violates the envelope is rejected
fail-closed and the candidate is skipped — never widened, never re-sized upward.

---

## 3. Two decisions, not one

### 3.1 ENTRY — at the trigger

Every candidate the detector produces, including the ones the ladder currently rejects. The
selection decision lives in that rejected set, so the agent must see it: **713 candidates per
span, not the 383 the canon takes.**

Briefing carries what the canon's checks read, PLUS the context the checks cannot express:
the level being traded and how price arrived at it, what sits overhead/underneath (VWAP bands,
POC, session extremes, prior-day levels), the book, the flow, the clock, the day's character
so far.

Output: `take` / `skip`, a conviction that drives size, and a thesis.

> The trade that prompted this spec: a long resting into the VWAP mid stacked with POC,
> approached from below, filled by the very drop that invalidated it. Measured across the fit
> book, that setup is **17 trades for +1.0R over 13 months** — dead money the ladder cannot
> see, because "which side price approached the confluence from" is not one of its five checks.
> This is not an argument for adding a sixth check. There is an unbounded supply of these and
> a rule per instance is a treadmill.

### 3.2 EXIT — for the life of the trade

The agent is woken **on events, not on a fixed schedule** — a fixed schedule is what produced
one decision per trade:

- a new high-water mark in the trade's favour
- flow flipping against (CVD sign change on the 5- or 15-min window)
- a new swing forming (structure it can trail behind)
- the mechanical target being reached — *as information, not as an instruction*
- a stall (N minutes with no new extreme)
- a hard heartbeat so a quiet trade is never abandoned

Output: `hold` / `exit_now`, an optional stop level, an optional partial. **No hard targets.**
A target ends the trade, and a trade that has ended cannot be managed — that single mechanism
caused 79% of the losses in the 29-Jul run. If a target is ever reintroduced it must be
revisable at every subsequent wake; a plan that can be updated is not a cap.

---

## 4. Journal — what it must learn from

One row per decision, carrying the state at the decision AND the forward outcome, so cohort
retrieval can answer *"what happened last time it looked like this"*.

Two rules learned the hard way on 29-Jul:

1. **Score capture, not obedience.** `realised R ÷ R available while alive`, per trade. The
   old journal asked "was overriding the canon right", which is a different and less useful
   question.
2. **Never let the journal grade the agent against its own record alone.** It cited
   *"holds here avg −$124"* to justify cutting sooner — a record that was negative because its
   earlier holds were too small. The loop ran downhill. Cohort statistics measure what the
   MARKET did; own-record measures only what the agent did. On disagreement, the cohort wins.

For entries, the journal must also carry **veto regret**: every skipped candidate scored
against what it actually went on to do. Without it, over-caution is invisible until it shows
up in a quarterly total — and over-caution is this agent's known failure mode (Angus, 27-Jul:
*"it shouldnt be scared to trade"*).

---

## 5. Scoring — what beating the baseline means

Never a single number. The canon is the benchmark on all of:

| metric | why |
|---|---|
| total P&L, funded sizing | the account's actual result |
| mean R and median R | Angus's stated goal is R, not win rate |
| capture ratio | realised ÷ available — the thing being optimised |
| months green | the canon's 13/13 is the consistency bar |
| maxDD | funded accounts die on drawdown, not on averages |
| trades taken | a book that beats canon on 30 trades has not solved the same problem |
| veto regret | the cost of caution, in R |

---

## 6. The selection bar, stated honestly

The ladder it replaces is not a naive filter:

    ladder REJECTED  449 candidates: WR 19%  mean R -0.42  (would have lost $73,806)
    ladder TOOK      264 candidates: WR 46%  mean R +0.46  (made $49,277)

An agent with a veto has to beat that. The way it loses is not by taking VWAP-mid longs — it
is by skipping winners it found unconvincing. Veto regret is the instrument for that and it
should be read every run.

---

## 7. Failure modes to design against — from the 29-Jul run

1. **Any lever that terminates the decision loop.** Targets did. Anything final does.
2. **Cautions stated before opportunity.** The doctrine's ordering changed the behaviour more
   than its content did.
3. **Statistics quoted at the agent that describe a strategy nobody proposed.** "78% of winners
   stop out if held" measures holding to 16:00 on the original stop with no management. It is
   a fact about doing nothing and it taught the agent to flinch.
4. **Self-referential learning.** See §4.2.
5. **Anchoring targets on a cohort median.** Caps at the median by construction; the tail
   becomes unreachable no matter how good the read.
6. **Unregistered agent types.** Verify the type resolves before launching anything long.
7. **Batching decisions that can see each other.** Two same-day briefings in one prompt hand
   the earlier one its own future.

---

## 8. Cost

The agent is live for the whole life of every trade and sees ~713 candidates per span rather
than 383. Event-driven waking is what keeps this affordable — a quiet trade generates no
events. Expect the 15-20 hour class of run, not the 5-hour one.

---

## 9. Open, needs Angus

- **Both sessions at once, or NY first?** London is the cleaner test (its book carries exit
  stamps and reasons) but NY is where the money is.
- **Does the agent see the canon's verdict on a candidate?** Showing it anchors; hiding it
  loses information the live system would have.
- **Fit first, or straight to 2023/24?** Fit is checkable against a known answer; the holdout
  is the real question.
