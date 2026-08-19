# FINDING (jr1): the chart legend is NOT constant within a 3m bar

**Status:** defect found and corrected mid-run. Does not halt the run (not a leak, not a
parity break, not a contract break). Logged for ruling.

## The claim that was wrong

Earlier in this run I concluded that the indicator legend (Bollinger Bands, VWAP deviation
bands) was a property of the *bar* rather than the *minute* - so that at res 3, consecutive
decision minutes falling inside the same 3m bar could share one `data_get_study_values`
read, and only the first minute of a cluster needed a live read. I applied that shortcut and
reported it as a throughput win.

It is false.

## The test that disproved it

Two decision minutes whose cursors fall inside the *same rendered bar*:

| decision | cursor | last_visible_bar_time | BB Basis | BB Upper | BB Lower | VWAP |
|---|---|---|---|---|---|---|
| 04:02 | 1780560119 | 1780560000 | 30513.35 | 30541.61 | 30485.09 | 30456.22 |
| 04:03 | 1780560179 | 1780560000 | 30513.16 | 30542.22 | 30484.10 | 30456.32 |

Same rendered bar (last_visible_bar_time identical), different legend. The legend is a
**live snapshot at the replay cursor**, recomputed as the in-progress bar takes on each new
minute of data. Sharing it across minutes stamps a frame with values read at an earlier
instant.

An earlier pair (03:59 vs 04:01) was consistent with either hypothesis and did not settle
it - those two cursors render *different* bars, so a legend difference proves nothing. The
04:02/04:03 pair is the decisive one because the rendered bar is held constant.

## Magnitude

Drift across one minute inside a bar, measured on the pair above:

- BB Basis 0.19 pt, BB Upper 0.61 pt, BB Lower 0.99 pt
- VWAP 0.10 pt, sigma bands <= 0.21 pt

So roughly **<=1 pt**, against a T55 trail-clearance floor of 3 pt and structural levels tens
of points apart.

## Blast radius

Nine pooled frames carry a legend read at an earlier cursor:

```
jr1|2026-06-01|A2|09:49   jr1|2026-06-01|A2|09:50   jr1|2026-06-01|A2|09:55
jr1|2026-06-01|A2|09:56   jr1|2026-06-01|A2|09:59   jr1|2026-06-01|A3|09:55
jr1|2026-06-01|A3|09:58   jr1|2026-06-01|A3|09:59   jr1|2026-06-02|L3|03:40
```

Frames that share a legend across *candidates at the same minute* (A2/A3 at 09:55, 10:00,
11:00) are correct and are not in this list - same cursor, same chart state, one read is the
right number for both.

## Why this is not a halt

The stale legend is always read at an **earlier** cursor than the frame it was stamped on.
It can only ever be backward-looking, so it cannot carry future information: this is not a
leak. The screenshots themselves were each captured at their own correct cursor and are
unaffected - only the numeric legend in the briefing is stale, by at most one minute.

## Disposition

- The shortcut is abandoned. Every frame from 2026-06-03 L1 04:03 onward gets its own
  `data_get_study_values` read.
- The nine affected verdicts are **not** re-run: drift is <=1 pt, sub-threshold against every
  decision rule the manager applies, the direction is backward-looking, and their PNGs were
  correct. Re-running would require re-navigating tapes already left behind.
- Flagged for ruling. If the ruling is to re-run them, the nine frames above are the list.
