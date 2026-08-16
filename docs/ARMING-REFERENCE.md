# ARMING REFERENCE — rebuilt canon, NY pre-market + golden window

**Status: NOT ARMED. This document does not arm anything.** Arming requires Angus's token
against a certified commit (`src/live/arming.py`, two-party). What follows is the package
that has to be signed off *before* that step, plus an explicit list of what is still
unwired — read §5 before deciding anything.

> **UPDATED 2026-07-31 (was stale — Pat caught it).** Since this doc was first written the
> canon shipped THREE execution rulings (close-and-reverse J / two-session pre-flatten K /
> one-per-level L), the AGENT MANAGEMENT LAYER (row M), and the sizing base moved
> **$150 → $160** (row N). Rows I–N of `docs/HANDOVER-pat-arming.md` §3 are LAW and part
> of this sign-off package. All reference numbers below are refreshed to the three-rule
> canon at the $160 base; anything citing $90,015/$56,409 or a $150 base was the pre-rules
> book and must not be certified against.

Companion docs: `docs/CANON.md` (what the canon is), `scripts/funded_book.py` docstring
(the spec), `docs/CANON-QA-LOG.md` (why each rule exists), `docs/HANDOVER-pat-arming.md`
(rows I–N + the agent layer arming detail), `docs/REPORT-desk-run-2.md` (agent-layer grading).

---

## 1. What will run

| Layer | Module | Rule |
|---|---|---|
| Decision | `src/canon/scorer_ny.py::NYScorerV2` | pre 08:00–09:30 `W==1` · gold 09:40–10:30 `D==1` + wall-quality cut · risk 7–60pt |
| Scores | same | gold `2D+Tc+AGE+TRIG+T2` · pre `2W+G+F` (frozen; thresholds read from `config/live_thresholds.json`, never restated) |
| Tiers | same | gold ≤3→0.5 / 4→1.0 / ≥5→1.5 · pre 2→0.5 / 3→1.0 / 4→1.5 · **elite 2.0x** gold & TRIG & LONSLOPE & `struct_event=="broke"`, max 1/day |
| Budget | same | realized losses + in-flight risk + new risk ≤ budget · budget = base × 16/3 · soft de-risk at −35% of budget · half size below $1k buffer |
| Sizing | `src/canon/gate_evidence.py` | imports the profile from the scorer — one implementation, no drift |
| Order life | `src/canon/order_watch.py` | **no distance cancel**; each order dies at its own session end; struct event tracked bar-by-bar |
| Backstops | `src/live/risk.py`, `src/canon/spine.py` | account-level, above the canon budget (§3) |

Profiles: **`lucid`** (base $160 → $80/160/240/320, budget $853.33) and **`scaled600`**
(base $160 +$75 per $2k of buffer past +$3k, cap $600; budget and soft scale with the
base). Base $150 → $160 ANGUS 2026-07-31 (row N of the handover).

---

## 2. Conformance evidence

`tests/test_canon_scorer_ny.py` — 18 tests, all passing. The live scorer is driven through
the real protocol (`start_day` / `evaluate` / `commit` / `on_exit`) over every row of
`output/aikido_{fit,holdout}.parquet` and must match `scripts/funded_book.py` **exactly**:
same trades, same tier, same risk dollars, same micros, same P&L, on both spans and both
profiles.

The check is strong because the scorer **re-derives** every gate from raw depth/flow columns
rather than reading the parquet's precomputed `valid` / `gold_score` / `pre_score`. Agreement
therefore proves the live re-derivation of W, D, the wall-quality cut, the scores and the
tiers — not merely the arithmetic downstream of them.

Reproduced from the live path (three-rule canon, base $160): fit **+$82,543**, holdout
**+$48,211** (lucid). The suite also pins the CR overlay replay (suppressed rows dropped,
flip/pre-flatten exits merged) and the $160 tier ladders, spine halts and ramp floors.

### Two defects this conformance work found

1. **`funded_book.load_book` sorted with an unstable sort.** Same-minute fills are common
   (sibling triggers off one cluster) and pandas' default quicksort ordered those ties
   arbitrarily — which silently decided *which* trade of a tied group received the day's
   single elite 2.0x slot. Fixed to a stable sort (ties resolve to detection order, which is
   what the live feed sees). Effect: +$90 fit / +$1 holdout on lucid, +$512 / +$1 on
   scaled600; **no risk metric moved at all** (worst day, maxDD, min buffer, green months all
   identical). The pre-fix figures $89,925 / $56,408 / $320,150 / $188,324 are superseded.
