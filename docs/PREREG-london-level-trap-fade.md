# PRE-REGISTRATION — LDN-TRAP-01: level-trap-fade

Filed per `docs/VALIDATION-PROCESS.md` §1, **BEFORE any census run**. The git timestamp of
this commit is the declaration. Trial family: **LDN-TRAP-01**.

Thesis: `research/candidates/london-level-trap-fade.md`, greenlit ANGUS 2026-08-04.
Feasibility established first (`scripts/london_feasibility_scan.py`): the raw event fires on
185 days in 2025 and 104 in 2026 — comfortably above the n ≥ 30 floor before further gates.

**Bars caveat:** §2 numbers remain `[PROPOSED]`. Thresholds used below are the proposed
defaults; if Angus ratifies different ones the verdict is re-graded, and the fragility gate
(§6) is bar-independent either way.

---

## 1. Claim (falsifiable)

The overnight high/low and prior-day RTH high/low carry stop clusters just beyond them. A
London-window break of one that **snaps back inside within minutes** was a liquidity run,
not a repricing: the stops were the target, and once consumed there is no flow to sustain
the move. Trapped breakout entrants liquidating fuels the rotation back.

> **After a break-and-reclaim of a watched level inside the London session, price continues
> AWAY from the level (back into the range) over the remainder of the session.**

If that is false, the candidate is dead — no entry refinement recovers a signature that
does not exist at structure level.

## 2. Specification — this document authorises exactly this computation

**Session window: 08:00–10:00 Europe/London**, converted per day via
`london_window_et(day)`. **ET hours are never hardcoded** (burn list item 1 — the defect
found in LDN-SWP-01's first run).

**Watched levels**, all frozen at the London open:
- **ONH / ONL** — overnight high/low from 18:00 ET (D−1) to the London open, computed per
  day. *Not* the substrate's `on_hi_0300`/`on_lo_0300`, which hardcode 03:00 and are stale
  by an hour on DST-mismatch days.
- **PDH / PDL** — prior RTH high/low (`prior_rth_hi`, `prior_rth_lo`).

Frozen at the open, deliberately: a level that keeps updating during the window would be
partly defined by the move being measured.

**Event (break-and-reclaim), all parameters declared here, none searched:**
1. Price trades **≥ 4 ticks (1.00 NQ point)** beyond a watched level, inside the window.
2. Within **≤ 15 minutes** of that break, a 1-minute **close** prints back through the
   level, on the range side.
3. The event completes at that reclaim minute, call it `t`.

**Direction:** the fade — opposite the break. Break above → short; break below → long.

**Outcome:** `signed_ret` = (close at window end − close at `t`) × direction. Positive means
the fade worked. Measured **strictly from `t` forward**, so nothing defining the event is
drawn from the interval being measured.

**Pooling:** all four levels pool into one event type; the first qualifying event per day is
taken, so days contribute once. Per-level breakdowns are descriptive companions and cannot
carry the verdict.

## 3. Causality audit (new gate — from `VERDICT-LDN-SWP-01.md` §4)

| variable | determined | before the outcome window? |
|---|---|---|
| ONH / ONL / PDH / PDL | at or before the London open | ✅ |
| break (≥4 ticks beyond) | at break minute, ≤ `t` | ✅ |
| reclaim close | at `t` | ✅ |
| direction | by which side broke, known at `t` | ✅ |
| outcome | measured over (`t`, window end] | ✅ |

Nothing that defines the event, its direction, or its grouping is drawn from the interval
being measured. **This audit is a required section of every prereg from now on.**

## 4. Eras

Discover 2025 / validate 2026-01..07, **and the inverse pass** (§2.1). Both directions must
agree. **2023/24 is NOT touched in any form** — the run asserts the sealed years absent
before computing anything. No holdout look.

## 5. Secondary — one, pre-specified

Candidate's level-quality refinement: **first revisit vs second-or-later revisit** of the
same level within the window. The thesis predicts the fade works on the first revisit and
inverts on later ones (defenders spent). One test, declared. The profile-structure variant
(poor/flat extremes, equal touches, no rejection tail) needs a builder and is **out of
scope** — a future prereg.

## 6. Fragility gate — runs FIRST

`signed_ret` mean is recomputed with the 1, 3, 5 and 10 largest-|signed_ret| events removed,
plus a 1/99-winsorised version. **Sign flip at any trim depth ≤ 3 in either era kills the
family regardless of every other result** (§2.5). Bar-independent, so a FAIL here is final.

## 7. Decision rules — three-way, declared in advance

Let `M` = mean `signed_ret`, and `M₂₅` its 2025 estimate.

| outcome | condition |
|---|---|
| **PASS** | `M > 0` at p ≤ 0.05 one-sided in **both** eras, fragility gate clear, n ≥ 30 per era |
| **FAIL** | validate-era 95% CI on `M` **excludes** `M₂₅` and contains 0 or is negative — or the fragility gate fires |
| **INCONCLUSIVE ON POWER** | neither — the CI contains both 0 and `M₂₅`; report minimum detectable `M` and events required at 80% power |

Absence is an equivalence claim, never a bare failure to reject (the criterion-2 defect,
`DIAGNOSIS-LDN-INV-01-power.md` §2).

## 8. Mandatory reporting

Event counts per era before and after every filter; the full fragility ladder whatever it
shows; power and minimum detectable `M`; the per-level and first-vs-later breakdowns; the
raw `signed_ret` distribution so a location shift is distinguishable from a tail artifact.

## 9. Trial accounting

**4 trials** into LDN-TRAP-01 (primary × 2 era directions, secondary × 2). Running total
across the London program: **12** (4 LDN-INV-01, 4 LDN-SWP-01, 4 here). These count in the
DSR denominator per §2.4.

## 10. Known limits

- **L0 structure measurement only.** No stops, targets or costs; the §2.5 cost stack applies
  from L1. Nothing here is tradeable evidence. A positive result means the signature exists,
  not that it survives friction — and the published MNQ falsification study is the reason
  that distinction is load-bearing.
- Holding to the window close is a measurement convention, not the candidate's exit (which
  is VWAP/mid-range targets with a 30–45 min stagnation kill). L0 asks only whether price
  drifts the right way.
- 4 ticks and 15 minutes are declared, not optimised. If the signature exists only at other
  values, this census will miss it — that is the cost of not searching, and it is deliberate.
- One event per day caps the sample at the day count; multi-event days are not exploited.
- NY-canon input overlap is MEDIUM (session structure + levels). The pairwise detector and
  correlation battery run at validation, not here.
