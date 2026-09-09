# FINDINGS — Funded-account sim for the armed book (2026-09-03)

Arming changes trade frequency 78.1 → 63.4/day and reshapes the stop
distribution, so the §33 Monte Carlo artifact describes the pre-arming
book. Re-run here.

Mechanics are a line-for-line Python port of `docs/artifacts/funded_sim.html`
so the two are comparable: day $ = Σ `micros × $2 × (gross_r × stop_pt −
0.5)`; every day draw reduced by `haircut × mean daily $`; eval balance
from 0 with a $2,000 EOD-trailing floor that locks at the start balance
once ahead, $3,000 target, pass after ≥1 day; funded phase restarts fresh
to a $4,000 target after ≥10 days; 5-day block bootstrap; 120-day cap;
30% edge haircut; 20,000 sims per cell. Receipt: `scripts/funded_sim_armed.py`.
Regenerated trade export for the artifact: `docs/artifacts/empire_trades_arm1.json`
(58,401 trades / 921 days — drop in place of `__TRADES__`).

## 1. At one micro, both books pass every time

| | trades/day | median stop | mean $/day (1 micro) | eval pass | median days to pass | start→payout |
|---|---:|---:|---:|---:|---:|---:|
| frozen spec | 78.1 | 8.2pt | +$211.55 | 100.0% | 21 | 100.0%, 50 days |
| armed 1R | 63.4 | 7.2pt | +$226.18 | 100.0% | 20 | 100.0%, 47 days |

At one micro the book earns ~$210–226/day against a $2,000 drawdown and a
worst day near −$300. It cannot fail, and the comparison is uninformative.
Even a 50% haircut leaves both at 99.8%+. **The one-micro question is the
wrong question.**

## 2. The real question: how much size does the $2,000 drawdown carry?

30% haircut, 20,000 sims per cell. "payout" = start → first funded payout.

| micros | $ risk/trade* | frozen pass | payout | **armed pass** | **payout** |
|---:|---:|---:|---:|---:|---:|
| 1 | $16 | 100.0% | 100.0% | 100.0% | 100.0% |
| 4 | $66 | 98.8% | 98.1% | 99.9% | 99.9% |
| **8** | $132 | 90.3% | **83.6%** | 96.7% | **93.9%** |
| 12 | $198 | 85.4% | 74.9% | 90.3% | 84.1% |
| **16** | $264 | 82.9% | **70.0%** | 88.6% | **81.2%** |
| 20 | $330 | 82.3% | 67.0% | 87.1% | 77.0% |
| 24 | $396 | 81.4% | 63.9% | 85.3% | 72.7% |
| 30 | $495 | 80.3% | 60.9% | 83.1% | 68.0% |

\* median-stop dollar risk per trade at that size.

**Holding start→payout odds at ≥80%: the frozen book carries 8 micros,
the armed book carries 16.** Arming roughly **doubles the size the same
drawdown allowance supports.**

That is the practical translation of the drawdown result (−18.1R →
−14.0R). "+30% expectancy per trade" is the academic statement; "twice
the contracts at the same odds of getting paid" is the one that matters
to a funded account, and they are the same fact.

## 3. Reading it honestly

- **The pass rates plateau around 80–85%, they do not go to zero.** Past
  ~12 micros the binding constraint stops being the edge and becomes the
  first bad day: one −14R to −18R session at that size simply exceeds the
  $2,000 floor. More size cannot fix a single-day tail.
- **The 30% haircut is doing real work** and should not be dialled down
  without a reason. At 0% haircut everything looks better; the haircut is
  the built-in dose of doubt about whether the backtest edge is the live
  edge, and today's queue work (edge dies between 2 and 4 ticks of fill
  penetration) is a concrete argument for keeping it at least that high.
- **The sample is the backtest.** Block-resampling 921 days cannot produce
  a regime the four years did not contain. Pass rates are conditional on
  the future resembling 2023–26.
- **Sizing here is flat micros**, which passes stop-size variance straight
  into dollar risk. The budget mode (floor $ ÷ stop) is gentler on the
  tail and was not re-swept for the armed book.

## 4. Practical read

At 1–4 micros both books are over-capitalised for a 50K eval — the
constraint is boredom, not risk. The decision point is 8–16 micros, and
that is exactly the band where arming stops being a nicety: **93.9% vs
83.6% at 8 micros, 81.2% vs 70.0% at 16.**

If the executor cannot implement arming (it needs the order placed within
the same minute the arming bar closes — see the latency finding), the
honest size ceiling on the frozen book is around 8 micros for ≥80% odds.
