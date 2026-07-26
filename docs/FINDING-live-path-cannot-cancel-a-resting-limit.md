# FINDING — the live order path can PLACE a limit but cannot CANCEL one

**Raised:** 2026-07-26, from Angus describing the model's cancel rule.
**Severity:** money-relevant fidelity gap. Not a blocker to *building*, but must be closed
before the bot is armed.

## What Angus described (the intended rule)

> "missed limit orders are because we have a thing where if it runs x points in our direction
> before filling us we cancel, because statistically it demotes setup quality"

This rule is real and parameterised in the repo:

- `config/strategy.yaml:111` — `cancel_if_runs_points: 22.0`
  *"§5.5 CALIBRATE — T_cancel: cancel unfilled order if price runs this"*
- Implemented in the **research engine**: `src/backtest/engine.py:731-737`
  ```python
  ran = (h >= order.limit + cfg.t_cancel) if sign == 1 else (lo <= order.limit - cfg.t_cancel)
  ... veto: "price ran {cfg.t_cancel} pts beyond limit unfilled"
  ```
- Load path: `src/backtest/engine.py:152` — `t_cancel=c["entry"]["cancel_if_runs_points"]`
- Covered by tests: `tests/test_backtest.py:108 test_t_cancel_wins_and_blocks_fill`

## The gap

**The live path has no equivalent, and no ability to build one as written.**

- `src/desk/dtc_client.py` order surface is **`submit_bracket()` only**. There is **no
  cancel-single-order method** anywhere in the client (full method list checked).
- `submit_bracket` sends no `TimeInForce` field — so the resting entry limit takes the
  server default (DAY on Sierra/DTC). It rests until filled or session end.
- The only cancel that exists is `spine.cancel_all(account)` — the kill switch (`spine.py:97,135`).
  That is flatten-everything, not "pull this one stale working order".
- Nothing in `src/live/runner.py` tracks a working order or expires it.

**Consequence:** price moves 22+ points away from our limit without filling. The model says
cancel — the setup has degraded. The live bot instead leaves the order resting, and it can
fill later on a deep pullback. That is an **EXTRA trade the book never took**, at exactly the
degraded setup quality the rule exists to avoid. It is a fidelity violation in the direction
that costs money, and it would not show up as a "missed" trade — it shows up as an "extra".

## What has NOT been verified (be honest)

Whether the canon's frozen +$56k substrate actually applied this rule. The canon's fills come
pre-computed from `output/trade_angles.parquet` / `substrate_v2_signals.parquet`, upstream of
`scripts/canon_mechanical.py`, and that chain was not traced. Two cases:

- **The substrate DID apply cancel-if-runs** → live must implement it to match. Gap confirmed.
- **The substrate did NOT** → then the frozen book itself lacks the rule Angus believes it has,
  which is a different and equally important thing to know before arming.

Either way this must be resolved, not assumed.

## Required work (for Pat)

1. **Trace the substrate**: did `trade_angles`/`substrate_v2_signals` apply a
   cancel-if-runs-22pts rule when producing `fill`? Answer determines the target behaviour.
2. **Add `cancel_order(client_order_id)` to `src/desk/dtc_client.py`** (DTC
   `CANCEL_ORDER` message) — the client currently cannot cancel a single order at all.
3. **Add a working-order lifecycle** to the live path: track the resting entry limit, and on
   each closed bar test `price ran >= cancel_if_runs_points beyond the limit, unfilled` →
   cancel. Mirror `src/backtest/engine.py:731-737` exactly so live == book.
4. **Force-test it** alongside the spine tests: place a limit, run price away, assert cancelled.

## Why it matters more than it looks

Angus's point stands that **frequency is fine** — 400 trades in 12.5 months, ~4/week, is a
selective book and a few missed fills are not a threat. The threat is the opposite: an
un-cancelled stale limit **adds** trades the edge was never measured on.

---

## RESOLUTION of step 1 — traced and measured (2026-07-26)

**Answer: the substrate DID apply cancel-if-runs. Case 1. The gap is confirmed and the live
path must implement it.** This was traced, then proved by running the engine both ways rather
than by reading the chain alone.

### The provenance chain, end to end

`scripts/_regen_build_substrate_v2.py` → **`simulate(seg, trigs, cfg)`** → `substrate_v2.parquet`
→ `scripts/orderflow_by_setup.py` → `substrate_v2_signals.parquet` → `scripts/universal_orderflow.py`
→ `scripts/trade_angles.py` → `trade_angles.parquet` → `scripts/trade_matrix.py` →
`scripts/canon_mechanical.py` → `canon_book.parquet`.

Every canon fill therefore originates in `simulate()`. The substrate's config is
`load_backtest_config().model_copy(update={win_start, win_end, max_trades_per_day})` — it does
**not** override `t_cancel`, so it carries the shipped `cancel_if_runs_points: 22.0`, and
`simulate()` enforces it at `src/backtest/engine.py:731-737`. (One caveat worth keeping in
view: E4/EC-displacement entries are MARKET entries, which the engine explicitly exempts —
"no resting limit, no T_cancel". The rule binds the limit-entry books only.)

### The measurement (why "it's in the config" wasn't enough)

Re-ran March 2026, E3 book, identical inputs, changing only `t_cancel`:

| | trades | P&L |
|---|---|---|
| shipped (`t_cancel = 22`) | 33 | +$1,943 |
| rule disabled | 35 | +$6,697 |

**18 fills exist only with the rule disabled; 16 exist only with it enabled** — fills *shift*,
they do not merely accumulate, because a cancelled order frees the day's trade slots for
different later setups. Trade-set divergence of that size in a single month on a single book
settles it: a live bot that cannot cancel does **not** reproduce the arming reference.

Note the P&L moved *up* without the rule in this sample. That is not an argument for dropping
it — it is one month of one book, and the canon's own selection layer sits above this. The
requirement is fidelity to the validated book, whichever way the sign happens to fall on a
sample. Deciding the rule is unprofitable would be a strategy change requiring its own
re-validation and Angus's sign-off, not a live-build shortcut.

### What this does NOT resolve

Steps 2–4 stand and remain **on-box work**: `dtc_client.py` still has no `cancel_order()` (its
order surface is `submit_bracket()` only), nothing tracks a working order's lifecycle, and the
force-test cannot run without a live Sierra DTC server. Gate **B7** stays RED.

**Related, and worse in the same area:** the exit driver (`src/canon/exit_driver.py`) now
faithfully reproduces engine.py's managed exits and emits `modify_stop` / `partial_close` /
`close` actions — but the `Broker` protocol (`spine.py`) exposes only `submit_bracket`,
`order_status`, `position`, `flatten`, `cancel_all`. **There is no way to modify a stop or
partially close a position through the live order path.** The canon has no fixed target; the
exit IS managed. So the same missing-order-surface defect that blocks B7 also blocks the
managed exit from ever running live. Both need the DTC client extended and verified on the box.
