# <Strategy Name> — Hypothesis

**Stage 2. This is the cheapest gate in the pipeline — most candidates should
die here, before anyone spends compute.**

---

## The mechanism (one paragraph, plain English)

_Why should this make money? Who is on the other side, and why do they keep
taking that trade?_

_Good: "Europe's open leaves resting orders stacked above the Asian high. Price
runs them at London open because that's where the liquidity is, then the move
fails because the buyers who lifted it were stop-driven, not real. We sell the
failure."_

_Bad: "When the 21 EMA crosses the 50 EMA, momentum is confirmed." That's a
description of an indicator, not a reason anyone loses money to us._

> 

## What would have to be true

For the mechanism to hold, these must be observable in the data:

1. 
2. 
3. 

## What would falsify it

**Write this before seeing any results.** It is the difference between running a
test and running a search for confirmation.

- If ______, the mechanism is wrong and we drop it.
- If ______, the mechanism is real but not tradeable by us.

## Session and instrument — and why

_The mechanism should imply the session. If a setup works equally well at every
hour of the day, that's evidence it isn't the mechanism you think it is._

- Session: 
- Instrument: 
- Why this session follows from the mechanism: 

## Relationship to what we already trade

- Does this overlap with an existing book entry? 
- If it fires in the same window as an incumbent, what's the argument it's a
  different trade rather than the same one relabelled?

## Discretion count (from the dossier)

- Discretionary points: _N_
- Assessment: mechanisable / borderline / style-not-strategy

## Data required

Check `context/data-inventory.md` **now**, not at Stage 7.

| Needs | Have it? | If not, fallback |
|---|---|---|
| 1-minute bars, in-sample window | | |
| 1-minute bars, OOS window | | |
| Heatmap (MBP-10) at entry | | |
| CVD at entry | | |

## Stage 2 verdict

- [ ] **PROCEED** — mechanism is plausible and stated, discretion is manageable
- [ ] **REJECT** — reason: 

Signed off by Angus: ______ Date: ______
