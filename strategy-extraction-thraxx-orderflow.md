# Strategy extraction — "Thraxx" order-flow entry mechanisms (@thraxxtrades)

**Status: HYPOTHESIS MATERIAL. Not a prereg. Nothing here is validated. No number in the source channel is evidence.**

## 1. Provenance

Materially better than the Kane/Lab case: this is **first-person source material**. The trader (handle: Thraxx, @thraxxtrades) publishes his own playbook on his own channel, streams his trading daily, and the mechanism videos are him describing his own entries — one remove from the strategy (his telling of it), not three. Retrieved 2026-08-07: full channel inventory (43 videos), transcripts pulled for 12 mechanism videos and 6 account-recap videos. Key sources:

| Video ID | Content used |
|---|---|
| raCTiS4RNno | 2 continuation entry models (big trades; stacked imbalances) — read in full |
| k41nIqVZaTg | Absorption reversal entry model (footprint POC + delta flip) — read in full |
| tm6qCMItaNw | Four-layer framework (environment/location/path/confirmation) — read in full |
| y11pylpC-5M | Premium/discount definition (fib 0.5 / 0.705 / 0.788 / 0.886 on active range) |
| 34MhSJsRF_M | FVG quality filter (intra-gap volume) |
| luMedeeFVug, zT5jcvUM6iU | GEX/gamma as regime context; pre-market mapping |
| WijZ8zXfM1A, yaCl9GYRzW4, xVQfTZToWo4, W34h3mWB4Oo, pkAPZQtCuAA, n0S7hjDr4nM | Account claims (§7) |

Caveats that remain: it is still self-description (what traders say they do and what they do diverge), the channel is monetised (Prop Firm Match sponsorship, ATAS affiliate links), and his own repeated framing is that the entry models "have no edge on their own" — the discretionary layers 1–3 carry the trade selection.

## 2. Instruments, platform, session

- Trades **NQ / MNQ** futures on prop-firm accounts (Topstep, Apex, Lucid and others mentioned by name).
- Footprint/order-flow platform: **ATAS** (bid/ask ladder footprints, per-candle volume profile, stacked-imbalance indicator, delta).
- Session framework: Asia builds the initial range/balance → London probes/manipulates it → New York resolves the move. Trades the NY morning; **hard personal rule: no trading after 8:00 a.m. Pacific (11:00 ET)** — breaking it is what blew his accounts (§7).
- Execution timeframes seen: 5m primary, 15m and 3m variants.

## 3. The four-layer framework (his stated order of operations)

Entries are explicitly the **last** layer. His words: "the entry model is the least important part of the trade."

1. **Environment** — expanding vs compressing, trending vs rotating vs chopping; where the higher-timeframe draw is; did a meaningful level get swept or are we stuck in balance.
2. **Location** — premium/discount via fib retracement on the "active range": levels 0.5, 0.705, 0.788, 0.886; the **0.705–0.886 zone** is the reversal/responsive sweet spot; a **close beyond 0.886 invalidates the range** read (then expects the 1.1 extension). A fixed-range volume profile narrows a focus zone inside the fib zone; premium/discount also read relative to value area.
3. **Path** — session sequence (did London take one or both sides of Asia; did pre-market already complete the move) plus **gamma regime as context only**: positive gamma → baseline expectation of rotation/pinning; negative gamma → expansion/cleaner directional follow-through. Explicitly "not a trade signal."
4. **Confirmation** — the order-flow entry models below. Any layer missing → no trade.

## 4. Entry models — raw triggers as described

All three share one governing concept, **acceptance**: the print (big trade / stack / absorption) is not the signal; the market's reaction on the revisit is. All are **two-candle patterns**: a confirmation candle that must CLOSE (prints can vanish intra-candle), then an execution candle that pulls back and flips.

### Model A — Big-trade continuation

1. Bias/location/path already aligned (layers 1–3).
2. A **big trade** prints in bias direction — single execution above a size filter (his MNQ filter: **minimum value ≥ 300**; small filters are "just noise") — and sits **deep in the candle body, not at its extreme** (deep placement = follow-through occurred after the print).
3. The candle **closes strongly** beyond the print (e.g. breaks out of the chop range).
4. Execution candle pulls back into the big-trade price zone; opposing aggression **stalls/fails** there (for shorts: buyers fail to push through); pressure **re-engages in trade direction** (candle flips) → enter.
5. Stop: other side of the big trade / its candle, with buffer. Target: contextual (examples used 2R).
6. Management: stop to break-even once the next 5m candle takes out the prior 5m candle's extreme in trade direction; optional trail near target.
7. No pullback → no trade ("if it just goes, I let it go"). A later revisit of a still-fresh level can re-arm the setup.

