# The London book — how it actually works, with the trades

Companion files: `output/london_trades/london_trades_all.csv` (all 686 trades)
and 16 annotated charts in the same folder.

---

## 1. The shared machinery — identical for all four arms

Everything below trades **London 03:00–04:59 New York time** (08:00–09:59 London).

| | Rule |
|---|---|
| Trigger timeframe | **15-minute**. Decision is made at the bar's *close*, never intrabar |
| Scale ruler | **W = the 15m Bollinger band width**. Every threshold is in W, never in points — this is what stops the book breaking when volatility doubles |
| Stop | the **trigger candle's own extreme, ± 1 tick** |
| Exit | **75% off at 3R**, remainder trailed on completed 15m structure |
| De-duplication | triggers within **0.5W** collapse to one "fight"; only the first is taken |
| Cost | 0.5 points round trip, inside the R numerator |

Two consequences worth holding onto, because everything interesting traces to
them: **risk is set by the trigger candle's size** (a small candle means a tiny
stop), and **R is self-scaling** (a 2-point stop means 2 points = 1R).

## 2. The four arms

| Arm | Locus | n | Win rate | EV |
|---|---|---|---|---|
| reject | 15m BB middle band | 172 | 42.4% | **+0.465R** |
| union_break | VWAP −1 band | 56 | 42.9% | **+0.506R** |
| union_break | Value Area Low | 73 | 35.6% | +0.190R |
| **sweep_b** | prior stopped attempt | **385** | 35.3% | +0.202R |

**reject** — price wicks *into* the 15m BB middle band and closes back out. The
level held. You enter at the next 1-minute open, trading *away* from the level.
Live until a 15m bar closes through the band.

**union_break** — a 15m bar closes *through* VAL or the VWAP−1 band. The level
flipped. You don't chase the close; you enter on the **retest**. About 93.5% of
breaks do retest; the other 6.5% leave without you.

**sweep_b** — the strangest and the most important, because it's 55% of the book
and the only component that passed the sealed holdout on its own. It requires
that **you already lost a trade**:

1. An earlier attempt at any of the seven loci was entered and **stopped out**.
2. A later 15m bar trades **≥4 ticks beyond that attempt's own stop price**.
3. A completed 15m bar **closes back inside** that stop within 3 bars.
4. Trigger fires at the reclaim close, **same direction as the trade that was
   stopped**.

The read: the market took the liquidity sitting at your stop and immediately
failed to hold there. Your thesis was right, your timing was wrong. Worth
knowing — the same sweep-and-reclaim pattern *without* a prior stopped attempt
was tested separately and came back null (+0.070R, neither era clears). The
stopped attempt is the load-bearing part, not the sweep.

## 3. What the charts show

Sixteen real trades, stratified across all four arms and winners/losers. Each
shows 15m candles, the locus, entry, stop, the 3R partial line, and the actual
entry and exit markers.

Start with **`2025-08-06_reject_bbma15_WIN_+10.00R.png`**. It's the most
instructive chart in the set and it points straight at the biggest improvement
available.

---

## 4. The thing I'd chase — the exit gives back nearly everything

That 2025-08-06 trade has a **2.0 point stop (0.05W)**, ran to an MFE of
**+94.88R**, and closed at **+10.00R**. It captured about a tenth of its own
move.

That is not an outlier. Across the book:

| `risk_W` quartile | n | Median stop | Mean MFE | EV | **% of MFE captured** |
|---|---|---|---|---|---|
| Q1 tight | 172 | 7.0 pt | **4.30R** | −0.003R | **−0.1%** |
| Q2 | 171 | 13.5 pt | 3.85R | +0.355R | 9.2% |
| Q3 | 171 | 21.3 pt | 3.05R | +0.281R | 9.2% |
| Q4 wide | 172 | 31.1 pt | 2.76R | +0.534R | **19.4%** |

**58 trades ran more than 10R of MFE. Their average result was +3.15R.**

And read the first column carefully, because it reverses the obvious
interpretation of the autopsy. **Tight-stop trades have the *largest* average
MFE in the book (4.30R) and capture literally none of it.** They are not bad
signals finding bad moves — they are good signals finding the *biggest* moves
and getting shaken out before those moves develop. Wide-stop trades find
*smaller* moves (2.76R) and keep four times the share of them.

So the mechanism behind "wider stops win" isn't selection quality at all. It's
survival.

## 5. Three improvement leads, in the order I'd test them

1. **Decouple the stop from the trigger candle.** Right now a small trigger
   candle mechanically produces a 2–7 point stop, which London noise reaches on
   its own. Flooring the stop at some fraction of W — while keeping the same
   entry signal — would let the Q1 population keep its 4.3R of average MFE
   instead of surrendering all of it. This is the single largest identified
   improvement in the book and it is a *geometry* change, not a selection change,
   so it doesn't cost frequency.
2. **Revisit the exit against the MFE distribution.** 75%-at-3R was chosen by
   ablation and it beat the alternatives tested, but a book capturing 9–19% of
   its own excursion is worth re-examining — particularly a runner that survives
   past 10R, given 58 trades went there.
3. **Check that 2025-08-06 trade's exit specifically.** MFE +94.88R closing at
   exactly +10.00R is one trade, so it's probably not a cap, but the roundness is
   worth eyeballing in the trail logic.

All three are **fit-era observations, not validated findings** — the bar-only
holdout is closed, so anything here confirms forward only. But item 1 is
mechanical rather than statistical, which is the kind that usually survives.
