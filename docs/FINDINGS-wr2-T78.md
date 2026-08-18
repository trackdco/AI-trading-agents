# FINDINGS — `wr2`, the 0.4.12 / T78 revalidation

**wr2's adjudication is COMPLETE: all 76 candidates are in the book.** The T78 numbers below
are final. The SCOREBOARD is not - 13 fills exist and 5 have exits written; the other 8 still
need their manage chains, several of which are blocked on chart frames no earlier run captured.
Everything below is traceable to a book row; nothing is asserted from memory.

---

## 1. T78 IS NOT PRODUCING LADDERS — 13 of 15 takes fail it

The full audit (`output/analysis/t78check.py`, run against the live book):

    T78 audit wr2: 20 take(s) adjudicated, 18 defect(s)     <- FINAL, all 76 candidates adjudicated
      11 x SINGLE_TARGET       - no TP2 named at all
       7 x TP2_TOO_CLOSE       - TP2 inside the ~1R spacing floor

**Only two of twenty takes carry a correctly-spaced ladder** — `06-22 L2` (TP2 1.28R past TP1)
and `06-25 P2` (three rungs, TP2 1.68R past TP1). **That is 10%.**

For contrast, wr1 under 0.4.11 produced 2 ladders out of 7 takes (29%). On the headline rate
**0.4.12 is no better than the contract it replaced**, on a sample nearly three times larger.
T78 changed the contract text; it did not change the output.

