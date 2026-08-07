# SPEC — Job 1: Value-Area Excursion Census

**Repo:** trackdco/AI-trading-agents
**Deliverable:** a measurement, not a strategy. Base rates and conditional lifts for the failed-auction and breakout arms of the 18:00–09:30 volume-profile model.
**Author of rulings:** Angus. Items marked *(assistant ruling)* were delegated and are logged as parameters, not facts.

---

## 0. Objective and non-goals

### Objective

Establish, from a complete census of value-area excursions, whether a **failed auction** predicts rotation to POC at a rate meaningfully above the unconditional rotation rate.

The POC is by construction the price at which the most overnight volume traded. Price returns there on ordinary days for mechanical reasons. **The unconditional rotation rate is therefore the null, and the only number that matters is the lift over it.** A high absolute hit rate is not a result.

### Non-goals — do not build any of these in Job 1

- No entry model, no stop placement, no targets, no position sizing, no P&L, no equity curve.
- No ICT layer (FVG inversion, CISD, breakers).
- No order-flow layer (aggressive prints, absorption, CVD).
- No optimisation for profitability. The only sweeps permitted are those enumerated in §7.
- No caps, no filters, no day limits. Completeness is the job.

If a base rate turns out to be interesting, entry mechanics are Job 2 and require a committed pre-registration document first.

---

## 1. Scope and data

| Item | Value |
|---|---|
| Instrument | NQ only *(Angus ruling)* |
| Contract | Front month, rolled per `docs/CONTRACT-ROLL-DATES.md` (volume roll, Wednesday two days before expiry) |
| Bar resolution | 1-minute |
| Timezone | `America/New_York`. Parse with `utc=True` then `tz_convert` — never localise naive timestamps |
| FIT span | 2025-06-01 → 2026-07-31 |
| HOLDOUT span | The six sealed 2023/24 months already used by the canon. Census is computed; results are sealed (§6.4) |

Footprint / volume-at-price data exists only for the FIT span. Bars exist for both spans. This asymmetry drives the ruling in §2.3 and is the single most consequential design constraint in this spec.

---

## 2. Profile construction

### 2.1 Window

For each session day `D`, the profile window is **18:00:00 ET on the prior CME trading day → 09:29:59.999 ET on `D`**, inclusive of the 18:00 bar and exclusive of the 09:30 bar.

- Sunday 18:00 opens Monday's window. This is correct and expected.
- Holidays and early closes come from the CME calendar. A session whose window contains fewer than **700 of the expected 930 minutes** of bar data is flagged `profile_status = 'INCOMPLETE'`, excluded from all base-rate tables, and reported in the completeness table. It is never silently dropped.
- Assert the expected minute count holds in **both** DST regimes. A window that is 930 minutes in November and 870 in July means the DST handling is wrong.

### 2.2 Freeze

The profile object is constructed once per session, stamped with `frozen_at = 09:30:00 ET`, and is **immutable thereafter**. No intraday recomputation, no extension, no `extend_right`.

This is the conf_PM bug class. Treat it as adversarial (see gate G1).

### 2.3 Volume source — *(assistant ruling)*

**Canonical construction for all spans is 1-minute bar volume distributed uniformly across each bar's high–low range in price bins.**

Reasoning: if the profile is built from footprint in 2025-6 and from bar volume in 2023/24, then the fit and holdout profiles are different objects and any era comparison is confounded by construction rather than regime. Comparability across eras is worth more than fidelity in one era.

The footprint construction is built too, for the FIT span only, and retained **as a comparator, not as the canonical series**.

### 2.4 Construction-validity gate — run this before anything else

A flow feature must be shown to measure what it claims before it is tested for edge. Over the FIT span, build both profiles and report:

- median and 90th-percentile `|ΔVAH|`, `|ΔVAL|`, `|ΔPOC|` in points
- **the excursion classification flip rate**: the fraction of excursions (as defined in §3) whose `failed` / `accepted` label differs between the two constructions at the canonical K

**GATE:** if the classification flip rate exceeds **5%**, the bar approximation is not a valid substitute for real volume-at-price. Stop. Report. Do not proceed to base rates on a construction that cannot be reproduced in the holdout era — because that finding means the 2023/24 months are unusable for this model, which is itself the most important thing Job 1 could discover.

If the gate passes, bar approximation is canonical everywhere and the holdout is live.

### 2.5 Bins — *(assistant ruling)*

- Canonical bin width: **1.00 index point** (4 ticks).
- Sensitivity variants: 0.25 points (1 tick) and 2.00 points.
- Report POC displacement across the three. If POC moves more than 3 points between the 0.25 and 2.00 constructions on more than 20% of sessions, POC is noise-defined at that session's range and must be reported as such — flag those sessions `poc_unstable = True` and report all tables with and without them.

