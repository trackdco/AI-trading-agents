# FINDINGS — VWAP calibration: the research build was on the wrong source

2026-08-10. Prompted by the trader, unprompted by any test:

> *"my vwap is Session open, not OHLC4. i even had it configured wrong from
> my trading view at the start of replay lol"*

This is the exact class of defect the MCP route exists to eliminate — a
silent mismatch between what the research code computes and what the chart
he actually traded from displays.

## WHAT IS ESTABLISHED, AND BY WHAT

**The source is `open`. The authority for that is the trader's own
TradingView config, not a fit.** Everything below either corroborates or
sizes it; none of it independently identifies the source, and it should
not be cited as if it did.

**Anchor: 18:00 NY session start.** Confirmed by bar-matching: 17:00 and
18:00 anchors are indistinguishable on the test bar (the 17:00–18:00 hour
is the CME maintenance break, so the two anchors accumulate identical
volume), and every other anchor tried was tens of points out.

**The single-bar screenshot match cannot discriminate between sources.**
On the 2026-01-07 09:14 2m bar (O 25769.75 / H 25774.50 / L 25767.75 /
C 25774.00), against a chart reading VWAP 25,782.50 and +1sd 25,811.19:

| source | VWAP | +1sd | mean abs err |
|---|---|---|---|
| **open** | 25782.39 | 25811.10 | **0.10** |
| ohlc4 | 25782.35 | 25811.00 | 0.17 |
| close | 25782.33 | 25811.04 | 0.16 |
| hlc3 | 25782.34 | 25811.00 | 0.18 |

`open` is best, but the whole spread across four candidate sources is
0.08pt — **under a third of one NQ tick**. By 09:14 the session has been
accumulating for 15 hours and the sources have converged; that bar has no
power to tell them apart. *Correction to an earlier statement in this
session: I reported hlc3 as "~0.5pt off, two NQ ticks" on this bar. It is
0.18pt. The 0.5pt figure was not reproducible and is withdrawn.*

## THE SWITCH IS MATERIAL ANYWAY — measured at population scale

The right way to size it is not one bar but every in-window minute.
25 session-days sampled across 2026-01 → 2026-03, |open-VWAP − other-VWAP|
over 03:00–10:30 NY:

| vs source | band | median | p95 | max |
|---|---|---|---|---|
| hlc3 | VWAP | 0.72 | 1.52 | 15.12 |
| hlc3 | +1sd | 0.87 | 1.92 | 38.28 |
| hlc3 | −1sd | 0.54 | 1.88 | 10.42 |
| ohlc4 | VWAP | 0.54 | 1.14 | 11.34 |
| close | VWAP | 0.87 | 2.02 | 20.65 |

Median 0.72pt is **~3 NQ ticks** on the band the trigger definition tests
a close against. p95 1.5pt; the tail reaches 15pt on VWAP and 38pt on the
+1sd band. The convergence seen on the 09:14 bar is not typical of the
windows as a whole — it is what a 15-hour-old session looks like, and the
London window at 03:00 is nothing like it.

So: borderline "closed through the band" calls **were being adjudicated
against the wrong line**, at a magnitude that flips them.

## WHAT THIS DOES AND DOES NOT INVALIDATE

**Does not rescue anything.** Every null in BR-97..BR-105 was measured
*within* a population defined by the hlc3 band. A mis-specified band
reshuffles which candles enter the census; it does not make an unselectable
population selectable, and the headline finding — that his own picks beat
the same-day baseline 5.48R vs 1.15R — was measured on *his fills*, matched
to triggers, not on the band definition.

**Does affect the census membership.** `output/htf_ma_census/raw_triggers.parquet`
and every earlier parquet were built on hlc3. They are not rebuilt here:
the trigger-census route is the one the trader has explicitly set aside
(*"I don't like this idea of looking at the raw triggers and doing all of
this shit because it's ineffective"*), so rebuilding would spend the
compute on a line of work that is closed. Any future run against those
files must rebuild first, and `vwap_bands`' docstring says so.

**Does change the code default.** `src/htf_ma/levels.py::vwap_bands` now
takes `source=` and defaults to `"open"`. `hlc3` / `ohlc4` / `close`
remain available for exactly this kind of comparison.

## THE GENERAL POINT

This was found by the trader glancing at his own settings, not by any of
the ~11,500 statistical tests run against this data. No amount of
permutation calibration detects a mis-specified input — the null and the
real data share the defect, so the calibration passes cleanly while both
sides measure the wrong thing.

That is the argument for the MCP route stated as a measurement, not a
preference: **read the levels off his chart and the class of error
disappears entirely.** The reconstruction stays only as a cross-check,
never as a substitute.
