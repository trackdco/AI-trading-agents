# SPEC: PXL/PXH specification lock and P-TABLE build

**Stage 0 + Stage 1 of BUILD-PLAN-pxl.md.** Part A is the locked mechanical specification — no rule requires a human to look at a chart. Part B is the build spec for Claude Code.

Source of truth for Part A is Angus's annotated 5-minute NQ chart (11 Aug 2026), not any transcript.

---

# PART A — THE LOCKED SPECIFICATION

## A0. Three declared assumptions — read these first

The annotation did not settle three things. Each is resolved below by internal consistency with the stated bias rule rather than by guesswork, and each is a **one-line change** if Angus rules otherwise. Nothing downstream is hard-coded to them.

**DA-1. The PXL is the most recent UNBROKEN swing low on the trigger timeframe.**
Reasoning: the bias rule is lower-high-lower-low. Only breaking the *most recent unbroken* low creates the new lower low. Breaking an older low would not produce "the next lower low," so continuation logic requires the most recent one. Mirror for PXH.

**DA-2 — SUPERSEDED. RULED BY ANGUS, 11 Aug 2026: the body must SPAN the wick zone in one candle — open above level 1 AND close below level 0.**
My original assumption required only the close below level 0. His ruling is strictly stricter: it adds the open condition, so the qualifying population is a subset of what I first specced. See A4 for the implementation and A4.1 for two consequences that follow from it.

**DA-3. "Top of the wick" is `min(open, close)` of the PXL candle — where the body begins — not the candle's high.**
Reasoning: a lower wick runs from the body's bottom down to the low; the annotation says "from the top to bottom of the **wick**." ⚠️ **This one materially changes the R denominator.** Stop distance becomes half the body-to-low span plus 2pt, which is *tighter* than if the fib spanned candle-high to candle-low. If Angus means the candle's high, stop distance grows and every R figure moves. Flag for ruling; the build must parameterise it (`WICK_TOP_MODE`) so both can be computed.

## A1. Instrument, sessions, timeframe

