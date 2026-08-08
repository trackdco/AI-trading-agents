# FOUR DECISIONS — what each one is, and how to make it

The pre-registration is written and the workbench result is computed and sealed. **Four
decisions are outstanding and all four are yours.** Nothing else is blocking.

Each section below gives: what is actually being asked, the numbers you need, the consequence of
getting it wrong, and how to decide. **No decision is pre-filled.** Where there is a defensible
default it is named as a default, not as a recommendation.

> **Why the order matters.** Decision 1 partly answers Decision 2. Decision 3 stands alone.
> Decision 4 should be made *last*, because it should be made without knowing anything about
> the result — and the result already exists.

---

## The thing to protect

The workbench result is **already computed, hashed, and unread**:

```
research/vwap-bb/data/workbench_results_SEALED.parquet
SHA-256  a9ddc2947ca6a5f4c7e453d90427bed91710d1bc94c86de81fa9b381739bd4f0
1,423 trades · 501 sessions · nobody has looked
```

That ordering is the strongest property this study has. Pass marks set *before* anyone sees a
number cannot be tuned to that number. **Once you read it, you can never un-know it**, and
every later choice becomes arguable. So: decide 1–4, then read.

---

# DECISION 1 — Parity readings

**Time: ~20 minutes.** Fill in `PARITY-SHEET.md`. Read its "HOW TO READ THESE VALUES" section
first — there is one trap (bar replay and the volume profile) that will otherwise generate fake
mismatches.

### What is actually being asked

Does the code compute the same numbers your charts show? Nothing else in this project checks
that. Every gate so far has tested the *logic*; none has tested whether the daily VWAP in the
engine is the daily VWAP on your screen.

### Why it blocks

If there is a systematic indicator error, it propagates straight into the holdout and comes out
looking like a strategy result. There is no way to detect it afterwards.

### How to decide

There is nothing to decide. Read the values off the chart and write them down. **The most useful
outcome is a mismatch** — it means the detector does not implement the strategy, and finding
that now saves the run rather than wasting it.

Two fields carry more weight than the rest:

- **Daily VWAP mid.** Every cluster in the strategy is anchored to the VWAP family. If the
  anchor or the source price differs, nothing downstream can agree.
- **The stop in §7.** See Decision 2 — your answer here largely *is* Decision 2.

---

# DECISION 2 — Stop anchor: is 10 points a floor, or is it the rule?

### What is actually being asked

Amendment A5 set a **minimum stop of 10.00 points** on top of the spec's "one tick beyond the
wick extreme". It was justified as a floor catching degenerate cases.

**It is not behaving like a floor. 59.9% of admitted trades sit exactly on it.** For the
majority of trades, the 10-point floor *is* the stop rule, and it has nothing to do with the
structure of the candle.

**Is that what you want?**

### The numbers

| | median stop |
|---|---|
| Your hand log, in-scope | **35.00 pts** |
| Spec as literally written (1 tick beyond wick) | **3.12 pts** |
| **With A5's floor** | **10.00 pts** — and 59.9% sit exactly there |
| Alternative: prior swing (15m fractal) | 16.29 pts |
| Alternative: 2 × ATR(20) on the entry TF | 25.32 pts |
| Alternative: 3 × ATR(20) | 37.99 pts |

Consequences of the current setting, measured: median hold **5–7 minutes** against your ~30, and
**2.84 trades/session** against your 1.00. **The frozen spec trades faster and smaller than you
did.**

### Why it blocks

It changes the stop on the majority of trades, and therefore breakeven, hold time, the drawdown
path, and how many trades the one-position rule blocks. It cannot be changed after the holdout is
read.

### How to decide

**Open the two parity charts and answer one question: where would you actually have put the
stop?** Not where the rule says — where your hand goes. Then pick:

| option | what it means | when it is right |
|---|---|---|
| **(a) Keep A5 as a floor** | Wick-anchored, floored at 10. Accepts that the modal trade has a fixed 10-point stop | Your answer on the charts is "just past the wick, and the wick is usually small" |
| **(b) Structural anchor** | Prior swing (~16 pts) or an ATR multiple (~25 pts). Closer to your realised 35 | Your answer is "past the swing" or "wide enough that noise doesn't take me out" |
| **(c) Something else** | Write down what you actually do | Neither of the above describes it |

**What the data cannot tell you.** Your hand log records stop **distances** and never stop, entry
or target **prices**. So no anchor can be confirmed from it. This is a question only you can
answer, and it is the single most valuable thing you can contribute.

**If you pick (b), the pre-registration must be re-issued** — a new spec hash, a new amendment,
and the sealed result becomes irrelevant and must be recomputed. That is fine and it is cheap
(~1 minute of compute). It is only expensive if you decide it *after* reading the result.

---

