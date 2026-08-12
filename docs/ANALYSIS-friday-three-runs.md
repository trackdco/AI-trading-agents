# Friday 26 June, three times: why the updated agents made less money

Session-day 2026-06-25. The same tape has now been replayed three times by three versions of
the stack. You asked how the updated version "literally did worse". Here is the arithmetic and
then the cause, which is not what the version numbers suggest.

## The three runs

| | v0.2.0 (pre-rulings) | v0.3.2 (post-rulings, contaminated prompt) | **v0.3.4 (post-rulings, clean prompt)** |
|---|---|---|---|
| takes licensed | 4 | 3 | **5** |
| fills | 4 (100%) | 3 (100%) | **2 (40%)** |
| R, full-target convention | **+5.12** | +2.45 | **+1.95** |
| R, blended across partials | **+3.80** | +1.80 | **+1.67** |
| agreement with you | — | 0/3 | **1/3** |
| log | `superseded/2026-06-25_v0.2.0_pre-rulings.jsonl` | `superseded/2026-06-25_v0.3.2_contaminated.jsonl` | `2026-06-25.jsonl` |

Your 5.1 / 3.8 figures are exactly reproduced: **5.125** on the full-target convention and
**3.801** blended 75/25 across partials. The blended column is the honest one and I will use it
below.

## Where the 2.13R went, window by window

| window | v0.2.0 | v0.3.4 | delta |
|---|---|---|---|
| LONDON | −1.00 | 0.00 | **+1.00 better** |
| NY_PRE | +1.87 | 0.00 | **−1.87 worse** |
| NY_AM | +2.93 | +1.67 | **−1.26 worse** |
| **day** | **+3.80** | **+1.67** | **−2.13** |

Three separate causes, and only one of them is a doctrine problem.

### 1. NY_PRE, −1.87R — one sentence in a Tier-1 field

This is the single biggest item and it has nothing to do with the trigger, the rulings, or the
de-identification.

Both runs' 08:00 thesis was **short**, with the same targets and the same invalidation. They
differed in one field:

> **v0.2.0 / v0.3.2** — *waiting for a rebalance back up to the 15m MA (~29420) before re-shorting*
>
> **v0.3.4** — *waiting for a 15m decisive close below 29290–29305, then short the retest*

The day delivered the rebalance and never delivered the break. Price rallied to 29400.50 at
08:33, was rejected two points under the 15m MA, and rolled over — which satisfies the first
wording exactly and the second not at all. The 08:36 candidate was **taken for +1.87R by v0.2.0
and passed by v0.3.4**, and both triggers read their thesis correctly.

**The lever is `waiting_for`, and nothing constrains how it is written.** The thesis agent picks
a trigger geometry ninety minutes ahead of the trade, and whichever geometry it happens to name
is the only one the day is allowed to pay on.

### 2. NY_AM, −1.26R — one fill instead of two

v0.2.0 took two longs (09:36 for +0.94, 10:02 for +1.99). v0.3.4 took one long (09:58 for +1.67)
and was holding it through 10:02, so the second entry was correctly declined as a re-entry.

The real loss here is the **09:36 reversal bar** — 119.5pt body, 5,941 contracts, the heaviest of
the session, off a swept weekly VAL. v0.2.0 bought it. **You bought it** (your N1). Both v0.3.x
runs passed it, and the reason is structural:

> `waiting_for` is treated as a hard gate on **every** candidate, including the very bar the
> thesis is reasoning **from**.

I originally wrote this up as a phrasing accident, because v0.3.2's thesis used blanket language
("No entries until one resolves"). That was wrong. v0.3.4's thesis used no embargo language at
all — a plain "waiting for X, then long the retest" — and the trigger passed anyway, citing
constraint 5 and calling `waiting_for` **binding**. It reproduces across wordings. **This is the
finding of the re-run.**

### 3. LONDON, +1.00R — the rulings working

