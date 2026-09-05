# PRE-REGISTRATION — NQ-bot re-test (three structurally-motivated changes)

**Written 2026-09-05, before any code change and before any run.** Subject: the MNQ liquidity-sweep
bot at `github.com/Prat617/ai-trading-bot`, commit `d1e5ec7`, project root `nq_bot_vscode/`. This
document fixes what will be changed, what will not, which readings of each change will be run, the
data split, the pass mark, and what counts as a read — so that nothing is chosen after seeing a
result. Modelled on `research/vwap-bb/PREREGISTRATION.md`; where this document is looser than that
one, it says so.

**Why this test exists.** A 4-year causal-replay backtest of the untouched bot (2021-09 → 2025-08,
5,947 trades) returned PF 1.13, win rate 46.7%, +$26,274 on $50k, max DD 10.8% — a near-breakeven
process, ~3 points above the win rate its own realized payoff ratio requires
(`TRADE-AND-ENTRY-REVIEW.md`). Three defects in its entry mechanism were identified, each of which
has an argument that **predates this data** — written for the VWAP/BB strategy in this repository
before the bot was ever run:

| defect in the bot | pre-existing argument | where it was written |
|---|---|---|
| stop = `min(ATR14×2, sweep wick + 2pt)`; median stop 0.66×ATR; 17% of trades have stops <5pt where friction is 120% of structural risk | a stop below ~10pt on this instrument "is not measuring structure, it is measuring the width of the book"; a fixed floor, later ATR-scaled | `strategy-definition-v1.0.md` A5 (2026-08-08), A22 (2026-08-08) |
| 42% of trades are overnight; the edge is entirely RTH | entry window RTH only, on structural grounds | `strategy-definition-v1.0.md` A1 (2026-08-07) |
| the min-R:R gate screens against an `ATR14×1.5` target the executor never places (it trails from +3pt), and by construction passes only when the stop is ≤ ATR — selecting the tight-stop population | an admission gate must certify a quantity the accounting actually delivers; a run built on a gate/accounting mismatch is discarded unopened | `STAGE3-DISCARDED.md`, A16 (2026-08-08) |

**The trap this document guards against.** Those three defects were *also* the three most profitable
slices of the 4-year trade log. That is encouraging and dangerous in equal measure: it is exactly
what a post-hoc selection would look like. The defence is (i) the argument for each change is dated
before the data was seen, (ii) every reading of each change is run and the **minimum** is taken,
(iii) the verdict is read once, on data that has never been seen.

---

## 1. The three changes, each with its readings fixed now

### C1 — stop floor

`effective_stop = max(stop_as_currently_computed, FLOOR)`, applied after the existing
`min(ATR14×2, structural)` rule and **before** the existing 30pt cap, which is unchanged. Two
readings, both run:

| reading | FLOOR | basis |
|---|---|---|
| **C1a** | **10.00 pt fixed** | A5: the floor the user's own spec set for the same price series (NQ points; MNQ is the same index at 1/10 the multiplier), 40 ticks, 13× median spread. **Disclosed difference:** on the bot's 2-micro-contract structure, total friction at a 10pt stop is ~33% of structural risk (commission on micros is a larger share), not the ~10% A5 targeted. A5's number is used as written, not re-derived from this data. |
| **C1b** | **2 × ATR14** (the bot's own 2-minute-bar ATR, already computed per signal) | A22: the ATR-scaled floor the user adopted when the fixed one was judged too blunt. Median ATR14 here is ~15pt, so this reading will collide with the unchanged 30pt cap on a large fraction of signals. That is a consequence of the reading, reported, not tuned. |

A third candidate — a floor derived from a friction-to-risk ratio (≈13–16pt) — is **excluded**: it would
be a number chosen from this dataset's own friction figures. Flagged, not run.

### C2 — RTH-only entry

An entry is permitted only when the **signal bar's** timestamp satisfies the bot's own
`is_rth()`: `09:30 ≤ t < 16:00 ET` (`scripts/full_backtest.py:225`). **One reading.** The bot's
definition is used rather than A1's (09:31–16:00, first tradeable bar 09:36) so that no new
boundary is invented for this test; the difference is disclosed. Exit rules are untouched — a
position opened at 15:58 is managed exactly as today.

### C3 — the min-R:R gate

The gate at `scripts/full_backtest.py:1096-1102` rejects a signal unless
`(ATR14 × 1.5) / stop ≥ 1.5`. The executor places no fixed target; C1 trails from +3.0pt, C2 trails
ATR×2. Two readings, both run:

| reading | rule | basis |
|---|---|---|
| **C3a** | **gate removed** | it certifies a target that is never placed; the risk discipline it was standing in for is carried by C1 |
| **C3b** | **gate kept as-is** | the current reading, retained so its effect is measured rather than assumed |

The risk engine's internal `min_rr_ratio` target adjustment (`risk/engine.py:342-344`) raises a
`target_distance` the executor also never uses; it is inert and is left alone.

### Fork set

**C1 {a, b} × C3 {a, b} = 4 combinations, C2 fixed.** All four are built and run; none is selected.

## 2. What is NOT changed — stated so it cannot drift

Sweep detector parameters (2pt min depth, 2pt stop buffer, 3-bar reclaim, 1.5× volume, 50pt round
grid); the score and its bonuses; `HIGH_CONVICTION_MIN_SCORE = 0.75`; `SWEEP_MIN_SCORE = 0.70`;
the 30pt max-stop cap; HTF gate 0.3 and HTF timeframes; C1/C2 exit rules (3.0 / 2.5 / 12-bar
fallback; BE+1, ATR×2 trail, 150pt cap, 120-min time stop); slippage (0.50 RTH / 1.00 ETH per
fill); commission $1.29/contract/side; daily loss $500, kill switch $1,000; 30-bar session warmup;
2-minute execution bars built from 1-minute data as the bot builds them.

**Known defects deliberately left in place for this test**, because fixing them changes which
signals fire and would be a fourth, un-argued change:
- `session_high` / `session_low` sweep detection is unreachable (ordering bug in
  `LiquiditySweepDetector.update_bar`). Left as-is.
- `sweep_log` / aggregator history grow unbounded. This is a **performance** defect, not a
  behavioural one; it may be patched for the test **only if** the patched engine reproduces the
  unpatched engine's trade list exactly on a verification slice (same trade IDs, prices, PnL). If
  it does not, the patch is not used.

## 3. Data, and what has already been seen

| segment | window | status |
|---|---|---|
| **Development** | 2021-09-01 → 2024-12-31 (checked-in TradingView exports; **Mar–Aug 2023 missing** from the repo) | all four combinations run here, each sealed once |
| **Contaminated semi-holdout** | 2025-01-01 → 2025-08-31 | **Already inspected.** Every slice in `TRADE-AND-ENTRY-REVIEW.md` — by stop bucket, RTH, hour, level type — included 2025 outcomes, and those slices are what these hypotheses' *magnitudes* were observed on. It is reported alongside, clearly labelled, **never as the verdict.** |
| **Holdout** | 2025-09-01 → latest available, a **fresh** TradingView `MNQ1!` 1-minute export supplied by the user | never seen by this analyst, the repo, or its author's published results. **Not to be delivered or opened until §5's dev runs are sealed.** One read. |

The bot's own published 6-month windows (Sep 2025–Feb 2026, FirstRate data) overlap the holdout
period but used a different data source and configuration; they are not consulted.

## 4. Pass mark — fixed here, evaluated once on the holdout

For each of the four combinations, on the holdout:
- **mean net $/trade > 0** (net of modelled slippage and commission), and
- **session-block bootstrap one-sided 95% lower bound > 0** — blocks are trading days
  (`get_trading_day()`), resampled with replacement, 10,000 iterations, lower bound = 5th
  percentile of the bootstrap distribution of the mean. α = 0.05 with no further correction: there
  is one pre-registered configuration family, and taking the minimum across its four readings is a
  conjunction, which cannot inflate the false-positive rate.

**The verdict is the minimum across the four combinations.** PASS only if all four clear both
conditions. A result positive under one reading and negative under another is **NO EDGE
DEMONSTRATED**, not a pass on the favourable branch.

**Abort conditions (no verdict read):**
1. Fewer than **300 holdout trades** in any combination. Stated honestly: at ~$100 per-trade
   standard deviation, n = 300–400 detects an edge of roughly **$12–15/trade** at 80% power; a true
   edge of $5/trade would be invisible. The dev-window slices ran $9–32/trade on the relevant
   buckets, so the test is powered for the effect it is looking for, not for a marginal one.
2. The sign of mean net $/trade **flips between the modelled slippage and a 2× stressed slippage**
   (1.00 RTH / 2.00 ETH) in any combination — then the finding is about the cost model, not the
   strategy.
3. Any lookahead detected by the engine's own verification checks.

**Reported, not binding:** profit factor, max drawdown, trade count, monthly PnL, win rate, the
contaminated 2025 semi-holdout, and one **disclosed sensitivity** — the same four combinations with
the 30pt cap lifted — reported next to the main result and never a candidate, exactly as
market-at-open is handled under A16.

## 5. Procedure and read accounting

1. Commit this document. Record its hash and the bot commit in `RESULT.md` when written.
2. (Optional) performance patch, gated by the exact-reproduction check in §2.
3. Build `retest_backtest.py` importing the bot's real modules, with flags for C1/C3 readings, RTH,
   and date bounds. Verify on a short slice that the untouched configuration reproduces the
   existing 4-year trade log for that slice.
4. Run the untouched configuration and all four combinations on the **development** window. Seal
   each trade list (SHA-256). Report all five. **These are development reads; they inform nothing
   about the verdict and change nothing in §1–§4.**
5. Only then: obtain the holdout export. Run all four combinations once. Apply §4. Write `RESULT.md`.

**Reads:** development, unlimited but each configuration sealed once and not re-run; **holdout, one
read total**, covering all four combinations. If §4 returns NO EDGE, this pre-registration is
finished — a second holdout read under a revised rule set requires a new document and fresh data.

## 6. What a pass would and would not mean

A pass says: on ~12 months never seen by anyone involved, a version of this bot with a book-width
stop floor, RTH-only entries, and no phantom-target gate has positive expectancy after modelled
costs, robust to the two documented readings of each change. It does **not** say the mechanism is
what its code narrates (round-number overshoots, not institutional sweeps, carry the profit), that
the edge exceeds a few thousand dollars a year per two micro contracts, or that live fills match
the 0.5/1.0pt model. Those are the next questions, not this one.
