---
id: orb-fvg-nyopen
name: NY-open opening-range breakout into a 1-minute FVG
trader: anonymous social post (see ../SOURCE-POST.md)
prefix: orb-
provenance: LOW — one social post, no corpus, no example, nothing re-readable
sessions: [New York open — 09:30-10:30 ET, window is OURS]
instruments: [NQ]
GAP_ENTRY: YES — the FVG is the entry
NY_SESSION: YES
sources: [SOURCE-POST.md]
verdict: INSUFFICIENT AS POSTED — baselined only as an ADAPTATION under our conventions
---

# `orb-fvg-nyopen` — opening-range breakout into a 1-minute FVG

> ## ⚠️ LOW PROVENANCE. READ THIS BEFORE ANY NUMBER ON THIS CARD.
>
> This card is built from **one social-media post**. There is no transcript, no second statement
> of any rule, no worked example, and nothing to re-read. Where `ash-*` and `zxck-*` cards could
> resolve an ambiguity by finding the rule stated again, **this one cannot**.
>
> **Six of the posted rules are undefined to the point of being unexecutable** (§2). Each blank
> below is filled by **us** and tagged `[A]` (our assumption) or `[U]` (stated-by-user). The
> result is therefore **an adaptation of a posted template, not a test of the poster's method.**
>
> **No result on this card is evidence for or against what he posted.** If it wins, our
> conventions may be carrying it; if it loses, his may have been better. Both directions are
> unfalsifiable from one post, and that is a property of the source, not of the test.

## Edge thesis

**None stated.** The post gives a procedure and a dollar figure. It contains no claim about who
is on the other side, why the opening range matters, why an FVG in the break direction should
resolve favourably, or why the edge persists. `[absent]`

The implicit thesis, entirely `[A]` **ours by reconstruction**: the first five minutes of the NY
cash open establish a reference range; a decisive break of it signals participation in one
direction; an FVG left behind by that break marks unfilled imbalance the market returns to before
continuing. **He does not say this.** It is recorded so the model has a stated mechanism to be
wrong about, not because he supplied one.

## Market context / bias

**Session:** New York open. `[stated]` — *"the first 5-minute candle of the NY open"*.

**Window: 09:30–10:30 ET.** `[U]` **stated-by-user.** The post gives a start (the NY open) and
**no end at all**. The 60-minute window is Brake's instruction for this card and is ours.

> **⚠️ This card deliberately breaks the standing 09:45–10:15 macro rule** that governs every
> `ash-*` and `zxck-*` card, on explicit instruction. The consequence is that the **overlap is
> partial**: this card can trade 09:35–09:45 and 10:15–10:30, where no other card can. Pooling
> is still valid (the exit convention is identical) but the *windows are not identical* and any
> pooled result must say so.

**Directional bias: NONE.** The direction comes entirely from which side of the opening range
breaks first. There is no higher-timeframe bias gate anywhere in the post. `[stated by absence]`

**The four marked levels are DECORATIVE AS POSTED.** The post opens with *"Mark NY session
high/low and overnight high/low"* and then **never refers to them again**. No rule consumes them:
they are not a bias input, not a filter, not a target, not a stop reference, not part of the
breakout definition.

> **We have not invented a role for them.** They are computed and logged as context features
> (`dist_to_onh_R`, `dist_to_onl_R`, `dist_to_pdh_R`, `dist_to_pdl_R`) so that a future,
> pre-registered hypothesis can use them — **and no rule in this baseline reads them.** Giving
> them a job would be us writing his strategy for him.

## Setup — conditions that must be present

| # | condition | as posted | our resolution |
|---|---|---|---|
| 1 | Mark NY session H/L + overnight H/L | `[stated]` | **decorative** — logged, never gated on |
| 2 | First 5-min candle of the NY open closes | `[stated]`, unambiguous | 09:30–09:34 inclusive; range frozen at 09:35 |
| 3 | Drop to the 1-minute chart | `[stated]`, unambiguous | 1-minute bars |
| 4 | A **"clean breakout"** | `[stated]` but **UNDEFINED** | `[A]` a 1-min bar **closes** beyond the range; wick-through run as sensitivity |
| 5 | An **FVG forming in the direction of the break** | `[stated]`, mostly clear | `[A]` standard 3-bar FVG, first one completing at/after the breakout bar |
| 6 | **"Enter on confirmation"** | `[stated]` but **UNDEFINED** | **BOUNDED — both readings run** |

## Entry trigger

> *"Enter on confirmation"*

