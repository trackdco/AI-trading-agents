# OFFLINE HARNESS — replay iteration without TradingView, without the Mac

**Status: Milestone 1 (briefing generator) BUILT and CERTIFIED, 2026-08-16.**
Approved by him the same day: *"we can calculate all of the levels... we could
just do it in this Claude Code chat, right?... deploy the versions of the
agents on a specific subset of time, run parallel workflows."*

## Why this exists

The iteration loop was: tweak a contract → burn a supervised 1.5–2h replay
day on his Mac → review → repeat. The expensive step tests something cheap:
whether the new contract reasons correctly on known situations. That question
never needed TradingView — the agents' entire world is the briefing file, and
`levels_at_decision_CHART` is EMPTY in every served briefing. Everything an
agent reasons over is computed from committed bars; the chart speaks only
through the screenshot.

So: generate briefings from bars → run the real agent contracts on them →
simulate fills from bars (the same touch model replay uses) → score with the
existing scorers. Replay on the Mac demotes from development loop to release
gate. The bar data covers 2023-01-02 → 2026-07-15 (1,251,240 one-minute NQ
bars, committed), so a candidate contract can be exercised against years of
history instead of five narrated days — subject to the rails below.

## The generator (`scripts/offline_briefings.py`)

Produces every deterministic briefing field by CALLING THE SAME CODE the Mac
orchestrator uses — `src/htf_ma/levels.py` (VWAP hlc3, BB MAs),
`scripts/agent_context.py` (daily / anchored-weekly / prior-day profiles,
integer bins, Monday-anchor fallback), `scripts/htf_level_behavior.py` (T46
blocks) — never a reimplementation. Conventions recovered and pinned by
certification:

- as-of row = the 1m row closing AT the decision minute (bar-start stamping);
- day-range fibs {0.382, 0.5, 0.618, 0.705} from the developing session low,
  2dp; `net_move_15m` is SIGNED; profile POC/VA on integer bin edges;
- manage-briefing 2m bars anchor to the CALL minute (odd-minute positions get
  odd-grid bars), not the session's even grid;
- indicator history is measured in TRADED BARS (2400), not wall-clock hours —
  a wall-clock lookback starves the 60m BB MA across the weekend gap on every
  Monday-label session. This was a real generator bug caught by certification
  against wk1 Monday and fixed; the Mac numbers were right.

## Certification (`scripts/certify_offline_briefings.py`)

Regenerates every deterministic field of every briefing ever served under
`output/briefings/` and diffs against what the agent actually saw. Result:

| prefix | era | briefings | verdict |
|---|---|---|---|
| v44 | current schema (0.4.x) | 24 | **100.0% exact, 0 leaf mismatches** |
| m1 | wk1 (0.4.5) | 6 | **100.0% exact, 0 leaf mismatches** |
| r2 | BURNED prefix, two eras mixed | 43 | 91.6% — clean half is the 0.4.x shakedown; dirty half is the 0.3.4-era Friday |
| c5 | invalidated 0.3.5 week | 54 | flat-schema era: old candle grid, pre-fix value area, VWAP-source span |
| d21–d25 | earliest runs | ~30 | same early-era schema drift |

Exact fields at 100% on current era: all VWAP bands, all BB MAs, day fibs,
session extremes, daily / anchored-weekly / prior-day profiles, the full T46
`higher_timeframe_at_candidate_levels` blocks, signal candles (2m and 3m,
even and odd grids), `last_15m_candles` with body ratios, `flush_inputs`,
`recent_2m_bars`, price_at_decision, and the sorted
`levels_above_price` / `levels_below_price` lists.

**The old-era mismatches are the certifier working, not failing**: every
delta lands exactly where recorded history says it must — the ~900–1041pt
weekly deltas are the same-weekday-minus-7 anchor bug (documented in
`agent_context.anchored_weekly_profile`), the 10–40pt VA deltas are the
2026-08-10 value-area convention fix, the VWAP deltas are the source
mis-measurement span (see `CHART_VWAP_SOURCE`). Regenerate-and-diff detects
real drift when drift exists; that is the property the harness needs.

**One advisory field.** `levels_closed_SCANNER` is orchestrator-AUTHORED text
on the Mac (tag formats vary; occasionally wrong on its own arithmetic —
which is why `levels_closed_note` tells the agent to verify and correct it).
The offline scanner is deterministic code: 31/44 string-identical, every
disagreement traced to Mac wording/choice, not arithmetic. The bridge test
compares CANDIDATE SETS, not tag strings.

## Not regenerable, by design

- **Cascade fields** (`thesis`, `macro`, `prior_thesis`): outputs of earlier
  agent calls — the harness produces them by RUNNING those agents in order.
- **State fields** (`position_state`, `fills_this_window`, caps, management
  trail): the harness's own state machine; verified by the bridge test.
