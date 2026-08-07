# PROTOCOL — conviction tiering and loss autopsy

**Status:** PRE-REGISTERED, UNRUN. Nothing in this document has been executed against
data. `[PROPOSED — Angus to ratify]` throughout unless marked otherwise.
**Companion:** `docs/RESEARCH-confluence-factors-beyond-library.md` (the factor library
this protocol tags against).
**Written to be handed to a research agent verbatim.** An agent running this document
should need no further instruction and should have no room to improvise.

---

## 0. The governing constraint, stated before anything else

> The live book is **28 hand-logged trades**, all from **February 2026** (2 Feb – 27 Feb),
> and **no backtest has been run**.

Therefore:

**Nothing in this document knows which setups win more.** Not one sentence here is
evidence about pattern A versus B2, about trend days versus range days, about any tier
of anything. This document is the **instrument** that will answer those questions later.
An instrument is not a result. If a reader comes away believing they have learned
something about this desk's edge, the document has failed.

Two consequences that bind every section below:

1. **The 28-trade log is used in this document for one purpose only: counting cells to
   establish what is and is not answerable.** Marginal counts per tag are reported,
   because cell size determines power and power determines what the protocol can ask.
   The **win/loss split within each cell is deliberately not reported here.** Reading
   that split before the protocol is registered is precisely the failure mode the
   protocol exists to prevent; a protocol that violated itself on page one would be
   worthless.
2. **Every threshold, cut and boundary in this document is frozen now, in ignorance.**
   Some of them are arbitrary. An arbitrary-but-frozen threshold is worth more than a
   well-chosen one picked after seeing the data, and this document says which is which.

What n=28 in one month actually supports, as a pure width statement: a single aggregate
win rate from 28 trades carries a **95% Wilson interval roughly 32 percentage points
wide**. That is wider than most of the effects anyone would want to act on. One month is
also **one regime** — zero era separation, so §2.1 of `docs/VALIDATION-PROCESS.md` cannot
even be attempted.

---

# 1. Tagging schema — what gets recorded, and when

## 1.1 The three classes, and the one rule that matters

Every field belongs to exactly one class, defined by **when it can be known**:

| Class | Definition | Filled | Revisable |
|---|---|---|---|
| **A — mechanical, pre-entry** | Computable from market data available strictly before the entry timestamp. No judgement. | Automatically, at or before entry | Only by re-running the deterministic producer; never by hand |
| **B — discretionary, pre-entry** | The trader's read at the moment of entry. Judgement, and that is the point. | By hand, **at entry**, before the outcome is known | **Never** |
| **C — outcome** | What the trade did. | After the position is closed | Only to correct a transcription error, logged |

**The rule:** a Class B field written after the outcome is known is not a conviction
record, it is a memory of the outcome. It will correlate with the result no matter what
the trader believed at entry, and that correlation is manufactured, not discovered.

The mechanical guard:

- Class B fields carry `tag_stamped_at` (ISO-8601, seconds). If
  `tag_stamped_at > entry_ts + 120s`, the row is stamped `late_tag = true`.
- **`late_tag = true` rows are excluded from every conviction analysis in §2** and
  reported as a count in every autopsy. They are kept for P&L and for §3 cuts that use
  Class A fields only.
- The stamp is written by the logging tool, not typed. A tool that lets the trader type
  the stamp does not satisfy this section.
- Class B fields are append-only in the store. An edit writes a new row with
  `supersedes = <row_id>`; the original stays. (Same discipline as the trial ledger's
  `status` / `superseded_by` fields.)

If the desk cannot yet stamp Class B at entry, **say so on every verdict** and treat
every conviction result as descriptive-only, in the same way `docs/AUDIT-depth-lookahead-exposure-by-family.md`
treats an era-local quintile: reportable, never quotable as tradeable.

## 1.2 Class A — mechanical, pre-entry (auto-filled)

Derived from the VALID column of `docs/RESEARCH-confluence-factors-beyond-library.md` §0.
Each cites the mechanical freeze that defines it; an agent must not re-derive them.

| field | type | source / freeze |
|---|---|---|
| `entry_ts` | ISO-8601 UTC | broker fill time; the causal anchor for everything else |
| `session_date` | date | trading session, not calendar date |
| `instrument`, `contracts`, `multiplier` | str, int, float | controlled vocabulary — see §1.5 defect 2 |
| `risk_pts`, `risk_usd` | float | fill → initial stop, at entry |
| `gap_class` | enum | RESEARCH §A1 |
| `day_type_preopen` | enum | RESEARCH §A2, computed on data closing at or before entry |
| `ib_state` | enum | RESEARCH §A3 |
| `ib_extension_r` | float | RESEARCH §A3 |
| `overnight_inventory` | enum {long, short, balanced} | RESEARCH §A4, measured against prior pit-session close |
| `calendar_tier` | enum {0,1,2} | RESEARCH §A5, frozen release list |
| `mins_to_next_release` | int | signed; negative after |
| `book_imb_L1..L10` | float | RESEARCH §A6; instantaneous **level**, never a difference |
| `book_press_bid`, `book_press_ask`, `wmid_offset` | float | RESEARCH §A6 |
| `wall_ahead_d`, `wall_ahead_sz` | float | deterministic tie-break (size desc, then nearest price, stable sort) |
| `htf_align_votes` | 0–3 | existing `align_votes` semantics, JOURNAL-SCHEMA-v1 |
| `session_minute` | int | minutes since window open |
| `depth_clock_verified` | bool | **hard requirement.** True only if the load-time second-clock assertion passed for this session's depth file. A row with `false` is excluded from any cut touching `book_*` or `wall_*`. |

