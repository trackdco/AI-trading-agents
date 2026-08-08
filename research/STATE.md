# STATE — canonical figures for the NQ trading project

**Source of truth as of 2026-08-08.** Every figure here was recomputed from the underlying
file, not copied from a report. Anything quoting a number cites **this file**, not another
report. Where a report disagrees, this file wins — see
[`mismatch-report.md`](mismatch-report.md).

N_trials: **0**. Holdout: **SEALED. No bar content read; no measurement made.** One
seal-boundary exposure is on record — 2 rows from each of 287 holdout-dated MBP-10 files,
read during a file inventory on 2026-08-08. Declared in
[`target-stop-reconciliation.md`](vwap-bb/target-stop-reconciliation.md) §7; both scripts are
now guarded.

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
| Contract rolls | 12 quarterly, ~250 pt unadjusted gaps | 2 sessions contain an intra-session switch, both in the evening |

Bars are **open-labelled** at source (verified: median \|book_mid − bar.close\| 0.38 pts vs
6.69 vs bar.open).

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

**Classification gap.** 2026-02-01 → 2026-07-22 (223 files) is neither workbench nor holdout in
`config/data_split.yaml`. Needs a ruling.

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
> A1 places out of scope. The in-scope figure is 3.678 mean / 3.370 median.** Several
> documents still carry 4.23 — see mismatch #1.

**Not in the source file:** entry, stop and target *prices*. Only distances, risk $, R
multiples and P&L are recorded. Any per-trade price figure would be fabricated.

## SPEC

Frozen at gate 4 (`preflight.md` rev 2), zero fitted:

| # | parameter | value | tag |
|---|---|---|---|
| 1 | VWAP typical price | HLC/3 | **[SPEC]** — §2 "standard TradingView VWAP" |
| 2 | Volume-profile bin | 1.00 point | [FIAT] |
| 3 | HTF classification | 15m fractal N=2; HH+HL up, LH+LL down, else range | [FIAT] |
| 4 | Stop buffer | 1 tick beyond the wick extreme | [FIAT] |
| 5 | Volatility stand-down | DISABLED for v1 | [FIAT] |

| figure | value |
|---|---|
| Free parameters | **13** (9 CALIBRATE + 4 TOURNAMENT axes); was 18 before the freeze |
| Tournament configuration space | **90** (W×E×V×weekly); **30** under §12.3's stated grid; **72** if V3 is struck |
| **N_trials** | **0** |

**§5.4 stop rule, verbatim:** *"Stop: beyond the wick extreme of the trigger candle /
displacement origin. Structural, never widened (Vault-enforced)."*

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
| 3 BREAKEVEN | **PASS** | p₀ = 40.61% at s=32.75, c=0.50 (40.57% at the correct s=35.00); c/s = 1.53% |
| 4 SPECIFIABILITY | **REOPENED** | Vault selector unstated; cap binds on 33–92% of sessions, discards 43–86% of qualified candidates |
| 5 DATA FEASIBILITY | **CLOSED — SCOPE ACCEPTED** | Feb 2026 absent; parity relocated, calibration downgraded |
| 6 SAMPLE SUFFICIENCY | **PASS**, floor p₁ ≈ 0.50 | Tripwire **0.4862** trades/session (n=262, ÷4, 539 sessions) |

Gate-6 arithmetic, recomputed at p₁=0.50, p₀=0.406, 80% power, 539 sessions:

| correction | required n | tripwire |
|---|---|---|
| ÷1 | 170.9 | 0.3170 |
| **÷4 (current, V3 struck)** | **262.1** | **0.4862** |
| ÷5 (superseded) | 276.6 | 0.5132 |

Cost-adjusted breakeven `p₀ = (s+c)/(s(1+R))` at R=1.5, recomputed:

| stop s (pts) | c=0.25 | c=0.50 | c=1.00 |
|---|---|---|---|
| 32.75 (hand log, full) | 40.31% | 40.61% | 41.22% |
| **35.00 (hand log, in-scope)** | 40.29% | **40.57%** | 41.14% |
| 21.50 (gate-1 proxy, 5m) | 40.47% | 40.93% | 41.86% |
| **3.12 (spec geometry)** | 43.21% | **46.41%** | 52.82% |

> The spec-geometry row is the live problem: at a 3.12-point stop, costs alone lift breakeven
> from 40% to **46.4%** at base cost and **52.8%** at adverse.

## COSTS

**Declared ladder: 0.25 / 0.50 / 1.00 points round-trip** (lean / base / adverse). NQ =
$20/point, tick 0.25. Basis: commission ≈ $4.50 RT = 0.225 pt, plus stop-exit slippage. Entry
is a limit (no spread paid), target is a limit at a level, so the spread is crossed once — on
the stop exit.

