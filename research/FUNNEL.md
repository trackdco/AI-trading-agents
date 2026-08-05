# THE FUNNEL — live per-strategy data cards (Angus's window into every stage)

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
- COST SENSITIVITY IS THE STORY: average risk on this branch is small (~5 pts, because
  the sweep extreme sits close to the fail-bar close), so a 1–2 pt cost is 20–40% of
  the stop. Fabio named NQ slippage as the thing that breaks his version; this is that,
  measured.
- VARIABLE LIFT SO FAR: **negative.** Minimum displacement ≥0.10× range: 2025 −0.255R,
  2026 −0.200R — worse than unfiltered in both.
- NEXT: conditioning search (earned — census premise passed, §5.9.2 forbids an
  expectancy kill here). Arm A (IFVG) still barred pending a mechanical definition.
  SMT confluence still dropped, no ES data.
- CANON SHAPE: raw ugly on schedule; first variable did not lift.

## nypre-gap-engine / nypre-inventory-correction — pre-market pair — SHELVED, back in play
- Under §5.9 book-level bars: gap PSR 0.77, inventory PSR 0.92 vs the new
  0.75 sleeve floor — both eligible as book components pending the book
  grading. Full history in research/candidates/nypre-*.md.

## nyo-rotation — overnight composite rotation (dual-sourced) — census done, conditioning owed
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
