# The Safety Spine

The hard, non-negotiable guardrails that protect the funded account **regardless of what
any canon, agent, or engine says.** The spine sits in Python at the execution boundary,
*below* and *outside* the strategy — nothing in the strategy path can override it.

## The one invariant

**When in doubt, the spine does nothing, or it flattens. It never opens risk and never
increases size on uncertainty.** This is the same lesson that held across all three
windows: unvalidated action is where money dies; the safe default is inaction. Every rule
below is a **HALT** or a **CLAMP** — there is no "maybe," no discretion, no LLM in this
layer. It is dumb, deterministic, and always wins ties against the strategy.

## Where it lives

- Pure Python, at order time, between the canon's `size` decision and the DTC order.
- It reads live **account state** (equity, drawdown line, open positions, order rate) and
  **feed health** — none of which the canon or agents ever see.
- It cannot be disabled by config in normal operation. Turning off a Tier-1 rule requires
  a deliberate code change, not a flag. (Angus ruling: account-survival rules are not
  tunable knobs.)

## Drawdown model: END-OF-DAY, not trailing (Angus, all accounts)

Lucid — and every account we buy — uses **end-of-day (EOD) drawdown**, not intraday
trailing. The distinction drives everything below:

- The max-loss **line updates only at end of day**, off the day's closing balance —
  `line = min(start_balance, max(prior_line, EOD_balance − DD))`. It trails EOD gains up by
  the DD amount and **locks at the starting balance** once you're clear. It does NOT ratchet
  against intraday highs, so you never fail by "giving back an intraday spike."
- **Available drawdown** = `equity − line`. It is fixed at the start of each day and grows
  as the day profits. This is the buffer the sizer scales off (below) AND the quantity the
  spine's Tier-1 halt watches.
