---
date: 2026-08-05
status: KILLED (final) — depth searched, W failed its selection-corrected null
tags: [london, session-structure, trigger-density]
sources: ["articles/2026-08-05-channel-map-four-traders.md", "findings/london-nq-what-three-traders-agree-on.md", "findings/london-window-LDN-WIN-01.md", "https://www.youtube.com/watch?v=hcVhQBAGGFw", "https://www.youtube.com/watch?v=JySO8cOWOIs", "https://www.youtube.com/watch?v=1noM1ogc5zM"]
---

# london-nq-open-break — the 08:00 UK level break on NQ, with a stop tight enough to pay

## Thesis (for Angus)

At 08:00 UK the London cash market opens and NQ gets its first real European
liquidity of the day. In the ninety minutes before that, price has been drifting
in a thin book and has left obvious marks — a high, a low, the edges of the
overnight balance. Those marks are where the orders sit, because they are the
only structure anyone can see.

When the open arrives, the first thing that happens is one of those marks gets
tested. Either real size is behind the move and it goes, or it isn't and price
snaps back through the people who chased it. **The trade is that resolution**, and
it happens in a tight window because the open is a scheduled event, not a mood.

The wrong side is whoever committed to the pre-open drift — someone who bought
the high at 07:40 on 200 contracts of evidence and finds out at 08:00 what
4,000 contracts think.

**Why I believe the clock and not just the trader.** Three independent sources
land on the same minute and none of them got it from each other:

- Brandan trades it as **08:00 UK sharp**, marking his levels from 07:55
- EzTrades' completely different model (PO3/IFVG) calls **03:00 ET** the
  manipulation window — the same instant
- And our own measurement, `LDN-WIN-01`, found **03:00 ET is the volume peak of
  the entire session, in both eras**, with a second peak at 04:00

I ran that measurement before reading either trader's clock. The agreement was
not arranged.

**Why the geometry is the point, not the setup.** This is a level break — the
most-taught idea in trading, and on its own worth nothing. Tradesharpe, who
trades a version of it, says so outright: naive opening-range breakouts backtest
to *"like a 50% win rate... the issue is stop loss is not optimized."* His fix is
not a better trigger, it is a tighter stop: *"you are wasting so much
profitability by running stops below that whole open candle."*

Brandan runs the same conclusion as a number: **~10-point stop on MNQ,
"predominantly 10", exiting at 1:2.** Fabio, on a different continent and a
different setup, describes his A+ trade as *"really low risk"* and names slippage
as the only thing that worries him.

**That axis is the one this programme has already died on.** `nypre-euro-handoff`
reached 78% win rate and paid +0.02R, tombstoned as *"the handoff is a fact, not
a trade — its natural geometry cannot pay per unit risk."* The published version
of this candidate arrives with the fix already attached. That is the reason to
test it and it is the only genuinely novel thing about it.

**What I do not believe.** The video is titled *"89.5% Win Rate"*. Inside the
same video he says *"if we know there's a 60 to 70% win rate."* In his December
backtest he re-scores a logged loss as *"realistically break even... nearly hit
our take profit."* He sells prop-firm discount codes throughout. **The hit rate
is marketing.** The number that decides this is R, which he never quotes — a
10-point stop at 2R needs about 35% to break even before costs, and that is the
bar we are actually testing against.

## Skeleton

Instrument **NQ** (he trades MNQ; same contract, different multiplier).

Before 08:00 UK: mark the pre-open structure — pre-open high/low over a declared
lookback, plus the overnight extremes we already carry in the substrate.

From 08:00 UK (03:00 ET; **use `euro_open_clock`, never `euro_open_det` —
`docs/FINDING-euro-open-det-is-noise.md`**): on a test of a marked level, trade
the resolution. **Two declared entry arms and they are the whole experiment:**

- **A — close-confirmed** (Tradesharpe): wait for a candle to close beyond the
  level, enter on the break of that candle's high/low
- **B — touch** (Brandan): enter on the reaction at the level, no close required

Stop: beyond the trigger candle, **not** beyond the whole range. Target 2R fixed
initially, with next-structural-level as a declared alternative. Flat by 05:00 ET
per `LDN-WIN-01` — the 05:00–06:00 hour carries the worst efficiency in the
session and should not be inherited.

