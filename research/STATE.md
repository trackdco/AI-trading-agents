# STATE — canonical figures for the NQ trading project

**Source of truth as of 2026-08-08.** Every figure here was recomputed from the underlying
file, not copied from a report. Anything quoting a number cites **this file**, not another
report. Where a report disagrees, this file wins — see
[`mismatch-report.md`](mismatch-report.md).

> ### THE HAND LOG IS A HAND-BACKTEST, NOT A TRACK RECORD
>
> **Angus has never traded this strategy.** The 28 trades are setups marked on historical charts
> — the spec says so on line 4 and this file wrote "realised" for a week anyway. Hindsight
> contamination is structural in hand-backtesting. **The 68.4% win rate cannot establish a win
> rate**; it describes the kind and scale of setup intended, nothing more. Gate arithmetic is
> unaffected — breakeven, sizing and the tripwire are computed independently — but every
> comparison against 68.4% is a sanity check, not evidence. See
> [`EVIDENCE-BASE-CORRECTION.md`](EVIDENCE-BASE-CORRECTION.md).

N_trials: **1 of 5** (Amendment 02 budget: Stage 3 ×1 · Stage 4 ≤3 · Stage 5 ×1). Consumed
2026-08-08 by sealing `workbench_results_SEALED_A15.parquet` under spec A1–A15 — **whether or
not the file is ever opened**, per the standing rule. Holdout: **SEALED.** See RULINGS below —
a seal event is on permanent record and must accompany any future holdout result.

> ### STANDING NOTE — a figure from a partial run is not a figure
>
> **Label sample scope on every reported number.** Rev 2 of the signal count reported
> frequency from a **150-session probe** and understated the full-workbench value — reading D
> came in at 1.54/session on the full 509 against a lower probe figure, and the gap was
> invisible because the scope was not on the number. A probe is for checking that code runs.
> It is not evidence about frequency, and it must never be compared against a threshold
> computed on the full sample.
>
> Every figure in this file carries its n and its scope. Anything that does not is not yet a
> figure.

---

## RULINGS

Permanent. Recorded verbatim as ruled on 2026-08-08.

> **SEAL EVENT:** on **2026-08-08**, a `*.csv` inventory read 2 rows from each of 287
> holdout-dated MBP-10 files before the date range was known. No measurement was computed on
> them; no finding rests on them. **RULING: recorded, not remediated** — the holdout's outcome
> data remains unseen. Both scripts now refuse holdout-dated sessions. **This entry is
> permanent and must accompany any future holdout result.**

> **POST-HOLDOUT MBP DATA (2026-02-01 → 2026-07-22, 223 files):** outside the declared split.
> **RULING: usable for MICROSTRUCTURE measurement only** — spread, book depth, liquidity.
> **Never for strategy-outcome computation.** If bars for this period are ever acquired it
> becomes a **fresh outcome holdout**, and prior microstructure measurement there is
> immaterial.

Scripts enforcing the first ruling: `research/star-trading/tools/mbp_census.py` (drops price
fields for holdout-dated files) and `mbp_feb2026.py` (raises `HoldoutBreach`; refuses 287 of
510). Both rulings are mirrored in `config/data_split.yaml` under `mbp10.seal_event` and
`mbp10.post_holdout`.

---

## DATA

| figure | value | source / computation |
|---|---|---|
| Archives | 4 files, `glbx-mdp3-*.ohlcv-1m.csv.zst` | repo root; exhaustive search found no others |
| Total rows | **1,656,226** | `zstd -dc \| wc -l`, minus 4 header lines |
| First bar | 2023-01-02T23:00:00Z | archive 1, line 2 |
| **Last bar** | **2026-01-30T21:59:00Z** | archive 4, last line |
| Front-month bars after spread exclusion | **1,089,712** | `alpha_data.py`, hyphenated symbols dropped |
| Globex sessions total | **796** | 18:00 ET (D−1) → 16:59 ET (D), labelled by end date |
| **Workbench** | **539 sessions**, 2023-01-03 → 2025-01-31 | 455 full-1380 |
| **Holdout (SEALED)** | **257 sessions**, 2025-02-03 → 2026-01-30 | 233 full-1380; index only, no bar content read |
| Sessions < 1380 bars | **108** | 71 missing 1–2 min, 34 holiday early close, 3 anomalies |
| Anomalies | 2023-04-07 (913), 2025-01-09 (930), 2025-11-28 (508) | Good Friday, national day of mourning, day after Thanksgiving |
| February 2026 | **0 BAR sessions** | the hand-log month has no bars — but see MBP-10 below |
| Contract rolls | 12 quarterly. **Unadjusted gaps 125.05 – 300.40 pts — see below** | 2 sessions contain an intra-session switch, both in the evening |

Bars are **open-labelled** at source (verified: median \|book_mid − bar.close\| 0.38 pts vs
6.69 vs bar.open).

### ROLL SPREADS — MEASURED, correcting "~230–250" [2026-08-08]

**The "~230–250 pt unadjusted gaps" shorthand was never right for any roll except roughly
2024-09.** Amendment 03 §1 asked for one figure corrected; measuring one invites the same error
again, so **all eight workbench rolls were measured** from the `NQxx-NQyy` calendar-spread
instrument's own quotes on the roll day — the deferred premium as the market priced it, not a
difference of two outright prints.

| roll (UTC front-month switch) | spread symbol | n quotes | **median** | min | max |
|---|---|---|---|---|---|
| 2023-03-13 | NQH3-NQM3 | 1,198 | **125.05** | 115.55 | 128.45 |
| 2023-06-12 | NQM3-NQU3 | 1,280 | **180.75** | 175.50 | 186.10 |
| 2023-09-11 | NQU3-NQZ3 | 1,127 | **197.90** | 194.95 | 199.35 |
| 2023-12-11 | NQZ3-NQH4 | 1,343 | **210.80** | 208.30 | 214.05 |
| 2024-03-11 | NQH4-NQM4 | 1,261 | **247.65** | 242.70 | 255.10 |
| 2024-06-17 | NQM4-NQU4 | 1,090 | **264.15** | 259.55 | 272.35 |
| 2024-09-16 | NQU4-NQZ4 | 1,101 | **236.00** | 230.30 | 239.95 |
| **2024-12-17** | **NQZ4-NQH5** | 1,341 | **300.40** | 295.75 | 305.85 |
| | | | **median 223.40 · mean 220.34 · range 125.05 – 300.40** | | |

**At the exact splice minute of the 2024-12-17 roll (2024-12-16 23:28 ET) the quote is 301.15**
— the figure cited in `vwap-bb/PARITY-P2-RESULT.md` §1.2. **The spread grew monotonically apart
from one dip, roughly tracking the rate environment: it is not a constant and must not be quoted
as one.**

**The four remaining rolls (2025-03-18, 2025-06-16, 2025-09-15, 2025-12-15) were REFUSED — they
are holdout-dated.** The measurement script guards on `WORKBENCH_END` and printed the refusal.

**Where this figure lived.** Amendment 03 names `research/data-audit.md`; **that file does not
exist in this repository.** The Stage 0 audit's data figures live here, in this file's DATA
section, which is the declared source of truth. The stale round number is corrected here and in
`prereg/layer-01-deseasonalisation-release.md`. Recomputed by
`research/star-trading/tools/roll_spreads.py`.

### MBP-10 — corrected 2026-08-08

**510 MBP-10 CSV files sit in the repository root.** The earlier entry here ("irrelevant") was
wrong. Census: `research/star-trading/tools/mbp_census.py`.

| family | files | dates | ET window | rows/file | symbol |
|---|---|---|---|---|---|
| `glbx-mdp3-<date>.mbp-10_condensed.csv` | 295 | 2025-06-02 → 2026-07-22 | 03:00–04:59 | 120 | NQ.v.0 |
| `condensed_glbx-mdp3-<date>.mbp-10.csv` | 115 | 2025-06-02 → 2025-11-20 | 08:00–10:29 | 150 | NQ.c.0 |
| `condensed_GLBX-<hash>.csv` | 100 | 2026-02-02 → 2026-07-08 | 08:00–10:29 | 150 | NQ.c.0 |

**All 19 hand-log dates have a file; 17 of 20 February 2026 trading days have one overlapping
RTH.** One book snapshot per minute (`ts_event` at `:00`, flags 128) — top-10 book plus the
single event that produced it.

**Cannot be derived:** intra-minute high/low (no OHLC, no wick, no trigger candle), traded
volume (no VWAP, no POC), anything after 10:29 ET. **The detector cannot be run on this
schema** — three of its four inputs are absent. What it *can* measure is the spread; see COSTS.

**Classification — RULED 2026-08-08.** 2026-02-01 → 2026-07-22 (223 files) is neither workbench
nor holdout. Usable for **microstructure only**; never for strategy-outcome computation. If
bars are ever acquired for it, it becomes a fresh outcome holdout. See RULINGS.

## HAND LOG

Source: `data/reference/feb2026_hand_log.csv`, unmodified. Scope ruling:
`data/reference/hand_log_scope.md`.

