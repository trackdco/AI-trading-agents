# Hand log — scope ruling

**Ruling date 2026-08-07. Authority: Amendment A1 in `strategy-definition-v1.0.md`.**

`feb2026_hand_log.csv` is unmodified and stays that way — it is Angus's raw evidence. This
file records which of its 28 rows are in scope for testing the frozen spec, and why.

## The ruling

The entry window is now **RTH 09:31–16:00 ET with the first tradeable signal bar at 09:36**.
Nine trades were entered before 09:36 and cannot be produced by the frozen spec.

**They are OUT OF SCOPE, not deleted, and not discredited.** They are evidence of what the
discretionary version of the strategy did. They are not evidence about what the frozen spec
will do, because the frozen spec cannot take them. Those are different claims and only the
second one is being tested.

## Out of scope — 9 trades

| Date | Entry | Dir | TF | Result | R | Why out |
|---|---|---|---|---|---|---|
| 2026-02-20 | 08:06 | long | 3M | win | +4.79 | before 09:36 |
| 2026-02-24 | 08:20 | long | 5M | win | +3.67 | before 09:36 |
| 2026-02-18 | 08:35 | short | 5M | win | +4.17 | before 09:36 |
| 2026-02-19 | 09:00 | short | 5M | loss | −0.35 | before 09:36 (also a discretionary close, unreproducible by any mechanical exit) |
| 2026-02-26 | 09:18 | short | 3M | win | +4.22 | before 09:36 |
| 2026-02-25 | 09:25 | long | 5M | win | **+12.98** | before 09:36 — largest single trade in the log |
| 2026-02-20 | 09:31 | long | 1M | win | +3.18 | inside the 09:31–09:35 entry blackout |
| 2026-02-17 | 09:32 | long | 1M | win | +3.69 | inside the entry blackout |
| 2026-02-13 | 09:33 | long | 3M | loss | −1.00 | inside the entry blackout |

Seven of the nine are winners. Removing them lowers the sample's apparent quality, which is
the point: the in-scope figure is the honest one for a spec that cannot trade before 09:36.

## In scope — 19 trades

| | |
|---|---|
| Trades | **19** |
| Wins | **13** (68.4%) |
| Wilson 95% | **[46.0%, 84.6%]** |
| Mean R | **+2.254R** (vs +2.792R across all 28) |
| Cost-adjusted breakeven | **40.6%** (1.5R floor, c/s = 1.53%) |
| One-sided binomial vs breakeven | **p = 0.0133** — clears at the lower bound |
| Sessions with ≥1 in-scope trade | **15 of 19** |

## Superseded figures — do not reuse

Two wrong numbers circulated before being caught, and both propagated through several
documents:

- **"22 wins / 28"** and the Wilson interval **[60.5%, 89.8%]**. The `Result` column reads
  **20 win / 7 loss / 1 BE**. The 22 figure never matched the file.
- **"66.7% breakeven"**. That is cluster α's figure at reward:risk 0.5. This strategy has a
  **1.5R floor** (§6.5) and realised **+3.678R** on **in-scope** hand-log winners, so its
  breakeven is ~40%, not 66.7%.
- **"+4.23R on winners"**. That is the mean over all 20 winners in the FULL log and includes
  the **+12.98R** trade of 2026-02-25 09:25, which this very document lists as out of scope
  under A1. The in-scope figure is **mean 3.678, median 3.370, max 5.98, n = 13**.
  *(Corrected 2026-08-08; the file previously contradicted itself on this line.)*

Neither figure should appear again in relation to this strategy. Where 66.7% still appears in
`research/star-trading/`, it is correct — those documents are about cluster α.

## What the in-scope sample can and cannot do

It **can** serve as the hypothesis that motivated the study: 13/19 clears cost-adjusted
breakeven at its Wilson lower bound, which is a real signal worth spending a study on.

It **cannot** serve as the calibration target spec-1 Step 8 was written around. That step
matches engine output against these 28 trades on (date, direction, entry time), and the
February 2026 bars those trades occurred in **are not in the held data** — coverage ends
2026-01-30. See `research/vwap-bb/preflight.md` gate 5.
