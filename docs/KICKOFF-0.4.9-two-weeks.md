# KICKOFF — 0.4.9 over both weeks, on the CHARTS

**His ruling, 2026-08-17, and it decides the venue:**

> *"That's why it's probably more important to do it via the TradingView MCP,
> because on a live chart they're going to be looking at the TradingView
> charts… they will be able to read the chart, which is the point."*

Correct, and it retires the idea of validating this offline. Chart-reading is
part of how the stack trades, so a book produced without a chart is not the
book being shipped. **Both runs go through the TradingView MCP.**

**His acceptance test, in his words:** *"If I can look at the trades and
think, 'Yes, these are trades that I would take,' then I'm happy to ship
that. I don't need an out-of-fit test… I care about it executing, like how I
execute trades."* So the deliverable is a trade-by-trade sheet he can read,
not a scoreboard.

---

## WHAT TO RUN

Two re-runs of days already run under older contracts, so the comparison is
contract-vs-contract on identical tape:

| run prefix | session-days | what it is |
|---|---|---|
| `w49` | 2026-06-21 … 2026-06-25 | the NARRATED week — doctrine was built on it |
| `j49` | 2026-05-31 … 2026-06-04 | June week 1 — the stack had never seen it |

Both prefixes are fresh. **Never reuse a prefix** (runbook §4 — `r2` is burned
twice and any tool scanning by prefix now mixes two eras).

## WHAT CHANGED SINCE THOSE DAYS WERE LAST RUN

**`tv-trigger` is now 0.4.9.** Two additions, both requiring a new briefing
field. The contract will not behave correctly without them.

1. **0.4.8 — FRESHNESS CAPS THE GRADE.** Only a level being traded for the
   first time this session (and tested at most twice on the 15m in the last
   hour) may grade **A**; a stale level tops out at B; a third visit caps at
   C. It caps the GRADE, never the licence — T48 re-entry stays licensed, it
   just no longer comes at A size.

   Requires `level_visits_this_session` in every trigger briefing:

   ```bash
   python -m scripts.level_visits <sess_day> <HH:MM> \
       --level <rejected_level_price> \
       --prior-take <HH:MM>=<price> ... --json
   ```

   Pass every PRIOR TAKE of the session. Passes are not visits. A candidate
   re-adjudicated after an escalation is ONE take, not two.

2. **0.4.9 — CHOP IS A MAP.** When the session is in a small sustained range,
   the licensed trade is from an EDGE toward the opposite side, targeting the
   structural level near it (his words: *"not necessarily the high — we still
   target our structural levels"*). The middle stays dead. A range fade from
   an edge is NOT counter-trend and must not cap at C.

   Requires `chop_state` in every trigger briefing (and it is worth putting
   in the thesis briefing too):

   ```bash
   python -m scripts.chop_state <sess_day> --at <HH:MM> --json
   ```

   His definition, hard-coded: a small range (bottom quartile of the normal
   3-hour NQ range, ~104pt, measured across 44 days) held for ~3 hours.
   Returns `state` (CHOP/TRENDING/FORMING), `range_high`, `range_low`,
   `middle_band`, `zone_now`.

**Both are MECHANICAL FACTS under §0c.** The orchestrator computes and states
them; it never decides from them and never editorialises. Run the scripts —
do not work either out by hand.

## WHERE THE LOGS GO — read `output/books/README.md`

**Not `output/agent_runs/`.** That directory is deny-listed for Read on
purpose, so a run cannot read other runs' outcomes, and it stays that way.
Write the live books to:

```
output/books/w49/<sess_day>_w49.jsonl
output/books/j49/<sess_day>_j49.jsonl
```

which is readable — so every row can be verified, audited and resumed as it
is written. `git add -f` still applies (`output/*` is gitignored).

**When a run is complete, scored and committed, MOVE its logs into
`output/agent_runs/`.** That seals them as outcome data for good.

## MODEL

**Run all four agents on Sonnet.** His instruction, and his reasoning:
*"Sonnet 5, for something like this, is good because it obviously doesn't
think as complexly as Opus and Fable, but it comes to decisions a lot quicker
because of that. For something like this, you don't need deep, complex
thinking."* Record the model in each row so the book is attributable — the
two weeks being compared against were produced by a different model, so if
the books diverge, model is a candidate cause alongside the contract change.

## EVERYTHING ELSE IS UNCHANGED

Same runbook, same windows, same caps (lifted, tagged `beyond_written_cap`),
same leak checks, same per-day audit, same day-end sequence. In particular
the capture sequence that was hard-won on day 3 still applies:
`replay_start(dec:00-04:00)` → `replay_status` → **clear the crosshair** →
`capture_screenshot` → `data_get_study_values` → `verify_legend.check(...)`.

His standing rules all hold: never block overnight (§2d — conservative
default, `open_question` row, keep running), the orchestrator has no trading
discretion (§0c), and the weekly-anchor gate is a hard per-day stop.

## THE DELIVERABLE

Not a scoreboard. A **trade-by-trade sheet** he can scroll through against
his own chart, per run:

- every FILL: time, side, entry, stop, targets, conviction grade, and the
  agent's own `reason` verbatim;
- what management did and why, in its own words, at each call;
- the exit and its reason;
- every PASS with its reason — the passes are where he has caught the most;
- and for each, the `chop_state` and `level_visits` that were in force, so
  the two new rules can be judged on the trades they actually touched.

He reads it and answers one question per trade: **would I have taken this?**

## WHAT THE OFFLINE WORK IS STILL FOR

Not this. The offline harness cannot show an agent a chart, so it cannot
answer his question. What it does provide, and what these runs consume:

- `scripts/chop_state.py` and `scripts/level_visits.py` — the two new
  mechanical facts above;
- `scripts/certify_offline_briefings.py` — proves the BUILD numbers in a
  briefing reproduce exactly from committed bars (100% on the current era);
- `scripts/gate_offline_causality.py` — adversarial no-lookahead proof for
  every offline-computed field: recompute after replacing the future with
  garbage, demand bit-identical output;
- `scripts/offline_scan.py` — reproduces 100% of the candidate minutes his
  Mac adjudicated, so a day's candidate list can be checked against the
  scanner if one looks wrong.
