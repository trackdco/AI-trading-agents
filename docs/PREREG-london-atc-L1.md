# PRE-REGISTRATION — LDN-ATC-01 L1: first P&L on the pre-London pullback

**APPROVED BY ANGUS 2026-08-06, WITH AMENDMENTS, BEFORE ANY DATA WAS SCORED.** This
file is the commitment; the git timestamp is the declaration
(`docs/BRAKE-HANDOFF-london-program.md` §4). Filed per `docs/VALIDATION-PROCESS.md` §1.
Amendments approved in the same message: the §4.1 target ruling, the §0.1 win-rate table,
the §8 chain-stripped control, the §6.2/§9.1 gate-vs-bar fix, and §10.1/§10.2 reporting.
**Stage 1 only is authorised. Stage 2 remains blocked pending the 2023/24 ruling.**

Trial family: **LDN-ATC-01**. Predecessor: `docs/PREREG-london-atc-census.md` (L0, PASSED
on premise — 27%/28% of sessions vs a declared 15% floor).

---

## 0. Two stages, both declared before either runs

This is the whole point of the document. Stage 1 uses data the family has already been
searched on; it therefore **cannot confirm anything**, and its only power is to kill.

| | STAGE 1 — screen | STAGE 2 — confirmation |
|---|---|---|
| span | fit: 2025-01-01 → 2026-07-15 (396 sessions) | **TBD, pending the 2023/24 ruling** (§7) |
| status | **in-sample. Permanently.** | out-of-sample if and only if the ruling permits |
| can it kill? | **YES** | yes |
| can it confirm? | **NO. Never.** | yes |
| bar | see §9.1 — native criteria + a **+0.110R** external floor | mean R ≥ **+0.48R** (§6.4) |

### 0.1 What those bars mean as WIN RATES — stated before anything runs [AMENDMENT 1]

An R bar is not intuitive; a win rate is. Against a 1R stop, with a target of *k*·R and
flat exits ignored:

> mean R = p·k − (1−p) = p(k+1) − 1  →  **p = (mean R + 1) / (k + 1)**

| target k | STAGE 1 needs (net, +0.110R) | STAGE 2 needs (net, +0.480R) | STAGE 2 gross, 2pt cost on a 20pt stop |
|---:|---:|---:|---:|
| **1.0R** | 55.5% | **74.0%** | **79.0%** |
| 1.5R | 44.4% | 59.2% | 63.2% |
| **2.0R** | 37.0% | **49.3%** | 52.7% |
| 2.5R | 31.7% | 42.3% | 45.2% |
| 3.0R | 27.8% | 37.0% | 39.5% |

Cost in R units is 2pt ÷ stop size: 0.133R at a 15pt stop, 0.100R at 20pt, 0.080R at 25pt.

**Measured win rates in this programme, for scale:** `LDN-CAN-01` book **28%** (best risk
band 40%) · `LDN-OBK-01` **32–38%** against an advertised 89.5% · `ash-unicorn-sb` **43.5%**
· random-walk null at 1:1 ≈ 50%.

**The 74% that a 1R primary would require is far outside anything this programme has ever
measured.** That is what forces the ruling in §4.1.

**Stage 1's threshold is a floor for continuing, not a bar for believing.** At n=108 the
deflation bar would be 4.876/√108 = +0.469R, but quoting that against an in-sample screen
would be a category error: no in-sample number clears a multiple-testing bar by
construction. Stage 1 asks only "is this alive enough to spend a real look on".

---

## 1. Hypothesis

> The taught as-is geometry — enter on the break of a bias-aligned 15m+30m trigger candle
> after a pre-London pullback, stop beyond that candle's opposite extreme — is profitable
> net of realistic friction in the London window.

## 2. Mechanism

Unchanged from L0. Asia trends in a thin book; the hour before the London cash open
retraces it because the participants who pushed it are done and no new size has arrived;
European size arrives at the open on the original side and runs the retracement over.
**The trapped counterparty is whoever read the pre-London pullback as a reversal.**

