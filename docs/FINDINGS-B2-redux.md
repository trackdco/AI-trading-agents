# FINDINGS — B2 REDUX: pricing the bust (2026-08-07)

Five items on the bust rate. Short answer to the framing question: **your
discomfort was misplaced for the reason you suspected, and justified for a
reason neither of us had modelled.** B2's per-account bust rate was the
wrong statistic — but so was the extraction number it was traded against,
because three firm rules that govern the whole problem were not in the
model. Those come first, because everything downstream moves.

Method: the B2 grid is replaced by a full LIFECYCLE simulation — eval →
funded → breach → buy a new eval → ... over a 250-day year — so a bust is
paid for in fees AND in the funded days it costs, by construction rather
than by arithmetic afterwards. Day-block bootstrap, whole days resampled
with intraday order preserved, 2,000 draws, seed 20260807. Book: A+S1
(first-of-fight reject, flow-agreeing), 832 fights / 275 days, +0.257R.
Scripts: `scripts/htf_ma_account_lab.py`, `scripts/htf_ma_portfolio_lab.py`.

---

## 0. THREE VERIFIED RULE FINDINGS THAT RESHAPE THE PROBLEM

All three fetched live from Lucid's own Help Center on 2026-08-07 and
marked VERIFIED-CURRENT. Sources in the appendix.

**0a. The 33-account plan is not permitted.** Max **10 accounts total**
(evaluation + funded combined) and max **5 funded**, *per household or
family* — not per login. One profile per trader, permanent, and profiles
"cannot be converted, deactivated, or replaced to create a new profile,"
which closes the register-a-business workaround explicitly. 33 exceeds the
cap by more than 3×. **This is a hard input to every number in item 4 and
it needs resolving before any capital plan is built on the fleet.**

**0b. There are at most 5 payouts per funded account, then the account
moves to LucidLive.** The sim-funded stage is not an income stream — it is
a *qualification ladder* with a hard ceiling. Combined with "max request =
50% of profit, capped at $2,000" and the 90/10 split, one 50K Flex account
can return at most ~$9,000 net in its sim-funded life, ever. B2's implicit
"withdraw forever" assumption inflated annual extraction by roughly 3×.

**0c. A funded breach kills the account; only evaluations are
resettable.** B2 modelled a bust as a cheap reset. It is not: a funded
breach destroys the account and you re-enter at the evaluation stage on a
newly purchased eval.

A fourth rule was found and modelled: the Flex **evaluation** carries a
**50% consistency requirement** (largest single day ≤ 50% of account
profit, measured at the moment of pass; funded Flex has none). Tested
directly — at the recommended $150 eval size it is **non-binding**: net
$8,689 → $8,683 and account-death 24.6% → 25.2% with the rule on. It only
starts to bite at eval sizes large enough for one day to be half the
$3,000 target, which is a reason not to size the eval up.

---

## 1. PRICE THE BUST INSTEAD OF MINIMISING IT

**Your arithmetic was right, and the world it applies to has been ruled
out.** Two worlds, same book, same policies:

*Counterfactual (payouts uncapped — what B2 implicitly assumed):*

| policy | net/yr | funded-death P(≥1) | fees/yr |
|---|---|---|---|
| 150→150 wd@$6k | $18,461 | 11.9% | $159 |
| 150→300 wd@$6k | **$28,280** | 27.9% | $190 |
| 150→600 wd@$6k | $29,879 | 45.4% | $250 |

Here your instinct is exactly correct: (150→300) beats (150→150) by
~$9,800/yr, and the extra death risk costs ~$30/yr in fees plus some
downtime. Priced rather than counted, the higher-size option wins by a
wide margin — the discomfort *was* misplaced.

*The verified world (5-payout cap):*

| policy | net/yr | p05 | funded-death P(≥1) | funded days |
|---|---|---|---|---|
| 150→150 wd@$6k | $8,695 | $8,645 | **11.8%** | 123.0 |
| 150→300 wd@$6k | $8,683 | $8,610 | 25.2% | 86.9 |
| 150→300 wd@$4k | $8,646 | $8,515 | 35.9% | 79.5 |
| 150→600 wd@$4k | $8,380 | $4,785 | 50.3% | 74.0 |

The cap flattens extraction to ~$8,700 for *every* policy — nearly all of
them reach 4.9 of 5 payouts inside a year. So the compensation that
justified the extra risk disappears: **you are buying 2–4× the account-
death probability for about $0.** In the world that actually exists, the
answer inverts and small is unambiguously correct.

Why the bust is nearly free in dollars but not in outcome: annual fees run
$155–$273 (one or two resets), which is noise against $8,700. The real
cost is *time* — a dead funded account sends you back to the eval queue,
and what you are actually racing for is the 5th payout and the move to
LucidLive. Under the cap, minimising death probability at equal net is the
whole optimisation.

## 2. THE WITHDRAWAL POLICY — CONFIRMED, AND IT IS FREE

Your mechanism is correct and it is the cheapest lever on the board. Post-
lock the floor is frozen at start, so cushion *is* the distance to ruin,
and every payout resets it to the minimum. Holding for more cushion before
withdrawing:

