# HANDOFF — NQ Trading System ("the canon") — paste this into the new chat

**Date:** 2026-07-24 · **Repo:** `trackdco/AI-trading-agents` · **Branch:** `claude/getting-started-6lwnvs`
**HEAD:** `289c4a0` — Add DESK dashboard exporter (desk-export/v2)

Read this whole file first, then say "caught up" and wait for direction. Do NOT re-derive
decisions already made below — they're settled.

---

## 1. WHO / WHAT

- **Angus (Bar)** — owner, the trader. Knows order flow deeply, NOT infra/technical.
  Needs click-by-click hand-holding on servers/software. Gets (rightly) frustrated when
  steps are skipped or when given options instead of a recommendation. **Give one
  recommendation, not a menu.**
- **Brake (patbarbrake)** — helps on the VPS/Sierra side. Knows nothing about trading.
  Needs "explain like I'm five" steps.
- **Pat** — builds the engine/agents (his own repo + this one). Has his own Claude.

**The project:** a fully-mechanical three-window NQ intraday trading system. Core doctrines:
- **Consistency is king.** Zero LLM/discretion in the trade path.
- **Frozen 2025 thresholds**, minimum RR of 2.
- **Agents ADD, never subtract** — agents are pure relays of the Python canon.
- Comprehensive journaling.

---

## 2. THE CANON — validated baseline (DO NOT RECOMPUTE)

`output/baseline_book.parquet` = the frozen ground truth, **400 trades, +$56,065.18**,
2025-06-02 → 2026-07-10 (combined NY + LONDON books, every qualifying setup every day).

| Metric | Value |
|---|---|
| Total P&L | **+$56,065.18** |
| Trades | 400 (NY 264 / LONDON 136) |
| Win rate | 50.7% · Profit factor 2.78 · max DD $1,511 |
| 2025 | +$28,948.55 · 228t · WR 48.7% · PF 2.56 |
| 2026 | +$27,116.63 · 172t · WR 53.5% · PF 3.10 |
| NY | +$34,558.68 · 264t · WR 46.2% · PF 2.57 |
| LONDON | +$21,506.50 · 136t · WR 59.6% · PF 3.25 |
| Conviction tiers | 0.25→14 · 0.5→144 · 0.75→10 · 1.0→126 · 1.5→98 · 2.25→8 |
| Patterns | A→33 (+$2,438) · B→146 (+$27,236) · B2→221 (+$26,391) |
| Books | E3, E4 (both fire; on 35 days both same day — all included) |
| Trading days | 225 across 403 calendar days (SELECTIVE, ~4 trades/week) |

**PARITY STATUS: PASSED.** Pat's `scripts/agent_replay.py` reproduced the baseline
**400/400 exact, +$56,065.18**. Verified independently via `scripts/parity_harness.py`.
Agents are confirmed **pure relays** (`docs/desk-skills/canon/canon-relay.md` relays the
Python canon verdict verbatim), so decision+sizing parity is fully covered.

---

## 3. SIZING RULEBOOK (frozen — part of the baseline definition)

```
risk_$   = min($400, conviction × $200)          # 1.0=$200, 1.5=$300, 2.25=$400 cap
micros   = min(40, round(risk_$ / (stop_pts × $2)))   # MNQ micros, $2/pt, 40-clamp
pl       = micros × dollars_1lot / 10
```
**NEVER risk >$400/trade.** Stop-width-normalized: every trade of a tier risks the same dollars.

**Live DD-scaling overlay** (NOT part of frozen baseline):
`base_dollar(ad) = 200 + 75·floor((available_dd − 3000)/1000)` for ad>3000, 40-micro clamp.
(+$75 per $1k available DD — Angus found this the "sweet spot" via MC.)

**Read NQ, route MNQ:** canon features computed on full E-mini **NQ** ($20/pt, liquid depth);
orders route in **MNQ** micros ($2/pt) for granularity. Front month **NQU6 / MNQU6**.

