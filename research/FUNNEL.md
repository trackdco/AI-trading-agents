# THE FUNNEL — live per-strategy data cards (Angus's window into every stage)

## PROGRAM MODE: ONE STRATEGY AT A TIME [ANGUS 2026-08-05]
"Lets go one strategy at a time... ill go through the same process i went
through for the canon, one strategy at a time. except it will be way
quicker now, and findings will be documented."
- Single-family work-in-progress. Angus operates each family through the
  full canon process start-to-finish (stage data cards -> his calls ->
  next stage); everything else PARKS at its current stage, state
  documented on its card. No new intakes/censuses until the active
  family resolves (ship, shelve, or kill).
- PARKED STAGES: nya-ivb-fadeB + NYA-IB50-01 = folded into the ACTIVE
  IB COMPLEX (NYA-IBC-01, card below); nya-daily-sweep =
  sleeve-certified, awaiting Brake redundancy + book decision;
  nya-failed-auction hours-clock = SHELVED BY ANGUS (frequency too low
  to be worth the slot, ~0.9/wk; history stands in the candidate file);
  nyo-rotation = park recommended; nypre pair = shelved-eligible.
- ACTIVE FAMILY (this chat): NYA-IBC-01 the IB Complex.
- SECOND CHAT (Angus): level-interaction family seeded with the
  MrZincx London-50/PD level set — the high-frequency substrate
  (~10-15 raw triggers/day); fit-span universe, uncapped from birth.

Standing rule (ANGUS 2026-08-05): every strategy past step 1 gets a data card
here, updated at EVERY stage boundary — raw trigger counts and frequency, raw
P&L, trade counts, win rate, the lift each variable stage produces, and the
canon-shape comparison. Numbers only; verdicts live in the candidate files.
The point: the framework must visibly behave like the canon build did — ugly
raw, honest lift from variables, out-of-fit survival — and Angus inspects
that arc himself, per stage, not post-hoc.

