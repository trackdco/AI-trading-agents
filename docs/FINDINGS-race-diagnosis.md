# FINDINGS — WINNER/LOSER DIAGNOSTIC + ENTRY-TIMING GAP (episode census)

2026-08-08. Report-only, fit-only, no holdout. Population: the corrected
(episode-M1) race census — the family's declared null, 3,153 fights /
10.76 per day. Day-clustered throughout (seed 20260807, 2000 draws).
Tools: `scripts/race_diagnose.py`, `scripts/race_timing.py` (committed
before the runs, `29c65f46`).

---

# PART 1 — WINNER/LOSER DIAGNOSTIC

**Law-2 classification declared in the script header before any outcome
was read**: `risk`, `w15`, `tf_won` are MECHANICAL (R-denominator-
coupled) and screened — every split carries a points-based control
(out × risk) beside its R-based read, and `tf_won` additionally gets a
within-risk-tercile control. Decision-time behavioral candidates:
`n_aff`, the eight per-structure affirmation flags, `n_tie`
(simultaneous-TF closes), `disp_abs_w`, `epi_max_w` (M1), `tmin`
(minutes into the window). Outcome: M1 → 15m-MA race; M2/M3 → near
target. Realized-R quintiles within each (window × mechanism) cell;
directions pooled within cells for power (flagged); windows and
mechanisms never pooled.

**Multiplicity, stated first: ~110 comparisons, no declared bar — at
95% expect ~5–6 false clears per side. Nine cleared.** The excess is
modest; what makes the result readable is not any single CI but the
cross-cell repetition of one theme.

## THE THEME: CONFLUENCE LOAD IS ANTI-PREDICTIVE

- **`n_aff` — more affirming structures at the zone → WORSE.** Clears
  negative in LONDON M3 (−0.384 [−0.696,−0.083]) and NY_AM M3 (−0.353
  [−0.621,−0.121]), and the winner-mean sits BELOW the loser-mean in
  **7 of 9 cells** (e.g. NY_PRE M1 winners 0.86 vs losers 1.18; NY_AM
  M1 0.97 vs 1.20). Points-based controls agree everywhere — this is
  not the denominator.
- **`disp_abs_w` — the further the trigger open sits from the 15m MA,
  the worse the continuation trade.** Clears negative in LONDON M2
  (−0.340), NY_PRE M3 (−0.547), NY_AM M3 (−0.356), points controls
  agreeing; the same sign in most other continuation cells. Chasing
  distance from the mean is the recurring loser shape.
- **Below-side structure flags**: `aff_val` clears negative in NY_PRE
  M1 (−0.612) and NY_AM M1 (−0.547); `aff_vwap_m1` in NY_PRE M2
  (−0.540) and NY_AM M1 (−0.553) — with points-basis agreement of
  −10 to −14pt. Thin uncorrected cells, but four clears in one
  direction across two windows.
- **No behavioral variable positive-clears in any cell.** As with every
  selection study this programme has run (closeloc included), the
  decision-time information marks trades to AVOID; nothing marks trades
  to chase.

**The Law-2 screen's results**: `risk`'s single clear (NY_PRE M3
+0.532) is screened by declaration. `tf_won` mostly dissolves inside
risk terciles; the one directional survivor is **NY_AM M3 taken via the
1m (−0.498, negative in all three risk terciles)** — recorded,
uncorrected, one cell.

**Bearing on the declared grammar (recorded, not acted on):** the
census's own data says heavier confluence at the zone degrades the
trade — which sits in tension with the ≥2-affirmation gate on the 1m
(a conviction gate keyed to a variable whose census direction is
negative) and coheres with BR-53/BR-74's obstacle logic and with the
trade check's T4 discrepancy (the trader's "double" counted the MA
itself, not two stacked structures). Any change to the gate is the
trader's declaration.

---

# PART 2 — THE ENTRY-TIMING GAP, whole population

**Question**: for every fight, what would entering at the FIRST 1m
close through the winning TF's (developing) MA inside the trigger
candle — instead of waiting for the full candle close — have done to
the fill and the resulting R.

**Two declared accounting choices flatter the early leg, and the
numbers below must be read as an UPPER BOUND on the recoverable gap:**

1. **The early leg keeps the actual stop** (full-candle extreme ± 1
   tick) — look-ahead at the early fill time. Because that stop sits
   one tick beyond the candle's final extreme, the early trade can
   never be stopped inside the trigger candle's remainder; a live
   early-enterer with a developing-extreme stop could be.
2. **182 raw rows (~2.7%) where the early fill was already through the
   final stop were dropped** as infeasible — these are precisely the
   early leg's worst continuation candles, excluded from the pairing.

With that framing:

| window | mech | out ACT → EARLY | mean ΔR [95% CI] |
|---|---|---|---|
| LONDON | M1 | −0.077 → +0.026 | **+0.103 [+0.053,+0.158]** |
| LONDON | M2 | −0.139 → +0.086 | **+0.225 [+0.127,+0.336]** |
| LONDON | M3 | −0.070 → +0.160 | **+0.231 [+0.149,+0.325]** |
| NY_PRE | M1 | −0.036 → +0.098 | **+0.134 [+0.077,+0.207]** |
| NY_PRE | M2 | −0.096 → +0.012 | **+0.107 [+0.030,+0.196]** |
| NY_PRE | M3 | −0.089 → +0.118 | **+0.207 [+0.102,+0.345]** |
| NY_AM | M1 | +0.005 → +0.120 | **+0.115 [+0.063,+0.178]** |
| NY_AM | M2 | −0.033 → +0.203 | **+0.236 [+0.163,+0.320]** |
| NY_AM | M3 | −0.181 → +0.046 | **+0.227 [+0.148,+0.306]** |

**Every one of the nine cells clears positive** — the only effect on
this family that has done that. Whole-book: **−0.069 → +0.092, mean ΔR
+0.161** under the favorable accounting.

**The structure of the gap says it is real and mechanical, not one
lucky tail:**

- **Monotone in trigger-candle length**: 1m-won fights ΔR +0.018
  [+0.001,+0.036] (just close-print vs next-open), 2m +0.186, 3m
  **+0.335 [+0.249,+0.427]**. More candle to wait through = more paid
  for confirmation. This is the cleanest possible signature of a
  waiting cost.
- **The median fight gains ~nothing** (ΔR med +0.000; median fill gain
  +0.25pt): in most fights the 1m cross only appears in the candle's
  final minute. The mean is carried by the minority of momentum candles
  where the cross printed early and the candle kept running — fill
  gains of p90 +3 to +17pt (NY_AM M2/M3 the largest).
- **Outcome flips are rare** (1.3% loser→winner, 1.2% winner→loser):
  the exit paths barely change. The gain is almost entirely fill price
  plus the smaller stop distance — which is economically real under
  stop-distance sizing, not an artifact of R arithmetic.

## WHAT THE TWO PARTS SAY TOGETHER

The diagnosis found no positive selector in the decision-time columns —
and the timing measurement found that **the single largest lever on
this family is not selection at all: it is the cost of waiting for the
candle to close.** Under favorable accounting, that cost alone spans
the entire gap between the mechanized book (−0.07) and breakeven-plus
(+0.09) — consistent with the trader's fills being structurally earlier
than the construction's (BR-85's T1: ~1.8R better on one measured
fill). The honest next construction, if this is pursued, is a DECLARED
early-entry trigger — enter on the first 1m cross with a
developing-extreme stop, no look-ahead — priced as its own census
against this one as the null. That is a new declaration, not made here.

Standing: fit-only, no holdout, report-only, nothing adopted, nulls
published.
