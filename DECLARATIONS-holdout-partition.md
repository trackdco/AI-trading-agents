# DECLARATIONS — holdout partition

Append-only. Every entry here is committed **before** the build it governs runs, and no
statistic, row count by outcome, or plot may be produced from a sealed span other than the
bare row count and file hash recorded at write time.

> **Provenance note (2026-08-11).** This file did not previously exist in this repository —
> no M-TABLE, no prior declarations, no `scripts/htf_ma_entry_gate.py`, and no
> `SPEC-htf-ma-mechanism-census.md` are present on any branch. This entry is therefore the
> file's first entry, created for the P-TABLE build. The schema conventions, sealing
> mechanics and gate procedures are implemented from `SPEC-pxl-p-table.md` Part B and
> `.claude/skills/strategy-validation/references/gates.md` (committed alongside), not
> reused from an earlier table.

---

## Entry 1 — P-TABLE (PXL/PXH population), declared 2026-08-11, pre-build

Governing spec: `SPEC-pxl-p-table.md` (Part A locked 11 Aug 2026; Part B build spec).
Coverage evidence: `output/flow_coverage_manifest.json` (committed with this entry).

### 1. Span and partition

| Object | Value |
|---|---|
| Full span | session dates 2023-01-02 → 2026-01-30 (extent of 1m OHLCV) |
| **Fit era** | session dates **2023-01-02 → 2025-05-31** (~29 months) — `output/p_table.parquet` and sidecars |
| **Sealed holdout** | session dates **2025-06-01 → 2026-01-30** (8 months) — `output/sealed/*.parquet`, written **unread** |
| Sealed integrity | SHA256 of every sealed file recorded in `output/sealed/SHA256SUMS` at write time |

A row's era is decided by its session's local trading date (`date` column), never by wall-clock UTC.

**Declared deviation from SPEC B1 ("Sealed: everything before the fit span").** In the
earlier programme the sealed span preceded the fit span. In THIS repository flow coverage
exists only from 2025-06-02 onward (manifest), so a pre-fit seal would hand the flow family
zero holdout — contradicting B1's own venue-partition clause, which reserves the
flow-covered NY-AM months for the flow family's look. The only arrangement satisfying B1's
venue partition with this repository's coverage is to seal the tail. One-line change
(`FIT_END`) plus a rebuild if Angus rules otherwise.

### 2. Venue partition inside the sealed holdout

- **FLOW family venue — one look.** NY-AM rows on the 115 family-A flow-covered dates
  (2025-06-02 → 2025-11-20; exactly the six flow-covered NY-AM months
  2025-06 … 2025-11; date list in the manifest). Whole dates are reserved, though book
  coverage at decision time exists only 09:30–10:29 ET; rows carry `flow_coverage`
  row-level.
- **BAR-ONLY family venue — two blocks, both must pass.**
  All other sealed rows: every london-session row in the sealed span, plus NY-AM rows on
  dates not family-A-covered.
  **Block 1:** session dates 2025-06-01 → 2025-09-30. **Block 2:** 2025-10-01 → 2026-01-30.
- **London-window book data (family B)** exists on 172 sealed dates and its features are
  computed as columns, but every london row is assigned to the BAR-ONLY venue. Consequence,
  declared now so it cannot be argued later: once the bar-only family has looked at the
  london blocks, **any london flow hypothesis can only be validated on forward-recorded
  data** — the historical london flow venue is spent by the bar-only look.
- Family-C files (2026-02 → 2026-07) lie beyond the OHLCV span: no P-TABLE rows exist
  there. They are a forward archive, not a venue.

### 3. Pre-committed unconfirmable outcome (flow)

The flow venue is six months of half-covered NY-AM sessions. Any flow finding that passes
fit but sits below what this venue can confirm is recorded as
**interesting-but-unconfirmable**, is not fought over, and does not spend the look. It
queues for forward validation on the live recorder.

**Flow data object (manifest):** all three extraction families are 1-minute-sampled MBP-10
**book snapshots** — no trade prints, no aggressor side. Delta / CVD / footprint are not
computable from the historical archive at all; `delta_decision_bar`, `delta_3bar`,
`cvd_state` are schema-present but NaN with `flow_data_object = 'book_only'`. The delta
family is forward-recorder-only from the start. Book families (walls, imbalance, spread,
censoring) are computable at 1-minute resolution; nothing shorter-lived than a minute is
observable, and depth is censored at 10 levels.

### 4. Session definitions used by this table (parameterised, one line to change)

| Session | Window | Warm-up (structure only, no triggers) | Anchor |
|---|---|---|---|
| `ny_am` | 09:30–11:30 | 08:00–09:30 | America/New_York |
| `london` | **08:00–12:00** | 07:00–08:00 | Europe/London |

