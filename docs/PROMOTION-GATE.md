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

The edge is validated: 400/400 exact, +$56,065.18. Only the plumbing is unproven.

---

## A. Correctness — pre-arming, all 100%, no tolerance

Every one of these is a **one-off check**, not a multi-week observation. There is no reason to wait.

| # | Gate | Pass condition |
|---|---|---|
| A1 | Feature parity | Live features == backtest to the decimal on the reconciliation day, re-checked daily thereafter |
| A2 | Verdict fidelity | Every signal matches what the canon scorer produces on the same journaled inputs. Replayable |
| A3 | Relay integrity | `canon-relay` output == Python verdict, byte-for-byte. Zero divergences |
| A4 | No missed trades | Every candidate the canon would take is seen and acted on. Misses journaled with cause |
| A5 | Both books wired | NY **and** London paths both proven to fire — force a signal through each if needed |
| A6 | Journal completeness | Zero trades with missing/malformed journal records |
| **A7** | **Bracket integrity proven on the box** | **Submit one bracket, read back THREE distinct order IDs (entry + stop + target) with live status — see note** |
| **A8** | **Roll alignment** | **RollWatcher's roll date == the backtest's volume-roll date (`docs/CONTRACT-ROLL-DATES.md`)** |

**Any A-failure is disqualifying, not a deduction.** One byte of divergence in A3 means the relay
computed something, and the "no LLM in the trade path" guarantee is void.

### A7 — do this one first

`src/desk/dtc_client.py::submit_bracket()` sends `"Stop"` and `"Target"` as fields on
`SUBMIT_NEW_SINGLE_ORDER`. **Those are not DTC fields.** DTC brackets are parent + children carrying
`ParentTriggerClientOrderID`, or `SUBMIT_NEW_OCO_ORDER`. A JSON decoder silently drops unknown keys.
The mock server reads only `ClientOrderID`, `Quantity`, `Price1` — so **every order test passes
whether or not the legs exist.** If they don't, we are placing naked entries with real money.
Nothing else on this list matters until A7 is green.

### A8 — the silent one

Databento (`NQ.v.0`, the backtest's data) rolls on **volume**: the Wednesday **2 days before
expiry**. Calendar rules roll 2–6 sessions earlier. In that gap live trades the back month while
the backtest scored the front — every level feature on a different instrument, separated by the
calendar spread. **A1 fails and nothing crashes.** Next roll ≈ **2026-09-16**.

## B. Execution — the part the backtest never modelled

| # | Gate | Pass condition |
|---|---|---|
| B1 | Fill vs intent | **Median 0 ticks on entries.** These are limits — you get your price or better. Any entry filled *worse* than the limit is a bug, not market movement. Stop-exit slippage tracked separately |
| B2 | No market orders | Zero. Ever. Structural, not statistical |
| B3 | Rejection rate | Below **2%**, each rejection explained |
| B4 | Bracket integrity | Every entry has its stop and target attached. **Zero naked positions, any duration** |
| B5 | Sizing | Micros placed == dollar-risk schedule, every trade, exact |
| B6 | Feed lag characterised | Sierra file-flush lag **measured, not assumed**, written down as a number (`BOX-HANDOFF.md` Step B.2) |
| **B7** | **Working-order cancellation** | **A resting limit can be cancelled, and `cancel_if_runs_points` is enforced live — see `FINDING-live-path-cannot-cancel-a-resting-limit.md`** |

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

## D. KILL CRITERIA — the bot stops itself, automatically, no discretion

**This replaces the protective function the paper window used to serve.** With money live from
trade one, the question is not "did it behave for four weeks" but "does it stop the moment it
misbehaves."

### D1 — Correctness kills (flatten + halt immediately, no human judgement)

| trigger | why |
|---|---|
| Any A-gate failure detected live | the system is no longer the validated system |
| **Any naked position — entry without both legs, any duration** | unbounded loss |
| Any order the canon did not authorise | the trade path has a second author |
| Sizing mismatch vs the dollar-risk schedule | risk is not what we think it is |
| Entry filled **worse than the limit price** | structurally impossible — means a bug or a market order |
| Feed stale past the `feed_guard` threshold | scoring on dead data |
| Duplicate orders after restart | state recovery is broken |
| Relay output != Python verdict | the no-LLM-in-the-trade-path guarantee is void |

### D2 — Risk kills (account protection; the bot may be behaving correctly)

| trigger | value |
|---|---|
| Daily loss limit | `[ANGUS]` — proposal: **2 losing trades or −2R**, matching the §10 backtest halt |
| Available-drawdown floor | halt within `[ANGUS]` of the Lucid EOD line — proposal **$400**, one max-risk trade |
| Consecutive halt days | 2 in a row → stop and review before re-arming |

**D1 is automatic and absolute. D2 is automatic, with human review before re-arming.**

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
