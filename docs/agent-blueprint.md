# The Desk — Phase 3 Agent Blueprint

**Status: DESIGN DRAFT — input to Spec 3. Not executable. Nothing in this document is built.**

| | |
|---|---|
| Lane | Pat (agents & bots, per `context/TEAM.md`) |
| Purpose | Have the five-agent design fully worked out so Spec 3 can be written fast and Phase 3 executed immediately after the Phase-2 calibration review |
| Authority | None. Spec 3 is written with Angus after Phase 2 and supersedes anything here. Items marked **PROPOSED** or **NEEDS-ANGUS** are suggestions, not decisions |
| Grounding | `strategy-definition-v1.0.md` (the constitution), `context/architecture.md`, `context/ai-workflow-rules.md`, and the **real** engine interfaces as of Step 6: `src/engine/snapshot.py` (`Snapshot`, `Cluster`, `Level`), `src/engine/triggers.py` (`Trigger`), `config/strategy.yaml` |
| Raw design material | `docs/agent-blueprint-design/*.json` — the full per-lane design artifacts this document summarizes |

---

## 1. Plain-English overview

The Desk is five judges. A deterministic Python engine spots a candidate trade and
writes two cards: a **Snapshot** (everything the market looks like right now) and a
**Trigger** (the candle pattern it found). Four specialist judges each check ONE
aspect of the candidate against the written rulebook — and only that aspect:

- **Atlas** — *where*: are the levels and clusters legal, is the location acceptable?
- **Helios** — *when*: is the clock, session, and news context right?
- **Apollo** — *what*: is the candle anatomy really the pattern the engine claims?
- **Hephaestus** — *how*: are the entry, stop, target, and size exactly what the rulebook commands?

**Hermes** is the clerk, not a judge: it hands each judge only their permitted slice
of the cards, collects four pass/fail verdicts, and requires **unanimity** — one
fail, any fail, even a late or malformed answer, and the candidate is vetoed. The
verdict (trade or veto, always with reasons) goes to the Vault, the deterministic
risk layer, which alone talks to the world.

The Desk's value is **not** that the LLM is smarter than the Python. It is:

1. **Independent re-derivation** — each judge recomputes the mechanical rules from
   raw snapshot values. If the engine has a bug or stale config, the recompute
   disagrees and the trade is vetoed loudly. (This already worked: designing these
   checks surfaced nine engine-vs-doc discrepancies — §8.)
2. **Judgment-shaped gates** — a small number of checks (location quality, pattern
   mechanism coherence) that pure arithmetic can't own. Every such judgment is
   anchored to enumerated evidence, never vibes or confidence scores.
3. **An auditable thesis** — every verdict carries a §-cited explanation a human
   can check against the rulebook in seconds.

## 2. Non-negotiables (inherited, restated)

1. **Agents propose; they never act.** No agent has any outbound channel — no
   Telegram, no orders, no network, no file writes. The Vault alone talks to the
   world (strategy §11, architecture invariant 6, `docs/telegram-setup.md`).
2. **Agents never see:** account state, P&L, prior trades, trade counts, halt
   status, open positions, or each other's outputs. Structurally enforced (§6.1).
3. **Fail-closed everywhere.** Invalid JSON, schema violation, timeout, missing
   field, unresolvable input → FAIL → veto. "Anything but valid schema JSON is a
   bug" (ai-workflow-rules). Hermes itself enjoys no exemption: the Python runner
   re-validates Hermes's output and vetoes on mismatch.
4. **No LLM arithmetic is load-bearing.** Every number in a Verdict is a verbatim
   copy from the Trigger or a specialist output, or a fixed-table result the
   Python runner independently recomputes and asserts.
5. **A prompt edit IS a strategy change** — versioned, hashed, gated (§6.4).
6. **When the doc and the engine disagree, neither is silently "fixed."** The
   specialist follows the doc, fails the check, and the divergence goes to Angus.

## 3. System position

```
Engine (Python): triggers.py fires one arbitrated Trigger + one Snapshot per candle close
        │
        ▼
Desk runner (Python, deterministic): validate pair → project per-agent slices
        │
        ├─────────────┬──────────────┬──────────────┐   (parallel, isolated)
        ▼             ▼              ▼              ▼
      Atlas         Helios         Apollo      Hephaestus     (Claude subagents)
        └─────────────┴──────┬───────┴──────────────┘
                             ▼
      Hermes (orchestration only) → one Verdict JSON (unanimity or veto-with-reasons)
                             │
                             ▼
      Runner re-validates + recomputes size/grade  →  VAULT (risk gates, journal, Telegram)
```

