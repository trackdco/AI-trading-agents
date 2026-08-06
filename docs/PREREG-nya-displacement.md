# PREREG — NYA-DSP-01: the canon rebuilt on displacement entries

**Committed before any number exists.** Date 2026-08-05. Authorises `scripts/build_l2_outcomes.py --entry EC`.

## 0. What Angus asked for

> *"i do think we should rebuild the canon around displacement through level entries and not
> limit retests. keep it ny specific for now. lets get the raw triggers including the ones
> where limits werent retested and they just ran... top down optimisation process like we
> did with the original canon, but this time we have no hindsight with depth"*

## 1. The change, and why the old population was censored

The canon enters on a **limit at the retest**. That entry cannot reach a trigger where price
closes through the level and never comes back — and those are not a random subset. Measured
on London: **109 such triggers, 82% win rate, PF 5.42, +$21,536** — roughly +9.9 points a
trade, which clears the design bar on its own. The limit book never saw one of them.

So the old canon was not merely entering differently. **It was trained on a population with
its best cohort structurally removed.**

Market entry on the close-through takes them. The cost, measured on London and stated
before this runs: re-pricing the trades that *would* have retested is expensive
(PF 0.48 on that half). The NY question is whether the recovered cohort outweighs it on a
population 2.2x larger.

## 2. NO HINDSIGHT ON DEPTH — the binding rule

`research/findings/LDN-depth-read-one-bar-late.md`: the canon's depth features read the
book at the fill bar's **close**, at or after the fill. `W` fell +19.0pp → +8.2pp and `FAR`
+20.5pp → +6.3pp once read honestly.

**With a market entry at the trigger candle's close, the decision moment and the entry
moment are the same instant.** Depth and flow at that candle are exactly what was acted on.
No anchor ambiguity, no approach bias, no fill-timing question — the defect class cannot
arise. That is a reason to prefer this entry independent of P&L.

**Every depth/flow feature is read at the trigger candle. The fill-bar-close read is barred
from the search entirely.**

## 3. Population

`output/l0_triggers_fit.parquet` — 19,137 triggers, 270 sessions, 2025-06 → 2026-07.
Entry arm `EC`: market on displacement, resting limit on rejection blocks (Angus's own
stated execution). `E3` (existing `l2_outcomes_fit.parquet`) is the CONTROL — same triggers,
limit entry — so this is a head-to-head, not two strategies.

Setup dedup and the VWAP-touch rule are re-derived **per arm**, never inherited: market
entries fill at a different moment, so E3's grouping does not describe this book.

## 4. Scored on the prop objective from the first number

`src/validation/prop_score.py`. Net ≥ 4 pt/trade after 2pt friction (design target +10),
T ≥ 2, N ≥ 200, green days ≥ 55%, max day ≤ 30%, every year green. **Profit factor is not
the objective** — it correlates −0.46 with green days on our own data.

## 5. Sealed

2023/24 and the sealed months untouched.
