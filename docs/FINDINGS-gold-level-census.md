# FINDINGS — which NQ confluences carry an edge on GC

The NQ level-family census (E1, BR-11/BR-12), re-run on gold. GC front month,
2023-01 → 2026-08, **105,365 triggers → 71,328 first-of-fight rows over 932 session-days**.

Not a reimplementation: `scripts/gold_level_census.py` imports
`scripts.htf_ma_level_census` and calls its own `day_rows`. The fight grammar, the as-of
level construction, the stop rule and the shipped exit are the incumbent's. Three things
change, each a property of the instrument rather than of the method — tick 0.25 → 0.10,
round-turn cost 0.50 → 0.20 points, and the bars. W stays the 15m BB width, an
instrument-relative ruler, so nothing was rescaled by hand.

Convention stated up front, because BR-10 records the same population reading −0.04R to
+0.20R across conventions: **first trigger per structural fight, shipped exit, 0.5-point
risk floor, no selection inside a cell.**

## Headline

**One cell of fourteen clears the E1.4 bar — positive with a day-clustered interval clear
of zero in BOTH halves. It is `vah · break`.**

| cell | n | /day | win % | EV | 95% CI | H1 | H2 | both eras |
|---|---|---|---|---|---|---|---|---|
| **vah · break** | 3972 | 4.6 | 36.6 | **+0.148** | [+0.099, +0.197] | +0.147 | +0.149 | **yes** |
| poc · break | 6518 | 7.0 | 34.6 | +0.108 | [+0.067, +0.145] | +0.044 | +0.160 | no |
| vwap_p1 · break | 4323 | 5.0 | 34.3 | +0.099 | [+0.056, +0.147] | +0.059 | +0.138 | no |
| val · break | 3754 | 4.4 | 34.4 | +0.098 | [+0.049, +0.144] | +0.025 | +0.184 | no |
| poc · reject | 7140 | 7.7 | 33.3 | +0.054 | [+0.018, +0.093] | +0.003 | +0.096 | no |
| val · reject | 4369 | 4.8 | 33.8 | +0.049 | [+0.002, +0.098] | −0.042 | +0.146 | no |
| bbma15 · break | 4656 | 5.0 | 34.5 | +0.047 | [+0.006, +0.089] | +0.007 | +0.083 | no |
| bbma15 · reject | 5350 | 5.8 | 32.9 | +0.040 | [+0.001, +0.079] | +0.001 | +0.076 | no |
| vwap_m1 · break | 3954 | 4.7 | 31.9 | +0.031 | [−0.015, +0.078] | −0.063 | +0.135 | no |
| vwap · reject | 4587 | 5.0 | 32.2 | +0.027 | [−0.018, +0.075] | −0.009 | +0.063 | no |
| vwap_m1 · reject | 4535 | 5.1 | 33.1 | +0.025 | [−0.020, +0.070] | −0.057 | +0.113 | no |
| vwap · break | 3989 | 4.5 | 32.6 | +0.018 | [−0.028, +0.064] | −0.008 | +0.046 | no |
| vah · reject | 4543 | 5.0 | 32.7 | −0.002 | [−0.044, +0.042] | −0.040 | +0.036 | no |
| vwap_p1 · reject | 4884 | 5.4 | 31.9 | −0.003 | [−0.049, +0.042] | −0.062 | +0.053 | no |

Eight of fourteen clear zero on the full sample. One clears it in both halves. That gap
is the whole reason the both-era bar exists.

**The arms split cleanly.** Break +0.080 [+0.058, +0.102], both eras clear. Reject +0.029
[+0.008, +0.051], H1 negative. On gold the break arm is where the money is.

## The locus does not transfer — the method does

On NQ (BR-12) the break-arm winners were **vwap_m1 (+0.248)** and **val (+0.234)**, with
**vah near the bottom at +0.068**. On gold the ranking inverts: **vah is the winner and
the only survivor**, while vwap_m1 is mid-pack at +0.031.

Porting NQ's answer to gold would have picked the wrong level. Porting NQ's *census*
found the right one. That is the transferable asset.

## The largest single effect is stop size, and most of it is arithmetic

| stop (pts) | n | win % | EV | EV before cost |
|---|---|---|---|---|
| 0.50–1.0 | 13823 | 28.5 | **−0.191** | +0.084 |
| 1.0–1.7 | 12807 | 31.2 | +0.001 | +0.155 |
| 1.7–2.7 | 13362 | 33.8 | +0.100 | +0.195 |
| 2.7–5.1 | 13274 | 34.4 | +0.134 | +0.189 |
| 5.1+ | 13308 | 39.5 | **+0.227** | +0.251 |

