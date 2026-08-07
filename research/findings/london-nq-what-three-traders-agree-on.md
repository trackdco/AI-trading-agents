---
date: 2026-08-05
status: active
tags: [london, session-structure, pattern-taxonomy, sizing]
sources: ["articles/2026-08-05-channel-map-four-traders.md", "articles/2026-08-05-tradesharpe-method.md", "articles/2026-08-05-orderflow-scalpers-fabio-carmine.md", "findings/london-window-LDN-WIN-01.md"]
---

# London NQ — what three traders actually agree on (and it isn't the trigger)

From the transcripts now cached. **This corrects my own earlier claim** in
`2026-08-05-channel-map-four-traders.md` §2, which said three channels converge
on a London session-open breakout. Having read the tape, that was wrong in an
instructive way.

## The correction

I inferred from titles that Tradesharpe's two ORB videos were London content.
They are not. In his own words [`W5Hxv3hL3vY` @ 2:55]:

> *"Works on NASDAQ. High volume pairs, NASDAQ, US30, S&P, gold... during the New
> York Stock Exchange open. **Don't— this doesn't really work too well in London
> open.** I have seen people use it as London open, but honestly I feel like New
> York Stock Exchange open is the best for this to work."*

So the "three-way convergence on a London breakout" does not exist. One of the
three explicitly says the setup fails in our session. Recording that rather than
quietly dropping it, because the inference was mine and it was wrong — titles
are not tape, which is the entire reason for pulling transcripts.

**What is left is a genuine two-source London claim** (Brandan and EzTrades),
plus something considerably more useful that all three do agree on.

## What they actually agree on: the geometry, not the trigger

Read across the three, the common ground is not *what to trade*. It is **where
the stop goes** — and all three arrive at the same answer from different
directions.

**Tradesharpe**, critiquing standard ORB [`W5Hxv3hL3vY` @ 2:10]:

> *"if you were to backtest it, it would have like a **50% win rate** just
> randomly entering on 15-minute candle closes targeting one to one. The issue is
> **stop loss is not optimized. Entry is not optimized**."*
> *"some people run stops below the range, which if you know anything about opens,
> they are massive. **You are wasting so much profitability by running stops below
> that whole open candle.**"*

His fix is not a different trigger. It is to drop to a lower timeframe for the
entry and put the stop **at the trigger candle** instead of beyond the whole
opening range. Same trigger, tighter geometry.

**Brandan**, stating his London spec outright [`hcVhQBAGGFw` @ 1:53–3:11]:

> *"London session. Looking at **MNQ only**... **Stop loss is usually around 10 to
> 15 pips. Predominantly 10.** Some days even lower... And we're **exiting at one
> to twos**."*
> *"**8:00 a.m. UK time.** So wherever you are in the world, convert your time to
> 8:00 a.m. UK time. So marking up **five minutes before**."*

A ~10-point stop on NQ with a 2R target. He does not derive it; he just runs it.

**Fabio**, from the earlier round, on the A+ setup [`xUyqIjCfZzg` @ 45:09]:

> *"That's an A+ perfect setup **and really low risk**." — "Very low risk."*

Three traders, three vocabularies, one shared property: **the stop is at the
trigger, not beyond the structure.**

### Why this is the finding rather than a detail

This is the exact axis our own programme has already died on. `nypre-euro-handoff`
reached **78% win rate and paid +0.02R** — tombstoned as *"the handoff is a fact,
not a trade — its natural geometry cannot pay per unit risk"*, because the
pattern's natural stop was the far side of a wide two-session range.

Tradesharpe is describing that same failure from the outside and naming the fix:
*you are wasting so much profitability by running stops below that whole open
candle.* Independent arrival at our own tombstone.

So the transferable component from this round is **not a setup. It is a stop
rule**: trigger-candle stop rather than structural-range stop, applied to
triggers we already have. That is testable against existing substrate without a
new entry model, and it is cheap in arms because it modifies geometry on
candidates rather than adding candidates.

