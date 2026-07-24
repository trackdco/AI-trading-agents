# FOR ANGUS — two gating rulings before the file-tail data path goes live

**Decisions needed from you before the Route-B data path (and the funded feed) go live.**
Neither blocks building or offline testing — both are done (431 tests green; the on-box
pin/replay steps are in `docs/BOX-HANDOFF.md`). These are the two things only you can settle,
plus one heads-up that shapes the research roadmap.

## Background in one paragraph

Sierra advertises `MarketDataSupported:1` but **rejects serving NQU6 market data over DTC**
("Market data request not allowed") — the CME non-professional / no-redistribution licence
blocks Sierra's DTC server from feeding *data* to an external client. Orders route over DTC
fine. So the data path was rebuilt as **Route B** (the primary route in your approved
`docs/architecture-hermes-v2.md` §2.2): our Python reads the **`.scid`/`.depth` files Sierra
itself writes to local disk**, on the same machine, and never takes a served feed. Orders
still go out over DTC unchanged.

---

## Q1 — Does the data agreement permit reading Sierra's own on-disk `.scid`/`.depth` files?

**The question:** is local **own-use** of the files Sierra persists to its own `Data\`
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

## Q2 — Does the Lucid / Rithmic plan deliver full 10-level DOM, not throttled?

**The question:** does the funded execution plan actually deliver the **full 10-level DOM
depth** for NQ, un-throttled — or is depth top-of-book / restricted?

**Why it's load-bearing:** the canon's depth signals (`WALLSZ`, `dep_wall_above/below`,
thickness, imbalance) are a **top-2 signal in every window** and die without the full ladder.
`docs/VPS-SETUP.md` Part 4 already found the answer for the *data source*: **Rithmic carries
no depth at all** (`MarketDepthIsSupported: 0`), so the ladder **must** come from **Denali (SC
Data)** — the funded CME real-time+depth subscription (~$40.50/mo non-pro, Part 4c), which
needs the funded account to qualify for non-pro rates. Rithmic stays the execution route +
drawdown-of-record.

**What I need from you:** confirmation that (a) the plan is **Rithmic-execution + Denali-data**
as Part 4 describes, and (b) the Denali CME subscription you'll buy includes **full 10-level
DOM** (depth is the pricey part of the non-pro bundle, not the ~$16 top-of-book figure). The
on-box replay (`BOX-HANDOFF.md` Step C) will show `10 bid / 10 ask` when depth is live; a thin
or empty book is the tell that depth is throttled or not yet subscribed.

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
| Q1 on-disk own-use ruling | trusting Route B live | **needs your ruling** |
| Q2 full 10-level DOM (Denali) | the depth signal family working live | **needs confirm at signup** (funded) |
| MBO substrate (heads-up) | the *next* research campaign, not go-live | **your roadmap call** |

Building + offline validation are done. Engine places nothing until the `StartupParityGate`
is human-cleared green (`src/canon/infra.py`).
