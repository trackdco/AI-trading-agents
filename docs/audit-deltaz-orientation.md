# AUDIT — `delta_z` / `dep_imbalance` ORIENTATION DEFECT

2026-08-08. Independent audit of the defect reported in `scripts/conviction_lib.py`'s
header. Population for the recomputation: `output/htf_ma_census/race_wide.parquet`,
the episode-M1 race census (3,153 fights / 290 days) that `conviction_lib.py` loads —
this is a **different, newer population** than the one underlying BR-19/26/62 (the
original M-TABLE / LTF-recensus / open-space books). That distinction matters for the
"does this rescue CONCORD" section below and is flagged there again. No parquet was
modified. Nothing was committed.

---

## 1. INDEPENDENT CONFIRMATION OF THE DEFECT

**Confirmed.** Direct inspection of both files, independent of the report that
prompted this audit:

**`scripts/htf_ma_mtable.py::flow_features`, line 77:**
```python
f["delta_z"] = (dsum - dmu) / dstd if dstd > 0 else np.nan
```
`dsum` is the raw signed sum of bar delta over the decision-bar window; `dmu`/`dstd`
are the mean/std of the last 20 completed same-timeframe bars' delta. `direction`
(the function's own 4th argument, in scope at this line) is never referenced. Contrast
with the other eleven features in the same function, which all **are** oriented:
`flowconf` (line 68, `np.sign(dsum) == direction`), `closeloc` (lines 52-54, branches
on `direction > 0`), and `cvd_slope30` (line 92, `... * direction` — explicitly
multiplied by direction). `delta_z` is the one feature in the twelve that computes a
signed quantity and never folds direction into it.

**`scripts/htf_ltf_flow.py::concord`, lines 46-58** (the zero-free-parameter count
whose docstring says "identical construction to BR-19's, so the numbers are
comparable"):
```python
for c in ("cvd_slope30", "delta_z"):
    a[c] = (X[c] > 0).astype(float)
```
Both columns are scored identically — `> 0` counts as agreement — but only
`cvd_slope30` arrives at this line already oriented (it was multiplied by direction
upstream). `delta_z` arrives raw. So `delta_z > 0` scores **buying pressure** as
agreement regardless of whether the trade is long or short. For a short trade, that is
scoring the opposing side's pressure as confirmation. The identical construction (same
bug, same code shape) recurs verbatim in `scripts/htf_ma_flow_depth_run.py` (lines
279-284, the original B1 CONCORDANCE behind BR-19) and in
`scripts/htf_ma_session_books.py::concord` (lines 162-172).

**Measured magnitude**, recomputed independently on the audit population:
```
direction = +1 (long):   mean delta_z = +1.217035
direction = -1 (short):  mean delta_z = -1.170097
```
This reproduces the reported **+1.217 / −1.170** to three decimal places. The defect
is real, exactly as characterized, and not overstated.

**`dep_imbalance`** — `scripts/htf_ma_flow_depth_run.py::depth_at`, line 103:
`"dep_imbalance": (bd - ad) / tot` — also raw, never multiplied by `direction` (`d` is
in scope two lines below, used for `support_minus_resist`, and skipped for
`dep_imbalance`). Confirmed as the same class of defect. Measured magnitude is far
smaller (see §2) — the "milder" characterization is also independently confirmed, not
just asserted.

One clarification for precision: `delta_z` and `dep_imbalance` were **not** part of
the same construct historically. The 12-feature CONCORD/CONCORDANCE behind BR-19/26/62
is flow-only (`FLOW_NAMES`); `dep_imbalance` is one of six *depth* features tested
separately (BR-20/21, wall-quality and bottom-quartile depth cuts), never folded into
an unweighted agreement count. Both are defective; they never compounded inside one
statistic.

---

## 2. SIGNAL-LEVEL IMPACT

Agreement rate of `s_deltaz` (fixed, oriented by direction) vs `s_deltaz_raw` (old,
`delta_z > 0`), on the audit population (n=3,153; longs 1,587 / shorts 1,566):

| | overall | LONG | SHORT |
|---|---|---|---|
| **fixed** agree % | 85.1% | 84.1% | 86.2% |
| **raw/old** agree % | 49.1% | 84.1% | **13.7%** |
| row-level match rate | 50.4% | **100.0%** | **0.06%** |

This is exactly the signature a correctly-oriented signal should have, and exactly the
signature a scrambled one should not: on longs the two are **mathematically
identical** (multiplying by direction=+1 changes nothing — 100.0% row match), and on
shorts they are **almost perfectly opposite** (0.06% match — direction=-1 flips the
sign on all but a handful of exact-zero rows). The old raw signal was agreeing with
short trades 13.7% of the time — barely more than "declared bad" — while the same
underlying data, oriented, agrees 86.2% of the time, essentially matching the long
side. The raw signal was not a weaker version of the real one; it was reading the
wrong side of the tape on short trades specifically.

`dep_imbalance`, same test (n avail = 2,521, ~80% coverage, matching the docstring's
"depth exists on ~80% of fights"):

| | overall | LONG | SHORT |
|---|---|---|---|
| **fixed** agree % | 48.5% | 42.3% | 55.0% |
| **raw/old** agree % | 42.3% | 42.3% | 42.4% |

A 13-point swing on shorts (42.4% → 55.0%) vs `delta_z`'s 72-point swing (13.7% →
86.2%). Direction-conditional means confirm it: `delta_z` is polarized (+1.22 / −1.17,
essentially mirror images); `dep_imbalance` is small and same-signed both directions
(−0.022 long, −0.019 short). "Same defect, milder" is confirmed quantitatively, not
just qualitatively.

