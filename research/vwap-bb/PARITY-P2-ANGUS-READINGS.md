# PARITY SHEET — ANGUS'S READINGS · FINAL

**P2 · Wednesday 2025-01-22 · 09:50 ET** — the candle covering 09:49:00–09:49:59 has just closed,
nothing from 09:50:00 onward has happened.

Recorded blind. No detector output consulted before or during the reading.

**COMPLETE. All fields answered, all follow-up questions resolved. Comparable in full.**

---

## §0 — Provenance

| | |
|---|---|
| Platform | TradingView |
| Contract charted | NQ continuous |
| Bar Replay used | Yes |
| Chart labels candles by | **open** time (stepped to the 09:48 two-minute bar) |
| Contract adjustment | **NOT back-adjusted — raw splice** |

**RESOLVED.** Re-checked on the daily timeframe across the mid-December 2024 roll: a visible
discontinuity is present. The series is a **raw front-month splice, not back-adjusted.**

**Consequence — good:** every price in this sheet is a true front-month (NQH5) price for
2025-01-22. Absolute level comparison against the detector is **valid**, no offset correction
needed.

**Consequence — one check for Stage B.** A non-adjusted series corrupts any lookback that crosses a
roll boundary. Session-anchored levels (Daily VWAP, NY VWAP, Daily POC) and the 20-bar BB lookbacks
on 2m/3m/5m are all far clear of the December roll and are unaffected. **The 4h range in §1d is
not obviously clear of it** — see the flag there.

---

## §1a — Cluster-eligible levels

| level | price |
|---|---|
| Daily VWAP — mid | 21904.36 |
| Daily VWAP — +1σ | 21953.28 |
| Daily VWAP — −1σ | 21855.44 |
| Daily VWAP — +2σ | 22002.20 |
| Daily VWAP — −2σ | 21806.52 |
| Daily VWAP — +3σ | 22051.12 |
| Daily VWAP — −3σ | 21757.59 |
| NY VWAP — mid | 21952.25 |
| NY VWAP — +1σ | 21963.50 |
| NY VWAP — −1σ | 21941.25 |
| Daily POC (4 ticks per row) | 21953.50 |

*Band spacing verified. Daily VWAP σ = **48.92**, exact across all six bands (±48.92 / ±97.84 /
±146.76). NY VWAP ≈ ±11.1 / ±22.25 / ±33.1. Both internally consistent.*

## §1b — Over-extension reference

| level | price |
|---|---|
| NY VWAP — +2σ | 21974.50 |
| NY VWAP — −2σ | 21930.00 |
| NY VWAP — +3σ | 21985.50 |
| NY VWAP — −3σ | 21919.25 |

## §1c — Structural levels

| level | price | note |
|---|---|---|
| Session high so far (from 18:00 ET) | 21988.00 | made on the 09:48 candle |
| Session low so far | 21768.00 | |
| Prior-day high | 21783.75 | **Globex** — full ~23h session, not RTH-only |
| Prior-day low | 21378.25 | **Globex** — same basis |
| Pre-market high (18:00 → 09:29) | 21934.25 | |
| Pre-market low | 21768.25 | |
| Week-to-date high | 21988.00 | 20–22 Jan |
| Week-to-date low | 21378.00 | 20–22 Jan |
| Prior-week high | 21686.75 | |
| Prior-week low | 20687.00 | |
| VAH | 21976.00 | out of scope (branch 7) — context only |
| VAL | 21879.00 | out of scope — context only |

*Cross-check: the pre-market high (21934.25) equals the 08:45 15-minute swing high in §5.
Consistent.*

**FINDING — prior-day high/low are read on a GLOBEX basis.** The specification does not state
whether "prior day" means the RTH cash session (09:30–16:00) or the full ~23h Globex session
(18:00–17:00 ET). The reference reading uses **Globex**. This is now the operative definition and
the detector must match it. It is not cosmetic: on 2025-01-22 the Globex prior-day high is
21783.75, and an RTH-only reading would return a different — almost certainly lower — value,
changing which structural levels are available to §4.

## §1d — HTF ranges

| | value |
|---|---|
| 4h range — high | 22428.75 |
| 4h range — low | 20695.50 |
| **Method** | **Swing highs and lows** |
| 1h range — high | 22111.00 |
| 1h range — low | 21379.00 |

Widths: 4h = **1733.25 pts** · 1h = **732.00 pts**.