| figure | FULL log | IN-SCOPE (≥09:36, per A1) |
|---|---|---|
| Trades | **28** | **19** |
| Win / loss / BE | **20 / 7 / 1** | **13 / 5 / 1** |
| Win rate | 71.4% | **68.4%** |
| Wilson 95% | [52.9%, 84.7%] | **[46.0%, 84.6%]** |
| Mean R, winners | 4.226 | **3.678** |
| Median R, winners | 3.680 | **3.370** |
| Max R, winners | 12.98 *(out of scope)* | **5.98** |
| Mean R, losers | −0.907 | −1.000 |
| Mean R, all | 2.792 | **2.254** |
| Median stop, points | 32.75 | **35.00** |
| Stop range, points | 8.25 – 65.00 | 11.00 – 65.00 |
| Trades / session | 1.474 | **1.000** |
| Sessions with ≥1 trade | 19 of 19 | **15 of 19** |
| One-sided binomial vs p₀=0.406 | 0.00095 | **0.01332** |

Date span: 2026-02-02 → 2026-02-27, **19 distinct sessions**.

> **The "+4.23R on winners" figure is the FULL-log mean and includes the +12.98R trade, which
> A1 places out of scope. The in-scope figure is 3.678 mean / 3.370 median, n = 13.**
> **Corrected everywhere 2026-08-08** — `preflight.md` (×2) and `hand_log_scope.md`. No
> document now carries 4.23 as a live figure; it survives only where labelled as the wrong
> number.

**Not in the source file:** entry, stop and target *prices*. Only distances, risk $, R
multiples and P&L are recorded. Any per-trade price figure would be fabricated.

## SPEC

Frozen at gate 4 (`preflight.md` rev 2, A2) and extended by A4/A5. **Zero fitted — no
parameter here was set by comparing outcomes.**

| # | parameter | value | tag | source |
|---|---|---|---|---|
| 1 | VWAP typical price | HLC/3 | **[SPEC]** | A2 — §2 "standard TradingView VWAP" |
| 2 | Volume-profile bin | 1.00 point | [FIAT] | A2 |
| 3 | HTF classification | 15m fractal N=2; HH+HL up, LH+LL down, else range | [FIAT] | A2 |
| 4 | Stop buffer | 1 tick beyond the wick extreme | [FIAT] | A2 |
| 5 | Volatility stand-down | DISABLED for v1 | [FIAT] | A2 |
| **6** | **Minimum stop distance** | **10.00 pt (40 ticks)** | **[FIAT]** | **A5 — 2026-08-08** |
| **7** | **Target selection ("valid")** | **first ladder level clearing the RR floor** | **[FIAT]** | **A4 — 2026-08-08** |
| **8** | **Vault selector** | **first-come, signal-time order** | **[FIAT]** | **A7 — 2026-08-08** |
| **9** | **Candidate during an open position** | **discarded, not queued** | **[FIAT]** | **A7 — 2026-08-08** |
| **10** | **Tie-break, level 1** | **highest entry TF** | **[SPEC]** | §1 MTF arbitration, CONFIRMED — Angus |
| **11** | **Tie-break, levels 2–5** | stand down on conflict → largest cluster → nearest cluster → lowest cluster low | [FIAT] | A7 — **levels 3–5 never fire** |

| figure | value |
|---|---|
| Free parameters | **13** (9 CALIBRATE + 4 TOURNAMENT axes); was 18 before the A2 freeze |
| Tournament configuration space | **72** (W×E×V×weekly), V3 struck by A6; **30** under §12.3's stated grid |
| Management axis | **4** — V0, V1, V2, V4 (V3 struck, A6) |
| **N_trials** | **0** |

**§5.4 stop rule, as amended (A5):** *"Stop: beyond the wick extreme of the trigger candle /
displacement origin. Structural, never widened (Vault-enforced). **Minimum stop distance:
10.00 points (40 ticks). Effective stop = max(structural stop, 10.00 pt).**"*

**§6 rule 5, as amended (A4):** *"Walk the ladder of opposing menu levels outward from entry.
The working target is the first level whose front-run-adjusted distance is ≥ 1.5R. Skip only if
no level in the menu clears the floor."* Superseded reading: test rung 1 only, then skip.

**§10 Vault, verbatim:** *"Max trades/day: **3** (config 2–3; Angus: 'no more than 2–3
genuinely high-probability setups exist per day')."* … *"One position at a time; no stop
widening; EOD flatten (§1); drawdown kill-switch vs trailing DD buffer; size ceiling from
MC."* **No ranking metric appears anywhere in §10.**

**§9 conviction, verbatim:** *"Full unit vs half unit per conviction score: full requires 3+
confluences AND (with-trend OR A-at-extension) AND target ≥2R; any of {2 confluences,
oversized stop, late-window entry, thin target} → half."* **Scoped to sizing, not selection.**

## CANDIDATES

Source: `research/vwap-bb/data/candidates.parquet`.

| figure | value |
|---|---|
| Total records | **45,214** (22,581 `prior` + 22,633 `rth`, × 4 readings) |
| Sessions: detector ran | **496** |
| Sessions: ≥1 candidate | **483** (482 under `prior`) |
| Zero-candidate sessions | **13** — full sessions, no qualifying trigger |
| Skipped | **43** — holiday/short 21, mixed contract 6, roll 8, session-after-roll 8 |
| Reconciliation | 539 = 496 ran + 43 skipped; 496 = 483 with candidates + 13 without ✓ |

Per session, warmup `prior`, **pre-Vault-cap**:

| reading | raw records | raw /sess | deduped by close-minute | deduped /sess |
|---|---|---|---|---|
| A | 12,595 | 26.13 | 9,558 | **19.83** |
| B | 5,622 | 11.96 | 4,084 | **8.69** |
| C | 2,766 | 6.09 | 2,489 | **5.48** |
| D | 1,598 | 4.24 | 1,461 | **3.88** |

> **Units matter.** `signal-count.md` reports deduplicated signal-minutes; the parquet stores
> one row per (cluster × direction × entry-TF). Compare only like with like — mismatch #4.

**Stop distance, reading A, points:** mean 4.204 · **median 3.125** · min **0.0125** · max
54.84 · p10 0.600 · p90 9.088. Under 1pt **17.9%**, under 5pt 68.8%, under 10pt 92.1%.

> Against the hand log's median of 35.00 points, the spec geometry is **~11× tighter**. This
> invalidates every R-normalised field in the parquet — see
> [`opportunity-set.md`](vwap-bb/opportunity-set.md) §1.

Conviction score (3-valued): **1: 2,540 · 2: 14,716 · 3: 5,325**.
Blocked under first-come, reading A: **54.2%**. Overlap (time-rank-1 = conviction-rank-1):
**A 38.8% · B 47.7% · C 54.6% · D 65.3%**.

## GATES 1–6

| gate | status | the number it rests on |
|---|---|---|
| 1 SIZING | **PASS** | Median MNQ risk $19–43/contract vs a $2,000 allowance |
| 2 SESSION OVERLAP | **RESOLVED** | Ruled RTH 09:36 (Amendment A1); 9 of 28 trades out of scope |
| 3 BREAKEVEN | **PASS — re-derived 2026-08-08** | p₀ = **43.90%** at the A5 floor s=10.00, c=0.975, R=1.5. c/s = **9.75%** (was 1.53%). Clears the 68.4% point estimate by 24.5 pt; clears the 46.0% Wilson lower bound by **2.1 pt at base, 0.0 pt at adverse** |
| 4 SPECIFIABILITY | **REOPENED 2026-08-08** | Was closed by A7. **Reopened:** two of Angus's own skip criteria have no stated rule — unfilled range, and liquidity swept. Gate 4's termination test is whether an unhandled state changes the sign of expectancy, which **cannot be known without reading the sealed result**, so this cannot be re-closed by argument |
| **4b LITERALISM** | **NEW — FIRED 3×** | Stop 11× tighter than intent; target 19.5× nearer; Vault cap acting as selector. See the runbook |
| 5 DATA FEASIBILITY | **CLOSED — SCOPE ACCEPTED** | Feb 2026 bars absent; MBP-10 present but cannot produce VWAP/POC/wick. Parity relocated, calibration downgraded (A6) |
| 6 SAMPLE SUFFICIENCY | **PASS** at every axis structure tested | **Recomputed at the new p₀ = 43.90%:** required n is 411 (÷1) to 1,083 (÷72); available is 1,185–1,450. The old 0.4862 tripwire assumed p₀ = 0.406 and is superseded — at ÷4 it is now **1.172 trades/session**. Measured 2.328–2.849 clears every divisor. See `research/prereg/axis_decision.py` |

Gate-6 arithmetic, recomputed at p₁=0.50, p₀=0.406, 80% power, 539 sessions:

| correction | required n | tripwire |
|---|---|---|
| ÷1 | 170.9 | 0.3170 |
| **÷4 (current, V3 struck)** | **262.1** | **0.4862** |
| ÷5 (superseded) | 276.6 | 0.5132 |

Cost-adjusted breakeven is now computed on the **measured** cost ladder — see COSTS for the
full table. The c=0.25 column is retired and must not reappear.

> The 3.12-point spec-geometry row was the live problem: costs alone lifted breakeven to
> **52.50%** at the measured base. **A5's 10.00-point floor closes it** — breakeven at the base
> cost falls to **43.90%** and the cost ratio from 31.25% to 9.75%.

## COSTS

### The cost model, as ruled 2026-08-08

| case | round-trip cost | basis |
|---|---|---|
| optimistic | **0.50 pt** | tighter than measured; retained as a stress case in the favourable direction |
| **base** | **0.975 pt** | **measured median spread 0.75 + commission 0.225** |
| adverse | **1.50 pt** | approaching the measured p90 spread (1.50) plus commission |

**The 0.25 "lean" case is RETIRED.** It is below one tick of spread and was never attainable
on a stop exit. It must not reappear in any table.

