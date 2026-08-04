# VALIDATION PROCESS — how a strategy earns its way from idea to live

**Status: DRAFT 2026-08-04, for Angus to ratify.** This is the master artifact from
the week brief §2a ("build process behind strategy validation"). It is **codified
existing practice** — every rule below is something this shop already does, with the
file that proves it cited inline — plus the brief's named additions, which are marked
as new. It is not new bureaucracy; it is the method written down once so it can be
referenced forever. The method is the deliverable (`docs/HANDOFF-london-rebuild.md` §1).

Markers used throughout:
- **[EXISTING]** — codified from repo practice, source cited.
- **[NEW — brief]** — required by the 2026-08-04 brief, not yet practiced; becomes law
  when Angus signs this doc.
- **[PROPOSED — Angus to ratify]** — a number only Angus can set; a defensible default
  is given so work isn't blocked, but it is not law until he ratifies it.
- **[OPEN — needs Angus/Pat]** — a fact or ruling this doc could not settle. Never
  guessed.

**Branch discipline:** this doc is drafted on `claude/canon-rebuild-deployment-7m48yv`,
off the live arming branch. Landing ANY commit on the arming branch — even docs — makes
the next arm refuse on provenance (`docs/HANDOFF` §4: "A docs commit is enough to make
the next arm refuse"). This doc reaches the live branch only via the deliberate
re-cert + re-authorization flow, never casually.

**Sign-off (whole doc):**
ANGUS — date: __________ — ratified: __________
(Appendix A carries its own signature block so Brake's round can be unblocked
independently — brief §9 item 7.)

---

## 0. Standing law (the sentences everything else hangs off)

All [EXISTING]:

1. **Measurement, not vibes. Every claim gets a number, a null, or a tombstone.**
   Kill criteria pre-committed before results are seen. (`docs/HANDOFF` §7.)
2. **Failures are findings** — report them with the diagnosis, never bury them.
   (`docs/HANDOFF-london-rebuild.md` §6.)
3. **Nothing self-authorizes.** A measurement, however favorable, never relaxes a gate
   by itself; Angus rules, dated and quoted. (`docs/REPORT-parity-2026-07-29.md` §5:
   "DO NOT ARM remains in force until Angus rules; nothing here self-authorizes.")
4. **Caveats ship with the verdict — stated, not hidden.** The agent layer shipped
   *with* the conviction-shuffle FAIL on the table (`docs/REPORT-desk-run-2.md`).
   Hiding a weakness is worse than the weakness.
5. **Do not torture the data until it confesses.** (`docs/HANDOFF-agents-capture.md` §8.)
6. **Stale-figure discipline:** superseded numbers are marked SUPERSEDED with a pointer
   to the replacement, never silently deleted (`docs/ARMING-REFERENCE.md` §2). Anything
   produced before 2026-07-28 is void as strategy truth (`docs/CANON.md`). Current
   references: fit +$82,543 / holdout +$48,211 (lucid, $160 base, rules J/K/L);
   the old +$77,202/+$44,844 and $90,015/$56,409 figures are superseded.
7. **Roles:** Angus rules (every parameter change is a dated ANGUS ruling — rows A–N,
   `docs/HANDOVER-pat-arming.md` §3); this chat measures and writes the spec; Pat
   certifies on the box with written confirmations. Neither party arms alone
   (`docs/ARMING-REFERENCE.md` §6).

---

## 1. Pre-registration — filled BEFORE a run

**[EXISTING]** — this is already how the shop's two strongest artifacts were made:

- `docs/HOLDOUT-2023-24-PREREGISTRATION.md`: "**This file is the commitment.** It is
  written and committed BEFORE any depth or trades data is pulled and before anything
  is scored. The SHA-256 below fixes the day list. If a later result is reported
  against a different set of days, this file is the evidence." It pins mode, n, seed
  (`20260727`), the drawn day list (128 days, 63/65 across 2023/2024, from a 513-day
  eligible universe), its SHA-256, the regeneration command, and a "Known limit,
  stated up front" section.
- `docs/PLAN-agents-capture-run.md` header: "Written 2026-07-30, BEFORE any agent
  verdict was generated, so the holdout protocol in §8 is a declaration, not a
  rationalisation." Its §9 kill criteria are titled "pre-committed" and the report
  grades against them by table, including the FAIL.

**The template.** Every hypothesis gets one of these, committed before any scoring run
touches data. Field list per brief §2a-1 plus the fields practice has shown to matter:

```
PRE-REGISTRATION — <id> — committed <date>, BEFORE any data is pulled or scored

Hypothesis:        one falsifiable sentence.
Mechanism:         why the market should pay this — the causal story, not the pattern.
Mechanism family:  the declared family (depth walls / overnight structure / order flow-
                   CVD / VWAP geometry / trigger density / structural events / pattern
                   taxonomy / ...). A new family is a new vault vocabulary entry
                   (docs/VAULT-SCHEMA.md §5).
Input columns:     the exact column names the entry or gate reads (e.g. dep_wall_below_d,
                   on_extreme_age, cvd_ASIA). This feeds the correlation input-family
                   veto at pre-registration time, before any returns exist
                   (docs/REPORT-correlation-2026-08-04.md; brief §3 item 1).
Session:           ny-pre | ny-gold | london (vault vocab, docs/VAULT-SCHEMA.md §5).
Entry type:        e.g. limit/rotation (E3-style) | momentum (E4-style).
Spans consumed:    which eras this experiment touches. Holdout look: YES/NO. If YES,
                   the declared question and its family go in the §4 ledger BEFORE
                   computing; if NO, say "fit-only, no holdout look spent" so the
                   tombstone can say it too.
Seed / day list:   pinned; SHA-256 where a day list is drawn.
Acceptance bars:   the §2 standard bars plus any experiment-specific bars, WITH NUMBERS.
Kill criteria:     "this dies if ANY of: ..." — pre-committed (PLAN-agents-capture-run §9).
Known limits:      stated up front, so the result is not over-read later.
Artifacts:         where outputs will land (output/...).
```

Two rules of use, both [EXISTING]:
- Both arms of any referendum are defined before computing (the execution-semantics
  holdout look "had both arms defined from Angus's netting-broker question before
  computing" — `docs/HANDOFF-agents-capture.md` §0).
- A negative result is a deliverable: "'Agents don't beat V8' is a valid, valuable
  outcome" (`docs/PLAN-agents-capture-run.md`).

---

## 2. Standard acceptance bars

### 2.1 Era split [EXISTING]

- **Fit span:** 2025-06-02 → 2026-07-15 (~230 days, 13 months — the span begins the
  exact day MBP-10 depth coverage begins; `docs/HOLDOUT-2023-24-PREREGISTRATION.md`,
  `docs/CANON-QA-LOG.md` entry 27).
- **Discover on 2025 ONLY. Validate on 2026** as the out-of-era check
  (`docs/HANDOFF-london-rebuild.md` §3; QA-LOG entry 27).
- **The inverse pass is also required** (ANGUS 2026-08-04): re-run the search with
  the eras swapped — discover on 2026, validate on 2025 — and a check survives only
  if it holds in BOTH directions. A rule that discovers one way but not the other is
  era-fragile, not an edge. The swap doubles the trial count; the ledger records
  both passes and the §2.4 denominators include them.
- **Triple-era survival:** "A check/cut/threshold survives only if it points the same
  way in 2025, 2026, AND holdout" (`docs/HANDOFF-london-rebuild.md` §3). Precedents:
  the wall-quality cut (cut set 37–41% WR in all three eras; book WR +7pp, maxDD
  −37%/−45% — QA-LOG entry 28), the elite 2.0x combo (70/79/70% per era), the press
  signal (79–88% in every era).
- **Era-flips kill:** weekday effects era-flipped → no calendar rules ship (QA-LOG
  entry 51); buffer-scaled risk rejected for era-flipping (entry 35).

### 2.2 Minimum n per era [PROPOSED — Angus to ratify]

Practice already refuses underpowered claims (the pre-registration's "Known limit"
section: the `Q <= 1` cut "will land only a handful of trades at this sample size.
This holdout cannot settle that layer"), but no number is written anywhere. Proposed
defaults:

- **≥ 30 trades in each era cell** (fit-2025, fit-2026, holdout) before a
  direction/sign claim counts as confirmed in that era. Below 30 the era can be cited
  only as "consistent direction, underpowered" — never as confirmation.
- **≥ 100 trades pooled** before any magnitude or threshold claim (a WR, a meanR, a
  cut level) is quotable as a number rather than a direction.
- **Sizing-tier claims** additionally need a Wilson lower bound above the pre-set bar
  — the existing instrument: the elite 2.0x combo shipped on pooled 72% with Wilson
  lower bound 64% against Angus's pre-set "wouldn't want to do double sizing on
  anything less than 70–75%" (QA-LOG entries 37–38).
- **Overlapping trades count less than trade count suggests** [NEW — education round
  2026-08-04]: when positions overlap in time, the effective sample size is smaller
  than n (concurrent labels are partial photocopies of one bet). Significance math
  on per-trade statistics uses effective N (average-uniqueness correction,
  `research/findings/quant-math-canon.md` §1.4), not raw trade count.

### 2.3 Permutation null, family-wise [EXISTING core, NEW — brief numbers]

The core is non-negotiable rule 4 (`docs/HANDOFF-agents-capture.md` §3): "Shuffle
outcomes, re-run the search, record the best apparent lift on noise." Note that
re-running the SEARCH under the null — not just re-scoring the winner — is already a
family-wise max-statistic correction; the brief's demand is to fix the count and the
bar, which have never been written down:

- **≥ 1,000 permutations** (10,000 where cheap) [PROPOSED — Angus to ratify].
- **Statistic = the best apparent lift across ALL arms tested in the family** (the
  max over the search grid), so the null is family-wise by construction.
- **Bar: family-wise p ≤ 0.01** [PROPOSED — Angus to ratify].

### 2.4 DSR / PBO [NEW — brief; numbers PROPOSED — Angus to ratify]

Not existing practice — these are this week's deliverables (brief §2a-2, §7). Brake
implements; Angus judges the implementation. Proposed bars:

- **DSR ≥ 0.95** on the discovery span — the Deflated Sharpe Ratio computed with the
  effective trial count from the **variance-of-Sharpes form** over the actual search
  grid (the brief §7 names why this beats nominal trial counting when grids are
  nested).
- **PBO ≤ 0.25** to pass (combinatorially symmetric cross-validation).
  **PBO 0.25–0.50 = INCONCLUSIVE**, which blocks exactly like FAIL (§5).
  **PBO ≥ 0.50 condemns the selection procedure, not the candidate** (brief §7) —
  the search design gets the tombstone, and re-running it with a new candidate is
  not a fix.
- **Effective trials, both directions** [NEW — education round 2026-08-04, for
  Brake]: the ledger records EVERYTHING including abandoned trials (they were
  lottery tickets too), then DSR's N deflates to *effective* independent trials by
  clustering correlated configurations (lookback 20 vs 21 is not two draws) —
  `research/findings/quant-math-canon.md` §1.6. Under-recording rigs the grade;
  over-counting correlated arms wastes power. Both corrections are mandatory.
- **Two-tier gate policy** [PROPOSED — education round 2026-08-04]: at the
  discover→validate promotion, control the false-discovery RATE (Benjamini–Hochberg,
  q = 0.10 proposed) — tolerate some duds to keep power in the funnel. At the
  validate→holdout→live gate, family-wise-grade evidence (DSR + the §2.3 family
  null) — a false go-live is the expensive error. One error philosophy per gate,
  stated on the verdict.
- **Search-program audit** [PROPOSED — education round 2026-08-04]: periodically
  (per session per quarter proposed), run a family-level test (SPA-style: is the
  BEST of everything we searched distinguishable from noise?) over the whole trial
  ledger. This is the health metric of the self-learning loop itself — a research
  program whose family max stops clearing the audit is mining noise regardless of
  how its individual candidates grade.

### 2.5 The rest of the standard battery [EXISTING]

- **Causality or it doesn't count:** decision at minute t uses only ≤ t information;
  the harness is built before anything plays (rule 1, `docs/HANDOFF-agents-capture.md`
  §3). Post-loss cooldown "looked great leaky, died honest" (London burn list item 8).
- **Beat the best mechanical control**, not just the baseline — the agent arm was
  graded against `lock1r_2r`, not only against V8 (`docs/PLAN-agents-capture-run.md`
  §9 criterion 2; `docs/REPORT-desk-run-2.md`).
- **Fragility / drop-top-3:** an edge that is positive only via ≤ 3 trades is dead
  (PLAN §9 criterion 1). Precedent: rr_floor 1.5 RETRACTED when 80% of the gain was
  one degenerate 6pt-stop fill (`docs/RULING-mechanical-only.md`).
- **Oracle ≠ policy:** a hindsight-optimal book is a CEILING for reporting, never a
  target (rule 5, `docs/HANDOFF-agents-capture.md` §3).
- **Design-target check:** the book must trade — shipped canon verified at ~4
  trades/day against a ~3/day minimum, gold ≥ 1 every month, zero zero-trade days
  across 352 days (QA-LOG entry 17).
- **Cost realism is a bar, not an accounting detail** [NEW — education round
  2026-08-04]: taker pricing by default (full spread both ways + commission);
  limit fills count only when price trades THROUGH the level, never on a touch;
  slippage modeled as a vol-conditioned distribution, with headline results also
  reported at a pessimistic slippage percentile. Rationale on record: a published
  falsification study on MNQ itself found zero naive OHLCV signals surviving
  honest friction (`research/findings/strategy-classes-evidence.md`), and a
  generous fill model makes the refinement search EVOLVE TOWARD strategies that
  harvest imaginary spread — cost fiction corrupts selection pressure, not just
  reported P&L.
- **Holdout:** §4. One look, declared, frozen.

---

## 3. The layer gates — L0–L4 [EXISTING]

From `docs/HANDOFF-london-rebuild.md` §1, the method doc:

```
L0  census      every structural trigger, no selection        gate: parity vs cached stream
L1  fills       every limit walked, no cancels enforced       gate: engine fill reproduction to the tick
L2  outcomes    every fill through the REAL engine, V8        gate: lookback outcome-invariance
L3  features    order-flow features, as-of-clean              gate: reproduce cached matrices to 1e-6
    trial       every check tested, fit-era vs out-era        gate: permutation null bars (§2.3)
L4  policy      caps/sizing/risk as POST-HOC causal walks     gate: causal (no lookahead) unit tests
```

**The governing invariant** (`docs/CANON-QA-LOG.md` entry 4): "layers above L0 may
only *remove or weight*, never add, and every kill must be attributable. Caps get
imposed last, at L4, where they can be measured rather than assumed."

**Gate mechanics, all evidenced:**
- **A verdict at every layer boundary, plus an explicit gate that must pass before
  the next layer starts** (QA-LOG entry 11 — Angus's own words made this standing
  procedure: "give me the verdict after each step so we can make sure we are tracking
  on the right path instead of coming to the end to see something fucked up").
- L0 parity: identity columns IDENTICAL on ≥ 3 overlap days vs the cached stream.
  **Bonus gate where hand data exists:** the NY census matched Angus's hand log
  **43 of 45** (QA-LOG entry 21) — that external ground truth is what made everything
  downstream trustworthy. Where no hand log exists (London), the statistical gates
  carry the full weight and are set stricter, not looser (brief §6; Appendix A).
- L1: fill minute + tick-rounded price reproduced by the engine.
- L2: lookback outcome-invariance (7d vs 30d) on days with real fills — "NY's 2d
  attempt FAILED this gate honestly" (`docs/HANDOFF-london-rebuild.md`).
- L3: cached matrices reproduced to 1e-6; the join must include entry price where
  same-minute sibling triggers exist (burn list item 4). Then the trial bars of §2.
- L4: causal walks only; first-N-clearing, never best-of-day.

### 3.1 The refinement loop — what L1–L4 are actually for [EXISTING practice, named per ANGUS 2026-08-04]

The expected starting state of a discretionary strategy's raw substrate is
**unprofitable**. The NY precedent is the method: the raw census was nowhere near the
hand edge — the shipped canon is what remained after the conditioning search (flow
confirmations, wall features, windows, exit mechanics: the exit-lab's rr_floor
tombstone; the 25-arm profit-taking family, measured and closed, live HANDOFF §5).
"The raw data behind this strategy is unprofitable — what can we do to make it
profitable?" is the job description of layers L1–L4, and it is **agent work**: agents
sweep the conditioning space over the substrate the way the NY sessions did by hand.
The **loser autopsy** is a named, expected move in that search (ANGUS 2026-08-04):
"what do the losers have in common that the winners don't share? If we cut off that
subset, or if we de-risk, does that outcome look better?" — acknowledged in-sample
conditioning, legal precisely because it is policed downstream: the resulting rule
ships as FROZEN code to the sealed holdout months, and DSR/PBO absorb the trials it
took to find (§2.4). Cut-sets follow the wall-quality-cut precedent: the cut cohort
must be bad in every era, not just the discovery era.
The success metric at each layer is **distance to the discretionary baseline** (the
hand-log P&L where one exists; stated as unmeasurable where it does not — brief §6),
not absolute profit at L0.

Three disciplines make that search an engine instead of an overfitting machine
(third added by the education round, 2026-08-04):

1. **The search space is pre-registered by family** (§1: mechanism family, input
   columns). Agents explore freely inside declared families; a new family mid-search
   is a new pre-registration, not an improvisation.
2. **The trial ledger is mandatory and agents cannot skip it**: every arm tested —
   winner, loser, abandoned — is logged as a vault `job` record
   (docs/VAULT-SCHEMA.md §3.2). The §2.3 family-wise null and §2.4 DSR/PBO
   denominators are the TOTAL count of arms tried, not the survivors shown. The bar
   rises with the size of the search; an unlogged trial silently lowers the bar for
   every result after it, which makes skipping the ledger a §0 violation, not an
   oversight.
3. **The refiner never grades itself** [NEW — education round 2026-08-04]: the
   documented institutional rule (López de Prado; the firms' practice in
   `research/findings/how-elite-quants-operate.md` §6) is that the researcher who
   invents a strategy must not be its validator — researchers unconsciously leak
   the holdout into their choices. Agent version: the context/agent that ran the
   conditioning search hands a FROZEN spec to a separate grading run that has
   never seen the search history; validation-era and holdout scoring execute from
   the frozen spec only. Within the search itself, any inner-loop model tuning
   uses purged/embargoed splits (`quant-math-canon.md` §1.1) — era-splits protect
   the macro boundary, not the inner loop.

### 3.2 The loser autopsy is MANDATORY for every L1-profitable candidate [ANGUS 2026-08-04]

Elevated from expected move (§3.1) to required stage: no candidate reaches
grading without a completed loser autopsy — "what do the losers have in common
that the winners don't share? If we cut off that subset, or if we de-risk, does
that outcome look better?" Procedure: (1) declare a SMALL feature set before
looking (regime, structure, sizing-geometry, calendar — from the substrate);
(2) compare loser vs winner distributions per era, with special attention to
any time-clustered losing stretch; (3) candidate cut-sets obey the
wall-quality-cut precedent — the cut cohort must be bad in EVERY era, not just
the discovery era; (4) every cut tried is a ledgered arm; (5) de-risk (half
size) is tested alongside hard cuts — sometimes the answer is smaller, not
none. Trigger event for this rule: the H2-2025 losing stretch both pre-market
winners shared, invisible at calendar-year granularity — half-year (or finer)
decomposition is now part of the standard autopsy.

Everything downstream (§6 promotion) consumes only what survived a layer gate.

---

## 4. The holdout rule and THE LEDGER

### 4.1 The rule [EXISTING]

- **The holdout is the sealed 2023/24 span**: 6 month-blocks (2023-07, 2023-09,
  2023-11, 2024-03, 2024-04, 2024-10), day list drawn seed `20260727` and pinned by
  SHA-256 in `docs/HOLDOUT-2023-24-PREREGISTRATION.md`, day list at
  `data/reference/holdout_2023_24_days.csv`. 128 calendar days drawn (63/65); cited
  elsewhere as 122 trading days — [OPEN — needs Angus/Pat: which count is canonical
  for citation, 128 drawn vs 122 traded].
- **"Run ONCE, frozen, at the very end. No peeking, no iterating. If you touch it
  twice, it is no longer a holdout and Angus should be told"**
  (`docs/HANDOFF-london-rebuild.md` §3).
- **"Score with the canon unchanged — no refits, no new knobs. Any threshold that
  moves makes this a fit, not a holdout"** (`docs/HOLDOUT-2023-24-PREREGISTRATION.md`).
- **One look per strategy/family, never one per knob:** "freeze combined candidates
  and spend ONE look per family" (`docs/HANDOFF-agents-capture.md` §0). Only a frozen
  policy earns a look; the holdout is never charged twice for the same question
  (`docs/PLAN-agents-capture-run.md` §8).
- **Never revise a strategy after its look** (brief §2a-4). A post-look revision is a
  new strategy and starts over at §1 — and its holdout look is already spent unless
  Angus explicitly grants another.
- **Every look is declared before looking** and entered in the ledger below, so
  results are always read in the light of how many were tested.
- **A holdout PASS does not auto-ship.** Look 2: the 25% partial PASSED holdout
  (+$60,017 vs +$56,409, +6.4%) and Angus ruled base V8 stays ("the profit difference
  is negligible"); the candidate is documented as available, unshipped
  (`docs/HANDOFF-agents-capture.md` §0/§7).
- **Merely building a sealed-span artifact is a look.** "Computing on the sealed span
  **is a holdout look**" — e.g. `output/london_canon_book_holdout.parquet` does not
  exist, and building it requires a declaration first
  (`docs/REPORT-correlation-2026-08-04.md`).

### 4.2 THE LEDGER — canonical copy

[PROPOSED — Angus to ratify]: the canonical home of the holdout ledger is
`vault/holdout-ledger.yaml` (docs/VAULT-SCHEMA.md §3.8) once the vault is ratified;
this section is the interim home and then becomes a citation of that file. Until now
the ledger has been restated in each successive handoff
(`docs/PLAN-agents-capture-run.md` §8 at 2 looks → `docs/HANDOFF-agents-capture.md`
§0/§1 at 5 → live HANDOFF §7) with no single home. Handoffs should now cite this
section and update it, not restate it.

**State as of 2026-08-04: 5 looks spent, each declared before looking**
(`docs/HANDOFF-agents-capture.md` §1; live HANDOFF §7):

| # | Question (one per family) | Outcome |
|---|---|---|
| 1 | Time-segment state confirmation | confirmed |
| 2 | The 25%-partial referendum | PASS (+$60,017 vs +$56,409); Angus ruled base V8 stays — unshipped |
| 3 | Close-and-reverse vs flatten-only (execution semantics) | flatten-only $49,880 / CR $59,407 vs shipped $56,409 |
| 4 | Two-session pre-flatten | shipped as rule K |
| 5 | One-per-level | shipped as rule L |

**UNSPENT and sealed: the agent layer's one-shot look.** "Shipped on fit + funded
evidence; the look stays available" — it needs Angus's explicit go, with a frozen
policy; post-shuffle the natural candidate is a mechanical distillate (defense cuts +
`lock1r_2r`-style refusal), not the chain (`docs/HANDOFF-agents-capture.md` §0
postscript; live HANDOFF §7, §8.5; `docs/REPORT-desk-run-2.md`).

---

## 5. Verdict format

**[EXISTING format, NEW — brief: the INCONCLUSIVE state.]** One message per gated
step, after EVERY gated step (`docs/HANDOFF-london-rebuild.md` §6), and the brief
§2a-5 fixes the target form:

```
VERDICT — <experiment id> — <date> — <commit>
Ran:     what ran, on which span(s)
Result:  PASS | FAIL | INCONCLUSIVE — with the numbers, against the pre-registered bars
Killed:  what died and why (with the number), or "nothing"
Next:    what runs next
Caveats: stated, not hidden
```

Rules of the form, all evidenced:

- **The verdict is stated before the diagnosis.** `docs/REPORT-parity-2026-07-29.md`
  opens: "**Result: FAIL, 93.06% gate agreement (bar: 100%). DO NOT ARM stands.**"
- **`INCONCLUSIVE` blocks exactly like FAIL** (brief §2a-5). Underpowered, ambiguous,
  or mixed results do not pass by default; they stop the ladder until resolved or
  tombstoned. (This codifies what §2.2's minimum-n rule already implies.)
- **Kill-criteria results are graded by table, per criterion, including the FAILs** —
  `docs/REPORT-desk-run-2.md` grades all four pre-registered criteria, reports the
  shuffle FAIL (p=0.978) in plain language ("The conviction shuffle, plainly"), and
  flags its own weakenings in Methods ("netting moved the control from +495.1R to
  +480.5R, which is what makes criterion 2 a narrow pass instead of a kill; flagged
  for honesty").
- **Nothing in a verdict self-authorizes** a gate change, a ship, or a scale-up (§0
  law 3). Ship decisions are Angus rulings quoted with a date.
- The vault serializes this format as the `verdict` record (docs/VAULT-SCHEMA.md
  §3.3); NARROW PASS is legal only as a per-criterion annotation there, never a
  top-level result.

---

## 6. The promotion ladder

Gauntlet → holdout → funded-rules MC → shadow → live at minimum size → scale on
evidence, **with a human sign-off at the paper-to-live step** (brief §2a-6). Every
rung already exists in practice; this section names them in order.

1. **Gauntlet** — §1 pre-registration + §3 layer gates + §2 acceptance bars, discover
   2025 / validate 2026. Output: a frozen candidate with a verdict at every layer
   boundary. [EXISTING]
2. **Holdout** — one declared look per §4, frozen policy, canon unchanged. A PASS
   does not auto-ship (§4.1). [EXISTING]
3. **Funded-rules MC** — the candidate under the funded shell (50k account, $2k
   EOD-trailing, budget = base × 16/3 = $853.33 at $160, rules J/K/L) through
   `scripts/mc_funded_lab.py`: P(bust), maxDD, worst day, payout frequency.
   **MC is never evidence of edge** (ANGUS critique 2026-08-04): a fit-span
   bootstrap resamples the very dataset the candidate was optimized on — circular
   as a proficiency grade. Rungs 1–2 (era split, permutation nulls, DSR/PBO, the
   holdout look) establish whether the edge is real; this rung only converts an
   already-established edge into funded-account arithmetic — sizing, ruin, payout
   cadence. Where a holdout day series exists, feed it alongside fit. Existing
   reference: the agent book runs P(bust) 0.1%, median 53 payouts (funded_book
   docstring). Proposed bar: **P(bust) ≤ 1.0%** standalone and combined [PROPOSED —
   Angus to ratify; the combined figure matches `docs/REPORT-correlation-2026-08-04.md`
   threshold 4]. **For a second strategy the promotion decision is marginal portfolio
   contribution, not standalone net** (brief §3): does adding B to A improve combined
   MC pass probability, reduce P(bust), raise payout frequency — with the correlation
   battery's thresholds (max pairwise |ρ|, tail dependence, min common days,
   input-family veto) per that report, all [PROPOSED — Angus to ratify] there.
   [NEW — brief, battery already running]
4. **Shadow** — on-box certification, force-tested rather than observed: replay-day
   runbooks, kill tests, burn-in (`docs/RUNBOOK-cert-saturday.md` — certified on
   attempt 4 — three non-certifying attempts (two labeled FAIL), four named bugs
   surfaced and test-pinned (ARMING-REFERENCE R13);
   `docs/RUNBOOK-cert-r15.md` — agent process killed mid-trade 7/7, trade completes
   mechanically, `agent_R == v8_R` exactly; `docs/RUNBOOK-burnin-r16.md` — connectivity
   heal + the KILL-file override proven, "the one behavior that must never fail").
   [EXISTING] Note the shop's deliberate stance from the old PROMOTION-GATE §0
   (Angus 2026-07-26, recovered git d420b10~1): **no paper P&L period — "the eval IS
   the test"** — with the compensating rule that the correctness gates get
   **stricter**, not looser. Shadow here means proving the machine, not auditioning
   the P&L. [PROPOSED — Angus to ratify: confirm the 2026-07-26 eval-IS-the-test
   stance extends to newly promoted strategies — that ruling was made for the canon,
   not dated after the brief.]
5. **Live at minimum size — the human sign-off.** The two-party arming protocol IS the
   paper-to-live sign-off: conformance lock green (`tests/test_canon_scorer_ny.py`,
   19/19 — live scorer must match `scripts/funded_book.py` exactly), gate checklist
   R1–R16 closed (`docs/ARMING-REFERENCE.md` §4), Pat's written confirmation naming a
   certified SHA, Angus's token committed in `config/arming.yaml` (hash + armed_sha +
   account + entrypoint), provenance enforced (HEAD == armed_sha or differs only in
   arming.yaml; else refuse, fail-closed, named reason — "A refused arm never silently
   degrades to a shadow run", live HANDOFF §4). Entries 100% mechanical. The KILL file
   overrides everything. [EXISTING]
6. **Scale on evidence.** Base changes are dated ANGUS rulings ($150→$160, ANGUS
   2026-07-31); `scaled600` exists as a measured reference (+$272,847 fit /
   +$142,565 holdout), not an entitlement. **Any behavior change re-runs the two-party
   step** (the R15b precedent). [EXISTING]

**Carried forward from the old PROMOTION-GATE §F (deleted in the `d420b10` canon
purge, recovered from git; the discipline survives):** P&L, win rate, and drawdown
over short windows are explicitly NOT gates, in either direction — "A profitable run
that fails an A-gate is halted. An unprofitable run that passes every gate keeps
running." Correctness failures are disqualifying, not deductions.

[OPEN — needs Angus/Pat]: `docs/PROMOTION-GATE.md` is deleted but still referenced by
`src/live/arming.py`, `src/canon/gate_evidence.py`, `config/live.yaml`, and
`docs/RUNBOOK-cert-saturday.md`. This doc now carries its process role; the code/config
cross-references need a redirect decision, and those files are frozen from this
working branch.

---

## 7. Kill criteria

### 7.1 For a hypothesis [EXISTING pattern]

Pre-committed at §1, in the form of `docs/PLAN-agents-capture-run.md` §9: "dies...
if ANY of." The standard list any pre-registration starts from:

1. **Era-split sign flip** (2025 vs 2026, or any era pair) — PLAN §9 criterion 3;
   QA-LOG entries 35, 51.
2. **Fails the family-wise permutation null** (§2.3).
3. **Positive only via ≤ 3 trades** (drop-top-3 fragility) — PLAN §9 criterion 1;
   the rr_floor-1.5 RETRACTION precedent.
4. **Loses to the best mechanical control** — PLAN §9 criterion 2.
5. **Only works leaky** — dies the moment the harness is causal ("looked great leaky,
   died honest").
6. **Monotone-worse ladder** — the parameter family is exhausted by measurement
   (the rr_floor pattern below).
7. **FAIL or INCONCLUSIVE on its one holdout look** (§4, §5).

**Every kill gets a tombstone** (brief §2b: "Formalise it"; the pattern is the
rr_floor tombstone, `docs/HANDOFF-agents-capture.md` lines 44–59). Required anatomy,
extracted from that tombstone:

1. `TOMBSTONE — <question> (CLOSED <date>, ...)`;
2. spans consumed, and explicitly whether a holdout look was spent ("fit-only, no
   holdout look spent");
3. whose idea, quoted;
4. run through the REAL engine on the canon fills — never a proxy;
5. the result table;
6. the *mechanism* of why it fails, not just the number (rr_floor: "a higher floor is
   increasingly an ENTRY change wearing an exit costume");
7. the conclusion;
8. **the reopening burden** — what evidence would justify reopening ("a triple-era
   result at least as strong as this monotone ladder");
9. artifact paths.

Statuses in the vocabulary, all in use: **TOMBSTONE/CLOSED** (killed with burden),
**RETRACTED** (a claimed result withdrawn with the diagnosis —
`docs/RULING-mechanical-only.md`), **SUPERSEDED** (replaced, pointer mandatory, never
deleted), **UNSPENT** (a sealed look not yet taken), **dormant** (a rule that never
fires on history, kept as insurance — the ramp) (canonical list:
docs/VAULT-SCHEMA.md §4).

### 7.2 For a session [NEW — brief §2a-7; defaults PROPOSED — Angus to ratify]

No session has ever been killed, so there is no precedent to codify — only the
standing law that bounds the search ("Do not torture the data until it confesses").
Proposed defaults for when a *session* stops being worked:

- **Breadth kill:** ≥ 10 pre-registered hypotheses spanning ≥ 3 distinct mechanism
  families all killed on the discovery span → the session goes **dormant** with a
  session-level tombstone. [PROPOSED — Angus to ratify]
- **Economics kill:** the session's best surviving candidate fails the funded-rules
  MC at minimum size (P(bust) above the §6 bar) → dormant; the strategy research was
  fine, the session cannot carry funded risk. [PROPOSED — Angus to ratify]
- **Validation-capacity kill:** the session has no external ground truth (no hand
  log) AND its candidates cannot clear the stricter statistical bars that substitute
  for it (Appendix A) → the session cannot be validated at all under current data;
  dormant until a new data source or ground truth exists. [NEW — brief §6 logic]
- A session tombstone carries the same anatomy as §7.1, including a reopening burden
  (new mechanism family, new data source, or a triple-era result at least as strong
  as the evidence that closed it — the time-based-cut burden phrasing,
  `docs/HANDOFF-agents-capture.md` §6).

---

### 7.3 Live decay monitoring [NEW — education round 2026-08-04; PROPOSED — Angus to ratify]

Edges decay as their normal life path (measured post-publication decay is ~25–50%
even for real effects — `research/findings/strategy-classes-evidence.md`). Two
additions at certification time, so retirement is mechanical rather than an
argument:

- **The era-decay slope is a certification statistic**: performance in later vs
  earlier eras is already computed by the split — report it on the verdict. A
  measured half-life shorter than the validation window blocks promotion (the
  pass was already stale when graded).
- **Probation rules are written before going live**: CUSUM on realized-vs-expected
  per-trade P&L against the certified MC distribution; trailing-N expectancy below
  the certified 5th percentile → probation (half size); CUSUM alarm → demote to
  paper pending review. Drawdown *within* the certified distribution is expressly
  NOT evidence of death (the MC percentile bands say which is which) — kill-speed
  matches the signal's half-life, and deciding kill rules after the drawdown
  starts is overfitting in reverse.

## 8. Re-speccing a gate — the R10b pattern [EXISTING, canonized]

Gates are never waived. When a gate fails and the bar itself is suspected, the ONLY
sanctioned path is the one R10b walked (`docs/REPORT-parity-2026-07-29.md`; live
HANDOFF §6):

1. **State the FAIL first, undiluted.** "Result: FAIL, 93.06% gate agreement (bar:
   100%). DO NOT ARM stands."
2. **Diagnose the failure into what it is NOT**, each exclusion with a number (not
   scale, not size inflation, not snapshot convention, not conflation).
3. **Pre-declare a decisive experiment with its decision structure written before the
   result exists**: vendor's own file vs itself at 500ms skew — if the floor ≈ the
   capture's score, the bar is unachievable by construction across clocks; if ≈ 100%,
   the feed is genuinely dirty and nothing arms.
4. **Run it, report it, and still do not self-authorize.** Floor came back 88.12% —
   the vendor disagrees with itself more than the box disagrees with the vendor — and
   the report still said "DO NOT ARM remains in force until Angus rules; nothing here
   self-authorizes."
5. **Angus re-specs with evidence, and the new spec is shop-proof:** PASS = agreement
   ≥ the same-day vendor self-skew floor at a **permanently fixed 500ms** (so nobody
   can shop for a friendlier floor), AND every bias check at full strictness (majority
   of matched levels byte-identical, size-ratio median ≈ 1.00, alignment best at lag
   0, exact price scale, full 10 levels both sides).
6. **The re-specced gate carries a reopening trigger:** any feed/config change REOPENS
   it with a fresh capture + floor.
7. **Bound the materiality, with its own caveat stated:** 3 flips / 280 probes
   (1.07%) ≈ 0.04 differing trades/session.

"Keep this pattern. Gates get re-specced with evidence and a pre-declared experiment,
never waived because they're inconvenient" (live HANDOFF §6). This applies to every
gate in this document, including the §2 bars once ratified.

---

## 9. Live-period change control — the 5-day-loop law [NEW — brief §5, ratified with this doc]

"Based off results fix + optimize, next 5 trading days repeat" is two very different
actions sharing a line. Ruled apart, per brief §5:

- **Bugs ship now.** A correctness defect in the live path is fixed immediately —
  and, because the arming branch is live, it ships via the deliberate re-cert flow:
  Pat certifies the new SHA, this chat re-issues the authorization, the two-party
  step re-runs (live HANDOFF §0 is the live example — the R16 audit changed the
  arming contract and the next arm refuses until re-authorized).
- **Optimisations NEVER ship off live results.** Five days of live data is fitting to
  noise on a sample far too small to carry a decision (§2.2's minimum-n makes this
  quantitative), and every mid-flight change resets the live-vs-backtest parity
  record being accumulated. Optimisation candidates are **logged** (vault entry,
  status: proposed — docs/VAULT-SCHEMA.md §4), **validated offline** through this
  entire document (§1 → §6),
  and **shipped as versioned releases** — a new certified SHA through the two-party
  step, never a casual commit.
- The existing stop-and-review discipline stands beside this: any code change to
  canon/sizer/spine/relay, any D1-class event, any feed/config change on the box →
  stop and review, re-arm deliberately (old PROMOTION-GATE §E's stop-and-review
  triggers); 2 consecutive halt days → stop and review before re-arming (old
  PROMOTION-GATE §D2, recovered, git d420b10~1).

---

## Appendix A — Acceptance bars for Brake's current London hypothesis round

*Separable sign-off (brief §9 item 7): Angus can ratify this appendix alone to
unblock Brake before the whole doc is ratified.*

**Scope.** London window 08:00–10:00 Europe/London, converted per-day via
`scripts/run_triggers_london.london_window_et` — never hardcode the ET hours
(`docs/HANDOFF-london-rebuild.md` §2). Rebuild method: the L0–L4 ladder of §3, per
`docs/HANDOFF-london-rebuild.md`. The old London book
(`output/london_canon_book.parquet`) is a reference to beat, not a book to trade
(`docs/CANON.md`); its +$35,219 is un-governed research sizing.

**Per hypothesis, before any scoring run:**
1. A §1 pre-registration, committed — statement, mechanism, mechanism family, input
   columns (exact column names), session, entry type (E3-style rotation/limit vs
   E4-style momentum), acceptance bars, kill criteria (brief §6: "Same format as
   his: statement, mechanism, mechanism family, input columns, entry type").
2. The input-column declaration is evaluated against the correlation input-family
   veto AT pre-registration time. NY↔London already shares 3/7 gating families
   (depth walls, overnight structure, order flow/CVD —
   `docs/REPORT-correlation-2026-08-04.md`), which trips that report's proposed
   ≥3-shared-families waiver line. Any new London hypothesis leaning further into
   shared families needs the waiver question answered before, not after, the work.

**Eras and bars for this round:**
- Discover on 2025 ONLY; validate on 2026; triple-era survival required (§2.1).
- Sealed 2023/24 holdout: **one look per surviving family**, declared in the §4
  ledger first. The London holdout book does not exist
  (`output/london_canon_book_holdout.parquet` unbuilt) and **building it is itself a
  look** requiring declaration (`docs/REPORT-correlation-2026-08-04.md`). Sealed-day
  inputs already exist without look-spending: 5,873 sealed-day London triggers
  (`scripts/holdout_london_triggers.py`), depth at
  `data/reference/depth_london_2023_24/` (128 sealed days), day list SHA-pinned in
  `docs/HOLDOUT-2023-24-PREREGISTRATION.md`.
- Minimum n per era: ≥ 30 trades per era cell for direction claims, ≥ 100 pooled for
  magnitude claims [PROPOSED — Angus to ratify, §2.2].
- Family-wise permutation null, ≥ 1,000 shuffles, p ≤ 0.01 [PROPOSED — Angus to
  ratify, §2.3].
- DSR ≥ 0.95, PBO ≤ 0.25 (0.25–0.50 INCONCLUSIVE = blocks; ≥ 0.50 condemns the
  search procedure) [PROPOSED — Angus to ratify, §2.4].
- Beat the best mechanical control; drop-top-3 fragility; causality; oracle ≠ policy
  (§2.5).
- **Stricter, not looser — the London-specific tightening** (brief §6: "you have no
  hand-log ground truth outside 08:00–10:30... Set the bars stricter, not looser,
  precisely because your eye can't backstop them here"). Concretely [PROPOSED —
  Angus to ratify]: the validate-2026 era must **independently clear the permutation
  null**, not merely point the same direction — same-direction-only is INCONCLUSIVE
  in London, and INCONCLUSIVE blocks (§5).
- London risk gate stands: risk ≥ 9.5 pt, no cap (`LON_RISK_MIN`,
  `docs/HANDOFF-london-rebuild.md` §2). In-trade management starts from the verified
  London finding "NONE — London holds to the stop. Do not port NY/gold cuts"
  (`scripts/london_canon.py` docstring); any managed-exit hypothesis argues against
  that measurement explicitly.
- Emission format per the data contract (brief §2c): day-level P&L series, signal
  timestamps, direction, risk, mechanism tag, input columns — with the mixed
  −04:00/−05:00 offset handling of burn-list item 1 (utc=True parse) plus the
  format="mixed" convention of `docs/HANDOFF-agents-capture.md` §5
  (`pd.to_datetime(..., format="mixed", utc=True)`).

**Blockers on this round, recorded so nothing silently proceeds:**
- **London execution-semantics rulings (the J/K/L equivalents) are owed by Angus
  before Brake's run can be baselined** (live HANDOFF §8.6): session-flatten
  (the old book holds trades into NY hours — 2 of 136 taken trades exited 09:00 and
  09:30 ET), close-and-reverse, one-per-level, plus the §5 re-verify items of
  `docs/HANDOFF-london-rebuild.md`. [OPEN — needs Angus]
- **The parked London wall-arm candidate** — the brief (§5) says Brake's brief parks
  it as a cousin of the canon, holdout look unspent, and asks Angus to confirm or
  overrule. No repo file names the candidate's spec; its exact definition and
  park/overrule status are [OPEN — needs Angus/Pat].

**Sign-off (this appendix alone):**
ANGUS — date: __________ — bars ratified for Brake's round: __________
(Every [PROPOSED] number above becomes the bar for this round on signature; changes
after signature follow §8 — evidence + pre-declared experiment, never waived.)

---

## Appendix B — roll-up of everything awaiting Angus

**[OPEN — needs Angus/Pat] (facts/rulings this doc could not settle):**
1. Holdout day-count canonical citation: 128 drawn vs 122 traded (§4.1).
2. PROMOTION-GATE.md cross-reference redirect in `src/live/arming.py`,
   `src/canon/gate_evidence.py`, `config/live.yaml`, `docs/RUNBOOK-cert-saturday.md`
   (§6) — code-side edits are outside this doc's scope and frozen paths.
3. London execution-semantics rulings, J/K/L equivalents (Appendix A).
4. The parked London wall-arm candidate — spec and confirm/overrule (Appendix A).

**[PROPOSED — Angus to ratify] (defensible defaults, not law until signed):**
5. Minimum n per era: ≥ 30/era for direction, ≥ 100 pooled for magnitude; Wilson
   lower bound above the pre-set bar for sizing tiers (§2.2).
6. Permutation null: ≥ 1,000 shuffles, family-wise max-statistic, p ≤ 0.01 (§2.3).
7. DSR ≥ 0.95; PBO ≤ 0.25 pass / 0.25–0.50 INCONCLUSIVE / ≥ 0.50 condemns the
   search (§2.4).
8. Funded-rules MC: P(bust) ≤ 1.0% standalone and combined (§6, rung 3; aligns with
   `docs/REPORT-correlation-2026-08-04.md` threshold 4 — that report's five
   correlation thresholds are their own ratification list).
9. The holdout ledger's canonical home is `vault/holdout-ledger.yaml`
   (docs/VAULT-SCHEMA.md §3.8) once the vault is ratified; §4.2 of this doc is the
   interim home and then becomes a citation of that file (§4.2).
10. Session-kill defaults (§7.2).
11. London tightening: validate-era must independently clear the null (Appendix A).
12. Appendix A as a whole — signable separately to unblock Brake (brief §9 item 7).
13. Confirm the 2026-07-26 eval-IS-the-test stance (old PROMOTION-GATE §0, recovered
    git d420b10~1) extends to newly promoted strategies (§6 rung 4).
