# PRE-REGISTRATION — LDN-OBK-01 / LDN-PO3-01 — the depth pass (canon variable map)

**Committed BEFORE any depth column is joined to the trade frame.** Closes gap 1 of
`research/findings/LDN-kill-vacated-under-511-512.md`, which vacated both kills for
running the weakest variable class at the weakest moment.

Required by §5.11.6 (canon variable map: every candidate's search must cover the canon
build's variable classes) and §5.12.10 (class priors — depth carried the entire canon
edge; flow at entry was a rounding error).

## Why this run exists

`research/findings/DISCOVERY-raw-triggers-to-canon.md` §2.2:

> *"Three variables out of sixteen produce a lift above 0.4R in any era: W, D, WALLSZ.
> **All three are DEPTH variables.**"*

London has **never been searched on depth.** The columns have existed since 27-Jul
(`scripts/london_depth.py`, 295 days of MBP-10) and the open-break work never touched
them. This is not a rescue attempt for two candidates; it is the missing variable class
for the whole London lane.

## The prediction I am NOT making, and why that matters

The canon's own §4.4:

> *"**Gold needs a wall AHEAD (D). Pre-market needs NO wall BEHIND (W).** Note the
> asymmetry — the same instrument, hours apart, wants opposite depth conditions. A
> framework that tests one global depth rule across a whole day would find nothing,
> because the two effects cancel."*

**So I explicitly do not predict which London wants.** Guessing would be inventing a
mechanism story to fit whichever result appeared. Both are declared open, and the honest
prior is only the class-level one: **depth is where the edge should be if it is
anywhere.** If neither W nor D survives, that is a genuine finding about the London open
and it is the second-strongest reason to close these candidates for good.

## Frozen checks — canon definitions, canon thresholds, nothing chosen here

Direction resolution first, per §4.2 — `behind`/`ahead` are relative to the trade, and
this differs by branch because the fade trades *against* the break:

```
long  = (branch == OBK) ? side>0 : side<0
behind_d = dep_wall_below_d if long else dep_wall_above_d
ahead_d  = dep_wall_above_d if long else dep_wall_below_d
ahead_sz = dep_wall_above_sz if long else dep_wall_below_sz
```

Eight single checks. Every threshold below is **inherited from the shipped canon**
(§4.3) or is a sign test at zero. None is fitted here.

| check | definition | source of threshold |
|---|---|---|
| `W` | `isna(behind_d)` — no wall behind | canon, as shipped |
| `D` | `notna(ahead_d)` — a wall ahead exists | canon, as shipped |
| `WALLSZ` | `D==1 and ahead_sz >= 7` | canon, as shipped |
| `WALLFAR` | `behind_d >= 2.75` | canon `wall_quality_cut` component |
| `IMBWITH` | book imbalance favours the trade direction | sign test at 0 |
| `SUPRES` | `dep_sup_m_res > 0` | sign test at 0 |
| `THICKHI` | `dep_thick` above the **discover-era** median | split frozen on 2025, applied to 2026 |
| `BUILD` | `dep_thick_d5m > 0` — book building, not pulling | sign test at 0 |

## Protocol — §5.12.2, followed literally

1. **Every check evaluated ALONE**, at its frozen threshold. No combinations in this
   run; a variable that only works in company is §5.12.4's back-door and needs a
   permutation null, which is a later step.
2. **NaN stands down.** `dep_thick` NaN ⇒ the whole depth family is unknown ⇒ the row is
   excluded from **both** arms. *"No data" ≠ "bad signal"* — and note `W` is a case where
   a **missing wall distance means the check PASSES**, while missing thickness means the
   row is dropped. Conflating those corrupts the trial and the live gate.
3. **`thin` = fewer than 15 rows on either side ⇒ no verdict.** Not a pass, not a fail.
4. **Survival = the same direction in EVERY era.** `lift_R` = mean R on the pass arm
   minus mean R on the fail arm, reported per era at both cost levels.