### Model B — Stacked-imbalance continuation

1. Layers 1–3 aligned; explicitly a **higher-momentum-environment** model.
2. An **extreme** stacked imbalance prints (ATAS indicator: one-sided bid/ask imbalances stacked across multiple consecutive price levels). **Wait for the candle to close** — stacks can disappear while forming. Weak/partial stacks are excluded ("stacked imbalances are incredibly common, and that alone makes them dangerous").
3. Typical corroboration: the stack sits in a **thin/low-volume pocket** of that candle's own volume profile.
4. Execution candle pulls back into the stack zone, opposing pressure fails, flips back in direction → enter on the retest.
5. Stop: other side of the candle that created the stack (tight by design). Invalidation: clean acceptance back through the imbalance ("price should not accept back through this area").
6. Break-even move on renewed aggression in trade direction, discretionary by proximity to "danger zones."

### Model C — Absorption reversal (footprint)

1. A **pre-marked key area** is mandatory ("absorption in the middle of nowhere doesn't mean much"): prior-day H/L, equal highs/lows, the 0.705–0.886 fib zone, a quality FVG, a GEX level.
2. Price tests the area; aggressors in the prevailing direction hit into it and **fail to progress** (aggression without price progression = absorption).
3. Confirmation candle **closes** with its **POC in the wick beyond the body** (abnormal — POC sits in the body "80% of the time"), on the **aggressor's side of the ladder** (short setup: POC on the ask at the highs; long: POC on the bid at the lows). POC on the wrong side = the "aggressors" aren't really aggressing → not absorption → no trade.
4. **Delta flip** (candle delta sign change with meaningful magnitude) on the absorption candle or the next candle. Entry without the flip is stated as permissible but lower-probability.
5. Entry: **limit order 1–2 points before the absorption candle's POC**, filled on the retest.
6. Stop: other side of the absorption zone/candle. Invalidation: price closes through the zone.
7. Target: minimum 1:2 R, or structural (session/London highs etc.).

### FVG quality filter (used for Model C areas)

A displacement candle is only a valid FVG if the move is genuinely **inefficient**: thin participation / low-volume nodes inside the gap on its volume profile. Displacement **with** two-sided volume is "displacement with acceptance" — the market traded through, didn't skip — and is excluded. This is a mechanically checkable filter (given trade data) and the most novel crisp idea on the channel.

## 5. Looseness ledger — logged, not resolved

1. "Active range" anchors for the fibs — swing selection is by eye; re-anchored when new extremes print. Same hindsight-swing problem as every discretionary model.
2. Big-trade threshold: stated for MNQ (≥300 value) but "at least"; NQ equivalent, and whether value = contracts or notional, unstated.
3. "Extreme" vs "weak/partial" stacked imbalance — no ratio, no stack-depth number (ATAS defaults implied but not stated).
4. "Strong close" after the big trade — undefined.
5. "Deep in the body" — no quantitative placement rule.
6. Delta-flip magnitude — "big difference in change," session-relative (Asia vs NY), no threshold.
7. POC "in the wick" — boundary case (POC at body edge) undefined.
8. Which key-area types rank above others for Model C; how far a retest may drift before staleness.
9. Targets — "whatever you're targeting"; examples use 2R/1:2 minimum but structural targets override ad hoc.
10. Break-even/trailing rules — stated patterns (prior-5m-extreme rule; aggression-failure exit) but applied "depending on location."
11. Layers 1–3 in their entirety — environment reads, session-path reads, gamma regime: all judgment. He is explicit that these carry the edge, which means **the tradeable content of the system is mostly outside the mechanical triggers**.
12. Re-arm rules for missed entries (how much later a revisit still counts).

## 6. What is genuinely testable here

Unlike the Kane case, the micro-mechanisms are close to mechanisable *given the right data*: big-trade prints, stacked imbalances, per-candle POC location and side, delta flips, and the FVG-volume filter are all objective functions of trade-by-trade data with aggressor side. The four construction-validation checks (CLAUDE.md §4) apply cleanly: each feature (absorption, stack, big-trade follow-through) can face a positive control, shuffle placebo, time-shift placebo, and parameter ladder **before** any edge question. His own null hypothesis is on record — "these have no edge on their own" — which makes an honest first experiment: *do the mechanical triggers alone carry anything, or is the claimed edge entirely in the discretionary layers?* Either answer is informative.

## 7. Account-claims audit

