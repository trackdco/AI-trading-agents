---
title: Zarb bias filters — measurement findings
date: 2026-08-09
status: CLOSED — layer measured, no lift, nothing to build
scope: fit-side measurement only; no holdout, sealed span, or reserved venue touched
---

# Zarb bias filters — findings

## 1. The verdict

**F1 (Golden Rule) and F2 (midnight open) both return NO LIFT, against all three
nulls, in both session-close configurations.**

Bars-mode directional test: enter at the 09:30 ET open in the direction the
filter implies, hold to 16:00 ET, declared 30-point stop. NQ front-month
1-minute data.

| | 16:30 close (Zarb's stated window) | 17:00 close (CME's real close) |
|---|---|---|
| Sessions | 749 (2023-01-04 → 2026-01-30) | 726 (same range) |
| Prereg sha256 | `509cc14aacbf7eac…` | `8e2f24de701c4505…` |
| F1 verdict | **NO LIFT** | **NO LIFT** |
| F2 verdict | **NO LIFT** | **NO LIFT** |

Neither filter clears a single null in either window. This is not a marginal
failure on the decisive null — it is a failure on all of them.

Both filters also land **below the unfiltered drift baselines**. Always-long
returns +0.1441 R and always-short +0.1858 R over the same 749 sessions; the
Golden Rule returns +0.0986 R. Reading the previous-day POC did worse than
picking a side at random and never changing it.

**The verdict does not depend on the roll bug described in §5.** That bug
touched 23 of 749 sessions (3.1%), and the real statistics sit far below every
null p95 — F1 is 0.21 R below null C's p95. Three percent of sessions cannot
close that gap in either direction.

## 2. Where the real values sit relative to the nulls

The p95 comparison is the decision rule, but the null **means** say what kind of
failure this is. For a 200-draw sampling distribution of a mean the null mean
and null median are effectively interchangeable, so "at the null mean" reads as
pure noise and "below it" as mildly anti-predictive.

**16:30 close**

| Filter | real mean R | null A mean | null B mean | null C mean |
|---|---|---|---|---|
| F1 golden rule | +0.0986 | +0.1168 (−0.018) | +0.0223 (**+0.076**) | +0.1644 (−0.066) |
| F2 midnight open | +0.1615 | +0.1965 (−0.035) | +0.3193 (−0.158) | +0.1619 (−0.000) |

**17:00 close**

| Filter | real mean R | null A mean | null B mean | null C mean |
|---|---|---|---|---|
| F1 golden rule | +0.1038 | +0.1077 (−0.004) | +0.0369 (**+0.067**) | +0.1633 (−0.059) |
| F2 midnight open | +0.2005 | +0.2291 (−0.029) | +0.3005 (−0.100) | +0.1770 (**+0.024**) |

Parenthesised figure is real minus null mean.

Nine of the twelve comparisons put the real value **below** the null mean. The
single most striking number is F2 against null C at the 16:30 close: the real
value sits 0.0004 R from the null mean — indistinguishable from a coin flip
weighted to the same 47% long rate. F2 against day-shuffled levels (null B) is
0.158 R **below** the null mean, meaning permuting the midnight opens across
days produced systematically *better* directional calls than using the correct
one for each day.

Read plainly: these levels are noise, with a mild anti-predictive tilt for F2.
The three positive deviations are all small and all fail their p95.

## 3. Mean close points is the load-bearing number, not mean R

**Mean close points was NEGATIVE for both filters.**

| | 16:30 | 17:00 |
|---|---|---|
| F1 golden rule | **−12.45 pts** | −11.77 pts |
| F2 midnight open | **−4.58 pts** | −2.13 pts |

This is the number to quote, because it is the one that is not distorted by the
metric. Taking the filter's direction at 09:30 and holding to the 16:00 close
**lost points on average**, over three years, in both windows, for both filters.

Mean R was positive for both filters and should not be quoted without this
alongside it.

### Why mean R misleads here

R at a declared stop is **floored at −1 and unbounded above**. You are stopped
out roughly 80% of sessions (F1: 81.3%, F2: 78.9%), so the median outcome is
−1.0000 R for every configuration measured — including both drift baselines.
The mean is dragged positive by a thin tail of very large winners: 137
always-long winners averaging +5.21 R, the largest being 2025-04-09 at +70.5 R
(the tariff-pause session, a genuine +2116-point NQ day).

The consequence is structural: **both** always-long (+0.1441 R) and
always-short (+0.1858 R) are positive over the same sessions. A metric where
committing to either direction, permanently, yields a positive mean is not
measuring whether the direction was right. It is measuring **whether NQ trended
far enough, on enough days, to pay for the 30-point stop** — and over
2023–2026 it did, in both directions on different days.

So a positive mean R for a filter is the default state of this metric, not
evidence. That is precisely what null C exists to expose, and both filters fail
it.

## 4. F3 is invalid as built

**The canonical 80% rule result (34.7% at 16:30, 34.9% at 17:00) must not be
reported as a finding, and does not validate the pipeline.**

