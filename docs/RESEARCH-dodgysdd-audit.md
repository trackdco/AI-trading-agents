# AUDIT — DodgysDD, the inversion fair value gap (iFVG) model

**RESEARCH ONLY. Reverse-engineered from public videos and UNVALIDATED.** Nothing here
is a measured edge; it is a catalogue of what the channel *states*, with the quote that
supports each line.

## Evidence limits — read this before using anything below

| | |
|---|---|
| channel | `@DodgysDD`, 90,700 subscribers, **1,628 videos**, since 2019-02-26, US |
| long-form videos (`/videos`) | **474** (the 1,628 count includes Shorts and streams) |
| transcripts fetched | **42** · 528,037 chars |
| coverage of long-form | **8.9%** |

Fetch stopped at 42: YouTube rate-limited this host (`IpBlocked` / `RequestBlocked`
after ~42 successes). The corpus is resumable — `scripts/fetch_channel_transcripts.py`
skips what is on disk — so coverage rises with each pass.

**Captions only, no video.** He teaches by drawing on a chart while talking, so every
visual definition is lost: *"you don't want it to be wick like this… it has to be like
this."* That is precisely where the quantitative meaning of "abnormal size" and
"relative to the candles around it" lives. Nothing below is invented, but the visual
half of this channel's teaching is not in evidence.

Densest sources in the corpus: *The Complete IFVG Masterclass* (50,926 chars), *Raw &
Real IFVG Masterclass* (37,613), *My full 2026 IFVG model Breakdown*, *IFVG's Don't
Work.*, *My High Accuracy Inverse Candle Closure Checklist*, *This Gold Trading Strategy
is Technically UNBEATABLE*.

**Instruments: NQ and ES.** Index futures, not gold. Session is *"the New York am
session, sometimes the PM."*

**Commercial context, because it shapes the content.** The channel sells an iFVG
indicator, runs a paid Discord, and every video carries an Apex prop-firm affiliate code.
Sizing advice is given in Apex-account terms. That does not make the rules wrong, but it
means the claimed accuracy figures are marketing-adjacent and should be treated as
hypotheses, not evidence.

---

## 0. THE CURRENT MODEL (2026) — and it is not the one in §2

The flagship changed. §2 below is the 2023 *"one setup for life"*; this is what he
teaches now, from `E1BIVjBwLxQ` *My full 2026 IFVG model Breakdown*. **Anyone coding
from the older videos would build the wrong system.**

**The base sequence, unchanged:**
> *"a delivery from a fair value gap… a liquidity sweep, so generally we're down
> trending, we sweep below inside of a fair value gap, and then we get some sort of
> inversion fair value gap back to the upside"*

**Context is mandatory, and this is stated as the discriminator:**
> *"We don't like just an inversion fair value gap in the middle of nowhere. We like it
> delivering out of a key area, which maybe this is a London low, maybe it's an Asia
> low, maybe it's a news low, it's equal lows, and then usually we want like a higher
> time frame fair value gap attached to that"*

**What he says changed in 2026** — *"Yes, but no… I am looking for a lot of other
confluences lately because of how bad price action's been"*:

| change | quote |
|---|---|
| **trend-line liquidity is now the primary draw** | *"The number one draw on liquidity I have used in the past year probably is the trend line liquidity"* — ~45°, built from lower lows/highs |
| **engineered > session levels** | *"ideally you want to combine like a London low with a relative equal low… That is going to be better than just targeting Asia high, which I did a lot more 2 years ago"* |
| **momentum entry now required** | *"entering off of good momentum, such as a death candle or birth candle, is the biggest change… I'm barely entering off of choppy closes"* |
| **added confluences** | order block at the same area, or a CISD |
| **time shifted earlier** | *"a lot of my trades are during 9:30 to 10:00 more than they ever were… I used to trade a lot more like from 10:00 to 11:00"* |
| **Judas swing added** | 9:30 open sweeps a high, then reverses — *"at least three times a week in today's market"*, vs *"we did not get that every day"* in 2024 |

**An explicit invalidation, which is rare and worth having:**
> *"If we had a giant wick sweeping the high, that is not a trend line anymore. All this
> liquidity right here, right here, and right here have been ran, so therefore even if
> we did get that long it would have been bad"*

A trend line whose stops are already taken is dead. That is mechanically codable.

**His stated reason for the trend-line focus is a claim about crowding**, not structure:
> *"we have more retail traders than ever trading, and they're all trading trend lines,
> and that's why you see all these trend lines being built up"*

## 0b. Win-rate philosophy — a real contrast with tomtrades

He teaches explicitly that a high hit rate is unnecessary, and has a whole video on the
arithmetic (`m1Ly_P-XnnU`, *How You Can be Profitable with Just 30% Win rate*):
> *"you don't need more than like a 30% win rate to be profitable taking five setups"*
> *"at a one to one RR… you need to have a 60% win rate or higher to be profitable. At a
> nine [R] play, you only need a 10% chance"*

