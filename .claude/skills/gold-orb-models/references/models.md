# ORB Model Specifications (extracted 17 Aug 2026 from three source transcripts)

Tier legend — **STATED**: the creator says it outright. **INFERRED**: visible only in their chart walkthrough. **UNDEFINED**: the source never pins it; it is a backtest decision variable.

Attribution note: source 1 credits the ORB to "Tony Krabble, chairman of Krabble Capital Management". The actual originator is **Toby Crabel** (Crabel Capital Management), *Day Trading with Short Term Price Patterns and Opening Range Breakout* (1990). Crabel's original method conditioned entries on volatility contraction (NR4/NR7, inside days) with a "stretch" offset — none of which appears in any of these three models.

---

## M1 — "Modified ORB" with volume profile (source 1; taught on NASDAQ/NQ, row sizes given for NQ and ES only)

### Shared setup
| Parameter | Value | Tier |
|---|---|---|
| Session anchor | 9:30 a.m. ET | STATED (NASDAQ example) |
| Opening range | High/low of first 15-min candle | STATED |
| Execution timeframe | 5-min | STATED |
| Value area | Fixed-range volume profile across the first three 5-min candles; ticks-per-row; row size 1 (NQ), 10 (ES); volume = total; value area = 70% → marks VAH, VAL, POC | STATED |
| Row size for GC | — | UNDEFINED (GC tick = 0.1; sweep row size ∈ {1, 2, 5, 10} ticks) |
| Liquidity definition | A swing point: "any candle that has a higher high than either candle on side of it" (stated for highs; mirror for lows) | STATED (highs) / INFERRED (lows) |
| Liquidity lookback window & proximity ("right outside the range") | — | UNDEFINED (sweep: lookback ∈ {prior session, 20/50/100 bars}; proximity ∈ {0.25×, 0.5×, 1.0× range width}) |
| Both-sides liquidity | If liquidity sits on both sides of the range → take no breakout, wait for a fade either side | STATED |

### M1-A — Fakeout fade (reversal)
| Parameter | Value | Tier |
|---|---|---|
| Precondition | Clean/obvious liquidity resting just outside the opening range → skip the initial breakout | STATED |
| Trigger sequence | (1) price hits the liquidity; (2) a 5-min candle **closes back inside the value area** | STATED |
| Liquidity "hit" = wick touch or close through | — | UNDEFINED (sweep both) |
| Entry | On the signal candle's close (enter the reversal) | INFERRED (walkthrough enters "as soon as that candle closes") |
| Stop | Just beyond the signal candle's extreme (high for shorts, low for longs) | STATED; exact buffer UNDEFINED (sweep {0, 1, 2} ticks) |
| Target | Nearby opposing liquidity, or "play it safe": opposite side of the opening range | STATED (discretionary choice; code both as variants) |
| Example outcome shown | ~5:1 R on one walkthrough | INFERRED (single chart example, not a statistic) |
| Close back inside **value area** vs inside the **price range** | Value area is explicit ("back inside your volume profile level") | STATED — do not substitute the OR boundary |
| Gap case: candle closes inside OR but outside VA | — | UNDEFINED (decide + report: treat as no-signal by default) |

### M1-B — With-trend value-area breakout
| Parameter | Value | Tier |
|---|---|---|
| Precondition | Clear trend, **or** a liquidity sweep just before/at range formation ("hit into a low and a really aggressive move to the upside just after it") | STATED; "clear trend" definition UNDEFINED (sweep: 1h EMA20 slope / prior-day close relation / VWAP side) |
| Trigger | Any 5-min candle **after the first three** closes outside the value area (VAH for longs, VAL for shorts) | STATED |
| Entry | On that candle's close | INFERRED |
| Stop | 2 ticks past the POC | STATED (NQ ticks; GC equivalent UNDEFINED — sweep {2 ticks, 0.2×VA width}) |
| Target | Fixed 2R ("target is two times the distance away from your entry as your stop") | STATED |
| Management | None — set and leave ("no more work to do") | STATED |

### M1 — unstated across both setups
Time-of-day cutoff; max trades/day; re-entry after a stop; risk % per trade; news handling; behaviour when no liquidity is nearby and no trend exists (presumably no trade — INFERRED). Source performance claim: account "10K to over $200,000" — asserted, zero evidence shown; the 15-min range being "most profitable if you test it over the long term" — asserted, no test shown.

---

## M2 — Plain 15-min ORB, applied to gold, + proposed context filters (source 2)

### Base rules (the version he tested informally on gold)
| Parameter | Value | Tier |
|---|---|---|
| Session anchor | 9:30–9:45 a.m. ET ("New York open") | STATED |
| Opening range | High/low of the first 15-min candle | STATED |
| Entry | A candle **closes** outside the range → long above / short below | STATED; entry-candle timeframe UNDEFINED (walkthrough appears to be the 15-min chart — INFERRED; sweep {5m, 15m}) |
| Stop | Opposite side of the range | STATED |
| Target | 1:1.5 risk-to-reward ("very conservative") | STATED |
| Trades per day | One ("one clean breakout trade every morning") | INFERRED |

