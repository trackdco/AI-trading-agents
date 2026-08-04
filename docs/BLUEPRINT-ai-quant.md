# BLUEPRINT — the self-learning AI quant (ANGUS 2026-08-04)

The end state, in Angus's words: dispatch an agent — *"find me three profitable
strategies in London, test them against our strategy validation criteria, make sure
they're uncorrelated with other things"* — including sourcing ideas from the
internet, and get back a shelf of validated, mutually-uncorrelated strategies that
Angus hand-picks and trades live. Angus and Brake are building the infrastructure so
that dispatch is efficient instead of hand-cranked.

This document is the map: the full sequencing a candidate strategy walks, which
existing artifact serves each stage, what is still missing, and where autonomy
hard-stops. It invents nothing — every stage cites the doc that governs it.

---

## The operating loop

```
 0 SOURCE      idea intake (Angus/Brake, internet research, vault mining)
 1 PREREG      claim + bars fixed BEFORE testing          VALIDATION-PROCESS §1
 2 SUBSTRATE   L0 census -> L1 fills -> L2 outcomes       VALIDATION-PROCESS §3
 3 REFINE      L3/L4 conditioning search, agent-run       VALIDATION-PROCESS §3.1
 4 GRADE       era split · permutation null · DSR/PBO     VALIDATION-PROCESS §2
 5 OVERLAP     duplicate check, then portfolio battery    pairwise_overlap · battery
 6 HOLDOUT     one declared look, ledger entry            VALIDATION-PROCESS §4
 7 ARITHMETIC  funded-shell MC (conditional on edge)      VALIDATION-PROCESS §6.3
 8 SHELF       vault status: available-unshipped          VAULT-SCHEMA §3.4
 ------------------------------- autonomy ends here -------------------------------
 9 PICK        Angus hand-picks; account-architecture     FOR-ANGUS-rulings §1
10 PROMOTE     ladder rungs 4-6, two-party arming         VALIDATION-PROCESS §6
```

Every stage emits vault records as it runs (claims, jobs, verdicts, tombstones,
correlation edges) — the memory is written by the loop, not reconstructed after it.

### 0. Source

Ideas come from three places, all landing as vault `claim` records with `source`
provenance (VAULT-SCHEMA §3.1, §3.6):

- **Hand experience** — Angus's and Brake's session hypotheses (brief §6).
- **Internet research** — an agent reading the public quant literature and trader
  material. A sourced idea is a claim like any other; its source record names where
  it came from. No special status, no shortcut past any gate.
- **Vault mining** — tombstones whose written reopening burden is now met, and
  mechanism families whose base rates (survivors per family per session) suggest
  under-explored space.

