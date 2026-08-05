---
date: 2026-08-08
kind: OVERNIGHT RUN — morning report
standing rule: the entire owned span through 2026-07-15 is IN-SAMPLE, permanently
---

# Overnight run — morning report

> **Standing rule for the whole run: nothing produced tonight is a finding, an edge, or a result.
> The owned span through 2026-07-15 is now in-sample permanently. Tonight produced fixes, audits,
> machinery, and pre-registered hypotheses for future data.**

## The single most important line

> ## 🔴 THE FLAGSHIP DID NOT FULLY SURVIVE AUDIT.
> `ash-unicorn-sb` carried a **Sunday-stub defect** in its daily-bias state machine.
> **n 24 → 23 · expectancy +0.655R → +0.516R · maxDD 3.0R → 5.0R · effect 74% → 60% of the bar.**
> It does not collapse. It degrades, and the degradation is in every direction at once.

---

## Stage 0 — bookkeeping (landed, committed `9f3abb5`, `603157c`)

### 0.1 Forward protocol amended before any forward trade accumulated (log: 0 rows)

- **H1 STRUCK** — failed out-of-sample. Cliff's δ +0.178 against an in-sample +0.596, p_holm
  0.1895, on a sample that detects d ≥ 0.58. *The power was there; the effect was not.*
- **H2 STRUCK** — the feature is not computable at entry. **This retroactively VOIDS the original
  Stage-4 F2 finding**, and the card now says so. The 52.6% → 72.7% improvement was a positive
  discrimination result on a feature whose contamination biases *toward* false positives.
  **Withdrawn, not weakened.**
- **H2′ REGISTERED, UNTESTED** — `participation_to_touch`, ending strictly at `entry_minute − 1`,
  direction pre-stated (winners **lower**), **threshold deliberately unset** — to be fixed at a
  percentile of future data only.

### 0.2 Roll contamination fixed at the shared data layer (`scripts/footprint_clean.py`)

The shipped clean bands ticks against each **day's** `[low, high]`, which cannot separate contracts
across a quarterly roll. **4.14% of rows / 2.32% of volume off-band**; 45 of 352 sessions above 1%.

**It is not merely back-month contamination.** On 2025-09-15 the raw price range is
**234.40 → 26,300.00** against a session bar range of 24,139.50 → 24,183.00. The low cluster is
**calendar-spread** ticks. That session's raw 08:00–09:29 **VPOC is 239.90 — not a wrong price, not
a price at all.** Cleaned: 24,172.75.

Minute-level banding zeroes off-band volume **by construction** and asserts it at runtime. Chosen
over roll-week masking because masking discards good front-month volume and needs a roll calendar
this repo cannot derive — `nq_1m_master.parquet` has **no contract identifier**.

### 0.3 Programme verdict memo written for Angus (`program-verdict-2026-08.md`)

Thesis falsified within tested scope; the searched-out window; the defect catalogue; **scope
conditions given their own section** so "nothing survived" is not over-read; and the data fork with
a recommendation (**tick resolution first, forward accumulation in parallel, deeper history only
against a registered slate**).

---

## Stage 1 — the flagship retro-audit

Five independent adversarial lenses, each finding attacked by an independent skeptic.
**29 agents · 24 findings filed · 16 refuted · 8 confirmed.**

### The material defect: Sunday stubs in `daily_bias`

`resample("1D")` on NY-local timestamps keys on the NY **calendar** day. Globex opens **18:00 ET
Sunday**, so every Sunday became its own "daily bar" holding only that 6-hour block.

| | |
|---|---|
| Sunday stubs over the span | **80** |
| median stub range vs weekday | **184.5pt vs 393.5pt** |
| bias-SET events involving a stub | **54 of 117** |
| days where the daily bias is wrong | **84 of 480** |

| | before | **after** |
|---|---|---|
| n | 24 | **23** |
| win / BE / loss | 12 / 5 / 7 | **10 / 6 / 7** |
| win rate | 50.0% | **43.5%** |
| avg R | +0.708 | **+0.565** |
| **expectancy net** | +0.655R | **+0.516R** |
| total | +17.0R | **+13.0R** |
| **max drawdown** | 3.0R | **5.0R (+67%)** |
| effect | +0.518 | **+0.421** |
| **% of the +0.6978 bar** | 74% | **60%** |
| direction | 21L / 3S | 17L / 6S |
| median stop | 26.2pt | 31.8pt |

