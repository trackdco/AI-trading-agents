# PRE-FLIGHT — VWAP/BB confluence strategy

**Three of six gates fire: 2 (session overlap), 4 (specifiability), 5 (data feasibility).
Gates 1, 3 and 6 pass, and gate 1 passes cleanly and by a wide margin.** Per the runbook,
diagnosis stops here and no remedies are proposed — a separate decision follows.

| Gate | Verdict | The number that decided it |
|---|---|---|
| 1 SIZING | **PASS** | Median MNQ risk $19–43/contract vs a $2,000 allowance; hand-log realised risk $150–420 |
| 2 SESSION OVERLAP | **FIRES** | 9 of 28 hand-log trades (32%) precede the 09:36 first-signal bar; BB(20)/ATR(20) reach into pre-open on all four entry TFs |
| 3 BREAKEVEN | **PASS** | p₀ = 40.61% at R=1.5 base cost; c/s = 1.53%, a normal cost ratio |
| 4 SPECIFIABILITY | **FIRES** | 18 free parameters, 5 of them with no stated value; 90 discrete tournament configurations against 19 usable calibration trades |
| 5 DATA FEASIBILITY | **FIRES** | February 2026 — the entire calibration month and both parity-gate dates — is absent from the OHLCV archives |
| 6 SAMPLE SUFFICIENCY | **PASS** | ~1,170 available trades vs 519 required at the pessimistic win rate |

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

## GATE 2 — SESSION OVERLAP · **FIRES**

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

## GATE 4 — SPECIFIABILITY · **FIRES**

**(a) Unhandled states.** The α hole is **closed**: §1 specifies an end-of-day flatten
(default 15:55 ET) for any position still open, so the "reaches neither target nor stop"
state that swung α's expectancy by 0.41R has a stated rule here. That is a genuine strength
and worth recording as such.

Two states remain unhandled:

- **Volatility stand-down** — §7 states the criterion is "computable definition TBD" and marks
  it **[OPEN]**. The doc names a filter it does not define.
- **Stop buffer** — §5.4 places the stop "beyond the wick extreme" without a distance. R is
  the denominator of every expectancy figure and the input to the 1.5R floor that decides
  whether a trade is taken at all, so an unstated buffer changes both the magnitude of R and
  the composition of the trade list.

**(b) Free parameter count: 18.**

*Explicitly marked CALIBRATE (9):* cluster proximity tolerance (~10 pts), B_min body/range
(0.6), ATR floor k (1.0), N_data minutes (15), T_cancel, front-run F (2–3 pts), RR floor
(1.5), daily halt thresholds, max trades/day.

*Marked TOURNAMENT (4 axes):* window W1/W2/W3, entry E1/E2/E3, management V0–V4, weekly
profile on/off.

*Not stated anywhere in the doc or spec-1 (5):* VWAP typical-price input (close vs HLC3 vs
HL2 — spec-1 specifies the *variance* formula but not the *price*), volume-profile bin size,
HTF trend/range classification rule (spec-1 defers it: "document the exact rule chosen"), stop
buffer, volatility stand-down.

The tournament axes alone span **3 × 3 × 5 × 2 = 90 discrete configurations**, before any of
the nine continuous CALIBRATE parameters. The calibration target is **19 usable trades** after
gate 2's window restriction. Eighteen free parameters against nineteen calibration
observations is a configuration space larger than the evidence intended to constrain it.

The five unstated parameters are the operative finding for this gate: **two competent
implementers working from these documents would produce different trade lists**, so the
strategy is not currently specifiable, and the 1-point parity gate in spec-1 Step 4 cannot be
adjudicated against an ambiguous VWAP price input.

**(c) Were parameters selected on the data?** **No.** No engine code exists (`src/` is absent;
progress-tracker records zero completed steps), so nothing has been fitted. **N_trials = 0.**
The doc's anti-tuning discipline is explicit (§12.3: axes tested one at a time, not as a grid)
and the out-of-sample reservation is written down (§12.4).

One qualification, recorded without prejudice: the CALIBRATE starting values were derived from
Angus's discretionary trading during February 2026, which is also the declared calibration
month. That is expert prior rather than curve-fitting, and the doc is transparent that
February is in-sample by construction — but the starting values are not independent of the
period they will first be measured against.

## GATE 5 — DATA FEASIBILITY · **FIRES**

