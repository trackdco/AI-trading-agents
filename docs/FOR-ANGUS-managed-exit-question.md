# FOR ANGUS — the managed-exit vs limit-bracket question (rulebook call)

**STATUS: ✅ RESOLVED (Angus, 2026-07-26).** RULING: **implement the canon exit as specified** —
V8 50% partial + prior-5m trail + break-even + 3-min cut + EOD flatten (this is Option A). **§B2
is scoped to ENTRIES only** (entries limit-only, always); **exits may be marketable** where the
canon exits at the market — the B1 ruling ("track stop-exit slippage separately, those genuinely
slip") confirms it. **§B4 reworded:** the invariant is a **resting protective STOP** attached at
the broker; there is no fixed target, so stop-attachment is the thing that must never fail. Built:
`src/canon/exit_manager.py` (decision engine), the order path now sends parent + stop child
(`dtc_client.submit_bracket`) and the spine read-back verifies the resting stop. Force-test added
(§C7): engine-death-mid-trade must fail-closed flatten. Document kept as the record of the call.

*(Original question preserved below.)*

---

## The problem in one paragraph

The signed-off canon (`baseline_book.parquet`, 400/400, **+$56,065.18**) exits every trade with
a **dynamic, path-dependent MANAGED exit** — partial at first structure, trail the runner, a
3-minute time cut, EOD flatten. The live executor (`src/canon/spine.py`) places a **static
limit bracket** — one resting stop leg + one resting target leg for the full size. A managed
exit **cannot be expressed as a single static bracket**, and the parts that can't (the time cut
and the EOD flatten) are inherently **market/marketable** exits — which collides head-on with
promotion gate **§B2 "No market orders. Zero. Ever. Structural, not statistical."** The edge was
validated on the managed exit; the executor can't reproduce it without either changing the exit
model or changing §B2. That is the ruling needed.

## 1. What the canon exit actually specifies (quoted)

The champion/canon management is **V8**, and the canon carries a **3-minute cut** on top:

- **V8 partial + trail** (`src/backtest/engine.py`):
  - `v8_partial_pct: float = 50.0  # pass-17 V8 (ANGUS March style): % booked at first structure`
  - `if cfg.mgmt_variant == "V8":  # prior-5m swing lookup for the V8 trail` (engine.py:489)
  - i.e. **book 50% at the first structural level, then TRAIL the remaining 50% on the prior-5-minute swing.**
- **Break-even stop**: `v1_be_at_r` (the stop is moved to break-even at a configured R).
- **The 3-minute cut** (`scripts/canon_mechanical.py`, "Layer 2d IN-TRADE"):
  - `cut = (T.r_3 <= -0.1106) & (T.fw_3 <= -13)` → `eff_dollars = np.where(T.cut3, T.r_3 * T.risk * 20, T.dollars)`
  - i.e. **if 3 minutes in the trade is adverse (r_3 ≤ −0.11 and fw_3 ≤ −13), exit NOW at the 3-minute price** — a time-triggered exit, not a price level.
- **Exit reasons the engine records** (engine.py:211):
  `exit_reason: str  # target | stop | be_stop | eod | partial+<reason>` — so an exit is one of:
  target hit, stop hit, **break-even stop**, **EOD flatten**, or a **partial** followed by one of those on the runner.
- London says the same explicitly (`scripts/london_canon.py`): *"the engine's partial/stop management already harvests"* the stalled trades.

So the canon exit is: **partial (50%) at first structure → trail the runner on prior-5m swings,
with a break-even stop, a 3-minute time cut, and an EOD flatten.** Multi-leg, dynamic, and two
of the triggers (3-min cut, EOD) are **time-based**, not price levels.

## 2. What the executor's limit-bracket model assumes — and precisely where it breaks

The spine builds one `OrderIntent(entry_ref, stop, target, size)` and submits a **single limit
bracket**: a limit entry with **one resting stop leg and one resting target leg for the full
size**, then verifies *"both bracket legs (stop + target) actually rest"* (`spine._verify_readback`).
§B4 requires *"every entry got its stop and target attached."*

Precisely where the two are incompatible:

| Canon exit behaviour | Static bracket | Incompatibility |
|---|---|---|
| **Partial 50% at first structure** | one target, full size | a bracket does not reduce size mid-trade |
| **Trail the runner (prior-5m swing)** | static stop leg | the stop must be **modified** as price moves; a resting leg is fixed |
| **Break-even stop** | static stop leg | same — requires modifying the stop |
| **3-minute cut ("exit at r_3")** | resting price legs only | a **time trigger**, not a price — no resting limit can express it; it fires at whatever price is trading at t+3min |
| **EOD flatten** | resting price legs only | a **time trigger** at session end — again not a price level |