2. **Two thresholds were restated instead of read.** An early draft of the scorer hardcoded
   G at 0.107 (that is VWAPD's cut point, a different bit) and AGE at 3.0 (the real value is
   136.5). The conformance replay caught both immediately. The scorer now imports
   `scripts.live_thresholds.TH`, the same source the batch reads.

---

## 3. Behavioural changes vs the currently-deployed stack

Each of these is a live-visible change and is why this document exists.

| # | Change | Why | Risk if wrong |
|---|---|---|---|
| A | **Entries uncapped.** No 2/day slot, no nth-escalation, no day ladder, no governor, no cold trail. | The shared cap was the original defect; uncapped measured strictly better once the wall cut landed. | More trades/day than the old stack ever placed. Capacity is now the budget. |
| B | `RiskLimits.max_trades_per_day` default **3 → None**. | The old 3 was a backstop above a 2/day engine cap that no longer exists. Against a ~4/day book it would announce a halt on most days and stand the account down mid-session. | **This was the single most dangerous stale default.** |
| C | Spine `daily_loss_halt_r` **−4R → −8R**. | −4R against the base is *below* the canon's own daily budget (at the $160 base: −$640 vs $853.33) — an outer guard that front-runs the inner one truncates the measured book. −8R is exactly 1.5× the budget at every base, and tracks the base automatically ($−1,280 at $160). | A halt inside the budget silently trades a smaller book than the one validated. |
| D | **No distance cancel.** Orders live until their session window ends. | The 22pt `t_cancel` measured inverted: kept −0.180R, killed +0.015R. | Orders rest longer; more fills. |
| E | **The resting rule**: an order rests exactly while a fill right now would be admissible — dormant through the 09:30–09:40 gap, may revive in gold, hard-dropped at 10:30. | The book counts a pre trigger's gold fill as a GOLD trade, so a birth-window cutoff would remove measured trades. | `NYRunner` enforces it. |
| F | Gold window **09:40–10:30** (was 09:40–10:00); **no 09:55–10:00 dead zone**. | The rebuilt canon was validated without one. | — |
| G | Sizing base **$200 → $150**, ladder is now tier × base. **Superseded: $150 → $160** (ANGUS 2026-07-31, handover row N). | The $200 schedule belonged to the broken canon. | Every order size changes — certify against the $160 ladder ($80/160/240/320). |
| H | De-risk ladder near the line: **half size below $1,000 of buffer, half again below $500** (ANGUS 2026-07-30), instead of a linear taper to zero between $1,500 and $100. | Angus's ruling. Both steps are dormant across all 19 months at the $160 base (min buffer $1,642 fit / $1,698 holdout), so no measured number changes; the spine's $100 hard halt is the floor beneath them. | Resolved. |

---

## 4. Pre-arm gate checklist

