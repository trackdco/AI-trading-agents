---
date: 2026-08-05
kind: as-taught spec sheet (agent, verbatim)
---

All 12 available transcripts read and cross-checked (`.md` block timestamps verified against the `.en.vtt` files — accurate to within a few seconds). **Coverage note: meQM_4kRdII ($300K MNQ) and bgGWVAz_bNY (prop firm) are listed in CATALOG.txt but have NO transcript files in `/home/user/AI-trading-agents/research/transcripts/daxton/` — spec below is triangulated from the other 12.**

---

# DAXTONTRADES — AS-TAUGHT SPEC SHEET
## "One Setup" = NY-Open Pullback FVG-Inversion Continuation (iFVG continuation), NQ 5-minute

---

## 1. NAME + THESIS

He never brands it beyond "my one setup" / "my system." Mechanically it is an **inversion-FVG (iFVG) trend-continuation entry on the first pullback around the 9:30 ET New York open**, with bias from higher-timeframe EMAs painted on the 5m chart.

**Thesis (his framing):** the day has one institutional direction (read off HTF EMAs: "what institutions are seeing" — q1eFMTC3VL8 @02:04). A counter-trend pullback forms an FVG; traders who fade with the pullback are wrong-sided. When price breaks back through that FVG in the trend direction ("inverses" it), the pullback has failed — enter and "trade the continuation" into the nearest resting liquidity pool (prior swing/session extreme) where the trapped side's stops sit. "If I simplify this strategy as simple as possible, we trade pullbacks" (8G4QAFjk7WA @09:24).

---

## 2. ENTRY MECHANISM (exact, with quotes)

**Instrument / TF / session:** "I trade only NQ, only using the 5-minute time frame, and only at the New York session" (u2GpAMi2FYU @01:33; identical in gzninzNXzqI @00:30, vfrELa5SIX4 @00:30, yVJm4Y4GS94 @08:10). One video says MNQ: "I only trade MNQ only using the 5-minute time frame and only on the New York session" (CeMT1KXGdqE @00:30) — and the missing meQM_4kRdII title is "$300K with MNQ". At $2K fixed risk on ~300-tick stops, MNQ sizing (or ~1-2 NQ) is what the P&L implies. Chart TZ must be New York, DST-aware: "make sure that you always have here the New York time zone to not be tricked by this summer and wintertime… We wait for the 9:30 candle" (8G4QAFjk7WA @00:30–01:02).

**Chart furniture:** LuxAlgo Sessions indicator (London AM + NYSE session box; "This session is where I trade" — q1eFMTC3VL8 @01:32) + "Daxton Trend indicator" = TradingView "10 in one different moving average": first three slots enabled, **EMA, 50 period each, on 15m / 30m / 1H**, displayed on the 5m chart (yVJm4Y4GS94 @01:02; tHnn8FxYPlM @07:52; LIWWf0oqDNo @01:00 "All of them are 50 EMAs period. The 15 minutes, the 30 minutes, and the 1-hour").

**STEP 1 — Bias (before 9:30 open, mandatory):**
- Long only: "If the price is at least above the 1 hour EMA, the three are pointing up, we will be only looking for buys" (u2GpAMi2FYU @02:03).
- Short only: mirror — price below 1H EMA, three pointing down.
- No trade: "If EMAs are flat, overlapping or too close to each other, we will not be taking a trade… the market is indecisive" (gzninzNXzqI @01:32).
- Slope is judged from Asia: "you should keep an eye on the EMA since the beginning of the Asian session" (u2GpAMi2FYU @02:34); "we need to count the EMAs from the beginning of the Asian session" (c2U9IZExE-s @05:41).
- Hard filter: "We always buy when we are over at least the one hour EMA and we always sell [when] we are at least below the one hour EMA. Never buy under the EMAs or sell over the EMAs" (vfrELa5SIX4 @06:40).