Superseded ladder, for traceability only: 0.25 / 0.50 / 1.00 (lean / base / adverse), declared
and unverified.

### The measurement

NQ = $20/point, tick 0.25. Entry is a limit at a level and the target is a limit at a level, so
the spread is crossed once — on the stop exit. Commission ≈ $4.50 RT = 0.225 pt.

MBP-10 book snapshots, **5,781 RTH samples over 99 sessions, 2026-02-02 → 2026-07-08**
(post-holdout only, per the RULINGS above; `mbp_feb2026.py`):

| | value |
|---|---|
| top-of-book spread, median | **0.75 pt (3 ticks)** |
| p25 / p75 / p95 | 0.75 / 1.00 / 1.75 |
| ticks | 2t 13.3% · **3t 44.7%** · 4t 23.4% · ≥5t 18.6% |
| inside size (bid+ask) | median 3 contracts |
| **implied stop-exit cost, median** | **0.975 pt** (spread + 0.225 commission) |
| implied stop-exit cost, p90 | **1.725 pt** |

Not a cancel artefact — adds median 0.75, modifies 0.75, cancels 1.00.

### Breakeven `p₀ = (s + c) / (s(1 + R))`, R = 1.5, recomputed on the ruled ladder

| stop s (pts) | c = 0.50 (optimistic) | **c = 0.975 (BASE)** | c = 1.50 (adverse) | c/s at base |
|---|---|---|---|---|
| 3.12 — old frozen geometry | 46.41% | **52.50%** | 59.23% | **31.25%** |
| **10.00 — §5.4 floor (A5)** | 42.00% | **43.90%** | 46.00% | 9.75% |
| 15.00 | 41.33% | **42.60%** | 44.00% | 6.50% |
| 20.00 | 41.00% | **41.95%** | 43.00% | 4.88% |
| 21.50 — gate-1 proxy, 5m | 40.93% | **41.81%** | 42.79% | 4.53% |
| 32.75 — hand log, full | 40.61% | **41.19%** | 41.83% | 2.98% |
| **35.00 — hand log, in-scope** | 40.57% | **41.11%** | 41.71% | 2.79% |

At the hand log's realised R of 3.678 and c = 0.975: p₀ = **23.46%** at s = 10.00, **21.97%**
at s = 35.00. The in-scope hand-log win rate is 68.4%, Wilson lower bound 46.0%.

> **Gate 3 re-derived formally 2026-08-08 — PASS confirmed, margin materially reduced.**
> A5's floor cuts the cost ratio from 31.25% to 9.75% and breakeven from 52.50% to **43.90%**.
> But measured against the **original** gate-3 basis (s=32.75, c=0.50, p₀=40.61%) the cushion
> over the 46.0% Wilson lower bound has fallen from **4.8 pt → 2.1 pt at base and 0.0 pt at
> adverse**, because cost rose and the stop fell together. Full working in `preflight.md`
> gate 3. Against the *point estimate* of 68.4% the margin is 22–26 pt at every cost level.

### COST BASIS — ruled 2026-08-08

> **0.975 is measured on 09:30–10:29, which holds ~9.7% of signals. The signal distribution is
> near-uniform across RTH, so this is CONSERVATIVE BY CONSTRUCTION — the widest hour applied
> everywhere — not representative. At the 10 pt floor the full 0.50–1.50 range moves breakeven
> by 4.0 points, so the strategy's viability does not hinge on which value is chosen.**

The 4.0-point span: at s = 10.00, p₀ runs **42.00% (c=0.50) → 46.00% (c=1.50)**. The in-scope
hand-log win rate is 68.4% with a Wilson lower bound of 46.0%. The cost choice moves breakeven
by less than the width of the confidence interval on the win rate — it is not the deciding
variable and should not be argued about further.

**Basis for "widest hour" — CORRECTED 2026-08-08 by the Stage 4 measurement.** The ruling's
conclusion may hold; **its stated justification does not.** Across the eleven 30-minute buckets
with data, **09:30–10:29 is the TIGHTEST**, at 0.75 median against 1.00–1.25 in every earlier
bucket (overnight 03:00–05:59 and pre-market 08:00–08:59). Nine of the eleven are outside RTH
and carry no signals, so **within RTH only this one hour is measured and nothing can be
established about whether it is widest, narrowest or typical.**

What survives is directional and weak: p90 falls 1.50 → 1.25 across 09:30 → 10:29, so the trend
at the right edge of the measured window is still tightening. **That is an argument from a trend
inside a 10% slice, not a measurement.** Post-10:29 spread is unmeasured — every MBP file ends
at 10:29 or 04:59.

**No figure or verdict changes.** The 0.50–1.50 range moves breakeven by 4.0 points at the A5
floor, less than the width of the confidence interval on the win rate. What changes is only what
may honestly be said about *why* 0.975 is defensible. See
[`STAGE4-ORDERFLOW.md`](vwap-bb/STAGE4-ORDERFLOW.md) §4.

### Correction — the earlier representativeness claim was wrong

**It was claimed the signal distribution peaks 10:00–10:30. It does not.** Deduplicated
signal-minutes by 30-minute bucket over the workbench (reading A, pre-RR-floor, n = 20,357)
are close to uniform across RTH — 7.0% to 9.5% per bucket, largest at **12:00–12:29 (9.5%)**,
while 10:00–10:30 is **7.0%**, below average:

| bucket | 09:30 | 10:00 | 10:30 | 11:00 | 11:30 | 12:00 | 12:30 | 13:00 | 13:30 | 14:00 | 14:30 | 15:00 | 15:30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| share | 2.6% | 7.0% | 7.5% | 7.6% | 7.3% | **9.5%** | 8.0% | 8.7% | 8.1% | 8.3% | 7.4% | 8.4% | 8.8% |

**The window covers 9.7% of the signal population by weight** — a 10% slice, not a
representative sample. Per the ruling above it is treated as **conservative**, not
representative: the widest measured hour applied to all hours.

Other caveats: point samples at minute boundaries, not time-weighted; continuous `NQ.c.0`;
sample period 2026-02 → 2026-07, which is neither workbench nor any period a result is fitted
on.

## OPEN ITEMS

| item | blocks | status |
|---|---|---|
| **§6 rule 2 defaults ambiguous and unimplemented** | Nothing — tournament variant | Pattern A's default target is "VWAP middle", but 85.4% of entries sit *inside* the firing cluster, which contains it. The A/B/B2 taxonomy (§4) is not implemented. **A4 supplies a working rule without it**, so this is a variant to test, not a blocker. Angus should still rule |
| **Stop anchor unconfirmable from data** | Nothing — A5 makes it non-blocking | Alternatives measured (prior swing 16.29, 2×ATR 25.32 vs frozen 5.62 pts). The hand log records **no entry/stop/target prices**, so no anchor can be confirmed from data. A5's floor makes the spec executable without it; the residual shows up as 5–7 min holds against the human's ~30. Requires Angus or marked-up charts. **NOT timeframe-dependent:** the four 1M hand-log entries carry stops of **33.00, 32.50, 26.50 and 44.25 pts** against an A5 floor of 10.00 and a detector median of 3.12 — the reference trader used ~30 pt stops even on 1-minute entries |
| **E1 + wick degenerate on 29.6% of triggers** | Nothing — E1 is one of three tournament entries | Entry falls on the wrong side of the wick extreme; those triggers are skipped. A5 deliberately does not rescue them. E2/E3 may not share the defect — the tournament will show it |
| **DEFERRED CAPABILITY — holdout depth data** | Nothing now; improves the cost model later | When the holdout is opened its MBP-10 becomes readable and can validate the cost model **against the very sessions the verdict rests on** — strictly better than the post-holdout window. 287 files, 2025-06 → 2026-01. **Recorded so it is not forgotten** |
| **Spread unmeasured after 10:29 ET** | Nothing — ruled conservative | 90% of signals fire in hours with no spread data. Ruled: treat 0.975 as the widest hour applied everywhere. The 0.50–1.50 range moves breakeven by 4.0 pts at the A5 floor, so nothing hinges on it. Would need MBP files with a later window to improve |
| **Pre-open warm-up bias** | Study design | BB(20)/ATR(20) at 09:36 read bars 1.65× quieter than RTH. Measured effect on counts: −0.8% |
| **SPEC OMITS TWO OF ANGUS'S ENTRY CRITERIA** | **Gate 4 REOPENS; the hand log as evidence** | Asked why he'd skip a valid setup he cited **unfilled range** (zero occurrences in the spec) and **no liquidity swept** (present only as a *target* concept; the MIG tool was explicitly EXCLUDED and deferred). **The hand log's 68.4% was produced WITH these filters; the spec runs WITHOUT them — they are not the same strategy.** Both computable from held bars. See [`MISSING-ENTRY-CRITERIA.md`](vwap-bb/MISSING-ENTRY-CRITERIA.md) |
| **§7 invalidation-at-entry: which "opposing ±1σ"?** | The traded population, more than anything else outstanding | Spec marks it **[Hypothesis — test]** and never disambiguates. As implemented (band you move toward) it blocks with-trend longs on **79–100% of minutes** on a trend day and makes the spec fade the trend; the other reading blocks almost none. On 2025-01-15 it killed **30 of 51** candidates in 09:36–10:10, including the setup Angus says he'd have taken. Needs Angus |
| **POC binning: 1.00-pt bins vs TradingView's 24 rows** | Cluster formation | At 24 rows the detector reproduces Angus's POC to 0.25, so the arithmetic agrees — but 24 rows locates the POC to ±8.75 pt, **coarser than the 10-pt cluster tolerance**. The spec should say which resolution it means |
| **INDICATOR FEED TIMEFRAME UNSPECIFIED** | **The whole level set. Largest item on the project** | §2 says *"standard TradingView VWAP"* — an indicator whose value depends on the **chart's timeframe** — and never names the feed. Same for the volume profile. Angus's chart is **2m**; the detector computes from **1m**. Recomputing on 2m reproduces his daily VWAP to **0.002**, NY VWAP mid to **0.07**, NY σ to **0.02** and the POC to **0.50**. Unresolvable by any implementation as written: §1 evaluates four entry timeframes at once, so no single feed matches all four. **Consequences measured at P2: NY ±1σ off by 3.23/7.81, ±3σ by up to 19.10, POC by 44.50.** Needs Angus |
| **4h RANGE — implementation contradicts the reference** | §7 location filter; §6 menu | Reference definition set at P2: **swing highs and lows** (method still unspecified). Implementation: **fixed 240-min clock blocks, ≤6, reset every session, current partial block excluded**. At 2025-01-22 09:50 that gives 21768.25/21920.00, width **151.75**, against the chart's 20695.50/22428.75, width **1733.25** — a factor of **11**. Price sits at **143.99%** of the detector's own range against **74.50%** of the chart's: opposite sides of the 0.80 block threshold. **A "range" price sits 44% above is not a range under any reading of §7** |
| **15m FRACTAL — tie handling unstated** | The HTF flag, hence every counter-trend confluence minimum | A2's frozen rule says *"15m fractal N=2"* and does not say how to treat **equal** extremes. On 2025-01-22 the 08:30 and 08:45 bars both print **21934.25** to the tick; the strict `>` test admits **neither**, so the detector falls back to 21905.00 @ 06:15 → lower high → **range**, while Angus reads 08:45 → higher high → **uptrend**. Three of the four swings matched to ≤0.25; the flag turns entirely on the tie |
| **PARITY 1m BLIND SPOT** | Nothing at P2 — **moot**. Live elsewhere | Entry-TF distribution in the hand log is **1M:4 / 2M:6 / 3M:7 / 5M:11** (full) and **1M:2 / 2M:6 / 3M:4 / 5M:7** (in-scope), so 1m is a timeframe the reference trader uses; Angus's platform has no 1m history for January 2025. **Materiality determined at Stage B: the detector produces zero 1m triggers at the P2 instant, so the gap costs that gate nothing.** It is not resolved — across 09:36–09:50 the detector produced **11 raw 1m trigger events**, three carrying 2 cluster types, at minutes that could not be checked. A gate one minute earlier would have been incomplete |
| **Prior-week H/L reading unreconciled** | Nothing — level not implemented | Angus 21686.75 / 20687.00 against a Sunday-18:00-anchored archive measurement of 21682.50 / 20694.00: **+4.25 / −7.00**. His week-to-date reading reconciled exactly (21988.00, and 21377.75 vs 21378.00), so the anchor is right and the prior-week bar is not. Not diagnosed — the detector computes no weekly level, so it is outside the parity comparison |
| **Calibration gate downgraded** | Phase 2 sign-off | Irrecoverable *as a bar-based gate* — Feb 2026 has no bars, and the MBP schema cannot produce the detector's inputs. §12.2 corrected by A6 |

