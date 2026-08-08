# PARITY GATE — STAGE B — P2 · 2025-01-22 · 09:50 ET

**Run 2026-08-08. Input: `PARITY-P2-FINAL.md`, Angus's blind hand-reading, recorded with no
detector output consulted. Tolerance 1.00 point. N_trials: 0. Holdout sealed. The sealed
workbench result was NOT opened — only the pre-outcome path (`signal_candidates`) was executed.**

---

# VERDICT: **PARITY FAIL**

**36 of 48 numeric fields MATCH. 12 MISMATCH.** The mismatches are not scattered — they are
**the entire NY VWAP band family, the daily POC, the 4h range, and the most recent 15m swing
high**. Those four groups drive cluster formation, the HTF classification and the location
filter: three of the four inputs to a trigger decision.

**The trigger decision itself agreed — both sides say NO TRIGGER — and that agreement is not
evidence of parity.** The single raw trigger the detector produced at this instant died at the
**first** gate it met (confluence count, 1 distinct type against a minimum of 2). None of the
mismatched values was ever consulted. A gate that agrees because nothing reached the disputed
logic has not tested the disputed logic.

**The bar data is identical.** All 12 OHLC fields across 2m/3m/5m match to **0.00**; Bollinger
basis and bands match to **≤0.09**; session, pre-market and prior-day extremes match to **≤0.50**.
This is not a data-feed disagreement — the reference chart and the bar archive are the same
market, to the tick. **Every mismatch is downstream of a definition choice, not a data problem.**

**No implementation bug was found at this instant.** Every mismatch resolves to spec ambiguity —
the specification does not say what the detector had to decide. That is a different finding from
the previous literalism checks and it is stated plainly rather than hedged.

---

# 1. ROLL CHECK — done first, and it points at the wrong range

Angus flagged the **4h** range as possibly straddling the December 2024 roll on a non-adjusted
series. **It does not. The 1h range does.**

## 1.1 The two 4h swing points, located in the archive

| | value read | archive print | ET timestamp | UTC day | **contract** |
|---|---|---|---|---|---|
| 4h **high** | 22428.75 | **22425.75** | **2024-12-16 23:28** | 2024-12-17 | **NQH5** |
| 4h **low** | 20695.50 | **20694.00** | **2025-01-13 04:16** | 2025-01-13 | **NQH5** |

**Both are post-roll NQH5 prints. They do not straddle.** The high is the highest print anywhere
in the front-month series before the instant; the low is the highest-volume print of the January
13 washout (1,162 contracts on that minute). The readings are 3.00 and 1.50 points off the
archive respectively — the same swing points, read to a different tick.

## 1.2 The roll, and its measured spread

The Databento front-month splice switches **NQZ4 → NQH5 on UTC day 2024-12-17**, i.e. at
**19:00 ET on 2024-12-16**. The spread at the 4h-high minute, quoted directly by the
`NQZ4-NQH5` calendar instrument:

| | |
|---|---|
| NQH5 | 22423.75 / **22425.75** / 22423.50 / 22425.25 |
| NQZ4 | 22123.50 / 22124.25 / 22123.50 / 22124.25 |
| `NQZ4-NQH5` | **301.15** |

**The roll spread is 301.15 points, not the ~230–250 assumed in the flag.** Worth correcting: the
deferred premium at this roll was larger than the project's earlier "~250 pt unadjusted gaps"
shorthand.

## 1.3 The 4h range, recomputed both ways

| basis | high | low | width | position of 21986.75 |
|---|---|---|---|---|
| **as read** | 22428.75 | 20695.50 | 1733.25 | **74.50%** |
| **archive-measured** (both NQH5) | 22425.75 | 20694.00 | 1731.75 | **74.65%** |
| counterfactual *if* the high were pre-roll NQZ4 (+301.15) | 22729.90 | 20695.50 | 2034.40 | 63.47% |

**The counterfactual does not apply.** The reading stands at 74.5%, and the archive independently
confirms it at 74.65%. Angus's ⚠ resolves **negative** — the concern was correct in kind and
wrong in target.