**Mechanism family:** overnight structure / session-handoff continuation.

## 3. Exact chain — frozen, inherited verbatim from the L0 prereg

No element below may move between Stage 1 and Stage 2. All windows declared in
**Europe/London**, converted per day, DST-correct.

| element | definition |
|---|---|
| Asian session | 00:00–07:00 |
| Bias window | 03:30–07:00, split into halves |
| **Bias** | **bearish** if the second half's high AND low are both below the first half's; **bullish** if both above; otherwise **no bias, no signal** |
| **Pullback** | in 07:00–08:00, price trades against the bias beyond the 07:00 price. No minimum size |
| **LTA** | ≥2 consecutive 15m closes in the pullback direction inside 07:00–08:00 |
| **Trigger (default)** | a 15m close AND its containing 30m close, both in the bias direction, at any 15m boundary in 07:00–09:00. **First occurrence per day** |
| **Hard flat** | 10:00 London (`LDN-WIN-01`: 10:00–11:00 is the worst hour of the session) |

**Observed trigger clock is 07:30 / 08:00 / 08:30 / 09:00 only** — a 15m and its
containing 30m can align solely on 30m boundaries. The opportunity set is half what
"15m boundary" implies. Recorded so nobody re-derives it as a finding.

**Inherited limits, restated so L1 cannot be read as broader than it is:**
- The source demonstrates on gold and forex and **never names NQ**. Applicability is an
  assumption; the verdict says so either way.
- His no-trade rule (*"if it's going to range like this, I'm not interested"*) is dropped
  as not same-time computable. **The tested spec is therefore stricter than the taught
  one.**
- "≥2 consecutive 15m closes" is our mechanisation and is loose: the pullback window holds
  a median 4 bars, and 47% of sessions reaching it clear the bar. The name "low traffic
  area" carries more weight than the column has earned.

## 4. Geometry — as taught, declared now

