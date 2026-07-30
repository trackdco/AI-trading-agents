# Combined job — Stage 2: chronological combined replay, shared $800 budget

**Fit only. Sealed 2023/24 never loaded.**

NY = the VERIFIED lucid canon: 920 trades, 230 days, **$+90,015**. `pl` already carries the real spine (base $150 static -> tiers $75/150/225/300, soft de-risk to half at -$280, ramp under $1k buffer, elite 2.0x capped 1/day); `risk_d` is the dollar risk that spine allocated. This job CONSUMES the spine rather than re-deriving it.

London flat 1 NQ lot. Budget rule: `realized losses + new risk <= $800`, chronological, causal — no ordering uses information from later in the day.

**Causally implementable rules only.** London fills 03:02-05:54 ET; NY opens 07:45 ET. Anything requiring foreknowledge of NY's setups is excluded. So: (a) clock order, (b) a reserved London sub-budget swept $0-$400 in $50 steps.

## Arm: window-end x uncapped

London standalone: 187 trades, $+22,795

| rule | NY blk | LON blk | combined net | vs NY-alone | worst day | maxDD | months green |
|---|---|---|---|---|---|---|---|
| clock order | 58 | 0 | $+109,060 | **$+19,045** | $-797 | $1,528 | 14/14 |
| reserve $0 | 20 | 187 | $+90,249 | **$+234** | $-762 | $1,603 | 13/13 |
| reserve $50 | 20 | 187 | $+90,249 | **$+234** | $-762 | $1,603 | 13/13 |
| reserve $100 | 20 | 187 | $+90,249 | **$+234** | $-762 | $1,603 | 13/13 |
| reserve $150 | 20 | 187 | $+90,249 | **$+234** | $-762 | $1,603 | 13/13 |
| reserve $200 | 22 | 165 | $+91,825 | **$+1,810** | $-762 | $1,534 | 13/13 |
| reserve $250 | 27 | 117 | $+102,074 | **$+12,059** | $-762 | $1,528 | 14/14 |
| reserve $300 | 27 | 96 | $+103,025 | **$+13,010** | $-762 | $1,528 | 14/14 |
| reserve $350 | 27 | 89 | $+102,043 | **$+12,028** | $-762 | $1,528 | 14/14 |
| reserve $400 | 28 | 83 | $+103,675 | **$+13,660** | $-762 | $1,528 | 14/14 |

## Arm: 22pt x 2/session

London standalone: 137 trades, $+18,105

| rule | NY blk | LON blk | combined net | vs NY-alone | worst day | maxDD | months green |
|---|---|---|---|---|---|---|---|
| clock order | 38 | 1 | $+110,916 | **$+20,901** | $-788 | $1,528 | 14/14 |
| reserve $0 | 20 | 137 | $+90,249 | **$+234** | $-762 | $1,603 | 13/13 |
| reserve $50 | 20 | 137 | $+90,249 | **$+234** | $-762 | $1,603 | 13/13 |
| reserve $100 | 20 | 137 | $+90,249 | **$+234** | $-762 | $1,603 | 13/13 |
| reserve $150 | 20 | 137 | $+90,249 | **$+234** | $-762 | $1,603 | 13/13 |
| reserve $200 | 21 | 120 | $+91,168 | **$+1,153** | $-762 | $1,534 | 13/13 |
| reserve $250 | 27 | 74 | $+101,703 | **$+11,688** | $-762 | $1,528 | 14/14 |
| reserve $300 | 27 | 54 | $+104,030 | **$+14,015** | $-762 | $1,528 | 14/14 |
| reserve $350 | 27 | 48 | $+103,378 | **$+13,363** | $-762 | $1,528 | 14/14 |
| reserve $400 | 28 | 44 | $+104,359 | **$+14,344** | $-762 | $1,528 | 14/14 |

## Day-level correlation on the CORRECT NY series

(the earlier ~0 was measured on the deleted pre-rebuild book)

| basis | n days | Pearson | Spearman |
|---|---|---|---|
| all days either book | 248 | +0.006 | +0.017 |
| days both traded | 89 | -0.005 | +0.036 |

**Loss-day coincidence** on 89 shared days: NY loses 32.6%, London 39.3%. Observed both-lose **13.5%** vs independence 12.8% (ratio **1.05x**).