---

## 3. COUNT-LEVEL IMPACT

Two comparisons, kept separate because the two named columns differ by more than
orientation.

**(a) Isolated effect of the fix alone** — `cc_flow` (12 features, FIXED `s_deltaz`)
vs `cc_flow_olddefect` (12 features, RAW `s_deltaz_raw`) — the only two Law-2-flagged
features (`closeloc`, `rangex`) present in both, so this isolates the orientation fix
with nothing else changing:

- 50.4% of fights: **no change** in level.
- 49.6%: move by **exactly ±1** level (never more — mathematically bounded, since only
  one binary component of twelve differs).
- Direction split: LONG mean count is **identical**, 6.895 both ways (expected — fixed
  = raw on longs). SHORT mean rises 6.320 → 7.045 (+0.72 of a level) under the fix.
- Per session×mechanism, 41–56% of fights move a level, always entirely in the "level
  rises" direction on the short side, never ≥2 levels. Consistent across all nine
  cells.

**(b) The two columns named in the task** — `cc_flow_clean` (fixed, 10 features, the
two Law-2-contaminated features **excluded**) vs `cc_flow_olddefect` (old, 12
features, Law-2 features **included**):

- 78.8% of fights move at least one level; 30.2% move by ≥2; mean count is *lower*
  under the "clean" column by ~1.0–1.2 levels in every session×mechanism cell.

This larger, ≥2-level-capable shift is **not** attributable to the orientation fix —
it is arithmetically impossible for a single binary swap to move a 0–10 sum by 2+
levels. It is the two-feature drop (`closeloc`, `rangex`, BR-43's known mechanical
risk-coupling) doing almost all of the work. Reported as instructed, but read
alongside (a): the fix by itself is a ≤1-level, symmetric-on-longs, short-side-biased
nudge; the larger apparent shift in (b) is mostly a different, already-known and
correctly-flagged issue (Law 2), not this defect.

---

## 4. OUTCOME-LEVEL IMPACT (permutation-calibrated)

All tests use `calibrate(fn, B, n_perm=10)` per instruction, and day-clustered
bootstrap CIs (`dboot_mean`-style, 2000 draws, seed 20260807) for point estimates.
BR-97's caution is taken seriously throughout: a result is only called real if it sits
outside the permutation band, not merely if a naive CI excludes zero.

