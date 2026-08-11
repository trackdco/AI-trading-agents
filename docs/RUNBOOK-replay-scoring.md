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
4. **At each surviving candidate**: freeze (no stepping), screenshot, build
   the trigger briefing (thesis + candle payload + `fills_this_window` +
   headroom fields + macro gate), call `tv-trigger`. Log the full verdict —
   takes AND passes. **The passes are the valuable rows.**
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
   intermediate band, break-even before 09:30 for pre-market carries, trail
   in chop, extend target only when the thesis confirms — each management
   action logged with its bar. Windows cap **entries only**; a position runs
   past the window until target or stop, so keep stepping to resolution even
   after the window shuts.

**Caps count FILLS, not placements** — LONDON 2 / NY_PRE 1 / NY_AM 2. After a
window's second London fill, candidates still get logged, as passes with
reason `window_cap`.

## 4. PHASE R3 — THE LOG

`output/agent_runs/<sess_day>.jsonl`, one JSON object per row:

- run header: symbol, TF, chart TZ, parity result, MCP commit, agent versions;
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
