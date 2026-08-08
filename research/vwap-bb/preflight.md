# PRE-FLIGHT — VWAP/BB confluence strategy

*Revision 3, 2026-08-07 — **PRE-FLIGHT COMPLETE**. Gate 2 ruled and closed, gate 5 closed by
scoping to held data, gate 6 recomputed at the true workbench size. No data was purchased.*

> **SUPERSEDED 2026-08-07 by [`signal-count.md`](signal-count.md) rev 2.** Gate 6 PASSES — the full filter stack yields 1.59–2.70 signals/session across all four trigger readings, clearing the 0.486 tripwire, so the frequency input is established. But **gate 4 has REOPENED**: the Vault's candidate-selection rule is not stated anywhere in the spec, it binds on 33–92% of sessions, and it discards 43–86% of candidates that passed every written filter. The statement below applied before those runs.

**All six gates are now closed. Nothing blocks the study design.** No backtest was run, no
parameter was fitted, the holdout was not read, and **N_trials remains 0**.

| Gate | Verdict | The number that decided it |
|---|---|---|
| 1 SIZING | **PASS** | Median MNQ risk $19–43/contract vs a $2,000 allowance; hand-log realised risk $150–420 |
| 2 SESSION OVERLAP | **RESOLVED** | Ruled: RTH 09:36 adopted, W1 superseded. 9 trades out of scope; in-scope evidence 13/19 |
| 3 BREAKEVEN | **PASS**, re-derived 2026-08-08 | p₀ = **43.90%** at the A5 10.00 pt floor, c = 0.975, R = 1.5; c/s = **9.75%**. Clears the 68.4% point estimate by 24.5 pt; clears the 46.0% Wilson lower bound by **2.1 pt at base and 0.0 pt at adverse** |
| 4 SPECIFIABILITY | **REOPENED 2026-08-07** | Signal count rev 2: the **Vault selection rule is unstated** and binds on 33–92% of sessions, discarding 43–86% of qualified candidates. See [`signal-count.md`](signal-count.md) |
| 5 DATA FEASIBILITY | **CLOSED — SCOPE ACCEPTED** | Coverage ends 2026-01-30, confirmed by exhaustive search. Parity relocated; calibration **downgraded** — one irrecoverable loss |
| 6 SAMPLE SUFFICIENCY | **PASS restored** | Signal count rev 2: full filter stack gives 1.59–2.70/session, clearing 0.486 on every reading. Floor p₁ ≈ 0.50 stands |

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
figure. The VWAP/BB doc sets an RR **floor of 1.5R** (§6.5) and the hand log's **in-scope**
winners realised a mean of **+3.678R** (median 3.370, max 5.98, n = 13). This is a positive-RR
strategy; its breakeven is ~40%, not 66.7%. Gate 3 is computed at the correct RR below.

> **Corrected 2026-08-08.** This line previously read **+4.23R**, which is the mean over all
> **20** winners in the FULL 28-trade log and includes the **+12.98R** trade of 2026-02-25
> 09:25 — a trade Amendment A1 places OUT OF SCOPE. The in-scope figure is 3.678.

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

## GATE 2 — SESSION OVERLAP · **RESOLVED**

