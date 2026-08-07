# PRE-FLIGHT — VWAP/BB confluence strategy

*Revision 2, 2026-08-07 — gate 4 closed, gate 6 run properly, gate 5 attempted and
**blocked on credentials**. Gate 2 untouched and still OPEN.*

**Gate 4 is now CLOSED. Gate 6 PASSES with a declared resolution floor. Gate 5 could not be
closed — the pull requires Databento credentials that are not present in this environment,
so it remains FIRING and is now the single blocking item.** Gate 2 remains OPEN pending a
human decision. No backtest was run, no parameter was fitted, and **N_trials remains 0**.

| Gate | Verdict | The number that decided it |
|---|---|---|
| 1 SIZING | **PASS** | Median MNQ risk $19–43/contract vs a $2,000 allowance; hand-log realised risk $150–420 |
| 2 SESSION OVERLAP | **OPEN** | 9 of 28 hand-log trades (32%) precede 09:36; W1 vs RTH document conflict awaiting a human decision — untouched in this revision |
| 3 BREAKEVEN | **PASS** | p₀ = 40.61% at R=1.5 base cost; c/s = 1.53%, a normal cost ratio |
| 4 SPECIFIABILITY | **CLOSED** | All 5 unstated parameters frozen: 1 [SPEC], 4 [FIAT], 0 [FIT]. Free count 18 → 13 |
| 5 DATA FEASIBILITY | **FIRES — BLOCKED** | Feb 2026 still absent. Pull not executable: no Databento API key, no `databento` package, and repo policy gates paid pulls |
| 6 SAMPLE SUFFICIENCY | **PASS**, floor p₁ ≈ 0.50 | Workbench 537 sessions resolves p₁ ≥ 0.50 under every correction regime; the 46–50% band is indeterminate |

**Scope of these verdicts.** This is *the VWAP/BB spec as currently written, implemented on
NQ, under the stated RTH 09:31–16:00 / first-signal-09:36 session convention, against the
OHLCV archives presently in the repo.* Nothing here is a statement about whether the
strategy has an edge. Gates 2, 4 and 5 fire on documentation and data availability, not on
performance — no performance claim is tested or contradicted by this stage.

---

## Two corrections to the brief

Recorded because the numbers propagate.

**The hand log has 20 wins, not 22.** The `Result` column reads 20 win / 7 loss / 1 BE across
28 rows. The brief's Wilson interval of [60.5%, 89.8%] corresponds to 22/28; the correct
intervals are:

| basis | rate | Wilson 95% |
|---|---|---|
| wins only, 20/28 | 71.4% | [52.9%, 84.7%] |
| wins + BE, 21/28 | 75.0% | [56.6%, 87.3%] |
| *brief's 22/28* | *78.6%* | *[60.5%, 89.8%]* |

**The RR 0.5 / 66.7%-breakeven line does not apply to this strategy.** That is a cluster-α
figure. The VWAP/BB doc sets an RR **floor of 1.5R** (§6.5) and the hand log's winners
realised a mean of **+4.23R**. This is a positive-RR strategy; its breakeven is ~40%, not
66.7%, and the hand-log win rate clears it comfortably on every reading. Gate 3 is computed
at the correct RR below.

Neither correction changes a gate verdict. Both change how much room the hypothesis has.

---

## GATE 1 — SIZING · **PASS**

The spec's stop is *"beyond the wick extreme of the trigger candle"* (§5.4), so the trigger
candle's range upper-bounds the entry-to-stop distance. Measured over RTH 09:36–16:00 across
794 sessions, all four entry timeframes:

| TF | n bars | p25 | median | p75 | p95 | p99 |
|---|---|---|---|---|---|---|
| 1m | 299,616 | 6.50 | 9.50 | 14.25 | 27.50 | 44.75 |
| 2m | 149,812 | 9.25 | 13.50 | 20.50 | 38.75 | 63.25 |
| 3m | 99,872 | 11.25 | 16.50 | 25.00 | 47.75 | 76.25 |
| 5m | 60,082 | 14.75 | 21.50 | 32.25 | 61.50 | 99.25 |

Dollar risk per contract:

| TF | median NQ | median MNQ | p95 NQ | p95 MNQ |
|---|---|---|---|---|
| 1m | $190 | **$19** | $550 | $55 |
| 5m | $430 | **$43** | $1,230 | $123 |

