---
date: 2026-08-05
status: greenlit — L0 passed, both branches to L1
tags: [ny-am, failed-auction, amt, dual-sourced]
sources: ["docs/PREREG-failed-auction.md", "research/findings/orochi-diagnosis.md", "research/findings/fabervaale-diagnosis.md"]
---

# nya-failed-auction — balance-break fail/succeed event tree (NYA-FA-01)

## Thesis (for Angus)

Price breaks out of a multi-day balance. Half the time the break holds and
trends; half the time it fails, traps the chasers, and their forced exit
fuels a move back through the range. Both intake gurus teach both trades and
neither defines what separates them — that discriminator is our program.

## Trial ledger — NYA-FA-01

### Trial 1 — L0 census (2026-08-05) — PASSED, folklore corrected, both branches advance
scripts/nya_composites.py + scripts/nya_fa_census.py (committed; outputs
force-added). 457 break events on 549 composite-live sessions, 2023-2026.
FINDINGS:
1. FAIL RATE era-consistent: 48-54% fail within 30 min, 59-60% within 120 —
   the picture really does resolve both ways near-evenly. No era flip.
2. THE "80% RULE" IS DEAD AS TAUGHT: after a fail, price traverses to the
   composite's FAR edge only 12-21% of the time (era-split 12/21/20). Even
   reaching the composite POC is only 46-57%. The published falsification
   (27-67%) was generous — on honest multi-day composites the far-edge
   target is folklore. CONSEQUENCE: the fail-branch L1 expressions target
   POC (not the far edge) and get judged on geometry, per prereg.
3. "TIME AND SPACE" IS VIBES: minutes-spent-outside shows ZERO
   discrimination of traverse odds (16/19/12% across terciles). The
   load-bearing discretionary concept of both gurus fails its first
   mechanical test.
4. DEPTH IS SIGNAL: max extension beyond the edge before re-entry
   discriminates cleanly — deep excursions that then fail traverse to the
   far edge 23% vs 8% for shallow (POC-traverse 55% vs 43%). Directionally
   confirms the trapped-mass mechanism: the further they chased, the harder
   they unwind. This is the declared discriminator search's first live wire.
5. ACCEPT SIDE IS BIG: accept days run a median 1.26 composite-widths of
   continuation; 91% reach 0.5 widths. CAVEAT logged: partially definitional
   (accept = no re-entry, so extension is survivorship-tinted); the honest
   L1 test is entry on the broken-edge retest AFTER the window expires.
STATUS: census PASSED for the family premise (both resolutions frequent,
era-stable, mechanism-consistent conditioning signal exists). ADVANCING to
L1 mechanics: fail-branch (enter on re-entry close, target POC, stop beyond
excursion extreme) and accept-branch (edge-retest continuation) — each with
declared cost stacks. Flow-at-entry discriminator search (delta at break,
absorption at edge on re-entry, CVD divergence outside, trapped-volume
estimate) follows L1, on the flow span. Family arm count: 1 (census).

### Trial 2 — L1 mechanics + depth cut (2026-08-05) — raw ugly as expected, depth separates
scripts/nya_fa_l1.py (window-partition bug found and fixed mid-trial —
first run mis-assigned late re-entries to the fail branch; corrected run is
the record). Raw fail branch (n=248, full span): PF 0.80-0.88, negative all
eras — NO KILL LEGAL (§3.2; raw substrate expected ugly). Accept branch raw
(n=62): flat (PF 1.02-1.04). Depth tercile on F2: WR 12% shallow → 59% deep;
deep points-positive but fixed-risk dollars negative — the euro-handoff
geometry disease (natural stop at the excursion extreme too wide). Declared
cures queued: tighter-stop arms + flow gates. Arms this trial: F1, F2, A1
(+3; family count 4).

### Trial 3 — flow-at-entry discriminator search (2026-08-05, flow span) — LIVE CELLS FOUND
scripts/nya_fa_flow.py (events in output/nya_fa_flow_events.parquet). 71
fail events, 2025-06..2026-07. Gates as declared: G1 edge-absorption fires
1% — dead as defined (looser variants would be NEW declared arms, not
silent retuning); G2 excursion-delta-opposes-break fires 66% and improves
every stop; G3 CVD-divergence fires 89%, mild help. Depth again the
strongest single conditioner. Stop geometry: S2 (0.5x excursion) fixes the
dollars. LEADING CELLS: deep+G2/S2 — n=28, WR 46%, +647 pts, $+984,
PF 2.06, survives strict friction (PF 1.99); deep+G3/S2 — n=34, +755 pts,
$+1,893, PF 2.14. Halves −109/+364..373/+392..492: the negative leg is
June-2025 only (partial month, tiny n) — flagged, not hidden. CAVEATS: n=28-34
(§2.2); flow gates exist only on the 13.5-month flow span; depth replicates
on the full candle span (census trial 1) which is the family's structural
anchor. Arms this trial: G1/G2/G3 x S1/S2/S3 + deep-combos = 9 (family
count 13; all count in DSR). NEXT: exit-arm tournament on the leading
cells, accept-branch conditioning, then grading.

