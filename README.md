# NQ Mechanical Trading System

A mechanical NQ futures trading system: a deterministic Python engine detects
fully-defined setups, Claude agents grade each candidate against the written
rulebook, and a deterministic risk layer gates everything before it reaches a
human or a market.

**The one mental model: Python sees, Claude judges, Python acts.**

Read `context/project-overview.md` first. The strategy constitution is
`strategy-definition-v1.0.md` — when code and that document conflict, the
document wins.

## Repo map

| Path | What it is |
|---|---|
| `strategy-definition-v1.0.md` | The constitution. Everything traces here. |
| `spec-*.md` | Build specs, executed one step at a time via Claude Code |
| `context/` | Project overview, architecture, code standards, workflow rules, progress tracker |
| `config/strategy.yaml` | Every configurable number, each commented with its § source |
| `config/news_calendar.csv` | Scheduled-release calendar (seed rows are UNVERIFIED estimates) |
| `src/engine/` | Market Engine: data, sessions, indicators, snapshot, triggers |
| `src/backtest/` | Backtester core, calibration, diagnostics |
| `tests/` | Unit tests + hand-computed fixtures (`tests/fixtures/`) |
| `data/raw/` | Databento downloads (gitignored) |
| `data/reference/feb2026_hand_log.csv` | Angus's 28 hand-backtested trades — ground truth (committed) |
| `output/` | Reports: parity, calibration, diagnostics (gitignored) |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then fill in keys — never commit .env
```

Python 3.11+. Approved dependencies only (see `context/code-standards.md`):
pandas, numpy, pydantic v2, PyYAML, pytest, ruff.

## Commands

Reports are reproducible from single commands (populated as spec steps land):

```bash
ruff check . && pytest            # must be green before every commit
# python -m src.engine.data       # step 2: ingest data/raw -> data/nq_1m.parquet + gap report
# python -m src.backtest.calibrate  # step 8: output/calibration_report.md
```

## Non-negotiables

1. No LLM in the risk/execution path. Ever.
2. No parameter tuning to make backtests look better — divergences are
   reported, not fixed.
3. When code and `strategy-definition-v1.0.md` conflict, the document wins;
   ambiguity means stop and ask Angus.
4. No lookahead: signals compute on closed candles only.