| Item | Value |
|---|---|
| Instrument | NQ (front month, continuous, roll convention per existing book) |
| Sessions in scope | `ny_am` (09:30–11:30 ET), `london` (03:00–07:00 London local) |
| Sessions excluded | Asia (ruled out on activity), `ny_pm` and lunch (recorded, not traded, in v1) |
| Trigger timeframe | **Any of 1m / 2m / 3m / 5m. The HIGHEST qualifying timeframe governs** (Angus's ruling, 11 Aug 2026) — and its geometry executes: its wick, its 50%, its stop. See A1.1 |
| Clock anchoring | `ny_am` anchored to New York local; `london` anchored to **London local**, not fixed ET (US and EU DST switch on different dates, so a fixed ET grid drifts an hour for 2–3 weeks twice yearly) |

## A1.1 Timeframe resolution — the highest qualifying TF governs

Per Angus's ruling: a setup may form on any of 1m / 2m / 3m / 5m, and where several qualify on the same fight, **the highest one is the setup**. His stated rationale is that conviction rises with timeframe.

This is a better deduplication rule than a convention-based collapse, because it is a real trading rule rather than an invented one: one row per fight, at the highest qualifying timeframe, lower timeframes subsumed. Adopt it as the primary resolution.

Two things follow that the build must be able to measure rather than assume.

**C3 — the rule buys conviction with R, and the exchange rate is measurable.**
Higher-timeframe candles carry larger wicks on average. Stop distance is `wick_width/2 + STOP_BUFFER` (A6) and the target is a fixed price (A7), so **selecting the highest qualifying timeframe selects the widest stop among the available options, which mechanically reduces `r_available` to the same draw.**

The rule and its rationale are separable, and both are testable:
- the *rule* is "take the highest qualifying TF";
- the *rationale* is "conviction rises with TF."

If win rate does not rise with timeframe while `r_available` demonstrably falls, the rule is costing expectancy. **Store the full geometry for every qualifying timeframe, not only the executed one**, so the highest-TF rule can be compared against lowest-TF (tightest stop, most R) and against a best-`r_available` rule — without a rebuild. Report median `wick_width_pts`, `stop_dist_pts` and `r_available` by timeframe.

**C4 — "take the highest" is a lookahead hazard unless the implementation is causal. ⚠️ NEEDS A RULING.**
Timeframes close at different times: a 1m trigger at 10:01 and a 5m trigger at 10:05 are separate events. At 10:01 it is unknowable whether a 5m trigger is coming. **Selecting the highest qualifying timeframe retrospectively across the whole fight is lookahead of exactly the class that killed the earlier canon.**

Two causally clean implementations. Build **(b)** as the base case because it is simpler and closer to what a trader watching a 5m chart actually does, and compute **(a)** in parallel so the choice is measured rather than assumed:

- **(a) Supersede.** Evaluate at each timeframe's close in ascending order. A higher qualifying TF replaces the lower one's resting limit. Honest but messy: if the lower TF's limit has already filled, that is the trade you are in, so the executed population depends on fill timing.
- **(b) Wait for the 5m close.** Always resolve at the 5m boundary, then take the highest TF that qualified within it. Simple and causal, but delays the order and will miss fast setups whose retrace completes before the 5m closes.

Record `resolution_mode` on every row. Whichever is chosen, **assert that `tf_trigger` is determined only by information available at `tf_trigger_ts`** — this belongs in Gate 1 (B4) alongside row existence, because timeframe resolution can smuggle in the future just as easily as a feature can.

## A2. The object — PXL and PXH

**PXL (for short setups, bearish structure).** Per Angus's ruling of 11 Aug 2026, the PXL is defined by **leg structure**, not by a bar-count pivot: price impulses down, retraces, and the low that terminated that down leg is the PXL.

- Track swing structure as alternating legs. A **down leg** ends, and its terminal low becomes a PXL candidate, once price retraces upward off that low by at least `MIN_LEG_RETRACE` (see A2.1 — **the one remaining open parameter**).
- `pxl_level_0` = that bar's `low` — the **0** level, the wick's outer edge.
- `pxl_level_1` = that bar's `min(open, close)` — the **1** level, the wick's inner edge (DA-3).
- `pxl_50` = `(pxl_level_0 + pxl_level_1) / 2` — the entry level.
- `wick_width_pts` = `pxl_level_1 − pxl_level_0`.
- Where several PXL candidates exist, the active one is the **most recent** (DA-1, confirmed).

**PXH is the exact mirror:** the high terminating an up leg; `pxh_level_0` = that bar's `high`; `pxh_level_1` = `max(open, close)`; `pxh_50` the midpoint.

⚠️ **Two different 50%s — do not conflate them in implementation.** The entry limit sits at 50% of the PXL **wick**. The roughly-50% retracement Angus describes is a retracement of the **down leg**, which is context for how price returns to the zone, not the entry level. They are different objects on different scales.

**Validity — structural, with no time component.** Per his ruling, a PXL stays valid while the retracement holds **below the swing high that began that down leg**. It is invalidated the moment that high is taken, because structure is then no longer lower-high-lower-low and the continuation premise has failed.

- Record `pxl_invalidated`, `invalidation_ts`, and `invalidation_reason` (`high_taken` | `triggered` | `session_end`).
- There is **no bar-count staleness rule.** An earlier draft of this spec used `PXL_MAX_AGE_BARS = 20`; that is deleted. A bar count mis-measures duration for the same reason a point threshold mis-measures distance — the invalidation is structural and self-scaling.
- Record `pxl_age_bars` as an observational column only, never as a filter, so staleness remains testable as its own hypothesis later.

**Re-arm — confirmed none.** One trade per PXL, never two. Once a PXL has produced a trigger it is spent; a new PXL must form. Note this is now doubly enforced: the span rule in A4 also disqualifies any level whose zone has been penetrated.

## A2.1 The one open parameter: `MIN_LEG_RETRACE`

Everything else in this spec is now pinned. This is not, and it matters: without a minimum, **every** minor pullback low inside a down leg qualifies as a PXL, and the population inflates with near-duplicate levels a few points apart.

Requirements for whichever value is chosen:
- **Scale-free**, expressed as a fraction of the down leg's own height or of ATR — never in points, per the scale law.
- **Declared, not swept.** Pick one value and commit it; report sensitivity across a small declared set (for example 0.236 / 0.382 / 0.5 of leg height) as a robustness check, exactly as the clustering-convention sensitivity is reported elsewhere in the programme.
- Build with a **placeholder of 0.382 of leg height** so the table can be produced, and treat every headline as provisional until Angus rules. Record `leg_height_pts` and `retrace_frac` on every row so the threshold can be re-applied post-hoc without a rebuild — this is the cheapest possible insurance against getting it wrong.

## A3. Context / bias gate

The setup is permitted only when the trigger timeframe's swing structure is aligned:

- **Short (PXL) permitted** when the last `STRUCT_N = 2` completed swing highs are descending AND the last 2 completed swing lows are descending.
- **Long (PXH) permitted** when the last 2 completed swing highs are ascending AND the last 2 completed swing lows are ascending.
- Otherwise the setup is **not permitted** and no row is written as a trigger — but see B2: a `structure_state` column is recorded on every candidate so the bias rule itself becomes testable later rather than being baked in unfalsifiably.

`STRUCT_N = 2` declared. Swing highs and lows are the **leg terminals** defined in A2 — the same objects that produce PXL and PXH candidates — so the bias gate and the level definition share one structural definition and cannot drift apart. The `PIVOT_N` bar-count reference in an earlier draft is deleted along with the pivot definition itself.

Note the bias gate is now partly redundant with the invalidation rule: a PXL is invalidated the moment the retracement takes the leg's starting high (A2), which is also the event that breaks lower-high-lower-low structure. Keep both — the gate is evaluated at the trigger, the invalidation is evaluated continuously — and record `structure_state` on every candidate so the gate itself stays falsifiable rather than assumed.

## A4. Trigger

A single 5m bar whose **body spans the entire wick zone** — per Angus's ruling of 11 Aug 2026:

- **Short (PXL):** `open > pxl_level_1` AND `close < pxl_level_0`
- **Long (PXH):** `open < pxh_level_1` AND `close > pxh_level_0`

where `level_1` is the wick's inner edge (the body boundary of the PXL/PXH candle) and `level_0` is its outer edge (that candle's low for a PXL, high for a PXH), per A2 and DA-3.

