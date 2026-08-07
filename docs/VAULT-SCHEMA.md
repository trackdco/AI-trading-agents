# VAULT SCHEMA — the knowledge vault (v0.1-proposed)

**Status: PROPOSED — awaiting Angus ratification, then Pat builds the mechanism.**
Semantics in this file are Angus's to ratify (brief 2026-08-04 §2b); every mechanism
choice is Pat's and is marked **[PAT'S CALL]**. On ratification, `vault-v0.1-proposed`
drops the `-proposed` suffix — same lifecycle as `docs/journal-schema-freeze.md`
("on sign-off drop `-proposed` from SCHEMA_VERSION"). After ratification the freeze law
of `docs/JOURNAL-SCHEMA-v1.md` applies verbatim: **additions require a version bump
(v0.2+) and never rename or remove v0.1 fields.** Reserved names are listed in §9; do
not improvise names.

Written 2026-08-04 against branch `claude/canon-rebuild-deployment-7m48yv`
(HEAD `db97e96`), the live HANDOFF (2026-08-04), and the ANGUS brief (week of
2026-08-04). Every number in this document is sourced inline; nothing is from memory.

---

## 0. Why this exists — the stale-figure failure, by example

The vault's one job: **a number without provenance is not a fact.** The repo already
paid for this lesson three ways:

1. **`docs/CANON.md` — "the law" — quotes retired numbers today.** Its headline
   (line 26) reads "lucid profile fit +$77,202 / holdout +$44,844 … (reproduce with
   `python -m scripts.funded_book`)". Those are the $150-base figures. Angus moved the
   base $150 → $160 on 2026-07-31 (HANDOVER-pat-arming row N), making the certified
   references **+$82,543 fit / +$48,211 holdout** (`scripts/funded_book.py` docstring;
   `docs/ARMING-REFERENCE.md` §2; live HANDOFF §1). CANON.md's own reproduce command no
   longer produces its own quoted number — and every fresh session is told to read
   CANON.md first.
2. **`docs/RULING-daily-loss-limit.md`** documents a figure quoted from nowhere: "the
   recorded cycle figure is **94%**, not 97% (`docs/SAFETY-SPINE.md:173`); the 97% is
   not in any file" — a number cited from memory, corrected only because someone hunted
   the file:line. The same doc's provenance banner now points at two parquets
   (`output/baseline_book.parquet`, `baseline_book_clean.parquet`) that have since been
   deleted — its pointers dangle.
3. **The canon purge (`d420b10`, 248 files) left living docs citing deleted ones** —
   `docs/PROMOTION-GATE.md`, `docs/CANON-MECHANICAL.md`,
   `docs/FINDING-conf_PM-lookahead-pre-window.md` and others are still cross-referenced
   but gone. The provenance chain snaps exactly where a supersession pointer should
   exist.

The team already invented the fix informally: `docs/ARMING-REFERENCE.md:8` "**UPDATED
2026-07-31 (was stale — Pat caught it)** … anything citing $90,015/$56,409 or a $150
base was the pre-rules book and must not be certified against." The vault makes that
catch structural instead of heroic. Hence the two laws of this schema:

- **PROVENANCE MANDATORY.** Every number in every record sits next to a provenance
  block (§2.2) naming at minimum the commit, the book identity (artifact/generator +
  span + profile + base + overlay), and how to reproduce it. A bare number is a lint
  failure, not a style complaint.
- **SUPERSEDE, NEVER DELETE.** A wrong or retired record gets `status: superseded` and
  a pointer to its replacement (§6). Deletion is what created failure 3 above.

---

## 1. Storage: plain files in the repo, under `vault/`

**Proposal [PAT'S CALL — recommended: plain files in git, for the four reasons
listed below]:** one directory tree of plain-text records, committed to git.

```
vault/
  vocab/                    # controlled tag vocabularies (§5) — one file per axis
    sessions.yaml
    mechanism-families.yaml
  claims/                   # one YAML file per claim
    2026-08-04-volume-reversal-london.yaml
  jobs/                     # one YAML per job, or jobs.jsonl   [PAT'S CALL]
  verdicts/
  strategies/
  tombstones/
  sources/
  edges/                    # correlation edges
  holdout-ledger.yaml       # the single canonical looks ledger (§3.8)
```

