# FOR ANGUS — gating rulings before the file-tail data path goes live

**STATUS 2026-07-26: BOTH RULINGS CLOSED. Q1 APPROVED by Angus; Q2 resolved (Lucid depth add-on; Denali deactivated). No decisions outstanding — Route B is cleared to build and go live.**

Decisions needed from you before the Route-B data path goes live. Neither blocks building or
offline testing — those are done (**432 tests green**; the on-box pin/replay steps are in
`docs/BOX-HANDOFF.md`), plus one heads-up that shapes the research roadmap.

## Background in one paragraph

Sierra advertises `MarketDataSupported:1` but **rejects serving NQU6 market data over DTC**
("Market data request not allowed") — the CME non-professional / no-redistribution licence
blocks Sierra's DTC server from feeding *data* to an external client. Orders route over DTC
fine. So the data path was rebuilt as **Route B** (the primary route in your approved
`docs/architecture-hermes-v2.md` §2.2): our Python reads the **`.scid`/`.depth` files Sierra
itself writes to local disk**, on the same machine, and never takes a served feed. Orders
still go out over DTC unchanged.

---

## Q1 — ✅ APPROVED (2026-07-26, Angus) — Route B on-disk own-use is authorised

> **RULING (Angus, 2026-07-26): "you can go ahead."**
>
> Route B is approved: our Python may read the `.scid`/`.depth` files Sierra writes to its own
> `Data\` folder on the same VPS, for own-use trade computation. Build on this. No feed is
> served to any external application and nothing leaves the machine as a feed.
>
> Scope of the approval: **local, same-machine, own-use reads only.** If the design ever needs
> to move data off the box as a feed, or serve it to a third party, that is a NEW question and
> must come back to Angus.

**The question (as put):** is local **own-use** of the files Sierra persists to its own `Data\`
folder — read by our Python process on the same VPS, purely to compute our trade decisions —
within the CME non-pro + Sierra terms?

**Why I read it as yes (but it's your call):** the redistribution line the DTC reject enforces
is about **serving a data feed to a separate/external application**. Reading files the
application already wrote to local disk, on the same box, for your own trading, is the same
class of act as any Sierra spreadsheet study, alert, or chart export consuming that data — it
is not a feed handed to a third party and nothing leaves the machine as a feed. This is
*cleaner* than the alternative in-process ACSIL-study route (which also stays in-process), and
far cleaner than DTC redistribution (which is what's actually prohibited).

**What I need:** your ruling that on-disk own-use is permitted. If you want maximum distance
from the line, the answer is the same route — it's already the most conservative one that
still gets us the data. If you read it as **not** permitted, the fallback is the funded-account
CME data subscription feeding Sierra's own charting only, with us consuming via a mechanism you
bless — flag it and I'll re-plan.

## Q2 — ✅ RESOLVED (2026-07-26, Angus) — depth comes from the Lucid add-on, NOT Denali

**Answered by events. Do not act on the superseded plan below.**

Angus bought Lucid's **Market Depth add-on** (~$27.30, full bundle) on the existing Rithmic
connection. Sierra now reports **`MarketDepthIsSupported: 1`** (was `0`) and **MBP-10 is
confirmed flowing**. The **Denali/CME trial has been DEACTIVATED** — confirmed by Angus
2026-07-26; nothing further to buy, no anchor/dormant live account, no monthly ritual.

**Current wiring: Rithmic for BOTH data and execution.** All four Sierra credential fields
(Market Data + Historical Data + Trading) are filled with `LT-QJ26R3G6` + the Rithmic
password. Monthly run cost ≈ VPS $80 + Sierra Pkg12 $56 + Lucid depth $27 ≈ **$163/mo**.

**Still to verify on the box (the one part of Q2 that remains):** that the ladder really is
**~10 levels a side and not throttled**. Count populated levels on the NQU6 Trade DOM, or read
it out of the `.depth` sample — `BOX-HANDOFF.md` Step C.1 prints `N bid / N ask`. A thin book
is the tell.

<details><summary>Superseded reasoning (kept for the record — this was WRONG)</summary>

> `docs/VPS-SETUP.md` Part 4 concluded **Rithmic carries no depth at all**
> (`MarketDepthIsSupported: 0`), so the ladder **must** come from **Denali (SC Data)** — the
> funded CME real-time+depth subscription (~$40.50/mo non-pro), which needs a funded account
> for non-pro rates.
>
> **Why it was wrong:** Rithmic's *base* plan carries no depth, but Lucid sells a depth add-on
> that enables Level 2 on the same Rithmic feed. The stack was tunnel-visioned on Denali
> instead of checking for a simpler path. Angus caught it.

</details>

---

## Heads-up (not a question) — Route B gives **MBP-10, not true MBO**

Sierra's `.depth` file is **level data (MBP)**: per-price-level size **and order count**
(`NumOrders`) per update. That is exactly what the canon was validated on (MBP-10), so
**live scoring is fully served** — no gap for go-live.

**But** it is **not** order-by-order **MBO**. The `.depth` file cannot reconstruct wall
*composition* (one whale vs forty minnows beyond the level's count), iceberg refresh, or
order pulls/fades as price approaches — the raw-MBO research substrate that `docs/LIVE-STACK.md`
(§C, "MBO from launch") earmarks as the next campaign's fuel. That substrate needs a **separate
order-by-order feed** (Denali's MBO stream / Package 12 order-by-order, captured on its own
path), added later — it never touches the live scoring path regardless.

**Implication for the plan:** LIVE-STACK's "capture raw MBO from day one" goal is **not**
delivered by Route B alone. Two ways to go, your call — no action needed now:
1. **Go live on MBP-10 now** (scoring is complete), and add the MBO capture path when the
   research campaign actually needs it. *(My recommendation — it unblocks go-live and defers
   the firehose-storage cost until there's a campaign to justify it.)*
2. **Stand up the MBO capture path before go-live** so the forward substrate accumulates from
   the first live day, per the original LIVE-STACK intent — at the cost of building +
   provisioning the order-by-order capture now.

---

## Summary — what unblocks on each answer

| Item | Blocks | Status |
|---|---|---|
| Q1 on-disk own-use ruling | trusting Route B live | ✅ **APPROVED** (Angus, 2026-07-26) |
| Q2 depth source | the depth signal family working live | ✅ **RESOLVED** — Lucid add-on on Rithmic, MBP-10 confirmed; Denali deactivated |
| 10-level ladder not throttled | depth signal quality | ⏳ **verify on box** — count DOM levels / `BOX-HANDOFF.md` Step C.1 |
| MBO substrate (heads-up) | the *next* research campaign, NOT go-live | ⏳ roadmap call — recommendation: option 1 (go live on MBP-10 now) |

Building + offline validation are done. Engine places nothing until the `StartupParityGate`
is human-cleared green (`src/canon/infra.py`).
