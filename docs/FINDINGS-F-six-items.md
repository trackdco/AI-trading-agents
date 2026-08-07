# FINDINGS — SIX ITEMS (2026-08-07)

Order respected: 1–3 completed before the item-4 declaration was written.
Item 5 was done first because it costs something every day it waits. Item 6
was declared blind before it ran. **No holdout row has been read.**

---

## 5. FLOW RECORDER MOVED TO THE SEVEN-LOCUS GRAMMAR — done first

The recorder imported `day_rows`; it now imports the level-census version
and logs **all seven loci** with the twelve flow features.

```
before: 18-26 triggers/session (bbma15 only)
after: 122-141 triggers/session across 7 loci — ~5x coverage
replay certification PASS on 2026-06-02 and 2026-03-10:
  100% flow coverage, every bbma15 row still bit-identical to the M-TABLE
```

This was the right call and nearly a costly miss: E1 found the edge at
break-of-VAL and break-of-VWAP−1, so a single-locus recorder would have
accrued a year of forward data on the grammar that *lost*. Forward data is
the only validation route for any selection layer, so the wrong grammar
would have been unrecoverable.

The builder also now emits `t_entry` / `t_3r` / `t_exit` — concurrency is
not computable without exit timestamps, and item 3 needs them. Outcomes are
bit-identical to the previous build (33,461/33,461 rows).

## 1. DIRECTION SKEW — real, measured, and it changes the holdout's meaning

Monthly book EV against the month's NQ return, 14 fit months:

| book | Pearson | Spearman | slope (R per 1% NQ) | 95% CI |
|---|---|---|---|---|
| val | −0.495 | −0.508 | −0.0156 | [−0.0255, +0.0007] |
| vwap_m1 | −0.582 | −0.574 | −0.0169 | [−0.0255, −0.0037] |
| **UNION** | **−0.624** | **−0.626** | **−0.0155** | **[−0.0207, −0.0063]** |

**Confirmed: part of the +0.230R IS a downside-continuation premium.** The
union slope's CI is clear of zero. The two worst months are the two biggest
melt-ups (2026-04, NQ +15.3% → EV +0.019; 2026-05, +10.5% → +0.067).

**But it is not purely directional.** Split by month sign:

```
up months    (9)  n=1,004  EV +0.183 [+0.076,+0.290]  CI clear of zero
down months  (5)  n=  502  EV +0.323 [+0.186,+0.460]
```

So: a level effect that survives in rising markets, **plus** a downside
enhancement. In strong rallies the book goes flat, not negative.

**Long-side power, stated explicitly as requested:**

| book | side | n | EV | day-boot 95% CI | MDE @80% |
|---|---|---|---|---|---|
| val | long | 189 | +0.223 | [−0.021,+0.470] | 0.346 |
| vwap_m1 | long | 297 | +0.151 | [−0.036,+0.343] | 0.270 |
| UNION | long | 411 | +0.166 | [+0.002,+0.329] | 0.230 |
| UNION | short | 1,095 | +0.254 | [+0.154,+0.351] | 0.119 |

Every long cell is positive; the union's just clears zero. The long-side
MDE (0.23–0.35R) sits at or above the observed short-side EV, so **the
long side is absence of evidence, not evidence of absence.** It cannot be
called dead on this data.

**Consequence, now written into the holdout declaration (R5):** the sealed
span is bull-heavy, i.e. adversarial for this book. A pass there is strong
evidence with no surviving regime caveat. A fail is *ambiguous* and is
pre-committed to be recorded as such — it cannot separate "no edge" from
"edge, wrong regime". Declaring that in advance removes the temptation to
discover the excuse afterwards.

## 2. THE COMPOSITE BOOK, SCORED ON GRADUATION

Populations barely collide — 3.6% share a (day, minute, side), 122 fire at
the same minute at all.

| book | fights | /day | EV | H2-2025 | H1-2026 |
|---|---|---|---|---|---|
| union_break | 1,506 | 5.16 | +0.230 | +0.223! | +0.238! |
| reject | 1,830 | 6.27 | +0.149 | +0.139! | +0.162! |
| **COMPOSITE** | **3,336** | **11.42** | **+0.186** | **+0.177!** | **+0.196!** |

P(graduate), the objective the verified 5-payout cap imposes:

| book | policy | GRAD | net | P(death) | t-1st-$ |
|---|---|---|---|---|---|
| COMPOSITE | cushion k=.05 | **100.0%** | $8,916 | 26.0% | **31d** |
| union_break | cushion k=.05 | 99.7% | $8,854 | 11.2% | 49d |
| reject | cushion k=.05 | 92.3% | $8,614 | 43.4% | 62d |

Ranking survives a −20% EV haircut (98.7 / 96.8 / 79.4). **The composite
wins, and it halves time-to-first-dollar** — the dilution concern was real
in EV terms (+0.186 vs +0.230) but graduation depends on frequency too, and
frequency wins here. Cost: composite death rate 26% vs union-break's 11%,
which is acceptable only because a death is cheap (~$95–130 + downtime) and
graduation is the objective.

