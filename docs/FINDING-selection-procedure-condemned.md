# FINDING — PBO 0.891: the *selection procedure* is condemned, not the candidates

**For Angus.** Reproduce: `python -m scripts.backfill_trial_series`, then
`pbo_cscv(load_matrix(), n_blocks=16)`.

This is the first time PBO has been computable on the London programme. The artifact it
needed — a T × N matrix of per-arm day series — did not exist until now
(`docs/CONFORMANCE-trial-ledger-vs-2.4.md`, gap 2).

---

## The number

**PBO = 0.891**, CSCV over 13 arms × 293 days, S = 16 blocks.

§2.4's declared reading: *"PBO ≥ 0.50 condemns the selection procedure, not the candidate
— the search design gets the tombstone, and re-running it with a new candidate is not a
fix."*

**In plain terms: if you had chosen the best-looking arm in-sample, it would have landed in
the bottom half out-of-sample 89% of the time.** Worse than a coin flip — the in-sample
winner is systematically the out-of-sample loser.

## Why it is that high, and why it is not a bug

Two measured facts explain it.

**The arms are near-duplicates.** On days when any two arms both fire, their outcomes
correlate at a **median |ρ| of 0.900**, with 88% of pairs above 0.5. That is structural,
not coincidental: LDN-DEF-01's three measures filter the *same* trap events, and
LDN-FLOW-01's four measures filter trap and vwap events. They are re-readings of one price
move, not different bets.

**The differences between them are noise.** Every arm graded FAIL, INCONCLUSIVE or
no-effect. When arms share a series and differ only by noise, whichever led in-sample did so
by catching a wobble that then reverses — which drives PBO above 0.5 rather than toward it.

## What this condemns — and what it does not

**Condemned:** "run several variants of an idea and promote the one that scores best."
On a pool like this that procedure is worse than useless.

**Not condemned:** the process we actually ran. Every arm had a pre-registered decision rule
and was judged against it; none was promoted for out-scoring its siblings. **PBO measures
the selection rule we deliberately did not use.**

That is worth stating plainly because it retroactively validates a call made in
`VERDICT-LDN-FLOW-01.md` §8:

> *"The threshold-free design is what made this cheap. Testing four measures by rank
> correlation cost 8 trials. The same four measures with five thresholds each would have
> cost 40, and would have found a 'winner' — TRAPPED in 2026 was sitting right there."*

PBO 0.891 is the measurement behind that intuition. Picking the winner would have been
wrong roughly nine times in ten.

## Where this bites next

1. **Pat's Obsidian green/red sorter.** A sorter's whole job is to rank and promote. On a
   pool of correlated variants that is exactly the condemned procedure. It must promote on
   pre-registered per-candidate rules, never on "highest score wins," and it must read the
   deflation bar from the merged ledger.
2. **The NY programme.** Same discipline from day one. Testing eight variants of one NY idea
   and shipping the best is the condemned procedure wearing a new session's name.
3. **Any future "confluence" work.** The literature sweep already priced a best-3-of-8
   search at ~500 effective looks. PBO 0.891 is the empirical version of the same warning.

## Second finding — effective-N is not estimable here, so nominal N stands

§2.4 mandates deflating nominal N to effective independent trials. With series now on disk,
clustering on realised co-movement gives **N_eff = 2** from 13 arms (34 ledger rows).

**That does not license a lower bar.** The canon requires V — the cross-sectional variance
of trial statistics — to be computed *across cluster representatives*. Two representatives
cannot support a variance estimate. Applying N_eff = 2 while keeping V from all 34 arms
mixes a clustered N with an unclustered V and drops the bar from **+0.1724 to +0.0422**,
which would flip the programme's best result (+0.1608) from fail to pass.

**The honest position: at N_eff = 2 the False Strategy Theorem does not apply, and the
nominal-N bar remains operative.** `n_effective()` reports the number with that warning
attached; nothing may be promoted on it.

## The uncomfortable read on the programme

N_eff = 2 says our nine candidates were **not** nine independent shots. They were roughly
two genuinely independent ideas — a level/mean-reversion family and a flow-reading family —
examined 34 ways on heavily overlapping event sets.

So "nine candidates, no survivors" overstates the breadth of what was searched. A fairer
statement is **"two ideas were tested thoroughly and neither worked."** That is still real
knowledge, and it is still worth what it cost. But it means the next round should buy
*genuinely different* ideas rather than more variations — new event types, new sessions,
new information families — because variations of a dead idea are almost free to generate
and almost worthless to test.

## What this does not establish

- PBO is a property of the **pool measured**, not a universal constant. A pool of genuinely
  independent strategies would score far lower.
- 8 of 34 ledger rows (LDN-INV-01, LDN-SWP-01) have no rerunnable census on this branch and
  contribute no series. They are counted in N but absent from the matrix and the clustering.
- The clustering uses simple correlation-threshold linkage, not López de Prado's ONC. It is
  the right *kind* of correction; it is not the specified algorithm.
- Days on which an arm did not fire are zero-filled, the standard CSCV construction. That
  *understates* pairwise correlation here — the co-firing figure (0.900) is the higher one.