**Single-bar requirement.** The span must be achieved by one bar. Note this is now largely enforced by the geometry itself rather than by a separate clause: if a prior bar's body already closed inside the zone, the following bar opens inside it and can never satisfy the open condition.

## A4.1 Two consequences of the span rule — both affect how later stages must be run

**C1 — `body_pts >= wick_width_pts` by construction, so displacement magnitude and stop width are mechanically linked.**
Stop distance is `wick_width/2 + STOP_BUFFER` (A6), so the qualifying body is bounded below by roughly twice the stop distance net of buffer. Any variable derived from displacement size is therefore correlated with the R denominator.

⚠️ **Consequence for Stage 6:** displacement-quality variables must be tested **in R, never in hit rate** — a wider stop mechanically buys hit rate through the denominator, which is how `close_dist_bw` died in the earlier programme. And they should be normalised by `wick_width_pts` rather than by ATR, because ATR normalisation leaves the wick-width dependence in place. Record `body_wick_ratio = disp_body_pts / wick_width_pts` explicitly; the *excess* body beyond the minimum required is the non-circular part of displacement quality and is the version worth testing.

**C2 — the zone must be approached from fully outside it, so the trigger enforces a fresh break.**
Any prior body penetration of the zone permanently disqualifies that PXL, because subsequent bars open inside the zone. This reproduces the fresh-break law from the earlier programme as a geometric property of the trigger rather than as a separate staleness parameter. Record `zone_pre_penetrated` and the count of prior penetrations so the rule's bite is measurable.

