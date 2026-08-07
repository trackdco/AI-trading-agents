# Artifact Errata — corrections from the adversarial verification pass

The seven JSON artifacts in this directory are the **unmodified raw output** of
the design pass (kept as the audit trail). A 4-lens adversarial verification
pass found defects in them. **`docs/agent-blueprint.md` is normative; where an
artifact disagrees with it or with this errata list, the artifact is wrong.**
Spec 3 must not copy any item below as-is.

## Blocker-class corrections

| # | Artifact | Defect | Correction |
|---|---|---|---|
| V-0 | `apollo.json` APL-1 + edge case 9 | **FALSE engine claim**: asserts `Trigger.ts` is START-labeled. Refuted: `detect_triggers` stamps ALL TFs (incl. 1min) via close-labeled `resample_ohlcv`. The strict `bar_ts == Trigger.ts` equality would veto **every 1-minute trigger** (`indicators_asof` serves the 1min slot START-labeled → off by exactly 1 min) | 1min lane expects `bar_ts == ts − 1min`, other TFs equality (mirrors Helios). Engine-side normalization = I-13; asymmetry recorded as E-12 |
| V-1 | `hermes.json` grade_derivation / thesis_composition / Step 5e; all four specialist schemas | Hermes reads `helios.facts.late_window_entry`, `apollo.facts.a_at_extension`, `hephaestus.facts.{target_r,oversized_stop,thin_target}`, `<agent>.finding`, per-check `{pass, ref}` objects — **none of which exist in any specialist schema** (Helios has `flags.*`, Apollo an enum, Hephaestus `recomputed.target_r_multiple`, gate shapes differ per agent) | The §4.3 envelope in the blueprint is normative: one gate shape `{pass, ref, note?}`, mandatory per-lane `facts` block, universal `finding`/`fail_reason`/`data_gaps`, uniform `agent_version` (not `prompt_version`). All five schemas regenerate from it |
| V-2 | `hephaestus.json` (all checks consume `proposed.*`); `hermes.json` Steps 1–3; `runtime.json` render signature | The ProposedConstruction has **no transport**: Hermes validates only (Snapshot, Trigger) and the render signature admits no third payload | Engine→Desk contract is a **triple** (Snapshot, Trigger, ProposedConstruction); runner validates all three; construction is a projected Hephaestus-only slice; tests updated accordingly |
| V-3 | `hermes.json` Step 6 vs `runtime.json` latency budget | Emission-time staleness re-check against the 10 s key would veto **every verdict** (design's own p50 is 8–12 s + overhead) | Two bounds: `desk.staleness_max_s` (10 s) at receipt/dispatch; emission bound = the 45 s hard deadline. Step-6 re-check as written is void |

## Major-class corrections

| # | Artifact | Defect | Correction |
|---|---|---|---|
| V-4 | `hermes.json` verdict_assembly | "Hephaestus computes it per the ACTIVE §5.3 variant… copied from hephaestus.construction.*" — LLM-originated executable prices | Verdict prices copy from the **engine-computed** ProposedConstruction that Hephaestus validated. No I-4 ⇒ no Desk (fail-closed). Also `construction.target_price` doesn't exist in the I-4 schema; `Verdict.target` = `working_target` |
| V-5 | `apollo.json` APL-5 | Derives pattern A from (OE OR counter_trend) — mirrors the engine, but §4's A-routes are OE and/or HTF range extreme; counter-trend is not a doc route | Marked PENDING-ANGUS (Q-23). Fail-closed default: A requires OE until ruled |
| V-6 | `apollo.json` over_extension description | "consumed by Hephaestus… single source of truth" — specialist-to-specialist flow violates independence | Emitted as a §9 fact to the runner only; Hephaestus independently recomputes the identical pinned formula |
| V-7 | `hephaestus.json` target_is_pattern_default | (a) B2 default = "nearest menu level" of ANY type — §6.2 says next **structural** level; (b) B default cites a "pre-market" extreme that maps to no existing field; (c) Asia/London extremes added to §6.2's list unflagged | B2 restricted to `type=='structural'` (which types qualify = Q-25); premarket mapping = Q-24; expansions flagged, not silently adopted |
| V-8 | `helios.json` late_window_entry | Fails closed on the missing `sizing.late_window_min` key ⇒ as designed **vetoes every candidate today**, contradicting its own "advisory, never a veto" framing | Missing-config policy (blueprint §4.3): advisory outputs emit null + data_gap and PASS; only gate-bearing indeterminacy fails closed (Hephaestus's force-half). Q-5 remains launch-blocking for full/A |
| V-9 | `runtime.json` field_filtering (3) + `test_desk_allowlist_paths_valid` | Path validation via `model_json_schema()` is vacuous — `Snapshot.indicators` is an untyped dict, so most declared paths are unresolvable and rename-detection is void | Validate against a golden fully-populated Snapshot fixture until I-12 (typed sub-models) lands |
| V-10 | `atlas.json` vs `apollo.json` cluster matching | Divergent numeric conventions (10-pt nearest-match + tie-break vs EPS-only + fail-on-ambiguity) — same candle could pass one lane and fail the other with contradictory journal rationales | Repo-wide pinned conventions (blueprint §5.6): one EPS (1e-3 on 4dp prices), one match rule, one tie-break |
| V-11 | `atlas.json` + `apollo.json` htf_flag gates vs `coverage.json` | `htf_flag_consistency` gated by TWO lanes with no ruling | Declared a deliberate dual-key (pure function of shared fields, mapping pinned verbatim in both) — blueprint §5.6 |
| V-12 | `coverage.json` §3.1 / §6.3 / §7.5 rows | Assigns Helios checks it cannot perform under its own allowlist (cluster members pre-9:30; untaken-extreme; release-day presence) | Atlas owns pre-9:30 composition; Hephaestus owns untaken-extreme (I-9); §7.5 presence-verification blocked on I-5 |
| V-13 | `coverage.json` §9.1 row | "Vault should deterministically recompute size as backstop" — third version of the size chain | Pinned chain (blueprint §4.4): engine computes in construction → Hephaestus gates → **runner** computes/asserts. One backstop |
| V-14 | `coverage.json` §2 Bollinger row | Phantom "Apollo BB corruption tripwire" — no such check exists and `bb_upper/lower` aren't on Apollo's allowlist | Claim deleted; if Spec 3 wants the tripwire it must add the check AND the allowlist fields |
| V-15 | `coverage.json` §5.4 row vs `hephaestus.json` | Opposite interim stop conventions ("strictly beyond" vs ≤1-tick-at-extreme) | Interim = Hephaestus's ≤1-tick tolerance, labeled pending Q-9/E-8 |
| V-16 | `apollo.json` APL-4 | Counts penetrations of ALL candidate levels (engine parity) — sides with the engine on the very E-7 divergence the Desk should surface | Count cluster-member penetrations per §3; engine mismatch FAILS (pending the E-7 ruling) |
| V-17 | `runtime.json` mandate texts + independence test | Every mandate names sibling agents; the static independence test would fail on day one | Agent files express boundaries without sibling names; test scans names/schema keys/verdict fields |
| V-18 | `helios.json` session_integrity | LLM calendar knowledge injected into the audit trail while another check forbids world knowledge | World-knowledge rule (blueprint §5.6): never in a gate; advisory-only, labeled, until I-5/I-6 |

## Minor-class corrections

- Config-key name drift normalized: `desk.staleness_max_s`,
  `sizing.oversized_stop_max`, `sizing.late_window_min` (each had two names
  across artifacts).
- `runtime.json` journal veto_reason enum must include `hermes_invalid`,
  `hermes_arithmetic_mismatch` (named in Step 9 but missing from the enum).
- Retry-policy default stated once (blueprint Q-15): one within-budget
  API-error retry; zero for invalid-JSON/timeout. `hermes.json`'s "NO RETRIES"
  and `runtime.json`'s retry text are both superseded by that single statement.
- `runtime.json`'s "queued and graded strictly serially" is a proposal;
  queue-vs-drop remains OPEN (Q-19).
- Blueprint §5.1 edge-case cross-reference corrected Q-8 → Q-4.
- `not_evaluated` whitelist extended to name the displacement-cluster case
  (Apollo APL-2) explicitly; Atlas FAILing the same gap is intentional
  (fail-closed preserved overall).
- Atlas's pre-9:30 gate also checks NY-VWAP nullity (not composition only) —
  §5.6 wording amended rather than trimming the gate.

*Produced 2026-07-17 from 44 verification findings (8 blocker / 22 major / 14
minor), 4 independent review lenses. Full finding detail is in the session
transcript; every item above was double-checked against the engine source
before being recorded.*