5. **Four kill classes (§5.12.3):** every-era-bad → kill; era-flip → kill or demote,
   never ship; too-thin → no verdict; holdout-negative → demote with stated reason.
6. **Lookahead audit (§5.11.7):** every check reads the book at or before the entry
   minute only. `depth_at` truncates at `ts <= minute` and `dep_thick_d5m` compares
   against `minute − 5`. Certified same-time computable.

## Applied to

Both default arms (`F1`, `A/S1`) plus `F2` and `B/S1` so the depth read is not
conditioned on one geometry. **Unconditioned trades** — no cuts, no filters, no
conditioning stack. Depth is being tested as a variable class, not as a rescue for a
particular spec.

## Spans and coverage limits, stated before use

- Depth: `data/reference/depth_london/`, **07:00–08:59 UTC**, 295 days from 2025-06-02.
  Under BST that is the full 08:00–10:00 London trigger window; under GMT it is the open
  hour only. **Macro-hour depth reads are seasonally incomplete and barred from being a
  gate**, exactly as in the L3 prereg.
- Discover 2025 (**H2 only** — depth starts June), validate 2026.
- **Holdout look: NO.** `data/reference/depth_london_2023_24/` is not read.

## What this run may conclude

- It may establish that a depth check survives every era, which would make the
  conditioned re-run of both candidates worth doing properly.
- It may establish that **none does**, which — combined with the flow null — would make
  a kill legal on the strongest possible grounds: the class that carries the canon's
  entire edge was tested at canon thresholds on this session and was not there.
- It may **not** promote anything. Frozen default specs are unchanged, and a surviving
  check becomes a declared arm in a later prereg, not a gate adopted here.

## Artifacts

`scripts/london_obk_depth.py`, `output/london_obk_depth.md`, trials to
`output/trial_ledger.parquet`, `research/FUNNEL.md` refreshed.

---

## CONSTRUCTION CORRECTION — the `BUILD` check is a BIASED measure (2026-08-06)

**Recorded after the fact, against a prereg that is otherwise unchanged.** This does not
respecify anything: the declared check stays as declared and any result already computed
under it stands as computed. It records what the check can and cannot mean.

`BUILD = dep_thick_d5m > 0`, read as *"book building, not pulling"*, is a **net depth
change across two snapshots five minutes apart**. The London depth extraction keeps one
row per minute out of a median **23,654 book events** (p75 33,606), so this differences
across roughly **118,000 unobserved additions, cancellations and executions** and retains
only the residual.

Cont-Kukanov-Stoikov's identity is the reason that residual cannot carry the intended
meaning: **a market sell and a cancelled buy of the same size have identical effect on
the queue.** A net change therefore cannot separate

- book building (the declared reading), from
- cancellations that happened to net positive, from
- executions on the opposite side,

and it can carry the opposite sign to true integrated order flow. Under the
`orderflow-construction` taxonomy this is the **BIASED** class -- computable, stable,
reproducible, and measuring something other than its name. It is not NOT-CONSTRUCTIBLE
and it is not merely noisy.

**Consequences, stated rather than fixed:**

- `dep_thick_d5m` is now emitted as `dep_thick_d5m_BIASED` with the legacy name retained
  as an alias (`scripts/london_depth.py`), so the caveat travels with the column.
- `output/london_obk_depth.parquet` contains a `BUILD` column built from it. Any reading
  of that column must carry this note.
- `src/canon/features.py` computes the identical quantity on the NY side. Stated as a
  fact; not analysed here, which is London-scoped.

**What would make it VALID:** event-level MBP-10 for the window -- the same Databento
schema, unsampled. A purchase, not a code change. At event resolution the quantity CKS
define is directly computable and the identity above stops being a confound.

**The sound alternative at this resolution is a book LEVEL, not a book DIFFERENCE.**
Levels survive coarse sampling; interval differences do not degrade, they become a
different quantity. `src/engine/book.py` provides the level forms (multi-level depth
imbalance, book pressure, weighted mid) with construction validation in
`scripts/book_feature_validation.py`.