Against a $2,000 trailing drawdown on MNQ, a median 5m stop is **2.2%** of the allowance and
a p95 stop is **6.2%**. The hand log corroborates: realised stop distances 8.25–65.0 points
(median 32.8), and realised dollar risk held in a narrow $150–420 band because contract count
is varied to hold risk roughly constant.

**Why this passes where α died.** α's stop was *forced* by geometry — a fixed 0.2 reward
multiple against a level-based target mandates a stop five times the target distance,
producing a 424-point median. Here the stop is *structural* — set by the trigger candle — and
position size is the free variable fitted to it. That is the correct dependency direction, and
it is the single structural difference between a model that fits inside a funded account and
one that cannot.

## GATE 2 — SESSION OVERLAP · **OPEN**

> **Status: OPEN pending a human decision on the W1-vs-RTH document conflict.** This section
> is carried unchanged from revision 1 and was deliberately not revisited. The conflict is a
> strategy-authority question (which session the strategy actually trades), not an
> engineering one, and resolving it either way would change what every other gate is
> measuring. Both readings are carried through gate 6 rather than one being assumed.

The brief expected this to pass. It does not, on two independent counts.

**(a) A third of the hand log is untradeable under the stated session convention.** Nine of
28 trades precede the 09:36 first-signal bar:

| time | result | R |
|---|---|---|
| 8:06 | win | +4.79 |
| 8:20 | win | +3.67 |
| 8:35 | win | +4.17 |
| 9:00 | loss | −0.35 |
| 9:18 | win | +4.22 |
| 9:25 | win | **+12.98** |
| 9:31 | win | +3.18 |
| 9:32 | win | +3.69 |
| 9:33 | loss | −1.00 |

Seven of the nine are winners, and the largest single trade in the whole log (+12.98R) is
among them. The testable subset is therefore **19 trades, 13 wins = 68.4%, Wilson95
[46.0%, 84.6%]**, mean **+2.254R** — against +2.792R over all 28.

The root cause is a conflict between two documents: the strategy doc's own entry window W1 is
**08:00–11:00 ET** (§1), and all 28 hand trades fall inside it. The stated session convention
here is **RTH 09:31–16:00 with first signal 09:36**. These are different strategies. The hand
log was generated under the first and is being evaluated under the second.

**(b) Every entry timeframe's lookback reaches into pre-open at the first tradeable bar.**
BB(20) and ATR(20) at 09:36:

| TF | lookback | window opens | |
|---|---|---|---|
| 1m | 20 min | 09:16 ET | pre-open |
| 2m | 40 min | 08:56 ET | pre-open |
| 3m | 60 min | 08:36 ET | pre-open |
| 5m | 100 min | 07:56 ET | pre-open |

And the imported regime is materially quieter than the traded one:

- pre-open 08:00–09:30, median 1-minute range: **5.75 pts** (n=72,224)
- RTH 09:36–16:00, median 1-minute range: **9.50 pts** (n=299,616)
- **RTH is 1.65× more volatile**

So every BB band width and ATR threshold on the first tradeable bars is computed from data
~40% quieter than the bars being traded. Bands will read too tight and the ATR size floor
(§3, k×ATR(20)) too low, in a direction that admits trades the rule intends to exclude. This
is precisely the hazard the gate specifies, and it is present on all four timeframes.

**(c) A related observation, recorded not scored.** NY VWAP anchors 09:30 (§2), so at 09:36 it
carries **six** bars. Its ±1/2/3σ bands are a volume-weighted variance over six observations.
The doc treats those bands as cluster levels (§3) with a ~10-point proximity tolerance; a
six-sample variance estimate is not stable at that resolution.

## GATE 3 — BREAKEVEN AND COST RATIO · **PASS**

At the hand-log median stop of 32.75 points:

| R | frictionless | p₀ lean (0.25) | p₀ base (0.50) | p₀ adverse (1.00) |
|---|---|---|---|---|
| 1.50 (doc floor) | 40.00% | 40.31% | 40.61% | 41.22% |
| 2.00 | 33.33% | 33.59% | 33.84% | 34.35% |
| 3.00 | 25.00% | 25.19% | 25.38% | 25.76% |
| 4.23 (realised) | 19.12% | 19.27% | 19.41% | 19.70% |