## 1.4 The 1h range DOES straddle the roll

| | value read | archive | ET timestamp | **contract** |
|---|---|---|---|---|
| 1h **high** | 22111.00 | 22112.25 first ≥ 22111.00 | **2024-12-16 13:21** | **NQZ4 — PRE-ROLL** |
| 1h **low** | 21379.00 | 21377.75 (session 2025-01-21 low) | 2025-01-21 | NQH5 — post-roll |

The 1h high is a **December 16 print from before the 19:00 ET splice**, six hours before the 4h
high on the other side of it. On a raw splice the two are not comparable prices.

| basis | width | position of 21986.75 |
|---|---|---|
| as read | 732.00 | **83.03%** |
| roll-corrected (+301.15 on the high) | 1033.15 | **58.82%** |

**A 24-point swing in range position — larger than the effect predicted for the 4h range.**
83% reads as "extended"; 58.8% reads as "just above mid".

## 1.5 Which the detector used: **neither**

The detector does not build a swing range on either timeframe. See §4.4 — its "4h range" is a
session-local construction that never crosses a roll, so it is **immune to the splice problem by
construction and wrong against the reference for an unrelated reason**.

---

# 2. FIELD-BY-FIELD COMPARISON

Every field, matches included. Detector values are shown to 4 dp as computed.

**Instant.** Detector close-minute label `cm = 590` = 09:50, i.e. the bar covering
09:49:00–09:49:59 has closed. Only timeframes with `590 % tf == 0` evaluate there — **1m, 2m and
5m**. The **3m** bar last closed at `cm = 588` (09:48), and its row is compared at that close,
which is also the bar Angus reported.

## 2.1 §1a — cluster-eligible levels

| field | Angus | detector | \|Δ\| | verdict |
|---|---|---|---|---|
| Daily VWAP mid | 21904.36 | 21903.4656 | 0.8944 | MATCH |
| Daily VWAP +1σ | 21953.28 | 21952.3491 | 0.9309 | MATCH |
| Daily VWAP −1σ | 21855.44 | 21854.5820 | 0.8580 | MATCH |
| Daily VWAP +2σ | 22002.20 | 22001.2327 | 0.9673 | MATCH |
| Daily VWAP −2σ | 21806.52 | 21805.6984 | 0.8216 | MATCH |
| **Daily VWAP +3σ** | 22051.12 | 22050.1163 | **1.0037** | **MISMATCH** |
| Daily VWAP −3σ | 21757.59 | 21756.8148 | 0.7752 | MATCH |
| **NY VWAP mid** | 21952.25 | 21950.0875 | **2.1625** | **MISMATCH** |
| **NY VWAP +1σ** | 21963.50 | 21966.7339 | **3.2339** | **MISMATCH** |
| **NY VWAP −1σ** | 21941.25 | 21933.4412 | **7.8088** | **MISMATCH** |
| **Daily POC** | 21953.50 | 21909.0000 | **44.5000** | **MISMATCH** |

The daily VWAP +3σ misses by **0.0037 of a point over tolerance**. It is recorded as a MISMATCH.
It is not softened, and the reason it is the only daily band to fail is exactly the reason all
six nearly failed — see §3.1.

## 2.2 §1b — over-extension reference

| field | Angus | detector | \|Δ\| | verdict |
|---|---|---|---|---|
| **NY VWAP +2σ** | 21974.50 | 21983.3803 | **8.8803** | **MISMATCH** |
| **NY VWAP −2σ** | 21930.00 | 21916.7948 | **13.2052** | **MISMATCH** |
| **NY VWAP +3σ** | 21985.50 | 22000.0267 | **14.5267** | **MISMATCH** |
| **NY VWAP −3σ** | 21919.25 | 21900.1484 | **19.1016** | **MISMATCH** |

## 2.3 §1c — structural levels

