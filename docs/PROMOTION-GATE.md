# ARMING GATE — what must be true before the executor is turned on

**Status:** numbers below are Angus's rulings unless marked `[ANGUS]`.
**Owner:** Angus (final say). Originally drafted by Pat as a paper→promotion gate;
**restructured 2026-07-26** for the decision in §0.
**Applies to:** NQ canon system, repo `trackdco/AI-trading-agents`, branch `claude/getting-started-6lwnvs`.

---

## 0. The decision: no paper period. The eval IS the test.

**Ruling (Angus, 2026-07-26):** we are not running a multi-week paper period. The stack is bought
and the Lucid Flex 50k eval is already paid for. The asymmetry decides it:

> If the bot is broken we lose **$100**. If it works, a two-week paper run costs us **two weeks of
> funded compounding**. Take the trade.

**What that does NOT change.** The canon fires ~3.8 trades/week. Fifteen or twenty-five trades were
never going to distinguish a working edge from a lucky one — a P&L gate at that sample size is
noise wearing the costume of a test. Nothing of value is lost by deleting the time-based
requirements, because they never tested the edge in the first place.

**What it DOES change.** Without a paper buffer, real money is exposed from trade one. So the
correctness gates get **stricter**, not looser, and the protective function a paper window used to
serve moves into **§D KILL CRITERIA** — continuous, automatic, no discretion.

The question this document answers:

> **Is the live plumbing provably doing what the backtested system did — and if it stops doing
> that at 03:00 on a Tuesday, does the bot stop itself?**

The edge is validated: the leakage-clean canon **plus the pre-open news blackout**
(`output/baseline_book_news.parquet`) is **+$55,617.56 over 386 trades** — the arming reference
(ANGUS 2026-07-26; `scripts/canon_news_clean.py`, `docs/FINDING-canon-has-no-news-blackout.md`).
The leakage-fix-only step was +$52,522.81 / 404. (The original **+$56,065.18 / 400** was
the *pre-lookahead-fix* figure; it was inflated ~$3.5k by a look-ahead in the pre-window `C`
check — `docs/FINDING-conf_PM-lookahead-pre-window.md` — and is retained only as that historical
baseline.) The edge survives the fix; only the plumbing is unproven.

---

## A. Correctness — pre-arming, all 100%, no tolerance

Every one of these is a **one-off check**, not a multi-week observation. There is no reason to wait.

| # | Gate | Pass condition |
|---|---|---|
| A1 | Feature parity | Live features == the **arming reference** (`baseline_book_news.parquet`) to the decimal on the reconciliation day, re-checked daily thereafter |
| A2 | Verdict fidelity | Every signal matches what the canon scorer produces on the same journaled inputs, **diffed against the arming reference**. Replayable |
| A3 | Relay integrity | `canon-relay` output == Python verdict, byte-for-byte. Zero divergences |
| A4 | No missed trades | Every candidate the canon would take is seen and acted on. Misses journaled with cause |
| A5 | Both books wired | NY **and** London paths both proven to fire — force a signal through each if needed |
| A6 | Journal completeness | Zero trades with missing/malformed journal records |
| **A7** | **Bracket integrity proven on the box** | **Submit one bracket, read back TWO distinct order IDs (entry + resting protective stop) with live status — the canon has no fixed target (managed exit), see note** |
| **A8** | **Roll alignment** | **RollWatcher's roll date == the backtest's volume-roll date (`docs/CONTRACT-ROLL-DATES.md`)** |

**Any A-failure is disqualifying, not a deduction.** One byte of divergence in A3 means the relay
computed something, and the "no LLM in the trade path" guarantee is void.

### A7 — do this one first

The bug is FIXED in code (2026-07-26): `submit_bracket()` used to send `"Stop"`/`"Target"` as
fields on `SUBMIT_NEW_SINGLE_ORDER` — **not DTC fields**, silently dropped → naked entries. It now
sends a parent entry + a **STOP child** carrying `ParentTriggerClientOrderID`, and
`spine._verify_readback` confirms the **protective stop is actually resting at the broker** (not
just that submit returned). The mock server now models real Sierra (drops unknown keys; asserts
parent+children). **A7 remains a hard ON-BOX gate:** submit one bracket against the live Sierra
DTC server and confirm **two distinct broker order IDs** come back (entry + resting stop) with live
status — the offline mock cannot prove the real Sierra accepts the linkage. The check is turnkey:
`scripts/dtc_surface_forcetest.py` (resting mode) submits one far-from-market bracket, prints the
two acknowledged order IDs with their ServerOrderIDs, and cancels it.

### A8 — the silent one

