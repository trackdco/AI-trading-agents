# SEALED RUN RUNBOOK — London holdout

**Status: PREPARED, NOT EXECUTED. Written 2026-07-31 on `claude/sealed-run-prep`, before
any sealed outcome exists. Nothing in this document was informed by sealed-span results,
because none have been computed.**

This runbook exists so that when the two signatures land, the sealed run executes with
**zero decisions remaining**. Whoever runs it does not choose what to report, does not
choose the comparison, and does not choose how a weak result is interpreted. All of that
is fixed below, in advance.

---

## 0. Preconditions — every one must hold before the command is typed

| # | precondition | verified 2026-07-31 |
|---|---|---|
| 1 | `docs/LONDON-HOLDOUT-REPORT.md` does not exist | ✓ absent |
| 2 | Brake re-confirms prereg rev-2a draft changes (§2/§3/§4) | ☐ PENDING |
| 3 | ANGUS signs ONE config: rev 2a **or** rev 3 (`docs/LONDON-REV3-BUNDLE.md` §6) | ☐ PENDING |
| 4 | ANGUS rules the three engine questions (bundle §3: twins, day-stop units, far-target) | ☐ PENDING |
| 5 | ANGUS yes/no on the pre-run era measurement (§4 below) | ☐ PENDING |
| 6 | Sealed L0→L3 artifacts built for `--span holdout` (+ `--mgmt V1` arm if rev 3) | ☐ not built |
| 7 | Fit rehearsal PASSES for the signed config on the same commit | ✓ both pass |

**Precondition 6 is deliberately unmet.** No sealed derived artifact exists in the repo
(`l0/l1/l2/l3_*_holdout*.parquet` — all absent, verified). Building them is a separate,
deliberate ~2h act that cannot happen by accident.

## 1. The command

Build the sealed artifacts first (mechanical, same code the fit rebuild verified):

```bash
.venv/bin/python -m scripts.build_l0_triggers_london  --span holdout
.venv/bin/python -m scripts.build_l1_fills_london     --span holdout
.venv/bin/python -m scripts.build_l2_outcomes_london  --span holdout --procs 3
# rev 3 ONLY — the V1 management arm:
.venv/bin/python -m scripts.build_l2_outcomes_london  --span holdout --procs 3 --mgmt V1
```

Then the single reporting command. **Fill in exactly ONE config, and the signature token
verbatim as given by Angus:**

```bash
.venv/bin/python -m scripts.london_holdout_report \
    --span holdout \
    --config ______________________   # rev2a | rev3 — the SIGNED one, no other
    --authorized-by "______________________________________"
```

<br>

**Signature token, transcribed from Angus's sign-off (name, date):**

```
________________________________________________________________
```

<br>

Run it **once**. The runner writes `docs/LONDON-HOLDOUT-REPORT.md` and refuses to run
again while that file exists (demonstrated, not assumed — see §7).

## 2. The exact figures the report will contain — decided now

Fixed by `scripts/london_holdout_report.py` and prereg §2. Whoever runs it gets exactly
this list; nothing may be added after seeing numbers, and nothing may be omitted.

**Items 1–8 (the book):** trades / days with a take · net P&L · win rate · mean R ·
maxDD (chronological, **trade-level** — the prereg reference convention, not day-level) ·
months green / total · worst month · trades per week. Plus the per-era table.

**Item 9:** W/FAR lift — mean R of `either` vs `neither` on floor-passing candidates,
pooled and per era, with n on each side.

**Item 10 / S2 (DESCRIPTIVE, no inference):** the `either` cell split, both-W+FAR vs
exactly-one. Prereg §4: **no decision may be taken on this number in this run** — doing
so retroactively converts the family to 3 tests.

**The two gated tests**, two-sided one-sample Student-t, Šidák α = 0.0253, PASS = mean R
> 0 AND p ≤ α:
- **PRIMARY** — book mean R > 0
- **S1** — sub-9.5pt wall-passing band mean R > 0 (**reported, not acted on**; the floor
  does not move on this result — standing ANGUS ruling)

**Bucket profile (DESCRIPTIVE):** half-hour fill-time buckets. Declared prior: the late
window was the weakest bucket on fit.

**Not in this run, at all:** sizing ladders, conviction tiers, funded dollars, Monte
Carlo, agent-exit work, V9. Those are post-holdout or separate-branch questions.

## 3. The comparison, fixed in advance

The holdout is read against a **declared prior**, not a remembered one. Three fit
figures exist and are easy to conflate — the signed config selects exactly one:

| fit reference | mean R | note |
|---|---|---|
| rev 2a book (187 trades) | **+0.513** | if rev 2a is signed |
| rev 3 plain 09:45 book (167 trades) | **+0.581** | window cut only, NO veto/serial/V1 |
| rev 3 full stack (130 trades) | **+0.758** | if rev 3 is signed — veto + serial + V1 |

