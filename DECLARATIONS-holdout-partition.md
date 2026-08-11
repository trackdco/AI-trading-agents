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

---

## Entry 2 — P-TABLE geometry repair run, declared 2026-08-11 (same day as Entry 1)

Mechanical diagnostics only, no conditioning/cuts/selection/holdout read. Sealed rows
untouched throughout. Parameter values declared here BEFORE the sweep ran.

**New additive parameter, `MIN_LEG_HEIGHT`** — a second, scale-free leg-qualification
floor alongside `MIN_LEG_RETRACE`, expressed as a fraction of ATR14 on the leg's own
timeframe (never in points). Gates pivot CONFIRMATION in the leg tracker (an
under-height retrace does not terminate the leg; it keeps extending), not row
existence after the fact — so it composes with `MIN_LEG_RETRACE` rather than
filtering its output.

- Declared grid, crossed with the existing `MIN_LEG_RETRACE` set:
  `MIN_LEG_HEIGHT_ATR_FRAC ∈ {0.5, 1.0, 2.0, 3.0}` × `MIN_LEG_RETRACE ∈ {0.236, 0.382, 0.5}`
  = 12 cells. Default `0.0` (gate disabled) preserves the Entry-1 build byte-for-byte;
  no previously-built table is invalidated by adding this parameter.
- Report only: qualified count, triggers/session/day, and per-TF (1/2/3/5m) medians +
  p90 of `leg_height_pts`, `wick_width_pts`, `stop_dist_pts`, `r_available`, plus a
  minimal fill/stop-touch check (fill boolean + same-bar stop touch only — no MFE, no
  exit, no R-multiple) for the stop-touched-on-fill-bar rate. No fill simulation, no
  outcome statistic, no win rate, no expectancy computed anywhere in this run.
- Noise floor: median 1-minute true range over the session window (pooled fit era,
  not per cell) — `output/p_table_geometry_sweep.json`. Cost assumption for anything
  downstream: DECLARED constant 0.5pt round trip (existing book convention), NOT
  measured — no book/spread data exists in the fit era.

**Object-definition test (Task 3a/3b of the repair run)** — on the SAME identified
qualified events (no re-run of leg tracking or trigger detection), recompute wick
geometry under `WICK_TOP_MODE=candle_high` (the SPEC's own pre-declared, never-built
alternative to DA-3's `body`) alongside the built `body` mode. `target_price` held at
its `body`-mode value (declared simplification — the liquidity pool depends on other
candidates' `level_0`, not on `wick_top_mode`; recomputing it per row under a shifted
limit is a rebuild, not a recompute). Definition (c) (multi-candle zone) is explicitly
NOT built — construction pending Angus's ruling.

**Provenance note.** This entry also records a Task-0 finding material to this file:
`docs/DECLARATIONS-holdout-partition.md` on `origin/claude/tradingview-mcp-agent-setup-ql18v8`
(and its ancestor `origin/claude/hello-zfmoq6`) declares the M-TABLE programme's
sealed+gray span as 2023-01-01..2025-05-31 — the exact inverse of Entry 1's P-TABLE
fit/sealed split. The M-TABLE bar-only holdout there is already closed (spent) as of
a commit dated within the last day, so no M-TABLE claim is retroactively voidable by
this table's fit-era work. The live, unresolved risk runs the OTHER direction: this
P-TABLE's sealed span (2025-06-01..2026-01-30) is the M-TABLE programme's actively
and extensively explored fit-accessible window (Census A, narrated-day corpus, live
agent trading tests, through 2026-08-11) — this repository's "written unread" claim
for that span is true of this session's eyes only, not of the team's collective
knowledge. No partition change is made in this entry; the decision belongs to Angus.

### 6b. Resolution, 2026-08-11 — partition risk from Entry 2 §Provenance note

Decision (user, in response to the repair run's question): **leave the
P-TABLE partition as built** — fit 2023-01-02→2025-05-31, sealed
2025-06-01→2026-01-30, unchanged. Rationale accepted: the M-TABLE programme's
own bar-only holdout use of the inverse span is already closed/spent, so no
retroactive contamination exists on that side; and this session already
published fit-era statistics for 2023-01→2025-05, so a swap could not cleanly
reset exposure in either direction. The cross-programme exposure risk on this
table's sealed span (2025-06→2026-01 sits inside the M-TABLE's actively
explored, currently-fit-accessible window on other branches) stands as a
recorded, accepted risk — not eliminated, but explicitly not acted on. No
rebuild, no reseal.

---

## Entry 3 — corrections and amendments, declared 2026-08-11 (same day, following user review)

### 3a. Anchor replacement — the imported target-stop bar is discarded

Entry 2's repair run was briefed against a target stop range of "0.17W, ~11pt in
2025 bands, ~20pt in 2026 bands." **That figure is discarded.** It traces to the
M-TABLE programme's own fit-era band-width measurement (`VERDICT-htf-ma-census.md`,
Census A, "fit only 2025-06..2026-07") — which is this P-TABLE's **sealed** span.
Using it to judge this table's fit-era geometry work was a direct leak, not merely
the abstract cross-programme exposure risk Entry 2 §Provenance flagged: the AIMING
POINT for this table's own diagnostic work was itself derived from the withheld
span's regime characteristics.

