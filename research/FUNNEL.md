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
- NEXT: 23-24 candle era check at the SAME geometry → exit/stop arms (§6.0
  default declared first) → graders under §5.9 bars.
- CANON SHAPE: ahead of canon's arc (canon raw was negative pre-wall-gate).
- HISTORY NOTE: killed twice by strawman censuses (missing trigger; harsher
  race than the taught trade), vacated on canon-parity, alive on retest —
  the correction that proved the framework audit mattered.

## nya-failed-auction — balance-break fail branch (dual-sourced) — ALIVE, deep pass
- STAGE: conditioning found; deep pass (walls, day/open type) + 23/24 loop owed.
- RAW TRIGGERS: 457 breaks / 911 sessions (~2.5/wk); 248 in-window fails; 71
  fail events on flow span.
- RAW P&L (L1, full span): n=248, WR 35%, −1,025 pts, PF 0.83 — ugly as the
  law expects.
- VARIABLE LIFT: depth tercile WR 12%→59% (the trapped-mass variable);
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

## london-nq-open-break (LDN-OBK-01) — continuation branch — ALIVE, census passed
- STAGE: L0 census done (`docs/PREREG-london-open-break-tree.md`). L1 owed.
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
- NEXT: L1 with the trigger-candle stop (the whole reason this candidate exists —
  `nypre-euro-handoff` died at 78% WR / +0.02R on exactly this axis), arm A default
  per the declared promotion rule, 1x and 2x costs.
- CANON SHAPE: too early — no P&L yet. Census arc is normal (premise clears wide).

## london-po3-ifvg (LDN-PO3-01) — failure branch — ALIVE, census passed, claim narrowed
- STAGE: L0 census done, same prereg, same event tree. L1 owed.
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
- NEXT: L1 on arm B (close back inside) — arm A (IFVG) is barred until a mechanical
  definition is committed in advance. SMT confluence dropped, no ES data.
- CANON SHAPE: too early. The placebo margin is the honest starting edge, not 85%.

## nypre-gap-engine / nypre-inventory-correction — pre-market pair — SHELVED, back in play
- Under §5.9 book-level bars: gap PSR 0.77, inventory PSR 0.92 vs the new
  0.75 sleeve floor — both eligible as book components pending the book
  grading. Full history in research/candidates/nypre-*.md.

## QUEUE (cards open at census)
- orochi-overnight-rotation (as taught: composite edge fade + DVA shift
  confirmation, overnight session) — prereg next.
- orochi-vwap-regime-pair (edge fade gated by rotational condition vs trend
  side) — prereg next.
- level-interaction trigger family (canon-frequency substrate, ~10-15 raw
  triggers/day) — prereg after.
- sweep-reclaim — awaiting Brake dedup vs london-level-trap-fade.