> ### RULING — 2026-08-07 — RTH 09:36 adopted, gate CLOSED
>
> **Decision.** The entry window is **RTH 09:31–16:00 ET, blackout 09:31–09:35, first
> tradeable signal bar 09:36**. The strategy doc's W1 (08:00–11:00 ET) is **superseded**.
> Settled decisions take precedence over the strategy doc where the two conflict.
>
> **Recorded as** Amendment **A1** in `strategy-definition-v1.0.md`, with date, reason and an
> explicit citation of the settled decision it defers to — a ruling, not a silent edit.
>
> **Consequences applied:**
> - Nine pre-09:36 hand-log trades marked **OUT OF SCOPE**, not deleted. Listed with reasons
>   in `data/reference/hand_log_scope.md`. The raw CSV is unmodified.
> - In-scope evidence is now **19 trades, 13 wins (68.4%), Wilson 95% [46.0%, 84.6%]**,
>   mean **+2.254R**, breakeven **40.6%**, one-sided binomial **p = 0.0133** — clears at the
>   lower bound.
> - Superseded figures (22 wins, [60.5%, 89.8%], 66.7% breakeven) were grepped for repo-wide.
>   They survive only in this document's own corrections section, where they are recorded *as
>   wrong*, and in `research/star-trading/`, where 66.7% is **correct** because those
>   documents concern cluster α at reward:risk 0.5. Nothing needed purging.
>
> **A downstream consequence — ACTIONED 2026-08-08 (Amendment A6):** §8 management variant
> **V3 ("BE at 09:30 open if entered pre-open") is unreachable** — nothing is entered pre-open
> under RTH. It has now been **struck**, reducing the management axis from 5 to 4 and the full
> configuration space from 90 to **72**.
>
> **OPEN ITEM carried to study design — the ruling does NOT fix this.** BB(20) and ATR(20)
> evaluated at 09:36 still reach back into pre-open bars on every entry timeframe (down to
> 07:56 on 5m). Pre-open median 1-minute range is **5.75 pts** against **9.50** in RTH, so
> every band width and ATR threshold on the first tradeable bars is computed from a regime
> **1.65× quieter** than the one being traded — biasing toward admitting trades the rule
> intends to exclude. Adopting RTH changes which bars are *traded*, not which bars are *read*.
>
> The original analysis follows unchanged.

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
| 3.678 (hand log in-scope, **not what the amended spec targets**) | 21.36% | 21.53% | 21.71% | 22.06% |

**Cost-ratio diagnostic:** c/s = **0.76% / 1.53% / 3.05%**, inflating breakeven by factors of
1.0076 / 1.0153 / 1.0305.

---

### RE-DERIVED 2026-08-08 at the A5 floor and the measured cost — verdict CONFIRMED, margin materially reduced

Everything above is computed at **s = 32.75** (hand-log median) and the **declared** cost
ladder. Both inputs are now superseded: **A5** fixes the operative stop at a **10.00 pt floor**
and the cost basis is **measured** at 0.50 / **0.975** / 1.50. This section re-derives rather
than inherits.

**Working**, `p₀ = (s + c) / (s(1 + R))` at s = 10.00, c = 0.975, R = 1.5:

```
frictionless          1 / (1 + 1.5)        = 40.00%
cost inflation        (10.00 + 0.975)/10.00 = 1.0975
p₀ = 0.4000 x 1.0975                        = 43.90%
```

| stop | c = 0.50 | **c = 0.975** | c = 1.50 | c/s at base |
|---|---|---|---|---|
| **10.00 — A5 floor, OPERATIVE** | 42.00% | **43.90%** | 46.00% | **9.75%** |
| 3.12 — old frozen geometry | 46.41% | 52.50% | 59.23% | 31.25% |
| 32.75 — hand log, full *(what gate 3 originally used)* | 40.61% | 41.19% | 41.83% | 2.98% |

**Margin against the evidence:**

| cost level | p₀ | vs the 68.4% point estimate | vs the 46.0% Wilson lower bound |
|---|---|---|---|
| optimistic 0.50 | 42.00% | +26.4 pt | **+4.0 pt** |
| **base 0.975** | **43.90%** | **+24.5 pt** | **+2.1 pt** |
| adverse 1.50 | 46.00% | +22.4 pt | **+0.0 pt** |

**VERDICT: PASS — but say the second half out loud.** On the point estimate the strategy clears
breakeven at every cost level by more than 22 points. **Against the pessimistic Wilson bound
the cushion has collapsed from 4.8 points to 2.1 at base cost and to exactly zero at adverse
cost.** Under the old basis the adverse breakeven was 41.22% against the same 46.0% floor.

Two changes compounded in the same direction: **cost rose** (0.50 → 0.975, measured) and the
**stop fell** (32.75 → 10.00, A5). The cost ratio went from 1.53% to **9.75% — a 6.4× increase**.
Gate 3 is no longer a comfortable pass; it is a pass whose worst case sits exactly on the line.

**One thing pulls the other way, and it is measured, not assumed.** R = 1.5 is the *floor*, not
the typical trade. Planned RR of admitted trades under A4+A5+A7 (509 sessions, known at signal
time, not an outcome) is **median 2.132, mean 2.481**, with only 41% of trades between 1.5R and
2.0R. At the median planned RR:

| R used | c = 0.50 | c = 0.975 | c = 1.50 |
|---|---|---|---|
| 1.500 — the floor (hard) | 42.00% | **43.90%** | 46.00% |
| 2.132 — median planned | 33.53% | **35.04%** | 36.72% |
| 2.481 — mean planned | 30.14% | **31.50%** | 33.01% |

The pre-registration commits to the **conservative 43.90%**. The measured row is recorded so
the size of the cushion is visible, not so it can be quoted as the pass mark.

*Superseded: the pre-A5 figure of 40.61% at s = 32.75, c = 0.50. Recompute source:
`research/prereg/axis_decision.py`.*
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
## STEP 0 — COVERAGE CENSUS · a conflict resolved against the user's belief

Two contradictory claims were on record: the Stage 0 audit said coverage ends January 2026;
the user stated the chart data runs through July 2026. I searched exhaustively rather than
assuming either — the whole repo, every `.csv`/`.zst`/`.parquet`/`.dbn` by extension,
`/home`, `/data`, `/mnt`, `/opt`, `/srv`, and every blob in git history across all branches.

**The evidence supports the Stage 0 audit. Coverage ends 2026-01-30.**

Four archives exist and no others. Exact first and last bar in each:

| Archive | First bar | Last bar | Rows |
|---|---|---|---|
| `…20230101-20250301` | 2023-01-02T23:00Z | 2025-02-28T21:59Z | 1,102,837 |
| `…20250101-20250501` | 2025-01-01T23:00Z | 2025-05-01T23:59Z | 175,786 |
| `…20250502-20251001` | 2025-05-02T00:00Z | 2025-10-01T23:59Z | 214,858 |
| `…20251002-20260131` | 2025-10-02T00:00Z | **2026-01-30T21:59Z** | 162,749 |

Month-by-month the series is **continuous with no missing months** from 2023-01 through
2026-01, then stops. There is no February 2026 and nothing beyond it.

**Said plainly: the holdout is a year shorter than believed.** Not 2025-02 → 2026-07 but
2025-02 → 2026-01 — 257 sessions, not roughly 380.

**Where the July 2026 belief most likely comes from.** The MBP-10 condensed order-book files
*do* run to 2026-07-22 — they are the London and NY heatmap pulls committed over several
sessions. That is a different product with a different end date sitting in the same
directory. **MBP-10 is irrelevant to this strategy and is not a constraint:** VWAP, Bollinger
Bands and volume profile are all computable from bar data alone, which the Stage 0 audit
established and which nothing here changes.

## GATE 5 — DATA FEASIBILITY · **CLOSED — SCOPE ACCEPTED**

Closed by scoping to held data. **No pull was proposed and none is needed** — the standing
decision is that the study runs on what exists.

### Acceptance test, against the coverage that exists

An earlier pass of this test reported 56% session completeness. **That was my error, not a
data defect:** I had grouped bars by ET *calendar date* when a Globex session spans 18:00
(D−1) → 16:59 (D). The tell was in the count distribution — 360 bars (18:00–23:59) and 1020
(00:00–16:59) summing to exactly 1380. Regrouped by session, the picture is healthy.

| # | Item | Result |
|---|---|---|
| 1 | 1380 bars per full Globex session | **688 / 796 = 86.4%** exactly 1380 |
| 2 | Intra-session gaps | 71 sessions (8.9%) short by 1–2 minutes — single no-trade minutes, normal for a real feed |
| 3 | Both parity dates present, full sessions | **NO** — 2026-02-11 and 2026-02-17 do not exist |
| 4 | ~19-session calibration window complete | **NO** — 0 of ~19 |
| 5 | Front-month outrights identifiable; spreads excludable | **YES** — 13 front symbols, none hyphenated; loader filters `-` |
| 6 | Open-labelled convention consistent | **YES** — 795 of 796 sessions begin at index 0 (18:00 ET) |

Shortfalls in item 1 are fully explained: **34 holiday early closes** (July 4th, Labor Day,
MLK, Presidents Day, Thanksgiving) and **3 anomalies** — 2023-04-07 (Good Friday, 913 bars),
2025-01-09 (930, national day of mourning), 2025-11-28 (508, day after Thanksgiving). None is
a data-integrity problem; all are real exchange schedule.