In **backtest mode the Desk is bypassed** — `triggers.py` IS the ruleset
(architecture.md). The Desk is a live-only, veto-only layer. The consequences of
that asymmetry are measured, not assumed (§6.6).

## 4. Interface contracts

### 4.1 Engine → Desk (exists today)

Bound to the real pydantic models:

- **`Snapshot`** (`src/engine/snapshot.py`): `ts`, `ref_price`, `session`,
  `htf_regime` (uptrend|downtrend|range|unknown), `indicators`
  (`tfs.{1min,2min,3min,5min}.{bar_ts,bb_basis,bb_upper,bb_lower}`,
  `daily_vwap.{mid,upper_1..3,lower_1..3}`, `ny_vwap.*` — null pre-09:30,
  `daily_profile.{poc,vah,val,...}`), `session_high/low`, `prior_day_high/low`,
  `prior_week_high/low`, `clusters[] {center, confluence_count, types, members}`,
  `data_levels[] {event, impact, data_high, data_low, event_time}`,
  `target_menu[] {name, price, type, distance}`.
- **`Trigger`** (`src/engine/triggers.py`): `ts, tf, direction, kind, pattern,
  htf_flag, entry_ref, stop_ref, wick_low, wick_high, cluster_center,
  confluence_count, close`.

### 4.2 Interface additions REQUIRED before Phase 3 (engine-driver work, Spec-3 scope)

Designing the checks against the real models exposed hard gaps. Without these,
several checks are uncomputable and fail-closed design would veto every
displacement trade:

| # | Addition | Why | Blocks |
|---|---|---|---|
| I-1 | **`Trigger.candle.{open,high,low}`** (full trigger-candle OHLC; `close` exists) | body/range ≥ B_min and extreme-quartile close are uncomputable without the far-side extreme | Apollo APL-4, APL-8; displacement grading entirely |
| I-2 | **`Trigger.atr`** (ATR value used) | ATR floor re-check if `atr_floor_enabled` is ever on | Apollo APL-4 |
| I-3 | **`Trigger.penetrated_levels[]`** (names) + real distinct-type count for displacements | engine hard-codes `confluence_count=2`, `cluster=None` for displacements | Atlas recount, Apollo APL-2, §9 sizing |
| I-4 | **`ProposedConstruction {direction, entry, stop, target_name, target_level, working_target, size}`** computed deterministically by the engine's Step-7 order builder | Hephaestus **validates** a full construction; agents never originate prices | Hephaestus (all gates) |
| I-5 | **`Snapshot.news_context`** `{is_high_impact_day, todays_events[{event, impact, scheduled_ts, occurred}], minutes_to_next_release}` from the calendar (known ex-ante config — NOT lookahead) | without it Helios can never say "normal day", §6.3 can't act pre-release, H4 buffer unimplementable | Helios news_day; Hephaestus §6.3 |
| I-6 | **`Snapshot.session_integrity`** `{is_roll_session, bars_missing_current_session, early_close}` (+ a CME holiday CSV in `config/`) | roll/holiday/gap context is currently LLM guesswork | Helios session_integrity |
| I-7 | **`Snapshot` HTF range extremes** (`htf_range_high/low`, 1h/4h) — already deferred in snapshot.py docstring | §7 location veto + §4 A-via-range-extreme + §6 menu name them | Atlas location_veto, Apollo A-validation |
| I-8 | **`Cluster.members` as `{name, price, type}` objects** (prices included) | name→indicator resolution breaks silently if naming drifts | Atlas, Apollo, Hephaestus recomputes |
| I-9 | **`data_levels[].swept: bool`** (engine-stamped, needs intrabar history) | §6.3 needs "untaken" — no agent can prove it from one snapshot | Hephaestus news override |
| I-10 | **MTF arbitration evidence** (`Trigger.suppressed_tfs[]`) or an explicit ruling that §1 arbitration is engine-trust + unit-test only | nobody can currently audit "highest TF won" | Apollo (or explicit N/A) |
| I-11 | **Shared correlation id** (`trigger_id` echoed in Snapshot+Trigger) | ts-string equality is the only join key today | Runner joins, journal |

### 4.3 Specialist → Hermes (common envelope)

Every specialist returns exactly one JSON object (strict schema,
`additionalProperties: false`), sharing this envelope; per-agent payloads are in
the design artifacts:

```
{ agent: "<name>",               // const per agent
  agent_version: "x.y.z",        // hash-locked, §6.4
  trigger_ts: "<ISO ET>",        // must byte-echo Trigger.ts
  verdict: "pass" | "fail",      // MUST equal AND(all gates)
  gates: { <check_name>: "pass"|"fail"|("not_evaluated" only where structurally N/A) },
  facts: { ... },                // §9 conviction inputs this lane owns (see §5.6)
  <recomputed/computed>: {...},  // shown work: expected vs observed numbers
  data_gaps: [ "<field path>" ], // inputs needed but absent/null
  thesis|finding: "≤ bounded chars, §-cited, no confidence language" }
```

`not_evaluated` is legal ONLY where structurally N/A (the other kind's anatomy
gate; a disabled config flag) and counts as pass; anything else missing = fail.

### 4.4 Desk → Vault: the Verdict

The **pinned core** (architecture.md, unchanged):
`{trade, pattern, direction, entry, stop, target, size, grade, thesis, gates: {atlas, helios, apollo, hephaestus}}`.

Field sourcing: `trade` = AND of gates (Hermes-computed, runner-asserted);
`pattern`/`direction` = verbatim `Trigger` (Apollo disagreement ⇒ veto, never a
rewrite — preserves backtest/live parity); `entry`/`stop`/`target` = copied from
Hephaestus's validated construction; `size` (`full`|`half` — the §9 **unit**
designation; contract count is the Vault's) and `grade` = fixed §9 lookup table,
recomputed by the runner.

**PROPOSED-ADDITIVE fields (NEEDS-ANGUS):** `schema_version`, `ts`, `tf`,
`trigger_kind`, `gate_reasons` (per-agent `{code, detail, refs}` — satisfies §10
"logged with the reason"), `gate_checks` (per-check pass/fail + § ref),
`conviction_facts` (the exact §9 inputs used), `desk_meta` (prompt versions,
allowlist hash, latencies, staleness). Alternative: keep the wire Verdict
pinned-core-only and journal the metadata Desk-side, joined on (ts, tf).

**PROPOSED veto convention:** on veto, `entry/stop/target/size` retain
Hephaestus's values when its output was valid (feeds §12.5 skipped-trade
diagnostics), null otherwise; `grade` always null on veto.

**PROPOSED grade mapping (NEEDS-ANGUS):** with H = count of §9 half-triggers
present ({min-confluence, oversized stop, late-window, thin target}):
**A** ⇔ size full (identical to the §9 full-unit predicate — A and full can never
drift apart); **B** ⇔ half with H ≤ 1; **C** ⇔ half with H ≥ 2. Every boundary is
a §9-traceable count. (Alternative for Angus: drop C.)

## 5. The five agents

Full checks with exact pass conditions, allowlists, output schemas, and edge
cases: `docs/agent-blueprint-design/{atlas,helios,apollo,hephaestus,hermes}.json`.
Summary per lane below. *kind*: `R` = recompute (independent re-derivation of an
engine-computed fact), `J` = judgment (anchored to enumerated evidence).

### 5.1 Atlas — market structure & levels

*Mandate:* everything about **where** — cluster legality, confluence counting,
location, level/menu integrity. Never candle anatomy, clock, or construction.

| Check | § | kind | Pass condition (compressed) |
|---|---|---|---|
| cluster_integrity | §3 | R | a Snapshot cluster matches `Trigger.cluster_center` within tolerance; every member resolves to a non-null indicator price; adjacent gaps ≤ `cluster.tolerance_points`; mean = center |
| confluence_recount | §3 | R | independent distinct-TYPE recount (VWAP family ×1, BB ×1, POC ×1) == cluster count == Trigger count ≥ `cluster.min_level_types` |
| member_legality | §3 | R | every member in the §3 allowlist — NY VWAP **mid/±1σ only, post-09:30 only**; any ±2σ/3σ NY member = FAIL (engine currently emits them — finding E-1) |
| pre0930_vwap_family | §3/inv-1 | R | pre-anchor: all `ny_vwap` fields null, no `nyvwap_*` member anywhere, no `ny_vwap_mid` menu entry |
| htf_flag_consistency | §4 | R | recomputed regime×direction mapping == `Trigger.htf_flag`; regime `unknown` = FAIL (fail-closed; finding E-2) |
| confluence_minimum | §7 | R | Atlas's OWN recount ≥ (with-trend ? min_with : min_counter); `range` flag takes the higher minimum pending Angus (Q-3) |
| location_veto | §7 | J | names an operative range top/bottom from available structural extremes (cited by field name); no long into top / short into bottom within tolerance |
| target_menu_integrity | §6/§2 | R | distances recompute; band/profile ordering sane; every non-null derivable level present; ≥1 opposing level exists; no future-dated data level |

