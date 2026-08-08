# STATE — canonical figures for the NQ trading project

**Source of truth as of 2026-08-08.** Every figure here was recomputed from the underlying
file, not copied from a report. Anything quoting a number cites **this file**, not another
report. Where a report disagrees, this file wins — see
[`mismatch-report.md`](mismatch-report.md).

N_trials: **0**. Holdout: **SEALED.** See RULINGS below — a seal event is on permanent record
and must accompany any future holdout result.

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
| 4 SPECIFIABILITY | **CLOSED** | Last item — the Vault selector — written into §10.1 by **A7**. Stop and target closed by A4/A5. §6 rule 2 and the A/B/B2 taxonomy remain open but are **tournament variants, not gate blockers** |
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
| **Stop anchor unconfirmable from data** | Nothing — A5 makes it non-blocking | Alternatives measured (prior swing 16.29, 2×ATR 25.32 vs frozen 5.62 pts). The hand log records **no entry/stop/target prices**, so no anchor can be confirmed from data. A5's floor makes the spec executable without it; the residual shows up as 5–7 min holds against the human's ~30. Requires Angus or marked-up charts |
| **E1 + wick degenerate on 29.6% of triggers** | Nothing — E1 is one of three tournament entries | Entry falls on the wrong side of the wick extreme; those triggers are skipped. A5 deliberately does not rescue them. E2/E3 may not share the defect — the tournament will show it |
| **DEFERRED CAPABILITY — holdout depth data** | Nothing now; improves the cost model later | When the holdout is opened its MBP-10 becomes readable and can validate the cost model **against the very sessions the verdict rests on** — strictly better than the post-holdout window. 287 files, 2025-06 → 2026-01. **Recorded so it is not forgotten** |
| **Spread unmeasured after 10:29 ET** | Nothing — ruled conservative | 90% of signals fire in hours with no spread data. Ruled: treat 0.975 as the widest hour applied everywhere. The 0.50–1.50 range moves breakeven by 4.0 pts at the A5 floor, so nothing hinges on it. Would need MBP files with a later window to improve |
| **Pre-open warm-up bias** | Study design | BB(20)/ATR(20) at 09:36 read bars 1.65× quieter than RTH. Measured effect on counts: −0.8% |
| **PARITY FAILS — volume-weighted levels disagree** | spec-1 Step 4 sign-off; prereg §10.1 | 2025-01-15 09:48: **2 of 8 fields match.** Price-only agree (BB 0.35, session high 0.25 and to the minute); **every volume-weighted one disagrees** — daily VWAP −9.50, NY VWAP +3.07, POC +4.00. Anchor, source price, chart timeframe and time-offset all ruled out by sweep. **Volume-feed difference is the surviving hypothesis**; decisive test is the 09:46 candle volume (archive: 4,279). At a 10-pt cluster tolerance a 9.5-pt VWAP error is nearly a full cluster width. See [`PARITY-COMPARISON.md`](vwap-bb/PARITY-COMPARISON.md) |
| **"Session low" definition unresolved** | Target menu | Angus read 20957.75 at "08:30"; archive says 20909.00 at 03:02 from the 18:00 Globex open. Either a reading-scope error or **a real difference in what a session is** — the latter would be a spec amendment. Only Angus can say |
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
Binds when Angus signs the four OPEN items. Spec pinned at SHA-256
`8ead725997b620678426bd41075bbdfd05356cab8325d2a92a95d63ee1bbf10f`.

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
