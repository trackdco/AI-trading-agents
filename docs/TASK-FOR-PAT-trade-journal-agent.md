# TASK FOR PAT — Trade-journaling agent (Angus directive, 18 Jul 2026, pass 24)

**Angus:** "We're going to need an agent specifically for trade journaling, where it logs all
of the executed trades with all of the relevant criteria to a point where I could give you
the data and I could look at where we can improve the trades."

**Phase note (Angus, same pass):** agents are SCAFFOLD-ONLY right now — like the regime-context
and HTF-structure agents, this gets designed/scaffolded but NOT integrated until the mechanical
strategy is down. Nothing agent-produced feeds the current backtest loop.

## What it is

A journaling layer that records EVERY executed trade (backtest first, live later) with the full
decision context, in a format both Angus and the engine lane can query. The backtester already
emits most of this (`TradeRecord` + the diag22 extensions); the agent's job is to make it a
first-class, always-on journal rather than a per-run diagnostic dump.

## Per-trade record (the "relevant criteria" — extend, don't trim)

- **Identity:** date, trigger ts, entry TF, direction, entry variant, mgmt variant, config hash
- **Setup:** trigger kind (rejection/displacement), pattern (A/B/B2), HTF flag, confluence
  count + cluster types (bb/vwap/poc/ote), cluster center, vwap_touched, day type
  (balanced/imbalanced once the AMT layer lands), session (pre-market/NY), news context
- **Execution:** limit/fill price + ts, slippage ticks, stop initial, target name/level,
  working target, RR at entry, size
- **Path:** MFE/MAE in R (already computed in diag22), time-to-MFE, partial fills, trail moves,
  BE arms
- **Outcome:** exit ts/price/reason, points, R multiple, dollars net
- **Review fields (for Angus):** free-text verdict slot ("valid setup I'd take" / "wouldn't
  take" / "missed context"), and a would-Angus-take-it flag the capture-matcher can prefill
  when a hand-log window matches

## Deliverables (scaffold)

1. Journal schema (the list above) as a pydantic model + parquet/csv writer — extend
   `TradeRecord` rather than duplicating it.
2. A `journal build` entrypoint that replays any backtest run and emits the journal file.
3. A summary view generator: per-month / per-setup-class / per-day-type aggregates, worst-10 /
   best-10 tables — the "give me the data and I look at where we can improve" artifact.
4. (Later, live phase) an execution-feed adapter so live fills journal identically to backtest
   fills — one schema, both worlds.

Acceptance: Angus can open one file per run and see every trade with every criterion above;
the engine lane can diff two journals to attribute a performance change to specific trades.

— Claude Code (engine lane), on Angus's direction.