**Excluded by construction, with the reason on the record** (RESEARCH §0 and Part B):
`ofi_*` is **BIASED** at snapshot resolution and may never enter a Class A field or any
§3 cut; `cvd_*`, `es_nq_*`, `tick_*`, `add_*`, `vix_*` and intraday `open_interest` are
**NOT CONSTRUCTIBLE** from held data. An agent that finds one of these names in a schema
should stop and report, not synthesise a proxy.

## 1.3 Class B — discretionary, stamped at entry

| field | type | notes |
|---|---|---|
| `conviction_tier` | enum {T1, T2, T3} | **the primary object of §2.** Assigned by the rules in §2.2 — which are empty. Until they are filled, this field is recorded but **carries no risk consequence**. |
| `conviction_free_text` | str | ≤ 200 chars, why this tier. Not analysed statistically; read during autopsy for hypothesis generation only. |
| `pattern` | enum {A, B, B2} | existing vocabulary |
| `entry_tf` | enum {1M, 2M, 3M, 5M} | existing vocabulary |
| `confluence_ids` | list[str] | which named factors the trader believes are present, from a **closed** list. Free text here destroys the field's testability. |
| `planned_target_r` | float | stated before entry, so §3.2 can measure plan-vs-outcome rather than rationalising the exit |
| `tag_stamped_at` | ISO-8601 | written by the tool (§1.1) |

## 1.4 Class C — outcome

| field | type | notes |
|---|---|---|
| `exit_ts`, `exit_price`, `exit_reason` | — | `exit_reason` from a closed list |
| `outcome` | enum {win, loss, scratch} | **convention frozen here:** `scratch` is `|R| < 0.10`. Scratches are excluded from win-rate arms and reported as a count. This is the arbitrary-but-frozen kind. |
| `r_multiple`, `points`, `dollars_net` | float | net of the cost stack, not gross |
| `mae_r`, `mfe_r` | float | Sweeney excursions, in R |
| `t_to_mae_min`, `t_to_mfe_min` | int | **new** — the current log has the magnitudes but not the timing, and §3.2 needs both |
| `post_exit_ext_r` | float | existing field; the "left on the table" measure |
| `hold_min` | int | |

## 1.5 Defects in the current hand log that this schema repairs

Found by inspecting `data/reference/feb2026_hand_log.csv` (28 rows). These are structural
defects, not performance observations.

1. **`In Window` is constant `Yes` across all 28 rows.** A zero-variance field can never
   be tested against anything. Either the population is widened so out-of-window trades
   exist, or the field is dropped from every cut list. It is dropped here. Recording a
   constant and later "testing" it is a way to appear to have more evidence than one has.
2. **`Contracts` is free text with 14 distinct spellings** (`5 MNQ`, `5 mnq`, `5 mnq `,
   `5`, `1 NQ`, `1 NQ mini`, `6 MNQ `, …) for what is a small number of real sizes.
   Replaced by `instrument` (enum) + `contracts` (int) + `multiplier` (float), so
   risk-normalised P&L is computable without string parsing.
3. **`Result` and `Exit Reason` overlap, and `BE` is a third outcome category** that
   silently breaks any binary win-rate arithmetic. §1.4 freezes the convention.
4. **`News Today` is a day-level flag at 19/28 = 68% `Yes`** — near-constant, and it
   answers "was there news in the session" rather than "where was this entry relative to
   the release." Replaced by `calendar_tier` + `mins_to_next_release`.
5. **No entry-time stamp distinct from fill time, and no tag stamp at all.** Without
   `tag_stamped_at`, §1.1's guard cannot run and no conviction claim is defensible.
6. **MAE/MFE magnitudes without timing.** `t_to_mae_min` / `t_to_mfe_min` added.

## 1.6 Cell counts in the existing 28 rows — a power statement, not a result

| tag | levels and counts |
|---|---|
| `pattern` | A **13**, B2 **10**, B **5** |
| `htf` | range **13**, downtrend **11**, uptrend **4** |
| `direction` | long **16**, short **12** |
| `entry_tf` | 5M **11**, 3M **7**, 2M **6**, 1M **4** |
| `news_today` | Yes **19**, No **9** |
| `day_of_week` | fri **8**, wed **7**, tue **6**, thu **4**, mon **3** |
| `in_window` | Yes **28** (degenerate — see §1.5) |

Carry this table into §2.4. The largest cell is 13 and the smallest is 5, and that is the
whole story about what the current log can and cannot answer.

---

# 2. Conviction-tier framework

## 2.1 The tiers and the multipliers, in principle

| tier | intended meaning | risk multiplier **once earned** | multiplier **today** |
|---|---|---|---|
| **T1** | highest conviction | 1.50× base | **1.00×** |
| **T2** | standard | 1.00× base | **1.00×** |
| **T3** | marginal — taken for information, or not taken | 0.50× base | **1.00×** |

