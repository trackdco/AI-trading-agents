---
date: 2026-08-07
kind: Step-1 self-resolution log — 18 of 23 questions closed from the transcripts
rule: "resolved ONLY where the transcript decides it; a narrowed guess is not a resolution"
---

# Self-resolution log — 23 questions → 5

Re-read in context around each cited timestamp. **18 resolved, 5 still need Brake.**

The single most productive passage was `5pL41Pl7GM4 @ 05:50–17:05`, a backtest walkthrough I had
only sampled at Stage 2. It labels **four** manipulation-wick sizes and states a **stop-size
acceptability band** that appears nowhere else.

---

## RESOLVED — `zxck-wick-ce`

**Q1 · Which entry point is the default?** → **START OF THE WICK. CE only when the resulting stop
is too big.** `[inferred — three independent statements]`
> *"If you want to make sure that you get an entry, then put it at the beginning of the wick. If
> the risk is too much, then put it at the CE."* `[6opmiyFvJBA @ 08:40]`
> *"you put your limit at the beginning of the rejection block"* `[tNyT7tHOmGI @ 06:09]`; *"I put
> my entry at the rejection block, the start of the rejection block **again**"* `[@ 16:41]`
> *"I usually just take the closest entry… I take the bigger risk."* `[5pL41Pl7GM4 @ 24:25]`
**And "too big" now has a number** — see the new stop band below.

**Q2 · Sweep, or tap a PD array?** → **SWEEP + directional close is MANDATORY. The PD array is the
upgrade.** `[stated]`
> *"We swept liquidity and we had a bearish candle close. You can say that that's good enough.
> Your win rate might not be the best… what can we do to make our rejection block even better?
> …we have a level in the form of an order block right above it… As long as we have liquidity
> below, we have those two confluences stacked together."* `[a3LzCUZU5ko @ 02:24–03:34]`

**Q4 · Is displacement a GATE or a TELL?** → **A TELL, and specifically it tells you WHERE to
enter inside the block — not whether to take it.** `[stated]`
> *"this is kind of how you can differentiate between what's a good one and what's a bad one…
> that is very often going to be good… **what you want to look for, like where in the rejection
> block would you want to enter ideally**"* `[pMv3USznFdU @ 06:39–07:24]`
He never says to skip a block that lacks it.

**Q5 · Does "draw already taken" kill the setup?** → **YES, and it flips the bias.** `[stated by
Powell, so the third-party version is corroborated and can be used]`
> *"we have the distribution to the downside to hit this level. You guys knew this was going to
> be the draw. And that's why you wouldn't short this… because we hit the draw. So, you're now
> bullish."* `[38YtF6xFX4o @ 06:08–06:31]`

---

## RESOLVED — `zxck-10am-keyopen`

**Q6 · How big must the manipulation wick be?** → **≥10 points on NQ is acceptable; ≥15 is good;
≤8 is not.** `[inferred from four labelled examples]`
| wick | his verdict | source |
|---|---|---|
| 2 pt | *"Do we see that as sufficient? No."* | `5pL41Pl7GM4 @ 01:58` |
| 8 pt | *"mm gray area… Not a huge fan of that."* | `@ 09:26` |
| 10 pt | *"I wouldn't call it a great wick, but you can clearly see that's a wick"* | `@ 09:48–10:10` |
| 15 pt | *"Is this a sufficient wick? **Yes**"* | `@ 05:50` |

His functional test is visual: *"you can clearly see there's a wick there"* vs *"you can barely
see there's a wick… it looks like a little period on top"* `[@ 06:12–06:34]`. And the purpose is
stated: *"We just need a little manipulation to fool people into entering in that direction."*
`[@ 10:10]`

⚠️ **ASSUMPTION RECORDED:** we implement a **fixed ≥10-point floor**. He never says whether it
scales with volatility. If it should be ATR-scaled, that would be **our** rule, not his.

