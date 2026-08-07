# Strategy extraction — "Trader Kane / Lab Model" entry mechanisms

**Status: SHELVED — not pursued. Owner decision, 2026-08-07, at triage stage, before any prereg or test was run. Reasons on record: no trustworthy evidence in the sources, edge likely resident in unformalisable discretion, 13-item looseness ledger implying a heavy multiple-comparison penalty, and an ES data purchase required for the core trigger. No holdout was touched; no search was run; no span was consumed. This document remains as the record of the triage.**

**Originally: HYPOTHESIS MATERIAL. Not a prereg. Nothing here is validated. No number in the source video is evidence.**

## 1. Provenance — read before using anything below

This is a **third-hand reconstruction**:

1. Trader Kane's actual model lives in his paid group ("The Lab") and is not public.
2. FX Replay (a backtesting-software vendor) reconstructed it from Kane's free YouTube/X/Reddit material and presented it in a promotional stream: "Backtesting Trader Kane's NQ Strategy | The Lab Model" (youtube.com/watch?v=3rdUZEbKSRA). The host states on-record: *"I've picked up as much as I can from totally free publicly available info, but I'm sure there's maybe a few nuances… I am not in his Lab discord."*
3. This document is extracted from that video's transcript (full text: not committed; retrieval route noted in session log), cross-checked against FX Replay's and TradeZella's written strategy pages, which repeat the same reconstruction.

Consequences:
- Any backtest built from this document tests **our formalisation of FX Replay's reconstruction**, not Kane's model. Results — good or bad — say nothing about Kane.
- Several components are explicitly discretionary in the source. Per standing instructions (CLAUDE.md §1), the looseness is **logged in §6, not tightened**. Every mechanical variant we later choose is a declared trial arm, counted in the multiple-comparison denominator.

## 2. Instruments, timeframes, window (as described)

| Item | As described in source |
|---|---|
| Traded instrument | NQ only |
| Reference instrument | ES — used solely for SMT divergence, never traded |
| Range/target timeframes | 4H, 1H, 5m (premium/discount ranges drawn on all three) |
| Execution timeframes | 1m, 3m, 5m (host also mentions 15m once); choice per-trade is discretionary |
| Session window | 10:00–13:00 ET, "after the 4-hour candle closes at 10:00 a.m." — host's preferred window; Kane also trades London and PM |
| Attempts per session | Max 2 attempts (host's mechanisation of Kane's habit); "pretty much done after a win" |

Note the 4H-close-at-10:00-ET premise implies a specific chart anchoring (equity-session-anchored 4H candles, not midnight-UTC). This is a **convention that must be settled empirically** before any window table is written (CLAUDE.md §7.1).

## 3. Concept definitions (as used by the source)

- **Range / leg**: a directional impulse from a swing high to a swing low (or inverse). Drawn by eye in the source. No mechanical swing definition is ever given.
- **Balanced / unbalanced**: a range is *balanced* once price has retraced to its 50% midpoint (fib 0.5); *unbalanced* until then. Unbalanced higher-timeframe ranges act as the *draw on liquidity* (directional bias), *not* as an entry filter — the source is explicit that this inverts the common ICT premium/discount usage: midpoints are **targets**, not filters.
- **LLT (logical liquidity target)**: "the first low beyond the discount, or the first high beyond the premium" — i.e. the first swing low past the 50% midpoint (for shorts; inverse for longs). Primary take-profit.
- **SMT divergence**: at a comparable swing, one of ES/NQ makes a new high/low and the other fails to. Marked by eye in the source; repeatedly qualified as "clear"/"obvious" with marginal cases rejected visually. Invalidated when both instruments subsequently make the new extreme.
- **FVG / IFVG**: fair value gap = 3-candle non-overlap gap; *inverse* FVG = an FVG that a candle then **closes** back through ("inversion"). The only crisply mechanical concept in the whole model.

## 4. Trigger A — Reversal

Conditions, in the order the source states them:

1. A higher-timeframe range (4H or 1H) is unbalanced → expected rebalance toward its midpoint defines trade direction.
2. The 10:00 ET 4H candle has closed.
3. **Sweep**: price takes out the reference extreme (the source uses "the 10 a.m. low" in the long example; the 4H high in the short example) on **either** ES or NQ.
4. **SMT divergence** between ES and NQ at that extreme.
5. **IFVG**: an FVG on the chosen execution timeframe (1m/3m/5m) is inverted (candle close through it). Order of (4) and (5) does not matter; if SMT arrives second, an earlier inversion may be reused.
6. **Entry**: limit order at the retest of the inverted FVG. Variants stated: stop-limit at the inversion when price is moving fast; or entry on a 1m close confirmation.
7. **Stop**: the recent swing high/low **or** the SMT-invalidation extreme (both stated as acceptable; occasionally "the overall high").
8. **Target**: the LLT of the most recent relevant leg ("base hit"), even when the higher-timeframe midpoint is further away.

## 5. Trigger B — Continuation

1. Higher-timeframe range unbalanced → draw still pointing in trade direction.
2. A **lower-timeframe range (5m) has already balanced** (retraced to its own midpoint) — this retracement into balance is the pullback being continued from.
3. Then the identical micro-trigger: SMT + IFVG on the execution timeframe.
4. **Target** — three stated options, choice discretionary: (a) LLT of the local leg, (b) a new low/high (e.g. resting relative-equal lows), (c) the higher-timeframe midpoint. The host additionally used a "power of three" variant: 4 standard deviations of the manipulation leg, attributed to Kane "in multiple videos".
5. Stops/entries as Trigger A.

Source's own observation: continuations tested markedly higher-probability than reversals in his (tiny) sample.

## 6. Looseness ledger — underdefined points, logged NOT resolved

Each of these must be either mechanised as a **declared trial arm** or dropped; none may be silently defaulted:

1. Swing definition underlying *everything* — ranges, legs, SMT, LLT, stops. Never defined. This is the load-bearing gap: legs and swings are marked by eye, after the fact.
2. Which execution timeframe's FVG to use (1m vs 3m vs 5m) — "up to you"; host switches per-trade.
3. Whether adjacent FVGs may be merged — "he doesn't usually combine them… I do."
4. What qualifies as "clear" SMT vs marginal — rejected by eye; no rule. Also: which swing pairs are comparable across the two instruments.
5. Minimum FVG size — host speculates small gaps are lower-probability; no threshold exists.
6. Stop placement — recent extreme vs overall extreme vs SMT-invalidation level.
7. Continuation target — 3 options + std-dev variant.
8. Break-even — "very discretionary" (Kane refers to 15m lows, distance travelled); the halfway-to-TP rule used in the video is **the host's invention**, explicitly labelled as such.
9. Sweep reference — which prior extreme counts (10:00 low, 4H high, session high…), and whether a wick suffices or a close is needed.
10. Entry order type on fast inversions — limit vs stop-limit vs close-confirmation; host freelances per-trade.
11. Window — 10:00–13:00 ET is the host's testing preference, not Kane's rule.
12. Higher-timeframe SMT veto (skipping days where daily/weekly SMT opposes the trade) — the host's own overlay, explicitly not sourced to Kane.
13. "Two attempts max / done after a win / no more than two losses" — approximated from observation, not a stated rule.

## 7. Audit of the evidence offered in the source video

None of the following survives our standards (CLAUDE.md §2, §8):

