# London de-risk test — half size after a same-day realized loss

**FIT ONLY. Sealed untouched. Rules keyed on exited-before-fill outcomes only (what live knows). Sizing frozen live; measurement for the post-holdout decision.**

## 1. The signal — are post-loss trades actually worse?

| state at fill | n | WR | mean R | Wilson LB | 2025 | 2026 | grade |
|---|---|---|---|---|---|---|---|
| no same-day realized loss | 123 | 63% | +0.677 | 55% | 53/70%/+0.66 | 70/59%/+0.69 | CALLABLE |
| last exited trade LOST (R1 trigger) | 16 | 44% | +0.105 | 23% | 5/20%/-0.43 | 11/55%/+0.35 | below-floor |
| day's first trade LOST (R2 trigger) | 18 | 61% | +0.517 | 39% | 3/33%/-0.12 | 15/67%/+0.65 | below-floor |
| realized P&L <= -$250 1-lot (R3-ish) | 2 | 50% | +0.314 | 9% | 2/50%/+0.31 | — | below-floor |

## 2. The rules, priced (funded flat $250 baseline; halved = $125)

| rule | n | trades halved | net | maxDD | worst day | months green | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| FLAT $250 (baseline) | 144 | 0 | $+22,030 | $1,231 | $-531 | 12/14 | $+7,996 / dd $981 | $+14,034 / dd $782 |
| R1 last-loss -> half, win resets | 144 | 16 | $+21,907 | $1,231 | $-531 | 12/14 | $+8,299 / dd $857 | $+13,607 / dd $782 |
| R2 first-loss -> half rest of day | 144 | 18 | $+20,909 | $1,231 | $-531 | 12/14 | $+8,077 / dd $857 | $+12,832 / dd $782 |
| R3 realized <= -$250 funded -> half | 144 | 7 | $+21,560 | $1,231 | $-531 | 12/14 | $+7,948 / dd $857 | $+13,612 / dd $782 |

## Read it

- Judge each rule by what §1 says about its trigger cell: if the cell's expectancy is normal, the rule is a pure risk trade (less net, less DD) — legitimate as a RULING, but not an edge. If the cell is genuinely weak AND era-consistent, the rule earns its keep on expectancy too.
- Angus's original instinct for slot 2 was a HIGHER CONVICTION BAR after a loss, not a size cut (L4 escalation, currently inactive at London threshold 1.0/1.0). If §1 shows post-loss weakness concentrated in low-conviction cells, the bar beats the haircut and both should go to the post-holdout table together.
- All fit-side; trigger counts are small; era columns rule.