The 0.5×–1.5× band is the range that setup-grading practice converges on across the
retail and prop literature; the sources agree on the shape and do not agree on the
numbers, and none of them publish a derivation. Treat the band as a convention this desk
has adopted, not a finding. It is recorded in §6 as provisional.

**Every tier sits at 1.00× today and stays there until §2.2 is filled and §4 has passed
a proposal.** A tier system with multipliers already switched on is not an experiment; it
is a live change that has skipped the gate.

## 2.2 Tier assignment rules — EMPTY BY DESIGN

> **This section is intentionally blank. It is not an oversight and it is not a
> to-do for the agent running this protocol.**

| tier | assignment rule | registered on | evidence |
|---|---|---|---|
| T1 | *(empty — not yet earned)* | — | — |
| T2 | *(empty — not yet earned)* | — | — |
| T3 | *(empty — not yet earned)* | — | — |

**Why it is empty, and the deadlock it encodes.**

The tier rules and the tier test cannot come from the same data. If T1 is defined as
"the conditions where the log shows the best outcomes," then testing whether T1 wins more
is testing the data against itself, and it will pass. That is the same defect as
LDN-INV-01's era-local quintile and it is not fixed by any amount of robustness testing —
`docs/RESEARCH-confluence-factors-beyond-library.md` cross-cutting failure mode 1:
**circularity is robust**, it survives drop-top-3, every trim depth and every
winsorisation.

So the rules must come from **outside the live log**, and there are exactly three legal
sources:

1. **A backtest** on the fit span, pre-registered and graded through the normal ladder —
   **not yet run**;
2. **An a-priori mechanism** taken from `docs/RESEARCH-confluence-factors-beyond-library.md`,
   declared in full before any live trade is tagged with it, with the mechanism written
   down and not just the threshold;
3. **A prior era of live trades**, sealed and never re-opened, used to write rules that a
   later era tests.

Anything else is the trader reading their own recent results and calling the result a
rule. **An agent asked to "just fill in reasonable tier rules from the log" must refuse
and cite this paragraph.**

## 2.3 Minimum sample size before a tier comparison is actionable

Two-proportion test, two-sided, 80% power, equal arms. `n` is **per arm**.

| true difference | α = .05 (primary) | α = .05/7 (secondary, §3.4) | α = .05/20 |
|---|---|---|---|
| 30 pp (35% → 65%) | **43** | 70 | 82 |
| 20 pp (30% → 50%) | **93** | 152 | 178 |
| 10 pp (35% → 45%) | **376** | 613 | 716 |

Read the other way — the smallest **true** gap detectable at 80% power, base rate 35%:

| n per arm | 5 | 10 | **13** | 20 | 30 | **43** | 60 | 100 | 200 |
|---|---|---|---|---|---|---|---|---|---|
| smallest detectable gap | 65.0 pp | 56.9 pp | **51.3 pp** | 42.7 pp | 35.4 pp | **29.8 pp** | 25.3 pp | 19.6 pp | 13.8 pp |

(n = 13 is the largest cell in the current log; n = 43 is the bar set below.)

**The bar, frozen:** a tier comparison is **actionable** only at **n ≥ 43 per arm in the
two arms being compared**, both arms drawn from at least two eras, with `late_tag = false`
on every row. Below that the comparison is reported as INCONCLUSIVE, which blocks exactly
like FAIL (`docs/VALIDATION-PROCESS.md` §5).

## 2.4 Worked example — at what N does an observed +30% win-rate difference stop being plausible noise?

The question has **two different answers**, and conflating them is the most common way a
small trading sample gets over-read. Both are given.

### Reading 1 — the design question: how much data do I need to *find* a 30 pp gap?

If T1 truly wins 65% and T3 truly wins 35%, how many trades per tier before an 80%-powered
test would detect it?

> **43 per arm at α = .05.** **70 per arm** at the Bonferroni-corrected α used for the
> secondary cuts in §3.4.

### Reading 2 — the inference question: I *observed* +30 pp. When is that not luck?

Take an observed 65% vs 35% split at equal n and ask when the two-proportion test clears
significance:

| n per arm | observed | z | p | p < .05 | p < .05/7 |
|---|---|---|---|---|---|
| 14 | 9/14 vs 5/14 | 1.51 | 0.131 | no | no |
| 20 | 13/20 vs 7/20 | 1.90 | 0.058 | no | no |
| **23** | 15/23 vs 8/23 | 2.06 | **0.039** | **yes** | no |
| 29 | 19/29 vs 10/29 | 2.36 | 0.018 | yes | no |
| **43** | 28/43 vs 15/43 | 2.80 | **0.005** | yes | **yes** |
| 47 | 31/47 vs 16/47 | 3.09 | 0.002 | yes | yes |

So an observed 30 pp gap first clears p < .05 at about **n = 23 per arm**, and clears the
corrected threshold at about **n = 43**.

### The trap between the two readings, quantified

n = 23 is *not* the answer, and this is the part that matters most.

A significant result from an underpowered design is not weak evidence of a real effect —
it is **evidence that the observed effect is inflated**. Gelman & Carlin (2014) call this
Type M (magnitude) and Type S (sign) error. Simulated directly on this desk's actual cell
sizes (150,000 draws per row, α = .05):

