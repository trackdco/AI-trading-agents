# FINDINGS — G3b killed, and the queue/latency stress (2026-09-03)

Two results. The first corrects a recommendation I made earlier today.

## 1. G3b (widen first-in-wins to any distance): KILLED

**The rule tested.** Current G3 blocks a same-direction entry when another
book holds a same-direction position within one stop floor (5pt). G3b
would block it at *any* distance.

**Why it was proposed.** The conviction audit found a bucket — "another
book holds a same-direction position more than 5pt away" — running
**−0.070 net EV, negative in all four half-cells** (n = 552 + 455). I
called it recommendation #1 and "the cheapest rail to add".

**Measured in the rail pass:**

| empire | rail | trades | total R | R/day | maxDD | Sharpe |
|---|---|---:|---:|---:|---:|---:|
| flat | G3 (within one floor) | 71,961 | +9,896 | +10.74 | −18.1 | 1.158 |
| flat | **G3b (any distance)** | 70,366 | **+9,482** | +10.30 | −19.0 | 1.138 |
| armed | G3 | 58,401 | +10,467 | +11.36 | −14.0 | 1.207 |
| armed | **G3b** | 57,724 | **+10,353** | +11.24 | −14.0 | 1.202 |

Worse on both books: **−414R flat, −114R armed**, drawdown-matched R/day
−9.4% IS / −8.8% OOS on the flat empire. **Not adopted.**

**Why the audit was misleading — the lesson.** The trades G3b actually
removes:

| | n | WR | net EV | total |
|---|---:|---:|---:|---:|
| kept by G3, blocked by G3b | 1,598 | **72.3%** | **+0.2580** | +412R |
| let in by G3b, not by G3 | 4 | 67% | −0.0768 | −0R |

They are not the audit's losers. They are **among the best trades in the
book** — 72.3% win rate against the book's 65.6%.

The audit measured its bucket on the **raw** book dumps, before any rail.
The rail pass is chronological and sequential: G3's floor rule already
removes the genuine duplicates (same level, same price, same direction),
and blocking a trade changes which positions are open for everything
after it. What survives G3 and would be caught by G3b is a *different
population*: a second book signalling the same direction at a **different**
level more than 5pt away — which is a trending move with multiple levels
breaking, not a duplicate. Those are good trades.

**General lesson for this program: an audit bucket is not a rule effect
whenever the rule changes occupancy.** This is the same shape as two
findings already logged — the zero-multiplier sizing scheme excluded
because a skip is not a size, and S34's +41R from skipped signals freeing
the book. A feature measured on a static dump tells you about a
population; a rail tells you about a sequence. They are not the same
thing, and the difference here was worth 826R of sign error.

## 2. Queue and latency stress

**Queue proxy** — require price to trade N ticks *through* the level
before a resting limit counts as filled. Full empire, rail-passed:

| variant | trades | /day | EV/trade | total R | R/day | maxDD | Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|
| frozen spec (1 tick) | 71,961 | 78.1 | +0.1375 | +9,896 | +10.74 | −18.1 | 1.158 |
| + arming 1R | 58,401 | 63.4 | +0.1792 | +10,467 | +11.36 | −14.0 | 1.207 |
| **2 ticks through** | 71,390 | 77.5 | +0.1040 | +7,422 | +8.06 | **−29.1** | 0.895 |
| 2 ticks + arming | 57,935 | 62.9 | +0.1428 | +8,271 | +8.98 | −20.3 | 0.979 |

Doubling the fill requirement costs **25% of the R and 61% more
drawdown** — the tail degrades faster than the return, because the fills
you still get are the ones where price kept running against you. Level
book across the full curve: 1 tick +0.141 → 2 ticks +0.105 → 4 ticks
+0.030 → 8 ticks −0.123. **The edge dies between 2 and 4 ticks.**

Arming recovers roughly half the damage but does not rescue it: a 2-tick
world costs more Sharpe (1.158 → 0.895) than arming gains (+4%).

**Depth calibration** (April 2026 MBP-10, 173,980 level observations):
median resting size at a level **3 contracts**, ~11.5 contracts trade per
tick per minute, and the strategy's own levels are only **~10% thicker**
than the rest of the book — the "everyone stacks orders at the obvious
levels" worry does not appear in the data. So 1 tick is defensible for a
retail-size order. The caveat: the uniform-volume assumption is generous
exactly at a bar's extreme, which is where the level sits on a
touch-and-reverse. A depth-conditioned EV test was attempted and
abandoned — only 51 fills landed in a minute where the entry price was
inside the visible 10-level book, and the buckets were noise.

**Latency** — extra whole bars between arming and the order going live.
The sim already withholds the arming bar itself, so the baseline carries
up to 60s implicitly:

| extra delay | trades | kept | EV/trade | WR | net R | maxDD |
|---|---:|---:|---:|---:|---:|---:|
| none | 18,582 | 100% | +0.1791 | 67.0% | +3,327 | −12.1 |
| **+1 bar** | 17,104 | 92% | **+0.1173 (−34.5%)** | 63.6% | +2,006 | −17.2 |
| +2 bars | 15,633 | 84% | +0.0814 (−54.5%) | 61.6% | +1,273 | −28.1 |

One bar is 60 seconds — a thousand times real network latency, so this is
not about the connection. It is about the executor's loop shape. The
+1-bar row is what you get if the executor notices the arming on a bar
close but places the order on the *following* bar. **Requirement: the
arming check must fire and the order must reach the exchange within the
same minute the arming bar closes.** A once-per-bar poll that acts on the
next bar costs a third of the edge.

## 3. What to do about it

The single highest-value instrumentation for the paper-trading bridge:
**log the fill penetration of every resting limit** — how far did price
trade through the level before you filled? Compare that distribution to
the 1-tick assumption. That converts the largest remaining unknown in the
whole program into a measurement, and it is a small amount of executor
code.
