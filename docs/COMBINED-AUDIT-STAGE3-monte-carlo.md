# Combined audit — Stage 3: funded-account Monte Carlo

**Fit only. Sealed 2023/24 never loaded.**

2,000 paths, 252 trading days each, seeded RNG (20260730).

**Day-level bootstrap keeping BOTH books in the same draw.** A drawn calendar day brings every trade that occurred on it, from both sessions, in original intraday order. The two books are never resampled independently — doing so would destroy the cross-book correlation this entire job exists to measure, and would flatter the combined distribution by manufacturing diversification that is not there.

Funded rules: start $50,000; $2,000 trailing EOD drawdown that locks at start once equity reaches $52,000; withdrawal threshold $53,000; a full $2,000 payout taken at $54,000 (leaving $52,000, i.e. $2,000 above start). Bust = end-of-day equity at or below the floor.

Both arms replay under the shared $800 budget, NY-first priority, London at 1 lot — so the comparison isolates London's addition, not a sizing change.

## Result

| | P(bust) | payout cycles (med / p90) | net payout (p10 / median / p90) |
|---|---|---|---|
| NY alone | **39.1%** | 28 / 40 | $4,000 / $56,000 / $80,000 |
| NY + London | **39.6%** | 35 / 47 | $4,000 / $70,000 / $94,000 |

## Does adding London raise or lower the distribution?

- P(bust): 39.1% -> 39.6% (**+0.4 pp**)
- Median net payout: $56,000 -> $70,000 (**$+14,000**)
- p10 (the bad tail): $4,000 -> $4,000

**Verdict: adding London raises payout but also raises bust risk.**

Caveat that travels with every number here: this is the FIT span bootstrapped. It assumes the future resembles 2025-06..2026-07 in both books, and the sealed 2023/24 holdout — the only untouched evidence — has not been run.