This is the opposite posture to the tomtrades corpus, which sells 76–88% hit rates and
whose arithmetic failed precisely because payoff was ignored. Dodgy's framing is
payoff-first and, as arithmetic, it is correct.

**Other stated absolutes worth pinning:**
- *"I'm always going to keep a hard stop at the swing high no matter what"*
- *"I'm always going to go to New York session"*
- *"The most obvious setup for me with IFVGs are always giant swing points"*
- *"we always want the market to sweep some sort of higher low"*
- the sweep must be **obvious** — *"it needs to be one, an obvious liquidity sweep"*

---

## 1. The core model: inversion fair value gap

> *"as you all know I only use inverse fair value gaps"*

The whole framework is one trigger: a fair value gap forms, price later **closes through
it**, and that inversion is the entry. Everything else — the data high/low setup, the
macro times, the quality filters — is context that decides *which* iFVGs to take.

> *"you play candle okay you short wherever the inverse is"*

The FVG must be **violated by a close**, not merely wicked:
> *"this candle doesn't close under, this one does close under barely, so this would be a
> short"*

**Preferred form is a singular FVG.** Where a leg contains several:
> *"if there's multiple fair value gaps in the same leg try to go to the higher time
> frame, use that one instead"*

Extra confluence if the zone is also a **BPR** and sits in **discount**:
> *"it is an inverse as well and it is a BPR so this one I would draw"* · *"you can see
> it's also in discount so to me this looks good"*

---

## 2. The flagship setup: data highs and data lows

Presented as *"my official one setup for life."*

**Definition.** A high or low printed on a **news candle** — 08:30, 10:00, FOMC, 14:00 —
whose wick is of **abnormal size**.
> *"it's a low or high we get on an 8:30 news candle, it could be a 10:00 news candle, it
> could be an FOMC news candle, and the thing that they all have in common is you want to
> see either one of the wicks have like an abnormal size"*

**Two hard conditions on the wick:**
1. Abnormal size — *"you don't want it to be wick like this, this doesn't really mean
   anything, it has to be like this"*
2. Also a **1-minute swing point** — *"I make sure that wick is on the one minute it is
   also a swing low… it has to be a low and then here's a lower low and then here's a
   higher low"*

**Then price must trade AWAY from it, not into it:**
> *"you want to see that traded away from… you do not want to see that hit, you want to
> see us totally just go the opposite way"*

**Entry requires a PD array to form on the move away.** This is stated as the gating
condition, not a preference:
> *"in order to actually entry, like the entry criteria on the setup, it needs PD
> arrays… it needs a FVG, it needs an order block"*
> *"if price doesn't form any bullish [FVGs] here, any PD arrays, how are we supposed to
> take this back down to these data lows? We can't."*

So the sequence is: **abnormal news wick → price trades away → PD array forms → PD array
inverts → enter, targeting the wick.**

**Stated frequency:** *"very rare, they probably form once every two weeks."*

---

## 3. Quality filters — the three iFVG characteristics

From the dedicated video, the criteria for an *"obvious"* iFVG. The stated rationale is
backtesting, repeatedly:
> *"I find the most obvious ones work the best and that's just based off back testing"*

**(a) Size relative to neighbours — "Gap Clarity Theory."**
> *"I'm always looking at the fair value gap we create relative compared to the maybe 10,
> 20, 30 candles around it"* · *"this one is too tiny relative to the candles around it
> but this one it's just right"*

Not the biggest, not the smallest — it must **stand out without being giant**.

**(b) Stop size in points — 10 to 20 is the sweet spot.**
> *"in terms of points I feel like 10 to 20 points is a sweet spot but anything 30, 40,
> 50 those get really big"*

The reasoning is **position sizing on a prop account**, not market structure: on a 50K
account risking \$200, a 100-point stop permits one micro contract, which forbids
scaling. Note this carefully — **it is a constraint of the account, not a property of the
setup**, and it would not transfer to a differently-sized book.

Large zones are handled by dropping timeframe rather than skipping:
> *"wait for like the 30-point entry zones to be tapped into and then go to the lower time
> frame and try to take a lower time frame setup off the higher time frame"*
(5-minute zone → 30-second entry, cutting a ~30-point stop to ~10.)

**(c) The ten-foot test.**
> *"can you see it 10 feet away from the screen"* · *"that means a lot of traders are
> seeing it, which means there's probably a lot of liquidity"*

---

## 4. Time: the ICT macros

**Macro windows** (their stated set): the **last 10 minutes of each hour plus the first
10 of the next** — 08:50–09:10, 09:50–10:10, 10:50–11:10 — plus **15:15–15:45**.

**What a macro is for:** *"during the macro times I'm typically looking for a draw on
liquidity to get ran."*

**Entry need not be inside the macro** — the *resolution* should be:
> *"you don't have to enter in the macro time… you should expect price, as long as it's
> moving that direction, to run that draw on liquidity during the macro time"*

**The macro is used mainly as an EXIT rule.** This is the most mechanically testable
thing in the whole audit:
> *"if it's 10:10 already I would probably get out of a lot of my position because I
> wouldn't like how this isn't ran by 10:10"*
> *"why would you want to waste mental capital when 80% of the time the macro should run
> the liquidity"*

**And it suppresses the breakeven rule while the macro is live:**
> *"even though we hit this internal low, I don't move myself to break even because we're
> in a macro time… if this candle occurs at the end of the macro time and the macro just
> ends, well then yeah, get out"*

**Consolidation into a macro is the preferred context:**
> *"a lot of times the best macros and the most movement inside macros will occur after
> consolidation"*

Their own framing of how load-bearing this is:
> *"I use them kind of more emotionally than actually for my strategy"*

---

## 5. Execution — entry, stop, targets

| element | rule | quote |
|---|---|---|
| entry | at the inversion level, on the close through the FVG | *"you short wherever the inverse is"* |
| stop | beyond the FVG | *"stop loss is going to be above this bearish fair value gap"* |
| target 1 | **internal liquidity, always** | *"your first target is always the internal liquidity"* |
| on TP1 | **stop to breakeven, always** | *"once you hit that first target stop always goes to break even"* |
| scaling | partial at TP1 | *"I'm scaling some there"* |
| final target | the data high / low | *"you hold the rest till those data highs or the lows and then you sell"* |
| re-entry | permitted after a BE stop | *"sometimes you might get stopped to break even which is okay but there's always a chance to reenter"* |
| distance filter | skip zones far from current price | *"I would not short this candle cuz this is kind of far away from me"* |

**Sizing (Apex-specific):** 50K account, **\$200 risk per trade** — *"I always say \$200
and I think \$200 is a really good risk… definitely the sweet spot."*

---

## 6. Claims on the record

| claim | source | status |
|---|---|---|
| data highs/lows are hit **the same day**, all but one day in five months | *"my friend back tested it"* | **second-hand, no data shown.** The single most testable claim here |
| macros run the draw **~80%** of the time | stated, no source | untested |
| obvious iFVGs outperform subtle ones | *"based off back testing"* | own backtest, not shown |
| data high/low setup is *"very accurate"* | stated | no number given |

---

## 7. Ambiguities that must be resolved before coding

1. **"Abnormal size" is never quantified.** No multiple of ATR, no percentile, no
   comparison window. It is the entry condition for the flagship setup and it is defined
   only by example.
2. **"Relative to the candles around it" — same problem.** *"10, 20, 30 candles"* is
   given as a range, and "stands out but isn't giant" has no threshold.
3. **Which timeframe is the FVG on?** Examples move between 1m, 30s and 5m without a
   stated rule for choosing, beyond "go higher if there are multiple in a leg."
4. **"Internal liquidity" is undefined** as a mechanical level, yet it is the first
   target and it triggers the breakeven move.
5. **The macro set is inconsistent.** The stated rule is last-10-plus-first-10 of every
   hour, but 15:15–15:45 is a 30-minute window that does not fit it, and is justified as
   *"he's also mentioned this time before and this does happen to work a lot."*
6. **The 10–20 point stop filter is an account artifact.** It follows from \$200 risk on
   a 50K Apex account. Whether it has any predictive content independent of sizing is an
   open and easily testable question — and worth testing, since a stop-size filter was
   the single largest effect in the GC census (BR-29/BR-45 territory).

---

## 8. What I would test first, in order

1. **The data high/low base rate.** Does an abnormal-wick news high/low get traded back
   to the same session? It is a pure base rate, needs no entry model, and it is the claim
   the whole flagship setup rests on. Directly analogous to BR-1 and measurable on NQ/ES
   1-minute data already in the repo.
2. **The macro exit rule.** "If the draw isn't run by the macro's end, get out" is fully
   mechanical once "draw" is fixed, and it is a *rule change*, not a filter — the same
   class of lever that mattered most in the CBR autopsy.
3. **Stop-size filter, independent of sizing.** Does 10–20 points beat 30–50 in EV once
   cost is charged correctly? The GC census says stop size is mostly the cost denominator
   — the same decomposition applies here and would settle it quickly.
4. **Obviousness.** "Relative size vs surrounding candles" is codable as a percentile and
   is the channel's central quality claim.

Everything above is a hypothesis catalogue. Per the repo's non-negotiables, none of it
is a finding until it is measured, day-clustered and calibrated against a null.
