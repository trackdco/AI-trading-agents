# RUNBOOK — replaying a specific time and scoring "does it trade like me"

The procedure the **local session** (orchestrator) runs to replay a chosen
day through the `tv-*` agent stack and score it against the trader's own
recorded decisions. This is the pure focus: **replay from a specific time,
and see if the agents actually trade like him.**

Doctrine: `docs/PLAYBOOK.md`. Agent contracts: `.claude/agents/tv-*.md`.
Tool reference: `docs/TOOLS-tradingview-mcp.md` (vendored from the MCP).
Every implementation fact below was read from the MCP source
(`src/core/replay.js`, `src/core/data.js`, `src/core/capture.js`) on
2026-08-11 — none of it is guessed.

---

## 0. WHAT THE REPLAY TOOLSET ACTUALLY IS — read before planning around it

| tool | what the source says it does |
|---|---|
| `replay_start {date}` | enters replay at a date. Schema says `YYYY-MM-DD`, but the implementation runs `new Date(date)` and only rejects `NaN` — **a full ISO datetime works** and is passed to TradingView's `selectDate(ms)`. Fails outright if replay is unavailable for the symbol/TF or the date has no data. |
| `replay_step` | advances **one bar of the current chart timeframe** (2m chart → one step = 2 minutes). Polls up to 3s for the cursor to move. |
| `replay_autoplay {speed}` | toggles autoplay. Speeds are a **hard whitelist**: 100, 143, 200, 300, 1000, 2000, 3000, 5000, 10000 ms. The server rejects anything else *because an invalid value permanently corrupts TradingView cloud account state* — never improvise a speed. |
| `replay_trade {action}` | **market buy / sell / close. Nothing else.** No quantity, no limit orders, no stops, no targets. |
| `replay_status` | `current_date`, started/autoplay flags, `position`, `realized_pnl`. |
| `replay_stop` | back to realtime. |

Two consequences that shape everything below:

1. **His entries are limit-on-retest; the MCP's replay tool surface is
   market-only — but the product underneath is not.** TradingView's replay
   trading natively supports **limit / stop / stop-limit orders and TP/SL
   brackets** (support doc 43000691889; brackets announced on their blog).
   The MCP wraps only five methods of `window.TradingViewApi._replayApi` and
   never mapped the order ticket. The decisions ARE limit orders — price,
   expiry, cancel rule, fill at the limit — and two paths exist to execute
   them:
   - **Native — probed, and CLOSED (2026-08-11, first local session).**
     `scripts/probe_replay_api.mjs` ran both passes on the live app — normal
     chart, then inside replay with the trading panel open immediately after
     a hand-placed fill and cancel. **Empty both times** (the only regex hits
     were `stopReplay`). The native ticket exists in the UI but exposes no
     scriptable order API where CDP can reach. Do not re-run the probe hoping
     — the simulated path below is THE path unless TradingView ships a new
     API surface.
   - **Simulated, otherwise.** The **orchestrator runs the limit lifecycle**
     (placement, expiry, cancel rule, fill detection) against replayed bars,
     and the JSONL log is the authoritative record. **Make the limit VISIBLE
     while it rests**: on placement, `draw_shape` a horizontal line at the
     limit price with a text label (`SHORT LMT 29,492.75 · expires 04:16`);
     on cancel, remove it and log why; on fill, remove it, mirror with a
     `replay_trade` market order at the fill bar so the position shows on the
     chart, and mark the entry. He watches limits rest, die, and fill —
     which is the point.
   Either way TradingView's `position`/`realized_pnl` does not reflect limit
   fills exactly — **never score from TradingView's replay P&L. Score from
   the log.**
2. **Stepping is the precision instrument; autoplay is for watching.** Use
   `replay_step` for everything scored. Use autoplay at 1000–3000ms only for
   his live-viewing sessions, and pause it (toggle) at every candidate.

## 0b. LANDING AT A SPECIFIC TIME — the timezone trap

`new Date("2026-06-25")` is **UTC midnight** = 20:00 NY the previous evening.
`new Date("2026-06-25T03:00:00")` is **the Mac's local timezone**. Neither is
guaranteed to be what TradingView's `selectDate` snaps to on a 2m series.

So never trust the landing:

1. `replay_start` with an explicit-offset ISO string a comfortable margin
   **before** the first minute you care about — e.g. for London of session-day
   2026-06-25, `date: "2026-06-26T02:30:00-04:00"` (30 min early). The
   explicit offset is non-negotiable everywhere: measured 2026-08-11 on a Mac
   running AEST (+10), where an offsetless datetime lands 14 hours away.
2. `replay_status` → read `current_date`. **`replay_start`'s own return can
   carry stale state** (measured: it reported the pre-jump cursor); the
   status call after the jump is the real read, always.
3. `data_get_ohlcv {summary: true}` → read `period.to` (last bar time).
4. If short of the target, `replay_step` forward — never land long and hope.
   If you overshoot the target, **restart replay earlier**; there is no step
   backwards. Re-verify after every correction.

**Candle times are START times on the chart** (his 04:04 2m candle closes at
04:06, which is the decision minute). The orchestrator owns this conversion
and must double-check it at the first candidate of every run.

---

## 0c. SEPARATION OF POWERS — the orchestrator has NO trading discretion

His ruling, 2026-08-13, and it is the strictest rule in this document:

> *"Please make sure that is agent-run, the orchestrator, as in my terminal.
> Claude is not fucking steering it or doing any of that bullshit."*

He is not describing a preference. A previous week had to be thrown away and
re-run because the orchestrator put commentary into an agent's context. **The
orchestrator is a machine that moves the chart, computes numbers, calls agents
and writes rows. It has opinions about none of it.**

| the ORCHESTRATOR decides | the AGENTS decide |
|---|---|
| where to land replay, and verifying the landing | direction and bias |
| whether a bar meets the **mechanical** candidate definition | take_full / take_light / pass |
| which levels and values go in a briefing (all of them, unfiltered) | conviction grade |
| whether a management minute occurred (level reached / broken / TP1 / stall) | entry price, stop price, targets |
| whether a limit filled, expired or cancelled, per the stated rules | every management action |
| that a stop only ever tightens | whether the thesis is stale |
| the window bounds, the caps, the news gate | whether to go again after a stop-out |
| logging every row, including the passes | |

**The four abuses, named so they cannot happen by accident:**

1. **Never override a verdict.** If a `pass` looks wrong to you, log it, and
   raise it with him **after** the run. The wrong trade, correctly adjudicated,
   is data. The right trade, orchestrator-inserted, is nothing.
2. **Never re-ask a question you did not like the answer to.** Calling
   `tv-trigger` a second time on the same candidate with a re-worded briefing is
   steering even when every fact in it is true. One candidate, one call. The only
   licensed second call is the escalation loop the contract itself defines, fired
   by the agent's own `thesis_stale`, never by you.
3. **Never editorialise in a briefing.** Free text in a briefing must be
   mechanically derivable — `"15m MA crossed at 09:42"` is a fact,
   `"this looks like a strong setup"` is a vote. No prose from any doc, no
   summary of the chart (the agent reads the screenshot itself), no mention of
   any other day, no count of how many candidates the day holds.
4. **Never let a decision be shaped by anything you learned after it.** You
   see the whole day; the agent sees one moment. That asymmetry is the entire
   reason you must not weigh in.

**One mechanical exception to "one candidate, one call": schema validation.**
An output missing a required field — a take without `retest_level`,
`cancel_if_reaches`, `stop` or `targets`; a manage row without `action` — gets
ONE re-invoke with the **byte-identical briefing** plus a single line naming
the missing fields. That is repair of a malformed answer, not a re-ask: the
briefing must not change by one byte, and the row records
`validation_retry: true`. This exists because a scored run logged four takes
with null `retest_level`/`cancel_if_reaches`, which made the cancel-at-TP1
rule unenforceable for the window that produced most of the day's R.

**And the same applies to him.** He watches these runs live. Anything he says in
the terminal that reads as an opinion on a pending decision is to be **ignored
and named** — *"that sounded like steering, I'm not passing it on"* — because on
live he will not be there to say it, and a week scored with his voice in the
briefings measures nothing. Between decisions, his rulings are welcome and become
teaching-loop entries; inside one, they are contamination.

---

## 1. PHASE R0 — GATES (once per replay session)

1. `tv_health_check` → `cdp_connected` and `api_available` both true.
2. `chart_get_state` → confirm symbol (his NQ contract) and 2m timeframe; log
   both into the run header. Run `chart_get_state` **once** and cache entity
   IDs — they are session-specific.
