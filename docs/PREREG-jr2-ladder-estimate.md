# PREREG — mechanical ladder estimate for jr2, registered before its book

**Registered 2026-08-19, before any jr2 rows exist.** His question: *"we
cant see what the result outcome would be without re running it would
we?"* — partially, we can: the GEOMETRY of enforced T78 is computable from
the bars and the certified level engine. What is NOT computable offline is
agent behaviour (what a bounced trigger actually names; what the manager
does with a real TP2 in hand). jr2 measures the behaviour; this doc pins
the geometry down first so the comparison cannot be fitted afterwards.

## Method

For each single-target FILLED trade in jr1 (8 of 12) and wr2 (11 of 18):
derive the TP2 T78 would name — the nearest structural level in the
offline set at the decision minute, at least 1R beyond TP1 — then walk the
bars: TP1 banks 50%; the runner goes to TP2 or breakeven, whichever prints
first; no trails, no third rungs, no re-rolled verdicts. Trades that never
reached TP1 are unchanged by construction.

## The estimate

**jr1 tape (the number jr2 is checked against):** the 8 single-target
trades go from **+0.06R as-run to +5.27R** under the mechanical ladder —
so the week's estimate moves from +3.08R to **≈ +8.3R blended**, right at
the jn1 yardstick (+7.69R). Two trades carry it:

| trade | as-run | with T78 TP2 | note |
|---|---:|---:|---|
| 06-04 A5 | −0.03 | **+3.76** | the trade flagged as "half of management's losses" — really a missing-TP2 casualty; TP2 (vwap_m3 ≈29579) printed |
| 06-01 A2 | +1.00 | **+2.88** | the Tuesday 09:46 long; TP2 (vwap_p3 ≈30672) printed |
| 06-01 A3 | +0.59 | +0.50 | runner BE'd — small cost |
| 06-03 A3 | +1.53 | +1.16 | runner BE'd — small cost |
| 4 losers/scratch | −3.03 | −3.03 | never reached TP1; ladder irrelevant |

**wr2 (why the fit week does NOT need a wr3):** its 11 single-target
trades go from **+9.74R as-run to +8.29R** under the same fixed walk —
the fit week's managers BEAT the mechanical ladder (e.g. 06-21 A6 +4.75
as-run vs +2.96 laddered; 06-22 A4 +2.10 vs +0.61). Enforcement adds a
floor, and manager discretion still overrides (0.3.4) — so wr2's result
is not expected to improve under 0.4.13, and re-running it buys nothing.

## What jr2 can differ on, legitimately

- The bounced trigger may name a DIFFERENT TP2 than the mechanical pick
  (nearer structure, a confluence) — or, being re-spawned, change its
  verdict entirely. Count of `t78_single_target` tags measures how often
  the first emission still comes back short.
- The manager may beat the fixed walk (it did on wr2) or undershoot it
  (it improvised at −5.96R vs full-target on jr1).

**The registered prediction: jr2 lands meaningfully above jr1's +3.08R,
with the 06-04 A5-shape and 06-01 A2-shape trades the main carriers. If
jr2 does NOT improve on jr1, the miss is in agent behaviour, not
geometry — look at what TP2s were actually named and what the manager did
at TP1.**

## 50/50 status, restated while we are here

Chosen on the N≈45 sweep for prop survival (94% pass, WR intact — his
priority: equity shape over max P&L). Evidence since: a 75/25-vs-50/50
tracker at ±0.05R by n=3 (noise), and a −2.88R "cost of the TP1 partial"
measured on a book where TP2s mostly did not exist — **structurally unfair
to the split, which only pays when the runner has a destination.**
Verdict: inconclusive by construction; jr2 + jl1 decide. Decision rule
pre-stated: judge 50/50 vs 75/25 on (1) win rate, (2) `mc_prop` pass
simulation, (3) week R — in that order, his stated priority.
