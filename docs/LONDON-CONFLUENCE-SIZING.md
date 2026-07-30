# London confluence sizing — 1.5x/0.5x, three readings priced

**FIT ONLY. Sealed span untouched. Sizing frozen at flat 1 lot live (ANGUS ruling); this doc measures, adopts nothing.**

## The cells first (cut@09:30 baseline, 144 trades)

| cell | n | WR | mean R | Wilson LB | 2025 | 2026 | grade |
|---|---|---|---|---|---|---|---|
| confluence 3 (high) | 40 | 70% | +0.681 | 55% | 19/89%/+1.04 | 21/52%/+0.36 | hypothesis |
| confluence 2 (low) | 104 | 59% | +0.611 | 49% | 39/54%/+0.34 | 65/62%/+0.77 | CALLABLE |
| both-wall | 102 | 63% | +0.759 | 53% | 37/65%/+0.71 | 65/62%/+0.79 | CALLABLE |
| exactly-one wall | 42 | 60% | +0.319 | 44% | 21/67%/+0.33 | 21/52%/+0.31 | hypothesis |
| A+ (B2 & both-wall) | 48 | 69% | +1.007 | 55% | 16/69%/+0.77 | 32/69%/+1.13 | hypothesis |
| not A+ | 96 | 58% | +0.442 | 48% | 42/64%/+0.50 | 54/54%/+0.40 | CALLABLE |

**confluence_count is an ERA CROSSING** — high-confluence was the best cell in 2025 (89%/+1.04) and a below-average cell in 2026 (52%/+0.36); low-confluence moved the other way. The same shape that rejected risk floor 5 (prereg §1). The wall and A+ axes do NOT cross.

## Ladders at matched total risk (flat book risk = the budget)

| ladder | net | 2025 net | 2026 net | maxDD (trade) | net/maxDD | zero-edge net |
|---|---|---|---|---|---|---|
| flat 1.0 | $+21,801 | $+8,252 (+0) | $+13,549 (+0) | $1,435 | 15.2 | $+21,801 |
| L-CONF 1.5 conf3 / 0.5 conf2 | $+22,934 | $+11,670 (+3,418) | $+11,264 (-2,285) | $2,697 | 8.5 | $+21,342 |
| L-WALL 1.5 both / 0.5 one | $+25,168 | $+8,957 (+704) | $+16,211 (+2,663) | $1,640 | 15.4 | $+21,950 |
| L-APLUS 1.5 A+ / 0.5 rest | $+29,017 | $+9,359 (+1,107) | $+19,657 (+6,109) | $1,432 | 20.3 | $+22,539 |

(Parentheses = delta vs flat within the era, at identical deployed risk.)

## Verdict

- **L-CONF fails the era test before it gets to pricing.** Whatever its pooled number, sizing up 3-type clusters is a 2025 trade that 2026 punished; the axis crosses eras, and the project's standing rule (the floor-5 precedent) is that era crossings are disqualifying, not averageable.
- **L-WALL is the same instinct pointed at an axis that does not cross** — both-wall beats exactly-one in 2025 AND 2026, with prior tier-test evidence (permutation p=0.0085). If 'size the confluent trades bigger' becomes a rule post-holdout, THIS is its defensible form.
- **L-APLUS concentrates harder** (adds the B2 requirement) at the cost of resting on an axis never guard-tested. Declared candidate, one rung more speculative than L-WALL.
- Nothing here ships now: flat 1 lot until the holdout validates the book, then the sizing decision is made against these pre-declared numbers (prereg S2 is the declared descriptive input for the wall split).
