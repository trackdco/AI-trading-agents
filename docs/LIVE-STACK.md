# Live Trading Stack — build spec

How the canon goes from CME to a filled order. The chain is:

```
Rithmic (CME feed + account)
   └─► Sierra Chart  ──DTC──►  Python ingestor  ──►  rolling feature state
          ▲                         │
          │                         ├─► session router → canon book (pre / gold / London)
          │                         ├─► frozen thresholds → score → size
          │                         └─► journaler
          └──────DTC (limit bracket order)◄──── execution
```

**One principle governs everything below: the live system must produce the exact same
numbers the backtest did, or the frozen thresholds are meaningless.** Sierra's built-in
studies are NOT trusted — Python recomputes every canon feature from the raw feed, and a
reconciliation day proves parity before a single funded order is placed.

Cost: ~$90–145/month all-in (Sierra package + Denali MBO data from launch + optional VPS;
the funded firm provides the Rithmic execution connection free). Full breakdown at the end.

---

## Step 1 — Data & account source: Rithmic (R|Trader Pro)

- Buy the funded account with the **Rithmic** connection option (not Tradovate).
- Download R|Trader Pro, log in once to sign the CME **non-professional** data agreement.
  After that Sierra takes the feed over the same credentials; you only reopen R|Trader to
  check the firm's daily drawdown state.
- **VERIFY BEFORE PAYING FOR ANYTHING ELSE:** the funded Rithmic plan must include full
  **10-level DOM depth**, not just top-of-book. Our depth checks (`WALLSZ`,
  `dep_wall_above_d`, wall-behind, etc.) are a top-2 signal in every window and die
  without the depth ladder. Some prop Rithmic feeds are restricted — confirm depth is on.

## Step 2 — Feed bridge: Sierra Chart (Advanced package)

- Sierra connects to the CME feed and is our **reliable raw-feed bridge and order router** —
  NOT the calculator whose numbers we trust. (See Step 4 for why.)
- **Feed = MBO (Market By Order), single source, dual purpose** (Angus ruling). MBO is the
  individual-order stream (every add / modify / cancel with an order ID) and is strictly
  RICHER than MBP-10, so one MBO subscription serves both roles:
  - **Aggregate MBO → MBP-10 for live canon scoring.** The canon was validated on MBP-10
    (`WALLSZ`, `dep_wall_*`, thickness, imbalance); the frozen thresholds only mean
    anything against MBP-10 definitions. The live scoring path consumes the *aggregated*
    view. The reconciliation day (Cross-cutting A) must prove our MBO→MBP-10 aggregation
    equals the Databento MBP-10 the backtest used.
  - **Retain raw MBO for the journal/research layer.** It never touches the
    frozen-threshold scoring path — it accumulates as the substrate for the next campaign.
    MBO exposes what MBP-10 discards: wall *composition* (order count vs total size — one
    whale or forty minnows), iceberg/refresh detection, order pulls/cancels as price
    approaches, queue dynamics, order-size distribution. This is a direct future upgrade to
    our strongest signal — a big wall that HOLDS vs one that VANISHES is invisible to
    MBP-10. After a few months of forward MBO around every trade, mine it the way the
    historical campaigns were mined.
- **Verify the MBO source.** MBO is a premium CME feed and a firehose (millions of
  events/day on NQ). Confirm how it's delivered in the funded setup — Rithmic's funded
  connection typically provides DOM (MBP) depth, not full order-by-order; true CME MBO may
  need Sierra's Denali/CME data feed (~$40/mo non-pro CME bundle) as the data source while
  Rithmic remains the execution route + the firm's drawdown-of-record. Provision storage
  and throughput for the raw MBO capture accordingly (capture a window around each trade
  rather than the entire tape if storage is tight).

## Step 3 — The bridge protocol: DTC server

- Sierra settings → enable **DTC Protocol Server** → it exposes a local port (e.g.
  `127.0.0.1:11099`).
- What DTC actually carries: **raw market data** (trades with aggressor side, quotes, DOM
  depth), historical data, and **orders/positions**. It does **not** cleanly broadcast
  Sierra's computed study values (VWAP-SD, footprint delta). This is why Step 4 recomputes.

## Step 4 — The ingestor (Python) — the real work