### (a) What is lost

The 2026-02-11 and 2026-02-17 parity dates and the ~19-session February 2026 calibration
window do not exist in the held data.

### (b) Replacements — one clean, one a downgrade

**Parity gate — relocated cleanly.** New targets **2025-01-15 09:48 ET** and
**2025-01-22 09:50 ET**. Both are full 1380-bar Globex sessions inside the workbench, midweek,
not roll sessions, and recent enough for easy TradingView retrieval; the clock times match the
originals so indicators sit at the same session position. Parity tests whether our maths
reproduces a charting platform's, which any charted date answers equally well — so this is
genuinely like-for-like. **Angus must supply fresh reference-chart readings for the two new
timestamps.**

**Calibration gate — DOWNGRADED, not relocated. This is the one irrecoverable loss.**

The original Step 8 matched engine output against Angus's 28 hand trades on
(date, direction, entry time), classifying each MATCHED / MISSED / EXTRA. It is the strongest
validation in the build because it measures detector fidelity *and* day-selection honesty
against a human ground truth.

**It cannot be moved.** The ground truth is welded to February 2026 dates that do not exist in
the data. Relocating the window to January 2025 supplies no reference trades, so
MATCHED/MISSED/EXTRA is undefined there. The replacement — a behavioural sanity report over
**2025-01-06 → 2025-01-31** — answers *"does the engine behave plausibly and at a sane rate?"*,
not *"does it reproduce Angus?"*. Necessary, not sufficient, and **it must not be presented as
though the original gate had been cleared.**

### (c) Documents amended

- `strategy-definition-v1.0.md` — Amendment **A3**
- `spec-1…md` **Step 4** — parity dates replaced, with the reason and the like-for-like
  argument recorded inline
- `spec-1…md` **Step 6 check** — February reference-trade spot-check replaced by a
  rate-and-boundary check, since no reference trades exist in range
- `spec-1…md` **Step 8** — retitled *Behavioural sanity report*, explicitly marked DOWNGRADED,
  with what was lost stated in the step itself
- `spec-1…md` acceptance checklist — the MATCHED/MISSED/EXTRA line marked not achievable

## FINALISED DATA SPLIT

Recomputed from actual coverage, grouped by Globex session (18:00 ET D−1 → 16:59 ET D,
labelled by end date):

| Partition | Span | Sessions | Full-1380 |
|---|---|---|---|
| **Workbench** | 2023-01-03 → 2025-01-31 | **539** | 455 |
| **Sealed holdout** | 2025-02-01 → 2026-01-30 | **257** | 233 |
| Total | | 796 | 688 |

Split 68% / 32%.

**The holdout is sealed mechanically, not by convention.** `config/data_split.yaml` declares
the boundary and carries an unseal token; `src/data_split.py` refuses to return holdout
sessions unless that token is passed, and refuses again if the config records the holdout as
already spent. A careless glob cannot reach it because the archives are never addressed
directly — sessions come from the guard. Verified:

```
workbench  2023-01-03 .. 2025-01-31  539 sessions
holdout    2025-02-01 .. 2026-01-30  257 sessions [SEALED]
guard verified: unauthorised holdout access raises SealedHoldoutError
```

It is one measurement, spent on first use.

## GATE 6 — SAMPLE SUFFICIENCY · **PASS**, floor p₁ ≈ 0.50

**Least battle-tested of the six.** Cluster α died at gate 1, before sample size mattered, so
this gate is specified from method rather than demonstrated by the closed branch. Its verdict
carries correspondingly less weight than gates 1–5.

Recomputed at the true workbench size of **539** sessions (was 537 under the earlier
calendar-day grouping — the correction is immaterial to the verdict).

Required n, `n = [z_α√(p₀(1−p₀)) + z_β√(p₁(1−p₁))]² / (p₁−p₀)²`, p₀ = 0.406, 80% power,
α = 0.05 one-sided with §12.3's one-axis-at-a-time correction (÷5):

| true p₁ | margin | required n (÷5) |
|---|---|---|
| 0.55 | +0.144 | 118 |
| 0.529 *(Wilson low, full log)* | +0.123 | 161 |
| 0.50 | +0.094 | **277** |
| 0.46 *(Wilson low, in-scope)* | +0.054 | 837 |

