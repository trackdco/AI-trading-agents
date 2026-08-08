# RESUME NOTE — paused 2026-08-08 mid-turn

Four-stage task. **Paused at the user's request.** Nothing is half-written to disk;
every file below is committed and pushed.

## Where it stopped

| stage | state |
|---|---|
| **1 — point-in-time audit** | **Harness run, verdict CLEAN.** Adversarial verification was launched and **STOPPED before it returned.** Stage 1 is NOT signed off |
| **2 — smoke test** | **NOT STARTED.** Gated on stage 1 |
| **3 — parity sheet** | **DONE.** `PARITY-SHEET.md` committed. Waiting on Angus |
| **4 — orderflow** | **NOT STARTED.** Independent of 1 and 2 |

## Stage 1 as it stands

`research/star-trading/tools/audit_pit.py`, 20 signal minutes spread across
2023-01-04 → 2024-12-26 and across the session (10:00, 10:30, 12:00, 14:00 buckets).
280 comparisons in `research/vwap-bb/data/audit_pit_detail.json`.

Three references per indicator per minute: **A** (bars with open ≤ T−1),
**B_full** (whole session, read at T), **A_plus1** (one bar of lookahead).

**All 14 indicators: D == A on 20/20. Zero leaks to B_full, zero to A_plus1, zero
"neither".** Structural checks: fractal confirmation PASS (a spike on the last 15m
bar is not counted as a swing until 2 more bars arrive); close-label shift PASS
(0/20 failures).

Discriminating counts — the number that decides whether a "CLEAN" means anything:

| indicator | disc vs full-session | disc vs one-bar |
|---|---|---|
| daily VWAP mid / sigma | 20 | 20 |
| NY VWAP mid / sigma | 20 | 20 |
| POC | 16 | 1 |
| session high / low | 8 / 7 | 0 / 1 |
| BB basis | 0 *(by construction)* | 12 |
| ATR(20) entry TF | 0 *(by construction)* | 12 |
| HTF classification | 16 | 0 |
| 4h range high / low | 10 / 9 | 0 |
| prior-day high / low | 20 | 0 |

Rolling indicators show 0 against full-session **by construction** — a full array
positionally indexed at T *is* the trailing window — so they are tested by the
one-bar column instead, which discriminates on 12 of 20.

## What is NOT yet established

**The CLEAN verdict has not been adversarially checked.** The workflow that was
stopped ran six refutation lenses: cross-session state, timeframe boundaries,
auditing the auditor, warm-up seeding, the outcome/excursion path, and the level
menu. Two of those matter most and neither has reported:

1. **audit-the-auditor.** `audit_pit.py` imports `htf_flag` and uses it as *both*
   the reference and the detector value, so it cannot detect a bug **inside**
   `htf_flag`. That hole is known and unresolved.
2. **the one-at-a-time gate.** `open_until = cm + hold`, where `hold` comes from
   future bars. Deciding "is a position still open at T2" legitimately depends on
   what happened between cm and T2 — knowable by T2 — but whether the
   implementation respects that boundary has not been verified.

**Do not run stage 2 until both are resolved.** A contaminated run is worse than no
run because it produces a number people defend.

## To resume

```bash
cd research/star-trading/tools && python3 audit_pit.py     # ~2 min, reproduces the audit
```

Then re-launch the verification workflow (script saved at
`.../workflows/scripts/pit-audit-adversarial-verify-wf_ec55d129-dad.js`), or check
the two holes above by hand.

Stage 4's constraint, so it is not rediscovered: MBP-10 runs Jul 2025 → Jul 2026 and
the workbench ends 2025-01-31 — **zero overlap**. 287 files are inside the sealed
holdout and unreadable; only 2026-02-01 → 2026-07-22 may be read, microstructure
only.

**N_trials: 0. Holdout: sealed, unread. No backtest has been run.**
