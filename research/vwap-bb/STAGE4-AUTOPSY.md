# STAGE 4 AUTOPSY — why, not whether. N_trials unaffected (2 of 5).

**2026-08-08.** Angus: "Autopsy." Per Amendment 02's structure — the only binding text found
anywhere in this repo is a single sentence, quoted wherever Stage 4 is mentioned: **"≤3
hypotheses about why, not a re-test of whether."** Amendment 02's own full text could not be
located anywhere in this repository — only its consequences (the N_trials budget, the n≥661
floor) are cited across a dozen files. **This gap is disclosed, not silently filled.** The
procedure below is my own reading of the one sentence that does exist, stated plainly so it can
be corrected: **diagnostic analysis only, of data already sealed by the identity-churn sweep — no
new backtest, no new rule variant tried to see if it performs better, no new trial consumed.**

**Source data:** all three hypotheses below are computed from `data/identity_churn_sweep/
combo_NN.parquet` — the 32 files already sealed by the sweep that returned NO EDGE DEMONSTRATED.
Each file's SHA-256 was verified against its `.sha256` companion before reading. **No new outcome
was computed; every figure below already existed inside data sealed on 2026-08-08 and is being
read for the first time, for diagnosis, not decided by a new run.**

---

## H1 — The win rate sits within ~2 points of its own breakeven line, not badly broken

**Claim to test:** is the strategy failing because its risk/reward is badly designed (win rate
far below what its own payoff ratio requires), or because it's marginal — close to breakeven and
tipped negative by something smaller?

**Measured, across all 32 combinations:**

| | range across all 32 |
|---|---|
| Realized win rate (gross P&L > 0) | 29.9% – 32.3% |
| Breakeven win rate implied by that combination's own realized avg-win/avg-loss ratio | 31.0% – 33.3% |
| Shortfall (win rate − its own breakeven) | **−2.3 to +0.2 percentage points** |
| Combinations where win rate exceeds its own breakeven (pre-cost) | **1 of 32** |
| Average winner | ~+2.0R to +2.1R |
| Average loser | ~−0.99R (essentially exactly −1R, as expected — stop-first resolution exits a loser at exactly the stop distance) |

**Finding: the shortfall is consistently tiny — never more than 2.3 points, and in one
combination (03) the win rate actually clears its own breakeven before cost.** This is not a
strategy whose risk/reward is grossly mis-shaped. It is one sitting almost exactly on its own
breakeven line, on the wrong side of it by a margin smaller than ordinary sampling noise on
~1,100–1,400 trades.

---

## H2 — The realized trade shape is the opposite of both the project's own framing and the hand log

**Claim to test:** does the mechanical detector actually produce the kind of trade this project
was built to describe?

**Measured:** ~31% win rate, ~2.0–2.1R average winner, ~−1.0R average loser. **This is a
low-win-rate, high-reward:risk trade profile.** Two things this cuts against:

- **This branch's own name is "high-win-rate-low-rr-strategy."** The mechanical detector, as
  specified through A1–A22, produces the structural opposite of what it is named for.
- **Angus's hand log shows a 68.4% win rate** (`research/STATE.md`, with the standing caveat
  that the hand log is a hand-backtest, not a track record, and cannot itself establish a true
  win rate — but it describes the *kind* of setup intended, per that same caveat). 68.4% and
  ~31% are not close.

**Candidate reading, stated as a hypothesis, not a finding:** §6.5/A4's RR-floor rule — *"walk
the ladder of opposing menu levels outward from entry, take the FIRST level whose front-run-
adjusted distance is ≥ 1.5R"* — mechanically manufactures a low-win-rate/high-reward shape by
construction: it always reaches for a target at least 1.5R away and stops at the first one that
qualifies, rather than targeting the nearest liquid level regardless of distance. If the setups
Angus actually takes look more like frequent, modest-target reversion trades, this rule may be
selecting a fundamentally different trade archetype than the one the hand log describes — not a
bug, a specification that encodes a different trading style than intended.

---

## H3 — Transaction cost is comparable in size to the pre-cost edge itself

**Claim to test:** is this primarily a cost problem (a real, thin edge erased by realistic
friction) or is the underlying geometry already unprofitable before any cost is applied?

**Measured, across all 32 combinations:**

| | range across all 32 |
|---|---|
| Mean gross R (before any cost) | **−0.0684 to +0.0075** |
| Combinations with positive gross R (pre-cost) | **1 of 32** |
| Cost drag at the base cost basis (0.975 pt) | ≈ +0.045 to +0.05R per trade, added to the negative side |

**Finding: both are true, and neither alone is the whole story.** The gross (pre-cost) result is
already negative or at best marginally positive (one combination, +0.0075R) in every single
reading. Cost then adds roughly as much further drag as the win-rate shortfall itself represents.
**Removing transaction costs entirely would not flip this to a demonstrated edge** — at most one
combination would cross zero, and barely. The cost is real and material, but it is compounding a
pre-existing, already-thin-to-negative geometric edge, not manufacturing the loss on its own.

---

## What this autopsy does NOT do

It does not propose a fix. It does not re-run the detector under a modified rule to see if
performance improves — that would be exactly "a re-test of whether," which the one governing
sentence found for Stage 4 rules out. It does not touch the sealed holdout. **It answers, as
precisely as the already-sealed data allows, why the identity-churn sweep came back negative**:
a near-breakeven win rate against its own realized payoff ratio (H1), a trade shape that looks
nothing like either the project's stated framing or the hand log it was built from (H2), and a
transaction cost that compounds rather than causes an already-thin-to-negative gross edge (H3).

**Whether any of this warrants a genuine re-specification (a fresh, pre-registered spec version,
not a patch) — for instance, a target-selection rule closer to "nearest qualifying level" instead
of "first level beyond 1.5R" — is Angus's decision, not concluded here.**

## N_trials

**Unaffected — 2 of 5.** Every figure above was read from data already sealed by the
identity-churn sweep (hashes verified before reading). No new admission list was built, no new
outcome was computed, and nothing was compared across configurations to select a favorable one.
