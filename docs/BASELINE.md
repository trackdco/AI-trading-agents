# ✅ CURRENT BASELINE — Champion v1.1 (regime-switched) (2026-07-21)

**This is the baseline we build from now.** Promoted per Brake (2026-07-21), on the brake branch.
It supersedes the *Golden-window 2+2 caps + CVD-absorption gate* (+$15,381 / 43%): **Champion v1.1
makes more money at a higher win rate** — +$17,814 / 45% over the same Feb–Jul 2026 window.

> Supersedes the prior baseline doc on `claude/getting-started-6lwnvs`. Baseline changes are
> normally Angus's call — this promotion is at Brake's request; forward validation is still
> pending (see Status), so treat it as the working baseline, not a frozen live green-light.

## Why it beats the 2+2 + CVD gate

| shape | trades | win% | P&L (1 NQ) | months green |
|---|---|---|---|---|
| Golden-window 2+2 + CVD-absorption gate (prev baseline) | 89 | 43% | +$15,381 | 5/6 |
| **Champion v1.1 (this baseline)** | **100** | **45%** | **+$17,814** | **5/6** |

Champion v1.1 earns the extra ~$2.4k (and +2% win) by being **regime-aware** instead of one flat
book, plus three journal-mined cuts:

- **Pre-open regime switch:** trailing-20-day imbalanced-day share ≥ 0.5 → **WAR** day, else
  **BALANCE** (day types per `output/amt_daytypes.csv`; vector in `output/regime_vector.csv`).
- **WAR book:** E4 market-on-confirmation, tight-stop only (|close − stop_ref| ≤ 15 pts), V0.
- **BALANCE book:** E3 reclaim limits + V8 management (50% off at first structure, 5m-swing trail,
  premarket BE at 09:29), champion config otherwise (B3 filter, min-stop 6, walkout, named list).
- **Cut 1:** skip if effective fill-to-stop risk < 5.0 pts (both books).
- **Cut 2:** skip B-pattern triggers whose fill lands in the 09:00–09:59 hour.
- **Cut 3:** BALANCE book skips `htf_flag == with_trend` triggers (the fade book only fades).

Window 08:00–10:15 ET · max 2 trades/day · per-session budgets when other sessions open.

## The numbers (Feb 2 – Jul 15 2026, 1 NQ, commissions in)

100 trades · 45.0% win · +915.7 pts · **+$17,814** · monthly: +6,599 / +4,250 / +3,705 / +10 /
+3,765 / −515 (Jul = half month).

## The canon setup this book is built on (Angus's CDR)

Angus, verbatim: *"Respect a VWAP, break the Bollinger Band and POC, enter on a retest of POC or
the Bollinger Band, stops below the candle that displaced through."* — 3-way confluence (VWAP + BB
+ developing POC) + displacement + retest + structural stop. See
`docs/SPEC-cash-open-confluence-setup.md`.

## Reproduce / inspect

- Full spec + reference results: `docs/CHAMPION-v1.1-FROZEN.md`
- Trade journal (pre-cut superset): `output/journal_champion.csv`
- Regime vector / day types: `output/regime_vector.csv`, `output/amt_daytypes.csv`

## Notes for anyone building on this

- **In-sample (Feb–Jul 2026) by design** — forward validation = July back-half + live paper-fills;
  the three cuts are journal-mined, so guard against overfit before sizing up.
- **CVD sign landmine:** the repo's `conviction()` / `load_cvd_delta()` produce the *negative* of
  the committed journal's CVD. Any fresh CVD computation must **negate** it, or `cvd ≤ 0` selects
  the hollow (losing) trades.
- **Oracle ceiling** for perfect daily WAR/BALANCE routing = $37,014/6mo (L2 benchmark) — the
  regime-resolution prize the agents are chasing above this baseline.
- Prior baseline (2+2 + CVD-absorption gate, +$15,381) is retained on
  `claude/getting-started-6lwnvs` for reference.
