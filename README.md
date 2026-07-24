# AI Trading Agents — NQ Mechanical Trading System

A mechanical NQ futures trading system built in phases: a deterministic Python
**Market Engine** detects fully-defined setups, Claude agents (later phase) grade each
candidate against the written rulebook, and a deterministic risk layer (**the Vault**)
gates everything before it reaches a human or a market.

**The one mental model: Python sees, Claude judges, Python acts.**

## The constitution

[`strategy-definition-v1.2.md`](strategy-definition-v1.2.md) is the single source of
truth for every trading rule. When code and that document conflict, the document wins.
When the document is ambiguous, stop and ask Angus — never guess trading semantics.

## Repo map

| Path | What it is |
|---|---|
| `strategy-definition-v1.2.md` | The rulebook. Everything traces here. |
| `spec-1-market-engine-backtester.md` | Active build spec (Phase 1), executed one step at a time. |
| `context/` | Project overview, architecture, code standards, workflow rules, progress tracker. |
| `config/strategy.yaml` | Every configurable parameter, each commented with its § source in the strategy doc. |
| `config/news_calendar.csv` | Scheduled economic releases (input file, `#` lines are comments). Feb 2026 seeded; rest is a marked TODO. |
| `src/engine/` | Market Engine: data → sessions → indicators → snapshot → triggers. |
| `src/backtest/` | Event-driven backtester + calibration report. |
| `tests/` | pytest suites with hand-computed fixtures. |
| `data/reference/feb2026_hand_log.csv` | Angus's 28 hand-backtested trades — calibration ground truth (committed). |
| `data/raw/` | Databento 1-minute NQ data (gitignored — put downloads here). |
| `output/` | Generated reports: trades, diagnostics, equity, parity/calibration reports (gitignored). |

## Status

Phase 1, Spec 1. See `context/progress-tracker.md` for the live state, gates ledger,
and where the last session stopped. Step-by-step progress is also the git history:
one commit per completed spec step (`step-N: ...`).

## Setup

Python 3.11+ (validated on 3.12). Approved dependencies: pandas, numpy, pydantic v2,
PyYAML, pytest, ruff, plus **pyarrow** (parquet I/O). Exact versions are pinned in
`requirements.txt`.

Reproducible runtime — a repo-local venv (`.venv/` is gitignored):

```bash
python3.12 -m venv .venv            # any interpreter >= 3.11
source .venv/bin/activate           # (deactivate with `deactivate`)
pip install -r requirements.txt     # exact pinned versions — no shims needed on 3.11+
```

Databento API key and Telegram credentials live in `.env` (gitignored, never committed);
see `.env.example`. Historical NQ 1-minute data goes in `data/raw/`.

## Running checks

```bash
source .venv/bin/activate
pytest         # full suite — 352 tests, must be green before every commit
ruff check .   # style gate
```

## Paper trading (Phase 4 — the live/paper runner)

`scripts/paper_run.py` assembles and runs the frozen champion as a paper bot
(`src/live/runner.py::LiveRunner`), driven entirely by `config/live.yaml`. It is
restart-safe, honors the kill switch (`output/live/KILL`), computes the E3/E4 book from
live bars (`LiveVectorPolicy` — no precomputed CSV on the live path), and alerts via
Telegram on start / stop / trade / halt / daily summary (also written to
`output/live/paper_run.log`).

```bash
source .venv/bin/activate
python -m scripts.paper_run                       # config/live.yaml (replay feed today)
python -m scripts.paper_run --session 2026-03-17  # override the replay session
python -m scripts.paper_run --telegram off        # run silent (log only, no network)
```

Feed is pluggable via `feed.type` in `config/live.yaml`: `replay` (historical parquet —
the validated path today) or `live` (the real-time adapter seam, marked
`<<LIVE FEED ADAPTER>>` in `scripts/paper_run.py` — not yet built). Kill switch:
`touch output/live/KILL` halts new trades every session; delete the file (a deliberate
human act) to resume — `/kill` from an allowed Telegram user does the same.

## Data ingest (Step 2)

Convert a Databento `ohlcv-1m` CSV export into the validated parquet the engine reads:

```bash
python -m src.engine.data data/raw/nq_ohlcv_1m.csv
# -> data/nq_1m.parquet  (ts_event tz-aware NY, open, high, low, close, volume, roll)
# -> output/gap_report.csv  (unexpected missing minutes per CME daily session)
```

Timestamps are converted to `America/New_York` (DST-aware). Prices in Databento's
native 1e-9 fixed-precision integers are auto-decoded. Duplicate or out-of-order
timestamps raise. DBN input is a documented TODO — CSV is supported today.

A Databento **"parent"** export (all NQ outright contracts + calendar spreads, i.e. many
rows per minute) is accepted directly: it is collapsed to a single volume-based, unspliced
continuous front-month series, and the roll is tagged in the `roll` column. A single-series
export (e.g. `NQ.v.0` continuous) is used as-is. See Step 2 flags in the progress tracker.

## Non-negotiables

1. No LLM in the risk/execution path. Ever.
2. No parameter tuning to make backtests look better — divergences are **reported, not fixed**.
3. The strategy document outranks the code; ambiguity means stop and ask Angus.
4. No lookahead: signals compute on closed candles only; orders activate next bar.