*Key edge cases:* displacement triggers (cluster=None, hard-coded count=2) must
still match a Snapshot cluster — no match = FAIL, not skip; single-linkage
chaining can exceed full-span tolerance (Q-8); equidistant cluster tie broken
deterministically (lower center).

### 5.2 Helios — session, time & news context

*Mandate:* owns the clock. Reads timestamps, nulls, and impact tags — deliberately
**never prices** (`data_high/low` excluded from its allowlist).

| Check | § | kind | Pass condition (compressed) |
|---|---|---|---|
| entry_window_validity | §1 | R | trigger close inside the ACTIVE window (wrap-aware for W2), recomputed from raw config |
| session_label_recompute | §2 | R | independently recomputed box label == `Snapshot.session` (including the legitimate `""` 16:00–18:00 gap) |
| timestamp_coherence | §5.2/inv-3 | R | Snapshot.ts == Trigger.ts == indicators.ts; no future-stamped bar_ts (lookahead tripwire); trigger-TF bar is fresh |
| premarket_vwap_time_regime | §3/inv-1 | R | pre-anchor: NY VWAP all null AND daily VWAP present; post-anchor+grace: NY VWAP present |
| data_level_availability | §2 | R | no future-dated event_time (veto = lookahead); still-forming extremes flagged (never silently final) |
| news_day_classification | §6.3 | R | emits `high_impact` (high-impact event this CME session) or `unknown` — NEVER `normal` until I-5 exists; no outside calendar knowledge permitted |
| late_window_entry | §9 | R | computes minutes-to-window-close; emits the §9 half-unit flag (advisory, never a veto); needs `sizing.late_window_min` (Q-5) |
| session_integrity | §1/§12.2 | J | hard: no trigger stamped inside a known CME closure (weekend/maintenance); advisory: suspected holiday/early-close/roll flags, clearly labeled suspicions until I-6 |

### 5.3 Apollo — trigger & pattern anatomy

*Mandate:* the anatomy of the one arbitrated trigger candle: is it really the §3
mechanism and §4 pattern the engine claims?

| Check | § | kind | Pass condition (compressed) |
|---|---|---|---|
| snapshot_trigger_coherence | §1/§5.2 | R | tf ∈ entry TFs; trigger IS the last closed bar of its TF; valid bar-boundary alignment |
| cluster_reconstruction | §3 | R | (rejections) the trigger's cluster reconstructs from raw indicator prices — gaps, types, count, center |
| rejection_block_anatomy | §3/§5.4 | R | traded into cluster, closed strictly back on trade side of ALL levels, wick exists; `entry_ref`/`stop_ref` are the anatomically correct references |
| displacement_anatomy | §3 | R | body through ≥ N levels, body/range ≥ B_min, extreme-quartile close, optional ATR floor — **uncomputable without I-1/I-2; fails closed until added** (the forcing function for the interface change) |
| pattern_taxonomy_mapping | §4 | R | derived pattern (B for displacement w/ wrong-side precondition; A needs over-extension or counter-trend; B2 needs with-trend) == label; `range`+no-OE rejection = unclassifiable = FAIL (finding E-6) |
| htf_flag_consistency | §4 | R | regime×direction mapping holds; `unknown` = FAIL |
| over_extension_classification | §3/§9 | R | direction-appropriate NY VWAP band touch → none/standard/extreme/unavailable; A-pattern without counter-trend requires standard/extreme |
| invalidation_at_entry | §7 | R | behind `filters.invalidation_at_entry`; designed now (opposing ±1σ touch) so enabling is a config flip; needs I-1 + a VWAP-family ruling (Q-7) |
| pattern_mechanism_narrative | §4 | J | every mechanism element of the labeled pattern has ≥1 supporting item from a FIXED evidence list, none contradicted — the one judgment gate, fully enumerated |

### 5.4 Hephaestus — trade construction (the forge)