**Volume: present and clean.** 1,089,712 bars, **zero** zero-volume bars, mean 419
contracts/bar. VWAP is computable. PASS on that limb.

**Roll corruption at the traded hour: not present.** Only 2 of 794 ET sessions contain a
contract change, and in both the switch falls in the evening:

| session | contracts | max 1-min move | BB(20) 5m window at 09:36 |
|---|---|---|---|
| 2024-12-16 | NQZ4 → NQH5 | 297.00 pts | switch at 19:00 — **clean** |
| 2025-03-17 | NQH5 → NQM5 | 199.50 pts | switch at 20:00 — **clean** |

The ~250-point gaps are real and large, but the longest entry-TF lookback (5m × 20 = 100 min)
opens at 07:56 ET on the same session, well after any evening switch. **No indicator value at
or after the 09:36 first-signal bar is corrupted by a roll.** Recorded as a genuine pass
against a hazard that was reasonable to suspect.

**What fires: February 2026 is absent from the data.**

```
OHLCV coverage: 2023-01-02 -> 2026-01-30   (961 UTC days)
  2026-01 days present: 26
  2026-02 days present:  0     <- the hand-log month
  spec-1 Step 4 parity dates:  2026-02-11 ABSENT,  2026-02-17 ABSENT
  spec-1 Step 8 calibration window 2026-02-02..02-27:  0 of ~19 sessions present
```

The hand log is February 2026. Spec-1 Step 4 gates all downstream work on reproducing
indicator values at two specific February timestamps to within 1 point, and Step 8 gates
Phase 2 on matching the 28 February trades. **Neither step can be executed on the data in the
repo.** Both are declared Angus sign-off gates, so the blockage is not confined to one step —
it sits across the front of the build.

A second, wider consequence: the strategy doc's validation plan (§12.1, §12.4) designates
Jan 2026→present as primary and reserves Mar–Jul 2026 as untouched out-of-sample. The
archives end **2026-01-30**, so there is no post-January-2026 data at all. Neither the primary
window nor the out-of-sample reservation exists as described.

## GATE 6 — SAMPLE SUFFICIENCY · **PASS**

*Least battle-tested of the six — α died before sample size mattered, so this gate is
specified from method rather than demonstrated by the closed branch.*

Frequency 28 trades / 19 sessions = **1.47/session** (below the Vault's 3/day cap, so not
truncated). Available: **794** RTH sessions → **~1,170** trades.

Required n to distinguish the win rate from a 40.61% breakeven at α=0.05 one-sided, 80% power:

| assumed true win rate | required n | sessions | years |
|---|---|---|---|
| 68.4% (in-window point estimate) | 19 | 13 | 0.05 |
| 52.9% (Wilson low, all 28) | 100 | 68 | 0.27 |
| **46.0% (Wilson low, in-window)** | **519** | **352** | **1.40** |

Even the pessimistic case needs 519 trades against ~1,170 available. **PASS**, with two
qualifications: the estimate assumes the trade frequency generalises from a single month, and
the available sample is 2023-01→2026-01 rather than the window the doc's validation plan
describes (see gate 5).

---

## What passed, stated as plainly as what fired

Gate 1 is the one that killed the previous candidate, and this strategy passes it decisively —
by a factor of roughly 40× on median MNQ risk against the allowance. The dependency runs the
right way round: the stop is structural and size is fitted to it, rather than the stop being
forced by a reward multiple. Gate 3's cost ratio is healthy and its pass is not the hollow
kind α produced. Gate 5's roll hazard, reasonable to suspect given unadjusted 250-point gaps,
measured clean at the traded hour. The α exit-rule hole does not exist here.

None of the three firing gates is a finding about the strategy's edge. Gate 2 is a conflict
between two session conventions in two documents. Gate 4 is five unstated parameters. Gate 5
is a missing month of data. All three fire on the specification and the inputs, which is what
PRE-FLIGHT is for and why it runs before anything is built.

**N_trials: 0.** No parameter was fitted, no configuration selected, no backtest run.

---

## Reproducing

```bash
cd research/star-trading/tools
python3 alpha_data.py          # front-month cache from the .zst archives (~19s)
python3 vwapbb_preflight.py    # all six gates (~7s)
```

Hand-log statistics are computed directly from `data/reference/feb2026_hand_log.csv`.