**This is the single largest blank in the post.** "Confirmation" has no antecedent — it could
mean the FVG completing, price retracing into it, or a close through it.

**We do not pick.** Both live readings are run and the result is reported as a **bound**:

| reading | rule | tag |
|---|---|---|
| **RETRACE** (primary presentation) | limit at the FVG's **near edge**, filled on the first return after the gap completes | `[A]` |
| **FORMATION** | market entry at the **close of the FVG's third bar** | `[A]` |

The third possible reading — *close through the FVG* — is **not run**: it is a strictly later and
strictly rarer version of RETRACE, so RETRACE bounds it from above on event count, and adding it
would spend a trial for a subset.

## Stop / invalidation

> *"stop above/below that candle"*

**"That candle" has no antecedent either.** The two candles in play are the **breakout candle**
and the **FVG candle** — and the FVG is three candles, so "the FVG candle" is itself ambiguous.

**We do not pick. Both are run and reported as a bound:**

| reading | rule | tag |
|---|---|---|
| **BREAKOUT** | beyond the breakout candle's extreme (its low for longs, high for shorts) | `[A]` |
| **FVG** | beyond the 3-bar FVG pattern's extreme (min low / max high across all three bars) | `[A]` |

A third, strictly literal reading — **the far edge of the gap itself** — is run as a
**sensitivity line only**, because it produces a stop the width of a 1-minute gap. `zxck-ifvg-50`
already established that a stop of that size on NQ in this session sits inside single-bar noise
and puts a quarter of every R into costs (n=186, t=−4.165). Running it here **measures** that
claim on this card rather than asserting it.

## Targets / trade management

> *"target 1.5-2R"* · *"move stop to BE once internal liquidity is taken"*

**Two problems, both resolved by convention and both recorded as replacements, not readings:**

1. **A target given as a RANGE is two strategies, not one.** 1.5R and 2R produce different win
   rates, different expectancies, and different BE behaviour. Picking the better one after seeing
   the data would be selection.
2. **"Internal liquidity is taken" is undefined** — and it is the *trigger* for his entire
   break-even rule. It is not defined in the post, and there is no second statement to check.

**⛔ HIS STATED BREAK-EVEN RULE IS REPLACED, NOT IMPLEMENTED.** We score on the
**LOCKED convention** (`research/zxcked/strategies/EXIT-CONVENTION-LOCKED.md`):

| | |
|---|---|
| target | **2R** — the top of his stated range, chosen *before* seeing data because it matches every other card |
| break-even | **at 1R** — replaces *"once internal liquidity is taken"*, which is undefined |
| trailing | **none** |
| same-bar stop+target | **stop first** |
| horizon | capped **16:00 ET** |
| costs | **separate**, $25/round-turn |

This is what makes the card **poolable** with `ash-unicorn-sb` and the `zxck-*` book. It is also
a **substitution of our rule for his**, and the 1.5R half of his range is untested here.

## Risk & sizing

**Not stated.** No risk per trade, no account size, no contract count. `[absent]`

## Filters / avoid conditions

**None stated** — no news filter, no volatility filter, no FOMC rule, no "skip if X" of any kind.

**We add none.** In particular **FOMC/Powell sessions are NOT excluded**, unlike the `zxck-*`
cards where Powell states the rule himself. Adding an exclusion he never gave would improve the
numbers by our choice. `news_day` and `fomc` are logged as features so the slice remains
available to a future pre-registered test.

## Management rules — measured, but NOT part of the primary sample

> *"max 2 trades/day; stop for the day after a win; one more attempt after a BE or loss"*

These are **bankroll and tilt management, not edge.** They cannot create expectancy — they can
only truncate a sequence of draws from whatever distribution the entry produces. Applying them to
the primary sample would destroy statistical power to measure a property they do not affect.

**Primary sample = every qualifying setup.** The capped version is reported as a **separate
secondary line** so the cost or saving of the cap is visible.

## Performance claims

> *"nearly $20K this month across my prop accounts"*

`[trader-claimed, unverified]` — **one month of one sample multiplied across accounts, which is
multiplication, not independent confirmation.** Full reasoning in `../SOURCE-POST.md`. Recorded;
used as evidence for nothing.

---

## 2 · SEVEN-PART COMPLETENESS CHECK