| policy | net/yr | funded-death P(≥1) |
|---|---|---|
| 150→300 **wd@$4k** | $8,646 | 35.9% |
| 150→300 **wd@$6k** | $8,683 | 25.2% |
| 150→300 **wd@$8k** | $8,680 | 22.2% |
| 150→150 wd@$4k | $8,715 | 18.3% |
| 150→150 **wd@$6k** | $8,695 | 11.8% |
| 150→150 wd@$8k | $8,583 | 11.6% |

Your "~13R" figure is exactly right, and it is the whole mechanism. Since
the request is capped at min(50% of profit, $2,000), the post-payout
cushion is:

| withdraw at | post-payout cushion | cushion in R at $150 |
|---|---|---|
| $4,000 | $2,000 | **13R** — your number |
| $6,000 | $4,000 | 27R |
| $8,000 | $6,000 | 40R |

Raising the threshold from $4k to $6k doubles the post-payout cushion and
cuts account-death probability by **11–14 percentage points for ≤$40/yr**. Beyond $6k the gain flattens and
time-to-first-dollar keeps rising (60d → 76d → 93d), so **$6k is the knee
and the declared recommendation**. Year-end sweeping is strictly worse
under the cap: it forgoes payouts entirely (0.00 taken) while carrying the
same risk. Your "12 cycles a year at ~2% each" intuition was structurally
right; the cap means it is ~5 cycles, not 12, which is why the observed
per-cycle cost matters *more* per cycle, not less.

## 3. CUSHION-PROPORTIONAL SIZING — THE FRESH HYPOTHESIS EARNS ITS TEST

Declared as a new hypothesis, not inheriting the old buffer-scaled
verdict: this is a different book with a measured edge. `size = clip(k ×
cushion, s_min, s_max)` post-lock, flat $150 pre-lock.

*Capped (verified) world:*

| policy | net/yr | funded-death P(≥1) |
|---|---|---|
| **k=0.05 [75,300] wd@$6k** | **$8,718** | **9.4%** |
| k=0.05 [150,300] wd@$6k | $8,740 | 12.1% |
| k=0.10 [75,600] wd@$6k | $8,719 | 12.6% |
| k=0.15 [150,600] wd@$6k | $8,631 | 28.1% |
| flat 150→150 wd@$6k | $8,695 | 11.8% |
| flat 150→300 wd@$6k | $8,683 | 25.2% |

*Uncapped counterfactual — where the money can actually move:*

| policy | net/yr | p05 | funded-death P(≥1) |
|---|---|---|---|
| **k=0.10 [75,600] wd@$6k** | **$30,251** | $12,470 | **12.7%** |
| k=0.15 [150,600] wd@$6k | $30,589 | $10,410 | 28.7% |
| flat 150→600 wd@$6k | $29,879 | $6,748 | 45.4% |
| flat 150→300 wd@$6k | $28,280 | $12,210 | 27.9% |

**VERDICT: cushion-proportional sizing dominates flat two-phase sizing on
both axes simultaneously.** In the uncapped world k=0.10 [75,600] earns
statistically the same money as flat 150→600 ($30.3k vs $29.9k) at **less
than a third of the account-death rate** (12.7% vs 45.4%), and nearly
doubles the 5th-percentile year ($12,470 vs $6,748). In the capped world
k=0.05 [75,300] is the lowest-risk policy tested at the best net. The
mechanism is obvious in hindsight: flat post-lock sizing bets the same
dollars whether you are $6,000 or $400 above a frozen floor.

This is a fit-book result and it inherits every in-sample caveat in item 5,
but the *ordering* is robust across the haircut grid.

## 4. THE PORTFOLIO PROBLEM — THE NUMBER THAT DECIDES IT

**Your framing is correct and the simulation makes it stark.** N accounts
on identical signals at identical starts are not N risks — they are
literally one account multiplied. The proof is in the output: for every
simultaneous configuration, P(≥50% of accounts die in one month) and P(ALL
die in one month) are *the same number* (24.2% / 24.2%). There is no
diversification at all, at any N.

What the per-account rate would have implied, versus the truth (N=33,
uncapped, 150→300 wd@$6k):

| | mean net | p05 net | monthly CV | zero-cashflow months | P(≥50% die in one month) |
|---|---|---|---|---|---|
| 33 **independent** streams | $927,311 | $850,884 | 0.63 | 7.6% | **0.0%** |
| 33 **shared** stream (reality) | $946,639 | $463,213 | 0.83 | 29.7% | **26.2%** |

Identical means, completely different businesses. The independent framing
says a mass simultaneous wipeout is essentially impossible; the correlated
truth puts it at better than one year in four, and halves the bad-year
5th percentile.

**Staggering works, and it is the cheapest risk reduction available.**
N=5 (the compliant fleet), capped, 150→300 wd@$6k:

| configuration | net/yr | P(≥50% die/mo) | P(all die/mo) | zero-cashflow months |
|---|---|---|---|---|
| simultaneous | $43,749 | 24.2% | 24.2% | 71.8% |
| staggered 60d | $43,216 | 13.0% | **3.0%** | 48.3% |
| cushion k=.05 simultaneous | $43,788 | 10.0% | 10.0% | 70.0% |
| **cushion k=.05 staggered 60d** | $43,014 | **4.0%** | **0.8%** | 48.2% |

Your reasoning was right — breach risk concentrates pre-lock, so
de-synchronising the pre-lock windows de-synchronises the deaths. Combining
staggering with cushion sizing cuts the total-wipeout probability from
24.2% to 0.8% — a **30× reduction for 1.7% of net**. Staggering also nearly
halves zero-cashflow months, which is the monthly-income problem in its own
right. (The small net cost is a one-time onboarding effect: staggered
accounts trade fewer days in year one, not fewer days per year thereafter.)

**On $100k/month: not reachable from Lucid sim-funded accounts, by rule
rather than by performance.** A compliant 5-account fleet under the
verified 5-payout cap returns ~$43.7k/yr ≈ **$3.6k/month**. Even the
non-compliant 33-account fleet caps at ~$289k/yr ≈ $24k/month. The
$100k/month target has to come from LucidLive (real-money, post-
graduation) or from a different firm structure entirely — and the sim
stage's only job is to get accounts through to that with minimum
mortality. That reframes the fleet's objective from *extraction* to
*graduation throughput*.

## 5. HAIRCUT SENSITIVITY — THE HONEST CAVEAT, QUANTIFIED

Every number above is in-sample twice over (the book is fit-period, and S1
was selected on it). Haircut construction, declared: a constant is
subtracted from every fight's R so the mean falls 20% / 40% while the
dispersion is preserved — the conservative form (scaling both mean and
volatility would flatter the drawdown).

| policy | frame | net/yr | p05 net | funded-death P(≥1) |
|---|---|---|---|---|
| 150→150 wd@$6k | fit | $8,695 | $8,645 | 11.8% |
| | −20% | $8,060 | $3,245 | 21.2% |
| | −40% | $6,281 | **−$510** | 37.1% |
| 150→300 wd@$6k | fit | $8,683 | $8,610 | 25.2% |
| | −20% | $8,169 | $3,113 | 39.9% |
| | −40% | $6,657 | **−$650** | 57.5% |
| 150→300 wd@$4k | −40% | $6,642 | −$615 | 67.7% |

**The haircut hits risk about three times harder than it hits return.** A
20% EV cut costs ~7% of net but nearly doubles account-death probability;
a 40% cut costs ~25% of net and roughly triples death, taking the
5th-percentile year *negative* (you pay more in eval fees than you
withdraw). Portfolio-level at −20%, N=33 shared: P(all die in one month)
rises 26.2% → 43.5% and the p05 year falls to $160,100.

**Sizing against a haircut edge is the right instinct and it changes the
answer**: at −40%, flat 150→300 dies in 57.5% of years. Cushion sizing at
k=0.05 degrades most gracefully of everything tested. If you want one
sizing rule that survives being wrong about the edge, it is
cushion-proportional with a low k and a hard floor.

---

## What must be personally verified before any of this is acted on

Ranked by how much of the model they move:

1. **The account cap** — 10 total / 5 funded per household is
   VERIFIED-CURRENT on Lucid's own page. The 33-account plan needs
   resolving first; items 4's compliant numbers assume N=5.
2. **The 5-payout cap and the 50%-of-profit / $2,000 withdrawal cap** —
   VERIFIED-CURRENT, and they set the ~$8,700/account/year ceiling that
   makes small sizing free. If your account tier differs, re-run.
3. **Whether the $2,000 cap is gross or net of the 90/10 split** — not
   resolved; modelled as trader-receives-90%-of-request. Moves every
   dollar figure by ~10%.
4. **Flex reset price** ($95 on a single secondary source; Lucid's pricing
   page is Cloudflare-blocked to automated fetches). Low impact — fees are
   noise at this cap — but check the dashboard.
5. **Whether a copier fanning one signal into many accounts trips the
   automated HFT detector.** Lucid runs automated HFT detection and cites
   "hundreds of orders within minutes" as the profile; a fan-out
   architecture produces exactly that order count. Not found in
   documentation either way. **This is the single largest silent risk to
   the fleet architecture — get it in writing.**
6. **Any lifetime cap on resets per account** — genuinely absent from all
   official documentation; ask support in writing.
7. **The inactivity rule** — an account with <$1 net P&L movement in 30
   calendar days is deemed abandoned and permanently deleted. This bites
   reserve accounts and any staggered account left idle before its start
   date; staggering must be implemented as *delayed funding*, not idle
   funded accounts.

Two corrections to the local compliance reference were also confirmed:
Flex now has a DLL as a purchase-time option (not "no DLL at any stage"),
and the Flex *evaluation* does carry a 50% consistency rule (the "no
consistency" claim holds only for funded).

## Unchanged by this round

Holdout looks both unspent; closeloc claim queued as declared; break arm
parked; recorder ready for the VPS.