⚠️ **Consequence for Stage 2:** trigger frequency will be materially lower than under a close-only rule. Frequency is not a free variable — it manufactures qualifying days, and the prop objective is scored on both axes. If frequency comes in below roughly one trigger per session per direction, record it as a finding in its own right, because a low-frequency book cannot clear a daily dollar floor regardless of per-trade expectancy.

⚠️ **Record, do not enforce, the accumulation count.** Column `break_bars` counts how many consecutive bars it took to move the same net distance through the level. The spec requires 1, but the multi-bar variant roughly triples the sample and the single-bar superiority claim has no published evidence — so the data must be able to answer it. Write `break_bars` on every row and additionally write **non-qualifying multi-bar breaks as rows with `qualified = false`** so the comparison is available without a rebuild.

## A5. Entry

- `limit_price` = `pxl_50` (resp. `pxh_50`).
- Order is a **resting limit**, placed at the close of the trigger bar, live from the **open of the next bar onward**.
- **Fill rule (base case): trade-through, not touch.** Filled only if a subsequent bar trades at least **1 tick (0.25 pt) beyond** `limit_price` — i.e. for a short, some bar's high ≥ `limit_price + 0.25`. A bar merely touching `limit_price` exactly does **not** fill.
- `limit_price` must be achievable: it is derived entirely from the PXL bar, which closed before the trigger bar. Assert no dependence on the trigger bar's own values.
- **Order cancellation — target-based, per Angus's ruling of 11 Aug 2026.** The limit rests until one of:
  - it fills;
  - **`target_price` (A7) is reached without a fill** → cancel, record `expired_target_taken = true`;
  - the PXL is invalidated by the swing high being taken (A2) → cancel, record `expired_invalidated = true`;
  - session end → cancel, record `expired_session_end = true`.
- An earlier draft used `LIMIT_TTL_BARS = 12`; that is **deleted**. There is no bar-count expiry.

🔑🔑 **Consequence, and it reframes the whole fill question.** Under this cancellation rule an unfilled setup is *by construction* one where the target was reached without a fill. So for every row with `expired_target_taken = true`, `unfilled_mfe_pts` is at least the full target distance. **The unfilled population is therefore not a random sample of setups — it is enriched in the cleanest, fastest continuations, the ones that never looked back.** The adverse-selection hazard is not hypothetical here; it is guaranteed by the rule's own definition, and its only open question is magnitude.

This makes the **fill rate** the single most important number the build produces, and it makes the comparison in B5 deliverable 8 the first thing to compute. If a large fraction of setups cancel with the target taken, the 50% limit is systematically declining the best continuations in exchange for a better price on the slower ones — and the correct response is to promote the market-entry control in A5's control block to primary, not to tune the limit.
- Stress variant (computed in parallel, not the base case): 2 ticks of trade-through, plus a 50% partial-fill assumption on bars whose range exceeds 2× ATR.

## A6. Stop

- Short: `stop_price = pxl_high + STOP_BUFFER`
- Long: `stop_price = pxh_low − STOP_BUFFER`
- **`STOP_BUFFER` is parameterised, not fixed.** Base case reproduces his rule at 2.0 pt for continuity with his hand-trading. Alternatives computed on the same rows: `0.15 × ATR14`, `0.25 × ATR14`, `0.33 × ATR14`, each floored at `4 ticks = 1.0 pt`. Rationale: a fixed point buffer does not scale — band widths roughly doubled 28.6 → 52.8 pt across eras, so 2 pt is a different object in each.
- `stop_dist_pts = |limit_price − stop_price|`. This is the R denominator: approximately `wick_width/2 + STOP_BUFFER`.

## A7. Target