**Closed 2026-08-08:**

| item | how |
|---|---|
| **Vault selector unstated — the last gate-4 item** | **A7.** First-come by elimination: ranking needs lookahead, thresholding needs a score with resolution and §9's is 3-valued with two-thirds on one value. §10.1 states admission order, discard-not-queue, the 3/day cap and a five-level tie-break. **Gate 4 CLOSED** |
| Spec stop geometry ~11× tighter than the hand log | Diagnosed, then amended. Not a stop-anchor problem alone — the target was 19.5× nearer too, so both ends compressed together and the R-multiple looked healthy. **A5** floors the stop at 10.00 pt; cost ratio 31.25% → 9.75% |
| §6 target rule discards viable targets | **A4** — "valid" disambiguated to "clears the floor". The RR floor now removes 4.6–11.7% of stage-0 instead of ~25%, and screens target quality rather than stop size |
| H1 — entry timeframe | **REJECTED.** The gap is 8.5–11.2× within every timeframe, tested against the hand log's own `Entry TF` column |
| V3 unreachable under RTH | **A6** — struck. Management axis 4, configuration space 72 |
| §12.2 described a calibration that cannot run | **A6** — corrected |
| 2026-02-01 → 2026-07-22 unclassified | **RULED** — microstructure only. Mirrored in `data_split.yaml` |
| Seal-boundary read | **RULED** — recorded, not remediated. Permanent entry in RULINGS; both scripts guarded |
| Gate 6 under the amended rules | **CONFIRMED** — 2.328–2.849 trades/session under A4+A5+A7 against a 0.4862 tripwire |
| Cost-basis representativeness | **RULED** — conservative by construction, and the 0.50–1.50 range moves breakeven by 4.0 points at the A5 floor. Earlier "peaks in the measured window" claim corrected: it does not |
| Partial-run figures | **STANDING NOTE** added at the head of this file — a figure from a partial run is not a figure |
| Gate 3 re-derived at the measured cost | **DONE.** p₀ = 43.90% at the A5 floor. PASS confirmed, but the cushion against the Wilson lower bound fell from 4.8 pt to 2.1 pt at base and 0.0 pt at adverse. Recorded in `preflight.md` gate 3 |
| "+4.23R" scope error | **CORRECTED** in `preflight.md` (×2) and `hand_log_scope.md`. In-scope: mean 3.678, median 3.370, max 5.98, n=13 |
| One-position lockout placeholder | **RETIRED.** The 30-min proxy is replaced by actual resolution timing in the A7 count. Median hold measured at 5–7 min |

---

*Recomputation scripts: `research/star-trading/tools/{alpha_data,vwapbb_signals,vwapbb_opportunity,vwapbb_analyse}.py`.
Full comparison against reported values: [`mismatch-report.md`](mismatch-report.md).*

---

## GEOMETRY (added 2026-08-08)

Source: `research/vwap-bb/data/geometry.parquet` — 63,195 records, **pre-RR-floor**, 496
sessions, warmup `prior`. Reading A: 33,993 records, 490 sessions.

| figure | value |
|---|---|
| Stop, wick+1tick, **pre**-RR-floor median | **5.62 pts** |
| Stop, wick+1tick, **post**-RR-floor median | **3.12 pts** (`candidates.parquet`) |
| Triggers with no valid wick stop (entry ≤ stop) | **29.6%** |
| Entry inside the firing cluster | **85.4%** |
| Target: nearest rung, median | **7.95 pts** |
| Target: 2nd / 3rd rung, median | 20.88 / **37.36 pts** |
| Target: nearest liquidity extreme, median | **75.76 pts** |
| Target: deepest rung in menu, median | **192.36 pts** |
| Hand log, in-scope winners' implied target | **155.2 pts** (median, n=13) |
| Records with a rung ≥ 155.2 pts available | **63.3%** |

> The 1.5R floor **selects for small stops**: it moves the median stop from 5.62 to 3.12.

Feasibility map (min-stop floor × target rung, tripwire 0.4862 as a selector-free session
floor) is in [`target-stop-reconciliation.md`](vwap-bb/target-stop-reconciliation.md) §5. The
feasible region is **not empty**: every 3rd-nearest cell clears the tripwire, including a
35-point floor (0.765). The nearest-target column fails from a 20-point floor upward.

---

## SIGNAL COUNT under A4 + A5 (rev 3, added 2026-08-08)

Source: `research/star-trading/tools/vwapbb_signalcount_amended.py`. **Full workbench, 509
sessions** (rev 2 used a 150-session probe). Entry logic only — no outcomes, no P&L.
Holdout never addressed.

Signals per session, after each cascade stage:

| stage | A | B | C | D |
|---|---|---|---|---|
| 0 raw + §7 confluence | 93.83 | 42.92 | 31.21 | 22.08 |
| 1 + §7 invalidation | 49.13 | 23.43 | 16.17 | 10.22 |
| 2 + §7 location | 40.82 | 18.50 | 12.86 | 8.54 |
| 3 + §6.5 RR floor **(A4)** | 29.89 | 16.53 | 11.12 | 7.15 |
| 4 + §10 Vault 3/day | 2.93 | 2.89 | 2.83 | 2.54 |
| **5 + one-at-a-time** | **2.83** | **2.75** | **2.66** | **2.24** |

**Every reading CLEARS the 0.4862 tripwire**, by 4.6× to 5.8×. Gate 6 holds under the
amendments.

### Against the superseded rules, like for like

Rev 2's rules re-run over the same 509 sessions (stages 0–2 are untouched by the amendments and
are identical, which is the control):

| stage | A rev2 → rev3 | B rev2 → rev3 | C rev2 → rev3 | D rev2 → rev3 |
|---|---|---|---|---|
| 3 + RR floor | 19.81 → **29.89** | 8.47 → **16.53** | 5.21 → **11.12** | 3.08 → **7.15** |
| 5 final | 2.72 → **2.83** | 2.48 → **2.75** | 2.21 → **2.66** | 1.54 → **2.24** |
| RR floor removes | 22.4% → **11.7%** | 23.4% → **4.6%** | 24.5% → **5.6%** | 24.7% → **6.3%** |

