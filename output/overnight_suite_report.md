# Overnight suite — February 2026 (pass 10)

_Generated 2026-07-17 17:47 ET. All arms on the committed Feb slice; E3/E4 = entry variants; 'walkout' = P5.16 ruling; 'PCE-list' = P5.14 named high-impact list._

**GUARDRAIL:** Phase B/C exclusions are February-derived CANDIDATES — they become rules only after surviving Mar–Jul out-of-sample (data pending re-pull, Brake). Phase A items are Angus rulings and stand on doctrine.

| arm | tr | wins | win% | totR | R/tr | avgW | avgL | PF | maxDD | top2% | M | Mwon |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 baseline (pre-rulings) | 44 | 9 | 20.5% | +31.08 | +0.706 | +6.16 | -0.70 | 2.27 | 8.70 | 83% | 6 | 2 |
| A1 +walkout | 52 | 12 | 23.1% | +28.76 | +0.553 | +4.54 | -0.64 | 2.12 | 9.46 | 89% | 8 | 2 |
| A2 +E4 only | 46 | 15 | 32.6% | +12.08 | +0.263 | +2.86 | -1.00 | 1.39 | 10.43 | 141% | 5 | 4 |
| A3 +PCE-list | 45 | 8 | 17.8% | +19.11 | +0.425 | +5.65 | -0.71 | 1.73 | 10.14 | 134% | 6 | 2 |
| A4 walkout+list+E4 | 47 | 13 | 27.7% | +5.30 | +0.113 | +3.10 | -1.03 | 1.15 | 15.41 | 320% | 8 | 1 |
| A4b walkout+list (E3) | 53 | 13 | 24.5% | +31.04 | +0.586 | +4.31 | -0.62 | 2.25 | 10.62 | 83% | 8 | 2 |
| B1 A4b(E3) -5min | 50 | 12 | 24.0% | +27.81 | +0.556 | +4.45 | -0.67 | 2.09 | 9.31 | 92% | 6 | 2 |
| B2 A4b(E3) -B2 | 52 | 12 | 23.1% | +28.34 | +0.545 | +4.42 | -0.62 | 2.15 | 10.63 | 91% | 8 | 2 |
| B3 A4b(E3) -unclassified | 50 | 12 | 24.0% | +29.73 | +0.595 | +4.50 | -0.64 | 2.23 | 9.70 | 86% | 8 | 2 |
| B4 A4b(E3) -5min-B2 | 50 | 12 | 24.0% | +28.77 | +0.575 | +4.45 | -0.65 | 2.17 | 9.66 | 89% | 7 | 2 |
| B5 A4b(E3) A/B only 1-3min | 44 | 12 | 27.3% | +31.65 | +0.719 | +4.49 | -0.69 | 2.43 | 8.74 | 81% | 7 | 2 |
| B6 A4b(E3) -1min | 52 | 12 | 23.1% | +27.25 | +0.524 | +4.35 | -0.62 | 2.09 | 9.96 | 94% | 10 | 2 |
| B7 baseline(A0) -5min-B2 | 38 | 9 | 23.7% | +36.79 | +0.968 | +6.16 | -0.64 | 2.97 | 6.45 | 70% | 4 | 2 |
| C1 A4b(E3) +touch | 53 | 11 | 20.8% | +22.58 | +0.426 | +4.20 | -0.56 | 1.96 | 8.58 | 96% | 9 | 1 |
| X1 E4 + A/B-1-3min (pre-rulings) | 30 | 8 | 26.7% | +10.48 | +0.349 | — | — | 1.46 | 6.62 | 162% | 5 | — |
| **X2 E4 + A/B-1-3min + rulings** | 44 | 16 | **36.4%** | +16.22 | +0.369 | — | — | 1.59 | 12.63 | 105% | **10** | — |

## The morning read (Angus: start here)

Three distinct frontiers emerged — pick by what you optimize:

1. **Consistency/money frontier — B7** (pre-ruling engine, no 5min, no B2): **+36.79R,
   PF 2.97, maxDD 6.45R, R/trade +0.97, top-2 share 70%** (the LEAST tail-dependent arm).
   Caveats: only 38 trades, just M4 of your 28, and it runs the PRE-ruling engine (no
   walk-out, strict red-folder) — the exclusions interact with the rulings (they rescue
   some of what the filter cuts).
2. **Win-rate/your-style frontier — X2** (E4 market entry + A/B patterns on 1-3min + your
   rulings): **36.4% win rate** (goal: 40) and **M10 — the engine's best capture of your
   actual trades**. Cost: +16.22R (E4 pays slippage and worse entries; avg winner shrinks).
3. **Rule-compliant balanced — A4b** (your two rulings on E3): **+31.04R, 24.5% win, M8** —
   same money as the old baseline with more of your trades and a better win rate. This is
   the honest "current rulebook" engine.

Attribution singles: walk-out (A1) = +2 MATCH, +2.6% win, −2.3R. PCE-list (A3) = −12R in
Feb (unblocked mornings added losers — doctrine ruling, revisit only with out-of-sample
evidence). E4 (A2) = +12% win rate, −19R (fills everything, pays for it; its matched
trades WON 4/5 vs 2/6 for E3 — it exits your setups the way you do).

**No arm reached 40% win.** The residual gap to your winners is no longer detection or
rules — with X2 the engine takes 10 of your 28 and the remaining misses are mostly
sequencing (stuck in an earlier trade / daily cap) which shrink as junk entries drop.

**Next steps (in order):** (1) out-of-sample Mar–Jul for the top three arms the moment the
full dataset lands (nothing tonight is a rule until it survives that); (2) the Feb-25
stop-placement bug (detector emits ~1pt stop_ref on displacement bars — clips the +12.98R
monster in every arm); (3) decide B7-vs-X2-vs-A4b (or a hybrid: E4 entries with B7's
exclusions on the ruled engine = untested).

## Best arm by total R: B7 baseline(A0) -5min-B2

### By pattern

| value | trades | win% | totR |
|---|---|---|---|
| A | 10 | 40% | +19.18 |
| B | 16 | 25% | +14.72 |
| unclassified | 12 | 8% | +2.90 |

### By timeframe

| value | trades | win% | totR |
|---|---|---|---|
| 1min | 9 | 22% | +2.79 |
| 2min | 17 | 29% | +16.80 |
| 3min | 12 | 17% | +17.21 |

**Best win-rate arm:** A2 +E4 only — 32.6% (+12.08R)
