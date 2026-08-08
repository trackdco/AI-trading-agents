# PRE-REGISTRATION — NQ VWAP/BB confluence strategy, v1

**STATUS: DRAFT. NOT IN FORCE.** This document commits the study when Angus signs the four
OPEN items in §10. Until then nothing here binds and no backtest may be run.

**N_trials at time of writing: 0.** Holdout: **SEALED, never read.**

Every figure below is recomputed from source and traceable to
[`research/STATE.md`](../STATE.md), which is the project's single source of truth. Where this
document and any other disagree, STATE.md wins.

---

## 1. SPEC IDENTITY

The study tests **exactly** the specification identified below. Any edit to that file after
signing invalidates this pre-registration and requires a new one.

| | |
|---|---|
| File | `strategy-definition-v1.0.md` |
| **SHA-256** | `8ead725997b620678426bd41075bbdfd05356cab8325d2a92a95d63ee1bbf10f` |
| git blob | `2235e2dc38f279951ddbf5f95805f071c4fdf21f` |
| Size | 30,059 bytes · 387 lines |
| Frozen at commit | `5bab7c5` (last commit touching this file) |

Verify with `sha256sum strategy-definition-v1.0.md` before the run and again after.

### 1.1 Amendments in force

| # | date | change | reason, one line |
|---|---|---|---|
| **A1** | 2026-08-07 | Entry window W1 08:00–11:00 → **RTH 09:31–16:00**, first signal bar 09:36 | The doc's window conflicted with the project's settled session convention; 9 of 28 hand trades fall out of scope |
| **A2** | 2026-08-07 | Five unstated parameters frozen | Gate 4 was firing on parameters with no stated value; all five now have one |
| **A3** | 2026-08-07 | Parity dates relocated; calibration downgraded | §12.2's February 2026 calibration month does not exist in the bar data |
| **A4** | 2026-08-08 | §6 rule 5: *"nearest valid target"* → **first ladder level clearing the RR floor** | "Valid" was undefined and read as vacuous; the rule discarded targets the menu already held |
| **A5** | 2026-08-08 | §5.4: **minimum stop 10.00 pt** | The literal 1-tick buffer produced a 3.12 pt median stop against the author's 35.00 |
| **A6** | 2026-08-08 | **V3 struck**; §12.2 corrected | V3 cannot fire under RTH; §12.2 still described a calibration that cannot run |
| **A7** | 2026-08-08 | §10.1: **Vault selector = first-come** | The selector was never stated; ranking needs lookahead and thresholding needs a score with resolution |

**None of A1–A7 was selected by comparing outcomes.** A4, A5 and A7 are specification
completions chosen on structural, execution-realism and implementability grounds. A6 is a
correction of internal inconsistency. **This is why N_trials is 0 and not 7.**

### 1.2 Frozen parameters

| # | parameter | value | tag | source |
|---|---|---|---|---|
| 1 | VWAP typical price | HLC/3 | **[SPEC]** | A2 — §2 "standard TradingView VWAP" |
| 2 | Volume-profile bin | 1.00 point | [FIAT] | A2 |
| 3 | HTF classification | 15m fractal N=2; HH+HL up, LH+LL down, else range | [FIAT] | A2 |
| 4 | Stop buffer | 1 tick beyond the wick extreme | [FIAT] | A2 |
| 5 | Volatility stand-down | DISABLED for v1 | [FIAT] | A2 |
| 6 | Minimum stop distance | 10.00 pt (40 ticks) | [FIAT] | A5 |
| 7 | Target selection — "valid" | first ladder level clearing the RR floor | [FIAT] | A4 |
| 8 | Vault selector | first-come, signal-time order | [FIAT] | A7 |
| 9 | Candidate during an open position | discarded, not queued | [FIAT] | A7 |
| 10 | Tie-break level 1 | highest entry TF | **[SPEC]** | §1 MTF arbitration, CONFIRMED — Angus |
| 11 | Tie-break levels 2–5 | stand down on conflict → largest cluster → nearest cluster → lowest cluster low | [FIAT] | A7 — **levels 3–5 never fire in the sample** |

**Free parameter count: 13** — 9 CALIBRATE + 4 TOURNAMENT axes. Was 18 before the A2 freeze.

