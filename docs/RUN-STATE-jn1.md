# jn1 RUN STATE — read this first in any fresh session

Durable handoff for the jn1 June-2026 walk-forward. Written 2026-08-15 so the run
survives context compaction. **The spec block the user pastes each session is still
authoritative** — this file records what has already happened and what has been fixed,
not the doctrine.

---

## 1. WHERE THE RUN IS

| day | session-day | cash day | status |
|---|---|---|---|
| 1 | 2026-05-31 | Mon 1 Jun | **COMMITTED** (2c11d06f). +7.071R full-target / +3.679R blended. Has one open question — see §5. |
| 2 | 2026-06-01 | Tue 2 Jun | **COMMITTED** (1c94701f). +2.254R full-target / +1.714R blended. |
| 3 | 2026-06-02 | Wed 3 Jun | **NEXT** - started once and cleared; see the day-3 recon below |
| 4+ | 2026-06-03 … 2026-06-29 | Thu 4 Jun … Tue 30 Jun | not started |

**Day 2 final (session-day 2026-06-01, trades Tue 2 Jun): +2.254R full / +1.714R blended.**
17 candidates (16 agent, 1 orchestrator-mechanical), 5 takes, 3 fills, 12 passes.
LONDON 0.000R (4 cand, 0 fills) · NY_PRE 0.000R (7 cand, 1 fill) · NY_AM +2.254R (6 cand, 2 fills).
Every fill inside the written caps, so as-run == as-written. 11 thesis emissions;
both escalations ACCOMMODATED, none reaffirmed; 6 tripwire resolutions all acted on
the minute they resolved.

**Seven orchestrator defects found on day 2** - four fixed in code, all logged in the
run file. The one that mattered: an inclusive bar slice put a not-yet-printed session
high into the 09:30 thesis briefing. That thesis was VOIDED and re-run clean; LONDON,
NY_PRE and the P2 fill were each measured against the corrected slice and were
identical, so they stand. See FIXES for the code changes.

**Standing conventions added on day 2:**
- every numeric fact in a briefing free-text field is substituted programmatically
  from a computed variable, never typed. `verify()` does NOT police prose.
- bar ranges for briefing text go through `htf.range_strictly_before` (end exclusive).
- `output/briefings/` holds ONLY real briefings (dict-shaped, one per agent call).
  Tier-3 call schedules go to `output/schedules/` - a list-shaped file in the
  briefings dir crashes `audit_run_leak`.
- `mk_thesis` hardcodes `open_position: null`; patch the built JSON when a position
  is live before spawning.
- tv-macro-events has NO tools - its briefing is passed INLINE, never as a path.

---

## 1b. DAY 3 RECON (session-day 2026-06-02, trades Wed 3 Jun) - already done, reuse it

Day 3 was opened once and then cleared at the day boundary rather than left partial.
Nothing was committed. These facts were established and do not need redoing:

- **Weekly-anchor gate PASSES.** Expected == computed Mon 2026-06-01 18:00 EDT (same
  anchor as day 2 - both session-days sit in the same cash week).
  Profile at 02:30: POC 30676.00 / VAL 30540.00 / VAH 30721.00.
- **19 candidates.**
  LONDON (10): 03:04 D · 03:06 U · 03:34 D · 03:38 U · 03:42 D · 04:03 D · 04:09 U ·
  04:24 D · 04:28 U · 04:39 D
  NY_PRE (3): 08:18 D · 09:08 D · 09:27 U (past the 09:10 cutoff -> mechanical)
  NY_AM (6): 09:36 D · 10:10 U · 10:15 U · 10:51 D · 10:54 U · 10:57 D
- **ISM SERVICES PMI PRINTS 10:00 ET.** This is the first time Services has appeared in
  the run, so his open question is LIVE. His ruling exempted ISM *Manufacturing* only;
  `data/reference/blackout_policy.json` records the conservative reading that Services
  still gates. Five of NY_AM's six candidates fall after 10:00. LONDON and NY_PRE are
  unaffected - the macro agent returned `news_blackout: false` for LONDON with the event
  correctly recorded in `blackout_events`.
