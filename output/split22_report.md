# Pass-22 split-test report — OTE/FIB + order-block + market-confirmation arms, Feb–Apr 2026

**Directive (Angus):** "With our new discoveries on the strategy… run some split tests between
February and April, and let's suss out the performance." Diagnosis standard per pass-23 ruling:
full detail, no dumbing down. Per-trade CSVs with MFE/MAE, veto ledgers, and hand-trade capture
maps for the four key arms are in `output/diag22/` (`<arm>_<month>_{trades,vetoes,capture}.csv`).

Benchmarks: Feb hand log 28 trades (20W/8L), Mar journal 17 (9W/8L, ~+$13–15k on 50k sizing).
April has no morning-band hand log (live records that month are overnight/London/post-10:15).
"cap aW/bL" = hand winners/losers with a taken engine trade within ±25 min, same direction.

## Part 1 — standard trigger set (E3 champion vs E5 order-block vs EC2)

```
== FEB (hand: 20W/8L) ==
  champ v2 (E3/V0)          33tr 36.4%win   +11,442$ maxDD   1,370$ posDays  56%  cap 9/20W 2/8L
  champ + V8                33tr 45.5%win    +7,712$ maxDD     755$ posDays  61%  cap 8/20W 2/8L
  E5 (OB entry)             35tr 20.0%win    +2,135$ maxDD   1,865$ posDays  39%  cap 7/20W 2/8L
  E5 + V8                   35tr 31.4%win      +522$ maxDD   2,336$ posDays  44%  cap 7/20W 2/8L
  EC2 (disp mkt/rej OB)     35tr 31.4%win    +9,325$ maxDD   3,000$ posDays  37%  cap 5/20W 1/8L
  EC2 + V8                  37tr 29.7%win    -1,328$ maxDD   2,689$ posDays  47%  cap 5/20W 1/8L
== MAR (hand: 9W/8L) ==
  champ v2 (E3/V0)          36tr  8.3%win    -4,430$ maxDD   4,708$ posDays  10%  cap 1/9W 3/8L
  champ + V8                36tr 22.2%win      -638$ maxDD   2,537$ posDays  33%  cap 1/9W 3/8L
  E5 (OB entry)             36tr  2.8%win    -7,718$ maxDD   7,718$ posDays   5%  cap 0/9W 3/8L
  E5 + V8                   37tr  8.1%win    -6,279$ maxDD   7,196$ posDays  10%  cap 0/9W 3/8L
  EC2 (disp mkt/rej OB)     40tr 15.0%win    -3,945$ maxDD   6,870$ posDays  27%  cap 4/9W 2/8L
  EC2 + V8                  43tr 23.3%win    -5,147$ maxDD   6,087$ posDays  27%  cap 4/9W 2/8L
== APR ==
  champ v2 (E3/V0)          37tr  8.1%win    -5,660$ maxDD   7,098$ posDays  10%
  champ + V8                39tr 17.9%win    -3,335$ maxDD   4,312$ posDays  19%
  E5 (OB entry)             36tr 11.1%win    -3,052$ maxDD   5,730$ posDays  20%
  E5 + V8                   36tr 11.1%win    -4,304$ maxDD   5,081$ posDays  15%
  EC2 (disp mkt/rej OB)     42tr 16.7%win    -7,142$ maxDD  10,108$ posDays  29%
  EC2 + V8                  42tr 19.0%win    -6,418$ maxDD   8,321$ posDays  19%
```

## Part 2 — OTE trigger set (fib levels join the confluence clusters; 6,009 triggers Feb–Apr)

