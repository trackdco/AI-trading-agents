# Daily loss limit — measurement, not opinion

**Angus's question, 2026-07-26:** *"the canon (+$56k since June last year across London + New
York) was made with risk-adjusted sizing we manufactured specifically for the funded, and Monte
Carlo says max-payout probability was 97% from the risk spine we built. There was no daily loss
limit in those tests, idk if adding one now would be beneficial, perhaps it would even degrade
performance."*

**Answering the two `[ANGUS]` placeholders in `docs/PROMOTION-GATE.md` §D2.**

Reproduce: `python -m scripts.daily_loss_limit_study`, `python -m scripts.dd_buffer_study`,
`python -m scripts.payout_cycle_halts`, `python -m scripts.dd_ramp_study`.

---

> ## WHICH BOOK EACH NUMBER CAME FROM — read this first
>
> §1–§6 below were measured on **`output/baseline_book.parquet`** (+$56,065.18 / 400), which was
> the signed-off anchor at the time. It has since been superseded: the pre-window `C` check used
> the look-ahead `conf_PM` (`docs/FINDING-conf_PM-lookahead-pre-window.md`). The **arming
> reference is now `output/baseline_book_clean.parquet`, +$52,522.81 / 404.**
>
> **Everything was re-run on the clean book — see §9. The conclusions hold, with one instructive
> exception.** All scripts now default to the clean book; `CANON_BOOK=output/baseline_book.parquet`
> reproduces the older figures.

---

## 0. First, correct the premise — in both directions

**You are right about the book.** `scripts/canon_mechanical.py` and `scripts/london_canon.py`
carry **no daily loss halt.** The only day-level rule in the canon is the escalation gate
(`nth >= 2 & score < threshold -> size 0`). So the +$56,065.18 in
`output/baseline_book.parquet` is genuinely a no-day-limit number.

