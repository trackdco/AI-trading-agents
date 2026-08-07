# Sample test candidates — for Stage 4 step 12 (test each skill alone first)

Two REAL historical trade candidates (built from actual March 2026 NQ data via the
same `build_snapshot`/trigger-detection code the live bot uses), in the exact
`{snapshot, trigger}` JSON shape a specialist skill expects. Use these to sanity-check
Atlas (and eventually the others) before wiring up the Hermes coordinator.

## How to use one

1. Open a chat with your Atlas skill inside Hermes Agent.
2. Paste the skill doc's instructions if it's not already loaded as the skill.
3. Paste the ENTIRE contents of one of these `.json` files as the input.
4. Compare what Atlas says against the "expected" note below.

**Note on isolation:** in production, the Hermes coordinator slices each specialist
down to only its allowed fields (`snapshot_allowlist`/`trigger_allowlist` in that
skill's doc) before calling it — a specialist never sees the whole payload. For this
manual, one-specialist-at-a-time sanity check, pasting the full JSON is fine; the
skill doc's own instructions already say which fields it's allowed to use. Once you
build the coordinator (step 11), it takes over doing the real per-specialist slicing.

## candidate_1_expect_atlas_pass.json

2026-03-02 10:20 ET, 5min timeframe, pattern B2, long. Cluster = `bb_basis_3min` +
`bb_basis_5min` + `poc`, types `['bb', 'vwap']`, confluence count 2.

**Expected Atlas verdict: PASS.** The cluster contains both a `bb_basis_*` member
and a VWAP-family member — satisfies the v1.2 §7 rule (BB + VWAP both present).
All other Atlas checks should also pass on this candidate (it's a real, clean
historical trigger) — if something else fails, that's worth reporting back.

## candidate_2_expect_atlas_fail_no_vwap.json

2026-03-02 09:31 ET, 1min timeframe, pattern A, long. Cluster = `poc` +
`bb_basis_3min` + `bb_basis_5min`, types `['bb', 'poc']` — **no VWAP member at
all**, confluence count 2.

**Expected Atlas verdict: FAIL**, specifically on the `confluence_minimum` check.
This is a real trade that would have passed under the OLDER (pre-v1.2) 2-type rule
— it has two distinct types (BB + POC) — but v1.2 specifically requires BB AND
VWAP, not just any two types. POC doesn't count as a substitute for VWAP. This is
a genuinely useful edge case: if Atlas passes this one, the skill doc's v1.2 rule
isn't being applied correctly and needs a wording fix — report back what it says.

## Getting more candidates

If these two aren't enough, tell Claude Code what kind of additional case you want
(a displacement trigger, a short, a pre-09:30/pre-market one, one that should fail
the location veto, etc.) and it can pull another real one from the same trigger
history and build the payload the same way.