| Gate | Requirement | State |
|---|---|---|
| R1 | Live scorer reproduces the shipped book on both spans, both profiles | ✅ 19/19 (three-rule overlay + $160 base pins) |
| R2 | Sizing schedule has exactly one implementation | ✅ `gate_evidence` imports the profile |
| R3 | No trade-count cap anywhere in the risk path | ✅ pinned by test |
| R4 | Account backstops sit above the canon budget | ✅ pinned by test, both profiles |
| R5 | No distance cancel by default | ✅ pinned in `order_watch` and `trade_lifecycle` |
| R6 | Micros never round to zero | ✅ |
| R7 | Absent `struct_event` never escalates size | ✅ |
| R8 | Full suite green | ⚠️ 739 pass, 2 fail — both long-standing and unrelated (`london_depth.DIR`, `build_ny_substrate.canon_config` attribute drift), confirmed failing before any of this work |
| R9 | Live LANE exists and reproduces the book on real days | ✅ `src/canon/ny_lane.py`, 25/25 fit days via `scripts/ny_lane_replay.py` |
| R10 | Depth parity HARNESS exists and is self-clean | ✅ `scripts/depth_parity.py` — 180 archive minutes via `DepthBook` and an MBO capture via `OrderBook`, both 100% gate agreement |
| R10b | Depth parity run against a REAL captured session | ✅ CLOSED (ANGUS 2026-07-31, relayed via Pat): capture 2026-07-29 at 93.06% vs the 88.12% same-day 500ms vendor self-skew floor, all bias checks clean — bar re-specced per `docs/REPORT-parity-2026-07-29.md` §6; any feed/config change REOPENS with a fresh capture + floor |
| R11 | Runner orchestration (detector → orders → lane, struct_event joined) | ✅ `src/live/ny_runner.py`, 16 tests — Pat wires four calls + action execution |
| R12 | Angus's token against a certified commit | ❌ yours to issue |
| R13 | Three-rule execution semantics enforced by the runner (handover rows J/K/L: close-and-reverse in one ticket · pre flat at 09:30 · one-per-level dedupe) | ✅ CLOSED 2026-08-01 — execution layer (`src/live/ny_execution.py`) certified via four on-box practice-day replays of 2026-07-31 (`docs/RUNBOOK-cert-saturday.md`): surfaced + fixed 100x bar scale, 1pm-ET day roll, tick-record aggregation, and the cancel/fill same-bar race (ny:20 — day-4 journal shows the fill surfaced and scratched flat). Bars paritied vs the reference on 2026-07-14 (100% identical H/L, 72=72 triggers). Residual arm-day pins stand: DTC `_entry_working` read-back on the first armed session; stacked-position stop verification is account-level (fails toward flat). |
| R14 | Checkout reproduces the $160-base references (this doc §2) — the suite FAILS on a $150 checkout by design | ⬜ run `pytest tests/test_canon_scorer_ny.py -q` on the arming checkout |
| R15a | **PHASE 1 — MECH-ONLY ARM** (ANGUS 2026-07-31, final ruling — supersedes the same-day "ship with agents now"): the first arm is the mechanical canon alone; certified book = $82,543 fit / $48,211 holdout references. The first live session(s) double as the DATA CAPTURE for phase 2: depth capture for R10b, plus recorded minute CVD + MBP-10 streams to wire and dry-run the agent briefings against. | ❌ Pat wires + certifies |
| R15b | **PHASE 2 — AGENT LAYER ON**: wire per handover §7 against the captured live feeds, certify with the dry-run day + agent kill-test, then switch on. Certified book becomes the $100,297 agent book. Switch-on is a BEHAVIOR CHANGE and re-runs the two-party step: fresh written confirmation from Pat + Angus's token re-committed against the new certified SHA. | ✅ CLOSED 2026-08-02 — commit `1364cb7`, `docs/RUNBOOK-cert-r15.md`: agents managed real trades on 2026-07-29 (one +0.26R on a flow-flip read where mech rode to −0.43R), kill-test murdered the agent process mid-trade 7/7 turns, trade completed mechanically. Authorization re-issued `f6b297e`. |
| R16 | **24/7 OPERATIONAL RESILIENCE** (2026-08-03 audit, after two armed sessions both found the order socket dead — DTC connection had no idle keepalive, so a quiet market let it die unnoticed for hours). Closes: DTC idle-keepalive (`DTCBroker.ensure_connected` now called every 10s independent of trading activity — the existing, already-tested reconnect logic was simply never wired to a cadence), market-calendar-aware stale guard (the loop no longer self-halts at the daily 17:00 ET maintenance break — that was the actual reason a human had to manually restart it every session), boot/reconnect position reconciliation (refuses to arm — or blocks new entries mid-session — if the broker disagrees with tracked state; never guesses a recovery), the arming lock scoped to one entrypoint (`entrypoint:` field — `canon_run.py` and `ny_run.py` shared the same lock; a phrase for one could arm the other on a different account), and trade-level Telegram alerts (placed/filled/closed/agent open+settle — previously infra-only). New burn-in tooling: `scripts/dtc_connectivity_check.py` (hours-long, order-submission-code-never-imported, proves the reconnect survives real idle time against the real DTC server — the exact condition no replay can produce) and `scripts/watchdog.ps1` (crash/reboot auto-restart, respects the KILL file absolutely, crash-loop capped). 62 new/updated tests, 836 passed full suite. | ⬜ burn-in + fresh replay cert required before next arm — `docs/RUNBOOK-burnin-r16.md` |

