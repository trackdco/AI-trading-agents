# FINDING — the depth family peeks up to 60s into the future (2026-08-05)

**Status: BLOCKING. The canon must not arm until this is fixed and the book re-validated.**
Found by ANGUS. Confirmed with numbers here. Reproduce with
`python -m scripts.audit_depth_lookahead`.

---

## 1. The bug

The depth archive stores, for each minute M, **the last book state in M**
(`data/reference/depth_2023_24/README.md`: *"ts | minute timestamp … (last book state in
that minute)"*; timestamps are minute-aligned, seconds always 0).

`src/canon/features.py::depth_at` selects the snapshot with `dep[dep.ts <= minute]` and
takes the max. So a fill in minute M is scored on the book as it looked at ~M:59.

Every `fill_ts` in the scored population is **minute-resolution** (seconds = 0), so the
fill could have occurred anywhere inside M. Using the end-of-M book therefore grants the
entry gates **up to 60 seconds of information that did not exist at the decision.**

**The live path does not do this** — `src/canon/ingestor.py::feature_row`:

```python
book = pd.DataFrame(self.book.long_form())
book["ts"] = fill                        # current snapshot is as-of the fill
f.update(depth_at(book, fill, entry, direction))
```

Live stamps the in-memory book as-of the fill instant. It is honest and it physically
cannot be otherwise.

**Note the asymmetry, which shows the bug is an oversight and not a convention:** the tape
and VWAP families in the same function truncate with STRICT `<` (`tape.index < fill`,
`b.mi < fill`). Only the depth family uses `<=` against an end-of-minute snapshot.

## 2. What it is worth — measured

`scripts/audit_depth_lookahead.py` re-scores every L3 candidate (risk band 7–60pt) two
ways and re-runs the exact `l3_check_trial.lift` table:

- **SHIP** = `ts <= M` (the shipped behaviour)
- **HONEST** = last book state in **M−1**, i.e. the newest snapshot that was complete
  before minute M began. With minute-resolution fills this is the only causally
  defensible backtest convention; the SHIP figure is only attainable if *every* fill
  happened at :59 of its minute.

Sanity: the lag-0 recompute reproduces the shipped W/D/WALLSZ bits **100.00%** on both
spans, so the harness is faithful.

| check | era | SHIP lift_R | HONEST lift_R | |
|---|---|---|---|---|
| **W** (pre) | fit 2025 | +0.488 | **−0.126** | sign flip |
| | fit 2026 | +1.272 | +0.384 | |
| | holdout | +0.836 | **+0.036** | ~zero |
| **D** (gold) | fit 2025 | +0.875 | +0.472 | |
| | fit 2026 | +0.810 | +0.374 | |
| | holdout | +0.806 | **+0.136** | |
| **WALLSZ** (gold) | fit 2025 | +0.667 | +0.110 | |
| | fit 2026 | +0.495 | **−0.072** | sign flip |
| | holdout | +0.749 | **+0.169** | |

Bit instability across that single minute:

| check | fit rows flipped | holdout rows flipped |
|---|---|---|
| W | 1,986 / 5,229 (**37.98%**) | 1,025 / 2,700 (**37.96%**) |
| D | 1,282 / 5,229 (24.52%) | 600 / 2,700 (22.22%) |
| WALLSZ | 1,570 / 5,338 (29.41%) | 688 / 2,747 (25.05%) |

## 3. Verdict against our own survival rule

The rule (`docs/HANDOFF-london-rebuild.md` §3): *a check survives only if it points the
same way in 2025, 2026 AND holdout.*

- **W — FAILS.** Sign-flips in 2025 (−0.126), ~zero on holdout (+0.036).
- **WALLSZ — FAILS.** Sign-flips in 2026 (−0.072).
- **D — survives, at roughly half strength.** Its honest holdout lift (+0.136) sits in the
  same band as checks that were killed (PAQ −0.110, VWAPD −0.201, LONSLOPE −0.117).

**The majority of the measured entry edge was the peek.** D remains a real signal; W and
WALLSZ as measured are not.

## 4. Scope — what is and is not affected

**NOT affected (no depth dependency):**
- **L0 census** — 19,137 fit / 10,397 holdout triggers
- **L1 fills** — the limit walk
- **L2 outcomes** — engine exits, MFE/MAE walk, the time-segment/press-state study, the
  whole winner/loser autopsy
- The exit engine, rr_floor work, profit-taking arms, the agent management layer's
  in-trade findings

**Affected — must be recomputed:**
- **L3 depth features** → `l3_features_*`, `l3_scored_*`
- the **check trial** (all 16 checks, since the population they are judged on changes)
- **scores** (`2D + …`, `2W + …`), **tiers**, the **aikido wall-quality cut**
- **`aikido_*.parquet`**, the CR overlay, `funded_book` references, and every downstream
  funded number
- `src/canon/scorer_ny.py` conformance pins and `tests/test_canon_scorer_ny.py`
  expectations

**The code fix is small** — the snapshot selection must exclude the fill's own minute
(and the live path must keep stamping as-of the fill, which it already does). The
re-validation is the work, not the patch.

## 5. Why no existing gate caught it

**Depth parity (R10b) could not have caught this.** That gate compared the live feed
against the archive **at the same minute convention** — it was validating *normalization*
(scale, alignment, level aggregation), not *causality*. Both sides of that comparison
carried the same end-of-minute assumption, so they agreed.

The conformance twin could not catch it either: `scorer_ny.py` re-derives the gates from
the same feature columns, so it faithfully reproduces a contaminated input.

**The framework lesson:** parity gates prove two paths agree. They say nothing about
whether the agreed-upon quantity was knowable at decision time. A validation framework
needs a distinct **causality audit** per feature family: *what does this value know, and
when did it know it?* — asked against the raw artifact's own timestamp semantics, not
against another implementation.

## 6. Open ruling for ANGUS

The sealed 2023/24 holdout has now been looked at through contaminated features. Whether
an honest re-validation counts as spending a fresh look, or as the first honest look at a
quantity the previous looks never actually measured, is a ledger judgment and is
explicitly left open here rather than assumed.
