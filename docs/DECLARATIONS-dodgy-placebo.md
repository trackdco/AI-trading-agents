# DECLARATIONS — is the iFVG trigger distinguishable from a matched coin flip?

Written and committed **before** `scripts/dodgy_placebo.py` is run. Seed 20260819, fixed
in the script, no seed search. Three controls, two populations, one pre-declared decision
rule.

## 0 — Why this is being run seventh instead of first

Six studies in this stream measured whether a **filter** improves the iFVG trigger. None
asked whether the trigger carries information. The arithmetic that prompted this:

| | full book | 08:30–11:00 |
|---|---|---|
| win rate | 32.80% | 32.28% |
| break-even at a clean 2R | 33.33% | 33.33% |
| EV gross of cost | −0.017R | −0.033R |
| cost | 0.111R | 0.077R |

**The trigger is under break-even before any friction is applied.** If a matched control
is also under break-even by the same margin, then the six filter studies were filtering
noise, and so is anything built on top.

## 1 — The controls

Each control copies its real signal's **direction**, **risk in points**, and **minute of
day**, and differs only in placement. Risk matching is not optional: an unmatched risk
distribution changes cost-in-R and would reintroduce the Law 2 denominator confound that
governs `FINDINGS-dodgy-session-split.md`.

| control | what it destroys | what it holds |
|---|---|---|
| `random_day` | the pattern | clock, direction, risk. K=5 draws averaged |
| `shift_1d` | the pattern | clock, direction, risk, **and the local volatility regime** |
| `flip` | the **direction call only** | bar, clock, risk, geometry |

`shift_1d` is the tighter of the first two. `flip` is the sharpest single question in the
study: it asks whether the trigger can tell up from down.

**Not matched, deliberately:** the stop's location at a fair-value-gap edge. That is the
claim under test.

## 2 — Statistic

Paired: each real trade is differenced against its own control before resampling, then
bootstrapped clustered by session day (BR-42). Reported in **R and dollars** (Law 3), with
win rates beside both.

## 3 — PREDICTIONS, recorded before the run

1. **`random_day` and `shift_1d` will be indistinguishable from the real book** — the
   paired difference interval will span zero on both populations. *Stated plainly: I expect
   the trigger to be worthless, not merely unprofitable.*
2. **`flip` will also span zero.** If the trigger had directional information, six filter
   studies would not all have come back inside ±1pp of win rate.
3. **If any control is beaten, it will be `random_day` and not `shift_1d`**, because
   `random_day` alone fails to hold the volatility regime, so a difference against it is
   the one most likely to be a regime artifact rather than signal.
4. **The dollar difference will agree in sign with the R difference**, because risk is
   matched by construction — this run is the one place in the stream where Law 2 cannot
   bite, and that is the point of matching on risk.

## 4 — Decision rule, fixed in advance

- **All three intervals span zero** → the trigger carries no measurable information. The
  filter programme stops. The stacked-conjunction test is not run, because a conjunction
  of filters over a null trigger cannot be interpreted.
- **`shift_1d` cleared and positive** → the trigger carries information that friction is
  eating. The conjunction and X1 become worth running, and the target is the +3.6pp of win
  rate the arithmetic in §0 requires.
- **Only `random_day` cleared** → treat as a regime artifact, not evidence. Report it and
  do not build on it.
- **Any interval clears NEGATIVE** → the trigger is worse than its own placebo, which is a
  stronger refutation than a null and must be reported as one.

## 5 — What this cannot establish

It cannot confirm the model. A control that fails to beat the trigger does not make the
trigger profitable — the book is loss-making in both currencies on every population tested
so far, and nothing here changes that. The only question on the table is whether there is
a signal *to* filter.