3. **Timezone fix.** `data_get_ohlcv {summary: true}` in realtime; reconcile
   the last bar's timestamp against the wall clock to establish the chart's
   TZ offset. Log it.
4. **Indicator parity** (spec Phase 0.3): step replay to a known minute of a
   narrated day, read the BB MAs and VWAP off the chart
   (`data_get_study_values`), then
   `python -m scripts.phase0_parity <sess_day> <HH:MM> --vwap ... --bb-ma-2m ...`
   — it exits 1 on FAIL. **>1pt VWAP / >0.5pt BB MA = stop and say so.**
5. **NO-LEAK CHECK** (spec Phase 0.4 — the one that matters most): at the
   landing minute, `data_get_ohlcv {summary: true}` and verify
   `period.to` ≤ the replay cursor, and `capture_screenshot` and verify no
   bars print right of the cursor. `data_get_ohlcv` reads the chart's own
   bar series, which replay truncates at the cursor — so the check is cheap
   (~500 bytes) and mechanical. **Re-run it after every landing, every
   restart, and every timeframe switch, and record `leak_check: pass` in
   every decision row.** A decision made on a chart showing later bars is
   worthless and the error is invisible in aggregate.

**Replay depth is plan-gated.** If `replay_start` on the 2m errors with "the
selected date may not have data for this timeframe", the intraday replay
window on his plan does not reach that day. Report exactly that; do not
silently fall back to a higher timeframe — a 15m replay cannot adjudicate a
2m doctrine.

## 2. PHASE R1 — CONTEXT AND FIRST THESIS (per session-day)

At the landing minute (before the window opens):

0. **THE WEEKLY-ANCHOR GATE — hard, per day, before anything else** (his
   ask 2026-08-15, after the anchor failed twice — once ~900pt out at the
   POC, once a Monday anchored to the prior Thursday):

   ```bash
   python -m scripts.gate_weekly_anchor <sess_day> --minute <landing HH:MM>
   ```

   Exit 1 stops the day, same standing as a parity FAIL — weekly edges are
   the only levels that grade A alone, so a day run on a wrong anchor is not
   worth scoring. The gate re-derives the expected anchor from pure calendar
   arithmetic (this cash-week's Monday 18:00 NY; a Monday cash session falls
   back to the prior Monday), compares it to what `agent_context` actually
   used, and verifies bars exist AT the anchor so the profile cannot
   silently start at whatever data happens to be loaded. After the first
   trigger briefing of the day is written, run it once more with
   `--briefing <path>` so the builder's weekly numbers are cross-checked
   against the recompute. When he has hand-anchored the chart drawing, pass
   `--chart-poc/--chart-val/--chart-vah` for the advisory visual check
   (never a hard fail — the ~30pt binning residual is documented and the
   chart wins).

1. Build the day context: `data_get_ohlcv` (count sized to cover 18:00 → now;
   465 2m bars covers 18:00→09:30, within the 500 cap), plus
   `scripts/agent_context.py` values for prior-day / weekly levels.
   The chart remains the source of truth for anything it can state
   (`data_get_study_values`, `data_get_pine_lines` / `_labels` for his
   Pine-drawn levels); the research build fills what the chart doesn't expose.
   **Both value areas, always** — daily and anchored weekly, labelled.

   **The anchored weekly profile is a MANUAL daily drawing, his ritual:**
   he re-anchors it each session-day to the Asia open (18:00 NY) of the same
   weekday one week back — which is exactly what
   `agent_context.anchored_weekly_profile` computes, in his own quoted words.
   The briefing numerics therefore never depend on the drawing existing. But
   when he is present (every replay run), have him anchor it on the chart
   before the window and re-screenshot, so the thesis agent's visual matches
   what he would actually be looking at. Unattended sessions run on the
   computed values alone; that is fine and expected.
2. Build the macro briefing **as-of**: `data/reference/news_archive.csv`
   filtered to `datetime_ET <= decision_minute`. Call `tv-macro-events`.
3. `capture_screenshot {region: "chart", waitForRender: true}` → PNG path.
4. Call `tv-thesis` with `event_trigger: "window_open"`, the screenshot path,
   the numeric context, and the macro output. Log the thesis JSON.


