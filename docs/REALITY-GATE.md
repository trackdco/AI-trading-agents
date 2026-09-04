# Reality gate

`scripts/reality_gate.py` runs on every trade dump before its results are read. It measures
believability, not edge. If any hard check trips, the script exits 1 and **the summary is not
quoted anywhere**: not in a FINDINGS file, not on the tearsheet, not in chat.

```
python3 scripts/reality_gate.py DUMP.jsonl.gz [more dumps] [--depth 3.0 --target 1.0] [--cost-pts 0.5]
```

## Hard checks (any one = find the modelling error first)
| check | limit | what it caught on 2026-09-04 |
|---|---|---|
| winners that exited on their own fill bar | > 5% | 73% |
| win rate above break-even for the target size | > +15 points | +15.9 |
| annualised Sharpe of daily net R | > 3 | 19.1 |
| worst day equals the max drawdown (200+ days) | within 1% | identical |
| no losing month (12+ months) | 0 red months | 0 of 45 |

## Soft checks (warnings)
median hold under 2 minutes; net edge under 3x the cost per trade; over 3% of exits on bars that
touched both stop and target.

## Benchmark rule (added 2026-09-04, from the overnight-drift test)
Any long-biased or time-of-day strategy must beat **buy and hold of the same instrument** on BOTH
raw return and risk-adjusted return, and that comparison must be declared in the pre-registration.
The overnight test passed all three of its declared conditions and was still worthless, because
holding NQ around the clock beat it on every tape. A positive result in a rising market is not an
edge until it beats owning the thing.

Also: on any continuous futures series that is not back-adjusted, exclude the quarterly roll window
before measuring session or overnight returns. On 2023-26 the roll accounted for ~40% of the apparent
overnight return.

## The rule
1. Every new dump goes through the gate before anyone looks at the P&L.
2. A tripped gate is a bug hunt, not a caveat. First suspects, in order: an exit decided inside the
   fill bar (`--exit-next-bar`), a fill assumed on touch, a level computed with later data.
3. Before any holdout, audit, Monte Carlo or sizing work: replay a few days on 1-second data
   (`scripts/sec_replay.py`) and run the rules in a second simulator you did not write.
4. Shadow before believing.

Proof it works: on the original armed empire it trips all five hard checks; on the corrected re-run it
trips none (`docs/FINDINGS-reality-gate-demo.txt`).
