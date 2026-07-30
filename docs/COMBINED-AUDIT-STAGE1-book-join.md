# Combined audit — Stage 1: joining the NY and London books

**Fit only. Sealed 2023/24 never loaded.** Both books at 1 NQ lot here so the correlation is not an artifact of two different sizing schemes.

- NY book: 264 trades on 202 days
- London wall arm: 187 trades on 107 days
- **Days both traded: 84** | NY-only: 118 | London-only: 23

## Day-level P&L correlation

| basis | n days | Pearson r | Spearman |
|---|---|---|---|
| all days in either book (absent = $0) | 225 | -0.033 | -0.041 |
| days BOTH traded | 84 | -0.066 | -0.081 |

## Loss-day coincidence vs independence

On the 84 shared days: NY loses on 57.1%, London on 38.1%.

- **Observed both-lose: 21.4%** (18 days)
- Independence predicts: 21.8% (18.3 days)
- Ratio observed/expected: **0.98x**

Losses cluster LESS than independence predicts — the diversification benefit is better than a naive correlation read suggests.

## Measured clock overlap — all times **America/New_York (ET)**

| book | earliest fill | latest fill | median |
|---|---|---|---|
| NY (window 07:45-11:00 ET) | 8.02 | 10.20 | 8.43 |
| London (window 08:00-10:00 Europe/London) | 3.02 | 5.90 | 4.08 |

London's latest fill is 5.90 ET; NY's earliest is 8.02 ET. **Clock overlap of the ENTRY windows: none — a 2.12 hour gap.** London 08:00-10:00 Europe/London maps to 03:00-05:00 ET (04:00-06:00 on the ~20 DST-misaligned days), which ends 2.02+ hours before NY's 07:45 band opens.

**Entries never overlap; POSITIONS can.** 0 of 187 London trades (0.0%) are still open at 07:45 ET when NY's window opens. That is the only channel through which the two books can compete for the one-position constraint or the shared budget intraday.
