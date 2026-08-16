# PHASE 0 — verification (blocking, before any new claim)

Run 2026-08-07/08. Four items from the cold-start handoff. Everything here
was executed BEFORE Phase 1 declarations and before any Phase 2/3 compute.

## Item 1 — entry-price test: FAIL, two defects found and fixed

The perturbation gate proves features are as-of the decision bar; it is
structurally blind to the entry price (a price read off the decision bar is
INVARIANT under post-decision perturbation — the invariance is the defect).
New standing gate: `scripts/htf_ma_entry_gate.py` (T1 flatten, T2 row-level
next-open assert, T3 fill-bar close perturbation).

**Gate result against the builder as handed off (8 fit days, stride 40):**

```
T1 flatten: 45 probes | flat-run entry wrong: 0 | entry moved vs real: 21
T2 next-open (reject): 21/23 FAIL — entry == decision-bar close, not next open
T3 fill-bar close (break): 15/22 FAIL — fill price moves ~dClose/20 when the
   fill bar's close is perturbed (developing-MA term)
ENTRY GATE: FAIL
```

Defect A (reject arm): `entry = b_.close` — the decision 15m bar's own close.
The prereg M-TABLE block declares "entry at the NEXT open". The recorded
entries differed from the true next 1m open by 1-7 ticks in probes; the error
is directional-flow-correlated (momentum at the trigger), so it is a bias,
not noise.

Defect B (break arm): the retest limit fill was tested against `ma_1m[j]` —
the as-of MA at bar j INCLUDES bar j's own close (1/20 developing term,
levels.py's own docstring: "usable for decisions at t+1m and later, never at
t itself"). The level the limit rests at was not knowable until the fill bar
closed. Same class as the canon's killer (limit filled mid-bar at a level
read end-of-bar), ~Δclose/20 magnitude.

**Fix (both at root in `scripts/htf_ma_mtable.py`):** reject entry = next 1m
bar's open (rows with no next bar remain excluded — the existing named
boundary exclusion; next-open gap-through-stop rows counted and excluded by
name in the build log); break fill level at bar j = `ma_1m[j-1]` (as-of the
previous 1m close), fill iff bar j's range touches THAT value, entry at that
value. Gate re-run after fix: PASS (see build log). Numbers restated in
item 4.

## Item 2 — gray-row quarantine criterion: STATED, outcome-independent

The criterion (verbatim from both builders, `htf_ma_mtable.py` and
`htf_ma_census_b.py`):

```python
(fit    if FIT_START <= d <= FIT_END else      # 2025-06-01 .. 2026-07-31
 sealed if d < "2025-01-01" else               # 2023-01-01 .. 2024-12-31
 gray)                                         # everything else
```