> **The amendments did not rescue frequency — frequency was never at risk.** Rev 2 already
> cleared the tripwire on the full workbench (1.54–2.72/session; the rev-2 report's lower
> figures came from a 150-session probe). What changed is *what the RR floor screens on*: it
> now removes 4.6–11.7% of stage-0 instead of a flat ~24%, because it stops discarding setups
> the menu already carried a valid target for. The final count rises 4% (A) to 45% (D), and
> the Vault cap absorbs most of the difference.

Two things the cascade shows:

- **The RR floor now removes 4.6–11.7% of stage-0**, against ~25% under the superseded
  nearest-level reading. A4 did what it was meant to: the floor stopped discarding setups the
  menu already carried a valid target for. It is now a screen on target quality rather than a
  proxy for tiny stops.
- **The Vault cap is doing 21–32% of all filtering** — more than any spec filter except
  invalidation — and stage 4 → 5 moves the count by 0.10 or less. **The 3/day cap, not the
  strategy, is setting the trade count.** That is the gate-4 selector problem restated in
  frequency terms and it is still open.

Frequency is not this strategy's constraint and never was: 2.83/session against a hand-log
1.00 and a tripwire of 0.486. **The open question is which 3 of ~30 qualified candidates get
taken, and the spec still does not say.**

---

## SCOPE RULING — nine spec branches OUT OF SCOPE (2026-08-08)

> **This study tests the spec AS IMPLEMENTED, at the pinned provenance hashes. The unimplemented
> branches are formally OUT OF SCOPE for this run. The seal stands.**

Out of scope, each quoted in [`OUT-OF-SCOPE-BRANCHES.md`](vwap-bb/OUT-OF-SCOPE-BRANCHES.md):
**§4 A/B/B2 taxonomy · §6 rule 2 pattern targets · §6 rule 3 news override · §6 rule 6 alignment
bonus · §10 daily halt · §5.5 T_cancel · §2 VAH/VAL/HVN/LVN · §2 Asia/London/NY boxes · §6 menu's
weekly H/L, pullback origin, HTF range extremes.**

**Every omission is permissive.** None could add a candidate. **The tested population is less
selective than the full spec intends.**

> **THE ASYMMETRY. A PASS is trustworthy — it survived a looser population and a worse fill
> (§4.2 next-bar-open) than the spec specifies, which establishes that the edge is present
> WITHOUT the refinements meant to help. A FAIL is AMBIGUOUS — the missing branches might have
> removed the losing trades, so it cannot distinguish "does not work" from "was missing the parts
> that make it work." A fail must not be reported as a verdict on the strategy.**

> **The pass does NOT carry over if the branches are later implemented.** That is a new
> specification and requires a new test. *"We already validated it, and the filters were designed
> to help, so adding them can only improve things"* is **invalid**: the filters shrink the trade
> set, and a mean over a subset is not guaranteed to beat the mean over the superset.

**Cost to bring them in: ≈23 new [FIAT] parameters** (taxonomy 9, rule 2 4, alignment 2,
T_cancel 1, VAH/VAL 2, session boxes 3, menu 2; daily halt 0) **plus an economic calendar the
project does not hold.** The A2 freeze moved 18 → 13 and was treated as significant; this would
add 23. It also voids the spec hash, this pre-registration and the seal, and reopens gate 4 on
all 23. **Not an afternoon.**

**§10's daily halt is flagged separately**: the spec states both values (2 losses, −2R), so it
was implementable and simply not built. An omission, not a specification gap.

> ### DRAWDOWN CARVE-OUT — ruled 2026-08-08
>
> **Drawdown is REPORTED but is NOT a binding pass criterion for this run.**
>
> The other eight omissions are permissive — they bear on *which trades* are in the sample. The
> daily halt is a **loss-limiting device**, and its absence changes **how deep a bad session
> goes**. Under V0 every stop is exactly −1R, so §10's two halt conditions coincide and the
> distortion is exact: worst session **−2R with the halt vs −3R without — exactly 1.50×**
> (21.95 vs 32.93 pts; $439 vs $659 on 1 NQ at the A5 floor, c=0.975).
>
> **The carve-out is unambiguously conservative, because of which statistic binds.** For a
> trailing-drawdown account the binding statistic is the **peak-to-trough excursion**, not the
> mean — one breaching session ends the account whatever the average is. The tail is worse by
> construction and nothing in the run makes a fully-losing session shallower than −2R. Sessions
> with under two losses are unaffected and a session whose third trade *wins* finishes better,
> so the *mean* could move either way; that is true and beside the point, because a mean
> drawdown does not breach a trailing limit.
>
> **The 1.50× is V0-only.** Every stop is exactly −1R there, which is why §10's two halt
> conditions coincide. Under **V1 / V2 / V4** a break-even exit produces 0R, the conditions
> diverge, and **this analysis must be redone before those variants are run.**
>
> **A drawdown failure is therefore not a verdict on the spec.** If the result fails on drawdown
> alone, re-test with the halt implemented — **cost: 0 new parameters**, since §10 states both
> values. It is the only out-of-scope item that is recoverable by a re-run rather than blocked
> behind ≈23 invented parameters.
>
> **Expectancy and win-rate criteria are unaffected** — those rest on the permissive omissions
> only.

---

## STAGE 2 — SEALED WORKBENCH RESULT (2026-08-08)

`research/vwap-bb/data/workbench_results_SEALED.parquet` — **1,423 trades, 501 sessions,
35 columns.**

| | |
|---|---|
| **SHA-256** | **`a9ddc2947ca6a5f4c7e453d90427bed91710d1bc94c86de81fa9b381739bd4f0`** |
| Reproduced byte-identical on a second run | **yes** |
| Trades / session | **2.8403** — clears every §6 tripwire from /1 (0.7631) to /72 (2.0091) |
| Excluded | 38 — holiday/short 22, roll 8, session-after-roll 8. Reconciles: 501+38+0 = 539 |
| Errors | 0 |

> **SEALED AND UNREAD.** No outcome column has been read, printed or aggregated. Reader is
> `stage2_smoke.read_results(token)`, which raises `SealedResultsError` without
> `RESULTS_UNSEAL_APPROVED_BY_ANGUS`. **Reading it spends N_trials and must wait for
> PREREGISTRATION.md §10.4 sign-off.**

**Nine defects were found and fixed by a pre-run adversarial review, before anything was
sealed.** Two mattered most: the EOD flatten was tested before the stop on the same bar, which
let 4.5 override 4.1 and made the flatten branch the only exit able to lose more than 1R; and
`trig()` returns a set whose unsorted iteration made the **sealed hash non-reproducible**. Roll
detection was also alphabetical rather than chronological — confirmed to have put 6 of 8 roll
dates one session late. Full list in [`STAGE2-SMOKE.md`](vwap-bb/STAGE2-SMOKE.md).

---

## A7 SELECTOR — confirmation count (added 2026-08-08)

Source: `research/star-trading/tools/vwapbb_a7_selector.py`. **Workbench, 509 sessions.**
Full filter stack + A4 + A5 + A7. Holdout never addressed.

**Resolution timing note.** The one-at-a-time rule cannot be applied without knowing when a
position closes, so each admitted candidate's bars are walked forward until the stop distance
or the target distance is touched. **Stop-first ordering is computed as an unavoidable
by-product. It was not aggregated, reported or examined** — no win rate, no expectancy, no P&L
exists in that script. Elapsed minutes were used only to decide when the next candidate could
be admitted.

| | A | B | C | D |
|---|---|---|---|---|
| qualified candidates / session | 47.430 | 27.436 | 13.762 | 8.866 |
| distinct signal minutes / session | 30.100 | 16.701 | 11.238 | 7.251 |
| **ADMITTED trades / session** | **2.849** | **2.782** | **2.699** | **2.328** |
| planned RR at entry, median | 2.132 | 2.162 | 2.206 | 2.208 |
| planned RR at entry, mean | 2.481 | 2.529 | 2.592 | 2.558 |
| stop distance, median (pts) | 10.00 | 10.00 | 10.00 | 10.00 |
| **% of trades AT the A5 floor** | **59.9%** | 55.0% | 52.4% | 54.6% |
| blocked — position open | 7.417 | 4.678 | 3.071 | 2.293 |
| blocked — 3/day cap | 27.346 | 12.491 | 7.088 | 3.658 |
| **% blocked — one-at-a-time** | 15.6% | 17.0% | 22.3% | 25.9% |
| **% blocked — 3/day cap** | **57.7%** | 45.5% | 51.5% | 41.3% |
| **% sessions where the cap binds** | **91.0%** | 86.8% | 81.5% | 63.1% |
| **% signal minutes with a tie** | 22.9% | 19.9% | 16.4% | 18.1% |
| median hold, minutes | 5 | 6 | 6 | 7 |
| admitted ÷ qualified | 6.0% | 10.1% | 19.6% | 26.3% |

**Tripwire: every reading CLEARS 0.4862 — by 5.9× (A), 5.7× (B), 5.6× (C), 4.8× (D).**

### Which tie-break level actually decides

| level | A | B | C | D |
|---|---|---|---|---|
| 0 — no tie, single candidate | 80.7% | 81.4% | 84.3% | 82.1% |
| **1 — highest entry TF [SPEC]** | **19.1%** | **18.6%** | **15.7%** | **17.9%** |
| 2 — stand down, long/short conflict | 0.2% | 0.0% | 0.0% | 0.0% |
| 3 — largest cluster | **0.0%** | **0.0%** | **0.0%** | **0.0%** |
| 4 — cluster nearest entry | **0.0%** | **0.0%** | **0.0%** | **0.0%** |
| 5 — lowest cluster low (arbitrary backstop) | **0.0%** | **0.0%** | **0.0%** | **0.0%** |

