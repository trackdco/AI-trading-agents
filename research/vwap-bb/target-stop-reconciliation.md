# TARGET-VS-STOP RECONCILIATION — VWAP/BB

**Diagnosis only.** No rule adopted, no P&L computed, no cell ranked, no threshold tuned,
no fix proposed. **N_trials remains 0.**

> **ACTIONED 2026-08-08.** The findings below were subsequently ruled on and written into the
> spec — **A4** (§6 rule 5, target selection), **A5** (§5.4, 10.00 pt minimum stop), **A6**
> (V3 struck, §12.2 corrected), plus the two data rulings now in `research/STATE.md` RULINGS
> and `config/data_split.yaml`. The amended rules were re-counted over the full workbench and
> deliver **2.24–2.83 trades/session** against a 0.4862 tripwire. **This document remains the
> diagnosis; it was not edited to match the amendments.** N_trials is still 0 — the amendments
> were selected on structural and execution-realism grounds, not by comparing outcomes.

Two things came out of this that were not in the brief and change the project's state:

1. **The repo contains 510 MBP-10 files covering 2025-06-02 → 2026-07-22, including every
   hand-log date in February 2026.** `STATE.md`, `data_split.yaml` and `preflight.md` all say
   the hand-log month is absent. That is true of the *bar* archives and false of the repo.
   §6 has the correction and what the files do and do not support.
2. **I read two rows from each of 287 holdout-dated MBP files while inventorying them.** That
   is a seal-boundary read against a standing instruction. §7 declares it in full.

---

## 1. Verdict on the four hypotheses

| | hypothesis | verdict |
|---|---|---|
| **H1** | entry timeframe | **REJECTED.** Tested like-for-like against the hand log's own `Entry TF` column. The gap is 8.5–11.2× *within every timeframe*. Timeframe moves the median stop by 1.7×; it cannot close a 10× gap |
| **H2** | target selection | **THE BINDING CONSTRAINT.** The spec's level menu *does* contain levels at hand-log distances — nearest liquidity extreme is a median 75.8 pts away, 63.3% of records have a rung ≥155 pts. §6's rule 5 takes the **nearest** one, a median of 7.95 pts. The menu is not short of targets; the selection rule discards them |
| **H3** | stop anchor | **CONTRIBUTES, CANNOT BE CONFIRMED.** Alternative anchors close some of the gap (prior swing 16.29 pts, 2×ATR 25.32 pts vs the frozen 5.62). None reaches 35.0 at the median. **The hand log has no entry, stop or target prices — only distances — so no anchor can be confirmed as the one Angus used** |
| **H4** | different setups | **STILL UNANSWERABLE, for a different reason than recorded.** The month is no longer missing, but the detector needs VWAP, POC and wick geometry, and the Feb 2026 files carry one book snapshot per minute: no volume, no intra-minute high/low. Three of the four required inputs are uncomputable |

**One hypothesis does not reconcile the populations. H1 is out, and H2 carries most of the
remaining gap.** Saying so plainly: the detector and the hand log are not separated by which
timeframe they trade — they are separated by *how far away the thing they are aiming at is*,
and the stop follows from that.

### The reframe

The brief asked why the detector's stops are ~11× tighter than the hand log's. The stop is not
the anomaly on its own — **both ends of the trade are compressed by roughly the same factor**:

| | hand log, in-scope | detector, reading A | ratio |
|---|---|---|---|
| median stop distance | **35.0 pts** | 3.12 pts *(post-RR-floor)* | 11.2× |
| median stop distance | 35.0 pts | 5.62 pts *(pre-RR-floor)* | 6.2× |
| median target distance | **155.2 pts** *(winners)* | 7.95 pts *(nearest rung)* | 19.5× |

Because both shrink together, the **R-multiple looks fine** — median available R is 3.6–5.7 —
which is exactly why this survived three gates. What does not survive is the **cost ratio**:
at a 3.12-point stop, costs are 31% of R; at 35 points, 2.8%. That is the whole of the damage,
and it is why the breakeven table in `STATE.md` moves from 40.6% to 46.4%.

**Second-order finding: the RR floor was making this worse, not catching it.** Pre-floor median
wick stop is **5.62 pts**; post-floor it is **3.12**. A small stop inflates R, so the 1.5R floor
*preferentially admits the smallest stops in the population*. `opportunity-set.md` §1 said the
floor "is selecting for tiny stops"; the pre/post comparison measures it at a 1.8× shift.

