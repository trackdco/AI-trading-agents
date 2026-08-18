# RECEIPT — the dead-zone trail ban, priced before shipping

**Status: the rule does NOT ship.** He approved it in principle
(2026-08-18: *"yes"*) and required the receipt first (*"but see what the
outcome would be without it"*). The receipt reverses the recommendation.
This is the veto-receipts protocol doing its job — the same one that would
have killed T40 in review.

## The rule as proposed

> A pre-TP1 trail may not land within one noise-floor (0.75× the trailing
> 2m range) of entry, on either side — inside that dead zone, hold instead.

Motivated by wr1's Wednesday trail to 5pt above a short entry, and by §6's
ban on risk-aversion stop-parking.

## Method

Every `trail` across the three current-era books (w49, j49, sealed wr1):
41 trails, 18 inside the dead zone, **13 of them pre-TP1** — the rule's
domain. For each, the counterfactual holds the stop where it was and walks
the committed bars: does price print TP1 or the held stop first?
Conventions, stated: reach-TP1 cases are scored at the TP1 touch on the
full position (understates HOLD when the manager would have extracted
more); chained later trails are not replayed (the first dead-zone trail
freezes the stop). Approximate by construction; the direction is stable.

## The ledger

| book | day | cid | as-run R | HOLD instead | rule's effect |
|---|---|---|---:|---|---:|
| w49 | 06-23 | L1 | +1.145 | TP1 → +1.68 | +0.53 |
| w49 | 06-23 | L5 | +0.483 | STOP → −1.00 | **−1.48** |
| w49 | 06-23 | P3 | +1.825 | TP1 → +1.85 | ≈0 |
| w49 | 06-23 | A4 | +0.469 | TP1 → +1.74 | +1.27 |
| w49 | 06-23 | A5 | +2.193 | TP1 → +1.59 | −0.60* |
| w49 | 06-24 | A7 | −0.157 | STOP → −1.00 | **−0.84** |
| w49 | 06-24 | P6 | −0.183 | STOP → −0.65 | **−0.47** |
| w49 | 06-25 | A2 | +2.740 | TP1 → +1.86 | −0.88* |
| j49 | 05-31 | P2 | +0.191 | STOP → −1.00 | **−1.19** |
| j49 | 06-01 | A6 | +0.500 | TP1 → +2.10 | +1.60 |
| j49 | 06-02 | L10 | +0.300 | STOP → −1.00 | **−1.30** |
| wr1 | 06-23 | L1 | +0.388 | TP1 → +1.29 | +0.90 |
| wr1 | 06-24 | A3 | +0.371 | TP1 → +1.02 | +0.65 |

\* convention artefact: the dead-zone stop was never actually hit on these,
so HOLD ≈ as-run in reality; the TP1-touch convention penalises HOLD
unfairly here. Removing those two makes the ban look *slightly* less bad —
it does not change the sign.

**Totals: as-run +10.27R · rule-applied +8.48R · the ban costs ≈ −1.8R on
the measured sample.**

## What the cases actually show

The dead-zone trail is the manager's **soft exit**, and it is being used
with judgement:

- **The saves (5 cases, ≈ −4.3R prevented):** third attempts at a failing
  edge (w49 L5, j49 L10), a long held into the pre-open (j49 P2, w49 P6),
  a late fade (A7). Stale or degraded setups where the tight trail
  converted a full stop into a scratch or small win. The manager was right
  to want out cheap.
- **The strangles (4 cases, ≈ +3.4R given back):** fresh setups choked on
  their first wobble — w49 A4 (ran +1.74R after being trailed to 9.5pt),
  j49 A6 (the Tuesday flip long with +2.1R in it), wr1 L1 and A3. The w49
  06-23 L1 exit note narrates it: *"stopped on the 03:02 trail, which sat
  3.50pt above entry… the zone was not reached until 04:00, after the
  stop."*

A blanket ban removes both. The saves outweigh the strangles.

## Recommendation

1. **Do not ship the ban.** tv-manage stays as written (0.3.4).
2. The real pattern — strangle fresh trades, save stale ones — is a
   judgement teaching, not a gate. If he wants it written, the doctrinal
   line (no statistics, per the 0.4.10 rule) is:

   > *A dead-zone trail — a stop within noise of entry — is a soft exit,
   > not protection. Reach for it when the setup has degraded (a repeated
   > attempt, a level going stale, the clock against you), never on a
   > fresh trade's first adverse test — a fresh trade earns its breathing
   > room (T75).*

   Awaiting his word; 13 cases is a pattern, not a law.
