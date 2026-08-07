# Cluster α — cheap-kill feasibility test on NQ

# VERDICT: DEAD — ON POSITION SIZING, INDEPENDENT OF WIN RATE

**The mechanism.** RR 0.2 against a level-based target forces
`stop = 5 × (entry-to-target distance)`. The median entry-to-level distance measured over
772 NQ sessions is 85 points, so the median stop is **424 points**. That is not a parameter
choice and no rule change reaches it — it is arithmetic. Negative RR combined with a level
target is **mathematically incompatible with a trailing-drawdown account on this instrument**.
No exit rule, no bias rule, and no win rate — not even 100% — alters it, because the
disqualifier is the size of a single loss, not the frequency of losses.

**MNQ is where the port actually dies.** The original analysis priced NQ only. MNQ is one
tenth the size and is the smallest listed contract in this family, so it is the floor:

| contract | $/point | median loss | p95 loss |
|---|---|---|---|
| NQ | $20 | $8,475 | $40,020 |
| **MNQ** | **$2** | **$848** | **$4,002** |

Against a **$2,000 trailing drawdown**, trading the minimum size of the smallest contract:

- median loss = **42.4%** of the entire allowance
- p95 loss = **200.1%** of the allowance — one such trade ends the account outright
- **bust in 2.4 median losses**

There is no smaller contract. There is no fractional futures contract. So there is no
position size at which this geometry fits inside the account type the model is sold for.
That is what makes this DEAD rather than unattractive.

