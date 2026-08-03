# HANDOFF — London NQ strategy, full context as of 2026-08-03

**Audience: a fresh session with zero prior context.** Read §1 and §2 before doing anything
else. Every number here was verified against the repo on 2026-08-03, not recalled. Where a
fact could not be verified it is marked UNVERIFIED.

---

## 1. READ THIS FIRST — the four things that change what you'd otherwise assume

1. **The sealed 2023/24 holdout has ALREADY BEEN RUN, and the primary test FAILED.** It ran
   2026-07-31 under Angus's authorization. Promotion is BLOCKED. The seal is spent — there is
   no second run. Anyone who tells you "the next step is the holdout" (including earlier notes
   in this repo, and including me earlier in the session that produced this file) is wrong.
   See §3.

2. **The sealed work is on a branch that is NOT merged and NOT in the main line of history:**
   `origin/claude/sealed-run-prep`, tip `1b186c56c9f165a5acea4e8e4eb3fbc0df86d4df`. If you
   `git log` on any other branch you will not see it, and `docs/LONDON-HOLDOUT-REPORT.md` will
   appear not to exist. Use `git show origin/claude/sealed-run-prep:docs/LONDON-HOLDOUT-REPORT.md`.
   **This is exactly how the holdout's existence got missed once already.**

3. **The LLM trade-management agent lost to the plain mechanical rule in all four runs.** That
   line of work is finished and archived. Its value was as instrumentation: it is *how we proved*
   hands-off management is optimal on this book. Do not resurrect it as a live component. See §5.

4. **Fit data is heavily mined — roughly 20 statistical "looks" spent.** Anything new "found"
   on the 2025-06-02 → 2026-07-15 span is now more likely noise than signal. Fit data is for
   *diagnosis*, not for selecting new strategy elements. See §7.

---

## 2. What the strategy is

**rev 3 London canon + V1 management.** Trades NQ futures in the London morning session.

| element | value |
|---|---|
| Window | 08:00–09:45 Europe/London (`cut_min=585`, fills strictly before) |
| Entry gate | wall = (W **or** FAR), stop floor 9.5 pt |
| Filter | score-0 conviction veto |
| Concurrency | one position at a time (`serial=True`, `day_stop=400.0`) |
| Management | **V1** — stop at −1R, move to breakeven on touch of +1R, then run untouched to the real structural target |
| Sizing (research convention) | flat 1 NQ lot |

Defined at `CONFIGS["rev3"]` in `scripts/london_holdout_report.py` (lines ~89–98).

### The gate mechanics (`src/canon/scorer.py::london_checks`, ~line 286)

- **W** = `1.0` iff the wall *behind* entry is NaN — i.e. **no resting liquidity wall behind you**.
  (NaN-as-signal, not NaN-as-missing. This trips people up.)
- **FAR** = `1.0` iff the wall *ahead* is farther than `LON_FAR_MIN = 4.5` pt — clear runway.
- **ROOM**, **ASIA** also exist in this function but **are not used by rev 3** (see below).

Score-0 veto literals are **FROZEN** (`src/canon/scorer.py`): `dep_thick > 57`,
`dep_resist > 29`, `trigdens_30 > 8`. ±10% perturbation was flat.

### Important: rev 3 does NOT use orderflow

The selection path is `lon_book()` → `score = wall` → L4 policy. It **bypasses**
`LondonScorer.decide()` entirely, so the `ASIA` (Asian-session CVD) check and the `opp5`
order-flow sizing layers in that function **never fire** in rev 3. The strategy uses **order
book depth** (MBP-10: walls, thickness, resistance) but **not** tape/CVD/aggressive delta.
CVD is computed and stored in the data; it influences zero rev-3 entries.

This matters because the fit span starts 2025-06-02 — the exact day MBP-10 depth coverage
begins. **Without depth data there is no strategy.**

### Fit-data performance (2025-06-02 → 2026-07-15)

