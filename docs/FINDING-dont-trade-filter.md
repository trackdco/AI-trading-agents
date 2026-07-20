# FINDING: the "don't trade" filter — below-value + CVD-absorption (20 Jul 2026)

**TL;DR:** Loser autopsy on the 2026 champion book (132t) found two dominant "don't trade" tells:
**hollow rejections (no CVD absorption)** and **below-value opens**. Cutting both:
**132t → 78t (−41% trades), +$14,009 → +$14,351 (MORE money), win 33% → 41%, still 5/6 months green.**
Cut nearly half the trades, kept all the money, raised the win rate. Min-stop (6pt pre / 10-15 post)
already applies via config — this is on top of it.

## The autopsy — what losers share that winners don't (132 champion trades)
| tell | winners | losers | read |
|---|---|---|---|
| **CVD (flow into the level)** | −74 (absorbed) | −10 (hollow) | #1 separator; losers are hollow rejections |
| open_vs_value = below_value | 44% win (above) | **0% win, −$2,355** (below) | below-value opens are dead (small n=9) |
| stop size (risk) | 18pt median | 12pt median | over-tight stops get wicked (Angus's own lesson) |
| gap_open_pts | +51 | +36 | the fade needs dislocation to revert |

## The filter (graded on month consistency)
| filter | trades | P&L | win% | green |
|---|---|---|---|---|
| baseline | 132 | +$14,009 | 33% | 5/6 |
| cut below-value | 123 | +$16,364 | 35% | 5/6 |
| **+ require CVD absorption (cvd<=0)** | **78** | **+$14,351** | **41%** | **5/6** |
| + cvd<=-30 | 57 | +$11,561 | 44% | 5/6 |
| + cvd<=-60 | 34 | +$7,228 | 50% | 4/6 (too aggressive) |

Sweet spot = **below-value cut + cvd<=0**: keeps all the money at 41% win. Tunable toward 50% win
(cvd<=-60 = Angus's live number) at a dollar cost; cvd<=-60 finally breaks a month, so ~cvd<=-30 is
the aggressive-but-still-consistent bound.

## July is a small-sample artifact, NOT a leak (diagnosed 20 Jul)
- July has **46 triggers/day** — same as May (45) / June (43). Setups are there.
- The champion took **only 4 trades in 11 days** (data ends Jul 15); 2 were junk (0.5pt & 4pt stops).
- One bad day (Jul 3, −$515) on a 4-trade half-month = red month. Not systematic.
- Flip side of the thesis: the gates **over-restrict** July — the bot isn't trading setups it should.
  Same root as "trading when it shouldn't": the mechanical selectivity != Angus's read.

## Honest caveats
- In-sample 2026; on the champion book (the substrate the agent selects from → tells the agent which
  trades to skip). below-value n=9 is small; the CVD-absorption tell (n=132) is the robust one.

## Forward
Fold the below-value + CVD-absorption gate into the agent's trade decision (skip hollow rejections,
skip below-value opens). Combine with the regime-gated post-open (FINDING-regime-gated-postopen) and
the leg-scaled exits. Grade on month consistency from the chained base.

## Scripts / data
- journal: scratchpad `champ_journal_cvd.csv` (per-trade + CVD) · regime: `output/regime_vector.csv`
- CVD sign: side B=buy, A=sell (verified scratchpad/sign_test.py); cvd oriented so negative = flow
  against the trade = real absorption.