| field | Angus | detector | \|Δ\| | verdict |
|---|---|---|---|---|
| Session high so far | 21988.00 | 21988.0000 | 0.0000 | MATCH |
| Session low so far | 21768.00 | 21768.2500 | 0.2500 | MATCH |
| **Prior-day high (Globex)** | 21783.75 | 21783.5000 | 0.2500 | MATCH |
| **Prior-day low (Globex)** | 21378.25 | 21377.7500 | 0.5000 | MATCH |
| Pre-market high | 21934.25 | 21934.2500 | 0.0000 | MATCH |
| Pre-market low | 21768.25 | 21768.2500 | 0.0000 | MATCH |
| Week-to-date high | 21988.00 | — | — | NOT COMPARABLE — not implemented |
| Week-to-date low | 21378.00 | — | — | NOT COMPARABLE — not implemented |
| Prior-week high | 21686.75 | — | — | NOT COMPARABLE — not implemented |
| Prior-week low | 20687.00 | — | — | NOT COMPARABLE — not implemented |
| VAH / VAL | 21976.00 / 21879.00 | — | — | NOT COMPARABLE — out of scope, branch 7 |

**Informational only, from the archive, not part of the verdict** (these levels are not
implemented, so they cannot be compared — but the readings can be sanity-checked):

| | archive, Sunday-18:00-anchored week | Angus | note |
|---|---|---|---|
| Week-to-date H/L | 21988.00 / 21377.75 | 21988.00 / 21378.00 | **agrees to 0.25** — confirms his week anchors Sunday 18:00 ET |
| Prior-week H/L | 21682.50 / 20694.00 | 21686.75 / 20687.00 | disagrees by **+4.25 / −7.00**, unexplained; recorded as an open item, not diagnosed |

## 2.4 §1d — HTF ranges

| field | Angus | detector | \|Δ\| | verdict |
|---|---|---|---|---|
| **4h range high** | 22428.75 | 21920.0000 | **508.7500** | **MISMATCH** |
| **4h range low** | 20695.50 | 21768.2500 | **1072.7500** | **MISMATCH** |
| 4h width | 1733.25 | **151.75** | — | **MISMATCH** |
| 4h position of 21986.75 | **74.50%** | **143.99%** | — | **MISMATCH** |
| 1h range high / low | 22111.00 / 21379.00 | — | — | NOT COMPARABLE — no 1h range is computed |

## 2.5 §1e / §1f — session boxes, data extremes

**NOT COMPARABLE — not implemented.** Out of scope, branches 8 and 3 respectively
(`OUT-OF-SCOPE-BRANCHES.md`). The detector has no Asia/London/NY boxes and no economic calendar.
Angus's box boundaries are recorded as spec input, not as a comparison.

## 2.6 §2 — Bollinger bands per entry timeframe

| field | Angus | detector | \|Δ\| | verdict |
|---|---|---|---|---|
| BB 2m basis | 21933.23 | 21933.2250 | 0.0050 | MATCH |
| BB 2m upper 2σ | 21982.97 | 21982.9653 | 0.0047 | MATCH |
| BB 2m lower 2σ | 21883.48 | 21883.4847 | 0.0047 | MATCH |
| BB 3m basis | 21928.59 | 21928.5875 | 0.0025 | MATCH |
| BB 3m upper 2σ | 21966.39 | 21966.3890 | 0.0010 | MATCH |
| BB 3m lower 2σ | 21890.70 | 21890.7860 | 0.0860 | MATCH |
| BB 5m basis | 21929.16 | 21929.1625 | 0.0025 | MATCH |
| BB 5m upper 2σ | 21970.49 | 21970.4878 | 0.0022 | MATCH |
| BB 5m lower 2σ | 21887.84 | 21887.8372 | 0.0028 | MATCH |
| BB 1m, all three | n/a | *(computed, withheld — see §6)* | — | not compared |

> **The ±2σ bands are not detector inputs.** §3 makes only the **BB MA (basis)** a cluster level.
> The bands were computed here purely to widen the comparison surface. Their agreement is
> reassuring about the price feed; it says nothing about the strategy path. **The basis — the
> level that does matter — matches on all three timeframes to 0.005.**

## 2.7 §3 — last completed candle per entry timeframe

| TF | label | field | Angus | detector | verdict |
|---|---|---|---|---|---|
| 2m | 09:48 | O / H / L / C | 21956.75 / 21988.00 / 21953.00 / 21986.75 | identical | **MATCH ×4, Δ = 0.00** |
| 3m | 09:45 | O / H / L / C | 21960.00 / 21980.25 / 21950.00 / 21955.25 | identical | **MATCH ×4, Δ = 0.00** |
| 5m | 09:45 | O / H / L / C | 21960.00 / 21988.00 / 21950.00 / 21986.75 | identical | **MATCH ×4, Δ = 0.00** |
| 1m | n/a | — | n/a | O 21970.75 H 21988.00 L 21969.00 C 21986.75 | not compared |

**Twelve of twelve exact.** The bar-labelling convention, the aggregation boundaries and the
price feed all agree. This is the single most important MATCH block on the sheet: it removes
data as an explanation for anything below.

## 2.8 §4 — clusters

| | Angus (2m, structural not eligible) | detector (2m) |
|---|---|---|
| count | **2** | **3** |
| lower | — *(none)* | **21903.4656 – 21909.0000**, span 5.53, types {vwap, poc} |
| middle | 21933.23 – 21941.25, span **8.02**, types {bb, vwap} | 21933.2250 – 21933.4412, span **0.22**, types {bb, vwap} |
| upper | 21952.25 – 21953.50, span **1.25**, types {vwap, **poc**} | 21950.0875 – 21952.3491, span 2.26, types {**vwap only**} |

**MISMATCH on count and on the composition of every cluster.** Two independent causes, both
already in the tables above: the detector's POC sits 44.5 points lower, so it anchors a cluster
Angus does not have and vacates the one he does; and the detector's NY VWAP −1σ sits 7.81 points
lower, collapsing the middle cluster's span from 8.02 to 0.22.

**The operative consequence:** on Angus's chart the upper cluster carries **two** distinct types
and clears a with-trend confluence minimum. On the detector it carries **one** and does not.
That is precisely the gate that killed the only trigger at this instant.

## 2.9 §5 — HTF classification

| field | Angus | detector | \|Δ\| | verdict |
|---|---|---|---|---|
| **classification** | **uptrend** | **range** | — | **MISMATCH** |
| **15m swing high, latest** | 21934.25 @ 08:45 | **21905.00 @ 06:15** | **29.25** | **MISMATCH** |
| 15m swing high, 2nd-latest | 21906.75 @ 04:30 | 21907.00 @ 04:30 | 0.25 | MATCH |
| 15m swing low, latest | 21880.25 @ 07:00 | 21880.00 @ 07:00 | 0.25 | MATCH |
| 15m swing low, 2nd-latest | 21868.75 @ 05:15 | 21868.75 @ 05:15 | 0.00 | MATCH |

**Three of the four swings match to ≤0.25, at the same timestamps.** The whole classification
turns on the fourth. Cause in §3.4.

## 2.10 §6 — filters

| filter | Angus | detector | verdict |
|---|---|---|---|
| **Location** | 74.50% of 4h, 83.03% of 1h — "genuinely ambiguous" | **143.99%** of its 4h range → **all longs blocked** | **MISMATCH** |
| **Confluence** | both clusters clear a with-trend minimum of 2 | the only cluster carrying a trigger has **1** type → **fails** | **MISMATCH** |
| **Invalidation at entry** | last candle touched **+1σ** (both daily and NY) | for a long: bar high 21988.00 ≥ NY +1σ 21966.73 → **blocks**; also ≥ daily +1σ 21952.35 | **MATCH on state** (the band prices themselves are already counted as MISMATCH in §2.1) |
| **Over-extension** | yes, NY ±2σ touched at 09:32 | **not implemented as a gate** (§3 defines it; only pattern A consumes it, and the taxonomy is out of scope, branch 1). On the detector's own bands it is trivially true from **09:30**, because σ = 0 on the anchor bar | NOT COMPARABLE |

## 2.11 §7 / §8 — the trigger and the trade

| | Angus | detector | verdict |
|---|---|---|---|
| **Trigger at 09:50** | **NO TRIGGER** | **NO CANDIDATE** | **MATCH** |
| timeframes checked | 2m, 3m, 5m (1m not checkable) | 1m, 2m, 5m at cm 590; 3m at cm 588 | — |
| raw trigger events before filters | — | **one**: 5m long rejection on cluster 21950.09–21952.35 | — |
| where it died | — | **confluence count** — 1 distinct type against a minimum of 2 | — |
| resulting trade | n/a | n/a | **MATCH** |

The engine's first candidate of the whole session is at **cm 623 (10:23)**. Nothing survives the
filter stack anywhere in 09:36–09:50.

---

# 3. MISMATCH DIAGNOSES — one category each, no fifth category

## 3.1 The daily VWAP +3σ, the whole NY VWAP family, and the daily POC — **SPEC AMBIGUITY**

**Nine mismatched fields, one root cause: the bar timeframe the indicator is computed from.**

TradingView computes VWAP and the session volume profile from the bars on the chart. Angus's
chart is **2-minute**. The detector computes both from **1-minute** bars. Recomputing from 2m
bars reproduces his readings:

| indicator | Angus | detector (1m) | recomputed on **2m** | residual |
|---|---|---|---|---|
| Daily VWAP mid | 21904.36 | 21903.4656 | **21904.3581** | **0.002** |
| Daily VWAP σ | 48.92 | 48.8836 | **48.9212** | **0.001** |
| Daily VWAP +1σ | 21953.28 | 21952.3491 | **21953.28** | **0.00** |
| NY VWAP mid | 21952.25 | 21950.0875 | **21952.3211** | **0.07** |
| NY VWAP σ | ≈11.10 | **16.6464** | **11.0757** | 0.02 |
| NY VWAP −1σ | 21941.25 | 21933.4412 | **21941.25** | **0.00** |
| Daily POC (1.00 pt bins, 18:00 anchor) | 21953.50 | 21909.00 | **21953.00** | 0.50 |

**The VWAP identification is conclusive** — six independent quantities reproduced to ≤0.07. The
POC identification is strong but not proof of TradingView's internals: 2m aggregation moves the
detector's POC from 21909.00 to 21953.00, within tolerance of his 21953.50, but the POC is a
coarse statistic and the uniform volume-spreading model is very sensitive to bar width.

**Why this is spec ambiguity and not a charting difference.** §2 specifies *"standard TradingView
VWAP"* — an indicator whose value depends on the chart's timeframe — and never says which
timeframe feeds it. This is not a convention difference where neither side is wrong and no code
change follows. **It is unresolvable by any implementation as the spec stands**: §1's MTF
arbitration evaluates four entry timeframes simultaneously, so a detector that computed the VWAP
per entry timeframe would still disagree with a 2m chart on three of the four. The spec has to
name the feed. Until it does, the level set is undefined.

**Why the daily bands nearly all passed and the NY bands all failed.** The daily VWAP has ~950
bars of history at this instant, so 1m and 2m aggregation converge — mid differs by 0.89 and σ by
0.04. The band error is `k · Δσ` plus the mid error, which is why **+3σ is the first daily band
to breach tolerance, by 0.0037**. The NY VWAP has only **20 bars** since its 09:30 anchor;
aggregation has not converged and **σ differs by 50% — 16.65 against 11.08**. Same mechanism,
opposite regime.

**Materiality: high.** The NY ±1σ levels are cluster-eligible *and* are the §7 invalidation
reference. A 50% error in their spacing changes both the cluster set and the filter.

## 3.2 The daily POC's downstream effect — **SPEC AMBIGUITY** (consequence of 3.1)

Counted once above, recorded again because it is the largest single number on the sheet. A POC
44.5 points from the reference is not a rounding difference: it is a **different level**, and it
moves the "poc" type from the upper cluster to a cluster the reference chart does not have.

## 3.3 The 4h range high and low — **SPEC AMBIGUITY**

**Detector's construction, read from the code:** a `deque(maxlen=6)` of completed **240-minute
blocks**, aligned to ET minute-of-day multiples of 240 and **rebuilt from scratch each session**.
At the instant it holds four blocks:

| block | ET window | high | low |
|---|---|---|---|
| 1 | 18:00–19:59 *(partial, 120 min)* | 21843.75 | 21768.25 |
| 2 | 20:00–23:59 | 21876.75 | 21811.50 |
| 3 | 00:00–03:59 | 21896.25 | 21839.50 |
| 4 | 04:00–07:59 | 21920.00 | 21868.75 |
| | **combined** | **21920.00** | **21768.25** |

The current partial block (08:00–09:49) is excluded, which is point-in-time correct — and which
is also where the session high 21988.00 was made. **So price sits at 143.99% of its own "4h
range", and the location filter blocks every long.**

**Reference construction:** multi-week swing high and low, 1733.25 points wide, price at 74.50%.

These are not two readings of one definition. They are different objects: a ~14-hour intra-session
window against a five-week swing range, **a factor of 11 apart in width**. §1 says only
*"1h/4h for range extremes"* and §7 says only *"no longs at HTF range top"*. Neither states a
lookback, a swing method, or whether the range resets at the session boundary. **The spec does
not decide this, so the implementation invented it.**

Recorded without softening: a "range" that price sits 44% above is not a range under any reading
of §7, and the filter derived from it is not doing what §7 describes.

## 3.4 The most recent 15m swing high, and therefore the HTF flag — **SPEC AMBIGUITY**

**The 08:30 and 08:45 fifteen-minute bars print the same high, 21934.25, to the tick.**

| 15m bar (ET open) | high |
|---|---|
| 08:15 | 21924.00 |
| **08:30** | **21934.25** |
| **08:45** | **21934.25** |
| 09:00 | 21933.25 |
| 09:15 | 21919.75 |

The detector's fractal test is **strictly greater on both sides**. Against an equal neighbour it
fails, so **neither** bar is admitted as a swing high — the left-side test on 08:45 returns
False. Its last two confirmed highs fall back to 21907.00 (04:30) and 21905.00 (06:15): a
**lower** high. With a higher low, that is **range**. Angus's eye takes 08:45, giving a higher
high and therefore **uptrend**.

The frozen parameter (A2, gate 4) reads *"15m fractal N=2; HH+HL up, LH+LL down, else range"*.
**It does not say how to treat equal extremes**, and this instant lands exactly on that silence.
Under `>=` on one side, the flag flips.

**Materiality at this instant: none.** The only trigger is a **long**, and under both `range` and
`uptrend` a long needs 2 distinct types. Only a `downtrend` flag would have raised it to 3, and
neither reading produces one. **Materiality in general: high** — the flag gates the confluence
minimum on every counter-trend setup in the study.

## 3.5 The location filter's range position — **SPEC AMBIGUITY** (consequence of 3.3)

143.99% against 74.50%. Counted separately because it is the field §7 actually consumes, and
because the two values fall on opposite sides of the `1 − LOC_BAND = 0.80` threshold: the
detector blocks all longs, the reference reading blocks none.

## 3.6 The confluence count on the triggering cluster — **SPEC AMBIGUITY** (consequence of 3.1)

1 type against 2. Downstream of the POC and NY VWAP mismatches, not an independent defect.

## 3.7 Categories NOT used, and why

| category | why not used |
|---|---|
| **implementation bug** | **No field was found where the code contradicts a stated rule.** Every mismatch traces to something the spec leaves undefined. The two literalism checks that *could* have failed — prior-day basis and the bar-labelling convention — both came back clean (§4). |
| **charting difference** | Considered for the VWAP/POC family and rejected: this is not a convention where neither side is wrong. §1 evaluates four entry timeframes at once, so **no implementation can match a single chart on all four**. The spec must name the feed; that makes it ambiguity, not convention. |
| **reading error** | Considered for the 4h high (22428.75 against an archive 22425.75) and the 15m swing high, and rejected in both cases. The 4h high is the correct swing point read 3.00 points off — a tick-level difference between feeds, not a wrong level, and it does not change the range position (74.50% against 74.65%). The 15m swing is a genuine tie in the data, not a misread. |

