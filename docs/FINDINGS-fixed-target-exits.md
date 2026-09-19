# FINDINGS — PURE FIXED-TARGET EXITS (a new exit family)

2026-08-07. Full close at the target, no partial, no trail. R ∈ {1, 1.5, 2,
2.5, 3}, all five reported for shape, **not tuned on**. Report-only.

## THE ANSWER

**The shipped 75%@3R + trail beats every fixed target, on every
population, on every metric, and it is not close.** The anticipated
sim-vs-live split **did not happen** — the same exit wins both stages on
all three books.

| population | shipped R/day | best fixed | fixed R/day | retained |
|---|---|---|---|---|
| INCUMBENT 15m | **0.813** | 3.0R | 0.274 | 34% |
| ROOM-GATED 3m | **0.624** | 3.0R | 0.458 | 73% |
| ROOM-GATED 5m | **0.434** | 3.0R | 0.336 | 77% |

And the shape is **monotone increasing in T on all three populations** —
1R is worst everywhere, 3R best, and **it has not turned over by 3R**. The
sweep's own message is "wider", and the thing at the end of "wider" is the
shipped exit's untruncated tail. A fixed target is a truncation of exactly
the distribution these books earn from.

## FIRST-PASSAGE vs "MFE EVER TOUCHED" — the distinction was load-bearing

| population | T | first-passage | MFE-ever | gap |
|---|---|---|---|---|
| INCUMBENT 15m | 1.0 | 55.0% | 91.9% | **+36.9pp** |
| INCUMBENT 15m | 3.0 | 29.2% | 77.0% | **+47.7pp** |
| ROOM-GATED 3m | 1.0 | 56.3% | 97.9% | **+41.6pp** |
| ROOM-GATED 3m | 3.0 | 38.0% | 91.6% | **+53.6pp** |
| ROOM-GATED 5m | 3.0 | 35.7% | 91.9% | **+56.2pp** |

Scoring a fixed target on "did MFE ever reach T" would have overstated its
win rate by **37 to 56 percentage points**. At 3R it is the difference
between a 92%-win-rate exit and a 38%-win-rate one. The gap is larger on
the room-gated stream because its stop is ~3.7× tighter, so more trades are
killed before their excursion peak.

Convention: if one 1m bar contains both target and stop, **the stop wins**
— conservative, and the same rule the shipped walk uses.

## DUAL CURRENCY — the whole family is a BR-20 inversion

Fixed targets do exactly what the wall-quality cut did, and at family scale:

| population | exit | win rate | EV |
|---|---|---|---|
| INCUMBENT 15m | fixed 1.0R | **55.0%** | +0.043 |
| INCUMBENT 15m | shipped | 39.8% | **+0.357** |
| ROOM-GATED 3m | fixed 1.0R | **56.3%** | −0.002 |
| ROOM-GATED 3m | shipped | 39.8% | **+0.546** |

**They buy 15–16 points of hit rate and sell 80–100% of the expectancy.**
Under Law 3 that is a refutation, not a trade-off.

## THE ACCOUNT LAB — no sim/live split

| population | exit | worst day | max size | SIM grad | LIVE $/yr |
|---|---|---|---|---|---|
| INCUMBENT | shipped | −5.41 | $350 | **98.5%** | **$28,501** |
| INCUMBENT | fixed 3.0R | −8.37 | $200 | 28.3% | $4,976 |
| ROOM 3m | shipped | −4.60 | $400 | **87.7%** | **$17,325** |
| ROOM 3m | fixed 3.0R | −4.60 | $400 | 72.6% | $13,637 |
| ROOM 5m | shipped | −6.65 | $300 | **57.7%** | **$9,289** |
| ROOM 5m | fixed 3.0R | −7.45 | $250 | 39.4% | $6,514 |

The watched-for pattern — tight target winning graduation while the
wide-tail exit wins live dollars — **does not occur**. Best-sim and
best-live are the same exit on all three books. That is a real answer: the
CONCORD dynamic was specific to a *selection* variable changing frequency,
not to an *exit* changing the outcome distribution's shape.

**Fixed targets do not even improve worst-day R.** The incumbent's worst day
degrades −5.41 → −8.37 and its max safe size drops $350 → $200. The trail
rescues trades a fixed stop kills; removing it means more full stop-outs on
bad days.

