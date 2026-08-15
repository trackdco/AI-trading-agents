# DATA PROVENANCE — the gold-track parquets

`docs/HANDOFF-2026-08-15-gold-research.md` §6 recorded that no committed script produced
the gold-track parquets and no doc recorded where they came from, and called that a real
gap in the stream's reproducibility. This closes it for GC.

The parquets are gitignored (`.gitignore` line 8, `data/*.parquet`) and live only in a
session container. That has already cost this stream once: the container holding the
original three was reclaimed and every gold number became unreproducible until the source
was re-supplied. **The binaries are disposable; this file is what makes them recoverable.**

## The Databento jobs

Both were pulled 2026-08-12 and verified here against their own manifests.

| | GC | DX |
|---|---|---|
| job id | `GLBX-20260812-QQVW3UJSQH` | `IFUS-20260812-PJBWPSAGEN` |
| dataset | `GLBX.MDP3` | `IFUS.IMPACT` |
| schema | `ohlcv-1m` | `ohlcv-1m` |
| symbols | `GC.FUT` | `DX.FUT` |
| `stype_in` / `stype_out` | `parent` / `instrument_id` | `parent` / `instrument_id` |
| range (UTC) | 2023-01-01 → 2026-08-12 | 2023-01-01 → 2025-07-01 |
| customizations | `pretty_px`, `pretty_ts`, `map_symbols` all true | same |
| CSV | `glbx-mdp3-20230101-20260811.ohlcv-1m.csv` | `ifus-impact-20230101-20250701.ohlcv-1m.csv` |
| CSV size | 486,429,799 B | 90,176,662 B |
| CSV sha256 | `ad2cdd7f538853d17bc5cd80a076fced7094a10ca94ec30625c33473a0370518` | `2ef7ef55bc3abd1ad68a32a04ce5ce4628d66163df7edc929e434cbc3149f6cb` |

`pretty_px: true` is why `src/research/tomtrades/data.py` treats prices as already decimal
rather than auto-detecting fixed-precision integers the way the NQ CSV path does. It is a
property of the export request, not of the instrument — a job pulled without it will
silently produce prices off by a factor of 1e9.

Neither CSV is committed. Both are re-pullable from the job ids above by the account that
made them; verify any re-pull against the sha256 before use.

## Rebuilding `data/gc_1m.parquet`

    python -m src.research.tomtrades.data <glbx csv> data/gc_1m.parquet

Expected output, and the accept/reject test for a rebuild:

    wrote 1,276,717 bars  2023-01-02 18:00:00-05:00 -> 2026-08-11 19:59:00-04:00  rolls=19

20,454,090 bytes; columns `ts_event, open, high, low, close, volume, symbol, roll`; **936
18:00-anchored session-days**; 20 contracts; zero nulls, zero `high < low`, zero duplicate
timestamps. `scripts/verify_gold_data.py` checks all of it and exits non-zero on any miss.

Count session-days with `htf_census._session_day`, not by calendar date — calendar dates
give 1,124, a 20% overstatement, and a naive hour-shift miscounts across DST.

The ingest drops 1,795,466 of 4,387,074 rows (40.9%) as calendar spreads and FX-Link legs
before it does anything else — those carry basis values, which are negative and are not
prices.

**Verified reproduction, 2026-08-15.** Rebuilt from the CSV above with the committed
ingest unmodified, then re-ran `scripts/gold_htf_census.py`. BR-1 returned 92.85%
[92.26, 93.42] against a 71.73% [70.52, 72.94] frozen-MA placebo over 4,934 episodes and
934 session-days — identical to `docs/FINDINGS-gold-htf-census.md` in every published
figure, including the H1/H2 split and the fixed-horizon table. The GC track reproduces
from source.

## What `condition.json` says, and the one thing it doesn't

Databento ships a per-day condition report with each job. Nobody had looked at it before;
it is worth ten seconds on any future pull.

GC: 1,167 days, **1,156 available and 11 degraded**. The degraded days do not matter, and
that is measured rather than assumed:

| degraded day | bars in series | reading |
|---|---|---|
| 2026-01-31, 2026-03-15, 2026-03-21, 2026-05-24 | 0 | weekends — nothing to degrade |
| 2024-09-18, 2025-09-17, 2025-09-24, 2026-03-16, 2026-04-10, 2026-07-30 | 1,379–1,380 | 100% of the 1,379 median — no data lost |
| 2025-11-28 | 602 | 44%, but it is the Friday after Thanksgiving — a genuine half-session |

Total exposure is 8,880 of 1,276,717 bars, **0.70%**. No filtering is applied on account
of it, and none looks warranted.

**The gap: `condition.json` does not flag the truncated tail.** The final session-day —
`2026-08-11` under the 18:00 anchor — carries 118 bars, about two hours, because the query
ends 2026-08-12T00:00:00Z and the NY session opens 18:00 the evening before. It is a
query-boundary artifact, not a market day. Given this stream's own finding that raw session tables are dominated by *how much
session was left* (`docs/FINDINGS-gold-htf-census.md`), a two-hour stub session is exactly
the shape of thing that distorts a session-window statistic. Anything reading whole
sessions should drop it explicitly rather than trust the condition report to have flagged
it. It is the only session-day under 50% of median that is not on the degraded list.

## DX: why it is parked

The DX job above is **not** the export that produced the `dx_1m.parquet` behind the D8
control test in `docs/FINDINGS-gold-level-census.md`. Two independent reasons, recorded so
the next session does not rediscover them:

**Coverage.** This job ends 2025-07-01 with 778,715 rows. The parquet described in the
handoff held 970,929 bars ending 2026-07-24. A parquet cannot hold more bars than its
source CSV has rows, so this is a different and roughly thirteen-months-shorter job.
Running the census on it would be a new test on a new sample, not a reproduction of D8,
and would have to be declared as such.

**The ingest rejects it**, and correctly:

    ValueError: 396 duplicate timestamps in the continuous series

ICE publishes DX under two `publisher_id`s — 97 with 778,224 rows and 98 with 491 — and
both emit bars for the same `(ts_event, symbol)`. `data.py` was written for CME GLBX,
where this does not arise, and has no publisher concept. The validator catching it is the
system working.

This is **not** a one-line fix, because the two publishers disagree about price: of 439
comparable pairs only 53 have identical closes and 386 differ. Keeping 97 and dropping 98
is very likely right — 97 carries 99.94% of rows and consistently larger volume — but that
is a decision about which prices are real, and it belongs in a declaration, not in a quiet
patch to the ingest.

One more thing to resolve first: 2,069 rows carry a `_Z` symbol suffix (`DX  FMH0023_Z`).
The spread filter keys on `-` and `:` so these pass through into the price series. What
ICE means by it is unestablished. Do not let them in until it is.

## Still missing

- **6J** — no export supplied. CME, so it would be a third `GLBX.MDP3` job on `6J.FUT`.
- **DX at full range** — 2023-01-01 → 2026-07-24, to reproduce D8 rather than replace it.
- **Round-turn cost data.** Queue item 1 wants GC's true round turn, and `ohlcv-1m` cannot
  answer it at any date range: a minute bar has no spread. That needs a quote schema
  (`mbp-1` or `bbo-1s`), which is a different and more expensive pull. The `vah · break`
  headline of +0.111R still rests on an assumed 0.20-point round turn against a +0.149R
  pre-cost book, and no amount of OHLCV closes that gap.
