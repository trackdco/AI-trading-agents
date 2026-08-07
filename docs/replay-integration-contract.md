# Replay Integration Contract — the combined-gate hook for `simulate()`

**For the engine lane.** The walk-forward replay's one remaining engineering
dependency: `simulate()` must consume the per-day combined de-risk gate the desk
lane produces (`src/desk/combined_gate.py` → `output/combined_gate_schedule.csv`).
This is baseline **B/C** of the three-arm replay; arm **A** (static champion)
runs `simulate()` unchanged.

## The hook (backward-compatible)

Add ONE optional parameter to `simulate()`:

```python
def simulate(df_1m, triggers, cfg, target_resolver=None, entry_price_fn=None,
             calendar=None, day_gate=None):   # <-- new, default None = today's behavior
```

`day_gate: Callable[[str], CombinedGate | None]` — given a session date
(`YYYY-MM-DD`, the CME 18:00-boundary date the engine already uses), returns that
day's gate, or `None` (no agent verdict → trade the day exactly as arm A would).
`CombinedGate` fields: `allow_reversion`, `allow_continuation`, `size_multiplier`
(0.0/0.5/1.0), `stand_down`, `directional_bias`.

`None` default means arm A is byte-identical to today. Only arms B/C pass a gate.

## Application rules (in the trigger-admission loop)

For each trigger, resolve its session date, fetch `g = day_gate(date)`; if `g` is
None, admit as today. Otherwise:

1. **`g.stand_down`** → skip every trigger that day (journal it `skipped_regime_standdown`).
2. Classify the trigger as a **fade** or a **continuation** (see mapping below);
   skip if its class isn't permitted (`skipped_regime_no_reversion` /
   `skipped_regime_no_continuation`).
3. Otherwise admit, but **scale size by `g.size_multiplier`** (0.5 → half unit;
   composes with the §9 conviction size already computed — multiply, don't replace).

The gate NEVER widens risk, adds trades, or overrides a Vault limit — it only
removes trades and shrinks size (a pure de-risk, matching the existing day/time
condition de-risks).

## Trigger → structure classification (PROPOSED — needs Angus)

The gate speaks in `reversion`/`continuation`; a `Trigger` carries `pattern`
(A/B/B2) and `htf_flag` (with_trend/counter_trend/range). Proposed mapping:

| trigger | class | rationale |
|---|---|---|
| pattern **A** (reversal) | fade / reversion | fades an over-extension |
| pattern **B2** (continuation) | continuation | rides the move |
| `htf_flag == counter_trend` | fade / reversion | against the 15m trend |
| `htf_flag == with_trend` | continuation | with the 15m trend |
| pattern **B** (reclaim) | **NEEDS ANGUS** | a reclaim is arguably continuation of the reclaim leg — rule it |

When pattern and htf_flag disagree, **pattern wins** (proposed). This one ruling
(plus the pattern-B case) is the only trading-semantics decision the hook needs;
everything else is mechanical.

## Who supplies what

- **Engine lane:** the `day_gate` param + the admission-loop application above +
  the three skip reasons in the journal (so the replay attributes each removed
  trade to the gate).
- **Desk lane (done):** `combined_gate.combine()` + `build_gate_schedule.py`
  producing `output/combined_gate_schedule.csv`. The replay driver will wrap it
  as `day_gate = lambda d: schedule.get(d)`.
- **Angus:** the pattern-B classification + the pattern-vs-htf tiebreak.

## Test the engine lane should add

`test_simulate_day_gate`: a stand-down day removes all its trades; a
reversion-only day removes continuation triggers and keeps fades; a 0.5 day
halves size; `day_gate=None` reproduces the arm-A baseline byte-for-byte.
