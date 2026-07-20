# Sample Trade Candidates (Hermes test fixtures)

Two hand-built candidate JSON files for testing the desk skills / agent stack end-to-end.
Every field maps to a specific agent check; both candidates carry the full field set.

| File | Verdict | Basis |
|---|---|---|
| `pass-candidate.json` | **TAKE (full unit)** | Feb 11 2026 short, Pattern A, +5.98R (real hand-log trade). Every field satisfies its check. |
| `fail-candidate.json` | **VETO — confluence** | Feb 3 2026 counter-trend long, Pattern A, real −1.0R. The `bb+poc, no vwap` edge case. |

## The fail case is deliberately a *single* real failure

Everything in `fail-candidate.json` passes — swept low, clean bullish order block, R:R ≈ 3.3,
in the AM kill zone, no news — **except** the confluence cluster. The trigger stacks only the
Bollinger basis (BB) + daily POC = 2 distinct types. The VWAP family (a CORE component per
strategy §2) sits 24+ pts away, outside the ~10-pt tolerance, so it doesn't count. A
counter-trend long needs ≥3 confluences (§7); 2 < 3 → skip. It's the exact cohort §7 exists to
filter, and the real Feb 3 instance lost −1.0R.

## Construction notes (read before trusting the numbers)

- **Price anchor:** our OHLCV data (`glbx-mdp3-*`) ends **2026-01-31**; the Feb hand-log period is
  not in it. Prices are anchored to *real* end-January NQH6 levels (Jan 30 traded ~25,640–25,920),
  not invented as exact Feb prints.
- **Confluence has no native schema field**, so the level stack lives in
  `trigger_zone.coincident_levels` + `distinct_confluence_types`. Relocate if Hermes reads it elsewhere.
- **Fail-case entry time** normalized 10:52 → 09:52 ET (into the core kill zone) so timing fully
  passes and confluence is the *sole* disqualifier.
- Fields prefixed `_` (`_meta`, `_rr_note`, etc.) are provenance/annotation, not part of the schema.

Ground truth: `data/reference/feb2026_hand_log.csv` and `strategy-definition-v1.0.md`.
