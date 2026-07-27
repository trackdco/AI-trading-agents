# FINDING — the discretion prize is in trade MANAGEMENT, not entry selection

**Angus, 27 Jul:** *"agent discretion for trade management, not entries specifically. entries
fire more than frequently enough that that isnt relevant."* Two rules, in his words:

1. *"if a trade is up 1r and there is heavy order flow against it, having an agent with
   discretion it could confidently close the trade then and there instead of waiting for it
   to lose."*
2. *"when theres a trade thats running, if the orderflow is heavily favouring the trade
   still, hold it for longer."*

Measured with `scripts/exit_headroom.py` (122 winners / 142 losers, 202 days, fit window).
Excursion is **path-correct**: measured only while the position is alive on its original
stop, so a trade stopped at 09:00 cannot inherit a 15:00 rally.

## Entry selection is the wrong place to spend discretion — Angus is right

`scripts/canon_attribution.py`: the canon's 449 rejects run **19% WR / −$73,806**, and every
ladder layer is dollar-negative on what it discarded bar one 5-trade cell. The skip layer is
already competent, and entries fire ~2.8 candidates/day for ~1.05 taken. There is no
frequency problem to solve.

## The exit side has real room

| winners only (n=122) | mean | median | p75 | p90 |
|---|---|---|---|---|
| realized R | **2.14** | 1.82 | 2.82 | 4.14 |
| MFE while alive, to 16:00 | **7.28** | 5.08 | 8.36 | 17.74 |

Mean available is **3.4× mean realized**. Separately worth noting: **57% of winners exit
below the 2R floor** — the floor governs the target, not what gets realized (managed exits,
BE stops, EOD flatten, partials).

Peak lands at a median **52 minutes** after fill (p25 18m, p75 88m). Pre has more room than
gold: 3.53R vs 1.68R median.

## Rule 1 — cut when flow turns (losers that were in profit)

| was up ≥ | n | % of losers | ceiling swing @1 lot |
|---|---|---|---|
| 0.5R | 90 | 63.4% | $43,518 |
| **1.0R** | **48** | **33.8%** | **$29,072** |
| 1.5R | 33 | 23.2% | $23,915 |
| 2.0R | 18 | 12.7% | $13,642 |

Those 48 losers actually realized **−$13,708**.

## Rule 2 — extend the runners (winners)

| left behind ≥ | n | % of winners | ceiling @1 lot |
|---|---|---|---|
| 1.0R | 95 | 77.9% | $227,496 |
| 2.0R | 75 | 61.5% | $215,952 |
| 3.0R | 60 | 49.2% | $197,756 |

## Rule 1's ceiling is the more credible one, despite being 8× smaller

Cutting at +1R exits at a price the trade **actually traded through** — the only thing
required is the decision. Rule 2's $227k assumes exiting at the exact high of every winner,
which nobody achieves. Read the small number as closer to reachable money and the large one
as a bound.

**And holding alone does not work: 78% of winners would eventually be stopped out if simply
held to 16:00 on the original stop.** Only 22% never touch it. The trail is not a refinement
of Rule 2 — it is the whole of it.

## The best argument for discretion is already in this repo

Layer 2d, the shipped 3-minute in-trade cut (`r_3 ≤ −0.1106 AND fw_3 ≤ −13 → exit`), is a
mechanical Rule 1. It earns **+$1,494 / +$2,369**. The attached finding
(`docs/CANON-MECHANICAL.md`, 25-Jul) is the point:

> **CRITICAL: only h=3 works — the same rule at 5/10min LOSES money** (late exits lock in
> drawdown + forfeit recoveries).

A frozen rule can fire at exactly one instant, because a constant cannot condition on where
the trade is or what flow has done since. That is a structural limit of mechanization, not a
tuning failure — and it is precisely the gap judgment fills. Angus's version of Rule 1 is the
same logic applied continuously.

## The bar, and the trap

That same finding is the warning. Cutting on adverse flow made money at 3 minutes and lost
it at 5. And the state "up ~1R with flow against" contains both the 48 losers **and**
winners that recover — they are not separable ex ante by the flag itself. This is the veto
trap the repo keeps rediscovering (26-Jul bad-PA campaign: hard-vetoing every negative
marker flags 80% of the universe and destroys $12k).

**So the agent's task is not "apply Rule 1". It is SELECTION INSIDE that state.** That is
where judgment could beat a constant, and it is a measurable claim:

- baseline = the canon's own managed exit on the same trades
- treatment = agent manages the exit, same entries, same sizing
- graded on months-green first, totals second

Anything that does not beat the canon's exit on the same fills is not discretion worth
unlocking.

## What the agent can actually see — MBP, not MBO (checked 27 Jul)