| part | tag | evidence / gap |
|---|---|---|
| **bias source** | **[absent]** | No bias rule of any kind. Direction is 100% mechanical (which side of the OR breaks). The four marked levels are named and then never used. |
| **setup conditions** | **[partial]** | *"first 5-minute candle of the NY open to close"* is exact. *"clean breakout"* is **undefined**. *"an FVG forming in the direction of the break"* is standard but its search window is unstated. |
| **entry trigger** | **[UNDEFINED]** | *"Enter on confirmation"* — confirmation of **what**? No antecedent anywhere in the post. |
| **stop / invalidation** | **[UNDEFINED]** | *"stop above/below that candle"* — **which** candle? Breakout candle and FVG candle are both in play, and the FVG is three candles. |
| **targets** | **[partial / self-conflicting]** | *"1.5-2R"* is a **range**, i.e. two strategies. |
| **risk / sizing** | **[absent]** | Nothing. No risk per trade, no size, no account basis for the $20K. |
| **avoid-filters** | **[absent]** | None stated. |

### ⛔ VERDICT: **INSUFFICIENT AS POSTED.**

**2 of 7 parts are outright UNDEFINED, 2 are ABSENT, 2 are PARTIAL, 1 is absent-by-design.**
As written, the post **cannot be executed twice the same way by two people**, which is the
operative test. It is baselined only as an adaptation under the conventions above.

---

## 3 · THE BLANKS — every one, listed before any test was run

Each is a hole in the source. None was resolvable from the source, because there is only one post.

**B1 · "Enter on confirmation" — confirmation of WHAT?**
- Candidates: the FVG *forming*; price *retracing into* it; a *close through* it.
- *Material to event count:* **YES, severely** — formation fires on every FVG; retrace fires only
  on those revisited. **→ BOUNDED, both run.**

**B2 · "stop above/below that candle" — WHICH candle?**
- Candidates: the breakout candle; the FVG's third (displacement) candle; the 3-bar FVG pattern;
  the gap's far edge.
- *Material:* **YES** — it sets R, so it changes every number including which trades are
  survivable. Note the literal single-candle reading is **degenerate**: a long entering at the gap
  top with a stop at the displacement candle's low has **risk ≈ 0**, because that low *is* the gap
  top. That reading is arithmetically impossible, which is itself evidence the post is
  under-specified. **→ BOUNDED (breakout vs 3-bar pattern), gap-far-edge run as sensitivity.**

**B3 · "clean breakout" — what disqualifies a breakout?**
- The post offers no disqualifier. "Clean" implies some are unclean; none is described.
- *Material:* **YES** — it is the event gate. **→ `[A]` close-through primary, wick-through run as
  sensitivity.**

**B4 · "internal liquidity is taken" — undefined, and it drives the BE rule.**
- Internal to what? Which liquidity? Taken by what — a wick, a close?
- *Material:* **YES** — it is the entire trade-management trigger. **→ NOT IMPLEMENTABLE.
  Replaced by the locked BE-at-1R. Recorded as a replacement, not a reading.**

**B5 · Target given as a RANGE (1.5–2R) — two strategies, not one.**
- *Material:* **YES** — different targets give different win rates and expectancies.
- **→ 2R by the locked convention, fixed before seeing data. The 1.5R arm is untested here.**

**B6 · The four marked levels have NO role in any rule.**
- *Material:* **NO to the event count** (nothing gates on them) — but material to whether this is
  even the posted strategy. **→ Declared decorative. Logged as features, never read by a rule.**

**B7 · No end to the session window.** *(added on inspection — the post gives a start, not a span)*
- *Material:* **YES** — it bounds how long a breakout stays valid. **→ `[U]` 09:30–10:30, Brake's.**

**B8 · Multiple setups per session — allowed or not?**
- The post's *"max 2 trades/day"* implies more than one is possible, but never says whether a
  second setup means a second FVG in the same direction or a break of the other side.
- *Material:* **YES, to n.** **→ `[A]` both: every FVG entry in the live break direction, and a
  break of the opposite side re-arms the direction. Capped line reported separately.**

---

## 4 · TEST SPEC — fixed before running

| | |
|---|---|
| instrument | NQ 1-minute (`data/reference/nq_1m_master.parquet`) |
| session window | **09:30–10:30 ET** `[U]`; opening range 09:30–09:34, scan from 09:35 |
| date range | **2025-06-01 → 2026-07-15** — the footprint-covered span, for comparability and flow coverage |
| sample target | n ≥ 30 per arm; below that the arm is reported **UNTESTABLE**, not interpreted |
| scoring | LOCKED convention — 2R target, BE at 1R, no trailing, stop-first same-bar, 16:00 ET cap |
| costs | $25/round-turn NQ at $20/pt, reported separately, never baked into R |
| primary sample | **every qualifying setup** |
| secondary | the capped version (max 2/day, stop after a win, one more after BE/loss) |
| bound | 2 entry readings × 2 stop readings = **4 arms**, all reported |
| flow | `retrace_ratio` and `disp_delta_magnitude` computed on identical definitions; **applied to nothing** |