| true gap | n per arm | P(significant) | mean observed gap **given** significant | exaggeration | P(wrong sign given significant) |
|---|---|---|---|---|---|
| 10 pp | **13** | 10.9% | **43.4 pp** | **4.3×** | **9.3%** |
| 10 pp | 23 | 10.8% | 34.8 pp | 3.5× | 3.6% |
| 10 pp | 43 | 16.2% | 26.3 pp | 2.6× | 1.4% |
| 10 pp | 100 | 30.6% | 17.9 pp | 1.8× | 0.1% |
| 20 pp | 13 | 22.7% | 45.4 pp | 2.3× | 1.0% |
| 20 pp | 43 | 47.6% | 29.0 pp | 1.5× | 0.0% |
| 20 pp | 100 | 82.8% | 22.1 pp | 1.1× | 0.0% |

Read the first row against §1.6. **13 is the size of the largest pattern cell in the
current log.** At that size, if the true gap is a modest 10 pp, the differences that reach
significance average **43 pp** — and roughly **one in eleven points the wrong way
entirely**. An observed +30 pp at n = 13 is *more consistent with* a small true gap that
got lucky than with a large one.

And the power to see anything at all is negligible at current cell sizes:

| comparison | n vs n | power at a true 30 pp gap | at 20 pp |
|---|---|---|---|
| A vs B2 | 13 vs 10 | **28.9%** | 15.3% |
| A vs B | 13 vs 5 | **20.1%** | 11.5% |
| B2 vs B | 10 vs 5 | **18.6%** | 10.9% |

**The answer to the question as asked:** an observed +30 pp difference stops being
plausible noise at roughly **43 per arm** — not at 23, because at 23 the design is still
exaggerating by ~3.5× whatever it does find, and not at 13 under any circumstances.

## 2.5 What that means in months, at this desk's observed cadence

28 trades in one month, split A 46.4% / B2 35.7% / B 17.9%. If both the rate and the mix
hold — a large "if", stated as an assumption not a forecast:

| arm | share | to n = 43 | to n = 70 (corrected) |
|---|---|---|---|
| A | 46.4% | ~3.3 months (93 trades) | ~5.4 months (151) |
| B2 | 35.7% | ~4.3 months (121) | ~7.0 months (196) |
| **B** | 17.9% | **~8.6 months (241)** | **~14.0 months (392)** |

The binding constraint is the **rarest** arm. A three-tier conviction system split evenly
reaches 43 per tier in roughly **4.6 months**; an unevenly split one takes as long as its
thinnest tier. This is the number to plan around, and it is the reason §4 has no fast path.

## 2.6 Why the default direction is down, not up

Fractional-Kelly work (MacLean, Thorp & Ziemba) establishes an asymmetry that applies
directly here: the penalty for **over**betting is far worse than the cost of underbetting,
and small errors in the edge estimate produce large errors in the bet size — a modest
overestimate of the edge can push the growth rate negative even when the edge is real. A
win rate estimated from ~100 trades carries a standard error around ±5 pp on its own,
before any tier-selection bias is added.

Combine that with §2.4: at small n, the tiers that *look* best are the ones whose
estimates are most inflated. **Raising risk on a tier is therefore the action with the
worst error asymmetry in the entire system**, and §4 gives it the heavier burden of proof
accordingly. Cutting risk on a tier that turns out to be fine costs some growth. Raising
risk on a tier that was a 4.3× exaggeration is how accounts end.

---

# 3. Loss-autopsy procedure

Runs under `docs/VALIDATION-PROCESS.md` §3.2, which already makes the loser autopsy
mandatory and already fixes two of its rules: **the cut cohort must be bad in EVERY era,
not just the discovery era**, and **every cut tried is a ledgered arm**. This section adds
the pre-commitment.

## 3.1 The pre-committed cuts — frozen, exactly eight

The list is closed. Thresholds are frozen here, before data. Where a threshold is
arbitrary it says so; an arbitrary frozen threshold is honest, an optimised one is not.

| # | cut | binary split, frozen | class | rank |
|---|---|---|---|---|
| **P** | **conviction tier** | T1 vs T3 | B | **PRIMARY** |
| S1 | pattern class | A vs (B ∪ B2) | B | secondary |
| S2 | HTF alignment | `align_votes ≥ 2` vs `< 2` | A | secondary |
| S3 | day type | trend-day vs non-trend (RESEARCH §A2 classifier) | A | secondary |
| S4 | overnight inventory | extreme (long ∪ short) vs balanced (RESEARCH §A4) | A | secondary |
| S5 | calendar tier | tier-1 release session vs not (RESEARCH §A5) | A | secondary |
| S6 | MAE band | `mae_r ≤ 0.50` vs `> 0.50` — **arbitrary, frozen at the midpoint of the risk unit; not chosen from data** | C | secondary |
| S7 | time in window | first 60 minutes vs after — **arbitrary, frozen** | A | secondary |

**Explicitly excluded, with reasons on the record** — this list is as much of the
pre-registration as the included one:

- **Day of week.** Five levels, **15** non-trivial binary splits, no proposed mechanism.
  It is the highest p-hacking yield per unit of sample in the entire schema and it is out.
