# DECLARATIONS — gold ORB programme (gold-orb-models skill)

Written before the Phase 3 measurement sweeps and not edited afterwards except to append
results under D7.

## D0 — Data, and what it is not

`data/gc_1m.parquet`, committed to this branch at `748df23`. GC front month, 1-minute
OHLCV, **2023-01-02 → 2026-08-11**, 1,276,717 bars over 936 CME session days.

| requirement (skill rule 5 / task Phase 0) | status |
|---|---|
| continuous, volume-based roll before First Notice | **met** — 19 rolls, all at 00:00 or 18:00 ET, 2–4 days before contract month |
| back-adjusted | **NOT met — raw stitched front month** |
| 2021 → present | **NOT met — starts 2023-01-02** |

**Back-adjustment.** Every roll gap is positive and scales with price (+16 pts at $1,930,
+60 pts at $4,080), which is gold's carry — the stitch is behaving correctly. It is not
back-adjusted, and for this programme that is immaterial and arguably preferable: ORB is
intraday, every roll falls at 00:00 or 18:00 ET so no trade spans one, and a back-adjustment
offset is constant within a contract era so it cannot change an intraday point distance.
Raw front-month prices are the prices that actually traded. **Stated, not assumed away.**

**2021–2022 is absent and cannot be obtained.** The Databento SDK is installed (0.83.0) but
there is no API key in this environment and the user has declined to buy one. The programme
therefore runs on 3.6 years, not 5. Every "5-year" figure the task asks for is reported as
the span actually measured.

## D1 — The seal

**Holdout: 2025-09-01 → 2026-08-11.** 235 session days.
**Train: 2023-01-02 → 2025-08-31.** 701 session days.

No Phase 3 sweep touches the holdout. One unlock, one run, at Phase 4, only for a config
that clears D4 on train.

## D2 — Declared holdout exposure at Phase 2, and why it was taken anyway

The calibration window the task specifies — **2026-03-02 → 2026-08-17 — lies entirely
inside the seal.** This is a direct conflict between Phase 0 and Phase 2 of the task, and
it is resolved here in writing rather than silently.

Calibration was run on it. The justification, and its limits:

1. **Calibration selects no parameters.** It runs one fixed v1-exact configuration and
   compares it to a fixed external artifact. Nothing about the sweep grid, the gates or the
   candidate config is chosen using what it returns.
2. **The window was already disclosed.** `references/tv-findings.md` publishes that window's
   headline P&L, win rate, profit factor, exit mix, MFE ladder, two named trades and the
   full weekday breakdown. The seal over that window was already broken by the briefing
   document before this session started.
3. **What I now know that I did not before:** v1-exact on 2026-03→08 runs 48.2% WR, PF 1.09,
   +$10,480 over 112 trades, with Monday at 33% and Tue/Fri above 60%. Items 1–2 mean almost
   all of this was already in evidence; the honest statement is that the *weekday effect is
   now confirmed to me on holdout data*, so **skipMon can never be presented as an
   out-of-sample discovery in this programme.** It ships, if it ships, as an A/B that was
   already public.

The remaining 2025-09-01 → 2026-03-01 stretch is untouched and stays sealed.

## D3 — The calibration gate could not be evaluated as written

The task requires a trade-for-trade diff against a 116-trade export: "count, entry
timestamps, directions, exit reasons, per-trade points."

**The export was not supplied.** Only the aggregates in `references/tv-findings.md` are
available. Timestamps, directions and per-trade points do not exist in this environment, so
the literal ≥90%-matched gate is not computable. What was run instead is every aggregate the
briefing publishes, plus the two named landmark trades and the weekday fingerprint.

Result recorded in `docs/FINDINGS-gold-orb.md`. Judgement taken: the engine is calibrated
enough to measure with, and the residual is located in the data feed rather than the logic.
**If the CSV export is supplied later, the literal diff should be run before any config is
promoted to demo.**

## D4 — Promotion gate, fixed now

From SKILL.md, unchanged: **OOS expectancy ≥ +0.10R/trade, PF ≥ 1.3, n ≥ 200, stable across
neighbouring cells, survives 2-tick slippage.** Kill if OOS EV ≤ 0, PF < 1.1, or the edge
dies going 1→2 ticks.

Costs: 1 tick/side baseline and 2 tick/side stress, both reported on every cell, per skill
rule 4. Commission is set to $0 and is therefore *not* modelled — stated because the skill
requires commission and this is a shortfall, not an omission I am hiding. Every reported
edge must be read as needing roughly a further $2–4/round turn to be real.

## D5 — Sweep discipline

One variable at a time off the v1-exact baseline. No cell is quoted as a result unless it
carries ≥30 trades per free parameter. Anchor, target, cap mode, time stop and the three
gates are swept independently; nothing is stacked in Phase 3.

Anything that dies at 2 ticks is reported as microstructure noise, per skill rule 4.
Anything concentrated in a single year is reported as regime-dependent and not promoted.

## D6 — Predictions, stated before the sweeps run

1. The plain 15m ORB on gold is **negative or flat before costs** on train. Priors:
   QuantifiedStrategies found naive ORB unprofitable on GC explicitly; M2's author netted
   −0.5% on his own 8-day gold sample; M3-BPC was refuted by its own author on S&P.
2. **08:20 ET beats 09:30 ET.** Deepest US metals liquidity, and 09:30 has no gold-native
   meaning. This is the skill's stated highest-prior variable.
3. **The 1.5R target is too far.** TV's MFE ladder shows only a minority of trades reaching
   it; 1.0–1.25R should score better on average R.
4. **The risk cap helps in dollars and not in R** — it truncates the left tail without
   changing trade selection, which is a dollar effect. If it improves R materially I should
   suspect the R denominator, not celebrate.
5. **skipMon will look good and is not evidence** — see D2.

## D7 — RESULTS

Appended after the runs. See `docs/FINDINGS-gold-orb.md`.
