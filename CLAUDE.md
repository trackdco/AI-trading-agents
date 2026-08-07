# CLAUDE.md — backtesting research, standing instructions

This file is the method, not a strategy. No strategy in this repo is inherited or assumed. Everything below is what has already gone wrong in this programme and what it costs to avoid repeating it.

Read this before doing anything. It is not optional context.

## 0. The one-sentence version

Most backtest results that look good are construction defects, not edges. The job is to make a number trustworthy before making it big.

## 1. How to work (standing behaviour)

**Enumerate, don't assert.** Never write "no X is affected" or "this only touches Y" from reasoning. Check every case and list them. This rule exists because blanket assurances were wrong four separate times in one session — each time the true scope was 2–3× what was claimed.

**A scan that reports zero findings is a suspect scan.** Before trusting a clean result, show the check fires on a known positive. A causality check that catches nothing is indistinguishable from no check. Build the known-positive case into the test suite, not into a one-off verification.

**Verify your own guards fail correctly.** For every test that protects something, break the thing deliberately and confirm the test fails with the right message. A test never seen red is a comment.

**Stop at blockers. Never substitute.** If a spec is underdefined, or a required input doesn't exist, report it and stop. Choosing a plausible substitute silently converts a declared hypothesis into a new one wearing the old one's name.

**Never tighten a loose specification.** If a rule says "and holds" with no threshold, that looseness is the finding. Log it; do not pick a number. Picking is invention, not correction.

**Report the undeterminable.** UNPARSEABLE, CANNOT-DETERMINE and UNVERIFIABLE are valid results and must be reported explicitly. Silently skipping a file is how a check passes vacuously.

**Correction is allowed; tuning is not.** The test is the order of the reasoning. A change that survives on the source evidence alone is a correction, and it being convenient is a consequence. A change that exists because it makes a threshold reachable is tuning, whatever the justification.

**Never edit history.** Wrong numbers get superseded — append the corrected row, mark the original superseded with a pointer, keep both. Deleting a wrong result destroys the record of the search.

## 2. Validation process — how a candidate becomes evidence

### Pre-registration

Write and commit the prereg before the run. The commit timestamp is the declaration. It must contain:

- The hypothesis and mechanism, in words, before any numbers
- The exact rule, tight enough that a stranger could code it
- Window table: every condition, its evaluation window, that window's close time, and the full set of decision times at which the rule can fire
- Clock provenance: for each data source, which timestamp is used and how it was verified
- Cost model (two stacks, strict one is the headline), fill model, anchor
- Sample: events per era, n_eff, and the minimum effect required
- Kill criteria, pre-committed — including what result makes you abandon it
- Controls, with type declared (see below)
- Trial count and its effect on the multiple-comparison denominator

Anything changed after seeing a result is a new experiment, and the clock restarts.

### Native before external

Order the pass criteria so the candidate's own economics are tested first. An externally-derived threshold is consulted only if the native criteria pass. If the native criteria fail, the foreign number is never used.

### Gate vs bar — a distinction that matters

- A **gate** imported from another population changes which trades are taken. It reshapes the population and compounds downstream. Importing one is adopting someone else's parameter. Don't.
- A **bar to clear** changes nothing about the strategy. It's an external reference point. Importing one is comparison, and is fine.

### Control admissibility

Declare every control as one of:

- **Population control** — changes which events qualify. Admits disjoint-group comparison only.
- **Mechanism control** — changes how the trade is constructed. Paired within-event comparison permitted.

A paired test against a population control is degenerate by construction — the entries are identical, so it returns exactly zero and looks like a measurement. Check structurally, before the run, that the control can differ from its comparator.

### Statistical discipline

- Sessions, not trades, are the independent unit. Overlapping trades within a session count less than the trade count suggests.
- Both eras must agree. An era-flip kills, regardless of the pooled number.
- Multiple comparisons deflate the bar. Every arm any harness evaluated counts, not just the ones you liked. `min effect ≈ k·√(2·ln N) / √n_eff`, where N is total comparisons.
- Measure your own noise floor. Run the search on shuffled labels and see what effect size it manufactures. If a 12-way search produces +0.31R half the time on your sample sizes, then +0.31R is not a result.
- Circularity is robust. A contaminated signal can return p<0.001 in both eras and survive every trim depth and winsorisation. Fragility testing cannot find lookahead. Neither can the P&L. That is why causality is checked at prereg time, not after.

