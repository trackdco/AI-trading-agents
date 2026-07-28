# THE COMPLETE SYSTEM, FROM SCRATCH — every layer, every software, every connection

Written 2026-07-26 at Pat's request: "how would I build the complete system from scratch,"
designed around an ever-improving Hermes agent, with Obsidian as its memory, including the
Lucid funded accounts and VPS. Plain language; each layer says WHAT software, WHAT it does,
and HOW it connects to the next.

The one design law that shapes everything (ANGUS RULING 2026-07-26,
`docs/RULING-mechanical-only.md`): **agents discover, humans sign, constants trade.**
Hermes is everywhere EXCEPT inside the live trade path. The thing that places orders is a
frozen, certified rulebook; the thing that makes the rulebook better every week is the AI.

---

## Layer 0 — Money & ground: the accounts and the machine

| Piece | Software/vendor | What it does | Connects to |
|---|---|---|---|
| Funded account | **Lucid Trading — Flex 50k eval** (choose the **Rithmic** data feed at signup, NOT CQG) | The capital. Eval fee ~$100–165/mo until passed, then the funded account. One account first; the design scales to several later | Rithmic (its data+routing rails) |
| Data agreement | **R\|Trader Pro** (free) | Log in once, sign the CME **non-professional** agreement; verify the plan carries full 10-level DOM depth | Rithmic backend |
| The machine | **ChartVPS "Alpha Mark-2"** (Windows Server, ~$80/mo, **Chicago** location) | The always-on computer. Chicago = same metro as the CME servers, so data and orders travel milliseconds, not continents | Everything below runs ON it |
| Remote hands | **Remote Desktop** (built into Windows/Mac) | How a human looks at the VPS | — |

## Layer 1 — Ears: market data in, and its permanent record

| Piece | Software | What it does | Connects to |
|---|---|---|---|
| Chart/bridge | **Sierra Chart** (trading package, ~$36–56/mo) | Logs into Rithmic; receives every NQ tick + the 10-level order book; **writes them to disk continuously** (`.scid` tick file, `MarketDepthData/*.depth` per-day book files); also exposes the **DTC server** (the order door, Layer 4) | Rithmic in; local disk out; DTC to our bot |
| Historical data | **Databento** (pay-per-download) | The two years of NQ history (1-minute bars, order flow, MBO) the strategy was BUILT on. Research-side only | Feeds the backtest engine (Layer 2) |
| Optional research feed | **Sierra Denali MBO** (~$40/mo, optional) | True order-by-order data for deeper research. The strategy itself runs on MBP-10 and never needs it | Research archives |
| Cold storage | **Backblaze B2** (~$5/mo) + `scripts/archive_sierra.py` + Windows Task Scheduler | Nightly copy of the day's `.scid`/`.depth` to the cloud. Sierra deletes depth after ~30 days; this is the only durable copy — the raw material for all future Hermes research | Reads Sierra's disk; uploads to B2 |

**Key principle:** the live bot never talks to the exchange for data. It reads the files
Sierra writes (the "Route-B file tail") — simple, licence-clean, and replayable.

## Layer 2 — The lab: finding, improving, and backtesting the strategy

All Python (**pandas / pyarrow / pydantic / pytest**), all in one git repo (**GitHub**).
This layer is where a strategy comes FROM:

1. **Trigger detection** (`src/engine/triggers.py`) — scans bars for candidate setups
   (rejection blocks, displacement) with fixed geometric definitions.
2. **The backtest engine** (`src/backtest/engine.py::simulate`) — takes bars + triggers +
   a config and simulates fills, stops, partials, trails, cancels, EOD — the SAME code the
   live exit driver reuses, so backtest and live cannot drift apart.
3. **Feature matrices** — for every historical trade, compute the ~40 observations
   (tape/CVD, VWAP geometry, depth walls, session structure) into parquet tables.
4. **Screening + adversarial verification** — Hermes fans out study agents: screen dozens
   of candidate filters, then try to KILL each survivor (out-of-sample years, half-period
   splits, "is it one lucky fill?"). Most die. (Today's example: rr_floor looked like
   +38R, died under autopsy — one degenerate fill; retracted.)
5. **Freezing** — surviving thresholds go into `config/live_thresholds.json` as constants
   with provenance. No live code ever computes a quantile.
6. **The book** — run the frozen rulebook over both years → `canon_book.parquet` etc. The
   headline (today: **+$55,989.81 / 383 trades**) becomes the ARMING REFERENCE.
7. **Stress** — Monte Carlo of the funded-account rules (trailing drawdown, payouts) sizes
   the risk numbers (−4R daily halt, the DD ramp) with measured, not guessed, values.

## Layer 3 — The brain: the frozen strategy (the "canon")

| Piece | What it does |
|---|---|
| `scripts/canon_mechanical.py` + `scripts/london_canon.py` | THE rulebook: checks → score → size ladder → quality tier → escalations → governor. Deterministic; same inputs, same trades, forever |
| `src/canon/scorer.py` | The same rulebook re-stated one-trade-at-a-time for live, proven identical row-for-row against the books |
| Corrections stack | conf_PM look-ahead fix + pre-open news blackout + 09:55–10:00 dead zone — each an Angus ruling, each a frozen veto |
| Certification | `canon_news_clean` must reproduce the reference to the cent; `agent_replay --news` + `parity_harness --ref` must match **383/383**. Run on the VPS before arming; re-checked daily |

## Layer 4 — Hands + bodyguard: the live trade path (zero AI inside)