**The 20 common trades are unchanged in direction and R.** Both eras remain positive (2025 n=15
+5.0R, 2026 n=8 +8.0R). **The fix is not tunable:** hour 17 ET holds **zero** bars (CME maintenance
break), so every boundary in [17:00, 18:00) gives the same frame, and CME session keying is
**byte-identical** to simply dropping the stubs.

### The intrabar bound — 128 admissible ordering books

Two channels where 1-min OHLC cannot certify the order: fill-minute break-even arming, and the
sweep-minute MSS reference. Bounding **both** across all 128 admissible books:

| | bound | shipped |
|---|---|---|
| n | [22, 25] | 24 |
| win rate | [41.7%, 52.2%] | 50.0% |
| expectancy net | [+0.446, +0.860] | +0.655 |
| total R | [+12.0R, +21.0R] | +17.0R |
| effect | [+0.370, +0.759] | +0.518 |

**Order-robust across 128/128 books** — these are proofs, not estimates: total R positive; net
expectancy positive; both eras positive; **n below the 30 floor**; maxDD ≤ 3.0R; win rate nowhere
near his claimed 70–80%.

**One claim stops being certifiable:** "it still does not clear the bar" holds in **126 of 128**.
Two books reach **+0.7591** and **+0.7156**, above the +0.6978 bar. *The failure direction favours
the candidate*, which is the honest way round to report it.

### ⚠️ An undisclosed fact the audit surfaced, arguably the sharper half

**The `o0` sweep-gate fix did NOT cure the collapsed MSS lookback**, and the card implies it did.
`s == 0` still holds on **12 of the 24 shipped trades**, carrying **+4.0R of the +17.0R**. The gate
removed *pre-window* sweeps; a sweep inside the window's **first minute** still leaves the MSS
reference equal to the sweep bar's own extreme. **This is now flagged and remains open.**

### Two independent checks I ran myself

**Code-order choice — the bound collapses to a point, provably.** 14 of 24 sessions produce more
than one valid setup, but **0 produce both directions** (the daily-bias gate admits one direction
per session), and in all 14 the several qualifying levels resolve through the same MSS bar to the
**same FVG edge and the same order block**. Every selection rule — first, last, earliest fill,
latest fill, earliest sweep, worst-case, best-case — returns **byte-identical results**. *Different
levels, one trade.*

**Direction control — the direction rule is doing real work.** On the same entries and stops:

| arm | total R | expectancy |
|---|---|---|
| **actual (as traded)** | **+17.0R** | +0.655 |
| always long | +11.0R | +0.405 |
| always short | −8.0R | −0.387 |
| random direction (20k reps) | +1.5R | +0.008 |

**The actual result sits at the 99.5th percentile of random direction.** The 3 shorts contributed
+3.0R. This is the strongest single defence against "it is just long in a rising market" — and it
is still in-sample.

*(Both computed on the pre-Sunday-fix n=24 set, before that fix landed. Direction remains
one-sided at 17L/6S after it.)*

### The other confirmed findings — all documentation, nil headline impact

The autopsy block on the card carried **nine stale pre-fix figures** while the card claimed the
autopsy had been re-run. Root cause found and fixed: `ash_autopsy.py` **hardcoded** the string
`"SEARCH over ~9 features on 15v12"` while computing the real sample beneath it. That is how the
stale numbers survived review. Also stale: the funded-sim prose, one window-robustness line.

---

## Stage 2 — at-entry flow feature library

`scripts/flow_features.py` · `scripts/test_flow_features.py` · `research/_shared/flow-features/`

**8 features. Every one reads only minutes ≤ `entry_minute − 1`.** The boundary is enforced **by
the library**, which masks every input frame before calling the feature — so a feature cannot read
past the boundary even if its own code were wrong.

| check | result |
|---|---|
| unit tests on synthetic sequences (hand-computable) | **15 / 15 PASS** |
| look-ahead proofs on real events — recompute with all rows from the entry minute deleted | **8 / 8 features, 1402 / 1402 events identical** |

The two are **orthogonal** and both are required: a wrong feature computed entirely from pre-entry
data passes the look-ahead proof and is still wrong.