## Where they disagree, and it matters

| | Tradesharpe | Brandan |
|---|---|---|
| London ORB | *"doesn't really work too well in London open"* | his entire London edge |
| Session anchor | 1h before → 1h after the open (~02:00–05:00 ET) | **08:00 UK sharp**, marked from 07:55 |
| Confirmation | **wait for the candle to close** beyond the range | *"if this comes up a buyers, **I'm in immediately**"* |
| Stop | at the trigger candle / structure / wicks | **fixed ~10 pts**, occasionally 5 |
| Target | next structural level, often 1:1 | fixed **1:2** |

The confirmation row is the sharpest disagreement and the most testable: one
waits for a close, the other enters on touch. That is a single binary variable
over the same trigger — a clean A/B, not two strategies.

**Brandan's 08:00 UK anchor lands on our measured 03:00 ET peak**
(`london-window-LDN-WIN-01.md`), which is at least consistent: 08:00 UK is
03:00 ET, the volume peak in both eras. His "mark up five minutes before"
(07:55 UK / 02:55 ET) is the bucket immediately preceding it.

## 🔴 The headline number does not survive its own video

`hcVhQBAGGFw` is titled *"89.5% Win Rate Backtesting NQ LONDON SESSION"*. Inside
the same video [@ 6:00]:

> *"if we know there's a **60 to 70% win rate**, we should essentially see us pass
> at least five accounts."*

His own working assumption is 60–70%, not 89.5%. And in the December backtest
[`1noM1ogc5zM` @ 16:28], on a trade he had logged as a loss:

> *"That's a losing trade. **Realistically, break even.** I mean, realistically,
> nearly hit our take profit. So realistically, we're—"*

Losses being re-scored as "realistically break even" is precisely the failure
mode logged as a prediction in `channel-map-four-traders.md` §4 *before* any of
this was read: *"a definition of 'win' that includes breakeven."* It is recorded
as a confirmed prediction, not a discovery.

Two further honesty markers on the same source:

- **The strategy is session-specific in his own experience.** Same method, London
  winning while *"for New York, I'm on my worst losing streak of all time"*
  [`hcVhQBAGGFw` @ 0:51]. Good for us — we only want London — but it also means
  his sample is one session in one favourable stretch.
- **Heavy affiliate incentive.** Prop-firm discount codes throughout, *"I'm going
  to be buying 10 Apex accounts"*. Commercial reason to overstate.

**None of this means the setup is worthless.** It means the 89.5% is marketing,
60–70% is his own estimate, and the number that decides it is **R, which he never
quotes**. A 10-point stop at 2R on NQ needs ~35% to break even before costs. That
is the actual bar, and it is a very different conversation from 89.5%.

## 🔴 Second correction: Tradesharpe's London edge is not on Nasdaq

His explicit London-session video landed after the above was written
[`A8KDclHRpGc` @ 2:40]:

> *"during London session you do want to trade a pair that is going to have the
> majority of the volume brought into London session, and in this case it's going
> to be **pairs with GBP**, euro is also fine — but **anything where we're using
> USD, anything where we're having something like gold and stuff like that and
> US30, NASDAQ indices, this is where you might see some inconsistencies and
> where it might be seasonal**."*

> *"hedge funds and major funds normally rebalance portfolios and they go hard in
> **February, March, April**, so even in London session we do see better moves on
> those compared to later in the year — whereas New York there's a consistent
> volume."*

He is a London specialist who trades **GBPJPY** in London, and he actively warns
that **Nasdaq in the London session is inconsistent and seasonal**. Two of his
three relevant claims now point away from NQ-in-London: the ORB material is New
York, and the index instruments are cautioned against outright.

**Timeline nuance, and it matters.** That video is ~2 years old. His current
livestreams are titled *"GOLD NQ & DAX"* — so he has since moved onto exactly the
instruments he cautioned about. Either he changed his mind, or the caution still
stands and the recent streams are a different (worse) business. **The 815-stream
archive can answer that**, and it is the strongest argument yet for mining the
recent era rather than the courses.

