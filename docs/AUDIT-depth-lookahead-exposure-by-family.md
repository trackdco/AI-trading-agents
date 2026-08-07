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

---

## RULING AND EXECUTION — ANGUS 2026-08-06, option 2

**And the scope was larger than the 31 rows I reported.** I filtered on the two *depth*
features and missed that the **inverted delta sign** contaminates the four tape features
in the same pass. The true set:

| cause | features | rows |
|---|---|---:|
| inverted delta sign (`A` signed positive) | `delta_entry`, `delta_pre5`, `delta_sweep`, `absorb_extreme` | 64 |
| ~60s depth lookahead | `book_imb`, `wall_ratio_opp` | 31 |
| | **total** | **95** |

Split LDN-OBK-01 47 / LDN-PO3-01 48; by stage, 71 `L3 flow` and 24 `autopsy`. The 8
`disp_frac` / `width_rel` autopsy rows are pure geometry and are **not** affected.

**Executed:** ledger **810 -> 903 rows**. No row edited, none deleted.

- **93 corrected rows appended** under the distinguished key suffix `[v2 clock+sign]`,
  regenerated from the corrected artifact by calling the same `feature_table()` and
  `cuts()` the originals came from -- not re-typed from markdown.
- **93 originals marked** `status = "superseded"`, `superseded_by = <corrected key>`.
  Zero dangling pointers.
- **2 originals marked** `status = "superseded_no_counterpart"` -- the corrected pass
  produces **no equivalent cell**, because the clock fix changes which trades carry a
  book read at all and `n` fell below the reporting threshold:
  `LDN-PO3-01 - L3 flow F1 wall_ratio_opp mid - 2026` and
  `LDN-PO3-01 - autopsy F1 cut wall_ratio_opp high - 2025+2026`.
  `superseded_by` is null on these because there is genuinely nothing to point at.
- **39 LDN-CAN-01 `dep_*` rows marked** `status = "stale"` -- effect 0.0, count without
  variance, never selected on. No correction.
- **1 corrected-pass cell NOT charged**, per the no-trials instruction:
  `LDN-OBK-01 - L3 flow A/S1 wall_ratio_opp mid - 2026` newly qualifies under the
  corrected clock and has no original to supersede. It is a genuine new cell and charging
  it is a separate decision.

**DSR impact: negligible.** 812 -> 903 trials, effect sd 0.1821 -> **0.1811**, deflation
bar **+0.5820 -> +0.5843** (+0.4%). Adding 93 rows raises the count and very slightly
lowers the variance; the two nearly cancel.

**Schema.** `scripts/ledger_io.COLUMNS` gains `status` and `superseded_by`, with permitted
`status` values enumerated in `STATUS`. `src/validation/trial_ledger.py` no longer writes
the derived parquet -- it reads and writes the canonical JSONL through `scripts.ledger_io`,
and `tests/test_ledger_integrity.py` fails if any module writes the parquet directly.

## The claim that survives, and the one that does not

**Survives:** a lookahead can only *inflate* apparent edge, so every null established on
the defective clock stays null. Nothing that came back negative becomes positive.

**Does not survive:** "no graded London verdict rests on it" was true but **too narrow to
be the answer to the question asked**. 70 committed ledger rows across three families rest
on it. They change no verdict, they change the DSR denominator only by count and not by
variance, and none of them was ever selected on — but they are wrong numbers sitting in
the evidence base, and that is worth saying plainly rather than filing under a
technically-true summary.


---

## SUPERSESSION — the `dep_wall_above_d` row above is off by one (2026-08-07)

**Appended, not edited**, per the same discipline as the ledger correction: the published
table stays as published, and the corrected value sits beside it.

`scripts/london_depth.py::depth_at` selected the wall with `idxmax`, which resolves a
size tie by ROW POSITION. Row position is an artefact of how the long frame was
assembled, so the same book in a different order gave a different wall. The rev-3 lineage
(`origin/claude/agent-capture-london`) has carried the deterministic fix — largest size,
then NEAREST price, stable sort — since 2026-08-03; trunk did not. Found 2026-08-07 while
porting trunk's clock correction the other way, and a wholesale port would have regressed
it. Now fixed on trunk and pinned by `tests/test_depth_tiebreak.py`.

**Effect on the published table: one number.**

| column | published | corrected |
|---|---:|---:|
| `dep_wall_above_d` | 687 | **686** |
| every other row (`dep_imb` 746, `dep_thick` 721, `dep_sup_m_res` 718, `dep_resist` 711, `dep_support` 705, `dep_wall_below_d` 698, `dep_thick_d5m` 581) | — | **unchanged** |

**Effect of the tie-break fix alone**, against yesterday's committed matrix: only the two
wall-DISTANCE columns move — `dep_wall_above_d` 19 rows, `dep_wall_below_d` 26 rows, 45
in total (6.0%). Both wall-SIZE columns and all seven other `dep_*` columns are identical
on all 749 rows, which is the signature of a pure tie: same size, different price.

**No conclusion in this audit moves.** "Zero graded verdicts affected", the 70-of-447
exposure count, and LDN-CAN-01's 39 rows all carrying `effect = 0.0` are each independent
of 687 vs 686.

**Ledger: no new action.** LDN-CAN-01's 39 `dep_*` rows are already marked `status =
"stale"` under the 2026-08-06 ruling, which covers this change too. The 93 appended
`[v2 clock+sign]` rows are **not** affected: `scripts/london_obk_flow.py::load_depth`
computes `bid_wall = bsz.max(1) / median(bsz)` — a ratio of SIZES with no price
selection — so it never calls `depth_at` and has no tie-break exposure.

**The same defect is live in 14 other call sites**, unfixed and out of scope here:

| file | sites | note |
|---|---:|---|
| `src/desk/trade_manager.py` | 2 | **the LIVE desk path** |
| `scripts/nya_live_desk_run.py` | 3 | live/desk runs |
| `scripts/capture_desk_run.py` | 1 | |
| `src/canon/features.py` | 2 | the NY canon's own `depth_at` |
| `scripts/nya_lvl_depth.py` | 2 | NYA-LVL-01 |
| `scripts/depth_features.py` | 2 | |
| `scripts/leak_damage_canon.py` | 2 | |
| `scripts/depth_walls.py` | 1 | `np.nanargmax`, same class |

`src/desk/trade_manager.py` is the one worth a ruling: a live wall selection that depends
on frame row order is non-deterministic in the same way, and the fix is the four-line
patch already applied here.
