# NYA-OFC-01 — footprint continuation entries (Thraxx, as taught)

**STATUS: NO SLOT ALLOCATED [ANGUS 2026-08-05] — "no strategies to test,
all good. some good findings tho".** Not a kill and not a tombstone: no
prereg was written, no data was touched, no census was run, so nothing has
been measured and no holdout look was spent. The intake is retained as
REFERENCE — the extracted specs, the footprint parameter set and the
credibility audit stand on file.

REOPEN PATH: a free slate slot, or a reason to want the footprint primitives
themselves (the 400%/10-contract imbalance definition and the big-trade
proxy are reusable as FEATURES for any candidate, independent of his entry
models). Anyone reopening starts by reading the declared trap below before
writing a prereg.

Spec: `research/transcripts/thraxx/SPEC-as-taught.md` SPEC 1 (big-trade
continuation) + SPEC 2 (stacked-imbalance continuation), gated by SPEC 3
(his mandatory four-layer context).
Credibility: `research/findings/thraxx-credibility.md` — named trader, ~5yr
footprint, 126 live sessions, published losses; but **paid by the prop-firm
funnel** (Goat Funded referral + Prop Firm Match sponsor). Test mechanics,
ignore every dollar figure.

## Why this is worth a slot

1. **It lands on the substrate our edge already lives on.** Every prior
   intake taught chart geometry. This one teaches tape mechanics — big
   prints, 400% diagonal imbalance, absorption — which map onto
   `data/reference/cvd/footprint_*.parquet` (per-minute, per-price,
   per-side volume and trade counts, 2025-06-01 → 2026-07-19, plus the six
   sealed 2023/24 months at the same coverage).
2. **The primitives are computable from what we hold**, without new data:
   - *Diagonal imbalance* — bid volume at price P vs ask volume at P−1,
     ratio ≥4× with a ≥10-contract floor. Direct from the footprint tables.
   - *Stacked imbalance* — qualifying imbalances on consecutive levels
     surviving the candle close.
   - *Big trade* — a (minute, price, side) cell whose `volume`/`trades`
     ratio indicates a single large print. **Note the limit honestly: the
     footprint tables are aggregated, so exact per-trade size is not
     recoverable — a cell with `trades=1, volume=300` is a 300-lot, but
     `trades=10, volume=300` is not. This is a proxy, and any prereg must
     say so.** Full per-trade reconstruction would need a fresh Databento
     `trades` pull.
   - *Low-volume-pocket filter* — his observation that stacks sit in thin
     parts of the candle's own volume profile. Computable, and a genuine
     secondary hypothesis.
3. **He teaches a stop.** First intake where the stop is not our invention
   (§ RESPEC cross-spec flag: stops were never taught anywhere in the
   Orochi corpus). His structural stop becomes the primary arm; the house's
   capped arms become challengers.
4. **Independent convergence with our own finding.** His claim that
   aggression only counts when measured against price response is the same
   object as §5.12-10 (edge in displacement measured against visible
   liquidity; flow decisive *inside* the trade, near-worthless at entry).

## The trap, declared before anyone runs anything

He states explicitly and repeatedly that both entry models have **no edge
standalone** — they are the last layer after environment, location and
session path. **A raw census of unfiltered big-trade or stacked-imbalance
triggers will return a negative, and that negative will be worthless.**
This repo has already burned that mistake twice (nya-ivb killed twice by
strawman censuses then vacated on canon-parity; NYO-ROT-01 trial 1
vacated). Per §5.9.1 the taught trade is tested WITH its mandatory
triggers. Either the SPEC-3 gate is implemented or the census does not test
his teaching.

## Known blockers to settle in the prereg

- **Gamma/GEX is not computable** — we hold no options data. It is part of
  his layer-3 context. Declare a documented N/A per §5.11-6; do not drop it
  silently.
- **Contract-size translation.** Every threshold he gives is MNQ-scaled
  (big trade ≥300). An unscaled port to NQ changes the filter by 10×.
  Declare both scalings plus a percentile variant — §5.12.1-15 warns
  absolute size thresholds are regime-sensitive (book thickness moved 1.45×
  inside our own fit span).
- **BE is his default management and our thrice-beaten null** (§5.12-6).
  His BE rule must defeat the null, not inherit it.
- **Depth covers 08:00–10:29 ET only** — his NY-open trades sit inside
  depth cover, afternoon trades do not.
- **No claimed base rate exists.** He never states a win rate, expectancy
  or sample size for either model. There is no number to falsify, only
  mechanics to measure — which also means no "his stat vs our stat"
  refutation rung is available (unlike NYA-IB50-01's 73% claim).

## Suggested shape if a slot opens

Stage 1 would be a two-part census: (a) the **primitive census** — how
often do qualifying big trades and stacked imbalances occur, and does the
two-candle acceptance sequence follow? This is the structural-existence
question §5.9.1 reserves the census kill for. (b) the **gated census** —
the same events inside a mechanized SPEC-3 gate, which is where any real
signal would live. Uncapped, both legs, per the standing convention.
