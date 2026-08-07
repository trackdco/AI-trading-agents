# SIGNAL COUNT — VWAP/BB frozen spec

**Revision 2, 2026-08-07 — full filter stack implemented.**

**VERDICT: SPEC INCOMPLETE.** Not for the reason revision 1 anticipated. The filters *do*
reconcile the count — they remove 92.5–97.1% and land the spec at **1.59–2.70 signals/session**
against a hand-log benchmark of ~1.0. That part of the rev-1 concern is answered, and answered
in the spec's favour.

The spec fails on the second limb: **the Vault's selection rule is not stated, and it is the
binding constraint that produces the reconciliation.** On 33–92% of sessions the cap discards
43–86% of qualified candidates using a rule that appears nowhere in the document.

Not a backtest. No P&L, no stops simulated, no equity. Workbench probe only; the holdout was
never addressed. **N_trials remains 0** — measurement, not hypothesis testing. Nothing was
tuned; no reading was adopted.

---

## 1. Per-filter reduction, all four readings

Signals per session, 141-session workbench probe, cascade in the spec's own order:

| stage | A | B | C | D |
|---|---|---|---|---|
| 0 raw trigger + §7 confluence min | 92.82 | 40.96 | 30.00 | 22.13 |
| 1 + §7 invalidation-at-entry | 49.23 | 22.79 | 15.89 | 10.65 |
| 2 + §7 location | 42.09 | 18.65 | 13.09 | 9.19 |
| 3 + §6.5 RR floor (1.5R) | 20.93 | 8.73 | 5.48 | 3.38 |
| 4 + §10 Vault max 3/day | 2.89 | 2.69 | 2.52 | 1.91 |
| 5 + §5.6 one position at a time | **2.70** | **2.48** | **2.26** | **1.59** |
| **total reduction** | **97.1%** | **94.0%** | **92.5%** | **92.8%** |

Attribution, as a share of stage-0:

| filter | A | B | C | D |
|---|---|---|---|---|
| invalidation | **47.0%** | **44.4%** | **47.0%** | **51.9%** |
| location | 7.7% | 10.1% | 9.3% | 6.6% |
| RR floor | 22.8% | 24.2% | 25.4% | 26.2% |
| Vault 3/day | 19.4% | 14.8% | 9.8% | 6.6% |
| one-at-a-time | 0.2% | 0.5% | 0.9% | 1.5% |

**No single filter is the strategy** on this measure — the work is spread across invalidation
(~47%), the RR floor (~25%), and the Vault cap (7–19%). That is a healthier picture than the
"one filter does 95%" case the brief was watching for.

But share-of-stage-0 understates the Vault, because by stage 4 the absolute pool is already
small. The load-bearing framing is **what fraction of *qualified* candidates the cap throws
away**:

| reading | post-RR candidates/session | after cap | discarded by the cap |
|---|---|---|---|
| A | 20.93 | 2.89 | **86.2%** |
| B | 8.73 | 2.69 | **69.2%** |
| C | 5.48 | 2.52 | **54.0%** |
| D | 3.38 | 1.91 | **43.5%** |

And how often it binds at all:

| reading | sessions where post-RR candidates > 3 | mean post-RR candidates |
|---|---|---|
| A | **91.7%** | 20.46 |
| B | 79.5% | 8.56 |
| C | 62.1% | 5.33 |
| D | 33.3% | 3.22 |

On the loosest reading the cap chooses 3 from ~20 on nine sessions in ten.

## 2. Final counts against both benchmarks

| reading | signals/session | vs tripwire 0.486 | vs hand log ~1.0 |
|---|---|---|---|
| A | 2.70 | 5.6× above | 2.7× |
| B | 2.48 | 5.1× above | 2.5× |
| C | 2.26 | 4.7× above | 2.3× |
| D | 1.59 | 3.3× above | 1.6× |

**All four clear the tripwire, and all four are plausibly near the hand log.** The
interpretation spread has collapsed: stage 0 spanned a factor of **4.2** (22.13→92.82),
stage 5 spans **1.7** (1.59→2.70). The filters do not merely reduce the count, they compress
the sensitivity to how §3 is read — which was the substance of the revision-1 failure.