### 2.6 Levels

- **POC** = centre price of the highest-volume bin. Ties broken by the bin closest to the volume-weighted mean price of the window; log every tie.
- **Value area** = 70% of window volume, expanded from POC outward using the standard paired-row rule: compare the two bins above the current region against the two bins below, add the larger pair, repeat until cumulative volume ≥ 70%.
- Sensitivity variant: single-bin symmetric expansion, and VA at 68% and 75%.
- **VAH** / **VAL** = upper and lower edges of the resulting region.

Persist to `output/vp_census/profiles.parquet`: `session_date, contract, vah, val, poc, va_pct, bin_width, total_volume, window_minutes, profile_status, poc_unstable, construction`.

---

## 3. Excursion census

Census window: **09:30:00 → 16:00:00 ET** on session day `D`.

### 3.1 Excursion start — *(Angus ruling: close beyond, not wick)*

An excursion begins on the first 1-minute bar whose **close** is strictly beyond a level:

- `side = 'above'` when `close > vah`
- `side = 'below'` when `close < val`

`excursion_start` is that bar's close timestamp. `entry_ref_price` is that bar's close price. Above and below excursions are logged independently and **are never pooled in any table** (§5.4).

### 3.2 Every excursion, with a re-arm rule — *(Angus ruling: every excursion; re-arm is an assistant ruling)*

Angus wants every excursion, not just the first of the day. Without a re-arm rule a single choppy hour generates forty near-identical rows and every significance test downstream is counting overlapping observations as independent.

**Re-arm:** after an excursion resolves, a new excursion on the same side may only begin once price has closed back inside `[val, vah]` and remained inside — no close beyond that side — for **≥ 5 consecutive minutes**.

**Clustering:** excursions on the same side, same session, whose starts are separated by less than 30 minutes share a `cluster_id`. Every significance test in §5 is reported twice: once per-excursion, once collapsed to one observation per cluster. Where the two disagree, the clustered number governs.

### 3.3 Classification — *(assistant ruling on "instant")*

The transcript never defines "instant." It is the only real free parameter in the model, so it is swept rather than guessed.

- `failed_K` = a 1-minute **close** back inside `[val, vah]` occurs within `K` minutes of `excursion_start`.
- `accepted_K` = not `failed_K`. This is the breakout arm and is measured with the same machinery.
- Canonical **K = 15 minutes**. Sweep `K ∈ {5, 10, 15, 20, 30, 45, 60}`.

15 sits in the interior of the sweep so there is a plateau to inspect on both sides. Per §5.6, the output is the response surface, not the best K.

---

## 4. Outcome measurement

For each excursion, measured forward from `excursion_start` to 16:00 ET:

| Column | Definition |
|---|---|
| `t_return_inside` | Minutes to first 1-min close back inside the value area. `NaN` if never |
| `max_beyond_ticks` | Furthest distance beyond the breached level reached before the first close back inside |
| `touched_poc`, `t_touched_poc` | Any trade at or through POC, and minutes to it |
| `closed_through_poc`, `t_closed_through_poc` | First 1-min close on the far side of POC |
| `reached_opposite_edge`, `t_reached_opposite_edge` | Touch of VAL for an `above` excursion, VAH for a `below` excursion |
| `mfe_ticks`, `mae_ticks` | Max favourable / adverse excursion from `entry_ref_price`, in the rotation direction |
| `poc_before_stop_S` | **For each `S` in {10, 20, 30, 40, 60, 80} ticks:** did price touch POC before trading `S` ticks beyond the excursion's running extreme? One boolean column per `S` |
| `session_id`, `cluster_id`, `contract`, `era` | Grouping keys |

`poc_before_stop_S` is the load-bearing column. It gives the full payoff shape across every plausible stop distance **without building an entry model**, which is what keeps Job 1 free of the parameters that would need pre-registering.

Persist to `output/vp_census/excursions.parquet`.

---

## 5. Required analysis

Every proportion is reported with a **Wilson 95% interval**. Point estimates alone are rejected.

### 5.1 Table A — unconditional (the null)

Over **all** excursions, regardless of classification: `P(touched_poc)`, `P(poc_before_stop_S)` for each `S`, `P(reached_opposite_edge)`, median `t_touched_poc`.

### 5.2 Table B — conditional on `failed_K`

Same columns, one block per `K`.

### 5.3 Table C — lift

`B − A` for every cell, with a confidence interval **on the difference**. Cells whose interval spans zero are reported as null, not as "positive but not significant."

### 5.4 Table D — by side

Everything above, split `above` vs `below`. Never pooled. Asymmetry between sides is expected and is a result in its own right.

### 5.5 Table E — by era

FIT split at 2025-12-31: discovery era 2025-H2, check era 2026-H1. **If the two eras disagree on the sign or the ranking of K, the verdict is `UNRESOLVED`** — never "take the pooled winner."