Connects to the DTC port, consumes the **raw** trade + depth stream, and **recomputes our
exact canon features in Python**. This guarantees parity by construction — we own the math
end to end — instead of trusting that Sierra's VWAP/CVD definitions happen to match ours
(they don't by default; the repo already documents that a naive CVD is the *negative* of
ours).

Responsibilities:
- **Maintain rolling state continuously**: footprint minutes (`fp_minutes` equivalent),
  session VWAP + bands, per-minute depth snapshots, session CVDs (overnight / Asia / PM /
  London), overnight range, trigger log. This is live state, not a file rewritten every
  few seconds.
- **On a trigger/fill candidate** (a limit-retest setup at a level), build that trade's
  feature row with the same definitions as `scripts/trade_matrix.py` (NY) /
  `scripts/london_matrix.py` + `scripts/london_depth.py` (London): `d15`, `fill_delta`,
  `ent_vs_vwap_sd_dir`, `dep_wall_*`, `cvd_ASIA`, `room_R`, `opp5`, etc.
- Hand that row to the router/brain (Step 5).
- Post-fill (NY books only): track `r_3` / `fw_3` for the 3-minute cut. London has **no**
  in-trade layer — nothing to track there.

Definitions must match the backtest exactly. When in doubt, copy the feature code verbatim
from the matrix scripts rather than re-deriving.

## Step 5 — Router + brain (Hermes)

**Two canon books, not one. Route by the clock, execute mechanically.**

- **Session router** picks the book by ET time, DST-aware:
  - pre-market window → `scripts/canon_mechanical.py` pre checks
  - golden window (~09:45–10:30 ET) → `canon_mechanical.py` gold checks + Q tier
  - London first-2h → `scripts/london_canon.py` (03:00–05:00 ET normally; **04:00–06:00
    during UK/US DST-misalignment weeks** — carry the `win_et` logic from the backtest)
- **Frozen thresholds.** Every quantile the canon uses (e.g. `d15` 2025-q25, `bbw` q75,
  London `room_R` 2.48/9.56, `cvd_ASIA` −748) must be **baked constants loaded from a
  config**, not recomputed live. The scripts currently derive quantiles from the 2025 slice
  of the backtest at load — that has to be extracted into a frozen thresholds file for
  production. (This is the first thing to build; see punch list.)
- **Decision is pure lookup:** compute the book's checks → score → OF stack / Q tier →
  size. Score/size ladders differ per book (NY tops at score 5; London at 4). No LLM
  judgment anywhere in the path — agents route and relay, they never re-derive or veto
  beyond the canon's own rules (ruled in the desk spec).

## Step 6 — Execution: limit brackets, not market orders

- **Read NQ, route MNQ (Angus ruling — the sizing depends on it).** The canon features
  (depth, walls, CVD, footprint) are computed on the **full E-mini NQ** ($20/pt) — the liquid
  book the wall checks need. But orders route in **MNQ** (Micro, $2/pt), because the
  dollar-risk sizing is in MNQ micros: `contracts = risk_$ / (stop_pts × $2)`. NQ at $20/pt is
  too coarse for the $200/$300/$400 risk steps. Prices track 1:1 (NQ and MNQ are the same
  index) — so the engine reads **NQ** depth/trades to compute the verdict + `entry_ref`/stop/
  target, then submits **MNQ** limit brackets at those exact prices. Front month e.g.
  `NQU26` (data) / `MNQU26` (orders). Sierra must have NQ subscribed for data AND MNQ routable
  for orders.
- **Contract rollover (Route B).** The front month rolls on the CME quarterly cycle — **4
  calendar days before the 3rd Friday** of the contract month (box Rollover Method). NQU26
  rolls to **NQZ26 on ~Sep 14, 2026**, inside the paper window. Sierra then writes a *new*
  file (`NQZ26-CME.scid`/`.depth`) and stops appending to the old one, so a file-tail feed
  pinned to the old path goes **silently stale**. `src/canon/sierra_symbol.py` resolves the
  active front-month symbol/file for a date (`resolve_scid_path`/`resolve_depth_path`) and a
  `RollWatcher` detects the switch. **Wired:** the Route-B live loop
  (`src/live/route_b.RouteBLive`, driven by `paper_run` `feed.type: sierra`) re-points the
  `.scid` at the roll and the `.depth` every session (per-day file) via `resolve_*_path`, and
  fires `format_roll_alert` over Telegram.