**Account:** Lucid Flex 50k, **EOD drawdown** (not trailing). Line = min(0, max(prior,
EOD_bal − DD)); floor locks at $50k once balance hits $52k. **Build-6 payout policy:**
build to +$6k, withdraw $2k, keep $4k cushion; 5 positive days ≥+$150 between payouts.
~$48k/acct/yr; 5 accounts ≈ $240k/yr. MC bust risk 1.5% naked / 0.18% with spine.
**Verdict on account type: Lucid Flex/Standard, NOT Pro** (Pro's 40% consistency rule
throttles our book −23%).

---

## 4. INFRASTRUCTURE — CURRENT STATE (all of this is DONE)

| Piece | State |
|---|---|
| **VPS** | ChartVPS Alpha Mark-2, Windows Server, ~$80/mo — live, Angus+Brake have RDP |
| **Sierra Chart** | Installed on VPS. **Package 12 (Integrated Advanced MBO), $56/mo**, active until 2026-09-14. Account: `patbarbrake` |
| **Broker/exec** | Lucid Flex 50k **BOUGHT** (order #7347007, $98). Rithmic. Trading Username `LT-QJ26R3G6`, Server `LucidTrading-Chicago Area-Aggregated` |
| **Depth data** | **Lucid "Market Depth (FULL BUNDLE)" add-on, $27.30 — PURCHASED & WORKING** |
| **Depth confirmed** | Msg Log shows `MarketDepthIsSupported: 1` ✅ (was 0 before add-on) |
| **Chart** | Live, current, heatmap study ("Market Depth Historical Graph") added |
| **DTC server** | Enabled, **Listening: Yes**, port **11099** (realtime+orders), **11098** (historical), Allowed IPs = **Local Computer Only**, no auth, no TLS |
| **Allow Trading** | **No** — deliberate seatbelt until go-live. Does NOT block data reads. |
| **Denali/CME sub** | **DEACTIVATED ✅** (confirmed by Angus 24-Jul) — not billed, not used |

**Monthly run cost:** VPS $80 + Sierra Pkg12 $56 + Lucid depth ~$27 ≈ **$163/mo**.

### ⚠️ THE DATA-FEED SAGA — read so you don't repeat my mistakes

I made several wrong calls here. The resolution:
1. Lucid's base Rithmic plan has **NO depth** (`MarketDepthIsSupported: 0`).
2. I wrongly pushed Sierra's **Denali** feed. That path needs a **CME sub (~$40.50/mo
   non-pro)** AND — the killer — **non-pro pricing requires a real LIVE funded futures
   account**; **prop/eval accounts (Lucid, Apex, Topstep) do NOT count.** Sierra's
   "Easy Solution" = keep a dormant live broker acct, connect 10 sec/month. Angus
   (rightly) refused this as absurd overhead.
3. **Angus was right:** Lucid sells a **Market Depth add-on** ($13 CME-only / $27–39 full
   bundle) that just enables Level 2 on the Rithmic feed. Bought it → `MarketDepthIsSupported: 1`.
   **No Denali, no anchor account, no monthly ritual.**

**LESSON: I tunnel-visioned on the stack we'd built instead of surveying alternatives.
When Angus pushes back on a painful requirement, CHECK FOR A SIMPLER PATH before defending.**

### Sierra config detail (in case it needs redoing)
To use Denali for data you blank Rithmic's Market Data + Historical Data user/pass
(keeping Trading user/pass). **We UNDID this** — all four fields are refilled with
`LT-QJ26R3G6` + Rithmic password, because data now comes from Rithmic (with the depth add-on).

---

## 5. THE ENGINE READ PATH — changed to FILE-TAIL (important)

Pat's build hit trouble pulling live data over the DTC socket. **The plan pivoted to
reading Sierra's on-disk files directly** (`.scid` = tick/order-flow, `.depth` = ladder).
This is more robust and sidesteps socket/binding issues.

**Likely cause of the DTC failure (unconfirmed):** DTC is bound `127.0.0.1` + "Local
Computer Only", so **the engine MUST run ON the VPS.** A test from any other machine
gets connection-refused.

