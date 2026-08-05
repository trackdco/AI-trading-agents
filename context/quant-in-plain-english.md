# Quant in Plain English

**Why this file exists.** Angus owns strategy authority, which means Angus has
to be able to audit every claim made about a strategy. That is impossible if
half the claims arrive in a vocabulary he doesn't use. Reading a paragraph and
thinking *"okay, sure, keep going"* is not sign-off — it is the absence of
sign-off wearing a costume, and it is the single most likely way this project
quietly goes wrong.

So: every statistical term this project uses, translated into the language
Angus already trades in — order flow, ICT, VWAP, Bollinger bands, RSI, sessions.

**Standing rule for whoever writes the reports:** if you use a term that isn't in
this file, either don't use it, or add it here. No exceptions. A report Angus
can't challenge is a report nobody has checked.

---

## The four numbers that describe a strategy

### R (R-multiple)
Profit measured in units of *the risk you took on that trade*. Risk 20 points,
make 40 → **+2R**. Risk 20, lose it → **−1R**.

Why we use it instead of dollars: dollars change when you change size, so a
dollar P&L tells you about your sizing, not your strategy. R strips size out and
leaves only the quality of the decision. Same reason you read a chart in points
rather than in the value of your account.

### Expectancy
**Average R per trade.** The one number that says whether a strategy makes money.

> `expectancy = (win rate × average win in R) − (loss rate × average loss in R)`

+0.20R expectancy means every time you take the setup, you're picking up a fifth
of your risk on average. Over 100 trades that's +20R. It says nothing about any
individual trade — it's the house edge, not a prediction.

**A strategy can have a 35% win rate and be excellent** (if the winners run 3R),
or an 80% win rate and be terrible (if the losers are 5R). Win rate on its own
is close to meaningless, which is why nobody selling a course ever quotes
anything else.

### Profit factor (PF)
Total money won ÷ total money lost. PF 1.5 = you make £1.50 for every £1.00 you
lose. Below 1.0 you're paying for the privilege.

Rough calibration for intraday futures: **1.3 is decent, 1.5 is good, above 2.0
on a real sample means check for a bug** — most commonly a lookahead leak.

### Drawdown
Peak-to-trough decline in the equity curve. **The number that decides whether
you can actually trade the strategy**, because it's what you have to sit
through, and on a prop account it's what fails you.

A strategy with +0.30R expectancy and a 25R max drawdown is unusable on a
funded account, no matter how good the expectancy looks.

---

## In-sample, out-of-sample, and why it's the whole game

**In-sample** = the data you built and tuned the rules on.
**Out-of-sample** = data the rules have never seen.

The analogy: in-sample is marking your own homework. You already know which days
worked, so of course you can write rules that catch them. Out-of-sample is the
exam.

**Overfitting** (= curve fitting) is when the rules have memorised the specific
data rather than learned anything general. The tell is always the same: fabulous
in-sample, dead out-of-sample.

Concretely, this is overfitting: *"the strategy works, but only between 09:47
and 10:02, only on Tuesdays and Thursdays, only when RSI is between 61 and 67."*
Every one of those clauses was added because it improved the backtest, and
every one of them describes 2025 rather than describing the market.

**Degradation ratio** = out-of-sample expectancy ÷ in-sample expectancy.
Some decay is normal — we tuned on the first window, so it flatters. Keeping
half is healthy. Keeping a tenth means the in-sample number was fiction.

---

## Why we count how many things we tried

**Multiple comparisons** — the reason the refinement ledger exists.

Flip a coin 20 times and you'll probably see a run of five heads. Nothing
special happened; you just looked at a lot of coin flips. Test 40 filters on a
strategy and two or three will look great by luck alone. If you only report the
best one and forget the other 39, you've found a coin that landed heads five
times and called it a strategy.

The fix isn't to stop testing. It's to **count the tests and raise the bar
accordingly** — which is exactly what the sliding B1 threshold in
`validation-gate-v1.md` does. Test more things, need a better result.

The trading-floor version: if you scroll a chart looking for *any* pattern that
would have printed money last month, you will always find one. That's not
research, that's pareidolia. Deciding what you're testing before you look is
what makes it research.

---

## Robustness — is the edge broad or is it a needle?

**Parameter plateau vs spike.** Say a filter is "at least 3 confluences".

- **Plateau (good):** 2 confluences → +0.15R, 3 → +0.22R, 4 → +0.19R.
  The whole neighbourhood works. The edge is real and 3 is just its best corner.
- **Spike (bad):** 2 → −0.10R, 3 → +0.35R, 4 → −0.05R.
  Only that exact number works, which means it's not the confluence count doing
  anything — you found the number that happened to fit last year's trades.

You already know this instinct from levels: a level that's been respected across
a 10-point zone is real structure. One that only holds to the exact tick, and
fails 2 points either side, isn't a level — it's a coincidence you drew a line on.

**Regime** = the market's current character: trending vs ranging, high vs low
volatility, pre- vs post-a-big-catalyst. A strategy that only works in one
regime isn't wrong — but it needs a stand-down rule, and it needs to be *known*,
not discovered live.

**Volatility terciles** = split every day in the sample into the third with the
lowest ATR, the middle third, the highest third. We want the strategy positive
in at least two. If it only works on the wildest days, it's a volatility trade
wearing a setup's clothes.

---

## Statistics we'll actually use

