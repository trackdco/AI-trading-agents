---
date: 2026-08-06
status: SPEC — not yet built
owner: Angus
tags: [agent, ict, htf-bias, narrative, spec]
---

# HTF Bias Agent — specification

ANGUS 2026-08-06:

> *"You will never be able to accurately mechanise higher time frame bias. That's a
> discretionary thing at its core… my awareness of the market, and my ability to read higher
> time frame context to draw that narrative, that's something that cannot be coded. What it
> can be tho, is an agent that is taught how to do so."*

> *"A bunch of these raw trades would not be taken if I was sitting there taking them, simply
> for the sake of well I'm very bullish so I'm not gonna short the market just because the
> setup is there. That's literally just pattern trading. I would veto 80% of the trades the
> raw trigger takes honestly, and I guarantee you the big majority of those would be losses.
> There's only one difference between me and an agent you can build, and that's knowledge.
> But you can train and educate."*

---

## 1. Why this layer exists — the empirical case

Every **mechanical** refinement attempted on the FVT book failed:

| attempt | result |
|---|---|
| setup quality score (5 dims, 4-yr consistent) | `corr(score, win rate) = +0.010` |
| entry order-flow filter | cuts winners and losers proportionally |
| 28 intra-trade price rules | **none** beat base |
| 18 intra-trade flow rules | **none** beat base |
| 800-cell parameter grid | rank correlation to holdout **−0.41** |
| tighter stops / wider stops / time stops | all worse |

The **only** lever that ever moved win rate was **direction**: 43.9% (shorts) → 50.4% (longs).

The mechanical layer is saturated at **+0.023R, PF 1.07, 47.1% win, 3.74 trades/day**. That
is the ceiling of what a rule can extract from this trigger. What remains is the read.

## 2. Architecture — a LIVE narrative, not a static gate

ANGUS, correcting an earlier draft of this spec:

> *"The goal isn't to veto 80% of trades. It's to be able to accurately draw a narrative on
> what's happening on the day, adapt intraday as things do or don't play out how u plan, and
> cut the shit trades. That's what the point of it is."*

That distinction drives the whole design. A pre-session bias set once and held is brittle: when
the read is wrong it stays wrong all session, vetoing good trades and waving through bad ones.
What is wanted is a **running thesis that revises against what price actually does.**

```
  PRE-SESSION      draw the narrative: draw on liquidity, premium/discount, PO3 state,
                   the levels that would CONFIRM it, the levels that would BREAK it

  INTRADAY         at each checkpoint, compare what happened to what was expected
   (revision)      -> CONFIRMED     price did what the thesis needed
                   -> DEVELOPING    unresolved, thesis intact
                   -> INVALIDATED   the stated invalidation hit
                   -> FLIPPED       the opposite thesis is now live

  ENTRY GATE       take mechanical entries agreeing with the CURRENT state
  EXIT             cut open trades when the thesis that justified them invalidates
```

The agent never picks entries and never sees the trigger. It maintains one thing: **what is
this market doing today, and is that still true.**

### 2.1 Why the revision loop is the valuable part

`fvt_intratrade.py` and `fvt_flowpath.py` tested 46 exit rules built on **price** and **flow**.
Every one lost to base, because ~a third of eventual winners look exactly like losers at any
given minute — the populations overlap and no threshold on *where the trade is* separates them.

A narrative exit is a different object. It does not ask *where is the trade*, it asks *is the
reason I took it still true.* That can fire while a trade is **green**, and it can hold through
a drawdown that price rules would cut. It is the only exit family not a function of the
excursion path, and the only one this project has not tested.

### 2.2 Checkpoints — event-driven, because narratives break at levels, not at times

| trigger | question |
|---|---|
| a mapped liquidity pool is swept | did it reject (confirmed) or accept through (broken)? |
| a HTF PD array is reached | did it react as the thesis required? |
| the stated invalidation level trades | thesis dead — say so |
| first 30 minutes of the session complete | did the expected manipulation leg happen? |
| a scheduled high-impact release passes | re-read from the new structure |
| every 30 minutes | floor, to catch drift the level map missed |

## 3. The prize, and the null that must be beaten