## 3. RISK SPINE — the failure mode is NOT what the old canon's was

Measured on the composite (11.42/day, median 11, max 24):

```
concurrency at entry:  0 open 68.1% | 1 open 23.6% | 2 open 6.1%
                       3 open 1.9%  | 4 open 0.2%  | max simultaneous 5
peak R-at-risk/day:    p50 2.0 | p90 4.0 | p95 4.0 | max 5.0
days exceeding the canon's 5.33R budget: 0 of 291 (0.0%)
```

**The in-flight term is not load-bearing for this book.** The old canon
needed it because its worst days were 4–8 *overlapping* losers whose losses
were unrealised when later entries fired. This book's worst days are
**sequential grind**:

```
2025-07-24  dayR -14.52 | 20 trades, 18 losers | peak R-at-risk 3.0
2026-05-19  dayR -12.00 | 13 trades, 13 losers | peak R-at-risk 2.0
2025-10-30  dayR -11.81 | 18 trades, 17 losers | peak R-at-risk 4.0
```

Eighteen losers out of twenty, never more than three on at once. A
concurrency cap would not have touched these days. **The binding constraint
is a daily loss cap, not an exposure cap.**

Pricing the rule anyway (it is still correct to have, and it is what
bounds the tail):

| rule | trades kept | dayR | worst day | P(death) | GRAD |
|---|---|---|---|---|---|
| none (current spec) | 100.0% | +2.122 | −14.52 | 26.0% | 100.0% |
| realised-loss only @5.33R | 89.7% | +1.948 | −6.27 | 24.9% | 99.9% |
| in-flight incl. @5.33R | 88.7% | +1.910 | −5.56 | 26.2% | 99.9% |
| **in-flight incl. @3.00R** | **64.1%** | +1.659 | **−3.54** | **16.1%** | 99.8% |

**Recommended: in-flight-inclusive budget at 3.00R.** It costs 0.2pp of
graduation and 22% of daily R, and buys a worst day of −3.54R instead of
−14.52R with account-death down from 26% to 16%. Note that because
concurrency is low, realised-only performs nearly as well — the in-flight
term is cheap insurance rather than the mechanism, and should be kept for
exactly that reason.

**This spine must exist before anything is armable, and it now does.**

## 6. SWEEP-RECLAIM — THE GRAMMAR IS VINDICATED, E3 IS REVERSED

Declared blind (451c8fd3) with the definition taken from the trader's own
words: *the reference extreme is the trader's own stop level.*

| cell | X=0.5W EV | fights/day | both eras clear | verdict |
|---|---|---|---|---|
| (a) standalone sweep+reclaim | +0.070 | 7.81 | no | park — base rate published |
| **(b) sweep of the OWN STOP** | **+0.175** | **12.79** | **yes, at all four X** | **FOLLOW-UP EARNED** |

Per the interpretation table declared in advance: **"(a) fails, (b) passes:
the prior stopped attempt is load-bearing — the edge is in the re-entry
context, not the pattern."**

E3 called plain and sweep-filtered re-entry dead. That verdict was against
a definition that provably did not capture the trader's own reference
example. With the trader's actual definition — the sweep of *your own
stop*, reclaimed — the concept clears the same bar VAL and VWAP−1 cleared,
in both eras, at every X. **The earlier null was a null about my
formalisation, not about the trader's grammar.** Censusing it as its own
population (rather than bolting it onto a book) is what made this
measurable: it sidesteps the Law-7 re-entry dilution arithmetic entirely,
which is exactly why cell (a) was declared.

## 4. HOLDOUT LOOK #1 — DECLARED, NOT YET SPENT

`DECLARATIONS-holdout-look-1.md`, committed. Contents:

- **R0** — the UNSELECTED base population is tested. No cut goes to the
  holdout; a pass/fail on a selected book cannot separate population from
  cut, and there is no second venue.
- **R1** — the composite is declared, not a component. **⚠ There is an
  open decision here**: item 6 produced a *third* qualifying population
  (sweep_b) after item 2 defined the composite. If sweep_b ships, then the
  two-population composite is itself a component and testing it would
  violate R1. The declaration therefore stands as the two-population book
  **unless you say sweep_b ships too**, in which case the file is amended
  to the three-way union and re-committed *before* contact. The three-way
  union runs ~24 fights/day, which item 3 has not sized for.
- **R2** — three claims (composite, sweep_b, the queued closeloc cut) at
  **Bonferroni ×3**, stated now.
- **R3** — two blocks (2023 / 2024-01–2025-05), both must pass.
- **R4** — aggregation fixed: same committed builders, entry gate must
  pass on the sealed build, X=0.5W not re-tuned, day-level bootstrap seed
  20260807, named exclusions only, one look, no re-runs.
- **R5** — pass/fail meaning pre-committed (see item 1).

---

## The one decision blocking the look

**Does sweep_b ship alongside the composite?** If yes, the holdout claim
must become the three-way union before any sealed row is read — and item 3
needs re-running at ~24 fights/day first, because the concurrency measured
above is for 11.42/day. If no, the declaration stands as written and
sweep_b is validated separately later.

Everything else is committed and ready.
