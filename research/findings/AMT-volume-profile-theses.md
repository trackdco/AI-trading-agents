---
date: 2026-08-05
status: RESEARCH — six falsifiable theses for the volume-profile / AMT build
tags: [amt, volume-profile, poc, lvn, research, theses]
---

# Volume profile and AMT — six theses worth testing, and one our own data already kills

ANGUS 2026-08-05: *"start using weekly volume profile as well, figure out how we can
incorporate it best and what time period is best… do some deep research on how we can use
volume profile and AMT most effectively overall in general so u actually have some theses
to test against."*

## What we already hold, and what is being thrown away

`src/engine/indicators.volume_profile` already returns **POC, VAH, VAL, HVN list, LVN
list, bin centers and bin volumes.** It is called for a **daily** profile only, and
`_gather_levels` exposes **only the POC** as a tradeable level.

**VAH, VAL, HVN and LVN are computed on every bar and discarded.** There is no weekly
profile, no multi-day profile, and no naked/virgin-POC tracking anywhere in the repo.

---

## The framework, stated so the theses are not vibes

AMT: the market alternates between **balance** (rotating around an accepted fair value,
two-sided, choppy at the edges) and **imbalance** (one-sided, seeking a new value area).
Value area = the ~70% volume band; POC = the most-traded price, the market's own statement
of fair value.

The four rules as commonly taught: (1) accepted *into* a balance → likely rotation to the
far side; (2) inside balance → edges reject, behaviour choppier; (3) accepted *outside*
balance → seeks new value, often an older balance's POC; (4) a strong reaction at POC can
cancel rule 1.

---

## T1 — LVN traversal. **The strongest thesis, and it rescues a failed idea.**

**Claim:** price moves *fast* through low-volume nodes and *stalls* at high-volume nodes.
An LVN is a price the market has already rejected as unfair — there is no resting interest
there, so there is nothing to slow it down.

**Why this matters more than it looks:** `LQV-01` died today trying to measure exactly this
— "where is there no liquidity" — from **one MBP-10 snapshot per minute**, and the
measurement was too coarse (aggregate side size never fell below 0.56× its own median).
**A volume profile is the same question answered with a far better instrument:** the
*historical record* of where trade did and did not occur, built from every bar, not a
once-a-minute photograph of resting orders.

**Test:** points travelled per minute while price is inside an LVN band vs an HVN band,
matched on volatility regime. Falsifiable and needs no new data.

## T2 — Naked POC as a magnet

**Claim:** a POC that has not been traded since it formed ("naked"/"virgin") attracts price.

**Test:** of naked POCs within N points at session start, what fraction are touched that
session — against a control of *already-tested* POCs at matched distance. The control is
the whole test: any level near price gets touched often, so an uncontrolled hit rate proves
nothing. **We have no naked-POC tracking at all — this needs building.**

## T3 — The 80% rule. **Our own data already contradicts the published claim.**

**Claim as taught:** open outside the value area, trade back inside, and there is an ~80%
chance of traversing to the far side. Independent write-ups quote 67%; one cites 72% on ES
2018–2024.

**What we measured, twice, independently:**

| our test | far-edge traverse |
|---|---:|
| `NYA-FA-01` (NY) | **12–21%** |
| `LDN-PO3-01` (London pre-open range) | **~20%**, midpoint ~46% |

`NYA-FA-01`'s verdict called the 80% rule folklore. **Two sessions, two ranges, ~20%
against a claimed 80%.** This is the cleanest example in the repo of Angus's own thesis:
a widely published number that does not survive independent measurement.

**BUT the test we ran was not the rule as stated**, and honesty requires saying so: the
rule requires **acceptance** — commonly two consecutive 30-minute periods closing back
inside — and our tests measured *any* re-entry. It is also stated to work in *balanced*
markets and to fail in trending ones, and we applied no regime condition. So the correct
statement is: **the rule as commonly traded fails at ~20%; the rule as originally specified
has not been tested here.** That is a declared arm, not a settled kill.

## T4 — Value-area edge behaviour is regime-conditional

**Claim:** inside balance, VAH/VAL reject (fade them). Once *accepted* outside, price seeks
new value (do not fade them).

**Why it matters to us:** this is a single mechanism that explains why our fades and our
displacements each work only sometimes — **they are the same trade in opposite regimes.**
Every fade we own is an implicit bet that we are inside balance; every displacement is a
bet that we are not. We have never once conditioned on which.

**Test:** classify each session's state against the prior profile, then split our existing
displacement and fade books by it.

## T5 — Which profile period. **An empirical question, not a preference.**

Candidates: previous session · previous calendar week · rolling 5 sessions · rolling 20
sessions. **Test all four the same way** — reaction magnitude at first touch of each
profile's POC/VAH/VAL, controlled against a random price at matched distance — and let the
data pick. Longer profiles give more robust levels but fewer, fresher ones react harder;
that trade-off is measurable rather than arguable.

## T6 — Value migration as a trend read

**Claim:** consecutive higher POCs and higher value areas = a healthy uptrend; overlapping
value = balance.

**This is the market-context layer Angus asked for**, expressed in profile terms rather
than as a moving average. Our only trend read today is `htf_flag`, which is the
**15-minute** regime — nothing in this repo knows whether we are in a bull market.

**Test:** POC-over-POC direction across the last N sessions as a daily trend state, then
score trades taken with it against trades taken against it.

---

## Build order

1. **T1 (LVN traversal)** — strongest mechanism, uses the best instrument we own, and it
   is the honest second attempt at the question `LQV-01` failed to answer.
2. **T5 (profile period)** — cheap, and everything downstream depends on picking the right
   window.
3. **T6 (value migration)** — the missing market-context layer.
4. **T4, T2, T3** — after the above, since each depends on levels or a regime label from them.

Every threshold relative. Every test controlled. Scored on the prop scoreboard, not PF.
