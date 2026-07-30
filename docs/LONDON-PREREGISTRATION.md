# London holdout pre-registration

**Status: REVISED 2026-07-30 (rev 2) — §2, §3, §4 and §5 changed. The earlier draft sign-off
(Brake, 2026-07-30) PREDATES this revision and does not cover it; the revision needs
re-confirming.**
**The sealed set may NOT be opened on this signature** — §1 (frozen config), §3 (secondaries)
and §4 (multiplicity) are strategy-authority decisions and still require Angus.
Draft sign-off exists so the fit-side work can run against a fixed configuration rather than a
moving one; it does not promote any recommendation to a ruling.

**What changed in rev 2** (all driven by `docs/LONDON-PREREG-TRADEOFF.md`, a power analysis that
projects the sealed span's size from the fit rate without reading it):
- §2 gains reporting item 10 — the both-W+FAR vs exactly-one split.
- §3 keeps S1 as the single INFERENTIAL secondary, and adds S2 as a DESCRIPTIVE report carrying
  no inference and no decision. Two new candidates (S3/S4) are explicitly declined, with reasons.
- §4 restates multiplicity as **2 gated tests**, and says why the descriptive report does not
  consume family-wise alpha.
- §5 records the finding that most constrains this run: the projected holdout book is ~84 trades.

Written 2026-07-30, before any holdout evidence was examined. The sealed 2023/24 days
(`data/reference/holdout_2023_24_days.csv`, 128 days) have been used ONLY to build the trigger
census and feature matrix; no outcome, check lift, or book figure has been read from them.

Purpose: fix what is being asked, and how many things, before the set is opened. Anything not
listed here is not a question the holdout answers — and adding one afterwards spends the
referendum retroactively.

---

## 1. The frozen configuration

| element | frozen value | why |
|---|---|---|
| **Arm** | `wall` = (W OR FAR) | L3 trial: only two of four checks survived, and they are one signal (r=0.834, agreeing on 94.2% of rows). Scored as one fact, not double-counted. |
| **Threshold** | score >= 1 | wall is binary |
| **Constraint level** | uncapped + $400 day stop | Grid Stage A: the level stops flipping under 14-month leave-one-out once lifetime is fixed. The earlier 4-of-14 instability was an artifact of unset lifetime. |
| **Order lifetime** | session-window-end, no distance cancel | ANGUS ruling: "the order lives while its session window lives" |
| **Risk floor** | `LON_RISK_MIN` = 9.5pt, **no ceiling** | London-native (`scorer.py:63`; 2025-London median), survived its own 24-cell floor x ceiling sweep |
| **Sizing** | flat 1 NQ lot | ANGUS: no sizing until the validated volume is visible |
| **Window** | 08:00-10:00 Europe/London, resolved per day | DST: 03:00-05:00 ET normally, 04:00-06:00 ET on ~20 fit / 21 holdout days |
| **Engine** | E3 limits, V8 management, `v8_be_at_open=False`, `rr_floor` 2.0, 7d lookback | v8_be_at_open off per ANGUS 29-Jul; 7d passed the L2 invariance gate |

**Rejected, and not to be relitigated on holdout evidence:**
- `old4` (W+FAR+ROOM+ASIA) — ROOM sits inside the permutation null in both eras (p=0.698/0.809); ASIA is significantly BACKWARDS in 2026 (lift -0.533, p=0.001).
- Risk floor 5 — better in 2025 (+0.599 vs +0.248) but worse in 2026 (+0.154 vs +0.364). Era crossing rejects it.
- 22pt distance cancel — better adjusted R in both eras but contradicts a standing ruling and lower net. A ruling, not a finding.

## 2. The exact numbers the single holdout run will report

Primary, on the frozen configuration, 128 sealed days, 1 NQ lot:

1. trades taken, trading days with a take
2. net P&L
3. win rate
4. mean R
5. maxDD (chronological equity curve)
6. months green / total
7. worst month
8. trades per week
9. W/FAR lift: mean R of `either` vs `neither`, with n on each side
10. **the `either` cell split: mean R and n for `both W AND FAR` vs `exactly one`** — added in
    rev 2. This is item 9 reported at one more level of detail, not a new measurement, and it
    is DESCRIPTIVE (see §3 S2 and §4).

Fit-span reference for comparison (NOT a target — stated so the holdout is read against a
declared prior rather than a remembered one):

| | fit |
|---|---|
| candidates (risk >= 9.5) | 884 |
| book trades | 187 on 107 days |
| net | +$22,795 |
| WR / mean R | 57% / +0.513 |
| maxDD | $1,720 (2025) / $2,550 (2026) |
| months green | 11/14 |
| W/FAR lift | +0.444 (2025) / +0.637 (2026) |

**Declared forward expectation: mean R ~ +0.48.** Selection-null calibration measured shrinkage
at the wall arm's OWN selection breadth (4 candidate checks) at **-0.014 R** — i.e. none — and
at zero breadth (rule held fixed) at -0.010 R. Exhaustive 29,161-combination search on the same
population shrinks +1.138 R, and the wall arm scores far BELOW what that search achieves
in-sample, which is why it does not read as an artifact. If the holdout comes in near +0.48,
that is the prediction met; materially below is the honest failure.

## 3. Secondary hypotheses — ONE inferential, ONE descriptive

### S1 (INFERENTIAL). Floor-5 / wall redundancy

On the fit span, dropping the risk floor from 9.5 to 5 raised net (+$28,276 on n=282 vs +$18,848
on n=155) because sub-9.5 candidates that PASS the wall check are profitable — L2 measured sub-9.5
bleeding only on the UNSELECTED population. So the floor and the wall check are partially
redundant.

**The question, stated as the decision it drives:** should the risk floor drop from 9.5 to 5?
Operationally — **does the incremental sub-9.5 wall-passing band have mean R > 0 on the sealed
days?**

That framing is deliberate and it is the difference between a usable test and a wasted slot.
Framed instead as "is the floor-5 book better than the floor-9.5 book", the test has **2% power**:
the two books' means are nearly identical (+0.590 vs +0.513) and the sets heavily OVERLAP, since
the floor-5 book *contains* the floor-9.5 book. Framed as a one-sample expectancy test on the
band the change actually admits, the same data gives **91% power**. Same run, same numbers,
different question.

Kept as the inferential secondary because it is both the best-powered question available — better
powered than the primary — and the one that would most change the shipped configuration: the
sub-9.5 band is **300 fit trades against the main book's 187**, so floor-5 roughly triples volume.

### S2 (DESCRIPTIVE, no inference). The both-W+FAR vs exactly-one split

`docs/LONDON-TIER-TEST.md` found that sizing the both-W+FAR cell above the exactly-one cell beats
flat sizing at matched risk (permutation p=0.0085 pooled, 14/14 leave-one-month-out), but per-era
p=0.117/0.021 — real, not independently significant in both eras.

**Reported, with no hypothesis attached and no decision gated on it.** Two reasons, and both must
hold or it should be dropped entirely:

1. **Power.** The cells project to ~60 / ~24 trades. At ~24, the exactly-one cell is below the
   25-per-era floor this project already adopted for calling a result. Gated, it would carry
   **~25% power** — it would usually return a shrug while tightening the alpha on the two
   questions that can be answered.
2. **The sizing freeze.** §1 fixes sizing at flat 1 NQ lot on the ANGUS ruling *"no sizing until
   the validated volume is visible"*. A conviction ladder is a SIZING rule, so it cannot be
   adopted here without contradicting a standing ruling — and it does not need to be. **This
   holdout run at 1 lot IS the validated volume that unlocks the sizing decision afterwards.**

So S2 is recorded now so that the post-holdout sizing decision is made against a number that was
declared in advance rather than one found later. **No sizing change may be taken on it in this
run**, whatever it shows.

### Explicitly NOT asked of the holdout, and why

- `dep_resist>33 AND ASIA==0` (65.6%/65.5% WR, n=61) and `cvd_ASIA>737 AND dep_wall_above_sz>5`
  (65.9%/65.4%, n=67) — both failed only the pooled Wilson floor, which is a SAMPLE-SIZE
  objection. At n~61-67 a 95% lower bound of 60% needs n~150. The sealed set is 128 days and
  cannot supply it. Asking is spending the referendum on a question it cannot answer.
- Concurring-timeframes (H1) — monotone in both eras but the 3+ bucket held n=1 (2025) and n=5
  (2026). At n=1 a win rate is 0% or 100% by construction. Underpowered, not a hypothesis yet.
- **S3, the mild deep-fade filter** (`docs/LONDON-VWAP-FILTER.md`) — the deep counter-VWAP fades
  project to ~33 trades, giving **~9% power**. DEFERRED to forward data.
- **S4, depth-gated deep fades** (`docs/LONDON-FADE-CONVICTION.md`) — projects to ~16 vs ~16
  trades, **~17% power**, and nothing in it cleared Bonferroni on the fit span either. DROPPED
  from this run.
- S3 and S4 are additionally **mutually exclusive, not complementary**: S3 asks whether to drop
  the deep fades, S4 asks which of them to keep. If S3 says drop, S4 has nothing left to gate; if
  S4 finds a gate, S3 is refuted. Asking both would spend two slots on one question and could
  return a contradiction with no declared rule for resolving it.

Both are real fit-side findings with their effect sizes and p-values recorded in their own docs.
They are held for FORWARD data — live, or a future sealed span — where sample size can be
accumulated rather than rationed.

## 4. Multiplicity, declared before opening

**The sealed set is being asked 2 GATED questions: the primary + S1.**

Šidák family-wise correction over 2 tests: per-test alpha = **0.0253**.

**Why S2 does not consume alpha.** Family-wise correction exists to control the rate of false
CLAIMS. S2 carries no hypothesis, no threshold and no decision — it is a number printed in the
report, exactly like items 1-8. Counting it would tighten the bar on the two questions that can
actually be answered, in exchange for nothing. The cost of this treatment is a discipline, and it
is binding: **if any decision is later taken on S2's value, the correction was wrong and the run
is retroactively a 3-test family.** It is written here so that cannot happen quietly.

Declared power at this multiplicity, from `docs/LONDON-PREREG-TRADEOFF.md`:

| test | projected n | fit effect | power at alpha 0.0253 |
|---|---|---|---|
| PRIMARY — book mean R > 0 | ~84 | +0.513 | **78%** |
| S1 — sub-9.5 band mean R > 0 | ~135 | +0.590 | **91%** |
| _S2 — both vs one (descriptive)_ | _~60 / ~24_ | _+0.586_ | _25% if it were gated — which is why it is not_ |

Holding the family at 2 rather than 3 is worth **+4.8pp** on the primary and **+2.7pp** on S1.
That is the entire reason S2 is descriptive rather than gated; it is a real statistical saving,
not a bookkeeping trick.

This is a deliberate reduction from the 5 questions once on the table (primary + 4 secondaries),
and from the 4 that this week's new findings could have pushed it to. Each additional question
dilutes the primary, and the holdout opens once.

## 5. Known residuals, recorded not fixed

- **THE BINDING CONSTRAINT: this holdout is small.** At the fit trade rate (187 trades over 284
  session days) the 128 sealed days project to a book of only **~84 trades**. R's standard
  deviation is 1.569, so the standard error on holdout mean R is about **±0.171** — a fit-sized
  effect of +0.513 sits roughly 3.0 standard errors from zero, giving the primary **78% power**.
  **This run can distinguish "the edge is real" from "the edge is absent". It cannot finely grade
  subsets, and it cannot resolve a mean R of +0.48 from one of +0.30.** Read the result at that
  resolution and no finer. A near-miss on the declared +0.48 is not evidence of decay; a sign
  flip is. (Projection only — nothing was read from the sealed span. If 2023/24 trades at a
  different rate, as a different volatility regime plausibly would, these counts move with it.)

- **`london_matrix.py:125`** — `w.high.idxmax()` / `w.low.idxmin()` feeding `on_extreme_age`.
  DETERMINISTIC (pandas returns the first index label at the max; the index is sorted), so not a
  nondeterminism bug. But it encodes a semantic choice: on a tied extreme it measures the age of
  the EARLIEST touch, not the most recent. Measured: the session high is tied in 6 of 600 windows
  (1.0%), differing by a median of 8 minutes. Left unchanged because altering it is a
  trading-semantics decision, not an engineering one.
- **Jan 2026 is in the fit population** (629 triggers, 20 sessions). Excluded historically only as
  a trigger-cache seam artifact; bars are complete. Included because L0 does not select.
- **The 9.5 floor and the four checks were originally fitted on 2025** by the pre-rebuild canon.
  The 4-check selection null assumes they were specified independently of this data; they were
  not. The sealed set is the only evidence owing nothing to any choice made in the rebuild.
- **The fit span is 14 months (2025-06..2026-07).** All figures above are 1-lot and fit-only.

## 6. Sign-off

| | |
|---|---|
| Written by | engineering (Claude Code), 2026-07-30 |
| Draft sign-off (rev 1) | **Brake, 2026-07-30** — authorised fit-side work against the frozen config |
| Rev 2 | engineering, 2026-07-30 — §2, §3, §4, §5 revised on the power analysis |
| Rev 2 draft sign-off | **PENDING (Brake)** — rev 1's signature predates these changes and does not carry forward |
| Still requires | **Angus** on §1 (frozen config), §3 (secondaries), §4 (multiplicity) |
| Holdout may be opened | only after ANGUS sign-off, once, frozen. Draft sign-off is NOT sufficient |

**Rev 2 changed the questions being asked, so it needs its own sign-off.** §1's frozen
configuration is unchanged — no trading rule moved. What moved is the question set (S2 added as
descriptive, S3/S4 declined), the multiplicity rationale, and the recorded resolution limit.