**Whole-book Spearman(count, out), isolated 12-feature comparison:**

| | real ρ | permutation null (mean, range over 10 draws) |
|---|---|---|
| `cc_flow` (FIXED-12) | 0.1493 | 0.039 [0.020, 0.069] |
| `cc_flow_olddefect` (OLD-12) | 0.1424 | 0.042 [0.024, 0.066] |

Both sit well above their own null bands (~3-4x the null mean) — but they sit there
**almost identically**, fixed vs old (Δρ = +0.007, smaller than the gap between the two
permutation-null means themselves). The whole-book "signal" in CONCORD-style counts is
real relative to noise, but it is not coming from `delta_z`'s orientation. Where is it
coming from: `closeloc` alone has ρ=0.150 with outcome, `rangex` alone ρ=0.298 — both
Law-2-flagged as mechanically coupled to the R-denominator (BR-43) — i.e. already known
to need exclusion for reasons unrelated to this defect. (This is also why
`cc_flow_clean`, fixed but 10-feature, reads *lower* than `cc_flow_olddefect`, 12-feature
raw, at the whole-book level: ρ=0.077 vs 0.142 — the gap is the two excluded
Law-2 features, not the fix. Isolating properly, as above, removes that confound.)

**Per session×mechanism, top-tercile-vs-bottom-tercile EV contrast** (day-clustered
bootstrap CI on the isolated `cc_flow` vs `cc_flow_olddefect` pair, 9 cells × 2
orientations = 18 tests):

| session | mech | count | EV top−bottom | 95% CI | excludes 0? |
|---|---|---|---|---|---|
| NY_PRE | M2 | OLD | −0.662R | [−1.316, −0.116] | **yes** |
| NY_PRE | M2 | FIXED | −0.551R | [−1.247, +0.031] | no |
| *(other 16 of 18 cells)* | | | | | no |

**17 of 18 tests show a CI spanning zero regardless of orientation** — no reliable
monotone conviction→outcome relationship survives day-clustering under either
construction, consistent with the programme's already-established null (BR-94, BR-97).
The single exception is instructive: under the **old, defective** orientation, NY_PRE
M2 shows a CI-excluding-zero result — but it is **inverted** (more raw "concordance" →
*worse* EV, the opposite of what a real conviction signal should do). Under the fix,
the same contrast weakens (−0.551 vs −0.662) and the CI now spans zero. One "clear" out
of 18 comparisons at a 95% bar is within the ~5% false-clear rate BR-97 already
calibrated — and the fix's only visible effect on outcome-level results in this audit
is to **make a spurious, backwards-signed "clear" go away**, not to create or rescue a
positive one. A secondary, orientation-*insensitive* win%-only split (NY_AM M1, ~11-15pp
win-rate gap, present under both FIXED and OLD, EV flat both ways) also appears — a
Law-3-style hit-rate/expectancy divergence unrelated to this defect, unchanged by the
fix, mentioned for completeness only.

---

## 5. BLAST RADIUS — every consumer found

`grep -rn "delta_z\|dep_imbalance" scripts/ src/` plus manual trace of every import.

**Directly affected (still contain the unpatched raw construction):**