## 2b. TRIGGER-DRIVEN REPLAY — his actual workflow, and it is leak-safe

**Do not step every bar.** His ruling, 2026-08-13: *"For me when I'm replaying a
session, I will yes skip through the minutes where there's no action, but as
soon as a trigger comes I make a judgement call there in a couple of minutes. I
don't need the agents to go proper minute by minute — I want them to replicate
how I would do replay. I can get through a week in 30 minutes."*

**Why this is not a shortcut that costs rigour.** The candidate scan is
mechanical: the trigger definition applied to committed bars. Knowing *a
candidate exists at 09:36* says nothing about its outcome — it is exactly the
information his eye gets while scrubbing. The agent still sees a chart truncated
at its own decision minute, and the no-leak check still runs at every landing.

**The loop:**

1. **Pre-scan the session-day** with the candidate scanner: every 2m/3m
   two-level close, every rejection-first shape, plus the thesis re-fire events
   (window opens, 15m MA closes, displacements, extremes taken out). Produces an
   ordered list of decision minutes.
2. **Jump replay to each decision minute in turn** (`replay_start` with an
   explicit `-04:00` offset, then `replay_status` to verify — the start call
   returns stale state). Run the no-leak check at every landing.
3. **Adjudicate** exactly as before: screenshot, briefing, `tv-trigger`.
4. **While a position is open, jump to the next MANAGEMENT minute** — the first
   bar that reaches an intermediate level, breaks one, hits TP1, or stalls, all
   computed mechanically from bars. Call `tv-manage` there. Repeat until the
   position resolves.
5. **Never jump past an open position's resolution.** Everything else is dead
   time and may be skipped.

**The one guard:** briefings stay strictly per-decision. The thesis agent must
never be told how many candidates the day holds or when the later ones fall —
that is forward information about activity, even though it carries no outcome.
The orchestrator holds the list; the agents see one moment at a time.

## 2c. THE MANAGEMENT TIER — `tv-manage`

Added 2026-08-13 after a scored week in which **11 of 12 losses were clean
−1.00R full stop-outs.** Management had been mechanical clauses fired by the
orchestrator; he described it as a judgement: *"I trail, take targets, and do
these things based on how the trade is favouring me in the moment. That's gotta
be an intra-trade judgement call."*

`tv-manage` is called at `intermediate_level_reached`, `intermediate_level_broken`,
`tp1_reached`, `stalling`, `pre_cash_open` and `window_closing`. It returns
`hold` / `breakeven` / `trail` / `partial` / `exit_now`, and the orchestrator
enforces the one hard invariant: **a stop only ever tightens.** Log every call
and every verdict, including the `hold`s — an unmanaged loser is now a defect
worth seeing in the report.

**A second same-direction setup while a position is IN PROFIT is a scale-in,
not a new trade (T53).** `tv-trigger` adjudicates the fresh candidate as
normal; on a take verdict **graded B or better**, the orchestrator routes
execution to `tv-manage` as `reason_for_call: second_setup` — a smaller clip
added to the open position, the whole position's stop moved to the new setup's
invalidation, ONE position in the log, and **no window slot consumed**. His
review of a scored pair four minutes apart, same direction, same rejected
shelf: *"If that setup fired on the three-minute with that many confluences, I
definitely would have scaled my position there."*

Two exclusions: a position not in profit never takes an add, and a **C-grade
second trigger is confirmation, not an add** (T53 rider) — route it to
`tv-manage` as `second_setup` anyway so the confirmation is on the record, but
the contract holds with the original stop untouched: *"If it's a C-grade
conviction, don't trail that. I'd rather just hold to my high-conviction
stops."*

**THE FLIP (T68) — opposite direction, defended-level licence.** When a
candidate fires OPPOSITE an open position AND the standing thesis's
`defended_level` + displacement satisfy the T67 licence (level with memory,
tested-and-failed, displacement through band + MA away from it), the
open-position gate does NOT apply: adjudicate the candidate with `tv-trigger`
as normal, flagging `flip_candidate: true` in the briefing (a fact, not a
vote). On a take verdict the orchestrator FLATTENS the open position at the
decision price (`exit_reason: "flipped"` on its exit row) and runs the new
limit lifecycle. **The flip outranks a T48 same-direction re-entry at the
same level** — check the flip before re-entering.