**FINDING — this answer defines the spec.** §6's menu and §7's location filter both depend on the
4h range, which the specification never defines. "Swing highs and lows" is now the operative
definition. The swing method (fractal N, or discretionary) is not further specified and remains
open.

**⚠ STAGE B MUST CHECK — the 4h range may straddle the December 2024 roll.** §0 establishes the
series is a raw splice. The 4h high (22428.75) and low (20695.50) are roughly a December-2024 high
against a January-2025 low. **Confirm both swing points post-date the roll.** If the high is a
pre-roll NQZ4 print and the low a post-roll NQH5 print, the measured width **understates** the true
range by the roll spread (~230–250 pts, per the Stage 0 audit), because the deferred contract
trades at a premium.

The effect on the only thing that consumes this number is material:

| | range width | price at 21986.75 |
|---|---|---|
| as read | 1733.25 | **74.5%** — upper quartile |
| if high is pre-roll, +240 | 1973.25 | **≈65%** — just above mid |

That is the difference between "extended" and "mid-range" for §6's location filter. The 1h range
(732.00 pts) is January-2025-only and is unaffected.

## §2 — Bollinger Bands, per entry timeframe

**1m: n/a — unavailable on this platform for January 2025 (history depth).** Live branch, not
dead: the hand log contains 4 entries on 1M, 2 of them in-scope.

| TF | lower 2σ | basis (20 SMA) | upper 2σ |
|---|---|---|---|
| 1m | n/a | n/a | n/a |
| 2m | 21883.48 | 21933.23 | 21982.97 |
| 3m | 21890.70 | 21928.59 | 21966.39 |
| 5m | 21887.84 | 21929.16 | 21970.49 |

**Correction applied:** the 3m row as submitted had upper and lower transposed. Values unchanged,
column assignment corrected. Spacing verified symmetric: 2m ±49.75, 3m ±37.85, 5m ±41.33.

## §3 — Last completed candle per entry timeframe

| TF | label | open | high | low | close |
|---|---|---|---|---|---|
| 1m | n/a | n/a | n/a | n/a | n/a |
| 2m | 09:48 | 21956.75 | 21988.00 | 21953.00 | 21986.75 |
| 3m | 09:45 | 21960.00 | 21980.25 | 21950.00 | 21955.25 |
| 5m | 09:45 | 21960.00 | 21988.00 | 21950.00 | 21986.75 |

*Cross-checked and consistent: 3m and 5m share the 09:45 open (21960.00); 2m and 5m share the
09:49:59 close (21986.75) and the session high (21988.00); the 5m low equals the 3m low (21950.00),
made in the first three minutes.*

---

## §4 — Clusters

Computed from §1a plus the per-timeframe BB bases. **Two spec ambiguities determine the answer.
Both are findings, not preferences.**

**(a) "within ~10 points of each other" — total span, or adjacent-gap chaining?**
The spec does not say, and the two readings give different clusters here.

**(b) Are structural levels cluster-eligible?**
§1a is headed "cluster-eligible" and contains no structural levels. §4's distinct-types list
includes "structural ×1". **The specification contradicts itself.** Here it determines whether
cluster 1 exists on one timeframe or three.

### Ladder in the active zone

| price | level | gap to next |
|---|---|---|
| 21904.36 | Daily VWAP mid | 24.23 |
| 21928.59 | 3m BB basis | 0.57 |
| 21929.16 | 5m BB basis | 4.07 |
| 21933.23 | 2m BB basis | 1.02 |
| 21934.25 | Pre-market high *(structural)* | 7.00 |
| 21941.25 | NY VWAP −1σ | **11.00** |
| 21952.25 | NY VWAP mid | 1.03 |
| 21953.28 | Daily VWAP +1σ | 0.22 |
| 21953.50 | Daily POC | **10.00** |
| 21963.50 | NY VWAP +1σ | 38.70 |
| 22002.20 | Daily VWAP +2σ | |

Two knots separated by exactly **11.00** points — just outside a ~10 point tolerance.

### CLUSTER 1 · ~21933–21941

**If structural NOT eligible — 2-minute chart only**
members: 2m BB basis 21933.23 · NY VWAP −1σ 21941.25
low **21933.23** · high **21941.25** · span **8.02** · **2 types** (BB, VWAP)
*3m basis is 12.66 away and 5m is 12.09 — neither reaches, so no cluster on those timeframes.*

