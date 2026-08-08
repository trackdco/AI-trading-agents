# FINDINGS — THE LOSERS DIAGNOSIS, and the end of the mechanical search

2026-08-08. The full attempt to separate the trades that die from the
trades that run, on the corrected (episode-M1) race census: 3,153
fights, 290 days. Fit-only, no holdout, report-only, nothing adopted.

---

## 1. THE PROBLEM, STATED IN ITS OWN ARITHMETIC

| | |
|---|---|
| fights that run **< 0.5R** before stopping | **1,000 (31.7%)** |
| what they cost | **−1,098R** |
| the entire book's P&L | **−392R** |
| remove exactly those, change nothing else | **EV −0.124 → +0.328R**, P(3R) **25.1% → 36.7%** |
| value of identifying them | **+0.452R per trade** |

The book is bimodal, not continuous:

| | share | median peak | bars held | median run |
|---|---|---|---|---|
| never reaches 1R | 48.2% | **minute 0** | 2 | 0.33R |
| 1R–3R | 26.7% | 5 min | 14 | 1.67R |
| reaches 3R+ | 25.1% | 55 min | 136 | **6.15R** |

Half the book dies in two bars; a quarter runs for two hours. **The junk
tail is the entire problem** — everything else is noise around it.

**The decision-relevant target**: the trader's actual exit (75% at 3R +
15m trail) pays +2.757R when 3R is reached and −1.088R when it isn't,
so it needs **P(3R) ≥ 28.3%**. The unselected population delivers
**25.1%**. Selection must add **+3.2 points**.

---

## 2. THE EXIT IS NOT THE PROBLEM (three independent proofs)

The obvious hypothesis — that the census scored the wrong exit — was
tested and is **false**.

1. **The trader's real exit makes it worse**: EV −0.124
   [−0.187,−0.054] vs −0.069 under the structural target. Win rate
   collapses 38.6% → 25.2%. It *did* fix the specific defect it was
   meant to (3R+ runners ending negative fell 14.6% → 1.5%), but
   chasing 3R gives up the small structural touches, worth +1,094R
   across 2,363 fights.
2. **Every flat target is within ~1 point of its own break-even**:
   1R needs 50% / has 51.8%; 2R needs 33.3% / has 34.2%; 3R needs 25% /
   has 25.1%; 4R needs 20% / has 19.4%. **The population is fairly
   priced at every horizon** — which is why no exit can rescue it.
3. **Every structural variant loses**: full exit at structure 2 or 3,
   75/25 splits, runner trailed vs untargeted, across a −0.5/−0.75/−1R
   stop grid. 0 of 48 cells positive, 15 negative; the current
   structure-1 full exit is unbeatable, and moving the target further
   out is *reliably worse* in M2 (the only family clearing its null).

**The runner is diagnosed**: when it survives it pays +2R to +16R, but
the break-even stop forecloses it **90–95%** of the time — which is why
its target choice barely matters.

---

## 3. AT ENTRY: NOTHING SEPARATES. THIS IS NOW DEFINITIVE.

Three levels of search, each calibrated against shuffled data:

| level | scope | result |
|---|---|---|
| **univariate** | 111 variables × 9 cells, ~2,646 tests | 130 "survivors" vs **112 ± 17 on shuffled data** (z = +1.05); 32 of them also survive on shuffled outcomes |
| **combinations** | all pairs+triples of 18 flow/depth signals, 8,721 tests | best real result **beaten by 9 of 10 shuffled searches** |
| **multivariate** | 5 models, 112 features, day-grouped CV | best AUC **0.522 vs null 0.501 ± 0.017, z = +1.20** — not significant |

The multivariate decision test is the clincher: skipping the model's
worst 30% gives EV −0.0998 / P(3R) 25.65%, against **randomly** dropping
30% at −0.1240 / 25.06% [24.1, 26.1]. **The model sits inside the
random-skip interval**; in one session it does worse than random.

**No function — linear or non-linear, single or combined — of price
state, structure geometry, confluence, volatility, trend regime, day
type, calendar, sequence, cross-session carry, order flow or book depth,
evaluated at the entry moment, separates these trades beyond chance.**

### The pre-declared five, and what they actually say

The trader named five measures in advance from his own trading — a
hypothesis test, not a search. Result: **negative, and informative.**

- **The wall AHEAD is a significantly negative marker** (M3: WALL_AHEAD
  EV −0.356 [−0.54,−0.14]; WALLSZ −0.406 [−0.61,−0.19]; WALLSZ+
  FILL_DELTA −0.486 [−0.72,−0.25]). **The old canon's `D` gate
  *required* a wall ahead and `WALLSZ` required it to be large.** On
  this population that is the worst thing you can have — mechanically
  sensible, since a large resting wall in the path is what stops the
  move.
- **Stacking degrades monotonically**: M2 baseline 24.7% → ≥3 of five
  23.2% (EV −0.255) → ≥4 of five **19.4% (EV −0.408)**; M3 24.2% →
  21.8% → 21.3%, all clearing negative.
- **Per setup type they behave differently** (the trader's insistence
  was correct): in M1/M3 the best single is `NO_OPP` — an *absence*;
  in M2, `CVD_CONF` is the **worst** (21.3%, EV −0.322 clearing).

**"More confirmation = worse" has now appeared four independent
times** (confluence load BR-91, affirmation count, conviction stacking,
these five). The physical reading: by the time flow, book and structure
all agree, the move has already happened.

---

## 4. IN-TRADE: THE SIGNAL IS REAL, AND IT STILL DOESN'T PAY

This is the one place a model genuinely works:

- Out-of-fold **AUC 0.88 (1 min) to 0.98 (10 min)** on the still-open
  subset, **beating 20 of 20 permutation draws** (null ≈ 0.50).
- It keys on excursion-so-far and already-stopped state; footprint order
  flow contributes ~0.001 against ~0.30 for excursion.

**But the policy does not cash out.** Best row: EV −0.116 vs
do-nothing's −0.124 — **+0.008R/trade, CI [−0.020, +0.035], containing
zero.** Every other horizon/threshold is flat-to-negative.

**The reason is a payoff asymmetry, not a lack of information**:
cutting a genuine 3R+ runner among the false positives costs
**3.2–3.5R**, while correctly cutting junk saves **0.45–0.61R** — a
5–8× asymmetry that even a 0.98 AUC is not precise enough to beat.

Confirmed alongside: **blanket tight stops are far worse than either**
(−0.5R stop: EV −0.532, killing 41% of runners). One uncorrected lead:
within M3 alone the same threshold clears its own bootstrap (p ≈ 0.006).

---

## 5. WHAT WAS TRIED ON THE TRADER'S OWN HYPOTHESES, AND FAILED

Every mechanical form of "trade less" was tested and rejected:

| rule | result |
|---|---|
| cap N fights per day (N = 1…10) | flat: −0.117 at N=1, −0.124 at N=∞ |
| cap N per session window | flat |
| stop after K fights today (causal) | flat at every K |
| pace-so-far (fights/hour) | slowest −0.125, fastest −0.119 |
| the Nth fight of the day | no trend (1st −0.117, 8th **+0.011**) |
| **busy days (15+ fights)** | **real: EV −0.268, P(3R) 22.4%, holding 34% of all fights** — but **hindsight-only**; every causal version fails, because busy days are bad *throughout*, not at the end |
| level freshness | **test invalid** — 87% of fights are the 8th+ MA visit; freshness is a static-level concept, wrong for a moving average |

---

## 6. WHAT THIS ESTABLISHES

1. **The junk tail is the whole problem**, and removing it would fix
   everything (EV +0.328, P(3R) 36.7%, comfortably past the 28.3% bar).
2. **It cannot be identified at entry** from any feature or combination
   of features in this dataset — established at three levels of search,
   all permutation-calibrated.
3. **It can be identified in-trade** (AUC 0.88–0.98) but cutting it
   costs more than it saves, because runners are worth 5–8× what junk
   costs.
4. **The exit is not the lever** — the population is fairly priced at
   every horizon and every structural target.
5. Therefore: **the discriminator is not in the data.** Everything
   encoded derives from price, volume and the book at one moment. What
   separates the trader's ~5 daily setups from the census's ~11 is
   evidently not a function of those.

**The remaining path is supervision, not search.** The census fires
~11 valid fights/day; the trader takes ~1.3. Marking take/pass against
the census's own fight list on 20–30 real days converts an unsupervised
search — which has now demonstrably exhausted itself — into a labeled
classification problem, where the target is concrete and already known:
**lift P(3R) from 25.1% past 28.3%.**

Standing: fit-only, no holdout, report-only, nothing adopted, nulls
published.