**Cost-ratio diagnostic:** c/s = **0.76% / 1.53% / 3.05%**, inflating breakeven by factors of
1.0076 / 1.0153 / 1.0305.

This sits in the normal band — costs bite, visibly and proportionately, which is what a
healthy geometry looks like. It is **not** the α pathology: α sat at **0.12%**, where costs
vanish against the stop, and that easy pass was a symptom of the oversized stop that killed it
at gate 1. Here the cost ratio is 13× larger and gate 1 passed on its own merits, so the pass
is genuine rather than an artefact.

Even the pessimistic in-window Wilson floor of 46.0% clears the 40.61% breakeven, though not
by much — see gate 6.
## GATE 4 — SPECIFIABILITY · **CLOSED**

*Was FIRING in revision 1 on five parameters with no stated value. All five are now frozen.*

**(a) Unhandled states.** Unchanged from revision 1: the α hole is closed by §1's end-of-day
flatten. The two open items — volatility stand-down and stop buffer — are resolved below.

**(b) The five frozen parameters.**

| # | Parameter | Value | Tag | Justification |
|---|---|---|---|---|
| 1 | VWAP typical-price input | **HLC/3** | **[SPEC]** | §2 specifies "standard TradingView VWAP". TradingView's built-in VWAP takes `hlc3` as its source by default, so the doc already fixes this — it was under-read, not unstated |
| 2 | Volume-profile bin size | **1.00 point** (4 ticks) | **[FIAT]** | Resolves the §3 cluster tolerance (~10 pts) at 10:1. Finer bins imply precision the method does not have: spec-1 distributes each 1-minute bar's volume across its own range, so sub-point structure is interpolation, not measurement |
| 3 | HTF classification rule | **15m fractal swings, N=2 either side; HH+HL ⇒ uptrend, LH+LL ⇒ downtrend, else range** | **[FIAT]** | spec-1 already fixes the *method* ("swing HH/HL–LH/LL"), leaving only the swing definition. N=2 is the conventional fractal width, symmetric, and the smallest that rejects single-bar noise |
| 4 | Stop buffer beyond the wick | **1 tick (0.25 pt)** | **[FIAT]** | §5.4 says "beyond the wick extreme" and "never widened". One tick is the minimum increment satisfying "beyond"; any larger buffer is an unstated widening, which the same clause forbids. The doc's own prohibition selects the value |
| 5 | Volatility stand-down | **DISABLED for v1** | **[FIAT]** | §7 marks it OPEN with no definition. Enabling an undefined filter with an invented threshold adds a free parameter with no basis and suppresses trades for unmeasurable reasons. "Off" is the neutral choice — it removes a filter rather than adding one, and admits *more* trades, which is the harder test. Left for a separately pre-registered layer |

**No parameter was set by examining outcomes. Zero [FIT] tags. N_trials remains 0**, and the
holdout was not touched. Parameter 2 was the only candidate that might have required data;
it was resolved from the cluster tolerance and the volume-distribution method instead, so no
data was consulted for any of the five.

**Parity is now adjudicable.** Revision 1 noted that the 1-point parity gate (spec-1 Step 4)
was *undefined* rather than failing, because an ambiguous VWAP price input makes "within
1 point" meaningless. Freezing parameter 1 to HLC/3 removes that ambiguity: parity can now
be computed and can now genuinely pass or fail. It still cannot be *run* — see gate 5.

**(c) Free-parameter count after the freeze.**

| Category | Before | After |
|---|---|---|
| CALIBRATE (explicit, numeric) | 9 | 9 |
| TOURNAMENT (variant axes) | 4 | 4 |
| Unstated / OPEN | 5 | **0** |
| **Total free** | **18** | **13** |

Tournament configuration space is unchanged at **90** cells
(W1/W2/W3 × E1/E2/E3 × V0–V4 × weekly-profile on/off = 3×3×5×2). §12.3 restricts the
immediate programme to **30** (W×E×V) and mandates one axis at a time rather than a grid —
which matters for the correction applied in gate 6.

## GATE 5 — DATA FEASIBILITY · **FIRES — BLOCKED ON CREDENTIALS**

**Volume clean, roll corruption clean at the traded hour** — both unchanged from revision 1
and both genuine passes.

**The February 2026 pull was attempted and could not be executed.** Environment check:

```
.env file:                    absent
DATABENTO_API_KEY in env:     not set
python `databento` package:   not installed
hist.databento.com:           reachable (HTTP 200)
```