| metric | value |
|---|---|
| Trades / days | 130 / 93 |
| Net (1 NQ lot) | +$22,665 |
| Win rate | 29% (structural — V1 scratches ~40% at BE; mean R and net are the health metrics) |
| Mean R | +0.758 |
| maxDD (trade-level chronological) | $1,310 |
| Months green | 10/14 |
| Era split | 2025: n=57, +$7,965, +0.578 · 2026: n=73, +$14,700, +0.898 |

Reproduce with: `python -m scripts.london_holdout_report --span fit --config rev3`
(re-verified 2026-08-03: 21/21 committed anchors reproduce, zero byte diff).

### The conviction ladder (developed this session, NOT validated out-of-sample)

Grades, applied as a **sizing overlay** — it does not change which trades are taken:

| grade | definition | weight |
|---|---|---|
| **A+** | `pattern == "B2"` AND `W==1` AND `FAR==1` | 2.0x |
| **neither** | NOT B2 AND NOT both-walls | 0.5x |
| **mid** | everything else | 1.0x |

Funded sizing formula (MNQ micros, $2/pt):
`micros = min(40, round(weight * 200 / (stop_pts * 2)))`

Verified to land on target: A+ target $400 → actual mean $402; mid $200 → $200;
neither $100 → $103. Rounding error ~$6-7/trade, no trade sized to 0 or capped at 40.

Fit performance by grade (n=130):

| grade | n | mean R | WR | net | biggest win |
|---|---|---|---|---|---|
| **A+** | 45 | **+1.597** | 49% | **+$18,050** | +10.37R |
| mid | 62 | +0.291 | 19% | +$2,210 | +7.58R |
| neither | 23 | +0.376 | 17% | +$2,405 | +5.44R |
| whole book | 130 | +0.758 | 29% | +$22,665 | +10.37R |

**35% of trades carry ~80% of the profit.** That is the case for the 2x weighting — and it
rests entirely on fit data. See §3.4 for what the holdout says about it (not much, and not good).

---

## 3. THE SEALED HOLDOUT — what happened, in full

### 3.1 The setup (all pre-committed, verifiable timestamps)

- Day list sealed 2026-07-27 08:25 UTC, **~6 hours before the first byte of 2023/24 data
  entered the repo** and 4 days before the run. SHA-256 `f4e17f1770a4d5314d02ccdda7d362b97ae891aa833ea21ef564fc5ca7c9a87e`
  (independently regenerated and confirmed).
- **128 days drawn from 513 eligible**, 6 monthly blocks: 2023-07, 2023-09, 2023-11, 2024-03,
  2024-04, 2024-10. Split 63/65 across the two years. Seed `20260727`.
- **2 gated tests only** → Šidák per-test **alpha = 0.0253**.
- Authorized by **Angus, verbal, in person, relayed by Brake, 2026-07-31**. The record itself
  flags this as "a weaker instrument… labelled as such here rather than dressed up," and notes
  the run proceeded "under time pressure."

### 3.2 Era inputs measured BEFORE the seal opened (this part is genuinely well done)

| metric | fit | sealed 2023/24 | deviation | verdict |
|---|---|---|---|---|
| session range (median) | 179 pt | **92 pt** | **−48.3%** | **OUTSIDE ±25%** |
| stop/range (median) | 7.38% | **13.06%** | **+76.9%** | **OUTSIDE ±25%** |
| candidate density | 3.76/day | 2.88/day | −23.4% | within ±33% |
| wall pass rate | 24.1% | 24.3% | +0.2 pp | within ±10 pp |

→ **Branch (B): regime materially different.** Pre-committed rule: a weak result may be read
as "untested in this regime," **never** as "validated," and **promotion is blocked either way**.

The mechanism was predicted in advance, before any outcome: NQ traded at roughly half the index
level in 2023/24, so the session moved ~half as far in points, but the stop floor is fixed at
9.5 pt. That doubles stop/range. A 2R target went from needing ~13% of session range to **26%**.
The prediction stated win rate would collapse. It did: **29% → 18%**, exactly as forecast.

