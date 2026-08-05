# PRE-REGISTRATION — LDN-OBK-01 — putting `W` through the remaining §5.11 gaps

**Committed BEFORE the runs.** The depth pass produced exactly one result that is
positive at strict cost in both eras: **`W` (no wall behind) on the `A/S1` continuation
arm**, +0.204R (2025H2, n=37) and +0.478R (2026, n=38), lift +0.734/+0.756.

It is also the only thing standing between this family and a legal kill. So it gets
attacked, not celebrated. Four tests, declared here with their pass conditions.

---

## Test 1 — permutation null, corrected for MY OWN selection (decisive)

**The problem to be honest about.** I tested **32 check×arm cells** and am now reporting
the best one. Quoting a per-cell p-value for the winner of 32 comparisons is the
standard way to fool yourself, and §5.12.4's permutation requirement exists for exactly
this.

**So the null is built around the whole procedure, not the cell.** Under H0 the depth
checks carry no information about outcome. Shuffle the check labels **within arm and
within era** — preserving every n, every era split, and the outcome distribution
untouched — then re-run **the entire 32-cell selection**, and record:

- `max_lift` — the largest era-consistent lift found anywhere in the shuffled table
- `n_pays` — how many shuffled cells survive every era **and** pay at strict cost in both

**Two p-values reported, and the second is the one that counts:**

1. **per-cell p** — fraction of shuffles where *this* cell's lift ≥ +0.734.
2. **family-wise p** — fraction of shuffles where the *whole procedure* produces at least
   one cell that survives every era and pays at strict cost in both. **This is the honest
   one**, because "at least one of 32 cells looked good" is precisely what happened.

**Pass condition, declared:** family-wise **p < 0.05**. At p ≥ 0.05 the `W` result is
consistent with what my own search procedure produces from noise, and the family is
killed on the strongest available grounds — the highest-prior variable class tested at
canon thresholds, with the one survivor failing its own selection-corrected null.

10,000 shuffles, seed `20260805`.

## Test 2 — event-universe sensitivity (§5.11.2)

The trigger was frozen at **first break per side per day**. §5.11.2 requires the
definition be stress-tested; the NY lane found +34% more events only on challenge.

Declared expansion: **all breaks**, not just the first — every re-break of the pre-open
range inside 08:00–10:00 London becomes its own event, with the same entry, stop and
target rules.

**Pass condition:** `W`'s lift stays positive in both eras on the expanded universe. A
gate that only works on the first event of the day is a gate fitted to a sample size,
and the expansion is the cheapest way to find that out. **n≈75 is the weakest thing
about this result and this is the test that addresses it directly.**

## Test 3 — stop-cap arm class (§5.11.3)

Never run here. The NY lane's `cap20` "found the family's best expression and rescued
2024." Declared arms, absolute caps on the trigger-candle stop: **10, 15, 20 points**,
target held at 2R of the *capped* risk.

**No promotion from this test.** The declared default remains the uncapped trigger-candle
stop; a cap becomes the spec only via the §6.0.1 route (PBO < 0.5 on the arm matrix plus
holdout adjudication). This run measures, it does not choose.

## Test 4 — state-conditional re-test (§5.11.4)

> *"Pooled nulls DO NOT close a gate question."*

`W` was found pooled. Re-tested inside declared states, all same-time computable:

- **strategy drawdown vs profit** — cumulative arm P&L to the prior day, sign
- **post-loss** — the immediately preceding trade on this arm was a loser
- **prior-day range regime** — prior session range above/below its trailing 20-day median

**Pass condition:** `W`'s lift stays positive in **every** state where n ≥ 15 a side. A
gate that only fires in one state is a state gate wearing a depth gate's name, and it
would need its own permutation null per §5.12.9.

---

## Order of operations

Test 1 runs **first and alone**. If the family-wise null fails, tests 2–4 are not run
and the kill is written — spending more search on a result that cannot clear its own
selection correction would be inflating the ledger denominator for nothing.

## What none of this can do

**None of these tests can promote `W`.** They can only fail it. Promotion needs the
§6.0.1 route and a holdout look, and no holdout look is spent by any of this. 2023/24
candles, sealed flow months and `depth_london_2023_24` all remain untouched.

## Artifacts

`scripts/london_W_scrutiny.py`, `output/london_W_scrutiny.md`, trials to
`output/trial_ledger.parquet`, `research/FUNNEL.md` refreshed.