**STEP 2 — Counter-trend pullback + FVG inside it:** "we want to find the fair value gap inside a pullback in the opposite of our bias" (u2GpAMi2FYU @03:05). "Draw all the fair value gaps that were created in the pullback" (u2GpAMi2FYU @03:36).
- **His FVG definition (verbatim, note it's non-standard):** "we have here a bearish fair value gap. The close of the first candle is higher than the close of the last candle. This what a bearish fair value gap means" (u2GpAMi2FYU @04:38 / VTT 04:40). What he actually *draws* is the standard 3-candle gap: "between this first candle, the second candle, and this third candle, we have a clear fair value gap" (q1eFMTC3VL8 @08:44; CeMT1KXGdqE @02:04 "formed right here between these three candles"). Code the standard 3-candle wick gap; his verbal definition is a misstatement.
- All on the **5-minute** candles only.
- **Session FVG (formed after 9:30) = A+ setup.** Pre-market FVGs allowed but "will always have a lower probability… it works really good when we have directional days" (u2GpAMi2FYU @04:07). Session FVG size irrelevant; "For premarket FVG's, the size matters, but for session FVG's, I don't care about the size" (c2U9IZExE-s @07:44).
- **Never a pre-market FVG on Monday:** "We never take premarket inversions on Monday because it's a very low probability trade" (CeMT1KXGdqE @04:06; repeated c2U9IZExE-s @00:32, EDmFnofLB4Y @04:02).
- Pre-market FVG must sit deep in the pullback: "the lower a premarket FVG is better for a buy position and the higher a premarket FVG is the better for a sell position" (c2U9IZExE-s @08:45). Skip FVGs far from price: "we trade pullbacks. That's why we don't take FVG's that are way higher" (8G4QAFjk7WA @09:24). FVG at all-time high = a weakness (u2GpAMi2FYU @07:12).
- Multiple FVGs: "You simply take the first FVG that was inversed. Simply as that" (u2GpAMi2FYU @09:45); equivalently "I kept drawing FVGs in this pullback, then we inverse the latest one" (CeMT1KXGdqE @09:16).

**STEP 3 — Trigger + entry:** "if price breaks this fair value gap and close above [for longs], always wait for the 5-minute candle to be over. Don't go in in the middle of the candle. If price closes above the FVG, we enter" (u2GpAMi2FYU @04:38). "please make sure to enter after the 5-minute inversion candle is over… price turns against them" (gzninzNXzqI @08:44). Entry = **market order at the close of the 5m inversion candle** (next-candle open). No limit-at-gap-fill, no sweep requirement, no displacement requirement, no session-open sweep — the *only* trigger is candle-close inversion of the pullback FVG in the bias direction. Direction mapping: "if you want to buy, you need to find the inversion of bearish fair value gap. If you want to sell… an inversion of a bullish fair value gap" (CeMT1KXGdqE @05:37).

**The "30 minutes":** not an entry window — it's total screen time. "taking only one trade per day for 30 minutes, then I close my laptop" (LIWWf0oqDNo @00:00); "It went to take profit in 25 minutes. After that, I closed my charts" (gzninzNXzqI @04:39). Operationally: bias check pre-9:30, watch from the 9:30 candle; nearly all shown entries occur within roughly the first hour after open. Soft late cutoff: skipped a setup whose "inversion happened 45 minutes from the market closure. Plus… volume started to die" (CeMT1KXGdqE @12:18).

---

## 3. STOP LOSS (as taught)

"We put our stop loss at the most logical place when the trade is not valid anymore" (u2GpAMi2FYU @04:38). Four sanctioned locations: "At the inversion candle, at the previous candle, at the swing high or swing low, or at the FVG" (vfrELa5SIX4 @04:36) — choice "depends solely on market structure and also on the risk appetite" (gzninzNXzqI @08:44). Heuristics:
- Strong momentum inversion candle → stop below FVG/inversion candle is enough; weak candle → previous candle/swing (vfrELa5SIX4 @05:08–05:39).
- Later formalization: **"three layers of protection"** — stop beyond FVG + inversion candle + previous candle (and/or the relevant EMA), used on nearly every trade in the c2U9IZExE-s and EDmFnofLB4Y recaps (e.g., c2U9IZExE-s @01:02, @10:50 "I keep saying three layers of protection over and over again").
- Size cap (soft): "my stop loss doesn't exceed usually 300 ticks" (gzninzNXzqI @07:13); "I usually don't exceed 300 to 350 ticks per stop loss. But you don't need to take this as a rule" (vfrELa5SIX4 @06:09). [300 ticks = 75 NQ points.]
- Fixed dollar risk, pre-sized: "always define your contract number before entering a trade to risk always the same amount" (vfrELa5SIX4 @06:40). His risk: $2K/trade, raised to $3K from June 8 (c2U9IZExE-s @05:10).
- No break-even management: "I don't move my stop loss to the break even" (xyI6BsoYpdU @04:08). Stop hit → flat, done for the day, no re-entry ("My stop loss was hit. End of the day. I don't go in another time" — u2GpAMi2FYU @09:14).

---

## 4. TARGETS (as taught)

Priority order:
1. **Previous liquidity** if it yields ≥2R: prior swing highs/lows and session extremes — named examples: "yesterday New York high" (CeMT1KXGdqE @06:40), "London high" (CeMT1KXGdqE @08:44), "the opening of the day" (EDmFnofLB4Y @04:32), prior wicks (EDmFnofLB4Y @01:32). TP set **short of the level**: "never put the TP right here at the liquidity because sometimes price will simply will not get to that liquidity" (q1eFMTC3VL8 @09:47).
2. **Fixed 2R** if no liquidity or liquidity <2R: "If it's under 2 hours ['2 Rs' — transcription artifact], we target the previous one. If we have no liquidity, we simply target 2 hours" (u2GpAMi2FYU @05:09); "since this liquidity gives me less than two [Rs]… 1.6 [R], I simply ignored it and targeted two [Rs]" (CeMT1KXGdqE @02:34).
3. **Time exit:** always flat before session close: "I always close my positions before market close" (CeMT1KXGdqE @09:16); closed at ~1R and 2.2R before closure (c2U9IZExE-s @01:02, @02:37).

---

## 5. MANDATORY CONTEXT / BIAS SOURCE

The 3-EMA stack (50-period EMA of 15m/30m/1H on the 5m chart) is the sole bias source — "That's my entire bias under 10 seconds. No weekly analysis" (q1eFMTC3VL8 @02:34). **Intraday bias flip is sanctioned** when price breaks through the EMAs (esp. the 1H) *with momentum*, but the new bias still needs its own FVG-inversion trigger: "yes, I switched the bias, but we didn't have any entry trigger. Where is the FVG that this candle inverse?" (c2U9IZExE-s @09:48–10:20; flips traded: 8G4QAFjk7WA Mar 9/13/31, EDmFnofLB4Y Jun 22/25/29). No-trade days: US bank holidays (u2GpAMi2FYU @07:43), flat/mixed EMAs, dying volume, freak news candles ("This was a Trump tweet… I didn't trade that day" — 8G4QAFjk7WA @15:42).

---

## 6. DISCRETION GAPS (literal readings enumerated)

1. **"Stacked and pointing up/down"** — no slope or separation threshold ever given. Readings: (a) strict ordering EMA15>EMA30>EMA60 with all slopes positive over N bars; (b) only price>1H-EMA + 1H slope; (c) visual. "Flat/overlapping/too close" equally unquantified — and the Asia-session-lookback nuance means flat-at-open can still be tradeable (u2GpAMi2FYU @02:34). He himself trades some flat days on "momentum" (8G4QAFjk7WA @12:33 Mar 17) and 6-day-trend override (u2GpAMi2FYU @10:46 May 28).
2. **"Counter trend / pullback"** — never defined (bars, depth, structure). Readings: any counter-direction retrace on 5m; a lower-high/higher-low sequence; anything visually "a pullback."
3. **FVG definition conflict** — verbal close-to-close vs drawn 3-candle wick gap (see §2). Code the wick gap (candle1.low > candle3.high for bearish).
4. **"Inversed"** — break-and-close beyond the gap, but "beyond" = beyond the far edge of the gap (as drawn) vs merely closing inside; all shown examples close fully through. Whether prior partial mitigation invalidates a gap: unstated ("unmitigated" is required for pre-market gaps — gzninzNXzqI @07:13, CeMT1KXGdqE @02:04 implied).
5. **Which FVG** — "first FVG that was inversed" vs "the closest FVG that the price didn't break" (q1eFMTC3VL8 @04:38) vs "take the last fair value gap that was inversed and we simply ignore this [earlier]" (tHnn8FxYPlM @05:13). Operational reconciliation: maintain ALL unmitigated FVGs in the current pullback; the first one to invert is the trade. "Way higher" FVGs excluded — no distance number.
6. **Pre-market FVG eligibility** — "directional day" belief (undefined), "size matters" (no threshold), depth-in-pullback (no metric), Monday ban (crisp). He concedes: "There is absolutely no single hard rule about it… it's your choice to either take it or leave it" (CeMT1KXGdqE @03:36; c2U9IZExE-s @03:08).
7. **Stop placement** — 4 options selected by "momentum candle" judgment (undefined); 300–350 tick cap explicitly "not a rule."
8. **Target liquidity** — the universe of "previous liquidity" levels is never enumerated; "slightly before" offset unquantified; early discretionary exits ("I chickened out and targeted 2R" — c2U9IZExE-s @02:05).
9. **No-trade overlays** — "volume started to die"/"candles becoming much smaller" (gzninzNXzqI @03:37), "I simply wasn't comfortable" (gzninzNXzqI @04:07), news days — all judgment calls.
10. **Bias-flip "momentum"** — break vs "rejected the EMAs" distinction is case-by-case (c2U9IZExE-s @09:48–10:50).
11. **Entry window bounds** — no hard start/stop; only the 9:30-open anchor, the 45-min-before-close skip precedent, and flat-by-close.

---

## 7. DATA NEEDS (to code it)

- 5m OHLC for NQ **and** MNQ (continuous front contract), 24h Globex (Asia session onward needed for pre-market FVGs, EMA slope since Asia open, and liquidity levels), timestamped America/New_York, DST-correct.
- 50-EMA on native 15m/30m/1H series (or resampled) projected onto 5m timeline.
- Session calendar: NYSE 9:30–16:00 ET, US bank holidays, half days; London session times (for "London high" targets).
- Liquidity level set: prior-day NY high/low, London high/low, day open, week open, recent 5m swing highs/lows and wicks.
- Volume (his "volume dying" proxy is candle range, so range works).
- Economic/news calendar for freak-candle exclusion (optional but he skips those days).
- Tick math: NQ tick 0.25 pt; 300 ticks = 75 pts; fixed $ risk sizing.

---

## 8. CLAIMED STATS + BACKTEST METHOD

**Claims across videos (chronological escalation):** $191K/3mo, "73% win rate", monthly $60K Jan/$64K Feb/$54K Mar, $2K risk (q1eFMTC3VL8 @00:00, @10:18); 5 months Jan–May "73% win rate", min $4K/winning day, "9 years" trading (u2GpAMi2FYU @00:32–01:03); "75% win rate" last 4 mo; April = $41,000, 83% WR, 10W-2L; one 5/5 week (LIWWf0oqDNo @00:00, @05:40–06:11); $242K/120 days (gzninzNXzqI @00:00); $228K/4mo (yVJm4Y4GS94 @07:08); $207K/90 days (tHnn8FxYPlM @00:00); $257K "almost 75% win rate in the last 4 months" (vfrELa5SIX4 @09:14); $60K in one month "78% win rate" on MNQ (CeMT1KXGdqE @00:00); $16,596 over 2 weeks, 9 trades ≈5W-4L, risk raised $2K→$3K Jun 8 (c2U9IZExE-s); 6 trades 4W-2L +$14,345 (xyI6BsoYpdU @00:00); +$10K in his worst (3-loss) week of 2026 (EDmFnofLB4Y @03:02). The "72%" figure appears only in the 8G4QAFjk7WA *title*. All P&L is TradeZella dashboards refreshed on camera; no broker statements.

**Backtest video method (8G4QAFjk7WA) — capture exactly what he counted:** Population = every NYSE trading day of March (Mar 2–31, 22 sessions), one trade/day. Method = TradingView bar-replay, day by day, **with his original live positions left drawn on the chart**: "I will leave my positions exactly like I took them because I don't want to waste time looking for FVG's on the chart" (@00:00). So it is a **replay/reconciliation of his own live trades against his account dashboard, NOT an independent rules-driven re-derivation** — the FVGs, entries, stops and targets are his recorded ones, and he admits recall gaps ("these trades were three months ago… bear with me if I don't remember" @15:42; "I think I was targeting this liquidities… I targeted two [Rs]. Let me see" @08:19). Day tally as shown: **wins Mar 2,3,4,9,10,12,13,16,18,20,26,27,30,31 (14); losses Mar 5,6,11,17,19,24,25 (7); no-trade Mar 23 (news)** = 21 trades, **66.7% WR for the month — below the 72% title**. Includes self-flagged rule breaks counted as trades: Mar 2 "aggressive," Mar 16 "very low probability… extremely aggressive… I just got lucky," Mar 24 "This was a no trade day… I made a mistake." R-multiples: mostly ~2R, a 3R, 2.12R, 3.3R, one ~4.4R ($8.82K on $2K risk, Mar 30); losses ~1R (-$2K).

---

## 9. CONSISTENCY CHECK — taught vs traded (recaps CeMT1KXGdqE, c2U9IZExE-s, EDmFnofLB4Y, xyI6BsoYpdU + backtest)

**Core mechanics hold:** in ~45 shown trades, entry is always a 5m close through a pullback FVG in bias direction; stops at FVG/inversion/previous candle; targets liquidity-or-2R; loss → done. The skeleton is real and repeated.

**Deviations (diagnostic):**
1. **Pre-market FVGs are his edge-eroding wildcard.** Taught as "lower probability / directional days only," yet ~⅓ of backtest-month entries were pre-market gaps, including both self-labeled "lucky"/"aggressive" wins. The filters (Monday ban, size, depth-in-pullback) appear only in later recaps — post-hoc patches. He concedes "no hard rule" — this branch is not mechanical.
2. **Flat-EMA rule violated by the teacher:** May 28 win on admittedly flat EMAs ("this should be no trade day, you are 100% correct… Maybe I had the formal [FOMO] entry" — u2GpAMi2FYU @11:48); Mar 17 loss, Mar 24 loss ("I should have avoided this day easily"), Apr 7 win ("This is no trade day… I was a little bit lucky" — CeMT1KXGdqE @05:07). The rule filters losses in hindsight but he overrides it on "momentum"/multi-day-trend grounds.
3. **Intraday bias flips** are traded routinely though the taught flow is "define bias before open" (≥6 shown flips). Flip legitimacy is argued case-by-case ("where do you see that the price broke all the EMAs with momentum?").
4. **"One trade per day" is really 90–95%**: "95% of the time I only take one trade per day" (CeMT1KXGdqE @11:17); two trades taken Jun 29 (EDmFnofLB4Y @05:03).
5. **Target discretion:** cut a would-be ~700-point runner to 2R ("I chickened out" — c2U9IZExE-s @02:05); regretted skipping a 6R pool (xyI6BsoYpdU @07:15); two before-close exits at ~1R. Realized R is spread around, not fixed at, 2.
6. **Execution slips he admits on tape:** late entry Mar 3 ("entry, honestly, should be here"); three stop-placement mistakes in June alone (c2U9IZExE-s @04:39, @06:12, @12:21 "I promise you, I will never repeat this stop loss mistakes ever again") — "three layers of protection" is a formalization invented after those losses.
7. **Numbers don't reconcile:** the only month audited on tape (March) shows 66.7% WR vs headline 72–75–78–83% claims; win-rate claims drift video-to-video over the same period; instrument drifts NQ↔MNQ.

**Bottom line for coding:** the mechanical core (bias stack + pullback FVG + 5m-close inversion + FVG/candle stop + liquidity-else-2R target, one trade/day, NY session) is fully specifiable. The claimed win rate, however, is carried by the discretionary overlays — flat-EMA exclusion (inconsistently applied), pre-market-FVG cherry-picks, volume/news skips, and early exits — precisely the branches he never defines numerically. A faithful mechanical backtest should implement the core, expose the §6 gaps as parameters, and expect materially below-72% out of the box (his own March replay = 66.7% *with* his discretion included).

Source files: `/home/user/AI-trading-agents/research/transcripts/daxton/{q1eFMTC3VL8,u2GpAMi2FYU,LIWWf0oqDNo,gzninzNXzqI,8G4QAFjk7WA,vfrELa5SIX4,yVJm4Y4GS94,tHnn8FxYPlM,CeMT1KXGdqE,c2U9IZExE-s,EDmFnofLB4Y,xyI6BsoYpdU}.md` (+ matching `.en.vtt` for precise timing); `CATALOG.txt` for titles. Missing transcripts: meQM_4kRdII, bgGWVAz_bNY.