| | rule |
|---|---|
| **Entry** | a **stop order** at the break of the trigger candle's extreme (below the low for shorts, above the high for longs), placed at the trigger candle's close |
| **Order life** | working from the next 1-minute bar until the **10:00 hard flat**. Unfilled at 10:00 = no trade. **Fill rate is mandatory reporting**, not a footnote |
| **Stop** | beyond the trigger candle's opposite extreme. This defines R |
| **Target (primary)** | **the structural target as taught: the pullback origin / next support** (§4.1) |
| **Target (declared secondary)** | fixed **1R**. **Reported, and may NOT displace the primary on in-sample rank** (§6.0.1 precedent: LDN-PO3-01's F2 arm) |
| **Exit** | target, stop, or 10:00 hard flat, whichever first |

### 4.1 RULING on the target — option (b), and the draft had it backwards [AMENDMENT 1]

**Chosen: (b), a larger pre-registered primary — the as-taught structural target.**

The draft made 1R the primary and "next support" the secondary. Re-reading the source,
that inverts what he teaches. He says **"At least a one to one"** — a *minimum acceptable*,
not a target — and then **"ultimately you can target to the bottom of the range. What
you're going to target is the next support."** The structural level is the taught target.
The draft demoted it and promoted the floor.

So this ruling is not a reach for a reachable bar; it is a correction to the mechanisation,
and it happens to resolve the tension. That ordering matters: **a target chosen because it
makes a bar reachable would be tuning.** The test is whether the change is defensible from
the source text alone, and it is.

**Why not (a).** Keeping 1R primary would set a Stage 2 bar of 74% net / 79% gross — 30
percentage points above the best win rate this programme has measured. A Stage 2 run
against a bar that cannot be cleared tells you nothing about the strategy; it tests the
exit convention. Spending an out-of-sample look on that would waste the one asset the
family has left.

**What the structural target is NOT: a free parameter.** It is the pullback origin — the
07:00 price the pullback traded away from, which the chain already defines. **No R
multiple is imposed, no RR floor is applied**, and the realised payoff distribution is
mandatory reporting (§10). Explicitly rejected: importing the canon's `rr_floor 2.0`. That
is a *canon* standing ruling (it sits in `CANON.md` beside "gold window 09:40–10:30", which
is plainly NY-specific), and importing it here would be the same error §6.2 refuses for
the 9.5pt floor.

**Consequence, declared now:** because k varies per trade, the required win rate is known
only once the realised payoff distribution is measured. §0.1's table gives the requirement
at every k, so the bar is pinned in advance even though the k is not. If the realised mean
k lands near 1.0, the Stage 2 bar is near-unreachable and §13 says so plainly.

## 5. Fill model, cost model, and the two defects they exist to prevent

**Fill model.** The entry is a **stop**, i.e. marketable — this is NOT CAN-01's limit
geometry and the limit fill rule does not apply.
- Entry fills when price trades through the stop level by **≥1 tick (0.25)**, at that
  level plus adverse slippage. Never at a touch.
- The path starts at the **fill minute**, not at the next bar boundary. This is the
  `NYA-LVL-01` defect (VOID NOTICE: the sim skipped a median 12 minutes during which price
  moved a median 21 pts against the trade; a 10pt stop was already hit before the sim
  began on 72.9% of trades). **Asserted in code, not by eye.**
- **Same-bar fill-and-stop:** if entry and stop fall in the same 1-minute bar, the **stop
  is taken first**. This is programme defect D2 (`zxck-10am-keyopen` −5.0R; a +2R win was
  really −1R). Conservative by declaration.
- **Bound-both-orderings** where a single 1-minute bar contains both target and stop: we
  hold no tick sequence, so the outcome is reported as a bound, never guessed, never
  silently dropped.

**Cost model** (`VALIDATION-PROCESS` §2.5, London precedent from `LDN-OBK-01`/`LDN-PO3-01`):
- **Taker by default** — full spread both ways plus commission.
- Two declared cost stacks, **1pt and 2pt**, both reported for every cell.
- **Headline is the strict (2pt) stack.** A result that only survives at 1pt is reported
  as such and does not count.
- Slippage modelled as a vol-conditioned distribution, with the headline also reported at
  a pessimistic percentile.
- Rationale on record: a published MNQ falsification study found zero naive OHLCV signals
  surviving honest friction, and a generous fill model makes the search **evolve toward**
  strategies that harvest imaginary spread.

## 6. The four decisions you asked me to make now

### 6.1 The 27% firing before 08:00 — **IN**

29 of 108 events fire at **07:30**, which is one grid slot, not a scattering.

**Decision: included in the primary population.** Four reasons:
1. The thesis is explicitly that the pre-London chain resolves *into* London. The 07:30
   trigger is the most on-mechanism event in the set, not an artifact.
2. Excluding it now would be **post-hoc selection** — the census is already seen, and
   dropping the cohort after seeing it is exactly the move §3.1 exists to police.
3. The entry may fire pre-open but the **holding period runs into the London session**;
   by outcome window these are London trades.
4. Removing them cuts n from 108 to 79 and would put Stage 2 below the §2.2 hundred-event
   magnitude floor. Kill-by-arithmetic, chosen after the fact, is not a kill.

**Mandatory split (adds no trial):** every result reported 07:30 vs 08:00-and-later, so if
the cohort carries or destroys the result it is visible rather than pooled away.

**Permanent limit, declared now:** London depth begins at 08:00 and the tape has no
pre-08:00 London coverage. **No depth or flow feature can ever gate the 07:30 cohort.**
Any future L3 rung is structurally limited to 73% of this population.

### 6.2 The 9.5pt risk floor — **does NOT gate. Measured, not imported**

`LDN-CAN-01` measured it on the canon-geometry population: below 9.5pt PF 0.77; the
9.5–15pt band PF 1.20 / +0.110R; 15pt+ gives it back — **a band, not a ray**.

**Decision: not applied as a gate in Stage 1 or Stage 2.** It was measured on a different
population with different entry geometry. Importing it would be precisely the error
`docs/HANDOFF-london-rebuild.md` flagged when it called `LON_RISK_MIN = 9.5` "a hypothesis
to re-test on the honest population" — and CAN-01 then re-tested rather than assumed.

**Instead:** the same risk-band table is produced on ATC's own population as a declared
secondary (adds no trial). If the floor replicates independently on a second London
population, that is a genuine structural finding about the session. If it does not, the
CAN-01 result stays population-specific. Either outcome is reportable.

**The inconsistency this section used to contain, now resolved.** The draft rejected
CAN-01's population as a source for a *gate* while borrowing **+0.110R** — a number from
the same table — as Stage 1's continue-bar. That was inconsistent as written. Two things
fix it:

1. **The asymmetry is real, and is now stated rather than assumed.** A *gate* imported
   from a foreign population **changes which trades the strategy takes** — it is a
   parameter, it reshapes the population, and its effect compounds into every downstream
   number. A *bar to clear* changes nothing about the strategy; it is an external
   reference point that the strategy's own, independently-computed economics are measured
   against. Importing the first is adopting someone else's parameter. Importing the second
   is comparing yourself to the only London population this programme has found that pays
   at all. Those are different acts and only the first is the error §6.2 refuses.
2. **Stage 1 no longer rests on the foreign number alone.** §9.1 now leads with two
   ATC-native criteria — positive net sign in both eras, and beating both controls — and
   demotes +0.110R to a third, external floor. If the native criteria fail, the foreign
   number never gets consulted.

### 6.3 Era agreement — sign must agree in **2025 and 2026 separately**

- **Stage 1 requirement:** mean R positive in **both** eras. An era-flip kills, per the
  standing rule ("Era-flips kill", QA-LOG 51/35).
- n per era: 2025 = 69, 2026 = 39. Both clear the §2.2 **≥30 direction floor**; pooled
  108 clears the **≥100 magnitude floor**, so a mean-R number is quotable rather than
  direction-only.
- **The inverse-era pass (discover-2026 / validate-2025) is NOT required at Stage 1**, and
  this is a deliberate reading rather than an omission: the inverse pass exists to catch
  era-fragile *search* results, and Stage 1 runs a frozen as-taught geometry with **zero
  conditioning search**. There is nothing to re-discover in the other direction.
  **It becomes mandatory the moment any conditioning search opens (L2+).**
- Half-year decomposition (2025H1/H2, 2026H1/H2) is mandatory reporting: calendar-year
  pooling has hidden a losing half twice in this programme. Note 2026H2 holds only 11
  sessions and is descriptive only.

### 6.4 Stage 2 sample and effect size — declared before Stage 1 runs

**n_eff is the event count here, and that is not a shortcut.** The default universe is
first-trigger-per-day, so events and triggering-sessions are 1:1 and the overlap
correction of §2.2 does not bite. (The all-triggers universe is 1.55×/1.51× larger but
clusters within sessions, so it would raise n without raising n_eff — which is exactly why
it is not the default.)

Observed trigger rate: **27.3%** of qualifying sessions (69/257 and 39/139).

| Stage 2 span | sessions | expected events | **min mean R = 4.876/√n_eff** |
|---|---:|---:|---:|
| Free 2023/24, with the ±1-day sealed-boundary buffer | 376 | **≈103** | **+0.480R** |
| Free 2023/24, unbuffered | 388 | ≈106 | +0.474R |
| Forward accumulation only (restrictive ruling) | ~5.7 events/month | 103 events | **≈18 months** |

**Declared Stage 2 bar: mean R ≥ +0.48R at the strict 2pt cost stack**, on the buffered
free span, with the sign agreeing in 2023 and 2024 separately (~51 events each, both above
the §2.2 direction floor; pooled ~103 above the magnitude floor).

The coefficient is √(2·ln N)·sd(R) with sd(R) ≈ 1.1 for this exit. **4.876** is N = 18,525
(the 293-row ledger count + the 18,232-comparison confluence scan). On the *current*
ledger (764 rows, N = 18,996) it is **4.883** — a 0.14% move, which at n_eff = 103 shifts
the bar from +0.4804R to +0.4811R. **Adding this family's 8 trials does not move it
either**, because the confluence scan dominates the denominator. Only n_eff moves the bar,
which is why §6.1's decision on the 07:30 cohort is a sample-size decision as much as a
semantic one. Stated at 4.876 per the declared convention; the distinction is immaterial
and is recorded so it cannot later look like a moved goalpost.

## 7. Spans, and what stays sealed

- **Stage 1:** fit span **2025-01-01 → 2026-07-15**, 396 sessions. Bars only.
- **Stage 2:** **BLOCKED pending the ANGUS ruling** on whether the 388 non-sealed 2023/24
  sessions are a legitimate pre-registered test bed or reserve. If restrictive, Stage 2 is
  forward accumulation and the timeline above applies.
- **SEALED AND UNTOUCHED at both stages:** the six sealed months
  (`data/reference/holdout_2023_24_days.csv`, 128 days),
  `data/reference/depth_london_2023_24/`, and the sealed footprint months.
  **Holdout look: NO, at both stages.**
- If Stage 2 runs on the free 2023/24 span, the ±1-day buffer around each sealed block is
  mandatory: prior-day features on the first free session after a sealed block would
  otherwise be computed **from a sealed day**. Lookbacks that can reach into a sealed
  month (e.g. trailing-252-day quantiles) are banned on that span.

## 8. Controls — declared, not optional

1. **Randomised-bias control.** The identical trigger set with the bias direction
   randomised, so "continuation" must beat **any direction** rather than merely beat zero.
   Declared in the candidate proposal before the census ran. *Answers: is there
   directional information in the bias at all?*
2. **CHAIN-STRIPPED control [AMENDMENT 2].** Same bias, same trigger clock
   (07:30/08:00/08:30/09:00), same geometry — **but with the pullback and LTA requirements
   removed**. Every session with a bias takes the first bias-aligned trigger on the grid,
   whether or not a pullback or an LTA occurred. *Answers: does the pullback + LTA chain
   earn its complexity, or is this just "trade the Asian bias at the London open"?*

   This is the control the family most needs and the draft did not have. The randomised-
   bias control can only show that direction beats noise; it cannot distinguish the taught
   chain from its own trivial subset. If ATC does not beat the chain-stripped arm, the
   pullback and the LTA are decoration and the honest description of the candidate changes
   even if the economics survive. **Declared now, while it is free, rather than
   reconstructed later as a defence.** Trials are effectively costless against an
   18,232-comparison denominator (§6.4: 8 trials move the coefficient by <0.02%).

   The funnel already implies this arm is much larger: 87 sessions terminate at `no_bias`,
   so ~309 of 396 carry a bias against 108 that complete the chain. **Expected n ≈ 2.9× the
   primary**, which also means the chain-stripped arm is the better-powered of the two —
   stated up front so a "the control had more data" objection cannot be raised afterwards.
3. **Head-to-head against the trigger-candle-stop prior.** `LDN-OBK-01` died partly
   because a trigger-candle stop at 2R was hit 65% of the time and the target 30%. ATC
   uses the **same stop shape** from inside an LTA. **That difference is the experiment**
   and it is stated as such, not assumed away.

## 9. Kill criteria — pre-committed, ANY of these

### 9.1 Stage 1 — native criteria first, external floor last [AMENDMENT]

To CONTINUE to Stage 2, **all three** must hold. The first two are computed entirely from
ATC's own economics; the third is an external reference and is consulted last.

| # | criterion | source |
|---|---|---|
| **1** | pooled mean R **> 0** at the strict 2pt stack, with the **sign positive in both eras** | **ATC-native** |
| **2** | beats **both** controls — randomised-bias AND chain-stripped — at 2pt | **ATC-native** |
| **3** | pooled mean R **> +0.110R** at 2pt | external reference (§6.2) |

**Stage 1 dies, and no further look is spent, if ANY of:**
- criterion 1 fails — negative pooled, or an era-flip;
- criterion 2 fails — it does not beat the randomised-bias control (no directional
  information) **or** does not beat the chain-stripped control (the chain earns nothing);
- criterion 3 fails — below the +0.110R external floor;
- the result is positive only via ≤3 trades (drop-top-3 fragility, PLAN §9 criterion 1 —
  precedent: rr_floor 1.5 retracted when 80% of the gain was one degenerate fill);
- the entry fill rate is so low that n falls below the §2.2 floors, in which case the
  verdict is **INCONCLUSIVE ON POWER**, which blocks exactly like FAIL.

**A pass on all three means "not yet dead". It never means "confirmed".** Stage 1 is
in-sample and no in-sample result confirms anything.

**Stage 2 dies if:** pooled mean R < +0.48R at 2pt, or the sign disagrees between 2023 and
2024.

## 10. Mandatory reporting — whatever it shows

Event counts before and after the fill-rate restriction · fill rate · mean R and PF per era
and per half-year · the 07:30 vs 08:00-and-later split · the risk-band table on ATC's own
population (§6.2) · both cost stacks with the **strict-2pt headline** · MFE/MAE and
time-segment schema built in from the start, not bolted on (§5.12.5) · **both controls —
randomised-bias AND chain-stripped** · exit-reason distribution (target / stop / 10:00
flat) · every bound-both-orderings case counted, never dropped.

**Also mandatory, because §4.1 made it load-bearing:** the **realised payoff distribution**
(§10.2), and the resulting required win rate read off §0.1 — so the Stage 2 bar's
reachability is a reported number rather than a later argument.

### 10.1 The chain-stripped comparison is reported as TWO tests, never blended [ANGUS]

ATC's 108 sessions sit *inside* the chain-stripped ~309. A straight 108-vs-309 comparison
shares ~35% of its population with itself and **dilutes toward zero by construction** — it
would understate a real effect and could not distinguish "the chain does nothing" from
"the chain does something to a third of the sample". Split it:

| test | comparison | question |
|---|---|---|
| **A — SELECTION** | ATC's 108 chained sessions **vs the ~201 bias sessions that did NOT complete the chain** (disjoint populations) | does the chain pick **better sessions**? |
| **B — ENTRY** | on the sessions where **both** fire, ATC's entry vs chain-stripped's entry (paired, same session) | does the chain pick a **better entry within a session**? |

**Either can pass alone, and they mean different things.** A passes and B fails → the chain
is a session filter and the entry timing is doing nothing. B passes and A fails → the entry
is doing the work and the pullback/LTA gate is discarding sessions for no reason. Both fail
→ the chain is decoration. **Reported separately. Never combined into one number.**

Test B is paired by session, so it is reported with a paired statistic; test A is between
disjoint groups. n for each is reported alongside, since A's ~201 and B's ~108 carry
different power.

### 10.2 The FULL k distribution, not a summary [ANGUS]

With a structural target, k varies per trade and **low-k trades carry the harshest
win-rate requirement** (§0.1: k=1.0 needs 74% for Stage 2; k=2.0 needs 49.3%). A
distribution centred at 2R with a third of its mass under 1R behaves nothing like a tight
one at the same mean, and a mean alone would hide that completely.

Mandatory: full decile table of realised k · **the fraction of trades with k < 1.0R** ·
**the left tail explicitly (p5, p10, p25, and the minimum)** · mean and median · and the
blended required win rate implied by the actual distribution rather than by its centre.

If a material share of trades sits below k = 1.0R, that is reported as a **structural
property of the target rule**, not as a tail to be trimmed away. Trimming it would be
tuning after the fact.

## 11. Trial accounting

**8 trials** into LDN-ATC-01 [AMENDMENT 2 raises this from 6]:

| arm | eras | trials |
|---|---:|---:|
| primary — structural target | 2 | 2 |
| secondary — fixed 1R target | 2 | 2 |
| control — randomised bias | 2 | 2 |
| control — chain-stripped | 2 | 2 |

Splits, ladders, the risk-band table and the MFE/MAE pack add **no** trials (DEF-01
precedent). Controls are ledgered as trials because §3.1 requires every arm tested —
winner, loser or control — to be logged; an unlogged trial rigs our own grade.

London programme running total becomes **42** on the declared count (`programme=='LONDON'`,
currently 34). **Note the open reconciliation:** the same ledger also supports **439**
London-family rows including harness writes. Which figure feeds the DSR denominator is an
outstanding ANGUS ruling and it changes nothing in this document — the §6.4 bar is set by
the 18,232-comparison scan either way.

## 12. Prior — `LDN-CAN-01`'s B row is a **WEAK ANALOGUE ONLY**

CAN-01's per-pattern result for **B (with-trend continuation, ANGUS 22-Jul taxonomy —
`docs/STRATEGY-SETUP-TAXONOMY.md`)** was **PF 1.05 (2025) / 0.57 (2026)** — a hard era-flip.

