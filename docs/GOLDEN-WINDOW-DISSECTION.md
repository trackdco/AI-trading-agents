# THE GOLDEN WINDOW, SECTION BY SECTION (2026-07-26)

Angus: *"we need to dissect section by section in the golden window."* Consolidates every
golden-window measurement from today into one reference. Population: champion engine,
otherwise-canon, 2025-07 → 2026-07 (385 trades) + the canon's own 53-trade gold book.
Reproduce: `window_flow_split.py`, `golden_deep_oos.py`, + inline bucket analysis.

## 1. The funnel (why golden "underperforms" pre — it doesn't)
Canon candidates: pre 495 / gold 218 over 224 days — gold fires DENSER per hour (1.67 vs
1.47) but the window is 35 min vs 90. Take-rate 24% vs 40% (gold has the Q-gate; pre has no
equivalent). Canon results: gold **$517/trade, 60% win** vs pre $123/trade, 44% win. Golden
is the best window per opportunity; it is short and strictly filtered, both by design.

## 2. The two regimes (both-years survival, $/t gap on↔off)
| check | 09:40–10:00 | 10:00–10:15 | (10:15–10:30) |
|---|---|---|---|
| walls W/D/WALLSZ | **+$532/+$557/+$436** | n.s. | +$288/+$249/+$214 |
| d15_conf (flow-with 15m) | **+$318** | **+$380** | n.s. |
| d30_conf (flow-with 30m) | **+$263** | **−$223 (inverts)** | −$80 |
| fill-bar delta with | **−$327** (retest fingerprint) | **+$294** | n.s. |
09:40–10:00 rides the drive (flow-with + walls); 10:00–10:15 is the transition (30-min flow
stale); past 10:15 everything inverts and the raw pool is −51.8R. `d30_conf` traces the open
drive's ~20-minute half-life: **+$263 → −$223 → −$80.**

## 3. Blind OOS (the adoption-grade test)
| derive → test blind | result |
|---|---|
| 2025 → **2026**: d15_conf ∧ wall-ahead | **43t, +21.4R, 44% win, 6/6 months green** |
| 2026 → 2025: REJ-off ∧ d15 ∧ d30 | +13.0R, 4/6 | 
`d15_conf` is the core of both derivations. **CONFIRMED.** (Same test KILLED the 10:15–10:30
fade subset: −4.1R / −16.1R blind — retracted.)

## 4. Micro-structure: 5-minute buckets (raw / refined = d15∧wall / per-year R)
| bucket | n | raw R | refined R (win) | 2025 / 2026 | verdict |
|---|---|---|---|---|---|
| 09:40–45 | 148 | −2.4 | **+43.9 (54%)** | +5.8/−8.1 | half the window's volume; FLAT raw, BEST refined |
| 09:45–50 | 84 | +43.1 | +20.2 (55%) | +0.6/**+42.5** | hot but 2026-skewed — not claimable |
| 09:50–55 | 44 | +6.6 | +8.9 | +11.0/−4.5 | mixed |
| **09:55–10:00** | 30 | **−23.0 (10% win)** | **−7.6 (0% win)** | **−12.9/−10.1** | **DEAD ZONE — toxic both years, even refined** |
| 10:00–05 | 22 | +3.2 | +5.1 | +1.0/+2.1 | quiet, positive |
| **10:05–10** | 25 | **+22.7 (40%)** | +10.6 | **+12.1/+10.6** | robust both years |
| **10:10–15** | 32 | −6.1 | −6.6 | **−3.2/−2.9** | bleeds both years, even refined |
The decay into the dead 10:15+ regime begins at ~10:10, not 10:15 — the original window cut
was roughly right, if anything 5 minutes generous. The canon's own book already concentrates
early (45 of its 53 gold trades fill before 10:00, 60% win).
Exit mix 09:40–10:00: 208 stops / 75 targets / 13 eod — 68% stop-outs in the raw pool.

## 5. Kind & book (per-year checked)
**Displacement carries golden:** +13.3R (2025) / +34.2R (2026), both years. Engine
rejection_blocks net ~0 both years (his live retests ≠ this population — they score 0–2 on
the engine checklist). Calm-vs-war-day split does NOT survive per-year (parked).

## 6. Package items from this dissection (all frozen constants, canon-convention revalidation)
1. **Early-golden refinement**: d15_conf ∧ wall-ahead (blind-OOS confirmed)
2. **09:55–10:00 entry skip** — **RULED & ADOPTED (Angus, 2026-07-26)**: canon's own zone
   trades were 0-for-3 (−$372), confirming the champion evidence. In `build_canon`
   `dead_zones=[(595,600)]`; arming reference now +$55,989.81/383
3. 10:10–10:15 review (bleeds both years; the regime turn starts here)
4. 10-min dead-trade cut (from the frontier study) — exit rule, unaffected by rr retraction

## 7. Consequences for the agents
Any adopted change reshapes the book → **A1/A2 parity re-runs against the current arming
reference (+$55,617.56 / 386, `baseline_book_news.parquet`)**. The historical 400/400 pass
was against the superseded +$56,065 book. rr retraction adds nothing (floor unchanged).
Layer-2d 3-min cut: the −7.9R "cut hurts" number lived on the RETRACTED 1.5 book and is
void; the shipped rule stands. At the 2.0 floor the alive-at-3 evidence is ~breakeven with
years split, while every 10-min cell is positive both years — an upgrade study, not an
invalidation.