**File-tail delivers the SAME data** — Sierra writes these files from the same Rithmic
stream. Coverage:
- `.scid` records carry **BidVolume / AskVolume** per trade → this IS order flow → builds
  `cvd_*`, `fill_delta`, `absorption`, `delta_div`, `stacked_imb`, `d5/d15/d30`.
- `.depth` records rebuild the live **10-level ladder** → `dep_thick`, `dep_imb`,
  `dep_support/resist`, `dep_wall_above_*`, `dep_wall_below_*`.
- Only downside vs socket: a few ms latency — **irrelevant**, canon evaluates on closed
  1-min bars + a depth snapshot at the candidate fill.
- **MBO (order-by-order) is NOT available this way** — that's a future research
  enrichment only, NOT a canon requirement. Correctly deferred.

### Byte layouts to pin against (little-endian)
```
.scid   header 56B: "SCID" magic, HeaderSize=56, RecordSize=40, Version, UTCStartIndex
        record  40B  struct "<q 4f 4I":
          int64 SCDateTime (MICROSECONDS since 1899-12-30 UTC)
          float Open,High,Low,Close   (tick: all four = trade price)
          uint32 NumTrades, TotalVolume, BidVolume, AskVolume

.depth  header 64B: "SCDD" magic, HeaderSize=64, RecordSize=24, Version
        record  24B  struct "<q B B H f I I":
          int64 SCDateTime, uint8 Command, uint8 Flags, uint16 NumOrders,
          float Price, uint32 Quantity, uint32 Reserved
```
**Two constants most likely to need adjusting:** (a) SCDateTime unit/epoch — decoded first
record must land on TODAY, not 1899; (b) the `.depth` Command enum values vary by build —
verify against captured bytes.

### PowerShell to capture samples (run on VPS, Start → "powershell")
```powershell
$dst="$env:PUBLIC\Downloads"
$scid = Get-ChildItem "C:\SierraChart\Data\NQU6*.scid" | Sort LastWriteTime -desc | Select -First 1
$s=[IO.File]::OpenRead($scid.FullName); $b=New-Object byte[] 131072; $n=$s.Read($b,0,131072); $s.Close()
[IO.File]::WriteAllBytes("$dst\NQU6_scid_sample.bin", $b[0..($n-1)])
$depth = Get-ChildItem "C:\SierraChart\Data\*NQU6*.depth","C:\SierraChart\Data\MarketDepthData\*NQU6*.depth" -ErrorAction SilentlyContinue | Sort LastWriteTime -desc | Select -First 1
Copy-Item $depth.FullName "$dst\NQU6_depth_sample.depth"
Write-Host "SCID : $($scid.FullName)  ($($scid.Length) bytes, modified $($scid.LastWriteTime))"
Write-Host "DEPTH: $($depth.FullName)  (modified $($depth.LastWriteTime))"
```
First thing to check in the sample: **BidVolume/AskVolume non-zero** (proves CVD path real).

**NOTE:** this repo has NO `.scid`/`.depth` reader yet. `src/canon/ingestor.py` has the live
source as a seam (`<<LIVE DTC FEED>>`, not built). The reader lives in **Pat's repo**.
Offer to build it here against the ingestor seam if wanted.

---

## 6. GO-LIVE GATES (strict order, each must pass)

Angus decided: **SKIP the multi-week paper-trading period, go straight to running on the
funded eval.** But these gates stay — they're the seatbelt, not the paper period:

1. **Live data connected** — file-tail feed running on live NQU6, prices + full ladder flowing.
2. **Reconciliation day** — THE HARD GATE. Features from the live feed must match the
   backtest **to the decimal**. Thin depth or broken order flow fails loudly here, pre-money.
3. **Shadow run** — full system live, journals every decision, **places no orders**.
4. **Spine force-tests on live setup** — trip every safety rule, confirm each halts/rejects.
5. **Written promotion gate** (one page, agreed BEFORE first tick).
6. **Angus's arming token** — one action, once. Nothing places an order before this.

**Kill switch exists:** Telegram bot (Hermes) — flatten-all, and bypass/unauthorize entries.
Must be verified working before arming.

