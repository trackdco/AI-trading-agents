# Launch Runbook — zero to live, on the VPS

From "Pat pushed Hermes + subagents to GitHub" to "one Lucid Flex 50k trading live, with the
desk on the VPS." Two hard gates in the middle — nothing goes live until both are green.

Reference docs: `LIVE-STACK.md` (stack), `SAFETY-SPINE.md` (guardrails + sizing),
`DESK-EVENTS.md` (dashboard contract), `desk-hud.html` (dashboard look),
`scripts/parity_harness.py` + `output/baseline_book.parquet` (the acceptance gate).

---

## Phase 1 — Buy the stack (verify before you pay)

Order matters: prove the depth feed exists before spending on the rest.

1. **Lucid Flex 50k eval** — at "Select Platform" choose the **Rithmic Data Feed** (NOT CQG). Sierra Chart is on Lucid's **Rithmic** supported list (confirmed: MotiveWave, Quantower, Tradesea, **Sierra Chart**, Jigsaw, Bookmap, ATAS, R\|Trader Pro, MultiCharts — "all work with all account types"). CQG only carries NinjaTrader/Tradovate/TradingView, so Sierra requires the Rithmic feed.  ~$100–165 (monthly until passed) + activation on funding.
2. **R\|Trader Pro** (free) — download, log in once, sign the CME **non-professional** data agreement. **VERIFY NOW:** the funded Rithmic plan includes full **10-level DOM depth**. Our wall/depth checks are a top-2 signal in every book and die without it. If depth is restricted, stop and sort it before buying anything else.
3. **ChartVPS — Alpha Mark-2** (Windows, Ryzen 9 9950X, **3 cores / 8GB DDR5 / 256GB Gen4 NVMe**). The 8GB removes the RAM tightness that a 4GB box (CNS Value/Standard, ChartVPS Mark-1) hits under Sierra + Python + MBO. Confirm **Chicago/US-central location** + Sierra/Rithmic support at signup.  **$80/mo ($880/yr = ~$73/mo).**
4. **Sierra Chart** — the **trading package** (must include DTC Server + order routing + full DOM).  ~$36–56/mo.
5. **Sierra Denali CME data with MBO** — **OPTIONAL / research only** (see below). **VERIFY** it's true order-by-order MBO, not just DOM.  ~$40/mo.
6. **Backblaze B2** (or Wasabi) bucket — nightly **.depth + .scid** offload (`scripts/archive_sierra.py`, repointed from the old raw-MBO offload). **REQUIRED before paper starts, not optional:** the feed is MBP-10 (no raw MBO to capture) and Sierra retains historical **.depth only ~30 days** — once a day's file ages out it **cannot be re-downloaded**, so during paper this is the ONLY durable copy of the live book. Register the nightly Windows task once: `python scripts/archive_sierra.py --register`.  ~$5–10/mo.

All-in ≈ **$95–125/mo** on the included feed, or **$135–170/mo** with the MBO research add-on, + the funded account. (Runs on the Mac? No — all this lives on the VPS; the Mac is just the remote screen.)

