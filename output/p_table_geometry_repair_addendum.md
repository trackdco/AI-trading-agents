# P-TABLE geometry repair — addendum (corrected bar, object (b) adopted, split-half)

Follows `output/p_table_geometry_repair.md`. This addendum: (1) discards the
imported target-stop anchor and re-derives it from the fit era alone, (2) runs
object (b) as the OPERATIVE trigger-governing definition rather than a
retroactive recompute, (3) split-half-checks the key findings, (4) answers the
virgin-span question. No expectancy, win rate, or outcome statistic computed.
Sealed rows untouched. Full reasoning: `DECLARATIONS-holdout-partition.md`
Entry 3.

---

## The corrected bar

The prior anchor ("0.17W, ~11pt in 2025 bands, ~20pt in 2026 bands") traced to
the M-TABLE programme's own fit-era measurement — which is this table's
**sealed** span. That was a leak, not just an exposure risk, and is discarded
entirely.

**New bar, self-contained:** `stop_dist_pts >= 1.5 ×` the **fit-era-only**
median 1-minute true range. Measured on 2023-01-02..2025-05-31 alone:
`ny_am` floor 12.5pt → **target 18.75pt**; `london` floor 4.25pt → **target
6.375pt**.

---

## Headline finding: adopting object (b) is not a drop-in geometry swap

Running `wick_top_mode=candle_high` as the OPERATIVE object (governing the A4
span trigger itself, not just recomputed after the fact on already-identified
events) shows a materially different and larger effect than the earlier
retroactive-recompute result:

| | `body` [built] | `candle_high`, RETROACTIVE recompute (prior addendum) | `candle_high`, OPERATIVE (this run) |
|---|---|---|---|
| qualified count, fit era | 4,815 (or thousands per retrace-cell) | 4,815 (same events, by construction) | **15–139** (across the 3 retrace values, `height=0`) |
| triggers/session/day | 2.1–3.9 | (same, by construction) | **0.006–0.31** |
| stop_dist_pts, pooled median | 3.25pt | 6.5pt | **3.5–6.9pt** (by TF, `height=0`) |
| meets corrected bar (1.5×fit-floor)? | No (0.32–0.65×) | Partial (0.92–1.18×) | **No, at any TF or cell tested** |

**Why:** the A4 single-bar span trigger requires a later bar's `open` to clear
`level_1`. Under `body` mode, `level_1` sits inside the PXL/PXH candle's own
range, so a moderate continuation clears it. Under `candle_high`, `level_1`
becomes that SAME candle's own extreme — clearing it requires a later bar to
gap beyond a level the market just finished setting as a local high/low, which
is geometrically rare at 1–5 minute resolution. Confirmed by direct trace (28
sample `ny_am` sessions, TF=1m): single-bar span events go from **80 to 0**
switching `body`→`candle_high`, independent of any `MIN_LEG_HEIGHT` setting.
Multi-bar break events (`qualified=false, reason='multi_bar_break'`) remain
non-zero under `candle_high` — the accumulated version of the break survives
even though the single-bar version essentially disappears.

Adding `MIN_LEG_HEIGHT ≥ 2.0×ATR` on top compresses the already-tiny
`candle_high` population further, to **2–10 qualified events across the
entire 29-month fit era** (full 6-cell table below). The few survivors' own
stops still fall well short of the corrected bar (median 2.0–6.0pt against
targets of 18.75/6.375pt) — clearing a prior candle's full extreme does not
select for a wide originating candle.

**Consequence:** the object redefinition and the A4 trigger rule are coupled,
not independent. Adopting `candle_high` cannot be decided apart from also
reconsidering whether the span should be allowed to accumulate over multiple
bars under that object — which the schema already tracks (`break_bars`,
non-qualifying multi-bar rows) but does not currently permit as a qualifying
trigger. That is a new hypothesis needing its own ruling, not something this
repair run resolves unilaterally.

### Full 6-cell table, `candle_high`, `MIN_LEG_HEIGHT ∈ {2.0, 3.0}`

| retrace | height | n qualified (all TF) | triggers/session/day | best single-TF stop_dist median | meets corrected bar? |
|---|---|---|---|---|---|
| 0.236 | 2.0 | 6 | 0.012 | 3.5 (1m) | No |
| 0.382 | 2.0 | 10 | 0.02 | 4.375 (1m) | No |
| 0.5 | 2.0 | 3 | 0.006 | 6.0 (1m) | No |
| 0.236 | 3.0 | 6 | 0.012 | 4.0 (1m) / 12.25 (3m, n=1) | No |
| 0.382 | 3.0 | 5 | 0.01 | 3.0 (1m) | No |
| 0.5 | 3.0 | 2 | 0.004 | 3.125 (1m) | No |

No cell reaches the corrected bar. The one double-digit stop_dist value
(12.25pt, 3m) is a single-event cell (n=1) and not a population claim.

Full data: `output/p_table_geometry_sweep_candle_high_h2h3.json` (height 2/3),
`output/p_table_geometry_sweep_candle_high_h0.json` (height 0, for
isolating the object-mode effect from the height effect).

---

## Split-half: both findings replicate independently

Fit era split chronologically at 2024-03-17 (~14.5 months each half).

**Object (a), height-insensitivity** (`retrace=0.382`):

| | half 1 (n / 1m stop / 5m stop) | half 2 (n / 1m stop / 5m stop) |
|---|---|---|
| `height=0.5` | 2,190 / 2.75pt / 4.0pt | 2,406 / 3.0pt / 4.375pt |
| `height=3.0` | 251 / 3.0pt / 4.25pt | 324 / 3.25pt / 4.5pt |

Population falls ~9× in both halves independently; stop_dist moves by
0.25pt at most. Same shape, same conclusion, on data the other half never
touched. (Noise floor itself drifted half-to-half: `ny_am` 10.75→15.0pt,
`london` 3.75→5.0pt — consistent with the SPEC's own band-width-doubling
note; a period-specific bar is a candidate refinement, not built here.)

**Object (b), population collapse** (`height=0.0`):

| retrace | half 1 n | half 2 n |
|---|---|---|
| 0.236 | 52 | 87 |
| 0.382 | 21 | 42 |
| 0.5 | 5 | 10 |

Same order of magnitude in both halves (versus thousands under `body` mode:
2,329 / 2,486 qualified in the same two halves) — the collapse is not an
artifact of one regime or period.

---

## Virgin-span check

No calendar span past this table's sealed end (2026-01-30) is untouched by
both programmes. The M-TABLE/TradingView branch (`origin/claude/tradingview-
mcp-agent-setup-ql18v8`) carries a narrated-day corpus through 2026-06-25,
data pulls dated 2026-07-20, and — beyond research exposure — **live armed
trading**: "ARMING AUTHORIZATION re-issued (ANGUS 2026-08-05)," real order
execution on an eval account, through commits dated today (2026-08-11).
Separately, this repository's own OHLCV data ends 2026-01-30 — no P-TABLE row
is buildable past that date regardless. No new seal declared; not actionable
from this session.

---

## Standing policy recorded (Declarations Entry 3, not a new analysis run here)

- A pass on this table's sealed span reads as **"consistent with," never
  "confirmed,"** given the M-TABLE programme's extensive characterization of
  that era's regime — and does not by itself authorise arming anything.
- **Split-half discipline inside the fit era is now load-bearing** for any
  claim this table produces going forward (derive on one half, attempt to
  kill on the other, report the kill rate) — mirroring the S1 precedent of
  shipping on fit + split-half when a holdout venue cannot cleanly confirm,
  with forward-recorded data as the real confirmation venue.