### The spacing rule is inert
Every TP2_TOO_CLOSE gap in the run: **0.34, 0.38, 0.40, 0.41, 0.46, 0.58, 0.67R.**
**Not one has cleared the 1.0R floor.** Seven for seven, clustered well below it, none even
close. That is not a judgement call going marginally wrong seven times — it says the trigger is
**naming the next adjacent structure and stopping**, without measuring the gap at all. T78
rule 2 ("at least ~1R past it") and rule 3 ("keep walking the level list until one clears the
spacing") are being read as "name a second level", with the distance test dropped entirely.

**If only one thing is changed before the next run, it should be this**: the spacing test needs
to be something the trigger must show its work on — a stated gap in R between TP1 and TP2 — not
a qualifier inside a sentence.

The failures are not one thing, and the breakdown matters more than the headline.

**(a) The fixed-R TP1 fallback swallows TP2.** — `2026-06-22 A3`
The agent walked T27's TP1 preference order correctly, found nothing structural in 1.0R–2.5R,
and fell through to rule 3's **fixed 1.5R** for TP1, which is legal. It then named no TP2 at
all. T78 forbids exactly this on both halves: *"the fixed-1.5R fallback exists for TP1 only…
a fixed-R number is never TP2"* and *"keep walking the level list… There is always structure
further out; name it."* The agent's own `stop_rationale` names a further level it could have
used (weekly/session low 29616.5). **Once the trigger leaves the structure list to compute a
TP1, it appears to stop walking that list, and the TP2 requirement goes with it.**

**(b) Wide stops compress the ladder into one R band.** — `2026-06-21 A2`, `2026-06-23 P2`,
`2026-06-24 L1`
Two rungs named, both real levels, but TP2 lands 0.40R / 0.41R / 0.58R past TP1 against T78's
"~1R past it". The common factor is a large R: 93pt, 34pt, 24pt respectively, set by a stop
placed correctly per T75 beyond a whole rejected cluster. A correct T75 stop and a correct T78
spacing rule can pull against each other, and nothing in either contract arbitrates.

**(c) TP1 selection consumes the thesis's furthest target.** — `2026-06-24 A4`
The clearest trigger-side failure, because the thesis was not at fault. The accommodated thesis
handed this trigger TWO targets (weekly_poc 29727 = 1.31R, day_fib_0.5 29779.75 = 1.80R). The
trigger chose the **further** one as TP1 and had nothing left above it. The ladder was consumed
on the first rung.

**(d) UPSTREAM: a thin or scope-capped thesis leaves nothing to build a second rung from.**
This is the largest single contributor, and there are **two independent same-candidate A/B
pairs** proving it — same tape, same minute, same T78 text, only the thesis different:

| candidate | under the stale thesis | under the accommodated thesis |
|---|---|---|
| `2026-06-23 A5` @10:26 | **1 target**, agent: *"not beyond, since that zone is where thesis wants shorts back"* | **3 targets** |
| `2026-06-23 A6` @10:30 | **1 target** (*"sub-1.5R at the cluster's near edge"*) | **3 targets** |

Corroborating: `2026-06-22`'s NY_AM thesis named exactly one target, and **both** takes under it
came out single-target. A thesis that scopes a counter-trade to a capped destination leaves the
trigger nothing to name, and **T78 cannot conjure structure the thesis has ruled out.**

### The contract tension worth ruling on
On counter-trend fades the thesis licenses as *temporary, never a bias flip*, naming a TP2 would
push the runner past the point the thesis wants the counter-move to end. Seen twice
(`2026-06-23 A5` first pass, `2026-06-21 A6`). T78 says *"there is always structure further
out; name it"*; the thesis says the move ends here. **Both cannot be satisfied.** No orchestrator
ruling was invented — logged and left for him.

---

## 2. Four escalations, all accommodated, all the same species

| day | candidate | the complaint |
|---|---|---|
| 06-21 | A4 @09:48 | a LATCHED rebalance gate that never printed while the tape moved past its framing |
| 06-23 | A3 @09:54 | a scoped counter-trade ceiling the tape had already passed |
| 06-24 | A2 @10:12 | a chop-range frame sitting ~450pt above price after a session crash |
| 06-25 | A2 @09:36 | a waiting_for gate one candle behind the tape |

**Not one was a disagreement about direction.** Every one is a thesis *condition* going stale
inside its own window while the bias stayed defensible, and in every case the trigger passed and
escalated rather than trading against it. That is the machinery working exactly as designed — but
four in one window across four days points at the **latched-condition grammar** itself, not at
four unlucky days.

Each accommodation cost real work: on 06-23, one take, its fill and a management action were all
withdrawn. All are retained in the book flagged `SUPERSEDED_BY_ESCALATION` / `VOID`.

---

## 2b. A counter-example the reviewer should weigh — `06-22 A4`

The single-target defect does not always cost. On `06-22 A4` the runner was banked 50% at TP1,
moved to breakeven, and then **price fell a further 238 points in its favour** — roughly 3R of
unbanked move — with **no target to close it on**. The breakeven stop was never touched over a
20-hour horizon. It had to be **marked out administratively at the cash close** for +2.10R.

Read that carefully: the missing rung did not lose money here, it gained. But it gained *by
accident*. No decision in the system closed that trade; the orchestrator did, by fiat, because
the plan had run out of instructions. That is not a repeatable process, and it is the strongest
argument for T78 in the whole book — not because the ladder would have made more, but because
without one the system had **nothing to say** about a position it was still holding.

## 3. Management is adding, not subtracting

On wr2's closed trades so far: **as-run +3.02R against an unmanaged full-target hold of +1.68R.**
Two of the five would have been full losers held to their final rung (`06-23 P2`, `06-25 P2`);
management turned both positive. This cuts against the intuition behind "hold half to a further
target" and deserves weight at week level.

The **75/25 counterfactual** is now priced mechanically (`output/analysis/score.py`) per his
ruling — same fills, same actions, only the first partial's fraction changed. On the two trades
that actually banked a partial: as-run **+2.84R** vs 75/25 **+3.12R**. **Two trades. That is the
mechanism, not a verdict**, and the tool says so in its own output.

One caveat the reviewer must not miss: `06-25 P2` had the best-spaced ladder in the run (three
rungs, TP2 1.68R past TP1) and was **flattened by T51 at the cash-open deadline before TP1 ever
printed**. Its +1.09R says nothing about whether the ladder works.

---

## 4. Orchestrator defects found (logged, not fixed mid-run)

- **Manage schedule is not recomputed when a trail moves the stop.** A tightened stop can resolve
  the position earlier than the schedule assumes, and the orchestrator keeps calling. Caught on
  `06-23 P2` — not by a check of mine, but by the manager refusing an incoherent briefing
  ("a long cannot have its stop above price"). Same failure wr1 hit on 06-21 L1.
- **Scheduler labels a call `tp1_reached` before the 2m grid confirms the print.** Seen twice
  (`06-22 L2` @03:45, `06-25 P2` @09:01). Both managers caught it and read actual price instead.
- **`stalecheck.py` has no thesis-version check.** It compares briefing *position* state against
  the book. A candidate adjudicated against a superseded thesis slips through; `06-23 A6` was
  caught only by reading the agent's reasoning.
- **Four agent verdicts were returned and never written to the book.** Found by
  `output/analysis/complete.py`, a want-vs-have sweep over the deterministic candidate-id map.
  Prose tracking missed them because they arrive in notification batches.
- **One exit row scored `+1.0000R` instead of `+0.0876R`** — the trailed stop was passed as the R
  denominator. Caught on read-back, superseded, rewritten.

---

## 5. What the safety net keeps catching

Every orchestrator error this run was caught **downstream by an agent refusing to act on an
incoherent briefing**, or by a mechanical sweep written after wr1's diagnosis — never by a check
written in advance of the work. That was the central lesson of wr1 and it held again here.
