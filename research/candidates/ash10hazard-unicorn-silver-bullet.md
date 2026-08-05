---
id: ash-unicorn-sb
name: "Unicorn Model / ICT Silver Bullet — his names, both used in the same video"
trader: ash10hazard
sources: [1cMWnAxElA0, pD5l_gEje9I, UBIHB1oB784, qngA8aIfV0M, 01xGCvuY3p8, N1EXytfVsiI, Ee_tC5P-F20]
sessions: [New York, London]
instruments: [NQ (traded), ES (confirmation only, not traded)]
timeframes: [HTF: 15m for sweeps/structure, entry: 1m–5m]
components: [liquidity-sweep, momentum-shift, fvg-fill, order-block-tap, multi-tf-alignment, session-timing, structure-stop, fixed-r, runner]
maturity: core (7 videos, rev d)
---

## Edge thesis

He never states a mechanism. The closest to a thesis is that the sequence is
algorithmic and repeatable — *"there are lots of times where outside a macro, a trade will
algorithmically play out perfectly"* `[1cMWnAxElA0 @ 01:04]` — and that macro windows are
*"the highest probability, you know, time zones for where these trades occur"* `[@ 01:04]`.

**No claim about who is on the other side, why they are wrong, or why the pattern
persists.** `[inferred]` from absence: this is a pattern-recognition model, not a
mechanism-based one. Flagging because every other card in this repo has a stated mechanism
and this one genuinely does not.

## Market context / bias

**Session:** New York open 09:30 ET to 14:15 ET. `[stated]`
> *"The New York open, which happens at 9:30 a.m. New York local time… And then you'll be
> trading until the end of the PM macro… till 2:15 p.m."* `[@ 00:00–00:21]`

**✅ MACRO IS A MANDATORY GATE — resolved rev d.** `[stated]`
> *"if there is a good setup outside of macro, even by 5 minutes, should you take it? **No,
> you shouldn't.**"* `[qngA8aIfV0M @ 03:00]`; *"**Even if it's 1 minute outside**, you should
> not take that trade."* `[@ 03:48]`

He argues against full-session trading `[qngA8aIfV0M @ 03:23]`, and treats a 30-second
overrun as a rule break `[N1EXytfVsiI @ 00:49]`. **`1cMWnAxElA0 @ 01:26` is superseded.**

| window (ET) | status |
|---|---|
| 09:45–10:15 | **highest probability** |
| 10:45–11:15 | traded |
| 11:45–12:15 | traded |
| 12:45–13:15 | **skipped — "low probability macro"** |
| 13:45–14:15 | traded, last of day |
| **London** 02:45–03:15, 03:45–04:15 | *"both very high probability"*; his own stated expectancy **1–2R per MONTH** `[qngA8aIfV0M @ 02:10]` |

**Daily stop:** two losing trades before the last session ends the day; wins never stop it
`[qngA8aIfV0M @ 00:52]`. `[stated]`

**Directional bias — two layers.**

*Which side to trade* comes from which side of liquidity was swept — sweep of buy-side →
look for shorts. `[inferred]` from all four examples in `1cMWnAxElA0 @ 05:03, 07:16, 08:50,
12:04`; never stated in the abstract.

*Whether bias is aligned* (step 6 of his checklist) is **multi-timeframe imbalance
alignment**. `[stated]` `[UBIHB1oB784 @ 01:07]`:
> *"on the 4-hour time frame, we're trading out of this 4-hour bullish gap. If we look on the
> 1-hour, we're trading out of this 1-hour bullish gap. Look on the 15, we're trading out of
> that 15. If we look at the five as well, trading out of a 5-minute bullish gap, too. So, we
> have a completely fully bullish bias."*

Price trading out of a gap in the same direction on **4H, 1H, 15m and 5m**. He shows 4/4 and
calls it "completely fully" bullish; **how many must align for a valid setup is not stated**
— `[unclear — needs review]`.

## Setup — conditions that must be present

**Rev 2026-08-05b — he enumerates the system explicitly for the first time** in
`pD5l_gEje9I @ 00:00–01:00`. This numbered form supersedes the reconstruction below it,
which came from watching examples rather than from a stated checklist:

> *"the key factors are one, you need to be inside a macro. Second, you need to have a
> liquidity sweep… And then you're looking for a market structure shift after on both
> assets… And then after a shift in market structure, you want to see an inverse of an order
> block… Then with that inverse order block, you want to see it paired with a Fav value gap.
> And that F value gap is going to be your point of entry… And then along with all of this,
> you need to have an aligned bias."*

| # | condition | notes |
|---|---|---|
| 1 | **Inside a macro** | ⚠️ contradicts `1cMWnAxElA0` — see Contradictions #1 |
| 2 | **Liquidity sweep** — 5- or 15-min low, or session liquidity (London/Asia highs and lows) | timeframe widened vs video 1 |
| 3 | **Market structure shift on both NQ and ES** | |
| 4 | **Inverse order block** — bearish OB inverses for longs, bullish for shorts | becomes *mitigation* or *breaker* block "depending on if the previous short-term high got taken" `[pD5l_gEje9I @ 00:42]` |
| 5 | **Inverse OB paired with a fair value gap** | the FVG is the entry |
| 6 | **Aligned bias** | ✅ **operationalised in rev c** — multi-timeframe imbalance alignment, see below |

**Optional confluence — SMT divergence.** `[stated]` Explicitly not required:
> *"that would be a bullish SMT between the two assets which is you know it's **not a
> compulsory confluence** with this model. However, it does help build the narrative."*
> `[pD5l_gEje9I @ 01:46]`

**Invalidation level.** `[stated]` A 5-min swing high/low, roughly three short-term highs
out, whose breach kills the setup:
> *"I have a 5 minute swing high marked out. That would be where the trade gets invalidated"*
> `[pD5l_gEje9I @ 01:24]`; *"That's three short-term highs out. So this would be your
> invalidation high."* `[@ 06:18]`

---

### Original reconstruction from `1cMWnAxElA0` (retained — consistent with the above)

Sequence, as demonstrated in every example:

1. **Liquidity sweep.** `[stated]` Any of:
   - a 15-minute swing high/low taken out — *preferred*
   - a 15-minute **internal** high/low — accepted *only* "if it's clear where price is drawing to"
   - **session liquidity**: *"London highs, Asia highs, New York lows, lunch highs, lunch lows"* `[@ 02:07]`
   > *"I look for 15-minute highs and lows to get swept. But for me personally, I don't need
   > to see a 15-minute swing high or swing low get swept, but I'll definitely prefer a swing
   > point."* `[@ 01:26–01:48]`

2. **Most recent short-term high/low also taken.** `[stated]` `[@ 05:26]`

3. **Shift in market structure — on BOTH NQ and ES.** `[stated]`
   > *"we can see here we have a clear shift in market structure on NQ, clear shift in market
   > structure on the S&P 500"* `[@ 05:26]`

4. **Inverted order block paired with a fair value gap** — located on ES. `[stated]`
   > *"We're looking for a bullish order block to get inverse. Where can we see it? On ES
   > right here… It's paired with a fair value gap on ES."* `[@ 05:47]`

**He does not define** how an order block is identified, or what makes a structure shift
"clear". `he doesn't specify`

## Entry trigger

Price fills the fair value gap on NQ. `[stated]`
> *"We have a clear shift on NQ and we have that bearish gap that's been presented and you
> can see that NQ has actually filled this bearish gap. So, this would have been your
> entry."* `[@ 05:47–06:09]`

**ES-lag sub-rule** `[stated]` — he flags this as new:
> *"If the model was there, and ES hasn't quite shifted, and there's a model to take, I will
> take the trade, but if ES then fails to shift on the next candle, I will close out that
> position."* `[@ 09:14]`

## Stop / invalidation

Recent swing high (for shorts) / swing low (for longs). `[stated]` `[@ 06:09]`

Variant, condition undefined:
> *"Sometimes now with my stop placements too, I'm actually putting it two previous swing
> highs if the RR is good enough."* `[@ 06:09]`

**He never defines "good enough".** `[unclear — needs review]`

## Targets / trade management

