# Architecture — Hermes v2 (order-flow feed + live execution plane)

**Status: APPROVED.** The overall architecture described here and in
`context/architecture.md` was signed off by **Angus on 2026-07-24**, relayed via Pat
(the sign-off did not come to this repo directly from Angus — provenance is Pat's relay
of Angus's verbal approval, 24 Jul 2026). This document records that approval and
specifies the one piece the sign-off unblocks: the **order-flow data source and its
integration seam**.

Scope: this extends — does not replace — `context/architecture.md`. All six key
invariants there still hold; §C.2 of `docs/UPDATED-PLAN-2026-07-23.md` (the live-feed
vendor decision, previously "Databento-live or broker-native, TBD") is now **resolved
for the order-flow plane** by §2 below.

---

## 1. Sign-off record

| Field | Value |
|---|---|
| What | The Desk + Vault architecture (Engine → Desk/Hermes → Vault) and this v2 order-flow extension |
| Decision | **Approved** |
| By | Angus |
| Date | 2026-07-24 |
| Provenance | Relayed via Pat (Pat's relay of Angus's verbal approval — not a direct written sign-off from Angus in-repo) |
| Effect | Unblocks the order-flow vendor decision (§2) and the Phase-2 live-infra plan (§2.3) |

This is a provenance-honest record: the approval is **second-hand (Pat relaying Angus)**.
If a direct written confirmation from Angus later lands, append it here rather than
overwriting this row — the chain of custody is itself auditable, same discipline as the
v1.2 ruling log.

---

## 2. Order-flow source — DECIDED: Sierra Chart (Denali CME depth)

**Decision:** the bot's **order-flow / market-depth** source is **Sierra Chart driving
the Denali CME depth feed**, NOT Databento-live. Databento **historical bars stay** for
OHLCV backtest parity (`context/architecture.md` §External services, unchanged) — this
decision is about the *depth / order-flow plane*, which Databento-live was never going to
serve as cleanly.

Why Sierra Chart + Denali:
- **Full CME depth** (MBP/MBO), which is exactly what the existing order-flow feature
  pipeline already consumes — `scripts/depth_features.py`, `scripts/london_depth.py`,
  `scripts/depth_daywin.py` all compute thickness / imbalance / walls / replenishment /
  CVD from **MBP-10 per-minute book snapshots** (`data/reference/depth_2026`,
  `data/reference/depth_london`). SC/Denali is a native source of that same book.
- **One vendor for real-time AND historical** depth, which sets up the parser-unification
  win in §3.
- The champion trades on **closed 1-minute bars** and per-minute order-flow features, so
  we do **not** need microsecond latency — this materially widens the viable integration
  routes (see §2.2, Route B).

### 2.1 Where it plugs in (the seam)

The connector is **deterministic Python in the data plane** — "Python sees" — and never
touches the risk/LLM path (invariant 6 preserved). It presents two Protocols:

```
Sierra Chart (Windows VPS, Denali CME depth)
        │  .scid / .depth  (files)   or   DTC (TCP)
        v
┌───────────────────────────────────────────────┐
│  DETERMINISTIC SC CONNECTOR (new, Python)      │
│  parses SC records → canonical schema          │
│   • BarFeed   (src/live/feed.py, EXISTS)       │  closed 1-min Bars
│   • DepthFeed (NEW, same shape as MBP-10)      │  per-minute book snapshots
└───────────────┬───────────────────────────────┘
                v   (feeds the Engine + order-flow feature stack; Vault unchanged)
```

- `BarFeed` already exists (`src/live/feed.py` — one `stream()` yielding closed `Bar`s).
  The SC connector is a new `BarFeed` implementation; **no Vault change** (per §C.2's
  swappable-adapter contract).
- `DepthFeed` is **new**: it must emit book snapshots in the **same MBP-10 long-form the
  existing depth scripts already use**, so the historical order-flow feature code is
  reused verbatim on the live path (no second feature implementation to keep in parity).
- **Feed-parity check is mandatory** before trusting it (per `context/architecture.md`
  §C.2 hard requirement): replay one day of SC-sourced bars **and** depth against the
  Databento historical bars + the frozen MBP-10 snapshots and assert they match in shape
  and values. This is the same gate discipline as `scripts/vector_parity.py` /
  `scripts/runner_drill.py`.

### 2.2 The two candidate routes (recon both)

Both routes read the **same Denali depth**; they differ in *how* our connector gets it.

#### Route A — SC as a DTC server; our connector is a DTC client

Sierra Chart implements **DTC (Data and Trading Communications)**, its own open TCP
protocol for market data *and* order routing. SC runs a DTC server; our deterministic
connector opens a TCP socket and subscribes.

- **Mechanism:** connect → `LOGON_REQUEST` → subscribe (`MARKET_DATA_REQUEST`,
  `MARKET_DEPTH_REQUEST`) → receive a `MARKET_DEPTH_SNAPSHOT_LEVEL` burst then
  incremental `MARKET_DEPTH_UPDATE_LEVEL` messages, plus `MARKET_DATA_UPDATE_TRADE` for
  the tape. Encoding is selectable (binary, binary-VLS, or JSON-compact).
- **Pros:** real-time push (lowest latency); a *documented wire protocol* rather than an
  on-disk file layout; **one connection could also carry order execution** to an
  SC-connected broker later (collapses toward the broker-native option in §C.4); no
  file-rotation / partial-write handling.
- **Cons:** live-only — **DTC does not give us the 3-year history** (historical is a
  separate HTTP/records path), so it does **not** unify with §3; we must maintain book
  state from snapshot+updates ourselves (correctly applying add/modify/delete at each
  level); requires SC running with the DTC server enabled and reachable from the
  connector; network-reliability + reconnect/resubscribe logic; depth-update semantics
  must be verified against SC's current DTC spec.

#### Route B — tail SC's `.scid` / `.depth` files

SC continuously writes intraday and depth data to disk; our connector tails those files.

- **Mechanism:** `.scid` = *Sierra Chart Intraday Data* — a fixed-layout binary file
  (header + fixed-size records: SCDateTime + O/H/L/C + NumTrades + TotalVolume +
  Bid/AskVolume). `.depth` = *Market Depth Data* — binary records of per-level book
  commands (add/modify/clear, side, price, quantity, timestamp). The connector memory-maps
  / seeks to EOF and reads newly appended records as SC flushes them, reconstructing the
  book and 1-min bars.
- **Pros:** **the same parser reads historical files and live files** — SC appends live
  data to the exact same `.scid`/`.depth` format it stores history in. This is the
  decisive property for §3: one parser ⇒ historical validation, the 3-year sim, and live
  order flow are byte-identical code paths. No protocol/session layer. Naturally
  resumable (offset in a file).
- **Cons:** couples us to SC's on-disk **record layout + version** (must be pinned and
  verified — layouts have byte-exact field orders; the `.depth` format is less documented
  than `.scid`); tailing must handle SC's **daily/size file rotation**, partial/last-record
  writes, and flush latency; **no order execution over this channel** (orders need a
  separate path — DTC or broker API); exact byte layouts must be confirmed against the
  installed SC build **and the sample day** before trusting the parser.

