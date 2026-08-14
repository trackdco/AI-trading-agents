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
| 2 | 2026-06-01 | Tue 2 Jun | **IN PROGRESS, fourth attempt, clean.** LONDON + NY_PRE complete (0.00R). NY_AM running. |
| 3+ | 2026-06-02 … 2026-06-29 | Wed 3 Jun … Tue 30 Jun | not started |

**Day 2 progress (attempt 4, the clean one):**
- **LONDON closed 0.00R** - 4 candidates, 4 passes, 0 fills. Theses v1 short 03:00,
  v2 long 04:15 (tripwire resolved, 15m close 30556.00 body 0.67 above 30547.25).
- **NY_PRE closed 0.00R** - 7 candidates (6 agent, 1 orchestrator-mechanical at 09:27
  on the 09:10 cutoff), 2 takes, 1 fill. Thesis v3 short 08:00. P2 short filled 08:36
  at 30540.00, R 22.0pt; tv-manage went breakeven at 08:38 on the crowded-path clause
  and it was collected at 08:39 for 0.00R. P4 take_light B routed to tv-manage as a
  T53 second_setup.
- **NY_AM in progress** - thesis v4 VOIDED for an orchestrator leak (see below), re-run
  clean as v4b long at 09:30. Its tripwire resolves 10:26, so a re-fire is due before
  the 10:27 candidate. Candidates: 09:33, 09:46, 09:51, then 10:27, 10:34, 10:45.

**Escalations used all day: 0.** No agent has escalated thesis_stale.

Day 2 was attempted twice before and both attempts were voided in full:
attempt 1 halted when the chart canvas froze; attempt 2 was abandoned after a missed
tripwire re-fire. Neither produced any net R (the only fill scratched at exactly 0.00R).

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
