# Scoring against a funded-account objective

Per-trade expectancy is the wrong objective for any account with a hard failure condition. The right one is the probability of reaching the goal state before the failure state, which is path-dependent — and expectancy and survival rank strategies differently. A strategy can win on expectancy and lose on the objective that actually pays.

Get this right before running any selection study, because every variable measured under the wrong objective may have to be re-measured under the right one.

## Establish the actual rules first

These vary by firm and change often, so read the current documentation rather than relying on a summary. The parameters that change the answer:

- **Is the drawdown checked intraday or end of day?** This is the single most consequential rule. If it is checked only at the close, intraday excursion is free — the account cannot be knocked out mid-session, only by the settle. That makes the distribution of *daily closes* the correct risk object rather than the path, which makes a day-block bootstrap exactly the right tool, and it means gambler's-ruin framings that assume a continuous barrier substantially overstate ruin risk.
- **Does the drawdown trail, and does it lock?** A trailing floor that freezes once a threshold is banked makes the problem two-phase: before the lock, effective room is constant and the floor chases you; after it, every further gain is cushion. The optimal seat on the risk curve should therefore *change* at the lock — minimum variance before, more variance tolerable after.
- **Is there a minimum profit threshold for a day to count as a qualifying day, and what is it in dollars?** This is frequently the binding constraint and is frequently not in public write-ups. Get the exact figure; without it the whole design question is unanswerable.
- **How many qualifying days per payout cycle, and is there a consistency rule?** Consistency rules (largest day capped as a fraction of total profit) and qualifying-day floors want *opposite* strategy shapes, so check whether both apply and in which phase.
- **What happens on a breach** — reset, or account death? And is there a cap on total payouts or accounts, per household rather than per login? Caps determine whether the account is an income stream or a qualification ladder, which changes the objective entirely: under a payout cap, nearly every policy extracts a similar amount while death rates vary enormously, so survival becomes the only thing that discriminates between policies.

## Why the two extremes both fail

**High risk-reward with a low hit rate fails on the drawdown.** At matched expectancy, a low-win-rate leg carries roughly double the per-trade volatility of a high-win-rate one, and losing streaks scale brutally: over a hundred trades the expected worst streak at an eighty percent win rate is around three losses, and at forty percent around nine. An automated strategy takes every one of them with no discretion to sit out.

**Very low risk-reward with a high hit rate fails on the dollar floor.** R is scale-free; the qualifying-day floor is a dollar amount. A target small enough to hit eighty percent of the time may produce a day that cannot clear the floor even when most trades win — structurally dead regardless of hit rate.

**So the optimum is mid-curve:** the highest win rate obtainable at a risk-reward of roughly one to two, and the binding constraint is usually **size**, not win rate. Because the floor is in dollars and R is not, the same strategy can fail the floor at one risk tier and clear it comfortably at another. The design problem is therefore a joint optimisation over target *and* size, never a target choice followed by sizing.

## The scoring function

Replace per-trade R with: **the probability of achieving the required number of qualifying days and the profit target before a drawdown breach.**

Implement it as a day-block bootstrap — resample whole days with intraday order preserved — because that matches the unit at which the account is actually evaluated and the unit at which trades are genuinely independent.

Report per candidate: probability of reaching payout, probability of breach, expected days to payout, distribution of daily closes, and the qualifying-day rate. Keep per-trade expectancy in R alongside as a diagnostic, but do not rank on it.

## Consequences for the research programme

**Every cut must be scored on two axes.** A filter that raises expectancy per trade while halving trade count can *reduce* the number of qualifying days, because frequency is what manufactures them. Report expectancy and frequency together, always.

**Once the book is positive, the objective for further selection changes** from making it positive to concentrating it enough that days clear the dollar floor. A cut that raises R per trade and keeps frequency helps; one that raises R and destroys frequency may not.

**Partial exits are worth more than their expectancy suggests** when their job is manufacturing qualifying days rather than maximising R. A partial that adds little to per-trade expectancy can materially raise the qualifying-day rate, and under this objective that is what counts.

**A state-dependent intraday policy becomes available and requires no market prediction.** Once a day is green, a scarce asset has been banked and further trading risks destroying it. "Stop or de-risk once green by a stated amount" is codeable, testable with the same day-block bootstrap, and needs no forecast.

**Position-limit structure may dominate strategy choice.** Where accounts are capped and simultaneous accounts run the same strategy, copy-traded accounts have zero diversification — the probability that half die and the probability that all die are the same number. Staggering entry into funding, rather than running idle accounts, can cut total-wipeout probability by orders of magnitude for free. This turns genuinely uncorrelated strategies from an aspiration into a requirement for scale.

## What the structure does and does not give you

It **reduces the edge required** — an end-of-day-checked barrier plus a downside capped at the evaluation fee are real gifts, and at modest positive expectancy with reasonable room the ruin probability becomes small. It does **not remove the requirement for positive expectancy**. That is still the entry ticket, and no amount of favourable account structure substitutes for it.