**Intake kill, before any compute:** query the vault by tags — *has anyone tested
this mechanism family in this session?* (VAULT-SCHEMA §5's acceptance test). A live
tombstone on the same question kills the claim at intake unless its reopening burden
is met. This is the cheapest gate in the loop and the first thing memory buys.

### 1. Pre-register

The §1 template: mechanism, family, input columns, session, entry type, acceptance
bars, kill criteria, and the **discretionary baseline** the refinement loop will
chase (hand-log P&L where it exists; stated as unmeasurable where not). Bars are
signable per session (Appendix A pattern) so dispatch doesn't wait on per-claim
signatures once standing bars exist for a session.

### 2. Substrate

L0 census → L1 fills → L2 outcomes through the real engine, gate at every boundary.
The raw substrate of a discretionary strategy is **expected to be unprofitable**
(§3.1) — stage 2's job is a trustworthy substrate, not a profitable one.

### 3. Refine — the agent's core work

The conditioning search of §3.1: sweep pre-declared families over the substrate,
distance-to-baseline as the metric, **every arm logged to the trial ledger** (vault
`job` records) because stage 4's denominators are the total tried. This is the NY
rebuild's two weeks, industrialized.

**MISSING — the refinement-lab harness**: the runner that lets agents execute
sweeps against an emission substrate with automatic trial logging (no self-reported
denominators). The single biggest build between here and the dispatch sentence.

### 4. Grade

Era split (discover fit-2025, validate fit-2026), family-wise permutation null,
DSR/PBO against the ledger's full arm count. **Brake's DSR/PBO models are this
stage** — they grade what the harness produces. MC has no role here (§6.3: never
evidence of edge).

### 5. Overlap — the "uncorrelated with other things" clause

Two instruments, in order, both consuming the standard emission
(CONTRACT-strategy-emission.md):

1. `scripts/pairwise_overlap.py` — same-session redundancy: entry-time twinning,
   concurrent open risk, same-day bleed. Duplicates die here, before the expensive
   questions. Run against every sibling candidate AND every shelf/live strategy.
2. `scripts/correlation_battery.py` — the portfolio question: day-level ρ, tail
   dependence, timing, input-family veto, combined ruin. Thresholds per
   REPORT-correlation-2026-08-04 [PROPOSED — Angus to ratify].

Results land as vault `correlation_edge` records — the accumulating pairwise map of
the whole portfolio.

### 6–7. Holdout, then arithmetic

One declared look per §4 (the ledger is sacred; agents request a look, they never
take one). Then the funded shell converts the surviving edge into money terms.

### 8 → 9. The shelf, and the human pick

Survivors sit at `available-unshipped` with their full paper trail. **The dispatch
sentence ends here**: the agent's deliverable is a stocked shelf, not a live book.
Angus hand-picks against the account-architecture ruling; promotion runs the ladder;
arming stays two-party. The standing laws are unchanged and load-bearing: live
agents get no tools and no open-ended objectives (the London-window incident,
HANDOFF §7); nothing an agent produces self-authorizes anything (§0 law 3).

---

## The memory layer — Obsidian and what "self-learning" means here

Pat is standing up Obsidian as the vault mechanism. That is compatible with
VAULT-SCHEMA as its [PAT'S CALL] storage substrate — Obsidian is markdown files
with YAML frontmatter in a folder, so the schema's requirements port directly:
frontmatter carries the record fields, tags carry the §5 vocabulary, the linter
(§9) still runs on the files, git still provides append-only history. **The one
requirement that must survive the tooling choice: records follow the schema.** A
freeform research notebook is not a vault; provenance blocks, tombstone reopening
burdens, supersession pointers, and the trial ledger are what make the memory
usable by the next agent instead of just voluminous.

Be precise about the learning claim. Desk-run-2 measured **no month-on-month
learning trend** in the trade-management agent's chained self-history (HANDOFF §2)
— "the agent gets smarter by rereading its own journal" is unproven. What provably
accumulates is **institutional memory**: tombstones that stop dead ideas from being
re-tested, correlation edges that make the portfolio map cheaper each time, base
rates per mechanism family that steer sourcing, and a trial ledger that keeps the
statistics honest as search volume grows. The system learns the way the shop
already learns — by writing things down with provenance — at agent speed and scale.
That is the self-learning bet this blueprint makes, and it is measurable: the cost
and death-rate of stage 0–5 per candidate should fall as the vault fills.

---

## State of the build

| Stage | Artifact | Status |
|---|---|---|
| 0 sourcing conventions | claim/source intake, vault-mining queries | **MISSING** (small: conventions + example records) |
| 1 prereg | VALIDATION-PROCESS §1 template | written; standing bars need Angus (Appendix A) |
| 2 substrate | engine, L0–L2 method | EXISTS (NY/London precedent) |
| 3 refinement | §3.1 + **refinement-lab harness** | doc written; **harness is the big build** |
| 4 grade | permutation bars; DSR/PBO | bars proposed; **models = Brake, in flight** |
| 5 overlap | pairwise_overlap, battery, emission contract | **BUILT + proven** (2026-08-04) |
| 6 holdout | §4 + ledger | discipline in place |
| 7 MC | mc_funded_lab | EXISTS |
| 8 shelf | vault statuses | schema written; **mechanism = Pat (Obsidian)** |
| 9–10 pick/promote | rulings memo §1; ladder; arming | rulings owed; arming unchanged |

Dependency order of the missing pieces: **Angus's signatures** (Appendix A, account
ruling, thresholds) → **vault mechanism** (Pat, schema-conformant Obsidian) →
**refinement-lab harness** (spec next, build after DSR/PBO exist to grade its
output) → **sourcing conventions** (cheap, anytime).
