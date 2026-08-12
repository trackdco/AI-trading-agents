# Loser autopsy — London book (Stage 8)

686 trades, 245 days. Winners 259 (37.8%, mean **+2.161R**), losers 427 (mean
**−0.842R**). Losers average better than −1R because the shipped exit banks 75%
at 3R and trails, so some "losers" are partial scratches.

**Exploratory by construction. Everything below is a HYPOTHESIS, not a finding** —
the autopsy cannot be priced by corrections that need an enumerable trial count.
Each item queues as a pre-declared cut with its own bar, on data it has not
touched.

---

## The pseudo-replication check — run first, and it comes back clean

The skill's warning for this stage is that a day-level property masquerades as a
trade-level one: *"ninety percent of losers could be ninety percent of twenty bad
days."* Measured directly:

| Check | Result |
|---|---|
| Losers' spread | 427 losers across **223 distinct days** (of 245) |
| Worst 20 days | hold only **19%** of all losers |
| Worst 20 days | −64.4R = 39% of losing-day R |
| **ICC of `out_ship`** | **0.000** — between-day variance ≈ 0 |
| Effective n | **686** (equal to raw n) |

**The outcome is essentially trade-level.** There is no day-clustering to inflate
significance, so trade-level separations can be read at face value and the
day-block bootstrap collapses to the ordinary one. That is the *opposite* of the
feared pattern and it makes this autopsy more informative than the stage usually
allows.

## Can winners be told from losers? Partially — modestly, not dramatically

The autopsy hoped-for prize is a property in ~90% of losers and ~30% of winners.
**Nothing here is remotely that large.** The best separation is a Cohen's d of
0.33 and a 10-point rate difference. Honest answer: yes, there is real signal,
but it is modest.

| Variable | Winners | Losers | Cohen d | Day-block 95% CI of difference |
|---|---|---|---|---|
| `risk_W` (stop ÷ band width) | 0.315 | 0.248 | **+0.327** | [+0.035, +0.101] ✓ |
| `risk` (stop, pts) | 24.58 | 20.02 | +0.254 | [+1.73, +7.44] ✓ |
| `closeloc` | 0.713 | 0.654 | +0.228 | [−0.003, +0.115] |
| `bp5opp` (opposing book pressure) | 0.486 | 0.585 | **−0.199** | [−0.183, −0.018] ✓ |
| `d15_conf` | 0.502 | 0.406 | +0.192 | [+0.013, +0.174] ✓ |
| `flowconf` | 0.645 | 0.562 | +0.168 | [−0.002, +0.169] |

Everything else — `volx`, `rangex`, `cvd_slope30`, `delta_z`, `w15`, `d30_conf`,
`eff_result`, `n_attempts`, `thru_delta_conf`, time-of-day — separates negligibly.

## Collinearity: this is two findings, not five

| | risk_W | risk | closeloc | bp5opp | d15_conf |
|---|---|---|---|---|---|
| risk_W | 1.00 | 0.67 | 0.58 | 0.03 | 0.02 |
| closeloc | 0.58 | 0.60 | 1.00 | −0.08 | 0.04 |
| bp5opp | 0.03 | 0.01 | −0.08 | 1.00 | −0.28 |

`risk_W`, `risk` and `closeloc` are **one geometry family**. `bp5opp` is
independent of it. So there are two candidate mechanisms, not five — and counting
them as five would have been the confluence-stacking error this programme has
already demonstrated four times.

---

## H-A1 — Trigger geometry: wider stops win

Dual-currency check (**mandatory here**, since this is exactly the variable class
that killed `close_dist_bw` and produced the permanent stop-width law):

| `risk_W` quartile | n | Win rate | EV (R) | Median stop |
|---|---|---|---|---|
| Q1 low | 172 | 28.5% | **−0.003** | 7.0 pt |
| Q2 | 171 | 37.4% | +0.355 | 13.5 pt |
| Q3 | 171 | 35.7% | +0.281 | 21.3 pt |
| Q4 high | 172 | **49.4%** | **+0.534** | 31.1 pt |

**Win rate and EV move in the same direction** (+0.209 and +0.536), so this is
*not* the artifact where a wider stop buys hit rate through the denominator. It
also survives controlling for both flow variables (gap +0.154/+0.316 within
`bp5opp`; +0.324/+0.142 within `d15_conf`), and holds on both split-halves
(+0.102 / +0.346).

**Mechanism, and it is the same diagnosis as the PXL work:** Q1's median stop is
**7 points**, against a London window whose median 15m candle range runs 17–28
points. That stop sits well *inside* a single candle. A tight stop here is not
precision, it is a marginal trigger that barely poked the level — small trigger
candle, weak displacement, and a stop the noise reaches on its own.

⚠️ **Direct contradiction to flag.** The *other* London programme's sealed run
found the **sub-9.5pt risk band passed strongly** (n=146, mean R +0.560,
p=1.4e-05) — the opposite direction on the same variable class. Different book,
different trigger grammar, and their frozen config nonetheless sets
`LON_RISK_MIN = 9.5` (excluding tight risk), which agrees with *my* direction and
not with their own S1 result. Unresolved, and worth resolving before anyone acts
on either.

## H-A2 — Absence of opposing book pressure

| `bp5opp` | n | Win rate | EV (R) |
|---|---|---|---|
| 0 (no opposition) | 310 | **42.9%** | **+0.432** |
| 1 | 376 | 33.5% | +0.176 |

Gap +0.255R, and the **most stable of everything tested** across halves (+0.194 /
+0.329). Independent of the geometry family.

This is not new — it independently rediscovers their own recorded result that
**"the best single flow construct in M1/M3 is an ABSENCE (`NO_OPP`)."** Treat it
as a replication of a known effect rather than a discovery, which also means it
inherits their finding that it does not survive being stacked with other flow.

---

## Multiplicity, stated plainly

22 comparisons were run. At 5% that is ~1.1 false positives expected by chance,
and 4 cleared. So probably three are real — but **which three cannot be
determined from this data**, and that is precisely why these stay hypotheses.

## Queued as pre-declared cuts

| Hypothesis | Declared direction | Bar |
|---|---|---|
| **H-A1** trigger geometry | Drop bottom-quartile `risk_W` | Positive lift, both halves, dual-currency same-direction, frequency reported |
| **H-A2** `bp5opp == 0` | Keep no-opposition only | Same, plus must not be stacked with other flow |

Both cost frequency — H-A1 removes 25% of the book, H-A2 removes 55% — and under
the payout objective frequency manufactures qualifying days, so both need scoring
on **both axes** before adoption.

**Venue: forward-recorded data only.** The bar-only holdout is permanently closed
and this autopsy has now touched the entire fit era. Neither hypothesis can be
confirmed on any existing data.
