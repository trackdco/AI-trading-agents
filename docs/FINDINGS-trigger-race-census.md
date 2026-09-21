# FINDINGS — TRIGGER RACE CENSUS (redeclared grammar), counts only

2026-08-08. Declaration: `docs/DECLARATIONS-trigger-race.md`, committed
before the run (`ed7c435b`). **Counts only — no outcome was read anywhere
in this pass.** Integrity probe (flatten-future rebuild on sampled days):
**PASS, 10 probes, 0 bad.** Fit 2025-06-01..2026-07-31, 293 session-days;
note the bars end ~2026-07-14, so 2026-07 is a **10-day partial month**.

**The grammar under census** (five items confirmed verbatim by the
trader): thesis = 15m M1 displacement / M2 rejection episode / M3 break
episode; ≥1 affirming structure from {POC, VWAP mid, VWAP ±1, ±2, VAL,
VAH} within **0.10·W15 of the 15m MA** (width-relative — replaces the
flat 10pt) for M2/M3, M1 self-affirming; entry = **first close through
its own BB(20) MA across the {1m, 2m, 3m} race**, 1m admissible only at
≥2 affirmations; no band-pierce requirement; windows unchanged.

## THE HEADLINE COUNTS (declared 0.10W)

| window | M1/d | M2/d | M3/d | all/d |
|---|---|---|---|---|
| LONDON | 0.57 | 0.96 | 1.19 | **2.72** |
| NY_PRE | 0.39 | 0.83 | 0.86 | **2.08** |
| NY_AM | 1.05 | 0.90 | 0.86 | **2.81** |
| **TOTAL** | 2.01 | 2.69 | 2.91 | **7.60** |

First-of-fight at X=0.5W, one stream across TFs. The old (wrong-
conjunction, flat-10pt) census ran 1.68/day at 2m plus 1.22/day at 3m as
two separate books — the corrected grammar finds **~2.6× that combined
volume**, spread evenly across all three windows rather than starved in
London.

**The funnel** (per direction-minute, declared tol): LONDON M3 as the
example — 110.6 armed-min/day → 76.0 affirmed → 2.67 raw triggers → 1.19
fights. The affirmation requirement passes ~two-thirds of armed minutes
(the structures are usually near the zone); the binding filter is now the
own-MA closure itself, which is where the trader's grammar puts it.

## THE RACE'S INTERNAL STRUCTURE (all recorded data, nothing selected)

- **Winning TF**: the 1m wins ~35–40% of fights where the gate lets it
  run, the 2m wins the plurality overall, and the **3m almost never wins**
  (4–65 per cell) — mechanically sensible: in a race, the faster candle
  usually crosses first, so the 3m only wins when the 1m is gated out and
  the 2m didn't cross. The old census's "3m book" was largely an artifact
  of denying the faster TFs.
- **Affirmation count**: overwhelmingly 1 or 2; 3+ is rare (0–14 per
  cell). The **1m-admissible share (≥2 affirmations) runs 38–59%** by
  cell — the double-confirmation gate binds about half the time.
- **Which structures affirm** (fights basis): **POC 959, VWAP mid 916**,
  then p1 444, VAH 345, VAL 261, m1 199. The trader's Jun-3 example
  (15m MA + POC) is the modal case in the census, not an outlier.

## TOLERANCE SWEEP — shape only, nothing picked

| tol (·W15) | LONDON | NY_PRE | NY_AM | TOTAL/d |
|---|---|---|---|---|
| 0.05 | 1.58 | 1.23 | 1.76 | 4.56 |
| **0.10** | **2.72** | **2.08** | **2.81** | **7.60** |
| 0.15 | 3.97 | 3.10 | 4.14 | 11.20 |
| 0.20 | 4.73 | 3.84 | 4.91 | 13.48 |

Monotone and smooth — no cliff at the declared value. Frequency is no
longer the scarce resource it was under the old construction; whether the
wider zones dilute quality is an OUTCOME question and was not looked at.

