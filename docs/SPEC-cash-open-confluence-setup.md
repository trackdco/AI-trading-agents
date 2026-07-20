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

---

## v2 — FULL MODEL from 11 live executions (Angus, 20 Jul) — supersedes the sketch above

v1 (close-through + fixed 2R) LOST (28-32% win). Reviewing 11 real trades (London + NY) crystallized the
actual method. It is a **confluence-rejection** system (reversion OR continuation), NOT close-through.

### The canonical setup
1. **Bias/context gate.** Read Asia→London behaviour, session sweeps (London/Asia highs-lows taken),
   and overall order flow → a directional bias for the day. Only take setups WITH the bias.
   ("I go with what the market's giving me.")
2. **Confluence anchor** — a STACK of levels sitting together (the tighter, the more A+):
   - **BB basis** (20 SMA, "the moving average") — the spine of almost every entry.
   - **VWAP deviation band** — usually ±1 (NY-anchored *and* Globex); ±2/±3 = over-extended → revert.
   - **Fib of a marked leg** (opening 9:30 leg or the impulse leg): **0.705 (OTE)**, 0.5 (equilibrium), 0.382.
   - **POC** — developing daily (sticks near price in NY), **weekly POC**, daily value-area high.
   - **15-minute BB basis** — a strong NY magnet ("price reaches it a lot").
3. **Trigger = displacement then REJECTION** (two flavours):
   - *Reversion:* over-extension to VWAP +2/+3 → return to 0.5/VWAP-mid → reject the aligned band+fib.
   - *Continuation:* displacement through BB-basis + VWAP band → **retest of the BB basis** → enter with trend.
   The confirmation is a **rejection block / wick / a candle closing back across the BB basis** — NOT the
   displacement candle itself (v1's mistake).
4. **Entry** — LIMIT at the confluence level (BB basis / VWAP band / fib 0.705), or MARKET on the
   rejection candle. Preferred: wait for the rejection confirmation.
5. **Stop** — beyond the **displacement/rejection candle** (or the 9:30 opening candle); the rejection
   high/low. NOT too tight — hold a buffer (repeated lesson: greedy tight stops got wicked out).
6. **Break-even at the first magnet** — POC or the VWAP middle band (~1R). Bank risk early.
7. **Target = the NEXT structural level** (never a fixed R): VWAP middle band, 15m BB basis, weekly/daily
   POC, opposite VWAP band (−2), session highs/lows (Asia/London), **midnight open**, daily VA high, HTF level.

### Level catalog to build (engine has BB, VWAP dev-bands, developing POC, fib; ADD:)
- weekly POC + daily value-area high (extend `profile_asof` scope)
- 15-minute BB basis
- midnight open (00:00 ET price)
- session highs/lows: Asia, London, NY (rolling session extremes)
- fib anchored on the **opening 9:30 leg** (impulse from the open)

### What v2 changes vs v1 (why v1 lost)
- entry = retest/rejection, NOT displacement close.
- exits = level-based (BE at first magnet → target next level), NOT fixed 2R.
- stop = beyond the displacement candle with a BUFFER, not minimal-risk-maximising.
- confluence must STACK (BB basis + VWAP band + fib + POC), not just POC≈BB.
- add the bias/context gate.

## Measurement plan (once built)
- Detect CDR triggers 09:40–10:15 over 2026; grade with the current engine (V8 mgmt, structural stop).
- Compare candidates/day vs current 0.5 and vs Angus's ~1 A+/night; win% and $/trade.
- Success = the engine captures a meaningful share of the post-open edge Angus takes live.
