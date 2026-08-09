---
title: Source audit — Zarb (@iamzarb / "zach anthony", ASFX TV)
purpose: Extract the raw, mechanical triggers from an 8-transcript corpus; separate what is specifiable from what is discretionary; price the claims against already-measured results
status: audit only — no spec, nothing commissioned
date: 2026-08-09
---

# Zarb — raw trigger audit

## 0. Provenance and coverage

- **Corpus:** 8 transcripts. Channel catalogue could not be enumerated (YouTube blocks page render and the RSS feed to automated fetch), so coverage is "what was supplied", not "the channel".
- **Instruments:** NQ (Model A, exclusively), ES + NQ (Model B), CL (one legacy example).
- **Chronology matters — the model changed.** Internal date markers put transcripts 2–8 in **2025** (doc 5: "we're in 2025 now"; doc 6: May 20 2025) and transcript 1 in **March 2026** ("in 2026 we are getting really nice volatility in the Asia session"). The payout narratives reconcile: doc 2's "$32,000 just from Tradeify" in Jul–Aug 2025 *is* doc 1's "previous record month back over the summer, 32,000".
- **Consequence:** this is not one strategy. It is a **legacy NY positive-R framework (Model B, 2025)** that he abandoned mid-2025 in favour of a **negative-R Asia scalper (Model A, current)**. He says the switch explicitly: *"my win rate last year used to be like 30%… average R multiple was usually three times my risk… what has helped me grow exponentially this year is switching to a negative risk-reward base-hit scalping approach."*
- **Named but absent from the corpus:** the SMT divergence explainer, the "80% rule" setup video, and an order-block explainer. The 80% rule is load-bearing in doc 5 and never defined there.

---

## 1. MODEL A — Asia scalping model (current; NQ only)

Nominal shape: **fixed 10-point target against a 25–40 point stop.** Two arms.

### A1 — Mean reversion arm

| # | Trigger | Mechanical? | Exact rule as stated |
|---|---|---|---|
| A1.1 | Session gate | Yes | Entry only after **20:00 ET** (Asia kill zone open). He states he has no data before 20:00 and speculates 18:00 may work. |
| A1.2 | Instrument gate | Yes | **NQ only.** Explicitly not ES, not CL, not gold — "I'm not saying it wouldn't work there" but no data. |
| A1.3 | HTF trend alignment | Yes | 1h trend direction, derived from his MSS definition (below). Trade *with* the 1h trend. So this is a reversal on LTF but a **pullback continuation** in HTF terms. |
| A1.4 | POI must exist | Yes | One of: (a) FVG on **15m or higher**; (b) previous-day **VAH / VAL / POC**; (c) a 15m/1h **liquidity sweep**. Stacked POIs (e.g. PD-VAL sitting inside a 15m FVG) are called higher-probability but no rule quantifies the bonus. |
| A1.5 | Entry | Yes | **Resting limit order** at the POI. No confirmation of any kind. FVG placement = **midpoint (50%)** as the systematic default; volume-profile levels = at the level itself. |
| A1.6 | Stop | Yes | Fixed **25–30 pts** (25 if target is 5, 30 if target is 10, 40 in high volatility). Not structural. |
| A1.7 | Target | Yes | Fixed **5–15 pts**, default **10**. |
| A1.8 | Management | Yes | **None.** No BE move, no partials, no trail. One in, one out. He argues against BE moves explicitly: *"they had 20 points of floating profit and they didn't take that money."* |

### A2 — Continuation arm

| # | Trigger | Mechanical? | Exact rule as stated |
|---|---|---|---|
| A2.1 | Session + instrument | Yes | Same as A1.1 / A1.2. |
| A2.2 | LTF trend alignment | Yes | **1m AND 5m trend must agree.** This is the required filter; 1h alignment is "bonus points", explicitly *not* a requirement. He shows a valid setup taken against the 1h trend. |
| A2.3 | Momentum / displacement | **No** | "Moving with purpose", "momentum behind those candles", "displacement". Only calibration given: an example he measured as **100 NQ points in a few minutes**. |
| A2.4 | Structure shift | Yes | 1m MSS (ideally also 5m), typically following a 20:00 volatility injection and a liquidity sweep. |
| A2.5 | Draw on liquidity, **untaken** | Yes | Must exist and must **not yet be taken**: unmitigated FVG, equal highs/lows, session liquidity (prior Asia/London session high/low), PDH/PDL, volume-profile levels. |
| A2.6 | **Hard invalidation** | Yes | **If the DOL is taken, the setup is dead — do not enter.** Stated in both A2 and Model B (where taking the objective downgrades an A+ to "a C minus"). This is his single cleanest binary kill rule. |
| A2.7 | Entry | Yes | Limit at the **50% midpoint of a 1m FVG** — *"nine out of ten times I'm looking for the 50% retracement."* |
| A2.8 | Stop / target | Yes | Stop **30–40 pts**; target **10 pts**. |
| A2.9 | Re-entry | Yes | Permitted and encouraged **while the DOL remains untaken and the POI still holds**. Re-arm on new internal structure (e.g. fresh internal equal highs). |

