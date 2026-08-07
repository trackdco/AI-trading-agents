# Open questions — 1m MNQ displacement setup (v1)

Companion to `docs/constitution.md`. Nothing here has been substituted or defaulted; every item below blocks or bounds the constitution until the owner supplies a value.

## A. Unresolved parameters (owner asked, no value given)

| ID | Parameter | Where it bites | What was asked |
|---|---|---|---|
| OPEN-1 | Range ×ATR multiplier `k` | S3 — the core displacement threshold. **The blocking parameter: no signal can be computed without it.** | Asked three ways: direct multiplier menu ("idk"), point-size elicitation ("it changes"), quantified ladder 2×/3×/4× ("I can't pick one"). |
| OPEN-2 | Wall persistence window `M` (minutes) | L3 | Menu 5/15/30/Other — "Other / can't pick", no value typed. |
| OPEN-3 | Trades per session + new-signal behaviour while order pending / position open (incl. opposite-direction signal during a trade) | F1 — the backtest cannot iterate a session without this rule. | Menu offered; "Other" selected, no text typed. |
| OPEN-4 | Skip conditions (news windows or other stand-aside rules) | F2 | Menu offered; "Other" selected, no text typed. |
| OPEN-5a | May the 09:30–09:31 candle use the 09:29 pre-market bar as its gap reference (S4)? | S5 lower edge | Bundle offered; "Type my own" selected, nothing typed. |
| OPEN-5b | Last candle eligible to fire a signal | S5 upper edge | Same. |
| OPEN-5c | Does a trade exactly AT the liquidity level count as "taken" (E3), or is 1 tick through required? | E3 cancel rule | Same. |

## B. Pins surfaced during drafting that were never asked (would-have-invented list)

Listed instead of chosen — each needs an owner decision before coding:

| ID | Item | Why it matters |
|---|---|---|
| OPEN-6 | ATR14 evaluation bar: does the ATR window end at `P`, or include `C` itself? | Including `C` makes the candle partly its own normaliser; the two versions fire on different candles. |
| OPEN-7 | Reference price for "nearest pivot high above" (L2): above `close(C)`, or above `high(C)`? | Changes which level is the target and whether a level exists at all. |
| OPEN-8 | "Average visible level size" basis for the wall test (L3): which book levels (how many deep), one side or both, sampled at what cadence? | The 3× multiple is meaningless until the denominator is defined. |
| OPEN-9 | Take-profit order offset at the wall: TP limit exactly at the level, or in front of it? | Constitution currently says exactly at the level (as answered); fill probability at a wall is queue-dependent — flagged for the fill model, but the price itself is a rule. |

## C. Interrogation log

Every question asked, in order, with outcome. PINNED = value in constitution; OPEN = above; SUPERSEDED = replaced by a later answer, both retained.

**Batch 1** — Size metric (range/body/both): **both** — PINNED (S2/S3). Normaliser family: "not sure" — re-asked B2′. Bullish definition incl. doji: **close > open strict** — PINNED (S1).

**Batch 1′** — Normaliser re-asked behaviourally: **vs recent average size (ATR family)** — PINNED (S3 family).

**Batch 2** — Instrument: **MNQ** — PINNED. Signal timeframe: **1-minute** — PINNED. Entry timeframe: **same** — PINNED. Session: **NY morning 09:30–12:00** — later SUPERSEDED by 09:30–10:30 (Batch 9).

**Batch 3** — ATR lookback: **14** — PINNED. ATR variant: **Wilder** — PINNED. ATR feed: **all 24h bars** — PINNED. Range multiplier: "idk" — re-asked.

**Batch 3′** — Displacement size in points: "depends on the day" — no value. Normal candle size in points: "IDK it changes" — no value. Body rule form: **% of range** — PINNED.

**Batch 3″** — Multiplier ladder 2×/3×/4×: "**I can't pick one**" — OPEN-1. Body %: **≥ 70%** — PINNED (S2).

**Batch 4** — Streak: **single candle** — PINNED (S6). Gap: **open gap** — refined in Batch 5. Structure break: **none** — PINNED (S6). Volume filter: **none** — PINNED (S6); owner's earlier "depending on the volume on the day" confirmed as volatility description, not a rule.

**Batch 5** — Gap reference: **prior candle's high** (chosen with the stated rarity warning) — PINNED (S4). Gap arithmetic: **> by ≥ 1 tick** — PINNED (S4). Close-location: **nothing stricter** than the top-30% implied by S1+S2 — PINNED (S6).

**Batch 6** (first presentation dismissed by owner; re-presented on instruction) — Entry type: "depends… limit at 50% if really big" — vague, restructured in Batch 7. Stop: **low − 1 tick** — PINNED (X1). Stop floor: "should never be that small" — belief, not a rule; forced binary in Batch 7. Contract cap: **none** — PINNED (Z5).

**Batch 7** — Entry structure: **always limit at 50%** — PINNED (E1); the "really big" branch dissolved. 50% of what: **range** — PINNED (E1). Order life: "until first draw of liquidity is taken" — new undefined term, interrogated in Batches 8–10. Stop-floor binary: **trade it** — PINNED (Z4).

**Batch 8** — Liquidity definition: "next high or low, match with heatmap liquidity wall" — decomposed in Batches 9–10. Target: **the liquidity level** — PINNED (X2). Management: **none** — PINNED (X4). Time exit: "9:30–10:30" — conflict flagged, resolved Batch 9.

**Batch 9** — Window conflict: **all activity 09:30–10:30** — PINNED (S5, X3); prior 09:30–12:00 SUPERSEDED. Next-H/L definition: **pivot** — PINNED (L1 form). Wall recognition: **size multiple** — PINNED (L3 form). No qualifying level: **skip** — PINNED (L4).

**Batch 10** — Pivot N: **3** — PINNED (L1). Wall multiple k: **3** — PINNED (L3). Wall measurement: **averaged over window** — form PINNED, M = OPEN-2. Match tolerance: **≤ 5 points** — PINNED (L3).

**Batch 11** — Wall window M: no value — OPEN-2. Frequency/overlap: no value — OPEN-3. Skips: no value — OPEN-4. Edge-case bundle: no value — OPEN-5a/5b/5c.

## D. Corrections and notes for the eventual prereg (not rules)

- **Correction on the record**: interrogator initially mis-stated NQ contract economics as "$5/point" in a Batch 2 option description ($5 is per tick; NQ = $20/point, MNQ = $2/point). Corrected before any rule used it; constitution Z2 uses $2/point MNQ.
- The gap condition S4 was chosen with an explicit rarity warning (true 1m gap-ups in RTH are scarce). Expected consequence: very low signal frequency. This is the owner's deliberate choice, not an accident — but sample-size implications (events per era, n_eff) will bind at prereg time.
- L3 requires historical order-book depth at minute-or-finer resolution over the full test span. Constructibility against the repo's current holdings (minute-sampled, book-only, ~2h/day condensed MBP-10 extracts) has NOT been assessed here and must be triaged before prereg (CLAUDE.md §4) — the "sustained over M minutes" clause in particular may exceed the data's resolution.
- Bar-label convention of the 1m OHLCV source must be settled empirically before S4/S5 are coded (CLAUDE.md §7.1, defect #3).
- Fill model (limit at E1, TP at a wall, stop-market slippage), cost stacks, and the decision-time window table are prereg items, deliberately absent from the constitution.