*Mandate:* validates a fully-specified **ProposedConstruction** (I-4; engine
computes, forge verifies). Takes `confluence_count`/`htf_flag`/`pattern` AS GIVEN
for the §9 formula (their verification is Atlas/Apollo's lane).

| Check | § | kind | Pass condition (compressed) |
|---|---|---|---|
| entry_matches_active_variant | §5.3 | R | E1 = trigger-TF BB basis; E2 = 50% of wick zone; E3 = penetrated level nearest close — recomputed, tick-rounded, must match exactly |
| stop_beyond_wick_extreme | §5.4 | R | stop at/just beyond wick extreme in the adverse direction, ≤ 1 tick from `stop_ref`, never widened (buffer ruling Q-9) |
| target_is_pattern_default | §6.1–6.2 | R | recomputed selection-tree default (A→VWAP mid; B2→next structural with move; B→opposing liquidity preferring ±2σ alignment) — and the target MUST be a menu level |
| news_day_override_applied | §6.3 | R | qualifying untaken high-impact extreme beyond default ⇒ it becomes the target (nearest); else default stands; "untaken" needs I-9 |
| front_run_working_target | §6.4 | R | working = level ∓ `targets.front_run_points`, tick-rounded, still beyond entry |
| rr_floor_met | §6.5 | R | R computed from entry/stop; target-R ≥ `targets.rr_floor`, else the ONLY passing behavior is skip — proposing anyway = veto |
| size_matches_conviction | §9 | R | full ⇔ (C ≥ min) AND (with-trend OR A-at-extension) AND (R ≥ min) AND no half-trigger; **indeterminate half-conditions (undefined "oversized stop"/"late-window") force half, fail-closed** (Q-5) |
| construction_coherent_and_tick_aligned | §5/§6 | R | direction consistency; stop < entry < working ≤ target (long, mirrored short); all prices exact 0.25 multiples |
| target_alignment_preference | §6.6 | J | no better-stacked valid same-family target was bypassed unexplained |

### 5.5 Hermes — orchestrator (no market opinions)

Nine-step flow (full detail in `hermes.json`):

1. **Boot integrity** — hash-check all four agent files + allowlists against the lockfile; drift = no Desk.
2. **Receive** exactly one (Snapshot, Trigger) pair. Stateless per invocation — no memory of prior candidates (memory = prior-trade info by the back door).
3. **Validate transport**: schemas, `Trigger.ts == Snapshot.ts`, tf legality, staleness bound. Failure ⇒ veto before fan-out.
4. **Project allowlists** — pure whitelist; out-of-lane fields are absent, not nulled. Hermes adds nothing.
5. **Parallel fan-out** to the four specialists; per-call + total deadlines.
6. **Collect & validate each independently**: on-time, parses, strict-schema, verdict == AND(own gates) — an arithmetic identity check, never re-scoring. No short-circuit on first failure (the §10 audit trail needs the full picture; the calls are parallel, so waiting is free).
7. **Unanimity**: `trade = AND(four gates)`. No weights, no quorum, no override in either direction.
8. **Assemble the Verdict** — verbatim copies + fixed-table size/grade + template-join thesis (§-cited specialist findings only; Hermes contributes ordering and joining, never judgment or numbers).
9. **Emit exactly one Verdict** to the runner, which re-validates and independently recomputes size/grade; mismatch ⇒ synthetic veto (`hermes_invalid` / `hermes_arithmetic_mismatch`).

Forbidden (selected; full list in the artifact): overriding/re-scoring any
specialist; any outbound channel; statefulness; leaking one specialist's output
to another (structurally impossible — payloads finalized before any dispatch, no
second round); inventing/rounding numbers; 3-of-4 quorum under time pressure;
emitting `trade=true` with any failed gate.

**PROPOSED (runtime designer's recommendation, NEEDS-DECISION Q-14):** unanimity
aggregation and size/grade computation live in **pure Python** in the runner; the
Hermes LLM call composes only the thesis. Conservative, costs nothing but schema
clarity.

### 5.6 Cross-lane seam rulings (so no rule is double-owned or orphaned)

- **§7 confluence-minimum gate lives in exactly one lane: Atlas** (using its own
  recount). Apollo owns the geometry of the same cluster; deliberate input
  overlap, single gate owner.
- **Pre-09:30 rule is deliberately dual-keyed**: Helios owns the TIME half (NY
  VWAP fields null), Atlas the COMPOSITION half (no `nyvwap_*` members).
  Redundant vetoes are harmless; a dropped half is not. Stated explicitly so
  neither lane assumes the other covers it.
- **§9 sizing facts flow to Hermes as facts, not verdicts**: C (Atlas recount ⊕
  Trigger), with-trend (flag), A-at-extension (Apollo), target-R / oversized-stop
  / thin-target (Hephaestus), late-window (Helios). Hermes applies the fixed
  table; the runner recomputes. Specialists never read each other.
- **Over-extension formula is pinned verbatim in both Apollo and Hephaestus**
  (identical text) until it is promoted to an engine-computed Snapshot field
  (recommended, I-7-adjacent).
- **News facts are raw-data-shared, not judgment-shared**: `data_levels[].impact`
  etc. sit on both Helios's and Hephaestus's allowlists; each derives
  independently from raw data. Keep it that way.
- **Deliberately NOT Desk-owned** (so the omission reads as designed): §5.5
  T_cancel/no-chase, §5.6 one-position, §8 management variants, EOD flatten —
  order-lifecycle mechanics for the engine/Vault. §1 MTF arbitration is
  engine-trust pending I-10.

## 6. Runtime & enforcement

Full detail: `docs/agent-blueprint-design/runtime.json`.

### 6.1 Structural allowlist enforcement
Allowlists live as machine-readable frontmatter **inside each agent file**; the
runner's `project()` builds a fresh dict of only the declared dot-paths — the
render function has no parameter through which the full Snapshot could even be
threaded. Declared paths are validated against `Snapshot.model_json_schema()` at
startup (a renamed engine field aborts boot rather than silently emptying a
slice). Changing an allowlist changes the file hash ⇒ forces a version bump.

### 6.2 Failure modes (all fail-closed, all journaled)
invalid JSON / schema violation / per-call timeout (cancel at deadline) / partial
completion / API error (one within-budget retry, else veto — Q-15) / duplicate
trigger (idempotency key; suppressed with reference) / stale snapshot (identity
+ freshness bounds) / conflicting same-ts triggers (= engine invariant violation:
veto both + operator alert) / agent-file hash mismatch (halt) / runner crash
(write-ahead intent rows ⇒ synthetic veto on recovery) / **journal write failure
⇒ Desk HALTS** — an unloggable verdict may not reach the Vault (§10).

### 6.3 Determinism — the honest version
Tier 1 (guaranteed): byte-identical rendered requests for identical inputs —
canonical JSON, no wall-clock/uuids in prompts, temperature 0, pinned dated model
ID (a silent model upgrade is a strategy change). Tier 2 (bounded): LLM sampling
is not bit-reproducible, so every verdict is **replayable** instead: full request
+ response stored as content-addressed blobs; `replay_verdict` re-runs and diffs;
binary-gate drift at temperature 0 is a tracked defect metric, not a shrug.

### 6.4 Versioning
Frontmatter semver + committed `agents.lock` (sha256 per agent file); runner
refuses to run on drift; every journal row stamps (agent versions, model ID,
strategy.yaml hash, engine git SHA). `test_desk_verbatim_slice` string-matches
every embedded strategy-doc slice against the constitution — a doc version bump
breaks CI until every affected agent file is re-verified. Change process = the
existing gate: hypothesis → Angus → bump + lockfile + progress-tracker in one
commit.

### 6.5 Latency budget (CALIBRATE from Phase-5 measurements)
Trigger closes → limit must be working early next bar. Proposed: 4 parallel
specialist calls, 20 s per-call timeout, 30 s total budget, 45 s hard deadline,
staleness bound 10 s — leaves ≥15 s of the minute for Vault + order placement.
Estimated p50 8–12 s. Breach ⇒ veto (`latency_breach`), never a late order.
All latencies logged on successes too, so the budget is recalibrated from
measured p50/p99, not asserted.

### 6.6 Backtest vs live — the shadow ledger
Live adds a veto-only layer the calibrated backtest never had: graded-live trades
a **subset** of the validated distribution, so backtest expectancy transfers only
if vetoes ≈ 0 or are measured. Phase-5 design: run the backtester's resolution
engine in shadow on the same live bars; join every trigger to
`{desk_outcome, shadow_outcome_R}`. Weekly §10 review reports: veto rate split by
gate class (**mechanical-gate vetoes should be ~0** — any nonzero one is an
engine bug or stale config, escalated as a defect); expectancy of vetoed vs
approved in shadow-R; operational vetoes (timeouts etc.) tracked separately; and
a re-run Monte Carlo on the veto-adjusted distribution before any funded eval.
Divergences are reported, never patched by loosening prompts.

### 6.7 Named tests Phase 3 must ship
`test_desk_allowlist_filter` · `test_desk_allowlist_paths_valid` ·
`test_desk_fail_closed_invalid_json` · `test_desk_unanimity_veto` ·
`test_desk_timeout_veto` · `test_desk_partial_completion` ·
`test_desk_specialist_independence_static` (no agent file references another;
dispatch signature admits no verdict-typed parameter) ·
`test_desk_no_outbound_import` (mirror of the Vault's no-LLM-import test:
`src/desk/*` imports no telegram/broker/vault/network modules beyond the pinned
SDK) · `test_vault_no_desk_llm_import` · `test_desk_golden_verdicts` (recorded
fixtures replayed offline; zero API calls in CI) ·
`test_desk_duplicate_trigger_suppressed` · `test_desk_stale_snapshot_veto` ·
`test_desk_conflicting_triggers_veto` · `test_desk_version_lock` ·
`test_desk_lockfile_ci_consistency` · `test_desk_verbatim_slice` ·
`test_desk_journal_schema_strict` · `test_desk_crash_recovery` ·
`test_desk_latency_logged` · `test_desk_prompt_determinism` ·
`test_desk_hermes_input_isolation`.

## 7. Rule coverage map

Completeness backbone: every rule in the constitution has exactly one enforcing
layer at live-trading time, with Desk re-checks noted. A rule with no owner is a
system hole. Full 74-row table: `docs/agent-blueprint-design/coverage.json`;
layer totals: engine 35 · vault 13 · backtest 7 · human 6 · desk-primary 4 ·
config 1 · not-active-in-Phase-3 8.

The four **desk-primary** rows (no deterministic layer can own them):
§7.2 location veto → **Atlas** · §7.5 news-is-bias-not-blackout → **Helios** ·
§9.1 full/half conviction composition → **Hephaestus** (runner-recomputed) ·
§11 unanimity orchestration → **Hermes**.

Everything else the Desk touches is a **redundant re-check** of an engine/vault
owner — which is the design: the deterministic layer enforces, the Desk
cross-examines.

## 8. Engine findings surfaced by this design ⚠️ (for the engine driver + Angus NOW)

Designing checks against the real code found nine engine-vs-doc discrepancies.
Per the constitution these are **reported, not fixed** — each needs an Angus
ruling (doc wins ⇒ engine change; engine behavior intended ⇒ doc bump):

| # | Finding | Where | § at stake |
|---|---|---|---|
| E-1 | ALL NY VWAP bands (±1/2/3σ) emitted as cluster candidates; §3 permits **mid/±1σ only** (the module's own docstring agrees with the doc; the code loops every band) | `snapshot.py _gather_levels` | §3 |
| E-2 | `htf_regime='unknown'` falls through to `trend_dir='short'` → unknown-regime shorts labeled `with_trend` (lenient §7 minimum), longs `counter_trend` | `triggers.py _htf_flag` | §4/§7 |
| E-3 | Displacement triggers hard-code `confluence_count=2`, `cluster=None`, `cluster_center=entry_ref` — feeds §7 minima and §9 sizing with a made-up number | `triggers.py _test_candle` | §3/§7/§9 |
| E-4 | Displacement `entry_ref = min(up_through)` (first level penetrated); §5.3 E3 reads "penetrated cluster level **nearest the block's close**" (= max for longs) | `triggers.py` | §5.3 |
| E-5 | `_over_extended` checks BOTH sides — a long can be "over-extended" because its high poked the upper band (extension WITH the trade); §3/§4 logic wants the trade-entry side | `triggers.py _over_extended` | §3/§4 |
| E-6 | Rejection with `range` flag and no over-extension is labeled pattern A; §4's A requires over-extension and/or HTF range extreme | `triggers.py` line 165 | §4 |
| E-7 | Displacement counts penetrations of ANY candidate level; §3 says through ≥2 **cluster** levels (levels forming a valid ≥2-type cluster) | `triggers.py _test_candle` | §3 |
| E-8 | `stop_ref` placed AT the wick extreme; §5.4 says "**beyond** the wick extreme" — at-vs-beyond needs a ruling + config key (`entry.stop_buffer_ticks`) | `triggers.py` | §5.4 |
| E-9 | `data_levels` has no retention bound — February events still appear in a July snapshot and leak stale rows into `target_menu` | `sessions.data_levels` | §2/§6 |

## 9. Open questions for Spec 3 (rolled up, deduped)

**Trading semantics — Angus:**
- Q-1: E-1..E-9 rulings above (each one individually).
- Q-2: does a structural level (prior-day/week/session extreme) within tolerance
  of a cluster add +1 to confluence count? (§3 taxonomy lists "structural ×1" but
  the candidate set has none; counter-trend min 3 is only reachable via
  bb+vwap+poc today.)
- Q-3: confluence minimum when `htf_flag == 'range'` (design fail-closes to the
  counter-trend minimum; needs `filters.min_confluence_range`).
- Q-4: §3 tolerance semantics — adjacent-gap (engine's single-linkage) or
  full-cluster-span?
- Q-5: numbers for §9's named-but-undefined half-triggers: "oversized stop"
  (points or ×ATR), "late-window entry" (`sizing.late_window_min`), "thin target"
  (proposed: rr_floor ≤ R < full_unit_min_target_r).
- Q-6: window boundary semantics (candle closing exactly at 11:00 — in or out;
  recommend half-open `[start, end)`).
- Q-7: §7 invalidation-at-entry "the opposing ±1σ" — of which VWAP (NY post-9:30 /
  daily pre)?
- Q-8: "VWAP middle" for the pattern-A default target — NY mid when non-null else
  daily mid (design's assumption)?
- Q-9: stop at-vs-beyond wick extreme (E-8) + tick-rounding direction
  (nearest vs conservative).
- Q-10: RR-floor basis — raw target level or front-run working target (design
  assumes working)?
- Q-11: "untaken" data extreme — computable definition (design: not strictly
  exceeded by session extreme since event_time; cleaner: engine `swept` flag I-9).
- Q-12: news_day `unknown` under an enabled §6.3 override — note-only, size
  downgrade, or veto? (Design: note-only.)
- Q-13: ratify/amend the A/B/C grade mapping and the veto nullability convention
  (§4.4); confirm `size` = unit designation only.

**Engineering — Spec-3 decisions:**
- Q-14: unanimity + size/grade computed in pure Python (runner) with the Hermes
  LLM composing only the thesis — recommended — or LLM-owned with runner assert?
- Q-15: retry policy — zero retries (strictest) vs one bounded transport-class
  retry (design default: one within-budget API-error retry; zero for
  invalid-JSON).
- Q-16: interface additions I-1..I-11 — engine-driver scope, ordering, and which
  land before vs during Phase 3.
- Q-17: desk config placement (`strategy.yaml desk:` block vs `desk.yaml`) +
  concrete timeout/staleness start values; per-day API spend guard (Vault-adjacent,
  must not live in the Desk).
- Q-18: verdict-on-veto wire format (additive fields on the Verdict vs Desk-side
  journal joined on ts/tf).
- Q-19: runner concurrency for triggers arriving mid-cycle (queue vs
  drop-with-log, and the §10 classification of drops).
- Q-20: blind re-derivation vs verification per lane — should specialists see the
  engine's computed answers (current design: yes, as cross-check targets) or
  re-derive fully blind (stronger, harder)? Decide per-lane.
- Q-21: blob/journal retention on the Phase-4 VPS (audit integrity vs disk).
- Q-22: Desk runner in-process with the live loop vs separate service + queue
  (affects crash semantics and whether a Desk halt stops trigger detection).

## 10. What happens next

1. **Now:** this document + `docs/agent-blueprint-design/*` sit in the repo as
   Spec-3 raw material. The §8 engine findings go to the engine driver + Angus
   immediately (they affect Steps 7–8 calibration, not just Phase 3).
2. **Phase 2 (calibration review):** Angus's rulings on Q-1..Q-13 fold in.
3. **Spec 3 (written with Angus, Claude-chat):** picks from §9, pins the
   contracts, and turns each lane summary into an executable agent file:
   `.claude/agents/{atlas,helios,apollo,hephaestus,hermes}.md` — each carrying
   role, **verbatim** strategy-doc slice, machine-readable allowlist frontmatter,
   and its mandatory output schema — plus `src/desk/runner.py` and the §6.7 test
   suite.
4. **Phase 3 execution (Pat + Claude Code):** build exactly what Spec 3 says.

---
*Design artifacts produced 2026-07-17 by a 7-way parallel design pass against the
Step-6 engine, followed by an adversarial verification pass (see progress
tracker). This document supersedes nothing and decides nothing — it exists so
Spec 3 starts from a worked design instead of a blank page.*