**More transparent than any comparable channel we've audited** — losses, fees, tilt and blown accounts are documented on-channel, often same-day. Still: all self-reported, no third-party verification.

Claimed figures from recaps: Jan payouts **$12,369** (post-split, single 50k Topstep account; ~$1,168 fees; ≈$11.2k net pre-tax; title claims +$31,777 PnL), Feb **+$18,909** payouts, Mar **+$10,848** payouts, Apr "worst month in a long time," early May: **blew every funded account (−$18,000 in two days)** — his own telling: broke his no-trading-after-8am-PT rule, tilted, lost a $7,300-balance anchor account inside an 88-point range day; the "12-month win streak" (title claim) ended there. Separately lost a $500→$10K small-account challenge.

Structural observations:

- **Scale**: credible five-figure monthly payouts, i.e. an order of magnitude below the Kane headline — and correspondingly more plausible.
- **The "fullport" strategy is an EV play on prop-firm economics, not trading edge**: he deliberately max-risks cheap evaluations because their rules are "gamified" — variance manufactures funded accounts at $100–300 per blown eval. This means monthly payout totals can be positive even with modest trading edge; payout figures ≠ strategy P&L. He is candid about exactly this (and warns it "will destroy you" without an edge).
- **Behavioural risk is documented by him**: two channel-documented tilt episodes destroyed months of accumulation. Whatever the entry models are worth, the account outcomes are heavily governed by rule adherence, not the triggers.
- Sponsor/affiliate incentives exist (Prop Firm Match, ATAS) but the loss-transparency partially offsets the usual promotional discount.

## 8. Constructibility triage against this repo's data

**Central finding — checked empirically, not assumed**: the repo's MBP-10 "condensed" files were inspected (one full read per variant + 8 random files across the 2025-06 → 2026-07 span). Every file is a **~120–150-row, minute-sampled, book-only extract (actions A/C/M only — zero trade messages), covering only a ~2–2.5h window per day**. There is **no trade-by-trade data with aggressor side anywhere in the repo**.

| Component | Verdict | Notes |
|---|---|---|
| Big trades, footprint ladders, delta / delta flips, per-candle POC + side, stacked imbalances, per-candle volume profile, FVG volume filter | **NOT CONSTRUCTIBLE** | All require tick-level trades with aggressor side. Fix: purchase GLBX trades (or full MBP-10) for NQ/MNQ over the target span — a purchase decision. Sign convention must then be settled empirically (defect #10). |
| Absorption from the condensed book snapshots | **NOT CONSTRUCTIBLE — and dangerous to fake** | Minute-end book states are post-trade residuals (defect #14); differencing them conflates cancellation with execution (defect #16). Do not proxy. |
| Fib levels / active-range premium-discount, session windows, 0.886 invalidation | VALID from 1m OHLCV | After bar-label/timezone conventions are settled and a mechanical swing rule is declared (arms). |
| Structure-only FVGs (without the volume filter) | BIASED | Computable, but his whole point is that structure-only FVGs are the *wrong* ones; label as proxy, bias = includes accepted displacement. |
| GEX / gamma levels | **NOT CONSTRUCTIBLE** | Requires options open-interest/dealer-positioning data (external vendor); no options data held. Omitting it changes layer 3. |
| Session-path logic (Asia/London/NY ranges, sweeps) | VALID from 1m OHLCV | Same conventions caveat. |

**Additional gate**: CLAUDE.md §6 requires the **orderflow-construction** skill before building or debugging any order-flow feature. It is not installed. Under standing instructions it must be built before any construction work on Models A–C begins, regardless of data purchases.

## 9. Gate before any backtest

Repo-wide prerequisites (chokepoint loaders, conventions file, clock assertions, ledger, prereg template — CLAUDE.md §7) still don't exist. Candidate-specific blockers, in order:

1. **Tick-level trade data purchase** for NQ/MNQ (hard blocker for every entry model). Decision needed.
2. **orderflow-construction skill** built/installed (standing-instruction gate).
3. Mechanical swing/active-range definition declared as arms (shared blocker with the Kane candidate).
4. Aggressor-sign convention verified empirically on the purchased data before any delta/footprint feature (defect #10).
5. Construction-validation battery per feature (positive control, shuffle, time-shift, ladder, era stability) **before** any edge question — most flow failures are construction failures.
6. Cost model: his stops are tick-tight by design; fill/queue modelling will dominate results exactly as in the Kane case.

Until then this document is the deliverable: the cleanest first-person trigger inventory we've collected, with its holes and its data bill on record.
