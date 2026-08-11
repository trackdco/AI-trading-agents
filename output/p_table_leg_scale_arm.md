# LEG-SCALE ARM (OTE) — mechanical build, alongside the candle-scale arm

Built on the SAME qualified event population as the existing candle-scale arm
(4,815 rows, fit era 2023-01-02..2025-05-31). No new trigger population — this
entry layers alternate entry/stop/target geometry and informational
displacement/sweep columns onto the existing rows. No expectancy, no win
rate, no exit outcome computed anywhere. Sealed rows untouched. Full
parameter declarations: `DECLARATIONS-holdout-partition.md` Entry 4.

**Source note.** The "OTE research" is a YouTube trading-education video
transcript (ICT/SMC-style explainer, including a sponsored prop-firm discount
segment), not a paper — treated per the skill's own discipline as an asserted
model, not measured evidence. Only the structural definitions are
operationalised here; the Tsinaslanidis et al. (2022) null on Fibonacci
bounce rates is accepted as given, and `r` is used purely as a declared entry
depth, per your framing.

---

## Task 4 — does any cell clear the fit-era stop bar? No.

**The bar, derived fresh from this table's fit era only** (does NOT reuse the
discarded M-TABLE 0.17W/~11-20pt anchor, and does NOT reuse the prior repair
run's 1.5×-noise-floor proxy — a new, more direct construction per this run's
own instruction): p90 of max adverse excursion from the candle-scale
`limit_price`, over the 5 real minutes starting at fill, on candle-scale
qualified+filled rows.

| session | n filled rows | median 5-min MAE | **bar (p90)** | for comparison: 1-min fill-bar-only MAE p90 |
|---|---|---|---|---|
| `ny_am` | 1,037 | 14.5pt | **44.7pt** | 25.95pt |
| `london` | 1,890 | 5.5pt | **15.75pt** | 10.0pt |

This is a materially **stricter** bar than either prior anchor — 5 minutes of
real adverse drift is a larger, more honest ask than a single bar's true
range, and it shows.

**Within the actually-traded window (`ny_am` 09:30–10:30), across the full
12-cell `MIN_LEG_HEIGHT × MIN_LEG_RETRACE` grid, all four `r` values, both
time sub-buckets: only 5 cell/TF/bucket/r combinations ever clear the bar,
and every one of them fails on frequency.**

| retrace | height (×ATR) | TF | bucket | r | n (whole 29-month fit era) | median leg | leg-scale stop |
|---|---|---|---|---|---|---|---|
| 0.236 | 3.0 | 3m | 09:45-10:30 | 0.50 | 17 | 90.0pt | 47.0pt |
| 0.382 | 3.0 | 3m | 09:45-10:30 | 0.50 | 19 | 103.75pt | 53.9pt |
| 0.382 | 3.0 | 5m | 09:45-10:30 | 0.50 | 15 | 111.5pt | 57.75pt |
| 0.5 | 3.0 | 2m | 09:45-10:30 | 0.50 | 14 | 87.9pt | 45.9pt |
| 0.5 | 3.0 | 3m | 09:45-10:30 | 0.50 | 18 | 103.75pt | 53.9pt |

14–19 events **total, across 29 months**, at the single most restrictive
height setting tested (`3.0×ATR`), only at `r=0.50` (the shallowest,
lowest-realised-R entry), only in the `09:45-10:30` sub-bucket. The
`09:30-09:45` sub-bucket never clears the bar at any cell, any TF, any `r`.
Every other apparent "pass" in the full sweep sits either in `london`
(explicitly not-traded, Task 6) or in `ny_am 10:30-11:30` (explicitly
excluded from the narrowed traded window) — mechanism evidence, not tradeable
cells.

**Reading it plainly:** the entry arithmetic needed legs of 30–55pt to clear
the *old*, now-discarded bar. Against the bar this table's own fit era
actually supports, it needs legs of ~90–110pt, and the population that
produces legs that size, in the traded window, at any MIN_LEG_HEIGHT setting
tested, is 14–19 events across the whole fit era — roughly one every 45–65
trading sessions. No cell is both viable and inside the traded window.

Full data: `output/p_table_leg_scale_bar.json`,
`output/p_table_geometry_sweep_timebucketed.json`,
`output/p_table_leg_scale_sweep_applied.json`,
`output/p_table_leg_scale_sweep_hits.json`.

---

## Task 7 — what it costs in frequency and fill rate

**Side by side, same event population, same stop-buffer constant:**

