# TV Live-Test Findings (18 Aug 2026) — evidence from Angus's own 116-trade export

Source: TradingView strategy-tester trade list, v1 Pine port, GC1! back-adjusted, 15m chart,
09:30 ET anchor, 15m OR, 1.5R target, opposite-side stop, 240-min flat, one trade/day,
2026-03-02 → 2026-08-17, n=116. TV's emulator reads optimistic vs this repo's engine
(same-bar both-hit heuristic; no intrabar protection on the entry bar) — treat these as
directional evidence for design, not as measurements. The Python engine owns measurement.

## Headline
- +$15,202 total ≈ +0.07R/trade · WR 52.6% · PF 1.14 · median stop ≈ 21 pts ($2.1k/GC)
- P&L ≈ direction-agnostic (corr to gold ≈ 0.19) — behaving as a both-ways breakout, not beta

## Exit mix — the defining defect of the 1.5R design
- target 24/116 (21%) · stop 36 · FORCED-FLAT 56 (48%)
- Flat winners banked only ~49% of their MFE (avg MFE $2,531 vs banked $1,229)
- MFE ladder: ≥0.75R 56% · ≥1.0R 47% · ≥1.25R 35% · ≥1.5R 14%
  → 1.5R overshoots gold's window; default target moved to 1.0–1.25R, judged on avg R

## The dollar-risk pathology (why the hard risk cap exists)
- Trade #2 (3 Mar): short, ~101-pt OR, opposite-side stop ~96 pts away, price wicked to
  within ~a tick of the stop, flat exit −$9,623 — ≈ −1R on its own risk, 5× normal dollars
- Trade #81 (24 Jun): same species, ~54-pt OR, −$5,393
- NOT engine bugs (anomaly scan clean: no stop exit had MFE ≥ 1.5× its own risk, so no
  eaten target fills; 0 multi-trade days; all entries 10:00–11:45 ET)
- Fix shipped in v3: maxRiskPts = 30 (cap mode pulls stop to entry±30 pts; skip mode
  stands aside). Sweep cap-vs-skip {25, 30, 40}.

## The giveback seven (why the profit ratchet exists)
- 7 trades touched ≥ +1.0R MFE and finished red: −$21,231 actual vs +$14,073 at a resting
  1.0R limit ($35.3k swing). Path logic near-clean: MFE precedes exit by construction;
  only a same-bar both-touch muddies 1–2 of them. Trade #15 alone is a $10.8k swing.
- Fix shipped in v3: ratchet — once +1.0R touched (1m highs/lows), stop locks to +0.25R.
- Early break-even stays OFF: 24/61 winners went ≤ −0.5R before winning ($42.7k of the
  win pool) — consistent with the documented ~0.36R EV cost of early BE.

## Time behaviour (why the time-stop exists)
- Decisive trades resolve fast: targets median 3 bars (~45 min), stops median 4 bars;
  flats drag ~14.5 bars (~3.6 h). 25/55 losers were ≥ +0.5R green before dying (−$54.6k).
- v3 default: scratch at 90 min if < +0.5R. Sweep {60, 90, 120} × {0.3, 0.5}.

## Calendar effects (suggestive, small-n — test, don't believe)
- Monday: 25 trades, 32% WR, −$13,135. Friday: 70% WR, +$20,911. Tuesday: 65%, +$10,771.
- Not outlier-driven (#2 was a Tuesday, #81 a Wednesday). skipMon ships ON in v3 as an
  A/B, not a conviction. Max losing streak: 5 (weekly 3-consec breaker calibration).

## Standing mandates carried into the repo
1. CALIBRATE FIRST: reproduce this exact window with v1-exact settings and diff
   trade-for-trade against the export (≥90% match with explained residuals) before any
   measurement run. Expected divergence classes: TV same-bar both-hit optimism,
   next-open fill ±1 tick.
2. All v3 mechanisms (cap/skip, ratchet, time-stop, VWAP gate, PDC gate, weekday skip,
   daily −2R / weekly −4R / 3-consec breakers with WEEKLY consec reset) require
   deterministic constructed-bar self-tests before touching data. A v2 Pine consec-loss
   latch bug (reset only on a win → permanent halt) is the cautionary example.
3. Verdict thresholds unchanged (see SKILL.md): OOS ≥ +0.10R/trade, PF ≥ 1.3, n ≥ 200,
   neighbour-stable, survives 2-tick slippage. Holdout sealed from 2025-09-01 in the
   repo programme; one unlock, one run.
