# FINDINGS — E-SERIES: level-family census, break arm, sweep re-entry (2026-08-07)

**The direction change was right, and the result is bigger than the
selection layer ever produced.** Running the same fight grammar at other
loci found two trigger populations whose UNSELECTED base rates beat the
incumbent's *selected* book — and they are the two loci the trader's own
narration cited most.

Everything here is declared-in-advance work: loci, run order, publication
rule, and the follow-up bar were committed in
`DECLARATIONS-level-family-census.md` (commit 58a03bb2) before any census
number existed. Fit span only; both holdout looks remain unspent.

---

## 0. Harness calibration (the control ran first, as declared)

The `bbma15` control locus reproduces the M-TABLE **bit-for-bit** — keys,
entry, stop, risk, out_ship and mfe_r all identical on three test days,
and 3,111 reject / 1,605 break triggers matching exactly. Its X=0.25W row
reproduces A1's sensitivity curve to three decimals. The harness is the
incumbent grammar with the level swapped and nothing else.

**Entry-price gate: PASS on all seven loci.** This mattered here more than
anywhere: VWAP accumulates the current bar's price×volume and the
developing profile accumulates the current bar's volume, so a careless
as-of alignment would let a fill price be set by the bar it fills in — the
exact defect class that killed the canon. The first gate run FAILED the
VWAP family; the cause was the *gate* locating the fill bar by scanning for
the first bar whose range contains the entry price, which for a drifting
level can land on a pre-fill bar whose close legitimately moves the level.
The builder now records the true fill bar and the gate perturbs exactly
that one — a stricter test, not a weaker one. Independently confirmed:
151/151 break fills equal the locus level recomputed from scratch as-of the
close of the bar before the fill.

---

## E1 — LEVEL-FAMILY CENSUS

33,461 triggers, 292 fit days, 7 loci × 2 arms. No selection, no cuts, no
filters. **Verdict at the declared bar** (EV>0 with day-boot CI clear of
zero in BOTH eras at X=0.5W, and sign positive at ≥3 of the four X):

| arm | locus | EV/fight | fights | verdict |
|---|---|---|---|---|
| reject | **bbma15** | +0.149 | 1,830 | **FOLLOW-UP EARNED** (the incumbent) |
| reject | val | +0.132 | 1,349 | park |
| reject | vwap_m1 | +0.122 | 1,322 | park |
| reject | vwap | +0.111 | 1,464 | park |
| reject | vwap_p1 | +0.110 | 1,493 | park |
| reject | poc | +0.084 | 2,195 | park |
| reject | vah | +0.042 | 1,439 | park |
| break | **vwap_m1** | **+0.248** | 972 | **FOLLOW-UP EARNED** |
| break | **val** | **+0.234** | 907 | **FOLLOW-UP EARNED** |
| break | bbma15 | +0.105 | 1,283 | park |
| break | poc | +0.094 | 1,793 | park |
| break | vwap | +0.096 | 1,047 | park |
| break | vah | +0.068 | 985 | park |
| break | vwap_p1 | +0.054 | 1,121 | park |

### The headline

**Break-of-VAL and break-of-VWAP−1 run +0.234R and +0.248R per fight with
ZERO selection.** The incumbent needed S1 — a cut that removes 54% of
fights — to get from +0.149R to +0.257R. These two match that *before any
selection layer exists at all*.