- **n = 14 trades**, hand-traded in a replay simulator with live discretion (timeframe choice, SMT acceptance, target choice, break-even timing all varied per-trade). Not reproducible, therefore not testable.
- Reported results — 54% win rate, ~3.14R average target, 3 break-evens, "nice equity curve" — are in-sample by construction, produced by the person who had already "done some testing" on the model. The viewer-supplied start date does not sanitise this: the operator's discretion embeds prior exposure.
- The **risk-reward-simulator findings** (e.g. "1R base hits on reversals → 80% win rate, higher profit factor") are post-hoc re-optimisation on **n = 5**. The host himself flags overfit; we treat it as pure tuning.
- **No cost model exists anywhere** in the video. No commissions, no slippage stack; only a remark that futures spreads are tight. Every R figure is gross.
- **Fill realism is decisive and unmodelled**: entries are limit retests into 1m-scale IFVGs with stops as tight as ~48 ticks; several trades hinge on whether a retest tags a limit before departure ("this one might take off without us"). At this scale, at-fill anchoring, same-bar stop/target ordering, and queue position (defect catalogue #4–#7) dominate outcomes.
- **Hindsight-defined predicates**: SMT and "balanced range" are drawn on completed swings. A swing high is only knowable after later bars confirm it. As drawn, the decision-time of these conditions is **after** the entries they justify. Any mechanical version needs an explicit confirmation lag in the window table, and the confirmation lag changes the strategy.
- **Selection context**: Kane's credibility is asserted via Apex payout leaderboards (~$2M). Prop-firm leaderboards are a survivorship filter over a large entrant population; they are not audit evidence of edge. Separately, the reconstruction is published by a vendor whose product the video demonstrates. Neither point falsifies the model; both mean the burden of proof is entirely on our own testing.
- **A direct audit of Kane's own account/channel was not possible from this environment** (YouTube blocks datacenter access; his channel page is unreachable). Claims about his live 100K–1M accounts are UNVERIFIABLE from here and remain so until primary material is supplied.

## 8. Constructibility triage against this repo's data (CLAUDE.md §4)

Current holdings: NQ ohlcv-1m (GLBX, 2023-01 → 2026-01, outrights **and calendar spreads in the same files** — defect #9 applies, front-month filtering required before anything else); NQ MBP-10 condensed (2025-06 → 2026-07).

| Component | Verdict | Notes |
|---|---|---|
| ES leg of SMT divergence | **NOT CONSTRUCTIBLE** | **We hold no ES data of any kind. SMT is the core trigger; without ES the strategy as described cannot be tested at all.** Fix: purchase ES ohlcv-1m (GLBX) for the matching span — a purchase decision, not a coding one. |
| 4H/1H/5m ranges, midpoints, LLTs | VALID (derivable from 1m) | Only after bar-label convention and session/4H anchoring are settled empirically (§2 note; defect #3). Requires a declared mechanical swing definition (looseness item 1). |
| FVG / IFVG on 1m/3m/5m | VALID | Equality/doji cases must be handled explicitly (defect #12). |
| Limit-retest fills, stop-limit entries, tight-stop outcomes | BIASED on 1m OHLCV / VALID on MBP-10 span | On 1m bars alone: bound both orderings, stop-first on same-bar conflicts (defects #6–#7). Tick-accurate only on 2025-06 → 2026-07 where MBP-10 exists. |
| 10:00–13:00 ET window | VALID | Timezone/DST conventions file first. |
| Break-even / trailing management | VALID mechanically | But every variant is a trial arm; the halfway rule is the host's, not Kane's. |

## 9. Gate before any backtest

Per CLAUDE.md §7, none of the repo's required infrastructure exists yet (conventions file, chokepoint loaders, clock assertions, JSONL ledger, prereg template). That work precedes any test of this or any other candidate. Specific to this candidate, the blocking items are:

1. **ES data purchase** — hard blocker for the SMT leg. Decision needed.
2. Mechanical swing/leg definition declared as trial arms — without it, ranges, SMT, LLTs and stops are all undefined.
3. Confirmation-lag rule for swing-based predicates, with the full (condition, decision-time) window table in the prereg.
4. Front-month filter for the OHLCV files (spreads share the feed).
5. Cost model (two stacks) — the source offers none.

Until those exist, this document is the deliverable: a raw-trigger inventory with its provenance and its holes on record.

## 10. Primary-source channel audit — youtube.com/@traderkane (retrieved 2026-08-07)

Full channel inventory at retrieval time: **8 videos**. Transcripts of all 8 were retrieved and scanned.

| Video ID | Title | Views |
|---|---|---|
| yLJMKtFphNM | The Real Story of Tradeify (fireside w/ founder) | 6.6k |
| QeS16NgB5oU | The Real Story of Lucid Trading (fireside) | 8.3k |
| dQcT_vmg7Qs | why you suck at trading prop firms (whilst I've profited $2.5M) | 37k |
| rtxG1DQ2Z6Y | before you quit your job to trade, watch this | 23k |
| UoIlbmzuXyw | the brutal truth about the trading industry | 30k |
| HPNztQD9bl0 | it was fun... I'm done | 29k |
| l65oghvEt84 | Coffee & a chat on why you suck at trading | 39k |
| WQvjW0xUkRM | 2024 was tough.. but the best yet | 17k |

### 10.1 Scan result: the channel contains essentially no strategy mechanics

A keyword scan (SMT, inversion, FVG, rebalance, midpoint, LLT, premium/discount, PO3, standard deviation, …) produced **1 hit across all 8 transcripts combined**. Known-positive validation per CLAUDE.md §1: the identical pattern fires **174 times** on the FX Replay reconstruction transcript, so the scan works and the absence is real. His YouTube is prop-firm commentary, firesides and recaps; the model itself lives in the paid Lab, his X feed, and livestreams. **The §4–§5 reconstruction therefore cannot be corroborated from his channel; his X feed is the next primary source.**

### 10.2 Fragments that do bear on the reconstruction (his own words)

- **Timeframe stack** (l65oghvEt84, answering a viewer): *"time frame alignment for the lab model — 15 minute for standard deviation, 3 minute for entry, an hourly for premium discount — is that valid? Seems pretty valid."* Partially corroborates §2 (1H premium/discount, low-TF entry) and puts the std-dev/PO3 leg on the **15m**, which the FX Replay reconstruction never specifies.
- **Base-hit character** (l65oghvEt84): *"my model is very very short-term bias — it just wants to get in that move and get out."* Corroborates the LLT/base-hit framing.
- **Capped-target overlay** (dQcT_vmg7Qs): during the first ~50 days of the big Apex account — where he says ~95% of that account's profit was made — he *"took basically the same trade every day"* with take-profit = **min(model TP, 100 ticks)**. This overlay appears nowhere in the FX Replay reconstruction. Candidate trial arm if the model is ever tested.
- **Win-rate tension** (dQcT_vmg7Qs): *"My model isn't a high win rate model."* This sits against the FX Replay video's 54% (n=14) and the host's stated preference to keep win rate above 50%. Unresolved; lowers confidence in the 54% figure describing Kane's actual distribution.
- **Regime self-description** (yLJMKtFphNM): he says he thrives when *"we're rangebound, we're consolidating, not really going anywhere"* and has not made his big money in strongly trending tape. Consistent with a rebalance-to-midpoint model; suggests a regime split (rangebound vs trending) as a declared arm, and that era stability should be checked across regime shifts.
- **Self-reported de-risking** (HPNztQD9bl0, ~May 2025): not quitting, but *"down-risking a massive amount whilst I get into a new phase of trading, new tools, new risk"* during choppy Fed/tariff conditions — his own usage of the model is regime-conditional by his own account.

### 10.3 Account-claims audit

Claimed (dQcT_vmg7Qs): **$2.5M+ total prop-firm profit**, of which **$1.86M was one single Apex payout**, plus ~$300K more from Apex (≈$2.23M of the $2.5M from Apex alone).

- **Concentration**: ~74% of the lifetime claim is a single payout event, and ~95% of that account's profit came in its first ~50 days. The headline number is dominated by one short window on one account — it is evidence of one exceptional run, not of a stationary edge.
- **Verifiability**: UNVERIFIABLE from here. No statements, no audited records; prop-firm payouts are not audited track records, and leaderboard visibility is a survivorship filter over a large entrant population.
- **Incentives**: he operates a paid community (the Lab) and publishes prop-firm reviews/referrals (he states he declines some sponsorships; affiliate economics still apply). Standard conflict-of-interest discount applies to all self-reported figures.

None of this falsifies the model. It does mean: the only evidence that will ever count is our own prereg'd testing, and the two channel-sourced arms worth declaring if we proceed are the **100-tick target cap** and the **rangebound/trending regime split**.
