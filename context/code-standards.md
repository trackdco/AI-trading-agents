# Code Standards

## Workflow (these outrank style)

1. **One spec step at a time.** Implement the step, run its check, verify it passes, THEN move on. Never batch steps.
2. **One commit per completed step minimum**, message format: `step-N: <what>`. The git history is the audit trail.
3. **Ambiguity = stop.** If a spec step or the strategy doc can be read two ways, ask Angus. Guessing trading semantics is the most expensive mistake available in this repo.
4. **No silent scope.** New files, new dependencies, or new components not named in the active spec require flagging before writing them.
5. **Reported, not fixed.** Backtest/calibration divergences are documented in output reports. Changing parameters or rules to improve results is prohibited without an approved hypothesis, out-of-sample evidence, Angus sign-off, and a strategy-doc version bump.

## Python

- Python 3.11+. Dependencies: pandas, numpy, pydantic v2, PyYAML, pytest, ruff. Anything else → flag first.
- `ruff check .` clean and `pytest` green before every commit. Type hints on all public functions.
- pydantic models for every cross-boundary object (Snapshot, Verdict, config, trade-log rows). Validation errors must raise, not warn.
- All datetimes tz-aware (`America/New_York` via zoneinfo). Naive datetimes are a bug by definition.
- Pure functions for indicator math; side effects (file IO, logging) live at the edges.
- No magic numbers: every threshold reads from `config/strategy.yaml`.
- Money/price arithmetic in floats is acceptable for NQ points at this scale, but round prices to the 0.25 tick at every order boundary.

## Testing

- Every engine module ships with unit tests against small hand-computed fixtures (bundle 1–2 day data fixtures in `tests/fixtures/`).
- Mandatory named tests: `test_no_lookahead`, `test_ny_vwap_absent_premarket`, `test_dst_boundary`, `test_single_position_invariant`, `test_fill_requires_trade_through`.
- Golden-file tests for Snapshot output; update goldens only with an explanatory commit message.

## Data & secrets

- `data/raw/` and `output/` are gitignored. `data/reference/` (the 28-trade hand log) IS committed — it's ground truth.
- API keys and tokens live in `.env` (gitignored). A `.env.example` documents required vars. Never print secrets to logs.

## Logging & outputs

- Structured logging (module, timestamp, level). The trade log and diagnostics are append-only CSVs with strict pydantic-validated schemas — the freeform-column chaos of the Notion log is exactly what this replaces.
- Reports are files in `output/` (markdown/CSV), reproducible from a single command documented in README.