**Pre-registered decision rule:** if **every arm of the bound** falls on one side of break-even,
that settles the card without further data. If the bound straddles zero, the card is
**undecidable from this specification** and no direction is claimed.

---

## 5 · RESULT

`scripts/orb_fvg_baseline.py` · trades `orb-fvg-nyopen-raw-trades.csv` (20,768 rows, all arms)

### Gate funnel — counts only, no outcomes

| gate | close-through | wick-through |
|---|---|---|
| 0. sessions in span | 290 | 290 |
| 1. + a complete 5×1min opening range | 290 | 290 |
| 2. + the range broke | 288 | 290 |
| 3. + an FVG formed in the break direction | 288 | 290 |
| **⇒ (breakout, FVG) EVENTS** | **1919** | **1999** |
| sessions dropped: both sides on one bar | **0** | 1 |

The close-through reading produces **no ambiguous sessions at all** — a single bar cannot close
both above and below the range. That is a real advantage of the reading and it is why it is
primary.

### ⚠️ The naive t-statistic is INVALID on this card. Read the clustered one.

This card fires **~6.7 setups per session**, all inside one 60-minute window, mostly in the same
direction, overlapping in time. They are **not independent draws**. Every table below reports the
**session-clustered t** (cluster-robust SE on session date, with the finite-cluster correction);
`t_naive` is shown only so the size of the overstatement is visible.

### PRIMARY — every qualifying setup, close-through breakout

| arm | n | /sess | win/BE/loss/TO | avgR | cost | **exp** | totR | maxDD | med stop | **t_clus** | *t_naive* |
|---|---|---|---|---|---|---|---|---|---|---|---|
| retrace · breakout | 1354 | 4.7 | 21.4/18.9/46.2/13.4 | +0.008 | 0.051 | **−0.043** | +10.8 | 67.2 | 53.0 | +0.16 | *+0.25* |
| **retrace · fvg** | 1558 | 5.4 | 26.3/24.6/49.0/0.1 | +0.038 | 0.053 | **−0.015** | +59.4 | 42.0 | 28.8 | +0.93 | *+1.21* |
| formation · breakout | 1858 | 6.5 | 20.9/17.1/45.6/16.4 | +0.005 | 0.039 | **−0.034** | +8.9 | 60.3 | 60.5 | +0.10 | *+0.18* |
| formation · fvg | 1919 | 6.7 | 25.0/25.0/49.2/0.7 | +0.012 | 0.036 | **−0.024** | +23.3 | 91.4 | 43.0 | +0.28 | *+0.43* |

## ⛔ BOUND ON EXPECTANCY: **[−0.043R, −0.015R] — ENTIRELY NEGATIVE**

**The pre-registered decision rule fires: every reading of every ambiguity loses money, so the
card is settled without further data.**

Note *how* it loses: **gross avgR is POSITIVE on all four arms.** Costs alone push all four under.
This is not a strategy that is wrong about direction — it is a strategy whose edge is smaller than
its own transaction cost.

The outcome mix is also close to the random-walk null for this exit (**25/25/50**): the best arm
is 26.3/24.6/49.0. The card selects *when* to be in the market, not *which way* — the same
diagnosis as `zxck-10am-keyopen`.

### SECONDARY — his management applied (max 2/day; a win stops the day FROM ITS EXIT)

> #### 🔴 CORRECTED 2026-08-07 — the first version of this table was produced by LOOK-AHEAD.
> An adversarial audit found it, and **two independent lenses filed it separately.** `cap_rules()`
> walked each session's trades in **entry order** and stopped the day on `R >= 2R` — but **R is
> not known until `exit_time`**, minutes to hours later. Because this card fires 4.7–6.7
> **overlapping** setups inside one 60-minute window, the trade the win-rule deleted had usually
> already been entered when the winner finally hit target: **201 of 288 deletions (70%) removed
> positions that were already open.** That is a filter on future information, not a management
> rule.
>
> ~~The original table showed expectancy −0.181 / −0.138 / −0.168 / −0.224 and t up to −3.68, and
> the card concluded his management was "actively harmful", costing 0.12–0.20R per trade.
> **That conclusion was an artefact of the defect and is withdrawn.**~~

