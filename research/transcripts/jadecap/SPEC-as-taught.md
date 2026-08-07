---
date: 2026-08-05
kind: as-taught spec sheet (agent, verbatim)
---

All 16 transcript files read in full. Two videos named in the task — tFKOaF4HMcg ("My Updated Trading Strategy (2026)") and Wqzz0sklMMA ("The 3-Step A+ ICT Strategy") — are listed in CATALOG.txt but have **no transcript files** in `/home/user/AI-trading-agents/research/transcripts/jadecap/`; only 16 of the 25 cataloged IDs have `.md`/`.vtt` files. Everything below is extracted from the files that exist. Timestamps are `[MM:SS]` from the `.md` transcripts (30-second blocks; `.en.vtt` files exist for finer resolution).

---

# JADECAP (Kyle) — AS-TAUGHT SPEC SHEET

Channel-wide context: ICT-derived intraday futures trader, primarily NQ (Nasdaq futures), also ES, gold, FX. Claims $2.5M single payout at Apex ("world record"), $4M+ over 3–4 years, 14 years trading, profitable only in the last ~5. All times **Eastern**.

---

## MODEL 1 — THE DAILY SWEEP (flagship)
Sources: dcIcXbzMcc4, gGiE3rx2wdg, nuYlnDwgEgg, DQiOqFFptfA (he explicitly names the 5-minute video's strategy "the daily sweep strategy" at DQiOqFFptfA [06:05]), wZ4ea0VJnrw (same model, "the only strategy I'd keep"), HaDJ16Q5W10 + LEBDs5WrUbE (the SFP engine in isolation).

### 1. Name + thesis
Daily Sweep = hourly swing-point liquidity raid + Swing Failure Pattern (SFP) confirmation + lower-timeframe entry. Who's trapped: "This one single candle tells us that anybody that chased short off the open is now stuck in a losing position" (wZ4ea0VJnrw [03:35]). LEBDs5WrUbE [06:35–07:35] enumerates the three trapped/paid parties: longs stopped out (sell stops), breakout shorts trapped (sell stops), buy-limit holders in profit — "because they took out all of these orders... the order book dries up below the market, and now this new swing low should be protected." You're paid by riding the reversal after stops are consumed: "We're not trying to be the first person entering into a market... I would rather catch the meat of a move" (dcIcXbzMcc4 [06:38]).

### 2. Entry mechanism, exact, as taught

**Step 0 — Daily bias (mandatory context).** From the D1 candle: "Sunday night I sat down and looked at where the daily candle closed on Friday. Now, this daily candle closed above the previous day's candle. So, what I'm looking for is bullishness" (nuYlnDwgEgg [15:10]). His own Discord-posted model card (nuYlnDwgEgg [19:17]): "Step one, determine daily bias based on D1 time frame. Plot all swing points from the previous day at session start... Wait for a swing failure pattern. Lower time frame execution starting the following hour (fair value gap, inverted fair value gap, order block, change in state of delivery). Target fixed one or two R... if bullish, we are waiting for a swing low raid or failure pattern. **No raid, no trade.**"

**Step 1 — Mark levels.** At 8:00–8:30 a.m. ET, on the **1-hour chart only**, mark all prior-day hourly swing points up to now (including Asia + London): "at 8:00 a.m. I'll sit down at my desk and I'll mark out all of the previous hourly swing points from the previous day leading up until 7:00 or 8:00 a.m." (dcIcXbzMcc4 [00:30]); "Not the 15-minute, not the daily, the 1-hour chart" [01:00]. Only untapped levels: "We are only marking swing points that haven't yet been traded to" (gGiE3rx2wdg [01:00]). If price is beyond yesterday's range, "use the next most recent day" (dcIcXbzMcc4 [00:30]) — go back 2–3 days if needed [03:03]. Takes 5–10 min per market.
- **Swing point definition (exact):** "a swing low is a candle where both the candle before it and after it have higher lows... a swing high is a candle where both the candle before it and after it have lower highs" (dcIcXbzMcc4 [01:00–01:32]). 3-candle fractal; confirmed **only on close of the third candle**: "swing points aren't yet confirmed until the third candle closes" (HaDJ16Q5W10 [02:03]).
- If bias is bullish, mark only opposing swing LOWS; bearish → swing HIGHS (wZ4ea0VJnrw [00:00–00:30]).

**Step 2 — The sweep + confirmation (the SFP).** Definition: "when price briefly breaks a significant swing high or low, but quickly reverses, failing to sustain the move and closing back within the previous range" (dcIcXbzMcc4 [03:34–04:05]). Confirmation is a **1H candle CLOSE back inside the range** — nothing else: "if the candle just trades up and then it trades back down, but it hasn't yet closed, that is not confirmation yet. What we're looking for is a candle closure" (gGiE3rx2wdg [03:34]). No minimum penetration depth is specified; any trade beyond the level counts as the raid.
- Strength grading: "If we raid out a high and then this candle closes all the way down here or bearish, that is much stronger" (dcIcXbzMcc4 [04:35]); "a bullish candle after taking out lows is much better than a bearish candle after taking out lows" (HaDJ16Q5W10 [08:09]); "The stronger the candle, the better. If this actually closed bullish, it would be a much stronger signal to go long" (mKdLG088-9U [14:41]). If SFP candle closes the "wrong" color he waits one more hourly candle (gGiE3rx2wdg [05:07–05:37]).
- Expectancy after confirmation: "we can anticipate at least two to three hourly candles trading the opposite direction" (dcIcXbzMcc4 [12:12]); "position ourselves for maybe the next two, three, or even four hours" (HaDJ16Q5W10 [07:08]).

**Step 3 — Lower-timeframe entry.** Only after a confirmed 1H SFP may you open a lower timeframe: "until I get this closure, I do not look at any of these lower time frames" (gGiE3rx2wdg [04:05]). Entry window = "starting the following hour" (nuYlnDwgEgg [19:17]). Entry models (his list, nuYlnDwgEgg [06:03–06:35]): "I focus on three main entry models. Fair value gaps, inverted fair value gaps, and order blocks" — plus breaker and change-in-state-of-delivery in examples; he explicitly says the entry model is interchangeable ("VWAP, moving averages, volume profiles, whatever" — because "the context and narrative... is already in place," nuYlnDwgEgg [06:35]).
- Canonical execution: 5-minute FVG. "Plot along... into the 5-minute fair value gap, put our stop loss below candle two of the fair value gap... target two to one" (wZ4ea0VJnrw [05:37]). DQiOqFFptfA [10:09]: "our entry goes at the midpoint of the fair value gap"; also enters on "a nice closure... through 50% of that candle of this fair value gap" (nuYlnDwgEgg [10:37]).

**Timeframes:** HTF = 1H (his fixed choice for this model; wZ4ea0VJnrw [00:30] says any HTF/LTF pair works). LTF = 5m default (1m/15m allowed, dcIcXbzMcc4 [07:40]).

**Session window and instruments:** NQ primarily. Trade only around NY equity open and PM session: "We're waiting for equity open because that's when NASDAQ is the most active" (nuYlnDwgEgg [16:41]); "I would not anticipate trading during London session if I'm going to trade NASDAQ" [08:35]; "we're not trading this one because it's 7:00 a.m. If you try and trade these setups off hours, your data is going to be very poor" [09:36]; "time is more important than price" [17:13]. AM window ≈ 9:30–11:30/12:00; "the PM session, which for me is about 1:00 p.m. till about 4:00 p.m." (gGiE3rx2wdg [10:40]). Avoid pre-9:30 SFPs (wZ4ea0VJnrw [02:34–03:04]); avoid days with data gaps (skipped Black Friday, dcIcXbzMcc4 [08:40]).

### 3. Stop as taught
Hierarchy, all quoted:
- Default: "stop loss below candle two of the fair value gap" (wZ4ea0VJnrw [05:37]; DQiOqFFptfA [10:40] "stop placed at candle two"; mKdLG088-9U [17:12]).
- OB/breaker entry: "we're going to put our stop above the breaker" (gGiE3rx2wdg [06:07]).
- Choppy conditions / PM session: widen to the hourly level: "use a higher time frame level like a 1 hour high or low as my stop loss, but still use a lower time frame for my entry" (gGiE3rx2wdg [10:40–11:11]).
- HTF fallback: "the candle that created the swing failure is a good place to have a higher time frame stop loss" (HaDJ16Q5W10 [09:10]) — i.e., below/above the SFP candle's extreme.
- Principle: stop goes "based on where your analysis should be wrong... For a bullish trade, your stop goes below the liquidity sweep and below the low that was just created" (1DsNwrQuLaE [12:44–13:15]).

### 4. Targets as taught
- "Target fixed one or two R" (Discord card, nuYlnDwgEgg [19:17]); "a fixed 1:2 or 1:3 risk-to-reward" (nuYlnDwgEgg [08:05]); examples run at 2R and 3R.
- Or opposing liquidity: "targeting a fixed 1:3 RR or the buy-side liquidity" (DQiOqFFptfA [10:40]); "I'm just targeting the most recent swing high because... I know that there are pending orders above swing highs and swing lows" (LEBDs5WrUbE [14:10]).
- **Time exits are mandatory:** "You either have a fixed target or you should have a time exit... leading up to lunch, you should be taking some risk off of the table. Whether that's taking a partial or adjusting your stop-loss... a mechanical decision that you should make leading up to 11:00 a.m. and 12 p.m." (gGiE3rx2wdg [07:37]). Partials: 50% off at first target, rest to second target; move stop to BE late in day (1DsNwrQuLaE [14:17–15:20]).
- Prop-firm overnight workaround: close before the 4–5 p.m. cutoff, re-enter at the 6 p.m. rollover at same price/risk (wZ4ea0VJnrw [08:38–09:09]).

### 5. Mandatory context
D1 direction (candle-over-candle closes, market structure) sets which side you hunt; only counter-sweeps in the bias direction are tradeable ("if bullish... waiting for a swing low raid... No raid, no trade"). Session timing filter as above. One-sided rule: "if the market is showing strength, I want to stay on side until the higher time frame is telling me to go in the opposite direction" (wZ4ea0VJnrw [07:07]). Premium/discount appears only as optional refinement in this model (HaDJ16Q5W10 [08:40]: "wait for price to enter a discount before we try and start hunting longs").

### 6. Discretion gaps (literal readings enumerated)
1. **"Significant"/"major" swing points** — no size filter given. Literal readings: (a) every 3-candle fractal on 1H; (b) only fractals untapped since formation; (c) only "obvious" ones (his charts skip minor ones). (b) is the only stated rule.
2. **SFP close quality** — "closure back into the range" vs "strong closure" vs "nice closure". Readings: (a) any close back inside; (b) close must be opposite color; (c) close beyond some fraction of the raiding candle's range; (d) wait one more candle if wrong color (he does this once). Never quantified.
3. **Bias derivation** — "D1 time frame" is the rule but demos also use: prior day's candle color, hourly structure, inverted FVG on H1, "let's say we're bullish." Readings: (a) yesterday's close vs prior close; (b) daily swing structure HH/HL; (c) discretionary synthesis.
4. **Which entry model on the LTF** — explicitly trader's choice ("every single trader... is going to have a different stop-loss and a different target and a different entry," gGiE3rx2wdg [06:37]).
5. **Entry price within FVG** — touch, midpoint, 50% close-through, or "closure above a down-close candle" (CISD) all demonstrated.
6. **Pre-market trades** — rule says wait for 9:30, but he personally entered 7:19 a.m. and calls an 8 a.m. entry "close enough for me... a little sketchy" (nuYlnDwgEgg [17:44]). Readings: (a) hard 9:30 gate; (b) 8:00+ allowed with HTF alignment.
7. **"Choppy" regime detection** (triggers hourly-stop mode) — undefined; purely visual.
8. **Marking time** — 8 a.m. same day (dcIcXbzMcc4) vs 5–6 p.m. prior evening (nuYlnDwgEgg [03:01]) vs 7–9 p.m. prior evening (1DsNwrQuLaE [02:35]). Functionally equivalent but not identical level sets (overnight session included or not at mark time).

### 7. Data needs
1H + 5m (and 1m optional) OHLC for NQ/ES with ET timestamps; D1 series for bias; prior 1–3 day lookback; session calendar (9:30 open, 4–5 p.m. futures close, 6 p.m. rollover); holiday/half-day flags (skip gap days); economic calendar (he closed a trade before 10 a.m. news, LEBDs5WrUbE [14:41]).

### 8. Implied frequency
Setup "happens nearly every single day" (dcIcXbzMcc4 [12:42]; HaDJ16Q5W10 [14:15]). Max 1–2 attempts/day: "You're going to take one or two attempts per day. If trade one is a loser, trade number two, use half of the risk. That way, your max daily loss is only negative 1 and a half R" (nuYlnDwgEgg [08:05]); "I'll give myself one more attempt in the PM session... If I lose during the PM session again, I will stop for the day" (gGiE3rx2wdg [10:09–10:40]). M8IiEAlUEDw: 3–5 trades/week, "structure your week around two or three high conviction trades" [12:08, 14:39].

### 9. Stats he quotes
- "My win rate jumped from 35% to over 50% literally overnight" after adding the SFP filter (nuYlnDwgEgg [03:32]).
- SFP hit rate: "We don't have a 100% hit rate on these patterns, but they are very, very high. I would say they're over 60%" (HaDJ16Q5W10 [11:13]).
- Directional guess quality: "maybe 60 to 70% of the time that we're getting this correct" (dcIcXbzMcc4 [02:32]).
- "A strategy that works 40 to 50% of the time is enough to make you rich" (DQiOqFFptfA [05:03]).
- Trade examples cited: 2R, 3R, 5R outcomes.

---

## MODEL 2 — SESSION-LIQUIDITY SWEEP + FVG ("Liquidity + Fair Value Gap = Profit")
Source: YxVU_Pm_1Jw. Same skeleton as Model 1 but the swept level is a **session extreme**, and the entry is a **limit order at the FVG**.

1. **Thesis:** price "is being delivered from one session's liquidity pool to the next" [02:03]; be counterparty to stops resting beyond Asian/London/NY-AM extremes. Claim: "all I used to do was liquidity and fair value gaps... over $4 million from prop firms over the past four years" [00:00].
2. **Entry:** (a) Bias from HTF (prior day / HTF order flow). (b) Mark session ranges — **exact defs [01:01]: Asia 8:00 p.m.–12:00 a.m. ET; London 2:00 a.m.–5:00 a.m. ET; New York 8:00 a.m.–12:00 p.m. ET ("when you're trading index markets... your New York range might be from 9:30 to 12:00")**. (c) If bullish, wait for a raid of the Asian or London LOW after 9:30 (index) / 8:00 (FX); (d) "wait for a closure back above the low. Now, if we take out the low and it doesn't close back above in a significant manner, then we just avoid the trade entirely" [10:39–11:09]; (e) wait for an FVG to form (= his displacement proxy): "we're looking for that displacement. If we don't get a bearish fair value gap that appears after raiding the London high and then breaking down, then we just wait" [14:46]; FVG must appear **inside the trading window** [15:16–16:17]; (f) "enter using a limit order at the fair value gap" [10:39] — leave the resting limit even if fill comes at lunch [13:44–14:15].
3. **Stop:** "below either candle 1 or candle 2's low" of the FVG (bullish) / above candle 1 or 2's high (bearish) [11:09, 13:13].
4. **Targets:** "target opposing session liquidity" — Asian range high, prior NY high, London low, previous-day liquidity [10:09–11:40]. Worked examples: 3.5R, 2.5R, 3R, 4.5R, 4.38R, 6R.
5. **Context:** step 1 is non-negotiable: "establish context and directional bias. Without that, you're basically trading blind" [09:39]. Premium/discount + "which session is delivering the move" (AMD phases) [08:08–08:38]. In HTF uptrend, only hunt low-sweeps [08:38].
6. **Discretion gaps:** "significant" closure undefined (readings: any close back inside / strong-bodied close); which of candle-1 vs candle-2 bounds the stop; target selection among multiple pools; bias derivation; whether a late-lunch fill is still taken (he says yes if order was resting).
7. **Data:** 5m/15m + 1H OHLC, ET session bucketing (his exact windows), FX vs index open handling.
8. **Frequency:** roughly daily candidate; same 1–2/day cap implied.
9. **Stats:** "when I've traded outside of those trading hours, I've typically done pretty poorly" [15:46] (his own journal, unquantified). RR examples above.

---

## MODEL 3 — 3-STEP ICT / PREVIOUS-DAY LEVELS + PREMIUM ENTRY
Source: 9QAk84wnL3c. (Companion Wqzz0sklMMA transcript missing.)

1. **Thesis:** fade the manipulation leg into premium near the prior-day extreme, in the direction of the daily bias; paid by continuation to the prior-day opposite extreme.
2. **Entry:** Mark previous daily high/low over "midnight Eastern to midnight Eastern" [00:31–01:02] plus intraday FVGs / inverted FVGs (order blocks and fib optional: "you can get away with using only fair value gaps" [01:02]). Bearish bias example: expect market "to slowly trade higher... into this fair value gap right at the open... hopefully not taking out the previous day's high" [04:07–04:37]; the retrace must arrive **during your window** ("this market up here needs to align with the time that I'm trying to trade" [03:05]; news events noted); trigger = "traded up into this fair value gap and it's given us a bearish engulfing candle... I'm actually waiting for the close here... right at 10:00 a.m." [05:39]; enter short at next candle open.
3. **Stop:** not stated numerically in this video ("logical area"); example implies above the FVG/engulfing high.
4. **Target:** "just targeting the previous day's low" [05:39–06:10]; example ≈ 2.4:1. Manage across the 5–6 p.m. rollover by close-and-reopen [06:40].
5. **Context:** prior-day candle direction + market structure break; skip entirely if price expands away without retracing into your premium level: "the market just drops without me... I don't take any trades" [07:41–08:11].
6. **Discretion gaps:** which FVG (multiple marked); engulfing vs any rejection close; "premium" not fib-quantified here; news handling ("maybe they're going to manipulate the market higher" — wait) is judgment.
7. **Data:** 1H (+ D1, 4H for analysis), midnight-anchored daily H/L, news calendar.
8. **Frequency:** ≤1/day; many no-trade days by construction.
9. **Stats:** none beyond the 2.4R example.

---

## MODEL 4 — DAILY-OPEN EXPANSION ("boring but profitable ICT")
Source: 4Ici-sAt30w.

1. **Thesis:** on a day you expect to close directional, the best fills are at/through the daily open; buy the manipulation below the open. "On a bullish day, my goal is to buy it as close as possible or below the opening price" [04:34].
2. **Entry:** (a) Direction: market structure (HH/HL vs LL/LH) **and** FVG order-flow test: "if bullish fair value gaps are being respected and bearish fair value gaps are being violated... order flow is currently bullish" [03:04]; "if market structure and order flow are unclear, then we have no real direction and no trades" [03:34–04:04]. (b) Entry: "We're looking for a sweep of liquidity. That might be an intraday high or low, session high or low, or previous day high or low. And then we're just going to enter on a fair value gap with the expectation that the daily candle is going to close higher" [06:37–07:07]. Anchor = midnight-open daily open [07:07]. (c) Veto: "if I sit down in front of the charts and the candle has already expanded, I typically will not take a trade" [06:07]; entry anywhere at/below the open qualifies [08:08].
3. **Stop:** not specified here (video is direction/location-focused); implied below sweep low.
4. **Target:** hold toward the daily close in bias direction; prior-day high implied as objective.
5. **Context:** the whole model IS context (structure + FVG order flow + open anchor).
6. **Discretion gaps:** "already expanded" threshold undefined (readings: any distance above open / beyond some fraction of ADR); which liquidity pool must be swept; exit timing into close.
7. **Data:** D1 + intraday with midnight-ET opens; session H/L; NFP/FOMC calendar (his examples straddle news).
8. **Frequency:** ≤1/day on clear-bias days.
9. **Stats:** none quoted beyond the $2.5M claim.

---

## MODEL 5 — ENGULFING BAR (market-maker-model compression)
Source: P4jxZwNZP9g.

1. **Thesis:** a 2-candle HTF engulfing at a liquidity extreme compresses a full market-maker buy/sell model (liquidity raid → smart-money reversal → market structure shift) into one signal [03:34–04:04].
2. **Entry:** Definition (exact): second candle "needs to take out the previous candle's low as well as the previous candle's high" [01:01–01:31] and close strong: "we're looking for a large body to close... towards the upper half, upper 50% of a specific candle" [04:34] — bullish version: sweep prior low first, then close above prior high. **Wait for the close** [09:40–10:11]. Location filter (mandatory): "avoid bullish engulfing bars that appear after taking out buy side liquidity" (exhaustion); want them "at a swing low after taking out sell-side liquidity" [07:39–08:39]. Timeframes: taught on 4H/daily; live trade keyed off a 4H candle [12:48]. Entry at close (he entered at the 6:00 p.m. futures reopen) or on retracement.
3. **Stop:** "my stop loss is at the weekly open because I don't anticipate this market trading lower down to this wick" [10:11] — i.e., a structural level the thesis says shouldn't trade; trail as it moves [13:49].
4. **Target:** first target = opposing buy-side liquidity; extended to "25,000 whole number as a psychological level" at all-time highs; "aiming for about a 1 to three risk-reward" [09:40–10:11].
5. **Context:** HTF trend + located inside a daily FVG + post-catalyst (FOMC) in his live example [09:09].
6. **Discretion gaps:** "strong closure" fraction; wick-take vs body-take of prior high/low; stop anchor choice (weekly open vs swept low); scaling/trailing entirely discretionary.
7. **Data:** 4H/D1 OHLC, weekly opens, liquidity map, news calendar.
8. **Frequency:** low — a few per month on 4H/D1.
9. **Stats:** "you might find out that 60% of the time these trade patterns do work" [06:37]; the showcased trade: 20 lots, +$98K in under 12 hours, live account shown floating +$93K.

---

## PROP-EVALUATION PROTOCOL (mechanical, separate)
Source: v2Epolr4olM. Firm: Apex.

**Account selection:** 25K = 4 minis/40 micros, target $1,500, trailing drawdown $1,000, passable in 1 day; 100K = $3,000 DD / $6,000 target; 150K = $4,000 DD / $9,000 target (what he used on the record run); "a really good sweet spot is the 50Ks" [02:02–02:33]. End-of-day trailing recalculates at close only (has daily loss limits that pause, not fail); intraday trailing counts unrealized peaks ("up $250... stops you out at break even, it will negatively impact your drawdown by $250" [04:03]) → forces early partials/aggressive stop management. Trailing locks once profit ≥ initial DD (100K locks at $103,000) — "take it slow when you get funded, get the trailing drawdown to stop" [08:06–08:37].

**Sizing rule (exact):** risk per trade = max drawdown ÷ 20. "What I do is take the drawdown amount and I divide it by 20 trades... I'm never going to lose 20 trades in a row. However, I have lost five, six, even seven trades in a row" [07:05]. E.g. $3,000 DD → $150/trade → "one to two micros" [08:06]. Same risk every trade, never size up on wins or losses [10:08].

**Daily rules:** max 1–2 trades/day; "if I lose two trades in a row, I'm done. There's no exceptions" [08:37–09:08]; daily stop non-negotiable; journal every trade with emotions logged during the session [09:08].

**Strategy layer (his A+ framework, = Model 1):** step 1 daily bias from "previous day high and low sweeps, unfilled fair value gaps, swing points, and the higher time frame order flow"; avoid counter-trend when HTF is displacing [10:39–11:11]. Step 2 SFP ("price to push beyond a key swing high or low, fail to hold, and reverse back through the level and close" [11:11–11:42]). Step 3 LTF entry, any model. "Manage your risk and not your targets": time exits, partial before lunch, aggressive trailing, optional scale-ins [12:12–12:42]. Worked short: stop "above the previous hourly high" / "above the swing failure high", target previous swing low; worked long: 3:1. Rollover close-and-reopen trick for no-overnight rules [14:46].

**Stats he quotes [04:34–05:35]:** eval pass rate "an abysmal 5 to 10%"; "7% of those traders ever reach a payout"; "65% of traders fail in their first week"; "70% lose their funded account before month three"; of 1,000 starters → 350 survive week one → 140 pass → 70 reach payout.

---

## VOCABULARY TRANSLATION (his definition first, our measurable object second)

| Term | HIS definition (quoted/paraphrased) | Machine translation (our conventions) |
|---|---|---|
| Swing point | 3-candle fractal; "candle before it and after it have higher lows"; valid only on 3rd-candle close (HaDJ16Q5W10 [02:03]) | fractal(k=1) on 1H, timestamped at bar3 close; keep only untouched-since-formation |
| Liquidity sweep/raid | price "briefly breaks" a prior swing/session/day extreme; no depth threshold | trade beyond stored extreme by ≥1 tick; record penetration depth as free parameter (his spec: any) |
| SFP (his trigger) | raid + same-candle **close back inside range** on the HTF | 1H bar with high>level & close<level (bearish) / low<level & close>level (bullish); optional strength flags: opposite-color close, close beyond mid-range |
| FVG | "three candle pattern where the high of candle 1 does not overlap the low of candle 3" (YxVU_Pm_1Jw [04:04]); gap bounds = candle1 high ↔ candle3 low (bullish), candle1 low ↔ candle3 high (bearish) | exact 3-bar wick gap; entry at touch/mid/CE; invalidation = close through |
| Inverted FVG | FVG "gets broken... and then we wait for the retracement" — "failure is the signal" (7zna17Noj_Q [06:06]) | FVG with subsequent close through it; retest of the zone from the other side |
| Displacement | "fast one-sided moves... proves intent" (7zna17Noj_Q [04:34]); **operationally he always uses "an FVG was created" as the displacement test** (YxVU_Pm_1Jw [14:46]) | primary: FVG-creation flag; secondary (ours): candle range > x·ATR — he never gives a number |
| Order block | "the last opposing candle prior to a price swing"; stop beyond its extreme (7zna17Noj_Q [07:07]) | last opposite-close candle before an N-bar directional leg |
| Breaker | failed OB, "the swing that creates the breaker needs to take out liquidity" (7zna17Noj_Q [08:07]) | OB whose leg swept a prior extreme, then closed through; trade the retest |
| Premium/discount | fib anchored on "visible swings"; >50% premium, <50% discount (7zna17Noj_Q [02:02–03:03]) | position of price vs midpoint of last confirmed swing-low→swing-high range |
| Session liquidity | Asia 20:00–00:00, London 02:00–05:00, NY 08:00–12:00 ET (09:30–12:00 for indices) | session H/L computed on those exact windows |
| Kill zone / timing | "time is more important than price"; NQ setups only ≥9:30 (FX ≥8:00), AM 9:30–~11:30, PM 13:00–16:00; lunch de-risk 11:00–12:00 | hard time gates on signal validity + forced partial/BE at 11:00–12:00 |
| Turtle soup (rejected) | entering AS the level breaks, "not knowing really where to put my stop loss" — his stated failure mode, win rate ~20% | do NOT implement raw touch-fade; close-back-inside is mandatory |

---

## CROSS-MODEL STATS LEDGER (everything he quantifies)
- Per-setup win rates from his own journal (mKdLG088-9U [07:34–08:35]): **FVG entries 65–70% ("almost seven out of 10")**, liquidity raids ~20% ("two of seven"), breakers ~25%, order blocks ~35% — which is why the system = SFP trigger + FVG entry only.
- SFP hit rate ">60%" (HaDJ16Q5W10); win rate 35%→50%+ after adding closure filter (nuYlnDwgEgg); direction call 60–70% (dcIcXbzMcc4); "something that works 50, 60% of the time" is the realistic edge (mKdLG088-9U [02:31]); 40–50% suffices with 1:2/1:3 (DQiOqFFptfA).
- Risk math: risk/trade = DD/20; max daily loss = −1.5R (full R then half R); 2-loss daily stop; historical worst streak 5–7 losses.
- Frequency: 1–2 trades/day, 3–5 (ideally 2–3) trades/week; hold time examples 2–9 hours; expect 2–3 hourly candles of follow-through.
- "85% of retail traders are losing money" (HaDJ16Q5W10 [05:08]); prop funnel stats as in the prop section.

## GLOBAL DISCRETION WARNING
The three Daily Sweep videos give inconsistent parameter values that must be reconciled by config, not code: level-marking time (8 a.m. vs prior evening), NY range definition (8:00 vs 9:30 start), fixed-R vs liquidity targets, stop anchor (FVG candle-2 vs candle-1 vs hourly swing vs SFP candle), and pre-market permission (he violates his own 9:30 rule live at 7:19 a.m., nuYlnDwgEgg [19:17]). His own resolution is explicit: steps 1–2 are fixed system; step 3 execution "is going to change for every one of you... requires reps" (gGiE3rx2wdg [06:37–07:07]) — i.e., anything inside the entry/stop/target layer is declared trader-specific by design.