#### Recommendation — **Route B (file tailing) as primary**, DTC as a later complement

Because the strategy runs on **1-minute** cadence, Route A's latency edge buys us nothing
material, while Route B's parser-unification (§3) is a first-order architectural win:
**one deterministic SC-format parser becomes the single source for historical validation,
the 3-year simulation, and the live order-flow feed** — the same "one Market Engine, both
modes" principle that already gives us backtest↔live parity, now extended to the depth
plane. Route A would force a *separate* live-vs-historical code path (DTC live + file/HTTP
historical), which is exactly the parity-risk we design against.

Adopt **Route B for the data plane**. Keep **DTC (Route A) as an explicit later option
for the execution plane** (order routing over one SC connection) and as a fallback if
file-tailing latency or flush behaviour ever proves inadequate for a faster future
strategy. Both routes must pass the §2.1 feed-parity gate before going live.

### 2.3 Infra requirement — Windows VPS (Phase-2 component), watchdogged by hermes-risk

Sierra Chart is **Windows-native** for production (no supported Linux build). Therefore:

- **Provision a small always-on Windows VPS** as a **Phase-2 infrastructure component**
  (distinct from the Linux VPS that runs the deterministic bot). It runs SC with the
  Denali subscription and either (Route B) writes `.scid`/`.depth` to a share the
  connector reads, or (Route A) hosts the DTC server. Size it minimally — SC + Denali
  depth for one instrument is light. This is net-new infra; `context/architecture.md`
  §Environments ("small always-on VPS, not provisioned yet") is extended, not replaced.
