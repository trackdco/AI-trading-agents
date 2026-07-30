# London robustness — cost stress, eval survival, perturbation

**FIT ONLY. Nothing here can flatter the strategy; every test is adverse or neutral. Frozen values do not move on any result below.**

## 1. Cost stress (on top of the engine's 1 tick/side + $2.50/side already charged)

| extra slippage | V8 stack net | V8 mean R | V1 stack net | V1 mean R |
|---|---|---|---|---|
| +0 tick/side | $+17,941 | +0.650 | $+22,360 | +0.855 |
| +1 tick/side | $+16,841 | +0.611 | $+21,250 | +0.816 |
| +2 tick/side | $+15,741 | +0.572 | $+20,140 | +0.777 |
| +4 tick/side | $+13,541 | +0.495 | $+17,920 | +0.699 |

V1-specific exposure: 47 BE-stop exits — each extra tick/side turns a $0 scratch into -$10/tick; that cost is inside the V1 column. Doubling commissions adds another -$555 to either book.

## 2. Monte Carlo eval survival — 50K / $2K trailing / +$3K target, $200 flat micros, 10,000 paths x 235 session pool

| book | P(bust) | P(pass) | median days to pass |
|---|---|---|---|
| V8 stack | **0.1%** | 99.9% | 50 |
| V1 stack | **0.1%** | 99.9% | 38 |

(iid day bootstrap — declared convention of the combined job; fit clustering was measured benign. Unresolved-in-250-days paths count in neither column.)

## 3. Parameter perturbation — one knob, one step, V8 outcomes

| knob | setting | n | mean R | net |
|---|---|---|---|---|
| risk floor | 8.5pt | 129 | +0.563 | $+17,601 |
| risk floor | 9.5pt * | 110 | +0.669 | $+17,941 |
| risk floor | 10.5pt | 90 | +0.712 | $+16,251 |
| window cut | 09:15 | 96 | +0.524 | $+12,401 |
| window cut | 09:30 * | 110 | +0.669 | $+17,941 |
| window cut | 09:45 | 129 | +0.613 | $+18,941 |
| veto thresholds | x0.9 | 113 | +0.630 | $+17,246 |
| veto thresholds | x1.0 * | 110 | +0.669 | $+17,941 |
| veto thresholds | x1.1 | 109 | +0.665 | $+17,734 |

(* = frozen value. PLATEAU = neighbors within ~15% of the frozen net; a CLIFF anywhere is a curve-fit warning to report, not tune away.)