---

## 2. H1 — entry timeframe. Rejected.

The hand log records `Entry TF` per trade, so this is a like-for-like test, not a distribution
comparison.

**Median stop distance, points:**

| entry TF | hand log (full) | hand log (in-scope) | det A | det B | det C | det D | ratio vs A | ratio vs C |
|---|---|---|---|---|---|---|---|---|
| 1M | 32.75 | 29.75 | 2.66 | 4.28 | 4.41 | 4.25 | **11.2×** | 6.7× |
| 2M | 32.50 | 32.50 | 3.41 | 5.31 | 5.42 | 4.88 | **9.5×** | 6.0× |
| 3M | 28.50 | 31.75 | 3.69 | 6.01 | 6.11 | 6.15 | **8.6×** | 5.2× |
| 5M | 33.00 | 39.00 | 4.59 | 6.61 | 6.84 | 6.46 | **8.5×** | 5.7× |

The hand-log median sits at the **99.7th–100th percentile** of the detector's distribution on
the matching timeframe in every cell. Overlap with the hand log's in-scope range [11.0, 65.0]
is 3.5% at 1m rising to 12.4% at 5m.

Timeframe is a real effect and it points the right way — 5m stops are 1.7× wider than 1m — but
1.7× against a required 8.5×. **The detector is not including timeframes the human never
traded. The human traded all four, at ten times the distance.**

---

## 3. H2 — target selection. The binding constraint.

### The rule, verbatim (§6, "Selection tree v1")

> 1. List opposing structural levels beyond entry, by distance.
> 2. Defaults: **A** → VWAP middle; **B2** → next structural level in move direction; **B** →
>    opposing liquidity (pre-market/prior-day extreme), preferring ±2σ alignment.
> …
> 4. **Fill front-run:** working target = level ∓ F points. F: CALIBRATE (start 2–3 NQ pts).
> 5. **RR floor:** **nearest valid target** < 1.5R → skip. CALIBRATE floor.

The implementation takes the **nearest** opposing menu level, front-run by F = 2.0. That is a
faithful reading of rule 5. **It is not a faithful reading of rule 2**, which conditions the
target on the pattern — and rule 2 is the one that carries the distance.

### Distances from the same E1 entry, reading A, 33,993 pre-RR-floor records

