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

Monte-Carlo note: under EOD rules with the dollar-risk sizing below, the **naked** book busts
a funded year ~1.5% of the time (early-sequence risk before the buffer builds — not a top-end
problem). **With the Tier-1 halts active that drops to ~0.18%** — an ~8× reduction. The spine
is not paperwork; it is the thing that clips that tail.

---

## Tier 1 — Account survival — THE THREE (never disable)

These three keep the funded account from dying. They are the "retain all three" core.

1. **Available-drawdown halt.** Watch `available_dd = equity − EOD_line` continuously. If it
   falls to a hard buffer, **flatten and stop trading for the day.** Because the EOD line is
   fixed intraday, this is equivalently "today's losses have consumed the day's cushion."
   It is the backstop below the dollar-risk sizer — a floor the sizer can't undershoot.
   In the MC this is the single largest contributor to cutting bust 1.5% → 0.18%. Config:
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

8b. **Broker read-back verification.** After a submit, **read the order and the resulting
   position back from the broker** (DTC order-status + position reports) and confirm they
   match intent — side, quantity, account, and that **both bracket legs (stop + target)
   actually rest** — before the order is treated as live; then reconcile position-vs-intent
   on a timer. **Any mismatch → flatten + halt.** The submit ack is never trusted on its own
   (a fill can differ from, or a bracket leg can silently fail to place against, what was
   sent). This is the execution-side twin of the champion's "no arithmetic is load-bearing —
   re-check independently." Implemented in `src/canon/spine.py` (`_verify_readback`).

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

## Sizing — conviction-based DOLLAR-RISK, scaled on available drawdown (Angus ruling, 24-Jul)

Strategy-side risk *shaping* that sits above the spine (the spine is the hard floor below
it). We size by **fixed dollar risk per conviction tier**, not by a fixed micro count. The
canon ladder gives a conviction multiplier per trade (0.25 … 1.0 … 1.5, plus Q-boosts to
2.25); that maps to a **dollar amount at risk**, and contracts are whatever makes the stop
cost exactly that:

```
risk_$   = base_dollar(available_dd) × min(2.0, conviction)      # 2.25 caps at 2× base
micros   = round( risk_$ / (stop_pts × $2) )                     # MNQ = $2/pt
final    = min(40, micros)                                       # 40-micro Tier-1 clamp
```

- **base_dollar = $200 for the 1.0 tier at ≤ $3k available DD.** At the floor that gives
  exactly Angus's schedule: **1.0 = $200, 1.5 = $300, 2.25 = $400** (the hard per-trade
  ceiling at the floor). Interpolated tiers are linear: 0.25 = $50, 0.5 = $100, 0.75 = $150.
- **Past +$3k available DD: +$75 to the 1.0-base per additional $1k of available DD**
  (`base_dollar = 200 + 75·⌊(available_dd − 3000)/1000⌋`). This is the MC sweet spot —
  it builds the operating buffer faster (which is where the account is safest) while
  holding max-payout probability essentially flat vs the gentler +$50. On a 50k the working
  band is ~$2k–$6k available DD (withdrawals keep pulling it back), so the 1.0-base runs
  ~$200–$425 in practice. All tiers scale in proportion; the 40-micro clamp is the ceiling.

**Why dollar-risk, not micro-count (the core reason):** under a fixed micro count, the same
"1.0 average setup" actually risked **$98–$724** across the book purely because stop width
varies 7–60 pts — you'd unknowingly risk $724 on an average setup on a fat-stop day, exactly
the "brutally rinsed" failure mode. Dollar-risk pins every 1.0 to $200, every 2.25 to $400,
**stop-width-normalized**: tight stops buy more contracts, fat stops fewer, dollars constant.
Consistency is king — now true at the dollar level, not just the setup level.

Live schedule (per-trade $ at risk; steps **down** the same way as available DD shrinks, so a
bad run mechanically de-risks toward the floor):