### 5.6 Table F — response surface, not argmax

Plot lift against `K`, against bin width, and against VA%. A `K` that works at 15 and dies at 10 and 20 is an artifact. Report the width of the plateau and state explicitly whether the canonical setting sits in its interior.

### 5.7 Table G — power

`n` for every cell. **Any cell with fewer than 30 excursions (clustered) is labelled UNDERPOWERED and is not ranked against anything.**

### 5.8 Placebos — both are required

1. **Stale-level placebo.** Rerun the entire census using VAH/VAL/POC taken from the profile of the session **5 trading days earlier**, applied to day `D`'s price action. If failed auctions at stale levels show comparable lift, the level is not doing the work and the finding is dead.
2. **Shuffled-level placebo.** Levels placed at the same *relative* position within day `D`'s overnight range, but with the relative positions drawn from a different, randomly chosen session. Run 20 draws and report the lift distribution.

Report the real result's percentile within each placebo distribution. Note that with 20 draws the p-value floor is 1/21 — quote the floor rather than implying more precision than the design supports.

---

## 6. Gates — must pass before any number in §5 is believed

| Gate | Check |
|---|---|
| **G1 Lookahead** | Unit test: perturb every bar after 09:30 to arbitrary values and assert `vah`, `val`, `poc` are bit-identical. Any change is a fatal lookahead |
| **G2 DST** | Expected window minute count holds in both DST regimes; no duplicate or missing timestamps at either transition |
| **G3 Roll** | Contract in use matches `CONTRACT-ROLL-DATES.md` for every session; assert no session's profile window and census window straddle different contracts |
| **G4 Determinism** | Two consecutive runs produce byte-identical parquet. All sorts use `kind="mergesort"` — the quicksort tie-ordering bug has already cost this repo a reference figure once |
| **G5 Completeness** | Every calendar session in span resolves to exactly one of: a profile, or an `INCOMPLETE`/holiday flag with a stated reason. Counts reconcile to the exchange calendar |
| **G6 Independence** | `cluster_id` populated on every row; report the distribution of excursions per session and per cluster |

`gate_report.py` convention applies: missing evidence yields `INCONCLUSIVE`, and `INCONCLUSIVE` blocks progression exactly like `FAIL`. Never infer a `PASS` from absent data.

### 6.4 Holdout sealing

The holdout census is computed and written to `output/sealed/excursions_holdout.parquet`. The reporting script **must refuse to read it** unless invoked with `--unseal` **and** `docs/PREREG-vp-excursion-census.md` exists in the commit. Job 1 does not unseal. The holdout answers "does this survive a different era," and it can only answer that once.

---

## 7. Parameter and trial ledger

Write `output/vp_census/trial_ledger.csv`, one row per configuration executed: `run_id, K, bin_width, va_pct, va_expansion_rule, construction, placebo_type, timestamp, git_sha`.

Enumerated sweep space: `K` (7 values) × bin width (3) × VA% (3) × expansion rule (2) = 126 nominal configurations, plus placebos.

State in the verdict that these are **highly correlated variants of one idea**, so the effective independent trial count is far below 126 and must be estimated by clustering the outcome series — not by counting configurations. Any Deflated Sharpe or significance figure quoted later without its trial count is decoration.

---

## 8. Verdict

Write `docs/VERDICT-vp-excursion-census.md` in this format:

```
VERDICT      LIFT ESTABLISHED / NO LIFT / UNRESOLVED / INCONCLUSIVE
MECHANISM    why a failed auction should predict rotation, and who pays for it
EVIDENCE     n excursions, n clusters, n sessions; unconditional rate; conditional rate; lift with CI
NULLS        both placebo results and the real result's percentile in each
SURFACE      plateau width across K, bin width, VA%; is the canonical setting interior?
ERA          2025-H2 vs 2026-H1 agreement or disagreement
GAPS         which numbers are unverified and what would verify them
NEXT         one test, with its acceptance bar stated now
```

Every figure must be reproducible from a named artifact. If a number cannot be traced to a file, it does not go in the verdict.

A `NO LIFT` verdict is a complete and successful outcome of this job and is reported as cleanly as a positive one.

---

## 9. Repo conventions

- Work on a dedicated branch; `git fetch` first.
- Do not touch canon files or the deployed stack.
- End the session with an explicit commit and push, and confirm it landed on origin. Work has been lost to this before.
- Artifacts: `output/vp_census/`, `output/sealed/`, `docs/SPEC-vp-excursion-census.md`, `docs/PREREG-vp-excursion-census.md` (Job 2), `docs/VERDICT-vp-excursion-census.md`.
- Layer discipline: this is L0/L1. Layers above may only remove or weight, never add, and every kill must be attributable.
