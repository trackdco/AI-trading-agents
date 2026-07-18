# Live-execution evidence catalog (Angus's uploads, 18 Jul 2026 — pass 21)

21 images from commits b1baa2c + 8414785 (branch r64muf). Times on phone/platform clocks are
AEST/UTC+10 (Angus) → ET = −14h; TradingView chart axes are ET unless noted. P&L fields on
Topstep shots are mostly masked — these are SETUP/EXECUTION evidence, not a complete ledger.

## Timeline of live activity (contradicts nothing; refines "stopped early May" → last seen May 7)
Mar 30 → Apr 10 (dense cluster) → Apr 14 → Apr 22–27 → Apr 29 → **May 7 (final)**.

## Executions (TopstepX, live)
- IMG_3161: $50K Combine, SHORT 4 MNQ @23,554 (MNQM26), +95pts onside, TP resting; 01:45 AEST = **11:45 ET** (late NY morning — after our 10:15 cutoff).
- IMG_3364/3366/3376/3378: **Apr 10 cluster** (MNQM26, 6-lot brackets): overnight RP&L +$1,416 banked (00:19 UTC+10 = 10:19 ET); LONG 6 @~25,261.75 w/ stop trailed to +1.75 lock (23:08 ET = Asia); LONG 6 w/ 6.75pt stop (03:10 ET = **London**); SHORT 6 w/ 31.75pt stop (04:24 ET = London).
- **Sessions traded live: NY morning, late NY, Asia, London — ALL of them.** (Full-day expansion is not speculative; it's how he actually traded.)

## Live MIG behavior (the "completely different live" evidence)
- **Three roles, all documented:** REJECTION at box edge (Mar 30, Apr 22 5m, May 7, NY-open sell-off IMG_3476); TARGET (bracket BUY LIMITs resting at box bottoms: Apr 27/29, May 7 pending shorts); **RECLAIM** (base inside box → break top → hold above: IMG_3501, IMG_3408).
- **Later live version carries B%/S% participation tags per box** ("B 82% | S 18%", "B 24% | S 76%", "B 30% | S 70%") — orderflow composition, unreproducible from OHLCV, reconstructable from tick/book data. Earlier (Feb–Mar era) version showed A–C grade codes instead ("15 A+BC", "5M A+A+B").
- **The recurring live bracket template: SELL LIMIT at the box's red supply edge, STOP just beyond the box, BUY LIMIT target at the box bottom/green demand band** — entry/stop/target ALL anchored to box geometry (Apr 27, Apr 29, May 7, Apr 14-era). This is the mechanization target for the level-memory layer.
- MIG presets evolved: "Mohs Mayfair 2 Close 20 50" (Apr) → "Mayfair 5 Wick 20 100" (May 7).

## OTE / Fibonacci — CONFIRMED live tool
Fib retracement with the 0.382/0.5/0.618/**0.705**/0.786 ladder drawn on FOUR live charts
(IMG_3481, 3408, 3476, 3479); typical use: retrace into OTE cluster after a box
breakdown/breakout, often coinciding with box edges and VWAP bands (3408: consolidation at
0.382 inside box → breakout; 3476: rejection at 0.618/box-top; 3479: reversal from fib 0 /
box bottom). Matches the pass-20b `ote` cluster-candidate spec.

## Management (live)
Stop trailed to near-BE lock on an open 6-lot (IMG_3366); bracket-always-on ("Position
Bracket Enabled"); replay practice reps (IMG_3661/3669 — **flagged: Replay mode, NOT live**)
show fixed $750 risk at 7.4–7.9 R/R from box lower edges.

## Open item for Angus
RSI-with-bands (7 ohlc4) appears on EVERY live chart with Bull/Bear divergence tags
(Mar 30, Apr 10, IMG_3479, IMG_3805) despite "I don't use RSI anymore" — rule on whether
divergence tags played any live role, or the panel was just legacy screen furniture. **→**