| arm | n | win/BE/loss/TO | avgR | **exp** | totR | t_clus | ~~exp before the fix~~ |
|---|---|---|---|---|---|---|---|
| retrace · breakout | 523 | 23.3/20.5/52.0/4.2 | −0.037 | **−0.097** | −19.2 | −0.60 | ~~−0.181 (t −2.12)~~ |
| retrace · fvg | 538 | 25.7/23.6/50.7/0.0 | +0.006 | **−0.043** | +3.0 | +0.09 | ~~−0.138 (t −1.63)~~ |
| formation · breakout | 556 | 26.8/18.3/52.7/2.2 | +0.023 | **−0.034** | +12.5 | +0.35 | ~~−0.168 (t −1.88)~~ |
| formation · fvg | 573 | 24.1/24.3/51.1/0.5 | −0.026 | **−0.058** | −14.8 | −0.41 | ~~−0.224 (t −3.68)~~ |

**Every |t| collapses inside 0.60.** avgR flips sign on two of four arms; post-cost expectancy
stays negative on all four, as it does everywhere on this card.

### SECONDARY — the 2/day cap ALONE, win-rule removed (isolates the win-rule)

| arm | n | avgR | **exp** | totR | t_clus | **win-rule's own cost** |
|---|---|---|---|---|---|---|
| retrace · breakout | 556 | −0.012 | −0.070 | −6.4 | −0.19 | **−0.027R** |
| retrace · fvg | 573 | +0.007 | −0.041 | +4.0 | +0.12 | **−0.002R** |
| formation · breakout | 572 | +0.034 | −0.022 | +19.6 | +0.54 | **−0.012R** |
| formation · fvg | 576 | −0.021 | −0.052 | −11.8 | −0.32 | **−0.006R** |

### ⛔ CORRECTED CONCLUSION ON HIS MANAGEMENT

**It has no measurable effect.** Isolated against the plain 2-per-day cap, his *"stop for the day
after a win"* rule costs between **0.002R and 0.027R per trade** — indistinguishable from zero at
every arm's standard error.

**The card previously claimed the opposite**, and claimed it as "the clearest result on the card"
and "the one finding that IS about his post rather than our conventions". **Both statements were
wrong.** The mechanism I described — truncating upside while leaving downside intact — is real
arithmetic, but it only bites if the rule can cancel a position *retroactively*, which a trader
cannot do. Implemented causally, it barely bites at all.

**There is now NO finding on this card that is about his post rather than our conventions.**

### SECONDARY — FIRST trade of each session only (one per session: independent draws)

| arm | n | win/BE/loss/TO | avgR | **exp** | totR | t |
|---|---|---|---|---|---|---|
| retrace · breakout | 286 | 23.4/20.3/53.8/2.4 | −0.061 | **−0.127** | −17.4 | −0.84 |
| retrace · fvg | 288 | 26.0/26.0/47.9/0.0 | +0.042 | **−0.004** | +12.0 | +0.57 |
| formation · breakout | 288 | 27.1/19.4/53.1/0.3 | +0.008 | **−0.051** | +2.2 | +0.10 |
| formation · fvg | 288 | 23.6/26.0/50.0/0.3 | −0.024 | **−0.054** | −6.9 | −0.34 |

**Bound [−0.127R, −0.004R] — still entirely negative**, best arm indistinguishable from zero.
This is the statistically cleanest slice on the card and it agrees with the primary.

### SENSITIVITY — the literal gap-far-edge stop

| arm | n | win/BE/loss | med stop | cost | **exp** | totR | t_clus |
|---|---|---|---|---|---|---|---|
| retrace · gapedge | 1558 | 20.8/8.5/70.7 | **6.2 pt** | **0.538** | **−0.829** | **−453.0** | **−9.08** |
| formation · gapedge | 1919 | 23.7/22.8/53.4 | 21.0 pt | 0.093 | −0.152 | −112.7 | −1.78 |

**This MEASURES the `zxck-ifvg-50` failure mode on this card rather than asserting it.** A 6.2pt
stop on NQ in this session puts **0.538R of every trade into costs before the market moves**. The
finding transfers exactly: tight-stop readings of ICT-style gap entries do not survive NQ's
opening volatility.

### SENSITIVITY — wick-through breakout instead of close-through

Bound **[−0.048R, −0.008R]**. The breakout definition does not rescue the card either.

### Flow coverage

