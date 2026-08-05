---
date: 2026-08-07
kind: locked exit convention — binds every zxck- card so its trades pool with ash-unicorn-sb
authority: scripts/ash_raw_baseline.py (the code that produced ash-unicorn-sb-raw-trades.csv)
verified against: research/ash10hazard/strategies/ash-unicorn-sb-raw-trades.csv (n=37)
---

# The locked exit convention

For zxcked trades to pool against `ash-unicorn-sb`, both books must be scored on the **same
exit**. Otherwise a difference in outcome is a difference in bookkeeping, not in edge.

## What `ash-unicorn-sb` was actually scored on

Read from `scripts/ash_raw_baseline.py` and **verified against its 37-row trade log**:

| # | rule | verification |
|---|---|---|
| 1 | **Target = entry ± 2 × risk** (A3) | `target` matches `entry ± 2·risk_pts` on all 37 rows, **max deviation 0.0** |
| 2 | **Stop = the card's own structural invalidation**, and it defines R | `risk_pts = \|entry − stop\|` |
| 3 | **Break-even at 1R** — once price reaches entry ± 1 × risk, the stop moves to entry (A4) | `be_moved` is True on all 10 BE rows and 14 of 15 wins; False on all 12 losses |
| 4 | **No trailing** beyond that single move (A5) | R takes only three values: **−1.0, 0.0, +2.0** |
| 5 | **Same-bar stop and target → the STOP fills first** (A8) | conservative by construction |
| 6 | **Horizon capped at 16:00 ET**; anything unresolved marked to that close as fractional R (A7) | latest actual exit **11:43**; the cap never bound in this sample |
| 7 | `R = (exit − entry) / risk`, signed by direction | |
| 8 | **Costs are NOT baked into R.** $25/round-turn NQ ($5 commission + 1 tick slippage each way) is reported as a separate `expectancy net` line | median stop 25.5pt ⇒ 0.053R/trade |

**Outcome vocabulary: `win` = +2R · `BE` = 0R · `loss` = −1R · `timeout` = fractional R at the cap.**

## What is now LOCKED for every zxck- card

> **Identical to the above, in full.** Target 2R, break-even at 1R, no trailing, stop-first on a
> same-bar conflict, capped at 16:00 ET, R signed by direction, costs reported separately.

Each card keeps its **own stop rule**, because the stop is what defines R and it is part of the
strategy. Everything downstream of the stop is the shared convention.

### ⚠️ Powell's own exits are NOT what we score on

His break-even and trailing are **explicitly Apex-driven**:
> *"I prefer to go break even because with these Apex accounts I have some pretty aggressive
> trailing drawdown."* `[5pL41Pl7GM4 @ 24:46]`
> *"the reason that I'm that aggressive with my stops, even on micros, is because I'm on 14
> accounts."* `[rQUMdf1gLJk @ 04:02]`
> trailing ladder: to the trigger low → below the last 1m/3m/5m order block → to each validated
> swing low `[rQUMdf1gLJk @ 00:50–02:00]`

And his target band is **1:3 minimum, 1:4–1:6 typical** `[WEeXKMzaJjY @ 15:56]` — **not 2R**.

**All of it stays on the cards as `[trader-claimed, unverified]` colour, and none of it is
scored.** Two consequences, stated in advance so nobody discovers them later:

1. **Our 2R target is BELOW his stated band.** A 2R scoring will systematically produce different
   numbers from his 1:4–1:6 claims. Any comparison to his quoted R-multiples is **not
   like-for-like** and must say so.
2. **A trailed exit is not a fixed-target exit.** His R-multiples come from trailing; ours cannot
   reproduce them by construction. This is a deliberate choice in favour of poolability, not an
   attempt to model him faithfully.

### Why lock at 2R rather than at his band

Because the purpose of this pass is **pooling**, and `ash-unicorn-sb` is already scored, already
in the trial ledger, and already carries the AM1 narrowing. Re-scoring 37 existing trades to
match Powell would spend a fresh look on a sealed result. **The book that has not been tested
moves to the convention of the book that has.**

A separate `zxck-*-hisexit` arm at 1:4 with structure trailing is a legitimate future trial —
**as a second arm in the ledger, not as a replacement**, and it would need its own prereg.