**The tie-break is carried entirely by §1's MTF arbitration — a rule Angus already confirmed.**
Levels 3–5 never fire. The [FIAT] content of the tie-break is, in practice, zero.

### A measurement-hygiene finding worth keeping

The first run of this count reported the arbitrary level-5 backstop deciding **36.1%** of
admissions under reading A, and ties on **39.3%** of signal minutes. Both were wrong.
`trig()` emits a rejection *and* a displacement for the same cluster on the same bar; those
duplicate records were tying with each other. Checked directly: **100% of level-5 invocations
were between two records of an identical trade** — same entry, same stop, same target — so the
choice was immaterial. Collapsing duplicates left **admitted trades/session unchanged** and
moved ties to 22.9% with level 5 at 0.0%.

> **An arbitrary rule that looks load-bearing may just be counting one thing twice.** Check
> whether the things being tie-broken are actually different before designing a rule to
> separate them.

### What the numbers say about the design

- **The cap is the dominant filter**, discarding 41–58% of qualified candidates and binding on
  63–91% of sessions. Under reading A only **6.0%** of qualified candidates are traded.
  Admission order determines the traded population. Recorded in §10.1(5) as a known property
  of the design, not an oversight.
- **Frequency is not, and never was, the constraint** — 2.33–2.85/session against a hand-log
  1.00 and a tripwire of 0.486.
- **Median hold is 5–7 minutes against the hand log's ~30.** A5's floor is 10.00 pt against the
  human's 35.00 median, so positions still resolve ~5× faster. Residual of the unresolved stop
  *anchor*, not a new problem.

---

## PRE-REGISTRATION (drafted 2026-08-08)

[`research/vwap-bb/PREREGISTRATION.md`](vwap-bb/PREREGISTRATION.md) — **DRAFT, NOT IN FORCE.**
Binds when Angus signs the four OPEN items. **Spec RE-HASHED 2026-08-08 after A8–A12:**

| | |
|---|---|
| **SHA-256 (current)** | `42d6f0f68ed35bef0280be782c58f72059333222047841473ab74d5b9fbd83bf` |
| git blob | `03f7a21b2841a99bb67932abbeebf00b6423d34a` |
| size | 52,574 bytes · 727 lines · amendments **A1–A13** |
| superseded | `59edd5b2…` (A1–A12, 46,617 B) · `8ead7259…` (A1–A7, 30,059 B — **the sealed run's spec**) |

> **`workbench_results_SEALED.parquet` was produced under the SUPERSEDED hash.** A9 and A10
> change the admitted population; A8's σ-band rule is new and unrun; A11 is output-only. The
> sealed result is a result on a superseded spec — **not invalidated, not re-sealed here.** Any
> Stage 3 run under A8–A12 is a **different run** and must be sealed separately. Spec A12.

### Axis decision table — required n at p₀ = 43.90%, p₁ = 0.50, 80% power

| divisor | corrected α | required n | tripwire /sess | A clears (1,450) | D clears (1,185) | resolution floor | blind zone |
|---|---|---|---|---|---|---|---|
| 1 | 0.05000 | 411.3 | 0.763 | YES | YES | 47.15% | 3.25 pt |
| **4 (current)** | 0.01250 | **631.7** | **1.172** | YES | YES | 47.93% | 4.03 pt |
| 5 | 0.01000 | 666.9 | 1.237 | YES | YES | 48.04% | 4.14 pt |
| 8 | 0.00625 | 740.9 | 1.375 | YES | YES | 48.26% | 4.36 pt |
| 16 | 0.00313 | 849.4 | 1.576 | YES | YES | 48.57% | 4.67 pt |
| 72 (full grid) | 0.00069 | 1082.9 | 2.009 | YES | YES | 49.17% | 5.27 pt |

> **Every axis structure clears on sample size.** The constraint is the **blind zone**: with
> breakeven at 43.90%, the study cannot resolve a true win rate below **47.15%** even
> uncorrected. **A true 45% win rate — genuinely profitable — is undetectable at any axis
> structure.** The correction costs ~2 points of resolution; the design costs 3.

At the measured median planned RR of 2.132 (p₀ = 35.04%) required n falls to 65 (÷1) – 169
(÷72). The pre-registration commits to the conservative p₀ = 43.90%.

Recompute: `research/prereg/axis_decision.py`.

### Session-accounting discrepancy, recorded

The A7 confirmation count processed **509** sessions and did **not** exclude roll /
session-after-roll, which the pre-registered accounting rule §4.3 requires. **13 sessions,
2.6%.** The §6 frequency figures are therefore an **upper bound**. Cannot move 2.849 below a
1.172 tripwire, so no verdict turns on it; the engine will apply the rule.

---

## PARITY GATE — spec-1 Step 4 (Stage A issued 2026-08-08)

**Stage A: the question sheet.** [`vwap-bb/PARITY-SHEET.md`](vwap-bb/PARITY-SHEET.md) **Rev 2**
— issued, awaiting Angus's readings. **Blind: it contains no computed value of any kind.**

| | |
|---|---|
| **P1** | 2025-01-15, **09:48 ET** — the candle covering 09:47:00–09:47:59, just closed |
| **P2** | 2025-01-22, **09:50 ET** — the candle covering 09:49:00–09:49:59, just closed |

**Rev 2 is wider than Rev 1**, which asked 8 values on P1 only (recorded in
`vwap-bb/PARITY-ANGUS-READINGS.md`, compared in `vwap-bb/PARITY-COMPARISON.md`). Rev 2 adds the
full §3 cluster-eligible menu, the §6 target menu, Bollinger bands on **all four** entry
timeframes, the last completed candle per timeframe, cluster membership and **span**, the 15m
fractal HTF classification, all four **§7 filter checks**, and the **entry / stop / target**
that follow. P1's 8 prior values carry over unchanged; everything else on both pages is unread.

**Three fields the sheet flags as load-bearing:** daily VWAP mid (the anchor everything else
depends on); the **stop** (a structurally different placement answers an open question rather
than being a mismatch); and the **4h range**, which the spec never defines and which the §7
location filter depends on — whatever Angus writes becomes the definition.

**Bar convention, reconciled explicitly on the sheet.** Source bars are **open-labelled**; the
detector shifts +1 so its own minute label is the bar's **close**. Same instant, two
descriptions. **RTH 09:31–16:00 is the entry window only** — the daily VWAP and session profile
anchor at **Globex 18:00 ET**, the NY VWAP at **09:30 ET**.

### STAGE B — P2 RUN 2026-08-08 → **PARITY FAIL**

Full report: [`vwap-bb/PARITY-P2-RESULT.md`](vwap-bb/PARITY-P2-RESULT.md). Detector dump:
`vwap-bb/data/parity_p2_detector.json`. Harness: `tools/parity_p2_dump.py` (read-only; it
re-executes `stage2_smoke.signal_candidates`, the sealed engine's own pre-outcome path, and
confirms agreement with it). **Sealed result never opened. No detector file edited. N_trials 0.**

> ### PARITY FAIL — 36 of 48 numeric fields MATCH, 12 MISMATCH
>
> **The market data agrees to the tick. The definitions do not.** All 12 OHLC fields on 2m/3m/5m
> match at **0.00**; BB basis to **0.005**; session, pre-market and prior-day extremes to
> **≤0.50**. Every mismatch is downstream of something the spec does not state.
>
> **The trigger decision agreed — both say NO TRIGGER — and that is not evidence of parity.** The
> detector's single raw trigger at the instant (5m long rejection, cluster 21950.09–21952.35)
> died at the **first** gate, confluence count 1 against a minimum of 2. Nothing disputed was
> ever consulted. **The trigger predicates, RR floor, stop anchor, target ladder and A7 selector
> were not exercised at all.**

**The 12 mismatches, all diagnosed SPEC AMBIGUITY** — no implementation bug was found, and
"charting difference" was considered for the VWAP family and rejected because no single feed can
match a four-timeframe evaluation:

| group | worst \|Δ\| | cause |
|---|---|---|
| NY VWAP mid / ±1σ / ±2σ / ±3σ (7 fields) | **19.10** | indicator feed timeframe — see OPEN ITEMS |
| Daily VWAP **+3σ** (1 field) | **1.0037** | same; only band to breach, error is `k·Δσ` |
| Daily POC (1 field) | **44.50** | same |
| 4h range high / low (2 fields) | **1072.75** | range definition — see OPEN ITEMS |
| 15m latest swing high (1 field) | **29.25** | fractal tie handling — see OPEN ITEMS |

**Cluster sets differ on count and on every member:** detector 3 clusters (one of them
vwap-only), chart 2 (both carrying 2 types). **HTF flag: detector `range`, chart `uptrend`.**
**Location filter: detector 143.99% of range → all longs blocked; chart 74.50% → none blocked.**

**Two spec definitions the reading sets, checked against the code:**
**"prior day" = GLOBEX → implementation AGREES** (21783.50/21377.75 vs 21783.75/21378.25; an
RTH-only reading would have been wrong by **147.50** on the low). **4h range = swing highs and
lows → implementation CONTRADICTS** (clock blocks, not swings).

**All four spec ambiguities were non-binding at this instant** — structural cluster-eligibility
(implementation: not eligible), span vs chaining (implementation: **chaining**), which VWAP's
±1σ (implementation: **NY**, band on the side of travel), the 4h range definition. **None
changes the trigger decision here, and that is a weak result, not a reassuring one:** the trigger
died before any of them was reached. **A second instant, chosen where a trigger survives past the
confluence gate, is required before any of the four can be called tested.**

### ROLL CHECK — the flag pointed at the wrong range

Both 4h swing points are **post-roll NQH5**: high **22425.75** @ 2024-12-16 23:28 ET, low
**20694.00** @ 2025-01-13 04:16 ET. **They do not straddle**, so no correction applies — as read
74.50%, archive-measured 74.65%. **The 1h range does straddle:** its high (22111.00, 2024-12-16
13:21 ET) is a **pre-roll NQZ4** print, its low post-roll NQH5. Measured roll spread from the
`NQZ4-NQH5` calendar quote is **301.15 pts**, not the ~250 the project's shorthand assumed.
Correcting it moves the 1h range position from **83.03% to 58.82%**. The detector used neither
range — its 4h construction is session-local and never crosses a roll.

**N_trials: 0.**

---

## AMENDMENT 03 EXECUTED (2026-08-08) — four resolutions, one measurement, P3 released

### Location gate — DESCRIPTIVE COUNT, run before any spec change

`research/star-trading/tools/loc_gate_measure.py` · full workbench, 501 processed sessions ·
`vwap-bb/data/loc_gate_measure.json`. **Not a hypothesis test — no outcome computed, nothing
ranked. N_trials 0.** Faithfulness check: the replication reproduces the sealed run's admitted
count **exactly (1,423)**.

| | |
|---|---|
| Otherwise-valid candidates (every gate except location, post-dedup) | **23,490** — 12,042 long / 11,448 short |
| **Blocked by the location gate** | **4,346 = 18.50%** |
| — of longs | **19.55%** |
| — of shorts | **17.40%** |
| Admitted, gate **ON** (as sealed) | **1,423** — 655 long / 768 short · 2.8403/session |
| Admitted, gate **OFF** | **1,453** — 719 long / 734 short · 2.9002/session |
| Delta | **+30 (+2.11%)** |
| Amendment 02 floor **n ≥ 661** | ON **2.15×** · OFF **2.20×** — **both CLEAR** |

Range-position distribution over the 23,490: p05 **−0.331** · p25 0.274 · median **0.514** ·
p75 0.765 · p95 **1.378** · min −3.109 · max 6.130.

| band | share |
|---|---|
| < 0.00 — below its own range | **9.79%** |
| 0.00–0.20 — blocks SHORTS | 8.67% |
| 0.20–0.80 | 58.78% |
| 0.80–1.00 — blocks LONGS | 11.41% |
| > 1.00 — above its own range, blocks LONGS | **11.34%** |

> **The feared failure mode did NOT materialise — recorded as a negative result.** Amendment 03
> §4 warned the gate might be suppressing longs systematically and pushing the count under the
> runnable floor. Block rates are **near-symmetric** (19.55% long vs 17.40% short) and the
> budget is never at risk. **Decision 2 is a footnote on sample size.** The demotion stands on
> specification-quality grounds, not on this count.
>
> **Two findings it did produce, neither the one being looked for:**
> **(1) the range fails to contain price 21.07% of the time** — 4,346 gate decisions were taken
> on a "range" price sat outside; **(2) the cap absorbs the gate** — 4,346 blocks yield only
> **+30** trades when removed, but the mix moves **46.0/54.0 → 49.5/50.5 long/short**. The
> gate's effect on *which* trades are taken is an order of magnitude larger than on *how many*,
> consistent with §10.1(5).

### The four resolutions, written into the spec

| # | resolution | tag | free params |
|---|---|---|---|
| **A8** | VWAP (both anchors) computed from **1-minute bars, one canonical series**; BB stay per-entry-timeframe. **NY σ bands ineligible until 30 bars since the 09:30 anchor (10:00 ET)** | [SPEC] feed · **[FIAT]** threshold | **+1** |
| **A9** | Location filter **demoted from gate to recorded covariate**; both range definitions carried as columns; gate on neither | [SPEC] | **−1** (`LOC_BAND` retired) |
| **A10** | Swing fractal: `H[i] > H[i−1…i−N]` **AND** `H[i] ≥ H[i+1…i+N]`, mirrored for lows. **First bar of a plateau is the swing** | [FIAT] | 0 |
| **A11** | 1m **retained**; boolean `entry_tf_1m` on every Stage 3 trade | [SPEC] | 0 |
| **A12** | Note: A9 and A10 change the admitted population, so the sealed result is a result on a superseded spec | — | — |

**A8's threshold was argued, not searched.** The relative standard error of σ̂ from *n*
observations is ≈ **1/√(2(n−1))** — a property of the estimator, evaluable without touching the
data. At n=6 (09:36) that is **31.6%**, a ±62% interval on the band's distance from the mid:
±9–12 pts at typical early-session NY σ, **wider than the 10-pt cluster tolerance the band
feeds**. At n=30 it is **13.1%**, ±26%, ≈±4–5 pts — inside tolerance. **30 is the point at which
the estimate's own interval stops dominating the membership decision.** No value was tried
against the trade list; α is untouched.

**Cost of A8, stated not hidden:** 09:36–09:59 now has the NY **mid** only, so fewer clusters
form and §7 invalidation fires less in that window. Effect on trade counts is **unmeasured**.
NY-band parity against the reference chart becomes **permanently unverifiable** — Angus cannot
render a 1m VWAP for January 2025.

### P3 — instant selected and released under the blindness control

> ## **P3 = 2025-01-29, 10:20 ET**
>
> **That is the entire release.** Not the timeframe, not the direction, not a level, not the
> reason. Selection reasoning and the detector's expected values are in
> [`vwap-bb/P3-SELECTION-SEALED.md`](vwap-bb/P3-SELECTION-SEALED.md) — **DO NOT OPEN until the
> reading is submitted.** Selector: `tools/p3_select.py`, pool = 30 January-2025 admitted trades
> on 2m/3m/5m.
>
> **The instant was chosen FROM detector output.** Legitimate as test design — P3 exists to
> reach the code paths P2 never did. **Illegitimate as an agreement rate:** the instants were
> not randomly drawn. **P3 may be cited as evidence the code paths behave as specified; it may
> NOT be cited as an agreement rate.**

Instrument: `PARITY-SHEET.md` Rev 2, unchanged apart from the date and time in its header.

**N_trials: 0.**

---

## 2026-08-08 — P3 RE-VERIFIED · SEALED RESULT ARCHIVED · A13

### 1. P3 was selected under the SUPERSEDED spec — and it survives

**Answered first because Angus was reading.** `p3_select.py` called
`stage2_smoke.signal_candidates`, i.e. the **frozen detector**, which implements **8ead7259**
(A1–A7). The A8–A12 amendments were written into the *document*, not the code, so the pool of 30
was generated under the superseded spec. **Three of the changes alter behaviour:** A8's σ-band
eligibility (unimplemented in the detector), A9's demoted location gate (the detector still
applies it), A10's fractal plateau rule (the detector uses strict `>`).