| available DD | 0.25 | 0.5 | 0.75 | 1.0 | 1.5 | 2.25 |
|---|---|---|---|---|---|---|
| ≤ $3k (floor) | $50 | $100 | $150 | **$200** | **$300** | **$400** |
| $4k | $69 | $138 | $206 | $275 | $412 | $550 |
| $5k | $88 | $175 | $262 | $350 | $525 | $700 |
| $6k | $106 | $212 | $319 | $425 | $638 | $850 |
| $7k | $125 | $250 | $375 | $500 | $750 | $1,000 |
| $10k | $181 | $362 | $544 | $725 | $1,088 | $1,450 |

EOD MC on the combined NY+London book at this sizing (Lucid 50k, 20k sims): full cycle
(eval → $4k max payout) **94% success, median ~32 days**; funded year **median ~$302k naked /
~$237k with the spine** halts active. Crucially the **naked funded-year bust is 1.5%, cut to
0.18% with the spine** — vs 4.9% / 0.9% for the old static-micro sizing. The stop-width
normalization removes most of the early-sequence tail *before* the spine even acts (a 3–5×
reduction in bust risk at equal median profit), which is the whole point of the rule.

**Baseline note:** the *frozen* combined baseline book (`output/baseline_book.parquet`, the
agent-replay ground truth) is sized at the **floor schedule only** — deterministic per-trade,
no DD-scaling — so it stays path-independent and reproducible to the dollar. The DD-scaling
above is a live overlay applied identically by the baseline sim and the agents from the same
account-state feed.

## Withdrawal policy — build the buffer, then harvest (Lucid 50k, `scripts/mc_payout_cycles.py`)

Lucid pays out **$2,000 max per withdrawal**, gated by **5 winning days between payouts**,
and a withdrawal **reduces balance** (hence available DD, hence sizer base). Run 5 funded
accounts per login, copy-traded off the identical book. Modeling the real cycle (not a
one-shot target) over a funded year, 20k sims:

| policy | withdraw when | back to | cash/acct/yr (median) | 1st payout | bust % | ×5 accounts |
|---|---|---|---|---|---|---|
| Harvest-min | bal ≥ $4k | $2k | **$50,000** | ~17d | 2.15% | ~$250k/yr |
| **Build-6 (chosen)** | bal ≥ $6k | $4k | **$48,000** | ~23d | **1.50%** | ~$240k/yr |
| Build-8 | bal ≥ $8k | $6k | $48,000 | ~28d | 1.51% | ~$240k/yr |

The counter-intuitive finding: **the 5-winning-day rule — not the balance — caps payout
frequency** (~24–25/yr either way), so building a bigger buffer does *not* meaningfully slow
the cash and does *not* speed it up. What it changes is **survival**: harvesting down to $2k
sits you just above the 50k floor after every payout, so a bad streak busts ~30% more often
(2.15% vs 1.50%). **Build-6** gives up ~4% cash (~$10k/yr across 5 accounts) to keep a $4k
cushion after each withdrawal — cheap insurance, since a busted account forfeits its entire
~$48k/yr stream plus the re-eval cost. Consistency is king. (These are *naked* rates; the
Tier-1 spine halts clip them a further 5–8×.) Lucid's consistency rule = **5 positive days of
≥ +$150 each between payouts** (confirmed); it barely bites — at the DD-scaled sizing our
winning days almost always clear $150, so Build-6 still nets ~$48k/acct/yr with it enforced.

## What the spine is NOT

- It is **not strategy.** It never *decides to trade* — the canon does that. The spine only
  ever says "no" or "smaller" or "flat." It cannot turn a canon no-trade into a trade.
- It is **not discretion.** No judgment, no LLM, no tuning in the moment. Every threshold is
  a frozen config constant.
- It is **not the dollar-risk sizer.** The sizer is strategy-side risk *shaping* (how
  much, as the buffer grows); the spine is the *hard floor* below it that the sizer can
  never breach.

## Launch checklist (spine must be green before the first live order)

- [ ] Tier-1 constants set to confirmed Lucid 50k numbers (EOD line + DD amount, lock point, 40-micro contract limit).
- [ ] Startup parity gate passes on a recent historical day.
- [ ] Feed-health, spread, order-rate guards tested with a forced-bad input each.
- [ ] Fail-closed verified (kill the brain mid-position → account flattens).
- [ ] Manual kill switch tested.
- [ ] Spine-event journaling confirmed writing.
