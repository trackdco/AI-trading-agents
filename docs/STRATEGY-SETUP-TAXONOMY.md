# Setup taxonomy — A / B / B2 (authoritative)

Angus's actual entry taxonomy, confirmed 22 Jul 2026. This is the source of truth; the engine
classifier (`src/engine/triggers.py`) implements it. Any earlier "rejection=A, displacement=B"
shape-based description is WRONG and superseded.

## The universal entry mechanism (all three setups)

Enter on a **limit order at the retest of the closest structural level** — POC, a daily-VWAP
deviation band (±1/±2), or the Bollinger MA. Price displaces through the daily POC / level; you
limit into the *nearest* structural level on the pullback. The three setups differ only in the
**context** of the move that precedes that retest — not in the candle shape.

## A — REVERSAL (counter-trend)

Price over-extends to the **±2 daily-VWAP** band (session-anchored, 18:00 ET reset). On an entry
timeframe (1/2/3/5-min) where the **BB MA aligns with the ±1 VWAP** band, a candle **closes
through** that confluence, reversing the extension. Enter on the retest of the closest structural
level. You are fading the extension — "price looks bearish, I see it going up."

- Trigger detail: the close-through must reverse a real ±2 extension. Engine checks the prior
  `_EXT_LOOKBACK=10` entry-TF bars actually **touched/wicked** the ±2 daily-VWAP band
  (within `_VWAP_TOUCH_TOL=0.5`). If yes → `A`; if a displacement with no such extension → `B`.

## B — CONTINUATION (with-trend)

Price over-extends and closes back through a band (e.g. +1), **but** levels are **stacked at the
mid band** — you get the displacement *off that stacked confluence* and it **continues** the
prevailing trend. Enter on the retest. "More than compelling it was going to continue that way."

## B2 — REJECTION / FADE

Price **wicks into** a level, **closes back** (rejects it), and you **fade** off the level — e.g.
after taking out London highs at the open, price rejects the BB MA + VWAP +1; enter on the BB MA
retest, stop above the rejection wick, ride the trend. Works with- or counter-HTF.

## Not part of the strategy

**Order blocks.** They were engine scaffolding (`ob_mid`, E5 book) and are not how Angus trades.
Ignore them for setup classification.

## Engine mapping (for reference)

`src/engine/triggers.py` classifies each trigger: a close-through (`displacement`) → `A` if it
reverses a ±2 daily-VWAP touch in the lookback, else `B`; a `rejection` (wick in, close back) →
`B2`. Cached triggers can be relabeled without re-detection via `scripts/reclassify_triggers.py`
(only the `pattern` label changes; entries/stops are unchanged).

## Order-flow findings tied to the taxonomy (as of 24 Jul, out-of-fit 2025+2026)

- **B2 requires CVD confirmation** — pushed. Pre-market CVD agreeing with direction lifts B2 in
  both years, both books. `path_lo` (session CVD at day lows) is a veto.
- **B needs the tape moving with you into entry** — `conf_last15`; `div15` (price/CVD divergence)
  is a veto. Signals flip sign by window (see docs/DAYREAD-SYNTHESIS-23jul.md): `conf_PM` keeps
  pre-window B, vetoes golden-window B.
- **Windows are separate animals** — pre-market (fills <09:30) and golden (09:30-10:15) agree on
  red/green only 14% of days and need their own rulesets. B2 structurally lives in the pre window.
- **The book is not fixed for the day** — trade both E3 and E4, adapt intraday to what CVD /
  footprint / depth give you. Sticking to one pre-chosen book leaves money on the table.
