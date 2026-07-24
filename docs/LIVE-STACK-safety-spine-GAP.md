# LIVE-STACK — safety-spine gap (for Angus / Pat)

**Raised by:** Claude (ops readiness sweep), 2026-07-24.
**Status:** OPEN — needs an Angus/Pat decision **before any order path is armed**
(before punch-list #6 execution / #11 wiring in `docs/LIVE-STACK.md`).

## The gap

`docs/LIVE-STACK.md` finalises the data → feature → score → order chain, but it does
**not** carry the three safety-spine primitives we last built to. A search of the doc
finds none of them by name. What the doc *does* have: Python-side order-time guards
(relative spread/slippage cap), a P&L-blind buffer sizer, "no LLM judgment in the path,"
and R|Trader Pro as the firm's drawdown-of-record. Those are necessary but are **not** the
safety spine. The three missing primitives:

### 1. Yes-only executor
The component that talks to DTC must accept **only** an explicit, fully-formed
"place THIS exact limit bracket (entry_ref, stop, target, qty, account)" instruction and
may only ever **add** safety (cancel / flatten). It never invents, resizes, re-derives, or
"improves" an order, and it fail-closes on anything malformed or ambiguous. This is the
execution-side twin of the Vault rule "commands can only ADD safety."

### 2. Broker read-back verification
After a submit, **read the order/position state back from the broker** (DTC order-status
+ position reports) and verify it matches intent — price, quantity, account, and that both
bracket legs (stop + target) actually rest — before treating the order as live; then
reconcile position vs intent on a timer and **halt on any mismatch**. The submit ack is
never trusted on its own (a fill can differ from, or a bracket leg can silently fail to
place against, what we sent). This is the execution-side twin of the champion's
"no LLM arithmetic is load-bearing — re-check independently."

### 3. Direct-to-broker kill path
A flatten / cancel-all that reaches the broker **independently of the normal decision
loop**, so a wedged or mis-scoring bot can still be brought flat: a DTC `cancel-all` +
flatten the `hermes-risk` watchdog (and a human) can fire directly, plus R|Trader Pro's
manual flatten as the out-of-band backstop. This must compose with the existing file kill
switch (`output/live/KILL`, `src/live/risk.py`) and `hermes-risk` (the deterministic
liveness watchdog) — a stale feed or a tripped kill must be able to *flatten*, not merely
stop admitting new trades.

## Why this can't be skipped

The champion/Vault path already enforces "guards in front of every order, re-checked
independently, kill can only add safety." The live canon stack routes real limit-bracket
orders to a funded account over DTC. Arming that order path **without** the executor being
yes-only, without reading back what the broker actually did, and without an out-of-band
flatten re-introduces exactly the failure modes the Vault design eliminated — on the side
where real money moves.

## Where it lands in LIVE-STACK.md

- Step 6 (Execution — limit brackets over DTC): make the order builder the **yes-only
  executor**, and add the **read-back verify** loop against DTC order/position reports.
- Cross-cutting D (Python-side execution guards): already the right home for the spread
  cap + sizer; add the read-back reconcile + halt-on-mismatch here.
- `hermes-risk` (this repo's `docs/architecture-hermes-v2.md`): owns the **direct-to-broker
  kill path** alongside its feed-liveness watchdog + `KILL` integration.

## Decision requested

1. Retain all three primitives on the live canon path? (recommended: yes)
2. Component boundaries: yes-only executor + read-back inside the DTC execution module;
   direct-to-broker kill owned by `hermes-risk`. Confirm or reassign.
3. Sequencing: treat this as a **blocker on punch-list #6/#11** (no order path armed until
   the spine is in), or as a fast-follow before the first *funded* (not paper) order?

Until this is decided, I will not build or arm any DTC order-submission path.
