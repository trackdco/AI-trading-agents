# FINDINGS — the iFVG trigger is not distinguishable from a matched coin flip

Run against `DECLARATIONS-dodgy-placebo.md`, committed before the run (`344a308`). Seed
20260819, K=5, no seed search. NQ, 1,251,240 bars, 2023-01 → 2026-07. Paired
day-clustered bootstrap on the real-minus-control difference.

**Read the CORRECTION at the foot of this document first if you are checking the method.**
The first version of this script was wrong in a way that produced a spectacular fake
result, and the guard that now prevents it is the most reusable thing here.

## The controls

Each control copies its signal's **direction**, **realized risk in points**, and **minute
of day**, and differs only in placement. Stops are re-derived from the control's own entry,
so risk matches to 1e-9 and cost-in-R is identical between arms — this is the one study in
the stream where Law 2 cannot bite.

## 1 — The result

| population | control | n pairs | real EV | control EV | **difference** | 95% CI | verdict |
|---|---|---|---|---|---|---|---|
| full book | `random_day` | 81,038 | −0.1277 | −0.1461 | **+0.0183** | [+0.0078, +0.0292] | real > placebo |
| full book | `shift_1d` | 80,922 | −0.1279 | −0.1352 | +0.0073 | [−0.0056, +0.0213] | indistinguishable |
| full book | **`flip`** | 81,038 | −0.1277 | −0.1292 | **+0.0015** | [−0.0146, +0.0179] | **indistinguishable** |
| 08:30–11:00 | `random_day` | 9,660 | −0.1092 | −0.1340 | +0.0249 | [−0.0054, +0.0553] | indistinguishable |
| 08:30–11:00 | `shift_1d` | 9,649 | −0.1096 | −0.1433 | +0.0337 | [−0.0042, +0.0717] | indistinguishable |
| 08:30–11:00 | `flip` | 9,660 | −0.1092 | −0.1203 | +0.0111 | [−0.0360, +0.0585] | indistinguishable |

Win rates: real 32.28–32.80%, controls **31.2–32.7%**. A matched coin flip on this
instrument wins about as often as the trigger does.

## 2 — Five of six cells are indistinguishable, and the sixth was pre-declared as an artifact

**`flip` is the sharpest number in the study.** Take the identical signals, at the identical
bars, with identical risk, and trade every one of them **backwards** — you get
**+0.0015R** worse, on 81,038 pairs, CI [−0.0146, +0.0179]. The trigger cannot tell up from
down. Every filter study in this stream has been sorting a book whose direction is a coin
flip.

**`random_day` on the full book is the one cell that clears zero**, at +0.0183R. §3 of the
declaration predicted in advance that *if* anything cleared it would be `random_day` and
not `shift_1d`, "because `random_day` alone fails to hold the volatility regime, so a
difference against it is the one most likely to be a regime artifact rather than signal."
That is exactly what happened: scattering entries across 3.5 years at the same minute of
day samples a different volatility mix, and `shift_1d` — which holds the regime as well as
the clock — falls to +0.0073R and spans zero.

**Decision rule §4, as written: "Only `random_day` cleared → treat as a regime artifact, not
evidence. Report it and do not build on it."** That branch fired. It is reported and it is
not built on.

## 3 — Even taken at face value, the effect is a fraction of what is needed

To break even the book needs **+0.128R** of gross expectancy full-book (**+0.109R**
in-window) — equivalently **+4.2pp** of win rate at 2R full-book, **+3.6pp** in-window.

| | R | as win rate at 2R |
|---|---|---|
| required to break even (full book) | **+0.128** | **+4.2pp** |
| measured vs `random_day` (the generous control) | +0.018 | +0.6pp |
| measured vs `shift_1d` (the tight control) | +0.007 | +0.2pp |
| measured vs `flip` (direction only) | +0.002 | +0.05pp |

**The trigger's entire measurable information content is at most 14% of the friction it has
to clear, and against the tighter control it is 6%.** No arrangement of filters over a
signal this weak reaches break-even, because filters redistribute a book's expectancy; they
do not manufacture it.

## 4 — The four predictions, scored

| # | prediction | outcome |
|---|---|---|
| 1 | `random_day` and `shift_1d` both span zero | **SPLIT** — `shift_1d` confirmed on both populations; `random_day` refuted full-book, confirmed in-window |
| 2 | `flip` spans zero | **CONFIRMED**, on both populations, and by the largest margin |
| 3 | if anything clears it will be `random_day`, not `shift_1d` | **CONFIRMED** — precisely the cell that cleared |
| 4 | dollar difference agrees in sign with R | **SPLIT** — agrees on all three full-book cells; disagrees on two in-window cells, where every dollar interval is wide enough to span zero and neither sign is interpretable |

## 5 — What this settles, and what it does not

**Settles.** There is no measurable signal in the iFVG trigger on NQ, at 1-minute
resolution, over 2023-01 → 2026-07, on 81,038 trades. This retro-explains the whole stream:
the sweep subtracted, obviousness showed no trend, rule 4 was inert, the near draw set
moved nothing, the session reversed under a currency change. **Those studies were not
finding weak filters. They were sorting noise, and noise does not sort.**

**Does not settle.** This is a test of *the trigger as implemented*, which is the
1-minute E1/E3 predicate. It does not test:

- **X1, the higher-timeframe nest** — his stated core, *"a trade off of a trade"*: a 1m
  entry taken **only while price sits inside a 1h/4h FVG or order block**. That is a
  different population, not a filter on this one, and it is the single claim this result
  does not reach.
- **his discretionary selection.** He takes 1–3 trades a day; this book is 88. Whatever
  reduces one to the other is not in the lecture in codable form.

**On the conjunction test.** §4 of the declaration says a stacked-conjunction test is not
run when the trigger is null, "because a conjunction of filters over a null trigger cannot
be interpreted." That still holds for filters *on this population*. X1 is not in that
category — it changes the population rather than filtering it — so it remains the one
live item, and it should be run as its own trigger with its own placebo, not as a filter.

---

# CORRECTION — the first version of this test produced a fake result, and how it was caught

The first run reported the **placebo beating the trigger by 0.60R**, with a placebo win
rate of **74.6%** and a `flip` control winning **99.98%** of its trades and making
**+$136 a trade**.

**None of that was reported as a finding, because a matched coin flip cannot win 74.6% and
nothing wins 99.98%.** The absurdity was the detection route, for the third time in this
stream after the 0%-availability Asia levels and the 16.7 median reward:risk.

**The bug.** `placebo()` copied each real signal's **stop price** — an absolute number —
onto a different bar, or onto a flipped direction. At the new entry that price is unrelated
to the trade and frequently sits on the **winning** side, so `simulate()`'s stop check
fired on the entry bar itself and booked an instant +1R. A control that cannot lose is not
a control.

The declaration promised matching on *"risk in points"*. The code matched on stop price.
**The specification was right and the implementation did not follow it** — which is the
failure mode that pre-registration alone does not catch.

**The fix, and the guard that generalises.** Stops are now re-derived per control as
`entry − direction × risk`, and `audit()` asserts before every run that (a) **no** control
stop sits on the winning side of its own entry and (b) control risk matches real risk to
1e-9. The guard immediately caught a second, smaller problem the fix had not addressed —
0.03% of signals whose next open sits exactly *on* their stop, giving risk 0 — which are
discarded by the 2-point floor and are now excluded from the check explicitly rather than
silently.

**Any placebo built from a real book must assert that the control can lose.** That check
costs two lines and would have caught this before the numbers were ever printed.