Format per card: STAGE / RAW TRIGGERS (count, freq) / RAW P&L (n, WR, pts, $,
PF) / VARIABLE LIFT (each stage's numbers) / SPLITS / NEXT RUNG / CANON SHAPE.

---

## NYA-LVL-01 — level-interaction family (London 50 seed) — **DEAD. W was a lookahead.**
- **VERDICT 2026-08-05: KILLED.** Placebo null 100 perms: observed +0.7082 R/trade vs
  null median **+0.7509**, family-wise **p=0.7500** against a declared 0.01. The null
  MEDIAN EXCEEDS the observed value.
- **THE KILL SHOT — W read the future.** W was computed from the book at the FILL MINUTE,
  which includes what price did after entry. Recomputed one minute earlier: lift falls
  from **+19.5pp to +4.2pp**. ~80% of the edge was information from the wrong side of the
  decision point. This also explains the null: W peeks regardless of which line it is
  attached to, which is why random lines scored BETTER than the real six.
- **THREE BUGS, ONE SHAPE, ALL MINE:** trail read a bar's high before its low; the sim
  started 12 min after the fill (PF 3.09); W read the fill minute (56.9% at 2R). Every one
  made the numbers better. Every one was post-decision information. I caught two by
  looking and the third only because Angus pushed back on an oversell.
- **STANDING CHECK ADOPTED:** any feature beating the bar-only baseline by >~5pp is
  recomputed one bar earlier BEFORE being reported — not after someone is sceptical.
- SURVIVES: the raw substrate (4,548 events, 16.2/session, six lookahead-clean levels) and
  an honest bar-only ceiling of ~60% at 1.0R / +0.20R. Marginal, not a strategy.
- **No 2023/24 look spent.** Full verdict: `research/findings/NYA-LVL-01-VERDICT-killed.md`.
- **VOID NOTICE 2026-08-05:** the simulation filled at the level mid-bar but did not start
  watching until the 15-minute bar CLOSED — a median 12 minutes later, during which price
  moves a median 21 pts against the trade. **A 10pt stop was already hit before the sim
  began on 72.9% of trades.** Every P&L number below and in stages 2/3a/3b is withdrawn.
  Event counts stand. Full notice: `research/findings/NYA-LVL-01-VOID-entry-bar-skipped.md`.
  Fix: detect the touch on 1-minute bars and start the path at the touch minute.
  Caught because Angus said the numbers looked 'almost suspiciously good'.
- STAGE: stage 1 complete — prereg + raw uncapped trigger set. **STOPPED for Angus's
  read before any optimisation**, per his order. Nothing filtered, nothing selected.
- RAW TRIGGERS: **4,808 touches / 286 sessions, 4,759 filled = 16.6 per session**
  (2025: 17.4, 2026: 15.8) vs the ~10-15/day design intent. Kill line was <2/session —
  cleared by 8x. Fill rate 99% under the §2.5 limit rule.
- BY LEVEL: PM_50 21% / PM_HIGH 20% / PM_LOW 18% / PD_HIGH 15% / PD_50 15% / PD_LOW 11%.
- RAW P&L (base cost, Version B raw touch, ALL SIX ARMS, nothing selected):
  S_LEVEL/T_LADDER n=4,310 WR 39% PF 0.79 | S_LEVEL/T_SCALP n=4,759 WR 61% PF 0.43 |
  S_LEVEL/T_TIME n=4,759 WR 39% PF 0.91 | S_FAR/T_LADDER n=2,539 WR 59% PF 0.96 |
  S_FAR/T_SCALP n=2,988 WR 79% PF 0.50 | S_FAR/T_TIME n=2,988 WR 50% PF 0.94.
  **Every arm negative at both cost levels.** Ugly raw is the expected shape (§5.9.1).
- **THE HEADLINE — REALISED STOP DISTANCE.** He teaches the stop as ~16 points. Measured
  as taught (a 15-minute CLOSE beyond the level), it costs a **median 48.4 pts, p90 87.9**.
  S_FAR is a **median 121 pts, p90 334**. His win rate is roughly real (61-79%); the stop
  is ~3x what he says, which is why a 61% win rate still runs PF 0.43.
- HALF-YEARS: 2025H1 PF 0.70 / 2025H2 0.47 / 2026H1 0.38 / 2026H2 0.30 — negative every
  half, and drifting worse. No calendar pooling hiding anything.
- VERSION A vs B (both taught, neither picked): break-then-retest n=1,133 WR 63% PF 0.87
  vs raw touch n=4,759 WR 61% PF 0.43. **Reported, not acted on** — selecting here would
  be a bin decision off the raw set (§5.9.1).
- RECORDED FROM BIRTH (§5.12-5): level type, tap number (2 timeframes), clock, level age,
  gap context, distance from open, MFE/MAE, t+5/15/30. His own filters (opening candle,
  three-tap, 80/20 bias, 11:00 stop) are declared ARMS, none applied.
- TWO BUGS CAUGHT AND FIXED BEFORE REPORTING: the far-extreme stop sat on the wrong side
  of a fade (simulator read it as an instant target — produced a fake PF 9.18/90% WR);
  and break-tracking skipped bars that touched the level, so Version A armed only twice
  instead of 1,133 times.
- NEXT: **Angus's call.** Stage 2 options per §5.11-9c are flow/depth/conviction; the
  depth archive covers 08:00-10:29 ET, overlapping level formation and his prime window.
- CANON SHAPE: canon-like so far — very high raw frequency, raw economics negative, all
  the discriminating variables recorded and untouched.

## nya-ivb-fadeB — IVB range fade (Fabervaale, as taught) — ALIVE, mid-funnel
- STAGE: geometry validated on flow span; era discipline + exit arms owed.
- RAW TRIGGERS: 356 touches / 911 sessions full span (~2/wk); 105 on flow span.
- RAW P&L AT TAUGHT GEOMETRY (flow span): n=105, WR 43%, +1,480 pts, +$4,104
  @$160-risk, PF 1.63.
- SPLITS: 25H1(June) −161 / 25H2 +681 / 26H1 +908 / 26H2 +52.
- GATES TRIED: absorption-as-defined fires 4% (n=4 — looser variant is a
  declared future arm); wall>=3 n=10 flat. Geometry, not gating, carries it
  so far.
- ERA CHECK (full span, candles): 2025 PF 1.56 (n=101, +$2,455) / 2026 PF
  1.57 (n=57, +$2,503) / 23-24 PF 1.20 (n=198, +$5,907) — POSITIVE EVERY
  ERA, no flip; 356 trades, WR 41%.
- TOURNAMENT: 6 arms all positive every era; PBO 0.10 (cleanest of the
  program); default stands, 15-min-IB challenger (PF 1.64, $+21,313) banked
  for holdout adjudication.
- GRADING: PSR(0) 0.994 vs 0.75 sleeve floor — PASS; min track 390d vs 911
  held (certifiable vs zero on its own track, program first); canon
  correlation +0.02 union / +0.17 both-active (88 days, trusted, passes).
- FLAGS: standalone MC P(bust) 20% (streaky WR-41% profile — book component,
  not solo ship); ledger-DSR denominator inflation flagged to Brake.
- NEXT: book-level grading (canon + this + pre-market pair).
- CANON SHAPE: ahead of canon's arc (canon raw was negative pre-wall-gate);
  era rung passed on the first attempt, no rebalance needed.
- IN-TRADE SIGNATURES (§5.12-5, trial 11): canon grammar TRANSFERS — press
  state at t+3 wins 67% vs 41% base (+26pp, positive lift every year); dying
  state (MAE<=-0.5R by t+3) wins 19% (-22pp, consistent every year);
  giveback ambiguous, as on the canon. This is the agent rung's playbook.
  HARNESS: adapting scripts/capture_desk_run.py (the desk-run code in this
  repo) to the fade myself — no Pat dependency for the backtest rung; Pat
  owns live-box integration only.
- FIRST-FORMED SPLIT (trial 13, intake round 2, prereg'd): REFUTED — the
  MrZincx/Edgeful 73% stat does NOT transfer as a gate. Fade-first-formed
  n=83 PF 1.02 vs fade-second-formed n=273 PF 1.52; permnull p=0.579.
  Default untouched; structural note: 273/356 tradeable touches are of the
  second-formed extreme, and that side carries the family's edge.
- HISTORY NOTE: killed twice by strawman censuses (missing trigger; harsher
  race than the taught trade), vacated on canon-parity, alive on retest —
  the correction that proved the framework audit mattered.

## nya-failed-auction — balance-break fail branch (dual-sourced) — ON HOLD: 23/24 look failed, retest banked
- TRIAL 10 (2026-08-05, hours-clock re-census per RESPEC Spec 6): the
  TAUGHT clock (30-min bars, >=4h outside) is a different, better trade —
  n=193, WR 47%, PF 1.24, $+1,893, years 0.97/1.06/1.57/1.24, frequency
  0.93/wk matches teaching. Fast clock (old picture): PF 1.14, 23/24 neg.
  All declared gates fail permnull (p~0.35) — population positive, gates
  unproven. Old "time is noise" verdict vacated (wrong clock). Earns next
  stage on the hours-clock expression; §5.9.4 banked-retest firewall holds.
- TRIAL 11 (next stage): strict costs PASS (1.23); flow-at-re-entry
  honest null (delta agreement near-universal, absorption no lift);
  autopsy — true bracket trade (99 stop/89 target), losers go green
  first, winners pay in ~17h, canon segments DON'T transfer at this
  clock. No internal gate proven; candidate for grading AS-IS at the
  next slate review, 2023-negative on the label.
- STAGE: deep pass complete; §5.9.4 look #1 SPENT and FAILED (deep skeleton
  PF 0.68 / with cut 0.76 on 147 events, negative both years); the single
  rebalance-retest is BANKED — no rebalance candidate has credible in-fit
  support yet (participation proxy: n=7, PF 5.66 — promising, too thin).
  Cannot ship until a successful retest. Regime note: thrives 25-26, starves
  23-24 — inverse of the canon's regime profile.
- RAW TRIGGERS: 457 breaks / 911 sessions (~2.5/wk); 248 in-window fails; 71
  fail events on flow span.
- RAW P&L (L1, full span): n=248, WR 35%, −1,025 pts, PF 0.83 — ugly as the
  law expects.
- VARIABLE LIFT: extension-depth tercile WR 12%→59% (how far price
  stretched beyond the edge — candle geometry, NOT order-book depth;
  renamed 2026-08-05 per §5.12.1-15);
  flow gate (tape-didn't-pay) + depth + fixed geometry: n=28, WR 46%, +647
  pts, +$984, PF 2.06 (strict-cost 1.99).
- SPLITS (conditioned): 25H1(June) −109 / 25H2 +364 / 26H1 +392.
- EXIT TOURNAMENT: run under §6.0 — PBO 0.50, no challenger displaced the
  declared default.
- NEXT: wall-at-entry (extractor live, 214 morning days), remaining candle
  variables, ONE 23/24 candle look per §5.9.4, graders re-run.
- CANON SHAPE: textbook — raw 0.83 → conditioned 2.06 is the canon arc.

## nya-ivb-brkA — IVB breakout — DEAD (earned, control case)
- RAW: 265 breaks flow span; PF 0.83 raw.
- FULL SEARCH: dz-confirmed 0.83, no-wall 0.68, dz+no-wall 0.54 — every gate
  equal or worse, every half negative. Killed as-taught after complete
  search (§5.9.1). Full-span decay: long-side race 57.8% (23-24) → 45.5%
  (25) → 43.9% (26).
- ROLE IN THE AUDIT: the negative control — the funnel lifts real edges
  (cards above) and fails to lift dead ones. Both behaviors are required.

## london-asian-trend-continuation (LDN-ATC-01) — pre-London pullback — ALIVE, census passed
- STAGE: L0 census done (`docs/PREREG-london-atc-census.md`). L1 owed.
- RAW TRIGGERS: 108 of 396 sessions complete the taught chain — **27% (2025) / 28% (2026)**
  vs a declared 15% census floor. Half-year 29/25/26/(55% on 11 sessions, noise).
- RAW P&L: **not computed.** Census counts events; §5.9.1 forbids a P&L kill here.
- FUNNEL (§5.12.1, no silent drops): no-bias 22% / bias-no-pullback 2% /
  **pullback-no-LTA 40%** / LTA-no-trigger 8% / fallback-only 1% / triggered 27%.
  The LTA requirement is the binding constraint, not the trend and not the trigger.
- TRIGGER GRID IS 30-MINUTE, NOT 15: '15m and 30m closing together' can only occur on
  30m boundaries. Observed clock is exactly 07:30/08:00/08:30/09:00 and nothing between.
  Opportunity set is half what a naive reading implies. 27% of triggers fire BEFORE the
  08:00 open — mechanically a different trade from both dead London candidates.
- SEMANTICS SELF-CHECK (§5.12.15): the '>=2 consecutive closes' LTA rule is MY
  mechanisation, and it is loose — the pullback window holds a median 4 bars, and 47% of
  sessions reaching it clear the bar. The column is not as selective as the name suggests.
  Stricter LTA is a declared L1 arm.
- EVENT CEILING (§5.11.2, declared before economics): all-triggers = 1.55x/1.51x.
- NEXT: L1 at as-taught geometry with the time-segment/MFE-MAE schema built in from the
  start, plus the declared randomised-bias control so 'continuation' must beat 'any
  direction', not merely beat zero.
- CANON SHAPE: too early — no P&L yet. Census arc normal (premise clears, ~2x the floor).

## london-nq-open-break (LDN-OBK-01) — continuation branch — **DEAD** (earned, search complete)
- STAGE: **complete** — census -> L1 -> conditioning -> L3 flow -> autopsy -> killed.
- RAW TRIGGERS: 425 breaks / 396 London sessions (~1.1/day); 92% of 2025 days and
  93% of 2026 days carry at least one. Declared census floor was 30%.
- RAW P&L: **not computed.** Census counts events; §5.9.1 forbids a P&L kill here
  and the prereg declared no P&L at this stage. First P&L is L1.
- THE EVENT: continued breaks extend a median **63.9 pts (2025) / 96.5 pts (2026)**
  beyond the level vs 8.6 / 11.5 for failed ones. ~7-8x separation — the tree is
  bimodal, which is what makes a discriminator worth building.
- SPLITS: break freq 92% (2025) / 93% (2026). Continuation share 15% / 16%.
- BREAK QUALITY: 27% (2025) / 9% (2026) of breaks extend < 5 pts — bare touches
  admitted because the prereg froze the as-taught definition with no minimum
  displacement. Minimum-displacement is the obvious first L1 declared variable.
- **RAW P&L (L1, `docs/PREREG-london-open-break-L1.md`) — UGLY, as the law expects.**
  A/S1 (declared default): 2025 n=256 WR 32% **−479 pts** PF 0.79 R/trade −0.198;
  2026 n=138 WR 38% **+88 pts** PF 1.06 R/trade +0.013. Strict cost: both negative.
- **THE TIGHT-STOP CLAIM FAILED, 0 of 4 era×cost cells.** Pre-committed reading was
  S1 beats S2 on R/trade in both eras at both costs. It never does. The one-line
  reason: at 2R the trigger-candle stop is hit **65%** and the target **30%**, and a
  2R trade needs 33.3% to break even before costs. Break-even geometry, cost stack
  decides. Brandan's advertised 89.5% WR lands at 32–38%.
- CONTROL CAVEAT: S2 exits on the clock 82% of the time (a 2R target on a range-width
  stop is 100–170 pts away; NQ does not go that far in 2h). S2 is not a working
  alternative — near-zero beating negative. **Neither stop makes this pay.**
- VARIABLE LIFT SO FAR: **negative.** Minimum displacement ≥0.10× range makes it worse
  in every era at every cost (2025 −0.124R, 2026 −0.129R vs −0.198/+0.013 unfiltered).
- CONDITIONING: 1 of 3 mechanism predictions confirmed (V1 macro hour, 4/4 cells;
  V2 and V3 flip sign between eras).
- **L3 FLOW: 0 of 6 declared features confirmed.** Autopsy: 16 cut-sets, 5 legal,
  **none** positive at strict cost; de-risk also negative on all.
- ~~VERDICT: KILLED on expectancy~~ — **VACATED**, see below.
- **VERDICT WITHDRAWN same day.** §5.11/§5.12 landed after the kill. The L3 pass was
  four tape features AT ENTRY plus two thin book features — §5.12.10 records that on the
  shipped canon depth carried the entire edge (+0.5 to +1.3R) and flow at entry was a
  rounding error. Weakest class, weakest moment, null treated as decisive. `W`/`D`/`WALLSZ`
  never built. Plus: pooled flow nulls cannot close a gate (§5.11.4), no event-universe
  sensitivity (§5.11.2), no stop-cap arm class (§5.11.3), no MFE/MAE pack so in-trade flow
  untested (§5.12.5), no permutation null on the carried combination (§5.12.4).
  Full reasoning: `research/findings/LDN-kill-vacated-under-511-512.md`.
- **DEPTH PASS RUN (gap 1 closed).** 8 canon checks, 32 cells, 1,168 trades with book.
  9 cells survive every era; ONE pays at strict cost both eras — `W` on A/S1, +0.204R (n=37) / +0.478R (n=38), lift +0.734/+0.756, inside the canon's depth band.
- **W THEN FAILED ITS SELECTION-CORRECTED NULL.** 10k shuffles re-running the whole
  32-cell selection: a cell that survives every era AND pays appears in **42.1%** of
  shuffles vs the declared family-wise bar of 5%. Lift magnitude passes (p=0.016) but that
  is a different claim from the one reported, and the declared test governs.
- **FINAL VERDICT: KILLED, search genuinely complete.** Both highest-prior classes tested
  at canon definitions: flow at entry 0/6, depth 9/32-survive-1-pays-0-survives-the-null.
  Premise stays true (+12/+14pp placebo margin); no way to get paid for it survives.
  No holdout look ever spent.

- SURVIVES: the 09:00 London / 04:00 ET macro hour, the only confirmed variable and the
  only London clock finding that came from our own measurement rather than a trader's
  claim. No live candidate uses it.
- CANON SHAPE: raw is ugly on schedule (canon raw was negative pre-wall-gate too). The
  difference from canon so far: **canon's first variable lifted, this one's didn't.**
  One variable is not a search, but it is not a good start either.

## london-po3-ifvg (LDN-PO3-01) — failure branch — **DEAD** (earned, search complete)
- STAGE: **complete** — census -> L1 -> conditioning -> interaction -> L3 flow -> autopsy -> killed.
- RAW TRIGGERS: same 425 breaks. Fail-within-120m on **85% (2025) / 84% (2026)** vs
  the declared 15% census floor. The strong "the break is usually the trap" form
  survives too — it needed >50% and got 84-85%.
- **PLACEBO MARGIN — the number that actually matters.** A 04:00-06:00 London range
  with no claim on the open fails at **73% / 70%**. So the headline 85% is mostly
  ordinary boundary mean-reversion. The trial is the margin: **+12pp (z=3.43)** and
  **+14pp (z=2.94)**, era-consistent. Never quote the 85% alone.
- SPLITS: up-break fail 78%/74%, down-break fail 80%/81% — no side asymmetry.
- TRANSFER TEST — **NEGATIVE, reported as one.** NYA-FA-01's excursion-depth
  discriminator does not replicate: points rho **-0.105** (inverted), normalised by
  range width rho **-0.017** (flat). Time-outside discriminates nothing here either,
  which does replicate NY. See `research/findings/nyfa-discriminator-does-not-transfer.md`.
- **RAW P&L (L1) — UGLY.** F1 (midpoint, declared default): 2025 n=234 WR 34%
  **−149 pts** PF 0.93 R/trade −0.190; 2026 n=125 WR 33% **+8 pts** PF 1.01 R/trade
  +0.002. Strict cost: both negative.
- **F2 (far-edge target, as taught) is the interesting loser.** 2025 −0.202R, 2026
  **+0.302R** (PF 1.20, +$6,031). Much better in 2026, no better in 2025 — **era
  INCONSISTENT**, so it does not displace the declared default on in-sample rank
  (§6.0.1). Ledgered as a declared negative, not promoted. Note this also means the
  census's implied midpoint correction is **not** confirmed: the target question is
  open, not settled in the midpoint's favour.
- ~~COST SENSITIVITY: average risk ~5 pts, so a 1–2 pt cost is 20–40% of the stop.~~
  **WRONG — corrected 2026-08-05.** That figure belongs to the OBK branch's
  trigger-candle stop. Actual risk on this branch: **median 14.0 pts, p10 5.5, p90
  39.8** — a 7.2× spread with no floor and no cap. Cost is 7–14% of median risk, not
  20–40%.
- VARIABLE LIFT: **negative.** Minimum displacement ≥0.10× range: 2025 −0.255R,
  2026 −0.200R — worse than unfiltered in both.
- **GEOMETRY CALIBRATION (2026-08-05, `docs/PREREG-london-po3-geometry.md`) — the
  stage this family was killed twice without.** Ordered by Angus: *"if u arent testing
  jack shit and just sending it off, its obviously not gonna do well."* Against the
  §5.11 checklist the family had cleared **2 of 9** items on **2 total arms**; the
  shipped IB fade got 28 arms across 13 trials. Kill vacated a second time, then:
  - **6 stops × 7 targets = 42 declared cells, identical 359-event set in every cell.
    0 of 42 are PF-positive at strict cost in both eras.** Best 0.97 (`E+F12/FAR`,
    `E/FAR`, `E+F8/FAR`); default `E/MID` 0.87; worst 0.63.
  - **Event universe (§5.11.2, never run here before): widening loses faster.**
    re-entry 359→1,109 trades at PF 0.77; window→11:00 London 405 at 0.85; both
    1,529 at 0.81.
  - **The as-taught FAR-edge target beat my midpoint substitution** — far-edge takes
    the top 3 slots and 5 of the top 6 (payoff 2.4–3.0 at 23–29% WR vs the midpoint's
    1.5–1.8 at 30–37%). Trial 1's census inference was wrong and is now settled.
  - **Stop floors help slightly, caps hurt, both are second-order** (~0.06 PF spread
    across all six stop rules). The stop was never where the problem lived.
- **VERDICT: DEAD (final), kill legal on the third attempt.** All three variable
  classes searched: geometry 0/42, flow-at-entry 0/6 confirmed, depth 1/32 paid and
  failed its null at family-wise p=0.42. Tombstone with the reopening burden:
  `research/findings/LDN-PO3-01-TOMBSTONE.md`.
- **NEVER SPENT: 2023/24 candles, the six sealed months, `depth_london_2023_24`.
  Three kills, zero holdout looks.**
- CANON SHAPE: raw ugly on schedule; **no variable class ever lifted** — that is the
  difference from canon, whose wall gate lifted a negative raw set into the book.

## nypre-gap-engine / nypre-inventory-correction — pre-market pair — SHELVED, back in play
- Under §5.9 book-level bars: gap PSR 0.77, inventory PSR 0.92 vs the new
  0.75 sleeve floor — both eligible as book components pending the book
  grading. Full history in research/candidates/nypre-*.md.

## nyo-rotation — overnight composite rotation (dual-sourced) — corrected retest ran WORSE; conditioning owed before verdict
- TRIAL 3 (2026-08-05, corrected as-taught grammar per RESPEC Spec 5):
  V-A shift-out n=63 PF 0.92 ($-1,060, only 2025 positive); V-B
  doubled-edge hold n=74 PF 0.82 ($-129, scratch-truncated). BOTH worse
  than the vacated touch-fade baseline below. Testing the RIGHT trade did
  not help.
- TRIAL 4 (conditioning, corrected events): no era-consistent positive
  gate; only consistent cell is NEGATIVE (V-A 18-22 PF 0.17 all 4 years);
  flow cells n=6-15 unclaimable; absorption structurally absent.
  RECOMMENDATION TO ANGUS: PARK as-taught (no verdict — too thin past the
  raw negatives); reopen when the flow span ~doubles. Awaiting his ruling.
- RAW TRIGGERS: 145 first-touch / 156 all-touch events over 548 composite-live
  overnight sessions (~3/month — overnight touches of day-built balances are
  structurally rare).
- RAW P&L: PF 1.10, +345 pts, $-665 at 1/risk sizing (wide natural stops),
  years +396/+74/-198/+74 — mediocre as the law expects; NO bin.
- CONDITIONING ROUND 1 (trial 2): weak — stop caps lift dollars (+$2.3-2.5k)
  but flip 2024 negative; flow-at-touch NEGATIVE on flow span (PF 0.95/0.58);
  euro-delta n=8 (nothing); time-of-night era-flips. No era-consistent gate
  yet. Remaining declared variables (absorption at edge, composite age/width,
  all-touch expansion) owed before any verdict — no bin off this.

## nya-daily-sweep — JadeCap 1H raid + SFP (NYA-DS-01) — census done, search owed
- STAGE: census + first declared splits (2026-08-05); full search owed.
- RAW TRIGGERS: 381 first-signal days / 845 biased days (~2.3/wk, matches
  teaching).
- RAW P&L: n=381, WR 38%, -1,132pts, $-454, PF 0.90 — ugly raw per law.
- YEARS: 2023 PF 1.11 / 2024 1.15 / 2025 0.87 / 2026 0.64 — DECAY shape
  (inverse of canon regime profile; book-diversification interest, live
  suspicion).
- FIRST SPLITS: PM window PF 1.56 (permnull p=0.030) but 2025 flips to
  0.32 — evidence not gate. Deep-penetration raids negative ALL 4 years —
  every-era-bad cut candidate for L1 (canon wall-cut precedent).
- TRIAL 2 — THE VARIABLE IS GAP CONTEXT: raids against a >20pt overnight
  gap are negative ALL FOUR YEARS (PF 0.68, n=227) — legal cut. L1b (cut
  gap-against + deep-pen): n=117, WR 46%, +$3,556, PF 1.89, EVERY YEAR
  POSITIVE (1.76/2.47/1.54/1.63), permnull p=0.008, ~0.69/wk. 2026 cell
  n=7 thin — flagged. The trial-1 decay lives in the gap-against cohort.
- TRIAL 3-5 (same day): strict costs PASS (PF 1.79 all years); flow round
  honest-thin (L1b∩flow n=30, discriminator open); autopsy done — time
  exits dominate (67/117), losers never go green (median MFE 0.11R),
  PRESS 88-100% / DYING 35-43% transfer from canon, GIVEBACK SIGN-FLIPS
  (76-100% good here — hourly rotation, declared for the agent playbook);
  exit tournament — default stands (PBO 0.50, displacement bar unmet),
  no_target/cap30/t3r/hold1555 banked, BE null defeated third time.
- TRIAL 6 GRADING: PSR(0) 0.986 vs 0.75 floor — PASS; MTRL 512d vs 915
  held; MC bust 0.1%, median +$1,032/yr (additive sleeve); correlation
  ~zero-to-negative vs canon AND fade; regime profile inverts the canon's
  — genuine diversifier. DSR carries the known ledger-denominator caveat.
- STATUS: SLEEVE-CERTIFIED pending Brake redundancy gate (blocked on his
  trade file) + Angus's book decision. 2026 n=7 on the label.
- CANON SHAPE: raw 0.90 → legal cuts → 1.89 era-consistent — the textbook
  arc, second family to show it.

## QUEUE (cards open at census)
- INTAKE ROUND 2 (2026-08-05, specs in research/transcripts/*/SPEC-as-taught.md,
  credibility in research/findings/intake2-credibility.md):
  - nya-ivb-fade first-formed-extreme arm — RUN AND REFUTED same day
    (trial 13, card above); no gate, default stands.
  - nya-ib50-continuation (MrZincx Model 1 as taught: enter IB midpoint
    toward predicted second-formed-extreme break; opposite vector to our
    fade) — new candidate, full funnel.
  - jadecap-daily-sweep (1H swing-point raid + SFP close-back-inside +
    5m FVG entry, NY AM/PM windows) — new candidate, full funnel.
  - orochi corrected respecs: sd2-rotation-fade w/ retest+add grammar
    (overnight analog) + failed-auction re-run on the taught hours-scale
    clock — verdict revisits, prior tests were strawmanned.
  - daxton-ifvg-continuation (EMA-stack bias + first inverted FVG after
    9:30, 5m close entry) — LOW priority: FCA warning on his handle,
    claims unverifiable; cheap census only if slate has room.
- orochi-vwap-regime-pair (edge fade gated by rotational condition vs trend
  side) — folded into the sd2 respec above.
- level-interaction trigger family (canon-frequency substrate, ~10-15 raw
  triggers/day) — prereg after.
- sweep-reclaim — awaiting Brake dedup vs london-level-trap-fade.
- §5.12.1-15 FEATURE SEMANTICS AUDIT on our depth features — RUN 2026-08-05,
  first pass CAUGHT A REAL BUG: the depth archive's second file family
  stores already-decimal prices; the blanket 1e-9 decode corrupted
  wall_dist/best_bid/best_ask on 52.5% of rows (295 days). FIXED
  (per-file scale detection in scripts/depth_walls.py, re-extracted,
  0% wrong-scale). NO VERDICT CONTAMINATED: every consumer (nya_fa_deep,
  nya_ivb_retest) read only wall_ratio, which is size-based and
  scale-free — verified identical pre/post fix. Price-based depth reads
  (wall_dist, book-vs-level joins) only became usable TODAY. Naming
  collision also fixed: the failed-auction card's "depth tercile" is
  EXTENSION depth (candle geometry), not order-book depth — renamed.

---

## THE BOOK — first portfolio grading (2026-08-05, scripts/nya_book_grade.py)
- COMPONENTS: live canon + IVB range fade (sleeve-passed) + pre-market pair
  (shelved-eligible under §5.9 bars).
- CORRELATION MATRIX: max |0.084| across all pairs — four independent
  P&L streams, no vetoes.
- FUNDED MC (12mo): canon alone P(bust) 0.2% / median +$77,882; FULL BOOK
  P(bust) 0.5% / median +$82,354 (+$4.5k/yr from the sleeves, maxDD
  $1,222→$1,460). New sleeves WITHOUT the canon: P(bust) 13.9% — the
  sleeves are additives, not a standalone account.
- BOOK PSR(0) 1.000 vs the 0.95 screen — PASS (canon-dominated; sleeve
  merit was established at sleeve level). Ledger-DSR still carries the
  denominator-inflation caveat (Brake fix pending).
- STATUS: book gates PASSED. Ship-track remaining for the range fade:
  chained-agents-vs-mechanical rung → shadow → Angus sign-off → two-party
  arming. Pre-market pair: same track at smaller weight, Angus's pick.
