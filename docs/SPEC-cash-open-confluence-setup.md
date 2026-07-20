# SPEC: Cash-Open Confluence Displacement-Retest (Angus's A+ post-open setup)

**Origin:** Angus, 20 Jul 2026. The bot's detector is nearly blind 09:40–10:15 (0.5 setups/day
vs Angus's ~1 genuine A+ per night — see `FINDING`/diagnosis). This is the setup it must learn to
see. Angus is strategy authority; this is his verbatim setup, formalized. Build to it faithfully.

## Window
Cash open **09:40–10:15 ET** (the diagnosed detection blindspot; Angus's proven live edge window).

## The A+ setup — "Confluence Displacement-Retest" (CDR)

Angus, verbatim: *"usually VWAP, Bollinger Bands, and the daily POC are pivotal. Alignment of all
3 is something else. Respect a VWAP, break the Bollinger Band and POC, enter on a retest of POC or
the Bollinger Band, stops below the candle that displaced through."*

Formalized (long example; short is mirror):
1. **VWAP respected** — price holds / bounces off session VWAP (VWAP is acting as support for a long).
2. **Displacement through confluence** — a candle *breaks through* BOTH the Bollinger Band AND the
   daily POC (a strong directional candle clearing the BB and POC that sit together = the confluence).
3. **Entry on retest** — enter on the pullback that **retests the broken level** (the POC or the
   Bollinger Band, now flipped to support).
4. **Stop** — just **below the displacement candle** (the candle that broke through); mirror above for shorts.

The edge = **3-way confluence** (VWAP + BB + POC aligned) + **displacement** (commitment through it)
+ **retest** (low-risk entry) + **structural stop** (the displacement candle).

## Fib-confluence variant
Angus: *"if a fib level aligns with VWAP and POC, if there is conviction I will wait for the reaction
and just enter."*
- When a **fib level coincides with VWAP + POC** (3-way), and there is conviction, wait for the
  **reaction** at that level and enter (no displacement-break required — the confluence + reaction is
  the trigger). Reuse the existing OTE fib anchors (`src/engine/snapshot.py::_ote_levels`).

## Buildable components (all confirmed available)
| piece | source | status |
|---|---|---|
| session VWAP | engine indicators | exists |
| Bollinger Bands | rolling mean ± k·σ | add (trivial) |
| daily / prior-day / developing POC | CVD footprint (`data/reference/cvd/*.parquet`) | verified computable |
| fib levels | `_ote_levels` (pass-22) | exists |
| displacement candle / retest / structural stop | new detection logic | build |

## OPEN PARAMETERS — need Angus's exact settings before building (they change the levels materially)
1. **Bollinger Bands:** period + σ (standard 20 / 2.0?) and **timeframe** (1m / 2m / 5m candles?).
2. **Which POC:** developing (today, live-building — thin at 09:40), **prior-day**, or overnight POC?
   ("daily POC" is ambiguous for a 09:40 entry.)
3. **VWAP anchor:** cash-open (09:30) or Globex/overnight (18:00)? "Respect" tolerance (ticks)?
4. **Displacement threshold:** what qualifies as "break through" — candle *close* beyond BB & POC, and
   by how much (ticks / % of ATR)?
5. **Confluence tolerance:** how close must VWAP, BB, POC be to count as "aligned" (ticks/points)?

## Measurement plan (once built)
- Detect CDR triggers 09:40–10:15 over 2026; grade with the current engine (V8 mgmt, structural stop).
- Compare candidates/day vs current 0.5 and vs Angus's ~1 A+/night; win% and $/trade.
- Success = the engine captures a meaningful share of the post-open edge Angus takes live.