```
Sierra files → SierraFileFeed → CanonIngestor (live features)
     → verdicts (frozen scorer) → PremarketGuard (news/dead-zone vetoes)
     → SAFETY SPINE (halts, ramp, read-back, arming lock)
     → DTC client → Sierra DTC server → Rithmic → CME
fill → OrderWatch (engine-identical cancels) → ExitBinder → LiveExitExecutor
     (stop moves, partials, 3-min cut, EOD flatten — engine.py's own decisions)
```

The spine can only say NO: daily −4R halt, DD ramp ($1,500→$0 at $100 + hard halt),
stale-feed/spread/rate/duplicate blocks, protective-stop verification ("read back, never
trust"), fail-closed flatten on anything unprovable, kill file, and the **arming lock** —
no Angus token, no orders, structurally.

## Layer 5 — Mouth, leash, ops

| Piece | Software | What it does |
|---|---|---|
| Alerts + kill | **Telegram bot** (BotFather) | Every trade/halt to the shared group; `/kill` from Pat's AND Angus's phones (IDs allow-listed in `.env`) |
| News sentinel | `scripts/news_daily_agent.py` + Task Scheduler (01:30 CT daily) | Fetches the day's economic calendar; **no snapshot → no pre-market trades** (fail-closed) |
| Journals | JSONL files under `output/live/` | Every verdict, guard decision, veto, order, alert — the gate evidence AND Hermes's daily reading |
| Gates | `docs/PROMOTION-GATE.md` + force-test scripts | The full checklist proving correctness/execution/ops BEFORE arming, and the kill criteria after |

## Layer 6 — HERMES: the ever-improving intelligence, and Obsidian as its memory

Hermes is not one program — it's a **team of Claude agents** (Claude Code sessions on the
VPS/cloud) with distinct jobs, all reading and writing ONE shared memory.

**The memory: an Obsidian vault = this repo's `docs/` folder.**
- **Obsidian** (free) opens `C:\ai-trading-agents\docs` as a vault directly — every
  FINDING-, RULING-, STATUS-, HANDOFF- file is already a note. Add the **obsidian-git**
  community plugin and the vault syncs through the same GitHub repo the agents push to.
- Humans get the graph view (rulings link to findings link to studies), search, and daily
  notes. Agents get the same memory as plain markdown — no translation layer.
- Conventions that make it work: one file per finding/ruling; front-links (`[[RULING-…]]`);
  every number carries provenance (which study, which data, which date); superseded notes
  are marked, never deleted (the dead ends are as valuable as the wins).

**The Hermes roles (each is an agent session; several already ran today):**
1. **Journal auditor** (nightly) — reads the day's live journals, diffs live behavior vs
   the book (A1 daily re-check), flags anomalies to Telegram.
2. **Research analyst** (nightly/weekly) — re-runs the standing study harnesses over the
   growing live+historical record; hunts decay in existing edges and new candidate edges.
3. **Adversary** — every candidate finding gets an agent whose only job is to kill it
   (OOS, splits, degenerate-fill autopsies). Survivors become adoption memos.
4. **Memo writer** — drafts the adoption note in the vault: evidence, frozen threshold,
   expected book delta, holdout plan.
5. **The relay** (the ONLY agent near the trade path) — `relay_one = json.loads(raw)`:
   it passes verdict bytes through unchanged and is structurally incapable of computing.
   This is deliberate: it proves the "agents" in the loop cannot invent a trade.

**The improvement flywheel (ran five times today alone):**
```
live journals + archives → Hermes studies → adversarial verify → memo in the vault
    → Telegram ping → ANGUS/PAT sign → constant freezes → book regenerates
    → VPS re-certifies to the cent → new arming reference → better bot trades tomorrow
```
The human signature is one click — and it is the ONLY thing standing between "improves
weekly with an audit trail" and "unverifiable self-modifying money-loser." Keep the click.

## Layer 7 — Scaling (later): more accounts

Lucid allows multiple accounts; the design scales by running one spine/account with the
same certified brain, sized per-account by each account's own DD state. Not tonight's
problem; noted so the from-scratch picture is complete.

---

## Build order from zero (what actually happened, compressed)

1. **Data + lab first** (no money): Databento history → engine → triggers → matrices.
2. **Find the edge**: screen → verify → freeze → book → +$55,989.81/383 reference.
3. **Stress the account rules**: MC → −4R, DD ramp (measured, signed).
4. **Buy the stack**: Lucid eval (Rithmic) → ChartVPS Chicago → Sierra → B2.
5. **Deploy + certify on-box**: clone repo, 636 tests, pin file formats (expect to catch
   real bugs — we caught three), certify the book to the cent.
6. **Wire the ops**: Telegram (both operators), sentinel, nightly archive.
7. **Prove the gates**: feed lag, SIM order surface, force-tests, break-it drills, dual
   kill switch, overnight disarmed shadow.
8. **Sign + arm**: written confirmation → arming token naming the commit → funded, live.
9. **Loop forever**: Hermes studies nightly; adoptions ship through the flywheel.

## Monthly cost of the whole machine

| Item | $/mo |
|---|---|
| Lucid Flex 50k (until passed) | ~$100–165 |
| ChartVPS Alpha Mark-2 | ~$80 |
| Sierra Chart trading package | ~$36–56 |
| Backblaze B2 | ~$5 |
| Databento (research, as-needed) | variable |
| Denali MBO (optional research) | ~$40 |
| Claude (Hermes agents) | per plan |