*(The champion-era engine is a different system and does have one —
`config/strategy.yaml: daily_halt_r: -2.0`, `src/backtest/engine.py:547`. That is not the canon
path. Neither is `config/live.yaml: daily_loss_dollars: 1500.0`, which belongs to the paper
Vault stack on a $25k seed. Don't let either govern the funded account.)*

**You are not right about the Monte Carlo.** `scripts/mc_dollar_risk.py:65` hard-codes
`if day_pl <= -800: break`. **Every "+spine" number we have ever quoted — the 1.5% -> 0.18%
bust reduction, the ~$237k funded year, the cycle success rate — was computed with a −$800
daily loss halt already switched on.** The recorded cycle figure is **94%**, not 97%
(`docs/SAFETY-SPINE.md:173`); the 97% is not in any file.

And a third correction: **a daily loss halt is not something we would be "adding."**
`SpineConfig.daily_loss_halt = -800.0` is Tier-1 rule #2, implemented and wired at
`src/canon/spine.py:43,190,243`. It ships today. The live question is not *whether* — it is
**what value, and in what units.**

---

## 1. The historical book: a −$800 halt is inert. Full stop.

225 trading days, 400 trades, both books, walked in fill order.

| threshold | days touching it intraday | days closing below |
|---|---|---|
| −$300 | 30 (13.3%) | 24 (10.7%) |
| −$400 | 10 (4.4%) | 10 (4.4%) |
| −$500 | 5 (2.2%) | 5 (2.2%) |
| −$600 | 1 (0.4%) | 1 (0.4%) |
| **−$800** | **0 (0.0%)** | **0 (0.0%)** |

**The worst day in fourteen months is −$619.** A −$800 halt would not have fired once. It
cannot have degraded the +$56,065.18, because it never had the chance to.

Replaying the book with the halt actually enforced:

| limit | total | vs canon | trades | skipped | halt days | months green | worst day | maxDD |
|---|---|---|---|---|---|---|---|---|
| none (canon) | $56,065 | — | 400 | 0 | 0 | 12/13 | −$619 | $1,404 |
| −$800 | $56,065 | **$0** | 400 | 0 | 0 | 12/13 | −$619 | $1,404 |
| −$600 | $56,065 | $0 | 400 | 0 | 1 | 12/13 | −$619 | $1,404 |
| −$500 | $56,167 | +$102 | 398 | 2 | 5 | 12/13 | −$580 | $1,404 |
| **−$400** | **$56,278** | **+$213** | 397 | 3 | 10 | 12/13 | **−$580** | $1,404 |
| −$300 | $51,756 | **−$4,309** | 383 | 17 | 30 | 12/13 | −$580 | $1,468 |
| 2 losers | $52,902 | −$3,163 | 386 | 14 | 35 | 12/13 | −$580 | $1,215 |

Three readings:

1. **−$400 is free, and slightly better than free.** +$213, worst day improves −$619 -> −$580,
   months-green unchanged. At floor sizing 1.0 conviction = $200 risk, so **−$400 is exactly
   −2R** — the same halt §10 already specifies. We would not be introducing new behaviour.
2. **−$300 is where it turns into a strategy filter** and costs $4.3k. That is the overfit
   cliff; stay off it.
3. **Drop the loser-count shape.** "2 losing trades" costs $3,163 and halts 35 days —
   re-confirming your 17-Jul ruling that set `daily_halt_losses: 0`. Damage, not attempts.

**Months green is 12/13 under every single variant.** No daily loss limit at any value changes
the consistency record on this book. Your objective function is untouched either way.

*(2026-01 is absent from all month tables — no trades in the book that month.)*

---

## 2. The trap: a fixed-dollar limit does not scale, and the sizer does

This is the part that matters, and it is why the shipped −$800 is the wrong number even though
it looks harmless above.

The book was sized at the **floor** schedule: 1.0 conviction = $200 risk. Live, `base_dollar`
scales with available drawdown (`SAFETY-SPINE.md`, Angus 24-Jul). So a fixed dollar limit means
a different thing every day:

| available DD | 1R = | −$800 means | −$400 means |
|---|---|---|---|
| $3,000 (floor) | $200 | −4.00R | −2.00R |
| $4,000 | $275 | −2.91R | −1.45R |
| $5,000 | $350 | −2.29R | −1.14R |
| **$6,000** | **$425** | **−1.88R** | −0.94R |
| $7,000 | $500 | −1.60R | −0.80R |

Under the chosen **Build-6** withdrawal policy the balance cycles $4k -> $6k, so this is the band
we will actually live in. At the top of it, one 2.25-conviction trade risks **$850** —
**more than the −$800 halt.** The halt stops the day before the first trade has finished losing.

That is the exact opposite of the intended behaviour: the limit is loosest when the cushion is
thinnest and tightest when the cushion is fattest. It is a backstop at the floor and a
strategy filter at the ceiling, and nobody chose the second thing.

**A limit expressed in R is invariant.** −2R is −$400 at the floor and −$850 at $6k available
DD — the same relationship to the day's own risk unit at every balance.

---

## 3. Funded-year MC: fixed-dollar day stops cost money and buy nothing

20,000 sims, DD-scaled live sizing, available-DD halt held at $250 so the day stop is isolated.

| daily limit | bust % | median | p10 |
|---|---|---|---|
| **none** | **0.14%** | **$309,736** | $224,088 |
| −$1,600 | 0.14% | $297,429 | $213,749 |
| −$1,200 | 0.14% | $248,317 | $171,914 |
| −$1,000 | 0.14% | $240,068 | $164,723 |
| **−$800 (shipped)** | **0.14%** | **$242,066** | $166,441 |
| −$600 | 0.14% | $229,910 | $155,839 |
| −$500 | 0.14% | $228,069 | $154,508 |
| −$400 | 0.14% | $226,999 | $153,832 |
| −$300 | **0.17%** | $222,447 | $148,392 |

**Bust does not move.** Not at any value. The −$800 halt we have been crediting for the
1.5% -> 0.18% improvement contributes **zero** of it — and it costs $67,670 of median. Tighten to
−$300 and bust gets *worse*, because the account stops booking the recoveries.

*(Caveat, stated plainly: this MC compounds for 252 days with no withdrawals, so available DD
runs to six figures and the sizer pins at the 40-micro clamp. The magnitudes are inflated. §4
prices the same question in the band we will actually trade.)*

So where did the 8× bust reduction come from? **Rule #1, alone:**

| available-DD halt buffer | bust % | median |
|---|---|---|
| $0 (off) | **1.44%** | $309,820 |
| $100 | 0.66% | $309,939 |
| $250 (shipped) | 0.14% | $309,736 |
| **$400** | **0.00%** | $308,407 |
| $600 | 0.00% | $306,497 |

The available-drawdown halt does all of the work, and does it essentially for free.

**The proposal's exact cell, run rather than inferred from the two halves:**

| configuration | bust | median | p10 |
|---|---|---|---|
| buffer $250, day stop off | 0.14% | $309,736 | $224,088 |
| buffer $250 + −4R | 0.14% | **$309,736** | **$224,088** |
| buffer $400, day stop off | 0.00% | $308,407 | $219,763 |
| **buffer $400 + −4R** | **0.00%** | **$308,407** | **$219,763** |

−4R is not "approximately free" — it is **identical to the decimal** at both buffer settings.
The entire cost of the proposal is the buffer move $250 -> $400: $1,329 of median (0.4%) and
$4,325 of p10 (1.9%), in exchange for the last 0.14% of bust. In the payout-cycle model that
same move costs nothing at all.

### How the two numbers were chosen

**$400** — two independent derivations agreeing. *A priori:* max per-trade risk at the floor is
2.25 conviction capped at 2× base = **$400**, so the buffer is exactly one max-risk trade of
headroom above the line; the worst possible next trade still cannot touch it. *Empirical:* it is
the **first** buffer where bust reaches 0.00% and the **last** before p10 erodes ($600 keeps
0.00% but costs $20k of p10; $800 collapses p10 to $635). A corner, not a fitted point.

**−4R** — the MC cannot choose this: −5R, −4R, −3R, −2.5R and −2R all return identical results.
So it was chosen by constraint — *the halt must not touch validated behaviour* — and the
historical day-loss distribution fixes it:

| worst days in the canon, in R | | | | |
|---|---|---|---|---|
| −3.09R (2025-11-24) | −2.90R (2026-03-12) | −2.90R (2025-12-10) | −2.71R (2025-06-10) | −2.66R (2026-02-09) |

Out of 225 days: 10 reach −2R, 5 reach −2.5R, **1 reaches −3R, 0 reach −3.5R, 0 reach −4R.**
−4R is the first round number strictly outside the whole validated distribution — 0.91R of clear
air above the worst day we have ever produced — and it equals −$800 at the floor, i.e. the value
already shipping. Pat changes a unit, not a number.

---

## 4. Payout-cycle MC — the realistic band, the KPI that matters

Available DD under Build-6 cycles roughly $4k -> $6k, so `base_dollar` runs $275–$425. This is
the regime we will actually trade. Build-6, $2,000 per withdrawal, 5 winning days between
payouts, 20,000 sims. **Cash withdrawn per account per year is the number**; ×5 accounts is the
business.

| configuration | cash/acct | ×5 accounts | bust % | p25 cash | 1st payout |
|---|---|---|---|---|---|
| naked — no halts at all | $48,000 | $240,000 | 1.44% | $44,000 | 23d |
| buffer $250, no day stop | $48,000 | $240,000 | 0.14% | $44,000 | 23d |
| **buffer $400, no day stop** | **$48,000** | **$240,000** | **0.00%** | $44,000 | 23d |
| buffer $600, no day stop | $48,000 | $240,000 | 0.00% | $44,000 | 23d |

**Fixed-dollar day stop** (buffer held at $250):

| day stop | cash/acct | ×5 | bust % | p25 | days a trade was blocked |
|---|---|---|---|---|---|
| −$1,600 | $46,000 | $230,000 | 0.14% | $44,000 | 20/yr |
| −$1,200 | $44,000 | $220,000 | 0.14% | $40,000 | 33/yr |
| **−$800 (shipped)** | **$42,000** | **$210,000** | **0.14%** | **$38,000** | **46/yr** |
| −$600 | $40,000 | $200,000 | 0.14% | $38,000 | 52/yr |

**R-indexed day stop** (buffer held at $250):

| day stop | cash/acct | ×5 | bust % | p25 | days a trade was blocked |
|---|---|---|---|---|---|
| −5.0R | $48,000 | $240,000 | 0.14% | $44,000 | 6/yr |
| **−4.0R** | **$48,000** | **$240,000** | **0.14%** | $44,000 | 6/yr |
| −3.0R | $48,000 | $240,000 | 0.14% | $44,000 | 6/yr |
| −2.5R | $48,000 | $240,000 | 0.14% | $44,000 | 6/yr |
| −2.0R | $48,000 | $240,000 | 0.14% | $44,000 | 7/yr |
| −1.5R | $46,000 | $230,000 | **0.17%** | $44,000 | 10/yr |

**Head to head:**

| pair | cash/acct | ×5 | bust % |
|---|---|---|---|
| shipped: buffer $250 + −$800 | $42,000 | $210,000 | 0.14% |
| **proposal: buffer $400 + −4R** | **$48,000** | **$240,000** | **0.00%** |
| alternative: buffer $400 + −2R | $48,000 | $240,000 | 0.00% |

**The shipped pair costs $6,000 per account per year — $30,000 across five accounts — and is
worse on bust than the proposal.** Every R value from −5R down to −2R is indistinguishable from
having no day stop at all. −1.5R is where it starts to bite, and it bites in both directions
(less cash *and* more bust).

Don't over-widen the buffer either: $600 is still free in the cycle model but in the funded-year
MC p10 drops $224k -> $204k, and $800 collapses it to $635 — the halt fires so often the account
stops trading. **$400 is the corner.**

---

## 5. The ruling I recommend

### D2 daily loss limit: **−4R — same number at the floor, but indexed**

**Change the units, not the value.** `-800.0` becomes `-4.0` R, evaluated against the day's own
`base_dollar`.

- At the eval floor, −4R **is −$800**. Nothing about day one changes. The number Pat has already
  built to, and every "+spine" MC we have ever quoted, stays exactly where it is.
- It never fires on the validated book — **0 halt days in 225** — so it cannot have degraded the
  +$56k and cannot degrade it going forward. The worst day we have ever produced is −3.09R.
- It stays a **backstop** as the buffer grows: −$1,100 at $4k available DD, −$1,700 at $6k.
  Because `base_dollar` tracks available DD, −4R is a near-constant **~27–28% of the buffer** at
  every balance. That is precisely what §Tier-1(2) says the rule is for — *"sized so one bad day
  can't consume the EOD buffer"* — and a fixed dollar figure cannot deliver it.

**Why not −2R, even though it made +$213 on history.** That +$213 comes from 10 halted days out
of 225 — an in-sample selection on 4% of the sample, worth 0.4% of the book. It is exactly the
kind of micro-gain this project has killed repeatedly, and it converts a survival rule into a
trade filter. The spine "is not strategy." −2.5R and −2R are also free in the payout model, so
if you want it tighter the cost is genuinely zero — but I would not buy noise with a Tier-1
constant.

**Whatever value you pick, index it.** Every R value from −5R to −2R prices identically in the
cycle model; every fixed-dollar value bleeds. The units are the decision; the number is taste.

### D2 available-drawdown floor: **leave it at $250**

> **Corrected 2026-07-26 (same day).** This section first recommended $400 on the strength of
> "0.00% bust at no cost in the payout model." That reading was wrong: annual cash is quantised
> into $2,000 payouts, so the median and p25 physically cannot move for an effect this size.
> `scripts/why_bust_falls.py` re-ran both policies on identical day sequences and priced it on
> the **mean**. There is no corner and no free lunch — every dollar of buffer is a straight
> trade of cash for bust. Original recommendation kept visible below the corrected one.

| buffer | bust | frozen years | mean cash | cost | bust removed | **cost per point of bust** |
|---|---|---|---|---|---|---|
| none | 1.59% | 0.0% | $46,533 | — | — | — |
| **$100** | 0.81% | 1.1% | $46,378 | −$155 | −0.78pp | **$199** |
| **$250 (ships)** | **0.17%** | **2.7%** | **$45,974** | **−$404** | **−0.64pp** | **$631** |
| $400 | 0.00% | 4.2% | $45,390 | −$584 | −0.17pp | **$3,435** |
| $600 | 0.00% | 6.9% | $44,158 | −$1,232 | **0** | **∞** |

*(naked bust reads 1.59% here against 1.44% in §3 — same quantity, different draw method: a
pre-drawn sequence matrix so both policies see identical days. This table is internally
consistent.)*

**Pricing a point of bust.** The five accounts are copy-traded off the identical book, so they
bust **together** — 1.59% is the probability of losing the whole ~$240k/yr stream in one year,
not a per-account risk. That values one point of bust at roughly **$465** of expected annual
cash per account, plus the re-eval and the lost weeks. Against that:

- none -> $100: pay $155 for $363. Worth it.
- $100 -> $250: pay $404 for $298. Break-even on cash, positive once keeping the account counts.
- **$250 -> $400: pay $584 for $79.** Five times the value it buys.
- $400 -> $600: pay $1,232 for nothing at all.

**$250 already captures 89% of the total available bust reduction for 1.2% of cash.** It is also
what ships, so Pat changes nothing.

### Why this is a trade-off at all — and the shape that might beat it

The available-DD halt is an **absorbing state**. Halted means no trades, so the balance does not
move, so the EOD line does not move, so you are still under the buffer tomorrow. Median
halt-days per firing path: **239 of 252.** It does not end your day, it ends your year. The
paired decomposition:

| group | count | outcome |
|---|---|---|
| untouched — never came within $400 of the line | 19,162 (95.8%) | $0 change |
| rescued — busted naked | 319 (1.59%) | survives, **with $6 of cash** |
| paid — survived naked, halted anyway | 519 (2.6%) | **−$44,058 each** |

Naked bust is concentrated at the start: **median bust day 15 of 252**, before the buffer builds.

It has to be a cliff because **`base_dollar` floors at $200 and never steps below it**. The spine
doc says sizing "steps down the same way as available DD shrinks" — but it stops stepping at
$3k. At $400 of remaining room the sizer still wants to risk $200 on a 1.0 setup, half the room,
so the only available response is to stop entirely.

### The ramp — `scripts/dd_ramp_study.py`

Keep stepping down instead of stopping: below a start point, scale the 1.0-tier base linearly to
zero, with a token hard halt underneath. A trade that sizes to 0 micros simply isn't taken, so
the account **de-risks and can grind back** rather than freezing.

| shape | bust | mean cash | median | p10 | years lost to stand-down |
|---|---|---|---|---|---|
| no halt at all | 1.59% | $46,533 | $48,000 | $42,000 | 0.0% |
| cliff, buffer $250 *(ships)* | 0.17% | $45,974 | $48,000 | $42,000 | 2.7% |
| cliff, buffer $400 | 0.00% | $45,390 | $48,000 | $40,000 | 4.2% |
| ramp from $3,000 -> $0 at $100 | 0.00% | $45,530 | $46,000 | $40,000 | 0.0% |
| ramp from $2,000 -> $0 at $100 | 0.00% | $46,833 | $48,000 | $42,000 | 0.0% |
| **ramp from $1,500 -> $0 at $100** | **0.00%** | **$47,052** | **$48,000** | **$42,000** | **0.0%** |
| ramp from $1,000 -> $0 at $100 | 0.00% | $47,074 | $48,000 | $42,000 | 0.2% |
| ramp from $750 -> $0 at $100 | 0.00% | $46,900 | $48,000 | $42,000 | 0.6% |

**Where the ramp starts is the whole game.** A funded account opens at **$2,000** available DD, so
a ramp beginning at $3k is inside the healthy build-up of every account from day one — that is
what costs section B's variants a payout off the median. Start it *below* the opening balance and
the tax disappears.

**The $1,500 start strictly dominates every other row**, including doing nothing: more mean cash
than the naked book (+$519), zero bust, zero frozen years, median and p10 both untouched. It
beats the shipped $250 cliff by **+$1,078/account/year (+2.3%), ~$5,390 across five accounts**,
and removes the 2.7% frozen-year rate entirely.

It reads as a free lunch and mostly is one, for a boring reason: the naked mean is dragged down
by the 1.59% of paths that bust with nothing, and the ramp converts those into paths that keep
earning — for less than that conversion is worth.

Two things that make it credible rather than fitted: **$2,000 / $1,500 / $1,000 / $750 all land
within $250 of each other**, so it is a plateau, not a spike; and the mechanism is principled —
don't de-risk above where the account started, do de-risk below it, because the sizer's $200
floor is too large against the room that remains.

**Effect on the canon: zero.** The ramp only engages below $1,500 available DD, and
`baseline_book.parquet` has no equity path at all. +$56,065.18 either way.

#### Fine sweep of the start point, and how often the thing even engages

| ramp start | bust | mean cash | median | p10 | years lost to stand-down |
|---|---|---|---|---|---|
| **$1,500** | 0.00% | $47,052 | $48,000 | $42,000 | **0.0%** |
| $1,250 | 0.00% | $47,082 | $48,000 | $42,000 | 0.1% |
| $1,000 | 0.00% | $47,074 | $48,000 | $42,000 | 0.2% |
| $900 | 0.00% | $47,040 | $48,000 | $42,000 | 0.3% |
| $800 | 0.00% | $46,944 | $48,000 | $42,000 | 0.5% |
| *cliff $250 (ships)* | *0.17%* | *$45,974* | *$48,000* | *$42,000* | *2.7%* |

Mean cash across the whole start range spans **$142** — flat. The only thing that moves
monotonically is stand-down, and it moves the wrong way as you start later: **0.0% -> 0.5%.**
Starting later does not make the rule rarer, it makes it *steeper*. From $1,500 the taper is
spread over $1,400 of room ($200 -> $186 at the top, barely a change); from $800, the same
descent is crammed into $700, so once inside it, size collapses fast enough that days round down
to zero micros and strand the year. **$1,500 gets the same money and never strands anyone.**

**How often we are actually down there** (measured on the shipped cliff, so it describes today's
behaviour, not the ramp's):

| available DD below | share of all trading days | share of years touching it at least once |
|---|---|---|
| $1,500 | 3.39% | **48.2%** |
| $1,000 | 2.73% | 15.7% |
| $600 | 2.58% | 6.1% |
| $250 | 2.54% | **2.7%** |

Read the right-hand column; the day-shares are distorted by the freeze (a stranded path sits
below $250 for hundreds of days, which is why all four day-figures collapse toward the same
number, and why the $250 row is exactly the 2.7% frozen-year rate from the decomposition above).

**Nearly half of all funded years dip below $1,500 of room at least once** — this is not a rare
backstop, it is a regularly-visited region. But only **6.1%** get below $600 and **2.7%** below
$250. So the shallow part of the ramp is common and nearly weightless, and the steep part is
rare. That is exactly the shape you want, and it is why the rule costs nothing.

For context on the exposure: the canon's max drawdown is **$1,404** at floor sizing. From a cold
start you open with $2,000 of room, so that run-down alone lands you at **$596**. Once a couple
of grand is banked and the line locks, the same drawdown leaves you well above $1,500 — which is
why the exposure, like the bust risk, is concentrated in the first few weeks.

**Still Angus's call — this is a SIZING change, not a spine constant.** It is also safely
deferrable: the shipped $250 cliff already reaches 0.17% bust, so nothing is blocked on it.

### Consecutive halt days: **keep 2 in a row -> stop and review**

Not a modelled number and it does not need to be. It is a human circuit breaker, and the cost
of being wrong about it is one day of not trading.

---

## 6. Two defects found while measuring this — both block arming

**1. `SpineConfig.max_contracts = 2` is in the wrong unit.** The comment says minis; `intent.size`
is **micros** (`src/desk/canon_lane.py:121`, `src/live/route_b.py:171` — both pass the sizer's
micro count). `src/live/route_b.py:437` constructs `SpineConfig()` with the default, and nothing
in the tree overrides it. **Live, the spine clamps every order to 2 micros** — a 4–20× under-size
on every trade, and gate **B5 (sizing exact) fails on trade one**. It fails safe rather than
dangerous, but the live book would bear no resemblance to the canon. Set it to **40**.

**2. Nothing pins the Tier-1 constants.** `dd_halt_buffer`, `daily_loss_halt` and `max_contracts`
all ride on dataclass defaults with no config file and no assertion at boot. The launch
checklist's first unchecked box is "Tier-1 constants set to confirmed Lucid 50k numbers" — that
box cannot be checked against defaults nobody set. Load them from config and assert them at
startup, the same way the parity gate asserts features.

---

## 7. What the model cannot tell you, and why the rule stays anyway

Every MC here bootstraps whole days **out of the canon's own 225 days**. By construction it can
only ever produce days the strategy has already survived. The tail a daily loss halt exists to
catch — a broken feature, a stale feed scoring garbage, a news day outside anything in the
sample, a bracket leg that silently didn't rest — **is not in the sample and never will be.**

So "the MC shows no bust benefit" is not an argument for removing the rule. It is an argument
for setting it **wide enough that it never touches validated behaviour**, which is what −4R does
(0 fires in 225 days), and then trusting it to catch the thing the data cannot show us. A
backstop that never fires in the backtest is a backstop working correctly.

---

## 8. Direct answer

**No — it will not degrade performance, and it would not have degraded the +$56k.** The worst
day in fourteen months is −$619, so the shipped −$800 never fires on this path. Your instinct
that tightening would cost money is also right: −$300 costs $4.3k on history and makes bust
*worse* in the MC.

**But the shipped rule is still wrong**, for a reason the historical replay cannot show: it is
denominated in dollars while the sizer is denominated in available drawdown. By the time the
account is at $6k available DD, −$800 is less than a single max-conviction trade's risk, and the
cycle model prices that at **$6,000/account/year — $30,000 across five accounts — for zero bust
reduction.**

**Fix the units, not the presence: −4R (= −$800 at the floor) and a $400 drawdown floor.** Both
are free on history, both are free in the payout model, and the drawdown floor is the one
actually buying the survival we have been attributing to the pair.

---

## 9. RE-RUN ON THE ARMING REFERENCE (`baseline_book_clean.parquet`, +$52,522.81 / 404)

Everything above was measured on the pre-lookahead-fix book. Re-measured on the clean one.

### The book itself

| | leaky (400) | **clean (404)** |
|---|---|---|
| total | $56,065.18 | **$52,522.81** |
| worst day | −3.09R / −$619 | **−3.18R / −$636** |
| days ≤ −3R | 1 of 225 | 2 of 224 |
| days ≤ −3.5R / ≤ −4R | 0 / 0 | **0 / 0** |
| max drawdown | $1,404 | **$1,614** |
| months green | 12/13, worst −$396 | **13/13, worst +$618** |

The fix cost $3,542 of P&L and **removed the only red month.** Reshuffling the clean book's own
days 200,000×: p90 max DD **$2,366**, p99 **$3,310**, **51.1%** of orderings worse than the one
that happened, **23.25%** breaching $2,000. The drawdown case for the parameters is *stronger*
on the clean book, not weaker.

### Daily loss halt — replay

| limit | total | vs canon | halt days | months green | worst day |
|---|---|---|---|---|---|
| none | $52,523 | — | 0 | 13/13 | −$636 |
| **−4R (−$800 at floor)** | **$52,523** | **$0** | **0** | 13/13 | −$636 |
| −3.5R | $52,523 | $0 | 0 | 13/13 | −$636 |
| −3R | $52,523 | $0 | 2 | 13/13 | −$636 |
| −2.5R | $52,625 | +$102 | 4 | 13/13 | −$636 |
| **−2R** | $52,339 | **−$184** | 12 | 13/13 | −$580 |
| −$300 | $49,871 | −$2,651 | 29 | 13/13 | −$580 |

**The instructive exception: −2R was +$213 on the leaky book and is −$184 on the clean one.** It
changed sign. It was always 10 halted days out of 225 — in-sample noise — and it did not survive
a substrate correction. **−4R, chosen to sit strictly outside the validated distribution rather
than to score well inside it, is unchanged at exactly $0.** That is the argument for picking a
backstop by constraint instead of by curve, and it paid for itself here.

### Cliff vs ramp

| shape | bust | mean cash | median | p10 | years lost to stand-down |
|---|---|---|---|---|---|
| no halt at all | 1.75% | $47,788 | $48,000 | $42,000 | 0.0% |
| cliff, buffer $100 | 0.90% | $47,574 | $48,000 | $42,000 | 1.3% |
| **cliff, buffer $250 (ships)** | **0.19%** | **$47,100** | $48,000 | $42,000 | **3.1%** |
| cliff, buffer $400 | 0.00% | $46,381 | $48,000 | $42,000 | 4.9% |
| cliff, buffer $600 | 0.00% | $44,987 | $48,000 | $40,000 | 7.9% |
| ramp from $3,000 | 0.00% | $46,616 | $48,000 | $40,000 | 0.0% |
| ramp from $2,000 | 0.00% | $48,068 | $48,000 | $42,000 | 0.0% |
| **ramp from $1,500** | **0.00%** | **$48,334** | **$48,000** | **$42,000** | **0.0%** |
| ramp from $1,000 | 0.00% | $48,370 | $48,000 | $42,000 | 0.2% |
| ramp from $750 | 0.00% | $48,112 | $48,000 | $42,000 | 0.9% |

Same conclusion, wider margin. **Ramp from $1,500 beats doing nothing at all (+$546/acct) and
beats the shipped $250 cliff by +$1,234/acct/yr — ~$6,170 across five accounts** — while taking
bust to 0.00% and stranding nobody. $1,500 vs $1,000 is $36 apart on cash and 0.0% vs 0.2% on
stranding, so $1,500 still wins. The $2,000–$750 plateau spans $302: still a plateau, not a spike.

### Verdict, unchanged

1. `max_contracts: 2` -> **40** — a unit bug, unaffected by any of this.
2. `daily_loss_halt: -800.0` -> **−4R** — confirmed on the arming reference, $0 effect.
3. **Ramp `base_dollar` from $1,500 down to $0 at $100** — confirmed, and the only one of the
   three that makes money. Sizing change, so Angus's call.
4. `dd_halt_buffer` **stays 250**. Loss-count halt **stays off**.

```
base_dollar(ad):
    ad >= 3000 :  200 + 75·floor((ad − 3000)/1000)     # unchanged
    ad >= 1500 :  200                                   # unchanged
    ad <  1500 :  200 · (ad − 100) / 1400               # the ramp
    ad <=  100 :  0  → no trade ("sized out", journalled distinctly from "halted")
```

Belongs in `dollar_risk_micros`, **not** the spine — the DD-scaling overlay must be applied
identically by the baseline sim and the agents off the same account-state feed, or A2 fails.

---

## 10. THE ACTUAL PROPOSED CONFIGURATION, END TO END

Everything above tested one knob at a time. This is the real head-to-head — same harness, same
20,000 pre-drawn day sequences, clean book, Build-6.

| configuration | bust | mean cash/acct | ×5 accounts | stranded years | day-halts |
|---|---|---|---|---|---|
| **SHIPS TODAY** — cliff $250 + −$800 flat | 0.19% (39/20,000) | **$40,853** | $204,265 | 3.1% | **42.3/yr** |
| fix #2 only — cliff $250 + **−4R** | 0.19% (39/20,000) | **$47,100** | $235,500 | 3.1% | 0.0/yr |
| **fix #2 + #3** — ramp $1,500→$100, halt **$100**, −4R | **0.00% (0/20,000)** | **$48,334** | **$241,670** | **0.0%** | 0.0/yr |
| ...same but hard halt left at $250 | 0.00% (0/20,000) | $48,261 | $241,305 | 0.2% | 0.0/yr |

**Just fixing the units is worth +$6,247/account/year — +$31,235 across five.** The shipped
−$800 flat blocks a trade on **42 days a year**; −4R blocks **zero**, because it never fires on
days this system has produced.

**Adding the ramp takes it to +$7,481/account/year (+$37,405 across five) and bust to 0.00%.**

### The buffer is COUPLED to the ramp — correction to §5

§5 said "keep `dd_halt_buffer` at 250" as a standalone. That holds **only if the ramp is not
adopted.** Row 4 shows keeping the $250 hard halt underneath the ramp costs **$73/acct and
strands 0.2% of years for no benefit** — by $250 of room the ramp has already sized the account
down to ~$21 a trade, so the halt only freezes accounts the ramp would have carried through.

| | `dd_halt_buffer` |
|---|---|
| ramp adopted | **$100** |
| ramp not adopted | **$250** |

Do not ship the ramp and leave the buffer at 250 — that pays for the ramp and keeps the freeze.

### −4R contributes nothing measurable on top of the ramp, and that is correct

Identical to the dollar with or without it (row 3 vs the no-day-stop run: both $48,334, 0 busts).
−3R is also identical. The daily halt's job is the tail the day-bootstrap **structurally cannot
generate** — it can only resample days the canon already survived, worst of which is −3.18R.
A backstop showing zero benefit in the model and zero cost on the book is behaving correctly.

### What 0.00% does and does not mean

It means: **no ordering of the canon's own 224 days kills the account.** That is sequence risk,
and 23.25% of reshuffles were breaching $2,000 before. Eliminating it is worth having.

It does **not** mean bust is impossible. Not modelled: gaps, slippage past the stop beyond the
backtest's 1-tick/4-tick assumption, a protective stop that never rested at the broker, a feed
scoring garbage, an engine death mid-position, or **any day worse than −3.18R** — the model
cannot produce one because we have never had one. That residual now lives in gates **A7**
(stop provably resting) and **C7** (engine dies mid-trade), not in sequencing.
