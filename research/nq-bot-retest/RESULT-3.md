# RESULT-3 — confluence features and conviction sizing (PREREGISTRATION-3.md)

**Status: fit half measured and committed (b728d7d5), test half read once (2026-09-07). No feature
holds; conviction sizing not run, as §4 requires. This pre-registration is finished.**

## 0. Identity

| item | value |
|---|---|
| pre-registration | `PREREGISTRATION-3.md`, blob `d8278718…`, commit `30e6732f` — written before any feature was computed |
| trades | C1a×C3a sealed lists across 2018-09 → 2026-09 (9,822 featured of 9,824; two lacked a signal minute in the bar file); C1a×C3b as robustness (5,553) |
| features | twelve, computed by `features_study.py` from bars up to the signal bar only; table `data/features/features.parquet` (not committed, regenerable) |
| fit / test | entries 2018-09-01 → 2024-12-31 (7,364 trades) / 2025-01-01 → 2026-09-02 (2,460) |

## A. Fit half — candidates

Primary cell, C1a×C3a. Gap = best bucket minus worst bucket (n ≥ 200 each), block-bootstrap LB95.

| feature | best bucket | worst bucket | gap $ | gap LB95 | candidate |
|---|---|---|---|---|---|
| F1 session VWAP position | beyond 2σ | inside ±1σ | +6.73 | -1.88 | no |
| F2 VWAP direction | toward | away | +2.23 | -2.95 | no |
| F3 prior-day value area | below VAL | inside VA | +4.02 | -1.64 | no |
| F4 VA edge | at edge | not | +3.64 | -6.38 | no |
| F5 POC distance | >1.5 | <0.5 | +9.29 | -3.95 | no |
| F6 POC direction | away | toward | +2.07 | -2.48 | no |
| F7 prior-session Fibonacci | ≤0.25 | >0.75 | +3.70 | -4.66 | no |
| F8 overnight Fibonacci | ≤0.25 | 0.25–0.75 | +5.35 | -2.24 | no |
| F9 EMA200 trend | flat | with | +3.09 | -3.78 | no |
| F10 EMA20 distance | < −0.5 | −0.5–0.5 | +5.71 | -0.57 | no |
| F11 EMA50 side | against | with | +5.95 | +1.08 | YES |
| F12 opening range | forming | beyond in direction | +4.48 | -0.94 | no |

Robustness cell, C1a×C3b:

| feature | best bucket | worst bucket | gap $ | gap LB95 | candidate |
|---|---|---|---|---|---|
| F1 session VWAP position | beyond 2σ | inside ±1σ | +11.70 | -2.42 | no |
| F2 VWAP direction | toward | away | +5.94 | -1.84 | no |
| F3 prior-day value area | above VAH | inside VA | +4.30 | -3.77 | no |
| F5 POC distance | >1.5 | 0.5–1.5 | +3.51 | -8.53 | no |
| F6 POC direction | toward | away | +0.36 | -7.24 | no |
| F7 prior-session Fibonacci | ≤0.25 | 0.25–0.75 | +9.64 | -4.78 | no |
| F8 overnight Fibonacci | ≤0.25 | 0.25–0.75 | +6.22 | -4.82 | no |
| F9 EMA200 trend | against | with | +7.42 | -1.89 | no |
| F10 EMA20 distance | < −0.5 | −0.5–0.5 | +10.27 | +1.46 | YES |
| F11 EMA50 side | against | with | +10.99 | +3.83 | YES |
| F12 opening range | beyond in direction | inside OR | +4.09 | -3.66 | no |

One candidate on the primary cell — **F11, EMA50 side: sweeps entered against the EMA50 (price on
the wrong side for the trade direction) beat with-trend ones by $5.95, LB95 +$1.08** — and the
robustness cell agreed (+$10.99, LB95 +$3.83) and added F10 (price more than 0.5 ATR against the
trade relative to the EMA20, +$10.27, LB95 +$1.46). Every other feature's gap had a negative lower
bound. A theme ran through the fit half: the "extended" buckets — beyond 2σ of VWAP, far from POC,
against the EMAs — were the better ones almost everywhere, consistent with the mechanism being
an overshoot-and-revert.

## B. Test half — read once

Rankings fixed from the fit half. A candidate holds if the fit-best minus fit-worst gap is positive
with LB95 > 0 on the test half.

**F11 on C1a×C3a — fit ranking: against > with.** Test half:

**F11 — EMA50 side** (n=2,460)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| against | 845 | 53.0 | +11.23 | +2.18 | 16.2 | 25.3 |
| with | 1615 | 56.8 | +19.25 | +12.68 | 17.3 | 23.3 |

gap (tool, test ranking): **with** (+19.25, n=1615) minus **against** (+11.23, n=845) = +8.03, LB95 -3.17 → not a candidate

Fit-fixed gap, against minus with: **−$8.03. Reversed. Does not hold.**

**F10 on C1a×C3b — fit ranking: < −0.5 > −0.5–0.5.** Test half:

**F10 — EMA20 distance** (n=1,893)

| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |
|---|---|---|---|---|---|---|
| < −0.5 | 587 | 49.4 | +7.44 | -3.18 | 14.4 | 27.7 |
| > 0.5 | 772 | 55.2 | +14.88 | +5.12 | 15.6 | 26.8 |
| −0.5–0.5 | 534 | 53.4 | +29.36 | +16.85 | 14.7 | 26.5 |

gap (tool, test ranking): **−0.5–0.5** (+29.36, n=534) minus **< −0.5** (+7.44, n=587) = +21.92, LB95 +6.02 → **CANDIDATE**

Fit-fixed gap, < −0.5 minus −0.5–0.5: **−$21.92. Reversed. Does not hold.** F11 on C1a×C3b likewise
reversed (against +10.45 vs with +20.28).

The tool also prints a "candidate" flag on the test half from the test half's own ranking; that
flag is post-hoc by construction and is not used for anything.

**No feature holds. Conviction sizing (§4) is not run.** `sizing_test.py` is committed, unused.

## C. What this establishes

- None of the twelve confluences — session VWAP and its bands, prior-day value area, POC, two
  Fibonacci sets, three moving averages, the opening range — carries information about which of
  this bot's sweeps win that survives from 2018–2024 into 2025–2026. The one that came closest,
  fading against the short-term averages, was worth +$6 to +$11 a trade for six years and then cost
  −$8 to −$10 a trade for the next twenty months.
- That is the third time the same lesson has appeared on this bot: its own five score bonuses do not
  rank outcomes (`RESULT.md` §B.10, §C.2), the autopsy's slices flipped between windows (§B.11), and
  now twelve external confluences do the same. The edge is the mechanical overshoot-and-revert with
  a stop wide enough to survive the noise; it is not a setup that can be graded.
- Conviction-based sizing therefore has nothing stable to size on. Sizing on any of these would have
  meant sizing up the fade of extremes through 2024 and being 1.5× exposed to it exactly when it
  stopped paying. Flat sizing is the finding.
- Two features are left as observations, not rules: on the test half the best trades were the ones
  sitting near the EMA20 (−0.5 to +0.5 ATR) and with the EMA50 — the opposite of the fit half.
  Whichever of those a reader prefers, the other window contradicts it.
