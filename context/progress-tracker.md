# Progress Tracker

Update at the END of every Claude Code session. This file is how sessions hand off to each other and how Angus audits without reading code.

## Current state

- **Active phase:** 1 — Market Engine & Backtester
- **Active spec:** spec-1-market-engine-backtester.md
- **Last completed step:** (none — setup nearly done; repo initialized, hand log committed)
- **Blocked on:** Databento data download (blocks Steps 2+ on real data; Steps 1–3 checks run on fixtures); Angus's reference-chart values for the Step 4 parity gate (Feb 11 09:48 ET, Feb 17 09:50 ET)
- **Next action:** Spec 1, Step 1 (repo scaffold) — can start immediately

## Gates ledger (Angus sign-offs — append-only)

| Date | Gate | Result | Notes |
|---|---|---|---|
| 2026-07-17 | strategy-definition v1.0 locked | PASSED | Q&A incorporated; daily VWAP anchor confirmed 18:00 ET |
| — | Spec 1 Step 4 parity report | pending | |
| — | Spec 1 Step 8 calibration classification | pending | |

## Decision log (append-only; one line per decision, with source)

- 2026-07-17 — MIG LiquidityEdge excluded from mechanical system (Angus; strategy doc §2)
- 2026-07-17 — Agents never see P&L/prior outcomes; system proposes, human disposes on rule changes (Angus + Claude)
- 2026-07-17 — Entry window W1 8:00–11:00 primary; W2 full-day priority test; BE-at-1R vs none = priority tournament (Angus)
- 2026-07-17 — Data: Jan 2026→present primary; 2025 as robustness check only (Angus regime rationale, honesty guard noted)

## Session log (newest first)

### 2026-08-11 — PXL/PXH P-TABLE build, Stage 1 of BUILD-PLAN-pxl (Claude Code, remote session, branch claude/pxh-pxl-strategy-2c4gzh)
- Steps completed: DECLARATIONS-holdout-partition.md created and committed PRE-BUILD (fit 2023-01-02..2025-05-31; sealed 2025-06-01..2026-01-30 unread; flow venue = six family-A NY-AM months one look; bar-only venue two blocks); flow coverage manifest committed; strategy-validation skill installed to .claude/skills/; P-TABLE built per SPEC-pxl-p-table.md Part B (scripts/p_table_lib.py, build_p_table.py); all three B4 gates implemented and passed (scripts/p_table_gates.py) incl. the two-part tf_trigger causality assert; B5 items 1–13 reported (output/p_table_build_report.md)
- Checks passed: Gate 1 (24 probes, both sessions × both directions × three row classes), Gate 2 (future-flatten + 1-tick close-shift invariance of the limit; eligibility on the 5m grid; fills strictly after eligibility), Gate 3 (510 flow files; magnitude-based scale detection; roll-week exclusions by declared criterion)
- Divergences/flags raised: (1) M-TABLE infrastructure named in the task (DECLARATIONS file, SPEC-htf-ma-mechanism-census.md, scripts/htf_ma_entry_gate.py) does not exist on any branch — conventions implemented from the SPEC itself, provenance noted in the declarations; (2) DA-4: SPEC A1's literal london window (03:00–07:00 London local = 22:00–02:00 ET) contradicts the trader's own London recording (08:00–09:59 London) and the Asia exclusion — implemented 08:00–12:00 Europe/London, parameterised, NEEDS ANGUS RULING; (3) flow archive is 1-minute BOOK SNAPSHOTS ONLY (3 trade rows in 510 files) — delta/CVD/footprint unmeasurable historically; delta columns NaN with flow_data_object='book_only'; forward recorder must capture trade prints; (4) Gate-1 finding: strict C4 reading unsatisfiable under mode (b) — ts_decision is the 5m boundary (declarations §6a); (5) 17 roll-week flow files excluded from flow_coverage (calendar criterion, rows kept); (6) sealed span is the TAIL not the head (declarations §1 explains why B1's venue partition forces it)
- Questions parked for Angus: DA-4 london window ruling; MIN_LEG_RETRACE value (built at 0.382, sensitivity 0.236/0.5 reported); mode (a) vs (b) resolution ruling once the A1.1 comparison is read
- Next session starts at: Stage 2 (base rates) — the fill-rate/adverse-selection headline in the build report gates whether Stages 4–10 are worth running

- Steps completed: repo created; full context pack committed (context/, strategy-definition-v1.0.md, spec-1); Angus's 28-trade hand log committed at data/reference/feb2026_hand_log.csv (as-is, per reported-not-fixed)
- Checks passed: all 28 reference trades present; hand-log P&L $ / R Multiple / Risk $ columns cross-check internally
- Divergences/flags raised: PNL Points column quirks in hand log, pending Angus confirmation — Feb 10 logged +11 pts on a −$220 loss (should be −11); Feb 18 09:42 logged 0 pts on −$400 stop (should be −20); Feb 19 logged 0 pts on −$150 discretionary close; Feb 27 09:40 logged 0 pts on −$324 stop (should be −27). Also noted: Feb 2 "BE stopped" means the hand sample already includes BE management (relevant to V0-vs-V1 tournament framing); Feb 19 discretionary close will never be matched by a mechanical exit (expected calibration divergence, not a bug)
- Questions parked for Angus: confirm the four PNL Points quirks above; provide reference-chart values (BB basis, daily VWAP ±1σ, NY VWAP, daily POC) for Feb 11 09:48 ET and Feb 17 09:50 ET for the Step 4 parity gate; formally confirm strategy-definition-v1.0.md final read-through (status line says "LOCKED pending final read-through")
- Next session starts at: Spec 1, Step 1 (repo scaffold)

### YYYY-MM-DD — (template)
- Steps completed:
- Checks passed:
- Divergences/flags raised:
- Questions parked for Angus:
- Next session starts at:
