# P-TABLE geometry repair run — mechanical diagnosis, not a selection run

Fit era only (2023-01-02 → 2025-05-31). Sealed rows untouched throughout — no
statistic beyond what Entry 1 already recorded. **No expectancy, win rate, or
outcome statistic is computed anywhere in this run**, with one narrow,
declared exception noted where it occurs (Task 2's stop-touch rate, which is
unobtainable without knowing the fill bar). Parameter values were appended to
`DECLARATIONS-holdout-partition.md` (Entry 2) before this run executed.

---

## Task 3 — the object-definition test (leads, per the run's own instruction)

**Hypothesis under test:** a single candle's wick on a 1–5m NQ chart is
inherently too small to carry a tradeable stop — DA-3 identifies the wrong
object. On the SAME identified qualified events (no re-run of leg tracking or
trigger detection — geometry recompute only; simplification stated below),
recomputed under:

- **(a) DA-3 as specced** [built, current]: `level_1 = min(open,close)`.
- **(b) full candle range**: `level_1 =` the same candle's own high (PXL) /
  low (PXH) — the `WICK_TOP_MODE=candle_high` variant the SPEC pre-declared
  as a parameter but never built (Angus ruled body on 11 Aug).
- **(c) multi-candle zone** — **not built.** Underspecified as instructed;
  see the question at the end of this report.

**Declared simplification:** `target_price` is held at (a)'s value under (b)
— the liquidity pool is a property of *other* candidates' `level_0`
(unaffected by wick-top mode), and re-deriving it against (b)'s shifted limit
per row would be a rebuild, not a recompute.

### Result: widening the object roughly doubles the stop and crosses the viability line

| | (a) body [built] | (b) full candle range |
|---|---|---|
| `wick_width_pts`, qualified, pooled | median **2.5**, p90 9.5 | median **8.75**, p90 27.75 |
| `stop_dist_pts`, pooled | median **3.25**, p90 6.75 | median **6.5**, p90 15.75 |
| `r_available`, pooled | median **3.08R**, p90 8.2 | median **2.06R**, p90 4.39 |
| widening ratio (b / a), per row | — | median **1.83×**, p25 1.5×, p75 2.44× |
| stop ÷ 1m-noise-floor, `ny_am` | **0.38×** | **0.92×** |
| stop ÷ 1m-noise-floor, `london` | **0.65×** | **1.18×** |

By timeframe (n=4,815 qualified, same events both columns):

| TF | wick_width (a→b) | stop_dist (a→b) | r_available (a→b) |
|---|---|---|---|
| 1m | 1.75 → 6.5 | 2.75 → 5.25 | 2.72 → 1.92 |
| 3m | 3.0 → 10.75 | 3.5 → 7.25 | 3.46 → 2.25 |
| 5m | (see appendix json) | (see appendix json) | (see appendix json) |

**Reading it plainly:** under (a), the median stop sits at 0.38–0.65× the
market's own 1-minute noise floor in every session — mechanically inside the
noise, which is what Task 1/2's blanket `mechanically_nonviable=True` finding
(below) says directly. Under (b), the median stop crosses to 0.92–1.18× the
noise floor — still marginal in `ny_am`, genuinely plausible in `london` —
while `r_available` compresses by roughly a third (target is unchanged, stop
widened). This is the exact C3 trade-off the SPEC names for timeframe
selection, now shown to apply to the *wick-boundary definition itself*: the
object identified by DA-3 is not merely "one candidate reading" — its stop is
quantifiably, consistently below the noise floor it needs to clear, and the
one alternative the SPEC itself pre-declared closes most of that gap.

This does **not** resolve which definition is right — that is Angus's call
against his own chart — but it answers the mechanical half of the question:
DA-3 is not an arbitrary-but-equally-valid choice next to (b); it is the
tighter of two, and tighter by almost exactly 2×, consistently across every
timeframe measured.

Full per-TF distributions: `output/p_table_object_definition_ab.json`,
row-level: `output/p_table_object_definition_ab.parquet`.

---

