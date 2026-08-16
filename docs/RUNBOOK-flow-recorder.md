# RUNBOOK — HTF-MA flow recorder (log-only, Phase C1)

**What it is.** A Stage-3 shadow artifact: logs every trigger of both
mechanisms at ALL SEVEN declared loci (bbma15, poc, val, vah, vwap,
vwap_m1, vwap_p1) with all twelve flow features, computed by the SAME
`day_rows` code as the level census (import, not reimplementation — parity
by construction).

**UPGRADED 2026-08-07 (E-item 5).** It previously logged the 15m BB MA
only. E1 found the edge lives at break-of-VAL and break-of-VWAP-1, so a
single-locus recorder would have accrued a year of forward data on the
wrong grammar. Coverage is now ~5x per session. It places
nothing, cancels nothing, and has no DTC/order code path in the file at
all. Its journal is S1's forward validation set: the flow holdout resolves
±10pp and S1 is a +4pp-class effect, so the sealed look cannot confirm it
(per D3 the look stays unspent) — forward flow is the only route, and every
un-recorded session is lost permanently.

**Certification status (2026-08-07, seven-locus).** `--replay` PASS on
2026-06-02 (122 triggers across 7 loci) and 2026-03-10 (141 across 7):
100% flow coverage both days, and every bbma15 row bit-identical to the
M-TABLE on entry, stop, risk and all twelve features.

## Wiring (VPS, same box as Sierra — data never leaves the box)

1. Copy `config/flow_recorder.json.example` → `config/flow_recorder.json`
   and point it at the intraday reader's live state files:
   - `bars_path`: the reader's rolling 1m OHLCV file (needs ≥30h retained).
   - `fp_path`: the reader's rolling footprint-minutes file, fp_minutes
     schema (`b/a/vol/delta/vwp`, NY-tz minute index).
     **Delta convention is LAW: delta = buys − sells = side'B' − side'A' of
     the footprint capture.** Empirically verified 2026-08-07:
     corr(delta, 1m vwp change) = +0.46 on 193k minutes. The recorder's
     G-DELTA gate refuses to log if the live feed's corr ≤ +0.2, which
     catches a sign-inverted or dead delta feed at startup rather than
     after a month of poisoned logs.
   - `journal`: append-only JSONL output. Back it up with the existing
     daily snapshot routine.
2. Certify ON THE VPS first: `python -m scripts.htf_flow_recorder --replay
   <recent sess_day>` must print PARITY PASS against the research table.
3. Run under the existing watchdog/Task-Scheduler pattern:
   `python -m scripts.htf_flow_recorder --live`. It wakes every 10s, logs
   ~40s after each 15m close, holds state across restarts (re-reads its own
   journal, never double-logs), and never dies on a data error (logs and
   retries next quarter).
4. Leave it running through the contract roll — roll handling comes from
   the bars/fp files it reads, which the intraday reader already rolls.

## Journal row

One JSON object per trigger: keys (`sess_day, t, arm, side, n_attempts`),
geometry (`entry, stop, risk, w15, ma_px`), all twelve flow features,
`s1_keep` (flowconf != 0 — the S1 verdict as the live system would have
read it), `retested` (break arm), `logged_at`. Outcome columns are NOT
logged live (they are not knowable at decision time); forward outcomes get
joined later from bars by the same walk the table uses.

## ⚠ Related defect found during wiring (2026-08-07)

`scripts/build_cvd_minute.py` labels side 'A' = buy aggressor and computes
delta = A − B. The footprint files' empirical semantics are the OPPOSITE
(side 'B' = buy aggressor; fp delta = b − a is the one that correlates
+0.46 with price). Its output `cvd_minute_apr2026.csv` — and anything
downstream that consumed it — likely carries an inverted delta. Audit
before next use; the recorder does not depend on it.

## One next action

Run the replay certification on the VPS against yesterday's session, then
schedule `--live` under the watchdog. Nothing else until the journal shows
its first clean week.
