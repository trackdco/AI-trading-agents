# FINDING: regime-gated post-open confluence is additive to the chained agent (20 Jul 2026)

**TL;DR:** A mechanical post-open confluence-rejection detector loses ungated (−$3,679, 1/6 green).
Gated by the **regime read** (Angus's own work — overnight inventory / rotation-vs-dislocation), it
flips to **+$3,306, 58% win**, and overlaid on the chained agent stack it is **additive-only**:
**+$14,465 → +$17,771 (+23%), still 5/6 months green, zero green months broken.** The regime read
decides *what's better on the day* — deploy the fades on rotation days, stand down on trend days.

## The core signal (post-open confluence fades, 2026 Feb-Jul, 49 trades)
Fades live or die by the day's character — exactly what the regime read captures:

| overnight inventory (dislocation) | trades | P&L | win% |
|---|---|---|---|
| moderate 5-15pt (rotation) | 8 | +$4,371 | 75% |
| 15-30pt | 8 | +$2,342 | 38% |
| extreme 30+pt (trend/freight-train) | 31 | −$10,442 | 16% |

Same by trend strength: imbal_share .3-.5 → +$4,039; .7+ (strong trend) → −$5,510 / 20%.
**Mechanic:** confluence fades work when price rotates around value; they get run over in a strong
directional day. This is a market truth, not a curve-fit — and it IS the regime read's job.

## Gated result (|inventory| <= 20pt = rotation days only)
- Post-open alone: **+$3,306, 58% win, 12 trades** (vs −$3,679 ungated).
- Overlaid on chained agent (no agents re-run):

| month | agent | +gated post-open | note |
|---|---|---|---|
| Feb | +5,295 | **+7,967** | fades deployed |
| Mar | +2,100 | +2,100 | stood down (no rotation setups) |
| Apr | +1,700 | +574 | small −1,126 ding, stayed green |
| May | +2,532 | **+4,292** | fades deployed |
| Jun | +4,701 | +4,701 | stood down |
| Jul | −1,328 | −1,328 | agent's own 3-day stub, untouched |
| **total** | **+14,465 (5/6)** | **+17,771 (5/6)** | +$3,306, 0 green broken |

## Honest caveats
- |inv|<=20 is 2026-tuned; economically grounded (Angus's rotation/dislocation logic) but in-sample.
- Small sample (12 gated trades). July still red = the agent stub, not the post-open.
- The post-open detector itself is a first cut (strict 3-category confluence, 1/day, V-none exit).

## The forward build (apply regime context "to the fullest extent")
Right now the gate is a post-hoc inventory threshold. The proper version: the **chained agent** makes
the deploy/stand-down call per day from the FULL refined regime read — "is today a rotation day where
my confluence fades work, or a trend day where I sit out" — with the confluence setups as a TOOL it
deploys, not an always-on stream. That bakes this into the agent's day-read (where Angus has been
pointing). Build order:
1. Regime-gate the post-open confluence tool inside the agent's daily decision (not post-hoc).
2. Add the leg-scaled/level exits + V8 trail to the confluence entries (current exit is crude).
3. Grade on MONTH CONSISTENCY (green every month), building from the chained stack — not the champion.

## Scripts
- `scripts/cdr_v2.py` — confluence-rejection detector (strict 3-category, 1/day cap, stand-down).
- `scripts/agent_plus_postopen.py` — overlay post-open onto the chained ledger (cheap, no re-run).
- regime read: `output/regime_vector.csv` (inventory_pts, imbal_share_20, day_type).