**DECLARED FORWARD EXPECTATION: mean R ≈ +0.48, under EITHER config**
(`docs/LONDON-REV3-BUNDLE.md` §1). This does **not** ratchet up with the rev-3
improvements: the window cut failed its own guard (p=0.076) and a guard-failed
improvement may not inherit into the prior.

**Reading resolution, from the prereg's power arithmetic — binding:**

> **A near-miss on +0.48 is not decay. A sign flip is.**

Projected n ≈ 59 (rev 3) / ≈ 84 (rev 2a). SE on holdout mean R ≈ ±0.17–0.19. **This run
can distinguish "the edge is real" from "the edge is absent". It cannot resolve +0.48
from +0.30, and it cannot finely grade subsets.** Read it at that resolution and no
finer.

## 4. ERA-GAP DECLARATION — written before results exist

**The problem, stated plainly.** The sealed span is **2023-07 .. 2024-10**. The fit span
is **2025-06 .. 2026-07**. There is roughly a one-year gap and no overlap. If the result
is weak, two explanations are confounded:

- **(A) EDGE DECAY / OVERFIT** — the edge was never real, or has died.
- **(B) REGIME DIFFERENCE** — 2023/24 was a market the strategy does not address.

After a weak result, (B) sounds like an excuse. So the evidence that would distinguish
them is committed **now**, with thresholds, and the measurement is ordered **before**
outcomes are opened.

### 4.1 What is known about the era gap already (from the repo, not from sealed outcomes)

`data/reference/cvd/README.md`, written at data-pull time: *"2023/24 NQ traded 195–273k
contracts/day against 400–420k in 2025/26, at roughly half the index level."*

**Half the index level is the load-bearing fact.** NQ point ranges scale roughly with
index level, and this strategy's stop floor is **fixed in points** (9.5pt). The era
diagnosis (`docs/LONDON-ERA-DIAGNOSIS.md`) already established that this system's one
known structural fragility is exactly this units axis — stops fixed in points while
range moves. So a materially different points-range regime is not a post-hoc excuse; it
is a **pre-existing, documented prediction** about where this strategy is fragile.

### 4.2 Fit-side baselines (computed 2026-07-31 from FIT data only)

| metric | 2025 | 2026 | pooled fit |
|---|---|---|---|
| London session range (`on_range`), median pts | 173 | 220 | **186** |
| stop/range fraction, median | 7.92% | 5.69% | **6.83%** |
| median stop size, pts | — | — | **12.50** |
| floor-passing candidates per session day | — | — | **3.76** |
| wall-check pass rate (on floor-passing) | — | — | **24.1%** (W 23.2% / FAR 18.2%) |

### 4.3 The pre-registered discriminator — measure INPUTS before opening OUTCOMES

**Protocol (requires precondition 5).** After the sealed L0→L3 artifacts are built and
**before** the reporting command is run, measure these four **market-condition /
input** quantities on the sealed span and write them into this runbook:

1. median London session range in points
2. median stop/range fraction
3. floor-passing candidates per session day
4. wall-check pass rate (and W / FAR separately)

