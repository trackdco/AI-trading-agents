# LDN-OBK-01 — `W` permutation null, selection-corrected

Authorised by `docs/PREREG-london-W-scrutiny.md`. 10,000 shuffles, seed `20260805`.
Check labels permuted WITHIN arm and era, so every n, every era split and the
outcome distribution are preserved exactly. Each shuffle re-runs the **entire**
32-cell selection, because selecting the best of 32 is what actually happened.

## Result

| quantity | observed | null | p |
|---|---:|---|---:|
| max era-consistent lift | **+0.734** | median +0.299, 95th pct +0.598 | 0.0158 |
| cells surviving every era AND paying at strict cost | **1** | mean 0.53, ≥1 in 42.1% of shuffles | **0.4209** |

**Declared pass condition: family-wise p < 0.05. Result: FAIL (p = 0.4209).**

## Read

**My own search procedure produces a result this good from shuffled labels
in 42.1% of runs.** The `W` finding is therefore consistent with
selection noise across 32 cells, and the per-cell number was never the
right thing to quote.

Per the prereg, tests 2-4 are NOT run — spending more search on a result
that cannot clear its own selection correction only inflates the ledger
denominator. **The kill is written.**

## The two statistics disagree, and the declared one governs

The lift *magnitude* clears its own family-wise bar: +0.734 sits
above 98.4% of shuffled maxima (p=0.0158). The
*existence* of a cell that survives every era and pays does not: that
happens in 42.1% of shuffles.

**They measure different claims, and the declared test matches the claim I
actually made.** The headline reported out of the depth pass was *"exactly
one survivor pays at strict cost in both eras"* — an existence claim about
the output of a 32-cell search. That is the thing the family-wise null
tests, and it fails. The magnitude statistic would support a different
headline (*"the lift is unusually large"*) that I did not lead with.

**Switching to the statistic that passes, after seeing which one passes, is
the exact procedure this framework exists to prevent.** So it is not being
switched. The magnitude result is recorded here because it is real
information and someone may want it later — but re-opening `W` on that
basis requires a NEW prereg declaring the magnitude criterion in advance,
on an independent sample. It cannot be done by re-reading this table.