### The in-sample rule

Any span already used for search is permanently in-sample. Tests on it can kill a candidate; they can never confirm one. State this in every prereg that runs on it, and never let a pass be read as confirmation.

### Holdout discipline

One look. Declared in writing before it happens. A holdout touched twice is not a holdout. Building any artifact over the sealed span is a look. Guard it in code — a loader that raises on sealed paths unless an explicit authorisation flag is passed, not a convention anyone must remember.

## 3. Defect catalogue — every one of these has actually happened

Check for these by default. Each destroyed or nearly destroyed a result.

### Causality

1. **Cross-window lookahead.** A rule spans two windows and the gating window closes after the earliest decision time. Per-column audits miss it entirely — the defect lives in the (condition, decision-time) pair. Assert `max(close_time(Wᵢ)) ≤ T` for every condition and every firing time.
2. **Lying timestamps.** An archive's primary timestamp was floored to the minute at extraction; the true observation time sat ~60s later. Every consumer read the book from after the decision it gated, and a declared window table certified it as clean. Validate every timestamped source against a second independent clock at load time. A causality check cannot detect a lying clock.
3. **Bar-label convention.** Bars may be start-labelled or close-labelled, and the wrong assumption shifts every window boundary by one bar. Settle it empirically against an independent source, not from prose. A careful audit got the opposite answer from correct measurements because of a wrong premise about a different file.
4. **At-fill anchoring.** Reading state at the fill bar already contains part of the answer — a limit fill requires price to have travelled toward the order. Anchor at the moment a trader could act: the trigger close, when the order is placed.
5. **Path starts at the fill minute, not the next bar boundary.** Skipping the remainder of the fill bar hid adverse movement in one case severe enough that a stop had already been hit on 73% of trades before the simulation began.
6. **Same-bar fill and stop → stop first. Always.** The optimistic ordering turned a "+2R win" into a real −1R.
7. **Bound both orderings** wherever a single bar contains both target and stop and you have no tick sequence. Bound it, never guess, never drop.
8. **Era-local or whole-span quantiles** classify a day using future days. Use trailing windows or fit-span-frozen thresholds.

### Data integrity

9. **Contaminated prices.** Calendar-spread and back-month prints sit inside the same feed. A percentage band does not exclude the back month — its cost-of-carry falls inside ±2%. Band against a front-month ground truth.
10. **Sign conventions.** Two scripts and a README disagreed on aggressor labelling. Settle it empirically — correlate signed flow against realised price movement on large unambiguous moves — then pin it with a test. A flipped sign is invisible to goodness-of-fit.
11. **Non-deterministic tie-breaks.** `idxmax` resolves ties by row position, which depends on input ordering. Use an explicit sort with a stable algorithm. This changed a gate condition on 9 of 749 rows and made rebuilds irreproducible.
12. **Flat bars treated as directional.** `~(close > open)` counts a doji as down. Check the equality case in every directional predicate.
13. **Forked binary artifacts.** Git cannot merge parquet, so every branch resolves take-ours/take-theirs and silently drops the other side. Store any append-only record as sorted JSONL with a union merge driver; derive the parquet and gitignore it.

### Measurement

14. **Post-trade residual snapshots.** A book sampled at minute end is the state after that minute's trades. Ratios of traded volume to displayed size are structurally inflated.
15. **Share-based concentration measures** fire less often when volume spreads across more prices — they track the volume regime, not the thing you meant. The dangerous case is the one with a workable sample, because it looks testable.
16. **Interval differences across coarse samples.** Differencing two snapshots that span tens of thousands of unobserved events does not measure flow — it measures the residual, conflates cancellation with execution, and can carry the opposite sign.
17. **Hardcoded prose in generated documents.** Tables regenerate; the narrative beneath them does not. A document contradicted its own table for weeks. But distinguish by intent, not form — citations, deliberate historical records and definitions legitimately don't regenerate.