# DECISION 3 — Tournament axis structure

### What is actually being asked

**How many configurations are you going to try?** Every extra one makes the statistical bar
harsher, because you get more chances to find something by luck.

### The numbers

Powered at p₁ = 0.50 against breakeven p₀ = 43.90%, 80% power. Available: 1,423 trades.

| divisor | what it means | required n | clears? | **can resolve a true win rate down to** |
|---|---|---|---|---|
| **/1** | one pre-committed configuration | 411 | YES | **47.15%** |
| **/4** | one axis at a time, 4 management variants — *current assumption* | 632 | YES | **47.93%** |
| /5 | as /4 before V3 was struck — superseded | 667 | YES | 48.04% |
| /8 | two axes crossed | 741 | YES | 48.26% |
| /16 | three axes, partially crossed | 849 | YES | 48.57% |
| **/72** | the full grid, W × E × V × weekly | 1,083 | YES | **49.17%** |

### The finding that matters more than the choice

**Every option clears on sample size.** Even the full 72-way grid needs 1,083 trades against
1,423 available. **You are not constrained by data.**

What you are constrained by is the **blind zone** — the band between breakeven and what the study
can actually resolve:

> Breakeven is **43.90%**. The study cannot detect a true win rate below **47.15%** even with no
> correction at all. **A strategy with a true 45% win rate — genuinely profitable — is invisible
> to this design at every axis structure.**

Going from /1 to /72 widens that band from 3.25 to 5.27 points. **The correction costs about two
points of resolution; the design costs three.** More data would not fix it.

### How to decide

The wrong question is "how many can I afford to test?" — the answer is all of them.

**The right question is: how many configurations would you actually be willing to trade if one
won?** If you would only ever trade E1 with V1, commit to /1 and get the tightest resolution. If
you genuinely do not know which entry variant is right and want the answer, you need the entry
axis and the harsher bar that comes with it.

A defensible **default is /4** — §12.3's one-axis-at-a-time discipline, with the management axis
at 4 after V3 was struck. It is the current working assumption and it has never been signed.

---

# DECISION 4 — Pass marks

**Make this one last, and make it before reading anything.**

### The draft on the table

> **Primary:** mean net R per trade **> 0** at c = 0.975, with the **session-block bootstrap
> lower bound above zero** at the corrected alpha.

Reasoning: net expectancy after costs is what decides whether it is worth trading. Win rate is
not — this project has twice found a win rate flattering a geometry that could not pay for
itself. Requiring the *lower bound* above zero, not the point estimate, is what makes a single
holdout read mean anything: a point estimate above zero on 1,400 trades is entirely compatible
with a true expectancy of zero. The bootstrap is session-blocked because trades in the same
session share a regime and are not independent.

**Abort conditions:**

| # | condition | why |
|---|---|---|
| 1 | frequency below the §6 tripwire for your chosen divisor | the study is then underpowered; a null is uninformative and a positive is noise |
| 2 | any lookahead found in the engine | a lookahead result is not a weak result, it is not a result |
| 3 | the result changes sign between cost levels | the finding is then about the cost assumption, not the strategy |

### Three specific things to say yes or no to

1. **The primary criterion** — sign it, tighten it, or replace it.
2. **Abort condition 3: does a sign change abort, or just get annotated?** Abort is stricter.
   Annotate is more informative. Pick one *now*, because after seeing a sign change you will
   have an opinion about which is fairer, and that opinion will not be trustworthy.
3. **Is the trigger reading (A/B/C/D) pre-committed, or is it a tournament axis?** If it is an
   axis, your divisor in Decision 3 must go up. If it is pre-committed, name which one. *(The
   sealed result was computed on reading A.)*

### How to decide

Ask: **"if the result came back just barely passing, would I trade it?"** If no, your pass mark
is too loose — tighten it now. If yes, it is honest.

Then ask the mirror: **"if it came back just barely failing, would I accept that and stop?"** If
no, you do not have a pass mark, you have a hope. That is the real test of a pre-registration and
it is worth being uncomfortable about before signing rather than after.

---

# What happens once all four are in

1. Decisions recorded in `PREREGISTRATION.md` §10–11, spec re-hashed if Decision 2 changed
   anything, pre-registration marked **IN FORCE**.
2. Parity comparison run at 1-point tolerance, field by field, MATCH/MISMATCH with both values
   shown. **A fail here stops everything** — it means the detector does not implement the
   strategy.
3. Only if parity passes: the sealed workbench result is read, **once**, against the pass marks.
4. Only if the workbench passes: the holdout is unsealed, read **once**, and `spent: true` is
   written with the date and reason.

Steps 3 and 4 are each one-way doors. Everything before them is reversible.

---

**Current state: N_trials 0. Holdout sealed and never read. Workbench result computed, hashed
and unread.**