```
== FEB (hand: 20W/8L, 1282 OTE-set triggers) ==
  OTE min-2 (E3/V0)         31tr 29.0%win    +7,508$ maxDD   1,825$ posDays  44%  cap 5/20W 1/8L
  OTE min-2 + V8            31tr 32.3%win    +5,378$ maxDD   1,550$ posDays  44%  cap 5/20W 1/8L
  OTE 3-conf (relaxed)      22tr 27.3%win    +4,712$ maxDD   1,218$ posDays  36%  cap 5/20W 1/8L
  OTE 3-conf + V8           22tr 31.8%win    +3,728$ maxDD     720$ posDays  43%  cap 5/20W 1/8L
  OTE + EC2 + V8            35tr 28.6%win    -1,703$ maxDD   3,230$ posDays  39%  cap 6/20W 1/8L
== MAR (hand: 9W/8L, 1448 OTE-set triggers) ==
  OTE min-2 (E3/V0)         34tr  8.8%win    -5,038$ maxDD   5,038$ posDays  10%  cap 1/9W 3/8L
  OTE min-2 + V8            34tr 26.5%win    -1,077$ maxDD   2,624$ posDays  40%  cap 1/9W 3/8L
  OTE 3-conf (relaxed)      23tr  8.7%win    -4,238$ maxDD   4,238$ posDays  12%  cap 0/9W 3/8L
  OTE 3-conf + V8           25tr 20.0%win    -1,971$ maxDD   2,921$ posDays  31%  cap 0/9W 3/8L
  OTE + EC2 + V8            41tr 22.0%win    -5,526$ maxDD   6,439$ posDays  27%  cap 3/9W 2/8L
== APR (1355 OTE-set triggers) ==
  OTE min-2 (E3/V0)         37tr  8.1%win    -5,415$ maxDD   6,852$ posDays  10%
  OTE min-2 + V8            39tr 20.5%win    -3,082$ maxDD   4,060$ posDays  19%
  OTE 3-conf (relaxed)      33tr 18.2%win    -2,282$ maxDD   2,790$ posDays  33%
  OTE 3-conf + V8           33tr 30.3%win    -1,149$ maxDD   1,884$ posDays  33%
  OTE + EC2 + V8            41tr 24.4%win    -3,229$ maxDD   4,779$ posDays  33%
```

## Part 3 — market-on-confirmation (E4: Angus's live execution — tap → reaction candle → market in)

```
== FEB (hand: 20W/8L) ==
  STD + E4 mkt-confirm      38tr 34.2%win    +4,380$ maxDD   3,422$ posDays  40%  cap 8/20W 3/8L
  STD + E4 + V8             39tr 41.0%win       +84$ maxDD   2,311$ posDays  50%  cap 8/20W 3/8L
  OTE + E4 mkt-confirm      35tr 28.6%win       +88$ maxDD   4,028$ posDays  37%  cap 6/20W 2/8L
  OTE + E4 + V8             37tr 40.5%win      -654$ maxDD   2,153$ posDays  42%  cap 7/20W 2/8L
  OTE 3conf + E4 + V8       35tr 25.7%win    -4,861$ maxDD   5,067$ posDays  28%  cap 10/20W 3/8L
== MAR (hand: 9W/8L) ==
  STD + E4 mkt-confirm      39tr 20.5%win    -3,302$ maxDD   6,300$ posDays  36%  cap 4/9W 2/8L
  STD + E4 + V8             43tr 30.2%win    -5,606$ maxDD   6,546$ posDays  27%  cap 4/9W 2/8L
  OTE + E4 mkt-confirm      37tr 16.2%win    -7,252$ maxDD   7,378$ posDays  27%  cap 3/9W 2/8L
  OTE + E4 + V8             41tr 31.7%win    -4,664$ maxDD   5,576$ posDays  27%  cap 3/9W 2/8L
  OTE 3conf + E4 + V8       39tr 43.6%win    -2,876$ maxDD   4,064$ posDays  38%  cap 1/9W 4/8L
== APR ==
  STD + E4 mkt-confirm      41tr 26.8%win    -2,938$ maxDD   9,208$ posDays  38%
  STD + E4 + V8             42tr 33.3%win    -2,512$ maxDD   6,348$ posDays  38%
  OTE + E4 mkt-confirm      39tr 20.5%win    -5,458$ maxDD  10,742$ posDays  29%
  OTE + E4 + V8             41tr 31.7%win    -1,672$ maxDD   4,541$ posDays  38%
  OTE 3conf + E4 + V8       36tr 30.6%win    -3,703$ maxDD   5,023$ posDays  30%
```

## Findings (diagnosis layer — the details behind the tables)

### F1 — E5 order-block entry is dead as a default. Angus concurred before seeing the numbers.
Feb +$2,135 vs champion +$11,442; Mar 2.8% win / −$7,718 (worst March arm ever run). The deeper
OB-midpoint limit is pure adverse selection: it only fills on deep retraces, which are
disproportionately the failures. Code stays (E5/EC2 variants) but no arm carries it forward.

