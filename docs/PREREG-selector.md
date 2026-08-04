# PRE-REGISTRATION — the selector (agent discretion over which strategy's signals to take)

**Status: PRE-REGISTRATION DRAFT 2026-08-04, for Angus to ratify. NOTHING IS BUILT
until this document's bars are ratified by Angus.** No selector code, no prompt, no
harness, no briefing format exists or may be started before the sign-off block below
is signed. This is the brief's §4 deliverable ("write the pre-registration, build
nothing" — ANGUS BRIEF week of 2026-08-04) and it costs writing, not a build.

The selector is **a strategy in its own right** and gets the full treatment of
`docs/VALIDATION-PROCESS.md` (§1 pre-registration → §6 promotion ladder). This file
is its §1 artifact, written before anything exists to test — the same discipline as
`docs/HOLDOUT-2023-24-PREREGISTRATION.md` ("This file is the commitment") and
`docs/PLAN-agents-capture-run.md` ("a declaration, not a rationalisation").

Markers, per `docs/VALIDATION-PROCESS.md`:
- **[EXISTING]** — codified from repo practice, source cited.
- **[PROPOSED — Angus to ratify]** — a number only Angus can set; a defensible
  default is given so this doc is complete, but it is not law until he signs.
- **[OPEN — needs Angus/Pat]** — a fact or ruling this doc could not settle. Never
  guessed.

**Branch discipline:** drafted on `claude/canon-rebuild-deployment-7m48yv`, off the
live arming branch. A commit on the arming branch — even docs — makes the next arm
refuse on provenance (live HANDOFF §4). This file reaches the live branch only via
the deliberate re-cert + re-authorization flow.

**Sign-off:**
ANGUS — date: __________ — bars ratified, build may begin: __________

---

## 0. What is being pre-registered, and why now

Half of the headline roadmap bullet — *"agents have knowledge behind, agent
discretion on what to take"* (brief §4) — is a selector: an agent that decides, each
day (or each signal), **which shipped strategy's signals get taken**, instead of
taking everything every strategy emits.

Why the pre-registration comes first: the shop has already produced one agent layer
whose gain was real and whose claimed mechanism was not (§5 below). The selector
invites the identical ambiguity — "the agent picked well" vs "the agent's
take-pattern happened to be a good fixed policy" — and the only way to tell them
apart honestly is to write down the baselines and the null **before** any selector
exists to defend. If the selector cannot beat the baselines below, the shop ships a
simple allocator and saves months of work (brief §4).

**Scope constraints carried in from the live design, all [EXISTING]:**