## Promotion rule — declared BEFORE any tournament (§6.0.1)

Rank-and-promote-the-top-scorer is a condemned procedure. So the winner here is
named in advance, on mechanism, not on results:

**Default spec = arm A, close-confirmed entry.** It is the mechanism prior: the
thesis is that the open *resolves* a level test, and a close beyond the level is
what resolution looks like. An entry on touch is a bet placed before the
resolution the thesis is about. A also inherits the tighter stop the whole
candidate rests on — the trigger candle exists only if you waited for it.

**Arm B (touch entry) may displace A only if BOTH hold:**
1. PBO on the A/B arm matrix is **< 0.5** (CSCV, day-level rows), and
2. the holdout adjudicates in B's favour under §5.9.4's single corrective
   iteration.

**In-sample rank alone never promotes B.** If B out-earns A in sample and fails
either condition, the frozen spec stays A and B is ledgered as a declared
negative result.

**If both arms fail their own bars, neither ships.** The candidate is not
promoted by being the better of two losers.

## Bars — pre-registered per §5.9.3 and §5.9.5

- **Census (L0) kill line, per §5.9.1:** this dies at census ONLY if the claimed
  behaviour does not happen — i.e. if levels marked before 08:00 UK are not
  tested in the window, or tests do not resolve. **Raw profitability does not
  kill at census.** Ugly P&L at raw triggers sends it to the variable search, it
  does not close the family.
- **Sleeve bars:** era consistency (2025/2026 agree in direction, plus the
  inverse pass), cost realism at the standard stack **and at 2× slippage**, and
  **PSR(0) ≥ 0.75** per §5.9.5.
- **Deflation is charged at book level** (§5.9.3), not against this sleeve alone.
- **Every trial goes to `output/trial_ledger.parquet` at trial time**, not just
  into this file's prose (§6.0.2).

## Flags

- **Data: fully in hand.** `nq_1m_master.parquet` and the 912-day London
  substrate. No purchase, no new plumbing.
- **A-vs-B is one binary variable over one trigger**, not two strategies. It is
  the cheapest informative experiment available here and it resolves a real
  disagreement between two live traders.
- **The stop rule is the transferable component.** If trigger-candle stops beat
  structural stops here, that result should be tried on triggers we already own —
  which is worth more than this candidate is.
- Costs are the kill test, not a formality. A ~10-point stop on NQ is a handful
  of ticks; Fabio names NQ slippage as the one thing that breaks his version.
  The 2× slippage arm decides this candidate.
- Redundancy: check `pairwise_overlap` against the canon's fills at census time,
  per program flag 1. Different session from the NY canon, so expected low, but
  measured not assumed.
- Instrument-transfer caveat: Brandan's other content is NAS100/US30 CFDs and
  gold. The structure transfers; the cost stack does not.

## Trial ledger — LDN-OBK-01

### Trial 1 — L0 census (2026-08-05) — **PASSED on premise, advances to L1**

`docs/PREREG-london-open-break-tree.md` (committed before the run, plus one
pre-run amendment replacing a null control with a real one).
`scripts/london_obk_census.py`. 396 London sessions, 2025 discover / 2026 validate,
**2023/24 untouched — no holdout look spent.**

**1. The break happens, overwhelmingly.** The pre-open range (06:00–08:00 London) is
broken inside 08:00–10:00 on **92% of 2025 days and 93% of 2026 days** — 425 break
events, about 1.1 per session. The declared census floor was 30%. There is no
question that the event exists.

**2. The event is bimodal, and that is the finding.** Splitting breaks by whether
they closed back inside within 120 minutes:

| era | outcome | n | median excursion beyond level |
|---|---|---:|---:|
| 2025 | failed | 234 | 8.6 pts |
| 2025 | **continued** | 42 | **63.9 pts** |
| 2026 | failed | 125 | 11.5 pts |
| 2026 | **continued** | 24 | **96.5 pts** |

Roughly a **7–8× separation** in both eras. This is the number that justifies the
whole event-tree framing: a break either dies within about ten points or it runs
most of a session's range. There is no meaningful middle. **A discriminator is worth
building here; picking a side without one is not.**

