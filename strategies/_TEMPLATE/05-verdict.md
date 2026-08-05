# <Strategy Name> — Verdict

**Stage 8.** Scored against `context/validation-gate-v1.md`. Every criterion
gets a PASS/FAIL and the number that produced it. No "borderline".

---

## Plain English

_Three sentences. What is the trade, did it work, and would we trade it? Written
so Angus can sign off from this section alone._

---

## Verdict: **ADOPT / PARK / REJECT**

Reason in one line: 

---

## Scorecard

### A — Sample sufficiency
| # | Criterion | Threshold | Actual | Result |
|---|---|---|---:|---|
| A1 | In-sample triggers | ≥60 | | |
| A2 | Triggers after refinement | ≥40 | | |
| A3 | OOS triggers | ≥25 | | |
| A4 | Days with a trigger | ≥30% | | |

### B — In-sample
| # | Criterion | Threshold | Actual | Result |
|---|---|---|---:|---|
| B1 | Expectancy | ≥ ____R *(scaled to _N_ filters tested)* | | |
| B2 | Profit factor | ≥1.30 | | |
| B3 | Max drawdown | ≤8R | | |
| B4 | Longest losing streak | ≤8 | | |
| B5 | Both halves positive | yes | | |

### C — Cost realism
| # | Criterion | Threshold | Actual | Result |
|---|---|---|---:|---|
| C1 | Survives 2× slippage | yes | | |
| C2 | Cost drag / gross edge | ≤35% | | |

### D — Out-of-sample
| # | Criterion | Threshold | Actual | Result |
|---|---|---|---:|---|
| D1 | OOS expectancy | >0 | | |
| D2 | Degradation ratio | ≥0.50 | | |
| D3 | OOS profit factor | ≥1.15 | | |
| D4 | Attempts used | ≤3 | | |
| D5 | Win rate within ±15pp of IS | yes | | |

**OOS windows used, and the pre-registered rule that chose them:**

### E — Robustness
| # | Criterion | Threshold | Actual | Result |
|---|---|---|---:|---|
| E1 | Parameter plateau | all ±1 positive | | |
| E2 | Positive in ≥2 of 3 ATR terciles | yes | | |
| E3 | Best month ≤40% of R | | | |
| E4 | Best trade <15% of R | | | |
| E5 | Filter stack ≤3 | | | |

### F — Book fit
| # | Criterion | Threshold | Actual | Result |
|---|---|---|---:|---|
| F1 | Max \|ρ\| vs any single book strategy | ≤0.40 | | |
| F2 | \|ρ\| vs aggregate book | ≤0.50 | | |
| F3 | Session overlap | <70%, or beats incumbent | | |
| F4 | Trades on days the book is flat | ≥15% | | |

Correlation matrix vs current book:

| vs | ρ (daily R) |
|---|---:|
| | |

### G — Legibility
| # | Criterion | Result |
|---|---|---|
| G1 | Mechanism in one plain paragraph | |
| G2 | Angus can restate the trigger unaided | |
| G3 | Every tuned parameter traced to the spec | |
| G4 | Falsification written before results | |

---

## If ADOPT — book entry

Copy into `strategies/BOOK.md`:

- **Name:**
- **Mechanism (one line):**
- **Session / instrument:**
- **Trigger, plain English:**
- **Prefer it when:**
- **Stand down when:**
- **Mechanical baseline:** expectancy ___R · PF ___ · max DD ___R · ___ trades/month

> The mechanical baseline is the benchmark agent discretion must beat. Write it
> down *before* the agents get discretion, or there is no way to tell whether
> discretion helped.

## If PARK — what would unblock it

| Missing | Needed to proceed |
|---|---|
| | |

## If REJECT — the failing criterion

Copy the one-line reason into `strategies/GRAVEYARD.md`. Rejections are kept so
we don't spend another week on this idea in six months.

---

Signed off by Angus: ______ Date: ______
