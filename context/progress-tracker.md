# Progress Tracker

Update at the END of every Claude Code session. This file is how sessions hand off to each other and how Angus audits without reading code.

## Current state

- **Active phase:** 1 — Market Engine & Backtester
- **Active spec:** spec-1-market-engine-backtester.md
- **Last completed step:** Spec 1, Step 4 (indicators) — BUILT + adversarially verified (8 findings, 2 medium auto-fixed, parity numbers unchanged). 40 tests pass, ruff clean. output/parity_report.md generated with LOCKED engine numbers (committed for cross-session review).
- **Blocked on:** Step 4 PARITY GATE — Angus's chart readings for Feb 11 09:48 ET, Feb 17 09:50 ET, read on **NQH2026 (not MNQ1! back-adjusted)**. Engine numbers are locked and waiting in output/parity_report.md.
- **⚠️ Parity instrument fix (from data/reference/parity_chart_settings.md, salvaged from Angus's branch):** Angus must read the chart on **NQH2026 (March 2026 NQ)** — NOT MNQ1! and NOT a back-adjusted `1!` continuous. Engine uses unspliced continuous NQ = NQH6 for Feb 11/17 (verified). Back-adjust + micro-volume would shift prices/VWAP/POC by tens of points and guarantee a false gate failure.
- **Branch consolidation:** canonical branch = `claude/getting-started-6lwnvs` (see context/TEAM.md). Three duplicate-engine branches superseded; useful files salvaged (.env.example, parity_chart_settings.md).
- **Next action:** finish Step 4 verification → lock parity numbers → Angus signs off → Steps 5-9.

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

### 2026-07-17 — Spec 1 Step 4: indicators + parity report, adversarially verified (Claude Code, Brake driving)
- Steps completed: Step 4 — src/engine/indicators.py (per-TF Bollinger population stdev; daily VWAP 18:00-anchored + NY VWAP 09:30-anchored, both hlc3 source with VOLUME-WEIGHTED σ bands, NY VWAP NaN pre-9:30; developing volume profile POC/VAH/VAL/HVN/LVN in 0.25-pt bins; indicators_asof with structural last-closed-bar semantics). tests/test_indicators.py (incl. mandatory test_ny_vwap_absent_premarket + no-lookahead). scripts/make_parity_report.py → output/parity_report.md.
- Build method: authored + 3-lens adversarial verification (formula parity / lookahead-tz / volume-profile) + fix pass. 8 findings, ALL confirmed. 2 medium FIXED: (a) daily-VWAP session boundary honored the config 18:00 anchor via a new anchor-aware helper in indicators.py (data._session_date left unchanged — it hardcodes 17:00 for the gap report; no real bars in 17:00–18:00 so parity numbers were provably unaffected); (b) added a resample-rule guard so HTF rules like 4h can't silently midnight-anchor. Parity numbers identical before/after fixes; independently recomputed to the cent.
- Checks passed: 40 tests pass (was 21), ruff clean. LOCKED engine values in output/parity_report.md.
- Low-severity findings FLAGGED for later refinement (none affect the parity gate): (1) HVN/LVN defined as strict 1-bin local extrema on 0.25-pt bins → ~113 "HVNs" (noise); needs a prominence/min-gap rule before HVN/LVN are used. (2) POC/VAH/VAL reported at bin CENTER (+0.125 vs the tick grid) — within the 1-pt gate tolerance; consider reporting the traded (lower-edge) price. (3) profile_asof scope='ny' window ends 17:00 (maintenance) vs the config NY box 16:00 — reconcile. (4) data._session_date's session_open param is dead (17:00 hardcoded) — worked around in the indicator layer; clean up at the source later. (5) HTF (1h/4h) session-anchored resampler deferred to Step 5.
- Flags for Angus (parity gate): read the chart on NQH2026 (dated March-2026 NQ), not MNQ1! back-adjusted (see data/reference/parity_chart_settings.md); check the BB row for the TF he traded (Feb 11 = 3M, Feb 17 09:50 = 2M); daily POC is the DEVELOPING (as-of) profile, read the chart profile as-of that time; POC reported at bin center (within tolerance).
- Next session starts at: Step 4 parity GATE — Angus fills chart values in output/parity_report.md; |Δ| ≤ 1.0 pt each → sign-off → Step 5. DO NOT build Steps 5-9 before sign-off.

### 2026-07-17 — Spec 1 Step 3: resampler + sessions (Claude Code, remote session, Brake driving)
- Steps completed: Step 3 — src/engine/sessions.py: resample_ohlcv/resample_all (1m→2/3/5/15m), session_of/add_session (Asia/London/NY §2 boxes), running_session_extremes, prior_day_levels, prior_week_levels, data_levels (extremes near news releases) + news-calendar loader. tests/test_sessions.py (8 tests).
- Checks passed: pytest tests/test_sessions.py = 8 passed incl. **test_dst_boundary** (spring-forward Mar 8: EST −05:00 vs EDT −04:00 handled; 09:30 classifies NY on both sides; resample + prior-day map correctly across it). Hand-computed resample fixture verifies close-time labels + boundary (09:35 bar aggregates 09:30–09:34, excludes 09:35). Real-data smoke: 2/3/5/15m counts ≈ base/N, volume conserved, 213 news events matched data-levels, Mar 6–9 resample shows both EST/EDT offsets. Full suite 21 passed; ruff clean.
- Divergences/flags raised: (1) **Resampler label convention** — Databento 1m is START-labeled (ts=interval open); to realize the spec's "right-closed, label=close time" the resampler bins `closed='left', label='right'` so N-min bars are stamped by CLOSE (no lookahead). Documented in-module + hand-tested. (2) **1m base stays start-labeled** while resampled TFs are close-labeled — the 1m entry-TF reconciliation (treat 1m signal as actionable at ts+1min) is deferred to Step 5 (snapshot); flagged. (3) **prior_week uses ISO week (Mon-start)** — trading-week (Sun 18:00→Fri 17:00) is a possible refinement, flag for Angus. (4) **data_levels window = [E, E+N]** (post-release reaction, N=15 from config); §2 says "within N min of a release" — confirm post-release vs symmetric with Angus. (5) Session box times are the Step-1 PLACEHOLDER values (Asia 18:00–03:00 / London 03:00–09:30 / NY 09:30–16:00) — still pending Angus confirmation.
- Questions parked for Angus: confirm items (3)(4)(5) above; all prior parked items still open (strategy.yaml PLACEHOLDERs incl. T_cancel & "oversized stop", news impact ratings, four PNL Points quirks, Step 4 chart values, parent→continuous derivation, Jan-1 data, strategy-doc read-through).
- Next session starts at: Spec 1, Step 4 (indicators) — the parity-gate step.

### 2026-07-17 — Real Databento data ingested; parent→continuous derivation added (Claude Code, Brake driving)
- What happened: Angus/Brake's Databento pull came as a **"parent" export** (all NQ outright contracts + calendar spreads, GLBX.MDP3 ohlcv-1m, 2026-02-01→2026-07-15, ~254k rows, decimal px / ISO ts). That is many rows per minute, not the single continuous series the engine needs.
- Decision (ENGINEERING, flagged for Angus): rather than have Brake re-download NQ.v.0, we derive the continuous series from the parent file. Added `to_continuous_front_month()` to src/engine/data.py. **Exact roll rule chosen:** outright contracts only (drop symbols containing '-'); front month = the outright with the greatest total volume per CME trade date (18:00 ET session boundary); continuous takes that contract's minute bars for the session; rolls at the session boundary on front-month change; **unspliced** (no price back-adjustment) per strategy-definition §3. This reproduces Databento's NQ.v.0 transparently/auditably (fits the project's anti-black-box stance). Volume separation is huge (~500k front vs a few hundred back) so front-month is unambiguous.
- Result: 161,525 continuous bars, 142 trading days, 2026-02-01→2026-07-15. Rolls tagged: 2026-03-15 (NQH6→NQM6) and 2026-06-14 (NQM6→NQU6) — the normal quarterly rolls. Unspliced roll price-gaps present as expected (+164.75 Mar, +513.25 Jun). Prices 22,973–30,970 (sane for NQ). Monotonic, no dup timestamps.
- Gap report (output/gap_report.csv): 6 sessions with "unexpected" missing minutes — ALL are US market holidays / early closes (Feb 16 Presidents' Day, Apr 3 Good Friday, May 25 Memorial, Jun 19 Juneteenth, Jul 3 Jul-4-obs) plus one trivial 1-minute overnight blip (Apr 21). i.e. the data is clean; gaps = real closures. `_is_closed` intentionally doesn't model holidays — cross-reference config/news_calendar.csv holiday rows.
- FLAGS for Angus: (1) **Data starts 2026-02-01, not Jan 1** — the download range was Feb–Jul. config data.primary_start = 2026-01-01. Calibration (Feb) is fully covered; re-pull with start 2026-01-01 before any full Jan-onward backtest. (2) Confirm OK to derive continuous from parent vs using Databento NQ.v.0 (result is equivalent; ours is auditable). (3) Presidents' Day (Feb 16) + Good Friday (Apr 3) are US market holidays not yet in news_calendar.csv (which is scheduled-releases focused) — note for the holiday cross-reference.
- Tests: added test_parent_collapses_to_volume_front_month (spreads dropped, one row/min, roll tagged). Full suite 13 passed; ruff clean. Parent CSV + parquet are gitignored (not committed).

### 2026-07-17 — Spec 1 Step 2: data ingest (Claude Code, remote session, Brake driving)
- Steps completed: Step 2 — src/engine/data.py (Databento ohlcv-1m CSV -> validated tz-aware parquet at data/nq_1m.parquet, columns ts_event/open/high/low/close/volume/roll); tests/fixtures/nq_1m_2day.csv (2-day Databento-native fixture with a deliberate 09:35 gap + an instrument_id roll); tests/test_data.py (12 tests); conftest.py (repo root on sys.path).
- Checks passed: `pytest tests/test_data.py` = 12 passed; ruff clean repo-wide; end-to-end CLI produced parquet (dtypes verified: ts_event datetime64[ns, America/New_York], roll bool) + output/gap_report.csv. Validation proven: duplicate/non-monotonic timestamps raise; tz conversion UTC->NY (DST-aware); 1e-9 fixed-precision prices auto-decoded to ~20000; roll tagged once at the instrument_id change; gap report counts a real RTH hole but EXCLUDES the 17:00-18:00 maintenance break and the weekend close (hand-built unit tests).
- Divergences/flags raised: (1) NEW DEPENDENCY **pyarrow** — not in the approved list, but Spec 1 Step 2 mandates parquet output; added to README setup, flag it to Angus. (2) SCOPE — implemented **CSV ingest only**; DBN input is a documented TODO in data.py (deferred until Angus's actual Databento export format is known, to avoid pulling the heavy `databento` package on assumptions). (3) The `roll` column is an extension beyond the spec's literal 6-column list, required by the "roll-date tags" validation clause (§3 "tag roll dates in the data"). (4) Step 2's SECOND check ("gap report generated for full dataset") is still BLOCKED on the Databento download — the gap-report machinery is built and tested on the fixture; run `python -m src.engine.data data/raw/<file>.csv` when data lands.
- Questions parked for Angus: OK to keep pyarrow? Confirm the Databento export flavour (continuous symbol e.g. NQ.c.0 vs NQ.v.0; CSV vs DBN; pretty-px/pretty-ts on/off) so the loader assumptions can be confirmed. Plus all prior parked items (strategy.yaml PLACEHOLDERs, news impact ratings, four PNL Points quirks, Step 4 chart values, strategy-doc read-through).
- Next session starts at: Spec 1, Step 3 (resampler + sessions).

### 2026-07-17 — News calendar extended Mar–Jul 2026 (Claude Code, remote session, Brake driving)
- Work done: parsed three Forex Factory calendar PDF exports Angus provided (Mar 1–May 2, May 2–Jul 3, Jul 3–present) into config/news_calendar.csv. Added 219 rows (2026-03-02 → 2026-07-17); file now holds 236 total (Feb seed kept as-is). Committed the reproducible extractor at scripts/extract_news_calendar.py.
- Data-quality issues caught and handled (these would have silently corrupted the backtest): (1) exports are in **Australia/Melbourne (GMT+10)**, not ET — every timestamp converted to America/New_York with zoneinfo (DST-aware; exports straddle the Apr 5 AU DST change), verified against known ET release times (NFP/CPI 8:30, ISM 10:00); (2) impact colour lives only in the PDF folder-icon graphics — read from rendered pixels (red→high, orange→medium, grey→holiday); (3) the two PDFs overlap on May 2 and Jul 3 — deduped; (4) fixed a July-page layout quirk that leaked the Actual value into event names; (5) US market holidays validated to the known set (Memorial Day May 25, Juneteenth Jun 19, Jul 3 obs); (6) AHE / Unemployment Rate snapped to travel with the payrolls print (correctly Thu Jul 2 that week, since Jul 3 is the holiday).
- Checks passed: 236 rows parse; columns intact; ruff clean on scripts/; committed script reproduces the committed rows byte-for-byte; 0 weekday violations on recurring releases (NFP=Fri, Claims=Thu) except the legitimate Jul-2 holiday shift.
- Flags for Angus (also in the news_calendar.csv header): confirm impact ratings match how we want news days classified; decide whether non-data rows (Trump/Fed speeches, DST shift, OPEC) should be ignored by the engine (Phase 2); dates around the Apr 5 AU DST change + holiday weeks are the least certain (recurring releases were weekday-validated, others worth a spot-check); all-day/tentative rows carry a 00:00 placeholder time. New TODO: extend calendar past 2026-07-17 before backtesting beyond that date.
- Note: input PDFs are NOT committed (gitignored under data/reference/news_pdfs/); Pillow used dev-only for pixel colour reading (not an engine runtime dependency).
- Next action unchanged: Spec 1, Step 2 (data ingest).

### 2026-07-16 — Spec 1 Step 1: repo scaffold (Claude Code, remote session, Brake driving)
- Steps completed: Step 1 — README.md, config/strategy.yaml (76 leaf parameters, all §-traced), config/news_calendar.csv (17 Feb 2026 seed rows), src/engine/, src/backtest/, tests/, data/raw/, output/, .gitignore (data/raw/ + output/ + .env ignored)
- Checks passed: repo tree matches Step 1 list; strategy.yaml parses via PyYAML; automated scan confirms every parameter line carries a §/spec-1 trace comment; news_calendar.csv parses with expected columns
- Divergences/flags raised — PLACEHOLDER values in strategy.yaml (doc names the parameter but gives no start value; all marked PLACEHOLDER in-file): T_cancel start value (§5.5, set 15.0 pts); session box times (§2, standard Asia 18:00–03:00 / London 03:00–09:30 / NY 09:30–16:00 used); W2 "full trading day" scope read as full CME session 18:00→15:55 (§1); volume-profile value-area % (set 70, industry standard); slippage S_normal=1 / S_news=4 ticks, N_news=15 min, commission $2.50/side (spec-1 §3, engineering placeholders). News calendar seeded from the hand log's News detail column because the reference journals are not in the repo — times use the log where stated, standard release times otherwise; impact ratings best-effort. `.env.example` flagged in next-tasks.md (required by code-standards, not named in Step 1) rather than silently added.
- Questions parked for Angus: confirm the PLACEHOLDER values above; prior session's four PNL Points quirks, Step 4 reference-chart values, and strategy-doc final read-through all still pending
- Next session starts at: Spec 1, Step 2 (data ingest) — Step 1 result shown to human for confirmation first

### 2026-07-16 — Repo initialization (Claude Code, remote session)
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
