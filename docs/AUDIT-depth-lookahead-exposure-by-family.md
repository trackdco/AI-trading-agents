# AUDIT — depth-lookahead exposure, per London family

**2026-08-06.** Enumerated against the canonical ledger (`output/trial_ledger.jsonl`, 810
rows, 447 London) and the code, not from recollection. No trials charged.

**This audit corrects a claim I made.** Closing Phase 4 I wrote *"no graded London verdict
rests on the depth lookahead"* and reasoned that a lookahead only inflates, so nulls stay
null. The conclusion holds for the seven **graded** families. It is **not** the whole
answer, because three London families carry depth-derived ledger rows and are not in the
graded-verdict table: **LDN-CAN-01 (39 rows), LDN-OBK-01 (15), LDN-PO3-01 (16) — 70 rows
in total.** A blanket statement scoped to "graded verdicts" silently excluded them.

---

## The defect, in one line

`data/reference/depth_london/*.csv` has `ts_event` **floored to the minute**: `ts_recv`
runs a median 59.889s later against ~13 µs of capture latency, so the row labelled T is
the book at ~T+59.9s. Any consumer taking "the last row at or before minute M" reads the
book ~60 seconds **after** the decision.
Detail: `docs/FINDING-london-depth-timestamp-lookahead.md`.

## Per-family table

| # | family | read ts_event-anchored depth? | committed numbers affected | does the correction move the verdict? |
|---|---|---|---|---|
| 1 | **LDN-ATC-01** asian-trend-continuation | **No** — bars only. Verdict §7 states it: *"Bars only. No depth, no flow."* And per prereg §6.1 the 07:30 cohort could not have been depth-gated anyway, since London depth begins at 08:00 | none | **No.** FAIL stands, on the causally-clean 08:00+ cohort at −0.135R/n=65 |
| 2 | **LDN-CAN-01** canon-rebuild | **YES** — 39 ledger rows, `L3 winner/loser separation dep_*` and `p1_dep_*`, via `scripts/l3_london_trial.py` reading `output/london_matrix.parquet` | 39 rows, era `fit`. **All carry `effect = 0.0`** and none is marked as confirming. Estimates are descriptive WR gaps (−8.6% to +3.5%) with era-consistency flags | **No verdict to move** — this is an L3 separation scan, not a graded verdict. But **all 39 estimates are stale**: the corrected `london_matrix.parquet` changes `dep_*` on 705–746 of 749 rows. Because `effect = 0.0` throughout, the **DSR denominator is unaffected** — they add trial count but no variance. **9 of the 39 are `p1_*`** (one-minute-earlier reads), which under the correction are the closest to honest of the three anchors |
| 3 | **LDN-DEF-01** level-defense-flow | **No** — reads the **footprint**, not the depth snapshots, with its own `assert max(mins) <= t` firing on every event | none | **No.** FAIL stands. Remains the §2.5 worked example |
| 4 | **LDN-FLOW-01** flow-confirmation | **No** — minute-aggregate tape only | none | **No** |
| 5 | **LDN-INV-01** inventory-fade | **No.** (A regex sweep flagged trial `D:hinged-slope`; inspected — `D:` is a *group* label, not depth) | none | **No.** Its live flag is the era-local quintile, unrelated |
| 6 | **LDN-OBK-01** open-break | **YES** — 15 rows: `L3 flow A/S1 book_imb {low,mid,high}`, `wall_ratio_opp {low,mid,high}` × eras, plus 4 autopsy cuts. Effects −0.444 … +0.311 | **15 rows hold contaminated estimates** | **No verdict to move** (L3 pass, not a graded verdict), but the **numbers move materially** — see below |
| 7 | **LDN-PO3-01** power-of-three | **YES** — 16 rows, same shape on the F1 arm. Effects −0.418 … +0.124 | **16 rows hold contaminated estimates** | Same |
| 8 | **LDN-SWP-01** asia-sweep pair | **No.** (`D:dead-hour` is the dead-hour *group*, not depth) | none | **No.** Both FAILs stand; §8 already certifies the FAIL safe against its own cross-window defect |
| 9 | **LDN-TRAP-01** level-trap-fade | **No** — bars only | none | **No** |
| 10 | **LDN-VT-01** value-traverse | **No** — bars + volume profile | none | **No** |
| 11 | **LDN-VWAP-01** vwap-σ-rotation | **No** — bars + VWAP geometry | none | **No** |
| 12 | **LDN-WIN-01** window-structure | **No** — bars only | none | **No** |