- **The day is a fast-churning rotation.** In the one attempt, the thesis re-fired three
  times before 03:40 (short 03:00 -> long 03:15 -> short 03:30), every flip licensed by a
  genuine DECISIVE 15m close through the same 30721-30725 daily/weekly VAH cluster.
  Expect many tripwire resolutions; budget for them.
- **The scanner is noisy on this day.** The first three candidates all had their
  `levels_closed` reading overturned by the agent on the level values - twice because only
  moving averages had been crossed (a lone MA closure is pending, not a candidate), once
  because the candle high never reached the level the scanner named.

**Two lessons banked from that attempt, both already in the conventions list:**
1. Do NOT write anything into a briefing that points at an answer. A re-fire reason
   ending "...if you judge the level is simply oscillating, say so, because stand_aside is
   a complete answer" is a vote, caught before spawn. State the countable fact - "second
   decisive 15m close through the same cluster in thirty minutes, opposite direction" -
   and stop. The agent reached the oscillation read on its own from that fact alone.
2. **Possible doctrine gap for his ruling:** the acceptance rule has no hysteresis. A level
   that whipsaws with decisive 15m bodies re-fires the thesis every 15 minutes by
   construction. That is different in kind from the old failure of flipping on 2m closes,
   and it is worth asking whether repeated same-level acceptance should need more than the
   next decisive close.

---

## 2. PRE-SCANNED CANDIDATES — day 2 (session-day 2026-06-01)

Regenerate with `.venv/bin/python -m scripts.replay_tools.candidates 2026-06-01 <WINDOW>`.

- **LONDON (4):** 03:46 DOWN · 03:51 DOWN · 04:04 UP · 04:26 DOWN
- **NY_PRE (7):** 08:24 UP · 08:33 DOWN · 08:36 UP · 08:38 DOWN · 08:42 UP · 08:57 DOWN · 09:27 UP
  - 09:27 is past the 09:10 entry cutoff → mechanical gate, no agent call.
- **NY_AM (6):** 09:33 DOWN · 09:46 UP · 09:51 UP · 10:27 DOWN · 10:34 UP · (one more — re-scan)

---

## 3. THE OPERATING LOOP — exact order, every decision minute

Deviating from this order is what caused two of the three day-2 failures.

1. `replay_start` with an explicit `-04:00` offset.
2. **`replay_status`** — non-negotiable. It is what forces the canvas repaint.
   Without it `capture_screenshot` returns a stale compositor frame, silently, for
   as long as replay stays paused. Byte-size comparison does NOT prove freshness.
3. `data_get_ohlcv {summary:true, count:2}` — verifies the landing AND is the leak check.
4. `capture_screenshot` (region chart, wait_for_render true).
5. `data_get_study_values` — chart levels for the briefing.
6. Build the briefing (§4), spawn the agent, log the verdict.

**After EVERY thesis emission**, before any candidate in the remainder of that window:
run the tripwire scan (§4). This is required by RUNBOOK §2b and its absence voided
attempt 2.

---

## 4. TOOLING — all in the repo, all durable