**Replacement bar, self-contained to this table's own fit era:**
`stop_dist_pts >= 1.5 × median(1-minute true range, session window, fit era ONLY)`.
Measured fresh, on 2023-01-02..2025-05-31 alone: `ny_am` floor 12.5pt → target
**18.75pt**; `london` floor 4.25pt → target **6.375pt**. (Split-half check below:
the per-half floor itself drifts — `ny_am` 10.75→15.0pt, `london` 3.75→5.0pt,
first half to second — consistent with the SPEC's own band-width-doubling
rationale for ATR-scaled buffers. The pooled fit-era figure is used as the single
declared bar; a regime-aware, period-specific bar is a candidate refinement, not
built here.)

### 3b. Venue degradation — what a future P-TABLE holdout look may claim

Because the M-TABLE programme has extensively characterized this table's sealed
span's regime (band widths, touch rates, session behavior — Entry 2 §Provenance),
that venue is **degraded, not destroyed**, for THIS table's own purposes. No
PXL/PXH-specific selection has occurred there — this table's own claims are not
literally void — but the design decisions feeding into what gets tested against
it were made with indirect knowledge of that era's character. Declared now,
before any such look: **a pass on this table's sealed span reads as "consistent
with," never as "confirmed," and does not by itself authorise arming anything.**
Genuine confirmation is deferred to forward-recorded data past whatever this
table's true look-boundary turns out to be (§3d).

**Split-half discipline inside the fit era is hereby load-bearing, not optional,**
for any claim this table produces going forward — derive on one chronological
half, attempt to kill on the other, report the kill rate — mirroring the
programme's own S1 precedent (ship on fit + split-half when the holdout venue
cannot cleanly confirm; validate forward via live recording).

### 3c. Virgin-span check

No calendar span past this table's sealed end (2026-01-30) is untouched by both
programmes. `origin/claude/tradingview-mcp-agent-setup-ql18v8` carries a narrated
corpus through 2026-06-25, data pulls dated 2026-07-20, and — materially beyond a
research-exposure question — **live armed trading**: "ARMING AUTHORIZATION
re-issued (ANGUS 2026-08-05)," real order execution against an eval account,
through commits dated 2026-08-11 (today). Separately and regardless: this
repository's own OHLCV ceiling is 2026-01-30 — no P-TABLE row is buildable past
that date without new data, whether or not a virgin span exists. No new seal is
declared; none is actionable from this session.

### 3d. `wick_top_mode` — additive parameter, and the finding that supersedes Entry 2's Task 3(a)/(b) headline

`wick_top_mode ∈ {body, candle_high}` threaded through candidate creation in
`run_tf_pipeline` (default `body`, byte-identical to every previously-built
table — regression-verified). Unlike `MIN_LEG_HEIGHT`, this parameter changes
`level_1` at candidate birth, which cascades into the A4 span trigger itself
(`open > level_1`), not only into the stop/target computed afterward.

**This changes the reading of Entry 2's Task 3(a)/(b) result.** That result
recomputed geometry retroactively on the events already identified under `body`
mode — a declared, explicit simplification at the time — and found stop_dist
roughly doubling, crossing toward the (now-discarded) viability bar. Running
`candle_high` as the OPERATIVE, trigger-governing object (this entry) instead of
a retroactive recompute shows a materially different and larger effect: the
single-bar span condition becomes geometrically hard to satisfy once `level_1` is
the full candle range rather than the body boundary (a later bar's open must
clear the PXL/PXH candle's own extreme, not just its body), and the qualified
population **collapses by roughly 30–120× even before any `MIN_LEG_HEIGHT` floor
is applied** — fit-era-wide qualified count falls from thousands (built table) to
15–139 across the three declared `MIN_LEG_RETRACE` values, at trigger frequencies
of 0.006–0.31 per session per day (orders of magnitude below A4.1 C2's ~1/session
concern floor). Adding `MIN_LEG_HEIGHT ≥ 2.0×ATR` on top compresses it further, to
2–10 events across the entire 29-month fit era. The surviving `candle_high`
population's own stops do not reach the corrected bar either (median 3.5–6.9pt
vs targets of 18.75/6.375pt) — the self-selected survivors are not systematically
wider, because clearing a full prior candle's extreme does not require a large
originating candle.

**Consequence, stated plainly: "adopt (b) as the working object" is not a
drop-in geometry substitution.** It is coupled to A4's single-bar span
requirement in a way that breaks that requirement almost entirely at 1-5 minute
resolution. Adopting `candle_high` cannot be decided independently of also
reconsidering A4 (e.g., whether the span itself should be allowed to accumulate
over multiple bars under this object — `break_bars`/`qualified=false,
reason='multi_bar_break'` rows already exist and are non-zero under `candle_high`,
unlike single-bar span events). No such redefinition is made here; it would be a
new hypothesis requiring its own ruling, not a mechanical repair.

**Split-half:** both the object-(a) height-insensitivity finding and the
object-(b) population-collapse finding replicate independently on both
chronological halves of the fit era (2023-01-02..2024-03-16 /
2024-03-17..2025-05-31) — see `output/p_table_geometry_sweep_half{1,2}.json` and
`output/p_table_geometry_sweep_candle_high_half{1,2}.json`.