- `target_price` = **nearest opposing liquidity draw** beyond entry, defined as: the nearest prior swing low (for shorts) that has not been broken, at the trigger timeframe, strictly beyond `limit_price` in the trade direction.
- `r_available = |limit_price − target_price| / stop_dist_pts`.
- **`min_1r_pass = (r_available >= 1.0)`. Recorded as a column, NOT applied as a filter in v1.**

⚠️ **Why it must not be a filter.** Because entry sits at 50% of the wick and the stop sits just beyond the wick's far edge, `stop_dist ≈ wick_width/2 + buffer` while the target is a fixed price. R is therefore mechanically determined by wick width, so "minimum 1R" is a **covert geometry filter on wick width relative to distance-to-draw** — and it plausibly excludes the widest, most violent displacements, which the displacement-quality literature suggests are the best ones. Recording it as a column makes it a testable hypothesis at Stage 6 instead of an invisible pre-filter.

## A8. Exits computed (all on every row, none privileged in v1)

`nearest_draw` (A7), `fixed_1R`, `fixed_1.5R`, `fixed_2R`, `fixed_3R`, `hold_with_stop` (session close), `partial_75_at_1R_trail`, `partial_75_at_2R_trail`.

Plus, independent of any exit: **`mfe_pts`, `mae_pts`, `mfe_R`, `mae_R`** — the excursion envelope from entry to session close. These drive all exit design at Stage 4 and are the most commonly skipped numbers in this kind of build.

## A9. Costs

`0.5 pt` round trip inside the R numerator (matching existing book convention). Hit-rate tables gross by design, labelled as such. Additionally record `spread_est_ticks` per row from the book where available, so Stage 5's spread-over-R viability test can run.

---

# PART B — P-TABLE BUILD SPEC (for Claude Code)

## B1. Scope and sealing

- **New table.** `output/p_table.parquet`. Do **not** extend the M-TABLE: PXL levels are swing wicks, M-TABLE levels are 15m BB MA fights — different level family, different population. Reuse the M-TABLE's *infrastructure*: schema conventions, sealing mechanics, and `scripts/htf_ma_entry_gate.py`.
- **Span:** full available history.
- **Fit era:** matches the existing programme's fit span.
- **Sealed:** everything before the fit span, written to `output/sealed/p_table_sealed.parquet` **unread**. No summary statistic, row count by outcome, or plot may be produced from it.
- Append the venue partition for this table to `DECLARATIONS-holdout-partition.md` and commit **before** the build runs: the six flow-covered NY-AM months are reserved exclusively for the flow family; the remaining months are reserved exclusively for the bar-only family. Two blocks for bar-only, both must pass; one look for flow.

## B2. Row definition — unconditional

**One row per (PXL object, trigger bar) pair.** Rows exist at the trigger, never at the fill.

Write rows for:
- `qualified = true` — all of A2–A4 satisfied
- `qualified = false, reason = 'multi_bar_break'` — level broken but over several bars (A4)
- `qualified = false, reason = 'structure_unaligned'` — clean single-bar break through a valid unstale PXL but structure not aligned (A3)

The last two exist so the bias rule and the single-bar rule are **testable rather than assumed**. Nothing filters on `qualified` at build time.

## B3. Schema

**Keys and time**
`event_id`, `ts_decision` (trigger bar close), `ts_entry_eligible` (next bar open), `date`, `session`, `tf_trigger`, `direction`, `cluster_id`, `qualified`, `reason`

**PXL geometry**
`pxl_ts`, `pxl_level_0`, `pxl_level_1`, `pxl_50`, `wick_width_pts`, `pxl_age_bars` (observational only, never a filter)

Leg-structure columns (per A2/A2.1): `leg_start_ts`, `leg_start_price` (the swing high that began the down leg — the invalidation trigger), `leg_height_pts`, `retrace_frac`, `retrace_high`, `pxl_invalidated`, `invalidation_ts`, `invalidation_reason` (`high_taken` | `triggered` | `session_end`)

