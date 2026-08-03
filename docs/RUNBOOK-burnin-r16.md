# RUNBOOK — R16 certification: 24/7 operational resilience (Pat, on the VPS)

Two armed sessions (2026-08-02 evening, 2026-08-03 morning) both found the DTC order
socket dead on the first real order — the connection had no idle keepalive, so a quiet
market let it die unnoticed for hours. Root cause, fix, and four related gaps are closed
in commit history following `f6b297e` (see `docs/ARMING-REFERENCE.md` row R16 for the
full list). This is the certification path before the NEXT arm — no replay cert alone
proves the fix, because the failure only exists in real idle time.

## 0. Nothing armed right now

Do not touch anything currently running. This runbook is for the NEXT session, not this
one. If a loop is currently armed and idle, leave it — these fixes land in a fresh pull
before the next `--arm`, same as every other certification this weekend.

## 1. Pull + full suite (expect ~836 passed, 2 known unrelated failures)

    cd C:\Users\Administrator\AI-trading-agents
    git pull origin claude/agents-capture-handoff-26rnvp
    python -m pytest -q

## 2. Re-run the R13/R15 practice-day replay (fresh evidence — execution code changed)

Six files that sit on the order/execution path changed tonight
(`scripts/ny_run.py`, `src/desk/dtc_broker.py`, `src/live/agent_desk.py`,
`src/live/arming.py`). The R13/R15 certification evidence predates all of it — get fresh
evidence the mechanical + agent path is still clean before layering the new resilience
fixes on top:

    Rename-Item output\live\ny ny_r16_pre
    python -m scripts.ny_run --dryrun --replay-day 2026-07-29 --agents

PASS = same bar as every prior cert: zero wrong-side stops, zero orphaned fills, zero
`dispatch_error`, agent journal rows schema-clean. If this isn't clean, stop here and
report back — nothing below matters until this is.

## 3. Telegram — wire it up and prove it (10 minutes)

You need a bot token and your chat ID once, ever:

1. In Telegram, message **@BotFather** → `/newbot` → follow the prompts → copy the token
   it gives you (looks like `123456789:AAdefgh...`).
2. Message **@userinfobot** (or your new bot after step 3) to get your own numeric chat ID.
3. On the VPS, open (or create) `.env` in the repo root and add two lines:

       TELEGRAM_BOT_TOKEN=<the token from BotFather>
       TELEGRAM_CHAT_ID=<your numeric chat id>

4. Prove it works before trusting it in a live session:

       python -m src.live.telegram --test

   You should get a message on your phone within seconds. If not, the command tells you
   which of the two values is wrong — fix and retry until it says `sent`.

## 4. The DTC connectivity burn-in — the real proof

This is a **new, separate tool** built tonight specifically because no replay can
reproduce hours of real idle time. It connects to Sierra's live DTC server and proves
the reconnect fix survives real time — **it never imports the order-submission code at
all**, so it cannot place, modify, or cancel anything, on any account, by construction.
Safe to run any time Sierra is up, armed or not.

    python -m scripts.dtc_connectivity_check --hours 4

Run it across a stretch that includes at least one full daily maintenance break
(5–6 PM ET) if you can — that's the single quietest, most failure-prone window and
exactly what bit you twice. Let it run genuinely unattended; don't touch the terminal.

**PASS** = it completes the full window and prints:

    drops detected: N   healed: N   unhealed at end: 0
    PASS

Any `unhealed at end: 1` or a `FAIL` line means the fix isn't proven yet — screenshot
the tail of the output and stop; do not proceed to arming.

If Sierra's DTC connection genuinely never drops during your window, that's a valid
(if less conclusive) PASS too — it means either the box's environment is fine right now
or the window was too short to hit whatever killed it before. Longer is more convincing;
a run spanning a full overnight or the weekend is the strongest evidence.

## 5. The watchdog — dry-run before trusting it unattended

`scripts/watchdog.ps1` is new and has NOT been exercised on the real box yet. Setup and
a careful first test, from an Administrator PowerShell:

    [Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "<token>", "Machine")
    [Environment]::SetEnvironmentVariable("TELEGRAM_CHAT_ID", "<chat id>", "Machine")

Decide on ARM_TOKEN persistence now — this is the one real security tradeoff in this
batch, made explicitly, not by default:

  * **Skip this and the watchdog stays alert-only** (pages you if ny_run dies, but
    won't restart it without you typing the phrase) — safer, recommended until you've
    watched the watchdog behave correctly at least once.
  * **Set it and restarts are fully automatic:**

        [Environment]::SetEnvironmentVariable("ARM_TOKEN", "<the phrase>", "Machine")

    Anything with access to this Windows account can now read the phrase from the
    environment. Only do this if you've decided that tradeoff is worth full autonomy.

Restart the terminal after setting anything (env vars set this way don't apply
retroactively), then dry-run it manually a few times BEFORE scheduling it:

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\watchdog.ps1

With nothing running and no KILL file: if ARM_TOKEN is set, it should start ny_run and
message you; if not, it should message you that manual arming is needed and do nothing
else. Check `output\live\watchdog.log`. **Then test the kill-file override explicitly**
— create `output\live\KILL`, run the watchdog again, confirm the log says "standing
down" and NOTHING starts. This is the one behavior that must never fail.

Only once both of those look right, register the scheduled task (see the header comment
in `scripts/watchdog.ps1` for the exact `Register-ScheduledTask` commands).

## 6. Push everything for the verdict

    git add -f output/live/ny output/live/ny_r16_pre
    git commit -m "R16 burn-in evidence - DTC connectivity + telegram + watchdog dry-run"
    git push

Include in the push message (or tell me directly) the connectivity burn-in's summary
block and how the watchdog dry-run went.

## 7. After PASS

Same two-party close as every gate before this one: I read the evidence, cut the
certified commit, you send Angus written confirmation naming the new SHA (mechanical +
agent + R16 resilience), he re-issues `config/arming.yaml` (this commit already voids
his current one, same as R15 voided R13's) with the phrase, then — and only then — arm.