**What the strategy needs vs. what's optional — the data picture:**
- **Lucid's account includes the Rithmic data feed** (real-time CME + **DOM depth / MBP-10**). The canon scores on MBP-10, so **this included feed runs the entire strategy** — no separate data purchase required for trading.
- **Sierra** connects to Rithmic for **both data and order routing**, and re-serves the raw feed to our engine over DTC. It's the bridge/router, not a data source. Our dashboard heatmap is drawn by *our* ingestor from that DTC depth.
- **Denali MBO (#5) is the only optional line.** Note: **"Denali" is Sierra's own market-data feed** — so MBO *does* come from Sierra, but as a **data subscription (~$40/mo) separate from the Sierra software package (#4).** Rithmic's funded feed gives aggregated DOM, *not* order-by-order MBO; Sierra's Denali is how you get true MBO, purely for the **journal/research substrate** (Angus's day-one choice). Sierra can run **Denali for data + Rithmic for execution** simultaneously. Drop Denali and the strategy is unaffected — you just stop accumulating the deeper-depth research data.
- **VERIFY at signup:** Lucid's Rithmic plan includes full **10-level DOM** (not throttled to top-of-book — our wall checks need the ladder), and whether they cover the CME non-pro data fee (~$16/mo) or pass it through.

---

## Cost summary (1 account)

**Recurring monthly — the live stack:**

| Item | Required? | $/mo |
|---|---|---|
| **ChartVPS Alpha Mark-2** (Ryzen 9 9950X, 3 core / 8GB / 256GB NVMe) | ✅ required | $80 ($73 annual) |
| **Sierra Chart — pick ONE package:** | | |
| &nbsp;&nbsp;• Pkg 5 Base Advanced (no MBO; data from Lucid Rithmic) | option A | $36 ($23.4 annual) |
| &nbsp;&nbsp;• **Pkg 12 Integrated Advanced MBO** (software + Denali data + MBO, all-in) | **option B (your plan)** | $56 ($36.40 annual) |
| Data feed for the strategy | ✅ required | **$0** on Pkg 5 (Lucid's Rithmic) / **bundled** in Pkg 12 |
| CME non-pro exchange fee | maybe | ~$16 (covered by Lucid on Rithmic path; on top of Denali — verify) |
| Backblaze B2 (MBO offload) | ⭕ optional (only with Pkg 12/MBO) | $5–10 |
| Lovable (if used for the dashboard) | ⭕ optional | $0–25 (self-host = $0) |

*Note: Sierra Pkg 12 already includes the Denali MBO data — there is NO separate ~$40 Denali line. "Integrated" = data bundled. Execution still routes via Rithmic to Lucid.*

**Funded account — Lucid Flex 50k (VERIFY exact numbers + discount codes at checkout):**

| Item | When | est. |
|---|---|---|
| Eval fee | upfront (one-time or monthly until passed) | ~$130–165 |
| Activation fee | once, on funding | ~$100–140 |
| Funded account monthly | after funding | usually $0 / small |

**Free:** R\|Trader Pro · Microsoft Remote Desktop (Mac) · Python · self-hosted dashboard.

**Two totals** (ChartVPS Mark-2 $80):
- **Minimum to trade** (Pkg 5, DOM only, data from Lucid): $80 VPS + $36 Sierra = **~$116/mo** + the account.
- **With MBO research** (your day-one plan, Pkg 12): $80 VPS + $56 Sierra Pkg 12 + ~$8 Backblaze (+~$16 CME) = **~$144–160/mo** + the account. On annual pricing (VPS ~$73, Pkg 12 ~$36.40), closer to **~$125–135/mo**.

**Month-1 out-of-pocket to get running:** ~$130–165 eval + the infra (~$116 min / ~$144–160 with MBO) ≈ **~$245–325 to start**, then the monthly stack once funded, plus the one-time ~$100–140 activation when you pass.

**At scale (5 accounts):** the infra (VPS + Sierra + Denali) is **shared** — one VPS runs all five copy-traded accounts, so it does *not* 5×. Only the **account fees** multiply (5 evals + 5 activations). Your recurring stack stays ~$130–170/mo total whether it's 1 account or 5.

---

## Phase 2 — Stand up the VPS

7. Spin up the CNS VPS. From your **Mac**, install **Microsoft Remote Desktop** (free, App Store) and RDP into it. This is how you'll see/control the Windows side.
8. Install **Sierra Chart** on the VPS. Configure two connections:
   - **Data = Denali (MBO)** — the feed the canon scores on (aggregated to MBP-10) + raw MBO for the journal.
   - **Trade = Rithmic** — order routing + the firm's drawdown-of-record.
9. Sierra → settings → enable **DTC Protocol Server** (e.g. `127.0.0.1:11099`).
10. Install **Python 3.11+** and **git** on the VPS.
11. VPS hygiene: set it to **never sleep**, auto-login, auto-restart Sierra + the engine on boot. It runs **24/5** (London needs the full overnight; NY-gold needs the overnight range).

---

## Phase 3 — Get the code on the VPS and build the engine

12. `git clone` **Pat's agents repo** (Hermes + subagents) and **this repo** onto the VPS.
13. Work the build punch list (from `LIVE-STACK.md`). Most is Pat's; the canon pieces are specified here:
    - **a. Freeze thresholds** → `config/live_thresholds.json`. Extract every `.quantile()` in `canon_mechanical.py` and `london_canon.py` into frozen constants (2025-derived). The scorers load constants, never recompute live.
    - **b. Feature-library parity** — the same feature functions serve backtest and live ingestor (copy from the matrix scripts verbatim; don't re-derive).
    - **c. Ingestor** — consume the DTC raw feed, maintain rolling state (footprint minutes, VWAP+bands, session CVDs, depth snapshots, overnight range), build the trade-candidate feature row.
    - **d. Router + scorer** — session/DST routing → book → frozen-threshold score → **dollar-risk size** (base $200, +$75/$1k available DD past $3k, 40-micro clamp; `SAFETY-SPINE.md`).
    - **e. Execution** — **limit brackets** at `entry_ref` via DTC (never market).
    - **f. Safety spine** — Tier-1/2/3 from `SAFETY-SPINE.md` (available-DD halt, daily-loss halt, contract clamp, parity gate, feed/spread/rate guards, fail-closed, watchdog, kill switch).
    - **g. Journaler** — full per-trade record (every bit + raw value, size path, exit, MAE/MFE, ambient, engine-version + threshold-hash) to **Parquet/DuckDB**, plus **raw MBO window** capture → nightly to Backblaze.

---

## Phase 4 — THE TWO GATES (nothing live until both are green)

14. **Reconciliation day** — point the ingestor at a historical day already in the repo and assert **every feature matches the backtest to the decimal**: CVD sign, VWAP anchor, and that our **MBO→MBP-10 aggregation reproduces the Databento MBP-10** the backtest scored on. If it fails, the thresholds are meaningless — fix before proceeding. **GATE.**
15. **Parity harness** — replay Pat's agents and diff their book against the frozen baseline.
    **This needs NO VPS and NO live feed** — it runs against the committed historical data, so
    run it **early** (the moment the agents can consume the repo's data, before buying hardware).
    Use a **staged, fail-fast ladder** — don't burn a full-year replay to find a week-2 divergence:
    ```
    python -m scripts.parity_harness agent_replay.parquet 2025-06-01 2025-06-07   # 1 week
    python -m scripts.parity_harness agent_replay.parquet 2025-06-01 2025-06-30   # 1 month
    python -m scripts.parity_harness agent_replay.parquet                          # full 2yr
    ```
    Each stage must be an exact **PASS** before widening; the full run must reproduce the
    **CURRENT ARMING REFERENCE — +$55,989.81 / 383 trades, `baseline_book_news.parquet`**
    (regenerate on the box: `python -m scripts.canon_news_clean`; see HEADLINE-NUMBERS.md —
    the +$56,065/400 and +$52,522/404 figures are superseded), every conviction/stop/micro/P&L
    matching exactly. This proves the
    agents ARE the validated edge, not a lucky look-alike. Any MISSING/EXTRA/MISMATCH → Pat fixes at
    the smallest failing window, re-run. **GATE.** (Because it's feed-independent, this gate can and
    should clear before Phase 1 — validate the agents, *then* buy the hardware.)

---

## Phase 5 — Make the VPS pretty (the desk)

16. **Event server** — Hermes emits the read-only WebSocket stream per `DESK-EVENTS.md` (FastAPI, `ws://localhost:8787/stream`, snapshot-on-connect).
17. **Dashboard UI** — build against `DESK-EVENTS.md` (the data) + `desk-hud.html` (the look):
    - **Self-host (your pick):** run the UI on the VPS next to the engine; open it in your **Mac browser** (or phone on the LAN). Nothing exposed publicly.
    - (Lovable is an option for a richer build + the chat — same event contract either way.)
18. **"Talk to Jarvis"** (optional) — a **read-only** Q&A layer over the journal + latest snapshot. It explains and reports; it **cannot** place, size, or alter a trade. Zero LLM in the trade path stays absolute.

---

## Phase 6 — Go live, safely, then scale

19. **Shadow/paper run** — run the live engine in shadow first: confirm it makes the same decisions live as the backtest for a few sessions, and **test every spine guard with a forced-bad input** (stale feed, wide spread, oversized order → all must halt/clamp/reject). Run the `SAFETY-SPINE.md` launch checklist.
20. **Pass the eval** — the canon does it mechanically. On funding, set Tier-1 constants to the confirmed Lucid numbers (EOD line, $2k DD, lock point, 40-micro cap).
21. **Live** — safety spine armed, dollar-risk sizing, **Build-6 withdrawals** (build to +$6k, take the $2k payout, keep the $4k cushion; 5 positive days ≥ +$150 between payouts). Watch it on the desk.
22. **Scale** — once one account is proven live, replicate to **5× Lucid Flex 50k** (max per login), copy-traded off the identical Hermes book. ~$48k/acct/yr → ~$240k across five.

---

## The critical path in one line

Buy (verify depth) → stand up VPS (Sierra: Denali data + Rithmic trade + DTC) → clone repos + build engine (freeze thresholds, ingestor, sizer, spine, journaler) → **reconciliation GATE** → **parity GATE** → wire the desk (event server + self-host UI) → shadow-test guards → pass eval → live with the spine → scale to 5.

**Do not skip the gates.** They are the difference between "we deployed the validated +$56k book" and "we deployed something that looks like it."
