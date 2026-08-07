# LONDON PROGRAM — progress tracker

**The one page to look at.** Updated at the end of every working session (same
discipline as the old context/progress-tracker.md). Owner of diagnosis and
verdicts: **BRAKE** (ANGUS ruling 2026-08-04 — see docs/BRAKE-HANDOFF-london-program.md).
Angus owns: rulings, holdout-look declarations, veto waivers, bar ratifications.

Pipeline stages: thesis → greenlit → **prereg** → census (L0) → refine (L1–L4)
→ grade (permutation/DSR/PBO) → holdout (declared look) → VERDICT → shelf.

## Candidates (as of 2026-08-04)

| # | Candidate | Stage | Latest | Next action |
|---|---|---|---|---|
| 1 | inventory-fade | **refine** | Trial 1 (L0): 2025 shows the inventory signature (+20.7pts worst-quintile, asymmetric); 2026 direction agrees but asymmetry absent (kill crit. 2 live) | joint conditioning: inv_skew × σ-location; inverse era pass |
| 2 | asia-sweep-reversal | greenlit | thesis filed | prereg |
| 3 | asia-sweep-continuation | greenlit | thesis filed | prereg (same family as #2 — one ledger) |
| 4 | euro-open-drive | greenlit | thesis filed (ITSM frame, not naive ORB) | prereg |
| 5 | level-trap-fade | greenlit | thesis filed | prereg |
| 6 | level-defense-flow | greenlit | flow-span only (Jun 2025+); NY veto expected | prereg |
| 7 | vwap-sigma-rotation | greenlit | thesis filed (3 legs, one family) | prereg |
| 8 | value-traverse | greenlit | thesis filed | prereg |
| 9 | eu-macro-windows | greenlit | thesis filed; stand-aside rule doubles as news spec layer | build EU release calendar → prereg |

## Program infrastructure

| Piece | Status |
|---|---|
| Shared substrate (912 days, 2023→2026-07) | **BUILT** — scripts/london_day_features.py → output/london_day_features.parquet |
| Candle master store | data/reference/nq_1m_master.parquet (verified span) |
| Emission contract + reference impl | BUILT — scripts/emit_strategy.py, 3 emissions committed |
| Redundancy detector (same-session) | BUILT — scripts/pairwise_overlap.py (--demo, --self-test) |
| Cross-portfolio battery | BUILT — scripts/correlation_battery.py; NY↔old-London measured (−0.09/−0.11) |
| Validation process doc | WRITTEN + 6 education-round amendments; bars [PROPOSED] — Brake reviews knobs, Angus ratifies |
| Vault schema | WRITTEN — Pat builds mechanism (Obsidian) |
| Education round (3 reference docs) | DONE — research/findings/ (elite-quant ops, math canon, strategy-class evidence) |
| DSR/PBO models | BRAKE — in flight; effective-trial clustering note in §2.4 for him |
| Refinement-lab harness | NOT BUILT — next big build after first manual refinement cycles prove the shape |

## Standing rules in force

- Same account as NY canon (ANGUS ruling) → every candidate measured against the
  NY book during validation; input-family veto waivers are Angus calls.
- 2023/24 untouched; holdout = the six sealed months, by declared look only.
- Discover-2025 / validate-2026 AND the inverse pass; era-flips kill.
- Every trial ledgered (including abandoned); costs taker-default from L1.
- New candidate ideas → thesis to Angus first (the thesis gate).

## Session log (newest first)

- **2026-08-04** — Program launched. Nine theses greenlit; substrate built +
  verified (DST clock corrected by measurement: mismatch-week euro open = 04:00
  ET); education round filed (3 docs); process amendments landed; PREREG
  LDN-INV-01 declared and census run same day (results above); NY↔old-London
  correlation measured; emission/redundancy/battery instruments built and
  self-tested. Handoff to Brake written.

## Program expansion — NY PRE-MARKET (ANGUS 2026-08-04)

Goal: apply the same research → prereg → validation pipeline to the NY
pre-market window, with a named bar — **outperform the shipped canon's pre
leg** (the canon's measured weak spot: desk-run-2 agent edge was entirely gold;
pre flat, −1.1R over 227). Status: research sweep running; thesis sheet to
Angus for greenlight next. Redundancy vs the incumbent canon's pre entries is a
first-class check from day one (same clock, same account).

## NY pre-market candidates (as of 2026-08-04 — thesis-pending, awaiting Angus)

| # | Candidate | Core evidence | Key flag |
|---|---|---|---|
| P1 | nypre-on-polarity | **census PASSED: 77.2%/74.4% by era** | → L1 mechanics; 09:30 ruling for carry |
| P2 | nypre-open-sweep-fade | **PARKED: 9 events/19mo — data-starved** | recondition needs fresh prereg |
| P3 | nypre-inventory-correction | academic + Dalton convergence, unquantified | fade family; matrix slice |
| P4 | nypre-gap-engine | fill-timing + news-minted split + survival flip | most branches cross 09:30 |
| P5 | nypre-0830-event-tree | hold/fail branches; falsification paper = null | release-day slippage honesty |
| P6 | nypre-prerelease-premium | JFE risk-premium channel, uncertainty-gated | low-Sharpe tilt by design |
| P7 | nypre-euro-handoff | ALN 75–81%, two independent datasets | HIGHEST canon-redundancy risk |
| P8 | nypre-quiet-hours-reversion | 76–83.5% hourly reversion 06:00–08:00 | popularized 2025 — decay split |

Parked pending event studies: opening-cross-echo (09:28 NOII tape echo),
0400-mini-open. Spec layers: release-tier gate (+ FREE canon pre-leg audit by
tier — never been done), FOMC-morning compression (+ canon FOMC audit),
premarket-range vol switch, day-classification matrix. Program bar: outperform
the canon's pre leg. Sweeps + merge map in research/articles + findings.
