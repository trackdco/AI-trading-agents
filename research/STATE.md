# STATE — canonical figures for the NQ trading project

**Source of truth as of 2026-08-07.** Every figure here was recomputed from the underlying
file, not copied from a report. Anything quoting a number cites **this file**, not another
report. Where a report disagrees, this file wins — see
[`mismatch-report.md`](mismatch-report.md).

N_trials: **0**. Holdout: **SEALED, never read**.

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
| February 2026 | **0 sessions — absent** | the hand-log month is not in the data |
| Contract rolls | 12 quarterly, ~250 pt unadjusted gaps | 2 sessions contain an intra-session switch, both in the evening |

Bars are **open-labelled** at source (verified: median \|book_mid − bar.close\| 0.38 pts vs
6.69 vs bar.open). MBP-10 condensed files run to 2026-07-22 but are **irrelevant** — VWAP, BB
and volume profile are all bar-computable.

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

**0.25 / 0.50 / 1.00 points round-trip** (lean / base / adverse). NQ = $20/point, tick 0.25.
Basis: commission ≈ $4.50 RT = 0.225 pt, plus stop-exit slippage. Entry is a limit (no spread
paid), target is a limit at a level.

**These are declared assumptions, not measurements.** The Stage 0 audit established there is
no trade-level data — 3 trade records across 67,419 order-book rows — so no execution-quality
estimate is possible from what is held. **UNVERIFIED by construction.**

## OPEN ITEMS

| item | blocks | status |
|---|---|---|
| **Vault selection rule unstated** | Gate 4; any backtest | Needs a spec amendment (Angus). Time-priority is implied by "one position at a time" but never written |
| **Spec stop geometry ~11× tighter than the hand log** | Every R-normalised measurement | E1 + 1-tick-beyond-wick gives median R 3.12 pts vs 35.00. Either the freeze or the E1 pairing is wrong |
| **Pre-open warm-up bias** | Study design | BB(20)/ATR(20) at 09:36 read bars 1.65× quieter than RTH. Measured effect on counts: −0.8% |
| **Parity readings not supplied** | spec-1 Step 4 sign-off | Angus must provide chart values for 2025-01-15 09:48 and 2025-01-22 09:50 |
| **Calibration gate downgraded** | Phase 2 sign-off | Irrecoverable — the 28 hand trades are in a month the data does not contain |
| **V3 unreachable under RTH** | Tournament sizing | Management axis 5 → 4, configuration space 90 → 72. Not yet actioned in the spec |
| **"+4.23R" in three documents** | Nothing — no verdict rests on it | Correct to 3.678 (in-scope) in a separate pass |

---

*Recomputation scripts: `research/star-trading/tools/{alpha_data,vwapbb_signals,vwapbb_opportunity,vwapbb_analyse}.py`.
Full comparison against reported values: [`mismatch-report.md`](mismatch-report.md).*
