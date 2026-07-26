# PROMOTION GATE — paper → real money

**Status:** DRAFT for Angus's ruling. Numbers marked `[SET]` are proposals, not decisions.
**Owner:** Angus (final say). Drafted by Pat.
**Applies to:** NQ canon system, repo `trackdco/AI-trading-agents`, branch `claude/getting-started-6lwnvs`.

---

## 0. The premise: this gate measures fidelity, not profit

The canon fires **400 trades in 2 years — about 3.8 per week.** Four weeks of paper is
~15 trades. Fifteen trades cannot distinguish a working edge from a lucky one, in either
direction. A P&L-based gate at this sample size is not a weak test; it is noise wearing
the costume of a test.

So the question this gate answers is **not** "did paper make money?" It is:

> **Did the live system do exactly what the backtested system would have done,
> under conditions the backtest never faced?**

The edge is already validated — 400/400 exact, +$56,065.18. What is unvalidated is the
*live plumbing*. That is what paper tests, and that is all it tests.

---

## A. Correctness — all must be 100%, no tolerance

| # | Gate | Pass condition |
|---|---|---|
| A1 | Feature parity holds | Live features == backtest to the decimal, every day, not just reconciliation day |
| A2 | Verdict fidelity | Every signal the engine produced matches what the canon scorer produces on the same journaled inputs. Replayable and re-run at gate time |
| A3 | Relay integrity | `canon-relay` output == Python verdict, byte-for-byte, every trade. Zero divergences |
| A4 | No missed trades | Every candidate the canon would have taken was seen and acted on. Misses are journaled with cause |
| A5 | Both books exercised | NY **and** London have each fired live. Neither is untested at promotion |
| A6 | Journal completeness | Zero trades with missing/malformed journal records |

**Any A-failure is disqualifying, not a deduction.** One byte of divergence in A3 means the
relay computed something, and the whole "no LLM in the trade path" guarantee is void.

## B. Execution — the part the backtest never modelled

| # | Gate | Pass condition |
|---|---|---|
| B1 | Fill vs intent | Slippage distribution recorded. Median within `[SET]` ticks of the limit |
| B2 | No market orders | Zero. Ever. Structural, not statistical |
| B3 | Rejection rate | Below `[SET]`%, each rejection explained |
| B4 | Bracket integrity | Every entry got its stop and target attached. Zero naked positions, any duration |
| B5 | Sizing | Micros placed == dollar-risk schedule, every trade, exact |
| B6 | Feed lag characterised | File-flush lag measured, not assumed. Documented as a number |

## C. Operations — can it survive a week alone?

| # | Gate | Pass condition |
|---|---|---|
| C1 | Uptime | `[SET]`% of market hours, gaps explained |
| C2 | Restart recovery | At least one unplanned restart survived without duplicate or lost orders |
| C3 | Feed interruption | At least one real gap/stall handled by `feed_guard` correctly |
| C4 | Kill switch | Drilled live during paper. Both Pat's and Angus's `/kill` verified working |
| C5 | Spine guards | Every Tier-1/2/3 rule fired at least once on the live feed, or was force-tested there |
| C6 | Alerting | Every halt and trade reached Telegram. Zero silent failures |

## D. Sample requirements

- Minimum **`[SET]` trading days** of continuous paper operation
- Minimum **`[SET]` live trades** (proposal: 25 — roughly 6–7 weeks at canon frequency)
- Must include at least one **DST transition week** if the calendar allows
- Must include at least one **full weekend gap** and Sunday reopen

## E. Conditions that reset the clock to zero

1. Any code change to canon, sizer, spine, or relay
2. Any A-section failure
3. Any naked position, any duration
4. Any Sierra/feed/symbol configuration change on the box
5. Contract rollover — unless rollover handling was itself part of the tested period

Not "investigate and continue." **Reset.**

## F. Explicitly NOT gates

- Paper P&L being positive
- Paper P&L resembling the backtest's ~$237k/yr median
- Win rate, drawdown, or Sharpe over the paper window
- Eval progress or payout eligibility

These are *observed and journaled* but do not gate promotion. At n≈25 they carry no
information. **A profitable paper run that fails one A-gate does not promote.
An unprofitable paper run that passes every gate does.**

---

## Sign-off

Promotion to real money requires, in order:

1. Every gate above marked PASS, evidence committed to the repo
2. Pat's written confirmation that A–D were checked against artifacts, not memory
3. **Angus's arming token** — the only thing that turns the executor on

Neither party promotes alone. The token is the mechanism; this document is the reason.

```
Gates verified by (Pat):        ____________________  Date: __________
Promotion approved by (Angus):  ____________________  Date: __________
Arming token issued:            [ ] yes
```
