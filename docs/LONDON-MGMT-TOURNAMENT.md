# London management tournament — V0 vs V1 (BE at +1R) vs V8, real engine

**FIT ONLY. Same census, same fills, same slippage; only management differs. Selection runs on each arm's own realized dollars. Pipeline gate: the V8 arm reproduces the canonical stack exactly (verified this run). Working stack, 1 NQ lot.**

## The head-to-head

| arm | n | WR | mean R | net | maxDD | 2025 n/WR/R/$ | 2026 n/WR/R/$ |
|---|---|---|---|---|---|---|---|
| V8 shipped (partial+trail) | 110 | 64% | +0.669 | $+17,941 | $958 | 46/65%/+0.58/$+6,658 | 64/62%/+0.73/$+11,284 |
| V1 BE at +1R | 111 | 32% | +0.875 | $+22,360 | $1,310 | 46/33%/+0.78/$+8,665 | 65/32%/+0.94/$+13,695 |
| V0 set-and-forget | 98 | 38% | +0.706 | $+14,850 | $2,440 | 41/44%/+0.84/$+8,150 | 57/33%/+0.61/$+6,700 |

Exit mixes: **V8 shipped (partial+trail)**: {'partial+stop': 47, 'stop': 37, 'partial+target': 21, 'target': 5} · **V1 BE at +1R**: {'be_stop': 47, 'target': 36, 'stop': 28} · **V0 set-and-forget**: {'stop': 61, 'target': 37}

## Where V1's difference comes from (106 shared trades)

- Full V8 losers that V1 scratches near BE (|R| <= 0.15): **17**
- V8 winners that V1 BEs out before the run: **28**
- Net management delta on shared trades: $+3,390 (biggest single save $+1,500, biggest single cost $-1,234)
- Trades only in one stack (selection drift via day-stop paths): 4 V8-only, 5 V1-only

## Read it

- V1-vs-V0 is the DECLARED head-to-head (Angus, 2026-07-17). V8 is the shipped control; it was chosen in the NY-era tournaments, not against V1 on London.
- Adoption of any arm change = ANGUS ruling + prereg rev + runner re-rehearsal. If V1 wins here it becomes the declared management CANDIDATE, judged on the holdout/forward like everything else.
- The bar-walk predicted +$1,194 for BE@1R over the shipped book; the engine number above is the real one (management interacts with partials, slippage and day-stop paths a bar-walk cannot see).
- One disclosed asymmetry: the 2025-11-27 Thanksgiving 5min short has no V0 outcome (set-and-forget never resolves before the holiday session ends) and is dropped from the V0 arm only. V8 booked +$70 on it, V1 -$10 — a one-trade, ~$70 edge to V8 in the table above.