```bash
# briefing builders (argv order is documented in each file's docstring)
.venv/bin/python -m scripts.replay_tools.mk_thesis  <sd> <dn> <dec> <window> <shot> <chart_levels_json> <macro_path> <out> [event] [prior_path] [since] [refire_reason]
.venv/bin/python -m scripts.replay_tools.mk_trigger <sd> <dn> <dec> <cid> <window> <shot> <thesis_path> <chart_levels_json> <cand_levels_csv> <side> <pair_shape> <levels_closed_csv> <fills> <cap_json> <macro_path> <out> [extra_json]
.venv/bin/python -m scripts.replay_tools.mk_manage  <sd> <dn> <dec> <cid> <shot> <reason> <level> <level_price> <side> <entry> <stop> <targets_json> <conviction> <chart_levels_json> <opened_at> <crowded_json> <prior_actions_json> <original_r> <out> [extra_json]

# tripwire sensor — run after every thesis, scan to window end
.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
from scripts.replay_tools.tripwire import resolve_tripwire_named
print(resolve_tripwire_named('<sd>','<dn>','<level_name>',<armed_price>,'<event>','<side>','<start>','<end>'))"

# hard per-day gate — exit 1 STOPS THE DAY
.venv/bin/python -m scripts.gate_weekly_anchor <sd> --minute 02:30
.venv/bin/python -m scripts.gate_weekly_anchor <sd> --minute <HH:MM> --briefing <first trigger briefing>

# candidate scan / escalation state / logging
.venv/bin/python -m scripts.replay_tools.candidates <sd> <WINDOW>
.venv/bin/python -m scripts.replay_tools.esc reset | open <WINDOW> | request <cid> <verdict_json> - | outcome <cid> <accommodated|reaffirmed>
python -c "from scripts.replay_tools import jn1; jn1.write(<sd>, row); jn1.sort_log(<sd>)"

# lifecycle / management-minute computation
from scripts.replay_tools.lifecycle import limit_lifecycle, resolve, excursion
from scripts.replay_tools.htf import management_minutes
```

The builders auto-inject two guard blocks: `chart_freshness_self_check` (expected
legend values; the agent must refuse with `stale_chart` if the chart disagrees) and
`session_calendar` (label / opening evening / **cash weekday traded**).

Screenshots land in `/Users/barbelldaddy/tradingview-mcp/screenshots/`.

---

## 5. HIS RULINGS IN FORCE

- **ISM Manufacturing PMI does NOT gate entries** (`data/reference/blackout_policy.json`).
  *ISM Services still gates* — he said "ISM" while a Manufacturing print was in front
  of him, and the narrower reading was taken. **Open: extend to Services?**
- **VWAP±2 is FADE-ONLY.** A long at or through +2, or a short at or through −2, is
  blocked by the orchestrator regardless of which nearby level the limit sits on.
  Enforced mechanically; the trigger reads constraint 0b narrowly.
- **Caps LIFTED**, fills beyond written caps tagged `beyond_written_cap`, both
  scoreboards per day.
- He scores **blended R across the 75/25 partials**, not the log's full-target
  convention. Report both, every day.

---

## 6. OPEN QUESTIONS AWAITING HIS RULING — do not act on these

1. **DAY 1 TRIPWIRE MISS (decision needed).** Day 1's NY_PRE armed a short-side
   tripwire at 08:26 that resolved unambiguously at 08:32 while the P2 long was open;
   it was never re-fired. NY_AM's 09:30 tripwire resolved 09:34, also never re-fired
   (that window had no fills). **+0.50R of day 1's +3.679R blended is downstream of a
   real miss.** LONDON is clean, so L1's +3.179R is unaffected.
   Options recorded in day 1's log: (a) accept with the caveat attached, or
   (b) void and re-run day 1's NY_PRE and NY_AM only, keeping LONDON.
2. **T53 scale-in is mechanically unreachable** — hit twice (day 1 L2, day 2 P4).
   The add and its trail are one package, but management has usually already tightened
   the stop inside the new setup's invalidation, so the trail would be a widening,
   which is forbidden. Every qualifying B+ add is being downgraded to confirmation-only
   by mechanics rather than conviction.
3. **Weekly profile == daily profile on trades-Tuesday sessions** (5 days this month,
   incl. 2026-06-22 in the narrated week). The weekly anchor IS the session open, so
   both cover identical bars. Weekly edges grade **A** alone and daily grade **B**, so a
   level can earn an A by calendar accident.
4. **Constraint 0b wording** — the trigger twice read it as applying only when the limit
   price *is* the band. With a properly-gated thesis it applied it correctly unaided,
   so the defect may sit in thesis-side `waiting_for` rather than 0b.
5. **His anchored weekly VP drawing was destroyed** by an orchestrator `draw_clear` and
   cannot be recreated via the MCP (`anchored_volume_profile` is a silent no-op). He must
   re-draw it by hand. Agents are unaffected — weekly values are computed and injected.

