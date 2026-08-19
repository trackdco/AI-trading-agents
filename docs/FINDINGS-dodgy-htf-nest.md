# FINDINGS — X1, the higher-timeframe nest: a whisker of information, a fraction of the bar

Run against `DECLARATIONS-dodgy-htf-nest.md`, committed before the run (`2533f6c`).
NQ, 1,251,240 bars, 2023-01 → 2026-07, 85,277 signals. Seed 20260819.

X1 was the last live item in the lecture, and the only claim
`FINDINGS-dodgy-placebo.md` did not reach — because he states it as a change of
population rather than a filter: *"tap into a giant 1 hour or 4 hour fair value gap and
then find a one minute entry out of that rally gap. So, it's a trade off of a trade."*

**Binning confirmed against his own claim before anything was measured.** Higher-timeframe
candles are binned by hours elapsed since each session's 18:00 open, which is DST-safe and
puts 4h closes on 02/06/**10**/14/17/22 ET — 99.2% of all boundaries. 10:00 being a 4-hour
close is his R1 claim, so the binning is the one he is describing. (17:00 rather than 18:00
is the CME maintenance break: the 14:00–18:00 bin holds no bars past 17:00.)

## 1 — The arms

| arm | signals | % of book | win % | **gross EV** | net EV | 95% CI | H1 | H2 | eras |
|---|---|---|---|---|---|---|---|---|---|
| baseline (all) | 81,038 | 100 | 32.80 | −0.017 | −0.128 | [−0.138, −0.117] | −0.148 | −0.110 | — |
| 1h FVG | 10,842 | 13.4 | 32.47 | −0.027 | −0.143 | [−0.169, −0.117] | −0.174 | −0.115 | — |
| **1h OB** | 15,285 | 19.1 | 33.07 | −0.009 | −0.127 | [−0.149, −0.105] | −0.149 | −0.106 | — |
| 4h FVG | 11,321 | 13.9 | 32.70 | −0.021 | −0.129 | [−0.156, −0.103] | −0.138 | −0.122 | — |
| **4h OB** | 12,884 | 15.9 | 33.21 | **−0.005** | **−0.115** | [−0.139, −0.093] | −0.151 | −0.085 | — |
| his set (1h/4h, FVG+OB) | 38,958 | 48.2 | 32.95 | −0.013 | −0.126 | [−0.140, −0.112] | −0.151 | −0.104 | — |
| 15m FVG *(robustness only)* | 10,825 | 13.4 | 32.13 | −0.037 | −0.150 | [−0.176, −0.125] | −0.174 | −0.128 | — |

**Prediction 2 confirmed: no arm reaches break-even.** Every interval sits entirely below
zero. The best arm, 4h OB, is −0.115R against a baseline of −0.128R.

**Prediction 1 partly violated, and it matters.** The four primary arms restrict to
13.4–19.1% of the book, inside the declared 5–40% band. **His combined set does not: at
48.2% it is barely a restriction at all**, and §4 of the declaration said in advance that
a near-total restriction is not a population change. That arm should be read as weak, and
it is one of the two that clears below.

## 2 — Against an in-zone coin flip

The control pool is drawn **only from bars that are themselves inside the zone**, so this
asks the question that matters: given that price is inside a 1h/4h zone, does his 1-minute
trigger beat a random entry taken there? Direction, realized risk and minute of day
matched; `audit()` asserts no control stop can sit on the winning side.

| arm | n pairs | real | control | **difference** | 95% CI | verdict |
|---|---|---|---|---|---|---|
| 1h FVG | 10,842 | −0.1428 | −0.1487 | +0.0059 | [−0.0222, +0.0338] | indistinguishable |
| **1h OB** | 15,285 | −0.1267 | −0.1510 | **+0.0243** | **[+0.0018, +0.0476]** | real > placebo |
| 4h FVG | 11,321 | −0.1290 | −0.1431 | +0.0141 | [−0.0141, +0.0432] | indistinguishable |
| 4h OB | 12,884 | −0.1154 | −0.1359 | +0.0205 | [−0.0033, +0.0455] | indistinguishable |
| his set | 38,958 | −0.1259 | −0.1430 | **+0.0171** | **[+0.0026, +0.0319]** | real > placebo |
| X2 (HTF stop) | 39,485 | −0.0422 | −0.0344 | −0.0078 | [−0.0220, +0.0075] | indistinguishable |
| 15m FVG | 10,825 | −0.1501 | −0.1471 | −0.0030 | [−0.0319, +0.0244] | indistinguishable |

**Five of seven are indistinguishable. Two clear zero, and both clear it by a hair.**
Lower bounds of **+0.0018** and **+0.0026**. Three qualifications, all of which cut the
same way:

1. **Against the bar, this is nothing.** Break-even needs **+0.128R**. The largest
   difference measured is **+0.024R — 19% of the requirement.** Inside the zone the trigger
   is very slightly better than a coin flip and nowhere near better than the friction.
