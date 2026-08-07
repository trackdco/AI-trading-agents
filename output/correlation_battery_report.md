# Correlation battery — raw run output

```
CORRELATION BATTERY — NY canon (funded, lucid fit) vs old London book (native sizing)
common span 2025-06-02 .. 2026-07-08 | NY active days 230 | London active days 109

1. INPUT-FAMILY OVERLAP (from the entry specs — a veto input, not a score)
   SHARED depth walls (dep_wall_*)               NY: W, D, WALLSZ, wall-quality cut     LDN: W, FAR
   SHARED overnight structure (on_range/age)     NY: AGE                                LDN: ROOM
   SHARED order flow / CVD / delta               NY: F_, Tc, T2, LONSLOPE               LDN: ASIA, opp5
          VWAP geometry                          NY: G                                  LDN: —
          trigger density (trigdens_30)          NY: TRIG                               LDN: —
          structural events (broke)              NY: elite gate                         LDN: —
          pattern taxonomy (B/B2/A)              NY: —                                  LDN: Layer 2p
   -> 3/7 families shared. Depth walls, overnight structure and
      order-flow are read by BOTH books: structurally, these are cousins.

2. DAY-LEVEL P&L — union (inactive book = $0): n=240
   Pearson  -0.094  [95% CI -0.185 .. +0.003]
   Spearman -0.096  [95% CI -0.216 .. +0.026]
2. DAY-LEVEL P&L — intersection (both active): n=99
   Pearson  -0.110  [95% CI -0.265 .. +0.065]
   Spearman -0.086  [95% CI -0.273 .. +0.104]

3. TAIL DEPENDENCE (worst-decile days, both-active universe, n=99)
   NY worst-decile cut $-296 (10 days) | London $-487 (10 days)
   P(LDN in worst decile | NY in worst decile) = 0.10  (independence: 0.10)
   P(NY in worst decile | LDN in worst decile) = 0.10  (independence: 0.10)
   both-red-decile days: 1 (independence expects 1.0)
   Pearson conditioned on either-in-worst-decile (n=19): -0.451
   [small-n warning: decile conditioning leaves ~10 days; treat point
    estimates as direction, not precision — this is battery item 5's whole point]

4. TIMING OVERLAP (in-market minutes, taken trades only)
   days with any simultaneous open risk: 0/240 | total overlapping minutes: 0

5. SAMPLE ADEQUACY
   both-active days n=99; London trades 109/230 of NY's active days.
   CIs above are 10k-resample percentile bootstraps; any threshold Angus sets
   should name the minimum n at which an estimate counts at all.

6. COMBINED RUIN (paired whole-day bootstrap, 2000 sims x 252 days,
   50k start, $2k EOD trailing locking at 50k; London at NATIVE sizing — see caveat)
   NY alone                     P(bust) 0.4% | median net/yr $+86,165 | maxDD med $1,267 p95 $1,954 | median worst day $-690
   London alone                 P(bust) 6.9% | median net/yr $+36,046 | maxDD med $2,115 p95 $3,803 | median worst day $-1,292
   combined (as paired)         P(bust) 0.5% | median net/yr $+123,458 | maxDD med $1,694 p95 $2,697 | median worst day $-1,266
   combined (pairing shuffled)  P(bust) 0.4% | median net/yr $+122,734 | maxDD med $1,631 p95 $2,683 | median worst day $-1,080

   CAVEAT: London runs its research sizing (multiplier ~1 NQ lot), un-governed by
   the shared $853.33 budget; the combined rows measure dependence shape, not a
   shippable book. A funded-profile London book is the data contract's first job.
```