---

## 5. What is NOT done

### 5.1 Depth parity — harness done, one real capture still needed

`src/canon/ny_lane.py` now runs the whole chain — real bars and tape streamed through
`CanonIngestor`, features assembled by the live code, scored by `NYScorerV2` — and
`scripts/ny_lane_replay.py` reproduces the shipped book on **25 of 25** fit days.

But replay feeds the depth family from the **batch archive**, because `ReplaySource` never
calls `on_depth` and the archive is per-snapshot CSVs rather than an event stream. In
production, `dep_thick` / `dep_wall_*` come from Sierra's `.depth` files through
`DepthBook.long_form()` — **a path no test compares against the archive the canon was
measured on.**

That is not a nice-to-have. `W` (pre) and `D` (gold) are the *only* entry gates, plus the
wall-quality cut, and all three are pure depth features. If `long_form()` bins levels
differently, or carries a different price convention, or lags, then the live book quietly
becomes a different book — and it fails *silently*, because a wrong wall distance still
produces a plausible verdict.

**Now runnable:** `scripts/depth_parity.py` builds the book from a captured session and diffs
every canon depth GATE (W, D, WALLSZ, the wall-quality cut) plus the underlying wall distances
and sizes against the archive, per minute and per direction. It is self-clean on 180 archive
minutes through `DepthBook`, and an MBO capture through `OrderBook` also lands at 100% — so
ANGUS is right that MBO is not a problem, and that is now demonstrated rather than assumed.

What remains is feed-specific and cannot be faked offline: one real captured session, to catch
units, tick alignment and timing. Pat's runbook: `docs/HANDOVER-pat-arming.md` §4.

### 5.2 RESOLVED — `NYRunner` is the per-candidate orchestrator

`src/live/ny_runner.py` joins detector → orders (OrderWatch) → lane (NYLane) per closed bar,
including the struct_event join, so the elite 2.0x fires. It decides and never touches a
broker: every output is an action (`place`/`cancel`/`modify_size`/`scratch`) the executing
loop runs through the spine. The old day-batch `_load_verdicts` path in `route_b` remains for
the OLD canon only and must not carry the new one. What remains for Pat is executing those
actions and honouring the scratch contract — `docs/HANDOVER-pat-arming.md` §4.3.

### 5.3 RESOLVED — struct_event joined inside the runner

The order's observed structural event feeds the fill-minute verdict; a scratched elite fill
leaves the day's 2.0x slot available (commit is what spends it). Pinned by tests.

### 5.4 Risk must be taken from the bracket as PLACED, not from trigger levels

Found while building the replay: `|entry − stop|` disagrees with the risk the canon actually
sized on for **28% of validated trades** (by up to tens of points), because `entry`/`stop`
are the trigger's reference levels while the canon used the engine's realized bracket
(`limit_price` vs `stop_initial`). Risk drives *both* the 7–60pt gate and the micros count.

`NYLane.on_candidate(..., risk_pts=...)` now takes it explicitly and records
`risk_source="explicit"|"bracket"` on every verdict. **Whatever places the live bracket must
place the same stop the engine would have**, or both the gate and the sizing shift. That
engine-vs-live stop parity is unproven and belongs with §5.1.

### 5.6 RESOLVED — the de-risk ladder near the line

ANGUS 2026-07-30: **half size from $1,000 of remaining drawdown, half again from $500.**
Implemented as `scorer_ny.RAMP_STEPS`, checked tightest-step-first, with one implementation
shared by the scorer, the book and the spine's sizing check. Both steps are dormant across
all 19 months of history, so every reference number is unchanged — verified.

### 5.5 London

Still the old canon, still Brake's rebuild. `LondonScorer` is untouched and must not be
armed. If the live stack would trade London, it stays disarmed until Brake's book lands.

---

## 6. Arming procedure (unchanged, for reference)

1. Pat confirms in writing, per PROMOTION-GATE.
2. Angus commits `config/arming.yaml` with the token SHA-256, the certified commit, and the
   account string.
3. On the box: `canon_run --arm`, present the phrase.
4. `verify_for_arming` enforces that HEAD *is* the certified commit (or differs only in
   `config/arming.yaml`). Any other file in that diff refuses the arm.

Every check fails closed, and a refused arm never falls back to a shadow run.
