# London conviction tiers — which sizing shape is best?

**Fit only. Sealed 2023/24 never loaded.**

London's wall score is BINARY (W or FAR; ROOM killed as noise, ASIA as backwards, and W/FAR are one signal at r=0.834), so there is no conviction ladder and 'funded sizing' was undefined. Every London figure quoted before this doc is flat 1 NQ lot — $20/pt, $255 median and $291 mean risk per trade, i.e. **1.7x** the lucid tier-1.0 unit of $150 on the median and **1.9x** on the mean. So '+$22,795' was never a funded-sizing number.

Declared grid, fixed upfront: ratio r = tier(both W+FAR)/tier(exactly one) in {1, 1.5, 2, 3} — 4 cells, shrinkage charge -0.014 R. Risk-band tiering is reported as a pre-rejected fifth shape (circular: risk is R's denominator).

## Part 1 — shape, at matched total risk

Trade set PINNED at 213 trades (frozen arm: floor 9.5pt, window-end lifetime, uncapped; day stop disabled here so every shape scores the SAME trades and only the weights move). Continuous contracts, so total deployed risk is exactly $150 x 213 = **$31,950** for every row below.

Cells: **both W+FAR n=153**, **exactly one n=60**. Mean R overall **+0.464**.

| cell | n | WR | mean R | 2025 n / R | 2026 n / R |
|---|---|---|---|---|---|
| both W+FAR | 153 | 57% | +0.620 | 54 / +0.489 | 99 / +0.692 |
| exactly one | 60 | 47% | +0.066 | 26 / +0.147 | 34 / +0.004 |

**Power:** the one-only cell must carry >= 25 trades per era to be called. Both eras clear it, but only just — treat the one-only mean R as a wide interval, not a point.

| ratio r = tier(both)/tier(one) | net | maxDD | net/maxDD | worst trade | 2025 net | 2026 net |
|---|---|---|---|---|---|---|
| **1.0 (flat)** | $+14,820 | $1,251 | 11.8 | $-158 | $+4,531 | $+10,290 |
| 1.5 | $+16,139 | $961 | 16.8 | $-174 | $+4,867 | $+11,241 |
| 2 | $+16,906 | $970 | 17.4 | $-184 | $+5,068 | $+11,787 |
| 3 | $+17,762 | $1,044 | 17.0 | $-194 | $+5,297 | $+12,388 |
| _inf (both only — a GATE change, not a tier)_ | _$+19,809_ | _$1,220_ | _16.2_ | _$-220_ | _$+5,864_ | _$+13,798_ |
| _risk-band 3-tier (PRE-REJECTED, circular)_ | _$+16,802_ | _$1,179_ | _14.3_ | _$-236_ | — | — |

**On r = inf.** Dropping the one-only trades entirely is the ratio family's limit and it scores $+19,809 at matched risk, but it is NOT a sizing decision — it redefines the gate from `W or FAR` to `W and FAR`, which is a structural hypothesis and would take pre-registration multiplicity from 2 to 3. It was also added AFTER the first look at the declared four, so quoting it as the winner would be exactly the selection inflation the stage-3 curve exists to charge for. Measured and recorded here; it is not selected, and if it is ever promoted it goes in as a declared structural hypothesis with its own alpha.

**Best ratio on net at matched risk: r = 3** ($+17,762 vs flat $+14,820, **$+2,941**). Charged shrinkage at the declared breadth of 4 cells: **-0.014 R** per trade, i.e. $-447 off the net -> **$+17,315** forward.

## Part 2 — permutation null on the both-vs-one separation

H0: the cell label carries no size-relevant information. Statistic: net at r=3 minus net at r=1 (flat), matched risk, same trades. The label is shuffled **within era** (2,000 shuffles, seeded 20260730) so era composition cannot supply the effect.

| span | observed advantage | null mean | null p95 | p-value |
|---|---|---|---|---|
| 2025 | $+766 | $-24 | $+1,053 | **0.1165** |
| 2026 | $+2,099 | $+21 | $+1,817 | **0.0210** |
| both eras | $+2,941 | $+36 | $+2,119 | **0.0085** |

**Jackknife leave-one-month-out:** the r=3 advantage keeps its sign in **14/14** months-removed refits. Not month-dependent.

**Verdict on shape:** pooled p=0.0085, but per-era p = 0.1165 / 0.0210 — it is NOT independently significant in both eras, so the ladder is a secondary hypothesis, not the frozen primary.

## Part 3 — scale, under the real funded constraints

NY = the verified lucid canon (920 trades, 230 days, $+90,015). Shared $800 daily budget, chronological and causal — London fills 03:02-05:54 ET and draws first, so it can crowd NY out (though not by the mechanism it looks like — see below). Integer MNQ contracts, day stop $400 on sized dollars, 2,000 MC paths keeping both books in the same day-draw.

**Sanity: NY-alone P(bust) = 2.4%** (must be 0.5-4%). PASS

**Baseline correction.** NY replayed under the same $800 rule with an EMPTY London book nets **$+90,249**, against $+90,015 for the raw book: the budget rule blocks NY trades worth $+234 on its own. Every 'vs NY-alone' figure below is measured against the REPLAYED baseline, so that offset is not credited to London. The first run of this script used the raw sum and every delta carried it — visible as an identical $+234 in the zero-edge column, where London contributes exactly nothing.

**Candidate set restricted to tiers that EXIST on the lucid ladder {0.5, 1, 1.5, 2}.** A first pass allowed ratio-preserving pairs off the ladder (3.0/1.0 = $450/$150 of risk) and that pair won — but tier 3.0 is not available on a profile whose ceiling is $300, so it was not a London decision at all, it was a request to change the NY profile. Excluded.

| London sizing | trades | LON net | mean risk/trade | NY blk | combined net | vs NY-alone | per $1 risk | P(bust) | med withdrawn |
|---|---|---|---|---|---|---|---|---|---|
| _NY alone_ | 0 | $0 | — | 0 | $+90,249 | $0 | — | **2.4%** | $92,552 |
| flat 0.5 | 213 | $+6,288 | $60 | 25 | $+97,003 | **$+6,754** | $112 | 1.2% | **$92,759** |
| flat 1.0 | 212 | $+13,545 | $136 | 34 | $+105,570 | **$+15,321** | $113 | 1.1% | **$101,680** |
| flat 1.5 | 199 | $+18,978 | $211 | 39 | $+109,095 | **$+18,846** | $89 | 1.1% | **$104,650** |
| flat 2.0 | 197 | $+25,462 | $287 | 53 | $+114,823 | **$+24,574** | $86 | 1.6% | **$110,406** |
| 1.5 / 0.5 | 202 | $+18,303 | $166 | 39 | $+108,419 | **$+18,170** | $109 | 1.1% | **$104,375** |
| 1 NQ lot (status quo, OFF-ladder) | 187 | $+22,795 | $280 | 58 | $+109,060 | **$+18,811** | $67 | 1.6% | **$105,021** |

### P(bust) cannot decide this, and neither can a haircut

Every config sits at or below NY-alone's 2.4%: London is profitable, its per-trade risk is small against a $2,000 trailing line, and the shared $800 budget already caps daily exposure. A proportional haircut is no better — it multiplies every candidate by the same factor, so the ranking survives by construction and a rule of the form 'maximise withdrawn subject to a haircut test' cannot lose. Both degenerate to 'pick the biggest', which is not a finding.

What CAN rank scales is London's true mean R landing below what the fit measured. The mechanism is worth stating precisely, because it is not what it looks like: under the budget rule a trade's risk gates its OWN admission, but only REALIZED LOSSES accumulate against the $800. London therefore does not crowd NY by being big — it crowds NY by LOSING while being big. At mean R = 0 the losses are real even though the net is not, and the crowding cost scales with the size chosen. That is where a large unit is punished, and it is the only place it is.

### Downside scenarios — London's true mean R, dispersion preserved

Fit measures mean R = **+0.471** on the taken book. Each column forces the mean to the stated value and re-runs the entire combined replay and Monte Carlo. Figures are London's contribution over the replayed NY-alone baseline.

| London sizing | R=fit | R=+0.30 | R=+0.20 | R=+0.10 | R=0.00 | R=-0.10 | R=-0.25 |
|---|---|---|---|---|---|---|---|
| flat 0.5 | $+6,754 | $+5,069 | $+3,788 | $+2,772 | $+1,491 | $-226 | $-2,149 |
| flat 1.0 | $+15,321 | $+8,937 | $+2,915 | $+463 | $-4,890 | $-7,120 | $-16,512 |
| flat 1.5 | $+18,846 | $+9,720 | $+6,299 | $+1,736 | $-2,158 | $-8,501 | $-18,736 |
| flat 2.0 | $+24,574 | $+7,914 | $+806 | $-3,451 | $-7,683 | $-13,542 | $-15,812 |
| 1.5 / 0.5 | $+18,170 | $+11,175 | $+8,477 | $+2,382 | $+1,516 | $-7,313 | $-11,330 |
| 1 NQ lot (status quo, OFF-ladder) | $+18,811 | $+3,424 | $+3,738 | $-1,384 | $-6,419 | $-12,401 | $-22,880 |

Same scenarios, P(bust):

| London sizing | R=fit | R=+0.30 | R=+0.20 | R=+0.10 | R=0.00 | R=-0.10 | R=-0.25 |
|---|---|---|---|---|---|---|---|
| flat 0.5 | 1.2% | 1.4% | 1.7% | 1.7% | 2.1% | 2.5% | 3.1% |
| flat 1.0 | 1.1% | 1.1% | 2.2% | 2.7% | 3.8% | 4.9% | 9.0% |
| flat 1.5 | 1.1% | 2.5% | 3.0% | 4.0% | 5.4% | 8.4% | 14.7% |
| flat 2.0 | 1.6% | 4.0% | 7.3% | 9.8% | 12.1% | 17.3% | 21.4% |
| 1.5 / 0.5 | 1.1% | 1.8% | 2.2% | 3.3% | 4.3% | 6.7% | 8.6% |
| 1 NQ lot (status quo, OFF-ladder) | 1.6% | 4.4% | 5.8% | 7.8% | 12.4% | 14.9% | 26.6% |

### Break-even mean R

How far can London's true mean R fall before it stops adding anything to the combined account? Scanned in 0.01 steps down from the fit value; not solved analytically, because the blocked set depends on the P&L.

| London sizing | break-even mean R | headroom below fit | cost at R = 0.00 | cost at R = -0.25 |
|---|---|---|---|---|
| flat 0.5 | -0.08 | 0.55 R | $+1,491 | $-2,149 |
| flat 1.0 | +0.08 | 0.39 R | $-4,890 | $-16,512 |
| flat 1.5 | +0.06 | 0.41 R | $-2,158 | $-18,736 |
| flat 2.0 | +0.17 | 0.30 R | $-7,683 | $-15,812 |
| 1.5 / 0.5 | +0.04 | 0.43 R | $+1,516 | $-11,330 |
| 1 NQ lot (status quo, OFF-ladder) | +0.10 | 0.37 R | $-6,419 | $-22,880 |

**Selection rule.** (a) both tiers on the lucid ladder — off-ladder sizes are a profile change, not a London decision; (b) P(bust) no more than 0.5pp above NY-alone (ceiling 2.9%) at a declared adverse scenario; (c) among survivors, maximise median withdrawn.

The binding scenario is declared as **mean R = +0.20**, i.e. roughly HALF the fit edge of +0.471 — the same margin of safety stage 4's haircut sensitivity already used. It is not chosen for its answer: enforcing the ceiling at the worst column instead (R = -0.25, London badly negative where the fit measures +0.47) is a rule that only a token size can pass, and it returns a spurious null. Here is the pick under EVERY scenario, so the choice is visible:

| ceiling enforced at | configs clearing | pick | med withdrawn (fit) | contribution (fit) |
|---|---|---|---|---|
| R = fit | 5/5 | flat 2.0 | $110,406 | $+24,574 |
| R = +0.30 | 4/5 | flat 1.5 | $104,650 | $+18,846 |
| R = +0.20 | 3/5 | **1.5 / 0.5** | $104,375 | $+18,170 |
| R = +0.10 | 2/5 | flat 1.0 | $101,680 | $+15,321 |
| R = 0.00 | 1/5 | flat 0.5 | $92,759 | $+6,754 |
| R = -0.10 | 1/5 | flat 0.5 | $92,759 | $+6,754 |
| R = -0.25 | 0/5 | _none — London flat 0.5 or not at all_ | — | — |

### Answer

**1.5 / 0.5** — 3 of 5 on-ladder configs clear the ceiling at R = +0.20, and this is the largest of them by median withdrawn.

| | fit | R = +0.20 | R = 0.00 | R = -0.25 |
|---|---|---|---|---|
| contribution | $+18,170 | $+8,477 | $+1,516 | $-11,330 |
| P(bust) | 1.1% | 2.2% | 4.3% | 8.6% |

Median withdrawn $104,375, mean risk $166/trade, break-even mean R +0.04 — 0.43 R of headroom below the fit measurement.

### Why this beats the flat tiers either side of it

The pick is not simply the biggest survivor — it is a different SHAPE, and the comparison that matters is against the flat tiers it sits between on mean risk per trade.

| config | mean risk | contribution fit | contribution R=+0.20 | contribution R=0 | P(bust) R=0 | break-even mean R |
|---|---|---|---|---|---|---|
| flat 0.5 | $60 | $+6,754 | $+3,788 | $+1,491 | 2.1% | -0.08 |
| flat 1.0 | $136 | $+15,321 | $+2,915 | $-4,890 | 3.8% | +0.08 |
| **1.5 / 0.5** | $166 | $+18,170 | $+8,477 | $+1,516 | 4.3% | +0.04 |
| flat 1.5 | $211 | $+18,846 | $+6,299 | $-2,158 | 5.4% | +0.06 |
| flat 2.0 | $287 | $+24,574 | $+806 | $-7,683 | 12.1% | +0.17 |

Read the two halves of that table differently, because they are not equally precise. **The contribution columns are deterministic** — one chronological replay of a fixed book, no sampling — and there the ladder genuinely dominates both flats either side of it: it holds $+8,477 at half the fit edge where flat 1.5 holds $+6,299 on 27% more risk per trade, and it is still positive at mean R = 0 where both flat 1.0 and flat 1.5 have gone negative.

**The P(bust) columns are Monte Carlo estimates** at 2,000 paths, so their standard error near 3% is about 0.4pp — call it +/-0.8pp at 2 sigma. Gaps of a few tenths are noise, and two consequences follow honestly. First, the ladder's 4.3% at R = 0 is NOT better than flat 1.0's 3.8% — bust risk tracks size, and the ladder carries more of it than flat 1.0 does. It does not degrade like something smaller; it degrades like its own size while paying like something bigger. Second, flat 1.5 misses the ceiling at R = +0.20 by 0.1pp, which is well inside that noise — so the bust screen does NOT separate the ladder from flat 1.5, and anyone reading it as the deciding evidence is over-reading it.

So the answer rests on the deterministic column, not the sampled one: at equal or lower risk per trade the ladder retains more of its contribution as the edge decays, because the size sits where the edge was measured and the weak cell stays small. The bust ceiling is a screen that rules out flat 2.0 decisively (7.3% at R = +0.20, far outside noise); it is not what picks the winner.

### Integer-contract rounding

Floor-with-1-minimum truncates the intended unit. At small tiers that is not a rounding error, it is the position.

| tier | intended risk | actual mean risk | mean contracts | trades forced to the 1-contract minimum |
|---|---|---|---|---|
| flat 0.5 | $75 | $60 | 2.4 | 32/213 |
| flat 1.0 | $150 | $136 | 5.3 | 1/212 |
| flat 1.5 | $225 | $211 | 8.1 | 0/199 |
| flat 2.0 | $300 | $287 | 11.1 | 0/197 |

## Reconciling Part 1 with Part 3

The two parts report different nets for the same nominal tier and that is expected, not a contradiction. Part 1 pins 213 trades with the day stop OFF and continuous contracts, so shape is the only moving part. Part 3 restores the real machinery: the $400 day stop on sized dollars (which removes trades, and removes MORE of them at larger tiers) and integer MNQ contracts (which truncate the unit downward). Flat 1.0 therefore reads $+14,820 on 213 trades in Part 1 and $+13,545 on 212 in Part 3. Earlier sessions quoted **187 trades** — that is the 1-NQ-lot set, whose larger unit trips the day stop more often; Part 3 reproduces it exactly, which is the cross-check that this script is sizing the same book everything else was measured on.

## What this settles

Shape and scale are answered separately and the answers do not have to agree: a shape can be real and still not be worth the drawdown it buys, and the scale that maximises withdrawn cash is set by the shared budget and the trailing line, not by mean R. The pre-registration takes the frozen primary from Part 3's selection rule and the ladder from Part 1/2 as the single declared secondary, keeping multiplicity at 2.