**T68 WIDENED (his ruling, 2026-08-16).** The defended-level licence is no
longer required. He allows the flip on the trigger's own comparative
judgement: *"make sure it can also flip trades and stuff as well… If it
thinks the short setup looks better than the long setup, then take the short
flip positions right there. Close the long. Set the limit order for the
short. Make sure that is a rule because I have allowed that."* So: ANY
candidate firing opposite an open position is a flip candidate. The briefing
flags `flip_candidate: true` and states the open position as a fact; the
agent adjudicates the new setup on its merits. On a take the orchestrator
FLATTENS the open position at the decision price (`exit_reason: "flipped"`)
and runs the new limit lifecycle. On a pass the open position simply stands.
The superseded sentence read "a flip is never available merely because an
opposite candidate looks good" — that is exactly the case he has now allowed.

**THE FLIP AND THE WRITTEN CAP (his ruling, 2026-08-16).** A flip does NOT
consume a fresh window slot. *"ny can have a cap of 2 if its flipping into a
trade it believes will payoff better. id disregard the first trade in that
instance for that."* The position that was flipped OUT is disregarded when
counting fills against the written cap — the flip inherits its slot rather than
taking a new one, the same way a T53 scale-in consumes no slot. Its realised R
still scores in full: a flipped-out loss is a real loss and is never dropped from
the scoreboard. Only the CAP ACCOUNTING disregards it.

## 2d. NEVER BLOCK ON HIM. The overnight rule.

**2026-08-16, after a session ran two days and then sat idle all night
awaiting a "ruling" that, when he asked, it admitted it did not need.** An
unattended run that stops to ask a question has not been careful — it has
destroyed the night, which is the only time these runs get to happen.

**A run NEVER halts for input. There are exactly three hard stops** (parity
FAIL, an unclearable no-leak check, a contract-version mismatch) and they
are data-integrity stops, not questions. Everything else continues.

When something genuinely needs his judgement mid-run:

1. **Apply the conservative default and carry on.** The conservative default
   is always the one that changes nothing: the existing rule as written, the
   more restrictive reading, or — where a candidate cannot be adjudicated
   without an answer — log it `pass` with `reason: awaiting_ruling`.
2. **Log an `open_question` row** in that day's log: what was asked, what
   default was applied, which rows it touched.
3. **Keep running.** Later days use the same default, so the month stays
   internally consistent.
4. **Surface every open question in the morning report**, together. He rules
   in one pass; anything affected is re-run then, cheaply, because the rows
   are flagged.

**Before pausing for any reason, ask: is this a data-integrity stop?** If
not, it is an `open_question` row and the run continues. A night that
produces twenty days plus four flagged questions is worth more than a night
that produces two days and a polite request.

**A second same-direction setup while a position is IN PROFIT is a scale-in,
not a new trade (T53).** `tv-trigger` adjudicates the fresh candidate as
normal; on a take verdict **graded B or better**, the orchestrator routes
execution to `tv-manage` as `reason_for_call: second_setup` — a smaller clip
added to the open position, the whole position's stop moved to the new setup's
invalidation, ONE position in the log, and **no window slot consumed**. His
review of a scored pair four minutes apart, same direction, same rejected
shelf: *"If that setup fired on the three-minute with that many confluences, I
definitely would have scaled my position there."*

Two exclusions: a position not in profit never takes an add, and a **C-grade
second trigger is confirmation, not an add** (T53 rider) — route it to
`tv-manage` as `second_setup` anyway so the confirmation is on the record, but
the contract holds with the original stop untouched: *"If it's a C-grade
conviction, don't trail that. I'd rather just hold to my high-conviction
stops."*

**THE FLIP (T68) — opposite direction, defended-level licence.** When a
candidate fires OPPOSITE an open position AND the standing thesis's
`defended_level` + displacement satisfy the T67 licence (level with memory,
tested-and-failed, displacement through band + MA away from it), the
open-position gate does NOT apply: adjudicate the candidate with `tv-trigger`
as normal, flagging `flip_candidate: true` in the briefing (a fact, not a
vote). On a take verdict the orchestrator FLATTENS the open position at the
decision price (`exit_reason: "flipped"` on its exit row) and runs the new
limit lifecycle. **The flip outranks a T48 same-direction re-entry at the
same level** — check the flip before re-entering. Absent the licence, the
open-position gate stands as before; a flip is never available merely because
an opposite candidate looks good.