---

# 4. SPEC DEFINITIONS SET BY THIS READING — implementation checked against each

## 4.1 "Prior day" high/low = **GLOBEX**, not RTH-only — **implementation AGREES**

Not a contradiction. The detector takes the prior session's extremes as
`max/min` over the **whole Globex session dict** (18:00 ET → 16:59 ET), in
`vwapbb_opportunity.main()` and `stage2_smoke.main()`:

| basis | high | low | vs Angus |
|---|---|---|---|
| **Globex (what the detector uses)** | **21783.50** | **21377.75** | **0.25 / 0.50 — MATCH** |
| RTH-only (what it does not use) | 21772.00 | 21525.75 | 11.75 / 147.50 — would MISMATCH |

**The RTH-only reading would have failed on the low by 147.50 points.** The definition Angus set
is the one already implemented, and the gate confirms it rather than changing it. Worth recording
that this was the one place the detector could have failed silently and did not.

## 4.2 4h range = swing highs and lows — **implementation CONTRADICTS this**

The detector uses **fixed 240-minute clock blocks, reset every session**. There is no swing logic
in the 4h path at all — no fractal, no lookback across sessions. Full detail in §3.3.

**This is a direct contradiction of the definition the reading sets**, and it is the largest
open item this gate produced. The swing *method* remains unspecified (fractal N, or
discretionary), so stating "swings" is necessary but not sufficient to close it.

---

# 5. THE FOUR AMBIGUITIES — reading taken, and whether the other would change the trigger

| # | ambiguity | reading the implementation takes | evidence | other reading changes the trigger? |
|---|---|---|---|---|
| **a** | **structural cluster-eligibility** | **NOT eligible.** The level list `lv` contains only `bb`, `poc` and `vwap` types; session/pre-market/prior-day extremes enter the **target menu** only | `stage2_smoke.py` lines building `lv` vs `menu` | **NO.** The nearest structural level to the triggering cluster (pre-market high 21934.25) is **15.84 pts** from 21950.09 — outside tolerance under either reading. Adding structural levels does create a 3-type cluster at 21929.16–21934.25 on 5m, but no bar at this instant trades into it (all four bars have lows ≥ 21950.00) |
| **b** | **span vs adjacent-gap chaining** | **CHAINING.** `cluster_levels()` groups while `p − previous ≤ tol`, with no cap on total span | `vwapbb_signals.cluster_levels()` | **NO.** Every detector cluster at this instant has a total span ≤ 5.53, so the two readings coincide exactly. The boundary cases Angus found — the 11.00 gap between knots, the POC sitting at exactly 10.00 from NY +1σ — **do not arise on the detector's numbers**, because its POC is 44.5 points away. The ambiguity is real and simply does not bind here |
| **c** | **which VWAP is "the opposing ±1σ"** | **NY VWAP**, and the band **on the side of travel** — a long is blocked when the bar high reaches NY +1σ | `if direction == "long" and th_ >= nmid + nsig` | **NO.** Bar high 21988.00 exceeds NY +1σ (21966.73) **and** daily +1σ (21952.35), so both named readings block. A third reading — the band *opposite* travel — would not block, but the trigger is already dead at the confluence gate, which runs first |
| **d** | **the 4h range definition** | **Session-local completed 240-minute blocks**, max 6, current partial block excluded, reset each session | `h4 = deque(maxlen=6)`, flushed on `(mm+1) % 240 == 0` | **NO** at this instant — the trigger dies at the confluence gate before the location filter runs. **But this is the ambiguity with the largest general effect:** the two readings put price at 143.99% and 74.50% of range, on opposite sides of the 0.80 block threshold |

**All four: no change to the trigger decision at this instant — and that is a weak result, not a
reassuring one.** The reason is uniform: the single raw trigger died at the **earliest** gate in
the stack, so no ambiguity downstream of confluence counting was ever reached. This instant
cannot discriminate between them. **A second instant, chosen where a trigger survives past
confluence, is required before any of these four can be said to be tested.**