Wall pass rate being identical (24.3% vs 24.1%) rules out a feature-pipeline fault. The
signal-detection layer travelled; the geometry did not.

### 3.3 The result

| test | n | mean R | SE | t | p | alpha | verdict |
|---|---|---|---|---|---|---|---|
| **PRIMARY — book mean R** | 56 | **+0.134** | 0.167 | +0.80 | **0.4278** | 0.0253 | **FAIL** |
| S1 — sub-9.5 stop band | 146 | +0.560 | 0.125 | +4.49 | 1.4e-05 | 0.0253 | **PASS** (reported, not acted on) |

Book: **56 trades / 38 days / net +$740 / WR 18% / maxDD $2,115 / 2 of 6 months green /
worst month −$905 / 0.8 trades per week.** maxDD exceeds net profit.

Per era: **2023 n=14, −$485, WR 14%, mean R −0.125** · **2024 n=42, +$1,225, WR 19%, mean R +0.220.**

Not a sign flip (mean R is positive) — but statistically indistinguishable from zero, and far
from the +0.48 declared forward expectation (which the recalibration had already ruled
inapplicable to this regime).

**Bucket profile (descriptive):** 08:00–08:30 n=25 +0.415 · 08:30–09:00 n=11 −0.201 ·
09:00–09:30 n=18 +0.012 · 09:30–09:45 n=2 −0.453. The early bucket was the only strong one.

### 3.4 What the holdout says about the conviction ladder — the wall half failed to select

**Item 9 (W/FAR lift, pre-designated as the primary *signal* evidence** because it compares
wall-passing vs non-wall candidates *within* the sealed span, so the geometric handicap
cancels):

| slice | either n | either R | neither n | neither R | lift | fit anchor |
|---|---|---|---|---|---|---|
| pooled | 74 | +0.135 | 237 | −0.167 | **+0.302** | +0.754 |
| 2023 | 17 | −0.104 | 64 | −0.129 | **+0.025** | +0.584 (2025) |
| 2024 | 57 | +0.206 | 173 | −0.181 | **+0.388** | +0.874 (2026) |

Survived in 2024 at roughly half fit magnitude; **absent in 2023**.

**Item 10 (descriptive, prereg forbade inference):** both W+FAR n=38 mean R **+0.159** ·
exactly one n=18 mean R +0.081 · whole book +0.134.

So requiring **both walls** lifted mean R by **+0.025** over the book on holdout, versus
**+0.136** on fit. **The wall component did not reproduce its fit-side selectivity.**

**The B2 pattern half of the A+ definition was NEVER computed on holdout.** It does not exist
anywhere in the record. And it is the bigger ingredient — on fit it is what carries A+ from
+0.894 (walls alone) to +1.597 (walls + B2). Attempting to compute it now requires rebuilding
the London L0→L3 pipeline for the holdout span (see §8.3), and would be a *second look at spent
data* — informative if negative, close to worthless if positive.

### 3.5 Governance rulings that bind (do not quietly override these)

- **No second run.** The runner refuses to execute while `docs/LONDON-HOLDOUT-REPORT.md` exists
  (demonstrated, not assumed). Runbook §8: *"Stop. Do not re-run. Do not slice. Do not propose
  a config change in the same session the numbers first appear."*
- **S1 is reported, not acted on.** Standing Angus ruling: the 9.5 floor stays; the era crossing
  already rejected floor 5 and it is not being relitigated.
- **Item 10 / S2 carries no decision.** Acting on it retroactively makes the family 3 tests and
  invalidates the Šidák correction.
- **No post-hoc subsetting** of the holdout by block, month, or volatility tercile (§4.6).
- **The parked list does not get re-opened on fit evidence to rescue a failed holdout** —
  "that is precisely how a 13-look dataset becomes a 20-look dataset."
- **Three engine rulings remain OPEN** and are *not* carried by this run: (1) same-order twins
  double-counting fills (329 population groups, 9 doubled positions), (2) day-stop units
  (the $400 stop was applied to 1-lot dollars in backtests; a funded Vault counts funded
  dollars — 144 vs 155 trades at $250 sizing), (3) no-realistic-target trades (engine posts
  an 8–36R far level meaning "no TP, managed by stop").
- The promised **verdict document was never written** — the sealed branch tip is the execution
  commit. That is an outstanding deliverable.

---

## 4. Where everything lives

| what you want | where |
|---|---|
| **Sealed holdout report, runbook, era-inputs script** | `origin/claude/sealed-run-prep` **only**, tip `1b186c5`. Not merged. |
| Holdout prereg (day list, SHA) | `docs/HOLDOUT-2023-24-PREREGISTRATION.md` — on both branches, byte-identical |
| Question prereg (alpha, power, gated tests) | `docs/LONDON-PREREGISTRATION.md` |
| The rev-3 decision package | `docs/LONDON-REV3-BUNDLE.md` |
| Known regime fragility (pre-dates the holdout) | `docs/LONDON-ERA-DIAGNOSIS.md` |
| **This session's agent work (runs 1-4)** | `claude/agent-capture-london`, tip `a5f7348` — currently checked out, clean, in sync |
| V9 / partial-BE exit sweeps | `claude/london-be-sizing-scratch`, tip `0963e52` |
| NY-session reference implementation | `claude/agents-capture-handoff-26rnvp` |
| Canon config | `scripts/london_holdout_report.py` → `CONFIGS["rev3"]` |
| Gate logic | `src/canon/scorer.py::london_checks` |
| Book construction | `scripts/london_combined_job.py::lon_book` + `build_book` |
| Funded sizing convention | `scripts/london_funded_test.py::fund` |

**18 remote branches exist.** The repo is ~236 MiB packed, 4274 tracked files.

### Files that are FROZEN — do not edit; if one needs changing, STOP and ask

`CONFIGS["rev3"]`, `src/canon/scorer.py`, `src/backtest/engine.py`, the preregistration docs,
the rev-3 bundle. Holdout guards (`src/research/holdout_guard.py`:
`assert_path_fit_only`, `filter_to_fit_years`) are load-bearing safety — do not route around
them. An auto-mode classifier will also block commands that explicitly target holdout data;
that is intended.

---

## 5. This session's work — the LLM agent experiment (runs 1–4)

**Question:** does an LLM given live tape/flow context manage trades better than mechanical V1?
**Answer, after four full runs: no.** V1 is undefeated.