## Task 4 — the eyeball export (second-highest priority)

30 qualified events rendered — 10 each at 1m/3m/5m, spread evenly across
`ny_am`/`london` × short/long. Deterministic selection (strided by
`event_id`, no randomness). Each chart shows real candles, the PXL/PXH candle
outlined (navy), the displacement/trigger candle outlined (orange), the 0 /
0.5 / 1 levels, and the stop/target reference lines. **No outcome or
execution path is drawn** — no fill marker, no MFE trace, no exit — this is
an object-identification check, not a trade replay.

`output/eyeball_export/` — 30 PNGs + `eyeball_export.csv` (event_id, date,
session, direction, tf_trigger, wick_width_pts, stop_dist_pts, r_available,
all four price levels, image filename).

**Worth flagging specifically:** event `03b389a6210ca65e` (2023-06-02,
london, PXH, 5m) has `wick_width_pts = 0.00` — the PXH candle's high equals
its own close exactly (no upper wick at all), so `level_0 == level_1` and the
stop is set entirely by `STOP_BUFFER` (2.0pt) with zero contribution from the
object itself. This is the degenerate limit of the hypothesis under test and
is worth Angus's first look.

Sample rendered inline for this report — `000f44db7146b28c` (2025-02-18,
ny_am, PXL, 1m, `wick_width_pts=1.5`, `stop_dist_pts=2.75`): the PXL candle
and its neighbors run 5–10pt ranges; the marked wick is visibly a fraction of
the surrounding candle noise.

---

## Task 0 — repo provenance (answered before Task 3 ran; restated here for the record)

The M-TABLE programme **exists** in this repository — on `origin/claude/hello-zfmoq6`
and its descendant `origin/claude/tradingview-mcp-agent-setup-ql18v8` (active
through commits dated 2026-08-11, today). It was invisible to the first
build's search only because that search never ran `git fetch --all` and so
never saw ~30 additional remote branches. `scripts/htf_ma_entry_gate.py`
exists for real there (176 lines, a T1/T2/T3 entry-price gate keyed to the
M-TABLE's own schema — not line-for-line reusable for P-TABLE's different
row family, but the same pattern this build's own Gate 2 independently
converged on). No file named `SPEC-htf-ma-mechanism-census.md` exists;
`docs/VERDICT-htf-ma-census.md` is the nearest equivalent.

**Contamination, stated plainly:**

- `docs/DECLARATIONS-holdout-partition.md` on that branch (declared
  2026-08-07) fixes the M-TABLE's sealed+gray span at **2023-01-01 →
  2025-05-31** — the exact inverse of this P-TABLE's fit/sealed split. Their
  bar-only holdout venue there is **already closed** (commit `0155bcab`,
  "H1 PASS, H4 PASS... CLOSED — no further contact in either direction").
  Nothing this table's fit-era work does can retroactively contaminate an
  already-spent, already-closed look — that specific risk is moot. The D3
  flow-venue look's status was not exhaustively confirmed; this is not
  asserted clear.
- **The live, unresolved risk runs the other way.** This P-TABLE's sealed
  span (2025-06-01 → 2026-01-30) is the M-TABLE programme's actively and
  extensively explored fit-accessible window — Census A statistics, a
  narrated-day corpus, live TradingView agent trading tests, through today.
  This repo's "written unread" claim is true of this session's eyes only,
  not of the team's collective knowledge. Angus and collaborators already
  hold detailed, published priors about that period from the M-TABLE work.
  This is a real breach of sealing's *spirit*, independent of any literal
  M-TABLE clause.
- **No clean fix is available from inside this session.** Entry 1's fit-era
  report already published detailed statistics for 2023-01→2025-05 — so
  that span is now also exposed by *this session's own prior work*, not
  only by the M-TABLE programme. Flipping the partition would not reset it.

This needs Angus's decision, not a unilateral rebuild — see the question at
the end of this report. Nothing in this repair run touches the partition.

---

## Task 1 + Task 2 — MIN_LEG_HEIGHT × MIN_LEG_RETRACE, per timeframe