Gray is therefore exactly the calendar band **2025-01-01 .. 2025-05-31**
(plus any post-2026-07-31 session days, none in the current bar set). The
assignment function reads ONLY the 18:00-anchored session date — no price,
no outcome, no feature enters. Outcome-independence: CONFIRMED by code
inspection and verified empirically on the rebuilt table (every gray row's
sess_day falls in the band; no fit/sealed row's does).

Why the band exists (recovered, not invented): the fit span starts 2025-06
because MBP-10 depth coverage starts 2025-06-02 (HOLDOUT-2023-24-
PREREGISTRATION.md); the sealed holdout was declared as calendar 2023-24.
The five months between belong to neither declaration — they were parked,
unread. Status: the band is UNLOOKED and therefore assignable by a Phase 1
declaration. It is assigned to the bar-only holdout in
DECLARATIONS-holdout-partition.md (which restores the handoff's "~23
bar-only months" arithmetic: 24 sealed + 5 gray − 6 flow months = 23).

## Item 3 — clustering: 30-minute window replaced by structural criterion

The 30-minute same-side time window (`CLUSTER_GAP_MIN = 30`,
htf_ma_census_a.py) is wrong on its face for the desk window: the trader
takes genuinely separate entries 15-20 minutes apart in NY am. The M-TABLE's
own cluster_id (same side, same cross-cycle) is structural on the reject arm
by construction (attempt chains reset on cross) but merges consecutive
cycles' rows only via the census-A window in downstream collapses.

Replacement criterion (declared before measurement): two same-session,
same-side triggers are the SAME event iff price never left the level between
them — no intervening excursion of at least X·W from the MA between the two
trigger timestamps. With an excursion, they are separate fights. X set from
the valley of the time-gap × price-gap distribution over same-session
same-side consecutive trigger pairs (fit rows only); result and the chosen X
recorded in the build log and below.

Confidence intervals: day-level bootstrap (resample session-days with
replacement, 2,000 draws) replaces cluster-collapsed Wilson everywhere a
new claim is made — same unit the MC lab already uses. Cluster collapse
remains for point estimates.

RESULT (run 2026-08-07, `scripts/htf_ma_clustering.py`, 4,148 consecutive
same-session same-side pairs over 291 fit days):

- **The valley procedure MISSED** — recorded as a miss. The excursion
  histogram decays monotonically from its 0.1-0.2W mode through the whole
  0.2-1.5W search range; there is no interior minimum flanked by higher
  density. A boundary minimum of a monotone curve is not a valley.
- **Declared fallback applied: X = 0.50W** — the programme's canonical
  displacement threshold (Census A's D=0.5W IS the established grammar for
  "price displaced from the MA"; the return from >=0.5W is an M1 rebalance
  approach, i.e. a NEW event). Justified by the existing event grammar,
  independently of any outcome.
- Time-gap coupling (for the record): pairs with excursion <=0.25W have
  median gap 15 min (adjacent bars — one fight); pairs beyond 1W are 3+
  hours apart.
- **Cluster counts on the same 4,717-row trigger set:** 30-min window
  2,412 (NY-am 592) | cross-cycle table-native 1,740 (NY-am 532) |
  structural X=0.5W 2,218 (NY-am 765). The structural rule separates MORE
  in NY-am (the trader's genuinely-distinct 15-20-min entries: 15.2% of
  10-25-min-apart pairs carry a >=0.5W excursion and were wrongly merged by
  any time window) and merges more overnight (31.5% of >30-min-apart pairs
  never left the level — one fight the 30-min rule wrongly split).
- Map: `output/htf_ma_census/mtable_fit*_structclust.parquet`; CIs for all
  new claims move to the day-level bootstrap (D4).

## Item 4 — restated numbers (run 2026-08-07, fixed table, 4,716 fit rows)

Reproduction first: the baseline (unfixed) rebuild reproduced the recorded
build EXACTLY (fit 4,717 | sealed 8,807 | gray 1,786; continuity
3,020/3,043 = 99.2%; stop p50 0.175/0.183W; MFE p90 7.28/6.38; H2-2025
book under cross-cycle collapse −0.049R vs recorded −0.047R). Every
comparison below is against a verified-identical substrate.

**Stop width (reject): UNMOVED.** p50 0.177W (H1-2026) / 0.184W (H2-2025),
p25/p75 0.10/0.30W. The 0.17W figure stands.

**MFE-in-R (reject): UNMOVED.** p50 0.95/0.87 | p90 7.2/6.4 | p95
12.4/10.6 by era. The recorded table stands.

**The entry-price fix moved the book by +0.001R — verified nil.** Entry
differences (next-open minus decision-close, signed toward trade
direction): mean +0.006 pts, sd 0.91 pts, median 0. The defect was real
(the gate proved the price was read off the decision bar) but its book
impact is symmetric noise on the reject arm. Named exclusions introduced:
no_next_open=67, gap_through_stop=6 (whole span).

**The −0.047R headline was a property of the COLLAPSE CONVENTION, not of
the book.** Same fixed table, four readings of the unselected reject book
under the adopted exit (out_ship):

| reading                              | H2-2025 | H1-2026 | pooled |
|--------------------------------------|---------|---------|--------|
| cross-cycle cluster-collapse (old)   | −0.042R | +0.098R | +0.024R |
| structural cluster-collapse (new)    | +0.163R | +0.236R | +0.197R |
| first-of-fight, executable           | **+0.139R** [+0.028,+0.253] | **+0.162R** [+0.051,+0.280] | **+0.149R** [+0.076,+0.224] |
| row-mean (every trigger)             | —       | —       | +0.120R |

Mechanism, recorded: the two cluster definitions carry OPPOSITE
size-outcome gradients. Cross-cycle: singleton chains −0.11R, 4-8-attempt
chains +0.50R (a level that keeps rejecting keeps paying). Structural:
singleton fights +0.29R, mult-touch chop fights −0.06R (price that sits at
the level without leaving doesn't travel). Equal-weighting fights under
either definition swings the mean by ±0.2R. The clustering criterion was
committed (671cd215) BEFORE the restatement was run — the ordering is on
the record.

**The load-bearing restatement is the first-of-fight row:** it is an
executable book (first trigger of each structural fight, real sequential
trades), not a weighting, and it clears zero in BOTH eras by day-level
bootstrap. Median fight −0.53R; the tail pays (top-1% of rows carries
0.057R of the 0.120R row-mean; p90 +2.6R). Under the adopted exit the
unselected reject book is ~+0.15R/fight, NOT −0.05R: selection's job is no
longer rescuing a negative book — it is concentration (fewer, better
fights vs the account-level frequency requirement). The cut study's Law-7
arithmetic must be recomputed against THIS baseline, and its book sim uses
the declared executable convention (SPEC-cut-study.md).

Caveats attached: out_ship's 3R leg fills on an intrabar touch (optimistic
by up to one tick, as recorded at adoption); cost constant 0.5 pt/trade;
break-arm restatement follows the same convention but was not the recorded
−0.047R claim.
