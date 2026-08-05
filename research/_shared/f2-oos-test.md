---
date: 2026-08-07
kind: STAGE 4 — pre-registered OUT-OF-SAMPLE test of H2 and H1-magnitude
spans: [ash10hazard, zxcked/Powell]
prereg: research/ash10hazard/strategies/ash-unicorn-sb-forward-protocol.md (2026-08-07)
script: scripts/f2_oos_test.py
log: f2-oos-trades.csv
verdict: BOTH HYPOTHESES FAILED
---

# H2 and H1-magnitude — tested out-of-sample. **Both failed.**

## HEADLINE

**H2 failed, and it failed in the OPPOSITE direction to the one pre-registered.**
**H1-magnitude held its direction but did not survive correction, at a third the claimed size.**

And this was **not** a null from a thin sample. The primary sample detects **d ≥ 0.58** at 80%
power. The in-sample effects being tested were **d ≈ 0.635 (H2)** and **d ≈ 0.596 (H1)** —
**both above what this test could see.** The sample had the power. The effects were not there.

---

## Why this is a real out-of-sample test

H2 and H1-magnitude were **generated on `ash-unicorn-sb`'s 29 trades** and, until now, had only
ever been evaluated on the same 29 trades that produced them. `zxck-10am-keyopen`'s decidable
flow-covered trades are a **different trader, a different setup, identical feature definitions**.

| sample | n | status |
|---|---|---|
| **PRIMARY — `zxck-10am-keyopen`, decidable only** | **115** | **independent** |
| ash-unicorn-sb flow-covered | 29 | **contaminated** — the hypotheses were born here |
| pooled secondary | 144 | **NOT an independent test**, reported separately and labelled |

The ~73 ambiguous-direction sessions are **excluded entirely** — undefined direction means
undefined outcome.

### All 115 have flow, not 102
`output/fp_minutes.parquet` is missing January 2026. Rather than regenerate a tracked artifact
shared with the canon work, this script builds its **own** per-minute frame from the raw
footprint files. The derivation was verified against `fp_minutes` on **31,271 minutes of July
2025**: `vol = A + B` and `delta = B − A`, both to **max|diff| 0.0**.

> ⚠️ **Side note for whoever owns `scripts/build_cvd_minute.py`:** its docstring says *"Side 'A' =
> ask-lift (buy aggressor)… delta = A − B"*. That is **inverted** relative to `fp_minutes`. The
> empirical check settles it in `fp_minutes`' favour — its `delta` correlates **+0.645** with the
> minute's (close − open) over 369,045 minutes. So **side B is the buy aggressor**. Not fixed
> here; out of scope.

---

## H2 — FAILED, in the opposite direction

**Pre-registered ordering:** median(win) < median(loss) < median(break-even).

### PRIMARY (out-of-sample), n = 115

| bucket | n | median `retrace_ratio` |
|---|---|---|
| win | 27 | **0.319** |
| loss | 59 | **0.226** |
| break-even | 29 | **0.262** |

**Observed ordering: loss < break-even < win.** The pre-registered ordering is not merely absent —
**winners have the HIGHEST retrace ratio**, which is the reverse of the claim.

- Jonckheere–Terpstra, one-sided against the pre-registered ordering: **z = −1.549, p = 0.9393**
- Winners vs losers alone: **Cliff's δ = +0.281** — against an in-sample **−0.635**. *The sign
  flipped.*

### SECONDARY (contaminated pool), n = 144
win 0.399 / loss 0.267 / break-even 0.313 — **same failure**, JT z = −0.952, p = 0.8296. Even the
sample that contains the trades the hypothesis was born on does not reproduce the ordering once
diluted.

### The original filter at its original threshold — not tuned

| arm | n | win% | avg R | expectancy | total | maxDD |
|---|---|---|---|---|---|---|
| unfiltered (primary) | 115 | 23.5% | −0.043 | **−0.127R** | −5.0R | 16.0R |
| **KEPT** `retrace_ratio < 1.0` | 104 | 22.1% | −0.067 | **−0.151R** | −7.0R | 19.0R |
| **REJECTED** `retrace_ratio ≥ 1.0` | 11 | 36.4% | +0.182 | +0.098R | +2.0R | 3.0R |