**Declared placeholders** (the spec states no value; these are stand-ins, not findings):
location band 20% of the trailing 4h range; front-run **F = 2.0 pt** (spec says "start 2–3",
low end chosen as most permissive); entry variant **E1** as default.

---

## 2. DATA

| | range | sessions | use |
|---|---|---|---|
| **Workbench** | 2023-01-03 → 2025-01-31 | **539** (509 processed, 30 skipped) | All development, calibration, freezing, the tournament |
| **Holdout — SEALED** | 2025-02-01 → 2026-01-30 | **257** | One measurement, once, after this document is signed |

Globex sessions, 18:00 ET (D−1) → 16:59 ET (D), labelled by end date. Source: four
`glbx-mdp3-*.ohlcv-1m.csv.zst` archives, 1,656,226 rows, 1,089,712 front-month bars after
spread-symbol exclusion. Bars are open-labelled at source.

**Session accounting, and a discrepancy recorded rather than smoothed over.** Two scripts
apply different exclusion sets, and the pre-registered engine must apply the stricter one:

| | sessions | exclusions applied |
|---|---|---|
| Opportunity / geometry runs | **496** processed | mixed contract 6, holiday/short 21, roll 8, session-after-roll 8 |
| **A7 confirmation count** | **509** processed | mixed contract 8, holiday/short 22 — **roll sessions NOT excluded** |

**The A7 confirmation count in §6 retains 13 roll and session-after-roll sessions that
accounting rule §4.3 commits to skipping.** That is 2.6% of its 509 sessions. The engine will
apply §4.3; the confirmation count did not. The effect is bounded by that 2.6% and cannot
plausibly move 2.849 trades/session below a tripwire of 1.172, so no verdict in this document
turns on it — but the figures in §6 are therefore an **upper bound on frequency**, not the
frequency the engine will produce, and they are labelled as such.

### 2.1 Seal mechanism

`config/data_split.yaml` carries `holdout.sealed: true`, an `unseal_token`, and `spent: false`.
`src/data_split.py` raises `SealedHoldoutError` for any loader that requests holdout sessions
without the token, and refuses again once `spent: true`. Detector scripts carry an independent
`assert_workbench()` that raises `HoldoutBreach` on any session after 2025-01-31.

**The holdout is spent on first use.** Reading it for anything other than the single
pre-registered measurement burns it.

### 2.2 Seal event — permanent record

> On **2026-08-08**, a `*.csv` inventory read 2 rows from each of 287 holdout-dated MBP-10
> files before the date range was known. No measurement was computed on them; no finding rests
> on them. **RULING: recorded, not remediated** — the holdout's outcome data remains unseen.
> Both scripts now refuse holdout-dated sessions. **This entry is permanent and must accompany
> any future holdout result.**

### 2.3 Post-holdout MBP data — ruling

> **2026-02-01 → 2026-07-22 (223 files)** sits outside the declared split. **Usable for
> MICROSTRUCTURE measurement only** — spread, book depth, liquidity. **Never for
> strategy-outcome computation.** If bars for this period are ever acquired it becomes a
> **fresh outcome holdout**, and prior microstructure measurement there is immaterial.

---

## 3. COST BASIS

**0.50 / 0.975 / 1.50 points round-trip** — optimistic / **base** / adverse. NQ = $20/point,
tick 0.25. Entry is a limit at a level and the target is a limit at a level, so the spread is
crossed **once**, on the stop exit. Commission ≈ $4.50 RT = 0.225 pt.

The base is **measured, not assumed**: top-of-book spread median **0.75 pt (3 ticks)** over
**5,781 RTH snapshots across 99 sessions**, plus commission. Not a cancel artefact — adds
median 0.75, modifies 0.75, cancels 1.00.

> **The measurement window is 09:30–10:29 ET, which holds ~9.7% of signals against a
> near-uniform RTH distribution. This makes 0.975 CONSERVATIVE BY CONSTRUCTION — the widest
> measured hour applied to every hour — not representative.** Spread after 10:29 is unmeasured.

**At the A5 10-point floor the full 0.50–1.50 range moves breakeven by only 4.0 points**
(42.00% → 46.00%). The strategy's viability does not hinge on which value is chosen, and the
cost figure should not be argued about further.

**The 0.25 "lean" case is retired.** It is below one tick of spread and was never attainable on
a stop exit. It must not reappear in any table.

---

## 4. ACCOUNTING RULES — fixed in advance

These are committed here so they cannot be chosen after seeing a result.

1. **Ambiguous bars resolve STOP-FIRST.** When a single bar's range contains both the stop and
   the target, the trade is recorded as **stopped**. 1-minute bars carry no intra-bar sequence,
   so the pessimistic assignment is the only one that cannot flatter the result.
2. **Entry fills at the OPEN of the bar after the signal bar closes.** The signal bar must
   close to confirm (§5.2); the earliest actionable price is the next bar's open. No fill at
   the signal bar's close, and no fill at the limit price unless it is also the next open.
   - **Consequence, accepted:** this departs from E1's stated limit-at-the-BB-MA. Modelling
     limit-fill probability is a fill model, not an accounting rule, and building one after
     seeing the data is exactly the freedom this document exists to remove. The next-open
     convention is worse than a filled limit and better than nothing, and it is fixed now.
3. **Contract rolls reset indicator state, and the following session is skipped.** VWAP,
   Bollinger and volume-profile state do not carry across a contract change. 8 roll sessions
   and 8 session-after-roll sessions are excluded.
4. **Spread symbols excluded.** Hyphenated Databento symbols are calendar spreads, not the
   outright contract. Excluded at load.
5. **EOD flatten at 15:55 ET** (§1). Positions open at that point are closed at the 15:55 bar.
6. **Costs applied per trade** at the level under test, deducted from realised R.
7. **No position sizing, no compounding.** Every trade is 1 unit of risk. R is the unit.

---

## 5. WHAT GETS REPORTED, AND IN THIS ORDER

The order is part of the commitment. Frequency is read first because it can invalidate
everything after it.

1. **Realised trade frequency (trades/session).** **FIRST.** If it falls below the tripwire in
   §6, **gate 6 reopens and NO VERDICT MAY BE READ.** Stop and report the frequency alone.
2. **Trade count**, with sessions processed and sessions skipped, each with a reason.
3. **Mean net R per trade at all three cost levels**, each with a **session-block bootstrap
   confidence interval** at the corrected alpha. Blocks are whole sessions, resampled with
   replacement, ≥10,000 iterations — trades within a session are not independent.
4. **Win rate printed BESIDE its cost-adjusted breakeven, never alone.** Any table containing a
   win rate contains the breakeven it must clear, in the adjacent column.
5. **Realised stop and R distributions** — min, p10, p25, median, p75, p90, max; plus the
   fraction sitting exactly at the A5 10.00 pt floor.
6. **Maximum drawdown path and longest losing streak**, in R.
7. **Blocked-candidate and cap-binding rates** — candidates discarded by one-at-a-time, by the
   3/day cap, and the fraction of sessions on which the cap binds.

**Not reported, because it was not pre-registered:** per-slice breakdowns by pattern, time
bucket, HTF flag or news flag. Those are §12.5 diagnostics for locating a leak *after* a
verdict, not evidence for one. Running them before the verdict is reading and re-reading the
same data.

---

## 6. SAMPLE SUFFICIENCY AND THE AXIS DECISION

One-sided one-sample proportion test, 80% power, p₁ = 0.50:

```
n = [ z(1-a) * sqrt(p0(1-p0)) + z(1-b) * sqrt(p1(1-p1)) ]^2 / (p1 - p0)^2
```

**p₀ = 43.90%** — the conservative breakeven, at the A5 10.00 pt floor, c = 0.975, R = 1.5.

**Available trades** = measured rate × 509 processed sessions: **1,450** (reading A, 2.849/sess)
to **1,185** (reading D, 2.328/sess). Per §2, these are an **upper bound** — the confirmation
count did not apply the roll exclusion the engine will apply, which affects 2.6% of sessions.

