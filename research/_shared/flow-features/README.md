---
date: 2026-08-08
kind: AT-ENTRY ORDER-FLOW FEATURE LIBRARY — spec and proofs
library: scripts/flow_features.py
tests: scripts/test_flow_features.py
roll-clean: scripts/footprint_clean.py
---

# At-entry flow feature library

> ## THE ONE RULE
> **Every feature reads only minutes ≤ `entry_minute − 1`. The entry minute is never read, by any
> feature, for any reason.**

This is not caution. `F2_retrace_ratio` ended its window **at** the entry minute; footprint data is
minute-aggregated and entries fill intrabar, so it carried **up to 59 seconds of post-fill tape**.
On 73% of one card's trades the entire numerator *was* the entry minute. It voided the programme's
flagship flow finding and halted a pre-registered test at Step 0.

`entry_minute − 1` is provably safe: that bar has **closed** before the entry minute begins.

**The boundary is enforced by the library, not trusted to the feature.** `compute()` masks every
input frame to `≤ cut` before calling the feature, so a feature *cannot* read past the boundary
even if its own code were wrong.

---

## The features

| feature | time boundary | roll-clean? | pre-stated direction |
|---|---|---|---|
| **`participation_to_touch`** | `(disp_end, cut]` over per-minute volume ÷ `[disp_start, disp_end]` | no | **winners LOWER** *(H2′)* |
| `disp_delta_magnitude` | `[disp_start, disp_end]`, a completed leg | no | none — **unsigned** |
| `cvd_slope_pre_15` | `[cut − 14min, cut]` | no | none |
| `cvd_price_divergence_pre` | two completed legs in `[sess_start, cut]` | no | none |
| `absorption_pre_5` | `[cut − 4min, cut]` | no | none |
| `volume_pace_at_entry` | `[cut − 4min, cut]` vs session median to `cut` | no | none |
| `vpoc_distance_at_entry` | volume-at-price `[sess_start, cut]` | **YES** | none |
| `value_area_location` | volume-at-price `[sess_start, cut]` | **YES** | none |

**Banned and not implemented:** delta **sign** confirmation of a structurally-defined move. It
removed 0 of 29 on `ash-unicorn-sb` because the structure gate already requires a directional
break, so signed delta over that leg agrees by construction. `disp_delta_magnitude` is
deliberately **unsigned**.

---

## Two independent checks, both required

**A ⟂ B.** A feature can pass one and fail the other. A wrong feature computed entirely from
pre-entry data passes the look-ahead proof and is still wrong.

### A · Unit tests on synthetic sequences — **15/15 PASS**

Hand-computable answers on constructed tapes. Highlights:

- `participation_to_touch`: 5-min retrace over 5-min displacement = **1.0**; 10-min = **2.0**;
  **a retracement shorter than one minute returns `NaN`, not 0** — undefined is not zero and must
  never be imputed.
- `disp_delta_magnitude`: identical for delta `+10` and `−10` — the unsigned property is tested,
  not asserted.
- `absorption_pre_5`: 500 volume over a 4pt range with zero net delta = **125.0**; fully
  one-sided = **0.0**.
- **Boundary enforcement**: a `1e6` volume spike placed *at and after* the entry minute **cannot
  move any value**.

### B · Look-ahead proofs on every real historical event — **8/8 features PASS**

Each feature recomputed with **every row from the entry minute onward physically deleted**. The
value must be identical. `NaN == NaN` counts as identical.

**1,402 events across 13 sources** (`ash-unicorn-sb` + all 12 sweep trials).

| feature | events | identical | **defined** |
|---|---|---|---|
| `participation_to_touch` | 1402 | **1402** | 16 |
| `disp_delta_magnitude` | 1402 | **1402** | 19 |
| `cvd_slope_pre_15` | 1402 | **1402** | 1397 |
| `cvd_price_divergence_pre` | 1402 | **1402** | 1156 |
| `absorption_pre_5` | 1402 | **1402** | 1397 |
| `volume_pace_at_entry` | 1402 | **1402** | 1397 |
| `vpoc_distance_at_entry` | 1402 | **1402** | 1397 |
| `value_area_location` | 1402 | **1402** | 1397 |

---

## ⚠️ H2′ availability — measured, and better than feared, but read the denominator

`participation_to_touch` is **defined on 16 events, not 1402**, and the reason is structural, not
a defect:

- It needs a **displacement leg**. Only `ash-unicorn-sb` logs one — **19 events**. The 12 sweep
  detectors do not define a displacement leg at all, so the feature is undefined on all 1,383 of
  their events **by construction**.
- Of those **19**, it is defined on **16 (84%)**. The other 3 have a retracement shorter than one
  full minute.

**84% is materially better than the H2 experience suggested** — on `zxck-10am-keyopen` 73% of
retracements were a single minute and on `orb-fvg-nyopen` 50%. `ash-unicorn-sb`'s retracements
have a median of 2 minutes, which is why it fares better.

**But n=16 is the honest availability number today**, and forward accumulation runs at ~1.5
trades/month. The protocol's warning stands: if a future sample is mostly undefined, H2′ must be
reported as untestable rather than run on the surviving minority — that minority selects **slow
retracements**, which is a biased subset and plausibly correlated with the outcome being tested.

---

## Roll-clean dependency

`vpoc_distance_at_entry` and `value_area_location` read volume-at-price and **must** use
`scripts/footprint_clean.py`. Un-cleaned, the day-level banding in the shipped data cannot
separate contracts across a quarterly roll: **2025-09-15's raw 08:00–09:29 VPOC is 239.90** — a
*calendar-spread* price — against a session bar range of 24,139–24,183. Cleaned it is 24,172.75.

The library reads the cleaned frames only. `f2_oos_test.flow_frame()` reads the **uncleaned** tape
and is deliberately not changed retroactively; results computed from it inherit the caveat.