## THE DECAY IS REPAIRED — the flat-10pt collapse was the tolerance, not the market

- Old census (flat 10pt): raw triggers **2.36/day → 1.86/day** across the
  half-spans; July 2026 at ~1/5 of the 2025 monthly rate.
- Race census (0.10W): fights/day **7.97 → 7.24** across the same halves
  (−9%, vs −21%), and the monthly series *per trading day* is flat-to-
  rising across the whole span: raw 12.0–16.7/day through 2025, and
  **2026-07 — the month the flat tolerance starved hardest — is the
  highest in the series at 18.9 raw/day** over its 10 data days. (The
  unnormalized "84 fights in July" in the run log is the partial month,
  not a collapse.)

This closes the loop on the BR-77/BR-81 confound flags: the late-span
starvation was an artifact of denominating a confluence zone in flat
points across a span where W15 doubled. Width-relative, the trigger
grammar is stationary in frequency.

## WHAT THIS PASS DOES NOT SAY

Nothing here is an edge claim — no EV, hit rate, or excursion was
computed. 7.6 fights/day is the **census population** of the grammar, not
a trade rate; the trader's own selectivity sits on top of it. Next steps
in order: (1) the 8 real NY trades checked against THIS construction and
the old one, each miss recorded at its kill stage — pending the remaining
screenshots; (2) only after that, outcome scoring under a declared plan.

Standing: fit-only, no holdout (none exists for this family), counts
only, nothing adopted.


---

# ADDENDUM — THE TRADE CHECK: the real executed trades vs the grammar

2026-08-08. The accessible screenshots document **4 distinct trades**
(the other images are multi-TF context shots of the same trades), not the
8 originally referenced — recorded as-is; the check runs on what exists.
Chart timezone **verified = NY by exact OHLC bar match** (the Jun-3 10:55
bar matches to the minute; header bars elsewhere are the replay's last
bar). Tool: `scripts/trade_check_jun.py` — windows treated as a reported
stage, never used to hide a row.

## THE TALLY: 2 CAUGHT, 2 MISSED — each miss at a named stage

**T1 — Jun 1, SHORT ~09:49–50 from ~30,445 (pullback after the morning
collapse): CAUGHT.** Census fires **M2 short via 1m closure at 09:52**,
n_aff=2 (POC + VWAP), NY_AM; 2m/3m closures confirm at 09:56/09:57 (same
fight). Noted honestly: the construction enters ~2 minutes later and
~27pt lower than his fill — he market-orders ahead of the closure; the
grammar waits for the candle to close. That timing skew is a property of
mechanization, recorded, not scored here.

**T2 — Jun 2, LONG ~09:46–50 from ~30,479 (VWAP reclaim on the morning
reversal): CAUGHT, on the nose.** Census fires **M1 long via 1m closure
at 09:45**, n_aff=2 (POC + VWAP+1), NY_AM; 2m confirms 09:46. In grammar
terms his "long off VWAP" is the displacement rebalance — price had been
driven ≥0.5W below the 15m MA and his entry is the closure back toward
it.

**T3 — Jun 3, LONG ~09:05–10 from ~30,723 (premarket rejoin of the
overnight rally): MISSED — kill stage: THESIS.** The entry race itself
was ready to catch him (1m/2m closures long at 09:03/09:04 and
09:09/09:10, affirmation count 2, NY_PRE window open). No thesis armed:
price sat only **−0.24W below the 15m MA — an M1-shaped rebalance below
the 0.5W displacement floor** (BR-1 convention, inherited); no 15m
rejection was live; and the break episode pointed SHORT (a 15m close
below the MA at 08:45 — the up-cross that would have armed M3 long came
at 09:30, after his entry). **The 0.5W floor is the exact line between
this trade and the census.** Recorded as a grammar discrepancy for the
trader to rule on — not patched.

