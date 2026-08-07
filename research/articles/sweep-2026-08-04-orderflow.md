---
date: 2026-08-04
status: reference
tags: [london, order-flow, research-sweep]
sources: ["see per-concept lists below"]
---

# Sweep record — order-flow / liquidity angle (agent sweep, 2026-08-04)

Sourcing: WebSearch extracts only; direct page fetches 403-blocked at egress
(`findings/london-session-clock.md`). URLs are leads for the deep-dive round.

## OF#1 asian-range-sweep-reversal → candidate `london-asia-sweep-reversal`
London-open push through an Asian-range extreme fills passive size against
triggered stops, then reverses once the stop pool is consumed — no follow-through
flow behind the break. Wrong side: Asian breakout traders and obvious-stop holders.
Candles-only; flow (delta fade on sweep bar) optional.
Sources: innercircletrader.net/tutorials/ict-asian-range/ ·
tradingfinder.com/education/forex/ict-judas-swing/ ·
fxnx.com/en/blog/ict-asian-range-liquidity-trading-london-judas-swing-trap ·
tradingstrategyguides.com/lecture-11-smc-strategy-for-the-london-session/
Crowding: extreme (core ICT curriculum); NQ 03:00-ET application less trafficked.

## OF#2 pre-london-sweep-continuation → candidate `london-asia-sweep-continuation`
17-yr 1-min NQ study (Herman, 4,262 days): sweeps of the Asian high occurring in
the 02:00–03:00 ET dead hour tend to be CONFIRMED and extended by London, not
reversed — especially after low-volatility Asia. Wrong side: reflexive sweep-faders.
The anti-crowd complement of OF#1, separated by WHEN the sweep occurs.
Sources: hermantrading.pro/backtest-library/... · x.com/R_Herman_/status/1947998216764391925 ·
nqstats.com/aln_sessions
Crowding: low — niche NQ session-stats community, not mass-market ICT.

## OF#3 overnight-extreme-failed-break → candidate `london-level-trap-fade`
Break of ONH/ONL/PDH/PDL that snaps back inside within minutes traps breakout
entrants; the break was a stop run, and trapped liquidation fuels the fade. During
London, fewer participants execute these levels than at the NY open.
Sources: trademomentum.org/blog/failed-breakout-reversal-strategy ·
futuresnetworks.com/post/fbot-failed-break-out-trade-strategy ·
fortraders.com/blog/false-breakouts-why-they-happen-how-to-trade
Crowding: concept old and known; London-window NQ application thin.

## OF#4 london-open-orb-expansion → candidate `london-euro-open-drive`
08:00 UK is a structural event (LSE + Xetra cash opens): European desks reprice
the overnight stack in the first deep two-sided book. Documented as repeatable
volatility expansion on FDAX (published ORB backtests); NQ takes direction from
the European tape in this window. Ride the repricing against wrong-sided
overnight inventory.
Sources: kagels-trading.de/dax-open-range-strategie/ ·
tradertom.com/breakout-strategy-for-the-dax-and-dow-open/ ·
forexfactory.com/thread/906691-open-range-break-out-dax-strategy ·
sessionclips.com/guide/all-market-trading-session-times-est/
Crowding: ORB extremely crowded at 09:30 ET; European-open NQ version far less.

## OF#5 absorption-fade-at-prior-day-levels → candidate `london-level-defense-flow`
Aggressive market orders hitting a level while price refuses to move = a passive
defender. In the thin London tape a defending institution is NOT camouflaged.
Trade with the defender; the absorbed aggressors' covering fuels the rotation.
Flow-essential (footprint/delta; June 2025+ span).
Sources: optimusfutures.com/blog/absorption-advanced-order-flow-strategy-using-footprint-charts/ ·
juselltradingacademy.com/absorption-trading · gocharting.com/blog/footprint-charts/... ·
bbntimes.com/science/order-flow-analysis-101-...
Crowding: standard order-flow education; London-window mechanized NQ version ~absent.

## OF#6 cvd-divergence-at-london-extreme → folded into `london-level-defense-flow` (+ overlay)
New session extreme on a CVD lower-high = extension made of covering and stops,
not initiative flow — exhaustion at the extreme, last entrants trapped. Also
serves as veto/confirm overlay on OF#1/OF#3.
Sources: bookmap.com/blog/how-cumulative-volume-delta-transform-your-trading-strategy ·
tradethematrix.net/post/delta-divergence · zitaplus.com/blog/analysis/... ·
quantum-algo.com/blog/guides/cumulative-volume-delta-complete-guide/
Crowding: moderate; London index-futures application essentially undocumented.

## OF#7 iceberg-defense-of-overnight-level → folded into `london-level-defense-flow`
Volume at one price far exceeding displayed depth = hidden reload; someone with
size decided the level matters before the US crowd arrives. Trade with the
defense; if the iceberg is pulled/consumed, flip with the hard break. Depth-essential.
Sources: bookmap.com/blog/how-to-read-and-trade-iceberg-orders-... ·
theledgermind.com/how-to-read-order-flow/ · cmcmarkets.com/en/trading-strategy/order-flow-trading
Crowding: low at retail (data barrier); undocumented mechanized on London NQ.

## OF#8 overnight-inventory-correction-at-london → candidate `london-inventory-fade`
Dalton: ~100% one-sided overnight inventory corrects at the first liquid
opportunity — canonically 09:30 ET, but the FIRST deep-liquidity event after an
Asia-long drift is the European open. Fade the overnight extension at the moment
holders finally have the liquidity to exit.
Sources: jimdaltontrading.com/glossary/overnight-inventory/ ·
marketcalls.in/market-profile/understanding-overnight-trading-inventory-... ·
shadowtrader.net/glossary/overnight-inventory/
Crowding: known in profile community for the RTH open; London transposition non-standard.