---

## 7. FIXES ALREADY MADE (do not re-litigate)

- **a5b87039** — anchored-weekly Monday fallback removed. It fired only on the
  trades-Tuesday session where it was always wrong; would have put weekly VAL 601pt out
  on 5 days. Day 1 unaffected and byte-identical after the fix.
- **2510e100** — `context_extras` dropped its final partial 2m bucket (an 08:03 briefing
  carried `swept_at 08:04`).
- **943c11bd** — `scripts/replay_tools/tripwire.py`: mechanical tripwire scanning at every
  candle close, resolving **named moving levels live** rather than against the frozen
  armed price (that distinction both fires early and misses late).
- Briefing guards: `chart_freshness_self_check`, `session_calendar`, BUILD stated
  authoritative for developing profile values.
- No blanket `draw_clear`; remove drawings individually by entity id.

---

## 8. KNOWN AGENT BEHAVIOURS

- **tv-trigger misses list-gates**: the 09:35 cash-open buffer (twice on day 1) and the
  outer band. Orchestrator blocks mechanically and logs the miss; never override a
  judgement, only enforce gates.
- **Scanner false positives are common** — agents have correctly corrected claimed
  level-closures three times on day 2 alone. The contract tells them to; that is working.
- **tv-macro-events has `tools: []`** — never embed a directive inside a data row; it
  will try to verify and stall. Standing doctrine goes in its own briefing field.
- Native `long_position` / `short_position` / `risk_reward_*` / `anchored_volume_profile`
  are **silent no-ops** here (success + null entity id). Use rectangle + 3 horizontal lines.
- `replay_step` is inert; every move is a verified `replay_start` jump.
- The top-left OHLC ticker can show a hovered/older bar — past data only, not a leak.
  The **indicator legend** is the freshness signal.

---

## 9. DAY-END SEQUENCE

1. `window_close` rows per window; `day_summary` with `day_r_full_target` AND
   `day_r_blended_across_partials`, plus the as-written-caps subset.
2. `jn1.sort_log(<sd>)`.
3. Re-lay position drawings, capture `<sess_day>_marked.png`.
4. `git add -f output/agent_runs/<sd>_jn1.jsonl output/briefings/jn1_<sd>_*.json` —
   **the `-f` matters**, `output/*` is gitignored and new files are silently skipped.
   Verify with `git diff --cached --name-only`.
5. Commit + push.
6. **Post-commit leak audit** (his instruction): run `scripts.audit_run_leak` with
   `--sess-day <sd>` and a **jn1-only briefings dir** (the shared dir mixes ~99 findings
   from older runs). Any unexplained failure stops the next day.
   Known-benign check-C classes: the `-04:00` UTC offset inside anchor timestamps,
   window-bound constants, and scheduled event times.

---

## 10. ESTABLISHED ON DAY 3 (session-day 2026-06-02)

### 10a. NEVER BLOCK (his standing rule, runbook §2d)
Only three things halt a run: a parity FAIL, an unclearable no-leak check, a
contract-version mismatch. Everything else — including anything you would want his
ruling on — applies the **conservative default** (the existing rule as written; or
`pass` with `reason: awaiting_ruling` if a candidate genuinely cannot be adjudicated
without him), logs an `open_question` row naming the question, the default applied and
the rows it touched, and **continues**. Reuse the same default on later days so the
month stays internally consistent. All open questions are surfaced together in the
morning report. Never stop overnight to ask anything.

### 10b. `replay_start` needs an explicit `-04:00` offset
`replay_start` parses a bare `"2026-06-03 04:23:59"` in **AEST (+10)** and silently
lands **14 hours early** on the wrong day. Always pass
`"2026-06-03 04:23:59-04:00"`. `replay_start`'s own response echoes the *previous*
cursor, so the jump is only confirmed by a following `replay_status` — which also
repaints the canvas, so it is required anyway.

