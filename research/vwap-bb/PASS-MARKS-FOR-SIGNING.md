# PASS MARKS — FOR ANGUS TO SIGN

**Prepared 2026-08-08, overnight queue item 10. Not signed. Fifteen minutes, not a research
task.** Companion to `PREREGISTRATION.md` §10, whose four OPEN items are restated here with the
options, what each commits to, and a recommendation with its reason. **Nothing below is a
decision — it is the decision laid out for you to make.**

Spec at time of writing: `f6b38bf4af1ca9696a12a6e9f80a12209ebff310` (A1–A15).

---

## 10.1 — Parity chart readings

**The requirement as written is now satisfied differently than it originally planned, and that
itself is a decision.**

§10.1 was written expecting **hand-chart readings** at two, then several, instants. That plan
changed overnight and needs your sign-off on the replacement, not just the original ask:

- **P2 (2025-01-15 15:48 ET... correction, 2025-01-22 09:50 ET)** ran as a real hand reading:
  **PARITY FAIL**, 36 of 48 fields matched, 12 mismatched, every one diagnosed to a specification
  gap (`PARITY-P2-RESULT.md`). Those gaps became **A8–A13**.
- **P3 was cancelled.** Amendment 03 §7 published its own selection criterion, which told the
  reader a trigger existed at the released instant before any chart was opened. No
  date-and-time-only discipline fixes that.
- **The P4–P9 batch was drawn, then withdrawn** for the identical structural reason, one level up
  — it was a pre-registered plan for more hand readings.
- **Machine verification replaced all of it**: 2a (81 spec-derived unit tests, 77 pass — the 4
  failures are 2 known mis-built test bars and now-fixed spec gaps), 2b (10 invariants over the
  full 1,472-trade admission list, all PASS or the one legitimately MOVED to 2a), 2c (a blind
  second implementation, differential-diffed against the detector).

**Options:**

| | commits to |
|---|---|
| **(a) P2 alone satisfies 10.1** | one hand-verified instant is enough, on the strength that its every finding was traced to a named spec gap and closed |
| **(b) The full verification suite satisfies 10.1**, superseding the original hand-chart plan | parity is established by code-path testing, not by chart-matching, given hand-chart availability is structurally limited to a few weeks in January 2025 and cannot reach most of the workbench at all |
| **(c) 10.1 is not yet satisfied** — require more hand readings on fresh, un-cancelled instants | rejects the P3/P4–P9 cancellations as premature; more chart time from you |

**Recommendation: (b).** The verification suite tests every code path a chart reading could only
sample, is reproducible, and does not depend on your platform's 1-minute history depth (a
structural limitation P2 already ran into). The P2 result is not discarded under (b) — it is the
finding that produced A8–A13, and its value is already banked.

---

## 10.2 — Stop anchor: floor or structural rule?

**Recomputed overnight under the current spec, not carried over stale.** 58.7% of the 1,472
admitted trades sit exactly at the A5 10.00 pt floor (was cited as 59.9% under an earlier
amendment state; the figure moved slightly under A14's rounding but the conclusion is unchanged).

**Options, unchanged from the original framing:**

| | commits to |
|---|---|
| **(a) Floor, as written** | the wick anchor stands, 10.00 pt catches the degenerate cases, and the modal trade has a fixed 10-point stop unrelated to structure |
| **(b) A different structural anchor** — prior swing (median 16.29 pt) or 2×ATR (≈25.32 pt) | closer to your 35.00 pt hand-log median, but **neither can be confirmed from the hand log**, which records distances, never prices |

**Recommendation: no change from the prior framing — this is genuinely yours to call**, and
nothing overnight moved the evidence enough to break the tie. What overnight work *did* add: the
figure is fresher (58.7%, not 59.9%) and the R-distribution behind it is now confirmed stable
under A14 (item 3: median R unchanged at 10.00 before and after rounding), so whichever way you
rule, it is ruling on a number that has been re-verified, not one computed once and left stale.

---

## 10.3 — Tournament axis structure

**Working assumption ÷4 has never been signed.** The axis decision table (`STATE.md`) shows every
divisor clearing on sample size; the cost of a wider structure is resolution, not power:

| divisor | required n | blind zone |
|---|---|---|
| 1 | 411.3 | 3.25 pt |
| **4 (working assumption)** | **631.7** | **4.03 pt** |
| 72 (full grid) | 1082.9 | 5.27 pt |

**Options:** any divisor in the table, or a different axis structure entirely (§12.3's "one axis
at a time" with the management axis at 4, per A6).

**Recommendation: sign ÷4 as proposed.** It is the working assumption every downstream figure in
this project already assumes (the tripwires in `stage2_smoke.TRIPWIRES`, the gate-6 comparisons).
Changing it now would not just require a decision, it would require re-deriving every threshold
already quoted elsewhere. If a different structure is wanted, flag it explicitly rather than
silently signing ÷4 — several documents cite the ÷4 figure by value already.

---

## 10.4 — Pass-mark sign-off

Three sub-decisions, each stated plainly:

### (a) Primary criterion
As drafted: **mean net R > 0 at cost 0.975, with the bootstrap lower bound above zero.**
**Options:** sign as drafted, or tighten/loosen the cost basis or the bound. **Recommendation:
sign as drafted** — 0.975 is the mid cost basis already used throughout (`COSTS = {"c050": 0.50,
"c0975": 0.975, "c150": 1.50}`), and the abort condition below already covers the case where the
sign flips at a different cost.

### (a-i) THE IDENTITY-CHURN CLAUSE — ADDED 2026-08-08, Amendment 05, before signing

> **Stage 3's expectancy is computed under one resolution of four documented spec ambiguities.
> The ambiguity sweep shows each resolution changes trade identity by 32–45% while changing
> trade count by under 3%. The pass mark is therefore evaluated as the minimum across every
> documented resolution combination, at the base cost basis. A result positive under one
> resolution and negative under another is recorded as NO EDGE DEMONSTRATED, not as a pass on
> the favourable branch.**

**Why this is being added to a document already being signed, rather than filed as a separate
finding.** The blind build's fork sweep (`data/2c-raw/NOTES.md`, `sensitivity.py`) measured what
2C-ADJUDICATION.md's A-01 shift test confirms independently: swapping a single documented
ambiguity's resolution — cluster linkage (A-04), the invalidation side (A-07), or the `range`
confluence minimum (A-06) — leaves the **admitted count** within ±3% while changing **which
trades** are admitted by 32–45%. Four such forks are documented and unresolved by the spec text
itself (§3's "proximity tolerance," §7's incomplete confluence table, §7's invalidation
`[Hypothesis — test]` tag, §6.4's F range). **A pass mark that only ever sees one resolution has
not tested the strategy — it has tested one arbitrary reading of four unwritten sentences, and a
different overnight run of this same project could easily have landed on a different one.**

**Confirmed in writing: this does NOT increase N_trials, and here is why.** A multiple-comparisons
correction exists to control the false-positive rate of a procedure that **selects** the most
favourable result from among several candidates — the danger is trying k variants and reporting
the best one, which inflates the chance of a spurious pass. **Taking the minimum across a
pre-specified set of variants is the opposite operation.** It is a conjunction: the criterion is
satisfied only if **every** variant clears the bar, decided *before* any of them is computed, with
no selection step anywhere in it. A procedure that can only make the pass condition **harder** to
satisfy cannot inflate a false-positive rate — it can only lower it. This is the same logic
already in force elsewhere in this project: taking the **minimum** across cost bases (already
part of §7.2's abort condition) has never been treated as a second trial, for the identical
reason. `N_trials` stays at **1** for Stage 3.

**What this requires operationally, recorded so it is not lost between now and the run:** the
"every documented resolution combination" in the clause means, at minimum, the fork set the
sweep already measured — cluster linkage, invalidation side, `range` confluence minimum — and
should also include the front-run F range (§6.4, "start 2–3 NQ pts" is itself unresolved in the
frozen detector, which fixed F=2.0) and the target-menu question of weekly H/L (§6's menu vs
`OUT-OF-SCOPE-BRANCHES.md` branch 9). **Enumerating the exact combination set is a pre-registration
task in its own right and is not done by this clause alone** — this clause fixes the *combining
rule* (minimum, at base cost); the *fork set* it runs over needs its own explicit list before
Stage 3 is ever re-run under it.

### (b) Abort condition 3 — sign change across cost levels
**Options:** **abort** (a sign change between cost bases voids the run entirely, no verdict
read) or **annotate** (report the sign change as a finding, alongside whatever the mid-cost
result was). **Recommendation: abort.** §7.2's own text (*"If mean net R is positive at 0.50 and
negative at 1.50, the finding is about the cost assumption, not the strategy"*) already commits
to this reading in prose; making it binding rather than advisory closes the loophole where a
cost-sensitive result gets reported as a strategy result anyway.

### (c) Trigger reading — A/B/C/D, fixed or itself a tournament axis
**Context:** `READING = "A"` is hardcoded in `stage2_smoke.py` and inherited by every downstream
script including `spec_current.py`. **Every measurement since the opportunity-set characterisation
has run on reading A.** Item 11's Stage 3 run below will also use reading A unless you say
otherwise **before it runs** — changing it after would mean re-running Stage 3, which consumes a
second N_trials slot for no new information.

**Options:** (i) fix reading A as pre-committed, matching everything already run; (ii) promote
the reading choice (A/B/C/D) to its own tournament axis, which **changes the ÷4 divisor in 10.3**
— four readings × the existing axis count.

**Recommendation: (i), fix reading A.** It is what every prior measurement in this project used,
changing it now multiplies the correction factor for no stated reason to prefer B, C or D over A,
and if reading sensitivity turns out to matter it can be tested as a **Stage 4 autopsy question**
(≤3 hypotheses, per Amendment 02) rather than folded into the primary tournament structure.

---

## Summary table for §11's sign-off block

| item | recommendation | what signing it commits you to |
|---|---|---|
| 10.1 parity | **(b)** verification suite supersedes hand-chart plan | P2 + 2a/2b/2c stand as the parity evidence; no further hand readings |
| 10.2 stop anchor | **no recommendation — genuinely open** | floor (a) keeps the spec as written; structural (b) requires picking prior-swing vs ATR, unconfirmable from the hand log either way |
| 10.3 axis structure | **sign ÷4** | required n 631.7, blind zone 4.03 pt, matches every threshold already quoted elsewhere |
| 10.4a primary criterion | **sign as drafted** | mean net R > 0 at c=0.975, bootstrap lower bound above zero |
| 10.4b abort condition 3 | **abort, not annotate** | a cost-level sign flip voids the run; no verdict is read |
| 10.4c trigger reading | **fix reading A** | matches every prior measurement; reading sensitivity becomes a Stage 4 question if it ever matters |

**If you sign everything above as recommended except 10.2, that is a coherent, internally
consistent pass-mark set** — nothing in 10.1, 10.3 or 10.4 depends on which way 10.2 goes.
