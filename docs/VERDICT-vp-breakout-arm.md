# VERDICT — vp-breakout-arm (Job 2) — 2026-08-07

```
VERDICT      NO LIFT (attributable to the level). The breakout arm's
             conditional lift is large, era-stable in sign AND K-rank,
             and lands DEAD CENTER of the proximity-matched placebo
             distribution: real levels rank at the 56th (above) and
             43rd (below) percentile of 100 matched random-level
             draws. A placebo level with the same distance-from-price
             and the same width does everything the real value area
             does. Neither the Wilson CIs nor the era agreement ever
             asked the question that matters; the matched placebo did,
             and the answer is no.

MECHANISM    Two generic engines, no level content. (1) Mechanical
             coupling: accepted_K conditions on surviving K minutes
             without a reentry close, which buys time toward any
             continuation target — the lift is partially guaranteed by
             construction, and grows monotonically in K (0.19 -> 0.51
             above, 0.21 -> 0.58 below) exactly as coupling predicts.
             (2) Proximity: a line near price that price leaves and
             stays beyond marks momentum, wherever the line came from.
             The overnight volume distribution contributes nothing
             measurable to either engine.

EVIDENCE     Population: the Job 1 census, 1,049 excursions / 747
             clusters / 290 sessions; G7 reconciliation PASS
             (failed_K + accepted_K == n for every K, every side).
             Unit = value-area width W. Headline outcome
             cont_before_reentry_1.0W, clustered:
               unconditional: above 16.1% [12.7, 20.1]
                              below 15.3% [11.9, 19.3]
               | accepted_15: above 52.7% [43.5, 61.8]  (110 clusters)
                              below 54.5% [44.2, 64.5]  ( 88 clusters)
               lift (cluster bootstrap): above +0.349 [+0.292, +0.405]
                                         below +0.370 [+0.301, +0.435]
             Table H complementarity (first event, all excursions):
               rotated-to-POC-first 51%/45%, continued-to-1.0W-first
               30%/32%, NEITHER by 16:00 18%/22% (above/below) — one in
               five excursions is simply not an event. Under
               accepted_15 the mix flips to continued-first 56%/57%.
             Artifacts: output/vp_census/job2_* (rates, lift, era,
             surface, power, table_h, placebos).

NULLS        Proximity-matched placebo (src/research/placebo.py, 100
             draws, donor geometry translated to each session's 09:30
             anchor — distance, W, and internal geometry matched by
             construction):
               above: real +0.367 vs matched median +0.363,
                      range [+0.290, +0.451], real percentile 56/100.
               below: real +0.393 vs matched median +0.399,
                      range [+0.312, +0.490], real percentile 43/100.
             Stale-level comparator: +0.243 / +0.271 — BELOW real this
             time. Read together with Job 1 (where stale showed 5x):
             an unmatched placebo is distance-confounded in whichever
             direction the outcome favours, which is why Job 1's
             "random beats real" overstated that case and why this
             harness is now the standard.

SURFACE      Bin width, VA%, expansion: flat (0.33-0.41, overlapping
             CIs; canonical interior). K axis is NOT flat — lift rises
             monotonically with K on both sides — but that is the
             coupling engine, not level information: the placebo
             distribution rises with it. Job 1's surface was
             featureless; this one has exactly one feature and it is
             mechanical.

ERA          Perfect agreement: sign 7/7 K values, K-rank Spearman
             +1.0, both sides (2025H2 +0.332/+0.406; 2026H1
             +0.366/+0.327 at K=15). Worth stating plainly: this arm
             passes the era test cleanly and is still dead — era
             stability screens regime luck, not attribution.

GAPS         Inherits Job 1 GAPS 1-5 (tape end 2026-07-15, bimodal-
             night construction tail, early-close truncation, G3 raw
             coverage, same-bar conservatism). New: (6) placebo draws
             share the mechanical coupling by design — that is the
             point — so this test cannot detect a level effect smaller
             than draw noise (~±0.04 at n=100); a real effect that
             small would be economically irrelevant here. (7) Ledger
             now 261 rows across both jobs; the joint effective
             independent trial count remains ~2-3 (two sides, one
             idea), not 261.

NEXT         None. Both arms are closed.
```

## Combined statement — the durable artifact

**Neither arm of the transcript's 18:00–09:30 volume-profile model
attributes to the overnight value area on NQ (2025-06-02 → 2026-07-15,
290 sessions, 1,049 excursions).** The failed-auction arm: rotation to
POC runs 56–60% unconditional; the failed-auction lift of +0.06/+0.10
sits at the bottom 5% of even unmatched placebo distributions — any
line shows the effect, most lines show more of it. The breakout arm:
continuation to one VA-width before reentry runs 15–16% unconditional,
rises to 53–55% under 15-minute acceptance, and matches
proximity-matched random levels to within draw noise (percentiles
56/43 of 100). The event grammar itself is real and generic — a quick
close-back marks local mean reversion, sustained acceptance marks
momentum, at any nearby line, however drawn. What is dead is the claim
that WHERE the overnight volume traded tells you anything those two
facts do not. These base rates enter the base-rate library as the
null for any future level-conditioned model: beat the
proximity-matched harness (`src/research/placebo.py`) or you have
remeasured this.

---

Gates: Job 1's G1–G6 stand unchanged on the same artifacts; G7 PASS;
`report.py --unseal` re-verified exit 2 after Job 2 (holdout sealed,
no look spent by either job). Every figure traces to a named artifact
under `output/vp_census/`.