**CORRECTED — this section originally said the landed cursor arriving at `:58` rather
than `:59` was "a snap to the last tick, not a miss." That was wrong and was never
checked against the data. It is a real one-minute miss. See §10h.** Request `dec:00`,
not `dec-1:59`.

### 10c. `price_at_decision` lags at ODD decision minutes
`brief04.price_at(dec)` returns the close of the **last complete 2m bar**. At an even
decision minute that is the close of minute `dec-1` and is correct. At an **odd**
decision minute (a 3m close that is off the 2m grid) it is the close of minute
`dec-2` — one committed minute stale, even though the chart cursor at `dec-1:59`
has reached that minute.
- It is material. At L6 (04:03) it made a short limit at 30710.50 read as marketable
  against 30711.50 when the true last price was 30705.00 and the limit rested correctly
  above the market. It also understates adverse excursion on manage calls.
- **Default applied, reused for the rest of the month:** validate take-row entry
  geometry against the **last committed 1-minute close** (close of minute `dec-1`).
  Leave `price_at_decision` untouched so day-3 briefings stay comparable with day 2;
  instead attach a clearly-labelled `last_committed_1m_close` block **only** to
  briefings where the two figures would otherwise contradict each other (odd decision
  minutes, and any manage call whose `reason_for_call` was computed from `dec-1`).

### 10d. Speculative parallel adjudication — the rule that came out of it
Candidate screenshots and chart-legend reads can be captured far ahead of the agents;
they are minute-stamped and leak-safe, and they cost no wall-clock while an agent runs.
Briefings, however, depend on window state. Building several ahead on an assumed
FLAT/`n`-fills premise cost two voided verdicts on day 3 when L8 came back `take_full`.
**Rule: only spawn a candidate speculatively when every candidate before it in the same
window has already returned a pass.** Voided briefings and their unscored verdicts are
recorded in `void` / `trigger_voided` rows so the discard is auditable.

### 10e. `scripts/replay_tools/mkcand.py`
Builds one trigger briefing from a small JSON spec: wraps `mk_trigger` and fills the
standing extras (`chart_truncation_note`, `position_state`, the outer-band gate **with
its arithmetic spelled out and the fire/no-fire verdict computed**, `escalation_state`,
`news_note`, `scanner_detail`). Prints the briefing path and whether the outer-band gate
fires. A candidate is one command instead of hand-assembly.

### 10f. news_blackout is applied to the WHOLE window
`news_blackout` is emitted per window and consumed per window. A scheduled release
sitting inside a window (ISM Services PMI 10:00 inside NY_AM 09:30-11:00) gates **every**
candidate in that window, which become orchestrator-mechanical passes with
`agent_spawn: "none - ..."` and no tv-trigger call. Logged as an `open_question`
(whether the gate should instead cover only a band around the print); default reused for
the rest of the month.

### 10g. Escalation, worked end to end
Day 3 L6 is the clean template: tv-trigger returned `pass` on `direction_mismatch` with
`thesis_stale: true` and an escalation. The orchestrator checked all five safeguards
(otherwise-TAKE with entry/stop/targets and a conviction; `pair_shape` same_candle;
budget 0 of 2; ratchet clear; no mechanical gate fired; one escalation on this
candidate), spent one, and re-fired Tier 1 **at the same decision minute on the same
screenshot** — the day-2 convention, no new capture. Tier 1 came back `accommodated`,
holding bias and relocating the other-side condition. The candidate was then re-run on a
briefing byte-identical except `thesis`, `thesis_version`, `escalation_state` and a
`POST_ESCALATION_NOTE`, and returned `take_full`.

### 10h. CAPTURE CURSOR: request `dec:00`, NOT `dec-1:59`
Found on day 3 by a tv-trigger agent that refused to adjudicate A1.

`replay_start` with `dec-1:59-04:00` LANDS at `dec-1:58`, at which point minute `dec-1`
is still forming and has **not committed**. The chart is therefore one minute short of
the briefing:
- at an **even** decision minute the 2m signal candle closes AT `dec` and needs minute
  `dec-1` committed — always short;