- **Direction (long/short).** A mechanism argument exists (index drift), but it is not
  strong enough to spend a Bonferroni slot on. Exploratory lane, §3.7.
- **Entry timeframe.** Four levels, 7 splits, and it is heavily confounded with pattern.
  Exploratory lane.
- **`In Window`.** Constant (§1.5 defect 1). Untestable.
- **Anything built on `ofi_*`.** BIASED at snapshot resolution (RESEARCH §B1). A biased
  input cannot produce an unbiased cut.
- **Any cut on `book_*` / `wall_*` for a session where `depth_clock_verified = false`.**

**Adding a ninth cut is a protocol amendment**, dated, registered, and it re-derives every
threshold in §3.4. It is not a decision made during an autopsy.

## 3.2 The MAE / MFE procedure

Sweeney's premise: if the entries are sound, winners and losers separate on how far the
trade went against them before it worked. Winners should cluster below some adverse
excursion; losers should extend past it. The output is a **stop placement grounded in the
distribution rather than in a round number.**

Fixed procedure:

1. Plot `mae_r` against final `r_multiple` for every closed trade, winners and losers on
   the same axes. Do this **per era**, never pooled — a boundary that only exists in one
   era is not a boundary.
2. Report the MAE distribution of winners: median, p75, p90, max. The candidate stop is
   read off the winners' upper tail, not off the losers.
3. Report `mfe_r` against `exit_reason`, and `post_exit_ext_r` against `planned_target_r`.
   These separate **"the entry was wrong"** from **"the entry was right and the exit was
   wrong"** — different diseases with different treatments, and the second one is not a
   reason to cut a pattern.
4. Report `t_to_mae_min` and `t_to_mfe_min`. A trade whose MAE arrives in minute one is a
   different animal from one that bleeds for forty minutes first, even at identical MAE.
5. **Any stop level suggested by this analysis is a §4 proposal, not a change.** Fitting a
   stop to the observed MAE distribution and then measuring the same trades against it is
   circular; the new stop is tested forward or not at all.
6. `n` for a usable MAE boundary: Sweeney's own framing is **100+ trades**. Below that,
   report the plot and the quartiles and stop.

## 3.3 Era rule

Every cut in §3.1 is evaluated **per era and reported per era**, and a cut cohort qualifies
only if it is bad in **every** era (§3.2 of VALIDATION-PROCESS, the wall-quality-cut
precedent). Half-year decomposition is part of the standard autopsy — the trigger for that
rule was a losing stretch invisible at calendar-year granularity.

**Today there is one era.** Until a second exists, every §3.1 cut is INCONCLUSIVE by
construction, regardless of what it shows. An agent must report this fact in the header of
every autopsy it produces rather than burying it in caveats.

## 3.4 The multiple-comparisons guard

**The arithmetic that motivates it.** The existing tag schema alone — before a single new
field from §1.2, before a single continuous threshold — already affords **30 non-trivial
binary splits**:

| field | levels | binary splits |
|---|---|---|
| pattern | 3 | 3 |
| htf | 3 | 3 |
| direction | 2 | 1 |
| entry_tf | 4 | 7 |
| news_today | 2 | 1 |
| day_of_week | 5 | **15** |
| **total** | | **30** |

At α = .05 across 30 independent tests on data with **no real structure at all**:

| k tests | expected false positives | P(at least one "significant") |
|---|---|---|
| 8 | 0.40 | 33.7% |
| 20 | 1.00 | 64.2% |
| **30** | **1.50** | **78.5%** |
| 50 | 2.50 | 92.3% |

**Slicing 28 trades thirty ways will produce a finding about four times out of five when
nothing is there.** Add the §1.2 fields and any continuous threshold and the count is
effectively unbounded. This is Simmons, Nelson & Simonsohn's result — undisclosed
flexibility in analysis inflates a nominal 5% false-positive rate toward 60% — and
pre-specification is the only thing that answers it.

**The guard, frozen:**

1. **Hierarchical (gatekeeping) structure.** The **primary** endpoint P is tested at
   **α = .05**. The **seven secondaries** are tested at **α = .05 / 7 = .00714** each.
2. **The primary is gated on §2.2.** P cannot be run at all until the tier assignment
   rules exist and were registered from a legal source (§2.2). Running P against tiers
   inferred from the same log is circular and its result is void.
3. **Everything not in §3.1 is exploratory** and can never reach §4 — see §3.7.
4. **Overlapping-observation correction.** S3, S4, S5 and S7 are **session-level** facts.
   A session contributing three trades contributes **one** independent draw on those cuts,
   not three. Effective n for those cuts is the **session count**, and the autopsy reports
   both numbers side by side. (RESEARCH cross-cutting failure mode 4.) Measured on the
   current log: **28 trades across 19 distinct sessions** (12 sessions with 1 trade, 5 with
   2, 2 with 3). For S3/S4/S5/S7 the honest n is **19, not 28** — this correction alone
   removes **32%** of the apparent sample before any other consideration.
5. **Report all eight, always.** Including the null ones, including the ones that came out
   backwards. A cut list is only a guard if the failures are published; reporting the
   winners from a pre-committed list is the same as not having one.

