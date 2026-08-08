# FINDINGS — CONFLUENCE TRIGGER, fresh build at 2m and 3m

2026-08-08. Report-only, fit-only, no holdout contact (the bar-only venue is
closed regardless). Day-clustered bootstrap (seed 20260807) from the start.
2m and 3m reported **separately, never pooled; overlap between them not
computed this pass**, as specified.

**Construction.** Trigger = a TF candle closes through its **own TF BB(20)
MA** in the required direction AND through whichever VWAP band (middle, ±1,
±2, ±3) is in **confluence** with that MA — tolerance **10.0 pts**, taken
from the confluence work's existing `cluster.tolerance_points` in
`config/strategy.yaml` (the value `src/engine/snapshot.py` reads), same at
both TFs, not re-tuned. Qualifying band **recorded as data**, never fixed.
POC **not required**; rows with POC also inside the stack are flagged.
Entry next 1m open; stop trigger-candle extreme ± 1 tick; levels
full-session, triggers inside the three trading windows. Entry gate (T1
flatten): **PASS** (11 probes, 0 bad, 9 moved).

**Multiplicity, stated up front:** 2 TF × 2 mechanisms × 2 directions = 8
cells, and M2 carries 3 targets per cell. ~32 scored numbers, **no declared
bar anywhere** — these are base rates, published nulls included. Nothing
below is a verdict.

## A SPEC DEFECT CAUGHT AT THE POPULATION STAGE, before any M1 outcome was read

The first build measured M1's displacement at the trigger candle's
**close** — which demands the market still be ≥0.5W displaced *after* the
reversal candle. The funnel (74 sampled days) showed that conjunction is
nearly a null set:

| stage | 2m | 3m |
|---|---|---|
| displaced ≥0.5W at candle close | 2,073 | 1,437 |
| …AND closes through own TF MA toward the 15m MA | **11** | **0** |

Same defect class as a D8 pathology — caught on counts, not outcomes (the
only M1 cells in that build printed THIN, no EV was read). Displacement is
now measured at the candle **open** — the state when the trigger candle
began, the faithful reading of "price displaced, trigger fires back." The
close-displacement value stays on every row as data.

## §1 — POPULATION, per timeframe

| | 2m | 3m |
|---|---|---|
| raw triggers | 350 | 242 |
| first-of-fight (X=0.5W) | 284 — **0.97/day** | 206 — **0.70/day** |
| qualifying band | vwap 58 · **p1 106 · m1 91** · p2 15 · m2 14 · **±3: 0** | vwap 69 · p1 75 · m1 54 · p2 5 · m2 3 · ±3: 0 |
| stack ≥2 bands | 10 of 284 | 11 of 206 |
| POC in confluence (flag) | 33.5% | 44.7% |

The trigger is **rare** — under 1/day at 2m across all three windows
combined. The band that qualifies is essentially always the middle or ±1;
**±3 never fires** and ±2 is marginal. The recorded-band column did its
job: had the definition been fixed at any single band in advance, most of
this population would not exist.

## §2 — M1 REBALANCE (first-passage to the 15m MA; same-bar → stop wins)

| TF | dir | n | /day | med dist | hit% | EV | day-boot 95% |
|---|---|---|---|---|---|---|---|
| 2m | long | 48 | 0.16 | 1.84R | 54.2% | +0.276 | [−0.118,+0.729] |
| 2m | short | 48 | 0.16 | 1.31R | 50.0% | +0.030 | [−0.394,+0.604] |
| 3m | long | 26 | 0.09 | **0.39R** | **92.3%** | **+0.419** | **[+0.095,+0.777] !** |
| 3m | short | 22 | 0.08 | 0.52R | 59.1% | **−0.279** | [−0.560,−0.020] ! |

Two cells "clear" — in opposite directions, on 26 and 22 rows,
uncorrected across ~32 numbers. **Read as base rates, not signals.** The
3m-long cell is a high-hit tiny-target scalp: the MA sits a median 0.39R
away, so 92% arrival buys small wins against full −1R stops. Its MFE table
says the same thing — p50 0.21R, P(≥2R) 3.8%: this trade does not run.

**The POC flag hurts M1, in every cell thick enough to split:**
2m-long +0.369 without the flag vs **−0.035 with it**; 3m-long +0.709 vs
+0.080. Direction is consistent, n is thin (11–14 flagged rows). Recorded
as a base rate: POC stacked on the trigger is, if anything, an
*obstacle marker* for the rebalance trade — coherent with the open-space
finding (BR-53) rather than with the confluence assumption.

