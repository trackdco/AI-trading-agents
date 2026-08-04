---
date: 2026-08-04
status: greenlit
tags: [ny-pre, overnight-structure]
sources: ["articles/sweep-2026-08-04-nypre-structure.md#S1", "articles/sweep-2026-08-04-nypre-stats.md#T1"]
---

# nypre-on-polarity — enter toward the overnight extreme the open predicts

## Thesis (for Angus)

The strongest published pre-open statistic on NQ: where price opens relative to
the overnight midpoint predicts which overnight extreme breaks first at ~76%
(82–84% with an aligned gap), on 2,827 days — and the break comes fast (a third
inside the first 5 minutes, median 09:41). The wrong side is the overnight
positioner whose stops sit at the near extreme; their stops are the fuel. Our
version enters 09:20–09:29, BEFORE the bell, converting a published at-open
stat into an approach-window trade — positioned before the ORB crowd arrives.
Depth gets used INVERSELY to your canon: skip when a wall blocks the path to
the target (the canon wants walls; this wants clear air).

## Skeleton

09:20: ON range/midpoint/location + gap agreement → enter toward predicted
extreme on a 1-min close holding the midpoint side. Target: ON extreme, runner
0.5–1× extension. Stop: midpoint. Time-stop 10:30. CVD slope agreement optional.

## Flags

- Candles-only. Event-tree pair with `nypre-open-sweep-fade` — one family.
- **Holds through 09:30** — needs the execution-semantics ruling (canon rule K
  flattens pre at 09:30; this deliberately doesn't).
- Stat published late 2025 → 2026 out-of-sample decay check mandatory.
- Canon redundancy: MEDIUM-HIGH (same clock; different logic — level-run vs
  wall-backed pullback). Pairwise vs canon pre fills at census.

## Trial ledger — NYP-POL-01

### Trial 1 — L0 census (2026-08-04, per PREREG spec)

**The published stat REPLICATES on post-regime data.** 2025: 94% of days break
an ON extreme; predicted side first **77.2%** (n=241; upper→ONH 77.0%,
lower→ONL 77.4%). 2026: **74.4%** (n=129; 74.0%/75.0%). Kill 1 (<60%) passed
comfortably both eras; no era flip; symmetric both directions; 2026 is the only
clean post-publication read and shows minimal degradation (76%→74%). Status:
census PASSED → proceed to L1 (entry/exit mechanics + costs, both the
flat-by-09:29 and carry-through variants).

### Trial 2 — L1 mechanics, first expression (2026-08-04)
09:20 entry toward predicted extreme, stop ON-mid, target extreme, TS 10:30,
1pt friction: LOSES both eras (−472 pts n=238; −404 pts n=136; −$843/−$3,744
at $160-risk). The 77/74% race odds are real but the geometry is uneconomic:
by 09:20 price sits near the predicted extreme — small reward, huge midpoint
stop. Base rate ≠ edge. Status: REFINING within family — next trials must fix
geometry (reward/risk ≥1 filter; pullback entries toward mid; earlier
measurement), each ledgered. Expectancy-below-cost kill fires if geometry
trials fail both eras.
