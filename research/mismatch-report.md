# MISMATCH REPORT — state reconciliation, 2026-08-07

Every figure below was recomputed from source files. Nothing was carried forward from a
report. Where source and report differ, **the source wins**.

No document was corrected in this pass. Correcting is a separate job. N_trials remains 0.

---

## Mismatch table

| # | NAME | SOURCE VALUE | REPORTED VALUE | FILE REPORTING IT | VERDICT |
|---|---|---|---|---|---|
| 1 | Hand-log mean R on winners | **3.678** (in-scope, n=13) | 4.23 | `preflight.md` ×2, `hand_log_scope.md` | **MISMATCH — scope error** |
| 2 | Gate-3 stop `s` | **35.00** (in-scope median) | 32.75 (full-log median) | `preflight.md` gate 3, `signal-count.md` | **MISMATCH — minor** |
| 3 | Sessions processed, opportunity run | 496 ran / 483 ≥1 cand / 482 prior | "496 of 539" | `opportunity-set.md` | **AMBIGUOUS — all three true** |
| 4 | Candidates per session, reading A | **26.13** raw / **19.83** deduped | 20.93 (post-RR, probe) | `signal-count.md` rev 2 | **MISMATCH — unit** |
| 5 | Gate-6 tripwire | **0.4862** (÷4) / 0.5132 (÷5) | both in circulation | `preflight.md`, `signal-count.md` | **RESOLVED — ÷4 current** |
| 6 | Total archive rows | **1,656,226** | 1,656,230 | Stage 0 audit (in `alpha-feasibility.md`) | **MISMATCH — trivial** |
| 7 | Hand log win/loss/BE | 20 / 7 / 1 | 20 / 7 / 1 | `preflight.md`, `hand_log_scope.md` | MATCH |
| 8 | In-scope subset | 19 trades, 13 wins | 19 trades, 13 wins | `preflight.md`, `hand_log_scope.md` | MATCH |
| 9 | Wilson full log | [52.9%, 84.7%] | [52.9%, 84.7%] | `preflight.md` | MATCH |
| 10 | Wilson in-scope | [46.0%, 84.6%] | [46.0%, 84.6%] | `preflight.md`, `hand_log_scope.md` | MATCH |
| 11 | Workbench sessions | 539 | 539 | `preflight.md`, `data_split.yaml` | MATCH |
| 12 | Holdout sessions | 257 | 257 | `preflight.md`, `data_split.yaml` | MATCH |
| 13 | Globex sessions total | 796 | 796 | `preflight.md` | MATCH |
| 14 | Full-1380 sessions | 688 (86.4%) | 688 (86.4%) | `preflight.md` gate 5 | MATCH |
| 15 | Front-month bars | 1,089,712 | 1,089,712 | `preflight.md` gate 5 | MATCH |
| 16 | Last bar in dataset | 2026-01-30T21:59Z | 2026-01-30T21:59Z | `preflight.md` step 0 | MATCH |
| 17 | Feb-2026 sessions present | 0 | 0 | `preflight.md` gate 5 | MATCH |
| 18 | Candidate records total | 45,214 | 45,214 | `opportunity-set.md` | MATCH |
| 19 | Stop distance median, reading A | 3.125 pts | 3.12 | `opportunity-set.md` | MATCH |
| 20 | Stop distance min | 0.0125 pts | 0.0125 | `opportunity-set.md` | MATCH |
| 21 | Fraction stop < 1 pt | 17.9% | 17.9% | `opportunity-set.md` | MATCH |
| 22 | Conviction distribution | 1:2,540 2:14,716 3:5,325 | 8.8/65.7/25.5% (A) | `opportunity-set.md` | MATCH |
| 23 | Blocked fraction, reading A | 54.2% | 54.2% | `opportunity-set.md` | MATCH |
| 24 | Overlap rate A / D | 38.8% / 65.3% | 38.8% / 65.3% | `opportunity-set.md` | MATCH |
| 25 | Breakeven @ s=32.75, c=0.50 | 40.61% | 40.61% | `preflight.md` gate 3 | MATCH |
| 26 | Gate-6 required n, ÷4, p₁=0.50 | 262.1 | 262 | `signal-count.md` | MATCH |
| 27 | Sessions < 1380 bars | 108 (71/34/3) | 108 | `preflight.md` gate 5 | MATCH |

---

## Detail on each mismatch

### 1. "+4.23R on winners" — the one that matters

**Source:** the 4.23 figure is the **mean R over all 20 winners in the FULL 28-trade log**,
and it **includes the +12.98R trade of 2026-02-25 at 09:25**.

