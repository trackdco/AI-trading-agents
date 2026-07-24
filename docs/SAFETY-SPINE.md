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
- It reads live **account state** (equity, trailing floor, open positions, order rate) and
  **feed health** — none of which the canon or agents ever see.
- It cannot be disabled by config in normal operation. Turning off a Tier-1 rule requires
  a deliberate code change, not a flag. (Angus ruling: account-survival rules are not
  tunable knobs.)

---

## Tier 1 — Account survival — THE THREE (never disable)

These three keep the funded account from dying. They are the "retain all three" core.

1. **Trailing-drawdown proximity halt.** If account equity comes within a hard buffer of
   the Lucid trailing floor, **flatten and stop trading for the session.** The
   buffer-scaling sizer already shrinks size as the buffer thins; this is the backstop
   below it — a floor the sizer can't undershoot. Config: `dd_halt_buffer` (default: halt
   at buffer <= $250 above the trailing floor; Lucid 50k trailing = $2,000).

2. **Daily loss halt.** If realized P&L for the trading day <= a hard limit, **stop for the
   day.** The canon carries a −$400 per-book day stop (Layer 2c); this is the
   account-level halt beneath it, covering both books combined. Config: `daily_loss_halt`
   (default −$800 account-wide; tighten to the firm's daily rule if the 50k tier has one).

3. **Contract / size clamp.** The order size is hard-clamped to the funder's max contract
   limit, no matter what the sizer computes. A sizing bug can never route an oversized
   order. Config: `max_contracts` (set to the Lucid 50k tier limit — verify at checkout;
   our sizing caps at 20 micros / 2 minis, so any real limit has headroom).

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

## What the spine is NOT

- It is **not strategy.** It never *decides to trade* — the canon does that. The spine only
  ever says "no" or "smaller" or "flat." It cannot turn a canon no-trade into a trade.
- It is **not discretion.** No judgment, no LLM, no tuning in the moment. Every threshold is
  a frozen config constant.
- It is **not the buffer-scaling sizer.** The sizer is strategy-side risk *shaping* (how
  much, as the buffer grows); the spine is the *hard floor* below it that the sizer can
  never breach.

## Launch checklist (spine must be green before the first live order)

- [ ] Tier-1 constants set to the confirmed Lucid 50k numbers (trailing floor, contract limit).
- [ ] Startup parity gate passes on a recent historical day.
- [ ] Feed-health, spread, order-rate guards tested with a forced-bad input each.
- [ ] Fail-closed verified (kill the brain mid-position → account flattens).
- [ ] Manual kill switch tested.
- [ ] Spine-event journaling confirmed writing.