### A3 — Session/day-level rules (doc 2)

- **2 wins → stop for the day. 2 losses → stop for the day.** Self-described as a general guide, not hard.
- **2–4 trades/day per account** is the target state; he attributes his best month directly to cutting frequency (July peaked at ~9–10 trades/day/account, August at 2–4).
- Overflow discipline: route the urge to trade to an **eval account**, never to a funded one.
- Setup selection heuristic: *take setups where 25–50 pts looks available, then only harvest 5–15.*

---

## 2. MODEL B — the "A+ / forever model" (legacy NY, ES + NQ)

Four **required** components. Positive R (2–4R typical; 3.3R standard on CL).

| # | Trigger | Mechanical? | Exact rule as stated |
|---|---|---|---|
| B.1 | **HTF zone** | Yes | Price must trade into a level from **1h or higher** — 1h/4h/daily FVG, order block, or a clean swing high/low. *Nothing below 1h.* Timeframe pairing convention: 1h zone → 5m structure → 1m entry; 4h zone → 15m structure → 5m entry; daily zone → 1h structure → 15m entry. |
| B.2 | **SMT divergence** | Mostly | Price-action divergence between **ES and NQ** at/around the zone, checked on the **same clock-stamped candle** (he timestamps: 08:13, 01:30). Bearish = one makes HH, the other LH. Bullish = one makes LL, the other HL. *No lookback window is defined* — that's the gap. |
| B.3 | **Draw on liquidity** | Yes | Equal/relative equal highs or lows; session liquidity (Asia high/low, London high/low); PDH/PDL, prior week/month high/low; an unfilled HTF FVG to rebalance; previous-day POC. Same hard invalidation as A2.6 — once taken, the setup is dead. |
| B.4 | **Inversion FVG entry** | Yes | An opposing FVG must be **inverted by a candle CLOSE**, not a wick. *"Technically we did not close below the gap, so if you're trying to be textbook you cannot take this entry."* Coincides with an MSS. |
| B.4a | — execution, aggressive | Yes | Enter at the close of the inverting candle. Stop 1 tick beyond the inverted FVG. |
| B.4b | — execution, patient | Yes | Limit inside the inversion for break-and-retest, **or** the **50% fib** of the impulse leg (premium/discount). |
| B.4c | — invalidation | Yes | A **closure back through** the inverted FVG on the entry timeframe. |

### Model B overlay filters (stated as strong, used inconsistently)

| # | Filter | Rule | His own compliance |
|---|---|---|---|
| B.5 | **The Golden Rule** | Above previous-day **POC** → longs only. Below → shorts only. Claims **8/10** standalone accuracy. | Admits violating it, twice, on camera — *"I probably would have had an easier time trading if I just followed my own golden rule."* |
| B.6 | **Midnight open** | Open below the **00:00 ET** price → discount → look long; above → premium → look short. Cited stat: **69%** of ES sessions opening below midnight open retrace to it during NY, trailing 1 year (source: Edgeful, "ICT opening retracement" report). | Used as the primary bias in doc 7. |
| B.7 | **Swing failure pattern** | Wick beyond a level, close back inside → trapped traders → reversal. | Used as a sweep confirmation, not an entry. |
| B.8 | **15m structure** | *"Following the 15-minute structure will always put you on the right side of the market."* | Used as a bias tiebreaker. |
| B.9 | **80% rule** | Referenced in doc 5 as "an 80% setup" (open without engaging PD-POC, then run up and engage it). **Never defined in the corpus.** Canonical version is: open outside the prior value area, rotate back inside → ~80% chance of traversing the full value area. | Explicitly declined to trade it in that example. |

### Model B exits

