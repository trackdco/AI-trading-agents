# London V9 (MFE-armed giveback ratchet) — tournament + grid, real engine

**FIT ONLY. Same rev-3 census, fills, and score-0 veto as the management tournament
(`docs/LONDON-MGMT-TOURNAMENT.md`); only management differs. V9 has never been run on
London before this branch. 1 NQ lot.**

## Declared grid (before running)

`v9_arm_r` in {4.5, 6.0} (default 6.0) x `v9_lock_frac` in {0.4, 0.5, 0.7} (default
0.5) — 6 cells total, `v9_floor_r` fixed at the engine default 3.0 (not swept) and
`v9_max_risk_pts` fixed at None (not swept), both declared limitations. (6.0, 0.5) is
the default cell, built once and reused rather than recomputed in the grid pass.

## Head-to-head (V0/V1/V8/V9-default)

| arm | n | WR | meanR | net | maxDD | net/DD |
|---|---|---|---|---|---|---|
| V8 shipped (partial+trail) | 129 | 61% | +0.613 | $+18,941 | $958 | 19.8x |
| **V1 BE at +1R** | 130 | 29% | +0.758 | **$+22,665** | $1,310 | 17.3x |
| V0 set-and-forget | 115 | 35% | +0.586 | $+15,055 | $2,560 | 5.9x |
| V9 default (arm=6.0, lock=0.5) | 115 | 35% | +0.512 | $+13,040 | $2,935 | 4.4x |

V9 default is **last place** on every column. Its exit mix (77 stop / 38 target) is
nearly identical to V0's (75 stop / 40 target) — the arm=6.0 threshold is rarely
reached (only 33% of the book ever touches +2R at all; per this session's own
terrain measurement, reaching +6R is rarer still), so the giveback ratchet almost
never engages. At its default setting V9 is functionally V0 with a small drag, not a
distinct management style.

## Mechanism decomposition (S1.3) — V9 vs V1, the comparison that matters

115 shared trades (15 trades only in V1's book — selection drift via the
one-position-at-a-time day-stop walk, same disclosed pattern as every other arm
comparison in the tournament doc):

- **defense** (V1's LOSERS/scratches, n=83): **$-3,490** — V9 does WORSE than V1 on
  the population V1's BE rule exists to rescue.
- **offense** (V1's WINNERS, n=32): **$-2,015** — V9 also costs money on trades V1
  already handles well.
- **net delta: $-5,505.**

This directly tests the framing this branch's task was given: "V1's BE@1R already
rescues most of the 75-gated-trades-that-hit-+1R-and-finished-negative population, so
V9's marginal gain over V1 should be small." **The result is not a small marginal
gain — it is a clear loss, on both fronts.** V9 vs V8 shows the same shape: defense
$-942, offense $-3,486, net $-4,429.

## The grid — every cell (declared 6, 1 reused from the default run)

| cell | n | WR | meanR | net | maxDD | net/DD |
|---|---|---|---|---|---|---|
| arm=6.0 lock=0.5 (default) | 115 | 35% | +0.512 | $+13,040 | $2,935 | 4.4x |
| arm=4.5 lock=0.4 | 115 | 36% | +0.516 | $+13,510 | $2,560 | 5.3x |
| arm=4.5 lock=0.5 | 115 | 36% | +0.482 | $+12,600 | $2,935 | 4.3x |
| arm=4.5 lock=0.7 | 115 | 36% | +0.509 | $+13,360 | $2,685 | 5.0x |
| arm=6.0 lock=0.4 | 115 | 35% | +0.546 | $+13,950 | $2,560 | 5.4x |
| arm=6.0 lock=0.7 | 115 | 35% | +0.534 | $+13,640 | $2,685 | 5.1x |

**No cell comes close to V1 ($22,665) — the best cell (arm=6.0, lock=0.4, $13,950) is
still $8,715 short, a 38% shortfall.** Every cell lands in a tight $12.6k-$14.0k band,
all with n=115 (identical to V0's book size), confirming that lowering the arm to
4.5R does not meaningfully change how often the ratchet engages on this book — London
winners average +2.82R at peak (this branch's own terrain measurement,
`docs/PLAN-agents-capture-london.md` §5) and rarely run far enough past that for any
tested arm level to matter. One disclosed data note: all 6 grid runs (default + 5
cells) drop the same single 2025-11-27 Thanksgiving 5min short — it never resolves
under any set-and-forget-style management before the holiday session's bars end,
identical to the pre-existing V0/V9-default disclosure in the tournament doc.

## Verdict

V9 (MFE-armed giveback ratchet), at every declared setting, loses to plain V1 by a
wide margin on London's rev-3 book. The mechanism decomposition shows this is not a
close call decided by one bad cell — V9 loses on both defense and offense at the
default setting, and the grid shows the ratchet is nearly inert across the entire
tested range. **V1 (BE at +1R, run to the real structural target, no ratchet, no
partial) remains the best tested management for London.**
