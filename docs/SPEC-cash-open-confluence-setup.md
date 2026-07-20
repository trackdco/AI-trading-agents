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

## PARAMETERS — CONFIRMED by Angus (20 Jul)
1. **POC = developing (today)**, live-building from the cash open — POC of the volume profile using
   only bars up to the current bar.  → `indicators.profile_asof(...)` (exists).
2. **Bollinger = 20 length, SMA basis, 2.0 σ, 0 offset.**  → `indicators.bollinger(df, 20, 2.0)` (exists).
3. **VWAP = Globex/overnight** (18:00 ET anchor).  → `indicators.daily_vwap` (exists).
4. **Multi-timeframe, execution TF = the TF the displacement prints on.** Angus: *"if it displaces
   through on the 2-minute Bollinger Band MA with POC aligning and VWAP rejection, I enter based on the
   2 minute. The entry mechanism is the same."* So scan {1m, 2m, 3m, 5m}; the displacement TF is the
   trade's execution TF (stop/retest measured on that TF's candles).
5. Still to tune (start with defaults, calibrate on data): confluence tolerance (how close BB-line, POC,
   VWAP must sit — start ~ a few points / ATR-scaled); displacement = candle **close** beyond the
   BB+POC confluence.

## ALL INDICATORS ALREADY EXIST (`src/engine/indicators.py`) — build is setup-logic only
| piece | engine function | note |
|---|---|---|
| Globex VWAP | `daily_vwap` (18:00 anchor) | + volume-weighted bands |
| Bollinger 20/SMA/2σ | `bollinger(df, 20, 2.0)` | population σ (ddof=0), matches TV |
| developing POC | `profile_asof` | developing profile; POC = max-volume bin as-of ts |
| fib levels | `snapshot._ote_levels` | for the fib-confluence variant |

## DETECTION ALGORITHM (per execution TF, per bar in 09:40–10:15)
1. Compute on this TF's candles: BB(20, 2σ) [basis + upper/lower], Globex VWAP, developing POC (asof bar).
2. **Confluence**: a BB line (basis per Angus's "BB MA"; also test outer band) sits within tolerance of
   the developing POC. VWAP is on the correct side (respected/rejected in the trade direction).
3. **Displacement**: a candle *closes through* the BB+POC confluence, moving away from VWAP (commitment).
4. **Entry**: on the **retest** of the broken level (POC or BB line) after the displacement candle.
5. **Stop**: just beyond the **displacement candle** extreme (low for long / high for short).
6. Direction: long when VWAP respected as support + up-displacement through confluence above; short mirror.

### Fib-confluence variant
When an `_ote_levels` fib coincides with VWAP + developing POC (3-way, within tolerance) and there is
conviction, wait for the **reaction** at the level and enter (no displacement break required).

## Measurement plan (once built)
- Detect CDR triggers 09:40–10:15 over 2026; grade with the current engine (V8 mgmt, structural stop).
- Compare candidates/day vs current 0.5 and vs Angus's ~1 A+/night; win% and $/trade.
- Success = the engine captures a meaningful share of the post-open edge Angus takes live.
