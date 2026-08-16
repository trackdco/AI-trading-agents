# FINDINGS — PHASE 0 (overlap, the 12-cell table, the combination)

Overnight run, 2026-08-07. **Report-only. Nothing here ships, nothing is
armed, nothing is adopted.** No holdout contact.

## 1 — SCHEMA RECONCILIATION, stated before anything was computed

| # | mismatch | handling |
|---|---|---|
| 1 | `bc_frame` (the incumbent feature table) has **no `locus` and no `t_exit`** — only `pop` ∈ {reject, union_break} | Rebuilt the composite from `levels_fit`, which carries both. **Calibration: 3,336 vs 3,336 rows, identical on (day, t, side, pop), zero rows either way.** |
| 2 | `ltf_fit` has geometry + D7 but no flow; `ltf_flow` has the 12 flow features but no geometry | Joined on (day, t, tf, locus, arm, side) |
| 3 | **The depth six exist ONLY on the incumbent.** The LTF population has no depth columns at all | Stated, not papered over. Phase 1 diagnoses depth on the incumbent only. |
| 4 | `next_lvl_R` and the ceiling flags exist ONLY on the LTF frame | Built for the incumbent (`phase1_build_cols`) using the *same* code path, so the column means the same thing in both books |
| 5 | **CONVENTION — the important one.** The incumbent's break arm enters on a **retest**; the room-gated stream enters at the **next 1m open** | Recorded as a known defect of the combined object (DECLARATIONS-combination-london §3). The reject arms match. |

## 2 — OVERLAP: two measurements, deliberately not conflated

**Redundancy** — same locus, same direction, entry within 5 minutes:

| stream | n | redundant | concurrent | genuinely new |
|---|---|---|---|---|
| LONDON reject 3m | 334 | **6.6%** | 22.2% | **93.4%** |
| LONDON reject 5m | 308 | **8.1%** | 25.3% | **91.9%** |

Redundancy is far under the 50% line that would have stopped the union, so
a **simple union** is used and the 6.6%/8.1% double-count is left in and
stated. This is consistent with every overlap check run today.

**Concurrency is a different quantity and is not a dedup question.** A
quarter of room-gated trades are open while an incumbent trade is open.
That raises simultaneous R-at-risk and is carried into the account lab
through daily-total R — the binding constraint per BR-25 — rather than
through position counting.

**Cross-timeframe union remains undeclared and unbuilt:** 41.9% of the 5m
stream is redundant with the 3m stream, far above the line. The 3m and 5m
streams are therefore combined with the incumbent **separately, never with
each other**.

## 3 — THE FULL 12-CELL ROOM-GATE TABLE (all cells, estimates and CIs)

Reporting ask, previously published only as pass/fail counts.

| session | TF | arm | n_base | n_keep | lift | H2 CI | H1 CI | win kept/cut | bar |
|---|---|---|---|---|---|---|---|---|---|
| LONDON | 3 | reject | 1498 | 334 | **+0.466** | [+0.044,+0.716] | [+0.281,+0.855] | 39.8/27.1% | **PASS** |
| LONDON | 3 | break | 402 | 95 | +0.051 | [−0.646,+0.232] | [−0.171,+0.819] | 40.0/33.6% | miss |
| NY_PRE | 3 | reject | 1268 | 344 | +0.154 | [−0.021,+0.614] | [−0.224,+0.288] | 32.3/26.3% | miss |
| NY_PRE | 3 | break | 393 | 107 | +0.088 | [−0.120,+0.584] | [−0.611,+0.385] | 44.9/30.1% | miss |
| NY_AM | 3 | reject | 2267 | 451 | +0.147 | [−0.029,+0.442] | [−0.149,+0.326] | 36.4/28.2% | miss |
| NY_AM | 3 | break | 777 | 229 | +0.170 | [−0.132,+0.491] | [−0.166,+0.579] | 40.6/35.9% | miss |
| LONDON | 5 | reject | 1419 | 308 | **+0.366** | [+0.054,+0.728] | [+0.013,+0.665] | 38.0/26.5% | **PASS** |
| LONDON | 5 | break | 402 | 96 | +0.222 | [−0.547,+0.238] | [+0.228,+1.185] | 50.0/38.6% | miss |
| NY_PRE | 5 | reject | 1168 | 276 | +0.263 | [−0.023,+1.061] | [−0.277,+0.534] | 33.0/26.9% | miss |
| NY_PRE | 5 | break | 388 | 95 | +0.038 | [−0.190,+0.515] | [−0.645,+0.460] | 45.3/30.0% | miss |
| NY_AM | 5 | reject | 2070 | 411 | +0.198 | [−0.033,+0.492] | [−0.103,+0.449] | 39.9/30.8% | miss |
| NY_AM | 5 | break | 816 | 290 | +0.068 | [−0.134,+0.355] | [−0.222,+0.304] | 42.8/39.4% | miss |