### Frequency sensitivity — the weakest input, and it is load-bearing

Frequency was estimated from 19 hand-log sessions, which is thin. The gate's verdict depends
on it directly:

| trades/session | workbench trades (539) | resolves p₁ = 0.50? |
|---|---|---|
| 1.00 | 539 | **yes** |
| 0.80 | 431 | **yes** |
| 0.60 | 323 | **yes** |
| 0.50 | 270 | **NO** |
| 0.40 | 216 | **NO** |

**The tipping point is 0.513 trades/session.** Below it the workbench cannot resolve p₁ = 0.50
and the declared floor rises.

### Requirement written into the pre-registration, in advance

> **The first thing the eventual backtest reports is realised trade frequency.** If it lands
> near or below **0.513 trades/session**, the gate-6 resolution floor rises above p₁ = 0.50
> and **gate 6 must be revisited before any verdict is read**.

Recording this now is the whole point. Discovering it after a null result is how an
underpowered study gets narrated as a finding — which is exactly the failure the closed
branch was shut down to avoid.

A second qualification worth stating: if the true win rate is lower than the hand log
suggests, trades will likely also be *rarer*, so both inputs move against the study together.

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

## Revision 3 — PRE-FLIGHT COMPLETE

| | |
|---|---|
| **Closed this pass** | Gate 2 (ruled: RTH 09:36), Gate 5 (scope accepted), Gate 6 (recomputed, passes) |
| **Closed previously** | Gate 4 rev 2; Gates 1 and 3 rev 1 |
| **Blocking** | Nothing |
| **N_trials** | **0** — no parameter fitted, no configuration selected, no backtest run, holdout unread |

**All six gates are closed. The strategy has earned a proper study**, which is a real result
and should be read as one: it cleared a sequence designed to kill candidates cheaply, and the
gate that killed the previous candidate outright it passed by roughly 40×.

Three things travel with it into study design and must not be lost:

1. **The pre-open warm-up bias.** BB(20) and ATR(20) at 09:36 read bars from a regime 1.65×
   quieter than the one traded. Recorded at gate 2, unresolved by the ruling, deliberately not
   fixed here.
2. **The calibration downgrade.** The engine can no longer be checked against Angus's 28
   trades. That validation is gone and no substitute reproduces it.
3. **The frequency tripwire.** Realised trade frequency is the first number the backtest
   reports; below 0.513/session gate 6 reopens before any verdict is read.

Two consequences of the gate-2 ruling needed a strategy-doc edit. **Both were made on
2026-08-08 under Amendment A6:** V3 is struck (management axis 5 → 4, configuration space
90 → 72), and §12.2's February-2026 calibration language is corrected to record that the step
cannot be performed — and that the MBP-10 book snapshots do not rescue it, since they carry no
intra-minute high/low and no volume.

**Also superseded in this document:** gate 3's breakeven rests on the declared cost ladder
0.25 / 0.50 / 1.00. That ladder was **retired on 2026-08-08** — the spread is now measured at
0.75 pt median and the ruled basis is 0.50 / **0.975** / 1.50. Gate 3 still passes (43.90% at
the A5 10.00 pt stop floor) but **should be formally re-derived rather than inherited**. The
frequency tripwire in point 3 above is **0.4862**, not 0.513 — the /5 figure is superseded.
Under the amended rules the count is 2.24–2.83/session. See `research/STATE.md`.

## Reproducing

```bash
cd research/star-trading/tools
python3 alpha_data.py          # front-month cache from the .zst archives (~19s)
python3 vwapbb_preflight.py    # gates 1-3, 5 roll check (~7s)
python3 vwapbb_coverage.py     # step 0 census + gate 5 acceptance + split
python3 vwapbb_gate6.py        # gate 6 required-n tables

cd ../../../src
python3 data_split.py          # prints the split; verifies the holdout guard
```

Hand-log statistics are computed directly from `data/reference/feb2026_hand_log.csv`.
Scope ruling: `data/reference/hand_log_scope.md`. Split: `config/data_split.yaml`.

**Note on `vwapbb_coverage.py`:** its acceptance-test block groups by ET calendar date, which
understates session completeness — the corrected session-grouped figures in gate 5 above
(86.4% at 1380 bars) are the ones to cite.