| file | role | fed base rate(s) | status |
|---|---|---|---|
| `scripts/htf_ma_mtable.py` | origin of raw `delta_z` (`flow_features`) | — (raw feature, correctly a raw feature; the bug is downstream in the scoring, not here) | unpatched, but this file need not change — see note below |
| `scripts/htf_ltf_flow.py` | `concord()` — the LTF re-measure of CONCORD | BR-31 | **unpatched** |
| `scripts/htf_ma_flow_depth_run.py` | original B1 CONCORDANCE; `depth_at` (raw `dep_imbalance`) | **BR-19**, BR-20, BR-21 | **unpatched** |
| `scripts/htf_ma_session_books.py` | own `concord()` duplicate | **BR-26** (via FINDINGS-H) | **unpatched** |
| `scripts/htf_ma_cut_study.py` | imports `concord`; also tests raw `delta_z` as a `CONT_LOW_BAD` Q1-cut candidate | VERDICT-cut-study.md | **unpatched** — see explained artifact below |
| `scripts/htf_ma_close_locus_set.py` | imports `concord`, builds a CONCORD column for an internal Bonferroni×15 restatement (§5b) | none found — script's own docstring says the pass was "HALTED because the population is still moving"; not cited by any BASE-RATES entry | **unpatched**, no traceable published conclusion depends on it |
| `scripts/concord_open_space.py` | imports `concord` directly from `htf_ltf_flow` | **BR-62, BR-63, BR-64, BR-65** (FINDINGS-concord-x-open-space.md) | **unpatched** — these published numbers were computed under the old orientation and have not been rerun |
| `scripts/race_flow_diag.py` | per-column (not stacked) winner/loser diagnostic; raw `delta_z`/`dep_imbalance` among 18 tested features, median-split, unoriented | **BR-94** (FINDINGS-race-diagnosis Parts 3-4) | unpatched, but see below — does not change BR-94's verdict |
| `scripts/phase1_diagnose.py` | same-style per-column diagnostic (FLOW12/DEPTH6) | none found — not cited by any FINDINGS doc; superseded in practice by `race_diagnose.py` + `race_flow_diag.py`, which produced the actually-published Parts 1-4 | unpatched, appears to be dead/unused code |
| `scripts/conviction_lib.py` | **the fix** — new, parallel, oriented construction | this audit only | fixed |

**Confirmed unaffected** (checked directly, no dependency found):

- `scripts/htf_room_gate.py` — explicitly declares "NO CONCORD. NO FLOW FEATURES." by
  design (room-to-run family: BR-32–BR-35 and downstream). Untouched.
- `scripts/fixed_target.py` — "CONCORD-style splits" is a descriptive analogy for a
  sim-vs-live divergence pattern (BR-48), not an actual `delta_z`/`concord` dependency.
  Untouched.
- `scripts/phase2_precondition.py` — one rhetorical mention of "CONCORD" in a
  docstring; its actual output (FINDINGS-phase1-diagnosis.md) is about `closeloc`
  mechanical screening, unrelated to `delta_z`/`dep_imbalance`. Untouched.
- All base rates not built from any of the files above (BR-1–18, 20-arm-cuts aside,
  22–25, 27–30, 32–48 except noted, 67–96 except BR-94, 97) — no dependency on
  `delta_z`/`dep_imbalance` found; **explicitly unaffected**.

**An explained (not newly-found) artifact:** `VERDICT-cut-study.md` records, for
`delta_z` as a `CONT_LOW_BAD` candidate: *"declared low=bad direction INVERTED on both
arms in Half 1 (the extreme-delta bin is where the money is). Recorded miss; no
flip."* That is exactly what an unoriented feature produces under a naive "low is bad"
univariate cut pooled across both trade directions: strong flow shows up at *both*
raw tails (very negative on shorts, very positive on longs), while only the bottom
quartile was tested as "bad." The cut study's own process caught this correctly — it
was recorded as a miss and never adopted, never flipped. **Nothing about the study's
one adopted, confirmed cut (S1, `flowconf`-based) is touched** — `flowconf` was already
correctly oriented (`np.sign(dsum) == direction`) throughout.

**Important operational note:** as of this audit, only `conviction_lib.py` contains
the fix. The functions that actually produced BR-19, BR-26, BR-62, BR-63, BR-64, BR-65
(`concord()` in `htf_ltf_flow.py` / `htf_ma_flow_depth_run.py` / `htf_ma_session_books.py`)
are **still unpatched in the working tree**. If those historical numbers are to be
corrected rather than superseded, the same `* direction` fix needs to be applied there
and those scripts rerun on their own original populations — that has not happened.
§6 addresses whether that rerun would be expected to change anything.

---

## 6. DOES THIS RESCUE CONCORD?

