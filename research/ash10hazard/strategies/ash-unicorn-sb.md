---
id: ash-unicorn-sb
name: "Unicorn Model / ICT Silver Bullet — his names, both used in the same video"
trader: ash10hazard
sources: [1cMWnAxElA0 @ 00:00–14:29, pD5l_gEje9I @ 00:00–08:54]
sessions: [New York]
instruments: [NQ (traded), ES (confirmation only, not traded)]
timeframes: [HTF: 15m for sweeps/structure, entry: 1m–5m]
components: [liquidity-sweep, momentum-shift, fvg-fill, order-block-tap, multi-tf-alignment, session-timing, structure-stop, fixed-r, runner]
maturity: core
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

**Macro windows are confluence, NOT a filter.** `[stated]` — important, and the opposite of
how the channel's video titles present it:
> *"Macro entries are obviously an added confluence"* `[@ 00:45]`
> *"just trading the full session completely eliminates the fact that you missed those
> trades. And if a trade presents itself, then it's valid to take."* `[@ 01:26]`

**Directional bias** comes from which side of liquidity was swept — sweep of buy-side →
look for shorts. `[inferred]` from all four examples `[@ 05:03, 07:16, 08:50, 12:04]`; he
never states the bias rule in the abstract.

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
| 6 | **Aligned bias** | never operationalised — `[unclear — needs review]` |

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

**Target: 2R, placed at "the opposing draw on liquidity".** `[stated]`
> *"I'll look for a two R at the opposing draw on liquidity which is clear price is going to
> go and draw to hit anyway"* `[@ 06:30]`

**Break-even:** when price reaches 50% of the entry→TP range. `[stated]`
> *"we have this swing low on NQ that's 50% of the range between our entry point and TP. So,
> once price takes this point, I would be going break even."* `[@ 06:53]`

In example 3 he instead uses the **New York open low** as the break-even trigger `[@ 10:01]`
— a different rule, same video. See Contradictions.

**Trailing — stated then disowned in the same breath.** `[stated]`
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

3. **"Aligned bias" is step 6 of his own checklist but never operationalised.** The only
   elaboration is *"we have a bullish bias using imbalances"* `[pD5l_gEje9I @ 02:57]`.
   `[unclear — needs review]`
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

**Still uncarded:** `UBIHB1oB784` (transcribed, not yet read). ~47 further videos enumerated
but not pulled — mostly P&L posts rather than tutorials.
