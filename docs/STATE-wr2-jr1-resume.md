# RESUME STATE — `wr2` / `jr1`, as of the overnight run

What is done, what is not, and exactly how to pick it up. Nothing here is a plan; it is the
state of the books.

---

## `wr2` — the fit week, 2026-06-21…25

### DONE: adjudication, 76/76
Every candidate has a book row. LONDON 21/21, NY_PRE 20/20, NY_AM 35/35.
Verify with `output/analysis/complete.py wr2` → expect `0 candidate(s) not yet in the book`.

- **20 takes, 13 fills, 6 exits scored.**
- **4 escalations**, all raised by the trigger and all accommodated by Tier 1.
- **~20 rows superseded or voided**, every one retained beside the reason it was withdrawn.

### NOT DONE: scoring — 7 fills still open, 74 manage calls outstanding

`output/analysis/score.py wr2` prints what is scored. The open fills and their call counts:

| day | cid | calls | frames pooled | frames needing LIVE capture |
|---|---|---|---|---|
| 06-21 | A2 | 6 (partial taken 10:01) | 3 | 10:18 done; 10:21, 11:00 |
| 06-21 | A6 | 3 | 0 | 10:25, 10:28, 11:00 |
| 06-22 | A3 | 2 | 1 | 09:53 |
| 06-23 | A4 | 12 | 11 | 09:59, 10:00 |
| 06-23 | A5 | 10 | 5 | 10:33, 10:34, 10:36, 10:40, 10:45 |
| 06-24 | A4 | 11 | 2 | 10:27, 10:31, 10:34, 10:41, 10:52, 10:53, 10:55, 10:56, 10:57 |
| 06-24 | A5 | 7 | 1 | 10:47, 10:52, 10:53, 10:55, 10:56, 10:57 |
| 06-25 | A5 | 4 | 4 | — fully unblocked |
| 06-25 | A8 | 7 | 3 | 10:09, 10:14, 10:16, 10:21 |
| 06-25 | A10 | 2 | 1 | 10:49 |
| 06-25 | A12 | 11 | 1 | 11:06, 11:07, 11:10, 11:12, 11:13, 11:15, 11:16, 11:17, 11:18, 11:26 |

**42 frames need live MCP capture.** Capture per TAPE DAY in one navigation pass — the cost is
almost all navigation, not the shot. Tape-day mapping is session-day + 1.

### Also outstanding on wr2
- **10 rows flagged by `stalecheck.py`** — all NY_AM candidates adjudicated while an earlier
  NY_AM fill was still open. They resolve automatically as exits land; re-check after scoring
  and run `output/analysis/refresh.py wr2` for any that remain.
- **Day summaries and window_close rows** not written.
- **Comparison against w49** not run.

---

## `jr1` — the j49 tape, 2026-05-31…06-04

**16 of 77 adjudicated**, all LONDON. NY_PRE and NY_AM not started.

- LONDON: d1 5/5 done, d2 4/4 done, d3 3/10, d4 1/1 done, d5 3/4.
- **3 fills open, none managed**: `06-02 L3`, `06-03 L1`, `06-04 L1`.
- `06-02 L4…L10` are superseded/rebuilt against real state and need re-adjudicating.
- All 15 thesis briefings exist; the 5 LONDON theses are in force and in the book.
- NY_PRE/NY_AM theses not yet fired — each needs its window's predecessor resolved first,
  then `patchps_thesis.py` before spawning.

---

## The toolchain (all in `output/analysis/`, all committed)

Nothing about run state is typed any more; it is derived from the book.

| tool | what it does |
|---|---|
| `mkps.py` | position state at a minute, replayed off the book. **As-of-OPEN semantics** — events on the decision minute itself are excluded and listed in `_ties` |
| `mkmng2.py` | tv-manage state for an open position; schedule re-anchors on each banked rung |
| `fillrow.py` | limit + fill rows, limit resolved mechanically off the bars |
| `buildwin.py` | one window's candidate briefings, state regenerated per candidate |
| `legendpool.py` | chart legends indexed by cursor epoch across every run; **anchors DERIVED, not typed** |
| `frameget.py` | PNG reuse, including candidate frames at the same cursor |
| `stalecheck.py` | briefing state vs book state, per live trigger row |
| `refresh.py` | mechanical supersede + rebuild for whatever stalecheck flags |
| `complete.py` | want-vs-have over the deterministic candidate-id map |
| `t78check.py` | the reviewer receipt: two targets, TP2 a level, spacing ≥0.75R |
| `score.py` | as-run R, full-target R, and the same-fills 75/25 counterfactual |

## Known orchestrator defects — logged, NOT fixed, deliberately

1. **Manage schedule is not recomputed when a trail moves the stop.** A tighter stop can resolve
   the position before the schedule expects it, and calls keep firing at a closed position.
2. **`reason_for_call` can describe post-cursor price.** `htf.management_minutes` reads the full
   bar series, so a call can be labelled `tp1_reached` or `broken` on a print the completed 2m
   grid has not shown. Three managers caught and refused it. Not a leak into decision data — the
   briefing's bars are cursor-bounded — but it should be derived from the same grid before `jl1`.
3. **`stalecheck.py` has no thesis-version check.** It compares position state only.
4. **`new_stop: 0.0`** emitted by tv-manage alongside non-stop-moving actions, three times.
