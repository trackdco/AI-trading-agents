# HYPOTHESES — how to capture more R

**Angus, 29-Jul:** *"hypothesise on how we can make the bots better at capturing more r... its
really good that it increased win rate by a fair margin, but it also sacrificed alot of
profit."*

Everything below is measured on the 383-trade arming book, not asserted. The measurements
changed my view of the problem twice while writing it.

---

## The shape of the opportunity — this is the whole thing

Holding past the canon's exit, walked forward honestly with a stop, on the 188 trades where
the canon exits in profit:

| policy | mean R | median R | total R | vs canon | better on |
|---|---|---|---|---|---|
| take the canon exit | 2.39 | 2.15 | 449 | — | — |
| hold, stop at break-even | 2.35 | **0.00** | 441 | −8R | 26/188 |
| hold, stop at half the canon R | 2.61 | 1.11 | 491 | +43R | 17/188 |
| **hold, stop AT the canon exit level** | 2.61 | 2.18 | 490 | **+41R** | **4/188** |

**Holding is right about one time in ten, and the entire gain comes from four trades.**

That single fact explains every result we have. The agent cut because on a per-trade basis
cutting genuinely is right ~90% of the time. Every mechanical trail loses because it pays the
90% cost to reach the 10%. The agent's journal taught it to cut harder because its own record
was dominated by the 90%.

It also kills the naive reading of the headroom. "Winners realise 2.14R against 7.28R
available" is true, but measured to 16:00 the median trade also goes **−7.95R against** the
canon exit price somewhere in that window. The room is real; so is the risk of reaching for it.

---

## H1 — Convert the canon exit into a zero-give-back trail (mechanical, no agent)

Instead of exiting at the canon's price, **place the stop there and let it run**.

    identical to canon : 184 trades  (each pays ~1 tick = 0.016R)
    ran further        :   4 trades  ->  +41R
    NET after slippage :  +38R   (+0.204R per trade)

The runners:

| trade | canon R | held R |
|---|---|---|
| 2026-02-16 NY short 09:01 | 1.66 | **6.38** |
| 2026-02-19 LON short 03:34 | 1.54 | **10.90** |
| 2026-02-25 NY long 09:23 | 1.93 | **17.26** |
| 2026-06-25 NY short 09:07 | 2.01 | **14.08** |

You cannot do worse than canon by construction — the stop sits where canon would have exited —
so the 90% costs a tick and the 10% is free optionality.

**The slack is the whole rule, and it is unforgiving:**

    stop AT the canon level      +38R
    stop 0.25R below            −5R
    stop 0.50R below           −51R
    stop 1.00R below          −143R

Give the trade *any* room to breathe and the 184 give-backs swamp the 4 runners. This is why
every trail tested has lost: they all breathe.

---

## H2 — The ceiling is the TARGET MODEL, not the exit management

R at the canon's exit, winners only:

| band | n | share |
|---|---|---|
| < 1.5R | 55 | 29% |
| **1.5–2.5R** (the `rr_floor` band) | **59** | **31%** |
| 2.5–4R | 52 | 28% |
| > 4R | 22 | 12% |

Median **2.15R** — sitting right on `targets.rr_floor = 2.0`. The canon is *designed* to take
about 2R, and it does. The "7.28R available" figure is measured against a system that aims at
2R by construction.

So the largest lever may not be in trade management at all. It is §6's target menu: when the
structure ahead is thin and the next real level is far away, the target could walk further out
at entry instead of resolving to the first level that clears 2R. That is a mechanical change,
it is testable on the existing substrate, and it needs no discretion.

**This is the hypothesis I would test first.** It attacks the cause rather than the symptom.

---

## H3 — Ask the agent the wrong question and you get a rational wrong answer

The decision point currently asks *hold or exit*. Given a 90/10 split against holding, a
well-calibrated agent will almost always exit — and ours did, holding on 7% of trades. It was
not being timid; it was being correct about the marginal trade.

**Reframe it to "where does the stop go".** Under H1 the downside of staying in is one tick, so
the question stops being a gamble and becomes stop placement. The agent's read then expresses
itself without a fear tax, and its demonstrated skill — it lifted win rate 52% → 66%, so it
genuinely can tell when a trade is in trouble — gets applied to the part it is good at.

---

## H4 — Ask at the right moment, not just the mechanical one

The peak lands a median **52 minutes** after the fill (`FINDING-exit-discretion-headroom`),
while the canon exit lands at a median **10 minutes**. At the canon exit the agent is being
asked to forecast forty minutes ahead from a two-minute-old tape.

Under H1 that forecast is no longer needed at the exit — but it becomes the right question
*while extended*. Re-checks currently run every 30 minutes; on a trade that is running, every
10 would let the read update as the move develops rather than committing once and waiting.

---

## H5 — Split the two skills; they pull in opposite directions

The agent is measurably good at **cutting** and measurably bad at **capturing**. Those are not
the same skill and this run showed they trade off directly (WR +14pp, mean R −0.24).

Proposal: the agent owns the `reached_+1R` decision — *"is this trade in trouble"*, which is
what it does well — and the zero-give-back trail owns the exit, mechanically. Nobody is asked
to do both at once.

---

## H6 — Stop letting the journal grade itself *(shipped)*

The agent repeatedly cited its own record to justify cutting: *"holds here avg −$124"*,
*"prior holds averaged −$359 vs canon"*. That record was negative because its earlier holds
were too small, so the journal reported that holding loses and pushed it to cut sooner still.
The loop ran downhill — Q4 (−$7,959) was worse than Q1 (−$2,734) with four times the data.

Fixed: the doctrine now says trust the cohort's `further_R` over your own record when they
disagree, because the cohort measures what the *market* did and your record only measures what
*you* did.

---

## H7 — Do not try to predict the four

4 of 188 is a 2% base rate on a sample of four. Nothing can be fitted to that without
overfitting it, and the `intrade_flow_autopsy` ceiling was already AUC 0.69 on the much easier
+1R question. The correct engineering response is not a better predictor — it is H1's
structure, where being wrong about the other 184 costs a tick.

---

## What I would run, in order

1. **H1** — add `trail_at_canon` as a mechanical arm and grade it beside the others. Cheap,
   no agents, and it is currently the best-evidenced idea here.
2. **H2** — re-resolve targets with a wider menu walk and re-score. Attacks the cause.
3. **H3 + H5** — re-run the chained test with the reframed question, if 1 and 2 leave anything
   on the table.

The already-shipped fixes (2R floor enforced, p75 anchoring, journal self-reference) all point
the same way, but none of them changes the 90/10 shape. H1 does, and it does it without asking
anyone to predict anything.