- **Run prose** (`leak_check`, provenance, `scanner_detail`): the harness
  writes its own honest equivalents; never copied.
- **The screenshot**: no offline equivalent until the chart renderer (M3) is
  certified against a real-screenshot day. Until then, offline thesis runs
  are briefing-only and say so.

## Does bar-data testing translate to the TradingView MCP path?

Yes, by construction, because the agents never see TradingView on either
path — they see this schema. The differences, enumerated:

1. **Chart legend values** exist only in the screenshot. The run-time parity
   gate measured the residual: ≤0.36pt on VWAP bands, exact on BB MA
   (recorded in every served briefing's `level_provenance`).
2. **Fills**: identical touch model offline and in replay; live paper is the
   real calibration and is a separate track regardless.
3. **LLM sampling**: same briefing can flip a borderline call — on BOTH
   paths. The bridge test measures the match rate instead of assuming it.
4. **The orchestrator**: on the Mac, a Claude session follows the runbook; in
   the harness, a deterministic script does. The script is the more
   repeatable of the two.

## The candidate scanner (`scripts/offline_scan.py`) — M2 part 1

The candidate set IS the day: agent quality is irrelevant if the two paths
never see the same moments. So the scanner is bridge-tested against the
minutes his Mac actually adjudicated, recovered from **briefing filenames +
their own `decision_minute`** — the outcome-bearing run logs are never
opened.

| Mac run | session-day | minutes reproduced |
|---|---|---|
| v44 (0.4.x, full day) | 2026-06-23 | **19/19 — 100%** |
| m1 (0.4.5 wk1) | 2026-06-21 | **3/3 — 100%** |
| d21 / d22 / d24 / d25 | narrated week | **100% each** |
| d23 (earliest era) | 2026-06-23 | 2/4 — the two misses are `rejection_first`, recovered with `--rejection-first` (3/4; the last is an old-era 09:45 with no scanner prose to reconstruct) |

**Misses are defects; extras are triage.** An extra is a candidate the
harness's state machine may legitimately never adjudicate — a window at its
fill cap, a position open, a spent level. Misses cannot be explained away,
and there are none on any current-era day.

Three scanner rules were RECOVERED FROM HIS MAC rather than assumed, each
paid for by a miss:

1. **Inside one candle the second leg must be a close-through.** The runbook's
   "rejection counts" first read as "a rejected level can be the second leg";
   his Mac disproves it — on 2026-06-23 the 3m closing 03:45 crossed its own
   MA and rejected the daily POC, and the Mac opened no candidate, holding
   the leg to pair with the next candle that CLOSED the POC (the 03:48
   sequential, "own-MA leg at 03:42"). Rejections ride along as recorded
   colour.
2. **Pending legs are a QUEUE, not a slot.** On 2026-06-22 the Mac paired
   09:06 with an MA leg from the 08:57 bar while a newer 09:00 leg existed
   and a same-candle candidate had already fired at 09:03. Legs expire only
   by age; forming a candidate extinguishes nothing; a pairing takes the
   oldest live leg of matching direction.
3. **An own-MA close always becomes a live leg**, even when it also pairs
   backwards as rejection-first — letting one branch consume it cost two real
   v44 candidates.

`rejection_first` (the mirror of sequential: level rejected → own-MA close,
spanning candles) is implemented but **default OFF**: both current-era
corpora reproduce at 100% without it and it only appears in the earliest
prefix, whose whole schema predates the current one. Switchable so the
question stays his. The rejection geometry itself is un-thresholded — the
narrowest reading of his words, no invented constant — and is **unratified**.

## Milestones

| # | deliverable | gate | status |
|---|---|---|---|
| M1 | briefing generator | byte-diff vs all served briefings | **DONE — current era 100.0%** |
| M2a | candidate scanner | reproduce the Mac's adjudicated minutes | **DONE — 100% on every current-era day** |
| M2b | day state machine (thesis/trigger/manage cadence, caps, limit lifecycle, touch fills, run log) | bridge test: reproduce the June week-1 book from the same frozen contracts | in progress |
| M3 | chart renderer for thesis | same-day thesis output vs real-screenshot run | after M2 |
| M4 | open history: parallel days, version-vs-version | M2 gate passed | after M2 |

## Rails (unchanged by any of this)

- **2023–24 holdout stays locked** (`docs/DECLARATIONS-holdout-partition.md`).
- **The June walk-forward on the Mac stays the clean out-of-sample test**: no
  offline runs on June days the Mac has not finished, no contract changes
  until June closes. Offline iteration uses pre-June history and the
  completed bridge days.
- **TradingView remains venue truth and the release gate**; the live-paper
  track is unaffected.
- The Mac runbook and its machinery are NOT touched by this work.