- **hermes-risk** — the deterministic health/liveness **watchdog** (introduced by this
  v2 doc; it is **not** the Vault, and it is **not** an LLM agent — it is Python, so
  invariant 6 holds) — monitors the Windows VPS + SC:
  - SC process up; Denali **connected** (not just running-but-disconnected);
  - Route B: the `.scid`/`.depth` files are **advancing** (new records within an
    expected interval during CME hours); Route A: DTC heartbeat / snapshot freshness;
  - on a **stale or unhealthy feed**, hermes-risk **trips the existing KILL switch**
    (`output/live/KILL`, `src/live/risk.py`) and/or raises a halt — a dead/stale
    order-flow feed must fail **closed** (no new trades), never trade on stale book.
  - hermes-risk needs its own component spec (scope, thresholds, where it runs — likely
    on the Linux bot host, watching the Windows VPS across the network). Flagged as an
    open deliverable; this doc only assigns it the watchdog duty Angus/Pat specified.

---

## 3. Flag — the 3-year historical export may itself be Sierra Chart format

**Open item to confirm on the sample day:** Angus's ~3-year historical order-flow export
may already be in **Sierra Chart format** (native `.scid`/`.depth`, or an SC text/CSV
export). **If the sample day confirms this**, then — with Route B chosen — a **single
deterministic SC-format parser covers all three consumers**:

1. **Historical validation** (parity against the existing Databento/MBP-10 depth features),
2. **the 3-year simulation** (the long-walk backtest over the export), and
3. **live order flow** (the same parser tailing SC's live files).

**Design implication (design for this now):** build the SC connector as a **format-first
parser** with a thin `source` shim — `historical_file` (a fixed `.scid`/`.depth` on disk),
`replay` (stream a historical file as if live, for the 3-year sim and drills), and
`live_tail` (follow SC's currently-writing files) all sit behind the **same record-parsing
core**. Do not fork a "historical parser" and a "live parser." The `DepthFeed`/`BarFeed`
Protocols (§2.1) are the boundary; the SC parser is the single implementation behind them.

**Verification gate before committing to this:** on the sample day, confirm (a) the export
is SC format, (b) the exact record layout + version matches the installed SC build, and
(c) a parity replay of the sample day reproduces the frozen MBP-10 depth features. If the
export turns out **not** to be SC format, Route B still stands for live; the historical
path then keeps its current Databento-derived depth and we lose only the single-parser
unification — so this flag is an *optimization to confirm*, not a load-bearing assumption.

---

## Open items (next actions)

- [ ] **Sample day**: confirm Angus's 3-year export format (§3) — gates the single-parser design.
- [ ] Pin the installed SC build's `.scid`/`.depth` record layouts; write the deterministic parser + unit tests against a captured sample.
- [ ] Implement the SC `BarFeed` + new `DepthFeed`; wire `DepthFeed` output to the existing MBP-10 feature scripts.
- [ ] Feed-parity gate (§2.1): SC-sourced bars+depth vs Databento bars + frozen MBP-10 snapshots for one day.
- [ ] Provision the Phase-2 Windows VPS; stand up SC + Denali.
- [ ] Spec + build **hermes-risk** watchdog (thresholds, cross-host liveness, KILL integration).
- [ ] Obtain a **direct** written architecture sign-off from Angus to append to §1 (current record is Pat's relay).