## 3. PHASE R2 — THE BAR LOOP (per window)

Step one 2m bar at a time through LONDON 03:00–04:59 / NY_PRE 08:00–09:29 /
NY_AM 09:30–11:00. After **every** step:

1. `data_get_ohlcv {summary: true}` → last bar (also the leak check).
2. **Candidate detection is the orchestrator's, mechanical, on chart bars** —
   not the precomputed census (it is a research artifact and known to miss
   real entries). A candidate exists when a 2m or 3m candle closes through
   its **own BB(20) MA** and a second level (VWAP band / POC / profile edge —
   rejection counts). Lone MA closure = pending, live for `SEQ_CANDLES = 3`.
   Levels come from `data_get_study_values` at that bar. The 3m read needs a
   TF switch or a 3m pane — establish which on his layout in R0, and re-run
   the leak check after any TF switch.
3. **Thesis re-fire events** (extreme taken out, 15m MA close-through,
   displacement ≥ 0.5·W15, rebalance completes, TP1 fills, destination
   prints): pause, screenshot, re-call `tv-thesis` with the event named.

   **Plus, from 0.4.2 (T68): the `other_side_tripwire` is a SENSOR.** Every
   thesis that emits one gets it checked mechanically at every candle close;
   the moment the named level+event resolves, re-fire `tv-thesis` with
   `event_trigger: "other_side_tripwire_resolved"` — do not wait for a
   candidate to wander in and escalate. A branch the thesis wrote down and
   was re-read 24 minutes late cost a scored week −2R plus its best trade.
4. **At each surviving candidate**: freeze (no stepping), screenshot, build
   the trigger briefing (thesis + candle payload + `fills_this_window` +
   headroom fields + macro gate), call `tv-trigger`. Log the full verdict —
   takes AND passes. **The passes are the valuable rows.**

   **The briefing must carry the HIGHER-TIMEFRAME behaviour at the rejected
   level** (trigger contract 0.4.2, T46). Without it the agent cannot tell his
   highest-conviction shape — 2m closing both sides while the 15m prints a wick
   that cannot close through — from a level that actually failed, and will grade
   the best setups of the day as C.

   **Do not compute this by hand.** It is the input to a conviction grade, so it
   has to be identical on every day and every run, and under §0c the
   orchestrator supplies mechanical facts, never judgements — an ad-hoc count is
   a judgement wearing a number's clothes. Run:

   ```bash
   python -m scripts.htf_level_behavior <sess_day> <HH:MM> \
       --level weekly_val=29693.61 --level poc=29821 --json
   ```

   and paste the JSON into the briefing under `htf` per level. It reports, per
   timeframe (2m/3m/5m/15m): tests, closes each side, max wick and max **body**
   beyond, the side price approached from, and a verdict. Two windows, and they
   answer different questions — the last 60 minutes is the CURRENT test and is
   what grades the shape; `session_closes_above/below` is whether the level has
   already been sliced today, which is conviction rubric point 4.

   It truncates per timeframe at the last candle whose CLOSE is at or before the
   decision minute — a 15m candle that opened at 03:30 is not complete at 03:40
   and including it would leak the future into the field the grade comes from.

   **Three more briefing fields, from 0.4.2/0.4.7 (T67/T68 + the cat-3 gaps),
   computed by `python -m scripts.context_extras <sess_day> <HH:MM> --json` —
   never by hand:**

   - `nwog` — the New Week Opening Gap: prior Friday's 17:00 close and this
     week's 18:00 Sunday open, both edges plus filled-or-not as of the
     decision minute. Both prices are given raw — his convention decides
     which edge matters; the briefing takes no position.
   - `swept_lows` / `swept_highs` — prior swing extremes taken out this
     session, each with the sweep time and whether price closed beyond or
     reclaimed. "We've taken out that low" is a cause in his reasoning; the
     agents cannot cite what they cannot see.
   - `chop_state` — **required by tv-trigger 0.4.9.** His definition of a
     choppy market, computed by `python -m scripts.chop_state <sess_day>
     --at <HH:MM> --json`: a small range (bottom quartile of the normal 3-hour
     NQ range, ~104pt) that has held for hours. Supplies `state`
     (CHOP/TRENDING/FORMING), `range_high`, `range_low`, `middle_band` and
     `zone_now`. A mechanical fact under §0c — the orchestrator computes and
     states it, never decides from it. It is a LICENCE to trade the range
     edge-to-edge, never a veto, and the trigger contract owns what to do
     with it.

   - `level_visits_this_session` — **required by tv-trigger 0.4.8.** For the
     candidate's own rejected level: how many takes have already been
     adjudicated at that level this session (the current one counts, so a
     first trade reports 1), plus its 15m test count in the 60-minute window.
     Computed by `python -m scripts.level_visits <sess_day> <HH:MM> --level
     <price> --prior-take <HH:MM>=<price> ... --json`, never by hand — it
     grades conviction, so under §0c it is a mechanical fact the orchestrator
     supplies and never a judgement it makes. Pass every PRIOR TAKE of the
     session (passes do not count as visits; a candidate re-adjudicated after
     an escalation is ONE take, not two — count deduplicated candidates).

   - `defended_levels` — prior-session and multi-day floors/ceilings within
     reach: the level, which sessions defended it (memory), tests this
     session, and closes-beyond count. This is the T67 licence's first
     condition, mechanically stated.
