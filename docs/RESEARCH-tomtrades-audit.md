# RESEARCH — tomtrades (@itstomtrades / @TomTradesJournal) strategy audit

Reverse-engineering of a public day-trading method into something mechanical enough to
backtest. **Nothing here is a recommendation and nothing here is validated.** It is a
faithful record of what one trader *says* he does, assembled so it can be tested against
our own data and, in all likelihood, falsified.

Status: **v2 — partial coverage.** See the coverage ledger before quoting any of it.

---

## 1. Method, and what that means for trust

Both channels were audited through the YouTube Data API for metadata and **Gemini's
server-side video ingestion** for content. Direct download was impossible: YouTube
blocks this container's IP (`429` → "Sign in to confirm you're not a bot"), and the
caption endpoint returns a CAPTCHA wall. Gemini fetches the video on Google's side, so
it bypasses the block entirely — see `scripts/setup_watch_deps.sh` for the full finding.

**Read this before trusting a number.** A model watched these videos; a human did not,
and neither did the assistant that wrote this document. Each extraction was constrained
to emit a verbatim quote plus timestamp for every claim, and anything without a quote
was dropped — but that guards against invention, not mishearing. Three consequences:

1. **Quotes may be misheard**, especially numbers ("22 to 52 minutes", "15-20 pips").
   Spot-check any figure before it becomes a parameter.
2. **Chart-only detail is weakly captured.** Entries marked `[ON-CHART ONLY]` were read
   off the screen by the model, not spoken. Treat as the softest evidence class.
3. **Extraction model varies by video** (free-tier quota forced rotation across
   `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.1-flash-lite` and others). The
   `_model` field in each note records which. A lite model's chart reading is not
   equivalent to a pro model's.

The consolidated corpus is committed as `docs/CORPUS-tomtrades-extractions.md` — every
rule there carries its verbatim quote, timestamp and source video, so any claim in this
document can be traced back. The per-video JSON notes remain in the session scratchpad.
Anything load-bearing should be re-derived against the corpus before use.

The method is encoded as a project skill at `.claude/skills/tomtrades-model/`, which
carries the parameterisation and the citation table keyed to rule IDs.

## 2. Coverage ledger

| Source | Videos | Runtime | Extracted |
|---|---|---|---|
| `@TomTradesJournal` (per-trade breakdowns) | 18 | 5h 0m | **18 / 18** |
| `@itstomtrades` main channel | 53 (excl. course) | ~15h 30m | **40 / 53** |
| `@itstomtrades` full course (single video) | 1 | 8h 30m | **0 / 13** segments |

The binding constraint is the **Gemini free tier: 20 requests/day/model**. Rotating the
model pool multiplies that, but full coverage of ~29 hours needs ~77 requests and will
not complete in one day on a free key. Enabling billing on the AI Studio key removes
this outright; the whole corpus is a few dollars of flash-tier input tokens.

**The journal channel was prioritised deliberately** — it shows *why* each trade was
taken, which is what a decision agent needs, where the main channel more often explains
what a setup *is*.

## 3. The method, as he describes it

One repeating trade. It is a **counter-trend reversal against a short-term
overextension, timed to the clock**, not a trend-following system.

His framing: *"Price is a push and a pull, it's like a pendulum... you can only be in a
certain direction for a certain amount of time until you have to swing back."* And:
*"think of price like an elastic band: the more you stretch it, the more likely you'll
have a snap back."*