**It is not ATC's comparator and must not be cited as one.** Three reasons:
1. **Different chain.** CAN-01's B is a close-through off a confluence cluster of BB MA /
   daily-VWAP bands / POC. ATC is an Asian-bias + pullback + LTA + multi-timeframe-close
   chain that references no cluster at all.
2. **Different window.** CAN-01's declared window is 08:00–10:00 London. **27% of ATC's
   triggers fire at 07:30 — outside it entirely.**
3. **Different entry.** CAN-01 enters on a limit at the retest; ATC enters on a stop at
   the break. The fill models are not comparable, and the fill model is where `NYA-LVL-01`
   died.

**The label trap this note exists to prevent:** under the superseded v1.0 taxonomy
(B = reclaim, B2 = continuation) a reader would take **B2's 0.88/1.32** as the continuation
row. That flips the era prior in the opposite direction. Same table, opposite conclusion,
nothing in the numbers to warn you. Cite the legend or cite nothing.

*Owed on the candidate card (`research/candidates/london-asian-trend-continuation.md`,
which lives on `claude/youtube-mcp-strategy-validation-1bf82c`, not on the research
branch): the same weak-analogue note.*

## 13. Known limits, stated up front so the result is not over-read

- **Bars only.** No depth, no flow, at either stage. Those are L3 and would need their own
  prereg — and per §6.1 could only ever address 73% of this population.