**Superseded 2026-08-08: the spread is now measured, not assumed.** MBP-10 book snapshots,
**5,781 RTH samples over 99 sessions, 2026-02-02 → 2026-07-08** (post-holdout only;
`mbp_feb2026.py`):

| | value |
|---|---|
| top-of-book spread, median | **0.75 pt (3 ticks)** |
| p25 / p75 / p95 | 0.75 / 1.00 / 1.75 |
| ticks | 2t 13.3% · **3t 44.7%** · 4t 23.4% · ≥5t 18.6% |
| inside size (bid+ask) | median 3 contracts |
| **implied stop-exit cost, median** | **0.975 pt** (spread + 0.225 commission) |
| implied stop-exit cost, p90 | **1.725 pt** |

Not a cancel artefact — adds median 0.75, modifies 0.75, cancels 1.00.

> **The declared ladder is optimistic by about one step.** "Lean" 0.25 is below one tick of
> spread and unattainable on a stop exit; "adverse" 1.00 is roughly the **median**.

Breakeven at R=1.5, recomputed at the measured cost:

| stop s | c=0.50 (declared base) | **c=0.975 (measured median)** | c=1.725 (measured p90) |
|---|---|---|---|
| 3.12 (spec geometry) | 46.41% | **52.50%** | 62.12% |
| 10.00 | 42.00% | **43.90%** | 46.90% |
| 20.00 | 41.00% | **41.95%** | 43.45% |
| 35.00 (hand log, in-scope) | 40.57% | **41.11%** | 41.97% |

**Caveats:** point samples at minute boundaries, not time-weighted; 08:00–10:29 ET only;
continuous `NQ.c.0`; 2026-02 → 2026-07, which is neither workbench nor a period any result is
fitted on. A first measurement, not a settled cost model.

## OPEN ITEMS

| item | blocks | status |
|---|---|---|
| **§6 target rule is the binding constraint** | Gate 4; the whole feasibility question | Rule 5 tests the **nearest** level (median 7.95 pts) while the menu holds levels at hand-log distances (nearest liquidity extreme median 75.8 pts; 63.3% of records have a rung ≥155 pts). Diagnosed in [`target-stop-reconciliation.md`](vwap-bb/target-stop-reconciliation.md) |
| **§6 rule 2 defaults are ambiguous, and unimplemented** | Gate 4 | Pattern A's default target is "VWAP middle", but 85.4% of entries sit *inside* the firing cluster, which contains it. The A/B/B2 taxonomy (§4) is not implemented at all. Needs Angus |
| **Vault selection rule unstated** | Gate 4; any backtest | Needs a spec amendment (Angus). Time-priority is implied by "one position at a time" but never written |
| **Stop anchor unconfirmable from data** | Gate 4 | Alternatives measured (prior swing 16.29, 2×ATR 25.32 vs frozen 5.62 pts). The hand log records **no entry/stop/target prices**, so no anchor can be confirmed. Requires Angus or marked-up charts |
| **Measured spread exceeds the declared cost ladder** | Gate 3; every breakeven figure | Median stop-exit cost 0.975 pt vs a declared base of 0.50. See COSTS. Gate 3's PASS should be re-derived at the measured cost |
| **2026-02-01 → 2026-07-22 unclassified** | Any use of the MBP files | 223 files outside both workbench and holdout in `data_split.yaml`. Needs a ruling |
| **Seal-boundary read, 2026-08-08** | Nothing — no verdict rests on it | 2 rows read from each of 287 holdout-dated MBP files during inventory. Declared in [`target-stop-reconciliation.md`](vwap-bb/target-stop-reconciliation.md) §7; both scripts now guarded |
| **Pre-open warm-up bias** | Study design | BB(20)/ATR(20) at 09:36 read bars 1.65× quieter than RTH. Measured effect on counts: −0.8% |
| **Parity readings not supplied** | spec-1 Step 4 sign-off | Angus must provide chart values for 2025-01-15 09:48 and 2025-01-22 09:50 |
| **Calibration gate downgraded** | Phase 2 sign-off | Irrecoverable *as a bar-based gate* — Feb 2026 has no bars, and the MBP schema cannot produce the detector's inputs |
| **V3 unreachable under RTH** | Tournament sizing | Management axis 5 → 4, configuration space 90 → 72. Not yet actioned in the spec |
| **"+4.23R" in three documents** | Nothing — no verdict rests on it | Correct to 3.678 (in-scope) in a separate pass |

**Resolved this pass:** "Spec stop geometry ~11× tighter than the hand log" — diagnosed. It is
not a stop-anchor problem in isolation: the *target* is 19.5× nearer as well, so both ends are
compressed together. The R-multiple therefore looks healthy while the **cost ratio** is 31% of
risk. H1 (entry timeframe) is rejected — the gap is 8.5–11.2× within every timeframe.

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