| | candle-scale (existing) | leg-scale r=0.50 | r=0.62 | r=0.705 | r=0.79 |
|---|---|---|---|---|---|
| stop_dist_pts, median (pooled) | 3.25pt | 10.9pt | 8.7pt | 7.2pt | 5.7pt |
| fill rate, `ny_am` traded window | 60.8%¹ | 13.7–16.3% | 11.5–14.2% | 9.9–12.7% | 9.4–11.8% |
| unfilled travel, median, `ny_am` traded window | 31.5pt¹ | 84–105pt | 91–111pt | 94–115pt | 99–118pt |

¹ candle-scale figures are whole-`ny_am`-session (09:30–11:30), from the
original build report — not yet re-cut to the narrowed traded window; see
caveat below.

**Fill rate falls steeply with `r`, exactly as the retrace_frac distribution
predicted — reported without smoothing:**

| r | `ny_am` 09:30-09:45 | `ny_am` 09:45-10:30 | `london` (not traded) |
|---|---|---|---|
| 0.50 | 16.3% | 13.7% | 15.4% |
| 0.62 | 14.2% | 11.5% | 12.8% |
| 0.705 | 12.7% | 9.9% | 11.4% |
| 0.79 | 11.8% | 9.4% | 10.0% |

Context (not the fill answer itself — a directional indicator only, since it
measures retracement AT the candle-scale trigger, not at the leg-scale
order's own eligibility): by trigger time, 73.3% of rows have already
retraced past `r=0.50`, 47.9% past `r=0.62`, 33.8% past `r=0.705`, 21.5% past
`r=0.79`. The *simulated* fill rates above are far below even these already-
retraced fractions, because "already past r once" is not "still resting
there when the order goes live and trades through by a tick" — most of that
already-deep retracement has moved on by the time an order could exist.

**Cancellation is overwhelmingly `target_taken`** — 84–99% of unfilled rows
across every `r`/bucket cell. This is the leg-scale mirror of the
candle-scale arm's `expired_target_taken` finding, but far more severe: where
29.3% of candle-scale setups cancelled with the target taken, **85–90% of
leg-scale setups do.** By construction (mirroring A5 exactly), every one of
those rows' `unfilled_travel_pts` is at least the full reward distance
(`r×leg_height`) — and the measured medians (84–118pt in the traded window)
run 3–4× past that floor. The setups that never offer the OTE retracement are
not a random subset of the leg population; they are the ones that kept
running.

**Frequency, from the base (MIN_LEG_HEIGHT=0) candle-scale-qualified
population, per session per direction, against the ~1/session/direction C2
floor — flagged regardless of geometry, as instructed:**

| bucket | short | long | pooled |
|---|---|---|---|
| `ny_am` 09:30-09:45 | 0.198 | 0.221 | 0.419 |
| `ny_am` 09:45-10:30 | 0.415 | 0.377 | 0.792 |
| `ny_am` 09:30-10:30 combined | 0.613 | 0.598 | 1.211 |

**Every bucket, every direction, is below the C2 floor** at baseline — before
any `MIN_LEG_HEIGHT` restriction, before any fill-rate attrition (13–16%,
above), and before any bar-clearing restriction (14–19 events total,
Task 4). Combining fill rate with frequency: at `r=0.50` in `09:45-10:30`,
expected FILLED triggers per session per direction ≈ 0.792 × 0.137 / 2 ≈
**0.054** — roughly one filled leg-scale entry every 18–19 trading sessions,
before even asking whether that entry's stop clears the bar.

**Candle-scale caveat, stated plainly:** the 60.8%/31.5pt candle-scale figures
above are whole-session numbers from the original build report, not yet cut
to the 09:30–10:30 window Task 6 narrows trading to. A true apples-to-apples
comparison needs the candle-scale arm re-cut to the same window; that re-cut
was not run in this entry (out of scope creep beyond what was asked) but is a
one-line filter on the existing `p_table.parquet` if wanted next.

Full data: `output/p_table_leg_scale_fill_report.json`,
`output/p_table_leg_scale_fill.parquet`.

---

## Task 1 — the leg-scale zone (pure relabeling, no lookups)

`level_1.0 = leg_start_price`, `level_0.0 = pxl_level_0` — both already on
every row. `leg_height_pts` recompute check: **0 mismatches** across 4,815
rows against `|leg_start_price − pxl_level_0|` — confirms the already-shipped
column is exactly this quantity.

---

## Task 2 — entry/stop/target, realised R, and the stop/invalidation coincidence

| r | reward (median) | risk (median) | **realised R (median)** | asymptotic r/(1-r) |
|---|---|---|---|---|
| 0.50 | 8.9pt | 10.9pt | **0.82R** | 1.00 |
| 0.62 | 11.0pt | 8.7pt | **1.26R** | 1.63 |
| 0.705 | 12.5pt | 7.2pt | **1.73R** | 2.39 |
| 0.79 | 14.0pt | 5.7pt | **2.45R** | 3.76 |

Realised R sits below the buffer-free asymptotic at every `r`, most at
`r=0.50` (0.82R realised vs 1.00 asymptotic) — exactly the erosion-on-small-
legs effect flagged in the run's own instructions (median leg height in this
population is 13.75pt; a 2.0pt buffer is a large fraction of a leg that
size).