**Revision 1's verdict is superseded.** It concluded the count was unmeasurable because
faithful readings spanned 25–109×. With the full stack the readings converge to within a
factor of 1.7 of each other and within a factor of ~2.7 of the human. On the frequency
question, gate 6's input can be established after all.

**The convergence is manufactured by the cap, not earned by the filters.** Two checks confirm
it — both of which would matter enormously if the filters were doing the discriminating, and
neither of which moves the answer:

| variation | A | B | C | D |
|---|---|---|---|---|
| with invalidation | 2.70 | 2.48 | 2.26 | 1.59 |
| **without** invalidation (§7 marks it `[Hypothesis — test]`) | 2.80 | 2.62 | 2.40 | 1.93 |

| location band (unstated in spec) | A | D |
|---|---|---|
| 10% | 2.73 | 1.63 |
| 20% | 2.70 | 1.59 |
| 30% | 2.67 | 1.53 |

Removing the single largest filter entirely changes the output by 4–21%. Tripling the
unstated location band changes it by 2–6%. That insensitivity is not robustness — it is the
signature of a cap absorbing whatever arrives beneath it.

## 3. The Vault question

**Answer: (c) — neither is stated.**

§10 states a cap and a sequencing constraint, and no ranking:

> Max trades/day: **3** (config 2–3; Angus: "no more than 2–3 genuinely high-probability
> setups exist per day").

> One position at a time; no stop widening; EOD flatten (§1); drawdown kill-switch vs
> trailing DD buffer; size ceiling from MC.

§5.6 repeats the sequencing constraint:

> One position at a time. No overlapping trades ever.

**There is no ranking metric anywhere in the document.** The nearest thing is §9, and it is
explicitly scoped to *sizing*, not selection:

> Full unit vs half unit per conviction score: full requires 3+ confluences AND (with-trend OR
> A-at-extension) AND target ≥2R; any of {2 confluences, oversized stop, late-window entry,
> thin target} → half.

That conviction score is the obvious candidate for a ranking metric — it already grades
candidates on confluence count, trend alignment and target quality. But the spec uses it to
decide *how big* a taken trade is, never *which* trades are taken. §6.6's "alignment bonus"
likewise ranks targets within a trade, not candidates against each other.

So (a) is *implied* — with one position at a time and no ranking, time-priority is the only
consistent reading — but it is never written, and nothing indicates it was a decision rather
than an omission. **The selector is unspecified, and the selector is where the edge would have
to live.**

**The premise the cap was written under does not hold.** Angus's parenthetical asserts that
only 2–3 genuinely high-probability setups exist per day. The mechanised spec finds 3.2–20.5
candidates per session that pass every stated filter. The cap was conceived as a backstop
against overtrading on a scarce signal; under the spec as written it is the primary selection
mechanism operating on an abundant one. A rule that was expected to rarely bind binds on the
majority of sessions.

The practical consequence: for reading A, on 92% of sessions the system's output is determined
by *which qualified candidate happened to occur earliest*, not by any quality judgement. Two
implementations agreeing on every written rule would produce different trade lists whenever
their candidate ordering differed — and would disagree about the strategy's performance.

## 4. Declared placeholders

Where the spec states no value, the placeholder is declared rather than silently chosen:

| parameter | value used | status |
|---|---|---|
| location band ("at HTF range top") | top/bottom 20% of trailing 4h range | **NOT STATED IN SPEC** — sensitivity reported above |
| front-run F | 2.0 pts | spec §6.4 says "start 2–3"; low end chosen, most permissive to the RR floor |
| one-position lockout | 30 min | spec §1: "median trade resolves ~30 min" — an approximation, since exact serialisation needs outcomes |
| entry variant | E1, limit at BB MA | spec-1 Step 8 names W1/E1/V0 as defaults |
| RR-floor target | nearest valid menu level beyond entry | §6.5 reads "nearest valid target < 1.5R → skip" |

The location band is the only one with no anchor in the text at all. Its sensitivity was
measured (2–6%) and found immaterial, but that is because the cap dominates, not because the
spec is complete.

---

## VERDICT

**SPEC INCOMPLETE.**

The brief's first limb is **satisfied**: filtered counts land at 1.59–2.70/session across all
four readings, near the hand log's ~1.0 and comfortably above the 0.486 tripwire. The filters
reconcile the count, they compress the interpretation spread from 4.2× to 1.7×, and no single
filter dominates the cascade. Revision 1's conclusion that the frequency was unmeasurable is
withdrawn.

The second limb **fails**: the Vault selection rule is unstated. The spec gives a cap and a
sequencing constraint but no ranking metric, and the one graded score it does define (§9
conviction) is explicitly assigned to sizing instead. This is not a technicality — the cap
binds on 33–92% of sessions and discards 43–86% of candidates that passed every written
filter. The reconciliation reported above is produced by that cap. Whatever rule fills the gap
will determine most of the trades the system takes, and it is currently the analyst's choice
rather than the strategy's.

**Gate 6's frequency input can now be established** — the count is measurable, and it clears.
Gate 4 cannot: specifiability fails on the selector, and it fails at the point where it
matters most.

---

## Reproducing

```bash
cd research/star-trading/tools
python3 alpha_data.py          # front-month cache (~19s)
python3 vwapbb_signals.py      # rev 1: bare detector, both warm-up variants (~20 min)
python3 vwapbb_fullstack.py    # rev 2: full cascade, four readings (~25 min)
```

---
---

# Revision 1 — superseded, retained as the evidence trail

*Rev 1 measured the bare detector with no filters and concluded the count was unmeasurable.
Rev 2 above shows the filters reconcile it. The rev-1 diagnostics remain valid and useful —
in particular the cluster-density measurement, which explains why the raw count is so high and
therefore why the cap ends up binding.*

## The bare detector

| Reading of the trigger rule | signals | per session |
|---|---|---|
| A — penetrate cluster top, any wick | 12,348 | 109.27 |
| B — penetrate cluster fully, any wick | 5,488 | 48.57 |
| C — penetrate fully + wick ≥ 50% of range | 3,906 | 34.57 |
| D — as C, plus cluster ≥3 levels | 2,795 | 24.73 |
| *Angus, discretionary, in-scope* | *19* | *1.00* |

Full 496-session run under reading A: **93.59/session**.

## Why the raw count is so high — the durable diagnostic

```
7,520  1-minute evaluation bars
13,807 clusters detected          -> 1.84 clusters per bar
median cluster: 2 levels, 6.6 pts span
```

**A cluster exists on essentially every bar.** Twelve candidate levels inside a 10-point
tolerance, on an instrument whose median 1-minute range is 9.5 points. Early in the session
the daily VWAP σ bands sit within a few points of each other, so the VWAP family clusters with
itself almost continuously.

This finding survives revision 2 and explains it: because clusters are ubiquitous, the stated
filters have to remove ~95% of candidates, and the last filter in the chain — the Vault cap —
ends up carrying the selection load.

## Distribution (bare detector, reading A, 496 sessions)

Zero sessions with 0, 1 or 2 signals. Max 183. Frequency flat year to year within 1%
(2023: 94.03, 2024: 93.16, 2025 Jan: 93.60), so the count is a property of the rule set, not a
regime. Time-of-day shape correct — 10:00–10:30 peak, midday sag — at the wrong magnitude.

## Sessions skipped

holiday/short 21, roll session 8, session after roll 8, mixed contract 6 — **43 of 539**;
496 scanned.

## Warm-up check (bare detector)

| variant | signals | per session |
|---|---|---|
| A — warmed from prior bars (as specified) | 46,422 | 93.593 |
| B — warmed from RTH bars only | 46,021 | 92.784 |
| difference | −401 | **−0.81%** |

Almost all of the effect sits in the 09:30 bucket (3,973 → 3,554, −10.5%). The pre-open bias
is real and precisely localised, and it is a second-order effect on a first-order problem.
No choice made between variants.

## Tripwire reconciliation

| correction | n at p₁ = 0.50 | tripwire on 539 sessions |
|---|---|---|
| ÷4 (largest axis after V3 struck) | 262 | **0.486** |
| ÷5 (before V3 struck) | 277 | 0.513 |

0.486 is current and used throughout.