### Trial 4 — exit tournament under §6.0 (2026-08-05) — DEFAULT SPEC STANDS
scripts/nya_fa_arms.py (arm matrix in output/nya_fa_arm_matrix.parquet).
First tournament run under the declared promotion rule. Four arms on the
G2-gated cohort (n=47): PF 1.46-1.63 on points, all within noise of each
other — PBO on the arm choice = 0.50 (P(OOS loss) 0.96): the arms do NOT
separate; no challenger displaces E1. DEFAULT SPEC STANDS by §6.0 without
needing rank. SECOND FINDING (important): the G2-only cohort is
dollar-NEGATIVE at fixed-risk sizing (~$-2.5k all arms) while trial 3's
deep+G2 cell was dollar-positive — the DEPTH component carries the
economics, not the exits; shallow events' tiny stops amplify losses under
1/risk sizing. Confirms the default gate must include depth. Arms this
trial: 3 new (E2/E3/E4; E1 = trial-3 cell). Family count 16, machine ledger
updated. STATUS: fail-branch spec frozen as declared default (deep + G2 +
S2 + min(POC, 0.5w) + TS 15:55); remaining before grading: accept-branch
conditioning, canon correlation battery. Sealed-holdout note: the six
sealed months HAVE footprint data — a declared look could add ~6mo of gated
events; banked, Angus's call at grading time.

### Trial 6 — GRADING (2026-08-05) — SHELVED-UNPROVEN; search flagged by PBO
scripts/nya_grade.py (pack in output/nya_fa_grading.md; book emitted to
output/emission_nya_fa_fit.parquet). Portfolio gates ALL PASS: correlation
vs canon ~0 (union −0.05), 1/3 shared families (order-flow only), canon+spec
P(bust) 0.1% — adding this sleeve costs the account nothing. But the
evidence gates fail hard: DSR 0.000 (daily SR +0.044 vs ledger-read SR0
+1.01; §6.0 denominator from 18 recorded trials incl. tiny-n cells that
honestly widen the null), PSR(0) 0.786, minimum certifying track 1,155 days
vs 270 held, and **PBO 0.85 on the 9-cell gate x stop search** — the
selection procedure that surfaced deep+G2+S2 lands below the OOS median in
85% of splits. The mechanism-prior story is coherent, but the machine says
a 9-cell search on 71 events cannot distinguish it from noise.
VERDICT: **SHELVED-UNPROVEN.** What stays solid: the census-level facts on
full-span n=457 (fail/accept ~50/50 era-stable; 80%-rule folklore killed;
depth discriminates traverse odds 8%→23%; time-outside is noise). What is
unproven: the tradeable expression (n=28, 13.5mo). Reopening paths: live
flow accrual, the banked holdout look (+~6mo flow-gated events, Angus's
written call), Brake's independent NY emissions for book-level grading.
NOT SHIPPED. Family arm count final: 20.

### Trial 7 — GRADING VERDICT SUSPENDED, search reopened (ANGUS 2026-08-05, canon-parity ruling)
The trial-6 grades were run after a THIN search relative to the canon
standard: the prereg's declared variables open type, day type, IB size,
poor/strong structure at the extreme, session clock, trapped-volume
estimate, and DEPTH-WALL STATE AT THE BROKEN EDGE (the canon's pivotal
variable class; extractor not yet built) were never searched. Grading a
thin search is premature in the opposite direction from a premature kill —
the DSR/PBO numbers stand in the record as measurements of the thin-search
spec, but the SHELVED verdict is suspended rather than final. STATUS:
search REOPENED per canon parity. Owed: (1) depth-wall-at-entry extractor
built and tested at the edge on re-entry; (2) the remaining declared candle
variables; (3) 2023-24 CANDLE validation of the candle-side spec per
Angus's step-4 loop (23-24 candles were never sealed — only the six flow
months are); (4) graders RE-RUN on whatever the deep search freezes.
Trial-6 numbers stay ledgered; nothing is erased.

