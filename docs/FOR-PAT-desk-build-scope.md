# FOR PAT — Desk build scope: what you can build NOW vs. what waits on rulings

**Angus's ruling (20 Jul):** start building. You are NOT blocked. Build the structure
now; slot the rulebook in as Angus's answers land. Details below.

## ✅ BUILD NOW — no ruling needed

The architecture doesn't depend on the 28 open questions. Go ahead and build:

1. **The scaffolding of all five agent files** (`.claude/agents/{atlas,helios,apollo,
   hephaestus,hermes}.md`) — their roles, I/O contracts, and the *shape* of their checks.
   Where a check needs a rulebook value that isn't ruled yet, put a **clearly-marked
   placeholder** (e.g. `# RULING PENDING Q-5: half-trigger thresholds`) rather than a
   guessed number. Never bake in a guess as if it were Angus's rule.
2. **`src/desk/runner.py`** — the orchestration: feed → engine → specialists → decision.
   The plumbing is ruling-independent.
3. **The `ProposedConstruction` contract (I-4)** — the engine computes entry/stop/target/
   size BEFORE Hephaestus runs; agents validate prices, never invent them. This is the
   spine everything hangs on. (Angus still needs to formally bless the "engine proposes,
   agent validates" split, but you can build to it — it's the design's stated shape.)
4. **The named test suite skeleton (§6.7)** — write the tests as pending/xfail against the
   placeholders so they light up the moment a ruling fills its value.

## ⛔ DO NOT FINALIZE — waits on Angus's rulings

Anything whose *behavior* depends on an unanswered rulebook question. Build the slot,
leave the value pending:

- The confluence-count rules (Q-2/Q-3/Q-4), stop placement (E-8/Q-9), the half-trigger
  thresholds (Q-5), the location veto scope (Q-26), the A/B/C grade mapping (Q-13), etc.
- Any of the 12 engine-vs-doc disagreements (E-1…E-12) where the direction of the fix
  isn't yet ruled — don't silently pick one; the divergence goes to Angus.

The whole point of the design is "Claude/Pat never guess Angus's rulebook." A pending
placeholder is correct; a plausible guess is not.

## 📌 E-11 — clarified, so you don't re-flag it

Engine lane traced this: **the confluence minimum IS enforced in the champion backtest**
(`engine.py:812` veto + detection only forms a cluster at ≥2 level types), and
`confluence_count` is **real** (varies 2–3 in the cached triggers — it is NOT the
hard-coded `2` that E-3 described; that doesn't match the data our numbers are built on).
The counter-trend minimum currently sits at **2, per Angus's own 2026-07-17 calibration
ruling** (was 3 — see `config/strategy.yaml:134`).

So E-11 is **not a champion-backtest hole.** If it applies anywhere, it's that the **new
Desk agent path** doesn't yet *re-assert* the confluence minimum itself — which is a build
task for you (wire the check into whichever specialist owns location/confluence), not a
correction to existing numbers.

## Starting order (Angus endorsed)

Your own "starting subset" is the right unblock sequence: **I-4 → E-3 → E-11 → Q-5**.
I-4 unblocks Hephaestus's whole reason to exist; the other three each unblock a gate that
otherwise can't run. Build those slots first; Angus is working through the rulings packet
(`docs/FOR-ANGUS-desk-spec-questions.md`).

## Note: the Desk is a separate path

None of this touches the champion bot or the regime-agent (v0.7 / regime-dial) work —
those stay as they are. The Desk is a later, separate live-trading path. Build it alongside,
not on top of.
