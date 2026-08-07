# FINDINGS — B2 REDUX: pricing the bust (2026-08-07)

Five items on the bust rate. Short answer: **your discomfort was misplaced
for exactly the reason you gave, and justified for a reason neither of us
had modelled.** B2's per-account bust rate was the wrong statistic — but
so was the extraction figure it was traded against, because three firm
rules that govern the whole problem were absent from the model.

Method: B2's grid is replaced by a full LIFECYCLE simulation — eval →
funded → breach → buy a new eval → … over a 250-day year — so a bust is
paid for in fees AND in the funded days it costs, by construction rather
than by arithmetic afterwards. Day-block bootstrap, whole days resampled
with intraday order preserved, 2,000 draws, seed 20260807. Book: A+S1
(first-of-fight reject, flow-agreeing), 832 fights / 275 days, +0.257R.
Scripts: `scripts/htf_ma_account_lab.py`, `scripts/htf_ma_portfolio_lab.py`.

**Provenance note.** The simulator was put through a five-lens adversarial
code review before these numbers were accepted. Thirteen candidate defects
were raised, five confirmed, eight refuted. All five confirmed defects
were fixed and everything below is post-fix — see "Defects found and
fixed" at the end. The largest of them reversed a conclusion.

---

## 0. THREE VERIFIED RULE FINDINGS THAT RESHAPE THE PROBLEM

Fetched live from Lucid's own Help Center on 2026-08-07, VERIFIED-CURRENT.

**0a. The 33-account plan is not permitted.** Max **10 accounts total**
(evaluation + funded combined), max **5 funded**, *per household or
family* — not per login. One profile per trader, permanent; profiles
"cannot be converted, deactivated, or replaced to create a new profile,"
which closes the register-a-business route explicitly. 33 exceeds the cap
by more than 3×. **This is a hard input to item 4 and needs resolving
before any capital plan rests on the fleet.**

**0b. At most 5 payouts per funded account, then the account moves to
LucidLive.** The sim-funded stage is not an income stream — it is a
*qualification ladder* with a hard ceiling. With "max request = 50% of
profit, capped at $2,000" and the 90/10 split, one 50K Flex account
returns at most ~$9,000 net in its entire sim-funded life. B2's implicit
withdraw-forever assumption inflated annual extraction ~3×.

**0c. A funded breach kills the account; only evaluations are
resettable.** B2 modelled a bust as a cheap reset. It is not: a funded
breach destroys the account and you re-enter at the evaluation stage on a
newly purchased eval.

A fourth rule was found and modelled: the Flex **evaluation** carries a
**50% consistency requirement** (largest single day ≤ 50% of profit at the
moment of pass; funded Flex has none). Tested directly — at the
recommended $150 eval size it is **non-binding**: net $8,785 either way,
graduation 97.1% → 97.0%. It only bites at eval sizes where one day can be
half the $3,000 target, which is a further reason not to size the eval up.

**Consequence of 0b: the right objective function is not annual dollars.**
Under the cap, nearly every policy extracts ~$8,700/account/year, so
extraction cannot discriminate. What varies is **P(graduate to LucidLive
within the year)** and the risk taken to get there. Every table below
reports GRAD alongside the dollars, and it is the column that matters.

---

## 1. PRICE THE BUST INSTEAD OF MINIMISING IT

**Your arithmetic was right, and the world it applies to has been ruled
out.**

*Counterfactual (payouts uncapped — what B2 implicitly assumed):*

| policy | net/yr | p05 | funded-death P(≥1) |
|---|---|---|---|
| 150→150 wd@$6k | $18,461 | $8,865 | 11.9% |
| 150→300 wd@$6k | **$28,280** | $12,210 | 27.9% |
| 150→600 wd@$6k | $29,879 | $6,748 | 45.4% |

Here your instinct is exactly correct: (150→300) beats (150→150) by
~$9,800/yr while the extra death risk costs ~$30/yr in fees plus some
downtime. Priced rather than counted, the bigger size wins by a wide
margin — **the discomfort was misplaced.**

*The verified world (5-payout cap), fit book:*

| policy | net/yr | p05 | funded-death P(≥1) | **GRAD** |
|---|---|---|---|---|
| 150→150 wd@$6k | $8,695 | $8,645 | **11.8%** | 96.4% |
| 150→300 wd@$4k | $9,226 | $8,550 | 35.9% | 94.0% |
| 150→300 wd@$6k | $8,785 | $8,610 | 25.2% | 97.0% |
| 150→300 wd@$8k | $8,701 | $8,610 | 22.2% | **97.5%** |
| 150→600 wd@$4k | $9,026 | $4,785 | 50.3% | 90.8% |
| 150→600 wd@$6k | $8,746 | $6,748 | 44.0% | 93.6% |
| 150→150 wd@yr-end | $1,639 | $1,540 | 11.6% | **0.0%** |