## 3.5 One look, at a declared N

**The default is a single analysis at a pre-declared N, with no interim looks.** Monthly
peeking at an accumulating sample is a multiple-comparisons problem in the time dimension
and it inflates the error rate exactly the way §3.4 describes.

If an interim look is taken anyway, it is legal only under a **declared alpha-spending
schedule fixed in advance** — and the nominal threshold per look drops accordingly:

| looks | nominal α per look (Pocock, two-sided .05) |
|---|---|
| 1 | .0500 |
| 2 | .0294 |
| 3 | .0221 |
| 5 | .0158 |
| 10 | .0106 |

O'Brien–Fleming is the more common choice in practice because it makes early stopping very
hard and leaves the final analysis near the uncorrected threshold; Pocock spreads the
budget evenly. **The sources agree that unadjusted repeated looks are invalid and disagree
about which spending function to prefer** — that disagreement is recorded, not adjudicated.
Either is legal here; neither may be selected after the looks have started.

**Declared N for the first autopsy: the primary endpoint's arms reaching 43 each (§2.3),
or 12 months elapsed, whichever comes first.** A 12-month look that arrives underpowered is
reported as INCONCLUSIVE — that is a legitimate and expected outcome, not a failure of the
protocol.

## 3.6 Ledgering

Every cut evaluated — all eight, and every exploratory one from §3.7 — is a ledgered arm in
the canonical JSONL trial ledger, with its pre-registered threshold, its per-era result and
its status. The ledger is append-only; a corrected row is appended under a distinguished key
with the original marked `superseded` and pointed at the replacement. Nothing is edited in
place. This is the same discipline already applied to the OBK/PO3 correction.

## 3.7 The exploratory lane

Curiosity is not the problem; laundering curiosity as evidence is. So exploratory cuts are
permitted, on three conditions:

1. They are **labelled `exploratory = true`** in the ledger, permanently.
2. They carry **no p-value and no significance claim**, ever. They produce descriptions.
3. **They cannot reach §4.** An exploratory finding's only legal destination is a **new
   pre-registration** with its own declared N, tested on data that did not generate it.

This is the same relationship the desk already has with a descriptive quintile result:
reportable, never quotable as tradeable.

---

# 4. The action gate

## 4.1 The only two legal outcomes

An autopsy or a tier analysis terminates in **exactly one** of two documents, or in
nothing:

- **(a) A pre-registered proposal to RAISE risk on a tier.**
- **(b) A pre-registered proposal to DE-RISK or RETIRE a pattern.**

Both are **proposals**. Both ship through **the same validation gate as every other spec
change** — pre-registration, acceptance bars, era split, permutation null, DSR/PBO, ledger,
human sign-off at the paper-to-live step. Neither self-authorizes; `docs/VALIDATION-PROCESS.md`
§0 law 3 already says nothing in a verdict authorizes a ship, and this section does not
create an exception for conviction work.

**There is no third outcome and no live-tinkering path.** The gate is not "usually" the
route. It is the only route.

## 4.2 What a proposal must contain

Identical fields for (a) and (b), so that raising and cutting face the same burden:

1. The **pre-registered hypothesis** it descends from, by ID, with the registration date.
2. The **cut or tier**, its frozen threshold, quoted from §2.2 or §3.1 — not restated from
   memory.
3. **n per arm, per era**, and effective n after the §3.4(4) session-level correction.
4. The **test statistic and the α it was judged against**, primary or secondary, stated.
5. **Power at the observed n for the effect being claimed**, and the **Type M exaggeration
   ratio** at that n (§2.4). A proposal that omits these is incomplete and is returned.
6. The **result in every era**, including the eras where it did not hold.
7. **All eight §3.1 cuts reported**, not only the one being proposed (§3.4(5)).
8. The **proposed multiplier change**, one step at a time. T3 → T2 or T2 → T1; never a
   two-step jump, and never a change to more than one tier in a single proposal.
9. The **kill criterion for the change itself** — what result would reverse it — declared
   before it ships (§7 of VALIDATION-PROCESS).
10. For **(a) only**: an explicit statement of the §2.6 asymmetry and why the estimate is
    believed not to be inflated.

**Asymmetric burden, deliberately.** A **(b)** de-risk proposal may proceed at the
declared α. An **(a)** raise-risk proposal additionally requires **two eras of agreement**
and **n ≥ 43 in both arms of the comparison it rests on**. §2.6 is the reason: the two
actions have different error costs, so they get different bars.

## 4.3 Illegal moves, enumerated

None of the following is a legal response to an autopsy, and an agent that produces one has
malfunctioned:

- Changing a live risk multiplier because a tier "has been working."
- Filling §2.2 from the log the tiers will be tested on.
- Adding a ninth cut mid-autopsy because the eight came back null.
- Reporting only the cuts that reached significance.
- Dropping a losing stretch as an outlier without it being a pre-registered cut.
- Re-running with a different MAE threshold because 0.50R "wasn't the right level."
- Treating an exploratory finding as a result.
- Quoting a descriptive or era-local number as a tradeable edge.
- Taking an interim look and then choosing the spending function.
- Any change to any live parameter that has not passed §4.1.

## 4.4 When neither outcome is reached

