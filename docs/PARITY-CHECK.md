# Parity Check — how Pat runs it (can be done NOW, no hardware)

The parity check proves Pat's agents reproduce the validated canon **exactly**. It needs no
VPS, no live feed, no funded account — it runs entirely against data already in this repo. Run
it the moment the agents can make decisions over historical candidates.

## What it actually tests

Given the same inputs, does the agents' produced **book** match the frozen ground truth
trade-for-trade — same trades taken, same conviction, same stop, same micros, same P&L to the
cent? If yes, the agents ARE the validated +$56k edge. If no, the harness says exactly which
trade and field diverged.

(This is *decision + sizing* parity. A separate later gate — the reconciliation day — checks
that the live ingestor computes the same *features* from the raw feed. Different gate, needs
the live feed. This one is pure logic and runs now.)

## Everything needed is already in the repo

| Role | File |
|---|---|
| **Candidate universe + features** (the agents' input) | `output/trade_matrix.parquet` (NY pre+gold), `output/london_matrix.parquet` (London) |
| Clean-tape input for London `opp5` | `output/fp_minutes.parquet` |
| **Ground truth** (what to match) | `output/baseline_book.parquet` — 400 trades, +$56,065 |
| **The checker** | `scripts/parity_harness.py` |

Every trade candidate row in the matrix files carries the raw feature values the canon scores
on (`d15`, `dep_wall_*`, `cvd_ASIA`, `room_R`, `risk`, `dollars`, etc.). The agents consume
those rows and apply their logic.

## Step 1 — Agents produce a replay book

Point the agents at the candidate universe (the matrix files) and have them run the full
mechanical path on each candidate: session route → canon checks → score → OF stack / Q tier →
**dollar-risk size** (base $200, +$75/$1k available DD past $3k floor, 40-micro clamp) →
take-or-skip. Write every **taken** trade (size > 0) to `agent_replay.parquet`.

**Required columns** (must match the baseline's schema and labels so the trade keys align):

| column | meaning |
|---|---|
| `session` | `"NY"` for pre+gold trades, `"LONDON"` for London (match the baseline's labels) |
| `day` | `"YYYY-MM-DD"` |
| `fill` | fill timestamp (UTC) — used to the minute for the trade key |
| `direction` | `"long"` / `"short"` |
| `conviction` | the size multiplier: 0.25 / 0.5 / 0.75 / 1.0 / 1.5 / 2.25 |
| `risk_pts` | stop distance in points |
| `micros` | contracts = `min(40, round(min(400, conviction*200) / (risk_pts*2)))` at floor |
| `pl` | `micros * dollars_1lot / 10` (dollars_1lot = R_multiple × risk_pts × 20) |

The floor schedule (no DD-scaling) is the parity target — deterministic per trade, so it's
reproducible to the dollar. (DD-scaling is a live overlay, not part of this frozen baseline.)

## Step 2 — Run the harness, staged (fail-fast)

Don't burn a full replay to find a week-2 bug. Widen only after each window is an exact PASS:

```bash
python -m scripts.parity_harness agent_replay.parquet 2025-06-01 2025-06-07    # 1 week
python -m scripts.parity_harness agent_replay.parquet 2025-06-01 2025-06-30    # 1 month
python -m scripts.parity_harness agent_replay.parquet                          # full 2 years
```

## Step 3 — Read the result

- **✓ PASS** — "byte-for-byte reproduction of the canon." That window's trades match exactly.
  Widen the window. Full-run PASS = 400 trades, +$56,065 → the agents are cleared.
- **✗ FAIL** — itemized list:
  - `MISSING` — a canon trade the agents didn't take (missed a setup / over-filtered).
  - `EXTRA` — a trade the agents took that the canon didn't (under-filtered / bad gate).
  - `MISMATCH` — same trade, wrong field (e.g. `micros: canon=12 agent=15` → sizing bug; `pl:` → P&L drift).

  Fix at the **smallest failing window**, re-run. Repeat until the week passes, then the month,
  then the full two years.

## The bar

The full run must be an exact **PASS** before any hardware is bought or any live order is
placed. This is what turns "one funded account passed" from a lucky data point into a proof
that all five accounts run the validated book. Validate first, buy second.