**Sample size and confidence.** With 30 trades, a 60% win rate could genuinely
be anywhere from about 42% to 76%. With 200 trades it narrows to roughly 53–67%.
That's why the gate wants 60+ triggers and 40+ after filtering: below that,
you're not measuring an edge, you're measuring noise and calling it an edge.

**Correlation (ρ).** Do two strategies win and lose on the same days?
- ρ near **+1**: they're the same trade. Two names, one risk.
- ρ near **0**: independent. One's bad week is the other's flat week.
- ρ near **−1**: they hedge each other.

This is the actual reason a big strategy book beats one strategy sized up. Five
strategies at ρ≈0 have roughly *half* the drawdown of one strategy doing the
same total volume. Five strategies at ρ≈0.9 have all the drawdown and none of
the benefit — that's just leverage with more paperwork.

**Monte Carlo.** Take the strategy's actual trades, shuffle their order
thousands of times, and look at the range of outcomes. Same trades, different
sequence. It answers the question a single backtest can't: *"how bad could the
ordering have been?"* — which is precisely what a trailing drawdown rule cares
about. You can pass an eval on the exact same set of trades in one order and
blow it in another.

**MAE / MFE** — Maximum Adverse / Favourable Excursion. How far a trade went
against you before it worked, and how far in your favour before it came back.
MAE tells you whether your stops are wider than they need to be. MFE tells you
whether you're leaving money on the table with your targets. Both are read
straight off the substrate, no modelling required.

**Bootstrapping.** Resampling the trades with replacement to build a range
around a number instead of a single point. When a report says "expectancy
+0.22R (0.11 to 0.33)", that range came from bootstrapping — and the range is
the honest part.

---

## Ways a backtest lies to you

**Lookahead bias** — using information the trade couldn't have had. The classic:
signalling on a candle's close but entering at that same candle's open. In a
backtest it prints money. Live it's impossible. Our engine only signals on
closed candles and activates orders on the next bar, and there's a mandatory
test named `test_no_lookahead` that fails the build if that breaks.

**Survivorship bias** — only testing what still exists. Less of an issue for NQ
than for stocks, but it shows up in a subtler form here: only testing the
strategies we remember hearing about, which are the ones that worked recently.

**Fill realism** — assuming you got filled when you wouldn't have. If your limit
sits at 20,000.00 and price ticks to 20,000.00 and reverses, you probably did
*not* get filled — you were at the back of a queue of a few hundred contracts.
Our backtest requires price to trade fully *through* a limit before counting a
fill, which is deliberately pessimistic.

**Slippage** — the gap between the price you wanted and the price you got. Stops
are the worst offenders, because a stop fires exactly when the book is thin and
moving away. We assume 2 ticks against us on every stop, and double that near
scheduled data. Then we re-run the whole thing at 2× that to make sure the edge
isn't just an underestimate of costs.

---

## Order-flow terms, so the flow reports read cleanly

**Heatmap** = a picture of *resting* orders — limits sitting in the book waiting.
Bright bands are where size is stacked. That's what the MBP-10 data in this repo
holds: a top-10-levels snapshot of the book every minute.

**CVD (Cumulative Volume Delta)** = the running total of *aggressive* buying
minus aggressive selling. Volume that lifted the offer minus volume that hit the
bid.

The distinction between those two is worth being precise about, because the
whole "what does the order flow say at entry?" step depends on it:

> **Heatmap = intent. CVD = action.** A wall of resting offers is someone
> *saying* they'll sell there. CVD rising into that wall is buyers *actually*
> paying up to take it. The wall holding while CVD climbs — buyers pushing,
> price not moving — is absorption, and that's a different trade from the wall
> simply never being tested.

**We currently have the heatmap and not the CVD.** See
`context/data-inventory.md` §3. Any refinement step that needs "what was the
flow doing at entry" is blocked until the `trades` data is bought.

**Book imbalance** = resting size on the bid vs the ask within some distance of
price. Computable from what we already have.

**Absorption** = aggressive volume arriving and price *not* moving — someone
large is filling into it. Needs both heatmap and CVD to identify properly.

---

## How to read a strategy report

Read it in this order and stop early if it fails:

1. **The plain-English mechanism.** Do you believe someone is losing money to
   this, and can you say who? If not, nothing below matters.
2. **Trade count.** Under 40 after filtering? Stop reading, it's noise.
3. **Degradation ratio.** Under 0.5? It was fitted. Stop reading.
4. **Number of filters tested** (from the ledger). Over 40? It was a search, not
   a test. Stop reading.
5. **Max drawdown in R.** Could you actually sit through that on a funded
   account?
6. **Correlation to the book.** Above 0.4? It's a strategy we already trade.
7. *Only then* look at expectancy and profit factor.

Most people read that list bottom-up, which is exactly why most backtested
strategies don't survive contact with a live account.

---

## Questions that are always fair to ask

Ask these of any result. If the answer is vague, the result isn't ready.

- *"How many trades is that based on?"*
- *"How many other versions did you try before this one?"*
- *"What does it look like if I nudge that number up or down one step?"*
- *"Which months made the money?"*
- *"What happens if slippage is twice what you assumed?"*
- *"Does it lose on the same days as the strategy we already run?"*
- *"Was this window used to build the rules, or is it genuinely untouched?"*
- *"Say the trade back to me without using any statistics."*
