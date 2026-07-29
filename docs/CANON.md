# THE CANON — single source of truth (ANGUS ruling, 2026-07-29)

**If you are a chat/session orienting yourself in this repo: this file is the law.**

The pre-2026-07-28 "canon" (CANON-MECHANICAL, CHAMPION-v1.1, the old dashboards, the
substrate/cap architecture, and every study built on it) was **structurally broken** — its
substrate shared a 2-trade cap across sessions and starved the golden window on 56% of
day-books. It has been deleted from this repo. Do not reconstruct it from git history and
treat it as truth; do not trust any number produced before the rebuild.

## The new canon

| What | Where |
|---|---|
| **THE configuration** (entries, gates, scores, tiers, elite, risk spine, both sizing profiles, reference results) | `scripts/funded_book.py` — the docstring is the spec |
| Rebuild methodology (L0–L4 layers, gates, era discipline, burn list) | `docs/HANDOFF-london-rebuild.md` |
| Pipeline | `scripts/build_l0_triggers.py` → `build_l1_fills.py` → `build_l2_outcomes.py` (+ `l2_mfe_walk.py`) → `build_l3_features.py` → `l3_check_trial.py` → `l3_score_apply.py` → `l4_select.py` (+ `tests/test_l4_select.py`) → `raw_validated_book.py` → `funded_book.py` |
| Canon dataset (validated trades, scores, L1 events, valid flag) | `output/aikido_{fit,holdout}.parquet` (committed) |
| Scored candidate population | `output/l3_scored_{fit,holdout}.parquet` (committed) |
| Sealed-holdout law | `docs/HOLDOUT-2023-24-PREREGISTRATION.md` |

Headline (reproduce with `python -m scripts.funded_book`): **lucid** profile fit +$89,925 /
holdout +$56,408; **scaled600** fit +$320,150 / holdout +$188,324; every month green in
both spans under both profiles.

## What survived from before (kept deliberately, NOT canon claims)

- `src/` — the deployed live stack (currently **disarmed** via structural _NoBroker). It
  still runs the OLD architecture and is pending the re-arm rewrite to the new canon
  (scorer W/D gates + wall-quality cut + score tiers + elite + budget spine). Until that
  lands, nothing in `src/canon/scorer.py` or its counters is canon.
- `scripts/canon_run.py`, `output/canon_book.parquet`, `output/london_canon_book.parquet`
  — operational entry point and runtime inputs of that deployed (disarmed) stack. They
  exist so the VPS doesn't break, not because their contents are trusted.
- `scripts/canon_mechanical.py`, `build_ny_substrate.py`, `holdout_verdict.py`,
  `baseline_dollar_risk.py`, `dayflow_features.py`, `gold_quality.py`, `trade_matrix.py`,
  etc. — legacy import dependencies of `score_canon_span.py` (the L3 feature builder) and
  of `src/`. Library code, not strategy truth.
- London old-book artifacts (`scripts/london_*.py`, `output/london_canon_book.parquet`,
  `output/fp_minutes.parquet`) — BRAKE's reference material for the London rebuild, per
  the handoff. The old London book is a *reference to beat*, not a book to trade.
- `docs/RULING-*.md`, `docs/LIVE-STACK.md`, `docs/SAFETY-SPINE.md`, desk/agent docs —
  standing rulings and infrastructure for the (separate) desk system.

## Standing rulings folded into the canon

rr_floor 2.0 hard · gold window 09:40–10:30 · no distance cancel (orders die at session
window end) · rejects must touch the level · red-folder news blackout · uncapped entries ·
elite 2.0x max 1/day · budget counts realized + in-flight + new risk · sizing designed
from observed data, never imposed.