**None of these is an outcome.** No P&L, no R, no win rate, no exit reason. They are
properties of the market and of the detector's inputs. They are also exactly the
quantities the era diagnosis flagged for authorization
(`docs/LONDON-ERA-DIAGNOSIS.md`: *"`on_range` is a market-condition feature, not an
outcome, but it IS sealed-span data, so ask first"*).

**Ordering them before outcomes is the whole point.** A regime characterisation written
down before anyone sees P&L is evidence. The same characterisation produced after a bad
number is an excuse. If Angus declines the pre-run measurement, it must then be run
**simultaneously with** the report and interpreted with that weakness stated.

### 4.4 The decision rule — committed in advance

| sealed-span inputs (measured per 4.3) | a WEAK result must be read as |
|---|---|
| session range within **±25%** of fit's 186pt **AND** stop/range within **±25%** of 6.83% **AND** candidate density within **±33%** of 3.76/day | **(A) EDGE DECAY.** The regime explanation is REJECTED — the strategy met a comparable market and failed in it. |
| session range **outside ±25%** (expected: materially LOWER, NQ at ~half index level) **OR** stop/range outside ±25% | **(B) REGIME DIFFERENCE is admissible** — but only as *"untested in this regime"*, never as *"validated"*. A weak result still blocks promotion. |
| wall-check pass rate outside **±10 pp** of 24.1% | **(C) FEATURE-ASSEMBLY FAULT suspected** — the detector is not seeing what it saw on fit (depth density, tape density, or a build defect). Investigate the pipeline **before** interpreting P&L at all. This is the `holdout_verdict.py` doctrine: *"if a check fires at 47% in fit and 14% out of fit, the P&L below it is uninterpretable until that is settled."* |

**The asymmetry that makes this honest:** every branch above **blocks promotion**. (B)
and (C) are not routes to shipping a weak strategy — they are routes to *"this run did
not answer the question; the answer needs forward data or a repaired pipeline."*

### 4.5 A second, independent discriminator available inside the report

Item 9 (W/FAR lift) and the PRIMARY test are measured on the same sealed data, and they
separate cleanly:

- **lift survives, book mean R weak** → the *signal* travelled; the loss is in
  selection, exits, or costs. Points away from "the edge never existed".
- **lift dies too** → the core signal itself did not travel. Points toward (A).

This costs nothing extra: both figures are already in the fixed §2 list.

### 4.6 What CANNOT distinguish them — stated so nobody tries

At n ≈ 59–84, *"+0.20R because regime"* and *"+0.20R because half-dead edge"* are **not
separable by this run**. Do not attempt a post-hoc split by block, by month, by
volatility tercile, or by any subset to rescue a verdict — every such slice is a new
look at a dataset that opens once, and the prereg's multiplicity accounting does not
cover them.

## 5. BLOCK STRUCTURE — six discrete blocks, not a contiguous run

The sealed sample is **not** a continuous 128-day period. It is six discrete monthly
blocks, drawn randomly and pre-registered before any data was pulled
(`scripts/sample_holdout_days.py`, seal committed before scoring):

| block | sealed days | depth files | CVD |
|---|---|---|---|
| 2023-07 | 21 | 21 | ✓ |
| 2023-09 | 21 | 21 | ✓ |
| 2023-11 | 21 | 21 | ✓ |
| 2024-03 | 20 | 20 | ✓ |
| 2024-04 | 22 | 22 | ✓ |
| 2024-10 | 23 | 23 | ✓ |
| **total** | **128** | **128** | **✓** |

**Consequences, binding on interpretation:**

1. **Bootstrap is BY DAY WITHIN BLOCK.** Resampling days across the whole 128 would
   treat six months as one homogeneous pool and silently manufacture regime diversity
   the sample does not have. Blocks are the natural cluster; days within a block are the
   resampling unit.
2. **Six blocks is limited regime diversity.** Effective independent regime observations
   ≈ 6, not 128. A result driven by one block is one month's weather, not an edge — so
   **the per-block breakdown is reported descriptively** (it is already implied by the
   monthly figures in item 6/7) and a headline that dies without one block must be
   stated as such.
3. **Three blocks carry UK/US DST divergence** (see §6) — 21 of 128 days, 16% of the
   sample, materially more than the fit span's ~7%.
4. **Seasonal skew is real and unfixable:** July, September, November, March, April,
   October. No December/January. Do not generalise to the full year.

## 6. DST — verified, and heavier in the sealed span than in fit

The sealed span contains **three** UK/US divergence windows, derived independently from
`tzdata` (not from any doc):

| block | divergent days | dates | 08:00 UK lands at |
|---|---|---|---|
| 2023-11 | 3 | 2023-11-01 .. 11-03 | 04:00 ET (vs normal 03:00) |
| 2024-03 | 14 | 2024-03-11 .. 03-28 | 04:00 ET |
| 2024-10 | 4 | 2024-10-28 .. 10-31 | 04:00 ET |
| **total** | **21 / 128 = 16%** | | |

**Verified 2026-07-31:** `window_et()` resolves **128/128 sealed days correctly** against
tzdata truth, including every transition boundary (2023-10-31→11-01, 2024-03-08→03-11,
2024-10-25→10-28). Depth files are London-local aligned on both normal and divergent
days (UTC hour shifts, UK window constant, 105 rows inside 08:00–09:45 UK on both).

Under rev 3 the 09:45 UK cut resolves to **04:45 ET** normally and **05:45 ET** on
divergent days. This is handled by the same per-day resolution, not a hardcoded hour.

## 7. Guards — demonstrated on 2026-07-31, not assumed

| guard | demonstration | result |
|---|---|---|
| authorization required | sealed run attempted with no `--authorized-by`, both configs | **REFUSED** |
| write-once | placeholder created at the report path, sealed run attempted **with** a token | **REFUSED**, placeholder left unmodified, then removed (no residue) |
| ordering safety | code read: `out_path.exists()` check raises **before** `load_pop()` | confirmed |
| `load_pop()` year guard | fit path fed a frame containing 2023/2024 rows | **SPAN VIOLATION** |
| `guard_holdout_days()` | book containing a non-sealed day | **SPAN VIOLATION** |
| structural | no sealed derived artifact exists (`l0/l1/l2/l3_*_holdout*`) | all absent |
| live | `load_pop("holdout")` today | halts: MISSING ARTIFACT |

## 8. After the run — the only permitted next steps

1. Read the report at §3's declared resolution.
2. Apply §4.4's decision rule using the §4.3 input measurements.
3. **Stop.** Do not re-run. Do not slice. Do not propose a config change in the same
   session the numbers first appear.
4. Post-holdout questions (sizing ladder, exits, NY profile) are unlocked only by a
   PASS, and are separate decisions with their own declared numbers
   (`docs/LONDON-REV3-BUNDLE.md` §4).

**If the primary FAILS:** the deliverable is a written verdict, not a fix. The parked
list (`docs/HANDOFF-london-session3.md` §4.6) does not get re-opened on fit evidence to
rescue a failed holdout — that is precisely how a 13-look dataset becomes a 20-look
dataset.