**If structural IS eligible — the pre-market high bridges, and it exists on all three**

| TF | members | low | high | span | types |
|---|---|---|---|---|---|
| 2m | BB 21933.23 · pre-mkt 21934.25 · NY−1σ 21941.25 | 21933.23 | 21941.25 | **8.02** | **3** |
| 3m | BB 21928.59 · pre-mkt 21934.25 | 21928.59 | 21934.25 | **5.66** | **2** |
| 3m *(chaining only)* | + NY−1σ 21941.25 | 21928.59 | 21941.25 | 12.66 | 3 |
| 5m | BB 21929.16 · pre-mkt 21934.25 | 21929.16 | 21934.25 | **5.09** | **2** |
| 5m *(chaining only)* | + NY−1σ 21941.25 | 21929.16 | 21941.25 | 12.09 | 3 |

### CLUSTER 2 · ~21953

**If span ≤10:**
members: NY VWAP mid 21952.25 · Daily VWAP +1σ 21953.28 · Daily POC 21953.50
low **21952.25** · high **21953.50** · span **1.25** · **2 types** (VWAP ×1, POC ×1)

**If adjacent-gap chaining:** add NY VWAP +1σ 21963.50 (exactly 10.00 from the POC)
low **21952.25** · high **21963.50** · span **11.25** · **2 types**

### No other clusters

Every remaining §1a level is isolated by 24+ points: Daily VWAP −3σ 21757.59 · −2σ 21806.52 ·
−1σ 21855.44 · mid 21904.36 · +2σ 22002.20 · +3σ 22051.12.

### Findings from §4

1. **Three levels sit inside 1.25 points** in cluster 2 — NY VWAP mid, Daily VWAP +1σ and the
   Daily POC. Unusually tight convergence from three independent computations.
2. **The two knots are separated by exactly 11.00 points.** Cluster membership here is decided by
   the last decimal of a tolerance written as "~10". Two faithful implementations can legitimately
   disagree.
3. **The Daily POC sits 1.25 from NY VWAP mid below it and exactly 10.00 from NY VWAP +1σ above
   it.** Under chaining it qualifies for both groups. The spec does not state which claims it, or
   whether a level may belong to more than one cluster.
4. **Ambiguity (b) is not cosmetic here.** Without structural, cluster 1 exists on 2m only. With
   it, on all three timeframes — a materially different signal population.

---

## §5 — HTF classification

**Uptrend.**

| | price | time (ET) |
|---|---|---|
| Most recent confirmed 15m swing high | 21934.25 | 22 Jan 08:45 |
| The one before it | 21906.75 | 22 Jan 04:30 |
| Most recent confirmed 15m swing low | 21880.25 | 22 Jan 07:00 |
| The one before it | 21868.75 | 22 Jan 05:15 |

*Verified: higher high (21934.25 > 21906.75) **and** higher low (21880.25 > 21868.75) — uptrend
follows from the data. All four swings are from the 08:45 bar or earlier, so all are confirmable
at 09:50 under a 15m N=2 fractal (completed bars run through 09:30; a swing at bar i requires bars
i+1 and i+2 completed, so 09:00 is the latest confirmable).*

---

## §6 — Filters

| filter | reading |
|---|---|
| **Location** | Recorded verbatim: *"Not really sure, because recent up movements yes. But overall no, still highs it can chase."* **Computed:** price at the instant (21986.75) sat at **74.5%** of the 4h range and **83.0%** of the 1h range — upper quartile of both. **FINDING: the §7 location filter has no numeric threshold**, and the reference trader found the call genuinely ambiguous. |
| **Confluence minimum** | **Hypothetical — no trigger fired.** Both clusters sit **below** current price (21986.75), so any setup at either would be a **long**. §5 is an **uptrend**, therefore any such setup is **with-trend**, requiring **2 distinct types**. Cluster 1: 2 types without structural, 3 with. Cluster 2: 2 types. **Both would clear a with-trend minimum under every reading.** |
| **Invalidation at entry** | Recorded: *"Last candle touched +1σ"* — clarified as **both Daily and NY**. Confirmed against the data: the 2m candle spanned 21953.00–21988.00, crossing **NY VWAP +1σ** (21963.50) fully, and its low (21953.00) sits 0.28 below **Daily VWAP +1σ** (21953.28). Both touched, so the reading is unambiguous *at this instant*. Moot regardless — no trigger — but **FINDING stands: the spec says "the opposing ±1σ" without naming which VWAP**, and on an instant where only one is touched the two readings diverge. |
| **Over-extension** | **Yes** — NY VWAP ±2σ touched this session at **09:32**. |