Design: 161 pre-serialization rev-3 candidates. One Claude CLI conversation per trade, all tools
disabled, event-driven turns (whole-R touches, giveback off peak, flow flips, stop proximity,
V1's own exit moment, EOD warning). Between turns the standing plan executes mechanically.
Admission is re-derived live per arm ("dynamic one-at-a-time re-walk", PLAN §4b) because each
arm's own realized exit times change which later candidates are reachable — so the agent and V1
can legitimately admit different subsets.

| run | design | result (paired) |
|---|---|---|
| 1 | Full discretion, no lockout | Lost heavily. Defense (V1 losers) **+17.8R over 91 trades**; offense (V1 winners) **−35.2R over 37**, with **−27.8R concentrated in 7 trades** where V1 won >4R. Mechanism: read an ordinary pullback on a deep runner as a reversal. |
| 2 | Harness-enforced **+2R peak lockout** (no tighten/partial/exit above +2R) | Improved but still lost. Two harness bugs found: a `target_r=null` trap (cost ~−7.6R) and a frozen-original-stop trap (~−2R). |
| 3 | Same lockout + **conviction grade shown in the briefing** | agent **+80.58R vs V1 +99.01R** (delta **−18.43R**), n=129. Conviction-weighted funded: V1 $33,371 vs agent $27,457. Shuffle null p=0.998 — random exit timing beat the agent's judgment. |
| 4 | Same lockout + **harness-enforced mirror-close** at V1's own exit (removes the "take it or refuse it" choice) | agent **+92.33R vs V1 +98.54R** (delta **−6.21R**), n=130. Best agent result. Funded: **V1 $33,191 vs agent $31,195** (−$1,996). Still fails kill criteria: era sign flip (2025 +1.06R / 2026 −7.27R), shuffle null p=0.859. |

Run 4 win/loss shape (funded, conviction-weighted): agent WR 31.5% vs V1 29.2%; avg $/win
$955 vs $1,043; avg $/loss −$89 vs −$70; maxDD $1,117 vs $1,080. **The agent wins slightly more
often but its winners run for less — that is the whole gap.**

### Why run 4 still lost — a finding worth carrying forward

The breakeven-at-+1R move is **discretionary in the harness**, not automatic. It only happens if
the model explicitly sends `stop_r: 0`. Measured: of 90 trades that reached +1R, the agent moved
to BE only **19 times (21%)**. Of the 71 skips, ~25 hit target anyway and 38 were rescued by run
4's mirror-close — but **7 cost real money, −5.51R total, which is essentially the entire run-4
deficit (−6.21R)**. In all 7 the agent's exit and V1's exit fall on the *same minute bar*: the
reversal was fast enough that the bar taking V1 out at breakeven swept through the agent's
still-at-−1R stop, so the mirror never got its turn.

A "run 5" that harness-enforces auto-BE at +1R would likely bring the agent to roughly parity
with V1 (≈ −0.7R). **That is not a reason to build it** — parity at the cost of an LLM call per
trade is a worse product than V1 alone. Recorded so nobody re-derives it.

Artifacts: `runs/desk_london/`, `desk_london2/`, `desk_london3/`, `desk_london4/` (journals,
per-trade transcripts, `grade.log`). Specs: `.claude/agents/trade-manager-london-v*.md`.
Drivers/graders: `scripts/capture_desk_run_london*.py`, `scripts/grade_desk_run_london*.py`.

### A process note worth repeating

Run 4's first draft over-generalized the fix — it removed the +2R lockout as well as the
ask-a-choice event. The mandatory single-day validation caught it immediately: the agent
tightened a stop on a trade running to +3.35R peak, got stopped at +2R, and missed a real
+10.37R target. Corrected to lockout-unchanged before the full run. **The one-day validation
before a long chain is not ceremony — it caught a real error.** A 6-agent adversarial review
then found no launch-blocking bug but did correctly force a walk-back of an overstated claim
(see §7).

---

## 6. Things V1 has beaten (do not re-test these)

Every one of these was tested properly and lost to plain V1 (BE at +1R, then untouched):

- **V8** (50% partial + trail) — the old canon. Winners reached full structural targets **5 times
  vs V1's 36**.
- **V0** (set and forget), **V9** (giveback ratchet, full grid).
- **Partial-then-BE at every level** 0.5R/0.75R/1.0R/1.25R/1.5R/2.0R. *An initial headline here
  was RETRACTED* — the bar-walk's "ride remainder uncapped to day close" convention credited 7
  of 130 trades with unrealistic 11–32R marks, 87% of the apparent edge. Retraction is enforced
  by an auto-running audit in `scripts/research/partial_be_sweep.py` so it cannot silently regress.
- Stop-lock-offset grids, max-RR caps, VWAP-band targets, a 24-cell BE-arm/lock/trigger grid,
  a 12-cell guardrail-clean recalibration grid.
- **Four LLM agent architectures** (§5).

**Consistent mechanism behind every failure:** London's edge lives in a small number of very
large winners. Any rule — mechanical or judgment — that reacts to interim price action pays more
than it saves, because ordinary mid-run pullbacks are statistically indistinguishable from real
reversals until very late. The best-measured dividing line is depth reached: eventual win rate
goes 29% (baseline) → 35% (+1R reached) → 47% (+1.5R) → **60% (+2R)**. Early shallow movement
carries nothing: 82% of the book touches +0.5R by minute 3 and those win at 32%, i.e. baseline.

---

## 7. Session-only findings — analysis that exists NOWHERE in the repo

These were computed in-session and are **not committed anywhere**. Recorded here so they are not
lost. All are fit-data diagnostics; none is validated.

### 7.1 The regime fragility, quantified

The strategy has **no volatility scaling**. Stop floor is fixed in points; targets are structural;
P&L is in R. So the whole risk/reward geometry moves with market range, uncontrolled.

Per-trade stop/range quartiles across the 130-trade fit book:

| quartile | n | stop/range | mean R | WR | biggest win |
|---|---|---|---|---|---|
| Q1 widest range | 33 | 1.7–4.8% | **+1.468** | 36% | **+10.37R** |
| Q2 | 32 | 4.8–6.8% | +0.744 | 28% | +7.58R |
| Q3 | 32 | 6.8–9.7% | +0.890 | 41% | +3.56R |
| Q4 tightest | 33 | 9.8–26.7% | **−0.066** | 12% | +3.20R |

**September 2025 is an independent replication of the holdout failure inside fit data:**

| | stop/range | n | mean R | WR |
|---|---|---|---|---|
| 2025-09 (fit) | 12.93% | 8 | **+0.119** | **12%** |
| 2023/24 holdout | 13.06% | 56 | **+0.134** | **18%** |

**BUT — the honest statistical caveat.** Decomposing which variable actually drives R
(rank correlation, 20k permutations):

- stop size alone: rho +0.104, **p = 0.24** (not significant)
- overnight range alone: rho +0.225, **p = 0.010**
- the stop/range ratio: rho −0.192, p = 0.028 — *weaker than range alone*

And holding stop size fixed (9.5–13 pt) then splitting by range gives +0.471R difference at
**p = 0.37 — not significant.** So "narrow range kills the edge" does **not** survive a
controlled test at this sample size.

What *does* survive is structural rather than statistical — the 2×2:

| | n | mean R | biggest win |
|---|---|---|---|
| narrow range, small stop | 39 | +0.903 | +3.56R |
| narrow range, big stop | 27 | +0.218 | +3.47R |
| **wide range, small stop** | 31 | **+1.570** | **+10.37R** |
| wide range, big stop | 33 | +0.266 | +5.44R |

**No trade in a narrow-range session ever produced better than +3.6R.** That is close to
tautological — if the session does not travel far, a structural target cannot be far away, so
large-R outcomes are physically unavailable. The edge is carried by +5R to +10R winners, and
those require room to exist.

### 7.2 Current regime is the OPPOSITE of the failure regime

Measured with the same definition as the pre-seal script (floor-passing candidates, median
actual stop ÷ `on_range`) — reproduces their 179pt / 7.38% baseline exactly:

| | on_range | stop/range | 2R needs |
|---|---|---|---|
| 2023/24 (failed) | 92 pt | **13.06%** | 26.1% of range |
| Fit era (worked) | 179 pt | 7.38% | 14.8% |
| **2026-04 onward** | **234 pt** | **5.89%** | **11.8%** |
| 2026-06 / 2026-07 | 386 / 328 pt | 4.5% / 4.1% | ~8–9% |

**Today's conditions are more favourable than the data the strategy was built on.** But
stop/range swung from 4.11% to 12.27% *within the fit era alone* — a 3x swing in core geometry
with no control on it. Low-vol regimes will return.

### 7.3 Day-of-week (run 4, agent-vs-V1 deltas — do NOT build a rule on this)

| day | n | agent WR | V1 WR | delta $ |
|---|---|---|---|---|
| Monday | 38 | 39.5% | 36.8% | −$262 |
| Tuesday | 28 | 21.4% | 21.4% | −$569 |
| Wednesday | 20 | 25.0% | 20.0% | +$13 |
| **Thursday** | 27 | 18.5% | 18.5% | **−$995** |
| Friday | 17 | 58.8% | 52.9% | −$185 |

Thursday looks terrible, but **3 of the 4 damaging trades are on one calendar day (2026-03-19)**.
Excluding that single date, Thursday's delta shrinks to −$425 across 18 other Thursdays. And
**V1 itself made +$2,606 on Thursdays** — this is an agent-execution artifact, not a property
of the weekday. A "half size on Thursdays" rule would have cost ~$1,300 of real profit.
This is recorded as a worked example of a post-hoc slice that should NOT be acted on.

### 7.4 A methodology bug found and corrected

The "real gain" shuffle test used in `scripts/london_ladder_lab.py` (and inherited by the
conviction-ladder work) has a **systematic bias**: under a null with no real signal, random
fake grades average **+$2,015** real gain, not $0. Corrected significance via z-score against
the empirical null: 2.0x ladders survive at ~4.0–4.2σ; the 1.5x ladder is only ~1.8σ (weak);
**the pre-existing committed Brake ladder in `docs/LONDON-LADDER-LAB.md` / `LONDON-LADDER-945.md`
is only ~1.2σ** — those committed real-gain figures need the same correction applied.

### 7.5 A claim I made and had to walk back

During run-4 design I stated the post-hoc replay "recovers the whole deficit (+99.13R vs
+99.01R)." An adversarial review could not reproduce it: different reasonable classification
methods give **76%–90% recovery**, not ~100%. The direction is robust across every method
(the deficit concentrates in one behavior — holding past V1's own offered exit) but the
magnitude is method-sensitive. The corrected framing is committed in the run-4 docstring.
**Flagging it here because overstated recovery claims are exactly the kind of thing that
propagates into a handoff and becomes "known."**

---

## 8. Where this actually sits, and what's open

### 8.1 Honest status

**The strategy has a large, well-documented fit-data edge that did not validate out-of-sample,
and the single available historical seal is spent.** If asked to rate readiness for live money:
roughly **3–4 out of 10**. Not because the research was sloppy — the process here is genuinely
better than most — but because the one test that separates edge from curve-fit was run and did
not pass.

The failure has a credible, *pre-registered* mechanical explanation (geometry, not signal decay),
and the pre-committed reading of that explanation is **"untested in this regime," never
"validated."** Honour that. It is not a licence to assume the edge is real.

### 8.2 What is NOT worth doing

- Re-running or re-slicing the 128 sealed days. Prohibited, and worthless.
- Building any new strategy element by mining the fit span. ~20 looks spent.
- Resurrecting the LLM agent for live trading (§5).
- Day-of-week rules (§7.3).
- Acting on S1 (sub-9.5 band) — standing ruling, and it would be a goalpost move.

### 8.3 What is legitimately available

1. **Forward data.** Everything after 2026-07-15 is genuinely unseen. Paper or micro-size
   forward testing is now the only clean out-of-sample path. Slow, but real. This is the
   highest-integrity option.
2. **385 unsampled 2023/24 days.** The seal drew 128 from 513 eligible; the other **385 were
   never pulled and never looked at** (verified). That is a real test bed, *weakened* by the
   fact that the era's character is now known — so any prereg using it must state that
   limitation honestly. Requires a data pull (raw depth exists for the 128 sampled days only).
3. **The vol-scaled stop floor hypothesis.** Explicitly parked by the recalibration as "a
   different hypothesis needing its own pre-registration and its own sealed data." §7.1/§7.2
   motivate it. **The trap: do not design it against the known 2023/24 failure and then test it
   on 2023/24 — that is fitting to the answer.** Note also that `LONDON-ERA-DIAGNOSIS.md`
   computed that holding 2025's real tightness in 2026 would require a **16.9 pt** floor.
4. **A regime gate** ("if stop/range > X, size down or stand aside") is a much lighter change
   than re-engineering stops, and sits on top of everything already built. Threshold must NOT
   be tuned on fit data.
5. **A written verdict document for the failed holdout** — promised in the execution commit,
   never delivered. Outstanding.
6. **The three open engine rulings** (§3.5) — required before any promotion regardless.
7. **A/B on the A+ B2 component on holdout** — would require rebuilding the London L0→L3
   pipeline for the holdout span (`--span holdout`; all inputs exist: 128 depth day-files,
   6 CVD footprint parquets, master bars, sealed day list). Pre-committed reading: negative
   is informative, positive proves little. Blocked by the auto-mode classifier without
   explicit approval — which is correct behaviour.

### 8.4 Recommended posture

Trade **plain V1 + rev-3 canon** if trading at all, keep the conviction ladder as an *untested
overlay* rather than a validated edge, size small, and treat forward results as the real
experiment. Measure `stop/range` before each session — it is observable in advance and it is
the variable most likely to explain a sudden performance change.

---

## 9. Conventions and gotchas

- **Two sizing conventions coexist.** Canon/bundle/holdout documents are **flat 1 NQ lot**
  ($20/pt). Funded/MC/dashboard work is **MNQ micros, conviction-weighted** ($200 base × grade).
  Same trades, different units. Run 4 example: 1-lot V1 +$23,315 vs funded V1 +$33,191.
- **`R` from the engine is GROSS** (`r_multiple = pts / risk_pts`, `src/backtest/engine.py:600`).
  Only `dollars` nets commission (`− 2 × commission_side`, `COMMISSION = $5` round turn).
  Mixing them silently shifts results by ~$5/trade.
- **maxDD in the prereg convention is trade-level chronological equity**, not day-level. The
  late-bucket doc uses day-level. They are not comparable.
- **Win rate is a misleading health metric for V1** — it scratches ~40% at breakeven. Use mean R
  and net.
- **`W` uses NaN as signal** (no wall behind), not as missing data.
- **Block structure of the holdout:** effective independent regime observations ≈ **6, not 128**.
  No December or January in the sample. Do not generalise to the full year.
- **DST:** 21 of 128 sealed days (16%) sit in UK/US divergence windows vs ~7% in fit;
  `window_et()` resolves all 128 correctly.
- **Background runs:** use the harness-native background mechanism, not shell `nohup &`
  (the classifier blocks it). Checkpoint-commit `runs/` periodically — containers die.
- **`git checkout <branch> -- .` does NOT switch branches** — it overwrites the working tree
  while leaving you on the original branch. This caused an incident; check `git status` after.

---

## 10. One-paragraph summary if you read nothing else

A London-session NQ strategy (rev-3 canon: 08:00–09:45 London, order-book wall gate, score-0
veto, one position at a time, V1 breakeven-at-+1R management) shows a strong edge on fit data
(130 trades, +$22,665, +0.758 mean R, $1,310 maxDD). Its sealed 2023/24 out-of-sample test was
run once on 2026-07-31 and **failed the primary gate** (56 trades, mean R +0.134, p=0.428 vs
alpha 0.0253; maxDD $2,115 > net $740). The failure has a pre-registered geometric explanation —
that era traded at half the point range against a fixed 9.5pt stop floor, doubling stop/range
and making 2R targets need 26% of session range instead of 13% — and the pre-committed reading
is "untested in this regime," never "validated." Promotion is blocked; the seal is spent; no
second run. Four LLM trade-management agent runs all lost to plain V1, confirming hands-off
management is optimal on this book. A conviction sizing ladder (A+ = B2 + both walls, 2x) looks
excellent on fit but its wall component failed to reproduce out-of-sample and its pattern
component was never tested there. Roughly 20 statistical looks are spent on fit data. The only
clean validation path remaining is forward data, or the 385 never-sampled 2023/24 days under a
fresh pre-registration.