- One in, one out. No partials, "mostly".
- Stops: aggressive = 1 tick beyond the inverted FVG; medium = beyond recent structure; wide = beyond the swing. He picks aggressive.
- **Risk reduction:** once the inversion holds and price breaks away, trail the stop to just above the last structure high/wick. Doc 6 turned 38 ticks of risk into ~4R this way.
- **BE at 1–1.5R** (doc 7, doc 8). Note this directly contradicts his Model A position, where BE moves are criticised.
- **Front-running targets:** deliberately exits *before* the DOL, most often at previous-day POC. Doc 6 takes profit at the **beginning** of the HTF FVG, not the midpoint or full fill, on the reasoning that a bullish HTF gap may hold.

---

## 3. Shared level infrastructure — fully specifiable

This is the most reusable material in the corpus. Exact and unambiguous:

| Parameter | Value |
|---|---|
| Tool | TradingView **Session Volume Profile** (SVP) — not VPVR, not fixed-range |
| Sessions | **All** (Asia + London + NY). His stated reason for the biggest divergence in other people's levels. |
| Value area volume | **68%** (says 70 also works; claims 68 is more accurate) |
| Chart timeframe for reading levels | **30-minute**, always |
| Profile window | **18:00 → 16:30 ET** (one full session) |
| Profile used | **Previous day's completed profile only** — never the developing/current one, because he wants static levels |
| Levels marked | PD-POC, PD-VAH, PD-VAL, PDH, PDL |
| POC extension | Off (aesthetic preference) |

⚠️ **Note the discrepancy with the failed-auction spec already run:** that used an **18:00 → 09:30** window at **70%** VA. Zarb's is **18:00 → 16:30** at **68%**. Different level set. Overlapping, not identical.

---

## 4. What is NOT mechanical — the spec blockers

Ranked by how much they'd bite a builder:

1. **FVG selection when several exist.** Never stated. Implied "nearest / the one price draws into first" but never said. This is the single largest ambiguity in both models.
2. **Momentum (A2.3).** Unquantified beyond one 100-point example. Needs an operational definition (range expansion vs trailing ATR, or displacement per unit volume).
3. **Limit placement inside a zone.** He offers start / midpoint / end and resolves it with *"how confident are you in the setup… this is where intuition may come in."* Default is midpoint but he admits missing fills and calls it acceptable.
4. **Stop selection 25 vs 30 vs 40, target 5 vs 10 vs 15.** Chosen by feel on volatility.
5. **SMT lookback window.** Which swing, how far back, on what timeframe. Undefined.
6. **"Relative" equal highs/lows.** He accepts a one-tick-lower high as an SMT lower high and calls near-equal highs "relatively equal". No tolerance band.
7. **He states the discretion outright, twice:** *"I'm not somebody who believes in a purely systematic trading strategy"*; *"do I follow that 100% of the time? Absolutely not."*

---

## 5. ⛔ The arithmetic problem — the published mechanics cannot produce the published results

This is the finding that matters most before anything gets built.

**Breakeven win rate at his stated stop/target combinations:**

| Target / stop | Nominal R | Breakeven WR |
|---|---|---|
| 10 / 25 | 0.400 | 71.4% |
| 10 / 30 | 0.333 | **75.0%** |
| 10 / 40 | 0.250 | 80.0% |
| 5 / 25 | 0.200 | 83.3% |
| 15 / 25 | 0.600 | 62.5% |

His **default** configuration (10 pts vs 30 pts) needs **75% wins to break even**.

**What he actually reports:**

| Sample | WR | Reported avg W/L | EV/trade (reported) | EV/trade at nominal 0.333R |
|---|---|---|---|---|
| Doc 1 — Tradeify, 2 months, both models | 65% | 0.840 ($372 / $443) | **+0.196R** | **−0.133R** |
| Doc 1 — March only, self-selected | 85% | 0.700 | **+0.445R** | +0.133R |
| Doc 2 — 437 trades, two firms | 73.0% (319W / 118L) | 0.626 ($339 / $542) | **+0.187R** | −0.027R |

**The gap:** his realised win/loss ratio is **0.63–0.84**, against a nominal **0.33**. That is a factor of **1.9–2.5×**. With wins hard-capped at the 10-pt target, the only way to get there is for average losses to land at roughly **40% of the stated stop** (~12 pts against a 30-pt stop).

**So there is an unstated exit layer doing most of the work.** Candidates: manual early loss-cutting, heavy scratching/BE-ing, or journal contamination from other models. Contamination explains doc 2 (he says outright: *"I don't only use Tradeify and I don't only use this model"*) but **not** doc 1, where the Tradeify Lightning accounts are described as purpose-built for this model and still show 0.84.

