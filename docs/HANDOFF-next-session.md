# HANDOFF — continue here (new account / session, 20 Jul 2026)

You are the engine lane on Angus's NQ trading project. Angus is strategy authority;
you measure and build, you do not change strategy unilaterally. Brake owns data.
This doc is the bridge — read it, then continue.

## What just happened (changes committed this session, need validation)

**Tier 1 — E-2 bug fix (`src/engine/triggers.py` `_htf_flag`).** Unknown HTF regime used to
default to "downtrend" (`else "short"`), which mislabeled ambiguous-regime SHORTS as
`with_trend` (lenient) and LONGS as `counter_trend`. On a long-biased instrument that
manufactured phantom "with-trend" shorts that bled: short+with_trend **18% win / −$2,878**
vs long+with_trend **46% / +$6,336** (same label, opposite outcome = the tell). Fixed:
unknown → `range` (neutral). **This changes DETECTION**, so the trigger cache is now stale.

**Tier 2 — config-driven (`src/backtest/engine.py` + `config/strategy.yaml`, defaults off):**
- `session.no_trade_start/end = 09:30/09:40` — sit out the cash open (22% win, pure chop).
- `sizing.post_open_after = 09:40` + `entry.post_open_min_stop = 10.0` — post-open tape is
  **~2.4× wider** than pre-market (bars 31pt vs 13pt), so a 6pt floor sits inside the noise;
  10pt floor after 09:40. (ATR-scaled floor is the ideal form; this is the window stand-in.)

**All three are 2026-tuned and PENDING OOS validation. Do not trust them live until validated.**

## YOUR IMMEDIATE TASKS (in order)

1. **Re-detect the trigger cache with the E-2 fix.** The cached `output/triggers_*_ob.csv`
   have the OLD htf_flag. Regenerate (2026 first, then 2023-2025 hist) so the fix is live.
2. **Re-grade the champion with all 3 changes across 2023-2026.** Confirm E-2 closes the
   long/short gap (re-run the long/short × htf split — see this session's finding). Confirm
   cash-open + 10pt-post-stop help on 2026 AND check they don't wreck 2023-2025. **If they
   fail OOS, revert them** — same discipline as everything else.
3. **Run the powered CVD test.** Data is now here: `data/reference/cvd/footprint_feb_mar2026.parquet`
   + `footprint_may_jul2026.parquet` + `footprint_apr2026.parquet` (~250 days total). Re-run
   the corrected tests (`scripts/test_cvd_heatmap_givebacks.py`, `scripts/test_cvd_intrade_hold.py`)
   at full power. This is the **build-a-real-edge-or-bin-it** verdict for CVD as the
   hollow-entry / conviction filter. April alone (n≈10) was underpowered-null.

## The strategic direction (Angus's reframe — the north star)

**Optimize for SELECTIVITY, not total P&L.** The bot takes too many bad trades (32-42% win)
vs Angus's live 50%+ on 1-2 trades/night. The win-rate gap is the target, not dollars.
Concretely: (a) make the trade cap **rank by quality and take the best 2, not the first 2**;
(b) use **CVD as the conviction filter** (is there real buying behind this level, or hollow?).
The mechanical selectivity gets partway; CVD closes the rest.

## Honest state of findings (do NOT re-discover these the hard way)

- **v0.7 regime dial** (`docs/SPEC-v07-regime-dial.md`): validated, current best day-level layer.
- **Window/cap "+44%" shape: 2026-ONLY, FAILS OOS** (2023-24 materially worse). Do not ship.
- **9:30 re-read at 0.45: lean-engine artifact, did NOT reproduce in the real engine. Dead.**
- **Longs-only: a SYMPTOM of the E-2 bug + 2026 bull run, not a fix.** Don't blanket-cut shorts
  — fix E-2, then judge shorts on merit.
- **Confluence is NOT the selectivity knob** — raising it to 3 lowered win rate. Verified.
- **The base detection champion LOSES out-of-sample (2023-25)** — it's 2026-calibrated. The big
  open question: does it have a cross-regime edge, or is it fundamentally 2026-fit? For live-now
  it's workable (trade 2026, monitor, re-tune), but validate EVERY change across 2023-2026.

## Key files / people

- Config: `config/strategy.yaml` · engine: `src/backtest/engine.py`, `src/engine/triggers.py`
- Champion journal builder (Pass-29 style, full features): the scratchpad `journal_v2.py` pattern
- Cap/window/stop sweeps: `scripts/cap_sweep.py` · stand-down: `scripts/standdown_study.py`,
  `scripts/regrade_standdown.py` · chop: `scripts/chop_detector.py`
- Brake's data status: VIX done, CVD feb-jul done, heatmap April verified-correct (thin book is real,
  not a bug). Pat's Desk-build rulings: `docs/FOR-ANGUS-desk-spec-questions.md` (separate track).
- Discipline: grade net dollars not accuracy; frozen-OOS split is the overfit defense; profitable-
  every-year is the north star; report in $/points/%; artifacts for major deliverables.
