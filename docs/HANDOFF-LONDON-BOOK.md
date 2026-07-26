# HANDOFF — NQ "London 10:00–13:00 UK" Pullback Book + Funded Plan

## Context
Building a mechanical **NQ (Nasdaq-100 futures)** trading strategy. This thread built and
stress-tested a **London-session pullback book** and a **funded-account plan** around it.
Bottom line: **the book is DONE at the trade level — lock it, stop tuning the geometry.**
Repo `trackdco/ai-trading-agents`, branch `claude/brake-43x58e`. (Angus's separate "London
canon" lives on branch `getting-started-6lwnvs` — do NOT merge this into it.)

Discipline rules that apply throughout: no lookahead, net of costs, "no naked numbers"
(every figure with N / base-rate / caveat), 2025-frozen thresholds, both-years + 4-quarter
checks, DST-week awareness.

## THE STRATEGY (baseline "Scheme A") — full reproducible spec
- Instrument NQ, **M15 bars**, window **10:00–13:00 UK (Europe/London)**, Jul 2025 – Jul 2026.
- **Setup** (long; mirror for short): MAs stacked 20>50>200, price above all three; the bar
  **wicks the 50-MA** (low ≤ 50MA) and **closes back above**, on **fading volume**
  (bar vol < mean of prior 10 bars).
- **Entry**: next M15 bar open + 1 tick slip.
- **Stop**: structural = min(swing-low-5, 50MA) − 1 tick, clamped **5–70 pt**. LEFT WIDE — load-bearing.
- **Target**: **3R**, fixed at entry, uncapped — the tail IS the edge.
- **Exits**: flat 16:30 UK if unresolved; **DAY-STOP** = stop trading that day after the first loss.
- **Sizing**: CVD-confirm → **1.0×** ($300 base risk); unconfirmed → **0.5×** ($150).
  "Confirm" = 3-min CVD delta at entry agrees with trade direction.
- **Costs**: 2 ticks slip + $5 RT commission, netted. **DST-excluded days**: 2025-11-28, 2026-04-03.

## RESULTS (funded fixed-$ lens, $300 base risk)
- **Net +$17,763 / 12.5 mo · max DD $917 · worst R-streak 3.06R · WR 56% (31W/24L) · 55 trades**
- Every quarter green: 25Q3 +$3,084 / 25Q4 +$3,381 / 26Q1 +$3,268 / 26Q2+ +$8,029
- avg win +2.98R / avg loss −1.02R · 29 of 55 CVD-confirmed
- Sizing alternatives: **flat 1.0×** (all full) = +$20,384 / DD $1,226 (more $, more risk);
  **confirm-only** = +$14,839 / DD $917 / **67% WR** (cleaner, fewer trades = 30)
- Fixed-contract lens (1 NQ, V1 1.5× on confirm), for reference: **+$75,668**

## FUNDED ACCOUNT PLAN
- $50k account, $2k trailing max DD modeled as **LOCK-at-$50k** (danger zone = only the first
  ~$2k of profit; after lock, drawdowns are profit give-back and can't blow you).
- **userB scaling ladder** (risk scales with locked buffer = balance − $50k):
  - < $750 (eval/pre-lock): $250 confirm / $125 unconfirm
  - $750–$2,000: $350 / $175
  - $2,000–$4,000: $500 / $250
  - ≥ $4,000: $700 / $350
  - Backtested on this ladder: **+$36,978 / 12.5 mo · P(blow) 0.16% · 5th-pctile +$22,151**
- Size off the stop with **MNQ micros ($2/pt)**, $250 rung: 15pt→8 MNQ, 25pt→5, 36pt(median)→3,
  50pt→2, 70pt→2. Unconfirmed = half the contracts.

## TESTED AND FAILED — do NOT redo (all lose vs baseline)
1. **Tighter (rejection-wick) stop** → +$10,147 (−$7.6k). Winners take median 0.42R heat before
   paying; tightening sheds them.
2. **Move to breakeven** → −$1.2k to −$11.4k. Scratches breathing winners.
3. **Armed reduced-risk trail** (arm +XR, move stop to +LR), full (X,L) sweep → −$1k to −$13k.
   Winners & losers both round-trip; post-+1R retrace overlaps (winners bottom −0.77R, losers −1.57R).
4. **Entry filters** (confirm-only / trim unconfirmed / drop wide-unconfirmed) → all lose or match.
   Day-stop already governs risk (DD invariant at $917 / 3.06R across every scheme), so trimming
   only sheds profit. Unconfirmed trades are net-accretive at 0.5×.
5. **ROOM-conditional target** (magnet at overnight extreme when room<CAP) → −$4.3k. Lowers DD
   ($917→$762) & raises WR (→64%) BUT the overnight extreme is a **weak wall** — capped 13–25
   winners, converted only 3–5 losers.
6. **Structural conclusion**: the edge is the **uncapped 3R tail**; every intervention caps a tail
   (stop / target / wall) → all lose. The book is **robust, not fragile. Leave the geometry alone.**

## KEY DIAGNOSTICS (reference)
- **Winner heat (MAE)**: median **0.42R** against before hitting 3R; 2/33 winners went to 0.90–0.98R
  (near the stop) then paid. All winners exit at target, all losers at stop.
- **Loser MFE**: ~65% go straight to stop showing no profit; ~27% tease +1R on a close then
  round-trip to −1R.
- **Confirmed-book losers (12)**: 10/12 had **ROOM<2.5** (3R target sits beyond the overnight H/L
  wall). ROOM is Angus's canon check; it separates WR (82% in-band vs 43% out) but fails as a
  filter (dropped trades made more profit than kept).

## THE TWO REAL LEVERS (both OUTSIDE trade geometry)
- **More profit** → the userB scaling ladder (already built).
- **Fewer losses** → **real depth/heatmap data for 10:00–13:00 UK** (only 08:00–09:59 UK exists
  today). The overnight-extreme proxy failed precisely because a static level can't tell a wall
  that holds from one that breaks — live resting-depth could. This is the one untapped lever,
  **blocked on data**.

## DATA SOURCES (in repo / worktree)
- Bars: `data/reference/nq_1m_master.parquet` (UTC `ts_event` → tz_convert Europe/London).
- CVD footprint (Databento aggressor tape, side B = buy):
  `data/reference/cvd/footprint_{q3_2025,q4_2025,feb_mar2026,apr2026,may_jul2026}.parquet`.
  **Jan-2026 missing** (1 file) → those trades size at unconfirmed half-rung.
- London MBP-10 depth: `data/reference/depth_london/` — **only 08:00–09:59 UK** (not the 10–13 window).
- Angus's London canon (separate, don't merge): `scripts/london_canon.py`,
  `scripts/run_triggers_london.py`, `docs/CANON-MECHANICAL.md` on `getting-started-6lwnvs`.
  His entries = A/B/B2 rejection-wick at confluence zones, **08:00–10:00 UK only**, W/FAR/ROOM/ASIA checks.

## OPEN THREADS / NEXT STEPS
- Write the **one-page funded trade plan** (rules + ladder + size table) — offered, not yet done.
- Re-run the funded Monte Carlo under a **NO-LOCK trailing** model (stricter; some prop firms) — offered, not done.
- (Untested) **scale-out** variant: bank half at +1R, let half run — genuinely different from breakeven, not yet tested.
- (Blocked) port real 10–13 UK depth → heatmap wall / FAR / magnet-target filters.
- An **HTML dashboard** was built (equity curve, quarters, sizing, robustness, ladder, 55-trade log).

## NOTE FOR THE NEW SESSION
This session's analysis scripts live in a **local scratchpad** (session-specific) and did NOT get
committed — they will NOT transfer to the other account. Rebuild from the spec above, or (if the
other account clones the same branch) ask me here to commit them to `claude/brake-43x58e` first.

## CAVEATS (state every time)
55 trades / 12.5 months / one favourable regime / **NO 2023–24 London holdout** → out-of-sample
unproven. The 3.06R DD and 0.16% blow-prob are in-sample / Monte-Carlo. Thresholds frozen on 2025,
book sliced many ways → treat any refinement as a **holdout candidate, not a ship**. Start bottom
rung; the buffer is the protection.