The first three could, in principle, be handled by **modifying** the bracket (move the stop,
reduce the target quantity). The last two — the **3-minute cut and EOD flatten — cannot be a
resting limit at all.** They fire on a clock, at the market, and the canon P&L (`eff_dollars`)
is computed on that "exit at the 3-minute price" behaviour.

## 3. Managed exit as a modified bracket, or does it need market exits? — and §B2

- **Trail / break-even / partial** → expressible as **bracket modifications** (move the stop
  leg, cancel/replace or reduce the target leg). These can stay **limit/stop orders** — no
  market order required, so **§B2 is preserved** for this part.
- **3-minute cut and EOD flatten** → these are **time-triggered exits at the market**. To
  reproduce "exit at r_3" (the price 3 minutes in) or an EOD flatten, the executor must send a
  **market or marketable order** at that instant. A resting limit cannot fire on a clock.
  **This is the direct §B2 conflict:** faithfully reproducing the canon's exits requires exit
  orders that are, at minimum, marketable — which §B2 as written ("zero market orders, ever,
  structural") forbids.
- Note §B2's rationale in the gate is about **entries** ("a market entry silently changes the
  edge" — the canon was validated on **limit entry fills**). Whether the "zero market orders"
  rule was intended to bind **exits** as well is itself part of the ruling: the +$56,065 book's
  exits already include time-triggered, market-like exits.

## 4. What the backtest did at exit (the reference the live path must match)

`simulate()` (the engine) produced the +$56,065.18 book by, per trade: filling the **entry as a
limit at the retest**, then **booking 50% at the first structural menu level via trade-through**,
**trailing the remaining 50% on the prior-5-minute swing**, moving the stop to **break-even** at
`v1_be_at_r`, applying the **3-minute cut** (exit at the 3-min price when r_3 ≤ −0.11 & fw_3 ≤ −13,
booked as `eff_dollars = r_3 × risk × 20`), and **flattening at EOD**. The recorded `exit_reason`
is one of `target | stop | be_stop | eod | partial+<reason>`. **That managed-exit behaviour — not
a single fixed target — is the reference the live exit must reproduce to keep the gate's A-section
fidelity.** A static bracket produces different exits and therefore a different book.

## 5. Options (trade-offs only — Angus's call)

- **Option A — Full managed-exit executor.** Reproduce V8 + 3-min cut + EOD live via active
  order management: modify the stop to trail, book the 50% partial, and send **marketable exit
  orders** on the 3-min cut and EOD flatten.
  - *Trade-off:* faithful to the +$56,065 book (keeps A-section fidelity), but **requires
    amending §B2** to permit **exit** market/marketable orders (entries stay strictly limit).
    More execution machinery (live position management, stop-modify, timers) and more broker
    surface to get right before arming.
- **Option B — Static-bracket approximation.** Enter limit; rest one stop + one target (e.g. the
  first-structure level or an RR target); no partial, no trail, no cut, no managed EOD.
  - *Trade-off:* **§B2-clean** (all limit, zero market orders), but the exits **diverge from the
    validated book** — different exit prices and P&L, so the +$56,065 edge is **no longer the
    thing being run**. Would require **re-validating** the canon under a static-bracket exit
    before it can be trusted (a new backtest + a new signed-off number).
- **Option C — Hybrid: bracket-with-modification, rule the time exits separately.** Keep the
  partial + trail + break-even as **bracket modifications** (limit/stop only), and get a specific
  ruling on the **two time-triggered exits** (3-min cut, EOD): either (c1) permit marketable
  orders for *those two exits only* (a narrow §B2 carve-out), or (c2) approximate them with a
  resting limit (e.g. a limit at the 3-min-expected level) and accept the residual divergence.
  - *Trade-off:* most of the exit stays limit and close to faithful; the residual §B2 decision
    is scoped to just the time-based exits. Still needs a ruling on (c1) vs (c2), and (c2) leaves
    a measurable fidelity gap on the cut/EOD trades.

**What I need from you:** which exit model the live executor should target, and — coupled to it —
whether §B2 "zero market orders" binds **exits** or only **entries**. Everything downstream (the
executor's order-management design, §B2/§B4 wording, and whether a re-validation backtest is
required) follows from that ruling. I am not building an exit model until this is ruled.