**Q7 · Retest, or re-cross?** → **RETEST. Manipulate through → move away → return to the level.**
`[stated]`
> *"10:00 a.m. opens lower, we distribute higher. Ideally for me, I want that retrace. I want the
> retrace to come down and **retest** 10:00 a.m."* `[tNyT7tHOmGI @ 15:56]`

**Q8 · Is the fib mandatory?** → **NO — a bonus. The 10:00 framework is the only requirement.**
`[stated]`
> *"0.79 on the fib, it doesn't get more discounted than that. **That's a bonus.** We have a one-
> and a five-minute rejection block… **That's a bonus.** And the 10:00 a.m. framework is
> following our idea, our plan."* `[tNyT7tHOmGI @ 16:19]`
Corroborated: *"we could mix the fib into it and we could have gotten a slightly better entry.
That's not worth it though. That's like three points better."* `[5pL41Pl7GM4 @ 11:21]`

**Q9 · Is 10:00 ET really the 4-hour candle open?** → **YES, on a CME-session-anchored grid.**
`[inferred — and arithmetically self-consistent]`
He asserts it directly and repeatedly `[Y-oqSZmNo4U @ 01:15, 02:03]`, and checks the 4-hour chart
live to judge the wick `[5pL41Pl7GM4 @ 05:50, 10:10]`. **A grid anchored at 18:00 ET (the CME
session open) gives boundaries 18 · 22 · 02 · 06 · 10 · 14 — which contains 10:00.** A
midnight-anchored grid gives 00 · 04 · 08 · 12 · 16 · 20 and does **not**. He also names **18:00
as a key open** `[38YtF6xFX4o @ 00:00]`, which is the grid anchor itself. Internally consistent.

---

## RESOLVED — `zxck-ifvg-50`

**Q12 · Is the standalone 5m/15m version real and separate from the 1m/3m trigger?** → **YES.**
`[stated — two explicit, different timeframe statements]`
> standalone: *"15 minute or five minute inverse fair value gap. Enter on the 50% mark… with a
> five-point stop."* `[lRgsHGWzO9E @ 07:44]`
> trigger: *"these are all on the one minute or three minute time frame."* `[r5_yNjXsv6k @ 02:20]`

**Q13 · Is a gap "inverted" on a CLOSE or a wick-through?** → **A CLOSE.** `[stated]`
> *"You see we **closed below** the fair value gap on the 545 candle. So what's your entry going
> to be?"* `[BOuJLWIisMI @ 04:39]`
Consistent with every other state change he defines by a close (rejection block, CISD).

---

## RESOLVED — `zxck-gap-fill-edge`

**Q16 · Separate model, or a level inside the wick-CE setup?** → **A LEVEL TYPE inside the wick-CE
setup.** `[inferred — both traded examples are wick trades]`
> *"This 4-hour wick… because we had this engineered liquidity, this wick, liquidity below the CE
> of the wick. Perfect. Short that."* `[86DOt135Wts @ 01:39]`
> *"today, I actually took the exact same setup. Which was this engineered liquidity below this
> 4-hour wick CE."* `[@ 02:04]`
**The card is kept** because the far-edge-vs-near-edge entry is the exact A/B against
`ash-unicorn-sb` and deserves its own spec — but it is a **variant, not an independent trial**.

**Q14 · Where does the stop go?** → **Consequential on Q16: beyond the wick, per `zxck-wick-ce`.**
`[inferred]` **Assumption stated:** since both traded examples are wick-CE trades, the gap-fill
entry inherits the wick-CE stop rather than getting a stop of its own.

**Q15 · Must the far edge be reached exactly?** → **YES, to the edge, within his ~1-point
tolerance.** `[stated + his general edge tolerance]`
> *"if you go on the 4-hour and look at these gap fills, it's going to look like it just ran
> through it. But if you actually go down in time frames, you're going to see we actually had a
> pretty decent **top tick** reaction of like 50 points."* `[86DOt135Wts @ 02:26]`
> tolerance: *"it hits 41, and the discount is at 40… I'm not really going to care."* `[y7KMT9CIVMo @ 03:32]`

