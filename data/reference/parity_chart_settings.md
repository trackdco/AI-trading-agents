# Parity Gate — Reference Chart Settings & Open Items

Purpose: capture the human chart-read configuration for the Spec 1 Step 4
parity gate (Feb 11 2026 09:48 ET, Feb 17 2026 09:50 ET), and flag mismatches
against `strategy-definition-v1.1.md` §2 and `spec-1` Section 3 BEFORE readings
are recorded. A 1.0-point tolerance is only meaningful if chart and engine use
identical definitions on the same instrument.

Source: Brakey's TradingView screenshots (received 2026-07-17).

## Settings read off the screenshots

**Bollinger Bands** — Length 20, Basis MA Type SMA, Source Close, StdDev 2,
Offset 0, Timeframe = **Chart** (screenshots displayed on 3m), "Wait for
timeframe closes" ON. Status-line label: `BB 20 SMA close 2`.
- vs §2 (`Bollinger Bands 20, SMA, close, 2σ`): **MATCH.** ✅

**VWAP Deviation Bands** (custom indicator) — VWAP + ±1σ/±2σ/±3σ all enabled;
fills on; alerts on. No anchor field visible in the Inputs tab shown.

**SVP HD** (Session Volume Profile HD) — Sessions = All, Volume = Up/Down,
Value Area Volume = 100, Extend POC/VAH/VAL Right = off. Custom-session
09:30–16:00 field is greyed (inactive while Sessions = All).

Also loaded on the chart (not used by the mechanical system): a killzone/session
indicator and **MIG LiquidityEdge** — MIG is EXCLUDED per §2, so no MIG-derived
number enters the parity read.

## Open items to resolve BEFORE recording the four readings

1. **INSTRUMENT / continuous-contract adjustment (blocking).**
   Chart symbol is `MNQ1!` with `B-ADJ` (back-adjustment ON) shown bottom-right.
   The engine uses Databento continuous **NQ**, **unspliced** (spec-1 §3) = true
   traded prices, no back-adjust. Between Feb 2026 and now (Jul 2026) NQ rolled
   H→M→U (two rolls); back-adjustment cumulates those roll gaps into the Feb
   prices, shifting them by potentially tens of points → guaranteed to blow a
   1-pt gate on price levels. Micro (MNQ) also carries different volume, which
   moves VWAP and POC (volume-weighted / volume-based).
   **Recommendation:** read the parity numbers off the actual dated front-month
   contract for those dates — **NQH2026** (March 2026 NQ, front month on Feb
   11/17) — not a `1!` continuous chart, and NQ not MNQ. That removes both the
   back-adjust shift and the micro-volume difference in one move.

2. **Two separate VWAPs required.** The gate needs (a) **Daily VWAP** anchored
   18:00 ET / CME session open, with ±1σ, AND (b) **NY session VWAP** anchored
   09:30 ET. Confirm which on-chart indicator supplies each anchor (one "VWAP
   Deviation Bands" instance = one anchor). Confirm the ±σ bands are
   **volume-weighted** stdev (standard TradingView formula), not simple price
   stdev — spec-1 §3 requires volume-weighted. NY VWAP does not exist pre-09:30.

3. **BB timeframe.** Setting is "Chart", so the BB basis value depends on the
   displayed TF. Engine computes BB per entry TF (1m/2m/3m/5m). Record the BB
   basis on the TF the reference trade was taken on (ideally all four), and note
   which TF each number came from.

4. **Profile scope.** Confirm SVP HD "daily" profile = the CME daily session
   (18:00–17:00 ET), matching the engine's "daily" profile. Value Area Volume =
   100% does not affect POC (POC is the max-volume price regardless of VA%); it
   only widens VAH/VAL. POC comparison is fine as-is.

## Sequencing note

Step 4 indicator code is not built yet, so there are no engine ("robot") values
to compare against yet. Order of operations: build Step 4 indicators → compute
values for the two candles → record chart readings (per above) → generate
`output/parity_report.md` (computed vs chart) → within 1.0 pt → Angus signs off →
proceed to Steps 5–9.