- **Live roll TAG (`RollTagger`/`RollState`, the twin of `src/engine/data.tag_rolls`).** The
  backtest **spans** rolls — its `roll` column is diagnostic-only (consumed solely by
  `diagnostics.py` to partition roll-day trades; `snapshot.py`/level logic ignore it and
  compute prior-week H/L across the unspliced gap). So the live buffers **also span** (they are
  NOT trimmed at a roll) — trimming would diverge from the validated book and fail the fidelity
  gate. What the live path adds is the TAG: `RollState` marks the first post-roll bar, stamps
  `roll`/`contract` onto the champion journal (via `LiveRunner(ambient_extra=…)`) and the
  shadow `sizing.jsonl`, and journals a `roll` decision. `gate_report.py` §E then verifies the
  roll was tagged (E1), flags the §E clock-reset when roll-day trades exist (E2), and leaves
  roll-timing parity (calendar-roll vs the backtest's volume-roll) for a reference date (E3).
  Net: a rollover inside the paper window is now **detected and reset mechanically** (§E),
  span-preserving, rather than silently spanning untracked.
- Entries are **limit retests** — the entire canon was validated on limit fills at the
  retest level. Send a **limit order at the computed `entry_ref`**, bracketed with the
  stop and target, via DTC `SubmitNewSingleOrder` (include `TradeAccount`, `Quantity`,
  `Price`). A market order takes a different price than the backtest assumed and bleeds a
  real fraction of the edge on a 9.5–14pt-stop book.
- Latency is irrelevant (minute-scale retests) — and keep order/modify chatter low so
  Lucid's HFT detector never looks at us.

---

## Cross-cutting requirements (missing from the original plan)

**A. Reconciliation day — the gate before any funded order.**
Point the ingestor at a historical day already in the repo and assert every feature
matches the backtest to the decimal (special attention to the CVD sign, the VWAP anchor,
and — since the feed is MBO — that our MBO→MBP-10 aggregation reproduces the Databento
MBP-10 depth the backtest scored on). Nothing goes live until this passes. This is the
single check that prevents a silent definition-mismatch from quietly un-tracking the
+$106k book.

> **Feed-append latency floor (Route B — file-tail path).** Because the live DATA path
> reads the files Sierra writes to disk (Route B; DTC won't serve data under the non-pro
> licence), there is a **write-latency floor with no backtest equivalent**: a bar's record
> is only readable once Sierra flushes it. On the box (SC build 2930) the
> **"Intraday File Flush Time in Milliseconds"** (Global Settings → Advanced Service
> Settings → General) was set to **`1000` (1 s)**; the Sierra default of **`0` means ~5 s**.
> The reconciliation day must therefore **measure observed file-append lag against this
> configured `1000 ms`**, not assume zero. `SierraFileFeed` instruments this per bar and
> emits a summary stat; the reconciliation-day gate carries the measured lag as a
> **reported line item** (we measure it, we do not "correct" for it). If the flush setting
> on the box changes, update this value so the gate compares against the real configuration.

**B. 24/5 continuous operation.**
The machine runs from 18:00 ET every session. London needs the full overnight
(`cvd_ASIA`, overnight range for `room_R`); NY-gold needs `AGE` and the ON range. This is
not a "start it at 3am" system.

**C. Comprehensive journaling (Angus mandate) + MBO capture.**
Every trade journals: session/book, every check bit AND its raw value, score, OF
confirmations, full size-multiplier path, fill/exit/exit_reason, MAE/MFE, in-trade marks
(`r_3`/`fw_3` for NY), ambient context (spread at fill, DST group, news-calendar state,
sweep state), and an engine-version + threshold-hash. PLUS the **raw MBO capture** in a
window around each trade (order-level book events: adds/modifies/cancels with IDs, so wall
composition, iceberg refresh, and pull/fade behaviour are reconstructable later). Purpose:
accumulate live data so recalibration runs on evidence, and build the MBO substrate for the
next campaign. Journal everything, gate nothing new — the MBO layer informs future
research, it never enters the live scoring path until a campaign earns it in.

**D. Python-side execution guards + sizer.**
- Mechanical spread/slippage cap before placing an order (relative, not a frozen absolute
  — London 2026 spreads regime-shifted). This is Python's job at order time, not an agent
  check.
- The dollar-risk sizer reads live account state (equity vs EOD line) and sets each order's
  contracts from a fixed $-at-risk per conviction tier (1.0=$200 … 2.25=$400 at floor, +$50/$1k
  available DD past $3k), contracts = risk_$/(stop_pts×$2), 40-micro clamp. Account
  state lives in Python — no agent gets P&L-based discretion.

---

## Software stack & costs (MBO from launch — Angus ruling)

The whole system is short because the funded account and Sierra each do double duty. The
chain: **Lucid Flex 50k** provides the Rithmic execution route + drawdown-of-record;
**Sierra Chart** connects to the CME data (Denali, for MBO), draws the order flow, and bridges
raw data + orders over DTC; **Python** (Pat's build) recomputes every feature, routes,
sizes, guards, and journals; the **agent layer** routes/executes/journals with no LLM in the
trade path.

| # | Component | Role | Cost |
|---|---|---|---|
| 1 | **Lucid Flex 50k** | Execution route (Rithmic) + drawdown-of-record. Rithmic execution connection is **free** with the account. | eval ~$100–165 (monthly until passed) + one-time activation |
| 2 | **Sierra Chart** (trading package) | Feed bridge, order router, DOM, order-flow charting. Must be the tier with **DTC Server + order routing + full DOM depth**. | ~$36–56/mo |
| 3 | **Sierra Denali CME data — MBO** | The market-by-order feed, **from launch**. Single source, dual purpose: aggregate → MBP-10 for live scoring; retain raw MBO for the journal/research substrate. | ~$40/mo (non-pro CME) |
| 4 | **R\|Trader Pro** | One-time CME non-pro data-agreement signup; then check the firm's drawdown. | free |
| 5 | **24/5 machine** (Windows) | Runs Sierra + Python + agents continuously (needs the full overnight for London Asia-CVD / ON range). Own always-on PC, or a Windows trading VPS. | $0, or ~$25–50/mo VPS |
| 6 | **Python stack** | Ingestor, feature library, router, dollar-risk sizer, safety spine, journaler. | free |
| 7 | **Agent runtime** | Mechanical trade path (free compute). Optional Claude Agent SDK for orchestration/journaling — not per-tick, so a small API cost at most. | ~$0–50/mo |

**All-in: ~$90–145/month** (own always-on PC → toward the low end; Windows VPS → high end),
on top of the funded-account cost.

**Why MBO from day one (not deferred):** every forward trade is journaled with full
order-book *composition* — a big wall that HOLDS vs one that VANISHES, iceberg refresh,
orders pulling as price approaches — all invisible to MBP-10. That is a direct upgrade to our
single strongest signal (depth/walls). Capturing it from the first live day means we
accumulate the forward substrate to run a full campaign on it in months, not years. It never
enters the live scoring path until a campaign earns it in; until then it's pure research fuel.

**Data-vs-execution split:** Denali provides the *data* (MBO); Rithmic remains the *execution*
route and the firm's drawdown-of-record. Sierra runs data and trade connections from different
sources — a standard setup. The reconciliation day (Cross-cutting A) must prove our MBO→MBP-10
aggregation reproduces the Databento MBP-10 the backtest scored on.

**Verify at signup:** the Sierra package tier includes DTC Server + Rithmic order routing +
full 10-level DOM; the Denali CME subscription includes true order-by-order MBO (not just DOM);
and the funded Rithmic execution plan isn't depth-restricted.

---

## Build punch list (order of operations)

1. **Freeze thresholds** — extract every `.quantile()` in both canon scripts into
   `config/live_thresholds.json`; make the scorers load constants.
2. **Feature library parity** — factor the matrix feature code so the same functions serve
   backtest and live ingestor.
3. **Ingestor** — DTC raw-feed consumer + rolling state + trigger detection + feature row.
4. **Reconciliation script** — replay a historical day, assert decimal parity. GATE.
5. **Router + scorer** — session/DST routing → book → frozen-threshold score → size.
6. **Execution** — limit-bracket order builder over DTC; spread guard; buffer sizer.
7. **Journaler** — write the full per-trade record.
8. **Paper/parallel run** — run live-shadow against the funded eval account before sizing up.

Nothing here is a dead end; the stack is sound. The corrections are: recompute features in
Python (don't trust Sierra's studies), place limit brackets (not market), freeze the
thresholds, route two books with DST, run 24/5, journal everything, and gate on the
reconciliation day.
