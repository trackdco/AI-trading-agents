# PREDICTION P12 — order-flow / data features (filed 20 Jul, before any data lands)

Pre-registered so Brake's tests grade the hypothesis, not hindsight. Reference base:
2026 champion journal 146 trades (+$13,857 as-traded); 2026 oracle+SD floored ceiling
$48,110; measured loss pools = 44 give-backs (hit +1R then reversed, ~$35k peak-to-loss
swing) + 45 entry-misses (never reached +0.5R, ~$18k of losses).

## The conceptual claim (the thing to verify first)

READ features (VIX, cross-market) lift AGENT CAPTURE of a fixed ceiling; they do NOT
lift the ceiling (oracle already selects books with perfect hindsight). TRADE-LEVEL
features (CVD, heatmap) lift the CEILING ITSELF + the champion + capture, because they
change per-trade outcomes (entry filtering, exit timing), not just selection.

## Per-feature hypothesis (wide error bars; testing WILL discount)

| feature | champion 2026 | oracle ceiling 2026 | agent capture | confidence |
|---|---|---|---|---|
| VIX + cross-market | ~flat | flat | +2-5 pts | med |
| CVD entry filter | +$4-7k | +5-12% | (via champion) | low-med |
| CVD + heatmap exit | +$8-14k | +10-25% | (via champion) | low-med |
| **CVD+heatmap combined** | **$14k → $25-35k** | **$48k → $55-65k** | **the big lever** | **low-med** |

Biggest structural claim: CVD+heatmap could turn the champion GREEN in the red years
(2023-25), because give-backs + hollow entries are what bleed those years.

## The discount rules (the honest part — after the stop sign-error lesson)

1. DETECTION != CAPTURE. The wick test detected 45% of give-backs; a wick exit
   false-positives on the 22% of winners that also wick, and those eat the gain. Score
   CVD on NET dollars after false positives, never on detection rate.
2. OOS shrinks everything — grade in >=3 of 4 years, never one era.
3. If the honest net is half the low end, that is still a large win. Do not chase the
   upper numbers; bank the robust floor.

Grading: Brake's CVD footprint -> engine re-runs the give-back + entry-miss autopsies ->
net-dollar effect per year. Heatmap -> the exit-magnet / wall studies. This doc gets a
PASS/PARTIAL/FAIL per row when each dataset lands.
