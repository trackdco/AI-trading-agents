# GO-LIVE STATUS — the plain-language checklist (Pat's copy)

Updated 2026-07-26 (Sunday), second pass — now merged with Angus's on-box list and the
09:55–10:00 dead-zone adoption. **ARMING REFERENCE: +$55,989.81 / 383** (corrections
1+2+3; the old +$55,617.56/386 and the 400/400 A1/A2 pass are void). Companion to
`docs/PROMOTION-GATE.md` (authoritative) — this file tracks where we ARE, in plain words.

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

## DONE ✅ (second pass, after Angus's list arrived)

- **Dead-zone adoption mirrored everywhere it must live**: the sequential scorer takes
  `dead_zones`, and the live loop now applies corrections 2+3 per verdict via
  `PremarketGuard` (news blackout + dead zone + the sentinel's fail-closed snapshot rule:
  no news board today → no pre-open entries). Wired into the shadow runner.
- **Angus item 2 PRE-VERIFIED from the stored matrices**: the full corrections-1+2+3
  construction reproduces **exactly +$55,989.81 / 383**, asserted in the test suite
  (630 tests green). The box re-run remains the certification; the number is confirmed
  reproducible.
- **Angus item 5 (boot assertions)**: Tier-1 config load+assert was already in; the boot
  **git SHA journal** is now in (`canon_run` logs + journals the commit at start, so the
  arming token can name the commit).
- **Angus item 6 (A8 statement)**: RollWatcher's exact rule = observed roll dates table
  (`KNOWN_ROLL_DATES`) when known, else Wednesday `VOLUME_ROLL_DAYS_BEFORE` days before
  3rd-Friday expiry — the Databento volume-roll pattern; a test pins the next roll to
  **2026-09-16** matching `docs/CONTRACT-ROLL-DATES.md`.

## DONE ✅ (third pass, Sunday daytime — GO-NOGO Block 1 + connections COMPLETE)

- **Telegram wired, both operators**: bot created, alerts to the shared group
  (`-5586663580`), kill authority = Pat (6920156996) + Angus (1814673340), `--test`
  delivered to both. TLS root gap on the fresh VPS fixed the clean way (certifi +
  SSL_CERT_FILE; verification stays ON). ⚠ Token was shown in a screenshot — rotate via
  BotFather when convenient.
- **News sentinel AUTOMATED (P12/A1-backup retired)**: on-box test run fetched 25 events
  ("premarket clear"), wrote the snapshot; scheduled task `NQDesk-NewsSentinel` daily at
  01:30 US Central (02:30 ET, pre-London). Fail-closed consumer wiring was already in.
- **P3 CERTIFIED ON-BOX, both halves**: `canon_news_clean` printed **+$55,989.81 / 383**
  to the cent, and the A1/A2 chain (`agent_replay --news` → `parity_harness --ref
  output/baseline_book_news.parquet`) returned **383/383 exact matches, PASS** on the VPS.
  (The chain itself was repaired first — it had still targeted the old baseline.)
- Sentinel launcher .bat committed; certifi/cloudscraper/beautifulsoup4 pinned in
  requirements (all three were on-box discoveries).

## DONE ✅ (fourth pass — ALL CONNECTIONS/SETUP COMPLETE, Sunday ~11:00 CT)

- **Nightly Sierra archive wired and scheduled**: existing B2 bucket `nq-mbo-archive`
  (config repointed), B2 keys in `.env`, dry-run listed BOTH file classes after the
  archiver's depth-glob fix (the box naming's third casualty — it was silently skipping
  every `.depth`), task `SierraArchive` daily 17:30 CT registered.
- Housekeeping owed (tomorrow, 5 min): rotate the Telegram bot token AND the B2 app key —
  both appeared in shared screenshots during setup.

## NEXT — TONIGHT (Sunday after 6:00 PM ET, market reopen; ~20 min total)

0. `git pull` on the VPS first — today's fixes + the dead-zone adoption.
0b. **Re-certify at the FINAL armed SHA (ANGUS, relayed via Pat 2026-07-26)** — the book
   regeneration is part of TONIGHT'S table even though it passed this afternoon, because
   commits landed after that run and the token names the commit:
   `python -m scripts.canon_news_clean` → **+$55,989.81 / 383 exactly**, then
   `python -m scripts.agent_replay agent_replay_news.parquet --news` →
   `python -m scripts.parity_harness agent_replay_news.parquet --ref output/baseline_book_news.parquet`
   → **383/383 PASS**. **That number goes verbatim into Pat's written confirmation.**
1. **Finish Stage 2:** measure the file-write delay on the live feed (needs data flowing):
   `python scripts\sierra_parity_replay.py "C:\SierraChart\Data\NQU26-CME.scid" --measure-lag 60`
   Record the number (want median well under a few seconds; gate B6). (Angus item 8a.)
2. **Stage 3: Sim-account order tests** (Angus items 3+4 — "nothing else matters until
   A7 is green"): place/verify/modify/cancel on Sierra's SIM — refuses non-SIM accounts:
   - resting mode → gates A7 + B7 (two distinct ServerOrderIDs back);
   - `--fill` mode → gate B8 (opens+closes a small SIM position).
3. **Angus item 2 on-box certification:** `python -m scripts.canon_news_clean` on the VPS
   must print **+$55,989.81 / 383**, then re-run the agent replay → A1/A2 certify 383/383.
4. **Angus item 5 on-box:** `python -m scripts.spine_forcetest` (corrected constants:
   clamp 40 micros, −4R halt) — every rule fires ✓.
5. **Angus item 7:** one test run of `python -m scripts.news_daily_agent` from the VPS
   (if Cloudflare blocks it, fall back to a cron on a home machine). The fail-closed
   wiring on the consuming side is DONE (PremarketGuard).

## THEN — WEEKDAYS (the shadow week)

3. **Stage 4: shadow run.** Fill `config/live.yaml` (Sierra data dir, account name,
   the box's depth naming) + Telegram keys in `.env`; start `python -m scripts.canon_run`.
   DISARMED — it journals every decision, places nothing. Its journals get diffed against
   the research books; that evidence closes gates A1–A6 + C6.
4. **Stage 5: break-it tests** (one session, on purpose): kill the process mid-session
   (C2), cut the feed (C3), both phones' /kill (C4), spine force-test (C5), kill the
   engine with a SIM position open → must flatten (C7).

## FINALLY — HUMANS, THEN LIVE

5. ~~Angus signs off the two risk numbers~~ **DONE 2026-07-26, signed in-thread**: −4R
   daily loss (indexed) + the **DD ramp** ($1,500 → $0 at $100, $100 token hard halt) which
   **replaces the $250 buffer** — shipped same day. ⚠ Tier-1 change: `dd_halt_buffer` is
   now **100** in both copies; a box `live.yaml` still saying 250 fails the boot assertion.
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
- ~~Angus's −4R / $250 sign-off~~ CLOSED 2026-07-26 — signed (−4R + the DD ramp replacing
  the $250 cliff), implemented, 632 tests green. See PROMOTION-GATE §D2 +
  `docs/RULING-daily-loss-limit.md` "The ramp".