---

## RESOLVED — `zxck-cisd`

**Q17 · Standalone, or only a trigger?** → **BOTH, explicitly.** `[stated]`
> *"it's not a strat — it **can be a strategy in and of itself**. You can just trade this and with
> good risk and just be done."* `[0u1L00q77bw @ 05:53]`
Standalone on daily/4H/1H `[rzfgAEYhxCg @ 00:47]`; trigger on the 1-minute `[BOuJLWIisMI @ 02:42]`.
**They are carded as two variants of one card, not averaged together.**

**Q18 · Which candle's opening price?** → **The IMMEDIATELY ADJACENT opposing candle.** `[stated]`
> *"we want then **the next candle after this one** to close above the opening price of this down
> close candle."* `[0u1L00q77bw @ 02:16]`; *"**The next candle** is going to close above this
> candle."* `[@ 02:41]`

**Q19 · Is the FVG-inversion pairing required?** → **NO — a bonus.** `[stated]`
> *"**if you want more confluence**, then this is what — this is like perfect."* `[0u1L00q77bw @ 10:11]`
⚠️ **Consequence:** `zxck-cisd` therefore does **NOT** pool with `ash-unicorn-sb` as a gap entry.
The `zxck-cisd-inversion` variant does, but only as a sub-case.

---

## RESOLVED — `zxck-news-draw`

**Q21 · Is the 30-second trigger essential?** → **NO — the sub-minute timeframe is optional and
the trigger is open-ended.** `[stated]`
> *"you can use the 30-second or even the 15-second, **whatever you feel like doing**."* `[c15YLeAKc2A @ 02:24]`
> *"you can use inverse fair value gaps **whatever you want** actually after the data high gets
> swept."* `[@ 03:11]`
**The card is NOT blocked on our 1-minute data.**

---

## RESOLVED — `zxck-amd-pdarray`

**Q23 · Is AMD a standalone model or a description?** → **A DESCRIPTION of the engineered-liquidity
mechanism.** `[stated — twice, independently]`
> *"Watch either engineered liquidity or the AMD. **They are pretty much the same thing.**"*
> `[D-suu0f3XKI @ 02:17]`
> *"this is also great to combine with the AMD video or engineered liquidity. **Those are kind of
> the same concept.**"* `[-izOcim8KRQ @ 01:38]`

**Consequence: `zxck-amd-pdarray` is WITHDRAWN as a card** and folded into `zxck-COMPONENTS.md` §B
as the shape description of the engineered-liquidity gate. Carding it separately would have
double-counted the same trades in the ledger. **Q22 no longer blocks it** — it only blocks
`zxck-mmxm-breaker`.

---

## NEW — a stop-size band nobody had, from the same passage

`5pL41Pl7GM4` states an **acceptability band for stop size** that appears in no other video:

| stop | his verdict | source |
|---|---|---|
| 5–7 pt | *"My favorite is like five to seven."* | `@ 16:42` |
| 15 pt | *"that's acceptable"* | `@ 06:55` |
| 17 pt | *"it's not great… Is it acceptable? Yes, **it is less than 20 points, which is acceptable**"* | `@ 10:59` |
| 25 pt | *"way too big… I'm not a huge fan of that"* | `@ 14:31` |

**Implementable rule: prefer 5–7 points; accept up to 20; reject at 25+.** This is the missing
half of Q1 — "if the risk is too much, put it at the CE" now has a number: **switch to the CE when
the start-of-wick stop would exceed ~20 points.**

---

## STILL OPEN — 5 questions for Brake

Q3 (liquidity side) · Q10 (ifvg bias) · Q11 (ifvg target) · Q20 (news CPI conflict) ·
Q22 (consolidation, MMXM only)
