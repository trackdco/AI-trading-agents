# Architecture

## System layers and data flow

```
Historical data (Databento 1m NQ)          Live data (later phase)
              \                                   /
               v                                 v
        ┌─────────────────────────────────────────┐
        │  MARKET ENGINE (Python, deterministic)  │
        │  data.py → sessions.py → indicators.py  │
        │  → snapshot.py → triggers.py            │
        └───────────────┬─────────────────────────┘
                        │ snapshot JSON + candidate trigger
                        v
        ┌─────────────────────────────────────────┐
        │  THE DESK (Claude agents, Phase 3)      │
        │  Hermes ─ polls → Atlas, Helios,         │
        │  Apollo, Hephaestus. Unanimity or no.    │
        └───────────────┬─────────────────────────┘
                        │ verdict JSON (proposal only)
                        v
        ┌─────────────────────────────────────────┐
        │  THE VAULT (Python, deterministic)       │
        │  limits, halts, EOD flatten, kill-switch │
        └──────┬───────────────────────┬──────────┘
               v                       v
        Telegram alert /         Strict-schema
        paper order              trade log
```

In **backtest mode**, the Desk is bypassed: triggers.py IS the mechanical rule set, and the backtester (src/backtest/engine.py) plays both Desk and Vault against historical bars. Backtest/live parity comes from both modes consuming the identical Market Engine.

## Layer contracts

- **Engine → Desk:** one pydantic-validated `Snapshot` JSON per closed candle when a trigger fires. Contains indicator values per TF, cluster composition, pattern classification, session context, HTF flag, distances to all target-menu levels. Contains NO account state, NO P&L, NO prior-trade info — agents are structurally incapable of revenge-trading because they cannot see losses.
- **Desk → Vault:** one `Verdict` JSON: `{trade, pattern, direction, entry, stop, target, size, grade, thesis, gates: {name: pass/fail}}`.
- **Vault → world:** Telegram message / paper order + append-only log row. Every verdict is logged whether taken, skipped, or vetoed, with the reason.

## Key invariants (enforce in code and tests)

1. NY-session VWAP anchors 09:30 ET and returns NaN before it; pre-09:30 clusters use daily VWAP (18:00 ET anchor) only.
2. All timestamps are tz-aware America/New_York. DST is handled by the tz library, never by offset arithmetic.
3. Signals compute on closed candles; orders activate next bar. A no-lookahead test must exist and pass.
4. One open position maximum, ever.
5. Every configurable number lives in `config/strategy.yaml` with a comment tracing it to a § of strategy-definition-v1.0.md.
6. The Vault has no import path from any module that calls an LLM.

## Environments

- **Build/backtest:** local machine (macOS), Python 3.11+, git.
- **Live loop (Phase 4+):** small always-on VPS. Not provisioned yet — do not build for it prematurely.

## External services

- Databento — historical (later live) NQ data. Key in `.env`, never committed.
- Anthropic (Claude Code) — build tooling now; Desk runtime in Phase 3.
- Telegram Bot API — Phase 4 alerting. Token in `.env`.
