# Regime Adaptation — the mechanism (pass 30, Angus directive)

**Problem statement (Angus):** external context — news, geopolitics, "Trump doesn't shut the
fuck up" — drives which playbook works. Regime resolution is the biggest P&L lever left
(evidence: 6-month journal; every failed arm was regime-local; the blend's entire edge is one
crude binary switch). We need a mechanism to TEST regime context and adaptation, not just
believe in it.

## Architecture: three layers, each testable alone

### L1 — Regime STATE (mechanical, engine lane, BUILT)
One row per day, everything computed strictly pre-open (zero lookahead):
`output/regime_vector.csv` — day_type, imbal_share_20/10, trap_rate_10, range_pctl_20,
gap_open_pts, streak_imbal, red_folder_today. (`scripts/build_regime_vector.py`.)
This is (a) the champion's existing switch, (b) the agent's structured input, (c) the
analog-lookup key. Honest note: the bar-proxy trap_rate did NOT peak in May as hypothesized
(May trap lives at trade level, not day level) — kept as a feature, claim dropped.

### L2 — Regime MEMORY (historical-analog module, engine lane, NEXT)
Angus spec via his Malaysia contact's bot: k-nearest-days lookup — "which past days looked
like today's vector?" → what worked on them (branch, pattern class, empirical win rate,
R distribution) → playbook weights + confidence + sizing input. Purely mechanical, fully
backtestable, no LLM required. Depth scales with data: buy multi-year 1m NQ (cheap,
Angus-approved) once the lookup proves itself on Feb–Jul.

### L3 — Regime JUDGMENT (the agent, Pat's build)
Daily pre-open briefing → strict-JSON verdict, journaled by Hermes:
- INPUTS: L1 vector · L2 analog days + outcomes · news headlines as-of 08:00 ET
  (historical archive in backtest, live feed in production) · the agent's OWN running
  playbook notes (its adaptation memory — it may rewrite them daily; every edit journaled).
- OUTPUT: regime call {balance | war | trap | event-risk} · playbook selection (branch
  weights, pattern set, stand-down) · confidence · cited reasons.
- No human gate DURING simulation (Angus ruling, pass 29). Live deployment stays gated.

## The test mechanism (how we know if it works)

Walk-forward replay, Feb 2 → Jul 15, day by day; agents see only that morning's information;
fill engine = `simulate()`; per-session budgets. **Three-way control — this is the part that
makes it science instead of vibes:**
  A. static champion (mechanical L1 switch only) — the bar to beat
  B. agent WITHOUT news (L1 + L2 + judgment) — isolates what judgment adds
  C. agent WITH news (full stack) — isolates what news adds on top
Scoring: P&L / green months / maxDD as always, PLUS regime-call accuracy vs realized day
character, PLUS the adaptation ledger (every playbook-note edit and its subsequent P&L delta —
"did the machine learn the right lesson?").
Contamination guard: Feb–Jul 2026 post-dates model knowledge cutoffs; models pinned; blobs
journaled per the Hermes determinism spec.

## Data acquisitions needed (Brake)
1. **Historical news archive with timestamps, Feb–Jul 2026** (GDELT is free; any headline
   archive works). As-of discipline: only items published before 08:00 ET reach that day's
   briefing. Without this, only arms A and B can run.
2. Multi-year 1m NQ history (analog-library depth) — after L2 proves itself on 6 months.
3. (Already in flight) April depth sessions + trades footprint.

## Prerequisites before the finalized agent-run script (engine lane)
1. Angus ruling on **Blend v1.1** (the three journal cuts) — agents adapt on top of the best
   mechanical baseline, and it must be frozen before the replay starts.
2. **Journal schema freeze** (+ regime-vector fields) — the replay's memory is the journal;
   mid-replay schema churn poisons the experiment.
3. Champion config frozen into strategy.yaml + a reproducibility stamp (config hash in
   every journal row — already in the Hermes design).
4. L2 analog lookup built + benchmarked against the static switch (if analogs alone beat
   the binary index, that lift is mechanical and shouldn't be credited to agents later).

— engine lane, on Angus's direction. Pat: L3 is yours; the ai-workflow-rules desk contract
(strict JSON, fail-closed, journaled blobs) applies to the regime agent exactly as to the
graders.