---

# 6. THE 1-MINUTE BLIND SPOT — **MOOT for this gate**

**Stated explicitly, as required.**

> **The detector does not fire on 1m at this instant. At `cm = 590` the 1-minute evaluation
> produces zero raw triggers, and the engine produces zero candidates on any timeframe. The
> inability to chart 1m for January 2025 therefore costs this gate nothing, and the verdict
> above does not depend on it.**

The 1m detector state was computed and is on record in `data/parity_p2_detector.json`. It is not
tabulated against a reading because there is no reading to tabulate it against.

**The blind spot is real elsewhere, and this is recorded so "moot" is not read as "resolved".**
Across 09:36–09:50 the detector produced **11 raw 1-minute trigger events**, three of them
carrying 2 distinct cluster types — all at minutes Angus could not have checked. None survived
the filter stack, and none is at the gate instant. But a parity gate placed one minute earlier
would have been **incomplete**, not moot.

---

# 7. WHAT THIS GATE ESTABLISHES, AND WHAT IT DOES NOT

## Established

1. **The price feed is not in question.** 12/12 OHLC exact, BB basis to 0.005 on three
   timeframes, session / pre-market / prior-day extremes to ≤0.50. The reference chart and the
   bar archive are the same market.
2. **The bar convention is correct.** Open-labelled source, +1 shift to a close label, TF
   aggregation boundaries — all confirmed by the exact candle match on 2m, 3m and 5m at three
   different labels.
3. **"Prior day" means Globex in the implementation**, matching the reference, where an RTH-only
   reading would have been wrong by 147.50 points on the low.
4. **The detector's level set diverges materially from the reference chart's** — NY VWAP bands by
   up to 19.10, POC by 44.50, 4h range by a factor of 11 — and the divergence is fully explained
   by definitions the spec does not state.
5. **No implementation bug at this instant.** Three prior literalism checks failed; this one does
   not. The failure is in the specification, not the code.

## Not established

1. **Nothing about the trigger logic.** Both sides say no trigger, but the detector's only
   candidate died at the first gate. The rejection-block and displacement predicates, the RR
   floor, the stop anchor, the target ladder and the A7 selector were **not exercised at all**.
2. **Nothing about the four ambiguities.** All four are non-binding here for the same reason.
3. **Nothing about 1m.**
4. **No verdict on the sealed result.** This gate is about whether the detector implements the
   strategy the spec describes on the reference chart. It says the level layer does not, for
   reasons the spec must fix. It does not say the sealed run is invalid — the sealed run tests
   the spec **as implemented**, which is exactly what the scope ruling already names.

## The honest summary

**The detector and the reference agree on every number that comes from the market, and disagree
on most numbers that come from a definition.** That is a specification failure surfaced by a
parity gate working as intended. It is also why the gate is FAIL and not PASS: the strategy is
defined by its levels, and the levels do not match.

---

# 8. PROVENANCE

| | |
|---|---|
| Instant | 2025-01-22, bar covering 09:49:00–09:49:59 closed; detector label `cm = 590` |
| Session | Globex 2025-01-21 18:00 ET → 2025-01-22 16:59 ET, 1380 bars, contract **NQH5** |
| Prior session | 2025-01-21, 1380 bars |
| Detector | `stage2_smoke.signal_candidates` — **the sealed engine's own pre-outcome path**, unmodified |
| Dump harness | `research/star-trading/tools/parity_p2_dump.py` — re-executes the engine's state evolution with dump hooks, then calls the real `signal_candidates()` and confirms the two agree on the candidate set |
| Raw dump | `research/vwap-bb/data/parity_p2_detector.json` |
| Sealed result | **NOT opened.** `read_results()` never called; no outcome field touched |
| Holdout | **SEALED.** Every date read is ≤ 2025-01-31; `assert_workbench()` enforced on every session in the list |
| Detector changes | **NONE.** No file under `tools/` was edited except the new read-only dump script |
| N_trials | **0** |