| divisor | corrected α | required n | tripwire /session | A clears | D clears | resolution floor | blind zone |
|---|---|---|---|---|---|---|---|
| **1** | 0.05000 | 411.3 | 0.763 | YES | YES | 47.15% | 3.25 pt |
| **4** | 0.01250 | 631.7 | 1.172 | YES | YES | 47.93% | 4.03 pt |
| **5** | 0.01000 | 666.9 | 1.237 | YES | YES | 48.04% | 4.14 pt |
| **8** | 0.00625 | 740.9 | 1.375 | YES | YES | 48.26% | 4.36 pt |
| **16** | 0.00313 | 849.4 | 1.576 | YES | YES | 48.57% | 4.67 pt |
| **72** | 0.00069 | 1082.9 | 2.009 | YES | YES | 49.17% | 5.27 pt |

*tripwire = required n ÷ 539 workbench sessions (gate-6 convention). Resolution floor = the
lowest TRUE win rate resolvable at 80% power on reading A's available n. Blind zone =
resolution floor − breakeven.*

| divisor | what it corresponds to |
|---|---|
| 1 | no correction — a single pre-committed configuration |
| **4** | one axis at a time, management axis at 4 after V3 struck — **the current assumption** |
| 5 | one axis at a time, management axis at 5 — superseded by A6 |
| 8 | two axes crossed, e.g. entry (3) × management (4) |
| 16 | entry × management × window, partially crossed |
| 72 | the full tournament grid W × E × V × weekly |

### What the data can and cannot support

**Every axis structure clears on frequency.** Even the full 72-way grid needs 1,083 trades
against 1,185–1,450 available. **The axis decision is not constrained by sample size.**

**What constrains the study is the blind zone, and it is present at every setting.** Breakeven
is 43.90%; the study cannot resolve a true win rate below **47.15%** even with no correction at
all. **A strategy with a true win rate of 45% — genuinely profitable, above breakeven — is
undetectable by this design at any axis structure.** Going from ÷1 to ÷72 widens that band from
3.25 to 5.27 points. The correction costs about two points of resolution; the design costs
three.

**Sensitivity to p₀.** The table above powers against R = 1.5, the hard floor. The measured
planned RR of admitted trades is **median 2.132, mean 2.481** (known at signal time, not an
outcome), at which breakeven falls to **35.04%** and required n collapses to 65 (÷1) – 169
(÷72). The conservative figure is the one committed to; the measured one shows the cushion.

**No recommendation is made here.** Which axis structure to run is a research-design choice and
it is Angus's — see §10.

---

## 7. PASS MARKS — DRAFT, marked OPEN for sign-off

**These are a proposal. Angus signs or replaces them. Do not treat this draft as settled.**

### 7.1 Primary criterion (proposed)

> **Mean net R per trade > 0 at c = 0.975, with the session-block bootstrap lower bound above
> zero at the corrected alpha.**

*Reasoning.* Net expectancy after costs is the quantity that decides whether the strategy is
worth trading; win rate is not, and this project has twice found win rate flattering a geometry
that could not pay for itself. Requiring the *lower bound* above zero, not the point estimate,
is what makes a single holdout read meaningful — a point estimate above zero on 1,200 trades is
compatible with a true expectancy of zero. The bootstrap is session-blocked because trades
within a session share a regime and are not independent; treating them as independent would
narrow the interval and manufacture significance.

*Why c = 0.975 and not the adverse case:* 0.975 is the measured value and is already
conservative by construction (§3). Requiring the pass at the adverse 1.50 would be conservative
twice over.

### 7.2 Abort conditions (proposed)

| # | condition | reasoning |
|---|---|---|
| **1** | **Realised frequency below the §6 tripwire for the chosen divisor** | The study is then underpowered for the effect it was designed to detect. A null is uninformative and a positive is noise. Gate 6 reopens; no verdict may be read |
| **2** | **Any lookahead detected in the engine** | A lookahead result is not a weak result, it is not a result. This includes any use of a session's later bars in a decision made earlier, and any selector that ranks across candidates not yet observed |
| **3** | **The result changes sign between cost levels** | If mean net R is positive at 0.50 and negative at 1.50, the finding is about the cost assumption, not the strategy. Report the sign change; do not report a verdict |

### 7.3 Not a pass mark

Win rate alone, at any level. Maximum drawdown alone. Any per-slice result. Any figure computed
after the primary criterion has been read.

---

## 8. CAVEATS