- We treat the line as **intraday-fatal** for safety (halt before it's touched) even though
  some EOD rules only check at the close — assuming the stricter interpretation costs
  nothing and protects against both. Confirm Lucid's exact check timing at onboarding.
- 50k account: DD = **$2,000**. Verify the tier's exact DD, lock point, and contract limit
  at checkout.

Monte-Carlo note: under EOD rules with the sizing below, the **naked** book busts a funded
year ~2.3% of the time (early-sequence risk at base-7 before the buffer builds — not a
top-end problem). **With the Tier-1 halts active that drops to ~0.5%** — a 5× reduction.
The spine is not paperwork; it is the thing that clips that tail.

---

## Tier 1 — Account survival — THE THREE (never disable)

These three keep the funded account from dying. They are the "retain all three" core.

1. **Available-drawdown halt.** Watch `available_dd = equity − EOD_line` continuously. If it
   falls to a hard buffer, **flatten and stop trading for the day.** Because the EOD line is
   fixed intraday, this is equivalently "today's losses have consumed the day's cushion."
   It is the backstop below the buffer-scaling sizer — a floor the sizer can't undershoot.
   In the MC this is the single largest contributor to cutting bust 2.3% → 0.5%. Config:
   `dd_halt_buffer` (default: halt at `available_dd <= $250`; 50k DD = $2,000).

2. **Daily loss halt.** If realized P&L for the trading day `<=` a hard limit, **stop for
   the day** — the second half of the tail-clip. Sized so one bad day can't consume the EOD
   buffer. The canon carries a −$400 per-book day stop (NY Layer 2c); this is the
   account-level halt beneath it, covering both books combined. Config: `daily_loss_halt`
   (default −$800 account-wide; tighten to the firm's daily rule if the tier has one).

3. **Contract / size clamp.** The final order size is hard-clamped to the funder's max
   contract limit, no matter what the sizer computes. A sizing bug can never route an
   oversized order. Config: `max_contracts` = **40 micros / 4 minis** (Lucid 50k max —
   verify at checkout). This is also the sizing cap (below), enforced here as the hard
   ceiling.

---

## Tier 2 — Execution integrity — don't place a bad order

4. **Startup parity gate.** On boot, the ingestor replays the most recent completed
   historical day and asserts its features match the backtest to the decimal (CVD sign,
   VWAP anchor, MBO→MBP-10 aggregation). **If parity fails, the desk does not trade** — it
   runs read-only until a human clears it. This is the guard against the silent
   definition-drift that would quietly un-track the validated book.

5. **Feed-health / staleness guard.** No order is placed if the feed is stale (last tick
   older than `feed_stale_ms`), the book is crossed/locked, or a session's required
   context is incomplete (e.g. missing overnight for a London or gold trade). Missing data
   → skip the trade, never guess.

6. **Spread / slippage guard.** No order if the spread at fill exceeds a **relative**
   ceiling (Q-31 ruling — London 2026 spreads regime-shifted, so never a frozen absolute).
   Config: `max_spread_rel`. Reject rather than chase.

7. **Order-rate / duplicate guard.** Never send more than `max_orders_per_min`, never two
   orders for the same setup, never a resend without confirmation the first failed. Fat-
   finger and runaway-loop protection, and it keeps us far under Lucid's HFT detector.

8. **Limit-not-market enforcement.** Entries must be **limit orders at the computed
   `entry_ref`** with the stop/target bracket. The spine rejects any market entry order —
   the canon was validated on limit fills, and a market entry silently changes the edge.

---

## Tier 3 — System integrity — fail safe, not open

9. **Fail-closed on any error.** Any unhandled exception, NaN in a required feature, or
   ambiguous state → **flatten open positions, cancel working orders, halt.** The system
   never trades through uncertainty. A crashed brain is a flat account, not a stuck one.

10. **Heartbeat / watchdog.** A separate process confirms the desk is alive and the feed is
    flowing every N seconds; on loss of heartbeat it flattens and halts. Covers the "the
    box froze mid-position" case.

11. **Manual kill switch.** A human can flatten-and-halt everything instantly, and the
    desk cannot restart itself without a human clearing the halt.

12. **Every spine event is journaled.** Each halt/clamp/reject writes a record (which rule,
    the state that triggered it, the order it stopped) alongside the trade journal, so we
    can see exactly why the desk stood down.

---

## Sizing — de-risk & scale on available drawdown (Angus ruling)

Strategy-side risk *shaping* that sits above the spine (the spine is the hard floor below
it). The canon ladder gives a conviction multiplier per trade (0.5 / 1.0 / 1.5, plus
Q-boosts up to 2.25). That multiplier is applied to a **base** that scales with available
drawdown:

- **Base = 7 micros for the 1.0 ladder unit** (everything scales off this).
- **Below +$3k available drawdown: base stays 7.** (You build the eval / early funded buffer
  at the floor size.)
- **Past +$3k: +3 micros of base per additional $1k of available drawdown.**
- **Hard cap 40 micros / 4 minis** on the final order (= the Tier-1 contract clamp).

Final order micros = `min(40, round(base × ladder_multiplier))`, `base = 7 + 3·⌊(available_dd − 3000)/1000⌋`.

| available DD | base | 1.0 trade | 1.5 trade | 2.25 trade |
|---|---|---|---|---|
| ≤ $3k | 7 | 7 | 10 | 16 |
| $4k | 10 | 10 | 15 | 22 |
| $5k | 13 | 13 | 20 | 29 |
| $7k | 19 | 19 | 28 | **40** |
| $10k | 28 | 28 | **40** | 40 |
| $14k+ | 40 | **40** | 40 | 40 |

The same rule steps size **down** as available DD shrinks (a bad run or a withdrawal), so
approaching the floor mechanically de-risks — exactly the reason the spine's Tier-1 halt is
rarely reached. EOD MC on the combined NY+London book at this sizing: full Lucid cycle
(eval → $4k max payout) **~95% success, median ~29 days**; funded year **median ~$282k**
naked / **~$227k with the spine** halts active. The base-7 aggressiveness carries a ~2.3%
naked funded-year bust tail (early-sequence, pre-buffer) that the spine clips to ~0.5%; if
that tail is ever unwanted, the lever is a lower *early* base (ramp from 5), not the cap.

## What the spine is NOT

- It is **not strategy.** It never *decides to trade* — the canon does that. The spine only
  ever says "no" or "smaller" or "flat." It cannot turn a canon no-trade into a trade.
- It is **not discretion.** No judgment, no LLM, no tuning in the moment. Every threshold is
  a frozen config constant.
- It is **not the buffer-scaling sizer.** The sizer is strategy-side risk *shaping* (how
  much, as the buffer grows); the spine is the *hard floor* below it that the sizer can
  never breach.

## Launch checklist (spine must be green before the first live order)

- [ ] Tier-1 constants set to confirmed Lucid 50k numbers (EOD line + DD amount, lock point, 40-micro contract limit).
- [ ] Startup parity gate passes on a recent historical day.
- [ ] Feed-health, spread, order-rate guards tested with a forced-bad input each.
- [ ] Fail-closed verified (kill the brain mid-position → account flattens).
- [ ] Manual kill switch tested.
- [ ] Spine-event journaling confirmed writing.