**3. The continuation branch is the rare one.** Only **15% (2025) / 16% (2026)** of
breaks continue. That is the honest shape of this candidate: it is a low-frequency
trade — roughly 42 and 24 events per era — hunting a large move. Under §5.9.3 that
ships as a book component if it pays, which is exactly what the frequency-floor
abolition was for. It also means **the trigger-candle stop is not a refinement here,
it is the entire candidate**: paying ~10 points to find out you are in the 15% is the
only version of this that can work, and that is the axis `nypre-euro-handoff` died on.

**4. Break quality — the as-taught definition admits noise.** 27% (2025) / 9% (2026)
of breaks extend less than 5 points. The prereg froze a bare 1-minute close beyond
the level because neither source states a minimum displacement, so that is as-taught
per §5.9.1. **Minimum displacement is the first L1 declared variable**, and the era
gap (27% vs 9%) is itself worth a look — 2026's ranges are wider, so a fixed
point-threshold is probably the wrong shape and a fraction-of-range threshold the
right one.

**No P&L was computed and none was needed.** §5.9.1 forbids a census expectancy kill
and the prereg declared no P&L at this stage.

**Recorded:** `LDN-OBK-01` × 2 eras in `output/trial_ledger.parquet` (frequency
premise, no effect charged — a trigger count is not an edge claim).

**Next rung — L1.** Trigger-candle stop vs structural stop, arm A (close-confirmed)
as the declared default per the promotion rule above, 2R fixed target with
next-structural-level as the declared alternative, costs at 1× and 2×. Minimum
displacement enters as the first declared variable, expressed as a fraction of range.

### Trial 2 — L1 mechanics (2026-08-05) — **the tight-stop claim FAILS as declared**

`docs/PREREG-london-open-break-L1.md` (committed before any P&L was computed).
`scripts/london_obk_l1.py`. Same 396 sessions, 2023/24 untouched.

**The declared default arm, A/S1 — close-confirmed entry, trigger-candle stop, 2R:**

| era | n | WR | net pts | $ @160 risk | PF | R/trade |
|---|---:|---:|---:|---:|---:|---:|
| 2025 | 256 | 32% | −479 | −$8,130 | 0.79 | −0.198 |
| 2026 | 138 | 38% | +88 | +$294 | 1.06 | +0.013 |

At strict (2 pt) cost both eras are negative. **Brandan's advertised 89.5% win rate
lands at 32–38%**, which is roughly where the file predicted it would once R was the
question instead of hit rate.

**The declared test failed in every cell.** The pre-committed reading was: the
tight-stop claim is supported only if S1 beats S2 on R/trade in both eras at both
cost levels. **It wins 0 of 4.**

**The one-line reason, and it is the whole finding.** At a 2R target the
trigger-candle stop is hit **65%** of the time and the target **30%**. A 2R trade
needs 33.3% to break even *before* costs. That is break-even geometry, and the cost
stack decides it. **The tighter stop does not rescue the level break — it gets you
tapped out.** This is the same shape that killed `nypre-euro-handoff`, arriving from
the opposite direction: that one had a 78% win rate and no room; this one has room
and no hit rate.

**Read the control before reading the verdict.** The structural-stop arms (S2) exit on
the clock **82%** of the time — a 2R target on a range-width stop sits 100–170 points
away and NQ does not travel that inside a two-hour window. So S2 is not "the same
trade with a wider stop", it is a two-hour hold that exits at market. Its apparent
edge over S1 is near-zero beating negative. **Neither stop makes this pay**, and the
honest verdict is about S1 on its own terms, not about S2 winning.

**Declared variable — minimum displacement — did not lift.** Requiring the trigger
candle to extend ≥0.10× range width makes it worse in every era at every cost
(2025 −0.124R, 2026 −0.129R vs −0.198 / +0.013 unfiltered), on roughly 40% of the
sample. Recorded as a declared negative.

**No expectancy kill here, by law (§5.9.2).** The census premise passed and the
trapped-counterparty story is intact, so the family earns the conditioning search.
What it does **not** have any more is its headline reason for existing: the stop
geometry was the novel component, and it is measured and unsupported.