**Target: the opposing draw on liquidity.** `[stated]` Whether that is *capped* at 2R is
disputed across videos:
> *"I'll look for a two R at the opposing draw on liquidity which is clear price is going to
> go and draw to hit anyway"* `[1cMWnAxElA0 @ 06:30]`; *"going for a flat 1 to 2 RR"*
> `[pD5l_gEje9I @ 02:57]`

but in `UBIHB1oB784 @ 01:29` he takes what the draw gives — 53-point stop, 122-point target,
≈**2.3R** — and banks ~2.45R. **Reading: the draw sets the target and R is the consequence;
"2R" is the typical result, not a cap.** `[inferred]` — see Contradictions #4.

**Break-even:** when price reaches 50% of the entry→TP range. `[stated]`
> *"we have this swing low on NQ that's 50% of the range between our entry point and TP. So,
> once price takes this point, I would be going break even."* `[@ 06:53]`

Confirmed three times: `[1cMWnAxElA0 @ 06:53]`, `[pD5l_gEje9I @ 03:50]`,
`[UBIHB1oB784 @ 03:12]`. **This is the most consistently stated rule in the whole card.**

The **New York open low** variant `[1cMWnAxElA0 @ 10:01]` appears once and never again —
now read as a one-off, not a competing rule.

**Trailing — stated then overridden in all three videos.** Treat this section as
documentation of what he *says*, not what he *does*. In `UBIHB1oB784 @ 07:40` he states his
own rule would have lost the trade being demonstrated:
> *"trailing with the normal way that I usually trail is, you know, it's going to get stopped
> out. You got to let price do its thing."*
> and `[@ 03:40]`: *"there's nowhere to really trail my stop loss to yet. I don't see any
> valid points to do that, and I want to let my trade run."*

The stated system: `[stated]`
> *"if it hits a 1R, you trail aggressively, hits a 2R, you go break even, and if it hits a
> 3R, then obviously you let the trade play out for a 3R."* `[@ 02:54]`

immediately followed by:

> *"I don't like to be so systematic anymore in terms of the way I trail. I look at the
> scenario."* `[@ 03:19]`

## Risk & sizing

**R:R target 2R** `[stated]`, once described as *"my TP for a one to two"* `[@ 12:52]`.
Risk per trade, position sizing, daily loss limits: `he doesn't specify`.

## Filters / avoid conditions

Only one, and it is discretionary: `[stated]`
> *"I didn't take any more trades throughout the day. I wanted to wait for the PM just
> because I didn't like the way price was kind of chopping around in this range here."*
> `[@ 12:04]`

No news filter, no volatility filter, no maximum-trades rule. `he doesn't specify`

## Performance claims

`[trader-claimed, unverified]`

- **8R over two days from four executions**, 21–22 May 2026 `[@ 00:00, 13:19]`
- *"Nine times out of 10 it's going to go to that draw if the model does play out"* `[@ 06:30]`
  — conditional on "if the model does play out", so not a win-rate claim
- All four examples shown are winners. **No losing example appears in this video.**

**Rev 2026-08-05b — `pD5l_gEje9I` discloses a live shortfall, which is worth crediting.**
The walkthrough of trade 1 reaches 2R; he then states the live trade did not:
> *"However, in the actual trade, we can see that price comes down and I got stopped out at
> this area here… So I got stopped out for a 1 [R]."* `[pD5l_gEje9I @ 04:46]`

And he names the reason explicitly:
> *"during the live market conditions, you know, you can't really go back and cherrypick
> precise entries… in the first trade, we were very close to a 2R, but it didn't hit.
> Whereas… when we're back testing here, the entry was better."* `[@ 08:30]`

He nets the day at **2.8R rather than the 4R shown on the chart** `[@ 08:04]`.
`[trader-claimed, unverified]` — but the correction runs *against* his own interest, and it
is the only instance so far in the reviewed material where a live result underperforms the
walkthrough. It should temper, though not overturn, the channel-level critique.

Channel-level context: of ~50 recent videos, ~40 are P&L headlines and **one** shows a loss.
See `research/ash10hazard/channel-overview.md`.

## Contradictions / open questions

