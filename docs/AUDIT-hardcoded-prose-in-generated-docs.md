# AUDIT — prose that cannot regenerate with its own table

**2026-08-06.** Swept every doc-generating script in `scripts/` and `src/` with an AST
pass: string constants reaching a markdown emitter (`L.append`, `L +=`, `lines.append`)
that contain a **result-shaped** number — a signed decimal, an `R` value, a `PF`/`WR`
reading, or an `n=` count. A number inside an f-string expression regenerates; a number
inside a plain string literal cannot, and will eventually contradict the table above it
while looking authoritative.

**Why this sweep exists.** `scripts/london_obk_flow.py` regenerated its scorecard table on
corrected inputs while the paragraph beneath it stayed frozen, so the document asserted
*"`delta_entry` high in 2026 is the strongest cell in the whole pass (+0.448R, PF 1.56)"*
about a cell that had become **−0.099R, PF 0.85** — and did so directly under a table
showing the corrected value.

**Result: 20 hardcoded result-shaped strings across 11 files. One was the same defect.**

## The finding

| file | verdict |
|---|---|
| **`scripts/l1_london_card.py`** L127–133 | **SAME DEFECT — FIXED.** Hardcoded *"The raw substrate is **69.6% B2** … After the floor it is **55.8% B**"* sat immediately below a computed table emitting exactly those shares per pattern, plus *"5-minute triggers clear the floor 26.0% of the time, 1-minute triggers 8.4%"* and two median stop distances. All five now read from the data, and the paragraph picks the largest share rather than naming a pattern that may no longer be largest |

## Not defects, and why

| file | string | why it is legitimate |
|---|---|---|
| `scripts/canon_depth_recheck.py` L147–148 | "+0.5 to +1.3R" | **Citation** of `VALIDATION-PROCESS` §5.12.10, explicitly attributed. Quoting another document's published figure is not a self-inconsistency risk — it is a reference, and it should not silently track this script's own recomputation |
| `scripts/london_obk_depth.py` L229 | "+0.5 to +1.3R there" | Same citation, same reasoning |
| `scripts/nya_lvl_rebuild.py` L176 | "_Old (void) figures were PF 1.07 base / 0.99 strict._" | **Deliberate historical record** of superseded numbers. Making this regenerate would erase the thing it exists to preserve — the same principle as `superseded_by` in the ledger |
| `scripts/london_obk_l1.py` L305 | "A 2R trade needs 33.3% to break even" | **Arithmetic identity**, 1/(1+2). Not a measurement |
| `scripts/london_obk_cond.py` L143 | "Buckets under n=15 are suppressed" | **Declared threshold**, not a result |
| `scripts/nya_ib50_diagnosis.py` L89–90 | "cut t+5 if MAE<=-0.5R" | Rule definitions |
| `scripts/nya_lvl_depth.py` ×5 | "WR 1.0R", "1.5R", table headers | **Column labels** naming the R-multiple each column reports |
| `scripts/capture_desk_run.py`, `scripts/nya_live_desk_run.py`, `src/live/agent_desk.py` | "trades that reached +0.5R" | **Population definition** for the metric that follows |

## Prose documents (not generated) carrying stale numbers

Verdict cards and research notes are written by hand and cannot regenerate at all, so the
question for them is whether their numbers still match the artifacts.

| document | status |
|---|---|
| **`research/candidates/london-po3-ifvg.md`** | **STALE — §0 CORRECTION appended.** Lines 304–319 carry the L3 flow tercile table and the `delta_entry` sentence. Both superseded; the kill stands but its stated reason was wrong — under the corrected sign 2025 H2 points *with* the prediction, so the kill is the era-flip, not a wrong-way 2025 |
| `output/london_obk_flow.md` | **REGENERATED**, and its prose now reads from data |
| `output/london_obk_depth.md`, `output/london_obk_cond.md` | **Generated artifacts, not re-run here.** `london_obk_depth` consumes the `dep_*` columns and its `BUILD` arm is the BIASED `dep_thick_d5m`, so it is stale in the same way. Re-running is a further step |
| `research/FUNNEL.md` L102/L362, `research/candidates/london-nq-open-break.md` L312, `research/findings/LDN-kill-vacated-under-511-512.md` L109 | **Not stale.** These match `PF 1.56` by coincidence — a candles-era check, a PM-window split, and the OBK candidate's own PF. Different passes, unaffected |
| The six graded London verdicts (SWP/TRAP/VWAP/VT/DEF/FLOW) + ATC L1 | **Not stale.** None consumes depth or the L3 flow pass — `docs/AUDIT-depth-lookahead-exposure-by-family.md` |

## The general rule this suggests

A generated document should not contain a result number that is not read from the data it
was generated from. Three exceptions earn their hardcoding, and all three are
distinguishable by intent rather than by form: **citations** of another document's
published figure, **historical records** of superseded values, and **definitions**
(thresholds, identities, labels, population criteria). Everything else is a claim about
the run, and a claim about the run belongs in an f-string.