The endpoint is reachable but there is no credential to authenticate with, and no client
library. Separately, `context/ai-workflow-rules.md` §22 lists Databento pulls among the
operations that "keep permission prompts" because they spend money — so this is gated by
policy as well as by credentials.

**I did not attempt to work around either constraint.** Coverage therefore stands exactly as
in revision 1:

| Month | Sessions present | Status |
|---|---|---|
| 2023-01 … 2025-12 | full | present |
| 2026-01 | 26 UTC days | present, ends 2026-01-30 |
| **2026-02** | **0** | **absent — the hand-log month** |
| 2026-03 … present | 0 | absent |

Both parity dates (2026-02-11, 2026-02-17) and all ~19 calibration sessions remain missing.
spec-1 Steps 4 and 8 remain unexecutable, and both are Angus sign-off gates.

**This is now the single blocking item in pre-flight.** Gate 4 is closed, gate 6 passes, and
gates 1 and 3 passed in revision 1. Gate 2 needs a decision rather than data. Gate 5 needs
one command run by someone holding the key:

```bash
# requires DATABENTO_API_KEY; spends money; permission-gated per ai-workflow-rules.md
databento download --dataset GLBX.MDP3 --schema ohlcv-1m \
  --symbols NQ.FUT --stype-in parent \
  --start 2026-02-01 --end <today>
```

The verification checklist requested — 1380 bars/session, no intra-session gaps, both parity
dates full, ~19 calibration sessions, front-month outrights identifiable, hyphenated spreads
present and excludable, open-labelling consistent — **cannot be reported because there is
nothing to verify.** It is carried forward verbatim as the acceptance test for whoever runs
the pull. Reporting a coverage table for data that was not obtained would be fabrication.

## GATE 6 — SAMPLE SUFFICIENCY · **PASS**, with a declared resolution floor

**Least battle-tested of the six.** Cluster α died at gate 1, before sample size mattered, so
this gate is specified from method rather than demonstrated by the closed branch. Its
verdict carries correspondingly less weight than gates 1–5.

**(a) Frequency, from the hand log's own span.** Log covers 2026-02-02 → 2026-02-27,
**19 distinct trading sessions** (Feb 16 is a holiday).

| reading | trades | per session |
|---|---|---|
| W1 convention, all 28 | 28 | **1.474** |
| RTH convention, post-09:36 subset | 19 | **1.000** |

**(d)** Gate 2 removed 32% of the log, so under the RTH convention the frequency estimate
must come from the 19-trade subset — and it does. Only **15 of 19** sessions retain at least
one post-09:36 trade. Gate 2 is OPEN, so both readings are carried throughout and the answer
is reported under each.

**Binomial verification** against p₀ = 0.406, one-sided — the brief's corrected figures
reproduce exactly:

| basis | observed | p |
|---|---|---|
| full log | 20/28 | **0.00095** |
| post-gate-2 subset | 13/19 | **0.01332** |

Both clear breakeven. The log is a hypothesis with real room, not an underpowered null.

**Required n.** `n = [z_α√(p₀(1−p₀)) + z_β√(p₁(1−p₁))]² / (p₁−p₀)²`, p₀ = 0.406,
z_β = 0.842 (80% power), z_α from α = 0.05 one-sided with the correction shown.

Correction regimes: §12.3 mandates **one axis at a time, not a grid**, so the honest
multiplier for the immediate programme is the largest single axis (V0–V4 = 5), not the full
90-cell space. All four are shown because the choice changes the verdict at the margin.

| true p₁ | margin | none | ÷5 (axis) | ÷30 (grid) | ÷90 (full) |
|---|---|---|---|---|---|
| 0.68 | +0.274 | 19 | 31 | 45 | 53 |
| 0.60 | +0.194 | 40 | 64 | 91 | 108 |
| 0.55 | +0.144 | 73 | 118 | 167 | 197 |
| 0.529 *(Wilson low, full log)* | +0.123 | 100 | 161 | 229 | 270 |
| 0.50 | +0.094 | 171 | 277 | 393 | 463 |
| 0.46 *(Wilson low, subset)* | +0.054 | 517 | **837** | **1,188** | **1,401** |
| 0.45 | +0.044 | **777** | **1,259** | **1,788** | **2,108** |

**(c) Capacity.** Existing archives, split as instructed and with the holdout untouched:

| split | span | sessions | trades @1.000 | trades @1.474 |
|---|---|---|---|---|
| workbench | 2023-01-02 → 2025-01-31 | **537** | 537 | 792 |
| sealed holdout | 2025-02-01 → 2026-01-30 | 257 | 257 | 379 |

**(b) What the workbench resolves**, at the RTH frequency of 1.000 trades/session (the
conservative reading — the W1 reading yields 792 and resolves strictly more):

- **p₁ ≥ 0.50 — resolvable under every correction regime**, including the full 90-cell space
  (463 ≤ 537). This covers the entire upper portion of both Wilson intervals.
- **p₁ = 0.529** (full-log Wilson floor) — resolvable everywhere; 270 needed at worst.
- **p₁ = 0.46** (post-gate-2 Wilson floor) — resolvable **only uncorrected** (517 ≤ 537).
  At the §12.3 axis multiplier of 5 it needs 837 and does **not** fit.
- **p₁ ≤ 0.45 — not resolvable under any regime.**

**Declared resolution floor: p₁ ≈ 0.50.** Above it the study answers cleanly. Between 0.46
and 0.50 the result will be indeterminate under the correction §12.3's own discipline
implies. Below 0.46 the workbench cannot answer the question at all.

**Why this is a PASS and not a FIRE.** The gate fires if required n exceeds available n at a
*plausible* true win rate. The plausible range is the Wilson interval, and its bulk —
everything from 0.50 to 0.85 — is comfortably resolvable, with the full-log Wilson floor of
0.529 resolvable even under the most punitive correction. Only the bottom four points of the
post-gate-2 interval fall outside reach. That is a known limitation accepted in advance,
which is materially different from discovering it after a null result.

Two qualifications. The frequency estimate rests on a single month, and if the true rate is
lower than the hand log suggests it will also be *rarer* — both estimates would move against
the study together. And the holdout adds 257 sessions if the workbench result warrants
spending it, which is a separate decision and not counted above.

## What passed, stated as plainly as what fired

Gate 1 is the one that killed the previous candidate, and this strategy passes it decisively —
by a factor of roughly 40× on median MNQ risk against the allowance. The dependency runs the
right way round: the stop is structural and size is fitted to it, rather than the stop being
forced by a reward multiple. Gate 3's cost ratio is healthy and its pass is not the hollow
kind α produced. Gate 5's roll hazard, reasonable to suspect given unadjusted 250-point gaps,
measured clean at the traded hour. The α exit-rule hole does not exist here.

None of the firing gates is a finding about the strategy's edge. Gate 2 is a conflict between
two session conventions in two documents. Gate 4 was five unstated parameters. Gate 5 is a
missing month of data. All fire on the specification and the inputs, which is what PRE-FLIGHT
is for and why it runs before anything is built.

**N_trials: 0.** No parameter was fitted, no configuration selected, no backtest run, no
holdout touched.

---

## Revision 2 — state after this pass

| | |
|---|---|
| **Closed** | Gate 4. Five parameters frozen — 1 [SPEC], 4 [FIAT], 0 [FIT]. Free count 18 → 13 |
| **Passed** | Gate 6, with a declared resolution floor at p₁ ≈ 0.50 |
| **Blocking** | Gate 5. Needs one Databento pull, executable only by a key-holder |
| **Awaiting decision** | Gate 2. W1 vs RTH — strategy authority, not engineering |
| **Already passed** | Gates 1 and 3, revision 1 |

Pre-flight cannot complete until gate 5's pull lands and gate 2 is decided. Neither is
research work: one is a purchase, the other is a ruling. Both were left undone deliberately
rather than worked around.

The order matters and is worth stating, because it is the discipline the closed branch
bought. **Gate 5's pull must precede any backtest, and it must precede it for a reason that
has nothing to do with convenience:** acquiring data after seeing a result is how a sample
gets shopped. Right now there is no result — no engine exists, nothing has been fitted,
N_trials is 0 — so the pull can be commissioned on a clean decision. That property is
perishable, and it is lost the moment anything is run.

---

## Reproducing

```bash
cd research/star-trading/tools
python3 alpha_data.py          # front-month cache from the .zst archives (~19s)
python3 vwapbb_preflight.py    # all six gates (~7s)
```

Hand-log statistics are computed directly from `data/reference/feb2026_hand_log.csv`.