The veto RATE is an outcome, not a target. What matters is **separation**. Base book: 4,122
trades, 1,941 winners / 2,181 losers, 47.1% win.

**Payoffs are the REAL ones, not the nominal 1.5R/1R.** Many trades exit at the window end
before touching either bracket, so the book actually pays **+0.788R on wins and −0.658R on
losses**. Using the nominal figures overstates this table by roughly double — an error caught
by checking that the null row reproduces the measured +0.023R.

| winners kept | losers kept | trades left | win rate | **expectancy** |
|---:|---:|---:|---:|---:|
| 40% | 10% | 995 | 78.0% | **+0.470R** |
| 30% | 12% | 844 | 69.0% | **+0.340R** |
| 25% | 15% | 812 | 59.8% | **+0.207R** |
| **20%** | **20%** | **824** | **47.1%** | **+0.023R** ← the null, = the measured base |
| 15% | 25% | 836 | 34.8% | −0.155R |

**Filtering at random reproduces the base exactly.** Any veto rate is worthless unless winners
survive at a higher rate than losers. That row — not the 80% — is what has to be beaten.

Even the optimistic 40/10 row lands at **+0.47R**, not the +0.95R the nominal payoffs implied.
Still a 20× improvement on base, and still worth building for, but the honest number.

**Standing assumption, flagged:** this holds average win and loss size constant under
filtering. If the agent's vetoes also change the *size* distribution — likely, since narrative
invalidation should cut trades early and small — the real result will differ and must be
measured on the actual gated book rather than inferred from this table.

## 4. What the agent consumes — causally clean, pre-session

All from **completed prior sessions** plus the current overnight up to the session open. No
intraday data from the session being predicted.

| block | contents |
|---|---|
| **structure** | last 20 daily and 60×4H OHLC bars |
| **dealing range** | most recent significant swing high/low; where price sits in it (premium/discount) |
| **liquidity map** | PDH/PDL, PWH/PWL, prior month H/L, equal highs/lows, session highs/lows, untested swing points |
| **PD arrays** | unfilled daily/4H FVGs, order blocks, breakers, mitigation blocks, with age |
| **gaps** | New Week Opening Gap, New Day Opening Gap |
| **PO3 state** | where in the daily/weekly candle cycle we are; has manipulation happened |
| **IPDA ranges** | 20 / 40 / 60 day lookback highs and lows |
| **overnight** | Asia and London session ranges, what they swept, where they closed |
| **calendar** | high-impact releases scheduled today (event type only, no outcome) |

## 5. The ICT reasoning framework it is taught

Not a checklist — a narrative order. The agent works through it and produces reasoning, not a
score.

1. **Where is the draw on liquidity?** Every move is toward liquidity. Identify the pools
   above and below (old highs/lows, equal highs/lows, untested extremes) and judge which one
   the market is being drawn to. *This is the primary question; everything else supports it.*
2. **Premium or discount?** Anchor the relevant dealing range. Above 50% = premium (favour
   selling toward discount); below = discount. Bias is only credible if price is positioned to
   travel toward the draw.
3. **What has already happened in the cycle?** Power of Three: has accumulation and
   manipulation already occurred, or is the manipulation leg still ahead? A bullish read with
   the Judas swing already printed is very different from one before it.
4. **What HTF PD arrays are in the path?** Unfilled FVGs, order blocks, breakers between price
   and the draw. These are where the move should react — they set targets and invalidation.
5. **What did the overnight do?** Did Asia/London sweep a level and reject, or accept through
   it? Acceptance and rejection mean opposite things.
6. **What invalidates this?** The agent must state the price or event that kills the read.
   A narrative with no invalidation is not a narrative.

**Explicitly excluded: SMT divergence.** Angus's ruling — *"nah fuck ES. smt divergences have
been proven to have no delta"* — and we hold no ES data.

## 6. Output contract

```json
{
  "session": "2026-03-14 NY_AM",
  "bias": "long | short | none",
  "conviction": 0-100,
  "draw_on_liquidity": "price level the market is being drawn to",
  "dealing_range": {"high": 0.0, "low": 0.0, "position": "premium|discount|equilibrium"},
  "po3_state": "pre-manipulation | post-manipulation | distribution",
  "key_levels": [{"price": 0.0, "type": "FVG|OB|liquidity|breaker", "role": "target|invalidation"}],
  "invalidation": "the level or event that kills this read",
  "narrative": "2-4 sentences of actual reasoning",
  "confidence_drivers": ["what is carrying the read"]
}
```