**And the caution is itself a censusable claim.** "Nasdaq in London is seasonal,
better in Feb–Apr" is directly testable on our substrate — 912 days, 2023→2026,
London-window range and efficiency by month. That is a cheap measurement that
either kills the concern or turns it into a regime filter we would want anyway.
Not run: it needs its own prereg and Angus should see the changed picture first.

## The swing vote landed — EzTrades' London Po3, fully specified but instrument-silent

[`uGE_GP9-nxU`] states a complete, time-anchored model in **Eastern time**,
which maps straight onto our substrate:

| Component | Rule |
|---|---|
| **Accumulation** | a range forms roughly **01:00–02:00 ET** — *"a lot of times London just accumulates, which is why the strategy works"* |
| **Manipulation** | the sweep of that range at **~03:00 ET** — *"you are only trading the 3:00 a.m. manipulation"*; *"most of the time you will see manipulation in that 3:00 a.m."*, sometimes 02:30, usually 03:00–04:00 |
| **Entry trigger** | **inverse fair value gap (IFVG) on a 1–3 minute chart**, *"ideally a V-shaped inverse within a few candles"* |
| **Direction** | catch the distribution leg after the manipulation |

**Third independent source pointing at 03:00 ET.** Brandan's 08:00 UK is 03:00
ET; EzTrades' "3:00 a.m. manipulation" is 03:00 ET; LDN-WIN-01 measured 03:00 ET
as the volume peak in both eras. Three sources and one measurement on the same
clock is the strongest agreement in this round.

**But the instrument is unresolved, and that was the whole point of this video.**
The transcript never names one — no "nasdaq", no "NQ", no "gold", no "futures".
He shows it on the chart, and captions do not carry chart content. Attempts to
pull the description for a hint hit the bot-check on every client.

So the swing vote is **still open**. It has to be settled visually or from his
other London video (`v7tdhjW84Ho`, queued), not from this transcript. Recording
the limitation rather than assuming NQ because it would be convenient.

**Worth noting what this model is.** PO3 + IFVG is ICT vocabulary. The
accumulation-manipulation-distribution frame is the same object as the
`london-asia-sweep-reversal` thesis the programme already greenlit — a sweep of
an overnight range that fails and reverses. The novel parts here are the tight
clock (03:00) and the IFVG entry trigger, not the mechanism.

### Where this leaves the sources

| Source | London? | NQ? | Net |
|---|---|---|---|
| Brandan | yes | **yes — MNQ explicitly** | the only genuinely NQ-London source |
| EzTrades | yes ("London Po3") | unknown, gold-heavy channel | **still queued — now the swing vote** |
| Tradesharpe | yes, deeply | **no — GBP pairs; cautions against indices** | method transfer only, not the instrument |
| Fabio / Chart Fanatics | no (NY open) | yes | geometry principle only |

The two-source London claim is now closer to **one-and-a-half**. EzTrades'
London videos matter more than they did an hour ago.

## What I would take forward

1. **The trigger-candle stop rule as a component**, testable against triggers we
   already own. This is the cross-strategy transfer and it costs no new entry
   model.
2. **Brandan's London spec as a candidate**, because it is fully specified —
   instrument (MNQ/NQ), clock (08:00 UK), prep window (07:55), stop (~10 pts),
   target (2R) — and it sits on our measured 03:00 ET peak. The discretionary
   joint is level marking, same as Tradesharpe's.
3. **The close-vs-touch confirmation A/B**, which is one binary variable across
   both sources rather than a new search.

## What I would not take forward

- Tradesharpe's ORB material for London. He says it belongs to the NY open and
  that is the other chat's lane.
- Any published win rate from this round, as a number. They are titles.

## Status

Transcripts still landing (57 of 725 cached; the yt-dlp path unblocked the
throttle). EzTrades' two London videos and Tradesharpe's explicit London-session
videos are still queued — both could move the two-source claim in either
direction, so nothing here is filed as a thesis yet.