### F2 — OTE as passive confluence is location without the trade. Not the encoded edge.
Adding fib levels to clusters SHIFTS which triggers form (6,009 vs ~4,200 std) but every OTE arm
underperforms its std twin in Feb (+7,508 vs +11,442 min-2; capture halves to 5/20W) and rescues
nothing in Mar. Two genuine positives: **OTE 3-conf + V8 is the best April arm of all 16**
(−$1,149, maxDD $1,884, 30.3% win — the 3-of-{fib,bb,vwap,poc} requirement + trail is the least-bad
war-month config) and its Feb maxDD $720 is the smallest of any arm. Angus's Mar/Apr fib success
came from the RETRACEMENT-CONTINUATION trade (leg-scaled stops/targets), which none of these arms
implement — that's the E6 build below.

### F3 — Market-on-confirmation (E4) SEES Angus's trades better than anything yet — and loses on
### broken risk geometry, not trade selection.
OTE 3conf + E4 + V8 takes **13/28 of his Feb hand trades** (10/20 winners — highest capture ever
recorded; champion takes 9/20) yet loses −$4,861. The autopsy:
- **Stop distance balloons**: median loser stop = **26.9 pts vs 13.0 (same triggers, E3)**. E3
  enters at the penetrated level (near the wick, tight fill-to-stop). E4 fills at next-bar open —
  after a big confirmation candle, that's 2× further from the wick extreme. Same setup, double the
  dollar risk, R halves.
- Even his own setups lose under this geometry: the 20 Feb trades inside his hand windows netted
  −$3,083 at 30% win. His "relatively tight stop above that high" implies a SMALL reaction candle;
  the mechanical arm market-orders after monsters too.
- Slippage is NOT the story: avg 1.6–1.7 ticks ($8/side) — geometry, not friction.
**Fix queued (E6):** market-on-confirmation ONLY when the confirmation candle leaves a tight stop
(fill-to-wick ≤ cap, e.g. ~15 pts — mirrors his hand geometry), plus leg-scaled continuation
targets for the OTE stack. E4-unfiltered is retired.

### F4 — The gate ledger: our own protections now cost more Feb winners than any signal defect.
Gates blocking his 20 Feb winners (champion arm): **vault max-2/day: 6 winners** · window end
10:15: 4 · t_cancel 22pt: 4 · bb+vwap composition: 2 · min-stop: 1 · position-already-open: 2.
March: window end blocks 5 of 9 winners (his best March trades ran later in the morning), t_cancel
3. The max-2 cap and the 10:15 cutoff were Feb-tuned safety rails; they are now the single largest
identifiable winner leak. **Decision needed from Angus** (not taken unilaterally): trial arms with
max 3/day and window end 11:00 — both were his original spec values.

### F5 — Loser anatomy: the war-month signature is unchanged, and it's not entries.
Champion losers' median MFE: Feb +0.73R, **Mar +1.33R, Apr +1.35R** — 62–67% of Mar/Apr losers
were up ≥1R before dying (Feb: 38%). Entries locate correctly in all three months; unmanaged
round-trips do the damage. V8 (trail) is the only management that monetizes any of it — it cuts
March bleed 86% (−$638 vs −$4,430) and is the best or near-best arm in EVERY month/set combination.
V8 graduates from experiment to default-candidate pending Angus sign-off.

### F6 — No arm out of 16 makes March or April positive. The gap to "no losing months" is regime,
### not another entry/management permutation.
Best Mar: champ+V8 −$638. Best Apr: OTE 3conf+V8 −$1,149. Angus's +$13–15k March came from trades
the morning-band mechanical system structurally can't take (all-session, leg-riding, regime-read).
The ceiling for entry/mgmt tweaks inside the current band is ~breakeven war months. Getting them
GREEN needs the layers in flight: AMT balance/imbalance day-typing (task #8), Pat's regime agent,
and the all-session question — plus depth confirmation later (Angus, pass 23).

## Next moves (in order)
1. **E6 build**: market-on-confirmation with tight-stop cap + leg-scaled targets on the OTE stack
   (his described execution, with the geometry guard the E4 test proved necessary).
2. **AMT day-typing gate** (task #8) — the no-losing-months lever.
3. **Angus rulings wanted**: vault max 2→3? window end 10:15→11:00? V8 as default management?
4. May stays soft holdout; Jun–Jul stay locked.