**Recorded:** 8 arm×era trials (all four arms, both eras) in
`output/trial_ledger.parquet` — losers included.

**Next rung.** Conditioning search on declared variables: range width, time of break
within the window, and the 04:00 ET / 09:00 London second peak from `LDN-WIN-01`
which no candidate currently uses. Exit-arm tournament is a later rung with the
default declared first; 2R was a placeholder, not an optimised target, and that is
stated so nobody mistakes this for an exit search that failed.

### Trial 3 — L3 flow + mandatory autopsy (2026-08-05) — **KILLED, expectancy, search complete**

Same prereg and same run as `LDN-PO3-01`: `docs/PREREG-london-obk-L3-flow-and-autopsy.md`.

**Zero of six declared flow features confirmed in their predicted direction.** Every
one flips sign between eras except `book_imb`, which is a control with no prediction
attached.

**Autopsy:** 16 candidate cut-sets, **5 legal** (cohort bad in every era), **none**
leaving the arm positive at strict cost. Baseline R −0.133 base / −0.233 strict on
n=300. De-risk tested alongside every hard cut, per §3.2 — all negative.

#### VERDICT — KILLED (expectancy, after the complete declared search)

This candidate had one novel component and it was measured and refuted at L1: the
tight trigger-candle stop lost to a structural stop in **0 of 4** era×cost cells, and
on its own terms it is hit 65% of the time against a 30% target rate — break-even
geometry that costs turn negative. The conditioning search then confirmed only 1 of 3
mechanism predictions, and the flow pass confirmed none.

**The clock was right and the trade was not.** Three independent sources and our own
`LDN-WIN-01` measurement agree that 08:00 London is the moment; the census confirmed
the level gets broken on 92–93% of days; the event is genuinely bimodal (failed breaks
run ~10 pts, continued breaks 64–97). **None of that converted into an edge per unit
of risk**, which is the same sentence written on `nypre-euro-handoff`'s tombstone and
is now the second time this programme has learned it in a different session.

**What survives:**

1. **The 09:00 London / 04:00 ET macro hour is the one variable that confirmed
   (4/4 cells).** It did not save this candidate — 2025's macro hour still loses — but
   it is the only London clock finding that came from our own measurement rather than
   a trader's claim, and **no live candidate uses it**. It should outlive this file.
2. **A negative control for the funnel.** Census passed wide, raw was ugly, the
   variable search ran in full, and the thing still died. That arc is what the funnel
   is supposed to do to a bad idea, and it is worth having next to the canon's arc.

**Never looked at:** 2023/24 candles, sealed flow months. No holdout look spent.

### VERDICT WITHDRAWN (2026-08-05, same day) — §5.11/§5.12 landed after the kill

The canon rebuild ratified §5.11 (pre-ship checklist) and §5.12 (canon map) after this
verdict was written. **The kill does not survive them and is vacated.** Full reasoning:
`research/findings/LDN-kill-vacated-under-511-512.md`.

The short version: §5.12.10 records that on the shipped canon, **depth carried the
entire edge (+0.5 to +1.3R) while order flow at entry was a rounding error** — and my
L3 pass was four tape features at entry plus two thin book features. I ran the weakest
variable class at the weakest moment and treated the null as decisive. The canon's
actual edge carriers (`W` = no wall behind, `D` = wall ahead, `WALLSZ`) were never
built here.

Five further gaps, each with a rule and an NY-lane precedent: pooled flow nulls cannot
close a gate question (§5.11.4); no event-universe sensitivity (§5.11.2); no stop-cap
arm class (§5.11.3); no time-segment/MFE-MAE pack, so in-trade flow — where the canon
says flow actually works — was never tested (§5.12.5); no permutation null on the
carried V1×V3 combination (§5.12.4).

**This is not a claim that the strategy works.** The L1 economics are poor and the
tight-stop claim genuinely failed 0/4. It is a claim that under §5.9.2 the expectancy
kill was not yet legal, on the same precedent that twice vacated `nya-ivb-fadeB`'s
kills — a candidate now running PF 1.56/1.57/1.20 and PSR 0.994.