**These will be the easiest things to soften after a result. They are written plainly for that
reason.**

### 8.1 The strategy enters the holdout never having been checked against the trades it was derived from

The calibration gate — *"February 2026 re-run must approximately reproduce the 28 hand
trades"* — **is gone and cannot return without February 2026 bars.** The bar archives end
2026-01-30. The repo holds MBP-10 book snapshots for all 19 hand-log dates, but at one snapshot
per minute with no intra-minute high/low and no volume: no OHLC, no VWAP, no volume profile.
Three of the detector's four inputs are absent, so the detector cannot be run on the hand-log
month by any route.

**State it directly: this strategy will be measured out-of-sample without ever having been
shown to reproduce the behaviour it was written to formalise.** The behavioural sanity report
substituted in its place (spec-1 Step 8, 2025-01-06 → 2025-01-31) checks that the system behaves
plausibly. It does **not** check it against Angus's trades, and it is not a pass.

### 8.2 The hand log is weaker evidence for this spec than it appears

The frozen spec **trades faster and smaller than the hand log did.**

| | hand log, in-scope | frozen spec, measured |
|---|---|---|
| median stop | **35.00 pt** | **10.00 pt** (A5 floor; 59.9% of trades sit exactly on it) |
| median hold | **~30 min** | **5–7 min** |
| median RR | 3.370 realised | 2.132 planned |
| trades/session | 1.000 | 2.849 |

The A5 floor is still **3.5× tighter** than Angus's median stop, and positions resolve roughly
**five times faster**. A5 supplies a floor; it does not supply the *anchor*, and the anchor
cannot be recovered from the hand log because the log records stop **distances** and never
stop, entry or target **prices**.

**The 68.4% win rate was achieved by a different trade than the one this spec places.** It is
context, not a prior.

### 8.3 Nineteen trades cannot separate a real edge from a good month

The in-scope hand log is **19 trades over 19 sessions in a single month**. Wilson 95% is
**[46.0%, 84.6%]** — a 38-point interval. Against the re-derived breakeven of 43.90% the lower
bound clears by **2.1 points at base cost and 0.0 points at adverse cost**.

One month of one instrument in one regime, with a confidence interval that wide, is consistent
with a strong edge and consistent with an ordinary month. **It cannot distinguish them, and it
is the only direct evidence for this strategy that exists.**

### 8.4 The Vault cap, not the strategy, selects the traded population

Under reading A the cap admits **6.0% of qualified candidates** — 2.849 of 47.430 per session.
It discards **57.7%** outright and binds on **91.0%** of sessions; one-at-a-time discards a
further 15.6%.

**Admission order materially determines which trades are taken.** Any change to trigger
sensitivity changes the traded population through the cap before it changes anything else.
This is a known property of the design (§10.1(5)), recorded so that a result cannot later be
attributed to the strategy when it belongs to the cap.

### 8.5 Smaller, still real

- **Pre-open warm-up bias.** BB(20)/ATR(20) at 09:36 read bars 1.65× quieter than RTH.
  Measured effect on counts: −0.8%. Not fixed, not fixable within A1.
- **E1 is degenerate on 29.6% of triggers** — entry lands on the wrong side of the wick
  extreme and the trigger is skipped. E2/E3 may not share this; the tournament will show it.
- **§6 rule 2's pattern-conditioned defaults are unimplemented**, and the A/B/B2 taxonomy is
  not implemented at all. A4 supplies a working rule without them.
- **The entry-fill convention (§4.2) is not E1.** Next-bar-open is not a limit at the BB MA.
- **Parity has never been verified against a chart** — see §10.

---

## 9. N_TRIALS LEDGER

**Current value: 0.**

| | |
|---|---|
| **What increments it** | Any decision that selects between alternatives **by comparing outcomes** — a parameter chosen because it performed better, a configuration ranked by profitability, a threshold moved after seeing a result, a selector adopted on the basis of measured returns, or **any read of the holdout**. |
| **What does NOT increment it** | Specification completions chosen on structural, execution-realism or implementability grounds (A4, A5, A7); corrections of internal inconsistency (A6); measurement passes that compute distributions without selecting on them. |
| **Who records it** | Whoever makes the decision, **at the moment it is made**, in `research/STATE.md` — never retrospectively. |
| **Non-editable** | Entries are append-only. A recorded increment is never removed, reduced, or reclassified. If a decision is later judged not to have been outcome-driven, that judgement is appended; the original entry stays. |

