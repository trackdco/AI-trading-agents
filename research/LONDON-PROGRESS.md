# LONDON PROGRAM — progress tracker

**The one page to look at.** Updated at the end of every working session (same
discipline as the old context/progress-tracker.md). Owner of diagnosis and
verdicts: **BRAKE** (ANGUS ruling 2026-08-04 — see docs/BRAKE-HANDOFF-london-program.md).
Angus owns: rulings, holdout-look declarations, veto waivers, bar ratifications.

Pipeline stages: thesis → greenlit → **prereg** → census (L0) → refine (L1–L4)
→ grade (permutation/DSR/PBO) → holdout (declared look) → VERDICT → shelf.

## Candidates (verdicts current as of 2026-08-06)

**⚠️ This table was stale for two days.** It read "greenlit / prereg owed" for five
candidates that had already been prereg'd, run and GRADED on 2026-08-04 — the same day
this page was written, in the afternoon after it was written. Reconciled 2026-08-06
against `output/trial_ledger.parquet` and the verdict documents. **Six London families
are graded. None passed.**

Evidence that these are real trials and not backfill: all six were present in the
ledger *before* the "Task 17: backfill 111 prose trials" commit (`f4e35c1^`, 116 rows),
all six carry `programme`/`researcher` provenance, and five carry `series_path`
pointers to committed per-trial artifacts under `output/trials/`.

| # | Candidate | Stage | Verdict / latest | Next action |
|---|---|---|---|---|
| 1 | inventory-fade (LDN-INV-01) | **refine** | Trial 1 (L0): 2025 shows the inventory signature (+20.7pts worst-quintile, asymmetric); 2026 direction agrees but asymmetry absent (kill crit. 2 live). NOT killed, NOT validated | joint conditioning: inv_skew × σ-location; inverse era pass |
| 2+3 | asia-sweep reversal + continuation (LDN-SWP-01) | **GRADED** | **FAIL both.** `VERDICT-LDN-SWP-01.md`. #3 fails cleanly under the declared spec; #2's declared test was invalid and the causal re-measurement is null. Carries a §0 CORRECTION — the first run hardcoded 03:00–06:00 ET, which is not the London session. Neither proceeds to L1 | closed unless re-thesised |
| 4b | **asian-trend-continuation (LDN-ATC-01)** | **GRADED — L1 Stage 1** | **FAIL.** `VERDICT-LDN-ATC-01-L1.md`. Primary (structural target) n=30, 2025 −0.489R / 2026 +0.101R — INCONCLUSIVE ON POWER (eras 22/8, both <30). Secondary (fixed 1R) n=88, **negative in BOTH eras** (−0.204 / −0.236), WR 44.3% vs the 55.5% needed. **Two defects found:** (i) LOOKAHEAD in the censused chain — the LTA gate reads the full 07:00–08:00 window but triggers fire at 07:30, so 29 of 108 (27%) are gated on bars that have not closed; the published L0 count of 108 is inflated. (ii) the prereg's structural target is already passed on 64% of triggers (100% at 07:30). Stage 2 NOT spent | causal respecification would be a NEW candidate, fresh prereg + fresh L0 |
| 4 | euro-open-drive | greenlit | thesis filed (ITSM frame, not naive ORB) — **genuinely untested** | prereg |
| 5 | level-trap-fade (LDN-TRAP-01) | **GRADED** | **FAIL.** `VERDICT-LDN-TRAP-01.md`. 2025 n=161 −2.30 pts (p=0.721); 2026 n=89 −2.64 pts (p=0.621). Wrong sign both eras, 48% of events positive. "The first candidate whose null means something" — real power, found nothing | closed |
| 6 | level-defense-flow (LDN-DEF-01) | **GRADED** | **FAIL all three measures.** `VERDICT-LDN-DEF-01.md`. ρ: ABSORB +0.040/−0.144, PIN +0.063/−0.012, ICEBERG +0.037/−0.116. AUC 0.451–0.515. n=99/89, min detectable ρ 0.248/0.262 — a null on evidence, not on power. All three fail the proximity ladder. Tombstone recommended | Angus ruling on the tombstone |
| 7 | vwap-sigma-rotation (LDN-VWAP-01) | **GRADED, leg 1 only** | **INCONCLUSIVE ON POWER** (blocks like FAIL). `VERDICT-LDN-VWAP-01.md`. 2025 n=77 −3.81; 2026 n=38 −12.15 — wrong sign both eras; 2026 CI [−37.87, +13.57] cannot separate slightly-negative from zero. Fragility clear | **legs 2–3 UNSPENT** (trend-day pullback to VWAP; late-window stall) |
| 8 | value-traverse (LDN-VT-01) | **GRADED, leg (a) only** | **INCONCLUSIVE ON POWER.** `VERDICT-LDN-VT-01.md`. 2025 n=53 +4.74; 2026 n=23 **below the n≥30 floor**. Two defects disclosed by the author: the feasibility count omitted the entry trigger, and the placebo was mis-anchored. Declared secondary (placebo-diff) returns "no effect" against the thesis's central claim | **legs (b)–(c) UNSPENT** (80%-rule verdict; LVN air-pocket path) |
| 9 | eu-macro-windows | greenlit | thesis filed; stand-aside rule doubles as news spec layer — **genuinely untested** | build EU release calendar → prereg |
| — | flow-confirmation (LDN-FLOW-01) | **GRADED** | Not on the original nine. 8 ledger rows, 4 committed artifacts, `PREREG-london-flow-confirmation.md`. Tested *minute-aggregate* flow and stated its own limit: price-level absorption is invisible at that resolution — which is what LDN-DEF-01 then went and tested | closed |

**Pattern legend** (ANGUS 22-Jul-2026, `docs/STRATEGY-SETUP-TAXONOMY.md` — authoritative):
**A** = reversal of a ±2 daily-VWAP over-extension · **B** = with-trend continuation ·
**B2** = rejection/fade. "Reclaim" is retired as a pattern name and survives only as the
E3 entry-reference level. Read any bare A/B/B2 in London artifacts against these.

**Trial-count reconciliation, unresolved and needing an ANGUS ruling.** Two London totals
are both quotable from the same ledger: **34** (rows carrying `programme=='LONDON'` —
Brake's declared trials, the figure `PREREG-london-level-defense-flow.md` §10 cites) and
**439** (all London-family rows, including 405 written by the L3/geometry search
harnesses for CAN-01/PO3-01/OBK-01). These count different things and imply materially
different deflation bars. §2.4's effective-trial clustering puts the truth between them.

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

- **2026-08-06** — Reconciliation, no trials charged. Ledger audited against the prose
  tracker: six London families are GRADED (SWP-01, TRAP-01, VWAP-01, VT-01, DEF-01,
  FLOW-01), none passed, and this page had been describing five of them as "greenlit /
  prereg owed" since 2026-08-04. All six pre-date the Task 17 backfill, so they are real
  trials the tracker never recorded, not backfill artifacts. Unspent legs identified:
  VWAP-01 legs 2–3, VT-01 legs (b)–(c). Two defects fixed at source: the A/B/B2 label
  conflict (code + `STRATEGY-SETUP-TAXONOMY.md` are canonical; `_trigger_class` was
  classifying B2 as continuation when B2 is a fade — dormant, arm-A only, no committed
  number affected) and footprint roll contamination + an inverted delta sign in two
  consumers (`src/engine/footprint.py` is now the chokepoint, both pinned by
  `tests/test_footprint_convention.py`). Sealed span untouched throughout.

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