- at an **odd** decision minute the displayed 2m bar closes at `dec-1` and is fine, but
  the 3m signal candle is still short.

At A1 this showed the chart's last 2m bar as `O30763.75 H30763.75 L30714.00 C30714.25`
— the **1-minute** bar for 09:34 — against the briefing's true 2m candle
`L30677.50 C30680.00`. A 34pt divergence in the body.

**Fix: request `dec:00-04:00`.** It lands at `dec-1:59`, commits minute `dec-1`, and is
still leak-safe (minute `dec` has not started; confirm with `data_get_ohlcv`).

**The freshness self-check cannot catch this.** `levels_at_decision_CHART` is read from
the same frame as the screenshot, so briefing and capture agree with each other while
both lag. The legend does move between the stale and correct frames (BB basis 30739.24
vs 30737.53 at A1) — the check simply had nothing correct to compare against. A real
detector would compare the chart's last-bar OHLC against the briefing's stated signal
candle, which is exactly what the agent did.

Day 2 and day 3's LONDON/NY_PRE carry the defect; they were NOT re-run (the briefings
state every candle numerically in text, and 8 of 9 candidates adjudicated without
objection). Flagged for his ruling.

### 10i. CLEAR THE CROSSHAIR BEFORE READING THE LEGEND
Found on day 3 at A4's 10:53 capture.

The indicator legend can display a **HOVERED** bar's values instead of the last bar's.
At 10:53 it reported BB basis `30760.53` / VWAP `30710.11` against true values of
`30698.16` / `30682.43` — out by 61.78 and 27.18 points, corresponding to roughly
08:18, over two hours earlier. It survived a repeated read, a `replay_status` repaint,
and a full re-jump away and back.

**This falsifies §8's claim that the legend is the reliable freshness signal.** §8
already noted the top-left OHLC *ticker* can hover; the legend can too — and the legend
is the exact field `chart_freshness_self_check` asks the agent to compare against. The
check cannot detect it: the orchestrator reads the legend from the same frame the
screenshot shows, so briefing and capture agree with each other while both describe the
wrong bar.

**Fix, two parts:**
1. **Clear the crosshair** — `ui_mouse_click` on empty chart space to the right (e.g.
   `x=1350, y=300`) before reading study values or capturing. This restored the correct
   values immediately.
2. **Verify every read** — `scripts/replay_tools/verify_legend.py` cross-checks the
   legend against `bb_ma_2m`, `vwap`, `vwap_p1`, `vwap_m1` computed independently from
   committed bars, 2.00pt tolerance. A failing read is marked UNVERIFIED in the briefing;
   the orchestrator states both numbers and never silently substitutes its own.

Sequence per capture: `replay_start(dec:00-04:00)` → `replay_status` → **clear crosshair**
→ `capture_screenshot` → `data_get_study_values` → `verify_legend.check(...)`.

### 10j. KEEP BRIEFINGS LEAN — cap candidate levels at 3
Raised by him after day 3: "watching the setups and verdicts playing out, it seems
like there was a decline in judgement/performance."

Outcome-independent defect counts back him up — validation failures 0/1/3 across
days 1-3, voids 0/2/6, and tv-manage held **3 of 3** adverse-excursion calls into a
full stop on day 3 having done so 0 times before.

The likeliest self-inflicted cause: **I grew the briefings**. Mean trigger briefing
13.1 KB (day 1) -> 22.3 -> 23.9 KB; manage 3.9 -> 6.0 KB. The dominant driver is
`higher_timeframe_at_candidate_levels`, 2.85 -> 8.55 -> 9.64 KB, about 85% of all
growth, because `cand_levels` per briefing went **1.9 -> 5.7 -> 6.4**. Every extra
level spawns a full four-timeframe behaviour block.

**Rule: pass at most 3 candidate levels.** The scanner's own MA, the second level the
scanner flagged, and the thesis-named level if it differs. Do not cast a wide net
"in case it is useful" — day 1 had the leanest briefings and the cleanest verdicts.
Correlation over three days, not proof, but it is free to reverse.