Monotone, and the same shape in W units (risk/W: −0.111 → +0.228 across quintiles). This
is BR-45 reproducing on gold.

**But 58% of it is the cost denominator.** Cost enters as `0.20 / risk`, which is 0.262R
on a 0.76-point stop and 0.018R on an 11.4-point one — a 0.244R swing out of the 0.418R
observed. Strip the cost and the spread collapses from 0.418R to 0.167R. The residual is
real and still monotone, but "wider stops are better" is mostly "fixed costs hurt small
stops", not a market fact. Anyone quoting the +0.227 cell as an edge is quoting a
division.

## Sessions: not NQ's answer either

| session | n | EV | 95% CI |
|---|---|---|---|
| ny_rth_am | 7536 | +0.086 | [+0.042, +0.134] |
| asia | 32342 | +0.082 | [+0.055, +0.109] |
| london | 13886 | +0.043 | [+0.008, +0.079] |
| ny_pre | 5408 | +0.025 | [−0.035, +0.087] |
| **ny_pm** | 7402 | **−0.069** | [−0.110, −0.026] |

None clears both eras. **London is not the standout it is on NQ** (BR-23: +0.357 there,
mid-pack here). The one durable session statement is negative: the NY afternoon is
reliably bad, on an interval well clear of zero.

That shows up inside the headline cell too — `vah · break` runs +0.248 in Asia, +0.192 in
NY AM, +0.126 in London, and **−0.255 in NY PM**. Cutting the afternoon would improve it,
and the cut has independent support since the whole book is negative there, but it is
still a post-hoc cut and is not included in the +0.148 above.

## Not the risk effect wearing a hat

`vah · break` beats the rest of the book by a near-constant margin inside every stop-size
quartile: **+0.077, +0.099, +0.087, +0.068**. It is an independent effect, not a
by-product of that cell carrying wider stops.

The ranking also survives the floor choice. Across floors 0.2 / 0.3 / 0.5 / 1.0 / 2.0,
`vah · break` is the top cell at every one (+0.113 → +0.226). Every cell's level rises
with the floor — which is the cost effect again — but the ordering does not move.

## Two defects, both found and fixed mid-run

**BR-29 reproduces on gold, and worse.** The stop is the trigger candle extreme ± one
tick, and GC's tick is 0.10 against a price near 3,000, so a flat trigger candle yields a
stop of a few cents and R detonates. **Three rows out of 71,328 carried −3.0 × 10¹¹ R
between them.** Median |R| is 1.11 and the 99.99th percentile is 15. The 0.5-point floor
removes 6.66% of rows; a stop smaller than the round-turn cost is not a trade, so the
floor is a tradeability requirement — but it is still a choice, which is why the sweep is
reported.

**My permutation calibration was invalid here and is withdrawn.** `autopsy.permute`
shuffles outcomes *within* (session, mech) cells, which preserves every cell mean exactly
— so it cannot test whether a cell's mean differs from zero. It returned `null = +0.1481
± 0.0000`, identical to the real value, which is the signature of a test with no power
rather than a result. The tests actually relied on above are the day-clustered interval,
the era split, and the risk-stratified contrast.

## What this establishes, and what it does not

**Does.** The NQ census machinery runs on gold unmodified and produces a coherent book:
+0.053R per fight overall at 71 fights/day. The break arm carries it. One locus — the
developing value-area high, break arm — clears the bar the NQ census used, at +0.148R and
4.6 fights/day, stable across halves (+0.147 / +0.149), independent of stop size, and
robust to the floor.

**Does not.** This is fit-side on the whole sample. Fourteen cells were tested and the
era split is the only out-of-sample-flavoured evidence in it; a single survivor from
fourteen is roughly what a generous multiplicity budget permits. Room-to-run (BR-32/35)
is untested here — it needs all loci at each minute, a second pass. The flow family is
untestable on this data and was weak on NQ anyway (BR-19/31). Cost is assumed at 0.20
points and not measured. And no size, no payout cap, no graduation analysis: BR-39's
finding that frequency beats EV means 4.6 fights/day at +0.148 may still lose to a
lower-EV, higher-frequency book.

Next, in order: seal a holdout and re-run `vah · break` on it; measure GC's actual
round-turn cost rather than assuming 0.20; then room-to-run, which was the largest
non-flow gate on NQ.

Per the repo's non-negotiables, no parameter was tuned to improve any number here. The
risk floor is reported as a sweep rather than a chosen value, and the NY-PM cut is
flagged as post-hoc and excluded from the headline.