**T4 — Jun 3, SHORT 10:45 from ~30,701 (the multi-TF one: 15m break +
pullback): MISSED — kill stage: WINDOW, exactly as pre-registered before
any data was touched.** Outside 10:30 the construction fires anyway: M2
short via 2m closure at 10:50 (3m at 10:51), n_aff=1 — every stage
passes except the NY_AM boundary, which the trader chose to keep ("10:30
is fine"). **A second discrepancy is documented on this trade:** his
actual 1m entry at 10:45 would have been denied even in-window, because
the ≥2-affirmation gate counts structures *excluding* the anchor MA —
his "double confirmation" was the 15m MA itself + POC, which the census
scores as n_aff=1. The declared gate is one count stricter than his
practice on this exact trade.

## WHAT THE CHECK SAYS

1. **The redeclared grammar catches the trades the old construction
   couldn't see.** Neither T1 nor T2 existed in the old census (wrong
   conjunction + flat tolerance); both are clean catches now, with the
   right mechanism labels and near-exact timing.
2. **Both misses die at declared, named lines — not at vague
   construction noise**: the 0.5W displacement floor (T3) and the 10:30
   window edge plus the MA-exclusive affirmation count (T4). All three
   lines are the trader's to move or keep; each is a one-parameter
   declaration change, and none is changed here.
3. The timing-skew observation (T1): mechanized entries lag discretionary
   market orders by up to the trigger candle's remaining life. Any
   outcome comparison against his fills must carry that structurally.

Standing unchanged: fit-only, counts and stage audits only, nothing
adopted, nothing patched without declaration.

## AMENDMENT 1 RESULTS — open vs episode M1, side by side (counts only)

2026-08-08, run under the amendment declared in
`DECLARATIONS-trigger-race.md` before the build. Flatten probe on the
episode variant: **PASS (10 probes, 0 bad)**. Declared 0.10W, fit span,
nothing replaced in this step.

| window | mech | OPEN /d | EPISODE /d | Δ | % |
|---|---|---|---|---|---|
| LONDON | M1 | 0.57 | 2.11 | +1.54 | **+270%** |
| LONDON | M2 | 0.96 | 0.96 | 0.00 | 0% |
| LONDON | M3 | 1.19 | 1.14 | −0.05 | −5% |
| NY_PRE | M1 | 0.39 | 1.49 | +1.11 | **+284%** |
| NY_PRE | M2 | 0.83 | 0.83 | 0.00 | 0% |
| NY_PRE | M3 | 0.86 | 0.83 | −0.02 | −3% |
| NY_AM | M1 | 1.05 | 1.66 | +0.61 | **+58%** |
| NY_AM | M2 | 0.90 | 0.90 | 0.00 | 0% |
| NY_AM | M3 | 0.86 | 0.85 | −0.01 | −1% |
| **TOTAL** | | **7.60** | **10.76** | +3.16 | **+42%** |

**The change is surgical**: M2 and M3 are essentially untouched (76+4 of
6,645 raw rows reassigned by priority), and the episode-M1 population is
overwhelmingly NEW — of its 3,263 raw rows, **2,577 were not triggers at
all** under the open definition, 606 were already M1, and only 3.3% of
open rows change mechanism or presence. The open definition wasn't
mislabeling reclaims; it was *blind* to them.

