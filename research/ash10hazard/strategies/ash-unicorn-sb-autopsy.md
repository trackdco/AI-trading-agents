---
date: 2026-08-06
kind: winner/loser autopsy (Stage 5)
strategy: ash-unicorn-sb (AM1 09:45–10:15 ET only)
source logs: ash-unicorn-sb-raw-trades.csv (Stage 3, n=37) + ash-unicorn-sb-orderflow-trades.csv (Stage 4)
features written to: ash-unicorn-sb-autopsy-features.csv
script: scripts/ash_autopsy.py
---

> ## ⛔ SUPERSEDED IN PART — 2026-08-07 code fix. n 37 → 24.
> An adversarial audit found the **liquidity-sweep gate in `scripts/ash_raw_baseline.py` tested
> where price *was*, not whether it *crossed*** a level. 30 of the 37 trades below took that
> path. The baseline is now **n=24, 12W/5BE/7L, 50.0% WR, +0.708 avg R, +17.0R, maxDD 3.0R**,
> and flow coverage is **19**, not 29. The 24 survivors are a strict subset of the 37 and no
> surviving trade's R changed, so the *reasoning* here still applies — the *counts do not*.
> Current numbers: `research/_shared/baseline-comparison.md` and the card.

# Autopsy — what separates winners from losers in `ash-unicorn-sb`

## HEADLINE: nothing does. Not after correction, and not by a distance.

Ten features tested on **15 winners vs 12 losers**. The best raw p-value is **0.017**; after
Holm adjustment for 10 tests it is **0.169**. **Zero features survive.** Every single row
carries the thin-sample flag (`min(nW, nL) < 15`).

This is the outcome the brief named in advance as a real result, and it is the one the data
gave: *the edge, if there is one, is not in these features.*

---

## The table

n = 37 (winners 15, losers 12, break-even 10). Winners = R ≥ +2, losers = R ≤ −1.

| feature | winners vs losers | p_raw | p_holm | Cliff's δ | nW | nL | survives |
|---|---|---|---|---|---|---|---|
| `F2_retrace_ratio` | med **0.60** vs **1.27** | 0.017 | 0.169 | **−0.635** | 13 | 8 | **no** |
| `F1_disp_delta` | med **0.33** vs **0.23** | 0.025 | 0.223 | **+0.596** | 13 | 8 | **no** |
| `news_day` | 33% vs 17% | 0.326 | 1.000 | — | 15 | 12 | no |
| `news_in_window` | 7% vs 0% | 0.362 | 1.000 | — | 15 | 12 | no |
| `dist_to_level_R` | med 1.53 vs 0.98 | 0.591 | 1.000 | +0.122 | 15 | 12 | no |
| `direction_long` | 80% vs 75% | 0.756 | 1.000 | — | 15 | 12 | no |
| `risk_pts_v` | med 22.25 vs 29.50 | 0.845 | 1.000 | −0.044 | 15 | 12 | no |
| `entry_min_into_window` | med 15.0 vs 12.5 | 0.884 | 1.000 | +0.033 | 15 | 12 | no |
| `atr_pct` | med 0.59 vs 0.45 | 0.922 | 1.000 | +0.022 | 15 | 12 | no |
| `htf_aligned` | **33% vs 33%** | 1.000 | 1.000 | — | 15 | 12 | no |

Cliff's δ convention: |δ| < 0.15 negligible, 0.15–0.33 small, 0.33–0.47 medium, > 0.47 large.

**Seven of the ten context features are in the negligible band or are literally identical.**
`htf_aligned` is 5/15 vs 4/12 — 33% against 33%, a difference of zero. Whatever decides these
trades, it is not the 1-hour trend, not volatility regime, not how far the level sat from
entry, not stop size, not the minute inside the window, not direction, and not the news
calendar.

---

## Why "no separator" here is weaker evidence than it looks — and the honest read

Two things must be said together, and the second is usually left out.

**1. The strongest result in the table is exactly what noise produces.**
Simulating the null 20,000 times — ten independent rank tests on 15-vs-12 random data — the
best-of-ten p-value comes in at **≤ 0.017 fifteen percent of the time**, and its median is
**0.071**. So an autopsy of this size, run on data with no structure at all, would *typically*
hand back a "finding" at p ≈ 0.07 and would beat our actual best result once every seven
attempts. The table's top row is not surprising; it is the expected shape of a search this
wide on a sample this thin.

**2. The test could only ever have seen enormous effects.**
At 15 vs 12 with 80% power and α = 0.05:

| what we were looking for | smallest we could have detected |
|---|---|
| continuous feature (Cohen's d) | **d = 1.09** — beyond Cohen's "large" (0.8) |
| binary feature vs a 33% base | the other group would need **87%** |

A filter that lifted win rate from 33% to, say, 55% — genuinely worth having — is invisible at
this sample size. **"Nothing separated" therefore means "no gigantic effect is present." It
does not mean "no useful effect is present."** Reporting the nulls as if they closed the
questions would be as wrong as reporting the 0.017 as a discovery.

---

## The two features that did move — and why neither is a discovery

`F1_disp_delta` and `F2_retrace_ratio` are the only large effect sizes in the table. **Both
are the Stage-4 order-flow features.** They were built to separate winners from losers, they
were tested for that in Stage 4, and finding them at the top here is confirmation of a known
result on a subset of the same trades — not a new signal. They are also the two thinnest rows
(nW=13, nL=8) because flow data starts 2025-06-01.

### One genuinely new observation, inside a known feature

Stage 4 tested F1 as a **sign** test (delta > 0) and it was **vacuous — it removed zero
trades**, because the MSS gate already guarantees a directional break. But the autopsy is
looking at **magnitude**, and the magnitudes do differ:

```
F1 winners: 0.20 0.23 0.27 0.30 0.30 0.31 0.33 0.36 0.36 0.44 0.64 0.94 1.01
F1 losers : 0.07 0.14 0.20 0.22 0.24 0.24 0.30           0.85
```

Seven of eight losers sit at or below 0.30; the winners' upper half runs to 1.01. Cliff's
δ = +0.596. **A magnitude threshold is a different hypothesis from a sign threshold**, and
Stage 4 did not test it. That is the one thing in this autopsy that is new.

It is also built on **eight losers**, one of whom (0.85) sits in the winners' range. Move that
single trade and the picture softens considerably.

### What F2 actually sorts — and it is not wins from losses

Reading F2 across all three outcome buckets rather than two:

| outcome | n | median F2 |
|---|---|---|
| win | 13 | **0.60** |
| loss | 8 | 1.27 |
| **break-even** | 8 | **2.35** |

The ordering is win < loss < **break-even**. F2 is not ranking trades by R — a BE trade (0R)
is a *better* outcome than a loss (−1R), yet it sits at the far end of the scale. What high
retracement participation predicts is that **the trade stalls**, not that it loses.

This explains the Stage-4 number that looked odd at the time: F2 removed 14 trades and added
only **+2R** of total profit. It was mostly deleting break-evens. That is worth something on a
funded account with a consistency rule, and close to nothing in raw R — which is what the
Stage-4 write-up concluded, now with a mechanism behind it.

---

## Day of week — descriptive only, and it is noise

| day | n | mean R | wins |
|---|---|---|---|
| Mon | 9 | +1.00 | 5 |
| Wed | 10 | +0.80 | 5 |
| Fri | 5 | +0.60 | 2 |
| Tue | 6 | +0.17 | 2 |
| **Thu** | 7 | **−0.43** | **1** |

Thursday is the tempting one. Against the 40.5% base rate, 1 win in 7 has raw p = **0.152**,
and **0.758** once corrected for having looked at five days. Monday's 5-in-9 is p = 0.278 raw,
1.000 corrected. **No day is distinguishable from the others.** Cells of 5–10 trades cannot
support a day-of-week rule and this one is recorded so that nobody re-derives it later and
believes it.

---

## Proposed filters

The brief asked for 1–3 mechanical filters **drawn only from features that separated**.
**Strictly applied, that instruction yields zero filters**, because no feature separated after
correction. What follows is therefore offered as **hypotheses to test on data we do not have
yet** — explicitly not as filters to run.

I am **declining to propose any filter from the context features** (`htf_aligned`, `atr_pct`,
`dist_to_level_R`, `entry_min_into_window`, `risk_pts_v`, `news_*`, `direction`, `dow`). Their
effect sizes are negligible or nil, and inventing a story for a 0.59-vs-0.45 ATR median would
be exactly the fabrication the brief forbids.

### H1 — displacement delta **magnitude** (not sign) — *highest value, because it is new*

> Skip the setup when normalised displacement delta is in the bottom half of its distribution.

- Pre-specified cut: **the running median of prior setups' F1** (0.282 on the current sample) —
  the median is the least-searched split that exists; no threshold sweep was run and none
  should be.
- Expected effect **if the observed δ = +0.596 is real**: it would remove ~7 of 8 losers'
  worth of low-delta setups. **On this sample that estimate is circular and inflated by
  selection — treat the direction as the claim, not the magnitude.**
- Blocking issue: **8 losers**, and one of them contradicts the pattern.

### H2 — retracement participation, restated as a stall filter

> F2 < 1.0, as already implemented in Stage 4 — but justified as *removing trades that go
> nowhere*, not as *removing losers*.

- Already tested: 44.8% → 73.3% WR, **+2R total**. The restatement doesn't change the numbers,
  it changes what to expect from them: **trade-count reduction and drawdown smoothing, not
  profit growth**.
- Blocking issue: n=15 in the kept arm, 4 trades in the 2026 era.

### H3 — the combination, and why it is not proposed

F1-magnitude and F2 would leave roughly **8–10 trades** across 16 months. Below any usable
floor, and the interaction cannot be estimated at all on 21 flow-covered trades. **Not
proposed.**

---

## What this cannot do, stated plainly

1. **Any filter found here is circular on this data by construction.** It was selected because
   it fit these 37 trades. Re-running the backtest with it and reporting the improvement would
   be measuring the fit, not an edge. **No filter from this autopsy has been applied to the
   baseline, and none should be until it is tested on trades that did not produce it.**
2. **These are 4 new arms** (F1-magnitude × 2 eras, plus the two already-logged F2 arms) that
   belong in the merged trial ledger before anything here is graded. At N = 58 the deflation
   bar is **+0.5636**; nothing in this document has been measured against it.
3. **The break-even bucket was excluded from the winner/loser comparison** (10 of 37 trades,
   27% of the sample). It is reported separately above because it turned out to carry the most
   information — but the headline tests are on 27 of 37 trades, not all of them.

---

## What would settle it

| need | why | unblocks |
|---|---|---|
| **Aggressor-tagged NQ trades, 2025-01-01 → 2025-05-31** | flow starts 2025-06-01, costing 8 of 37 trades and leaving only **8 losers** with flow | H1 goes from 8 losers to ~12 |
| **Forward sample, ~18 months** | at **27 trades/year**, 80% power for a *large* (d = 0.8) effect needs **~49 trades**; d = 0.6 needs **~87** (3.2 years) | the only non-circular test of H1 |
| **ES 1-minute** | still the largest gap — his entry fires on the ES tap, and Stage 4 showed NQ delta cannot substitute | the model as actually taught |

**Nothing in this document is a verdict.** No trial was graded, no deflation bar was applied,
and the sealed 2023/24 span was not touched.

---

# REVISION 2026-08-07 — backfill audit: sample unchanged, autopsy not re-run

`scripts/ash_flow_coverage_audit.py` · full detail in `ash-unicorn-sb-orderflow.md`

**The backfill added 0 trades.** Every trade inside the owned aggressor-tagged span
(2025-06-01 → 2026-07-19) already had its derivations; the 8 without flow all sit *before*
every non-sealed footprint file we hold. **29 flow-covered was a calendar boundary, not a
processing shortfall.** The winner/loser split is unchanged at **15 v 12** overall and
**13 v 8** on the flow-covered subset.

Nothing above is superseded. The Holm result, the power floor (d = 1.09; 87% for a binary
feature at a 33% base) and the null simulation (best-of-10 p ≤ 0.017 fifteen percent of the
time) all describe this same sample and still hold.

## The two live hypotheses were NOT tested — deliberately

H1 (F1-magnitude) and H2 (F2-as-stall-filter) were generated **on these 29 trades**. The only
honest test of either is behaviour on trades that did not produce them. The backfill added
**zero such trades**, so:

> **There is no quasi-out-of-sample set. Re-testing H1 and H2 here would measure the fit that
> created them, not an edge.**

Re-running would have returned δ = +0.596 for H1 and the 0.60 / 1.27 / 2.35 three-bucket
medians for H2 — identical to the numbers above, because they are the same trades — and
reporting them a second time would read as replication. It is not.

## What actually moves this forward

| | |
|---|---|
| **Forward accumulation** | ~9 months (+20 trades) to reach n ≈ 49, the 80%-power bar for a *large* effect. This is the only path that yields a genuinely out-of-sample test of H1/H2. |
| **Databento `GLBX.MDP3` trades, 2025-03-01 → 2025-05-31** | recovers the 8 pre-span trades (3 losses, 2 wins, 2 BE, 1 loss), taking flow-covered to 37 and losers-with-flow from 8 to ~12. Still short of 49, and still in-sample for H1/H2. |
| **ES 1-minute** | unchanged as the largest gap in the model as taught. |

**Verdict unchanged: plausible but unconfirmed, needs forward data.** The backfill pass
established that this is not a data-processing problem that more diligence can solve — the
sample is at its ceiling within what we own.

---

# 2026-08-07 — H1 and H2 are now PRE-REGISTERED

`ash-unicorn-sb-forward-protocol.md` · log `ash-unicorn-sb-forward.csv` ·
logger `scripts/ash_forward_log.py`

Both hypotheses above are locked for a forward out-of-sample test: directions stated in
advance (H1 winners higher `F1_disp_delta`; H2 three-bucket order win < loss < break-even on
`F2_retrace_ratio`), definitions frozen to the existing code, two pre-planned looks at
n_forward = 20 and 46, α = 0.0125 per hypothesis × look, decision rule written before any
data exists. **The forward span begins 2026-08-08** and the logger refuses earlier dates.

**H1 and H2 must not be tested on any set that includes these 29 trades.** They were generated
here; the protocol is the only place they can be confirmed.
