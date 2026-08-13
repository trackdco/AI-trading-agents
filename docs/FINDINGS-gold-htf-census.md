# FINDINGS — BR-1 on gold: the mean-reversion base rate transfers

First measurement of the NQ book's foundational statistic on a metal. GC front month,
1,276,717 one-minute bars, 2023-01-02 → 2026-08-11, **4,934 displacement episodes over
934 session-days**.

Measured with `src.htf_ma.levels.bb_ma_asof` — the same function the NQ census used, not
a reimplementation — so any difference between the instruments is a difference in the
market and not in someone's definition of a band. W = upper − lower = 4σ on BB(20) of
15-minute closes; displacement threshold 0.5W, matching `DISP_W`. Sessions are
18:00-NY-anchored. Episodes, not bars: one excursion contributes one row.

## The headline

| | gold (GC) | NQ (BR-1) |
|---|---|---|
| touch before session close | **92.85%** [92.26, 93.42] | 89% (87–91% all cells) |

**It transfers, and slightly stronger.** Day-clustered bootstrap, 934 days.

## It is not just "a level near price"

The control is the same MA **frozen** at the instant of displacement — same level, same
distance, same session, with only the ability to drift toward price removed.

| | rate | 95% CI |
|---|---|---|
| moving 15m BB MA | **92.85%** | [92.26, 93.42] |
| frozen at displacement | 71.73% | [70.52, 72.94] |
| **edge** | **+21.1pp** | intervals nowhere near overlapping |

A static level at the same place is touched 72% of the time, so most of the raw number
really is "price comes back to where it was." The Bollinger construction is worth
21 points on top of that, which is a much wider margin than the 3–4pp the NQ placebo
left on BR-2's race.

## Stable where it should be

| cell | n | touch % | 95% CI |
|---|---|---|---|
| up-displacement | 2484 | 92.91 | [92.02, 93.82] |
| down-displacement | 2450 | 92.78 | [91.84, 93.70] |
| era H1 | 2518 | 93.88 | [93.09, 94.70] |
| era H2 | 2416 | 91.76 | [90.87, 92.55] |

Sides are indistinguishable. The eras differ by 2.1pp with a mild decay, and the placebo
decays faster (74.9% → 68.4%), so the **edge over control grows** across the sample
(+18.9pp → +23.4pp) rather than eroding.

## The session split was an artifact — and this is the part worth reading

The raw per-session numbers look spectacular and are almost entirely a clock effect:

| window | raw touch % | |
|---|---|---|
| asia | 99.95 | |
| london | 99.14 | |
| ny | **80.42** | |

Sessions start at 18:00 NY, so an Asia displacement has roughly twenty hours of session
left to rebalance and an NY one has about four. That table measures time-remaining, not
the market. Restricting to episodes that had the time to spend, and asking only whether
the touch landed inside a fixed horizon:

| horizon | asia | london | ny |
|---|---|---|---|
| 30 min | 21.6 | 16.9 | **24.5** |
| 60 min | 37.9 | 34.5 | **39.9** |
| 120 min | 58.0 | **59.3** | 56.6 |
| 240 min | 80.2 | **85.0** | 78.2 |

The windows converge. NY is marginally *fastest* early and London marginally best by four
hours — 85.0% [82.60, 87.39] against NY's 78.2% [76.03, 80.36], intervals clear of each
other, which faintly echoes the NQ London result (BR-23) without being evidence for it.

**Anyone reading the raw session table would have concluded gold mean-reverts in Asia and
trends in NY. It does neither. It reverts at the same rate everywhere and the sessions
differ by how much session is left.**

Median time to touch: 91 minutes.

## BR-2's race is degenerate here

Extension beyond the displacement point runs p50 **0.11W**, p90 **0.28W**, and effectively
never reaches a further 1.0W before the touch — `before_1w` equals `touched` in every
single cell. On NQ that race is a live 64–66% question with a 60–63% placebo; on gold it
does not exist, because the excursion is over long before another full W.

Caveat on the comparison: this measures *incremental* extension past the displacement
point, and BR-4's 0.43–0.44W may be measured from a different origin. The gold number
stands on its own; treat "gold extends less than NQ" as unestablished until BR-4's
definition is checked against this one.

## What this establishes, and what it does not

**Does.** The physics the NQ book is built on are present in gold, at a slightly higher
rate, on both sides, in both eras, and not explained by proximity. The session structure
does not differentiate it. A gold book built on the 15m BB MA has a real base rate under
it rather than a hopeful one.

**Does not.** This is a base rate, not an edge. BR-1 was the foundation of the NQ work,
not its result — the tradeable question needed arms, loci, exits and costs (BR-9 through
BR-16), and none of that is measured here. Touching a level is not the same as making
money going to it, and gold's spread is 0.56 against 2–3 point stops, which is where the
CBR autopsy died.

Next, in order: the level-family census (which locus, reject and break arms separately),
then per-window books, then exits. That is the sequence that worked on NQ, and the base
rate above is the licence to run it.

Per the repo's non-negotiables, no parameter was tuned to improve any number here. Two
defects found and fixed during the run are recorded in the commit: a slice-local index
that stamped every episode with one session-day, and the time-remaining confound above.
