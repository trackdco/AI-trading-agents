# Which hypotheses can the 128-day holdout actually answer?

**Fit only. The sealed span is NOT read here — the 128-day count is quoted from the pre-registration, and every holdout n below is a PROJECTION from the fit rate.**

Fit span: **284 session days**, book **187 trades**, R standard deviation **1.569**. Holdout: **128 days**, so subsets project at **x0.45** — a projected book of only **~84 trades**.

## The arithmetic that decides this

Sidak over k tests sets per-test alpha = 1 - (1 - 0.05)^(1/k). More questions means a tighter bar on EVERY question, the primary included:

| questions asked | per-test alpha |
|---|---|
| 2 | 0.0253 |
| 3 | 0.0170 |
| 4 | 0.0127 |
| 5 | 0.0102 |

## Projected size and POWER, per candidate

Power = the chance this holdout detects the effect **if the fit-measured effect is real and persists exactly**. It is the honest quantity: a yes/no 'answerable' flag hides the difference between 20% power and 79% power. Under ~50% is a coin flip dressed as a test — it will usually return an inconclusive shrug, and a shrug still costs a slot and still tightens everyone else's alpha.

| hypothesis | the decision it drives | fit n | projected n | fit effect (mean R) | k=2 | **k=3** | k=4 | k=5 |
|---|---|---|---|---|---|---|---|---|
| PRIMARY — book mean R > 0 | does the edge exist on unseen data | 187 | ~84 | +0.513 | 78% | **73%** | 69% | 67% |
| S1 — sub-9.5 wall band mean R > 0 | drop the risk floor 9.5 -> 5? | 300 | ~135 | +0.590 | 91% | **88%** | 86% | 84% |
| S2 — both-W+FAR vs exactly-one | is there a conviction ladder? | 133 / 54 | ~60 / ~24 | +0.586 | 25% | **20%** | 17% | 16% |
| S3 — deep fades mean R > 0 | filter out deep counter-VWAP fades? | 73 | ~33 | +0.332 | 12% | **9%** | 8% | 7% |
| S4 — depth-gated vs ungated fades | does depth give conviction on fades? | 36 / 37 | ~16 / ~17 | +0.790 | 21% | **17%** | 15% | 13% |

**Read the primary row first.** Even at 2 questions it carries only **78%** power, and ~84 trades with R's standard deviation at 1.57 puts the standard error on holdout mean R at about **0.171**. A fit-sized effect of +0.513 sits roughly 3.0 standard errors from zero. **This holdout can tell 'the edge is real' from 'the edge is absent'. It cannot finely grade subsets** — and that single fact decides most of what follows.

## The surprise: the declared secondary is the strongest question

S1 is already in the prereg as the single secondary, and on this arithmetic it is the **best-powered question available — 88% at k=3, better than the primary itself**. The reason is size: the sub-9.5 wall-passing band is **300 fit trades — larger than the 187-trade main book** — projecting to ~135 on the holdout, and it carries mean R +0.590, *higher* than the main book's +0.513.

It nearly got mis-scored. Framed as 'does the floor-5 book beat the floor-9.5 book' it returns **2% power**, because those two means are almost identical and a difference-of-means test on overlapping sets asks a question nobody cares about. The decision is whether the ADDED trades make money, which is a one-sample expectancy test on the incremental band. Same test, same data, 2% vs 88% — the framing was the whole result.

## The conflict nobody should miss

**S3 and S4 are not independent — they act on the SAME trades in OPPOSITE directions.** S3 asks whether to drop the deep fades; S4 asks which of them to keep. If S3 says drop, S4 has nothing left to gate; if S4 finds a gate, S3 is refuted. Asking both spends two slots on one question and can return a contradiction with no declared rule for resolving it. **At most one of S3/S4.**

## S2 and the sizing freeze

§1 freezes sizing at **flat 1 NQ lot** on an ANGUS ruling — *"no sizing until the validated volume is visible"*. The tier ladder is a SIZING rule, so adopting it now would contradict a standing ruling — and it does not need the holdout's permission to exist later, because the holdout run at 1 lot IS the validated volume that unlocks the sizing decision afterwards.

The ladder's UNDERLYING claim — that the both-W+FAR cell carries materially more R than the exactly-one cell — is a SIGNAL claim, testable at 1 lot without touching sizing. That version is already half-asked: §2's reporting item 9 is "W/FAR lift: mean R of `either` vs `neither`", and splitting `either` into both-vs-one is a small extension of a number the run already reports. But at **20% power** it will most likely come back inconclusive, so the honest framing is REPORT IT, do not gate a decision on it.

## Recommendation

| candidate | power @ k=3 | verdict |
|---|---|---|
| **S1** sub-9.5 band expectancy | 88% (usable) | **KEEP** — best-powered question on the list, and the one that would most change the shipped config (floor 5 nearly triples volume) |
| **S2** both-vs-one separation | 20% (futile) | **ADD as a REPORTED number, not a gated test** — extends an item §2 already reports, respects the sizing freeze, but is underpowered to rule on |
| **S3** deep-fade expectancy | 9% (futile) | **DEFER** — ~33 projected trades cannot resolve it |
| **S4** depth-gated fades | 17% (futile) | **DROP** — smallest subset (~16 vs ~17), and mutually exclusive with S3 anyway |

**Net recommendation: 3 questions — primary + S1 + S2.** That holds the primary at 73% rather than 67% at k=5, keeps the one genuinely well-powered secondary (S1 at 88%), and reports S2 without pretending the holdout can rule on it.

S3 and S4 are this week's genuinely new findings, and the honest thing to say is that **this holdout is the wrong instrument for them**. They live in a ~33-trade subset where nothing resolves at a corrected alpha. They are recorded with effect sizes and p-values intact in `docs/LONDON-VWAP-FILTER.md` and `docs/LONDON-FADE-CONVICTION.md`, to be tested on FORWARD data where sample size can be accumulated rather than rationed. Spending the referendum on them would answer neither them nor the primary well.

## Caveat on these projections

Every holdout n is the fit rate scaled by days (128/284 = x0.45). If the sealed span trades at a different rate — plausible, 2023/24 being a different volatility regime — the counts and the power move with it. The ORDERING is robust (S4's subset is smallest under any rate; S1's is largest), but the absolute percentages are indicative, not exact. Nothing was read from the sealed span to refine them, which is the point.
