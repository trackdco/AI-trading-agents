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

RESULT (recorded after the run): see PHASE0-results appendix below.

## Item 4 — restated numbers (after the item-1 fix and item-3 re-clustering)

See PHASE0-results appendix below: the 0.17W median stop, the MFE-in-R
table, and the −0.047R unselected reject book are restated on the fixed
table; BASE-RATES.md is updated in the same commit iff any moved beyond
noise.