| arm | n | F1 present | F2 present |
|---|---|---|---|
| entry = retrace | 4470 | **4470 (100%)** | **4470 (100%)** |
| entry = formation | 5696 | 5696 (100%) | **0 — by construction** |

Full coverage because the span sits inside the footprint window and January 2026 is read via
`f2_oos_test.flow_frame()` (the complete rebuild) rather than the defective `fp_minutes.parquet`.

**F2 cannot exist under formation entry.** Entry is the close of the gap bar, so the retracement
window is empty. That is a property of the reading, not a data gap.

### Verification performed before these numbers were reported

| check | result |
|---|---|
| `w` is the contiguous leading slice of the 09:30–16:00 block (the exit walk's index assumption) | **290/290 sessions, 0 prefix mismatches, 0 missing minutes** |
| clustered t recomputed independently from the CSV | **+0.931 vs +0.93 reported** |
| outcome percentages sum to 100 in every arm | **yes** |
| equity curve is chronological (maxDD validity) | **yes** |
| bar-by-bar replay of one win and one loss | **exact** |
| **fill bars already through the stop (retrace arms)** | **923 / 4470 = 20.6%** |
| adversarial audit — 4 lenses, every finding independently refuted | **13 filed, 10 refuted, 2 distinct defects confirmed** |

That last row matters. On 2025-06-03 the trade fills at 10:07, breaches the stop **in that same
minute**, and *would have reached target at 10:49*. It is booked −1R. Had this card carried the
same-bar defect found in the sibling scripts on 2026-08-07, it would have looked dramatically
better than it is.

### Does this card add usable n to the pooled F2 test?

**Yes — but only 288 of its rows, and only from the retrace arms.**

- The retrace arms give **286–288 independent, fully flow-covered F2 observations** (one per
  session), which would take the pooled sample from **134 to roughly 420**.
- The other ~1,270 retrace rows are **pseudo-replication** and must not enter — 5.4 per session,
  overlapping, same direction.
- The formation arm contributes **nothing**: F2 does not exist for it.
- The card can only enter the pool under a **chosen stop reading**, so either it enters twice or
  the pooled result inherits this card's bound.

⚠️ Outcome-conditional F2 statistics were **computed and deliberately NOT reported here**, because
publishing them would informally pre-run the pooled test. They are in the trade log.

---

## VERDICT

**RETIRED — the expectancy bound is entirely negative under every reading of every ambiguity,
including the independent-draw slice and both sensitivity dimensions.**

**And this verdict says nothing about the poster.** Every rule that mattered was ours: the entry
trigger, the stop, the breakout definition, the window, the break-even, and the choice of 2R from
his range. **This tested our adaptation, and our adaptation loses.** A different filling of the
same blanks could produce a different answer, which is precisely the problem with a single-post
source and is why this card is flagged LOW PROVENANCE.

**And there is NO finding here that is about his post rather than our conventions.** The card
briefly claimed one — that his management was actively harmful — and an adversarial audit showed
that result was produced by look-ahead in our own harness. Corrected, his management does
essentially nothing (0.002R–0.027R per trade, all |t| < 0.61). **The correction removed the only
conclusion this card had about the poster.**

### Defects found by the audit and fixed

| # | defect | impact | status |
|---|---|---|---|
| 1 | **`cap_rules()` look-ahead** — the day stopped on a win's *outcome* while walking *entry* order, un-taking already-open positions (70% of deletions) | **falsified a stated conclusion**; every management |t| collapsed from up to −3.68 to inside ±0.61 | **fixed** — a win now blocks only entries at/after its own exit minute |
| 2 | **`marked_levels()` prior session** — `prev` was the previous *calendar* key, which is Globex-only Sunday on Mondays, so `pdh`/`pdl` were silently NaN on **61 of 290 sessions** (59 Mondays + 2 post-holiday Fridays) | nil on every reported number (decorative features), but a day-of-week-correlated hole in data the card promises for a future prereg | **fixed** — now the most recent prior day that actually has an RTH session; NaN count 293 → **0** |

**Ten further findings were filed and refuted**, including: the same-bar convention's asymmetry
(it is the locked convention), `atr_pct` ranked over the whole sample (logged, gated on nothing),
the 10:30 entry cutoff (declared, not silent), and the objection that the bound is four point
estimates whose CIs each straddle zero — correct, and the reason the verdict rests on *every*
reading landing negative rather than on any one arm's significance.

**Ledger:** this card spends **4 primary arms + 4 sensitivity arms**, raising the deflation bar
for every other candidate in the programme.