**The filter makes the card worse.** Keeping what H2 says to keep lowers expectancy from −0.127R
to −0.151R and *raises* max drawdown. **The threshold was not tuned** — 1.0 was the original cut
and it stays.

---

## H1-magnitude — direction held, effect did not

| bucket | n | median `F1_disp_delta` |
|---|---|---|
| win | 27 | **0.095** |
| loss | 59 | **0.072** |
| break-even | 29 | 0.023 |

Direction is **as pre-registered** (win > loss). But:
- Mann–Whitney one-sided **p = 0.0733** → **Holm-corrected 0.1466**
- **Cliff's δ = +0.196** against an in-sample **+0.596** — roughly **one third** the size, and in
  the "small" band rather than "large"

**Does not survive correction.**

---

## Correction and power

| test | p_raw | p_holm | |
|---|---|---|---|
| H1 magnitude | 0.0733 | **0.1466** | does not survive |
| H2 ordering | 0.9393 | **0.9393** | does not survive |

**Power — and this is the part that makes the failure meaningful.** With 27 winners vs 59 losers,
one-sided α = 0.05, the smallest detectable Cohen's d at 80% power is **0.58**. The effects being
tested were **0.635** and **0.596**. **This test could see effects of the size claimed, and did
not find them.** That is a genuine negative, not an underpowered shrug.

---

## VERDICTS

> ### H2 — **FAILED.** Reversed sign out-of-sample; the filter degrades the card at its original threshold.
> ### H1-magnitude — **FAILED.** Correct direction, one-third the effect, does not survive correction.

A failed out-of-sample test on n = 115 closes these questions far better than the original n = 29
ever could. **Both are retired.** Neither is to be resurrected by re-cutting this sample.

---

## One mechanistic observation — explanatory, NOT a rescue

The two books put `retrace_ratio` on **different scales**:

| | n | p25 | median | p75 | share ≥ 1.0 |
|---|---|---|---|---|---|
| `zxck-10am-keyopen` | 115 | 0.14 | **0.25** | 0.44 | **10%** |
| `ash-unicorn-sb` | 29 | 0.50 | **0.89** | 1.84 | **48%** |

Powell's retracements are far lighter relative to their displacement leg, so a 1.0 threshold
removes only 10% of his trades against ~half of ash's. **This does not rescue H2**: the ordering
test is rank-based and therefore scale-free, and it failed too — with the sign reversed. Recorded
because it is the honest reason the *filter form* is nearly vacuous here, not because it excuses
the result.

Same pattern on F1: median 0.067 with 65% positive on zxck, versus 0.282 with **100%** positive on
ash. The structural gates differ, so the flow signature differs.

---

## NEW, UNTESTED hypothesis — logged, not acted on

The **REJECTED** arm (`retrace_ratio ≥ 1.0`) shows 36.4% wins and +0.098R on **n = 11**.

**This is explicitly NOT a finding.** It is the mirror of a hypothesis that just failed, on eleven
trades, discovered *after* looking. Recording it as a future hypothesis is the honest disposal;
acting on it would be exactly the reframing this test was designed to prevent.

> **NH-1 `[UNTESTED]`** — on gap-entry setups whose retracement participation *exceeds* the
> displacement leg, win rate is higher rather than lower. **Requires a fresh sample. Must not be
> tested on any data used above.**

---

## What this does not touch

- `ash-unicorn-sb`'s **AM1 baseline is unchanged.** This tests two features, not the strategy.
- The **pre-registered forward protocol stands.** Its LOOK 1 was specified for forward trades; this
  is a different sample and does not consume it. But **the forward test's purpose is largely served
  now** — these hypotheses have been answered on 115 independent trades.
- **No filter is applied to any card.** `zxck-10am-keyopen` remains a card with an entirely
  negative expectancy bound, and no subset of it is presented as a profitable strategy.
