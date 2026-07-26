# GO-LIVE STATUS — the plain-language checklist (Pat's copy)

Updated 2026-07-26 (Sunday) after the first on-box session. Companion to
`docs/PROMOTION-GATE.md` (the authoritative gate list) — this file tracks where we ARE,
in order, in plain words. Update it as steps complete.

## DONE ✅

- **All code written and tested** — 622 tests green on the VPS itself (84s run).
  Order surface, cancel rules, managed exit, live scorer (row-for-row identical to the
  research books), exit binder, safety spine, kill switch, news blackout, sizing.
- **Stage 1: code deployed to the VPS** (Python 3.12, Git, repo cloned at
  `C:\ai-trading-agents`, branch `claude/getting-started-6lwnvs`).
- **Stage 2 (offline half): data pipe verified on real Sierra files.**
  - `.scid` pin check PASS — 13.7M records, order-flow volumes on every record.
  - `.depth` pin check PASS — after TWO real bugs were caught and fixed on-box:
    1. the depth Command numbering differed from the offline guess (modifies would have
       been read as deletes) — re-pinned to the build's real enum;
    2. this box writes depth prices **100× scaled** vs `.scid` — the feed now detects the
       scale from the files themselves and refuses to guess.
  - Full replay PASS: 65,970 bars + 1.2M book events → 10/10-level book at real prices,
    42-feature sample row. This is exactly why on-box gates exist.
  - Box facts pinned: depth files are named `NQU6.CME.<date>.depth` (resolver now
    auto-detects); depth recording started 2026-07-24; the `.scid` stopped updating
    Friday 11:33 ET — **keep Sierra + the NQU26 chart open continuously from tonight**.

## NEXT — TONIGHT (Sunday after 6:00 PM ET, market reopen; ~15 min total)

1. **Finish Stage 2:** measure the file-write delay on the live feed (needs data flowing):
   `python scripts\sierra_parity_replay.py "C:\SierraChart\Data\NQU26-CME.scid" --measure-lag 60`
   Record the number (want median well under a few seconds; gate B6).
2. **Stage 3: Sim-account order tests** (place/verify/modify/cancel on Sierra's SIM —
   refuses to run on any non-SIM account):
   - resting mode → gates A7 + B7;
   - `--fill` mode → gate B8 (opens+closes a small SIM position).

## THEN — WEEKDAYS (the shadow week)

3. **Stage 4: shadow run.** Fill `config/live.yaml` (Sierra data dir, account name,
   the box's depth naming) + Telegram keys in `.env`; start `python -m scripts.canon_run`.
   DISARMED — it journals every decision, places nothing. Its journals get diffed against
   the research books; that evidence closes gates A1–A6 + C6.
4. **Stage 5: break-it tests** (one session, on purpose): kill the process mid-session
   (C2), cut the feed (C3), both phones' /kill (C4), spine force-test (C5), kill the
   engine with a SIM position open → must flatten (C7).

## FINALLY — HUMANS, THEN LIVE

5. **Angus signs off** the two risk numbers: −4R daily loss, $250 drawdown buffer.
6. **Pat's written confirmation** that every PROMOTION-GATE item is green.
7. **Angus's arming token** → arm the spine on the funded Lucid account. Neither person
   can arm it alone.
8. Calendar note: **contract roll ≈ Sept 16, 2026** — watch that morning live, kill
   switch ready (gate A8 / §E).

## Known open items (not blockers tonight)

- The stored-reference depth parity day (BOX-HANDOFF C.2) cannot run: Sierra only began
  recording depth 2026-07-24 and the archived reference days are from February. The
  equivalent evidence comes from the shadow-run reconciliation diffs (A1/A2) on freshly
  captured days.
- Angus's −4R / $250 sign-off is still outstanding (values measured, units settled).
