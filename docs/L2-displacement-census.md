# L2 CENSUS — the displacement-entry population, top-down (2026-08-06)

**Fit only, holdout sealed. ANGUS directive: restart from raw triggers —
"splitting winners from losers, running stop caps, going through all of that
again." No gates inherited from the sweep.** Harness:
`scripts/l2_displacement_study.py`; row-level grid in
`output/l2_displacement_caps.parquet`.

Entry: market at the open of the first 1m bar after the close-labeled signal bar.
Base stop: signal-candle adverse extreme ∓1 tick. Walk: stop-first, 1m bars, to
15:55. Population: 18,822 triggers (309 sub-2pt dropped, 6 gap-through-stop cases
per the conventions).

## 1. The census — the regime shift is in the raw candles

| era | n | candle risk p10/50/90 | ≥30pt share | rejection_block / displacement |
|---|---|---|---|---|
| 2025 | 11,407 | 4.2 / **12.2** / 37.0pt | **15.1%** | 7,973 / 3,434 |
| 2026 | 7,415 | 7.0 / **21.8** / 64.8pt | **36.3%** | 5,284 / 2,131 |

The same trigger definitions fire off candles nearly twice as large in 2026.
Any era comparison that ignores this is comparing regimes, not signals.

## 2. Stop caps — the candle stop is load-bearing; no cap rescues 2025

Full grid re-walked per cap (R in effective risk; net = 1 tick + $5/RT):

- **2025, every scope, every arm: no cap configuration is net positive.** Best
  2025 cells anywhere: gold cap-30 hold +0.034 / gold uncapped hold +0.030 —
  marginal, hold-arm (tail-carried) numbers. The 2R arm is net negative at every
  cap in both scopes (−0.061..−0.263).
- **Tightening the cap hurts 2025 monotonically** (ALL-sessions 2R net: −0.089
  uncapped → −0.224 at 5pt). Overriding the structural stop with an arbitrary
  tighter one destroys the geometry: stop% rises 89.6%→97.1% and WR falls.
  Verdict: **the candle extreme is the right stop for this entry; "stop below
  that candle" survives its first measurement.**
- **WARNING — do not chase the 2026 tight-cap hold cells** (ALL-sessions cap-7
  holdNet +0.336): capping divides P&L by a 5–7pt risk on structures whose
  median candle is 21.8pt, so the ~10% never-stopped runners get their R
  inflated 3–4×. It is a denominator/tail artifact concentrated in the confirm
  era — the exact class of 2026-only, tail-carried cell this program kills on
  sight. 2025 shows the truth: cap-7 holdNet −0.045.
- Base rates, uncapped: stop-touch **84–90%** of trades before 15:55; 2R WR
  31–34%; gross m2R ≈ −0.04 (2025) / +0.03..+0.04 (2026). The raw displacement
  census is breakeven-to-slightly-negative net in the discover era under EVERY
  stop geometry — entry+stop engineering alone does not make a book, same as the
  raw limit census didn't.

## 3. The winner/loser autopsy — the first ERA-STABLE structure in this population

Uncapped walk; eventual 2R-winners vs stopped losers, compared **while both are
still open** at fixed checkpoints (identical conditioning — the survivorship
guard):

| | 2025 | 2026 |
|---|---|---|
| median time-to-resolution W / L | **7m / 3m** | **7m / 3m** |
| 3m: still-open W / L | 66.6% / 48.4% | 65.6% / 45.8% |
| 3m: MAE median W / L | **0.333 / 0.476** | **0.331 / 0.469** |
| 5m: MAE median W / L | 0.359 / 0.516 | 0.370 / 0.510 |
| 10m: MAE median W / L | 0.405 / 0.580 | 0.440 / 0.579 |
| 30m: MAE median W / L | 0.530 / 0.632 | 0.521 / 0.670 |

Every entry-moment separator tested this week was era-fragile. The **in-trade**
structure is era-identical to two decimals: losers reveal themselves in ~3
minutes; winners that survive the first minutes carry materially less adverse
excursion at every horizon, in both regimes. This mirrors the original canon's
deepest lesson — the durable edge lived in trade management, not trigger
selection — and it is the mandate for the next stage: an early-cut /
management-ladder study (cut rules of the form "from minute m, if adverse ≥ θR,
exit at bar close"), era-split, net of costs, sacrifice rate reported.

## 4. Where the top-down program stands

1. ✔ census — regime shift quantified at the raw level
2. ✔ stop geometry — candle stop validated; caps rejected; 2026 tight-cap hold
   flagged as artifact
3. → early-cut ladder from the autopsy (in progress)
4. → fresh separation trial for entry features **against managed outcomes** (the
   canon's own pipeline order: the check trial judged features on engine-managed
   outcomes, not naive walks)
5. → sizing, assembly, era rule, and only then a frozen candidate for the one
   human-authorized holdout look
