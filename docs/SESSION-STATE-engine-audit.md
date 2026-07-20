# SESSION STATE — engine audit + entry-timing fix (Brake, 20 Jul 2026)

Resume point. Read top-to-bottom. Work is on `getting-started-6lwnvs` (the real pipeline) but
LANDS here on `brake-43x58e` (no push to getting-started without Brake's OK). The engine fix is
captured as `patches/engine-entry-timing-fix.patch` so nothing is lost across a reconnect.

## P0 engine audit — VERDICT: the champion engine is SOUND
Three parallel auditors (fill-realism, lookahead, timezone/session), each verified by code-trace +
empirical probes. No material inflation of the +$14k champion; no lookahead (prefix-invariance:
indicators 80/80, triggers 22/22). The textbook backtest-inflation bugs are ABSENT (stop-first
ties, trade-through fills, correct slippage, min-stop floor, next-bar activation, correct R/$).

### Confirmed bugs (none inflate the current Jan–Jul champion)
| # | Bug | Impact | Status |
|---|-----|--------|--------|
| 1 | Entry activated 1 bar LATE (fill block ran before trigger block) | DEFLATES (under-fills) | **FIXED (patch)** — Brake ruled not intended |
| 2 | Sit-out / VWAP-warmup / news-preopen blocks gated NEW triggers only, not RESTING fills | filter-completeness | **FIXED (patch)** — Brake confirmed |
| 3 | DST session-date: `normalize()+fixed 24h` mislabels fall-back-Monday evening bars → wrong daily-VWAP reset, POC, prior-day levels, vault limits | corrupts Nov fall-back days + 2023–2025 data only | **PENDING** — latent, does NOT touch Jan–Jul 2026 (spring-fwd Mar 8 works; Feb all EST) |
| 4 | Same-bar entry+target books full winner on fill bar | INFLATES, RARE (needs ~12-18pt 1-min bar, stop-first-guarded) | low priority |
| 5 | Minor: `_session_date` rolls 17:00 not 18:00 (inert); commission = 2 sides on multi-leg (tiny); `require_bb_vwap` skipped when cluster_types empty (inert) | ~none | note only |

Aside: the **superseded `brake-43x58e` naive engine** (`src/backtest/engine.py` here) DOES have a real
lookahead (`resample_tf(closed="right")`). It is not the champion; ignore its numbers. Do not confuse
it with the sound `getting-started` engine.

## Fix applied this session (patches/engine-entry-timing-fix.patch)
In `getting-started` `src/backtest/engine.py`:
- Moved the working-order FILL block to AFTER the new-trigger→order block, so an order activates on
  the 1-min bar stamped == its trigger's close ts (bar `[ts, ts+1min)` — strictly after the trigger
  candle, so causal, NOT lookahead). Was 1 bar late.
- Added `avoid_entry(tod, ts)` and gated the fill path with it, so resting orders don't fill inside
  the 09:30-09:40 sit-out / VWAP-warmup / high-impact-pre-open blocks.

## Test status (getting-started): 61 pass, 4 fail — EXPECTED
The 4 failures are all E4/EC MARKET-entry tests that hard-coded the OLD 1-bar-late fill (e.g. expect
a fill at 09:49 when the trigger closed at 09:48). With the fix they correctly fill on the trigger's
own bar. **They encode the bug and must be updated to the corrected `>= ts` timing** (NOT the fix
reverted). All fill-realism tests (stop-first, trade-through, slippage) still pass — core grading intact.

## ON RECONNECT — do these, in order
1. **Apply the patch on getting-started** (or re-run this session's worktree): `git apply
   patches/engine-entry-timing-fix.patch` from the repo root of a getting-started checkout.
2. **Update the 4 E4/EC tests** in `tests/test_backtest.py` to expect the fill on the trigger's own
   bar (corrected `>= ts` timing). Re-run: expect 65 pass / 0 fail.
3. **MEASURE the champion P&L delta** (the whole point): reproduce the champion (E3 non-WAR + E4 WAR,
   first-2-by-time/day) before vs after the fix. Report Δ trades, Δ win%, Δ net$, Δ expectancy.
   Fix #1 should ADD fills (deflation removed) — verify it doesn't degrade expectancy.
4. **Angus review**: the fix changes the champion baseline (even though it's a bug fix). Show him the
   delta before it becomes "the champion." Then decide whether to push to getting-started.
5. **DST fix (bug #3)**: replace `ts.normalize() + pd.to_timedelta(roll_next, unit="D")` in
   `data._session_date` and `indicators._anchor_session_date` with a tz-naive next-calendar-day
   computation. Needed before 2023–2025 robustness runs or live past Nov 1. Add a fall-back-DST test.
6. Then resume the P1 roadmap (session-wide time gating; kill 09:15-09:45; extend past 10:15).

## Still open from earlier
- Depth pull (Angus running `pull_depth_window.py`) → re-run magnet/absorption on real Feb-Jul n.
- Rotate the Databento key pasted in chat.