Recording `leg_height_pts` and `retrace_frac` on every row lets `MIN_LEG_RETRACE` be re-applied post-hoc at any threshold without rebuilding the table.

`level_1` is `min(open, close)` of the PXL candle, or `max(open, close)` of the PXH candle — the wick's inner edge. `level_0` is that candle's `low` (PXL) or `high` (PXH). The fib spans the **wick only**, never the whole candle (DA-3, ruled 11 Aug).

**Trigger bar**
`disp_open`, `disp_high`, `disp_low`, `disp_close`, `disp_body_pts`, `disp_range_pts`, `disp_body_range_ratio`, `disp_close_loc` (`(close−low)/(high−low)`), `atr14_pts`, `disp_range_atr`, `disp_vol`, `disp_range_per_vol`, `break_bars`, `break_depth_pts`

Span-rule columns (per A4.1): `open_outside_zone` (bool), `close_beyond_zone` (bool), **`body_wick_ratio`** (`disp_body_pts / wick_width_pts` — the excess above 1.0 is the non-circular part of displacement quality), `zone_pre_penetrated` (bool), `n_prior_penetrations`, `body_excess_pts` (`disp_body_pts − wick_width_pts`)

**Multi-timeframe**
`tf_trigger` (the highest qualifying timeframe — the one that executes), `tf_qualifying_set` (list of all of 1/2/3/5m that qualified on this fight), **`tf_agreement_count`**, `tf_first_ts` (close time of the earliest qualifying TF), `tf_trigger_ts` (close time of `tf_trigger`), `resolution_lag_bars` (bars of the lowest qualifying TF between the two)

**Per-timeframe geometry must be stored for EVERY qualifying TF, not just the executed one** — as a nested struct or a sibling long-format table keyed on `event_id`: `wick_width_pts`, `pxl_50`, `stop_dist_pts`, `r_available` per TF. Without this, A1.1's resolution test cannot run and the highest-TF rule cannot be compared against alternatives without a full rebuild.

**Context**
`structure_state` (`aligned` | `unaligned` | `neutral`), `n_desc_highs`, `n_desc_lows`, `htf_align_1h`, `htf_align_15m`, `dist_vwap_pts`, `dist_pdh_pts`, `dist_pdl_pts`, `dist_onh_pts`, `dist_onl_pts`, `level_set_snapshot`

**Fill — the load-bearing block**
`limit_price`, `filled`, `ts_fill`, `bars_to_fill`, `trade_through_ticks`, `fill_rule_version`, **`unfilled_mfe_pts`**, **`unfilled_mae_pts`**, `filled_stress_2tick`, `filled_stress_partial`

Cancellation reasons, mutually exclusive (per A5): **`expired_target_taken`**, `expired_invalidated`, `expired_session_end`

> `unfilled_mfe_pts` is the single most important column in this schema. It answers whether the limit entry is adversely selected — whether the setups that never retrace are the bigger winners. That question gates whether Stages 4–10 are worth running at all.

**Market-entry control**
`ctrl_entry_price` (next bar open after trigger), `ctrl_mfe_R`, `ctrl_mae_R`, `ctrl_outcome_nearest_draw`. Same population, market entry — so the limit's contribution is measurable rather than assumed.

**Risk and target**
`stop_price_base`, `stop_dist_pts_base`, and one pair per `STOP_BUFFER` alternative in A6; `target_price`, `target_dist_pts`, `r_available`, `min_1r_pass`

**Outcomes**
One column per exit in A8, in R and in points; plus `mfe_pts`, `mae_pts`, `mfe_R`, `mae_R`, `bars_held`, `spread_est_ticks`

**Flow (covered months only)**
`flow_coverage` (bool), `delta_decision_bar`, `delta_3bar`, `cvd_state`, `closeloc`, `rangex`, `wall_size_ahead`, `wall_dist_ticks`, `book_imbalance`, `depth_censored` (true when the relevant level sits beyond the 10-level window)