## PENDING ITEM 1 — the per-population MFE table

**Yes, the room-gated population runs further — but only in the tail.**

| population | p25 | p50 | p75 | p90 | p95 | P(≥1R) | P(≥2R) | P(≥3R) |
|---|---|---|---|---|---|---|---|---|
| INCUMBENT 15m | 0.39 | 1.20 | 3.74 | 9.52 | 14.53 | 55.0% | 37.7% | 29.2% |
| ROOM-GATED 3m | **0.02** | 1.34 | **5.72** | **21.04** | **35.29** | 56.3% | 44.9% | **38.0%** |
| ROOM-GATED 5m | 0.19 | 1.30 | 4.49 | 13.50 | 31.27 | 55.8% | 42.9% | 35.7% |

The room-gated stream is **more tail-heavy, not uniformly better**: worse at
p25 (0.02 vs 0.39 — a fifth of its trades barely move before stopping),
similar at the median, and more than **double** at p90. That is the tighter
stop showing up on both sides of the distribution.

**This is the strongest argument against a fixed target on this stream
specifically.** A book whose p90 is 21R and whose p95 is 35R is destroyed by
truncation at 3R.

## PENDING ITEM 2 — what the trail actually references, stated plainly

**The room-gated stream's trail STILL REFERENCES THE 15m BB MA, at 15m
granularity. It was never updated when the trigger moved to 3m/5m.**

`scripts/htf_ma_ltf_census.py` L79–84: *"trail reference stays the 15m BB MA
at 15m granularity (shipped exit)"* — and the same `f15` frame feeds every
timeframe including TF=1.

So the room-gated book is a **3m/5m trigger with a ~3.7× tighter stop and an
unchanged 15m trail**. That is a genuine inconsistency, and it is *not*
resolved by this pass — a fixed target avoids the question rather than
answering it. **The obvious untested exit is the shipped structure with a
trail matched to the trigger timeframe**, which has never been run.

## CAVEATS, both against the shipped exit

1. **The shipped exit is under-costed relative to a fixed target.** It
   executes two exits (75% at 3R, then the trailed remainder) but is charged
   one 0.5pt round trip. A fixed target closes once. Magnitude: an extra
   0.5pt on the 25% remainder is ~0.004R for the incumbent (~30pt stop) and
   ~0.013R for the room-gated stream (~10pt stop). **Too small to change any
   ranking here**, but it means the shipped exit's margin is very slightly
   flattered.
2. **Nothing was tuned, and 3R is the sweep's edge, not its peak.** The
   monotone shape means the best fixed target in this sweep is the widest
   one tested. Extending the sweep would likely keep improving until it
   converges on "don't cap the tail" — which is the shipped exit. That is a
   reason to stop sweeping, not to sweep further.

## A DEFECT THIS RUN EXPOSED IN EXISTING DATA

The first run produced incumbent worst-days of **−60R and −113R**, which is
impossible for an exit that caps loss at −1R.

Cause: `sweepb_london_frame.parquet` **has no `stop` column**, so **367 of
the 664 rows in the incumbent London book — every sweep_b row, 55% of the
book — had `stop = NaN`.** A NaN stop makes the stop-hit test all-False, the
trade never resolves, and the outcome falls through to an unbounded
end-of-day value.

Fixed by joining the stop back from `sweep_fit.parquet` (100% recovered,
and `|entry − stop| == risk` verified on every row). Two guards added: rows
without a finite stop are now **counted and reported, never silently
skipped**, and a **sanity bound** asserts the worst single trade ≥
−(1 + max cost_R) — it passes exactly at the bound on all three books.

**This mattered.** Before the fix the incumbent's first-passage win rate at
1R read 76.1%; it is actually **55.0%**. Every incumbent fixed-target EV was
negative and would have supported the wrong conclusion for the wrong reason.

The repaired `incumbent_london.parquet` is the version now on disk — any
number computed from the previous copy is suspect.

## VERDICT

The fixed-target family is **refuted as a replacement** for the shipped
exit, on all three populations, at every target tested, on both stages. It
is recorded as a null with a clear mechanism: these books earn from a tail
that a fixed target truncates, and the truncation cost rises with how
tail-heavy the population is.

The live question this leaves is not "fixed or trailed" but **"trailed on
what timeframe"** — and that has never been tested.