### His own gold sample (evidence tier: informal eyeball test)
8 recent trading days on gold: 2 wins, 5 losses, 1 open-likely-win → ≈ +4.5% vs −5%, **net ≈ −0.5%**. STATED. Tiny sample; no costs modelled; treat as anecdote consistent with "plain ORB on gold loses", not as a measurement.

### Proposed fixes (all untested claims)
1. Trade only in the direction of the higher-timeframe trend — "the 15-minute or the 1-hour bias". STATED; bias definition UNDEFINED.
2. Watch for fakeouts and "trade the re-entry back inside the range" — i.e. a fade, kin to M1-A but keyed to the **price range**, not a value area. STATED; entry/stop mechanics for the re-entry UNDEFINED.
3. Add confirmation: structure breaks, liquidity sweeps, trendlines, Fibonacci retracement zones. STATED as categories; every threshold UNDEFINED. (Note: a separate audit in this workspace found Fibonacci levels carry no standalone edge — see /areas/ote-model context if available.)

---

## M3 — Backtested plain ORB + breakout-pullback-continuation test (source 3; S&P 500 data, 5 years)

### M3-base (his standing strategy — the only fully specified model in the set)
| Parameter | Value | Tier |
|---|---|---|
| Chart/timezone | 15-min chart, New York time (UTC−4) | STATED |
| Opening range | High/low of the 9:30 candle | STATED |
| Entry signal | First candle to break **and close** outside the range | STATED |
| Fill | Open of the **next** candle | STATED |
| Stop | Opposite side of the range | STATED |
| Target | 1.5R | STATED |
| Cutoff | No entries after the 12:00 candle | STATED |
| Range filter | Skip ranges too small or too big vs recent ATR | STATED; thresholds UNDEFINED here (in his other video — sweep {0.5–2.0}×ATR bounds) |
| Instrument | "S&P 500 data" | STATED; index vs ES futures UNDEFINED; costs/slippage modelling UNDEFINED |

### M3-BPC — the variant he built and refuted
Rules tested: 5-min chart; OR = first three 5-min candles; breakout candle height ≥ 1×ATR (his codable breakout definition); wait for pullback to the OR; confirmation candle breaks into the range boundary but **closes back outside** it (a close back *inside* the range invalidates); enter on break of the confirmation candle's high; stop at the opposite side of the OR (alt tested: pullback-candle extreme); target 1.5R.

Results (STATED, backtest shown): 5 years, ~130 trades, flat equity first 3 years, mildly positive 2023+, overall poor and below his base strategy; win rate ≈ unchanged vs base. TP sweep 2.5R→4.5R in 0.5 steps: monotonic slight improvement, still poor. Stop-order entry at the OR boundary (no confirmation): worse. Stop-order entry at the 50% range midpoint: worst. **Verdict: unprofitable — refuted on S&P.** Exact win rates/PF/returns not quoted numerically in the transcript.

His diagnosis (STATED): promo examples are cherry-picked; the strongest breakouts have momentum and **don't** pull back to the range, so waiting for a pullback adversely selects the weak breakouts. His proposed next direction: filter on the momentum/strength of the initial breakout instead.

---

## Cross-model conflicts and how to treat them

1. **Fade vs continuation is not one question.** M3 refuted *same-direction* pullback-continuation. M1-A and M2-fix-2 are *reversals* against a failed breakout, conditional on external liquidity — a different trade population. M3's result does not refute M1-A; it does raise the prior that "wait for price to come back" mechanics leak edge. Test M1-A independently; do not average the populations.
2. **Range vs value area.** M1 keys everything to the 70% value area; M2/M3 key to the raw price range. When implementing M1, the VA is the boundary — logging both boundaries per trade costs nothing and settles which carries the information.
3. **Anchor.** All three use 9:30 ET (stock open). Gold-native anchors (8:20 ET COMEX, ~03:00 ET London) are untested by all three — sweep per SKILL.md rule 6.
4. **Evidence ranking.** M3 > M2 > M1. M3 shows a real backtest (negative for BPC); M2 shows an 8-day eyeball sample (negative); M1 shows two winning walkthroughs and an account claim (no evidence). Weight priors accordingly when a sweep produces marginal results.

## Consolidated sweep list (the UNDEFINED set, in priority order)

anchor {8:20 ET, 9:30 ET, 03:00 ET London} · GC VP row size {1,2,5,10 ticks} · liquidity lookback {prior session, 20/50/100 bars} × proximity {0.25/0.5/1.0× range} · trend definition {1h EMA20 slope, prior-day close side, session VWAP side} · entry-candle TF for M2 {5m, 15m} · stop buffers {0,1,2 ticks} · ATR range-filter bounds {[0.5,2.0]×ATR grid} · cutoff {none, 12:00 ET} · trades/day {1, unlimited} · re-entry after stop {no, one} · news blackout {none, ±15 min around 8:30 ET releases + FOMC}
