---
date: 2026-08-07
kind: mock funded-account run (position sizing, NOT a validation)
strategy: ash-unicorn-sb (AM1 09:45–10:15 ET only)
script: scripts/ash_funded_sim.py
equity curve: ash-unicorn-sb-funded-sim.csv
---

# Mock $50k funded account — split risk on the F2 arm

## ⚠️ READ THIS BEFORE THE NUMBERS

**The A-arm is a filter found in-sample on 15 trades, and it is currently under
pre-registered forward test** (`ash-unicorn-sb-forward-protocol.md`, hypothesis H2). Sizing
1.5× on it is a **bet that the filter is real**, taken before the test that would establish
that. Everything below is a sizing exercise on a known trade sequence — it is not evidence
that the strategy works, and no trial from it enters the ledger.

The account never blows up in this run. That is one 16-month sequence, not a risk estimate.
The bootstrap section is the risk estimate.

---

## Setup

| | |
|---|---|
| account | $50,000, MNQ micros ($2/pt) |
| **A-arm** | `F2_retrace_ratio < 1.0` → risk **$375** (1.5×) |
| **B-arm** | everything else → risk **$250** |
| sizing | `contracts = floor(budget ÷ (stop_pts × $2))`, minimum 1 |
| costs | $2.50/contract/round turn — the desk's $25 NQ convention ÷ 10 |
| span | 2025-03-07 → 2026-07-15, 37 setups, one per session |

**Micros are required, not a preference.** $250 against the median 25.5-point stop is **0.49
NQ contracts**. In MNQ it is 4. Realised sizes run 1–23 contracts (median 5), actual risk
$170–$371 — always at or under budget, because sizing floors rather than rounds.

**The 8 pre-2025-06-01 trades are sized as B (normal) by necessity** — flow data does not
cover them, so at the time you could not have known they were A-arm. Sizing them up on
hindsight would be the fabrication this programme keeps refusing.

| arm | n | risk | win rate | avg R |
|---|---|---|---|---|
| **A** (F2 < 1.0) | 15 | $375 | **73.3%** | **+1.33** |
| **B** (all else) | 22 | $250 | 18.2% | −0.09 |

**The B-arm is a losing arm.** All of the strategy's profit comes from A.

---

## Results — profile: $2,000 trailing drawdown + $1,000 daily loss limit

| variant | trades | net P&L | final equity | worst buffer | $3k target |
|---|---|---|---|---|---|
| **SPLIT $375 / $250 — as asked** | 37 | **+$5,931** | $55,931 | $1,280 | 2025-11-21 |
| FLAT $250 everywhere | 37 | +$3,546 | $53,546 | $1,280 | 2026-05-07 |
| A-arm only ($375, skip 22) | 15 | **+$6,589** | $56,589 | $1,612 | 2025-10-27 |

*"worst buffer" = closest the equity ever came to the trailing liquidation threshold.*

**The 1.5× added ~$2,385 and pulled the $3,000 target forward by ~6 months** — without moving
the worst buffer at all ($1,280 in both), because the drawdown is driven by the B-arm losses,
which were not sized up.

On the **$2,500 trailing, no daily cap** profile every P&L figure is identical and the worst
buffer becomes $1,780. The daily cap is irrelevant either way: **AM1 is one trade per day and
the largest possible loss is $371**, so a $1,000 daily limit can never bind. **The only
constraint that matters on this account is the trailing drawdown.**

Consistency: best single day is **$713 = 12% of total profit**, comfortably inside a typical
50%-of-profit consistency rule.

---

## Risk — 20,000 bootstrap runs of 37 trades

The single 16-month sequence is one draw. Resampling the trades with replacement lets streaks
form and break differently, which is the honest read of "same edge, worse luck":

| scenario | P(blow up) | P(hit $3k) | median P&L | 5th percentile |
|---|---|---|---|---|
| as observed — filter works | **1.1%** | 92.5% | +$5,904 | **+$2,069** |
| **filter is NOISE** — labels random | **3.5%** | 79.7% | +$4,356 | **+$311** |

**The sizing scheme survives either way.** Even assuming F2 carries no information at all,
blow-up risk is 3.5% and the 5th-percentile outcome is still slightly positive. That is the
useful result here: **the 1.5× is not what would kill this account.** The strategy's own
edge holding up is the open question; the sizing is not reckless.

Observed sequence: longest losing streak **3**, largest single loss **$368**, trade frequency
**2.3/month**.

### One number that is circular, and should not be quoted

The permutation test (`P(random labelling ≥ actual) = 0.0014`) is reported by the script but
**does not test whether F2 is real.** F2 was selected *because* it separates these 37 trades,
so of course labelling by F2 beats random labelling on them. It is in the output only for
completeness. The forward protocol is the only thing that can answer that question.

---

## Assumptions, stated rather than implied

1. **Prop-firm rules are generic, not quoted from any contract.** Two $50k profiles were run
   ($2,000 trail + $1,000 daily; $2,500 trail, no daily) so the answer does not depend on one
   firm's numbers. Check the actual rulebook before treating any of this as a plan.
2. **No minimum-activity requirement is modelled.** At **2.3 trades/month**, this strategy
   alone would likely fail the minimum-trading-day requirements many firms impose. It is not
   a standalone account programme.
3. **Fills are assumed at the stop and target prices**, per the raw-baseline assumptions
   A1–A9. Slippage beyond the 1-tick allowance in the cost figure is not modelled, and gap
   risk through a stop is not modelled.
4. **F2 is knowable at entry** — it reads only minutes at or before the entry bar, with
   runtime asserts in `scripts/ash_orderflow_test.py`. The 1.5× decision is implementable in
   real time; that part is not hindsight.
5. **The ES leading trigger is still absent**, as in every number in this programme.

**No trial recorded. Sealed 2023/24 untouched.**