**DA-4 (implementation declaration, flagged for Angus's ruling).** SPEC A1 literally says
`london (03:00–07:00 London local)`. 03:00–07:00 Europe/London is 22:00–02:00 New York —
an overnight window that contradicts (a) the SPEC's own DST rationale of anchoring to the
market generating the flow (the London cash open is 08:00 London), (b) the trader's own
London book recording, which runs 08:00–09:59 London local on 295 days (manifest,
family B), and (c) the Asia exclusion, since 22:00–02:00 ET is the Asia-adjacent overnight.
Resolved by internal consistency, like DA-1..3: the digits `03:00–07:00` are read as the
ET-convention label for the London morning and the session is implemented as
**08:00–12:00 Europe/London** (`LONDON_SESSION_LOCAL`). If Angus rules the literal window,
it is one line and a rebuild.

### 5. Parameters declared for the build (v1)

- `MIN_LEG_RETRACE = 0.382` of leg height (placeholder pending Angus's ruling);
  sensitivity row-counts reported at declared set {0.236, 0.382, 0.5}. No sweep.
- `WICK_TOP_MODE = body` (DA-3, ruled 11 Aug 2026); `candle_high` variant not built.
- `STOP_BUFFER` base 2.0 pt; alternatives 0.15/0.25/0.33 × ATR14(tf_trigger), floored at
  1.0 pt, all recorded per row.
- Fill rule v1: resting limit at the wick 50%, live from the bar after the decision,
  filled only on ≥1 tick (0.25 pt) trade-through. Stress variants: 2-tick trade-through and
  50% partial fill where the fill minute's range > 2 × minute-ATR14.
- Cancellation: target-based per A5 (`expired_target_taken` / `expired_invalidated` /
  `expired_session_end`). No bar-count TTL, no bar-count staleness anywhere.
- `resolution_mode` base = `wait_5m_close` (A1.1 option b). Option (a) supersede is
  computed in parallel from the per-timeframe sibling table plus mode-a columns.
- Costs: 0.5 pt round trip inside the R numerator; `*_pts` outcome columns gross,
  `*_R` columns net. Hit-rate style columns are gross by design and labelled so.
- Structure gate `STRUCT_N = 2`; legs and swing terminals per SPEC A2 (leg structure, no
  bar-count pivots).
- Front month = maximum daily volume among NQ outrights; continuous but never
  back-adjusted; no level survives across days (structure is per session window plus
  same-day warm-up), so roll gaps cannot create phantom legs.

### 6. Gate obligations accepted for this build (B4, all three must pass before merge)

1. **Row existence under perturbation** — ≥15 probes across both directions and both
   sessions; the set of `event_id` keys at or before the probe's decision must be
   bit-identical, and every pre-decision column of those rows unchanged. **Includes the
   added assertion: `tf_trigger` (and `tf_qualifying_set`) depend only on information
   available at `tf_trigger_ts`** — timeframe resolution must not smuggle in the future.
2. **Entry-price perturbation** — limit unchanged under future-flattening (it derives only
   from the PXL bar); `filled` false on a flat future; row-level
   `limit_price == pxl_50` exactly; market-entry control price equals the open of the bar
   strictly after the resolution boundary and moves under perturbation;
   developing-indicator check (no level derives from any indicator that includes the
   current bar; trigger-close ±1-tick invariance of `limit_price`).
3. **Convention check** — families A and B share zero common minutes, so the check runs
   transitively: every flow file's normalised prices must agree with the same-minute
   front-month OHLCV bar (declared tolerance), per-file price-scale detection asserted
   against the family convention (three known anomaly files logged), book ordering asserts
   (bids strictly descending, asks ascending, bid < ask). Roll-mismatch days (NQ.c.0 or
   NQ.v.0 disagreeing with the volume-front) are excluded from `flow_coverage` and logged —
   a calendar-based, outcome-independent criterion. The absent same-minute overlap is
   recorded as a standing MISS: every future extension must preserve one deliberately.

### 6a. Amendment, 2026-08-11 — pre-merge, during gate iteration

Gate 1 demonstrated that the C4 assertion's strict reading — "`tf_trigger` is fully
determined at `tf_trigger_ts`" — is **unsatisfiable under resolution mode (b)** as the
SPEC defines it: within a 5m window, a higher-timeframe bar closing later than an
earlier trigger supersedes it by design (probe case 2023-07-27 london: a 3m bar closing
07:18 stole governance from a 2m trigger at 07:16 inside the 07:20 window), so
governance is only fixed when the window ends. Accordingly, and before any merge:

- **`ts_decision` under mode (b) is the 5m resolution boundary** — the moment the
  decision completes and every row column is fixed. B3's parenthetical
  ("ts_decision = trigger bar close") is carried by `tf_trigger_ts` instead; under
  mode (a) the two instants coincide.
- The C4 assert is enforced in its satisfiable two-part form: (1) flattening bars
  strictly after `ts_decision` leaves row existence, `tf_trigger`, the qualifying set
  and every row column unchanged; (2) flattening bars strictly after `tf_trigger_ts`
  leaves the governing event present in the per-timeframe stream with identical
  geometry and qualification.
- This is a recorded property of mode (b), not a waiver: it is additional evidence for
  running the mode (a) comparison at Stage 4+, which the `a_*` columns and the sibling
  table exist to support.

### 7. Out of scope for the build this entry governs

No conditioning, no cuts, no filtering, no parameter selection, no exit choice, no holdout
read. The build produces a population only. Later stages get their own declared bars and
spend looks only on the venues reserved above.