Databento (`NQ.v.0`, the backtest's data) rolls on **volume**: the Wednesday **2 days before
expiry**. Calendar rules roll 2–6 sessions earlier. In that gap live trades the back month while
the backtest scored the front — every level feature on a different instrument, separated by the
calendar spread. **A1 fails and nothing crashes.** Next roll ≈ **2026-09-16**.

## B. Execution — the part the backtest never modelled

| # | Gate | Pass condition |
|---|---|---|
| B1 | Fill vs intent | **Median 0 ticks on entries.** These are limits — you get your price or better. Any entry filled *worse* than the limit is a bug, not market movement. Stop-exit slippage tracked separately |
| B2 | No market orders **on ENTRIES** | Entries are limit-only. Zero, ever, structural. Exits **may** be marketable where the canon exits at the market (3-min cut, EOD flatten, stop-outs — Angus B1: those genuinely slip, tracked separately) |
| B3 | Rejection rate | Below **2%**, each rejection explained |
| B4 | Protective stop attached | Every entry has a **resting protective STOP** at the broker — the invariant that must never fail. The canon has **no fixed target** (managed exit), so stop-attachment is the thing verified. **Zero positions without a resting stop, any duration** (spine read-back + timer reconcile) |
| B5 | Sizing | Micros placed == dollar-risk schedule, every trade, exact |
| B6 | Feed lag characterised | Sierra file-flush lag **measured, not assumed**, written down as a number (`BOX-HANDOFF.md` Step B.2) |
| **B7** | **Working-order cancellation** | **A resting limit can be cancelled, and `cancel_if_runs_points` is enforced live — see `FINDING-live-path-cannot-cancel-a-resting-limit.md`** |
| **B8** | **Managed-exit order surface** | **A resting stop can be MODIFIED and a position PARTIALLY closed through the live path — the canon has no fixed target, so the exit is managed and needs both. See the B7/B8 note below** |

**B7 + B8 — one missing order surface, two gates (updated 2026-07-26).** The provenance
question B7's finding said "must be resolved, not assumed" is now **resolved: the substrate DID
apply cancel-if-runs.** Every canon fill originates in `simulate()`, whose config carries the
shipped `t_cancel = 22.0`; re-running March 2026 (E3) with the rule disabled moves **34 fills**
(18 appear only without it, 16 only with it), because a cancelled order frees the day's trade
slots for different later setups. So live **must** implement it to reproduce the arming
reference. The missing surface is now BUILT (2026-07-26): `dtc_client.py` carries
`cancel_order` / `modify_order_price` / `submit_reduce` with server read-back (`order_state`),
`dtc_broker.DTCBroker` implements the full spine Broker protocol over it, `order_watch.OrderWatch`
mirrors the engine's cancel decisions boundary-for-boundary, and `exit_live.LiveExitExecutor`
executes the driven managed exit fail-closed — all verified against the Sierra-strict mock
(tests/test_dtc_*, test_order_watch, test_exit_live). **Both gates stay RED until the same
sequences pass against the real Sierra DTC server**, and that run is turnkey:
`python -m scripts.dtc_surface_forcetest --account <SIM> --symbol MNQ... --entry <far-below>
--stop <lower>` covers A7 + B7 (resting mode) and adds the full B8 fill path with `--fill`
(SIM-only by construction — the script refuses non-SIM accounts).

## C. Operations — FORCE-TESTED before arming, not waited for

The old version asked us to observe these over weeks. **Cause them instead** — deliberate testing is
stronger evidence than hoping an event happens inside an arbitrary window.

| # | Gate | Pass condition |
|---|---|---|
| C1 | Uptime | **99%** of market hours once running; gaps explained |
| C2 | Restart recovery | Kill the process mid-session on purpose. No duplicate or lost orders on restart |
| C3 | Feed interruption | Induce a stall/gap. `feed_guard` halts correctly |
| C4 | Kill switch | Drilled live. Both Pat's and **Angus's** `/kill` verified from their own devices |
| C5 | Spine guards | Every Tier-1/2/3 rule force-tripped on the live setup (`scripts/spine_forcetest.py`) |
| C6 | Alerting | Every halt and trade reaches Telegram. Zero silent failures |
| **C7** | **Engine dies mid-trade** | **Kill the engine while a position is OPEN. The managed exit (trail, 3-min cut, EOD flatten) all need the engine alive — confirm it FAIL-CLOSES: flatten the position, do NOT leave it running on the resting stop alone** |

## D. KILL CRITERIA — the bot stops itself, automatically, no discretion

**This replaces the protective function the paper window used to serve.** With money live from
trade one, the question is not "did it behave for four weeks" but "does it stop the moment it
misbehaves."

### D1 — Correctness kills (flatten + halt immediately, no human judgement)

| trigger | why |
|---|---|
| Any A-gate failure detected live | the system is no longer the validated system |
| **Any naked position — an open position without a resting protective stop, any duration** | unbounded loss |
| **Engine dead while a position is open** (managed exit can't run) | the trail/cut/EOD are unmanaged → fail-closed flatten |
| **Newly discovered look-ahead in a scored column** | the validated edge was measured on different information |
| **Live-vs-backtest contract mismatch at a roll** (A8) | scoring a different instrument than the backtest |
| Any order the canon did not authorise | the trade path has a second author |
| Sizing mismatch vs the dollar-risk schedule | risk is not what we think it is |
| Entry filled **worse than the limit price** | structurally impossible — means a bug or a market order |
| Feed stale past the `feed_guard` threshold | scoring on dead data |
| Duplicate orders after restart | state recovery is broken |
| Relay output != Python verdict | the no-LLM-in-the-trade-path guarantee is void |

### D2 — Risk kills (account protection; the bot may be behaving correctly)

| trigger | value |
|---|---|
| Daily loss limit | **−4R**, indexed to the day's own `base_dollar` — **not** a fixed dollar figure. = −$800 at the eval floor, −$1,700 at $6k available DD. Measured in `docs/RULING-daily-loss-limit.md` |
| Available-drawdown floor | **keep the shipped $250.** It captures 89% of the available bust reduction (1.59% → 0.17%) for 1.2% of mean cash. $400 buys the last 0.17pp at **$3,435 per point** when a point is worth ~$465 — corrected 2026-07-26 after the paired test; the payout median is quantised to $2,000 steps and hid the cost |
| Consecutive halt days | 2 in a row → stop and review before re-arming |
| ~~Loss-count halt~~ | **Not used.** "2 losing trades" costs $3,163 on the canon and halts 35 of 225 days — re-confirming Angus's 17-Jul `daily_halt_losses: 0` ruling. Damage, not attempts |

Both numbers are measured, not assumed — see `docs/RULING-daily-loss-limit.md` for the
replay, the funded-year MC and the payout-cycle MC. **Awaiting Angus's sign-off on the two
values;** the *units* finding (R, not dollars) is not a preference and holds at any value.

**D1 is automatic and absolute. D2 is automatic, with human review before re-arming.**

### D2 blockers in the code — ALL THREE FIXED 2026-07-26

| # | defect | resolution |
|---|---|---|
| 1 | `SpineConfig.daily_loss_halt = -800.0` was a fixed dollar constant while the sizer is DD-scaled. At $6k available DD it is tighter than one max-conviction trade; the payout-cycle MC priced that at **−$6,000/account/year for zero bust reduction** | ✅ replaced by `daily_loss_halt_r` — an R multiple of the day's own `base_dollar`, recomputed per check from `equity − trailing_floor`. −4R reproduces this doc's two reference points exactly (−$800 at the eval floor, −$1,700 at $6k available DD). The fixed-dollar field is **removed, not kept as an override**, and a test asserts it stays removed. **The VALUE still awaits Angus's sign-off; the units do not.** |
| 2 | `SpineConfig.max_contracts = 2` was commented "minis" but `intent.size` is **micros** (`canon_lane.py`, `route_b.py`). `route_b.py` used the default. Live, every order clamped to 2 micros → **gate B5 fails on trade one** | ✅ now imports `gate_evidence.MICRO_CLAMP` (**40**) — the sizing schedule's own cap — so the clamp and the sizer cannot drift apart again |
| 3 | No config file or boot assertion pinned any Tier-1 constant — they rode on dataclass defaults, and `canon_run.py` never passed a config at all | ✅ Tier-1 limits now live in the `spine:` block of `config/live.yaml`, loaded by `load_spine_config()` and checked by `assert_tier1_pinned()` **before the spine is built**. Fails closed on a drifted value, a missing block, or an unknown key (a typo'd limit silently defaulting). Config/code duplication is deliberate: two copies + a boot assertion make any limit change a reviewable act, per §E |

Regression-tested (`tests/test_canon_spine.py`). **These were code defects, not gates** —
fixing them does not turn any A/B/C gate green; it removes three known-wrong behaviours that
would have corrupted those gates' evidence.

## E. What forces a STOP-AND-REVIEW mid-eval

1. Any code change to canon, sizer, spine, or relay
2. Any D1 trigger
3. Any Sierra/feed/symbol configuration change on the box
4. **Contract rollover** — do not halt for it, but watch it live on the day with the kill switch
   ready. **Prerequisite: A8 green.** Rollover handling is built, tagged and unit-tested; it gets
   validated on the real roll (≈2026-09-16). If it misbehaves, that is a D1 kill.

Not "investigate and continue." **Stop, review, re-arm deliberately.**

## F. Explicitly NOT gates

- P&L being positive, over any window
- P&L resembling the backtest's median
- Win rate, drawdown, or Sharpe over any short window
- Eval progress or payout eligibility
- **Any minimum number of trading days or live trades** — *deleted 2026-07-26; the eval is the test*

Observed and journaled, but they gate nothing. At this trade frequency they carry no information.
**A profitable run that fails an A-gate is halted. An unprofitable run that passes every gate keeps
running.**

---

## Sign-off

Arming requires, in order:

1. Every A, B and C gate marked PASS, evidence committed to the repo
2. §D kill criteria implemented, force-tested, and confirmed to fire
3. Pat's written confirmation that A–D were checked against artifacts, not memory
4. **Angus's arming token** — the only thing that turns the executor on

Neither party arms alone. The token is the mechanism; this document is the reason.

```
Gates verified by (Pat):     ____________________  Date: __________
Arming approved by (Angus):  ____________________  Date: __________
Arming token issued:         [ ] yes
```
