# London funded test — flat $250 risk/trade, MNQ micros (cut@09:30 baseline)

**FIT ONLY. Sealed untouched. Measurement for the funded lane — nothing deploys before the holdout + ANGUS sizing decision.** Sizing convention = `baseline_dollar_risk.py`: micros = min(40, round($250 / (stop_pts x $2))), pl = micros x dollars_1lot / 10.

## The funded books

| book | n | net | maxDD (trade) | worst day | months green | worst month | avg micros (range) | avg $ risk | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| OVERLAY flat $250 (frozen selection) | 144 | $+22,030 | $1,231 | $-531 | 12/14 | $-593 | 9.5 (3-13) | $249 | $+7,996 / dd $981 | $+14,034 / dd $782 |
| REWALK flat $250 (day stop on funded $) | 155 | $+21,462 | $1,311 | $-644 | 12/14 | $-741 | 9.4 (3-13) | $249 | $+7,996 / dd $981 | $+13,466 / dd $1,311 |
| OVERLAY wall ladder $375/$125 | 144 | $+29,550 | $1,950 | $-971 | 12/14 | $-445 | 11.5 (2-20) | $301 | $+10,221 / dd $1,251 | $+19,329 / dd $1,214 |
| OVERLAY A+ ladder $375/$125 | 144 | $+22,373 | $1,096 | $-774 | 13/14 | $-301 | 8.1 (2-20) | $207 | $+6,774 / dd $792 | $+15,599 / dd $892 |

**Day-stop unit check:** overlay and rewalk DIVERGE — the day-stop unit (1-lot vs funded dollars) changes the book and needs an ANGUS/Vault ruling before any funded deployment.

## Reference points

- 1-NQ-lot book (the prereg convention): +$21,801, maxDD $1,435, avg risk/trade $286 (stop-dependent, $190-$725). The funded book risks a CONSTANT ~$250 — equal-dollar normalization shifts weight from wide-stop to tight-stop trades.
- Prop-eval frame (50K / $2K trailing / $400 Vault day stop): maxDD and worst-day above are the binding numbers. Rounding to integer micros on a 9.5-60pt stop book means actual risk wobbles around $250 — the avg $ risk column states realized truth.
- Ladder rows are the funded translation of the declared candidates in docs/LONDON-CONFLUENCE-SIZING.md; same evidence caveats apply (wall validated, A+ one rung more speculative).