`conviction` matters as much as `bias`: it lets the gate be graded (veto below X, size up above
Y) rather than binary, and it is the field that makes the agent auditable when it is wrong.

## 7. THE VALIDATION PROBLEM — and this is the crux

**An LLM asked "what was NQ's bias on 14 March 2025" may simply recall the answer.** Any
backtest built that way is contaminated, and it is the same class of failure as the depth read
that was one bar late and the "confirmation" signal that was really a +10.57pt head start —
except it hides inside the model instead of the code, so it cannot be caught by reading the
diff.

**The fix: anonymised replay.**

- **strip all dates** — no year, month, weekday
- **normalise price** — index the window to 100.00 at its first bar; report everything in index
  points and percentages
- **strip the instrument** — no "NQ", no contract codes
- **randomise presentation order** across the corpus
- **cap the window** — only the trailing context, never the full history that would fingerprint
  a period

A model cannot recall what it cannot identify. Then score the calls against what actually
happened. That converts "can an agent read context" into a testable claim on the **1,103
sessions we already hold**.

**Contamination audit, run before anything else:** present 50 anonymised windows and ask the
agent to name the instrument and date. If it can do better than chance, the anonymisation has
failed and the whole result is void.

## 8. Controls — non-negotiable

| control | why |
|---|---|
| **vs "always long"** | NQ went ~11,000 → ~29,000 across our data. A bullish agent looks brilliant for free. **This is the single most important control.** |
| **vs random bias** at the same veto rate | the 20%/20% null in §3 |
| **vs the crude mechanical proxies** | D1 candle, 20-day trend, premium/discount — the agent must beat the rules it is replacing |
| **four-era split** | 2023 / 2024 / 2025 / 2026 independently, as with everything else |
| **conviction monotonicity** | high-conviction calls must outperform low-conviction ones. If they don't, the agent isn't reading, it's guessing |

## 9. Curriculum

Source material, in priority order:

1. **ICT's own content on narrative and bias** — the long-form material on draw on liquidity,
   PD arrays, PO3, IPDA ranges. Not the entry-model videos.
2. **The 110 transcripts already cached** in `research/youtube/transcripts/`.
3. **Angus's own read process** — the highest-value input and the one thing not in any video.
   What he looks at, in what order, and what makes him say "I'm very bullish today."
4. **Our own findings**, which correct the folklore: the 80% rule fails at ~20% on our data;
   prior-session HVNs hold price but LVNs do nothing; SMT is out.

The agent is taught the **reasoning order**, not a lookup table. It should be able to explain
why a level matters, not just name it.

## 10. Build order

1. **Context builder** — assemble §4 per session, causally clean, anonymised. Pure data work,
   no agent involved. *(This is also independently useful.)*
2. **Contamination audit** (§7). If this fails, stop.
3. **Curriculum + system prompt** from §5 and §9.
4. **Bias calls on 1,103 anonymised sessions**, cached to disk with full reasoning.
5. **Score against controls** (§8) before ever touching the trade book.
6. **Only if it beats "always long"**: join to the FVT book and measure the gated expectancy
   against §3.
7. Forward-test. We have no clean holdout left — every era is used — so live paper trading is
   the only remaining honest validation.

## 11. Kill criteria, declared now

- fails the contamination audit
- does not beat **always-long** on directional accuracy
- conviction does not correlate with accuracy
- gated book does not beat the ungated book in all four eras
- veto rate lands far from Angus's stated ~80% without a reasoned explanation

## 12. What this is not

It is **not** a prediction model, and it does not need to be right often. It needs to be right
**more often than the coin-flip baseline, on the trades the mechanical layer would otherwise
take blind**. The mechanical layer already generates the edge candidates; the agent's only job
is to stop the ones that are fighting the market.

As Angus put it: *"that's literally just pattern trading"* — the veto is what turns a pattern
into a trade.
