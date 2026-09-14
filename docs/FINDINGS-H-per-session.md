
# FINDINGS — PER-SESSION BOOKS (2026-08-07)

Three books, scored, selected and risk-budgeted separately. **Never
pooled, never averaged.** sweep_b in London only. Fit-only; holdout look #1
amended to match, before any sealed row was read.

**Headline: London is the book. NY_PRE and NY_AM are not standalone-viable
— they graduate 3–11% against London's 98.5%. And the concordance count
that FAILED on the pooled book CONFIRMS in London on the frozen
split-half.**

---

## 1. The three books

| book | window (NY) | composition | fights/day | EV | H2-2025 | H1-2026 | zero-days |
|---|---|---|---|---|---|---|---|
| **LONDON** | 03:00–04:59 | composite + sweep_b (367) | 2.28 | **+0.357** [+0.222,+0.503] | +0.347 ! | +0.370 ! | 58/291 |
| NY_PRE | 08:00–09:29 | composite | 0.86 | +0.286 [+0.063,+0.537] | +0.343 ! | +0.221 | 128/291 |
| NY_AM | 09:30–10:30 | composite | 1.36 | +0.171 [+0.018,+0.343] | +0.115 | +0.237 | 82/291 |

`!` = day-boot CI clear of zero.

**Only London clears both eras.** NY_PRE clears H2-2025 only; NY_AM clears
neither era individually (its pooled CI barely clears at +0.018). Splitting
the sessions exposed this — the pooled window book (+0.277, both eras
clear) was averaging one strong session with two weak ones.

## 2. P(graduate) per session, at each book's own frequency

| book | policy | GRAD | P(death) | net |
|---|---|---|---|---|
| **LONDON** | cushion k=.05 | **98.5%** | 5.5% | $8,796 |
| LONDON | flat $150 | 97.1% | 5.6% | $8,762 |
| NY_PRE | cushion k=.05 | **9.7%** | 14.3% | $2,529 |
| NY_AM | cushion k=.05 | **11.2%** | 24.5% | $2,438 |

**This is the decisive number.** London alone graduates 98.5% — matching
the all-session composite's ~100% — at 2.28 fights/day instead of 11.42,
because its EV is roughly double. NY_PRE and NY_AM graduate 3–11%: too
infrequent *and* too low-EV to reach five payouts inside a year on their
own. They are not businesses by themselves.

