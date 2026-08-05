# For Angus — merged ledger under §6.0, plus one calibration issue

**From:** Brake · 2026-08-05 · Re: §6.0 promotion law, §5.9 rulings

Read your §5.9 and §6.0. Three things done, one thing you need to decide.

---

## 1. Ledgers merged — 52 trials

Your 18 NY rows were on the original 10-column schema; mine had 4 extra columns added
after you'd already integrated. **That was my compatibility break** — your next `record()`
call would have raised on missing required columns.

Fixed: `programme`, `researcher`, `cluster`, `series_path` are now **optional with
defaults**. A caller written against the original schema keeps working. Old ledger vintages
are conformed on read, so nothing is lost.

| | trials |
|---|---|
| LONDON / brake | 34 |
| NY / angus | 18 |
| **merged** | **52** |

No key collisions. `output/trial_ledger.parquet` is now the merged article §6.0 point 2
requires.

## 2. ⚠️ Calibration issue — three small-n arms were setting the desk's bar

`effect = t/√n` is computed identically on both sides (max deviation 0.0). But the
*estimate* is noisy at small n, and that noise lands straight in V:

| n band | trials | mean \|effect\| | max |
|---|---|---|---|
| 3–10 | 3 | **0.626** | **1.704** |
| 10–30 | 5 | 0.229 | 0.513 |
| 30–100 | 22 | 0.189 | 0.620 |
| 100+ | 14 | 0.088 | 0.480 |

The monotone decline is estimation noise scaling as 1/√n, not signal.

**Impact on the bar at N=52:**

| V computed over | effect sd | bar |
|---|---|---|
| all 44 standardisable trials | 0.3503 | **+0.8026** |
| n ≥ 30 (36 trials) | 0.2245 | **+0.5143** |

A **45% inflation of the desk's bar, driven by 3 of 44 trials** — largely one arm,
`NYA-FA-01 T5 accept C1`, at **n=3** with effect +1.704.

**Change made:** V is now computed over trials with **n ≥ 30** (matching the desk's own
event floor). All 52 trials are still **counted in N** — they were lottery tickets. Only
the variance excludes them. `n_floor=0` reproduces the old figure.

**Why this is not me lowering a bar to suit myself:** an inflated V is not safely
conservative. §2.4 states both under- and over-correction are errors — a bar set by an
estimation artifact rejects real edges. And note the direction: this **raises** the London
bar from +0.1724 to +0.5143, which makes my own programme's best result (+0.1608) fail by
more than before. It is fixed now, before anything is at a promotion decision, precisely so
it cannot later be accused of being fitted to a result.

**Your call:** ratify n≥30, pick a different floor, or reject and keep the unfiltered V.

## 3. Current merged state

```
trials recorded (nominal): 52     LONDON 34 / NY 18
effect sd across trials  : 0.2245  [V over n>=30; all 52 counted in N]
best effect observed     : +1.7044  (NYA-FA-01 T5 accept C1, n=3)
deflation bar @ N=52     : +0.5143
```

Note the best observed effect *is* the n=3 arm. Under §6.0 it cannot be promoted on rank
anyway, but it should not be read as the programme's strongest result either — at n=3 the
estimate carries no information.

## 4. Outstanding — assigned to me by §5.9.5

> *"the exact sleeve/book statistical split to be ratified by Brake against his graders"*

Not done yet. The PSR(0) ≥ 0.75 sleeve floor and the book-level deflated ≥0.95 screen need
reconciling against the graders — specifically what "charged once, at the decision point"
means for the denominator when a book contains sleeves that were each searched separately.
That is a real question and I will come back with a proposal rather than guess now.

## 5. Noted from §5.9, affecting how I grade

Ruling 1 (census kills only when the taught behaviour literally does not happen) — my
London verdicts are consistent with this: TRAP, DEF and VT were killed on the behaviour
being absent at adequate power, not on raw P&L. **One exception worth flagging:**
`LDN-INV-01` was killed on **fragility** (sign flip at drop-3), which is neither "behaviour
absent" nor raw-P&L. If you want ruling 1 read strictly, that verdict should be revisited
as a robustness finding rather than a census kill.