**What this does not say** — see [Scope of the claim](#scope-of-the-claim), which is not
optional reading. This kills α *on NQ inside a trailing-drawdown account*. It does not kill
α as taught.

| | |
|---|---|
| Date | 2026-08-07 |
| Verdict | **DEAD — on position sizing** (supersedes the INCONCLUSIVE finding retained below) |
| Model under test | Cluster α, from ledger records 3, 6, 7 (masterclass + two supporting videos) |
| Instrument tested | NQ front-month outrights; MNQ by scaling |
| Sample | 772 sessions, 2023-01-03 → 2026-01-30 |
| N_trials (this study) | **1** — see [N_trials](#n_trials) |
| Ledger | Separate from the AUG-01 pre-registration. Different base model; α's α-budget is not the sweep model's. |

---

## Scope of the claim

Stated precisely, because overclaiming here would repeat the exact error this audit was built
to catch.

**What died:** α traded on NQ, inside a prop-firm trailing-drawdown account.

**What did NOT die:** α as taught. α is a forex and gold model, and those instruments have
**fractional lot sizing** — position size scales continuously with the stop, so a 424-point
equivalent stop is met by shrinking the lot rather than by blowing the risk budget. The
geometry that kills the model here **does not arise there.** Futures are quantised at one
contract, and that quantisation is the whole disqualifier.

**We have not tested α on forex or gold, and we are making no claim about its performance
there.** Nothing in this report is evidence for or against the author's results on his own
instruments. A reader who takes "cluster α is dead" to mean "negative RR does not work" has
drawn a conclusion this study does not support and cannot support.

The separate criticisms in the retained analysis below — the absent exit rule, the missing
win-rate denominator, the arithmetic error in the masterclass — stand on their own as
documentation defects, and they are reasons the model could not be *specified*, not evidence
that it does not *work*.

---

## Retained analysis — superseded but preserved

Everything below was written before the MNQ sizing check and concluded **INCONCLUSIVE**. It
is retained deliberately and should not be deleted: it is the evidence trail for the verdict
above, and the sensitivity work in Step 2 is the most valuable part of the report — it is
what caught a profitable-looking result that was an artefact of an arbitrary hold cap.

Where the text below says "INCONCLUSIVE", read it as *inconclusive on win rate*, which
remains true. The verdict above kills the model on a criterion win rate cannot affect.

---

## Declared ports

Stated up front because results do **not** transfer back to the author's claims.

**1. Instrument.** α is taught on forex and gold. This is NQ. Every number below is a
statement about NQ index futures and says nothing about whether α works where he trades it.
A model can be sound on GBPUSD and unsound on NQ purely through tick structure and
overnight liquidity.

**2. "Previous day" — declared as the prior CALENDAR UTC DAY.** α is an FX model whose day
boundary is 00:00 UTC and whose entry is the 00:00 UTC candle, so the level it targets is
the high/low of the 24-hour block that has just closed at the instant of entry. Prior-UTC-day
is the only NQ definition preserving both properties. A Globex-session definition would put
the boundary at 17:00 ET, hours from entry; an RTH definition would discard the overnight
move entirely. Declared once, used throughout, not varied.

**3. Session.** 00:00–01:00 UTC is 19:00–20:00 ET in winter, 20:00–21:00 ET in summer — thin
overnight liquidity, not RTH. Costs are modelled accordingly (below), never with RTH
assumptions.

**Data handling.** Front-month outrights only; every symbol containing a hyphen excluded as
a calendar spread. Not back-adjusted, so indicator state resets at each of the 12 detected
quarterly rolls and the session after each roll is skipped (24 sessions dropped). Bars are
open-labelled at source, verified empirically in the Stage 0 audit, so the bar stamped 00:00
covers 00:00:00–00:00:59 and its open *is* the price at 00:00:00 — the α entry reference.

---

## Step 1 — Cost gate

At RR 0.2 with a level-based target the geometry is self-defining: `stop = 5 × target`.

### 1a. Distance from the 00:00 UTC open to the previous-day level

| | median | IQR (25–75) | p05 | p95 | p99 |
|---|---|---|---|---|---|
| to prev HIGH (pts) | 61.0 | 25.8 – 153.9 | 6.2 | 402.1 | 712.6 |
| to prev HIGH (ATR) | 0.24 | 0.10 – 0.61 | 0.02 | 1.36 | 2.09 |
| to prev LOW (pts) | 108.2 | 43.9 – 209.8 | 12.0 | 394.4 | 672.8 |
| to prev LOW (ATR) | 0.42 | 0.17 – 0.79 | 0.05 | 1.44 | 1.81 |

**In 0 of 1,544 legs is the 00:00 open already beyond the level.** That is structural, not
luck: the 00:00 open is effectively the prior day's closing price, which lies inside the
prior day's range by definition. So **both legs are always valid, every session** — the model
can never fail to produce a signal. A system that always fires is a system whose signal
carries no selection information, and it is the reason the bias rule has to do all the work.

### 1b. Implied stops and dollar risk

| | p05 | p25 | median | p75 | p95 |
|---|---|---|---|---|---|
| target (pts) | 8.0 | 32.2 | 84.8 | 186.4 | 400.2 |
| **stop (pts)** | 40.2 | 160.9 | **423.8** | 932.2 | 2,001.0 |
| **risk ($/contract)** | 804 | 3,219 | **$8,475** | $18,644 | **$40,020** |

Stated plainly, as instructed: **the median trade risks $8,475 on a single NQ contract, and
one trade in twenty risks more than $40,000.** This is the intended consequence of the
geometry, not a modelling artefact — a 0.2 reward multiple against a level 85 points away
*requires* a 424-point stop.

### 1c. Cost-adjusted breakeven

`p₀ = (s + c) / (s × (R + 1))`, R = 0.2.

Cost levels, in points ($20/pt, 0.25 pt tick). Entry is a limit (no spread paid); the target
is a limit at a level (no slip); the stop becomes a market order on trigger and pays spread
plus depth. Commission $4.50 round turn = 0.225 pt. Slip brackets ordinary / thin / stressed
overnight depth at 19:00–21:00 ET, where NQ top-of-book is a fraction of RTH.
**These are declared assumptions, not measurements** — the Stage 0 audit established there is
no trade-level data, so no execution-quality estimate is possible from what we hold.

| cost level | c (pts) | s@p05 | s@p25 | s@p50 | s@p75 | s@p95 |
|---|---|---|---|---|---|---|
| LOW (comm + 1 tick) | 0.475 | 84.32% | 83.58% | 83.43% | 83.38% | 83.35% |
| MID (comm + 3 tick) | 0.975 | 85.36% | 83.84% | 83.53% | 83.42% | 83.37% |
| HIGH (comm + 7 tick) | 1.975 | 87.43% | 84.36% | 83.72% | 83.51% | 83.42% |

The asymptote is `1/(1+R) = 83.33%` — the cost-free breakeven at RR 0.2. Because the stops
are enormous, costs are proportionally negligible and every cell sits within a few points of
that floor.

**TERMINATION CHECK: worst case across the p05–p95 stop range and all cost levels = 87.43%.
Below 95%. Gate NOT triggered.**

The irony is worth stating: α survives its cost gate *because* its stops are so large that
commission and slippage round to nothing against them. The gate is passed by the same
property that makes the model untradeable at Step 1b.

---

## Step 2 — Unconditional both-directions test

Bias rule removed entirely, not guessed. Both legs taken every session, identical geometry.
**Ambiguous bars resolve stop-first, unconditionally.**

| | resolved | wins | losses | unresolved | hit rate |
|---|---|---|---|---|---|
| LONG | 735 | 633 | 102 | 37 | 86.12% |
| SHORT | 667 | 569 | 98 | 105 | 85.31% |
| **POOLED** | **1,402** | **1,202** | **200** | **142** | **85.73%** |

Mean net per leg, pooled: **+36.84** (LOW), **+36.34** (MID), **+35.34** (HIGH) points.
Pooled path at MID cost: final +50,948 pts, max drawdown **−5,669 pts (−$113,388/contract)**,
longest losing streak 2.

Win/loss asymmetry (MID cost, resolved legs):

| | n | mean | median | extreme |
|---|---|---|---|---|
| wins | 1,202 | +115.05 | +72.40 | +1,360.78 |
| losses | 200 | **−436.71** | −315.98 | **−2,607.22** (−$52,144/contract) |

Sum of wins +138,289; sum of losses −87,341; net +50,948.

### The result is an artefact of an assumption α does not specify

Two choices in my implementation drive the entire answer, and **neither comes from α**:

**(a) I capped holding at 20 days.** α states no time exit — record 3 refuses break-even and
partials, so a trade runs to target or stop. But α is simultaneously a *day* model: MOS
window 00:00–01:00, "two to three" trades a day. Only **67.8%** of legs resolve within the
same UTC day. Holding a day-model trade for twenty days to reach its target is not α; closing
it at session end is not α either, because α specifies no such exit.

**(b) I excluded 142 unresolved legs (9.2%) from the hit rate.** They are asymmetric —
37 long, 105 short — so the exclusion is not neutral.

The verdict flips on both:

| hold cap | win rate, unresolved **excluded** | win rate, unresolved **as loss** |
|---|---|---|
| same UTC day (0d) | 89.70% | **55.25%** |
| ≤ 1d | 88.87% | 62.56% |
| ≤ 2d | 88.15% | 65.03% |
| ≤ 5d | 87.36% | 70.27% |
| ≤ 10d | 86.54% | 74.94% |
| ≤ 20d (as reported) | **85.73%** | **77.85%** |

Against a breakeven of 83.56%, the model clears in the left column and fails in the right
one, at every cap. **The answer is determined by an exit rule the source material does not
contain.** That is the honest headline of Step 2.

---

## Step 3 — Required lift

Base rate (pooled, stop-first, 20-day cap, unresolved excluded): **85.73%**

| cost level | breakeven @ median stop | required lift |
|---|---|---|
| LOW | 83.44% | **−2.29 pts** |
| MID | 83.56% | **−2.18 pts** |
| HIGH | 83.79% | **−1.95 pts** |

Under the reported treatment the required lift is *negative* — the unconditional base rate
already clears breakeven without any bias rule. Under the unresolved-as-loss treatment it
becomes **+5.71 pts**.

So the required lift spans **−2.2 to +5.7 win-rate points**, depending entirely on the
unspecified exit rule. Both ends are well inside the ~10-point threshold at which a
discretionary rule stops being plausible.

**Is a discretionary bias rule plausible at that magnitude?** At +5.7 points, yes —
comfortably. That is a modest edge, and picking the nearer level, or the level in the
direction of the higher-timeframe trend, would plausibly supply it. This is not a case where
the arithmetic forecloses the question.

### Hindsight ceiling

**762 of 770 sessions (98.96%) had at least one winning leg.**

That is the absolute upper bound on any bias rule, and it sits far above breakeven. No
bias-rule-based kill is available here: perfect foresight would produce a 99% win rate, so
the model is not arithmetically doomed the way a low ceiling would prove.

The ceiling is also uninformative in a specific way worth recording: because both legs are
always valid and both targets sit inside yesterday's range, *almost every session offers a
winner to someone with foresight*. A near-99% ceiling on a system that always fires tells you
the levels get touched, not that they can be chosen in advance.

---

## The disqualifier: position size

*Written before the MNQ check. It was flagged here as outranking the verdict; the MNQ
numbers at the top of the file confirmed that and converted it into the verdict.*

This sits outside the DEAD / NOT VIABLE / INCONCLUSIVE trichotomy but outranks it for the
project's actual purpose.

- Median risk per contract: **$8,475**
- p95 risk per contract: **$40,020**
- Largest single realised loss: **$52,144 on one contract**
- Max drawdown on the pooled path: **$113,388 per contract**

α is marketed as a prop-firm evaluation method, and the masterclass carries a refund
guarantee tied to passing a challenge. Against a 50K evaluation with a 2,000-point trailing
drawdown, **a single median-sized loss is roughly four times the entire drawdown allowance.**
The smallest quartile of trades still risks $3,219. There is no contract count at which this
geometry fits inside a funded-account risk envelope — one contract is already the minimum,
and one contract is already far too much.

Two further observations, recorded not resolved:

- The masterclass claims two consecutive losses at a 95% win rate is "still 10%" [08:00].
  It is 0.25%. 10% corresponds to a ~68% win rate. The arithmetic underpinning the model's
  central safety argument is wrong by a factor of forty.
- The realised longest losing streak here was 2, consistent with a high win rate — but each
  loss averaged −437 points. The streak statistic is reassuring and the per-loss magnitude
  is not; quoting the first without the second is how this style is usually sold.

---

## Verdict (superseded — see the DEAD verdict at the top of this file)

**INCONCLUSIVE *on win rate*.** This remains accurate and is retained. It is no longer the
operative verdict: the sizing analysis above kills the model on a criterion that win rate
cannot influence.

By the stated criteria: Step 1 did not terminate (worst-case breakeven 87.43% < 95%); the
hindsight ceiling (98.96%) is far above breakeven, so no bias-rule kill is available; and the
required lift (−2.2 to +5.7 points) is small enough that the bias rule genuinely decides the
outcome. That is the definition of INCONCLUSIVE, and per the brief this is where a real study
would begin — as a separate decision.

**My recommendation is not to take that decision.** Three reasons, in order:

1. **Position size is disqualifying for the stated use case** and is not a tuning problem —
   it is forced by RR 0.2 against a level-based target. No filter fixes it.
2. **The inconclusiveness is caused by missing source material, not by a close call in the
   data.** The exit rule is absent from α, and it is worth ±16 win-rate points. Until the
   remaining cluster-α videos are pulled, any further study is estimating a parameter the
   corpus may simply state.
3. This is an **NQ port of a forex model**. Even a clean pass would not license the author's
   claims, and the project's own instrument is NQ, so a pass would need re-derivation from
   scratch as an NQ model with its own pre-registration.

What would change the verdict: cluster α's missing videos, specifically anything stating an
exit rule for a trade that reaches neither level within the session. Priority #6, the *Full
Negative RR Masterclass*, is the most likely source and is already the top target in the
caption-pull manifest.

---

## N_trials

**1.** This study tested one hypothesis: does cluster α's geometry clear its costs and its
base rate on NQ.

The declared 02:00 window extension was **not run**, and honesty requires saying why rather
than reporting it as executed: α's entry is *at* the 00:00 candle, so modelling the entry as
a limit resting at that candle's open makes the fill instantaneous and the
cancel-if-unfilled rule can never bind. The 01:00 and 02:00 variants are therefore identical
by construction. The limit *price* rule is not stated anywhere in records 3, 6 or 7 — another
underspecification. A resting limit away from the open would shrink the sample without
changing the geometry.

The sensitivity analyses in Step 2 (unresolved treatment, hold cap) are **not** hypothesis
trials and do not increment N_trials. They are robustness checks on my own implementation
choices, and reporting them was mandatory rather than exploratory — without them the study
would have reported a profitable strategy that is an artefact of an arbitrary 20-day cap.

Nothing was tuned. No filters were added. No variant beyond the one declared was attempted.

---

## Reproducing

```bash
cd research/star-trading/tools
python3 alpha_data.py     # build front-month cache from the .zst archives (~19s)
python3 alpha_step1.py    # cost gate
python3 alpha_step2.py    # unconditional test + required lift
```
