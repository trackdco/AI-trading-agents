# HANDOFF — the certified trigger engine, for ai-trading-v2

The "cluster/trigger detection, not yet built" on the v2 side exists here,
certified. Minimal lift list, entry points, and the discipline that comes
with it. Updated 2026-08-20.

## The modules (self-contained set)

| file | what it is |
|---|---|
| `scripts/offline_briefings.py` | the as-of feature engine: bars loader, session bounds (18:00 NY anchor), levels (VWAP bands, BB MAs, fibs, developing + prior-day + Monday-anchored weekly profiles), candles on any grid |
| `scripts/offline_scan.py` | the candidate scanner: two-timeframe MA-break + close-through-second-level pairs, same-candle and sequential shapes, pending queues with age expiry. `scan_day(bars, sess_day)` → list of candidate dicts |
| `scripts/chop_state.py` | regime state v2: window-local trailing range (60m London / 20m NY) vs quartile thresholds FROZEN on 2026-01..04 |
| `scripts/level_visits.py` | per-level session visit/test counts |
| `scripts/gate_offline_causality.py` | the no-lookahead gate: corrupt every bar at/after t with garbage, recompute every field, demand bit-identical. Run it after ANY change |
| `scripts/certify_offline_briefings.py` | regenerate-and-diff against served briefings (this repo's use; optional for v2) |
| `scripts/export_candidate_corpus.py` | the dataset: one row per candidate, all days, features + crude mechanical outcome |
| `scripts/enrich_corpus_freshness.py` | adds `zone_touches_session` (freshness proxy) |

## Certification status, honestly stated

- Scanner: reproduces 100% of the live-adjudicated candidate minutes on
  the certified era (queue-not-slot pending, close-through-only second
  legs). Semantics quirk logged: a lone 15m-MA closure counts as a valid
  second leg (inflates candidates; cannot manufacture a take).
- Causality: ALL PASS on the adversarial gate, including the July week.
- Calibration constants (chop thresholds) frozen pre-test-period; if you
  re-fit them, re-fit walk-forward — recent regime only (2023 prices
  deflate point thresholds by ~half).

## The corpus

`output/analysis/candidate_corpus.jsonl.gz` — 18,965 candidates / 919
session-days (2023-11 → 2026-07-14). `reserved: true` rows (255) are
tapes consumed by agent runs — hold them out. The `mech_*` outcome model
is a crude finder (decision-close entry, structural-proxy stop, 2R-or-stop
at 120m) — re-derive outcomes your own way; entry/stop anchor any
re-model. Corpus-scale pre-tests already run (see `docs/GAP-LEDGER.md`
"standing corrections" and `docs/PREREG-jl1-observables.md`): CHOP-state
outperformance is real at scale; sequential-leg-type and London-ordering
effects are NOT (small-n artifacts, documented).

## The acceptance bars (his ruling 2026-08-20)

Two gates, in series, never blurred:

1. **The mechanical bar (v2's):** sweep target-distance bands on the
   full-day multi-year set — his prior: the definitive winner sits in
   **1.5–2.5R**. The system must hold **≥50% win rate to target inside
   the chosen band**, walk-forward and holdout. His words: *"until we are
   holding 50%+ win rate in that bound its a fucking failure."* For
   scale: the unselected corpus baseline reaches 2R ~26% of the time —
   the selection layer's job is roughly to double the raw hit rate.
2. **The live bar (his):** *"what matters more is when an agent is live
   on a chart, is that it is thinking like me"* — judged by him reading
   its trades. Passing one gate without the other ships nothing.

## What v2 sends back

1. `grading.py` input schema → the corpus re-export becomes one command.
2. Card format for the labeling drive so his labels serve both repos.
3. Verdicts on the graded conditions, whichever way they fall — this
   repo's doctrine register records kills as loudly as confirms.