The published independent figure of roughly 60–70% on ES is an **RTH-session**
rule: price opens outside the prior day's value area, rotates back inside for
two consecutive 30-minute periods, and the question is whether it then traverses
the value area *within the regular trading session*.

As implemented, the rule is evaluated over the **full 22.5-hour 18:00 → 16:30 ET
profile session**. That is a different question on a different window. The
trigger can fire overnight, in thin Asia-hours liquidity, hours before the RTH
auction the published statistic describes. The 34.7% figure is therefore not
comparable to the 60–70% band, and the ~30-point shortfall is not evidence about
NQ — it is the expected consequence of running an RTH rule over a 22.5-hour
window.

Because F3 was included specifically as pipeline validation, and it cannot serve
that purpose as built, **the pipeline is unvalidated by F3**. It is validated by
the selfcheck (both modes, edgeless synthetic data, correct NO LIFT / DESCRIPTIVE
ONLY results, all ten null p95 values non-zero) and by nothing else.

**The Zarb POC-engagement variant (72.5% / 73.3%) is not a finding.** It has no
null, no published prior, and no control of any kind. "Price engages a level at
some point during a 22.5-hour session" is a statement about how often price
revisits a nearby price over a long window, and the base rate for that is high
by construction. Nothing was measured against it. It should not be cited.

## 5. The contract-roll bug, and the fix

**The bug.** `nq_1m_frontmonth.csv` originally picked the front-month contract
per **UTC** calendar date. Because 00:00 UTC is 19:00 ET (EST) or 20:00 ET
(EDT), every roll landed one to two hours *inside* the 18:00 → 16:30 ET profile
session. Each roll splices in a calendar-spread discontinuity of **+128 to +297
points**, so twelve sessions had their volume profile built across two
contracts. Their POC, VAH and VAL are meaningless, and because each session's
levels are read as the next session's "previous day", 23 of 749 sessions (3.1%)
in the measured population were affected.

**Why the original detector missed it.** Roll detection tested the *overnight
gap* — session open minus previous session close. That can only see a
discontinuity falling exactly on the session boundary. A mid-session splice is
invisible there. The consequence was the worst of both: it caught **0 of 12**
rolls while dropping 43 sessions (16:30) and 66 (17:00) that were ordinary large
overnight gaps, median 108 points.

**Fix 1 — the splice, at source.** `prep_bars.py` now selects the front month
**per session** and applies it to every bar in that session, so the roll step
falls between sessions where no profile spans it. Rolling on ET calendar dates
would *not* have fixed this: 00:00 ET is still mid-session for a session that
opened at 18:00 the previous evening. The session boundary is the only cut that
works. Verified: **0 of 954 sessions contain more than one contract**, versus 12
in the old file — exactly the twelve roll dates.

**Fix 2 — the detector.** `zarb_filters.py` now flags on the largest
close-to-close step between consecutive bars *inside* a session, which is where
a mid-session splice is unmistakable. Verified against the old, corrupted file:
**11 of 12 rolls caught** at the default `--roll-sigma 6`.

The one miss is 2023-03-13, whose splice is 128.50 points against a z=6
threshold of 146.83 (z = 5.00) — the smallest calendar spread in the sample,
being the earliest date and the lowest index level. **The threshold was not
tuned to catch it.** Lowering `--roll-sigma` would, at the cost of more false
positives; that is a live choice, not a fix applied here.

**Known limitation of the fixed detector.** It cannot distinguish a 150-point
splice from a 150-point news minute. On the corrected bar file it still flags
~21 sessions, of which essentially none are rolls — they are genuine violent
minutes (2024-08-05 yen-carry unwind, 2025-01-15 CPI, and similar). On a bar
file spliced at the session boundary the correct exclusion count is **zero**,
because no profile spans a roll. Anyone running against the corrected file
should expect the roll-exclusion count to be noise and check the reported step
sizes against the known calendar-spread width before trusting it.

## 6. What was deliberately not done

- **The filter test was not re-run on the corrected bar file.** The verdict is
  unaffected by 3.1% of sessions, and re-running a measurement after changing
  something in response to its result is the exact pattern the hashed prereg
  exists to prevent. The splice fix is for future work only.
- No variants were tried, no parameters tuned, no filter re-tested.
- Each configuration was run exactly once.
- The commit at which the measurement was run is tagged
  `zarb-measurement-utc-splice`, and the original bar file is retained as
  `nq_1m_frontmonth_utcsplice_DEPRECATED.csv`, so the measured state stays
  reproducible.

## 7. Bottom line

The Golden Rule and the midnight open, read as directional bias at the NY open,
do not beat proximity-matched random levels, day-shuffled levels, or direction-
matched coin flips. They do not beat committing to one side and never changing
it. And on the one number the metric does not distort — mean points at the
close — both are **negative**.

Per the source audit's §8 ranking, these were the two cheapest real questions in
the Zarb corpus and the two highest-value tests available. Both are now answered
in the negative. The level-as-bias-filter layer is closed.
