# PRE-REGISTRATION — WHERE THE MONEY LEAKS (June walk-forward book)

**Registered 2026-08-16, BEFORE the June book is complete.** His ask, in his
words: *"let's see where the agents might be leaking, not leaking coded-wise,
but leaking with their performance, and see where money is leaking over the
next two weeks we'll have of complete data."*

Same discipline as `PREREG-chop-regime-gate.md`: the buckets, the
measurements and the decision rules are fixed here so the analysis cannot
become a search for whatever story the data happens to tell.

---

## §0 — The filter that outranks every number below

`docs/ANCHOR-reasoning-first.md` governs. **Reasoning-match is the target;
performance is the consequence.** So a "leak" is only a leak if closing it
moves the agents TOWARD his reasoning. A change that recovers R by moving
them away from it is a regression and gets rejected explicitly, with the
number stated so the rejection is on the record.

Three behaviours are therefore **NOT leaks** and are excluded from the
optimisation surface in advance, because he has already ruled on them:

| behaviour | his ruling |
|---|---|
| stall → break-even | *"the agent management saved more from losers than it took from winners... worth keeping unchanged"* — measured and reported, never optimised |
| declining most mechanical triggers | the mechanical book was ~flat over the narrated week; the agents' +14.22R came from declining 72%. Passing is the edge, not a leak |
| C-grade positions not trailed | *"If it's a C-grade conviction, don't trail that. I'd rather just hold to my high-conviction stops"* |

If the data argues against one of these, that is a finding to put to HIM, not
a change to make.

## §1 — The leak taxonomy, fixed in advance

Every bucket reports **R, points, and dollars at his parameters** (base /
A $250 / B $200 / C $150), **per window, never pooled** (LONDON / NY_PRE /
NY_AM), with **day-clustered** intervals and n stated.

**A. ENTRY — money not made, or lost, at the decision**

| # | leak | measurement |
|---|---|---|
| A1 | declined winners | for every `pass`, re-walk the setup it declined from its own would-be entry and stop to session end. Distribution, not total — the total is an upper bound nobody trades |
| A2 | taken losers a stated rule should have declined | cross-tabulate losses against the rubric fields already in each verdict (grade, headroom, crowded path, HTF verdict) |
| A3 | limit-discipline cost | `no_fill_expired` + `no_fill_ran` rows: what did those setups do afterwards? Prices the retest-limit style against signal-close entry |
| A4 | grade↔outcome coherence | does A actually beat B beat C? If the ladder does not sort, conviction is decoration |

**B. MANAGEMENT — money made and given back (the give-back tax)**

`scripts/mech_vs_agent.py` already computes the frame: capture rate against
each position's own available R. On the narrated week that was **36%**, and
trail-outs on winners were the largest single component.

| # | leak | measurement |
|---|---|---|
| B1 | trailed out before a target that later printed | per fill: did the named target print after the trail stop hit? Cost = target R − realised R |
| B2 | partial timing | R left on the runner vs R banked, by structure type |
| B3 | target selection | how often the named target printed at all — a target that never prints is a thesis problem, not a management one |
| B4 | T51 flatten at 09:29:59 | what pre-market positions did after being flattened. Report both directions; T51 is his ruling and stands regardless |

**C. REGIME — leaks that are a property of the day, not the trade**

| # | leak | measurement |
|---|---|---|
| C1 | day-clustering | **this is `PREREG-chop-regime-gate.md` §1, and the June book is what it was deferred for.** Decompose loss into within-day and between-day variance. If damage concentrates in a few sessions, the fix is a session-level gate, not a trigger-level one |
| C2 | window asymmetry | London vs NY_PRE vs NY_AM separately — he has said repeatedly they must be treated differently; this quantifies how differently |
| C3 | chop §5 net-of-frequency | the deferred stage: does the book improve after chop trades are removed, with the frequency cost stated alongside any EV gain |

**D. STRUCTURAL — costs that are not judgement at all**

| # | leak | measurement |
|---|---|---|
| D1 | fill-model optimism | count fills where the limit was touched by ≤1 tick; re-score the book without them. Replay touch-fills are documented optimism and live paper is what settles it |
| D2 | cost drag | commission + spread at his contract sizing, in dollars, against the same book |

## §2 — Decision rules, fixed before seeing the numbers

1. **Rank by (expected R recovered × confidence), not by raw size.** The
   biggest number in the table is usually the one with the widest interval.
2. **June diagnoses; June does not ratify.** June is the clean out-of-sample
   walk-forward. A fix derived from June is FIT to June — adopting it makes
   June in-sample for that change and burns the only clean month we have.
   The honest path: diagnose on June → state the fix as a hypothesis →
   validate on pre-June history through the offline harness (`M4`, which
   exists precisely to provide a validation span that is not June) → only
   then does it touch a contract.
3. **Every candidate fix is written as a reasoning claim first**, in his
   vocabulary, and checked against the teaching loop (T1–T71) for conflict
   before it is written as a rule. Working-forward rule T66 applies: surface
   the conflict, never re-litigate silently.
4. **n is stated everywhere.** At ~3–4 fills/day, three weeks is ~50–60
   trades. That is enough to rank leaks and nowhere near enough to certify a
   fix — which is exactly why rule 2 exists.
5. **Report what did NOT leak.** A bucket that comes back clean is a real
   result and gets the same line as one that does not.

## §3 — Artifacts

Mostly built; the June book is the missing input, not the tooling.

| what | artifact | state |
|---|---|---|
| give-back tax, mechanical control | `scripts/mech_vs_agent.py` | built (wk1) |
| MC / prop-rule survivability | `scripts/mc_prop.py`, `scripts/mc_bootstrap.py` | built (n=33, needs the bigger book) |
| reasoning comparison | `scripts/score_replay_run.py --reasoning` | built |
| chop substrate | `scripts/raw_trigger_census.py` | built |
| A1/A3 re-walks, B1–B3, C1–C2, D1–D2 | one new script over the run ledger | to build while June runs |

## STAGE STATUS

| stage | status |
|---|---|
| taxonomy + decision rules | registered 2026-08-16, before the book |
| June week 1 | running on the Mac (MCP path, leak-clean) |
| weeks 2–3 | pending — venue depends on the M2b bridge test |
| analysis | runs when the book is complete |