They are also the more robust books. `vwap_m1` break clears both eras at
**all four X values** (+0.236 / +0.248 / +0.276 / +0.278, rising with X);
`val` break clears both eras at three of four and is positive at all four
(+0.242 / +0.234 / +0.247 / +0.261). The incumbent reject book clears both
eras at X=0.5W **only** (A1's qualifier on BR-9). So the new loci are
*less* convention-dependent than the thing they beat.

### The union book — the decision-relevant number

VAL and VWAP−1 fire on the same (day, minute) only 42% of the time, so
they are largely distinct events, not one signal in two costumes:

```
val break        907 fights  3.11/day  +0.234R  win 34.7%
vwap_m1 break    972 fights  3.33/day  +0.248R  win 36.6%
UNION          1,506 fights  5.16/day  +0.230R [+0.150,+0.310]
   H2-2025  +0.223 [+0.112,+0.328] n=831
   H1-2026  +0.238 [+0.121,+0.358] n=675
   at $150/trade: +$194/day
```

Against the incumbent reject book (+0.149R, 6.27/day, ~$117/day) that is
**+55% per trade at 82% of the frequency**, with both eras clear and no
selection spent.

### Corroboration from outside the model

The two winners are the two loci the narration cited most: VAL ("Setups 1
and 3 and the setup I rejected all keyed off VAL") and VWAP−1 ("Setup 1's
was the 2m BB MA stacked on VWAP−1", "Setup 6's target was VWAP−1"). This
is an out-of-model prior — the loci were scoped from the trading before any
number existed — which substantially blunts the multiplicity concern below.

Note also that the two WEAKEST loci are `vah` (+0.042 reject) and
`vwap_p1` (+0.054 break) — precisely the two included by declared symmetry
rather than by narration. The trader's edge lives at the lower value-area
edge and the lower band, not their upper mirrors.

### Caveats, stated plainly

1. **Multiplicity.** 14 locus×arm cells were tested and 3 cleared. The bar
   was declared in advance and requires both eras independently, which is
   stringent, and the X-stability (4/4 for vwap_m1) is corroborating —
   but 3 of 14 is not the same evidential weight as a single
   pre-registered test. **These are fit-side leads, not confirmed edges.**
2. **Direction skew.** Both winners are short-heavy — val 79% short,
   vwap_m1 69% short — which is mechanical (VAL and VWAP−1 are *lower*
   levels, so breaking them is downward) but means the significance rests
   on the short side: val short +0.237 [+0.125,+0.352] vs long +0.223
   [−0.021,+0.470] (n=189, underpowered). A span containing more downside
   than upside would flatter this. **Untested against a bull-only regime.**
3. **Session breadth is good** — the union book is clear of zero in asia
   (+0.235), london (+0.282), ny_pre (+0.310) and ny_rth_am (+0.272), and
   flat only in ny_pm (+0.050). Not a single-session artifact.
4. Fit-only. Nothing here has met a holdout.

---

## E2 — BREAK ARM, unparked

Measured cleanly for the first time since the row-existence fix, at the
incumbent locus:

```
break = 34% of the population | P(ever-retest) 93.5% [92.4,94.6]
never-retested 6.5% (n=104) — they escape without offering the entry
executable break book, X=0.5W: +0.105R, 4.39/day
   H2-2025 +0.081 [-0.043,+0.201]   H1-2026 +0.132 [+0.003,+0.253]
positive at all four X; H2-2025 CI never clears zero -> FAILS the BR-9 bar
stop width p50 0.221W (vs reject 0.188W) | win rate 35.2% | MFE p90 6.08
```

**At the incumbent locus the break arm does not clear its bar.** But E1
shows that was a LOCUS problem, not an ARM problem: move the same arm to
VAL or VWAP−1 and it clears both eras comfortably. The "different bets"
thesis is supported in the strongest possible way — the break arm's edge
was invisible because it was being measured at the wrong level.

The combined both-arm book at the incumbent locus is worth recording
because it answers the frequency question directly:

```
reject only   1,830 fights  6.29/day  +0.149 [+0.076,+0.224]  both eras clear
break only    1,283 fights  4.41/day  +0.105 [+0.018,+0.194]  H2 not clear
COMBINED      3,113 fights 10.70/day  +0.131 [+0.074,+0.191]
   H2-2025 +0.115 [+0.030,+0.203]   H1-2026 +0.150 [+0.064,+0.240]  both clear
   at $150/trade: +$210/day (vs $117 reject-only)
```

Combining arms nearly doubles daily throughput at the same per-trade risk
while keeping both-era significance — "frequency without size" is real.
Caveat: 72% of break fights share an episode with a reject fight, so
exposure within an episode is correlated; they add trades, not independent
bets, and the median day carries 10 trades (max 22), which has execution
implications the current spec does not address.

**The break-arm candidate set is deliberately NOT run yet.** Per the same
logic that motivated this direction change, running cuts on a population
whose base rate fails its bar is polishing a marginal foundation. The
candidate set should be declared against the loci that DID clear
(VAL / VWAP−1 break), not against bbma15.

---

## E3 — SWEEP-CONDITIONED RE-ENTRY: MISS, plus a specification failure

Law 7 was published before measurement, as declared:

```
book A: n_A=1,830 fights, E=+0.149R. Re-entries are ADDED.
required mu_s for +0.02R of book:  n_s=100 -> +0.535R | 200 -> +0.352R
                                   400 -> +0.261R | 600 -> +0.230R
ceiling: 998 stopped-then-retriggered pairs exist; the sweep can only shrink it
```

Result under the declared definition (8-bar lookback, 4-tick penetration,
3-bar reclaim):

```
qualifying re-entries n_s = 119 of 998 (12%)   mu_s = -0.143R
day-boot 95% CI [-0.376,+0.107] — includes zero
non-sweep re-entries: n=879, mu=-0.168R
book with sweep re-entries added: +0.149 -> +0.132R  (-0.018)
half 1 -0.329 [-0.599,-0.024] | half 2 +0.105 [-0.242,+0.490]  (opposite signs)
```

**MISS, recorded as declared. No redefinition.** The sweep filter barely
separates from no-filter (−0.143 vs −0.168) — it is not that swept
re-entries are bad, it is that the whole re-entry population is bad and
this filter does not fix it.

**But there is a specification failure that matters more than the result.**
The trader's own reference example — the London fight of 3 Jun 2026, where
the 04:45 attempt stopped (−1.06R) and the 05:00 re-entry won (+2.94R) —
**does not qualify under the declared definition**. The 8-bar reference low
was 30,679.75; the bars between the stop and the re-entry only reached
30,707. The reference extreme was never penetrated.

That is an outcome-independent fact about the definition (it compares the
rule to a price path, not to a P&L), so stating it is not a rescue. What it
means: **the declared rule is not the trader's concept**, so E3 tested a
strawman, not the grammar. The natural alternative reading — that the
"sweep" IS the stop-out itself (price takes out the prior attempt's low,
then reclaims) — is a materially different rule.

**I have deliberately not measured that alternative.** Doing so after
seeing this result would be exactly the rescue the protocol forbids. It
needs a fresh blind declaration justified from the trading. The one
question that would settle it: *when you say "after the low sweep", do you
mean price swept the low your previous stop was sitting under, or a
separate prior swing low?*

---

## BASE-RATES.md updates (all published, nulls included, as declared)

BR-11 through BR-14 added: the level-family census base rates for all seven
loci on both arms, the break-arm-at-incumbent-locus null, the combined
both-arm book, and the sweep-re-entry null.

## What this changes about the programme

The trigger-population hypothesis is **supported**. Selection at the
incumbent locus was near-exhausted (1 survivor from 18×2 candidates);
changing the locus produced two books that beat the selected incumbent
before any selection is applied. The natural next step is NOT more cuts —
it is to re-run the E-series discipline on the winners: a fresh
pre-registration of the VAL / VWAP−1 break population, and only then a
selection layer on top.

**Nothing has touched a holdout.** The bar-only venue (23 months) is the
natural confirmation ground for VAL/VWAP−1 break, since both loci are pure
OHLC+volume constructions requiring no flow tape — which means, unlike S1,
**this lead is confirmable at ±4pp rather than ±10pp.** That is the single
most valuable property of this result and it should govern what gets
declared next.