1. **⚠️ TOP PRIORITY — Macro: hard requirement or optional confluence? The two videos say
   opposite things.**

   | source | position |
   |---|---|
   | `1cMWnAxElA0 @ 01:26` | **Not required.** *"just trading the full session completely eliminates the fact that you missed those trades. And if a trade presents itself, then it's valid to take."* |
   | `pD5l_gEje9I @ 00:00` | **Required, key factor #1.** *"the key factors are one, you need to be inside a macro."* |

   And in `pD5l_gEje9I` he has a fully valid model and **waits** for the macro:
   > *"we've got a FEL gap paired with the breaker, but we just need that entry inside a
   > macro."* `[@ 02:34]`

   **Unresolved, and it matters more than any other open question**: it decides whether the
   macro windows are an event filter, which changes any test's event count by roughly an
   order of magnitude. Needs a third video or a direct answer.

2. **Sweep timeframe disagrees between videos** — "15-minute highs and lows"
   `[1cMWnAxElA0 @ 01:26]` vs "a five or 15 minute low" `[pD5l_gEje9I @ 00:21]`.
   Which governs? `[unclear — needs review]`

3. ~~**"Aligned bias" never operationalised.**~~ **RESOLVED rev c** — it is multi-timeframe
   imbalance alignment (4H/1H/15m/5m) `[UBIHB1oB784 @ 01:07]`. Residual: how many of the four
   must align. `[unclear — needs review]`

4. **Target: fixed 2R or take-the-draw?** *"flat 1 to 2 RR"* `[pD5l_gEje9I @ 02:57]` vs a
   122-point target on a 53-point stop ≈2.3R `[UBIHB1oB784 @ 01:29]`. Current reading is
   take-the-draw, but it is `[inferred]`.

5. **The stated trailing system is contradicted in all three videos**, most sharply in
   `UBIHB1oB784 @ 07:40` where he says his normal trailing *"is going to get stopped out"* on
   the trade being demonstrated. **Any faithful test must implement the discretionary
   behaviour, which is not specifiable — or test a fixed variant and label it as ours.**
2. **Break-even has two different rules in one video** — 50% of entry→TP range `[@ 06:53]`
   vs the New York open low `[@ 10:01]`. He does not reconcile them.
3. **Trailing is stated as a system then explicitly abandoned** `[@ 02:54]` vs `[@ 03:19]`.
4. **"Good enough" RR** for the wider stop is undefined `[@ 06:09]`.
5. **"Clear where price is drawing to"** — the gate admitting internal 15-min levels — is
   undefined `[@ 01:48]`.
6. **Gap-continuation entries** `[@ 02:07]` may be a separate model. One example described,
   never revisited. **Needs a second video.**
7. **He states the core cannot be taught:**
   > *"you're probably wondering, well, how do I know? … if you understand price action, then
   > you'll know. But, it's kind of hard to teach it to you unless you've been in the Discord
   > watching me trade every day."* `[@ 04:42]`

   Three components (order-block ID, stop variant, trailing) rest on that judgement.

## Backtest / forward-test notes

**Not yet tested.**

**Blocker on faithful testing: this repo holds no ES data.** Conditions 3 and 4 both live on
ES `[@ 05:47, 07:40, 09:14]`. An NQ-only reconstruction tests a strictly weaker model than
the one taught and must be labelled as such.

Testable-as-stated: the sweep (1), the structure shift on NQ (3, partial), the FVG entry,
the swing stop, the 2R target. Not testable as stated: order block identification, the stop
variant, trailing.

---

## Revision log

**2026-08-05a** — card created from `1cMWnAxElA0`. Setup reconstructed from worked examples;
no stated checklist existed in that video.

**2026-08-05b** — revised from `pD5l_gEje9I`. Changes:
- Setup replaced with his own **numbered 6-step checklist** `[pD5l_gEje9I @ 00:00–01:00]`;
  the video-1 reconstruction retained beneath it and is consistent.
- Added **SMT divergence** as explicitly optional confluence `[@ 01:46]`.
- Added the **invalidation high/low** level `[@ 01:24, 06:18]`.
- Added the **mitigation vs breaker block** naming rule `[@ 00:42]`.
- **Macro contradiction promoted to top open question** — the two videos state opposite
  requirements.
- Performance section now records a **disclosed live shortfall** (2R walkthrough → 1R live)
  `[@ 04:46, 08:30]`, which runs against his own interest and partially offsets the
  channel-level highlight-reel critique.