That trade is **OUT OF SCOPE** under Amendment A1 — it precedes the 09:36 first-signal bar and
is listed as out-of-scope in `hand_log_scope.md` itself.

| basis | n | mean R | median R | max |
|---|---|---|---|---|
| winners, full log | 20 | **4.226** | 3.680 | 12.98 |
| winners, in-scope | 13 | **3.678** | 3.370 | 5.98 |

**Documents carrying the wrong figure:** `research/vwap-bb/preflight.md` (twice — the
"corrections to the brief" section and gate 3), and `data/reference/hand_log_scope.md`
(which lists +12.98R as out-of-scope on one line and cites 4.23R as the winners' mean a few
lines later — internally inconsistent).

**Was a decision made on it?** Partly. Gate 3's breakeven table includes a row at "R = 4.23
(realised)", giving p₀ = 19.41%. At the correct in-scope 3.678 that row becomes **21.38%**.
Neither figure changes gate 3's PASS — the hand-log win rate clears both by a wide margin — so
**no verdict flips**. But the number was used to characterise the strategy's realised payoff
after A1 had already excluded the trade inflating it, which is a scope error, not a rounding
one.

### 2. Gate-3 stop distance

Gate 3 computed breakeven at **s = 32.75**, the median stop of the full 28-trade log. The
in-scope median is **35.00**. Effect at c = 0.50: p₀ moves 40.61% → **40.57%**. Immaterial to
the verdict; recorded because the same scope error as #1 produced it.

### 3. Session counts — three numbers, all correct

| number | means |
|---|---|
| **496** | sessions the detector ran on (539 − 43 skipped) |
| **483** | sessions with ≥1 candidate in any warmup treatment |
| **482** | sessions with ≥1 candidate under warmup = `prior` |

The gap is **13 sessions that ran and produced zero candidates**: 2023-04-27, 2023-12-07,
2023-12-18, 2023-12-26, 2023-12-28, 2024-01-08, 2024-02-12, 2024-05-22, 2024-06-05,
2024-07-11, 2024-07-12, 2024-10-23, 2024-12-16. All have 1,373–1,380 bars — full sessions that
simply generated no qualifying trigger.

**Not a defect.** Every one of the 56 workbench sessions absent from the parquet is
accounted for: 43 skipped with a named reason (holiday/short 21, mixed contract 6, roll 8,
session-after-roll 8) plus these 13 zero-candidate sessions. `opportunity-set.md` reports 496
without drawing the distinction, which is defensible but ambiguous.

### 4. Candidates per session — a unit mismatch, not a value error

`signal-count.md` rev 2 reports reading A at **20.93** post-RR pre-cap. The parquet gives
**26.13**. They measure different things:

- the signal count **deduplicated to one signal per close-minute**, highest TF winning (MTF
  arbitration per §1)
- the opportunity run **emits one record per (cluster × direction × entry-TF)** with no dedup

Deduplicating the parquet the same way gives **19.83/session** over 496 sessions, against
20.93 over the 141-session probe — consistent, the residual being sample.

**Consequence:** `opportunity-set.md`'s per-session figures are **not** comparable to
`signal-count.md`'s without deduplication, and the report does not say so. Any downstream
comparison of the two is wrong unless the units are aligned first.

### 5. Gate-6 tripwire — resolved, both correct

0.4862 at ÷4 (management axis after V3 is struck) and 0.5132 at ÷5 (before). **0.486 is
current.** Both appear in the record; the ÷5 figure is superseded and labelled as such in
`signal-count.md`.

### 6. Total archive rows

1,656,226 data rows recomputed vs 1,656,230 reported. The difference is exactly **4 — the CSV
header line of each of the four archives.** Trivial, recorded for completeness.

---

## Figures that could not be verified

| figure | why |
|---|---|
| Reference-chart values for the parity gate | Angus has not supplied readings for the relocated dates 2025-01-15 / 2025-01-22. **UNVERIFIED** — no source exists yet |
| Cost assumption 0.25 / 0.50 / 1.00 pts | No trade-level data exists (Stage 0). These are declared assumptions, not measurements. **UNVERIFIED by construction** |
| Hand-log entry/target prices | The CSV carries `Stop pts`, `Risk $`, `R Multiple`, `PNL Points` but **no entry, stop or target price columns**. Stop *distance* is verifiable; stop *placement* is not. **UNVERIFIABLE from this file** |
| Holdout bar content | Sealed. Session counts read from the index only; no bar was read |

The hand-log gap in row 3 is worth noting: the brief asked for "per trade: entry, stop,
target" and those fields **do not exist in the source file**. Only distances and multiples are
recorded. Any figure purporting to give hand-log entry or target prices would be fabricated.