The cap compresses extraction into an $8,583–$9,226 band for every in-year
policy — a 7% spread against death rates spanning 11.8%–50.3%. **The
compensation that justified the extra risk is gone: at 150→600 you buy 4×
the account-death probability for ~$300.** In the world that exists, the
answer inverts and small is correct.

Two secondary results worth keeping. **Year-end sweeping is catastrophic,
not conservative** ($1,639, GRAD 0.0%): deferring extraction means the
qualifying-day gate and the $2,000 per-request cap let you take exactly
one payout, so you never reach the fifth and never graduate. And **the
dollar cost of a bust really is trivial** — fees run $155–$275/yr, noise
against $8,700. The bust's true price is *time*: a dead funded account
sends you back to the eval queue, and what you are racing is the 250-day
clock to the fifth payout.

## 2. THE WITHDRAWAL POLICY — CONFIRMED, AND IT IS THE CHEAPEST LEVER

Your mechanism is exactly right and the arithmetic confirms your "~13R"
figure. Post-lock the floor is frozen at start, so cushion *is* distance
to ruin; since a request is capped at min(50% of profit, $2,000):

| withdraw at | post-payout cushion | cushion in R at $150 |
|---|---|---|
| $4,000 | $2,000 | **13R** — your number, exactly |
| $6,000 | $4,000 | 27R |
| $8,000 | $6,000 | 40R |

Effect on 150→300:

| threshold | net/yr | funded-death P(≥1) | GRAD |
|---|---|---|---|
| wd@$4k | $9,226 | 35.9% | 94.0% |
| wd@$6k | $8,785 | 25.2% | 97.0% |
| wd@$8k | $8,701 | 22.2% | **97.5%** |

**It is not quite a free lunch on raw dollars — it is better than one on
the objective that matters.** wd@$4k does earn ~$440 more per year (a
replacement funded account gets a fresh 5-payout allowance, so dying
faster buys extra payout cycles inside a 250-day window — a real but
perverse effect). But it graduates *less often* (94.0% vs 97.5%) while
carrying 14pp more death risk. Since graduation to LucidLive is worth far
more than $440, **wd@$6k–$8k dominates; $6k is the knee** (beyond it,
time-to-first-dollar keeps climbing: 54d → 63d → 71d). Your "12 cycles a
year at ~2% each" reasoning was structurally right; the cap makes it ~5
cycles, which raises the cost of each one rather than lowering it.

## 3. CUSHION-PROPORTIONAL SIZING — THE FRESH HYPOTHESIS WINS

Declared as a new hypothesis, not inheriting the old buffer-scaled
verdict. `size = clip(k × cushion, s_min, s_max)` post-lock, flat $150
pre-lock.

*Capped (verified) world, wd@$6k:*

| policy | net/yr | p05 | funded-death P(≥1) | **GRAD** |
|---|---|---|---|---|
| **k=0.05 [150,300]** | $8,745 | **$8,737** | 12.1% | **97.9%** |
| k=0.05 [75,300] | $8,718 | $8,680 | **9.4%** | 96.9% |
| k=0.10 [75,600] | $8,737 | $8,680 | 12.6% | 97.5% |
| k=0.15 [150,600] | $8,826 | $8,585 | 28.1% | 95.7% |
| flat 150→150 | $8,695 | $8,645 | 11.8% | 96.4% |
| flat 150→300 | $8,785 | $8,610 | 25.2% | 97.0% |

*Uncapped counterfactual — where dollars can still move:*

| policy | net/yr | p05 | funded-death P(≥1) |
|---|---|---|---|
| **k=0.10 [75,600]** | **$30,251** | **$12,470** | **12.7%** |
| k=0.15 [150,600] | $30,589 | $10,410 | 28.7% |
| flat 150→600 | $29,879 | $6,748 | 45.4% |
| flat 150→300 | $28,280 | $12,210 | 27.9% |

**VERDICT: cushion-proportional sizing dominates flat two-phase sizing on
every axis at once.** In the capped world k=0.05 [150,300] posts the best
graduation rate tested (97.9%), the best 5th-percentile year ($8,737), and
half the death rate of the flat policy it beats. In the uncapped world
k=0.10 [75,600] earns flat-150→600 money ($30.3k vs $29.9k) at **less than
a third of the death rate** (12.7% vs 45.4%) and nearly double the p05.
The mechanism is obvious in hindsight: flat post-lock sizing bets the same
dollars whether you are $6,000 or $400 above a frozen floor.

