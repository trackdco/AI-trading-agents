# FINDINGS — the session refutation reverses on the corrected detector, and Law 2 explains it

NQ, 1,251,240 bars, 2023-01 → 2026-07. **85,277 signals** on the corrected detector
(`require_revisit` enforced, CORRECTION 2). Day-clustered intervals, both eras, win% and
EV on every row, dollars alongside R.

Two things prompted this. `FINDINGS-dodgy-ifvg.md` reported that restricting to New York
made the book **worse** (pre-cost −0.026 → −0.071) and that has been cited since as
settled — but it was measured on **n=21,219**, the population the CORRECTION withdrew, and
never re-run. And every result in this stream so far ran with **no session filter at all**,
so 88.5% of the tested book sits in hours he tells students to avoid.

## 1 — In R, the session restriction now HELPS

| cell | n | /day | win % | EV | 95% CI | H1 | H2 |
|---|---|---|---|---|---|---|---|
| ALL, no filter | 81,038 | 88.2 | 32.80 | **−0.128** | [−0.138, −0.117] | −0.148 | −0.110 |
| Asia 20:00–00:00 | 12,851 | 14.1 | 33.24 | −0.138 | [−0.164, −0.113] | −0.191 | −0.095 |
| London 02:00–05:00 | 11,139 | 12.2 | 33.11 | −0.125 | [−0.152, −0.099] | −0.148 | −0.103 |
| NY AM 08:30–11:00 | 9,660 | 10.6 | 32.28 | −0.109 | [−0.138, −0.080] | −0.129 | −0.089 |
| **NY 09:30–11:00** | 5,753 | 6.3 | 32.28 | **−0.094** | [−0.130, −0.056] | −0.105 | −0.083 |
| NY mid 11:00–16:00 | 18,893 | 20.7 | 32.23 | −0.118 | [−0.137, −0.098] | −0.114 | −0.121 |

**The published direction flips.** NY 09:30–11:00 is the *best* cell in the table at
−0.094R against −0.128R unfiltered — a **+0.034R improvement**, where the withdrawn
population said the same restriction cost −0.045R pre-cost. Asia is the worst, which is at
least consistent with his own advice to avoid it.

**Do not read that as a rescue.** See §2.

## 2 — In dollars it goes the other way, and that is the real answer

| cell | median stop | cost in R | **$/trade** | $/day |
|---|---|---|---|---|
| ALL, no filter | 5.00 pt | 0.100 | **−$11.31** | −$997 |
| Asia | 3.75 pt | 0.133 | −$8.56 | −$120 |
| London | 4.50 pt | 0.111 | −$8.30 | −$101 |
| NY AM 08:30–11:00 | 8.25 pt | 0.061 | −$16.95 | −$179 |
| **NY 09:30–11:00** | **10.75 pt** | **0.047** | **−$17.83** | −$113 |

**The NY session has the biggest stops in the day — 10.75 points against 5.00 unfiltered —
so a fixed 0.5-point round turn costs 0.047R there against 0.100R overall.** That is the
entire R improvement: the cost drag halves because the denominator doubles.

**Per trade in dollars the NY session is the WORST cell tested, not the best**: −$17.83
against −$11.31. Sorting the same book by R and by dollars produces opposite orderings.

This is Law 2 operating exactly as written — *"most 'wider stops are better' results are
the cost denominator, not a market fact."* The session restriction does not find better
trades; it finds trades with wider stops, which flatters EV-in-R and costs more money.

**Correction to the record:** the published session refutation should not be cited as
settled — it was measured on a withdrawn population and its sign reverses in R. But the
replacement claim is not "New York helps"; it is **"the session comparison is a
denominator comparison and must be read in dollars."**

## 3 — The structural target is worse in every single session

Ten of ten. NY 09:30–11:00: fixed 2R −0.094 vs structural −0.113. Asia: −0.138 vs −0.148.
London: −0.125 vs −0.139. NY mid: −0.118 vs −0.134. The median reward:risk of the nearest
unswept pool is 1.03–1.15 in every session, and win rate rises 8–11pp everywhere while
expectancy falls everywhere.

`FINDINGS-dodgy-structural-target.md` is not a whole-sample artifact. It holds in every
sub-population his own rules would select.

## 4 — The macro windows, tested for the first time

| window | n | /day | win % | EV | 95% CI |
|---|---|---|---|---|---|
| 08:50–09:10 | 1,245 | 1.58 | 29.08 | **−0.228** | [−0.302, −0.153] |
| 09:50–10:10 | 1,244 | 1.55 | 31.59 | −0.111 | [−0.184, −0.038] |
| 10:50–11:10 | 1,289 | 1.59 | 32.74 | −0.087 | [−0.160, −0.009] |
| all three | 3,778 | 4.15 | 31.15 | −0.141 | [−0.181, −0.097] |

**08:50–09:10 is the worst cell in the entire study at −0.228R** — trading into the cash
open, on a 5.75-point median stop, is roughly twice as bad as the book average. The other
two macros are unremarkable and the pooled set is worse than no filter at all.

The macro windows were the last untested piece of his time model. They do not help.

## Standing conclusion

Every cell in this document is negative, every interval clears zero on the negative side,
and **no cell clears both eras**. The best cell in R (NY 09:30–11:00, −0.094R) is the worst
in dollars per trade.

What changed: the session claim needed re-opening and did reverse in R, so the old
refutation should not be quoted. What did not change: the model is negative in every
session, at every macro, under both exits.

## Method note

Sessions are clock-hour boxes in America/New_York on the signal timestamp, not
18:00-anchored session days — the boxes are intraday and do not span midnight except Asia,
which is handled explicitly. Cells under 200 trades are dropped rather than reported.
