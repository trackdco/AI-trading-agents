---
date: 2026-08-05
status: active
tags: [london, asia, session-structure, research-sweep, youtube]
sources: ["https://www.youtube.com/@tradesharpe/videos", "https://www.youtube.com/@tradesharpe/streams", "https://www.youtube.com/@eztradesyt/videos", "https://www.youtube.com/@chart-fanatics/videos", "https://www.youtube.com/@BrandanTrades/videos"]
---

# Channel map — four traders, 1,539 videos, 1,666 hours

Catalogue-level map of four channels supplied by Angus 2026-08-05. **Transcripts
are not in yet** — YouTube rate-limited this IP mid-dive, and the queue is
grinding through a backoff (`output/transcript_pull.jsonl`). So this file is
what the *catalogues* say, which is a real finding on its own and determines
where the transcript budget goes. Nothing here is a strategy claim; those wait
for the tape.

| Channel | Subs | Videos | Hours | Shape |
|---|---:|---:|---:|---|
| [Tradesharpe](https://www.youtube.com/@tradesharpe) | 108K | **932** | **1,481** | 117 education + **815 livestreams**, 5-year archive |
| [EzTrades](https://www.youtube.com/@eztradesyt) | 29.6K | 406 | 70 | short-form mechanical strategy breakdowns |
| [Chart Fanatics](https://www.youtube.com/@chart-fanatics) | 479K | 43 | 73 | long-form live sessions with ranked traders (median 83 min) |
| [Brandan Trades](https://www.youtube.com/@BrandanTrades) | 5.88K | 158 | 42 | prop-firm journey, one named breakout strategy |

---

## 1. 🔴 The find: Tradesharpe's livestream archive

**815 livestreams, 1,448 hours, median 108 minutes, spanning five years** — from
2021 to yesterday. The `/videos` tab shows only 4 long videos; the archive lives
on `/streams`, which is why a naive channel pull misses it entirely.

Two properties make this archive unusually valuable and neither is about the
strategy:

**Every stream is date-stamped in its title.** *"🔴LIVE DAY TRADING THU 04 AUG |
GOLD NQ & DAX MOMENTUM + PRICE ACTION"*. That means each stream maps to a
specific trading day, and **his live commentary can be aligned against our own
substrate for the same session.** We can check what he called, when, against what
the tape actually did — a form of ground truth no educational video provides.

**It is real-time thinking, not retrospective narration.** He states the read
before the outcome is known. Retrospective strategy videos are curated; live
commentary is not, and it exposes the discretionary joints the rules paper over.

**Instrument evolution matters.** Oldest streams (4–5 years) are *"LIVE FOREX
TRADING AND EDUCATION"*. Mid-era (1–2 years) is *"GBPJPY & GOLD"*. Current is
*"GOLD NQ & DAX"*. **The strategy was developed on forex and migrated to
futures** — so anything we take from the older material has an instrument-transfer
question attached, and the recent GOLD/NQ/DAX era is the era that counts for us.
430 streams fall in the recent window.

---

## 2. 🔴 Three of four channels converge on the same London idea

Independently, and with different vocabularies, three of these traders point at
one thing for London: **a session-open breakout.**

| Channel | Their framing | Video |
|---|---|---|
| Tradesharpe | "Session High Breakout Strategy I Use Every Day" | `J1E4XtJvCSw` |
| Tradesharpe | "The ORB Strategy Wasn't Working… Until I Did This!" (47K views) | `W5Hxv3hL3vY` |
| Tradesharpe | "Stop Using 15 Min ORB — Use This 5min Strategy Instead!" (88K) | `UoIKVfLGXXw` |
| Brandan | "**89.5% Win Rate Backtesting NQ LONDON SESSION** With My Breakout Strategy" | `hcVhQBAGGFw` |
| Brandan | "How I Trade London Session Breakouts (Pass Accounts & Take Payouts)" | `JySO8cOWOIs` |
| EzTrades | "The ONLY London Session Strategy You Will Ever Need (**London Po3**)" | `v7tdhjW84Ho` |
| EzTrades | "Opening Range Breakout & Retest Strategy Is INSANE" | `RJXe1rF9kXM` |

Convergence is evidence of *something*, but of what is the open question, and
there are exactly two readings:

1. **A real structural effect** — the European open is a genuine liquidity event
   and a breakout of the pre-open range is the naive expression of it. Three
   traders found the same thing because it is there.
2. **Shared lineage** — ORB is the most-taught intraday idea in existence. Three
   people teaching ORB is not three independent discoveries; it may be one idea
   with three narrators.

The discriminator is not the base rate — it is **what each adds on top of the
naive breakout.** Two of the three titles say the naive version failed them
("The ORB Strategy Wasn't Working… *Until I Did This*", "*Stop* Using 15 Min
ORB"). The modification is the content. That is what the transcripts are for.

**This also connects to a standing program question.** Angus asked whether we can
find where one strategy's component pairs with another's. This is the first
concrete instance: three independent modifications to the same base trigger, which
is exactly the shape of a component library — one trigger, several candidate
confirmation layers, testable in combination rather than as three whole
strategies.

---

## 3. Where the transcript budget goes

Priority targets, chosen for session relevance and rule density, not view count.

**London (the lane):**

| Video | Len | Channel | Why |
|---|---:|---|---|
| `hcVhQBAGGFw` | 31m | Brandan | NQ + London + backtested + a stated number. The single most on-target video across all four channels. |
| `v7tdhjW84Ho` | 8m | EzTrades | "London Po3" — a named, structured model |
| `uGE_GP9-nxU` | 14m | EzTrades | full London breakdown |
| `ci24AdpcRaA` | 11m | Tradesharpe | "Almost Every London Session" + live trade, 25K views, 4mo |
| `A8KDclHRpGc` | 12m | Tradesharpe | his explicit London-session strategy |
| `J1E4XtJvCSw` | 8m | Tradesharpe | session-high breakout, daily use |
| `JySO8cOWOIs` | 16m | Brandan | London breakouts for prop payouts |
| `W5Hxv3hL3vY` `UoIKVfLGXXw` | 16m/13m | Tradesharpe | the two ORB-modification videos |

**Asia / gold** (the other open lane):
`XZryPPjpOmk` (Tradesharpe, gold day-trading), `7pA2SyCsVkg` (gold backtest),
`FQHXbi3MmpI` (scalping gold), `zieKLMBRR1c` + `A1FoFtxSq98` + `ijoJ7UrEbYo`
(EzTrades gold, one explicitly "mechanical"), `ixKpElCU3Es` (Brandan, XAUUSD).

**Method spine** (session-agnostic, needed to read the rest):
`e6TIug9jQQs` (Tradesharpe, 112m full course, 7mo — the systematic statement),
`7jCUl1Bh89Q` (43m A+ scalping course), `qdZA2tTwwDE` ("I Tested The Top 5
Strategies And THIS Was The Best" — his own comparison).

**Chart Fanatics** is not London-specific and is deliberately deprioritised for
this lane — but it is the highest-quality corpus of the four (ranked traders,
long-form, live). Two are already cached from an earlier round. `HNuRp9Z1bMs`
("World's BEST NQ Scalper Reveals His A+ Trading Strategy", 663K) and
`TvoQr6ObjnU` (341 min) are the standouts.

**Deliberately skipped:** vlogs, car content, psychology, prop-firm-promo. On
Tradesharpe that is roughly a quarter of the education tab.

---

## 4. What to be suspicious of, recorded before we look

Written now so it is a prediction rather than a rationalisation later.

- **The win rates are extraordinary and uniform.** 75%, 75–80%, 75–85%, 89.5%,
  100%. Sustained high win rates on discretionary intraday trading almost always
  mean one of: wide stop / tight target geometry (high hit rate, poor R — the
  exact way `euro-handoff` died at 78% WR and +0.02R), selective reporting, or
  a definition of "win" that includes breakeven. **The geometry question matters
  more than the hit rate and none of these titles mention R.**
- **Forex-native heritage.** Tradesharpe, EzTrades and Brandan all come from FX
  (GBPJPY, XAUUSD, NAS100/US30 CFDs). Session structure, spread, tick value and
  liquidity all differ on CME NQ. Rules do not transfer for free.
- **CFD indices are not futures.** "NAS100" and "US30" are broker CFDs.
  Behaviour near the open, and the cost stack, differ from NQ/YM.
- **Prop-firm framing skews toward hit rate.** Passing an evaluation rewards a
  smooth curve, not expectancy. That biases published strategies toward exactly
  the geometry our validation process kills.

## Method note

Catalogues pulled with `youtube_channel_videos` across both `/videos` and
`/streams` tabs — the streams tab is the one that matters on Tradesharpe and a
`/videos`-only pull would have reported 117 videos instead of 932. Full
catalogues in `research/youtube/sweeps/`. Transcript queue of 749 videos / 462
hours at `output/transcript_queue.json`, worked by
`tools/youtube-mcp/pull_queue.py` with backoff; progress in
`output/transcript_pull.jsonl`. The queue is re-runnable and skips anything
already cached, so it can be killed and resumed freely.

## Candidate leads

_None yet — deliberately._ Nothing gets a thesis until the tape says what the
rules actually are. The convergence in §2 is the thing to resolve first, and it
resolves into either one candidate with three variants or three unrelated
candidates. That distinction decides how many arms this costs, so it is worth
getting right before anything is declared.