- **The selector may only remove or weight-down, never add.** Its action space over
  mechanically-generated signals is {take at shipped size, decline}. It never
  originates an entry, never resizes above the shipped tier, never touches stops or
  exits. This is the L-invariant ("layers above L0 may only remove or weight, never
  add" — `docs/CANON-QA-LOG.md` entry 4) applied at portfolio level, and it keeps
  the entries-mechanical law intact (live HANDOFF §7: "Entries mechanical,
  mechanical, mechanical"). Upsizing would be a sizing-tier claim and needs its own
  Wilson-bound bar per `docs/VALIDATION-PROCESS.md` §2.2 — out of scope here.
- **Fail-closed, isolation law.** A hung, dead, or malformed selector never blocks
  the mechanical path (the `agent_desk` isolation law, live HANDOFF §2; kill test
  7/7). Default on selector silence: the portfolio falls back to the ruled
  mechanical configuration — which book that is (B1 take-everything or the A1
  allocator of §2.4) is Angus's call. [OPEN — needs Angus]
- **No tools, no open-ended objective, ever** — the London "backtested the last 6
  months and took no trades" failure is why (live HANDOFF §7). Briefing strings in,
  one JSON verdict out, exactly like `src/live/agent_desk.py`.

**Decision granularity** [PROPOSED — Angus to ratify]: the bars in this document
bind at whichever granularity the built selector claims — per-day (each morning:
which strategies trade today) or per-signal (each eligible signal: take/decline).
Every baseline and the shuffle are defined at the **same** granularity as the
selector under test, so the comparison is never apples-to-oranges. The default
assumption below is per-day, because that is implementable from the brief-§2c data
contract alone (§6).

---

## 1. The claim, stated falsifiably

> **C1 (value):** An agent selector choosing among the shop's shipped strategies
> produces a combined day-level book that beats taking every eligible signal (B1),
> even rotation (B2), random picking (B3), and the best fixed-weight mechanical
> allocator (A1), on the pre-registered funded statistic of §2.5, on the discovery
> span, with the bars of §4.
>
> **C2 (mechanism):** the value in C1 comes from **discrimination** — the selector
> telling which strategy's conditions are live on a given day — and not from a
> reproducible take-pattern. Operationally: the selector's real picks beat the
> strategy-identity shuffle of §3 at the §4 bar.

Both halves are falsifiable and each has a distinct death:

- **C1 false** → no selection layer ships in any form. Take-everything (or the
  allocator, if it separately clears the ladder) stands. Tombstone per
  `docs/VALIDATION-PROCESS.md` §7.1.
- **C1 true, C2 false** → the win is *policy shape, not discrimination* — the exact
  run-2 outcome (§5). The agent selector does **not** ship; its converged
  take-pattern is distilled into a mechanical allocator, which ships instead
  (§4.3). This branch is pre-committed here precisely so it cannot be renegotiated
  after a seductive headline number.
- **C1 true, C2 true** → the selector is a real discriminating strategy and
  proceeds down the promotion ladder (`docs/VALIDATION-PROCESS.md` §6) like any
  other — holdout look declared (§6.3), funded-rules MC, shadow, two-party arming.

"The selector doesn't beat the baselines" is a valid, valuable outcome
(`docs/PLAN-agents-capture-run.md`: "'Agents don't beat V8' is a valid, valuable
outcome").

---

## 2. The baselines it must beat

### 2.0 Common setup

Notation, all implementable from the per-strategy emission contract of §6: shipped
strategies s ∈ {1..K}; per-strategy day-level P&L series `p_s(d)` at shipped sizing;
signal timestamps per strategy per day. **Eligibility (interim definition):**
`E(d)` = the set of strategies with ≥1 **taken trade** on day d (derived from
entry timestamps — eligibility is mechanical and logged, never the selector's own
claim). The limitation, stated plainly: the emission contract v0.1
(`docs/CONTRACT-strategy-emission.md`, emission-v0.1-proposed) emits taken trades
only, so the original definition — "emitted ≥1 signal on day d" — is **not
computable from it** for limit-entry (E3-style) strategies: a day with signals but
zero fills vanishes from `E(d)`. Target: the contract's reserved `candidates`
emission (`docs/CONTRACT-strategy-emission.md` §2.4) activates in v0.2, and `E(d)`
then derives from signal timestamps as originally specified. Until then this is a
**BLOCKING dependency** for baselines B2/B3 and the §3 identity shuffle on
limit-entry strategies. All arms —
selector and every baseline — run under the identical risk shell: same per-trade
risk schedule, same daily budget, same funded accounting (50k account, $2k
EOD-trailing, budget = base × 16/3 = $853.33 at $160 — `scripts/funded_book.py`
docstring; live HANDOFF §1).

**The account-architecture dependency, named up front:** under separate accounts,
combined day P&L is plain addition of `p_s(d)`. Under ONE account, the shared
budget accumulator is consumed in fill order, so the union book must be replayed in
signal-timestamp order with per-signal risk — the same gap
`docs/REPORT-correlation-2026-08-04.md` names ("Under one shared $853.33 budget the
answer must be re-run; that is the data contract's first job"). The brief §5 calls
this ruling "the big one" and it changes what the selector is even optimizing.
[OPEN — needs Angus: account architecture — same account or separate — before any
selector arithmetic is final.]

### 2.1 B1 — take every eligible signal (no selection at all) [EXISTING definition]

Every day, take all signals from all strategies: `P&L_B1(d) = Σ_s p_s(d)` (separate
accounts), or the timestamp-ordered shared-budget replay of the union (one
account). "'Take everything' is just the union" (brief §4). B1 is the null of the
whole enterprise: it is what the shop does by default if no selector is ever built,
and it consumes zero discretion. Any selector that cannot beat B1 has negative
value — it spent decisions to lose money.

### 2.2 B2 — rotate evenly among eligible strategies

Deterministic, zero free parameters. Fix the strategy order as vault registration
order (strategy id sort). Keep a pointer. On day d: take all signals of the first
strategy at-or-after the pointer (cyclic) that is in `E(d)`; score
`P&L_B2(d) = p_{s*}(d)`; advance the pointer one past s*. Days with `E(d)` empty
score 0 and do not advance the pointer. Per-signal-granularity variant: alternate
across strategies in signal-timestamp order, taking every K-th eligible signal
cyclically. B2 answers: does the selector beat *mere diversification across time
with no information at all*?

### 2.3 B3 — pick at random among eligible

At the selector's granularity: each day (each signal slot), draw uniformly at
random from `E(d)`, score the drawn strategy's actual `p_s(d)` (that signal's
outcome). One draw sequence = one replication; run **≥1,000 replications** (10,000
where cheap) to form the null distribution of the statistic [PROPOSED — Angus to
ratify; count matches `docs/VALIDATION-PROCESS.md` §2.3]. The selector's statistic
must sit above the **99th percentile** of this distribution — i.e. p ≤ 0.01,
family-wise per §4.1. B3 differs from the §3 shuffle: B3 is a fresh naive random
*policy* (its take-count and timing are random too); the shuffle preserves the
selector's entire policy shape and randomizes identity only.

### 2.4 A1 — the best simple mechanical allocator (the control, not a baseline)

[EXISTING discipline — "beat the best mechanical control", the lock1r_2r precedent:
`docs/PLAN-agents-capture-run.md` §9 criterion 2, `docs/VALIDATION-PROCESS.md`
§2.5.] A fixed-weight allocation across shipped strategies — default: equal risk
weight; if the correlation battery's marginal-contribution MC
(`docs/REPORT-correlation-2026-08-04.md`) has produced ratified weights by test
time, use those instead, frozen before the selector run. No per-day discretion;
weights change only by versioned release (`docs/VALIDATION-PROCESS.md` §9). A1 is
what actually ships if the selector fails — so the selector must beat it, not just
the strawmen. Run-2's lesson is literal here: a one-line mechanical rule captured
92% of the agent delta (§5).

### 2.5 The comparison statistic — pre-registered so it cannot be chosen post-hoc

[PROPOSED — Angus to ratify.] For every arm, from its combined day-level P&L
series, compute both:

1. **Net:** total net R (equivalently $ at the shipped risk schedule) over the
   evaluation span.
2. **Funded risk shape:** the correlation battery's ruin harness
   (`scripts/correlation_battery.py`: whole-day bootstrap, 2,000 sims × 252 days,
   50k start, $2k EOD trailing) — P(bust), median net/yr, p95 maxDD, median worst
   day.

**PASS vs a baseline requires:** median net/yr strictly greater, AND P(bust) and
p95 maxDD not worse. A split result (wins net, worse risk shape — or the reverse)
is graded by the funded criterion, which is hereby pre-committed rather than
invoked after the fact: **on a funded account the risk shape outranks raw net**
(Angus's own run-2 ship rationale, `docs/REPORT-desk-run-2.md` postscript:
"remember its a fundd — it prevented lots more losses than where it didnt capture
winners fully, and thats completely fine"). A selector that wins net only, at worse
P(bust)/maxDD than A1, does not ship on a funded account.

---

## 3. The shuffle test — strategy-identity shuffle

The decisive null, modeled directly on the conviction shuffle of
`docs/REPORT-desk-run-2.md` (and pre-registered this time *before* the thing it
tests exists).

**Hold the selector's policy shape constant** — the realized trade count per day,
the timing of every pick, the sizing of every pick — **and randomize which strategy
each pick came from.** Concretely: for each pick the selector actually made at time
t (day d) with size w, replace the picked strategy with a uniform draw from the
strategies eligible at that slot, `E(d)` (per-signal: eligible at that timestamp),
and score the drawn strategy's actual outcome for that slot at size w. Draws are
permutations within strata so the shuffled book keeps the same per-day pick counts
the selector had; stratify by day (per-day granularity) or by (day × session)
(per-signal), mirroring run-2's stratification note ("the closest stable
stratification" — `docs/REPORT-desk-run-2.md` Methods). Replay through the same
day-level accounting as §2.5. **≥1,000 draws** (10,000 where cheap) [PROPOSED —
Angus to ratify, matching `docs/VALIDATION-PROCESS.md` §2.3].

**Reading the result:**

- If the selector's real assignment beats the shuffled null at the §4 bar, the
  value is **discrimination** — the selector knows which strategy to take. C2
  holds.
- If performance survives the shuffle — the null matches or beats the real picks —
  **the value was the policy, not the discriminating** (brief §4): everything the
  selector added is carried by *how much, when, and how big it takes*, which is a
  mechanical allocator's job. C2 is dead, regardless of how good C1 looked.

This is exactly the instrument that caught run 2: real +550.2R vs null mean
+602.5R (σ 25.9), p = 0.978 — random reassignment of the same time budget beat the
agent's specific choices (`docs/REPORT-desk-run-2.md`, "The conviction shuffle,
plainly"). The selector gets the same test, declared first.

---

## 4. Bars, kill criteria, and the allocator outcome

### 4.1 Statistical bars — all [PROPOSED — Angus to ratify], aligned with `docs/VALIDATION-PROCESS.md`

| Bar | Number | Consistent with |
|---|---|---|
| Null replications (B3 and shuffle) | ≥ 1,000 (10,000 where cheap) | VALIDATION-PROCESS §2.3 |
| Significance vs stochastic nulls | family-wise p ≤ 0.01 | VALIDATION-PROCESS §2.3 |
| Family-wise correction scope | the null statistic is the **max over every selector variant tried** — every prompt version, briefing format, config. Trying two selectors and reporting one is a search and gets deflated as one (brief §7: "choosing between two candidates is itself a search") | VALIDATION-PROCESS §2.3 |
| Minimum n, direction claims | ≥ 30 selector picks per era cell (fit-2025, fit-2026 (discover/validate), holdout) | VALIDATION-PROCESS §2.2 |
| Minimum n, magnitude claims | ≥ 100 picks pooled | VALIDATION-PROCESS §2.2 |
| Minimum overlap | ≥ 60 both-active days between any strategy pair in the eligible universe before return-based selector claims are trusted | REPORT-correlation-2026-08-04 threshold 3 |
| Era discipline | discover on 2025, validate on 2026; the ΔR vs the best baseline must point the same way in both; triple-era survival once the holdout look is taken | VALIDATION-PROCESS §2.1 [EXISTING] |
| DSR / PBO on the selector book | DSR ≥ 0.95; PBO ≤ 0.25 over the selector-config search; 0.25–0.50 INCONCLUSIVE (blocks); ≥ 0.50 condemns the search procedure itself | VALIDATION-PROCESS §2.4 |
| Funded MC | combined P(bust) ≤ 1.0% at shipped sizing | VALIDATION-PROCESS §6 rung 3; REPORT-correlation threshold 4 |
| Verdict states | PASS / FAIL / INCONCLUSIVE; **INCONCLUSIVE blocks exactly like FAIL** | VALIDATION-PROCESS §5 [EXISTING + brief] |

### 4.2 Pre-committed kill criteria — the selector dies if ANY of:

(Form per `docs/PLAN-agents-capture-run.md` §9; standard list per
`docs/VALIDATION-PROCESS.md` §7.1.)

1. **Fails to beat B1** on the §2.5 statistic — or beats it only via ≤ 3 picks
   (drop-top-3 fragility; the rr_floor-1.5 RETRACTION precedent,
   `docs/RULING-mechanical-only.md`).
2. **Fails to beat B2 or the B3 null** at family-wise p ≤ 0.01.
3. **Loses to A1**, the best simple mechanical allocator, on the §2.5 statistic.
4. **Era-split sign flip** in ΔR vs the best baseline (2025 vs 2026, or any era
   pair once holdout is in play).
5. **The strategy-identity shuffle survives it** — real picks not better than the
   shuffled null at p ≤ 0.01 → the discrimination claim (C2) is dead and the agent
   selector dies *as a selector*; see §4.3 for what ships instead. (Bar mirrors
   run-2 criterion 4, which killed "the agent arm as a per-trade discretionary
   discriminator" at p = 0.978.)
6. **Only works leaky** — any t-time information leak found in the harness kills
   all results ("looked great leaky, died honest" — London burn list, via
   `docs/VALIDATION-PROCESS.md` §2.5).
7. **FAIL or INCONCLUSIVE on its one declared holdout look** (§6.3). Holdout
   INCONCLUSIVE → KILLED + tombstone, per `docs/VALIDATION-PROCESS.md` §7.1
   criterion 7 and the holdout carve-out of `docs/VAULT-SCHEMA.md` §4.

Every kill gets a tombstone with the full anatomy — spans consumed, holdout look
spent or not, result table, mechanism of failure, reopening burden — per
`docs/VALIDATION-PROCESS.md` §7.1 (the rr_floor pattern). Reopening burden for a
killed selector [PROPOSED — Angus to ratify]: a materially different knowledge
substrate (new journal history, new strategy universe) plus a triple-era result at
least as strong as the evidence that killed it.

### 4.3 What shipping a simple allocator instead looks like

The pre-committed off-ramp, so the months are actually saved:

- **Trigger:** kill criterion 5 fires while C1 holds (beats baselines, fails the
  shuffle) — or the selector is never built because these bars make the prior look
  poor. Either way the value on the table is *policy shape*, which is mechanizable
  (run-2: "policy shape is mechanizable" — `docs/REPORT-desk-run-2.md` verdict).
- **The ship:** A1 — fixed weights over shipped strategies (equal risk, or
  marginal-contribution weights from the correlation battery once ratified), plus
  any *distilled* shape rules extracted from the selector's converged take-pattern
  (e.g. per-day strategy-count cap, budget split). Zero per-day discretion; no
  agent in the entry path; certifiable with ordinary unit tests instead of R15-class
  agent certification.
- **Its process:** the allocator is itself a strategy config — it gets its own
  short pre-registration, the same §2.5 statistic vs B1, the promotion ladder, and
  version-controlled weight changes only (`docs/VALIDATION-PROCESS.md` §9: logged,
  validated offline, shipped as a versioned release through the two-party step).
- **The one caveat carried from run 2:** if the distillate cannot reproduce the
  shape's risk profile on fit — run-2's open question, where the agent's genuine
  advantage over lock1r_2r was maxDD $810 vs $2,476 — that is evidence some
  discretionary component matters after all, and the decision returns to Angus with
  that number on the table (`docs/REPORT-desk-run-2.md`, "What this means" item 2).

### 4.4 If it survives everything

Survival here earns exactly one thing: entry to the promotion ladder at
`docs/VALIDATION-PROCESS.md` §6 with a frozen policy — holdout look (declared,
one), funded-rules MC, shadow certification (R15-class, kill test included, since
an agent would sit in the take/decline path), two-party arming. **A PASS here does
not auto-ship** (§4.1 of VALIDATION-PROCESS: the 25%-partial precedent — PASSED
holdout, Angus ruled it stays unshipped). Nothing in this document self-authorizes.

---

## 5. The precedent — the shop has already lived "real gain, wrong mechanism"

All numbers from `docs/REPORT-desk-run-2.md` (2026-07-30; funded dollars there are
the run-2 grading accounting at $150 base — the current live references are the
$160-base +$82,543 fit / +$48,211 holdout, `docs/ARMING-REFERENCE.md`).

The exit-layer agents beat the three-rule mechanical canon by **+100.1R over 763
trades (p = 0.003)** — +488.7R vs +388.6R, 12 of 13 months green, surviving
drop-top-3, both eras positive (fit-2025 +38.8R, fit-2026 +61.4R). Genuinely real.
And the **conviction shuffle came back p = 0.978**: within (session × mech-outcome)
strata, randomly reassigning the agent's own holding times across trades replayed
to a null mean of +602.5R (σ 25.9) against the agent's real +550.2R — random
reassignment of the same time budget *beat* the agent's specific choices. Per the
pre-commitment, "the agent arm as a per-trade discretionary discriminator is dead."
The gain was the policy shape — average loser cut −0.708R → −0.576R with the
average winner unchanged (+1.462R → +1.464R), defense +231.4R across 335 mech
losers, offense −131.3R across 428 mech winners — and a one-line mechanical rule
(lock1r_2r) captured 92% of the delta. Angus shipped the agent layer anyway, for
the right, *stated* reason: the funded risk shape (maxDD $810 vs the control's
$2,476; "remember its a fundd — it prevented lots more losses than where it didnt
capture winners fully, and thats completely fine"), with the shuffle FAIL on the
table.

The same ambiguity will appear with the selector, and **knowing which kind of win
you have determines what you do with it** (brief §4): a discrimination win justifies
building and certifying an agent in the take/decline path; a policy-shape win
justifies a fixed allocator and no agent at all. Last time, the distinction was
discovered *after* the build, and the ship decision had to be argued post-hoc from
a criterion (funded risk shape) that wasn't in the pre-registration. This document
exists so that next time the branch is chosen in advance: §1 defines the two wins,
§3 tells them apart, §4.3 pre-commits what ships in each case.

---

## 6. What must exist before this test can run

### 6.1 The per-strategy emission contract (the correlation battery's contract)

The test consumes exactly what the brief-§2c data contract emits per strategy —
"day-level P&L series, signal timestamps, direction, risk, mechanism tag, input
columns" — the same contract the correlation battery consumes directly (brief §2c;
`scripts/correlation_battery.py` currently derives day P&L and in-market minute
sets from the two existing books). From it this test derives: `p_s(d)` (day-level
P&L), eligibility `E(d)` (from signal timestamps), and shared-budget replay order
(timestamps + per-signal risk). "The baselines cost nothing extra — once the
correlation infrastructure exists you'll have per-strategy day-level P&L and signal
timestamps, and 'take everything' is just the union" (brief §4).

- The proposed contract is `docs/CONTRACT-strategy-emission.md`
  (emission-v0.1-proposed), which drafts the exact field formats and cites this
  document back. What remains open is its **ratification** in the thirty-minute
  conversation with Brake (brief §2c), not its existence. [OPEN — needs Angus:
  contract ratified and frozen; includes the mixed −04:00/−05:00
  timestamp-offset handling named in `docs/VALIDATION-PROCESS.md` Appendix A.]
- **Per-signal granularity extension:** if the built selector acts per-signal, the
  contract additionally needs a per-signal outcome field (R at shipped exits) —
  day-level P&L cannot score signal-level reassignment. At per-day granularity the
  brief-§2c contract is already sufficient. [PROPOSED — Angus to ratify with the
  granularity choice, §0.]
- Provenance mandatory on every number per the vault rule (brief §2b): each
  emission names its commit, book version, and profile.

### 6.2 A portfolio to select from

- **K ≥ 2 strategies through the promotion ladder.** Today K = 1: the NY canon is
  the only shipped book. The old London book is a dependence measurement, not a
  candidate — 6.9% P(bust) at native sizing, median worst day −$1,292 against an
  $853 budget (`docs/REPORT-correlation-2026-08-04.md`). Until a second strategy
  ships, the selector has nothing to select and this document simply waits. This is
  itself a reason nothing is built now.
- Each pair in the eligible universe has cleared (or been explicitly waived
  through) the correlation thresholds of `docs/REPORT-correlation-2026-08-04.md` —
  max pairwise |ρ| 0.30, tail dependence ≤ 0.25, ≥ 60 both-active days, combined
  P(bust) ≤ 1.0%, the ≥3-shared-input-family veto — all [PROPOSED — Angus to
  ratify] there, their own ratification list.
- The account-architecture ruling (§2.0). [OPEN — needs Angus]

### 6.3 Holdout sequencing

The selector's evaluation runs on the fit span. Its sealed-2023/24 confirmation is
**one declared look for the selector family** (`docs/VALIDATION-PROCESS.md` §4:
one look per family, declared in the ledger before computing, never revised after).
It cannot run until every member strategy's holdout book already exists from that
strategy's own promotion — building a member's sealed-span book is itself a look
requiring its own declaration (`docs/REPORT-correlation-2026-08-04.md`:
"computing on the sealed span **is a holdout look**";
`output/london_canon_book_holdout.parquet` is unbuilt). The selector's look is
spent only with a frozen policy and Angus's explicit go, and re-scoring any revised
selector on the sealed span is a new look Angus would have to grant. [EXISTING]

### 6.4 A causal harness, built before the selector plays

Decision at time t uses only ≤ t information; the eligibility sets, briefing
content, and journal state visible to the selector at each decision are archived so
every pick is replayable — the same harness-first rule as run 2
(`docs/HANDOFF-agents-capture.md` §3 rule 1; harness built BEFORE agents play).
The selector's knowledge substrate (which journal, which digests) gets frozen and
named in a build-time addendum to this pre-registration **before** the first scored
run — the substrate is part of the policy. [EXISTING pattern]

---

## 7. Roll-up — everything awaiting Angus

**[OPEN — needs Angus/Pat]:**
1. Account architecture: same account or separate (§2.0, §6.2) — changes what the
   selector optimizes and how B1 is computed. The brief §5 calls it the big one.
2. Fail-closed default when the selector is silent: B1 or A1 as the standing
   mechanical configuration (§0).
3. The emission contract with Brake: ratified and frozen — drafted as
   `docs/CONTRACT-strategy-emission.md` (emission-v0.1-proposed) (§6.1).

**[PROPOSED — Angus to ratify] (defensible defaults, not law until signed):**
4. Decision granularity binding rule, per-day default (§0).
5. The §2.5 comparison statistic and the funded-criterion tiebreak (§2.5).
6. Null replication counts ≥ 1,000 / p ≤ 0.01 family-wise, incl. the
   all-variants-tried correction scope (§4.1).
7. Minimum n: ≥ 30 picks/era cell, ≥ 100 pooled, ≥ 60 both-active days (§4.1).
8. DSR ≥ 0.95 / PBO ≤ 0.25 on the selector-config search (§4.1).
9. Combined P(bust) ≤ 1.0% (§4.1).
10. Kill-criteria list §4.2 and the killed-selector reopening burden.
11. The allocator off-ramp as pre-committed (§4.3).
12. Per-signal contract extension, if that granularity is chosen (§6.1).

**And the standing rule, restated once more because it is the point of the
document: NOTHING IS BUILT — no selector code, prompt, harness, or briefing —
until Angus ratifies this document's bars by signing the block at the top.**