**Recommended: cushion k=0.05, bounds [150,300], withdraw at $6k.** Note
the floor matters — dropping s_min to $75 lowers death further (9.4%) but
*costs* graduation (96.9%), because a shrunken size cannot reach the fifth
payout inside the year. The bounded version is the better trade.

## 4. THE PORTFOLIO PROBLEM — THE NUMBER THAT DECIDES IT

**Your framing is correct and the simulation makes it stark.** N accounts
on identical signals with identical starts are not N risks — they are one
account multiplied. The proof is in the output: for every simultaneous
configuration, P(≥50% of accounts die in one month) and P(ALL die in one
month) are *the same number* (22.2% / 22.2%). There is no diversification
at any N. (Confirmed independently: two accounts on the same sequence
return bit-identical results.)

What the per-account rate would imply versus the truth (N=33, uncapped,
150→300 wd@$6k):

| | mean net | p05 net | monthly CV | zero-cashflow months | P(≥50% die in one month) |
|---|---|---|---|---|---|
| 33 **independent** streams | $927,019 | $839,014 | 0.48 | 7.0% | **0.0%** |
| 33 **shared** stream (reality) | $950,930 | $466,463 | 0.74 | 27.7% | **23.2%** |

Identical means, completely different businesses. The independent framing
says a mass simultaneous wipeout is essentially impossible; the correlated
truth puts it at nearly one year in four, halves the bad-year 5th
percentile, and quadruples the frequency of months that pay nothing.

**Staggering works, and after correcting a modelling error it is free.**
(The first version truncated staggered accounts' horizons instead of
shifting them, so they traded up to 24% fewer days — the entire apparent
cost of staggering was that artifact. Corrected: every account trades a
full 250 days on a longer shared calendar.)

N=5 — the compliant fleet — capped, wd@$6k:

| configuration | net/yr | P(≥50% die/mo) | P(all die/mo) | zero-cashflow months |
|---|---|---|---|---|
| flat 150→300 simultaneous | $44,098 | 22.2% | 22.2% | 73.9% |
| flat 150→300 staggered 60d | $44,189 | 12.8% | 2.2% | 60.5% |
| cushion k=.05 simultaneous | $43,869 | 8.8% | 8.8% | 73.0% |
| **cushion k=.05 staggered 60d** | $43,910 | **2.8%** | **0.2%** | 61.3% |

At N=33 uncapped the same pattern is larger: staggering moves net
$950,930 → $954,523 (**up**, not down), p05 $466,463 → $559,650, and P(all
die in one month) 23.2% → **1.0%**. Your reasoning was right — breach risk
concentrates pre-lock, so de-synchronising the pre-lock windows
de-synchronises the deaths. **Combining staggering with cushion sizing
cuts total-wipeout probability by ~100× at no cost in expected dollars and
a better tail.** Staggering also cuts zero-cashflow months by a third,
which is the monthly-income problem in its own right.

**On $100k/month: not reachable from Lucid sim-funded accounts, by rule
rather than by performance.** A compliant 5-account fleet under the
verified payout cap returns ~$44k/yr ≈ **$3.7k/month**. Even the
non-compliant 33-account fleet caps at ~$291k/yr ≈ $24k/month. The
$100k/month target must come from LucidLive (real-money, post-graduation)
or a different firm structure — and the sim stage's only job is to deliver
accounts there with minimum mortality. That reframes the fleet objective
from *extraction* to **graduation throughput**, which is what item 3's
recommended policy maximises.

## 5. HAIRCUT SENSITIVITY — THE HONEST CAVEAT, QUANTIFIED

Every number above is in-sample twice (fit-period book; S1 selected on
it). Haircut construction, declared: a constant is subtracted from every
fight's R so the mean falls 20% / 40% with dispersion preserved — the
conservative form (scaling both would flatter the drawdown). Verified: the
haircut lands at exactly 0.800 and 0.600 of the fit mean with sd unchanged
(2.796 → 2.797 → 2.800).