---

## §7 — Trigger

**No trigger.**

Timeframes checked: **2m, 3m, 5m. 1m not checkable** (platform history depth).

Reason, verbatim:

> *"Too early in session, it's just been steady up. Since we're hella bullish I'd want it to go
> down first before going up."*

**FINDING — two unwritten entry conditions.** Neither exists anywhere in the specification:

1. **A time-into-session judgement** — "too early", at 09:50, twenty minutes after the cash open.
   The spec's only time gate is A1's first tradeable signal bar at 09:36.
2. **A pullback requirement** — declining to enter long into sustained one-directional movement,
   wanting a retracement first. No such condition exists in the spec.

Both are candidate spec gaps and should be recorded regardless of the parity verdict. This is the
same class of finding the §9 box produced previously.

---

## §8 — Resulting trade

**n/a — no trigger fired.** Recorded: *"no trade was open in this chart, PA wasn't allowing a valid
setup."*

---

## §9 — Anything the sheet did not ask for

**Nothing.** Asked and answered — the reference trader reports no observation outside the sheet's
fields at this instant. Recorded as a genuine null, not an unfilled box.

---

## SUMMARY FOR STAGE B

### Nothing open. All four follow-ups resolved

| # | item | resolution |
|---|---|---|
| 1 | Contract adjustment | **Raw splice, not back-adjusted.** Visible discontinuity at the Dec-2024 roll. Absolute level comparison is valid, no offset. Raises one derived check — see §1d. |
| 2 | Prior-day high/low basis | **Globex** (~23h session), not RTH. Now the operative spec definition. |
| 3 | §6 invalidation — which ±1σ | **Both** Daily and NY were touched. Confirmed against the bar data. Ambiguity remains a finding for other instants. |
| 4 | §9 | **Nothing** — genuine null. |

### Comparable now

**Every section.** §1a · §1b · §1c · §1d · §2 · §3 · §4 · §5 · §6 · §7 · §8 · §9.

### One derived check, not a gap in the reading

The 4h range may straddle the December 2024 roll on a non-adjusted series (§1d). This is a
**detector-side and data-side** question, not something the hand reading can answer, and it is
answerable from the bar archive directly.

### Findings recorded independently of the parity verdict

1. **The 4h range has no spec definition.** "Swing highs and lows" becomes the operative
   definition; the swing method remains unspecified.
2. **The §7 location filter has no numeric threshold.** Price at 74.5% / 83.0% of the 4h / 1h
   ranges was genuinely ambiguous to the reference trader.
3. **The spec contradicts itself on structural cluster-eligibility.** Here it decides whether
   cluster 1 exists on one timeframe or three.
4. **"Within ~10 points" is undefined** — span or chaining. Both boundary cases occur at this
   instant: the two knots sit exactly 11.00 apart, and the POC sits exactly 10.00 from NY VWAP +1σ.
5. **"The opposing ±1σ" does not name which VWAP.** Moot at this instant — both were touched — but
   unresolved in the spec.
6. **Two unwritten entry conditions** in §7: a time-into-session judgement and a pullback
   requirement.
7. **Three independent levels converge inside 1.25 points** in cluster 2.
8. **"Prior day" is undefined in the spec.** The reference reading is **Globex**, not RTH. Same
   class of gap as findings 1, 4 and 5: a structural input the spec names but never scopes.
9. **The 4h range is measured on a non-adjusted series and may cross the December 2024 roll.** If
   it does, the location filter's input is wrong by ~14 percentage points of range position.

### Stage B instructions

Compare at **1.00 point tolerance**, field by field, MATCH/MISMATCH with **both** values shown.
Diagnose every mismatch as exactly one of: **spec ambiguity · implementation bug · charting
difference · reading error**.

**The detector is not assumed correct** — it has been wrong on three of three literalism checks in
this project, and this chart is the reference the specification was written from. **Do not adjust
the detector to match in this pass.** Do not soften a mismatch into "close enough."

**Materiality of the 1m blind spot is determined here:** if the detector does not fire on 1m at
this instant, the gap is moot for this gate.
