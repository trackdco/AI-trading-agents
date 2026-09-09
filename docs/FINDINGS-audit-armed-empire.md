# AUDIT — the armed NQ empire, adversarially re-derived (2026-09-03)

His instruction: *"do a full audit — find out if all the information and results
you gave me are true and not misleading or lying in any way. Run as many tests as
needed."* Ten stages, every one written fresh (no reuse of the scripts that
produced the numbers), run without supervision, reported as printed.

## Verdict

**Every headline number reproduces. No claim is false.** Seven points where the
page's wording is stronger or simpler than the exact truth are listed in §3 and
have been added to the page. The largest possible overstatement found anywhere is
**1.8% of total R** (§3.1), and it is a modelling convention, not an error.

## 1. What reproduced exactly

| stage | check | result |
|---|---|---|
| 1 | Headline: 61,194 trades, +0.1775 EV, +10,863R, +11.46 R/day, −14.0 maxDD, Sharpe 1.208, 91% green, 66.0% WR | **exact**, with an independently written rail (G3/G5/G6) |
| 1 | Flat baseline 75,481 / +0.1361 / +10,273 / −18.1 | exact |
| 1 | By year +2,280 / +2,918 / +3,108 / +2,557; 45/45 months; worst month +20.1 | exact |
| 1 | Arming drawdown-matched lift +33.3% / +38.2%; raw EV lift +30% | exact (+30.4%) |
| 1 | Risk bounds 5.0–30.0, TARGET r=+1, STOP r=−1, pts = r×risk, no fill before signal, no exit past session | all hold; 0 violations |
| 1 | News gate: fills 08:00–09:30 on 172 high-impact mornings | **0** |
| 1 | Rail counts: G5 bound 0×, G6 0×, no duplicate rows | exact |
| **2** | **Bar replay of 3,000 random armed trades (1,000 per book)** against the raw 1-minute tape: signal candle closed ≥3pt through the level, prior close on the other side, stop = one tick past the signal candle (+prior candle rule), floor/cap, arming reached ≥1R before the fill, fill strictly after the arming bar and the first one-tick-through touch, exit = first-touch order with ties as STOP, SAR at the opposing candle's close | **3,000 / 3,000 consistent** |
| 3 | Determinism: armed level book re-run from bars and diffed | 19,513 lines, **0 differing** |
| 4 | Funded sim, replicated under its own rules (30% haircut, eval $3k → funded $4k, 120-day cap, $2k EOD-trailing floor), 6,000 sims/cell, 948-day tape: armed payout 94.3 / 83.6 / **80.0** / 77.1% at 8/12/16/20 micros | claimed 93.9 / 84.1 / 81.2 / 77.0 — **within ~1 point** |
| 5 | Selection grid: (depth 3.0, 1R) best cell; 1R best at every depth; monotone in depth | exact |
| 6 | 2020–22 replication (flat +0.1348/−39.4, armed +0.1666/−30.1, +29.0%/+34.2%); 2017–19 (+0.070/−84.8, +0.103/−55.4, +135.7%/+71.9%); both VA-book holdout lines | exact |
| 7 | No-lookahead: prior-day high/low levels equal the prior session's high/low from bars | 396/400 (4 residuals are a different previous-session convention in my check, not future data); 0 signals at or before the open |
| 8 | Master tape: 1,299,540 bars, monotonic, unique, 0 OHLC-inconsistent, only holiday gaps; the 51 >200pt jumps are weekend opens, the April-2025 tariff days and NQ at 30k in June 2026 — all real | clean |
| 9 | Book correlations; every level family positive in both halves | see §3.4; families all positive |
| 10 | Queue (2 ticks: 71,390 / +0.1040 / +7,422 / −29.1) and latency (+1 bar +0.1173, +2 bars +0.0814) | exact |

## 2. Two bugs found — both in the audit, not the engine

- The dumps round times to 3 decimals (±1.8 s). My first replay did not snap to
  the minute and mis-indexed ~half the trades (48% "consistent"). The same leak
  bit the first conviction audit in August. Snapped: 100%.
- My SAR check read the close one bar late. The engine scores SAR at the
  opposing signal candle's close. Corrected: 100%.

## 3. Where the page is simpler than the truth — now disclosed on it

1. **Same-minute pairs (rail convention).** 545 kept trades fill in the same
   minute, same direction, same level as a trade that entered and exited
   *inside that fill bar* (hold 0 min). The rail treats the 0-minute trade as
   closed before the next fills; live, both limits rest and both would fill.
   The later trades earn **+198R = 1.8%** of the armed total. Strictest
   reading: +10,665R instead of +10,863R.
2. **"Ambiguity counts as a loss."** 2,244 ambiguous bars: 2,229 scored −1;
   **15** were pre-empted by an opposing close (SAR) and scored at that close,
   mean −0.63. None scored as a win. The VWAP dumps carry no `ambig` field at
   all, but all 236 tie bars sampled from them were scored −1.
3. **Sharpe 1.208 is a daily ratio.** Annualised (×√252) it is **≈19**, a
   figure no live book prints. The page already says "not a forecast"; it now
   says the number.
4. **Book correlations** are +0.18 (8-level × session-VWAP), +0.11, +0.13 —
   the page said "around +0.10". Now "+0.10 to +0.18".
5. **Roll days.** The 2023–26 master tape has no roll-day exclusion list (the
   holdout tapes do). The 14 first-post-roll sessions, whose prior-day levels
   come from the old contract, earned +17.5 R/day against +11.5 — **+86R
   (0.8%) above average days**. Small, borderline noise on 14 days, but it is
   a consistency gap: the holdouts excluded these days, the in-sample tape did
   not. Recommendation: build a roll list for the master and exclude them.
6. **G4 boundary:** 3 VWAP fills (of 61,194) sit inside an open same-direction
   level position within 5pt — all three at the exact same fill minute, a
   `<`/`≤` boundary. Negligible.
7. **16 micros at ≥80%** lands at **80.0%** on the fuller tape. On the line.

## 4. What this audit cannot say

It confirms the simulator computed what the rules say, on data that is what it
claims to be. It cannot confirm the rules describe live fills: queue position,
latency and cost are modelled (§10, and the cost sensitivity in
`FINDINGS-*`), not measured. That gap closes only in paper trading.

Scripts: `scripts/audit1.py` … `audit7_lookahead.py`, `audit4b_funded.py`.