2. **Multiplicity was not pre-specified, and it should have been.** Five primary arms at
   95% gives roughly a 23% chance of at least one false positive by luck. With lower bounds
   this close to zero, any correction erases both cells. I did not declare a correction in
   advance, so I am not applying one after the fact — but the reader should treat two
   marginal clearances out of five as consistent with chance.
3. **Neither clears both eras**, and the weaker of the two (his set) is the arm whose 48.2%
   coverage breaches the declared interpretability condition.

**One pattern worth recording without believing it.** Both **order block** arms sit at
+0.020/+0.024 and both **FVG** arms at +0.006/+0.014 — the OB side is consistently higher,
including on gross EV (−0.005/−0.009 against −0.021/−0.027). That is the right shape for a
real effect and far too small to act on. It is the only thing in this stream pointing
anywhere, and he explicitly dismisses order blocks relative to FVGs.

## 3 — X2 is the cost denominator, and this is the cleanest proof of it in the ledger

*"I got stopped out on the one minute time frame, but we still held the five-minute for
gap"* — so the stop belongs at the higher-timeframe zone edge. Applied to his set:

| | median stop | cost in R | win % | **gross EV** | net EV | **$/trade** | $/day |
|---|---|---|---|---|---|---|---|
| his set, 1m stop | 4.75 pt | 0.105 | 32.95 | **−0.013** | −0.126 | **−$10.46** | −$446 |
| **X2, HTF stop** | **35.50 pt** | **0.014** | 39.14 | **−0.013** | **−0.042** | **−$26.17** | **−$1,128** |

**Net EV improves by +0.084R. Gross EV does not move at all — −0.013 in both arms, to
three decimals.** The stop widens 7.5×, cost-in-R falls from 0.105 to 0.014, and every
point of the "improvement" is that arithmetic. In dollars the same trade costs **2.5× more**
per trade and **2.5× more** per day.

**Prediction 4, confirmed exactly as written.** This is Law 2 in its purest observed form:
a rule that looks like a 0.084R edge, has literally zero effect on gross expectancy, and
loses two and a half times as much money. Anyone reading only EV-in-R would adopt it.

X2 is also indistinguishable from its own in-zone placebo (−0.0078, spanning zero) — the
wider stop does not make the *trigger* any better either.

## 4 — The predictions, scored

| # | prediction | outcome |
|---|---|---|
| 1 | in-zone share between 5% and 40% | **SPLIT** — primaries 13.4–19.1% ✓; his combined set 48.2% ✗, and that arm is one of the two that clears |
| 2 | no arm reaches break-even | **CONFIRMED** — every interval entirely below zero |
| 3 | in-zone trigger indistinguishable from in-zone placebo | **SPLIT** — 5 of 7 confirmed; 1h OB and his set clear by lower bounds of +0.0018 and +0.0026 |
| 4 | X2 improves R and worsens dollars | **CONFIRMED** — +0.084R in R, identical gross, −$10.46 → −$26.17 |

## 5 — Decision rule, applied

§5 of the declaration, verbatim: *"Difference clears zero but net EV does not → the trigger
has information inside the zone that friction still eats. Report it, do not trade it, and
the next question is X2's cost arithmetic priced in dollars, not in R."*

**That branch fired, and X2 was priced in the same run: it is the denominator, not an
edge.** Saying so plainly, as the rule requires.

## 6 — Standing conclusion for the whole stream

X1 was the last item in the lecture that had not been tested. It is now tested, and it does
not rescue the model:

- the 1-minute trigger carries no measurable information unrestricted (`flip`: +0.0015R on
  81,038 pairs);
- inside a 1h/4h zone it carries at most **+0.024R**, on 2 of 7 arms, by a hair, without
  multiplicity control and without era stability;
- **+0.128R is required to clear friction.** The gap is roughly five-fold;
- his own stop rule closes that gap on paper and widens it 2.5× in money.

**The DodgysDD model, in the form stated across 23h 56m of lecture, is refuted on NQ
2023-01 → 2026-07.** Every codable component has now been measured: the trigger, the sweep,
obviousness, the four E5 rules, the draw set, the equal-highs ladder, the exit, the
break-even rule, the session and macro windows, and the higher-timeframe nest.

**The honest residual is not a parameter.** He takes 1–3 trades a day; this book is 88. The
selection that reduces one to the other is discretionary — *"if I back away 10 feet from
the screen and it's obvious to me"* — and is not stated in codable form anywhere in the
corpus. That gap cannot be closed by more testing of what he said. It could only be closed
by data on what he actually traded.

**Not refuted, because never testable:** L2 trend lines (no fitting rule), E5 rule 2
obviousness at any threshold beyond the three already swept, and F1, which remains
untested and is now the only cheap item left on the board.
