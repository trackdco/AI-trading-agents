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

---

# SECOND DEFECT: `data_get_study_values` can race a resolution change

Found while capturing 2026-06-03 A3 09:59. The read returned:

```
BB Basis 30513.68  VWAP 30453.98      <- WRONG: this is the LONDON price regime
```

immediately after `chart_set_timeframe(3)`. A3 is short at 30299 in NY_AM; two minutes
earlier (09:57) the same study read 30292.94 / 30336.76. A 20-period SMA cannot move 220 pt
in two minutes, and if price had actually reached 30514 the position would have been stopped
out at 30357 long before.

`replay_status` confirmed the cursor was correct (1780581539). Re-issuing the identical call
returned:

```
BB Basis 30291.51  VWAP 30336.29      <- correct, continuous with 09:57
```

So the first call returned values computed against the **previous** chart state, before the
resolution change had settled. `capture_screenshot` with `wait_for_render: true` is not
affected - the PNG file sizes cluster cleanly by price regime (LONDON captures ~234-244 KB,
NY_AM ~208-212 KB) and the 09:59 PNG is 211,879 bytes, i.e. correctly in the NY_AM regime.
Only the numeric study read raced.

## Why this one is more dangerous than the legend drift

The legend-drift defect above is bounded at ~1 pt and is always backward-looking. This one is
unbounded: it silently substitutes a legend from a completely different part of the session,
220 pt away. A manager handed those numbers would read every level wrong.

## Guard now in force

Every stored legend is sanity-checked against its own position's entry price before it is
written. Audit of all 38 frames captured so far:

```
clean - all 38 frames carry a VWAP within 250pt of their position's entry
```

The 09:59 read was caught and corrected before storage, so no frame in the pool carries a
raced legend. The check is cheap and stays on for the rest of the run.

---

# THIRD DEFECT: a partial booked on a non-`partial` action was silently dropped

Found resolving 2026-06-03 L1. At TP1 the manager returned:

```json
{ "action": "breakeven", "new_stop": 30498.0, "partial_pct": 0.5,
  "reason": "TP1 30412 traded ... bank 50% here, stop tightened 30507 -> breakeven 30498." }
```

`exitcalc.replay` booked the stop move but **not** the 50%, because the partial leg was gated
on `act == "partial"`:

```python
elif act == "partial" and a.get("partial_pct"):
```

So the whole position rode to the stop and the banked half vanished.

## Why the manager was right and the code was wrong

tv-manage 0.3.4 mandates *both* things at TP1 - bank 50% **and** tighten the stop - and the
action taxonomy has no single verb for that pair. Returning `breakeven` + `partial_pct: 0.5`
is the honest encoding of the mandate. The scorer, not the manager, had the bug.

## Fix

The partial now books whenever `partial_pct > 0`, whatever the action verb says; the stop
move still applies independently.

## Blast radius: one row

Audited all three books (wr1/wr2/jr1) for manage rows carrying `partial_pct > 0` on a
non-`partial` action:

```
1 manage row(s) carry partial_pct>0 on a non-'partial' action:
   ('jr1', '2026-06-03', 'L1', '04:15', 'breakeven', 0.5)
```

Only the row that exposed it. No already-scored position changes.

## Regression check

Re-resolved 2026-06-01 A3, which books a genuine `partial` action, before and after the fix:

```
EXIT jr1 2026-06-01 A3: +0.5913R blended / +1.0000R full-target  [partial_50pct -> stopped]
```

Byte-identical to the stored row. (The re-run appended a second exit row, which was removed;
the two were confirmed identical first - that comparison *is* the regression evidence.)

---

# FOURTH DEFECT: score.py's 75/25 counterfactual had the same verb gate

The same bug as the third, in the place where it does the most damage. `counterfactual_75`
gated on:

```python
if not done and a.get("action") == "partial" and a.get("partial_pct"):
```

So a trade whose 50% was booked on a `breakeven` row was **silently excluded from the
like-for-like sample** - and that sample is the entire basis of the 75/25 split ruling. jr1
reported `n=1` when the truth was `n=2`.

Fixed to match exitcalc: the first row carrying `partial_pct > 0` is the partial, whatever
the verb.

## Before / after (jr1)

```
before:  LIKE-FOR-LIKE subtotal   0.5913        0.8534   <- 1 trade
after:   LIKE-FOR-LIKE subtotal   2.7214        2.8302   <- 2 trades
```

wr2 is unchanged (`16.5304 / 11.0002`, n=4, 75/25 ahead by 0.5397R), as the blast-radius
audit predicted - no wr2 row books a partial on a non-`partial` verb.

## What the recovered trade actually says

06-03 L1 is the first jr1 trade whose runner reached **target_2**, and it is the first trade
in any book where 75/25 **loses**:

| trade | runner outcome | as-run | 75/25 | 75/25 delta |
|---|---|---|---|---|
| 06-01 A3 | stopped | 0.5913 | 0.8534 | **+0.2621** |
| 06-03 L1 | reached target_2 | 2.1301 | 1.9768 | **-0.1533** |

That is the mechanism stated plainly: banking 75% early wins when the runner is going to
fail, and loses when the runner is going to reach TP2. Which is precisely why T78 matters -
the split ruling and the two-target mandate are the same question asked twice. A book where
runners reliably reach a real TP2 should prefer a *smaller* early partial, not a larger one.

Sample is still 2 trades. This is the mechanism, not the verdict.