- Sweep timeframe conflict logged (15-min vs 5-or-15-min).

**2026-08-05c** — revised from `UBIHB1oB784`. Changes:
- **Open question 3 RESOLVED**: "aligned bias" = multi-timeframe imbalance alignment across
  4H/1H/15m/5m `[@ 01:07]`. Residual: how many must align.
- Mitigation-vs-breaker rule **confirmed in application** `[@ 01:07]`.
- Break-even at 50% now confirmed in **all three** videos — the card's most consistent rule.
  The NY-open-low variant reclassified as a one-off.
- Target section rewritten: the draw sets the target, R is the consequence `[@ 01:29]`.
- Stop section: he gives a **confluence justification** for placement, not just "recent
  swing" `[@ 01:58]`.
- Trailing reframed as *documentation of what he says, not what he does* — he states his own
  rule would have lost this trade `[@ 07:40]`.
- Macro dispute now **2–1 toward required** on behaviour `[@ 00:00, 00:23]`, still formally
  unresolved.
- New terms logged to glossary: *breakaway gap* `[@ 04:53]`, *draw on liquidity*.

**Still uncarded:** ~47 further videos enumerated but not pulled — overwhelmingly P&L posts
and vlogs rather than tutorials. Next highest-value targets if the team wants more:
`bnVKxbOokBQ` (Silver Bullet breakdown) and `01xGCvuY3p8` (trade management / break-even /
trailing — likely to resolve Contradiction #5).

---

**2026-08-05d** — revised from `qngA8aIfV0M`, `01xGCvuY3p8`, `N1EXytfVsiI`, `Ee_tC5P-F20`.
Full detail in `research/transcripts/ash10hazard/EXTRACTION-B-macros-management.md`.

**Both major contradictions resolved:**
- **#1 macro** → **mandatory gate**, with reasoning and behavioural corroboration. Schedule
  now explicit, including a *skipped* 12:45–13:15 window. `1cMWnAxElA0 @ 01:26` superseded.
- **#4 trailing** → **structure-based**: *"you trail your stop loss to the next point where
  your trade becomes invalidated"* `[01xGCvuY3p8 @ 03:28]`. He explicitly rejects mechanical
  early break-even `[@ 03:08]`. The R-multiple ladder is superseded and IS specifiable.

**Refined:**
- **Bias** — *"straight imbalances, no PD arrays, no order blocks on the high time frame"*
  `[qngA8aIfV0M @ 04:39]`; state machine (out-of-gap → directional, swing taken → neutral)
  across daily/4H/1H/15m/5m. **Mixed bias is tradeable** — he trades 5m+15m bullish against a
  bearish 1H `[@ 06:21]`. Aggregation rule still unstated.
- **Break-even** — 50% mark **AND** an FVG printing in the trade's direction
  `[01xGCvuY3p8 @ 06:24]`. Batch A had only the 50% half.
- **Target** — *"a 1 to 2 or 1 to 3 is perfect. You wouldn't really want to look for anything
  more than that"* `[qngA8aIfV0M @ 08:35]`. Contradiction #3 resolves to a 1:2–1:3 band.
- **ES is a LEADING trigger** — entry fires on ES tapping its FVG *before* NQ taps its own
  `[qngA8aIfV0M @ 08:01]`. Deepens the ES data blocker: ES is part of the entry, not decoration.
- **Sizing** — fixed dollar risk, contracts varied to match stop distance `[Ee_tC5P-F20 @ 00:29]`.
- **London** — the same model on London macro windows; **not a separate card**
  `[Ee_tC5P-F20 @ 00:01]`. `sessions` updated to [New York, London].

**Reliability — highlight-reel characterisation formally withdrawn.** `N1EXytfVsiI` discloses
an active losing streak, attributes losses to his own rule breaks, states an anti-guarantee
(*"Anyone who's… guaranteeing you 100% win rate, that's not how it is"* `[@ 04:28]`), and
discloses losing £10k at 16 `[@ 05:19]`.

**Still unspecifiable after all seven videos:** order-block identification; bias aggregation;
the *"clear where price is drawing to"* gate. Everything else is now mechanical.