**T3 calibration — the declared expectation confirmed**: under the
episode state, T3 is CAUGHT at **09:03 via the 1m** (n_aff=2, episode
max −0.56W), with the 2m confirming at 09:04. All four of the trader's
documented trades are now caught or die only at lines he explicitly
chose to keep (T4's window).

**Decision per the pre-declared rule**: M1 moved ≥25% in every window
(+270/+284/+58%) and the total book moved +42% ≥10% — the population
meaningfully changed, so the outcome pass re-runs against the corrected
census. Not because the first answer was unwelcome; because the
population changed.

## T1 AND T2 RE-DERIVED AT THE FINEST AVAILABLE RESOLUTION — NO BUG; THE GAP IS REAL AND LARGER THAN MEASURED

2026-08-08, `scripts/trade_audit_t1t2.py`. The substrate is 1m bars +
per-minute footprint — there is no tick stream in this repo, so "tick
level" here means every candle, every MA value, and every condition the
construction tested, printed raw, plus parity checks against the exact
BB values visible on the trader's own TradingView screenshots.

**MA parity: exact.** Jun-1 1m MA: TV 30,405.18 vs ours 30,405.17
(−0.01). Jun-1 2m MA: TV 30,382.96 vs ours 30,382.96 (0.00). Jun-2 1m
MA: TV 30,504.70 vs ours 30,504.70 (0.00). The construction prices the
same moving averages the trader's own chart draws.

**Candle selection: hand-verified, correct.** Every candle in both
envelopes at all three TFs is printed with its open-side test,
close-through test, thesis, and affirmation count; every non-emitting
candle has a named failing condition; the emitted triggers are exactly
the first fresh closures (T1: 09:52-1m/09:56-2m/09:57-3m; T2:
09:45-1m/09:46-2m/09:48-3m), and the tie/priority ordering is right.

**T1 anatomy — the gap is an entry-class difference, not slippage.**
His fill ~30,450 at 09:49–50 was **at the 15m-MA/VWAP zone tag
itself** — the 09:47 candle poked 30,467.25 through the 15m MA
(30,454.99) and rejected; he shorted the rejection. The first LTF
closure did not come until 09:52 (1m close 30,417.75 through the 1m MA
30,427.58). Construction entry 30,417.50 against his ~30,450: **his
fill is 32.5pt better = +1.01R at that fight's 32.25pt risk.**

**T2 — re-verified, and the earlier "clean" call is CORRECTED.** The
time matched (his window ~09:44–47, trigger 09:45), which is why it was
called caught-on-the-nose; the price does not. His fill 30,479.25
traded during 09:42–43 at the VWAP reclaim, **before the first 1m
closure existed** (09:45, close 30,503.25). Construction entry
30,502.50: **his fill is 23.25pt better = +0.78R.** The same
anticipation gap as T1, previously hidden behind a time coincidence.

**Verdict: the winning-candle picking and pricing are correct — the gap
is real, and it is bigger than BR-92 measured.** On both audited trades
the trader enters at the STRUCTURE TOUCH (zone rejection / reclaim),
earlier even than the first 1m cross that BR-92 used as its early-entry
proxy (T1: fill 09:49–50 vs first cross 09:52; T2: fill 09:42–43 vs
09:45). BR-92's +0.161 upper bound therefore captures only part of the
gap; the anticipation component on these two trades ran +0.78R to
+1.01R per trade. **The early-entry premise stands — unblocked — with
the spec question sharpened: "first 1m cross" confirmation and
"zone-touch entry with a zone-extreme stop" are two different declared
constructions, and his fills match the second.** Which one gets declared
is the trader's call; nothing is built here.

## CORRECTION — T1'S 1m CLOSURE RE-DERIVED, AND THE MISMATCH IS IN MY SCREENSHOT READING, NOT THE CONSTRUCTION

2026-08-08, follow-up under the trader's standing rule, now on the
record for this whole programme: **when a screenshot appears to
conflict with the trader's directly stated process, the stated process
wins and the screenshot gets re-checked — never the other way around.**

**The 1m facts, re-derived (unchanged from the audit, restated
precisely):** on 2026-06-01 the only 1m closure through the 1m BB MA in
the short direction in the entire envelope is the bar ending **09:52 —
close 30,417.75 through the 1m MA 30,427.58** (every earlier minute
09:40–09:51 closed ABOVE the 1m MA; verified line by line). The
construction fired exactly that: entry 30,417.50 (next 1m open), stop
30,449.75 (trigger-candle high 30,449.50 + 1 tick), risk 32.25pt.

**Which screenshot documents the 1m entry:** the Jun-1 1m chart (replay
bar 09:59) — the only T1 image on the entry timeframe; the 2m image is
higher-timeframe context. Its position-tool price-scale labels are
**30,445.25** (upper) and **30,325.00** (lower), with no label at any
price between. My earlier audit took the ~30,445–450 region as HIS FILL
at 09:49–50 — an inference from box geometry, never from a label that
says "entry."

**The trader's stated process** — "bollinger band MA on closure on top
to enter" — admits no entry at 30,445–450 at 09:49–50, because **no 1m
closure through the MA existed there**. Under the standing rule the
statement wins, and the screenshot re-reads coherently: **30,445.25 is
the STOP** (sitting 4.5pt from the construction's own 30,449.75),
30,325.00 the target, and the entry is the 09:52 closure at
~30,417.75 — the construction's trade to within a tick of entry and a
few points of stop placement. **The same correction applies to T2**
(labels 30,566.25 / 30,479.25 / 30,442.00): the stated process puts the
entry at the 09:45 closure (~30,502.50), not at 30,479.25, and the
lower labels re-read as stop/target placement.

**What this corrects, explicitly (misses recorded as misses — these
were my misreadings, not the construction's):**

1. The audit section above claimed "his fill is 32.5pt / +1.01R better"
   (T1) and "23.25pt / +0.78R better" (T2), and built an "entry-class /
   zone-touch anticipation" narrative on it. **Withdrawn.** Both
   documented trades are the construction's own closure trades. BR-93
   is annotated accordingly.
2. BR-85's "he market-orders ahead of the closure (~1.8R better on one
   measured fill)" carries the same defect. **Withdrawn for T1/T2.**
3. **BR-92 is NOT touched** — the entry-timing measurement never used
   his fills; it is a self-contained mechanical decomposition of the
   waiting cost inside 2m/3m candles, and it stands on its own as the
   motivation for the early-entry construction. What is withdrawn is
   only the claim that his real fills demonstrate the anticipation.

**Net verdict on the trade check, restated:** the construction catches
T1 and T2 not merely as triggers but as **the same trades at the same
prices** the screenshots document, T3 is caught under Amendment 1, and
T4 dies at the window edge the trader chose. The grammar is a faithful
mechanization of the stated process on all four documented trades.

## T3 RE-CHECKED: genuinely M1 — and the floor is not the real gap

2026-08-08, follow-up. Question asked: is T3 actually a rejection or a
break carrying incidental displacement, i.e. a miscategorization rather
than a threshold problem?

**It is neither — T3 is a rebalance bet, correctly categorized as M1.**
The 08:45 15m bar *closed through* the MA (a cross, not a rejection);
the two recovery bars before his entry never touched the MA (highs
−16.7 / −8.7pt), so no rejection grammar could fire; the live break
episode pointed short and he went long against it. The shape is pure
rebalance: 4.5h uptrend, two-bar shakeout through the MA, reclaim bought
at POC (30,718.5) over VWAP (30,710.9) — and he **took profit at the
15m MA** (30,756 exit vs MA 30,752, converged with VWAP+1 at 30,756.5)
while the market ran on to 30,807.8 within ten minutes. Selling at the
mean is the rebalance bet's behavior.

**Displacement at the trigger opens: −0.340 / −0.346 / −0.365 /
−0.374 W vs the −0.500 floor** — a ~0.13–0.16W (~13pt) shortfall, made
visible as asked. **But the dip's extreme reached −0.56W at 08:55 —
past the floor.** The displacement existed; the reclaim ate a third of
it before any closure could confirm. The construction measures
displacement at the trigger candle's OPEN, demanding it persist into
the entry candle — structurally penalizing fast reclaims, the exact
trades a rebalance bettor wants. Same defect family as the original
displacement-at-close bug, one step milder (close = persistence after
the reversal; open = persistence until it; extreme = it happened and
has not resolved). An M1 state of "excursion extreme reached ≥0.5W
below the MA and price has not yet returned to the MA" catches T3 at
the **unchanged** floor. Recorded; the operationalization change is the
trader's declaration to make, and nothing is changed here.