| policy | frame | net/yr | p05 net | funded-death P(≥1) | GRAD |
|---|---|---|---|---|---|
| 150→150 wd@$6k | fit | $8,695 | $8,645 | 11.8% | 96.4% |
| | −20% | $8,062 | $3,245 | 21.2% | 81.8% |
| | −40% | $6,285 | **−$510** | 37.1% | **51.5%** |
| 150→300 wd@$6k | fit | $8,785 | $8,610 | 25.2% | 97.0% |
| | −20% | $8,317 | $3,113 | 39.9% | 87.1% |
| | −40% | $6,789 | **−$650** | 57.5% | 64.8% |
| 150→300 wd@$4k | −40% | $7,050 | −$615 | 67.7% | 56.1% |

**The haircut hits risk roughly three times harder than it hits return.** A
20% EV cut costs ~7% of net but nearly doubles death probability; a 40%
cut costs ~25% of net, roughly triples death, and takes the
5th-percentile year *negative* — you pay more in eval fees than you
withdraw. Portfolio-level at −20%, N=33 shared: P(all die in one month)
rises 23.2% → 42.5%.

One honest tension the haircut exposes: under a degraded edge, *larger*
sizes graduate more often (64.8% vs 51.5% at −40%) because they race the
250-day clock better, even while dying far more. So "small is safe" is
conditional on the edge being real; if the edge is badly overstated,
nothing in the sizing grid rescues the year. **Sizing against a haircut
edge is the right instinct, and cushion-proportional with a floor degrades
most gracefully of everything tested.**

---

## Defects found and fixed (adversarial review, 2026-08-07)

Five confirmed of thirteen raised. All fixed before the numbers above:

1. **Year-end sweep bypassed all three payout constraints** (no
   qualifying-day gate, no $2,000 per-request cap, never incremented the
   payout counter) — paid up to $10,000 in one day. **This inverted a
   conclusion**: wd@yr-end appeared competitive at ~$8,500 and is actually
   the worst policy in the grid at $1,639 with 0% graduation.
2. **The payout counter was not reset on a funded death**, so a
   replacement account inherited the dead one's consumed allowance and
   graduated prematurely.
3. **Staggering truncated horizons instead of shifting them** — staggered
   accounts traded up to 24% fewer days, making the entire reported cost
   of staggering an exposure artifact. Corrected, staggering is free.
4. **Month buckets** — 250 // 21 = 11 buckets left the last "month"
   spanning 40 days, inflating monthly cashflow statistics.
5. **Correlated-blowup metric counted breach events, not distinct
   accounts**, so the ≥50% threshold could trip on fewer accounts than
   claimed; and eval resets were counted as account deaths.

One acknowledged asymmetry, not fixed: in-year policies leave residual
terminal equity uncredited while the year-end sweep is credited for one
final payout. Capping the sweep to the stated rules is the literal
reading; a fully consistent treatment would credit terminal equity across
all policies. It does not change any ranking here.

## What must be personally verified before any of this is acted on

Ranked by how much of the model they move:

1. **The account cap** — 10 total / 5 funded per household is
   VERIFIED-CURRENT on Lucid's own page. The 33-account plan needs
   resolving first; item 4's compliant numbers assume N=5.
2. **The 5-payout cap and the 50%-of-profit / $2,000 request cap** —
   VERIFIED-CURRENT; they set the ~$8,700/account/year ceiling that makes
   small sizing free and make graduation the objective.
3. **Whether the $2,000 cap is gross or net of the 90/10 split** — not
   resolved; modelled as trader-receives-90%-of-request. Moves every
   dollar figure ~10%.
4. **Flex reset price** ($95, single secondary source; Lucid's pricing
   page is Cloudflare-blocked to automated fetches). Low impact.
5. **Whether a copier fanning one signal into many accounts trips the
   automated HFT detector.** Lucid runs automated HFT detection and cites
   "hundreds of orders within minutes" as the profile; a fan-out
   architecture produces exactly that order count. Not documented either
   way. **The single largest silent risk to the fleet architecture — get
   it in writing.**
6. **Any lifetime cap on resets per account** — genuinely absent from all
   official documentation; ask support in writing.
7. **The inactivity rule** — an account with <$1 net P&L movement in 30
   calendar days is deemed abandoned and permanently deleted. This bites
   reserve accounts and any staggered account left idle before its start
   date: **staggering must be implemented as delayed funding, not as idle
   funded accounts.**

Two corrections to the local compliance reference were confirmed: Flex now
has a DLL as a purchase-time option (not "no DLL at any stage"), and the
Flex *evaluation* does carry a 50% consistency rule (the "no consistency"
claim holds only for funded).

## Unchanged by this round

Holdout looks both unspent; closeloc claim queued as declared; break arm
parked; recorder ready for the VPS.
