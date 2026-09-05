# REPRODUCTION — the re-test driver against the bot's own engine

**Purpose.** PREREGISTRATION.md §2 allows a performance patch *only if* the patched engine
reproduces the unpatched engine's trade list exactly on a verification slice, and §5.3 requires the
untouched configuration of `retest_backtest.py` to reproduce the bot's existing 4-year trade log.
This file records both checks. Everything here was run **before** any development-window result
was read.

Bot: `github.com/Prat617/ai-trading-bot` @ `d1e5ec7`, `nq_bot_vscode/scripts/full_backtest.py`
(sha256 recorded in every output's `meta`). Reference log: the bot's own
`logs/full_validation_trades.json` from the 4-year run (5,947 trades, 2021-09-01 → 2025-08-29),
supplied by the user.

## 1. What the driver changes, and what it does not

`retest_backtest.py` imports the bot's `full_backtest.py` as a module and subclasses its
`CausalReplayEngine`. The **only** overridden decision method is `_generate_signal`, copied
verbatim and diffed against the original with `inspect.getsource` — **7 hunks**, all of them the
pre-registered switches:

| hunk | what |
|---|---|
| 1 | signature line (type hints dropped) |
| 2 | **C1** floor inserted after `raw_stop = min(ATR14×2, structural)` and before the NaN guard / 30pt cap |
| 3–4 | 30pt cap gate wrapped in `if not self.cap_lifted` (sensitivity only) + counters |
| 5–6 | **C3** min-R:R gate wrapped in `if self.rr_gate == "kept"` + would-have-rejected counter |
| 7 | **C2** RTH-only rejection inserted as the *last* gate before the pending entry is stored |

With `--stop-floor none --rr-gate kept` and neither flag, every inserted branch is inert.

Two **non-behavioural** patches are applied in-process (the bot's files are never edited):

1. **Bounded write-only lists.** `sweep_detector.sweep_log`, `signal_aggregator._signal_history`
   and `engine._shadow_signals` are replaced by a `list` subclass that trims on append. The
   backtest script never reads any of them (`grep` of `full_backtest.py`: no reference to
   `sweep_log`, `_signal_history`, `get_signal_history`, or the aggregator's `get_stats`; the shadow
   list is read only by the post-run shadow simulation, which this test does not run).
2. **Deterministic trade IDs.** `uuid.uuid4()` inside the executor is replaced by a sequential
   counter. The ID appears only in the records; no decision reads it. This makes a sealed output
   byte-reproducible.

Why the lists matter: the bot's 4-year run averaged ~12 bars/s over 13 hours, yet its final
43k-bar segment — resumed from a JSON checkpoint that does **not** store these lists — ran at
133 bars/s (`meta.bars_per_second` in the reference log). The growth is the slowdown.

## 2. Exact-reproduction results

All comparisons use `compare_trades.py`: every trade matched **in order** on 14 entry fields
(timestamps, direction, prices, slippage, stop, score, source, regime, HTF bias/strength, ATR,
RTH flag) and 11 exit fields (timestamp, both exit prices, raw/adjusted PnL, slippage cost,
per-leg PnL and exit reasons, commission). Trade IDs are excluded (uuid4 in the reference).

| run | window (ET dates) | trades | vs reference | records sha256 |
|---|---|---|---|---|
| smoke, untouched, patched | 2021-09-01 → 09-03 | 6 | **6/6 exact**, PnL +194.38 both | — |
| **A** untouched, patched | data start → 2021-12-31 | 347 | **347/347 exact**, PnL −137.78 both | `49e72a78…0767` |
| **B** untouched, patched (repeat) | same | 347 | **347/347 exact** | `49e72a78…0767` (= A) |
| **U** untouched, **unpatched** | same | 347 | **347/347 exact** | `49e72a78…0767` (= A = B) |

Full hash: `49e72a78ceec04dbc6c62b5493b45b71ef51a5d9611f0d8c5017a60c09560767` (sha256 of the
entry/exit records, sorted keys). Patched and unpatched engines produce byte-identical records;
two patched runs produce byte-identical records; all three equal the bot's own log on every
compared field. **Gate met — the patch is used.**

The sealed slice outputs are in `data/verification/` (gzipped, with the uncompressed sha256).

## 3. Checkpoint / resume is exact

The driver's `--checkpoint` pickles the whole engine (executor closure detached and re-attached;
HTF scheduler indices and the ID counter stored alongside; ~300 KB). Test, window 2021-09-01 →
09-10 (4,890 bars, 21 trades):

| | trades_sha256 |
|---|---|
| straight run | `c777cb563338cb990c8cb05112f0cd609a233b960497462a1399746091605256` |
| stopped after the checkpoint at bar 2,000, resumed in a new process | `c777cb56…5256` (identical) |

An earlier in-process test (4,020 bars, pickle at bar 1,500) was also identical. Development
and holdout runs therefore survive a container restart without any state discontinuity — unlike
the bot's own JSON checkpoint (below).

## 4. A caveat on the reference log itself

The bot's 4-year log was produced in two segments: bars 0–574,999 continuously, then **resumed
from the bot's JSON checkpoint at bar 575,000 (2025-06-03)**. That checkpoint restores the
feature engine, HTF engine, risk state, executor and trades, but **not** the sweep detector
(prior-day/week levels, pending candidates, volume window), the aggregator, or the regime
histories. Reference trades from 2025-06-03 onward were generated by a cold-restarted detector.
This lies wholly outside the development window (→ 2024-12-31), so nothing above is affected; it
is one more reason the 2025 segment is labelled *contaminated* in PREREGISTRATION.md §3, and it
is why this test uses its own exact checkpoints.

## 5. Throughput on the slice

Three concurrent processes (plus the checkpoint tests) on 4 cores: A 227, B 223, U 220 bars/s
overall, with the same within-slice decline in all three (444 → ~170 bars/s across 59,498 bars) —
so on a 4-month slice the decline is contention/regime, not list growth; the growth effect only
emerges over hundreds of thousands of bars. The development runs' 25k-bar rate logs are kept in
each output's `meta.rate_log` and summarised in RESULT.md.