5. **On `take_full` / `take_light`**: run the limit lifecycle (native tool if
   the Phase B probe found one; simulated otherwise) —

   **DRAW THE POSITION AS A TRADINGVIEW POSITION TOOL** (his request,
   2026-08-11: so he can eyeball every agent trade against his own read).
   `draw_shape`'s `shape` field is a free-form string passed straight to
   TradingView's `createMultipointShape`, so the native risk/reward tools are
   reachable: try **`long_position`** / **`short_position`** first. On fill,
   draw it with the agent's own numbers — entry, `stop`, and the final
   target — so the box shows the real R geometry, and label it with the
   candidate id.

   **Probe once, on the first fill of the first day, then reuse what worked.**
   If `long_position` errors or `draw_list` does not show the new shape, try
   `risk_reward_long` / `risk_reward_short`, then fall back to a
   **rectangle + three horizontal lines** (entry / stop / target) with the
   same label. Whatever works, record it in the run header as
   `position_tool` so later days do not re-probe, and report to him which
   form is live.

   Keep the drawings: at end of day, do **not** `draw_clear` — the marked-up
   chart is the artifact he reviews. Screenshot the full window with all
   positions drawn and save it as `<sess_day>_marked.png`.
   - placed at the agent's `entry` (retest level, forward offset), and
     **drawn on the chart** (`draw_shape` horizontal line + label) so it is
     visibly resting;
   - **expiry: 5 bars** (10 minutes on 2m), then cancelled → line removed →
     row `no_fill_expired`;
   - **cancel rule**: if a bar reaches the next structural level before the
     fill → cancelled → line removed → row `no_fill_ran` (*"if it runs to a
     structural level and then fills me, I'm not very confident in that
     anymore"*);
   - **fill**: first bar whose range contains the limit price fills at the
     limit → line removed, `replay_trade buy|sell` mirrors the position on
     the chart. Touch-equals-fill is optimistic for a resting limit (no
     queue model); every fill row carries `fill_model: "touch"` so scoring
     can discount marginal ones later.
6. **Manage open positions on doctrine** (`PLAYBOOK.md` §5): partial at
   intermediate structure, break-even after TP1 or on touching an
   intermediate band, **flatten before 09:30 for pre-market carries (T51 —
   supersedes the old break-even)**, trail in chop, extend target only when
   the thesis confirms — each management action logged with its bar. Windows cap **entries only**; a position runs
   past the window until target or stop, so keep stepping to resolution even
   after the window shuts.

**Caps count FILLS, not placements** — LONDON 2 / NY_PRE 1 / NY_AM 2. After a
window's second London fill, candidates still get logged, as passes with
reason `window_cap`.

When he lifts the caps for a run (*"the more trades we have data off of, the
easier it will be to generalize"*), keep adjudicating and filling — but tag
every fill beyond the WRITTEN caps `beyond_written_cap: true` and print both
scoreboards, as-run and as-written. A number produced under lifted caps is not
comparable to doctrine unless the capped subset is recoverable from the log.

## 4. PHASE R3 — THE LOG

`output/agent_runs/<sess_day>.jsonl`, one JSON object per row:

- run header: symbol, TF, chart TZ, parity result, MCP commit, agent versions,
  and a **run prefix unique to this run** used on every candidate id and
  briefing filename. Never reuse a prefix: `r2` is burned twice (a 0.3.4-era
  Friday re-run and the 0.4.x shakedown share it), so any tool scanning
  `output/briefings/` by prefix now mixes two eras;
- every thesis emission (with its `event_trigger`);
- every macro read;
- every candidate with the full `tv-trigger` payload, `leak_check: pass`,
  the screenshot path, and — for fills — entry/stop/targets, the management
  trail, and exit in R at his convention (**full-target R, not blended**);
- every unfilled limit as its own row (`no_fill_expired` / `no_fill_ran`).

A run that logs only its trades is close to worthless for teaching.

## 5. PHASE R4 — SCORING

```bash
python -m scripts.score_replay_run output/agent_runs/<sess_day>.jsonl
```

v0 scores **agreement**: per-window take/pass/no-fill counts against
`data/narrated_days/<file>.json`, then a side-by-side decision table for the
teaching loop (his row ↔ agent row, matched on window + time). The outcome
axis (in-window P(2R) vs same-day baseline) comes after agreement runs are
stable — one month cannot settle it anyway (p ≈ 0.07 on his own 20 picks).

**The two rows a naive scorer marks wrong, and must not** (PLAYBOOK §7): the
2026-06-25 break-even before the open (29.2R left on the table, and correct),
and the 2026-06-26 refusal to tighten a limit. Score the process, not the
counterfactual. The scorer prints both as reminders when those days are run.

**Both axes are required eventually.** High agreement whose picks don't run
is cosmetic; good outcomes with wholesale disagreement is a different
strategy and gets labelled as such, not as "trades like him".

## 6. CONTEXT ECONOMY — how the orchestrator stays fast

From the MCP's own rules (`docs/TOOLS-tradingview-mcp.md`), applied to this
loop; the point is that an orchestrator drowning in bars adjudicates late
and sloppy:

- `summary: true` on every per-bar OHLCV poll; full bars only for the day
  context (capped `count`).
- `study_filter` on every pine-graphics call; never scan all studies.
- `chart_get_state` once per session, never per bar.
- screenshots return a **file path** (~300 bytes); the agents read the PNG
  themselves via `Read` — never describe a chart in prose to an agent.
- `data_get_study_values` is ~500 bytes and is the per-bar level source;
  `verbose: true` on anything is never needed in this loop.

## 7. WHAT THE AGENTS SEE — unchanged, and why

`tv-thesis` and `tv-trigger` carry `tools: [Read]` for exactly two file
kinds: the screenshot PNGs and the briefing files the orchestrator writes.
**They never touch the MCP.** An agent that could step the chart could read
past its own decision minute, and the error would be invisible in aggregate.
The MCP repo's own example agent (`agents/performance-analyst.md`,
`tools: "*"`) is built for casual chart chat, not for scored replay — do not
copy its pattern into this stack.

With `Read` comes one poison to name: `data/narrated_days/*.json` holds what
**he** did on the day being replayed — reading it during a scored run
destroys the agreement axis. The agent contracts forbid it; the orchestrator
must also never place those paths in a briefing.

## 8. DISCIPLINE — and the live path this feeds

Replay and practice orders only. No live orders under any circumstances
until scoring has been run and reviewed with him.

**The live execution architecture is DECIDED (Angus, 2026-08-11): orders go
through the Tradovate API directly; TradingView stays the eyes.** The agents
keep reading his actual chart via this MCP; the orchestrator places, modifies
and cancels orders against Tradovate's own API (demo endpoints first, then
the funded account). Chosen over driving TradingView's trading panel because
it gives real order acknowledgments instead of UI automation, and because
**working orders then live at the broker, not on the Mac** — a bracket's stop
and target keep standing server-side even if the Mac dies mid-position. Lucid
permits API connection (confirmed by him, 2026-08-11).

It stays behind two gates, in order: **(1)** replay scoring run and reviewed
with him — the rule every doc in this repo carries; **(2)** the supervised
ladder (live shadow → demo with him watching → unattended with alerts and a
kill switch), each rung gated on reviewing the previous rung's logs. Nothing
in this runbook wires a broker.