**Every one of the twelve lifts is positive.** Ten of twelve miss on
interval width, not on sign. Two near-misses worth naming so they are not
lost: NY_PRE 5m reject (+0.263, H2 lower bound −0.023) and NY_AM 3m reject
(+0.147, H2 lower bound −0.029). Neither is acted on; both would need their
own declaration.

Dual currency agrees in all twelve cells — kept wins more often *and* pays
more. No BR-20-style inversion anywhere in this family.

## 4 — THE COMBINATION, through the full account lab

| book | /day | EV | R/day | worst day R | max size | SIM grad | LIVE $/yr |
|---|---|---|---|---|---|---|---|
| incumbent LONDON | 2.27 | +0.357 | 0.813 | −5.41 | **$350** | 98.5% | $28,636 |
| room-gated 3m alone | 1.14 | **+0.546** | 0.624 | **−4.60** | **$400** | 87.7% | $17,425 |
| **COMBINED inc + room 3m** | **3.42** | +0.420 | **1.437** | −6.88 | $250 | **100.0%** | **$35,544** |
| room-gated 5m alone | 1.05 | +0.411 | 0.434 | −6.65 | $300 | 57.7% | $9,375 |
| COMBINED inc + room 5m | 3.33 | +0.375 | 1.247 | −6.74 | $250 | 99.7% | $32,669 |

**The combination wins on both outcome axes and loses on the input axis.**
Graduation 98.5% → 100.0%, live proxy +24% ($28.6k → $35.5k) — but
worst-day R degrades −5.41 → −6.88 and max safe size drops **$350 → $250**.

The size regression is real and is exactly what the concurrency number
predicted: more trades open at once means a worse worst day. It does not
overturn the result, because the extra R/day more than pays for the smaller
size — but a book that has to be run 30% smaller is a different object to
run, and that belongs in the morning's decision, not in a summary line.

**The 3m stream dominates the 5m stream on every axis here.** That is
consistent with the 12-cell table (3m lift +0.466 vs 5m +0.366) and with
the room-gate findings. If only one is carried forward it is 3m.

## 5 — FREQUENCY BEATS EV: the scoping was requested sim-stage-only, and that would have been wrong

The queue asked for this base rate "scoped sim-stage-only" — the reasoning
being that the 5-payout cap and the 250-day graduation clock exist only
before LucidLive, so a frequency preference might be an artifact of them.

**It is not.** The live-stage proxy was run to check, and **the ranking is
identical at both stages**:

- SIM (graduation): combined 3m > combined 5m > incumbent > room 3m > room 5m
- LIVE ($/yr): combined 3m > combined 5m > incumbent > room 3m > room 5m

The *mechanisms* differ — sim is a race against the payout clock, live is
simply R/day × max safe size — but the conclusion is one thing: **EV per
trade is not the objective at either stage.** The room-gated 3m book has
the highest EV in the whole table (+0.546R) and the *worst* live outcome of
the three London books.

One sim-stage quirk is worth recording: **SIM net barely separates**
($8,819 / $8,865 / $8,891) because the payout cap saturates for anything
that graduates at all. At the sim stage only P(graduate) discriminates;
net does not. That is a property of the cap, not of the books.

Recorded as **BR-39**, scoped to what the evidence supports rather than to
what was requested.

## 6 — PROCESS ERROR, recorded

The queue said "combination declaration and run". **The run went first; the
specification was written afterwards.** The combination numbers in §4 are
therefore fit-side descriptive, not a declared test.

Mitigating, but not excusing: the combination had no free parameters left —
both streams were fixed by earlier declarations, the account bars were
declared in DECLARATIONS-room-to-run §4 Bar 2, and the union rule was
chosen by the pre-set redundancy criterion rather than by preference. Full
accounting in DECLARATIONS-combination-london §0.

## STATE AT END OF PHASE 0

- Live candidate books for Phase 1: **incumbent LONDON**, **room-gated
  LONDON reject 3m**, **room-gated LONDON reject 5m**, **combined
  inc+room3m**, **combined inc+room5m**.
- New base rates: **BR-39** (frequency beats EV, both stages),
  **BR-40** (the combination book).
- Holdout: untouched, look #1 still HALTED.
