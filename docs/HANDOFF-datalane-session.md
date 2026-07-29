# HANDOFF — data-lane session (Brake), 20 Jul 2026

Resume point for a fresh session. Read this top-to-bottom, then continue. Brake owns data;
Angus owns strategy; the engine lane measures. This session = data delivery + selection-signal
analysis on the champion. Reproduce everything with `python scripts/selection_signal_test.py`.

## THE HEADLINE LEAD (what we were doing when we cut off)

Testing which entry-known signals separate champion WINNERS from LOSERS. The strongest result:

| April 2026 config | Trades | Win rate | P&L | Avg R |
|---|---|--:|--:|--:|
| Baseline (all) | 30 | 33% | +$2,635 | +0.23R |
| CVD confirm only | 20 | 40% | +$2,855 | +0.40R |
| Magnet only (wall on target side) | 15 | 47% | +$2,975 | +0.50R |
| **Magnet + CVD confirm** | **10** | **60%** | **+$3,345** | **+1.01R** |

**Magnet + CVD confirm hit 60% win rate, made MORE than the baseline on 1/3 the trades, at +1.01R.**
This is the first 60% we've reached through *selection* (not degraded targets). **It is a LEAD, not
PROOF — n=10, April-only, in-sample, and depth has spoofing/replay risk.** Needs confirmation on
more months before anyone trades it.

## The two signals that work (entry-known, causal, tradeable)

1. **CVD confirmation** — net-buy over the 3-min pre-entry window agrees with trade direction.
   Full Feb–Jul: confirm 42% win / +$12,111; against 24% / +$1,746. Carries ~all the profit.
   (Independently found by the engine lane's `selection_study.py`, but LABELED "fade" there — the
   sign is inverted; see `docs/FINDING-cvd-confirm-vs-fade-signcheck.md`. It's confirmation.)
2. **Real stop (≥6pt)** — trades with sub-6pt wick-stops win 7% (pure junk / instant stop-outs).
   Requiring ≥6pt alone: 39% win, +$14,512 (MORE than baseline), +0.47R. Cleanest single filter.
3. **Heatmap LIQUIDITY MAGNET** — resting wall on the TARGET side (where price travels TO).
   April 47% vs 20%. NOTE: an earlier test of "support BEHIND entry" was the wrong framing and
   showed nothing — the magnet (wall AHEAD) is the one that separates. April-only, n=15/15.

## What FAILED (don't re-test these hoping)
- **Confluence count** — backwards (3-conf 24% vs 2-conf 35%).
- **VIX** — null (engine lane confirmed; too blunt/whole-day).
- **Book imbalance, support-behind-entry, total depth, RVOL≥1, outer-band-at-trade-level** — no separation.
- **Liquid-hours (>=09:30)** — cut the win rate barely but threw away most profit: this champion's
  edge is in the **08:xx pre-open** window (16 of 30 April trades; 08:xx = best hour). Opposite of
  generic NQ "trade 9:45–11:30" advice — our data wins.
- **Stacking all 5 filters** — over-filters to 7 trades and goes NEGATIVE. More filters ≠ better.

## Trade timing (April)
Entries span **08:02–10:08 ET**. By hour: 08:xx 16t/38% (magnet+CVD 4t/75%), 09:xx 12t/25%,
10:xx 2t/50%. The edge concentrates pre-open (08:xx).

## Broken / unfinished
- **Stop-buffer test** (`scripts/_stopbuffer_test.py`): tests placing the stop N pts BEYOND the
  wick (currently it's AT the wick tip = zero cushion → instant stop-outs). My harness did NOT
  reproduce the baseline champion (gave 194t/−$21k vs the real 146t/+$14k) because I dropped the
  min-stop floor and trimmed the price window. **Needs the engine lane to re-grade "+5pt beyond
  wick" through the REAL champion pipeline** (proper min-stop, full-day price for exits).
- **Delta-divergence at +1R** (for the give-back losers) — proposed, NOT yet tested. Angus's
  original give-back thesis. Untested lead.

## DATA ON GITHUB (all pushed, current)
- CVD footprint full Feb–Jul: `data/reference/cvd/` (feb_mar + apr + may_jul, int64, front-month).
- Heatmap depth April: `data/reference/depth_apr2026/` (48 files, verified correct — thin book is
  real NQ, not a bug; see task doc Update 14).
- VIX daily: `data/reference/vix_daily.csv`. News: `data/reference/news_archive.csv`.
- Findings: `docs/FINDING-cvd-confirm-vs-fade-signcheck.md`, this file, `scripts/selection_signal_test.py`.
- Interactive dashboards (claude.ai artifacts, NOT in repo): footprint chart, results dashboard,
  hold-time dashboard.

## TASKS FOR BRAKE (do these to resume + advance)

1. **[BUY] More heatmap months — Feb, Mar, May 2026 mbp-10.** This is now JUSTIFIED (was not
   before): the magnet+CVD=60% lead needs Feb/Mar/May depth to confirm at ~40–50 trades instead of
   April's 10. Same pull as before: Databento GLBX.MDP3 `mbp-10`, NQ, cost-check first, download,
   run `scripts/condense_depth.py *.csv.zst --outdir depth_out`, zip, upload. Commit into
   `data/reference/depth_<month>2026/`.
2. **[ANALYSIS, next session] Re-run magnet+CVD on Feb–May once depth lands.** Extend
   `selection_signal_test.py` to all depth months; report whether 60% holds. This is the make-or-break
   for the whole magnet lead.
3. **[ENGINE-LANE ASK] Re-grade the "+5pt beyond wick" stop test** through the real champion pipeline
   (my harness in `scripts/_stopbuffer_test.py` is broken — reproduces −$21k not +$14k). Flag to Angus.
4. **[ANALYSIS] Test delta-divergence at +1R** on the 44 give-back losers (price new high, CVD lower
   high = exhaustion → exit). Untested; attacks a real loss pool. Data is in hand (full CVD span).
5. **[LATER, optional] Market internals ($TICK / breadth)** — the one genuinely new confirmation axis
   that could push past ~45% WR (classic index-futures fade confirm). Not in hand; a new data pull.
   Only after the magnet lead resolves.

## THE HONEST FRAME (carry this forward)
- Optimize **expectancy**, not raw win rate. Baseline is +0.22R; CVD+stop is +0.65R; magnet+CVD (April)
  is +1.01R. That's the real improvement — 60% WR is the headline, expectancy is the substance.
- Everything is **2026 in-sample** (no footprint pre-2026). Leads, not proof. OOS is the missing piece.
- Never chase WR by shrinking targets (tail law — Angus proved it halves the money).