Census, L1 and the conditioning search all stand and are not re-run. No holdout look
was spent, so nothing is lost by re-opening.

### FINAL — KILLED (2026-08-05), depth searched, `W` failed its selection-corrected null

The vacated kill has now been re-run properly. `docs/PREREG-london-depth-pass.md` and
`docs/PREREG-london-W-scrutiny.md`, both committed before their runs.

**Gap 1 closed — depth WAS searched, at canon thresholds.** Eight single checks,
direction-resolved, NaN standing down, on 1,168 trades with book data. 9 of 32 check×arm
cells survived every era. Exactly one was positive at strict cost in both:
**`W` (no wall behind) on `A/S1`** — +0.204R (2025H2, n=37), +0.478R (2026, n=38), lift
+0.734/+0.756. That is inside the canon's own +0.5 to +1.3R depth band and it is the
canon's pre-market gate transferring on mechanism.

**And it does not survive its own selection correction.** I tested 32 cells and reported
the best one, so the null was built around that whole procedure: shuffle the check labels
within arm and era, re-run the entire 32-cell selection, 10,000 times.

| quantity | observed | null | p |
|---|---:|---|---:|
| max era-consistent lift | +0.734 | median +0.299, 95th pct +0.598 | 0.0158 |
| cells surviving every era **and** paying at strict cost | 1 | ≥1 in **42.1%** of shuffles | **0.4209** |

**Declared pass condition was family-wise p < 0.05. It came in at 0.42.** My own search
procedure produces a result this good from shuffled labels in more than two runs in five.

**The two statistics disagree and the declared one governs.** The lift *magnitude* clears
its bar (p=0.016); the *existence* of a survivor does not. The headline I actually
reported was "exactly one survivor pays at strict cost in both eras" — an existence claim
about the output of a 32-cell search, which is precisely what the failing test nulls.
Switching to the statistic that passes, after seeing which one passes, is the procedure
this framework exists to prevent. Re-opening on the magnitude result would need a new
prereg declaring that criterion in advance, on an independent sample.

Per the prereg, tests 2–4 (event expansion, stop caps, state-conditional) were **not
run** — more search on a result that cannot clear its own selection correction only
inflates the ledger denominator.

## VERDICT — KILLED, and this time the search is genuinely complete

Both highest-prior variable classes have now been tested at the canon's own definitions
and thresholds:

- **flow at entry** — 0 of 6 features confirmed; the declared mechanism variable
  (`delta_sweep`) pointed the wrong way
- **depth at entry** — 9 of 32 cells survived, 1 paid, and it failed its selection null

The premise stays true and on the record: the pre-open range breaks on 92–93% of days,
breaks fail 84–85%, and that beats a placebo range by +12/+14pp in both eras. **There is
no way to get paid for it that survives honest scrutiny.**

**No holdout look was ever spent** — 2023/24 candles, the sealed flow months and
`depth_london_2023_24` are all untouched. The family dies without costing the programme
a single look.

### §5.12.15 SEMANTICS CORRECTION (2026-08-05) — `W` was described wrongly above

Everywhere this file calls `W` *"no wall behind"* and attaches a thin-overnight-liquidity
story, **that description is wrong.** The v2 dissection established, and an audit on our
own 300 `A/S1` trades confirmed, that `W` is **displacement geometry**: `W=1` means the
entry sits beyond the entire visible ladder (96.0% of the time; median 3.62 pts beyond a
ladder spanning ~5.5 pts). The book has not caught up to price — it is not a statement
about resting size at all.

**The verdict is unchanged.** `W` failed its selection-corrected permutation null at
family-wise p = 0.42, and a permutation null shuffles labels and is indifferent to what
they mean. A better mechanism story for a result that failed its own null is not grounds
to reopen. Full audit: `research/findings/LDN-W-semantics-audit.md`.

Also flagged there: this run used the canon's **absolute** thresholds (`WALLSZ >= 7`,
`WALLFAR >= 2.75`) where §5.12.15 now prefers quantile/relative ones, and the basis stamp
(§5.12.13) for every depth conclusion here is 1,168 trades with book state at the L1
geometry, $160-risk, 1pt/2pt costs.
