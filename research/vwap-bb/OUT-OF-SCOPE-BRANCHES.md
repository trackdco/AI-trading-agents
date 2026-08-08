# RULING — unimplemented spec branches are OUT OF SCOPE for this run

**Ruled 2026-08-08. Decision only — nothing implemented, nothing re-run, the sealed file
unopened. N_trials: 0.**

> **This study tests the spec AS IMPLEMENTED, documented at the pinned provenance hashes. The
> unimplemented branches listed below are formally OUT OF SCOPE for this run.**

The sealed result at
`a9ddc2947ca6a5f4c7e453d90427bed91710d1bc94c86de81fa9b381739bd4f0` was produced without them.
Implementing them now would change the admitted population and require re-sealing, leaving two
results and a choice made after the fact. **The seal stands.** What changes is that the thing it
tests is now named precisely rather than implied.

**The brief named two branches. There are nine.** A partial ruling would be worse than none, so
all of them are enumerated.

---

## 1. What is out of scope, quoted

| # | branch | spec text, verbatim | why unimplemented |
|---|---|---|---|
| **1** | **§4 pattern taxonomy** | *"**A — Reversal:** over-extension and/or HTF range extreme → rejection block against prior move → retest entry. **B — Reclaim:** price on wrong side of cluster → displacement back through → retest of reclaimed cluster. **B2 — Continuation:** established move → pullback to cluster → rejection block with the move → retest entry."* | Every clause needs a threshold the spec does not state — "prior move", "wrong side", "established", "pullback", "retest" |
| **2** | **§6 rule 2, pattern-conditioned targets** | *"Defaults: **A** → VWAP middle; **B2** → next structural level in move direction; **B** → opposing liquidity (pre-market/prior-day extreme), preferring ±2σ alignment."* | Depends on #1. Also ambiguous on its own — pattern A's default names a level that is *inside the entry cluster* 85.4% of the time |
| **3** | **§6 rule 3, news-day override** | *"on high-impact data days, data extremes have elevated sweep probability. If trade direction points at an untaken data extreme beyond the default target, target the data extreme instead."* | **Blocked on DATA, not parameters.** Requires an economic calendar with impact ratings. Not held, and purchases are a standing no |
| **4** | **§6 rule 6, alignment bonus** | *"prefer targets where ≥2 menu levels stack within tolerance."* | "Prefer" has no rule. A4 takes the first level clearing the floor; no preference is expressed |
| **5** | **§10 daily halt** | *"Daily halt: after **2 losses** or **−2R** on the day, whichever first (placeholder; MC calibrates)."* | **Different from the rest — see §4 below. This one is implementable as written and was simply not built** |
| **6** | **§5.5 no-fill-no-chase** | *"Order cancels if price runs T_cancel points beyond entry without filling. T_cancel: CALIBRATE."* | Moot under accounting rule §4.2 (fill at next bar's open, so no unfilled state exists), but it would matter under a real E1 limit |
| **7** | **§2 profile, VAH / VAL / HVN / LVN** | *"POC, VAH/VAL, HVN/LVN"* | Only POC is computed. Value area needs a percentage the spec does not state |
| **8** | **§2 session boxes** | *"Session boxes — Asia / London / NY — session extremes for targets/liquidity"* | The detector uses the whole Globex session extreme and prior-day H/L. The three named sub-sessions have no stated boundaries |
| **9** | **§6 menu, three entries** | *"weekly H/L; pullback origin (B2); HTF range extremes"* | Weekly H/L not computed; pullback origin depends on #1; the 4h range is computed for the §7 location filter but never offered as a target |

### Not out of scope — deliberately excluded, which is different

| | |
|---|---|
| **§9 conviction sizing** (full vs half unit) | Excluded by accounting rule **§4.7**: one unit of risk per trade, no sizing. A stated decision |
| **§8 management V1 / V2 / V4** | A **tournament axis**. This run is V0 (set-and-forget) by design |
| **§2 weekly profile anchor** | A **tournament variant** by the spec's own words |
| **§7 volatility stand-down** | **DISABLED for v1** by Amendment A2 #5 |

---

## 2. Direction of the effect

**Every one of these omissions is permissive.** None of them would have *added* a candidate;
each is a classification, a target refinement, or a stop condition that could only have removed
or redirected trades.

> **The tested population is LESS SELECTIVE than the full spec intends.**

Concretely: without #1 and #2 every trigger is treated identically and targeted by the same
first-clears-the-floor rule, so setups that the taxonomy would have routed to a different target
— or excluded for not matching any pattern — were admitted and targeted generically. Without #5
a session that had already lost twice kept trading.

---

## 3. THE ASYMMETRY — the operative consequence

> **A PASS is trustworthy. A FAIL is ambiguous.**
>
> **PASS:** the strategy cleared its bar on a population *looser* than the one the spec
> describes. Adding the missing branches removes or redirects trades; it does not add any. A
> result that survives the looser population is not made worse by tightening it, so a pass here
> is a conservative pass and can be relied on.
>
> **FAIL:** uninformative about the full spec. The missing branches might have removed precisely
> the losing trades — the taxonomy might have excluded them, the pattern-conditioned targets
> might have redirected them, the daily halt might have stopped the session before them. **A
> fail cannot distinguish "the strategy does not work" from "the implementation was missing the
> parts that make it work."**

### The pass does not carry over — the practical consequence [ADDED 2026-08-08]

The PASS reading above says the edge does not *depend* on the missing branches. It does **not**
say the branches can be added afterwards and the pass kept. Recorded plainly, because this is the
sentence that will be reached for later:

> **If the nine branches are ever implemented, the pass does NOT carry over. That is a new
> specification and requires a new test. The reasoning "we already validated it, and the filters
> were designed to help, so adding them can only improve things" is invalid: the filters shrink
> the trade set, and a mean over a subset is not guaranteed to beat the mean over the superset.**

Mirrored in `PREREGISTRATION.md` §8.5, which corrects the same overstatement in this document's
earlier wording.

**This mirrors the next-bar-open fill decision (§4.2) exactly, and for the same reason.** Filling
at the next bar's open rather than at the E1 limit is strictly worse than the spec's intent: the
limit would fill at the level or not at all, while the open fills wherever the market opened.
**Same shape — a pass survived a handicap and is trustworthy; a fail might be the handicap
rather than the strategy.**

Two independent handicaps, both in the same direction. **The sealed result is a conservative
test of the strategy, and it should be read as one.**

---

## 4. §10's daily halt is a different kind of gap, and is flagged separately

Branches 1–4 and 6–9 are unimplemented because the spec never states the values they need.
**Branch 5 is not.** §10 gives both numbers — *"after 2 losses or −2R on the day"* — and marks
them *"placeholder; MC calibrates"*, meaning provisional, not absent.

**It was implementable as written and was simply not built.** The A7 admission loop caps at three
trades per session and holds one position at a time; it has no loss limit. Recording it here
honestly: this is an **omission**, not a specification gap, and it is the one item on this list
that could have been included in the sealed run at no cost in invented parameters.

It does not change the ruling — the seal stands, and the asymmetry covers it — but it should not
be filed alongside the branches that genuinely could not be built.

---

## 5. What it would cost to bring them in

**Recorded now so it is not underestimated later.** Every entry is a value the spec does not
state and that someone would have to invent, i.e. a new `[FIAT]` parameter.

| branch | new parameters required | count |
|---|---|---|
| **§4 taxonomy** | prior-move lookback; prior-move minimum magnitude; HTF-range-extreme proximity band; "wrong side" minimum duration; retest tolerance; retest window; pullback minimum depth; pullback maximum depth; precedence when a trigger matches more than one pattern | **9** |
| **§6 rule 2** | which VWAP is "VWAP middle" for A; which menu subset counts as "structural" for B2; pre-market window boundaries; ±2σ alignment tolerance | **4** |
| **§6 rule 6** | stacking tolerance; how "prefer" resolves against A4's first-clears rule | **2** |
| **§5.5** | T_cancel | **1** |
| **§2 VAH/VAL** | value-area percentage; HVN/LVN threshold | **2** |
| **§2 session boxes** | Asia / London / NY start and end | **3** (6 boundaries) |
| **§6 menu additions** | weekly-anchor definition; whether the 4h range qualifies as an HTF range extreme | **2** |
| **§10 daily halt** | none — values are stated | **0** |
| **§6 rule 3 news** | **not a parameter problem.** Needs an economic calendar with impact ratings. Data acquisition, and purchases are a standing no | **blocked** |
| | **TOTAL** | **≈ 23 new `[FIAT]` parameters, plus one data dependency** |

### What that number means

The A2 freeze took the spec from 18 free parameters to 13 and was treated as significant.
**Bringing these branches in would add roughly 23 more — nearly tripling the count — and every
one would be invented, not stated.**

That is the real cost of a future run, and it is not mainly compute. It is:

- **23 parameters chosen by someone.** Chosen on structural grounds they cost no N_trials;
  chosen by comparing outcomes they cost 23 increments and the corrected alpha collapses.
- **A new pre-registration.** The spec hash changes, so this one is void and the sealed result
  with it.
- **Gate 4 reopens on all 23** until each has a stated rule.
- **The news branch cannot be brought in at all** without buying data.

**Doing this properly is a larger job than the entire study to date.** Recording it here so that
"we should just add the pattern taxonomy" is never again said as though it were an afternoon.

---

## 6. The seal stands

| | |
|---|---|
| Sealed result | `a9ddc2947ca6a5f4c7e453d90427bed91710d1bc94c86de81fa9b381739bd4f0` |
| Tests | the spec **as implemented**, at the provenance hashes in [`CODE-PROVENANCE.md`](CODE-PROVENANCE.md) |
| Out of scope | the nine branches above, each quoted and each with its reason |
| Population | **less selective** than the full spec — every omission is permissive |
| Reading rule | **a PASS is conservative and trustworthy; a FAIL is ambiguous and must not be reported as a verdict on the strategy** |
| Still unread | yes |
| N_trials | **0** |

**The specification under test is now named rather than implied**, which is the condition the
seal needed and did not previously have.

---

## 7. UNTESTED BRANCH — A14's opposite rounding convention [ADDED 2026-08-08]

**A14 fixed the tick-rounding direction as "the direction that makes the trade worse" — stops and
targets away from entry, the entry itself against the trader.** The opposite convention —
round every price *toward* entry / *in the trader's favour* — is a coherent alternative and is
recorded here, unevaluated, so it is available if A14's conservatism is ever challenged.

| | A14 (in force) | opposite (untested) |
|---|---|---|
| Stop | away from entry (widens R) | toward entry (narrows R) |
| Target | away from entry (harder to reach) | toward entry (easier to reach) |
| Entry | against the trader (worse fill) | in the trader's favour (better fill) |

**Why it is not run:** A14's own text is explicit that the direction was fixed *before* any
recompute, specifically to avoid choosing a number after seeing its effect. Running the opposite
convention now, after A14's effect is known, would be exactly that — a comparison of outcomes
used to pick a rounding rule, which is a parameter search and consumes N_trials under the
project's own standing rule. **It stays untested for that reason, not because it is implausible.**

---

## 8. UNTESTED BRANCH — A15's ladder collapse, the never-collapse alternative [ADDED 2026-08-08]

**A15 formalised the target ladder's existing behaviour: menu levels within one tick collapse to
a single rung, keeping the nearer one.** The alternative — never collapse, walk every raw menu
level as its own rung regardless of spacing — is a coherent reading of §6.5's *"Walk the ladder of
opposing menu levels outward from entry"* taken fully literally, and is recorded here, unevaluated.

| | A15 (in force) | never-collapse (untested) |
|---|---|---|
| Two levels ≤1 tick apart | one rung, the nearer kept | two rungs, both walked |
| Effect on the RR-floor walk | a near-duplicate cannot supply a second, independent chance to clear the floor | it can |

**Why it is not run:** it is a behaviour change to the target ladder that every admitted trade in
this project already depends on, and evaluating it now — after the collapsing version's admission
counts and geometry are already known — would be choosing a ladder rule by comparing outcomes.