`closeloc` and `rangex` were previously found 100% NaN. **Assert non-null on every flow-covered row before merge.**

## B4. The three gates — must pass before merge

**Gate 1 — row existence under perturbation.** Replace every bar strictly after `ts_decision` with the previous close and rebuild. **Assert the set of `event_id` keys is bit-identical.** If rows appear or vanish, row existence depends on the future. Run ≥15 probes across both directions and both sessions.

**Gate 2 — entry price.** Two asserts:
- (a) Flatten every bar strictly after `ts_decision` to the previous close; assert `limit_price` is **unchanged** (it derives only from the PXL bar) AND `filled` becomes false for all rows (nothing can trade through a flat series).
- (b) Row-level: assert `limit_price == pxl_50` exactly, and that `limit_price` equals no trigger-bar OHLC value except by numeric coincidence — log any coincidences for inspection.
- (c) **Developing-indicator check:** assert no level used anywhere in the row derives from an indicator including the current bar. The signature of that defect is an offset of exactly `Δclose / period`; scan for it explicitly.

**Gate 3 — convention check.** For every flow field, recompute on a deliberate overlap period present in both extractions and assert agreement to 100.00%. Convention is **bid-minus-ask**, matching the existing book. If the sealed span came from a different extraction than the fit span, it needs its own format check — verifiable without unsealing any analysis.

## B5. Acceptance criteria

The build is done when all of these hold and are reported:

1. All three gates pass, with probe counts printed.
2. `closeloc` and `rangex` non-null on 100% of flow-covered rows.
3. Row counts by `session × direction × qualified × reason`, fit era only, **plus triggers per session per day** — the span rule cuts frequency and that number is a finding in itself (A4.1 C2).
4. Sealed rows written, count printed, **no other statistic computed from them**.
5. Exclusion log: any dropped rows with a written criterion and a demonstration it is outcome-independent.
6. `wick_width_pts` distribution printed (median, p25, p75, p90) — needed for Stage 4's geometry work.
7. `stop_dist_pts` distribution printed under the base buffer and each alternative.
8. **Fill rate printed**, broken out by cancellation reason, and the distribution of `unfilled_mfe_pts` versus filled-trade `mfe_pts`. Report `expired_target_taken` as its own rate — that subset is the missed-winner population by construction (A5), so it is the direct measure of how much the limit entry costs.
9. `tf_agreement_count` distribution, `tf_trigger` distribution, and the events-per-cluster distribution. Plus the table required by A1.1: **median `wick_width_pts`, `stop_dist_pts` and `r_available` by timeframe**, which is what shows whether the highest-TF rule is buying conviction with R.
10. `wick_top_mode` fixed to `body` per DA-3 (ruled 11 Aug); the `candle_high` variant is no longer needed.
11. **`body_wick_ratio` distribution printed** (median, p25, p75, p90). Its floor is 1.0 by construction — the shape above 1.0 is what displacement quality actually is here (A4.1 C1).
12. `leg_height_pts` and `retrace_frac` distributions printed, plus row counts at each of the declared `MIN_LEG_RETRACE` sensitivity values (A2.1), so the open parameter's impact on population size is visible before it is ruled.
13. **`zone_pre_penetrated` rate printed** — how often a candidate PXL is disqualified by prior penetration, i.e. how much bite the fresh-break geometry has (A4.1 C2).

## B6. Explicitly out of scope for this build

No conditioning, no cuts, no filtering, no parameter selection, no exit choice, no holdout read. This build produces a **population**. Every one of those is a later stage with its own declared bar.

---

## What lands first, and why

Deliverable 8 is the reason to run this. One number — the fill rate — plus one comparison — unfilled travel versus filled travel — determines whether PXL's entry model is sound. If setups that never retrace systematically outrun the ones that fill, the limit entry is adversely selected, and the correct response is to test the market-entry control as the primary model rather than tuning a limit that is picking the weaker half of its own opportunity set.

That is one query against this table, and it is worth more than everything in Stages 4 through 10 combined.
