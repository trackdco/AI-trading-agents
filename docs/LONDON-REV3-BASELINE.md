# Rev 3 baseline proposal — window 08:00–09:45, adopted as a RULING

**Status: DRAFT. Changes prereg §1. Requires ANGUS signature before the sealed set opens
under it. Until signed, rev 2a (window 08:00–10:00) remains the strategy of record and the
rehearsed holdout runner reports that book.**

## Boundary revision + full disclosure (2026-07-30, late session)

The ruling was revised same-day from 09:30 to **09:45** (Brake: "just go to 9:45") after
the robustness perturbation showed 09:45 DOMINATES 09:30 as a cut: identical stack
maxDD ($958 — all drawdown damage lives in 09:45–10:00), +$1,000 net, +19 trades, both
eras improve. On the record: **the window boundary has now been examined three times on
the same fit data** (the session-2 bucket analysis, the 09:30 adoption, the perturbation
suite — whose own header declared its results non-actionable). This is disclosed so the
signature is made with eyes open, and **the boundary is closed to further fit-side
moves**: the remaining window evidence comes from the holdout bucket profile and forward
data only.

| stack (veto + one-at-a-time) | n | net | maxDD |
|---|---|---|---|
| cut 09:30 | 110 | +$17,941 | $958 |
| **cut 09:45 (ruling)** | 129 | **+$18,941** | **$958** |
| full 10:00 | 147 | +$18,121 | $2,036 |

## The ruling and its honest basis

Brake, 2026-07-30: *"we'll go with cutting trades at 9:30, and use that as our baseline"*
— revised same day to 09:45 per the disclosure above.

Recorded as a **risk ruling, not a finding**, because the evidence status is on the record
and unchanged: the late-bucket cut FAILED its worst-of-4-buckets permutation guard
(p=0.076, `docs/LONDON-LATE-BUCKET.md`). What is being bought is not expectancy — it is
drawdown and capital efficiency, at a known price:

| PLAIN BOOK (no veto/serial overlay) | rev 2a (08:00–10:00) | rev 3 (08:00–09:45) |
|---|---|---|
| trades / days | 187 / 107 | 167 / 99 |
| net | +$22,795 | +$23,065 (+$270) |
| WR / mean R | 57% / +0.513 | 60% / +0.581 |
| maxDD trade-level | $2,550 | **$1,555 (−39%)** |
| months green | 11/14 | 11/14 |
| per-era mean R | +0.434 / +0.570 | +0.505 / +0.638 (both improve) |

(At 09:45 the cut is better than free on the plain book: +$270 net AND −39% maxDD —
the removed 09:45–10:00 slice was net-negative on its own.)

Precedent: the no-distance-cancel rule entered §1 the same way — "a ruling, not a finding" —
against a measurement that mildly favoured the cancel. Authority is Angus's; this document
exists so the ruling is exercised with the guard failure in plain sight, not around it.

## A clean property, verified

Cutting at the population level (candidates filling ≥09:30 London never exist) and cutting
post-hoc (drop late fills from the full book) produce **byte-identical books** — the $400
day stop's path never interacts with a late trade on any fit day. The cut is well-defined
and needs no re-run of L0–L3.

## What rev 3 changes downstream (all mechanical, none done yet)

1. **Prereg §1** window → 08:00–09:30 Europe/London (03:00–04:30 ET normal, 04:00–05:30 on
   misaligned days); §2 fit-reference tables → the rev 3 column above.
2. **Holdout projection:** ~65 trades (vs ~84). Power on the primary at Šidák α=0.0253,
   two-sided: **85%** if the fit effect (+0.630, sd 1.547) persists — UP from 78%, the
   larger effect outweighing the smaller n. **Declared forward expectation stays ≈ +0.48**:
   if the late bucket's weakness is noise (which p=0.076 cannot exclude), cutting it does
   not raise true expectancy, and the declared prior must not inherit a guard-failed
   improvement.
3. **The rehearsed runner** gets a rev-3 anchor set and re-rehearses against the table
   above before the sealed run. Zero logic changes — window filter plus new anchors.
4. **The era-crossing, grid-audit and determinism verdicts** were run against 08:00–10:00.
   Their conclusions (floor 9.5, uncapped, window-end lifetime, order-dependence neutrality)
   are re-asserted, not re-derived, on the narrower window — the rev 3 rehearsal anchor
   gate is the check that nothing moved.

## The decision Angus actually makes

- **Sign rev 2a unchanged** — window stays 08:00–10:00; the cut stays parked; the holdout's
  bucket profile (already a declared descriptive output) adjudicates the late bucket on
  sealed data for free.
- **Sign rev 3** — the cut becomes §1 config by ruling; the holdout opens on the 144-trade
  book with the anchors above.

Either signature unblocks the sealed run. What may NOT happen is opening the sealed set
under one window and reading it under the other.