## §2 — M2 CONTINUATION (no exit assumed; three targets side by side)

| TF | dir | n | target | med dist | hit% | EV | 95% |
|---|---|---|---|---|---|---|---|
| 2m | long | 101 | vwap_p1 | **−0.24R** | 65.3% | −0.172 | [−0.477,+0.245] |
| | | | vah | 0.65R | 49.5% | −0.209 | [−0.454,+0.073] |
| | | | vwap_p2 | 2.62R | 33.7% | −0.222 | [−0.478,+0.075] |
| 2m | short | 87 | vwap_m1 | −0.34R | 67.8% | **−0.300** | **[−0.452,−0.148]** |
| | | | val | 0.22R | 52.9% | **−0.280** | **[−0.459,−0.098]** |
| | | | vwap_m2 | 1.98R | 33.3% | −0.229 | [−0.483,+0.047] |
| 3m | long | 89 | vwap_p1 | −0.24R | 66.3% | −0.141 | [−0.388,+0.125] |
| | | | vah | 0.60R | 56.2% | −0.159 | [−0.398,+0.092] |
| | | | vwap_p2 | 1.89R | 38.2% | −0.131 | [−0.436,+0.229] |
| 3m | short | 69 | vwap_m1 | −0.14R | **79.7%** | +0.073 | [−0.246,+0.493] |
| | | | val | 0.27R | 71.0% | −0.045 | [−0.281,+0.198] |
| | | | vwap_m2 | 1.79R | 39.1% | +0.185 | [−0.281,+0.726] |

**M2 as a fixed-structural-target construction does not price positively
anywhere.** 10 of 12 target-cells are negative; 2m-short clears zero on the
*negative* side at two of its three targets. Which target the data supports:
**none as a full-close exit** — and the table shows why:

- **The first target is behind the entry.** Median distance to VWAP±1 is
  *negative* (−0.14 to −0.34R): the trigger candle just closed through the
  stack, so the nearest band is at or behind the fill. It "hits" 65–80% of
  the time and pays roughly nothing.
- **The far target (±2) sits ~2R away and arrives ~33–39%** — below the
  50%-at-2R breakeven line against a −1R stop, before cost.
- **The tail is where the population earns** — M2's MFE p90 runs 2.3–3.7R —
  and a fixed structural target truncates exactly that. This is BR-46/49's
  fixed-target lesson reproducing on a fresh population.

The dual currency reads the same: high hit rates, negative R. A
hit-rate-led reading of this table would repeat BR-20.

## §3 — BATTERY (remaining items)

**Clustering-X** — both populations and both mechanisms are nearly flat in
X (2m: 1.05 → 0.83/day across 0.25–2.0W; M1 EV +0.147/+0.153/+0.143/+0.128;
M2 t1-hit 67→62%). No convention sensitivity to speak of at this rarity —
the triggers are too far apart for clustering to matter.

**Cost** — M1 survives all three assumptions (2m: +0.153 → +0.128 → +0.103;
3m: +0.099 → +0.081 → +0.062). M2's first-target read is negative at every
cost level and worsens monotonically.

**Per-session (compact, no verdicts):** NY_AM carries the most flow at both
TFs (0.42/day at 2m) and the strongest M2 t1-hit (77.8%/82.4%); M1's
London cell at 3m is 5 trades — noise. No session verdicts drawn.

## WHAT THIS PASS SAYS

1. **The confluence trigger exists but is rare** — ~1/day at 2m, 0.7/day at
   3m, and the stack is nearly always the MA plus exactly one band (middle
   or ±1). ±2/±3 confluence is a near-empty set under the existing 10pt
   tolerance.
2. **M1 is the only faintly positive corner** (+0.10 to +0.15 pooled,
   cost-robust, X-robust) — but it is a sub-0.2/day, small-target
   population whose only "clearing" cells are 22–26 rows in opposite
   directions. Nothing here approaches the standing books.
3. **M2 with fixed structural targets is refuted as priced** — the
   geometry puts the first target behind the entry and the far target
   beyond the hit rate that would pay for it, while the exit style discards
   the tail the population actually has.
4. **The POC flag is, directionally, a negative marker for M1** — the
   opposite of the confluence intuition, on thin n. Recorded, not acted on.

Nothing is adopted. No holdout exists for any of this — the bar-only venue
is closed, so anything carried forward from this family validates on
forward data only.