Angus: *"the agents have MBO data because we configured for it specifically."* Close, and the
distinction matters for what can be built and validated.

- **Live (Route B) is MBP, per price level.** `src/canon/book.py`: *"Sierra's `.depth` feed is
  MBP (per-price-level), NOT order-by-order."* `src/canon/ingestor.py` splits the two
  explicitly — `OrderBook` (MBO, order-by-order) is the **Databento/replay** path;
  `DepthBook` (MBP levels) is the **Sierra `.depth` file-tail**, which is the live one.
- The `nq-mbo-archive` bucket name is legacy; `config/live.yaml` records the prefix being
  *"repointed from the old `mbo` prefix"*. The name says MBO, the contents are Sierra depth.
- **But the live book does carry `NumOrders` per level.** Not queue position, not order IDs —
  yet enough to tell one order of 500 from fifty of 10, which behave nothing alike.

**So the AUC 0.69 above is a FLOOR, not a ceiling.** It was computed from 1-minute aggregated
aggressor delta with no book at all. Angus's argument that an agent sees more than this
measurement did is correct.

### HARD LIMIT: MBP-10 sees ~5 points of book, so "structural level" reads are impossible

Angus, 27 Jul, correcting a proposed test: *"you cant see that because you have mbp 10 data
not mbo."* Correct, and the magnitude matters. Measured on real snapshots
(`depth_2026/nq_depth_2026-02-02_ny.csv`, 150 snapshots):

| | points |
|---|---|
| bid side depth | median **2.25** |
| ask side depth | median **2.25** |
| full book width | median **5.25** (max 18.5) |

His worked example — *"theres a massive heatmap level 40 points away, im gonna trail my
stops and target there"* — is **~8x beyond what MBP-10 can represent**. Any attempt to test
"did price run to the big resting level ahead" on this data is fitting noise, and a test to
that effect was abandoned rather than run.

This also reframes the canon's own depth checks: observed `dep_wall_above_d` runs at a
median 3.50 pts from entry. `WALLSZ` / `D` read immediate microstructure AT THE TOUCH. They
are not structural-level reads and should never be described as such.

**Consequence for the discretion design:** the level-selection half of Angus's judgment
(pick a further structural target) cannot be validated on any historical data we hold. Only
the flow half can. Either the agent is given a level source that is not the MBP-10 book
(volume profile / prior-session structure from bars, which we DO have), or that half stays
unvalidated until a richer book feed is recorded.

### The `ct` gap, and why it is not urgent

| format | order count kept? |
|---|---|
| NY long (`depth_2025/2026`, read by `trade_matrix`) | NO — `ts,side,price,size` |
| London wide (`depth_london/`) | yes, 20 `_ct_` columns |
| `depth_london_10_13/` parquet | yes |
| 2023/24 holdout pull | NO for NY, yes for London |

NY discards exactly the field that separates book structure from book size. The gap is
**symmetric** though: 2025/26 NY lacks `ct` as well, so re-pulling only the holdout would
give the field out-of-fit and not in-fit — useless for deriving anything. Using `ct` for NY
means re-pulling both spans; a deliberate decision, not a mid-run correction.

London already has `ct` across the full history AND the holdout, so whether order count
carries signal can be answered there first, with no new data.

## Why R-expansion, not win rate — Angus's framing, priced

*"our win rate is already around 50%, im far more worried about taking 50% win rate 2rr to
50% win rate average 3rr then taking it from 50 to 70% at the same average r."*

Canon as it stands: 46% WR, avg winner +2.14R, avg loser −0.99R, **expectancy +0.455R/trade**.

| route | expectancy | vs now | what it needs | evidence it is reachable |
|---|---|---|---|---|
| **A** 50% WR @ 3.0R | +1.006R | 2.21x | winners 1.41x bigger | median MFE 5.08R available vs 1.82R realized |
| **B** 70% WR @ 2.14R | +1.198R | 2.63x | win rate 1.51x higher | none — see below |

Stated honestly: **B is worth marginally more if achievable.** The case for A is not that it
pays better, it is that it is the only one with demonstrated headroom. Against B: the canon's
skip layer already discards at 19% WR / −$73,806, every attribution layer is dollar-negative
on what it rejected, and the 26-Jul bad-PA campaign put 18 candidate entry filters through
the bar with ZERO surviving out of sample. One route has measured room; the other has a
record of failed attempts.

## Status

Measurement only. No trading behaviour changed; `RULING-mechanical-only.md` stands. This
sizes the prize and sets the bar for the exit-discretion design — it does not authorize one.
The 2023/24 holdout comes first, and it is also the honest place to run the test: a
discretion trial on the fit window would be an agent learning on data the canon was tuned to.
