# London TF conviction — twins, backing, and the per-TF ledger

**FIT ONLY. Sealed 2023/24 untouched. The frozen book is unchanged by this doc — variants are measurements, adoption is an ANGUS ruling.**

## 0. Integrity finding (REPORTED, NOT FIXED)

Same-order twins: **329 population groups / 713 rows** (TF grids detecting one level 1-4 min apart, converging on identical direction+entry+stop+fill — one resting order, simulated 2-4 times). On the cut book: **9 twin groups survive selection** = a doubled position at flat-1-lot sizing; plus **26/144 entries while a prior position was open** (doc §5 violation). Doc §1's 'simultaneous triggers → highest TF' can never fire as written (zero same-minute census collisions) and is not live-causal anyway — the LOWEST TF triggers first in 290/329 groups, so live behaviour is first-order-wins. ENGINE FLAG for Pat: 46/329 twin groups produce divergent simulated exits from the identical order (V8 management context leaks from the trigger candle); live there is one exit.

## 1. Per-TF cells on the book as it stands (cut@09:30; charged worst-of-4)

| tf | n | WR | mean R | Wilson LB | 2025 | 2026 | lift | p(worst-of-4) | grade | full-book n/WR/R |
|---|---|---|---|---|---|---|---|---|---|---|
| 1min | 17 | 41% | +0.321 | 22% | 7/57%/+0.42 | 10/30%/+0.25 | -0.309 | 0.577 | below-floor | 25/32%/+0.10 |
| 2min | 27 | 63% | +0.813 | 44% | 12/58%/+0.51 | 15/67%/+1.06 | +0.182 | 0.874 | hypothesis | 36/56%/+0.57 |
| 3min | 44 | 64% | +0.506 | 49% | 17/76%/+0.72 | 27/56%/+0.37 | -0.124 | 0.949 | hypothesis | 52/58%/+0.39 |
| 5min | 56 | 66% | +0.734 | 53% | 22/64%/+0.54 | 34/68%/+0.86 | +0.104 | 0.971 | hypothesis | 74/65%/+0.71 |

(Composition, not entry-rule quality — a TF cell mixes solo triggers with twin members. Sections 2-4 are the causal reads.)

## 2. Level backing — distinct TFs converging on the taken trade's order (the honest 'concurring timeframes' signal; charged worst-of-K)

| backing | n | WR | mean R | Wilson LB | 2025 | 2026 | lift | p(worst-of-K) | grade |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 126 | 62% | +0.613 | 53% | 54/63%/+0.48 | 72/61%/+0.71 | -0.018 | 0.958 | CALLABLE |
| 2 | 18 | 61% | +0.755 | 39% | 4/100%/+1.74 | 14/50%/+0.47 | +0.124 | 0.710 | below-floor |

(Backing counts twin rows in the book double where both survived selection; the count itself is knowable by fill time — every twin trigger precedes the shared fill. Prereg H1 declared this axis underpowered on candidates; same verdict applies unless the cells below say otherwise.)

## 3. Constitution variants, priced (cut@09:30 baseline)

| variant | n | days | net | WR | mean R | maxDD | 2025 | 2026 | twin groups | overlapped entries |
|---|---|---|---|---|---|---|---|---|---|---|
| V0 as-is (frozen) | 144 | 85 | $+21,801 | 62% | +0.630 | $1,435 | 58/66%/+0.57 | 86/59%/+0.67 | 9 | 26 |
| V-DEDUP-FIRST (live-causal) | 142 | 85 | $+19,284 | 61% | +0.584 | $2,185 | 56/64%/+0.53 | 86/58%/+0.62 | 0 | 19 |
| V-DEDUP-HIGH (doc reading) | 135 | 85 | $+19,754 | 61% | +0.615 | $1,300 | 56/64%/+0.53 | 79/59%/+0.68 | 0 | 17 |
| V-SERIAL one-at-a-time | 118 | 85 | $+16,866 | 61% | +0.600 | $1,000 | 49/63%/+0.51 | 69/59%/+0.66 | 0 | 0 |
| V-BOTH dedup-first + serial | 123 | 85 | $+15,729 | 60% | +0.561 | $1,710 | 49/63%/+0.51 | 74/58%/+0.60 | 0 | 0 |

## 4. Single-TF gate counterfactuals (a GATE change — hypothesis-grade by construction, own prereg if ever pursued)

| gate | n | days | net | WR | mean R | maxDD | 2025 | 2026 | twin groups | overlapped entries |
|---|---|---|---|---|---|---|---|---|---|---|
| 1min only | 19 | 18 | $+751 | 42% | +0.283 | $715 | 7/57%/+0.42 | 12/33%/+0.21 | 0 | 0 |
| 2min only | 34 | 28 | $+5,245 | 56% | +0.665 | $1,375 | 13/54%/+0.39 | 21/57%/+0.84 | 0 | 1 |
| 3min only | 46 | 36 | $+6,535 | 63% | +0.507 | $2,282 | 17/76%/+0.72 | 29/55%/+0.38 | 0 | 1 |
| 5min only | 60 | 50 | $+8,789 | 63% | +0.708 | $810 | 22/64%/+0.54 | 38/63%/+0.81 | 0 | 4 |

## Read this before quoting

- The §0 finding needs an ANGUS ruling regardless of the TF question: either doc §1/§5 bind London (a dedup/serial variant becomes the book → prereg re-anchors, runner re-rehearses) or the London rulings supersede them (frozen book stands; divergence recorded as a London ruling). What may NOT happen is opening the holdout under one reading and quoting it under another.
- Single-TF nets do not sum to the book: dropping TFs frees day-stop budget and slots on shared days.
- Every inferential number is charged worst-of-K within its section; nothing here re-opens the frozen config on its own.