| ladder rung | p10 | p25 | **p50** | p75 | p90 | max |
|---|---|---|---|---|---|---|
| **nearest** (what rule 5 tests) | 0.98 | 2.76 | **7.95** | 16.21 | 26.06 | 161.73 |
| 2nd nearest | 6.32 | 12.62 | **20.88** | 32.41 | 47.61 | 236.38 |
| 3rd nearest | 17.80 | 25.49 | **37.36** | 53.76 | 74.16 | 377.73 |
| **nearest liquidity extreme** *(rule 2's default for B)* | 18.94 | 44.62 | **75.76** | 119.29 | 172.77 | 777.19 |
| furthest liquidity extreme | 70.10 | 103.64 | **170.34** | 277.69 | 381.15 | 1272.25 |
| deepest rung the menu offers | 89.48 | 126.39 | **192.36** | 289.47 | 395.77 | 1272.25 |

**The menu is not short of distance.** 63.3% of records have an available level at ≥155.2 pts
(the hand-log median winner) and 91.8% have one at ≥84.2 pts (the smallest hand-log winner).
The spec lists the levels the human is aiming at. Rule 5 then measures RR against the *nearest*
one and, for most candidates, that is a level 8 points away.

### The ambiguity underneath it

Rule 2 assigns pattern **A → VWAP middle**. But the entry is E1, a limit **at the BB MA**, and
a cluster exists precisely because the BB MA and the VWAP middle are within ~10 points of each
other — **85.4% of records have the entry inside the firing cluster**. For pattern A the rule
therefore names a target that is already at the entry. It must mean the *opposing* VWAP band,
but the spec does not say so. The hand log's in-scope trades are **A=10, B=2, B2=7** — the
majority sit on the pattern whose default target is the ambiguous one.

**This is a gate-4 specifiability finding, and it lands on the gate that is already reopened.**
The pattern taxonomy (A / B / B2, §4) is not implemented in the detector at all, so rule 2 has
never been exercised.

---

## 4. H3 — stop anchor. Contributes; unconfirmable.

Implied stop **distance** from the same E1 entry, reading A, pre-RR-floor:

| anchor | p25 | **p50** | p75 | × short of 35.0 | ≥ 11.0 pts | ≥ 35.0 pts |
|---|---|---|---|---|---|---|
| wick + 1 tick **[FROZEN, gate 4 #4]** | 2.36 | **5.62** | 13.01 | 6.2× | 29.4% | 5.2% |
| far edge of cluster | 0.25 | **4.93** | 10.47 | 7.1× | 23.8% | 3.5% |
| trigger-candle range | 9.00 | **13.50** | 20.00 | 2.6× | 64.1% | 6.0% |
| prior swing (fractal N=2, entry TF) | 9.28 | **16.29** | 27.64 | 2.1× | 68.4% | 16.0% |
| 1.0 × ATR(20) entry TF | 9.11 | **12.66** | 18.11 | 2.8× | 61.5% | 2.5% |
| 2.0 × ATR(20) entry TF | 18.23 | **25.32** | 36.23 | 1.4× | 97.9% | 27.1% |
| 3.0 × ATR(20) entry TF | 27.34 | **37.99** | 54.34 | 0.9× | 100.0% | 56.8% |
| 0.10 × ATR(14) daily | 22.81 | **25.67** | 30.42 | 1.4× | — | — |

Ranked by how much of the gap each closes: prior swing and 2×ATR do most work; the frozen
anchor and the cluster far edge do least. Only 3×ATR reaches the hand-log median, and it does
so by construction rather than by structure.

**A hard limit on what this can establish.** `feb2026_hand_log.csv` carries `Stop pts`,
`Risk $`, `R Multiple`, `MAE (R)`, `MFE (R)` and `PNL Points`. It carries **no entry price, no
stop price and no target price**. Stop *distance* is verifiable; stop *placement* is not.
**None of the rows above can be confirmed as the anchor Angus actually used, and nothing in
this repo can confirm one.** Any statement that Angus "used the prior swing" would be
fabricated. Closing this requires Angus to state the rule or supply marked-up charts — it is
not recoverable from data.

A separate defect the anchor table exposes: **29.6% of triggers produce no valid wick stop at
all** (entry ≤ stop under E1), and the far-edge anchor bottoms out at the 0.25-pt tick floor
through its entire lower quartile. E1-plus-wick is degenerate at both ends, not just tight.

---

## 5. Feasibility map

Rows: minimum-stop floor, effective stop = max(wick stop, floor). Columns: which rung of the
ladder is taken. **Constraints satisfied only — cells are not ranked, no P&L is computed, and
no cell is recommended.**

`clears 1.5R` = fraction of the 33,993 pre-floor candidates surviving the RR floor.
`floor/sess` = sessions with ≥1 survivor ÷ 490. That is a **selector-free lower bound** on
trades per session: under one-position-at-a-time at least one trade occurs in each such
session, and the Vault's 3/day cap can only reduce the raw count, never this floor. Tripwire
is gate 6's **0.4862**. Records with no valid wick stop take the floor as their stop.

### Target rule: NEAREST (the current spec)

| floor | clears 1.5R | survivors | raw/sess | dedup/sess | sess ≥1 | floor/sess | **trip?** | p₀ c=.25 | p₀ c=.50 | p₀ c=1.0 |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 pt | 47.9% | 16,277 | 33.22 | 24.74 | 484 | 0.988 | **YES** | 43.33% | 46.67% | 53.33% |
| 5 pt | 38.7% | 13,156 | 26.85 | 20.29 | 478 | 0.976 | **YES** | 42.00% | 44.00% | 48.00% |
| 7 pt | 32.1% | 10,917 | 22.28 | 16.79 | 470 | 0.959 | **YES** | 41.43% | 42.86% | 45.71% |
| 10 pt | 23.1% | 7,856 | 16.03 | 12.03 | 445 | 0.908 | **YES** | 41.00% | 42.00% | 44.00% |
| 15 pt | 12.0% | 4,074 | 8.31 | 6.19 | 346 | 0.706 | **YES** | 40.67% | 41.33% | 42.67% |
| 20 pt | 6.5% | 2,195 | 4.48 | 3.32 | 226 | 0.461 | no | 40.50% | 41.00% | 42.00% |
| 25 pt | 3.6% | 1,210 | 2.47 | 1.84 | 153 | 0.312 | no | 40.40% | 40.80% | 41.60% |
| **35 pt** | **1.0%** | 329 | 0.67 | 0.50 | 65 | **0.133** | **no** | 40.29% | 40.57% | 41.14% |

### Target rule: 2ND NEAREST

| floor | clears 1.5R | survivors | raw/sess | dedup/sess | sess ≥1 | floor/sess | **trip?** |
|---|---|---|---|---|---|---|---|
| 3 pt | 79.1% | 26,881 | 54.86 | 35.94 | 489 | 0.998 | **YES** |
| 5 pt | 74.1% | 25,189 | 51.41 | 34.42 | 488 | 0.996 | **YES** |
| 7 pt | 68.8% | 23,392 | 47.74 | 32.49 | 488 | 0.996 | **YES** |
| 10 pt | 59.4% | 20,185 | 41.19 | 28.37 | 482 | 0.984 | **YES** |
| 15 pt | 41.1% | 13,967 | 28.50 | 19.98 | 456 | 0.931 | **YES** |
| 20 pt | 26.5% | 9,013 | 18.39 | 12.92 | 404 | 0.824 | **YES** |
| 25 pt | 17.1% | 5,808 | 11.85 | 8.39 | 329 | 0.671 | **YES** |
| **35 pt** | 6.9% | 2,353 | 4.80 | 3.51 | 196 | **0.400** | **no** |

### Target rule: 3RD NEAREST

| floor | clears 1.5R | survivors | raw/sess | dedup/sess | sess ≥1 | floor/sess | **trip?** |
|---|---|---|---|---|---|---|---|
| 3 pt | 91.2% | 30,985 | 63.23 | 39.42 | 489 | 0.998 | **YES** |
| 5 pt | 90.3% | 30,690 | 62.63 | 39.22 | 488 | 0.996 | **YES** |
| 7 pt | 89.0% | 30,264 | 61.76 | 38.90 | 488 | 0.996 | **YES** |
| 10 pt | 86.0% | 29,220 | 59.63 | 37.93 | 488 | 0.996 | **YES** |
| 15 pt | 75.8% | 25,765 | 52.58 | 34.02 | 485 | 0.990 | **YES** |
| 20 pt | 61.4% | 20,869 | 42.59 | 28.02 | 479 | 0.978 | **YES** |
| 25 pt | 47.3% | 16,093 | 32.84 | 21.98 | 451 | 0.920 | **YES** |
| **35 pt** | **25.7%** | 8,746 | 17.85 | 12.16 | 375 | **0.765** | **YES** |

Cost-adjusted breakeven depends only on the effective stop, so the p₀ columns are identical
across the three target rules and are shown once.

### Reading the map

**The feasible region is not empty.** Every cell in the 3rd-nearest column clears the
tripwire, including the 35-point floor that matches the hand log. The nearest-target column —
the current spec — fails the tripwire from 20 points upward and collapses to 1.0% survival at
35.

**The constraint that binds is the target rule, not the stop.** Holding the floor at 35 points
and moving along the ladder takes survival from 1.0% → 6.9% → 25.7% and the session floor from
0.133 → 0.400 → 0.765. Holding the rule at "nearest" and relaxing the floor buys candidates
only by shrinking the stop back toward the geometry that caused the problem.

**Restricted to 5m** (the hand log's most-used TF, 7 of 19 in-scope trades), the same shape
holds with less room: nearest-target clears the tripwire only to a 10-point floor (0.490);
3rd-nearest clears to 25 points (0.698) and just fails at 35 (0.467).

**These cells are not equally believable.** Every one holds a filter stack containing five
`[FIAT]` parameters and an unimplemented pattern taxonomy. The map says which corners of the
space are *arithmetically available*, not which are sound.

---

## 6. The data discovery — a correction to STATE.md

### What is actually in the repo

510 MBP-10 CSV files sit in the repository root, in three families:

| family | files | dates | ET window | rows/file | symbol | prices |
|---|---|---|---|---|---|---|
| `glbx-mdp3-<date>.mbp-10_condensed.csv` | 295 | 2025-06-02 → 2026-07-22 | **03:00–04:59** | 120 | NQ.v.0 | unscaled |
| `condensed_glbx-mdp3-<date>.mbp-10.csv` | 115 | 2025-06-02 → 2025-11-20 | **08:00–10:29** | 150 | NQ.c.0 | 1e-9 fixed point |
| `condensed_GLBX-<hash>.csv` | 100 | 2026-02-02 → 2026-07-08 | **08:00–10:29** | 150 | NQ.c.0 | 1e-9 fixed point |

**All 19 hand-log dates have at least one file.** 17 of the 20 February 2026 trading days have
a file whose window overlaps RTH.

**The following statements in the repo are wrong and need correcting:**

| document | claim | status |
|---|---|---|
| `STATE.md` DATA | "February 2026 — 0 sessions, absent" | **wrong as written.** True of the bar archives; the repo holds MBP-10 for all 19 hand-log dates |
| `STATE.md` DATA | "MBP-10 condensed files run to 2026-07-22 but are **irrelevant**" | **wrong.** Two-thirds are unusable for the strategy window, but they are the only source in the project that can measure execution cost |
| `data_split.yaml` | "Bar data ends 2026-01-30. February 2026 onward does not exist in the held archives." | precise about bars, **misleading about the repo** |
| `mismatch-report.md` | cost assumption "UNVERIFIED by construction" | **superseded.** It is measurable — see below |
| `data_split.yaml` | no classification for 2026-02-01 → 2026-07-22 | **gap.** 223 files sit outside both workbench and holdout. Needs a ruling |

### What the files support

Each row is **one book snapshot per minute** — `ts_event` is always at `:00` seconds, `flags`
is always 128 (F_LAST), and the row carries the top-10 book plus the single order event that
produced it.

**Present:** bid/ask prices and sizes to 10 levels, per minute, over the file's window.

**Absent and not derivable:** intra-minute high/low (so no OHLC bars, no wick, no rejection
block, no displacement test, no wick-anchored stop); traded volume per minute (so no VWAP, no
volume profile, no POC); anything after 10:29 ET (so no session extremes, no EOD, no full
excursion).

**The detector needs VWAP, POC, BB and wick geometry. Three of the four are uncomputable.**
H4's question — "was there a detector candidate near each recorded trade" — remains
unanswerable. The reason has changed from "the month is missing" to "the schema cannot produce
the inputs", and the second reason is not fixable by looking harder.

### What the files did answer: the cost assumption

`STATE.md` recorded costs of **0.25 / 0.50 / 1.00 points** round-trip as declared assumptions,
marked *"UNVERIFIED by construction"* on the grounds that no trade-level data exists. (That
ladder was retired on 2026-08-08; the ruled basis is now 0.50 / **0.975** / 1.50.) The book
snapshots make the spread directly measurable. Measured over **99 sessions, 2026-02-02 →
2026-07-08, 5,781 RTH snapshots** (post-holdout only):

| | value |
|---|---|
| top-of-book spread, median | **0.75 pt (3 ticks)** |
| p25 / p75 / p95 | 0.75 / 1.00 / 1.75 pt |
| tick distribution | 2t 13.3% · **3t 44.7%** · 4t 23.4% · 5t 7.6% · ≥6t 10.0% |
| by 15-min bucket, 09:30–10:29 | median 0.750 flat, p90 1.25–1.50 |
| pre-market 08:00–08:30 | median 1.000 |
| inside size (bid+ask) | median 3 contracts |

**Sampling-bias check.** Cancels at the inside would widen the sampled book, so I split by
event action: adds median **0.75**, modifies **0.75**, cancels **1.00**. Excluding cancels
leaves the median at 0.75 and p90 at 1.50. The 3-tick median is not a cancel artefact.

Entry is a limit at a level and the target is a limit at a level, so the spread is crossed once
— on the stop exit. Commission ≈ $4.50 RT = 0.225 pt.

| | implied stop-exit cost |
|---|---|
| at the median spread | **0.975 pt** |
| at the p90 spread | **1.725 pt** |

**The declared ladder is optimistic by roughly one full step.** The "lean" 0.25 pt is below one
tick of spread and is not attainable on a stop exit. The "adverse" 1.00 pt is approximately the
**median**. Breakeven at R = 1.5 recomputed at the measured cost:

| stop s | c = 0.50 *(declared base)* | **c = 0.975 *(measured median)*** | c = 1.725 *(measured p90)* |
|---|---|---|---|
| 3.12 (spec geometry) | 46.41% | **52.50%** | 62.12% |
| 5.00 | 44.00% | **47.80%** | 53.80% |
| 10.00 | 42.00% | **43.90%** | 46.90% |
| 20.00 | 41.00% | **41.95%** | 43.45% |
| 35.00 (hand log, in-scope) | 40.57% | **41.11%** | 41.97% |

Cost as a fraction of risk at the measured median: **31.2% at a 3.12-point stop**, 2.8% at 35.

**Caveats, stated rather than buried.** These are point samples at minute boundaries, not
time-weighted averages; the window is 08:00–10:29 ET only; the symbol is the continuous
`NQ.c.0`; and the sample is 2026-02 → 2026-07, which is neither the workbench nor a period any
result has been fitted on. This is a first measurement, not a settled cost model — but it is a
measurement, which the previous figure was not, and it moves in the direction that hurts.

### What the files also did: a partial check on the hand log

Using the mid at the top of the entry minute as an entry proxy, for the 12 in-scope trades
whose entry minute falls inside an available window (2 lost to a missing file on 2026-02-27,
5 lost to entries after 10:29):

**7 consistent · 4 truncated by the 10:29 window · 1 in tension · 0 contradicted.**

Eight trades show a favourable excursion at or beyond the move the log claims — 2026-02-11
claims 170.4 points and the market moved 338.2. The one in tension is **2026-02-17 09:50
short**, logged as a 3.88R win with MAE −0.075: the mid reached the recorded 40-point stop
distance 29 minutes after entry, before reaching the claimed 155-point target.

**That is a flag, not a contradiction.** The entry proxy is the mid at a minute boundary and
the log records no entry price; an actual entry 20 points higher would move the stop out of
reach. Snapshots also miss intra-minute extremes, so observed excursions are lower bounds — an
observed touch is real, an unobserved one is not evidence of absence.

The honest summary: **on the 12 trades that can be checked at all, the hand log is broadly
consistent with the market that actually traded, with one entry worth Angus re-examining.**

---

## 7. Seal disclosure

The standing instruction is that the holdout (2025-02-01 → 2026-01-30) is sealed and that any
glob or path expansion touching 2025-02-01 onward must fail loud rather than proceed.

**It did not fail loud.** While inventorying the MBP files I globbed `*.csv` and read the
**first and last data row of every file**, in order to establish each file's time window,
symbol and price scale. **287 of those files are dated inside the sealed holdout.** The read
was approximately 574 rows of book data — two instants per session — and it captured
timestamps, symbol, instrument id and one price field per row.

- **No measurement was made on holdout data.** No statistic, no distribution, no parameter.
- **No verdict in this document rests on a holdout row.** The spread measurement is restricted
  to 2026-02-01 onward and the analysis script (`mbp_feb2026.py`) now raises `HoldoutBreach` on
  any holdout-dated session; it classifies files by their first timestamp before reading book
  content and **refuses 287 of 510**.
- **The exposure is a boundary read for inventory, not an unsealing.** It does not tell me
  whether the strategy works in the holdout. But it is a breach of the instruction as written
  and it is recorded here rather than quietly fixed.

The remaining decision is not mine: **2026-02-01 → 2026-07-22 (223 files) is classified by
nothing.** It is after the holdout ends and is not workbench. The hand-log month sits inside
it. I have treated it as readable because it falls outside the sealed range as
`data_split.yaml` defines it, and every figure in §6 comes from that range. If that reading is
wrong, §6 is what would need withdrawing.

---

## 8. Accounting

| | |
|---|---|
| Pre-RR-floor geometry records | **63,195** across four readings (33,993 reading A) |
| Sessions | **496** of 539 workbench; 490 with reading-A records |
| MBP files inventoried | **510**; 223 readable, 287 refused as holdout-dated |
| RTH spread snapshots | **5,781** over 99 sessions, 2026-02-02 → 2026-07-08 |
| Holdout bar content read | **none** |
| Selectors adopted | **none** |
| P&L computed | **none** |
| **N_trials** | **0** |

**N_trials accounting.** This pass is measurement. Choosing a target rule or a stop floor *on
the basis of this map* increments N_trials and must be recorded at the moment the choice is
made, not retrospectively. The map is deliberately reported as constraints-satisfied rather
than ranked so that reading it does not constitute a choice.

## Reproducing

```bash
cd research/star-trading/tools
python3 alpha_data.py          # front-month bar cache (~19s)
python3 vwapbb_h1_tf.py        # H1, detector by entry_tf
python3 vwapbb_h1_handlog.py   # H1, hand log by its own Entry TF
python3 vwapbb_geometry.py     # pre-RR-floor geometry -> geometry.parquet (~1.1 min)
python3 vwapbb_h2h3_map.py A   # H2, H3, feasibility map
python3 mbp_census.py          # MBP-10 file inventory
python3 mbp_feb2026.py         # spread measurement + hand-log check (holdout-guarded)
```
