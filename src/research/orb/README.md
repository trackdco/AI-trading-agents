# ORB harness — the entry is retired, the harness is not

The opening-range-breakout **signal** on GC is retired (see
`.claude/skills/gold-orb-models/references/null-result.md`). Everything else in this module
is calibrated, tested and signal-agnostic, and is meant to be reused.

**What survived:** a trade-for-trade parity match against a live TradingView v3.1 export —
100.0% day match (73/73), 100% direction, 98.6% exit reason, median entry-price difference
0.00 pt, median per-trade P&L difference $10 — and 35 constructed-bar self-tests
(`tests/test_orb_engine.py`) that must pass before any run touches data.

## Dropping in a new signal

`run()` takes a `signal_fn`. The default is `orb_candidates`, the retired generator, kept
as the reference implementation.

```python
from src.research.orb.engine import Candidate, Config, daily_context, load_gc, run

def my_signal(day, cfg, row, feat, anchor, or_end) -> list[Candidate]:
    ...
    return [Candidate(signal_tmin=..., fill_tmin=..., direction=..., stop_ref=...,
                      meta={"whatever": ...})]

bars = load_gc()
trades = run(bars, Config(...), daily_context(bars, 14), signal_fn=my_signal)
```

### What the harness gives you

`day` is one calendar day of 1-minute bars, already carrying `tmin` (minute of day), `dow`,
`sess` (CME session, rolls 18:00 ET) and `vwap` (session VWAP anchored to that roll).
`row` is the prior-day-shifted daily context for that date — `pdc`, `atr`, and the Crabel
flags `nr4` / `nr7` / `inside` / `idnr4`. `feat` is a `{tmin: (relvol, rng_atr)}` lookup,
populated only when a participation filter is configured. `anchor` and `or_end` are minutes
of day derived from `cfg`.

### What your signal must return

| field | meaning |
|---|---|
| `signal_tmin` | minute-of-day of the bar whose **close** produced the signal |
| `fill_tmin` | minute-of-day of the bar whose **open** fills it |
| `direction` | `+1` long, `-1` short |
| `stop_ref` | price the protective stop sits at, **before** any cap |
| `meta` | free-form dict, copied onto the trade row |

Two rules the harness relies on and will not enforce for you:

- **`fill_tmin` must be strictly after `signal_tmin`.** No same-bar fills. If your signal
  is confirmed on a bar's close, the earliest honest fill is the next bar's open.
- **Your generator must not read past `signal_tmin`.** The harness has no way to detect
  lookahead inside a candidate. `test_truncating_the_future_cannot_change_a_closed_trade`
  is the pattern to copy: truncate the series after the signal and assert the candidate is
  unchanged.

Return candidates in chronological order. The harness stops taking them once
`max_trades_per_day` is reached or a breaker trips.

## What runs unchanged, whatever the signal

Everything below is applied by `run()` and needs no work from a new generator.

- **Fills and costs** — `slip_ticks` per side charged adversely on entry and exit,
  `commission_usd` per round turn. GC point value $100, tick 0.10.
- **Hard risk cap** — `risk_mode` `cap` (pull the stop to the cap) or `skip` (stand aside).
  Express it as **`max_risk_atr`**, not `max_risk_pts`: a point cap is a different parameter
  in every era. On GC a 30-pt cap fires on 0.6% of 2023–25 trades and 29.5% of 2026 days,
  while 0.5 × prior-day ATR fires 8.8% and 7.1%. `max_risk_pct` does **not** transfer either.
  Whichever caps are set, the tightest binds.
- **Profit ratchet** — once `ratchet_trigger_r` is touched on the exit-walk extremes, the
  stop locks to `ratchet_lock_r`. Arms for *subsequent* bars only, because 1-minute OHLC
  does not order its own extremes.
- **Time stop** — scratch at `time_stop_min` if the trade is below `time_stop_r`.
- **Forced flat** — `flat_minutes`, measured from entry, or from the anchor with
  `flat_from_anchor=True` (the Pine v3.1 convention).
- **Directional bias gates** — `vwap_gate`, `pdc_gate`. These *continue* to the next
  candidate on failure rather than abandoning the day.
- **Breakers** — `daily_stop_r`, `weekly_stop_r`, `consec_loss_halt`. The consecutive
  counter resets **weekly**; a counter that resets only on a win latches permanently, which
  is the bug the Pine v2 shipped with.
- **Day filters** — `skip_weekdays`, `crabel`.
- **Exit resolution** — `exit_tf` (1 = minute-accurate, 15 = emulate a 15-minute chart) and
  `optimistic` (whether a both-touched bar resolves as the target). On this strategy the
  two were identical, because an opposite-side stop and a 1.5R target are 2.5 opening ranges
  apart and no bar ever spanned both. A tighter-stopped signal will not have that luxury —
  check it rather than assuming it.

## Reporting

`summarise()` returns win %, EV in R, total R, points, dollars, profit factor, median risk,
max drawdown and the exit mix. **Report R first and points alongside** — the house rule
exists because slippage on an R-multiple target *adds* points while *costing* R, which
`test_slippage_costs_R_even_when_it_flatters_points` pins.

Judge any wider-stopped variant against the **cost-denominator control** before believing
it: fixed costs enter as `cost/risk`, so a wider stop lifts EV arithmetically. Compare
pre-cost EV.

## Files

| | |
|---|---|
| `engine.py` | `Config`, `Candidate`, `orb_candidates`, `run`, `summarise`, `daily_context`, `entry_frame` |
| `../../../tests/test_orb_engine.py` | 35 self-tests — run these first, always |
| `../../../scripts/orb_parity_v31.py` | the TradingView parity diff |
| `../../../scripts/orb_sweep2.py` | the retired sweeps, kept as a worked example of the reporting discipline |
| `../../../docs/FINDINGS-gold-orb.md` | full results and the correction log |
| `../../../docs/DECLARATIONS-gold-orb.md` | pre-registered declarations D0–D10 |
