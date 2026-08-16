# VERDICT — THE CUT STUDY (Phase 3, run 2026-08-07)

First study in the programme to REMOVE trades and measure the remaining
book. Design, cut rules, bars: SPEC-cut-study.md (all committed before the
corresponding readouts). Books are executable (first trigger per structural
fight), arm-separated, out_ship exit, $160 risk/trade for the account
score.

## The result

```
VERDICT   ONE cut confirmed of 18 candidates x 2 arms: S1 — REJECT arm,
          remove fights whose decision-bar delta DISAGREES with the trade
          direction (flowconf==0).
S1        Half 1: lift +0.053R, score 56.9->72.1%. Half 2 (pre-registered,
          unchanged): lift +0.175R, score 71.1->95.3% — CONFIRMED, stronger
          out of sample within fit.
FULL FIT  book +0.149R/fight -> +0.257R/fight after cut; removes 54.5% of
          fights (removed bin +0.060R); ~2.9 fights/day remain.
GATES     G1 max single-day contribution 6.6% (bar 25%) PASS
          G2 LODO by month 14/14 folds positive (+0.089..+0.134) — ADOPT bar
          G3 dual currency: win rate 34.4%->38.3% (+4.0pp) — both
          currencies agree. Eras: +0.081 (H2-2025) / +0.136 (H1-2026).
STATUS    ADOPTED ON FIT. Holdout: NOT LOOKED. flowconf is a flow-family
          claim -> D3 (one batched look, declared resolution). Spending the
          flow family's single look is a human sequencing decision, not
          this study's.
```

## What died, and how

9 of 10 pre-registered survivors failed Half 2 exactly as the split-half
was built to force:

- break volx<Q1 — Half 1's strongest cut (+0.116 lift, removed bin
  −0.215R, score 88.6%) — Half 2 lift +0.022, removed bin 0.000R. Fluke.
- break confluence>=3 (the Phase-2-motivated, prior-full-fit-read flagged
  candidate) — Half 2 lift −0.013. The flag was warranted.
- reject volx, reject d30_conf, reject ny_pm, break thru_delta/d15/
  cvd_slope30/closeloc — all below the +0.05R bar on Half 2, several
  negative.
- Mirror illustration, recorded not advanced: reject closeloc<Q1 FAILED
  Half 1 (+0.034) and would have shone on Half 2 (+0.148, 96.2%) —
  advancing it would be sign-shopping across halves. It is dead unless
  independently re-declared blind.
- delta_z: declared low=bad direction INVERTED on both arms in Half 1
  (the extreme-delta bin is where the money is). Recorded miss; no flip.

The break book itself is half-fragile (EV +0.130 -> +0.076, score 63.7% ->
44.5% across halves): NO break-arm cut confirmed, and any break-arm claim
must first explain the book's own instability.

## Law 8 note

S1 is a gate, not a weight — the lift converts ~1:1 into the book. The
+0.107R full-fit lift against the +0.05R feasibility bar makes it the
first selection variable in the programme's history to clear
effect-size arithmetic, split-half confirmation, and all three gates on
one population.

## Standing cautions

- flowconf's disagree bin holds 54.5% of fights — the cut halves
  frequency. At ~2.9 fights/day the account-score improved anyway (95.3%
  on Half 2), but the A-1 assembly must re-verify cadence in the desk
  window specifically.
- The score constants ($160 risk, $2k trailing DD, +$3k target, $150
  winning day, 5 days) are the house Lucid mechanics; the HTF book's
  live sizing is unset — score RANKS cuts, it does not promise pass
  rates.
- Sealed holdout remains unread; both family looks (D2 bar-only, D3 flow)
  remain unspent.