> **The deflated result depends on this number being true.** The corrected alpha in §6 divides
> by the number of things tried. If the true count is higher than the recorded count, every
> confidence interval in the final report is too narrow and the verdict is overstated by an
> amount nobody can measure after the fact. **An undercount is not a bookkeeping error; it is a
> false result.** This is the one number in the project that cannot be reconstructed from the
> data later — it exists only if it is recorded honestly at the time.

---

## 10. OPEN — BLOCKING, requires Angus

**This document is not in force until all four are resolved. None may be filled by inference.**

### 10.1 Parity chart readings — OPEN

Required: reference chart values for **2025-01-15 09:48 ET** and **2025-01-22 09:50 ET** —
daily VWAP mid and ±1σ/±2σ, NY VWAP mid and ±1σ, BB(20,2) basis, session POC, on each of the
four entry timeframes.

*Why it blocks:* spec-1 Step 4 is the only check that the engine's indicators match the charts
the strategy was designed on. Without it, a systematic indicator error would propagate into the
holdout undetected and be indistinguishable from a strategy result.

### 10.2 Stop anchor — floor or structural rule? — OPEN

A5 sets a **10.00 pt floor** over the wick-based stop. **59.9% of admitted trades sit exactly
at the floor**, so in practice the floor *is* the stop rule for the majority of trades.

The question for Angus: **is that intended?** Two readings, and this document does not choose:

- **(a) Floor, as written.** The wick anchor stands and 10.00 pt catches the degenerate cases.
  Accepts that the modal trade has a fixed 10-point stop unrelated to structure.
- **(b) A different structural anchor.** Prior swing (median 16.29 pt) or an ATR multiple
  (2×ATR ≈ 25.32 pt) sit closer to Angus's 35.00 pt median. **Neither can be confirmed from
  the hand log**, which records distances and never prices.

*Why it blocks:* it changes the stop on the majority of trades, and therefore breakeven, the
blind zone, hold time and the drawdown path. It cannot be decided after the holdout is read.

### 10.3 Tournament axis structure — OPEN

Choose the correction divisor and the axes it covers, informed by §6. **Every option clears on
sample size**; the cost of a wider structure is resolution, not power — the blind zone widens
from 3.25 pt (÷1) to 5.27 pt (÷72).

The current working assumption is **÷4**, one axis at a time per §12.3 with the management axis
at 4 after A6. **That assumption has never been signed.**

*Why it blocks:* the corrected alpha determines the bootstrap interval in the primary criterion.
Choosing it after seeing the result is the specific failure this document exists to prevent.

### 10.4 Pass-mark sign-off — OPEN

§7 is a draft. Angus signs it, amends it, or replaces it. **Specifically requiring a decision:**

- the primary criterion — mean net R > 0 at c = 0.975 with the bootstrap lower bound above zero
- whether abort condition 3 (sign change across cost levels) aborts or merely annotates
- whether reading A, B, C or D is the pre-committed trigger reading, **or whether the trigger
  reading is itself a tournament axis** — which changes the divisor in §10.3

---

## 11. SIGN-OFF

| item | status | signed |
|---|---|---|
| §10.1 parity chart readings | **OPEN** | |
| §10.2 stop anchor ruling | **OPEN** | |
| §10.3 tournament axis structure | **OPEN** | |
| §10.4 pass marks | **OPEN** | |
| Spec hash verified unchanged | | |
| **Pre-registration IN FORCE from** | | |

Once signed: freeze this file, record its own SHA-256 in STATE.md, and run. The holdout is read
**once**. `config/data_split.yaml` is updated to `spent: true` with the date and the reason at
the moment it is read.

---

*Sources: [`research/STATE.md`](../STATE.md) (canonical figures), `preflight.md` (gates 1–6),
`target-stop-reconciliation.md` (A4/A5 diagnosis), `opportunity-set.md`, `signal-count.md`.
Recompute: `research/prereg/axis_decision.py`, `research/star-trading/tools/vwapbb_a7_selector.py`.*