- **NQ applicability is an assumption**, not a claim. The source never names NQ.
- **The tested spec is stricter than the taught one** (his no-trade rule is dropped).
- **Stage 1 cannot confirm.** If it passes, the honest statement is "not yet dead", and
  the only thing that changes is that Stage 2 becomes worth its cost.
- **The 2026H2 cell holds 11 sessions.** Descriptive only; no claim rests on it.
- **HOW TO READ A STAGE 2 FAILURE — declared now so it cannot be spun later
  [AMENDMENT 1].** The Stage 2 bar of +0.48R is set by n_eff ≈ 103 against an
  18,996-comparison denominator, **not** by any judgement about this strategy. At the
  realised payoff ratio it may prove near-unreachable:
  - if the realised mean **k ≈ 1.0**, Stage 2 requires a **74% net / 79% gross** win rate.
    Nothing in this programme has exceeded **43.5%**. **A failure at that k is a statement
    about the sample size and the exit convention, NOT evidence that the setup has no
    edge**, and the verdict must say exactly that.
  - if the realised mean **k ≈ 2.0**, Stage 2 requires **49.3% net**, which is within
    reach of measured programme win rates, and a failure there *does* carry information
    about the setup.
  The verdict is required to state which regime it landed in **before** interpreting the
  result. Absence of evidence is not evidence of absence, and at k ≈ 1 the test cannot
  distinguish them.
- **The chain-stripped control is better powered than the strategy it controls** (~309
  bias sessions vs 108 chained). If ATC loses to it, check whether that is a real finding
  or a power artefact before concluding the chain is decoration.

---

**Sign-off**

ANGUS — approved: __________ — date: __________

BRAKE (diagnosis + verdict owner, ANGUS ruling 2026-08-04) — __________