### The funded decision = FIDELITY audit, NOT P&L
~4 trades/week means a 2-week window is ~8 trades — pure noise (a faithful system can be
red; a broken one green by luck). Judge on:
selection (0 extra / 0 missed) · sizing (100% exact) · slippage (median ≤1 tick, max ≤3–4) ·
stops/exits · timing · spine trips correct · feature drift within tolerance.
Report P&L but explicitly **not** as a criterion.

---

## 7. OPEN ITEMS / NEXT ACTIONS

**Blocking-ish:**
1. ~~Deactivate Denali/CME trial~~ — **DONE ✅** (confirmed 24-Jul). No further action.
2. **Confirm depth is truly 10-level, not throttled** — open Trade DOM on NQU6 and count
   populated levels each side (want ~10). Or read it out of the `.depth` sample.
3. **Capture the `.scid`/`.depth` samples** (PowerShell above) → verify byte constants →
   replay through parity.
4. **Engine must run ON the VPS** (localhost-only binding).

**Non-blocking housekeeping:** close PR #9 · send `/status` to the bot · Angus DM the bot
so his `/kill` works · confirm max position size on a 50k account.

**In flight (Angus + Brake):** building **THE DESK** dashboard in **Lovable**. I gave them
a complete build prompt (saved as `THE-DESK-lovable-prompt.txt`) with the data contract,
14 seed trades, and the verified aggregates. They upload `output/desk-export.json` (400
trades) into it. **Possible next ask:** tighten the eval-survival panel to real Lucid 50k
EOD-drawdown mechanics.

**Also speced but not built:** update the desk HTML loader to accept `desk-export/v2`
(object with meta/trades/spine_events, backward-compat with bare `Trade[]`; pattern chips;
spine_events → SPINE station; meta → provenance strip).

---

## 8. KEY FILES

**Scripts:**
- `scripts/baseline_dollar_risk.py` — builds `output/baseline_book.parquet` (THE ground truth)
- `scripts/parity_harness.py` — the acceptance gate; `python -m scripts.parity_harness [candidate] [from] [to]`
- `scripts/agent_replay.py` — Pat's replay (passed 400/400)
- `scripts/export_dashboard.py` — **NEW** desk-export/v2 emitter → `output/desk-export.json`
- `scripts/canon_mechanical.py`, `scripts/london_canon.py` — the canon itself
- `scripts/mc_dollar_risk.py`, `mc_payout_cycles.py`, `mc_lucid_pro.py` — Monte Carlos

**Artifacts (committed, force-added past gitignore):**
`output/baseline_book.parquet` (400) · `trade_matrix.parquet` (970, NY) ·
`london_matrix.parquet` (749) · `fp_minutes.parquet` · `canon_book.parquet` ·
`london_canon_book.parquet` · `desk-export.json`

**Docs:** `SAFETY-SPINE.md` · `LIVE-STACK.md` · `LAUNCH-RUNBOOK.md` · `VPS-SETUP.md` ·
`PARITY-CHECK.md` · `DESK-EVENTS.md` (WebSocket event schema) · `desk-hud.html` (live HUD)

**Tests:** `tests/test_export_dashboard.py` (11 pass) + large existing suite.

---

## 9. HOW TO WORK WITH ANGUS (learned the hard way)

- **Recommend, don't enumerate.** He hates being handed a menu of options with no verdict.
- **One micro-step at a time** for anything technical/infra. Screenshot-driven. He'll say
  "you're skipping steps, I don't know these things" — believe him and slow down.
- **When he pushes back, he's usually right** — he caught me on MBO, on Rithmic depth,
  and on the Lucid depth add-on. **Search/verify before defending a position.**
- He may swear/get heated when frustrated. Don't get defensive, don't moralize — just fix
  the actual problem and own the miss plainly.
- Never say "fund the account" — **the Lucid funded/eval is already BOUGHT.**
- Skip paper-trading talk — decided: straight to the eval.

**Git:** develop + commit + push to `claude/getting-started-6lwnvs` (canonical, where
artifacts + Pat's work live). Push with `git push -u origin <branch>`; on rejection
`git pull --rebase origin <branch>` (Pat pushes concurrently). Don't open PRs unasked.