They may still be worth trading **alongside** London (they add dollars
without London's risk budget), but they cannot be declared standalone
books, and any plan that funds an account on NY_PRE or NY_AM alone fails.

## 3. Risk: can a single session breach the $2,000 EOD drawdown?

Daily total R per session against the drawdown expressed in R at each size:

| book | worst fit day | DD in R @$150 / $300 / $450 / $600 | breach days | **max safe size** |
|---|---|---|---|---|
| LONDON | **−5.41R** | 13.33 / 6.67 / 4.44 / 3.33 | 0 / 0 / **2** / **10** | **$300** |
| NY_PRE | −3.48R | " | 0 / 0 / 0 / **1** | **$450** |
| NY_AM | −3.07R | " | 0 / 0 / 0 / 0 | **$600** |

London is the highest-EV book *and* the one that must be sized smallest —
its worst day is −5.41R, which at $450 is −$2,436 and breaches outright.
At $300 the worst fit day costs $1,624, leaving $376 of the daily
allowance. **$300 is the cap for London**, and that is a fit-measured
ceiling, not a target.

Note this metric answers a different question from item 3's concurrency
work, and it is the one that binds: London's peak *concurrent* exposure is
low, but its worst *daily total* is what approaches the barrier.

## 4. Selection variables re-scored per session

Every variable was previously measured on a population that is not the
book. Re-scored inside each session's own book (lift = q·(EV−μ_cut)/(1−q)):

| variable | LONDON (EV +0.357) | NY_PRE (EV +0.286) | NY_AM (EV +0.171) |
|---|---|---|---|
| CONCORD < 7 | **+0.239** | +0.066 | +0.066 |
| CONCORD < 5 | **+0.128** | −0.059 | −0.017 |
| closeloc < Q1 | +0.080 | +0.061 | +0.047 |
| S1 flowconf==0 | +0.062 | **+0.157** | −0.007 |
| dep_thickness_vs_day < Q1 | +0.067 | −0.070 | +0.043 |
| dep_imbalance < Q1 | +0.005 | +0.005 | −0.014 |
| support_minus_resist < Q1 | −0.044 | −0.068 | −0.022 |
| support_wall_dist < Q1 | −0.023 | −0.003 | **+0.068** |
| support_wall_size < Q1 | +0.027 | −0.078 | −0.008 |
| dep_thickness_delta_5m < Q1 | −0.020 | +0.035 | +0.041 |

**The variables behave differently by session, which is why the pooled
measurements were uninformative.** CONCORD is strong in London and near-nil
in NY. S1 is strong in NY_PRE and dead in NY_AM. The depth six remain
mostly negative everywhere — no session rescues them.

In-trade recovery flag (t+5, cumulative-delta sign), per session:

| book | underwater n | base P(recover) | precision | recall |
|---|---|---|---|---|
| LONDON | 328 | 22.3% | **33.3%** | 37.0% |
| NY_PRE | 133 | 12.8% | 8.3% (worse than base) | 11.8% |
| NY_AM | 190 | 14.2% | 15.6% | 18.5% |

The in-trade flag only works in London (+11pp precision at 37% recall).
In NY_PRE it is actively worse than the base rate.

## 5. CONCORD in London — it confirms on the frozen split-half

The concordance count **failed** on the pooled all-session book (max lift
+0.046, half-2 collapse). Re-scored in London, on the same frozen day-split
and the same seed:

| candidate | full-book lift | half-1 | half-2 | verdict |
|---|---|---|---|---|
| **CONCORD < 7** | **+0.239** | +0.153 | **+0.342** | **CONFIRMS** |
| CONCORD < 5 | +0.128 | +0.108 | +0.146 | **CONFIRMS** |
| closeloc < Q1 | +0.080 | +0.066 | +0.095 | **CONFIRMS** |
| S1 flowconf==0 | +0.062 | −0.029 | +0.166 | no |
| dep_thickness_vs_day < Q1 | +0.067 | +0.038 | +0.099 | no |

The London book after cutting CONCORD < 7:

```
294 fights | 1.01/day | EV +0.596 [+0.356,+0.839]
  H2-2025 +0.688 [+0.411,+0.988]!   H1-2026 +0.486 [+0.123,+0.905]!
worst day -4.18R | zero-days 127/291
breaches: none at $150/$300/$450 — one at $600
```

Cutting raises EV from +0.357 to **+0.596** and *lowers* the worst day
(−5.41 → −4.18R), which raises the safe size ceiling from $300 to $450.
Both effects push the same way:

| London config | /day | EV | max safe size | GRAD | $/day |
|---|---|---|---|---|---|
| uncut @ $300 | 2.28 | +0.357 | $300 | 98.5% | $245 |
| CONCORD≥7 @ $300 | 1.01 | +0.596 | $450 | 97.4% | $181 |
| **CONCORD≥7 @ $450** | 1.01 | +0.596 | $450 | **96.2%** | **$271** |

**Read this carefully: the cut does NOT improve graduation** (98.5% uncut
vs 96.2% cut-and-sized-up). It improves dollars per day ($245 → $271) and
per-trade quality, at 44% of the frequency and with 127 blank days. Under
the payout cap, graduation is the objective and the uncut book wins it.
The cut is a *sizing* opportunity, not a graduation one.

## 6. Caveats I am not burying

- **These selection numbers are in-sample and uncorrected.** The
  split-half confirmations above are real and used the pre-existing frozen
  split, but 5 candidates × 3 sessions = **15 cells**, and no Bonferroni
  was applied to the per-session re-scoring. CONCORD<7 in London would
  survive a ×15 correction on magnitude; the marginal ones would not.
- **The London book was chosen partly because it looked best.** Selecting
  a population on its own performance and then measuring selection
  variables inside it inherits that selection. The confirmations are
  suggestive, not established.
- **Nothing here goes to the holdout.** Per R0 the sealed look tests the
  UNSELECTED per-session base rates only. CONCORD, closeloc and S1 ship on
  fit + forward validation via the seven-locus recorder.
- **NY_PRE/NY_AM may be underpowered on the holdout**, not merely wrong.
  R3 now declares the threshold (<100 fights in a block ⇒ UNDERPOWERED,
  neither passed nor failed) so that a thin result is not read as a
  refutation.

## 7. Holdout look #1 — AMENDED, still unspent

`DECLARATIONS-holdout-look-1.md` rewritten to the per-session book:
**five claims** (LONDON, NY_PRE, NY_AM base rates, sweep_b-London alone,
and the queued closeloc cut) at **Bonferroni ×5**, two blocks both must
pass, per-session windows applied by NY clock, X=0.5W not re-tuned,
aggregation fixed, pass/fail meaning pre-committed, and the per-session
size caps recorded so a pass is not read as licence to size past the
measured breach point. It also declares in advance that NY_PRE and NY_AM
are expected to be the weak claims — so a fail there is confirmation of a
known fit-side weakness rather than new information.

**No sealed row has been read.**