### Trial 8 — DEEP PASS: walls + candle variables (2026-08-05, canon-parity)
scripts/nya_fa_deep.py. Three findings:
1. LEGAL CUT FOUND (bad every era, no lookahead): open_type=test_drive —
   PF 0.40, negative in all three eras (open type is known by 10:00; every
   entry is post-10:00). Declared arm for grading: spec + test_drive cut.
2. DIAGNOSTIC ONLY (LOOKAHEAD — cannot gate): day_type=trend (PF 0.13, bad
   every era) and day_type=neutral (PF 0.36, bad every era). day_type is
   classified from the FULL session including the close — knowing it at
   entry time is lookahead. Recorded as the autopsy explanation (fading
   into a trend day is the death mode, mechanism-consistent) with a
   TRADEABLE proxy declared as a future arm: one-timeframing state AT entry
   time. Not applied to the spec.
3. WALL-AT-ENTRY: canon-style wall-support gate does NOT transfer —
   spec+wall>=3 is n=2 (0% WR); spec+wall<3 runs n=19, WR 58%, PF 2.91
   (+$1,451). Direction consistent with the sweep doctrine (thin book after
   the trap = fast traverse) but n=2/19 is far too small to ADOPT the
   inverse as a gate — doing so would be the §6.0 failure in miniature.
   VERDICT: no wall requirement enters the spec; observation recorded for
   the holdout to adjudicate. Coverage honesty: 55% of events have wall
   reads (depth ends 10:29); the uncovered cohort still runs PF 1.84.
Arms this trial: 4 (test_drive cut, wall>=3, wall<3, day-type diagnostic).
Family count 24. NEXT: 23/24 candle look (the ONE §5.9.4 iteration),
graders re-run with the test_drive-cut arm included.

### Trial 9 — THE 23/24 CANDLE LOOK (2026-08-05, §5.9.4) — FAILED; retest BANKED
scripts/nya_fa_2324_look.py (output/nya_fa_2324_look.parquet). Look #1 of
the family's allowance, spent on the conditioned candle skeleton (deep
cohort, frozen flow-span threshold 0.117, with/without test_drive cut):
147 fail events 2023-24 — deep PF 0.68 (n=73, −456 pts), deep+cut PF 0.76
(n=63), negative BOTH years (2023 worse than 2024). Depth still
discriminates directionally (WR 29% deep vs 12% shallow) but does not pay
out-of-fit. DIAGNOSIS (in-fit, flow span, legal): the missing half of the
trapped-mass mechanism is PARTICIPATION — a candle-legal excursion-volume
proxy separates the spec cohort in-fit (evr>=1.3: n=7, WR 71%, PF 5.66 vs
low-participation PF 1.22) but n=7 is too thin to bet the single retest on,
the 1.3 threshold is ad hoc, and the proxy disagrees with G2 on 62% of
events (different variable, not a stand-in). Composite age: noise-shaped
(2.61/1.02/7.26 on 16/9/3). Very-deep: worse (1.45).
RULING APPLIED: the ONE rebalance-retest is BANKED, not spent — no
candidate rebalance has credible in-fit support at meaningful n, and
spending the family's last out-of-fit bullet on a 7-trade cell is the
exact gamble §6.0 exists to prevent. STATUS: family CANNOT SHIP until a
successful retest (§5.9.4); stays shelved with the participation thesis
maturing as flow-span events accrue (live + Brake's data). Honest regime
note: 25-26 success + 23-24 failure may be genuine regime dependence — the
mean-reversion fade thrives where the canon's with-trend logic starves,
and vice versa; a book story, but not one that overrides the ruling.
Arms this trial: 4 (look cells + evr proxy + age + very-deep). Family 28.
scripts/nya_fa_accept.py (events in output/nya_fa_accept_events.parquet).
Only 15 accept-then-retest events exist on the whole flow span — accepted
breaks rarely return to the broken edge (which is itself consistent with
trial 1's finding that accept days run: median 1.26 widths of continuation).
Gated cells are n=1-4: nothing is gradeable at any honesty standard. VERDICT:
PARKED (open-sweep-fade precedent — insufficient events is not a kill).
Reopening: more span, or an entry expression that does not require the edge
retest (would be a fresh declared arm). Arms this trial: 4 (A1 gates; family
count 20). FAMILY TO GRADING on the fail-branch frozen spec alone.
