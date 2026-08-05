# Validation Gate v1.0 — the bar a strategy must clear to enter the book

Every criterion is PASS/FAIL with the number that produced it written next to
it. There is no "borderline" and no "close enough with a note". If a criterion
needs softening, that is a change to *this document*, made deliberately, before
the run — never a judgement call made while staring at a result you like.

Everything is measured in **R** (multiples of the trade's initial risk) and
**net of costs** (§C). Dollars are derived at the end, never used for
decisions — dollars change with size, R doesn't.

---

## A. Sample sufficiency — is there enough here to conclude anything?

| # | Criterion | Threshold |
|---|---|---|
| A1 | Triggers in the in-sample window | **≥ 60**, target ≥ 100 |
| A2 | Triggers surviving refinement | **≥ 40** |
| A3 | Triggers in the out-of-sample window | **≥ 25** |
| A4 | Trading days with ≥1 trigger | ≥ 30% of days in the window |

**Why A2 is where most strategies die.** It is easy to filter 100 trades down to
the 12 that worked. Those 12 tell you nothing — you selected them *because* they
worked. Forty is the floor at which a win rate is distinguishable from a
coin flip at anything like useful precision.

A4 catches the strategy that made all its money on nine days in March.

---

## B. In-sample performance (2025-07-01 → 2026-06-30)

| # | Criterion | Threshold |
|---|---|---|
| B1 | Expectancy per trade | **≥ +0.20R**, or higher per the refinement-ledger scale below |
| B2 | Profit factor | **≥ 1.30** |
| B3 | Max drawdown | **≤ 8R** |
| B4 | Longest losing streak | ≤ 8 trades |
| B5 | Both halves positive | 2025-H2 and 2026-H1 each expectancy > 0 |

**B1 scales with how many things we tried** (from the refinement ledger — this
is the multiple-comparisons adjustment, and it is not optional):

| Filters/variants tested | B1 threshold |
|---|---|
| ≤ 5 | +0.15R |
| 6 – 15 | +0.20R |
| 16 – 40 | +0.30R |
| > 40 | automatic FAIL — go back to Stage 2 |

---

## C. Cost realism

Applied to every trade before any number above is computed:

| Component | Assumption |
|---|---|
| Commission + fees | $5.00 round turn per NQ contract |
| Entry (limit) | no slippage, **but price must trade fully through the limit** to count as filled |
| Stop exit | **2 ticks** adverse (stops fill worse — that is what a stop is) |
| Target exit | fills at target − F points, front-run per strategy doc §6.4 |
| Near a scheduled release (±2 min) | double the slippage assumptions |

| # | Criterion | Threshold |
|---|---|---|
| C1 | Still passes B1 and B2 at **2× all slippage** | required |
| C2 | Cost drag as share of gross edge | ≤ 35% |

C1 is the cheapest robustness test in existence and it kills a specific, common
failure: the strategy whose edge is real but smaller than the spread it has to
cross. If doubling slippage flips it to a loser, we were never trading an edge —
we were trading an estimate of one.

---

## D. Out-of-sample — the one that actually matters

Windows are picked **before looking at them**, by this rule: three calendar
months of 2023 and three of 2024, chosen by taking months whose index is
`(strategy_slug hashed) mod 12`, then the next two non-adjacent months. Written
into the verdict before the run. This exists so nobody can pick "the months
where it works" without it being visible in git.

| # | Criterion | Threshold |
|---|---|---|
| D1 | OOS expectancy | **> 0** after costs |
| D2 | Degradation ratio (OOS expectancy ÷ IS expectancy) | **≥ 0.50** |
| D3 | OOS profit factor | **≥ 1.15** |
| D4 | OOS attempts used | **≤ 3**, each on a different window, all logged |
| D5 | Direction agreement | OOS win rate within ±15pp of in-sample |

**D2 is the single most informative number in this document.** A strategy that
made +0.40R in-sample and +0.35R out-of-sample (ratio 0.88) is real. One that
made +0.60R in-sample and +0.10R out-of-sample (ratio 0.17) was fitted, no
matter how good that 0.60 looked. Some decay is normal and expected — we tuned
on the first window, so of course it flatters. Half is the line.

D5 catches the strategy that "passes" out-of-sample on two lucky outliers while
its actual hit rate collapsed.

---

## E. Robustness

| # | Criterion | Threshold |
|---|---|---|
| E1 | Parameter plateau | each tuned parameter still positive at ±1 step either side |
| E2 | Volatility regimes | positive expectancy in ≥ 2 of 3 ATR terciles |
| E3 | Month concentration | no single month > 40% of total R |
| E4 | Trade concentration | best single trade < 15% of total R |
| E5 | Filter stack depth | ≤ 3 filters beyond the raw trigger |

E1 in plain terms: if the rule needs *exactly* 3 confluences, and 2 and 4 both
lose money, then 3 isn't a rule — it's the number that happened to fit. Real
edges are broad and tolerate being nudged.

E4 catches the equity curve that is one great trade and 80 breakevens.

---

## F. Book fit — does it add anything we don't already have?

| # | Criterion | Threshold |
|---|---|---|
| F1 | Daily-R correlation vs any single book strategy | \|ρ\| ≤ **0.40** |
| F2 | Correlation vs the aggregate book | \|ρ\| ≤ **0.50** |
| F3 | Session/window overlap with an existing strategy | if > 70%, must show a higher expectancy than the incumbent |
| F4 | Adds trading days the book doesn't already cover | ≥ 15% of its triggers on days the book is otherwise flat |

Two strategies that lose on the same days are one strategy wearing two hats.
They double the drawdown and don't double the edge. F1/F2 are what make a
"massive strategy book" genuinely more robust than one strategy sized up —
without them it's just leverage with extra paperwork.

---

## G. Legibility — can the owner audit it?

| # | Criterion | Threshold |
|---|---|---|
| G1 | Mechanism stated in one plain-English paragraph | required |
| G2 | Angus can restate the trigger without reading code | required |
| G3 | Every tuned parameter traced to a line in the mechanical spec | required |
| G4 | Falsification condition written *before* results were seen | required |

G2 is a real gate, not a formality. A strategy the owner cannot describe is a
strategy the owner cannot supervise, override, or sanely stop trading when it
stops working — and that moment always arrives.

---

## Verdict

- **ADOPT** — every criterion PASS. Goes into `strategies/BOOK.md`.
- **PARK** — mechanism sound (G-block passes), blocked only by sample size or
  missing data. Revisit when the data arrives. Records what data would unblock it.
- **REJECT** — anything else. Goes to `strategies/GRAVEYARD.md` with the failing
  criterion. Rejections are kept: they stop us re-testing the same idea in six
  months, and the pattern of *why* things fail is itself information.

---

## What this gate is not

It is not a promise the strategy will make money. It is a filter that removes
the strategies that were **never going to** — the fitted ones, the ones riding a
single regime, the ones whose edge is smaller than their costs, and the ones
that are just a strategy we already trade.

Passing means the idea has survived every cheap way we know of being wrong.
That is the most any backtest can offer. The remaining risk gets managed by
position size and the Vault's limits, not by more testing.