Re-verified with a new harness, `tools/spec_current.py`, which re-implements the pipeline with
A8+A9+A10 and **leaves the frozen detector untouched**:

| spec | admitted at `cm 620` on 2m/3m/5m |
|---|---|
| **8ead7259** superseded (frozen detector) | **1 — triggers** |
| **59edd5b2** A8–A12, fixed-30 σ rule | **1 — triggers** |
| **42d6f0f6** A13, live σ rule | **1 — triggers** |

> ### **P3 stands at 2025-01-29 10:20 ET. No replacement, nothing new released.**

The session's *other* admitted minutes move between specs, so the surrounding context differs —
but the released instant survives all three.

### 2. `workbench_results_SEALED.parquet` — ARCHIVED, NEVER OPENED

Moved with `git mv`, byte-identical, **`a9ddc2947ca6a5f4c7e453d90427bed91710d1bc94c86de81fa9b381739bd4f0`**
verified before and after:

`research/vwap-bb/data/archive/workbench_results_SEALED_PRE-A8_UNOPENED.parquet` (+ `.sha256`)

| | |
|---|---|
| Status | **SUPERSEDED · NEVER OPENED · retained, not deleted** |
| Spec it tests | `8ead7259` (A1–A7) |
| Why superseded | **A9** demotes the location gate it applied; **A10** changes HTF flags wherever a 15m plateau occurs. Both change the admitted population |
| Performance numbers | **UNUSABLE.** They describe a specification no longer in force, and reading them now would be reading a result chosen after the spec moved |
| What it did deliver | **the pipeline verification it existed to provide** — `loc_gate_measure.py` reproduced its admitted count **exactly (1,423)** from an independent replication, confirming the engine is deterministic and faithfully re-implementable |
| N_trials | **0** — no outcome field has ever been read |

> **Two operational consequences.** `stage2_smoke.RESULTS` now points at an empty path, so its
> refuse-to-overwrite guard no longer fires; a re-run would create a new seal there, which must
> be a deliberate act. And **`stage2_smoke.py` does not implement A8/A9/A10/A13 — it cannot be
> used for Stage 3.** Stage 3 needs an engine built on `spec_current.py`.

### 3. A13 — the σ criterion tightened, and n=30 FAILS it

Criterion as restated: a NY VWAP σ band is eligible when the 95% CI on its distance from the mid
is **≤ half** the §3 cluster tolerance — `1.95996 · σ̂ / √(2(n−1)) ≤ 5.00 pt`.

Descriptive σ̂ census, 537 workbench sessions:

| n | ET | median σ̂ | CI half-width | ≤ 5.00 |
|---|---|---|---|---|
| 6 | 09:36 | 9.23 | 5.72 | no |
| 20 | 09:50 | 16.00 | 5.09 | no |
| **30** | **10:00** | 19.48 | **5.01** | **NO — by 0.01** |
| **35** | **10:05** | 20.91 | **4.97** | yes |
| 90 | 11:00 | 30.10 | 4.42 | yes |

**30 does not fall out. 35 does, at the median — and at the p75 σ̂ nothing does, up to n=90.**

> **The deeper result: the CI half-width is nearly FLAT in n** — 5.72 → 4.42 while n grows
> fifteen-fold. NY dispersion grows through the session at almost exactly the rate √(2(n−1))
> shrinks the estimator error. **Waiting does not buy resolution, so no waiting period fixes
> what A8 was written to fix.** The fixed-n form is the wrong shape, not merely mis-set.

**A13 therefore evaluates the criterion LIVE, per instant, from the session's own σ̂.** Zero
fitted constants — z is the normal quantile, 5.00 is half of §3's stated tolerance. **A8 added
one free parameter; A13 removes it. Net zero.** Named honestly: σ̂ gates its own admissibility,
the same circularity a t-statistic has.

**The 10:00 ET coincidence, recorded as the argument AGAINST a fixed boundary.** 30 bars past
09:30 lands exactly on the conventional slot for ISM Manufacturing and Services, JOLTS, Consumer
Confidence, Michigan sentiment, home sales and factory orders. *(No economic calendar is held —
out-of-scope branch 3 — so this is the conventional schedule, not a verified list.)* A fixed
boundary there would (a) **confound the Stage 5 release layer**, putting a detector-side
discontinuity in the level set at the modal release minute, and (b) estimate σ̂ over the
pre-release drift window and then apply it *into* the release — **estimation and application on
opposite sides of the volatility break.** The live rule has no fixed minute, so neither arises.
**Recorded for Stage 5: if any future rule reintroduces a clock boundary it must not sit at
10:00, 08:30 or 14:00 ET, and the release layer must control for it.**

**N_trials: 0.**

---

## 2026-08-08 — CODE-PATH VERIFICATION SUITE · P3 CANCELLED

### Part 1 — the parity gate CLOSES AT P2

**P3 is CANCELLED.** `vwap-bb/P3-SELECTION-SEALED.md` is deleted from the working tree and
survives in git history at `36229ea`. The instant 2025-01-29 10:20 ET is withdrawn and
`vwap-bb/PARITY-P3-SHEET.md` is void.

**Why: Amendment 03 §7 published the selection criterion** — *"P3 must be chosen where a trigger
survives past the confluence gate. On 2m, 3m or 5m"* — which told the reader that a trigger
exists at the released instant and that it is not on 1m, before he opened a chart. **No
date-and-time-only discipline repairs that**, because the criterion had to be published to
justify the instant. **Machine verification replaces it.**

**UPDATE 2026-08-08, item 9 of the overnight queue — the open decision above is now closed.**
The P4–P9 batch pre-registration is **WITHDRAWN**, formally, in its own document
(`PARITY-BATCH-PREREG.md`, header note). No further hand readings will be performed; the
parity gate closed at P2 and machine verification replaced it, and the batch was a
pre-registered plan for more of the thing that was just replaced. The document, including its
already-executed draw (six instants, seed `4617547402224582382`), is retained verbatim below
the withdrawal notice for the record. `PARITY-BATCH-SEALED.md` and its JSON companion stay
sealed permanently — not to protect a blind that will be used, but because there is no
remaining reason to open them.

### Two premises the suite assumed and the repository does not satisfy

> **1. There is NO Stage 3 run.** Nothing named Stage 3 has been executed. The only sealed
> artefact is the **Stage 2** workbench smoke result, archived unopened, on the superseded spec
> `8ead7259`. The suite's Part 2b was therefore run over a **freshly computed admission list** —
> geometry only, no outcome field of any kind — and Part 4's rule governs a run that does not
> yet exist.
>
> **2. The spec hash in the brief is stale.** It named `59edd5b2` (A1–A12). The repository is at
> **`42d6f0f6` (A1–A13)**, because A13 was added at Angus's own instruction. The suite ran
> against `42d6f0f6`, and the hash was **identical at the start and at the end** of the run.

### Results

| part | outcome |
|---|---|
| **2a** spec-derived unit tests | **64 written, 64 run, 61 PASS, 3 FAIL — no detector bug.** 2 failures are mis-constructed test bars, left unedited; 1 asserted something no clause states |
| **2b** invariants | **8 PASS at 1,472 of 1,472 evaluated · 1 NOT TESTABLE (7, stop-first) · 1 UNSPECIFIED IN SPEC (9, tick grid)** |
| **Part 3** bar archive | first **2023-01-02**, last **2026-01-30** (UTC days). `data_split.yaml` needs **no change** — it already records `2026-01-30`; the brief's `2026-07-31` is the MBP-10 window, which ends 2026-07-22 |
| **Part 4** unseal rule | created at `vwap-bb/STAGE3-UNSEAL-RULE.md` — **it did not previously exist**. Verdict **DO NOT OPEN** |

> ### THE FINDING WITH THE LARGEST BLAST RADIUS — invariant 9
>
> **1,401 of 1,472 intended entries, 824 stops and 1,134 targets do not sit on the 0.25 tick
> grid.** §5.3 says *"E1: limit at the BB MA"* — a 20-bar mean — and **no clause anywhere in the
> spec rounds a price to the tick.** These orders cannot be placed as written. Actual fills are
> bar opens and are all on-grid, so the defect is in the *intended* order prices, i.e. in the
> stop and target that a live system would transmit. **UNSPECIFIED IN SPEC: the spec must say how
> prices round, and in which direction, before any run claims to be executable.**

**Invariant 7 (stop-first) is NOT TESTABLE and is not marked PASS.** Attributing an exit is
outcome information, barred by the suite's own rule 6, so it can only be tested against a Stage 3
engine — and it must be tested there *before* that engine's output is sealed.

**`stage2_smoke.py` implements none of A8, A9, A10 or A13 and cannot be used for Stage 3.** The
current-spec harness is `tools/spec_current.py`.

### Determinism

| artefact | hash |
|---|---|
| 2b trade list (geometry only), run 1 and run 2 | `1c9fce7d494f84fff18ec5e769abb6b995f378ba3e2bdff49b938c38075554bd` — **identical** |
| 2a result, `PYTHONHASHSEED=0`, run 1 and run 2 | `dcc9f9c67f56e9e536bbb558e5a78b85b2b45add9b52ab1a1ced52239d234b7e` — **identical** |
| 2a result, unseeded | **DIFFERED between runs** |

**Disclosed rather than quietly fixed:** the first determinism attempt FAILED on 2a. The cause is
`repr()` of Python sets in the serialized report, whose ordering depends on the per-process
string hash seed. **The pass/fail verdicts are stable** — a hash over `(test id, status)` alone is
identical across all four runs, seeded and unseeded — so the non-determinism is in the artefact's
serialization, not in any outcome. Fixed by pinning `PYTHONHASHSEED=0`, which is the fixed seed
the suite's rule 9 required in the first place.

**N_trials: 0.** Nothing in the suite tested a hypothesis and no outcome was computed anywhere.

---

## 2026-08-08 — ITEM 11: STAGE 3 SEALED. N_trials 1 of 5.

**Gate check first, per item 11's own condition:** items 2–6 introduced no behaviour
contradicting an existing clause. A14 and A15 are additions closing documented gaps, not bug
fixes, and are exempted from tripping this gate by the item's own text. The two bugs actually
found and fixed overnight (§ above) were in the verification tooling I wrote — a sort-key crash
and a stale status label — not in the detector or in any amendment's implementation. **Gate
PASSES.**

`stage3_sealed_a15.py` — a new sealed engine, admission via `spec_current.signal_candidates_current`
(A8/A9/A10/A13/A14) + the A7 loop, resolution via `resolve_bar_stop_first` (item 5) + EOD flatten,
A11's `entry_tf_1m` flag, costs at three bases (lean 0.25 / base 0.50 / adverse 1.00 pt). Modelled
on `stage2_smoke.py`'s own sealing discipline, restricted further: **this script's console output
contains only completion status, the row count, the file path and the SHA-256** — no frequency or
audit figures, stricter than Stage 2's report, per item 11's own report restriction. Self-check
scanned the printed text for outcome tokens before returning: **PASS, none found.**

| | |
|---|---|
| **Ran** | YES |
| **Realised trade count** | **1,472** |
| **SHA-256** | **`0caf65cfdb2a0bfd939215ed95805e0a4b729210c5c35eef0d5f4bf05d55ce71`** |
| **Amendment 02 floor n ≥ 661** | **CLEARS** |
| File | `research/vwap-bb/data/workbench_results_SEALED_A15.parquet`, 29 columns |
| Spec | `f6b38bf4af1ca9696a12a6e9f80a12209ebff310` (A1–A15) |

**Nothing about expectancy, win rate, drawdown, Sharpe or direction appears here or anywhere
else this run touched — per item 11, that information does not exist in any file this session
produced.** `STAGE3-UNSEAL-RULE.md` updated: precondition now MET, a.1 and a.2 now PASS, a.3
awaits the morning's 2c adjudication, b.1 awaits signature. **Verdict unchanged: DO NOT OPEN**,
now resting on b.1 and a.3 alone rather than on the absence of a run.

**N_trials: 1 of 5.**
