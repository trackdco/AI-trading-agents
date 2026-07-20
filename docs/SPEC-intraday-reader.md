# SPEC — The Intraday Reader (Angus, 20 Jul 2026)

## Why it exists (the measured case)

The chop detector quantified it: **2025's entire loss is trading both-books-lose days**
(on tradeable days, 2025 champion +$26,320 ≈ 2026's +$27,838). Perfect both-lose
avoidance turns 2025 from −$15,962 to **+$26,320**. But only **~38% of those chop days
are flagged pre-open** — the other **62% look identical to good days in the morning**.
Their character only reveals itself *after* the open. That 62% is the intraday prize,
and it's why Angus has said since the start: "so many days I just adapted off of what
market open gave me."

## Role — narrow by design

The intraday reader is a **stand-down-only second verdict**, not an entry system.

- The pre-open v0.7 dial still does its job: picks the book + morning stance.
- The reader runs **once, post-open**, sees the opening tape, and can do exactly one
  thing: **veto the rest of the day to FLAT** when the opening prints chop character.
- It never changes book choice (pre-open's job) and never *adds* trades. It only
  removes bad days. This keeps it aligned with the 2026-first constraint: the only way
  it can hurt the live year is by standing down on a good 2026 day, which is the single
  thing the validation must bound.

## Timing (a parameter to tune, not a guess)

The champion enters 08:00–10:15 ET. The reader watches an **opening read-window** and
emits its verdict at a **decision time**, gating entries *after* that point:

- Candidate read-windows: 08:00–08:30, 08:00–08:45, 08:00–09:00.
- Trade-off is explicit and measurable: a shorter window decides earlier (protects more
  of the day's entries) but has less tape to read; a longer window reads better but only
  gates the tail. The validation sweeps this and picks by net dollars, not by taste.

## Opening-character features (all computable from the 1m master, full history, free)

Computed live from the read-window bars — the mechanical signature of a chop day:

- `or_range` — read-window high−low vs trailing-20d median (expansion vs contraction).
- `or_persistence` — |close − open| / (high − low) over the window (drive vs oscillation).
- `or_trap` — did an initial extreme reverse >X% back through the open (the trap tell).
- `or_location` — did price hold one side of the opening range, or whipsaw through it.
- `or_volume` — read-window volume vs trailing-20d median (conviction vs thin chop).
- Plus the pre-open context it already has: `regime_health`, `inventory_pts`, day_type.

## Method — measure before believe (identical discipline to the inventory gate)

1. **Mechanical validation FIRST (free, no agent):** build the opening-character features
   from 1m bars for all history. Test whether they separate the **both-lose days pre-open
   features MISSED** (the 62%) from good days. Grade on **net dollars per year**, not
   detection rate. Gate = walk-forward conditional expectancy of champion P&L given the
   opening-character bucket (prior days only), exactly as the inventory gate works.
2. **Anti-overfit:** frozen 2023-24 → 2025-26 split; the rule must protect 2025 OOS and
   **must not tax 2026** (worst-case check: 2026 P&L under the reader ≥ 2026 without it,
   within a small tolerance).
3. **Only if the mechanical signal clears** → wire it into the agent as a genuine second
   call: the v0.7 agent re-runs post-open seeing the opening-character features + its own
   morning verdict, and may revise stance to risk_off. Chained memory can carry "today
   opened choppy / the morning drive failed" as a same-day note.

## What success looks like

A reader that recovers a meaningful slice of the ~$22k/yr of 2025 both-lose bleed that
pre-open can't touch, **while leaving 2026 intact** (the live year is untouchable). If
even the best opening-character signal can't separate the 62% — that too is decisive: it
means the chop only resolves *late* in the session, and the lever moves to management
(tighter stops / faster flatten) rather than a stand-down read. Either outcome is worth
the free validation.

## Next action

Build the opening-character feature set from the 1m master and run the mechanical
validation (free) — measure how much of the pre-open-invisible 62% the opening tape
actually catches, and confirm 2026 is untouched, before any agent wiring or spend.