**Constraint check: PASS.** All four declared `r` values exceed
`MIN_LEG_RETRACE=0.382`; asserted programmatically
(`scripts/p_table_leg_scale_geometry.py`), would halt the build on violation.
(Minor, pre-existing footnote: 0.71% of qualified rows — 34 of 4,815 — carry
`retrace_frac` fractionally below 0.382 at trigger time, a small boundary
effect already present in the gated, committed table; unrelated to this
constraint, which is a fixed-parameter comparison.)

**Stop/invalidation coincidence, confirmed:** both anchor to `leg_start_price`.
Stop sits at `leg_start_price ± 2.0pt` (`STOP_BUFFER`); structural
invalidation (A2) fires at `leg_start_price ± 0.25pt` (`TICK`) — tighter by
1.75pt, so invalidation always fires at or before the nominal stop. A row
still alive at trigger time has, by construction, not yet had its leg-scale
stop touched either.

---

## Task 3 — displacement on the leg (three columns, no selection)

n=4,815 qualified rows, all resolved (0 lookup failures):

| definition | rate |
|---|---|
| (a) FVG present on the leg | 41.4% |
| (b) leg range ÷ ATR14 at pivot bar (median) | 2.04× |
| (c) ≥2 consecutive same-direction closes on the leg | 50.9% |

All three true simultaneously: 19.3%. None true: 17.4%. These are
**informational columns on the existing population**, not a new gate — no
selection was made between them, and none was applied as a filter.

`(b)` is measured strictly at the pivot bar's own ATR — never the entry/
trigger candle — avoiding exactly the A4.1-C1 circularity the run's own
instructions named (a wider stop mechanically buying a "big displacement"
reading through the same denominator that sets risk).

Full data: `output/p_table_leg_scale_displacement_sweep.parquet`.

---

## Task 5 — the sweep precondition (recorded, not filtered)

**New declared reference window** (not previously defined anywhere in this
build — Asia stays excluded from *trading*, per SPEC A1; this is a reference
level only): Asia = 19:00 ET (prior evening) → 03:00 ET.

| | rate / distribution |
|---|---|
| `sweep_present` | **57.6%** |
| extreme swept, when present | pre-open range 1,160 · overnight 970 · asia 644 |

Sweep detection is direction-aware (short/PXL legs check for a HIGH swept
then closed back below; long/PXH legs check for a LOW swept then closed back
above — matching the transcript's own bullish/bearish examples), searched
backward from `leg_start_ts`, trade-through-then-close-back-inside within 3
bars of the trigger timeframe. Not applied as a filter anywhere in this run.

---

## Task 6 — session scope

Traded window narrowed to `ny_am` 09:30–10:30 ET, sub-bucketed at 09:45 in
every table above. `london` carries a noise floor of 15.75pt (this run's
bar) against `ny_am`'s 44.7pt — genuinely the venue where the geometry is
least broken — and is reported throughout, explicitly marked not-traded, per
your instruction. It is the source of most of the sweep's few nominal
bar-clearing cells (Task 4), which is exactly the "free mechanism evidence"
framing: informative about whether the OTE mechanism works at all, not a
tradeable result.

---

## Summary

Task 4 and Task 7 together answer the question this run was built to ask.
The candle-scale object's stop is too tight; the leg-scale object's stop is
wide enough in principle (median 5.7–10.9pt depending on `r`) but the legs
that would make it *clear the market's own fit-era-derived bar* are rare
enough (14–19 events in 29 months, in the traded window) that the fix trades
one failure mode for another: geometry that could work, on a population that
essentially doesn't exist inside the hours you're willing to trade. The
`09:45-10:30` sub-bucket is where what little exists concentrates;
`09:30-09:45` never clears the bar at all. Fill rate for the OTE entry itself
is 9–16%, roughly a fifth of the candle-scale arm's, and unfilled travel runs
3–4× candle-scale's — the same adverse-selection shape as before, sharper.