v0.2.0 bought at 29493 into the 0.5-fib ceiling and lost 1R. v0.3.4 read the same ceiling as
resistance, passed the long on direction, and licensed **two shorts** instead — including the one
**you** took, which is the first and only agreement any version has scored on this day.

Neither short filled. That is the second problem, and it is mechanical:

- **04:06** — limit 29489.5, twelve points above the close; **cancel level 12pt below it**. The
  next minute traded 29474.75 → 29457.25, through the cancel, without touching the limit. Killed
  on its first bar. The minute after that ran to 29502.75 — straight through the limit.
  Counterfactual: **+1.81R**.
- **04:33** — limit priced off a 2m close of 29493, but the 3m adjudication lands at 04:33, by
  which time price is 29483.50 and falling. Highest print in the limit's whole ten-minute life:
  29483.75. Both of its targets printed within twelve minutes while the order sat unfilled.

v0.2.0 filled 4 of 4 because its cancel levels sat **40–70pt** away. v0.3.4's sit at the nearest
structural level, which on a quiet tape is often ten points from the close. **T12 was never
closed out, and this is the bill.**

## Three distinct T12 failures now on record — none is the one T12 was written about

1. **Limit too far** (day 2) — sat 13pt out on a conviction-A setup, expired.
2. **Cancel too near** (this run, 04:06) — 12pt from the close, killed by an ordinary wiggle.
3. **Limit stale on arrival** (this run, 04:33) — priced off a 2m close, adjudicated at the 3m
   close a minute later, never live at a reachable price.

The third is **mine, not the agent's**: clustering a 2m and a 3m signal to the later completion
costs a minute of price, and on a fast tape that minute is the whole entry. A T12 rule needs a
minimum distance on the **cancel** as well as a maximum on the **limit**, and the orchestrator
needs to stop pricing entries off a bar that closed a minute before the decision.

## The caveat that matters most

**v0.2.0's +5.12R is itself a contaminated number.** It ran on the same contracts that named this
session by date with its exact high, low and 0.5 fib. Its NY_PRE short targeted the weekly VAL at
29292 and its NY_AM long targeted 29369 then 29465 — the levels the day actually turned on. That
may be judgement. It may be recall. **The audit cannot tell the difference, which is the whole
reason the prompts were de-identified.**

So the comparison is not "good old version vs worse new version". It is:

> **a contaminated run that made 3.80, versus the first clean run of this day, which made 1.67
> while identifying more of the day's real trades than either archived version and agreeing with
> you for the first time.**

## What I would put in front of you for a ruling

1. **Should `waiting_for` gate the bar the thesis is reasoning from?** It cost the 09:36 reversal
   long in both v0.3.x runs, and that is your trade. My read: a `waiting_for` should gate entries
   **outside** a location the standing thesis has already licensed, not inside one.
2. **A minimum distance on the cancel level**, expressed in ATR or in points, not "the nearest
   structural level". Two of five takes died on this today.
3. **Is there a floor and a ceiling on R?** This run produced a 17.5pt stop (04:33) and a 121pt
   stop (09:58) from the same rule, four hours apart. The archived run produced a 120pt stop whose
   empty 1.5–2.5R band pushed a target beyond the weekly low.
4. **Should the orchestrator stop clustering 2m and 3m signals to the later close?** Adjudicating
   the 2m signal at the 2m close and the 3m separately doubles the adjudications but stops pricing
   entries off stale bars.

## What is not broken

- Every ruling that fired, fired correctly. **T14 saved 1R** on the 10:54 short, whose first
  target was missed by 5.75 points and whose raw stop was tagged 31 minutes later.
- **T11 was satisfied on all five takes** and I re-derived the band by hand on each.
- The **de-identification worked**. Four thesis emissions and six trigger adjudications, no
  recognition of the day anywhere, and one trigger wrote *"Resembles a contract example — decided
  from data"* unprompted.