**Format: YAML, one file per record** for everything human-authored (claims, verdicts,
strategies, tombstones, sources, edges); **JSONL acceptable for `jobs/`** if Pat wants
runners to append machine-emitted rows — **[PAT'S CALL]**, provided every row carries
the same required fields.

**Why plain files in git, not a database:**

- **Git history IS the audit trail.** The shop's provenance currency is already the
  commit SHA (`armed_sha: 1364cb7`, cert "THIS commit is the R15-certified SHA",
  QA-log entries pinned to `ea20116`/`d420b10`). Records that live in git get that for
  free; records in a DB need it bolted on.
- **Retrieval is grep** (§5's acceptance test). No query engine to build, no server on
  the box, nothing that can be down.
- **Review = ratification.** A claim moving to `pre-registered` is a diff Angus can
  read; the commit is the timestamp proof it happened before the data was pulled —
  exactly the `HOLDOUT-2023-24-PREREGISTRATION.md` mechanism ("It is written and
  committed BEFORE any depth or trades data is pulled").
- **Write-only, fail-soft.** Same contract as every live sink: "write-only, fail-soft,
  never read back into a decision … a full disk cannot raise into the trading loop"
  (`docs/SPEC-adaptive-journal.md` §3). Files satisfy this trivially.

**Mechanism choices left open — all [PAT'S CALL]:** YAML vs JSONL per directory; one
file per record vs per-day bundles for jobs; whether the linter (§9) runs as a
pre-commit hook, a CI job, or a pytest module; index/cache files for faster retrieval
(any index must be derivable, never authoritative).

**Two constraints Pat must design around:**

1. **The live-branch trap.** Provenance enforcement refuses any arm where HEAD differs
   from `armed_sha` in anything but `config/arming.yaml` — "A docs commit is enough to
   make the next arm refuse" (live HANDOFF §4). Vault records want frequent commits;
   the arming branch cannot take them while live. Where vault commits land (separate
   branch merged at re-cert points, or another arrangement) is **[PAT'S CALL]**, but
   the constraint is law and comes from the arming protocol, not from this schema.
2. **Naming collision.** `src/live/vault.py` already exists — the old Stage-2
   market-replay "Vault" component (`docs/REVIEW-stage2-vault.md`). The knowledge
   vault's tooling must not reuse that module name or the word unqualified in code —
   suggest `kvault` or `knowledge_vault` for any module **[PAT'S CALL]**.
3. **The live path never reads the vault.** Not "reads carefully" — never. The vault
   is research memory. Nothing under `src/live/` or `scripts/ny_run.py` may import,
   open, or stat it. (Same isolation reasoning as the no-tools agent design, live
   HANDOFF §7.)

---

## 2. The record envelope and the provenance block

### 2.1 Envelope — fields on EVERY record, all types

| field | type | req | notes |
|---|---|---|---|
| `schema` | str | yes | `vault-v0.1-proposed` (then `vault-v0.1`) |
| `id` | str | yes | Dated records (claim, job, verdict, tombstone, correlation_edge): `{prefix}:{YYYY-MM-DD}:{slug}`, where correlation_edge's prefix is the short form `edge` — mirrors the live order ref `ny:{day}:{seq}` (`src/live/ny_runner.py:133`). Strategy and source records are dateless singletons: `{type}:{slug}`. Immutable once created. Filename = `{YYYY-MM-DD}-{slug}.yaml` in the type directory (dateless: `{slug}.yaml`). |
| `type` | enum | yes | `claim` \| `job` \| `verdict` \| `strategy` \| `tombstone` \| `source` \| `correlation_edge` |
| `created` | date | yes | date the record was first written |
| `author` | str | yes | `angus` \| `pat` \| `brake` \| `chat` (research chat) — who wrote the record, not who ruled |
| `status` | enum | yes | per-type state (§3, §4) |
| `tags` | map | yes* | the three axes of §5. Required on claim/tombstone/strategy/edge; optional elsewhere |
| `links` | map | no | `supersedes`, `superseded_by`, plus type-specific refs (§3). All values are vault ids or repo paths |
| `note` | str | no | free text. Never the home of a number |

*Backfilled records (historical items re-expressed in the schema) additionally carry
`backfilled_from: <doc path + section>` so the original prose stays the verbatim
authority.

### 2.2 The provenance block — MANDATORY next to every number

Any field or table containing a measured or derived number MUST have a sibling
`provenance` block (record-level if all numbers share one origin; per-table otherwise):

```yaml
provenance:
  commit: 87a7a11              # REQUIRED. The SHA at which the number reproduces.
  book:                        # REQUIRED for any book/P&L number. Book identity is
    generator: scripts/funded_book.py     #   (commit, span, profile, base, overlay) —
    artifact: output/aikido_cr_fit.parquet  # the docstring-spec convention, CANON.md row 1
    span: fit                  #   fit | holdout | fit-2025 | fit-2026 | triple-era
    profile: lucid             #   lucid | scaled600 | native | n/a
    base: 160                  #   dollars. The $150-vs-$160 distinction is load-bearing
    overlay: cr                #   cr (rules J/K/L) | none (pre-rules)
  reproduce: "python -m scripts.funded_book --span fit --profile lucid"
  expected: "+$82,543"         # REQUIRED with reproduce — a command whose output is
                               # not stated cannot be checked for drift (the CANON.md
                               # failure mode, §0.1)
  artifacts: [output/rrfloor_sweep_fit_25.parquet]   # per-experiment outputs
  measured: 2026-07-30         # as-of date of the measurement
  measured_by: chat
  seed: 20260727               # REQUIRED when stochastic (grader "deterministic,
                               # seeded"; preregistration seed convention)
  content_sha256: null         # REQUIRED when a sealed list/file is part of identity
                               # (the preregistration day-list SHA-256 pattern)
  holdout_looks_spent: 0       # REQUIRED integer on anything that touched data.
                               # 0 is a statement, not an omission ("fit-only, no
                               # holdout look spent")
  ruled_by: null               # when a number's standing comes from a ruling:
                               # who, date, relay chain ("ANGUS 2026-07-31, relayed
                               # via Pat"), verbatim quote where available
```

Field-level rules:

- `commit` is never "current" or blank. If the origin commit is unknown (backfill), the
  field reads `"[OPEN — needs Angus/Pat]"` — visible debt, not silent absence.
- `reproduce` + `expected` travel together. This is the house style already:
  "`python -m scripts.funded_book --span fit --profile lucid # +$82,543`" (live
  HANDOFF §9).
- `base` and `overlay` exist because their absence is precisely what made
  $77,202/$90,015/$95,194 silently misquotable (§0, §8.2).
- A number quoted from a conversation or from memory is inadmissible. The 97%-not-in-
  any-file case (§0.2) is the precedent: if it is not in a file at a commit, it does
  not go in a record.

---

## 3. Entity types and required fields

Seven types (brief §2b): **claim, job, verdict, strategy, tombstone, source,
correlation edge** — plus the singleton holdout ledger (§3.8). All carry the §2.1
envelope; tables below list type-specific fields.

### 3.1 `claim` — a falsifiable statement queued for testing

The unit of research. **If it ran, it has a claim record** — retrieval (§5) is only
trustworthy if an empty result means "never tested", so off-vault experiments are
banned once the vault exists.

| field | type | req | notes |
|---|---|---|---|
| `statement` | str | yes | one falsifiable sentence ("London rejects overnight-low sweeps harder on high-volume opens") |
| `mechanism` | str | yes | WHY it would work — the causal story, not the pattern |
| `entry_type` | str | yes | per the pre-registration template (brief §2a-1): limit-at-structure, market-on-signal, etc. |
| `proposed_by` | str | yes | person; verbatim quote if it came from chat (tombstones inherit this — "Angus's idea (\"a structural target but minimum x r …\")") |
| `status` | enum | yes | lifecycle of §4 |
| `preregistration` | ref | at `pre-registered`+ | path/id of the prereg (doc or inline block): acceptance bars, kill criteria, seeds, sealed lists with SHA-256 |
| `acceptance_bars` | list | at `pre-registered`+ | frozen at transition (§4); each bar a testable predicate with numbers |
| `kill_criteria` | list | at `pre-registered`+ | "dies if ANY" semantics, the PLAN §9 pattern |
| `holdout_plan` | str | yes | `none` \| `one-look:<family>` — declared intent; an undeclared holdout touch is invalid (§3.8) |
| `links.tested_by` | list | no | job ids |
| `links.verdict` | ref | terminal | the verdict that closed it |
| `links.tombstone` | ref | at KILLED | REQUIRED — no KILLED claim without a tombstone (§7) |

### 3.2 `job` — one concrete run against a claim

The unit that produces numbers. Every number in a verdict must trace to a job.

| field | type | req | notes |
|---|---|---|---|
| `claim` | ref | yes | the claim this run serves |
| `status` | enum | yes | `queued` \| `running` \| `done` \| `failed` \| `abandoned` |
| `command` | str | yes | exact invocation, repo-root relative |
| `commit` | str | yes | SHA the command ran at |
| `seed` | int | when stochastic | |
| `inputs` | list | yes | source ids / book identities consumed (§2.2 `book` shape) |
| `artifacts` | list | at `done` | output paths (the `output/` naming conventions apply: span suffixes, parameter-encoding filenames) |
| `spans_touched` | list | yes | `[fit]`, `[fit, holdout]`, … If `holdout` appears, `ledger_look` is REQUIRED |
| `ledger_look` | ref | conditional | the holdout-ledger entry DECLARED BEFORE the job started (§3.8). A holdout-touching job without one is invalid by construction |
| `executor` | str | yes | `chat` \| `box` \| `brake` |
| `started` / `finished` | datetime | yes / at terminal | |

### 3.3 `verdict` — the graded outcome, against pre-registered criteria

The record serializes the verdict format of `docs/VALIDATION-PROCESS.md` §5.

| field | type | req | notes |
|---|---|---|---|
| `claim` | ref | yes | |
| `jobs` | list | yes | every job whose numbers appear |
| `graded_against` | str | yes | the prereg, by § reference ("Graded against the pre-registered protocol in `docs/PLAN-agents-capture-run.md` §6–§9") |
| `result` | enum | yes | `PASS` \| `FAIL` \| `INCONCLUSIVE` — strictly these three at top level, per `docs/VALIDATION-PROCESS.md` §5; `NARROW PASS` is legal ONLY as a per-criterion value, never top-level. **INCONCLUSIVE blocks exactly like FAIL** (brief §2a-5) — it never promotes, never spends further looks without a new prereg |
| `headline` | table | yes | all arms side by side including controls, every cell under a provenance block |
| `per_criterion` | table | yes | one row per pre-registered criterion with its own result (`PASS`/`FAIL`/`NARROW PASS` seen in practice) and the numbers |
| `killed` | str | yes | what died and why, with the number, or `nothing` — the §5 `Killed:` line (`docs/VALIDATION-PROCESS.md` §5) |
| `caveats` | list | yes | may be empty but must exist — "stated, not hidden" is the standing law; the shuffle FAIL shipped on the table |
| `what_runs_next` | str | yes | the verdict format of `docs/VALIDATION-PROCESS.md` §5: "what ran, PASS/FAIL with the numbers, anything killed and why, what runs next" |
| `ruling` | map | when ruled | `who`, `date`, `relay` chain, `quote` verbatim. A ruling can override a FAIL for shipping purposes (§8.2) — the verdict still records FAIL; the ruling is a separate, attributed act |
| `provenance` | block | yes | §2.2, incl. `holdout_looks_spent` |

### 3.4 `strategy` — a shippable/shipped trading policy

| field | type | req | notes |
|---|---|---|---|
| `status` | enum | yes | `candidate` → `holdout-confirmed` → `certified` → `live` → (`retired` \| `superseded`), plus `available-unshipped` (the 25%-partial state: PASSED holdout, Angus ruled base V8 stays — "documented as available, unshipped") — vocabulary is the repo's own |
| `spec` | ref | yes | the authoritative spec ("the spec is the `scripts/funded_book.py` docstring") |
| `book` | map | yes | §2.2 book identity of its current reference numbers |
| `reference_numbers` | table | yes | fit/holdout net, worst day, maxDD, months green — each under provenance |
| `gates` | list | at certified+ | R-numbers with closure evidence pointers (ARMING-REFERENCE §4 rows) |
| `conformance` | ref | at certified+ | the lock ("`tests/test_canon_scorer_ny.py`, 19 tests") |
| `account` | str | at live | |
| `links.edges` | list | yes once >1 strategy | correlation edges touching this strategy |
| `links.claims` | list | no | surviving claims folded in |

### 3.5 `tombstone` — a closed question with a reopening burden

See §7. Summary of fields: `closes_claim` (req — claim ref OR session tag, the
session-level tombstone of `docs/VALIDATION-PROCESS.md` §7.2), `question` (req), `proposed_by` +
verbatim quote, `what_ran` (engine identity — "through the REAL engine on the canon
fills", never a proxy), `spans_consumed` (req), `result_table` (req, under provenance),
`mechanism_of_failure` (req — WHY, not just the number), `conclusion` (req),
`reopening_burden` (**req, non-empty**), `provenance` (req, incl.
`holdout_looks_spent` stated even when 0).

### 3.6 `source` — a thing numbers come from

Formalizes what the repo does with LAW/FROZEN/SUPERSEDED stamps, and makes dangling
pointers detectable.

| field | type | req | notes |
|---|---|---|---|
| `kind` | enum | yes | `doc` \| `parquet` \| `jsonl` \| `script-docstring` \| `dataset` \| `vendor-file` \| `ruling` |
| `path` | str | yes | repo-relative (or box path, flagged) |
| `status` | enum | yes | `law` \| `frozen` \| `current` \| `stale` \| `superseded` \| `void` \| `deleted` |
| `asof` | date | yes | last date the source was known good |
| `content_sha256` | str | for sealed kinds | the preregistration pattern |
| `links.superseded_by` | ref | at superseded/deleted | REQUIRED — this is the §6 rule; `docs/PROMOTION-GATE.md` would today be `status: deleted` with a pointer at ARMING-REFERENCE §4, and the RULING-daily-loss-limit parquets would resolve instead of dangling |

### 3.7 `correlation_edge` — a measured (or pending) pairwise relationship

Correlation is not one number (brief §3) — the edge carries the whole battery.

| field | type | req | notes |
|---|---|---|---|
| `strategies` | list[2] | yes | strategy ids, order-insensitive |
| `status` | enum | yes | `queued` \| `measured` \| `stale` (a `reopens_on` condition fired) |
| `common_span` | str | at measured | |
| `active_days` | map | at measured | per-strategy and both-active counts |
| `measurements` | map | at measured | Pearson AND Spearman (union and both-active universes, each with bootstrap CI and n), tail co-crash at decile conditioning with the independence floor stated, both-red-decile days observed vs expected, timing-overlap minutes, combined ruin (paired vs pairing-shuffled P(bust)), input families shared (count, of, names) |
| `thresholds_ref` | ref | at measured | the ratified threshold set evaluated against. Currently `[PROPOSED — Angus to ratify]` (§10.3) |
| `evaluation` | str | at measured | which thresholds clear/trip; a tripped veto names whose call the waiver is |
| `reopens_on` | list | yes | conditions that flip `measured` → `stale` — the R10b convention ("any feed/config change REOPENS with a fresh capture + floor") applied to edges: book change on either side, sizing/budget regime change, ruled account-architecture change |
| `provenance` | block | at measured | §2.2 — incl. `holdout_looks_spent` (see §8.3: a holdout replication IS a look and is declared, or not run) |

### 3.8 The holdout ledger — singleton, append-only

Not an entity type; one file, `vault/holdout-ledger.yaml` — the canonical ledger home
ONCE the vault is ratified. Until ratification, `docs/VALIDATION-PROCESS.md` §4.2 is
the interim home and the source of the rule text + backfill table. Before that, the
ledger lived scattered ("restated with its count in each successive handoff" —
currently "Looks spent so far: 5, each declared before looking", live HANDOFF §7).
Each entry: `look` (int, monotonically increasing), `family`,
`claim` ref, `declared` (date — must precede any job's `started` that cites it),
`spent` (date or `UNSPENT`), `result` ref (verdict id). Backfill: the table in
`docs/VALIDATION-PROCESS.md` §4.2 — the five spent looks
enumerated in `docs/HANDOFF-agents-capture.md` §0–§1, and the agent layer's one-shot
look recorded as declared-UNSPENT. Append-only; an entry is never edited after
`spent` is set. Format **[PAT'S CALL]**.

---

## 4. Claim status lifecycle

The lifecycle mirrors `docs/VALIDATION-PROCESS.md` §§1–7.

```
proposed  →  queued  →  pre-registered  →  testing  →  SURVIVED
                                                    →  KILLED (tombstone required)
```

| state | entered by | requirements to enter | who moves it |
|---|---|---|---|
| `proposed` | writing the record | statement + mechanism + tags (§5) | anyone |
| `queued` | acceptance onto the board | Angus accepts; priority optional | Angus |
| `pre-registered` | committing the prereg | acceptance bars + kill criteria + seeds + sealed lists (SHA-256) written and committed BEFORE any data is pulled or scored — the `HOLDOUT-2023-24-PREREGISTRATION.md` mechanism. Bars are frozen at this transition (§9 lint hashes them); "Any threshold that moves makes this a fit, not a holdout" | Angus signs the bars (brief §0: "acceptance bars pre-registered — yours to sign") |
| `testing` | first job starts | jobs reference the claim; holdout touches require a declared ledger look | executor |
| `SURVIVED` | verdict `PASS` | terminal. **SURVIVED ≠ shipped**: shipping is a separate Angus ruling on the strategy/promotion side — precedent: the 25% partial PASSED holdout (+$60,017 vs +$56,409) and stays `available-unshipped` by ruling | verdict record only |
| `KILLED` | verdict `FAIL` | terminal. A tombstone record (§7) MUST exist and be linked before the transition is valid | verdict record only |

- A verdict of `INCONCLUSIVE` blocks exactly like FAIL (brief §2a-5): the claim does
  not promote and spends nothing further. INCONCLUSIVE on the declared holdout look
  → `KILLED`, tombstone required, per `docs/VALIDATION-PROCESS.md` §7.1 criterion 7.
  Routing after a fit-span INCONCLUSIVE — back to `queued` for a fresh prereg, or
  straight to `KILLED` — is **[OPEN — needs Angus]** (§10.2); the [OPEN] routing
  question applies to fit-span INCONCLUSIVE only. Until ruled, those claims sit in
  `testing` with the blocking verdict linked.
- **Never revise a claim after its holdout look** (brief §2a-4). Post-look edits to
  anything but `status`/`links` are lint failures.
- Terminal states are forever. New evidence means a NEW claim whose prereg must meet
  the old tombstone's `reopening_burden` — the claim links `supersedes:` the old one.
- Orthogonal annotations (not lifecycle states): `RETRACTED`, `SUPERSEDED`, `VOID`,
  `WITHDRAWN` — the repo's existing vocabulary — plus `dormant` (strategies/claims
  parked by a session-kill, `docs/VALIDATION-PROCESS.md` §7.2). Any of these may
  stamp a record post-terminal
  via `status_annotation` + a pointer. Example already on the books: "rr_floor 1.5
  RETRACTED 2026-07-26 — 80% of the gain was one degenerate 6pt-stop fill"
  (`docs/RULING-mechanical-only.md`).

---

## 5. Tag vocabulary — how retrieval works

Three controlled axes on every claim, tombstone, strategy, and edge. Controlled means:
values come from `vault/vocab/*.yaml`; adding a value is a one-line PR; improvised
values are lint failures (the JOURNAL-SCHEMA-v1 "do not improvise names" law).

| axis | field | starter values (sourced) |
|---|---|---|
| session | `tags.session` | `ny-pre` (08:00–09:30), `ny-gold` (09:40–10:30) — the canon's two sessions; `london` — Brake's lane. Extend per session actually defined |
| mechanism family | `tags.mechanism_family` | the seven measured input families of `docs/REPORT-correlation-2026-08-04.md`: `depth-walls`, `overnight-structure`, `order-flow`, `vwap`, `trigger-density`, `structural-events`, `pattern-taxonomy`; plus claim-mechanism families with repo history: `exit-mechanics` (the exit lab), `sizing` (risk-lab sweep), `calendar` (weekday effects, killed for era-flipping — QA-LOG entry 51), `volume`, `reversal` |
| input columns | `tags.input_columns` | actual column names the mechanism reads (`dep_wall_below_d`, `WALLSZ`, `cvd15`, …) — free-form but real: a named column must exist in a feature matrix |

Starter lists are **[OPEN — needs Angus]** to ratify (§10.5); the axes themselves are
the schema.

**The acceptance test** (brief §2b: "folders won't answer it, tags will"):

> "Has anyone tested a volume-based reversal in London?"

must be answerable from the vault alone, mechanically:

```bash
grep -rl 'session:.*london' vault/claims vault/tombstones \
  | xargs grep -l -E 'mechanism_family:.*(volume|reversal)'
```

The schema PASSES the test iff: (a) the query returns every matching claim/tombstone;
(b) each returned record's `status` + `links` answer what happened (tested and KILLED →
the tombstone with its reopening burden; SURVIVED → the verdict; in flight → the
prereg) **without opening any prose doc**; and (c) an empty result is trustworthy —
which holds only under the §3.1 rule that every experiment has a claim record. Pat
should wire this exact query (any mechanism — **[PAT'S CALL]**) as a vault CI check
with a seeded fixture.

---

## 6. The supersession rule

**Mark superseded with a pointer to the replacement. Never delete.** (Brief §2b,
verbatim.)

1. A superseded record keeps its content untouched, gains `status: superseded` (or
   `status_annotation: superseded` on terminal records), `links.superseded_by: <id>`,
   `superseded_date`, and `superseded_by_whom`.
2. The replacement carries the back-pointer `links.supersedes: [<id>]`.
3. `links.superseded_by` non-empty is REQUIRED the moment the status lands — a
   superseded record with no pointer is the CANON.md failure (§0.1) formalized as a
   lint error.
4. Deletion is forbidden while any record references the id — and since references are
   forever, effectively forbidden always. The `d420b10` purge (248 files, dangling
   citations in five living docs — §0.3) is the precedent this rule exists to prevent.
   What the purge got right — "deleted, not deprecated … do not reconstruct it from
   git history and treat it as truth" — is preserved by `status: void`: the record
   stays, its numbers are marked untrustworthy, the pointer says what replaced it.
5. Done well, the shop already does this: "**SUPERSEDED (2026-07-31)** … rows M/N,
   gate R15, grading in docs/REPORT-desk-run-2.md" (HANDOVER §6); "(later superseded,
   entry 54)" (QA-log). The rule makes the good examples the only legal form.

---

## 7. The tombstone requirement

**Every kill records what was tested, on what span, the result, and what evidence
would justify reopening it** (brief §2b). Modelled verbatim on the rr_floor tombstone
(`docs/HANDOFF-agents-capture.md` §0, committed at `87a7a11`), whose anatomy is the
required field list:

1. `closes_claim` + CLOSED date — "(CLOSED 2026-07-30, fit-only, no holdout look
   spent)";
2. `spans_consumed` + `provenance.holdout_looks_spent` — the look accounting is stated
   even when zero;
3. `proposed_by` with the verbatim quote — whose idea it was;
4. `what_ran` naming the engine — "ran the full ladder through the real engine on the
   canon fills", never a proxy;
5. `result_table` — the numbers, all arms;
6. `mechanism_of_failure` — WHY it fails ("a higher floor is increasingly an ENTRY
   change wearing an exit costume"), not just that it fails;
7. `conclusion` — what stands ("The 2.0 floor was already right; the first-leg PARTIAL
   is the live lever");
8. `reopening_burden` — **non-empty, always** ("Burden for ever reopening: a
   triple-era result at least as strong as this monotone ladder");
9. `provenance.artifacts` — the parquets.

A claim cannot reach `KILLED` without a linked tombstone (§4). A tombstone's
`reopening_burden` is the acceptance bar any future claim on the same question must
pre-register against (§4, terminal-states rule). Two more in-repo instances confirm
the shape generalizes: the profit-taking family close (25 arms, "ZERO additional
holdout looks spent … Uniform mechanics are exhausted BY MEASUREMENT") and the
time-based-cut kill ("the burden of proof for ever adding one is a triple-era result
at least as strong as what killed it here").

---

## 8. Worked examples

Three records, fully expressed. These are backfills: `backfilled_from` names the prose
authority; the YAML is the retrieval surface, the prose stays verbatim truth.

### 8.1 The rr_floor tombstone, re-expressed

Source: `docs/HANDOFF-agents-capture.md` §0 (committed `87a7a11`). Note what
provenance forces into the open: these dollars are the **pre-rules (pre-J/K/L),
$150-base, 956-entry book** — floor 2.0's $90,015 is exactly the figure
ARMING-REFERENCE §2 warns "must not be certified against". The kill is the monotone
*shape*, which survives; the absolute dollars do not transfer to the current book.
Without `base`/`overlay` fields, that distinction lives in one person's memory.

```yaml
schema: vault-v0.1-proposed
id: tombstone:2026-07-30:rr-floor
type: tombstone
created: 2026-07-30
author: chat
backfilled_from: "docs/HANDOFF-agents-capture.md §0 (TOMBSTONE — the rr_floor question)"
status: closed
closes_claim: "claim:2026-07-30:rr-floor-ladder"   # backfill stub — claim predates the vault
question: >
  Does raising the structural-target minimum-R floor above the shipped 2.0
  improve the funded book?
proposed_by: angus
proposed_quote: '"a structural target but minimum x r COULD be the course of action"'
what_ran: >
  The full floor ladder (2.0/2.5/3.0/4.0) through the REAL engine on the canon
  fills — not a proxy.
spans_consumed: [fit]
result_table:
  columns: [floor, n_entries, funded_net_usd, win_days, win_meanR]
  rows:
    - [2.0, 956, 90015, 150, 1.75]   # <- shipped, already right
    - [2.5, 944, 88893, 144, 1.78]
    - [3.0, 922, 86248, 139, 1.82]   # maxDD worsens $1,603 -> $1,711
    - [4.0, 884, 81463, 136, 1.89]   # WR 50% -> 47%
mechanism_of_failure: >
  Deeper floors DO pay more per winner (win meanR 1.75 -> 1.89) but the reach
  ladder caps it (48% touch 2R in-trade, 23% touch 3R) and the veto contamination
  grows 12 -> 34 -> 72 entries — a higher floor is increasingly an ENTRY change
  wearing an exit costume. Funded net and win-day count fall monotonically.
conclusion: >
  The 2.0 floor was already right; the first-leg PARTIAL is the live lever.
reopening_burden: >
  A triple-era result at least as strong as this monotone ladder.
provenance:
  commit: 87a7a11
  book: {generator: scripts/sweep_rr_floor.py, span: fit, profile: lucid,
         base: 150, overlay: none}     # pre-J/K/L 956-entry book — absolute $ are
                                       # that era's; the monotone kill is what stands
  artifacts:
    - output/rrfloor_sweep_fit_25.parquet
    - output/rrfloor_sweep_fit_30.parquet
    - output/rrfloor_sweep_fit_40.parquet
  measured: 2026-07-30
  measured_by: chat
  holdout_looks_spent: 0               # "fit-only, no holdout look spent"
tags:
  session: [ny-pre, ny-gold]
  mechanism_family: [exit-mechanics, structural-events]
  input_columns: [rr_floor]
links:
  related: ["docs/RULING-mechanical-only.md"]   # rr_floor 1.5 RETRACTED 2026-07-26
```

### 8.2 The desk-run-2 grading as a `verdict` record

Source: `docs/REPORT-desk-run-2.md` (committed `8e592e9`). This example carries the
schema's two hardest lessons at once. First: the protocol result is **FAIL** —
criterion 4 tripped and the pre-commitment was "dies if ANY" — while the layer
SHIPPED anyway by an attributed Angus ruling on a criterion outside the prereg (funded
risk shape). The verdict records the FAIL; the ruling is a separate, quoted act. That
separation is the R10b lesson ("nothing here self-authorizes") in schema form.
Second: every dollar figure below is the **$150 base** — the run predates row N — and
the record says so, with the pointer to the $160-base references, so nobody quotes
$95,194 as current (today `docs/REPORT-desk-run-2.md` itself carries no such marker;
see §10.1).

```yaml
schema: vault-v0.1-proposed
id: verdict:2026-07-30:desk-run-2-phase-1
type: verdict
created: 2026-07-30
author: chat
backfilled_from: "docs/REPORT-desk-run-2.md"
status: final
claim: "claim:2026-07-29:agent-exit-layer"       # backfill stub
jobs: ["job:2026-07-30:desk2-chained-run"]       # backfill stub — runs/desk2/
graded_against: "docs/PLAN-agents-capture-run.md §6-§9 (written 2026-07-30 BEFORE any
  agent verdict was generated)"
result: FAIL          # criterion 4; pre-commitment "the agent arm dies if ANY".
                      # What died is the per-trade-discrimination claim; what
                      # survived is the policy shape — see caveats + ruling.
headline:
  columns: [arm, trade_R_net, funded_lucid_net_usd, funded_lucid_maxDD_usd, worst_day_usd]
  rows:
    - [mech-3-rule-canon, 388.6, 77202, 1268, -670]
    - [agent,             488.7, 95194,   810, -479]
    - [lock1r_2r_control, 480.5, 96433,  2476, -650]
  note: "delta +100.1R over 763 trades, p=0.003, 12/13 months green; WR 59.2% vs
    56.1%; avg winner unchanged (+1.464 vs +1.462), avg loser cut -0.708 -> -0.576"
per_criterion:
  - {n: 1, test: "mean dR <= 0, or positive only via <=3 trades",
     result: PASS, numbers: "+0.131R mean, t=2.94, sign-flip p=0.00325; without top-3 still +81.2R"}
  - {n: 2, test: "loses to best mechanical control on fit",
     result: NARROW PASS, numbers: "+8.2R over lock1r_2r on R; control wins raw funded
       net ($96.4k vs $95.2k) at 3x the drawdown ($2,476 vs $810); netting moved the
       control +495.1R -> +480.5R — flagged for honesty"}
  - {n: 3, test: "era-split sign flip (2025 vs 2026)",
     result: PASS, numbers: "fit-2025 +38.8R, fit-2026 +61.4R"}
  - {n: 4, test: "conviction shuffle matches real verdicts",
     result: FAIL, numbers: "null >= real with p=0.978; agent timing replays +550.2R,
       null averages +602.5R (sigma 25.9)"}
caveats:
  - "The edge is policy shape (cut losers fast, refuse canon exits on runners), not
     per-trade discrimination — the shuffle preserves the hold-time distribution and
     beats the agent's specific choices."
  - "lock1r_2r captures 92% of the delta mechanically, at 3x the drawdown."
  - "No month-on-month learning trend; the learning hypothesis, as instrumented, is
     not supported."
  - "The measured edge is entirely gold session (+101.3R on 536); pre is flat
     (-1.1R on 227)."
what_runs_next: >
  Natural holdout candidate is a mechanical distillate (defense cuts +
  lock1r_2r-style refusal), not the chain. The one-shot holdout look stays sealed
  and UNSPENT; only a frozen policy earns it. Decision is Angus's.
ruling:
  who: angus
  date: 2026-07-31
  quote: '"remember its a fundd — it prevented lots more losses than where it didnt
    capture winners fully, and thats completely fine."'
  effect: >
    SHIPPED to live as-is on the funded risk-shape criterion (maxDD $810 vs the
    distillate's $2,476), with the shuffle FAIL on the table. Frozen v3 spec,
    763-row journal seeded as live memory. Arming detail: HANDOVER row M.
provenance:
  commit: 8e592e9
  book: {generator: scripts/funded_book.py, span: fit, profile: lucid,
         base: 150, overlay: cr}       # run predates row N (base $150 -> $160,
                                       # ANGUS 2026-07-31)
  reproduce: "python scripts/grade_desk_run2.py"
  expected: "+100.1R delta, p=0.003 (deterministic, seeded)"
  artifacts: ["runs/desk2/journal.jsonl (763 rows)", "runs/desk2/transcripts/"]
  measured: 2026-07-30
  measured_by: chat
  seed: "grader-internal (deterministic, seeded)"
  holdout_looks_spent: 0
tags:
  session: [ny-pre, ny-gold]
  mechanism_family: [exit-mechanics]
  input_columns: [agent_R, v8_R, mfe_R, capture]
links:
  superseded_by_numbers: >
    $160-base references — mech lucid +$82,543 fit / +$48,211 holdout; WITH agent
    layer +$100,297 fit (worst day -$542, maxDD $878). Live HANDOFF 2026-08-04 §1;
    scripts/funded_book.py docstring. This verdict's dollar figures are the $150-base
    run and must not be quoted as current references.
```

### 8.3 The NY↔London correlation edge — queued, then measured

The task brief anticipated this edge as a placeholder "awaiting this week's
measurement". The measurement has since landed (`db97e96`,
`docs/REPORT-correlation-2026-08-04.md`) — so this example shows **both snapshots**,
which is the lifecycle demonstration anyway: the queued form any new pair starts in,
and the measured form that replaces it in place (same id, status flips, history in
git).

The queued form (what this record looked like before Friday):

```yaml
schema: vault-v0.1-proposed
id: edge:2026-08-04:ny-canon--london-old
type: correlation_edge
created: 2026-08-04
author: chat
status: queued
strategies: ["strategy:ny-canon", "strategy:london-old-book"]
note: >
  Never measured — both books have been leaning on assumptions about it (ANGUS
  brief 2026-08-04 §3). Known before measurement: zero clock overlap (NY taken
  fills 08:00–10:29 ET, 762 trades, funded lucid fit; old-London taken fills
  03:01–05:50 ET — min/max of the 136 taken fills,
  output/london_canon_book.parquet, measured 2026-08-04; supersedes the
  03:02–05:54 range quoted in the HANDOFF/brief), so the only contention channel
  is the shared budget.
measurements: null
reopens_on: [book-change-either-side, sizing-regime-change, account-architecture-ruling]
```

The measured form (current — all numbers from `docs/REPORT-correlation-2026-08-04.md`):

```yaml
schema: vault-v0.1-proposed
id: edge:2026-08-04:ny-canon--london-old
type: correlation_edge
created: 2026-08-04
author: chat
backfilled_from: "docs/REPORT-correlation-2026-08-04.md"
status: measured
strategies: ["strategy:ny-canon", "strategy:london-old-book"]
common_span: "2025-06-02..2026-07-08"
active_days: {ny: 230, london: 109, both: 99}
measurements:
  pearson_union:        {value: -0.094, ci95: [-0.185,  0.003], n: 240}
  spearman_union:       {value: -0.096, ci95: [-0.216,  0.026], n: 240}
  pearson_both_active:  {value: -0.110, ci95: [-0.265,  0.065], n: 99}
  spearman_both_active: {value: -0.086, ci95: [-0.273,  0.104], n: 99}
  tail_cocrash_decile:  {value: 0.10, independence_floor: 0.10}
  both_red_decile_days: {observed: 1, expected_independent: 1.0}
  tail_conditional_pearson: {value: -0.451, n: 19,
    note: "direction only at n=19 — hedging, not stacking, on the days that matter"}
  timing_overlap_minutes: 0
  combined_ruin: {paired_pbust: 0.005, shuffled_pbust: 0.004,
    note: "payout-free comparative MC, mechanical NY book — a comparison statistic
      between rows, not a funding forecast"}
  input_families_shared: {count: 3, of: 7,
    families: [depth-walls, overnight-structure, order-flow]}
thresholds_ref: "docs/REPORT-correlation-2026-08-04.md 'Proposed thresholds'
  [PROPOSED — Angus to ratify]"
evaluation: >
  Clears proposed thresholds 1-4 at native/separate sizing. TRIPS the proposed
  input-family veto (3 shared >= 3): on returns the books are indistinguishable
  from independent, but structurally they are cousins — the waiver is Angus's
  call, mitigating evidence being zero clock overlap, tail independence, and
  negative point correlation. Shared-budget accounting NOT yet measured — blocked
  on the account-architecture ruling.
reopens_on:
  - book-change-either-side
  - shared-budget-accounting (account-architecture ruling + emission contract)
  - london-holdout-book-build
provenance:
  commit: db97e96
  book:
    - {generator: scripts/funded_book.py, artifact: output/funded_book_lucid_fit.parquet,
       span: fit, profile: lucid, base: 160, overlay: cr,
       note: "regenerated at 2157069, prints the reference +$82,543"}
    - {generator: scripts/london_canon.py, artifact: output/london_canon_book.parquet,
       span: fit, profile: native, base: n/a, overlay: none, note: "rows with size>0 only"}
  reproduce: "python -m scripts.correlation_battery"
  expected: "union Pearson -0.094; see output/correlation_battery_report.md"
  artifacts: [output/correlation_battery_report.md,
              output/correlation_daily_ny_london.parquet]
  measured: 2026-08-04
  measured_by: chat
  seed: 7          # 10k-resample bootstrap CIs, 2,000-sim ruin MC
  holdout_looks_spent: 0   # holdout replication deliberately NOT run — computing on
                           # the sealed span IS a look and was not declared
tags:
  session: [ny-pre, ny-gold, london]
  mechanism_family: [depth-walls, overnight-structure, order-flow, vwap,
                     trigger-density, structural-events, pattern-taxonomy]
  input_columns: []
links:
  supersedes: ["source:london-canon-docstring-daycorr"]   # the +0.11 pre-rules figure
    # in the scripts/london_canon.py docstring — sign flips against the shipped book
    # (-0.09/-0.11). "Per the stale-figure rule, quote this report, not the docstring."
```

---

## 9. Validation — what Pat's linter enforces

Mechanism (pre-commit hook, CI, pytest module) is **[PAT'S CALL]**; the rules are
schema:

1. **Referential integrity.** Every id in `links`/`claim`/`jobs`/`closes_claim`
   resolves. No record is ever deleted (§6.4).
2. **Provenance completeness.** Any numeric leaf outside a `provenance` block must
   have a sibling `provenance`. `commit` non-empty (or the explicit
   `"[OPEN — needs Angus/Pat]"` marker); `reproduce` implies `expected`; book numbers
   carry the full book identity incl. `base` and `overlay`;
   `holdout_looks_spent` present on anything that touched data.
3. **KILLED implies tombstone**, linked both ways, with non-empty `reopening_burden`.
4. **superseded implies pointer** (`links.superseded_by` resolves).
5. **Prereg freeze.** At `proposed/queued → pre-registered`, the linter records a
   SHA-256 over `acceptance_bars` + `kill_criteria` + `preregistration`; any later
   change to those fields fails. Post-holdout-look, any edit outside
   `status`/`links` fails (§4).
6. **Holdout discipline.** A job with `holdout` in `spans_touched` must cite a
   `ledger_look` whose `declared` date precedes the job's `started`. Ledger is
   append-only; `spent` entries immutable.
7. **Controlled vocabulary.** `tags.session` and `tags.mechanism_family` values must
   exist in `vault/vocab/`.
8. **Result gating.** A claim may reach `SURVIVED` only via a linked verdict with
   `result: PASS`; `FAIL` and `INCONCLUSIVE` both block promotion.
9. **The retrieval acceptance test** (§5) runs against a seeded fixture.

Reserved field names for later versions (do not improvise): `dsr`, `pbo`,
`family_wise_null`, `portfolio_contribution`, `regime_tag` — the brief's planned bars
(§2a-2, §3) that do not yet exist as practice; their definitions are
`docs/VALIDATION-PROCESS.md` §2.4's, and the fields activate via a schema version
bump.

---

## 10. Open items — decisions explicitly left for Angus

1. **[OPEN — needs Angus] Stale-doc refresh policy.** `docs/CANON.md` and
   `docs/REPORT-desk-run-2.md` both quote $150-base figures with no marker (§0.1,
   §8.2). Banner-update them to $160, or freeze them with a supersession pointer?
   Both currently mislead silently; nothing in-repo states the policy for refreshing
   "the law" doc itself. The vault's §6 rule implies the pointer option, but the call
   on the prose docs is Angus's.
2. **[OPEN — needs Angus] INCONCLUSIVE routing (fit-span only).** After a fit-span
   INCONCLUSIVE verdict (which blocks like FAIL), does the claim return to `queued`
   for a fresh pre-registration, or go to `KILLED` with a tombstone? §4 leaves it
   parked in `testing` until ruled. Not open: INCONCLUSIVE on the declared holdout
   look → `KILLED`, tombstone required, per `docs/VALIDATION-PROCESS.md` §7.1
   criterion 7.
3. **[OPEN — needs Angus] Correlation thresholds ratification.** The five proposed
   numbers in `docs/REPORT-correlation-2026-08-04.md` (max |rho| 0.30; tail <= 0.25;
   min 60 both-active days; max combined P(bust) 1.0%; >=3 shared families = veto)
   are all marked [PROPOSED — Angus to ratify] — including the NY↔London
   input-family-veto waiver the measured edge trips (§8.3).
4. **[OPEN — needs Angus/Pat] Canonical holdout day count.** The pre-registration
   drew 128 days; `docs/HANDOFF-agents-capture.md` and QA-LOG entry 27 cite "122
   days". Which count do vault records cite?
5. **[OPEN — needs Angus] Tag vocabulary starter lists.** §5's session and
   mechanism-family values need ratification before Pat seeds `vault/vocab/`.
6. **[OPEN — needs Angus/Pat] Backfill scope.** Which historical records get
   re-expressed in week one? Minimum useful set: the three §8 examples, the five
   spent holdout looks + the UNSPENT agent look (§3.8), the standing tombstones
   (profit-taking family, time-based cuts), and `source` records for the LAW docs
   and the known-deleted ones (§0.3).
7. **[OPEN — needs Angus/Pat] Vault commits vs the live arming branch.** §1's
   constraint 1: frequent vault commits cannot land on the armed branch without
   tripping provenance refusal. The branching/merge cadence is Pat's mechanism, but
   whether vault currency is allowed to lag live re-certs is a process ruling.
8. **[OPEN — needs Angus] The holdout ledger's single home.** §3.8 makes
   `vault/holdout-ledger.yaml` the canonical ledger home once the vault is ratified;
   until then `docs/VALIDATION-PROCESS.md` §4.2 is the interim home and the source of
   the rule text + backfill table. Confirm that the vault file, once ratified, is THE
   ledger and handoffs (and §4.2) merely cite it.
9. **[PAT'S CALL] Storage substrate.** §1's files-in-git proposal is itself a
   mechanism choice (brief: mechanism is Pat's). Pat to accept or replace the
   files-in-git substrate; the four reasons in §1 are the recommendation, not a
   ruling.