**The expected result of the first autopsy is neither (a) nor (b).** At the sample sizes in
§2.5 that is arithmetic, not pessimism. The correct output is then:

> `INCONCLUSIVE — n insufficient. No change proposed. Next look at N = <declared>.`

`INCONCLUSIVE` blocks exactly like `FAIL`. Nothing changes; tagging continues; the next look
is at the next declared N. An agent that manufactures a proposal to avoid returning
INCONCLUSIVE has broken the protocol in the most damaging way available to it, because that
failure looks like productivity.

---

## 5. What this instrument cannot do

Stated so no one has to discover it later:

- It cannot tell you anything today. §2.5 puts the first meaningful tier comparison
  **~4.6 months** out at the current cadence, and the thinnest pattern arm **~8.6 months** out.
- It cannot rescue a small sample with a better statistic. Bayesian methods, bootstrap,
  permutation — all of them are honest about the same width; none of them manufacture
  information. Where they differ from the frequentist numbers above, the difference is
  smaller than the interval.
- It cannot detect a lookahead. Circularity is robust (RESEARCH failure mode 1). That is the
  §2.5 window-causality bar's job and the load-time clock assertion's job, and this protocol
  assumes both have already run.
- It cannot validate a factor the data cannot construct. Every **BIASED** and **NOT
  CONSTRUCTIBLE** entry in RESEARCH §0 stays out, and no proxy substitutes for one.
- It cannot substitute for the backtest. A pre-registered backtest on the fit span is the
  cheapest source of tier rules by an enormous margin — thousands of trades instead of
  ~28/month — and §2.2's deadlock is most naturally broken there, not by waiting.

---

## Sources for this protocol

Methodology sources, distinct from the factor sources in the RESEARCH report:

- [Gelman & Carlin — Beyond Power Calculations: Assessing Type S (Sign) and Type M (Magnitude) Errors, *Perspectives on Psychological Science* 9(6), 641–651 (2014)](https://sites.stat.columbia.edu/gelman/research/published/retropower_final.pdf) — §2.4's exaggeration and sign-error framing
- [Simmons, Nelson & Simonsohn — False-Positive Psychology, *Psychological Science* (2011)](https://journals.sagepub.com/doi/10.1177/0956797611417632) — §3.4's researcher-degrees-of-freedom argument
- [Ensuring the quality and specificity of preregistrations (PMC7725296)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7725296/) — pre-registration is only as good as its specificity; the reason §2.2 and §3.1 freeze thresholds rather than gesture at them
- [Lan–DeMets alpha spending function approach](https://eclass.uoa.gr/modules/document/file.php/MATH301/PracticalSession3/LanDeMets.pdf) and [Penn State STAT 509 §9.6 — Alpha Spending Functions](https://online.stat.psu.edu/stat509/lesson/9/9.6) — §3.5
- [Introduction to Conducting Interim Analyses Using Alpha Spending](https://jfiksel.github.io/2021-02-03-alpha_spending_explained/) — Pocock vs O'Brien–Fleming comparison, the disagreement recorded at §6.2(14)
- [Downey — Why fractional Kelly? Simulations of bet size with uncertainty](https://matthewdowney.github.io/uncertainty-kelly-criterion-optimal-bet-size.html) and [Kelly betting with uncertainty in probability estimates, arXiv:1701.02814](https://arxiv.org/pdf/1701.02814) — §2.6's overbetting asymmetry (MacLean, Thorp & Ziemba, *The Kelly Capital Growth Investment Criterion*, 2011, cited through these)
- [QuantifiedStrategies — MAE and MFE explained](https://www.quantifiedstrategies.com/maximum-adverse-excursion-and-maximum-favorable-excursion/) and [TradingMetrics — Max Adverse Excursion: Where Your Stops Should Sit](https://docs.tradingmetrics.com/en/technical-analysis/trading-metrics/trade-specific-metrics/max-adverse-excursion) — §3.2, Sweeney's method as reported by secondary sources
- [Traders Second Brain — MAE and MFE: How to Read Trade Excursion Data](https://traderssecondbrain.com/guides/mae-mfe-analysis) — the winners-cluster-below-a-boundary framing and the 100+ trade figure

In-repo, load-bearing: `docs/VALIDATION-PROCESS.md` §2.1–§2.5, §3.2, §4, §5, §7;
`docs/RESEARCH-confluence-factors-beyond-library.md`;
`docs/FINDING-london-depth-timestamp-lookahead.md`;
`data/reference/feb2026_hand_log.csv` (cell counts only).

All arithmetic in §2.3, §2.4, §2.5 and §3.4 was computed for this document — closed-form
two-proportion power and sample size, and a 150,000-draw simulation per row for the Type M
/ Type S table. None of it is quoted from a source.

---

## 6. Provisional claims — everything I could not source

Covers **both** deliverables: this protocol and
`docs/RESEARCH-confluence-factors-beyond-library.md`. Each entry is a claim that is either
unsourced, sourced only to material that publishes no method, or subject to a disagreement
between sources that I have recorded rather than resolved.

### 6.1 Unsourced or vendor-sourced performance claims (RESEARCH report)

| # | claim | why provisional |
|---|---|---|
| 1 | NYSE TICK: "five or more extreme readings in one direction with zero in the other during the first hour" identifies a trend day **82%** of the time | Single trading-education source. No sample size, span, instrument or method published. Unreplicated. |
| 2 | Market Profile **Neutral days occur 30.21%** of sessions | The two-decimal precision implies a specific study that is never cited. Span and instrument unstated. |
| 3 | Gap fill: **SPY 59%** of gap-ups and **69%** of gap-downs fill same session | Blog-sourced. Span not stated; SPY ≠ NQ, and the transfer to NQ is assumed, not measured. |
| 4 | "Common" gaps fill **70–75%** within five sessions; breakaway gaps **<30%** within a month | Vendor blog. The gap *taxonomy itself* is discretionary, so the base rates are conditional on an unstated classifier. |
| 5 | Initial balance: ES stays inside the IB on **2.2%** of 2,686 sessions; NQ **3.8%** | Single aggregator. Sample size given, method not. IB definition (60 vs 30 min) affects the number and is not stated. |
| 6 | YM initial-balance-breakout **76.8% win rate** | Vendor. No cost model, no fill model, no span. RESEARCH failure mode 6 applies directly. |
| 7 | VIX9D/VIX ratio is "too noisy" versus VIX/VIX3M | Practitioner assertion. No comparative study located. |
| 8 | VIX term structure in backwardation on **~8%** of days | Span-dependent and the span is unstated; the figure moves a lot with the window chosen. |
| 9 | Volatility around NFP is **2–4×** normal | CME educational material; range given without a definition of "normal" or a measurement window. |
| 10 | Footprint absorption at a **3:1** bid/ask imbalance | A convention, not a finding. No derivation located anywhere. |
| 11 | Depth replenishment half-life **~20s** (Large 2007) | Real paper, but LSE equities in 2007. Transfer to NQ futures in 2026 is an assumption I could not test. |

### 6.2 Recorded disagreements — not adjudicated

| # | disagreement |
|---|---|
| 12 | **Pre-FOMC drift.** NY Fed (Lucca & Moench) documents large pre-announcement excess returns; NBER work offers a competing explanation; a 2024 follow-up questions whether it persists post-publication. I did not pick a side. |
| 13 | **MAE's origin.** Sourced variously to Sweeney's *Maximum Adverse Excursion: Analyzing Price Fluctuations for Trading Management* (Wiley, 1996) and to *Campaign Trading* (Wiley, 1996). Same author, same year, two titles. Unresolved. |
| 14 | **Alpha-spending function.** Sources agree unadjusted repeated looks are invalid; they disagree on Pocock vs O'Brien–Fleming. §3.5 permits either, pre-declared, and picks neither. |
| 15 | **ES/NQ divergence.** Described both as a leading signal and as ordinary beta dispersion. No study located that separates them. Moot here — NOT CONSTRUCTIBLE without an ES feed. |

### 6.3 Unsourced conventions in this protocol

| # | claim | status |
|---|---|---|
| 16 | Conviction multipliers **0.5× / 1.0× / 1.5×** | Convention. The literature converges on the shape and disagrees on the numbers; **no source publishes a derivation.** Adopted as a placeholder, inactive until §4. |
| 17 | **Three** tiers rather than two, four or five | Arbitrary. Chosen because three-tier grading is the most common practice; note that more tiers means thinner arms and a longer §2.5 timetable. |
| 18 | `scratch` threshold at **\|R\| < 0.10** | Arbitrary, frozen. Not derived. |
| 19 | MAE cut at **0.50R**; time-in-window cut at **60 minutes** | Arbitrary, frozen. Explicitly not chosen from data — see §3.1. |
| 20 | **Eight** pre-committed cuts | A judgement balancing coverage against the Bonferroni penalty. Not derived from anything. |
| 21 | `late_tag` window of **120 seconds** | Arbitrary. Should be tightened once the logging tool exists and its real latency is known. |
| 22 | Declared N for the first look = **43/arm or 12 months** | The 43 is derived (§2.3); the 12-month backstop is arbitrary. |
| 23 | Sweeney's "**100+ trades**" for a usable MAE boundary | Sourced to secondary summaries of Sweeney, not to a derivation in the original. |
| 24 | Raise-risk requiring **two eras** where de-risk requires one | A deliberate asymmetry justified by the Kelly overbetting argument (§2.6), which is sourced — but the specific choice of "two" is not. |

### 6.4 Assumptions about this desk's own data, not findings

| # | assumption |
|---|---|
| 25 | **28 trades/month** and the **46/36/18** pattern mix persist. Drawn from one month. Every month-count in §2.5 inherits this and is a projection, not a forecast. |
| 26 | The 28 rows are a **complete** record of trades taken in that window, not a filtered subset. Not verifiable from the file. If trades were omitted, every count in §1.6 is wrong in an unknown direction. |
| 27 | ~~Session count approximated~~ — **superseded**: counted exactly. 28 trades across **19 sessions**. §3.4(4) now states the measured figure. Retained here so the correction is visible rather than silently edited. |
| 28 | The tier structure will be **roughly balanced**. If it is not, §2.5's timetable is set by the thinnest tier and could be far longer. |

---

**Nothing in this document has been run. No trial has been ledgered against it. It grades
nothing and authorizes nothing.**
