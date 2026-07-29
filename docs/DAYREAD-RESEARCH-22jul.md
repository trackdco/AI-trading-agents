# Day-read research: every CVD angle, tested (22 Jul 2026)

**Goal:** bridge the gap to the oracle+stand-down ceiling ($43.4k 2025-span / $45.4k 2026-span
on the footprint-covered days). Autonomous deep-dive: build every order-flow variable the data
supports, screen all of them out-of-fit (2025 vs 2026), keep only what holds both years.

## What was tested

- **Day-level:** 65 features per day over 256 labeled days — CVD by session window
  (overnight / Asia / London / 08:00-09:30 pre-market / 09:30-09:50 post-open), efficiency,
  linearity (r²), sign flips, price-CVD divergence, edge-of-range delta, absorption & burst
  counts, London sweeps, ±2 daily-VWAP touches, plus the regime-vector and value-area context.
  Targets: (T1) both-books-red = stand down, (T2) which book won. `scripts/dayflow_features.py`,
  `scripts/dayflow_screen.py`.
- **Trade-level:** 10 at-entry tape angles on the 970-trade both-books/all-days universe —
  window CVD confirmations (ON/London/PM/session), last-15/30-min tape delta, CVD path
  position, 15-min divergence, strength quartiles. `scripts/trade_angles.py`.
- **Portfolio:** the surviving rules run with NO day forecasting at all.
  `scripts/noforecast_portfolio.py`.

## Finding 1 — the day cannot be predicted pre-market

Best single-feature AUC for "should we stand down today": **0.58** (barely above coin-flip),
and the best book-pick feature is the **first 20 minutes after the open** (`abs_px_chg_OP`),
i.e. not pre-market information at all. 2025-fitted day-rules captured 12-26% OOF — no better
than the chained agent (30%). This is why every attempt at a smarter morning call keeps
disappointing: **the information isn't there at 08:00.** The only pre-market cell with teeth:
extreme one-sided overnight CVD (top quintile |cvd_ON|) → 63% / 73% both-red (2025/2026) —
a stand-down warning, not a trade signal.

## Finding 2 — the tape at entry IS predictable (OOF survivors)

Per setup, on/off gaps that hold in BOTH years (≥$60/t, n≥12 per cell):

| Setup | Rule | 2025 on/off $/t | 2026 on/off $/t |
|---|---|---|---|
| **B** | last-15-min tape delta agrees with direction | +17 / −136 | +57 / −51 |
| **B** | 15-min price-CVD divergence at entry = VETO | −145 (div) / −24 | −184 (div) / +55 |
| **B2** | pre-market CVD agrees (the known cvd_conf) | −14 / −79 | +60 / −96 |
| **B2** | session CVD path at day's lows = VETO | −109 (lo) / −22 | −74 (lo) / +6 |
| **B2** | weakest-quartile \|cvd_PM\| is the bleeder | Q1 −140 | Q1 −81 |

Continuations need the tape moving with you *into* the entry; fades need pre-market conviction
behind them and must not be taken while cumulative delta collapses to new lows. A is too thin
to clear the bar (n=70); CVD-confirmed A stays a flagged lead.

## Finding 3 — the no-forecast portfolio

Trade **both books, every day** — no day call, no book call — under the surviving rules
(thresholds fit on 2025 only): B2 needs conf_PM + |cvd_PM| ≥ 197 + not path_lo; B needs
conf_last15 + no div15; A needs conf_PM.

| | universe raw | portfolio | capture of ceiling |
|---|---|---|---|
| 2025 | −$25,324 (559 tr) | **+$9,871** (212 tr, 33% win, maxDD $8.0k) | 23% |
| 2026 | −$5,591 (411 tr) | **+$15,684** (152 tr, 39% win, maxDD $3.0k) | **35%** |

The 2026 portfolio **beats the chained agent (+$13.1k on the same span) with zero forecasting**.
8/13 months green; worst stretch Aug-Sep 2025 (−$4.6k). ~1.4 trades/day.

## Finding 4 — the ceiling, revisited

With the rules inside the books, the *hindsight* oracle drops (raw sim books $50.7k/$62.0k →
filtered $34.3k/$39.9k) because a perfect day-picker could monetize trades the filters cut.
The rules trade ceiling for floor: **the floor (no forecasting at all) rises from −$25k/−$6k
to +$10k/+$16k.** The day-read's job shrinks from "carry everything" to "add on top": veto the
worst days (extreme overnight CVD), size up the best, arbitrate July-2026-style dead tape.

## Caveats (honest)

- Rules were selected for both-year consistency — that guards against, but does not eliminate,
  selection bias. No third year of footprint exists yet; the next quarter is the true holdout.
- Portfolio trades both books simultaneously (up to 2 concurrent positions ≈ double capital).
- Sim-universe books (our engine config), not the committed daily books.
- A-with-CVD is net +$1.2k across both years but −$1.2k in 2026 on n=6: flagged, not proven.

## Where this leaves the agent

Stop asking the agent "what kind of day will it be" — the data says nobody can know at 08:00.
The mechanical layer trades the tape; the agent's leverage points are now: (1) stand-down veto
on extreme-overnight-CVD days, (2) conviction sizing on top of rule-passing trades, (3) the
July-2026 problem — recognizing dead tape mid-month and cutting size. Next experiment: re-run
a fresh-eyes walk where the agent receives the portfolio's rule-passing trades and only sizes
or vetoes them.
