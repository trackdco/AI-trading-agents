# NYA-LVL-01 — placebo null on the depth result

Authorised by `docs/PREREG-level-interaction-depth.md`, declared before the depth pass ran. 100 permutations, seed 20260805.

Six random lines drawn from the same day's pre-RTH range, identical touch
grammar, identical depth join, and the **whole 5-check x 5-payoff selection
re-run** — because selecting W-at-2R out of that grid is what actually happened.

| | value |
|---|---:|
| observed family-wise best | **+0.7082 R/trade** |
| null median | +0.7509 |
| null 95th pct | +0.8837 |
| null 99th pct | +0.9397 |
| **family-wise p** | **0.7500** |

**Declared bar p <= 0.01. Result: FAIL.**

Random lines in the same price zone reach the same best cell. The depth
result does not survive its own selection correction.
