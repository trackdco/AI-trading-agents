# Launch Runbook — zero to live, on the VPS

From "Pat pushed Hermes + subagents to GitHub" to "one Lucid Flex 50k trading live, with the
desk on the VPS." Two hard gates in the middle — nothing goes live until both are green.

Reference docs: `LIVE-STACK.md` (stack), `SAFETY-SPINE.md` (guardrails + sizing),
`DESK-EVENTS.md` (dashboard contract), `desk-hud.html` (dashboard look),
`scripts/parity_harness.py` + `output/baseline_book.parquet` (the acceptance gate).

---

## Phase 1 — Buy the stack (verify before you pay)

Order matters: prove the depth feed exists before spending on the rest.

1. **Lucid Flex 50k eval** — choose the **Rithmic** connection option (not Tradovate).  ~$100–165 (monthly until passed) + activation on funding.
2. **R\|Trader Pro** (free) — download, log in once, sign the CME **non-professional** data agreement. **VERIFY NOW:** the funded Rithmic plan includes full **10-level DOM depth**. Our wall/depth checks are a top-2 signal in every book and die without it. If depth is restricted, stop and sort it before buying anything else.
3. **CNS Windows VPS** (Chicago / Aurora) — ~4 vCPU / 8 GB / 100 GB+ SSD.  ~$50–65/mo.
4. **Sierra Chart** — the **trading package** (must include DTC Server + order routing + full DOM).  ~$36–56/mo.
5. **Sierra Denali CME data with MBO** — **VERIFY** it's true order-by-order MBO, not just DOM.  ~$40/mo.
6. **Backblaze B2** (or Wasabi) bucket — nightly raw-MBO offload.  ~$5–10/mo.

All-in ≈ **$135–170/mo** + the funded account. (Runs on the Mac? No — all this lives on the VPS; the Mac is just the remote screen.)

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
15. **Parity harness** — replay Pat's agents over **Jun 2025 → Jul 2026** and diff the book they produce against the frozen baseline:
    ```
    python -m scripts.parity_harness agent_replay.parquet
    ```
    Must be an exact **PASS** — 400 trades, **+$56,065**, every conviction/stop/micro/P&L matching `baseline_book.parquet`. This proves the agents ARE the validated edge, not a lucky look-alike. Any MISSING/EXTRA/MISMATCH → Pat fixes, re-run. **GATE.**

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