**No, and the arithmetic says why.**

CONCORD/CONCORDANCE, as used in BR-19/26/62, is an **unweighted sum of 12 binary flow
features**. `delta_z` is 1 of those 12 (1/12 ≈ 8.3% nominal weight). Two others
(`closeloc`, `rangex`) are already known, independent of this defect, to be
mechanically coupled to the outcome's own denominator (BR-43) — those two alone carry
more measured association with outcome (ρ=0.150, ρ=0.298) than fixing `delta_z` moves
the aggregate count's association at all (Δρ=+0.007, on the audit population, smaller
than the permutation-to-permutation noise). The other 9 of 12 features were already
correctly oriented and untouched by this defect.

Directly testing the counterfactual (§4): on the audit population, using the same
12-feature construction with only `delta_z`'s orientation swapped, the whole-book
rank-correlation with outcome is statistically indistinguishable fixed vs old (0.149 vs
0.142), and the per-cell top-vs-bottom EV contrast is null under **both** orientations
in 8 of 9 session×mechanism cells. The one cell where orientation changes the formal
result, fixing it makes a spurious inverse "clear" disappear — it does not produce a
new positive one anywhere.

So: CONCORD's three refutations were not built on a foundation where this one
component could plausibly have flipped the verdict. BR-19 failed on multiple
independent grounds beyond any single feature (worst bin still profitable, max
whole-book gate lift +0.046R below the +0.05R bar, half-1 survivors dying on half-2).
BR-62 failed because the trades CONCORD *discarded* were shown to be just as good as
the ones it kept (`open only (CC<7)` +1.562/+1.179, matching or beating the conjunction)
— a finding about what the *other* 11 components plus the open-space interaction do,
not about `delta_z`'s sign. Nothing in this audit's recomputation moves that.

**Caveat, stated plainly:** this is a structurally-equivalent recomputation on a
different (newer, larger) population, not a literal rerun of BR-19/26/62's original
frames with the actual defect line patched — those scripts remain unpatched (§5). If
someone wants certainty rather than a strong analog, the honest next step is: apply the
same `* direction` fix to `concord()` in `htf_ltf_flow.py` / `htf_ma_flow_depth_run.py`
/ `htf_ma_session_books.py`, rerun BR-19/26/62 on their own original frames, and diff
the published numbers directly. Based on everything measured here, that rerun is
expected to reproduce this audit's finding — real defect, small blast radius,
conclusions unchanged — but it has not been executed, and this report does not claim it
has.

---

## SUMMARY TABLE

| Question | Answer |
|---|---|
| Is the defect real? | Yes, confirmed independently by direct code inspection, not on the reporter's word. |
| Blast radius (code) | 9 scripts touch raw `delta_z`/`dep_imbalance`; 3 unrelated scripts checked and cleared. |
| Blast radius (published base rates) | BR-19, BR-26, BR-31, BR-62/63/64/65, BR-20/21 (dep_imbalance), BR-94 (both features, already null there) touch the defect. All other cited base rates (BR-1–18, 22–25, 27–30, 32–48 except BR-43 itself, 67–97) do not. |
| Does fixing it change any tested outcome relationship? | Only one of 18 outcome tests changes formal significance, and the fix *removes* a spurious backwards-signed result rather than creating a positive one. |
| Does it rescue CONCORD? | No. `delta_z` is 1 of 12 components; the whole-book association with outcome is essentially unchanged by the fix (Δρ≈+0.007) and dominated instead by two already-flagged Law-2-contaminated features. CONCORD's refutations rested on multiple independent grounds beyond this one component. |
| Anything previously concluded need revising? | No adopted or published conclusion changes. `VERDICT-cut-study.md`'s one documented `delta_z` anomaly is now explained (not overturned — it was already correctly treated as a non-adopted miss). BR-19/26/62/63/64/65's exact published numbers were computed by still-unpatched code and have not been rerun; a rerun is recommended for completeness but is not expected, on this evidence, to change their verdicts. |
