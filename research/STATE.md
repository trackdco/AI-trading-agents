# STATE — canonical figures for the NQ trading project

**Source of truth as of 2026-08-08.** Every figure here was recomputed from the underlying
file, not copied from a report. Anything quoting a number cites **this file**, not another
report. Where a report disagrees, this file wins — see
[`mismatch-report.md`](mismatch-report.md).

N_trials: **0**. Holdout: **SEALED.** See RULINGS below — a seal event is on permanent record
and must accompany any future holdout result.

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
> A1 places out of scope. The in-scope figure is 3.678 mean / 3.370 median.** Several
> documents still carry 4.23 — see mismatch #1.

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
| 3 BREAKEVEN | **PASS — needs formal re-derivation at c=0.975** | p₀ = **43.90%** at the A5 floor s=10.00, c=0.975 (was 40.61% at s=32.75, c=0.50). c/s = 9.75% |
| 4 SPECIFIABILITY | **REOPENED** | Vault selector unstated; cap binds on 33–92% of sessions. A4/A5 closed the stop and target sub-items; §6 rule 2 and the A/B/B2 taxonomy remain open |
| **4b LITERALISM** | **NEW — FIRED 3×** | Stop 11× tighter than intent; target 19.5× nearer; Vault cap acting as selector. See the runbook |
| 5 DATA FEASIBILITY | **CLOSED — SCOPE ACCEPTED** | Feb 2026 bars absent; MBP-10 present but cannot produce VWAP/POC/wick. Parity relocated, calibration downgraded (A6) |
| 6 SAMPLE SUFFICIENCY | **PASS**, floor p₁ ≈ 0.50 | Tripwire **0.4862** trades/session (n=262, ÷4, 539 sessions). Amended rules deliver **2.24–2.83** — see SIGNAL COUNT |

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

> **Gate 3 still PASSES at the new base**, and by a wider margin than the arithmetic suggests:
> A5's 10-point floor moves the operative stop from 3.12 to ≥10.00, which cuts the cost ratio
> from 31.25% to 9.75% and breakeven from 52.50% to **43.90%**. The cost rise and the stop
> floor land in opposite directions and the floor wins. **Gate 3 should still be formally
> re-derived at c = 0.975 rather than inherited.**

### Caveats — stated, not buried

Point samples at minute boundaries, not time-weighted; continuous `NQ.c.0`; sample period
2026-02 → 2026-07, which is neither workbench nor any period a result is fitted on.

**On representativeness — correcting the premise.** The measurement window is **09:30–10:29
ET**, and it was suggested this is representative because the signal distribution peaks
10:00–10:30. **Measured, it does not.** Deduplicated signal-minutes by 30-minute bucket over
the workbench (reading A, pre-RR-floor, n = 20,357) are close to uniform across RTH — 7.0% to
9.5% per bucket, with the largest at **12:00–12:29 (9.5%)**, not 10:00–10:30 (7.0%):

| bucket | 09:30 | 10:00 | 10:30 | 11:00 | 11:30 | 12:00 | 12:30 | 13:00 | 13:30 | 14:00 | 14:30 | 15:00 | 15:30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| share | 2.6% | 7.0% | 7.5% | 7.6% | 7.3% | **9.5%** | 8.0% | 8.7% | 8.1% | 8.3% | 7.4% | 8.4% | 8.8% |

**The window covers 9.7% of the signal population by weight.** It is therefore *not*
representative — it is a 10% slice, and 90% of signals fire in hours with no spread measurement
at all. On direction of bias: within the measured window the median holds flat at 0.750 while
p90 falls from 1.50 to 1.25 by 10:15, which is consistent with the early session being the
wider part of the day — so 0.975 is more likely conservative than optimistic. **That is an
extrapolation from a trend inside a 10% slice, not a measurement.** Spread after 10:29 is
unmeasured and remains unknown.

## OPEN ITEMS

| item | blocks | status |
|---|---|---|
| **Vault selection rule unstated** | Gate 4; any backtest | **The largest open item.** The 3/day cap does 21–32% of all filtering and sets the trade count — 2.83/session out of ~30 qualified. Which 3, and why, is unwritten. Time-priority is implied by "one position at a time" but never stated. Needs Angus |
| **§6 rule 2 defaults ambiguous and unimplemented** | Gate 4 | Pattern A's default target is "VWAP middle", but 85.4% of entries sit *inside* the firing cluster, which contains it. The A/B/B2 taxonomy (§4) is not implemented at all. **A4 does not fix this.** Needs Angus |
| **Stop anchor unconfirmable from data** | Gate 4 | Alternatives measured (prior swing 16.29, 2×ATR 25.32 vs frozen 5.62 pts). The hand log records **no entry/stop/target prices**, so no anchor can be confirmed. A5 supplies a floor, not the anchor. Requires Angus or marked-up charts |
| **E1 + wick degenerate on 29.6% of triggers** | Gate 4 | Entry falls on the wrong side of the wick extreme; those triggers are skipped. A5 deliberately does not rescue them. The E1 pairing itself may be the defect |
| **Gate 3 not formally re-derived at c = 0.975** | Gate 3 sign-off | Arithmetic done (43.90% at the A5 floor, still PASS); the gate document still records the old basis |
| **Spread unmeasured after 10:29 ET** | Cost model confidence | The 5,781-snapshot sample covers 9.7% of the signal population. 90% of signals fire in hours with no spread data. Would need MBP files with a later window |
| **One-position lockout placeholder** | Signal count precision | 30 min, derived under the *old* geometry. A5's wider stops lengthen holds, so the placeholder is now more approximate. Declared, not hidden |
| **Pre-open warm-up bias** | Study design | BB(20)/ATR(20) at 09:36 read bars 1.65× quieter than RTH. Measured effect on counts: −0.8% |
| **Parity readings not supplied** | spec-1 Step 4 sign-off | Angus must provide chart values for 2025-01-15 09:48 and 2025-01-22 09:50 |
| **Calibration gate downgraded** | Phase 2 sign-off | Irrecoverable *as a bar-based gate* — Feb 2026 has no bars, and the MBP schema cannot produce the detector's inputs. §12.2 corrected by A6 |
| **"+4.23R" in three documents** | Nothing — no verdict rests on it | Correct to 3.678 (in-scope) in a separate pass |

**Closed 2026-08-08:**

| item | how |
|---|---|
| Spec stop geometry ~11× tighter than the hand log | Diagnosed, then amended. Not a stop-anchor problem alone — the target was 19.5× nearer too, so both ends compressed together and the R-multiple looked healthy. **A5** floors the stop at 10.00 pt; cost ratio 31.25% → 9.75% |
| §6 target rule discards viable targets | **A4** — "valid" disambiguated to "clears the floor". The RR floor now removes 4.6–11.7% of stage-0 instead of ~25%, and screens target quality rather than stop size |
| H1 — entry timeframe | **REJECTED.** The gap is 8.5–11.2× within every timeframe, tested against the hand log's own `Entry TF` column |
| V3 unreachable under RTH | **A6** — struck. Management axis 4, configuration space 72 |
| §12.2 described a calibration that cannot run | **A6** — corrected |
| 2026-02-01 → 2026-07-22 unclassified | **RULED** — microstructure only. Mirrored in `data_split.yaml` |
| Seal-boundary read | **RULED** — recorded, not remediated. Permanent entry in RULINGS; both scripts guarded |
| Gate 6 under the amended rules | **CONFIRMED** — 2.24–2.83 trades/session against a 0.4862 tripwire |

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
