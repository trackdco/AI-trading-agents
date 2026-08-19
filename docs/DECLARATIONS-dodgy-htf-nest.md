# DECLARATIONS — X1, the higher-timeframe nest, as its own trigger

Written and committed **before** `scripts/dodgy_htf_nest.py` is run. Seed 20260819.

## 0 — Why this is run at all, when the trigger is null

`FINDINGS-dodgy-placebo.md` established that the 1-minute iFVG carries no measurable
information on NQ: flipped backwards it produces the same book (+0.0015R, n=81,038). §4
of that declaration bars a stacked-conjunction test over a null trigger, because filters
redistribute expectancy and cannot manufacture it.

**X1 is exempt from that bar for one specific reason: it is not a filter.** He states it
as a change of population — *"Ideally what we're looking for is us to tap into a giant 1
hour or 4 hour fair value gap and then find a one minute entry out of that rally gap. So,
it's a trade off of a trade"* (`RESEARCH-dodgysdd-lecture.md` X1) — and *"I'm only looking
at like the one or 4 hour order block. I don't really care like the daily, the weekly."*
The claim is that the 1m tape behaves differently inside a higher-timeframe zone. That is
a testable proposition about a subpopulation, and the placebo result does not reach it.

**This is the last live item in the lecture.** If it fails, the model has been tested as
completely as its stated form allows.

## 1 — Construction

**Zones.** Higher-timeframe candles are binned by hours elapsed since each session's 18:00
open, not by clock time, so the bins are DST-safe and the 4h boundaries fall on
22:00/02:00/06:00/**10:00**/14:00/18:00 ET — which matches his own R1 claim that 10:00 is a
4-hour candle close.

| type | definition (his words) | born |
|---|---|---|
| FVG | three-candle imbalance, `low[k] > high[k-2]` and the mirror | at the **close** of candle k |
| OB | *"a red candle sandwiched between two green candles"* — a down-close candle whose successor closes above its high | at the **close** of the confirming candle |

A zone is live from its birth bar until price **closes beyond its far side** (mitigated) or
it exceeds `max_age` HTF candles. `htf ∈ {1h, 4h}` are the declared primaries; **15m is a
robustness row only** and is not eligible to be reported as a finding.

**In-zone** means the 1-minute signal bar's close lies within the zone. No lookahead: a
zone cannot be used before the HTF candle that completes it has closed.

## 2 — Arms

1. **baseline** — the whole book, as a control.
2. **in-zone**, for each of {1h, 4h} × {FVG, OB}.
3. **his set** — inside a 1h *or* 4h FVG *or* OB.
4. **X2** — his set, but the stop is placed at the far edge of the **HTF** zone rather than
   the 1m gap edge: *"I got stopped out on the one minute time frame, but we still held the
   five-minute for gap."*

## 3 — The placebo, and why its pool must be restricted

Each arm gets a matched control by the method of `DECLARATIONS-dodgy-placebo.md` —
direction, realized risk in points and minute of day copied, stop re-derived from the
control's own entry, `audit()` asserting no control stop can sit on the winning side.

**The control pool is drawn only from bars that are themselves in-zone.** This is the whole
point of the design. An unrestricted pool would measure whether *the higher-timeframe zone*
is a good place to be, which is a different and much easier question; restricting it asks
the question that matters — **given that price is inside a 1h/4h zone, does his 1-minute
trigger beat a coin flip taken there?**

## 4 — PREDICTIONS, recorded before the run

1. **In-zone signals will be a minority of the book, between 5% and 40%.** If the
   restriction turns out to be near-total, it is not a population change and the arm is
   uninterpretable.
2. **No arm will reach break-even.** Break-even requires +0.128R full-book / +0.109R
   in-window, and nothing measured in this stream has moved EV by more than 0.03R.
3. **The in-zone trigger will be indistinguishable from the in-zone placebo** — the paired
   difference will span zero, as it did unrestricted.
4. **X2 will improve EV in R and worsen it in dollars.** A wider stop shrinks cost-in-R
   while raising dollars at risk. This is Law 2 and it is the same trap that made New York
   look like the best session in R and the worst in dollars.

## 5 — Decision rule, fixed in advance

- **Paired difference vs the in-zone placebo spans zero** → X1 does not rescue the trigger.
  The model is refuted in its stated form and the programme ends. No further filters.
- **Difference clears zero AND the arm's own net EV clears zero AND it clears both era
  halves (E1.4)** → a genuine finding. It would still be fit-side and would need
  confirmation on data this analysis has not touched.
- **Difference clears zero but net EV does not** → the trigger has information inside the
  zone that friction still eats. Report it, do not trade it, and the next question is X2's
  cost arithmetic **priced in dollars**, not in R.
- **X2 improves R but not dollars** → it is the denominator, not an edge. Say so plainly.

## 6 — What this cannot establish

It cannot test his discretionary selection. He takes 1–3 trades a day and this book is 88;
whatever reduces one to the other is not stated in codable form anywhere in 23h 56m of
lecture. If X1 fails, that gap — not a further parameter — is the honest residual.