**Consequence for any build:** a mechanical backtest of the rules exactly as published will produce a materially worse result than his screenshots, and at his own overall reported win rates (65% / 73%) the published mechanics are **negative expectancy**. Only the self-selected best month clears breakeven.

---

## 6. Evidence quality

- **Payout proof ≠ strategy proof.** $79k lifetime, $34k in March, $44k in six weeks — all real-looking screenshots, all from **5 accounts across 3 firms at 150k sizing**. Dollars scale with size and account count, not edge.
- **Zero losing examples in 8 transcripts.** Every chart walkthrough is a winner, in replay mode. One trade is labelled "ugly" and "scary to be in" — it still wins. This is the most reliable tell in the corpus.
- **To his credit, he discloses against himself:** a red February he had to grind back and nearly blew the accounts; that the 85% figure is a filtered subset of a 65% sample; that he violates his own golden rule; that he mixes firms and models in the same journal; that March was *"an outlier month."*
- **One third-party, quantified, independently checkable claim in the entire corpus:** the 69% midnight-open retracement stat, attributed to Edgeful, ES, trailing year. Everything else is his own screenshots or unquantified assertion.

---

## 7. Collision map — against results already on the board

| Zarb component | Status against measured work |
|---|---|
| **Asia session, NQ** (Model A's whole premise) | ⛔ **Ruled out yesterday** — Asia closed for NQ, gold-futures-later. Model A is *only* an Asia NQ model. |
| **PD-POC / VAH / VAL levels** | ⚠️ The **rotation** claim is dead (failed-auction census: no lift, both placebos fired at ~5× the real effect). But the **Golden Rule is a different claim** — POC as a *directional bias filter*, not a rotation target. Never tested. It would inherit the proximity-matched placebo burden. |
| **Fixed 10-pt target, no management** | ⚠️ Fixed targets were refuted on the London book — but only across **1R–3R**. Nothing sub-1R was tested, and it was London-only. Not a clean kill; not a clean pass either. |
| **Negative R at high WR** | ⚠️ Directionally aligned with the prop-EV finding, but **0.33R is below the point already computed as structurally dead against the winning-day dollar floor** at current sizing. Zarb solves this with size (150k × 5 accounts, multiple contracts), not with R. The binding constraint is size, exactly as the prop-EV work concluded. |
| **A1's passive limit at the zone, no confirmation** | ⛔ **Opposite of stated grammar** — "I always wait for candle closure through a lower timeframe moving average." Adopting A1 means adopting an entry style explicitly not used. |
| **A2 / Model B — closure-confirmed entry** | ✅ Compatible. B.4's "must close through, a wick doesn't count" is the same grammar. |
| **Model B overall** | ⚠️ ~80% redundant with the PB Blake model already queued (sweep → rebalance → IFVG entry → DOL target). |
| **SMT divergence** | 🔑 **The one genuinely discriminating test available.** Blake proposed the SMT filter and then **removed** it mid-transcript. Zarb makes it mandatory and calls it confluence #2. Two independent sources, same base model, opposite calls on the same filter. Cheap to settle. |
| **Reported edge** | 🔑 **+0.187R to +0.196R across both multi-month samples** — statistically indistinguishable from the already-holdout-confirmed London book (+0.221R Block A / +0.177R Block B). The payouts are bigger; the *edge* isn't. |

---

## 8. If anything gets tested, this is the order

Ranked by information per unit of effort, not by how exciting it is.

1. **The midnight-open retracement (B.6).** One afternoon, binary answer, third-party-quantified prior to beat, NY session, no new data. The cheapest real question in the corpus. It is also a pure *bias filter* — it composes with existing triggers rather than replacing them.
2. **The Golden Rule as a bias filter (B.5).** Not what the failed-auction census killed. Measurable as a conditional lift on the existing NY population with zero new ingestion. Must clear proximity-matched placebos.
3. **SMT divergence as a filter on the PB Blake population.** Settles Blake-vs-Zarb on the one point where they disagree, and rides infrastructure already being built.
4. **Model A — do not build.** Asia NQ is closed, the entry grammar is wrong, and §5 shows the published mechanics are negative-EV at his own reported win rates.
5. **Model B as a standalone model — do not build separately.** Fold the distinct pieces (SMT, the 1h-zone/5m-structure/1m-entry pairing convention, the front-run-the-target exit) into the PB Blake work as variants.

**Worth carrying forward regardless of what gets tested:** the VP settings block in §3, because it is exact, and the sessions=All / 68% / 30m-read combination is a genuinely different level set from the one already censused.