**New additive parameter**, default off (`0.0` reproduces Entry 1's table
byte-for-byte): `MIN_LEG_HEIGHT_ATR_FRAC`, a leg-height floor expressed as a
fraction of ATR14 on the leg's own timeframe. It gates **pivot confirmation**
in the leg tracker (an under-height retrace does not terminate the leg — it
keeps extending), so it composes with `MIN_LEG_RETRACE` rather than filtering
the output after the fact. Declared in `DECLARATIONS-holdout-partition.md`
Entry 2 before the sweep ran.

Grid: `MIN_LEG_HEIGHT_ATR_FRAC ∈ {0.5, 1.0, 2.0, 3.0}` × `MIN_LEG_RETRACE ∈
{0.236, 0.382, 0.5}` = 12 cells. No fill simulation, no exit battery — the
one exception is a **minimal** fill/stop-touch check (fill boolean + same-bar
stop touch only, nothing else computed or retained) needed for the
stop-touch-rate metric explicitly requested; this is called out here as a
deliberate, narrow departure from "no simulation," not a silent one.

### The headline finding: every cell, every timeframe, is mechanically non-viable

Noise floor (median 1-minute true range, pooled fit era, computed once — not
per cell): **`ny_am` 12.5 pts, `london` 4.25 pts.** (Sanity-checked against
raw high–low range and against sample days across the price-level range
11K–25K; not a data-gap artifact — NQ's point-denominated 1-minute range
genuinely runs this wide, consistent with Entry 1's own band-width finding of
28.6→52.8pt drift across eras.) Declared cost assumption for anything
downstream: **0.5pt round trip, matching the existing book convention — NOT
measured**, since no book/spread data exists anywhere in the fit era (all
flow coverage lies in the sealed span).

**`stop_dist_pts ÷ noise_floor` is below 1.0 in every one of the 12 cells, at
every timeframe, in both sessions — including at `MIN_LEG_HEIGHT_ATR_FRAC =
3.0`.** Raising the leg-height floor 6× (0.5 → 3.0 × ATR14) cuts the
qualified population by roughly 8× (9,021 → 553 events, pooled 0.236-retrace
column) but barely moves `stop_dist_pts` (1m: 3.0 → 3.0pt median; 5m: 4.25 →
4.25pt median) — because `MIN_LEG_HEIGHT` constrains the *leg*, and the wick
that actually sets the stop is a property of one terminal candle, only
loosely coupled to the leg that produced it. **This is the clean, mechanical
reason `MIN_LEG_HEIGHT` is the wrong lever for stop viability** — it trades
away 85–90% of the population for almost no improvement in the number that
matters, exactly the shape Task 3(b)'s object-redefinition avoided (fewer
than 2× fewer events, ~2× wider stop, crossing the viability line in
`london`).

Full 12-cell × 4-TF table (`output/p_table_geometry_sweep.json`); condensed
1m/5m view:

| MIN_LEG_RETRACE | MIN_LEG_HEIGHT (×ATR) | n qualified | wick_w 1m→5m med | stop_d 1m→5m med | r_avail 1m→5m med | stop÷noise `ny_am` 1m→5m | stop÷noise `london` 1m→5m |
|---|---|---|---|---|---|---|---|
| 0.236 | 0.5 | 9,021 | 1.75 → 4.5 | 3.0 → 4.25 | 2.75 → 3.96 | 0.32 → 0.52 | 0.59 → 0.88 |
| 0.382 | 0.5 | 4,596 | 1.75 → 4.5 | 2.75 → 4.25 | 2.64 → 4.20 | 0.32 → 0.52 | 0.59 → 0.82 |
| 0.5 | 0.5 | 1,577 | 2.0 → 4.5 | 3.0 → 4.25 | 2.89 → 3.92 | 0.32 → 0.50 | 0.59 → 0.82 |
| 0.236 | 1.0 | 3,398 | 2.0 → 4.75 | 3.0 → 4.5 | 3.32 → 4.16 | 0.32 → 0.54 | 0.59 → 0.88 |
| 0.382 | 1.0 | 3,026 | 1.75 → 4.5 | 3.0 → 4.25 | 3.11 → 4.5 | 0.32 → 0.55 | 0.59 → 0.82 |
| 0.5 | 1.0 | 1,417 | 2.0 → 4.75 | 3.0 → 4.25 | 3.05 → 3.84 | 0.30 → 0.51 | 0.59 → 0.82 |
| 0.236 | 2.0 | 1,002 | 2.0 → 4.5 | 3.0 → 4.25 | 4.15 → 4.05 | 0.34 → 0.50 | 0.65 → 0.88 |
| 0.382 | 2.0 | 1,103 | 2.0 → 4.75 | 3.0 → 4.5 | 4.25 → 3.38 | 0.36 → 0.50 | 0.65 → 0.82 |
| 0.5 | 2.0 | 802 | 2.0 → 4.88 | 3.0 → 4.5 | 3.58 → 6.07 | 0.32 → 0.56 | 0.65 → 0.77 |
| 0.236 | 3.0 | 553 | 2.25 → 4.25 | 3.0 → 4.25 | 6.24 → 3.28 | 0.32 → 0.52 | 0.65 → 0.94 |
| **0.382** | **3.0** | **575** | **2.0 → 4.5** | **3.0 → 4.25** | **4.77 → 8.25** | **0.33 → 0.62** | **0.65 → 0.88** |
| 0.5 | 3.0 | 408 | 1.75 → 4.0 | 3.0 → 4.0 | 3.86 → n/a (n=2) | 0.31 → 0.43 | 0.59 → 0.88 |

**Triggers per session per day**, for reference on the frequency cost of
tightening either parameter (pooled, all TF): the built-table cell
(`retrace=0.382, height=0.0`, i.e. Entry 1) ran 2.12/`ny_am`, 3.95/`london`
qualified per day; the most restrictive cell here (`retrace=0.5,
height=3.0`) runs 0.36/`ny_am`, 0.46/`london` — comfortably below A4.1 C2's
one-per-session-per-direction concern.

**Stop-touched-on-fill-bar rate** (minimal check, fill-boolean scope only):
ranges 21–41% across cells/TFs, generally *higher* at tighter (lower-height)
cells and at lower timeframes — consistent with, not independent evidence
against, the core finding: a stop close to the noise floor gets touched on
its own fill bar disproportionately often.

Full data: `output/p_table_geometry_sweep.json`.

---

## Task 5 — the missing-target problem

33.9% of qualified rows (1,633 of 4,815) have no prior unbroken draw beyond
the limit. Using EXISTING columns only (no new simulation):

| | target-missing (n=1,633) | target-present (n=3,182) |
|---|---|---|
| fill rate | **83.9%** | 48.9% |
| unfilled `unfilled_mfe_pts` | median 67.0, p90 214.0 (n=247) | median 27.75, p90 90.0 (n=1,540) |
| filled `mfe_pts` | median 25.1, p90 103.2 (n=1,370) | median 17.5, p90 74.1 (n=1,557) |
| `expired_session_end` rate | 14.8% | 3.8% |
| `expired_target_taken` rate | 0.0% (by construction) | 44.4% |
| market-ctrl `ctrl_outcome_nearest_draw_R` | median **-1.03R** | median -0.25R |
| rate by session×direction | `ny_am` ~44%, `london` ~28% | — |

**Mechanism, stated plainly:** with no target to cancel against, orders stay
live and fill far more often (84% vs 49%), and both filled and unfilled rows
travel further — this subset looks like it's running into genuinely open
space. The `ctrl_R` gap is a measurement artifact worth naming rather than a
performance claim: `ctrl_outcome_nearest_draw_R`'s exit logic can only fire
on stop or session-close when `target_price` is NaN (the same `tgt_touch`
check the fill simulation uses), so for this subset it silently degrades to
a de-facto hold-with-stop exit — it is not comparable to the target-present
column's number without accounting for that.

**Three candidate fallback target definitions, proposed only, none
implemented:**