He names it **CBR / CBRA — "Candle Behaviour Reversal"** (*"CBR is called a candle
behaviour reversal"*). The load-bearing idea is that an hourly candle is a container of
lower-timeframe structure — *"An hourly candle is 60 minutes of 1-minute market
structure"* — so the position **within** the hour is itself a signal.

### The sequence

1. **Context — middle-timeframe range.** A rangey condition over roughly the prior
   5–12+ hours. *"You always want to have a middle timeframe sort of rangey condition...
   over the past 5-12 plus hours."*
2. **Overextension.** The hourly candle opens and immediately drives one way on volume,
   without a meaningful pullback, pushing beyond structure into a higher-timeframe area
   of interest (1H/4H/daily AOI). *"All my trades is when the hourly candle is
   immediately pushing in one direction with high volume... overextending in one
   direction."* Best when *"beyond structure"* — prior highs/lows or all-time highs.
3. **Clock window.** The reversal is timed to minutes-into-the-hour. His stated range is
   **22–52 minutes**, preferred **30–45**, favourite **37**. *"My favourite time to take
   reversals is 37 minutes into the hour"* — reasoned as *"the second half of the hour
   and it's approaching the second half of a 15-minute candle."* One video cites 20–30
   min with a **75%** figure attached; see §7, this is not self-consistent.
4. **Correlation check.** For Gold, DXY must be moving inversely; for USDJPY, the Yen
   basket. He also watches a "Gold Spread" instrument. **Hard veto:** *"If both dollar
   and yen are moving in the same direction with high volume, I should not be taking a
   trade."*
5. **Trigger — a lower-timeframe structure shift.** Drop to 1m, then 15s/5s/1s. The
   shift is a sweep-then-break: price takes out a high and then breaks the low (or the
   mirror). He calls this a **"Type 3 shift"**. A nested version — *"a shift within a
   shift"* — is his higher-confidence variant.

   **He distinguishes a "shift" from a "change of character", and this is the single
   most mechanisable definition in the corpus.** A shift is a **W-shape swing break**; a
   change of character is a **V-shape minor break**, and he does not take it: *"if we
   were to enter here on the break, it would be a pretty big stop loss... it wouldn't
   technically be a shift, it would be more of a change of character."* Note the tell —
   the invalid pattern is identifiable by requiring an oversized stop.
6. **Entry.** On the break of the 5s/1m candle low (or high), typically after a retrace
   into the **50%** of the shift leg. *"Took the entry at the break of the candle low
   targeting that 50%."*
7. **Stop.** Beyond the local swing/wick that formed the shift, or tight above the 50%
   zone. One note gives **15–20 pips**. He trails: *"I trail my stop loss when we break
   a high in my favour."*
8. **Target — 50% of the prior impulse.** This is the single most consistent rule in the
   corpus, stated in seven of the extracted videos. *"Normally I do target 50% of the
   previous move, but sometimes I can be a pussy and target less."*
9. **Discretionary exit.** He will cut before target on fading volume: *"once we took
   out this low around here the previous 15 minute candle low I was looking for an exit,
   volume started to decrease."*

### Timeframe stack

| TF | Stated purpose |
|---|---|
| Daily / Weekly | Directional context, candle behaviour |
| 4H / 1H | Areas of interest; the overextension that gets faded |
| 30m / 15m | Candle-flip confirmation; exit reference |
| 5m / 1m | Structure shift location |
| 15s / 5s / 1s | Entry trigger — *"I mainly use the 5 second chart for fractal shifts"* |

## 4. Gold specifically

Gold (XAUUSD) is the primary instrument, with USDJPY second; DXY and a "Gold Spread"
are read as confirmation, not traded.

- Traded mostly in the **Asian session**, frequently the *second or third hour*.
- **He does not always trade Gold, and the reason is a hard regime filter.** *"For Gold,
  I'm not going to be touching Gold because it's very directional, very trendy... and I
  only trade reversals in range-bound conditions."* The method is explicitly a
  **range-regime** strategy; a trending Gold is a no-trade, not a fade. Any backtest that
  runs this on all Gold data will misrepresent it badly.
- **Sized up relative to other instruments, at lower R:R** — *"I've been sizing up a
  little bit on gold especially... going for like smaller you know around 1 1.5 risk to
  reward trades."* This is the clearest instrument-specific deviation in the corpus:
  Gold gets more size and a nearer target, not a different pattern.
- DXY inverse alignment is treated as **required** in some videos and **optional** in
  others — unresolved, and worth testing as a switchable filter.
- The journal channel carries at least six Gold-specific trade breakdowns including a
  loss (*"How I Lost $8,375 Trading Gold in 30 mins"*), which is the most useful single
  video for invalidation logic.

## 5. Filters — when he explicitly does NOT trade

These are the most directly codable rules in the corpus, and the most likely to carry
real edge, because they are the discretionary skips a naive backtest would take anyway.

| Filter | Quote |
|---|---|
| Instrument is trending, not ranging | *"very directional, very trendy... I only trade reversals in range-bound conditions"* |
| Setup absent in the prior 4–5 hours | *"If you haven't seen your setup in the past 4 to 5 hours prior to your trading time, you shouldn't be looking for a trade."* |
| Too early in the hour | *"You're more likely to be stopped out when you're taking a reversal around 15 minutes in, especially if you're around the open of the hour."* |
| Just before a 15m candle open | *"ideally I don't want to be like entering a trade just before the next 15-minute candle open"* |
| Correlations aligned rather than inverse | *"If both dollar and yen are moving in the same direction with high volume, I should not be taking a trade."* |
| Gold Spread and DXY same direction | *"You see the consolidation on Gold simply because we have Gold Spread and DXY both moving in the same direction."* |
| No clean entry model on the traded pair | *"I shouldn't be taking a trade if there's no clean entry model on the main pair... especially if it's like range-y"* |
| Pattern is a change of character, not a shift | *"it wouldn't technically be a shift, it would be more of a change of character"* |
| Low-volume, rangy instrument | *"I'm not really looking at UJ... because it's just low volume kind of shit, rangy."* |

Note the tension between "only trade range-bound conditions" and "avoid low-volume rangy
pairs" — range is required at the higher timeframe but disqualifying at the instrument
level. Worth resolving empirically rather than by reading harder.

## 6. Risk, sizing and psychology

- *"Most of your edge doesn't really come from your technical analysis, it comes from
  your risk management."*
- **1:1 RR when sized up** — *"just a nice one-to-one risk-to-reward... I'm trying to
  maximize consistency and win rate with big size."* Sizing and target are coupled.
- Second position scaled in at **40–60%** of initial; later re-entries at **25%**.
- Size down and widen the stop when the range is unclean: *"less position sizing, more
  breathing room."*
- Concentration over diversification: *"You're not really going to make more money from
  taking more trades, you're going to make more money from risking more on the one setup
  you practiced."*
- Claims to miss **30–40%** of his own setups — relevant, because a backtest takes every
  signal and will therefore not reproduce his results even if the edge is real.
- Deliberate non-management while a trade is live: *"What I tend to do is just distract
  myself, cause you've got to kind of let it play out."*

## 7. Contradictions and cautions — read before backtesting

Flagged by the extraction pass, not editorialised in:

1. **The timing window is not one number.** 22–52, 30–45, 30–37, 20–30, and "37" all
   appear across videos, with a 75% winrate attached to the 20–30 variant. These cannot
   all be the rule. Treat minute-of-hour as a **parameter to sweep**, not a constant.
2. **DXY confluence is required in some videos, optional in others.** He took a Gold
   long with DXY pushing against him and said afterwards he should have waited.
3. **Session claims conflict.** *"Especially London session, I've been trading London
   session now"* — while demonstrating the identical setup in Asia.
4. **Counter-trend at extremes.** He shorts Gold at all-time highs while acknowledging
   the trend is up.
5. **The published statistics are unverifiable.** "81% WR", "88% WR", "85% WR entry
   model", "75.0" at the 30m mark, and the P&L figures are all self-reported, on
   thumbnails engineered for clicks. Two of the 18 journal videos are losses; a channel
   is a selected sample by construction. Treat every number as a marketing claim until
   our own backtest says otherwise — this repo's own non-negotiable #2 applies.
6. **Missed-setup rate cuts both ways.** If he skips 30–40% of signals discretionarily
   and is still profitable, either the skipped ones were losers (an unmodelled filter
   carries real edge) or the edge is robust to them. Only a backtest separates these.

## 8. What is still missing for mechanisation

Each of these is currently ambiguous and must be pinned before code:

- **"Overextension" is undefined numerically.** No ATR multiple, no point distance, no
  candle-body ratio was stated. This is the single biggest gap.
- **"Range condition"** over 5–12h has no width or compression test.
- **"Area of interest"** — how a level is chosen is never mechanically specified.
- **"Type 3 shift"** needs a precise swing definition (what qualifies as the high that
  gets taken, and the low that breaks).
- **Correlation alignment** has no threshold — how inverse is inverse enough, over what
  lookback.
- **Timezone.** "Asia session" and minute-of-hour rules are meaningless until anchored;
  he is AU-based, so verify against exchange time rather than assuming.

## 9. Relevance to this repo

The shape is familiar: a deterministic context filter (range + overextension + clock
window + correlation), a mechanical trigger (structure shift), and a fixed target (50%
retracement). That maps cleanly onto the existing **Python sees, Claude judges, Python
acts** split — context and trigger are engine work, the discretionary skip is the only
part that would need a judge.

It is also, on its face, **a different instrument and session from the NQ system**. This
is a research note, not a proposal to change the strategy document. Per the repo's
non-negotiables, any actual adoption needs a written hypothesis, out-of-sample testing,
and a strategy-doc version bump.