**H2′ availability, measured:** defined on **16 events**, not 1402. It needs a displacement leg;
only `ash-unicorn-sb` logs one (19 events), and the 12 sweep detectors define none, so it is
undefined on all 1,383 of theirs **by construction**. Of the 19, defined on **16 (84%)** — better
than the H2 experience suggested, because ash's retracements have a median of 2 minutes. **But 16
is the honest availability today.**

---

## Stage 3 — confluence scan

## Total comparisons scanned: **18,232** — tonight's ledger N

17 event streams × the Stage-2 library + context features, ≤2 conditions, thresholds only at
fixed 25/50/75 percentiles. Matched control: outcomes **permuted within stream**, 400 reps each.

## ⛔ Registered hypotheses: **ZERO**

| check | result |
|---|---|
| streams whose best reaches the **99th** percentile of its own best-of null | **0** (expected 0.17) |
| streams reaching the **95th** | 3 (expected 0.85) |
| observed maximum across 17 streams | **0.980** |
| expected maximum of 17 uniform draws | **0.944** |
| **P(at least one reaching 0.980 by chance)** | **0.291 — unremarkable** |

Three independent reasons: the best result is **what 17 draws produce**; **19 of the top 20
subsets sit within four events of the n=25 floor**; and the top 30 rows collapse to **16 distinct
subsets** — 14 are the same subset relabelled via a second condition that excludes nothing.

**No feature discriminates across streams either** — mean improvement −0.06R to +0.03R across 15
features on ≥8 streams each.

*(I corrected my own calibration mid-run: the scan first reported "0 of 18,232 reached p99,
expected ~182". That expectation was wrong — each comparison is already scored against a
best-of null, so the correct question is per-stream.)*

---

## Decision memo — what data would test the registered slate at once

**The registered slate is currently ONE hypothesis: H2′.** The confluence scan added none. That is
itself the most useful input to this decision: **there is very little to buy data *for* right now.**

### What H2′ needs

| | |
|---|---|
| availability today | **16 events** (needs a displacement leg; only ash logs one) |
| forward rate | ~1.5 trades/month → **84% defined** → ~1.3 usable/month |
| n for a Mann–Whitney at 80% power, d ≈ 0.6 | **~35 per group ≈ 70 events** |
| **forward-only time to test H2′** | **~4.5 years** |

**Forward accumulation alone cannot test H2′ in any useful horizon.** That is the finding, and it
governs everything below.

### Option A — deeper history (Databento GLBX.MDP3, 1-min bars + footprint, 2022→2025-05)

- **Legitimate**, because H2′ is registered *now*, before the data is seen.
- ~3 extra years ≈ **2.2× the current span** → `ash-unicorn-sb` events ~23 → **~75**, H2′ defined
  on ~84% → **~63 events**. Close to the ~70 needed, **in days rather than years**.
- Also re-tests **every** existing detector on unseen data — including the four negatives, where a
  regime with a bear phase is the actual open question.
- **Caveat that must be honoured:** it is a legitimate test bed for H2′ **only**. Anything else run
  on it is a new search, and the deflation bar already stands at N=293 plus tonight's 18,232.

### Option B — tick/trades resolution (GLBX.MDP3 *trades*, the existing span)

- The **only** thing that can settle H2/H2′ *properly* — minute aggregation is precisely what broke
  H2, and H2′ works around it by discarding the entry minute rather than by measuring it.
- Collapses **every intrabar bound in the programme** to a point estimate: the flagship's
  [+0.446, +0.860] expectancy band, and the 73 ambiguous `zxck-10am-keyopen` sessions.
- Does **not** add events.

### Recommendation

**A and B together, and B first if only one.** B removes a defect class and makes the flagship's
own numbers exact — including whether it is one of the 126 books below the bar or one of the 2
above. A is what makes H2′ testable this decade.

**Do not buy A to search it.** With one registered hypothesis, a purchase justified as "more data
to look at" would convert a clean pre-registration into a fresh search against an already-inflated
bar. The value of A is entirely in the fact that **the slate was registered first**.

---

## Everything committed

| stage | commit |
|---|---|
| 0.1 + 0.2 protocol amendment, roll fix | `9f3abb5` |
| 0.3 programme verdict | `603157c` |
| 2 feature library + proofs | `45ac406` |
| 3 confluence scan, zero registered | `be62d50` |
| 1 flagship correction | `f8c70d3` |