**Totals: 3 of 12 families exposed, 70 of 447 London ledger rows (15.7%). Zero graded
verdicts affected.**

## LDN-CAN-01's depth layer, explicitly

Called out because it is the largest exposure and the least visible — it has no verdict
document, so it does not appear in any tracker table of graded families.

- **39 rows**, all era `fit`, written by `scripts/l3_london_trial.py`, sourced from the
  `dep_*` columns of `output/london_matrix.parquet` (tracked in git).
- Those columns are produced by `scripts/london_depth.py::depth_at`, which carried **two
  stacked hazards**: the ~60s floored-label lookahead, *and* an at-**fill** anchor
  (`main()` passes `t.fill`, not the decision minute). A limit fill requires price to have
  travelled to the order, so a book read anchored there contains part of the answer
  independently of the timestamp defect.
- Measured effect of the clock correction on the source artifact:

  | column | rows changed | of | median \|Δ\| |
  |---|---:|---:|---:|
  | `dep_imb` | 746 | 749 | 0.1201 |
  | `dep_thick` | 721 | 749 | 7.0 |
  | `dep_sup_m_res` | 718 | 749 | 7.0 |
  | `dep_resist` | 711 | 749 | 5.0 |
  | `dep_support` | 705 | 749 | 4.0 |
  | `dep_wall_below_d` | 698 | 749 | 2.0 |
  | `dep_wall_above_d` | 687 | 749 | 2.0 |
  | `dep_thick_d5m` | 581 | 599 | 11.0 |

- **Why the exposure is bounded anyway:** every one of the 39 rows carries `effect = 0.0`,
  so they contribute trial *count* to the DSR denominator but **no variance**, and the
  deflation bar is driven by the variance term. None is marked as confirming; the scan
  found nothing to select on. The largest WR gap is −8.6% (`dep_sup_m_res`), and a
  lookahead inflates rather than suppresses, so the honest version is weaker still.

## LDN-OBK-01 / LDN-PO3-01 — the numbers that actually move

These 31 rows were regenerated today with the corrected sign, band clean and clock. The
committed ledger rows were **not** updated, because `src.validation.trial_ledger.record()`
is append-only by design and only writes keys it has never seen.

Committed vs regenerated, `LDN-PO3-01` F1 `book_imb`, base cost:

| tercile · era | committed (contaminated) | regenerated (corrected) |
|---|---:|---:|
| low · 2025 | −0.4448 (n=51) | **−0.115 (n=52)** |
| mid · 2025 | −0.3783 (n=47) | **−0.318 (n=48)** |
| high · 2025 | −0.0502 (n=54) | **−0.422 (n=52)** |
| low · 2026 | −0.3965 (n=42) | **−0.004 (n=43)** |
| mid · 2026 | +0.1725 (n=39) | **+0.017 (n=39)** |
| high · 2026 | +0.2316 (n=44) | **−0.006 (n=43)** |

Every estimate moves, two change sign, and **`n` moves too** — the corrected timestamp
changes which trades carry a non-NaN book read at all.

**This needs an ANGUS ruling, and I have not acted on it.** The ledger is append-only on
purpose — *"a trial that was run happened, and a ledger you can quietly shrink is not a
ledger"* — so silently overwriting 31 estimates is not available. Three options:

1. **Annotate in place** — keep the rows, add a `contaminated` marker and a pointer to
   this audit. Preserves the append-only property; the DSR denominator keeps 31 rows whose
   effects are known-wrong.
2. **Append corrected rows under a distinguished key** (e.g. trial suffix `(v2 clock)`),
   leaving the originals as the historical record. Denominator grows by 31, which is the
   honest accounting if both were genuinely run.
3. **Retract and re-charge** — remove the 31 and record the corrected pass as a fresh
   trial set. Cleanest numerically, and the only option that breaks the append-only rule.

My reading is (2): both passes did happen, the corrected one is a real trial set, and
inflating the denominator is the conservative direction for a deflation bar. But this is a
ledger-integrity decision and it is Angus's.

## The claim that survives, and the one that does not

**Survives:** a lookahead can only *inflate* apparent edge, so every null established on
the defective clock stays null. Nothing that came back negative becomes positive.

**Does not survive:** "no graded London verdict rests on it" was true but **too narrow to
be the answer to the question asked**. 70 committed ledger rows across three families rest
on it. They change no verdict, they change the DSR denominator only by count and not by
variance, and none of them was ever selected on — but they are wrong numbers sitting in
the evidence base, and that is worth saying plainly rather than filing under a
technically-true summary.