## 4. Data hygiene — required structure

**Chokepoint modules.** Exactly one module may read each raw source. It applies cleaning, the clock correction and the sealed-path guard. Every consumer imports it.

Enforce the chokepoint with a test, and use AST taint analysis, not a regex. A regex matching inline paths misses a module that builds the path in a variable one line before reading it — which is exactly where a three-defect file was hiding. Report unparseable modules rather than skipping them.

**Constructibility triage before code.** For every planned feature, classify it against the actual data resolution:

- **VALID** — computable and measures what it claims
- **BIASED** — computable, but measures something else; may be used only if labelled a proxy with the bias direction stated
- **NOT CONSTRUCTIBLE** — requires data you don't have; say what data would fix it, since that is a purchase decision rather than a coding one

**Construction validation before any edge question.** A feature must be shown to measure what it claims before it is tested for profitability:

1. **Positive control** — a relationship you know exists must be detectable. If it isn't, the harness is broken and every null is meaningless.
2. **Shuffle placebo** — compare the effect against its own shuffled null. An effect inside the null's p95 is not an effect, however it looks.
3. **Time-shifted placebo** — does the feature explain the past interval or the next one? Residual-dominant means it measures memory, not prediction.
4. **Parameter ladder** — does the effect survive across the parameter range, or exist at one setting?
5. **Era stability** — the feature's own distribution, not just its effect. An event definition whose frequency moves 40% between eras is fragile at the definition layer.

Most flow failures are construction failures, not absence of signal.

## 5. Infrastructure patterns that earned their place

**Reproduction gate before any P&L.** When a downstream script must reproduce an upstream census, assert the counts match before computing anything. This caught two silent population-moving bugs that would never have shown up in the P&L.

**Append-only trial ledger**, keyed `(family, trial, era)`, one JSON object per line, sorted. A re-run producing different numbers under the same key is a supersession, not an update. Never overwrite.

**Pre-commit hook** refusing a ledger change with no prereg or verdict staged, with an explicit logged exemption path for legitimate bypasses. An invisible bypass is worse than no hook.

**Guards refuse, they don't warn.** And they refuse in both directions — a correction applied to data that didn't need it is the same size error as the one it fixes.

**Verdict documents** with the reproduce command, the artifacts, and the trial count. If the reproduce script isn't on the same branch as the verdict, the verdict is unverifiable.

**One trunk branch.** Work scattered across branches produced two divergent ledgers, verdicts separated from their scripts, and a constitution that lived on no working branch for two weeks.

## 6. Skills to install

- **orderflow-construction** — required before building or debugging any order-flow feature. Triage gate, resolution limits, construction failure modes, the five-check validation battery. If it isn't installed, build it before touching flow.
- **live-trading-mentor** — only for go-live: execution bridges, prop-firm compliance, VPS operation, live risk. Never triggers for research.

## 7. First actions in a new repo

1. Write the conventions file: bar labelling, session windows, timezone handling, fill model, cost model. Verify each empirically; do not inherit from prose.
2. Build the chokepoint loaders and their guard tests before any feature code.
3. Run the clock assertion against every timestamped source. Report FLOORED / CLEAN / UNVERIFIABLE per source.
4. Stand up the ledger as JSONL with its integrity tests.
5. Commit the prereg template — including the window table and clock provenance fields — before the first backtest exists. Pre-registration is trivial to adopt on day one and nearly impossible to retrofit after you've seen a result you liked.
6. Only then specify a candidate.

## 8. What "done" looks like for a candidate

- Rule written so a stranger could code it, with a ground-truth label set
- Detector reproduces the labels; every mismatch adjudicated in writing
- Prereg committed before the run, with pass marks and kill criteria
- Causality and clock checks pass at prereg time
- Full battery: real costs, delayed entry, 2× costs, best-5%-removed, era split, permutation test
- Controls declared, admissible, and beaten
- Out-of-sample confirmation on a span never searched
- Only then is it a result. Before that it is a hypothesis with a number attached.
