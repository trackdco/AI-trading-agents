---
id: ash-unicorn-sb
name: "Unicorn Model / ICT Silver Bullet — his names, both used in the same video"
trader: ash10hazard
sources: [1cMWnAxElA0 @ 00:00–14:29]
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

Channel-level context: of ~50 recent videos, ~40 are P&L headlines and **one** shows a loss.
See `research/ash10hazard/channel-overview.md`.

## Contradictions / open questions

1. **Macro windows: filter or not?** Called "highest probability… time zones" `[@ 01:04]`,
   then he trades the full session anyway `[@ 01:26]`. Channel titles foreground the macros;
   this tutorial demotes them.
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