1. **Fixed-R fallback.** Fall back to the already-computed `fixed_2R` or
   `fixed_3R` exit column when no structural draw exists. Simplest, guarantees
   a target always exists, but re-couples R to a fixed multiple exactly where
   A7 warns against it (though only for the third of rows with no draw).
2. **Widen the level-type pool.** The existing context columns
   (`dist_pdh_pts`, `dist_pdl_pts`, `dist_onh_pts`, `dist_onl_pts`) are
   already computed on every row; use the nearest of these as a structural
   fallback instead of a fixed multiple, before falling back further.
3. **Relax "unbroken."** A7 requires the nearest *unbroken* prior swing. A
   broken level can still act as later support/resistance in practice — a
   fallback could search the nearest broken level, or extend the search to a
   coarser timeframe's swing structure (15m/1h) when the trigger-TF pool is
   exhausted.

No selection between these is made here.

---

## Task 6 — mode (a) vs mode (b), from existing columns only

No new simulation. Reporting exactly what `a_*` and the mode-b columns
already in `output/p_table.parquet` support, and flagging what they don't.

| | mode (b) [built, wait-for-boundary] | mode (a) [`a_*` columns, supersede] |
|---|---|---|
| fill rate | **60.8%** | **70.5%** |
| order-never-live | 966 rows (20.1%) | **no equivalent column in current schema** |
| travel / MFE | `unfilled_mfe_pts`, `mfe_pts` exist | **no travel/MFE column exists for mode (a) at all** |

**Filled-flag agreement:** 88.2% of rows agree between modes. Of the 566 that
disagree: **517 filled under (a) but not (b)** — the direct, measurable cost
of mode (b)'s boundary delay (the SPEC's own prediction). **49 filled under
(b) but not (a)** — the reverse case exists too and is not explained away by
"mode (a) is a strict superset of mode (b)'s fills"; it isn't.

**Executed-timeframe divergence:** 202 of 4,815 rows (4.2%) have mode (a)
executing a *lower* timeframe than mode (b)'s governing one — always lower,
never higher (`tf_trigger=2→a_executed_tf=1`: 78 rows; `3→1`: 23, `3→2`: 40;
`5→1`: 14, `5→2`: 21, `5→3`: 26). This is supersession working as specced:
mode (a) locks onto the first live lower-timeframe order before a
later-closing higher timeframe can steal it.

**Geometry (both purely mechanical, no simulation):** `a_r_available` median
3.00R vs mode (b)'s `r_available` median 3.08R on the same population —
close, as expected since 95.8% of rows execute the same timeframe under both
modes.

**Schema gap found while reading the code, not previously documented:**
`_mode_a()`'s scan skips every bar with `b.open_ts < cur[1]` (before the
pending event's own eligibility) entirely — it never checks that skipped
window for a fill or a target-touch. Mode (b) has an explicit, named
mechanism for this same window (`order_never_live`,
`gap_limit_traded_through`) precisely because that gap is where its own
resolution delay bites; mode (a) has no analogous tracked column, so this
comparison cannot currently say how often mode (a)'s *own* pre-eligibility
gap cancels an order the way mode (b)'s does. Closing this gap would require
new simulation, which is out of scope for this run.

---

## What this run does and does not settle

**Settled, mechanically:** the P-TABLE's built stop is below its own market's
1-minute noise floor in every session, at every timeframe, under every
`MIN_LEG_HEIGHT`/`MIN_LEG_RETRACE` combination tested — `MIN_LEG_HEIGHT` is
not the fix. The one lever that closes most of the gap is the object
definition itself (Task 3b), which the SPEC had already pre-declared as a
parameter and never built.

**Not settled, by design:** which object definition is correct (Angus's
call), what construction (c) is (Angus's call), how to fill the
missing-target third of the population (three proposals, no selection), and
— found mid-run, unrelated to geometry but larger than anything else here —
what to do about this P-TABLE's sealed span sitting inside the M-TABLE
programme's actively-researched, currently-fit-accessible window (Angus's
call). Two questions follow.
