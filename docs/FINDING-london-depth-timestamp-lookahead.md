# FINDING — the London depth snapshot is stamped ~60 seconds before it was observed

**Found 2026-08-06** during the Phase 4 flow-feature inventory, using the
`orderflow-construction` skill's triage gate. No trials charged. Sealed span untouched.

---

## The finding

`data/reference/depth_london/*.csv` carries two clocks. `ts_event` sits **exactly** on
every minute boundary, which reads as a clean per-minute sample and is how every consumer
has treated it. `ts_recv` says otherwise:

```
ts_recv - ts_event   median 59.889s | p1 58.193s | 95.9% inside [59s, 60s) | min 56.0s
ts_in_delta (matching-engine -> capture latency)   ~13 microseconds
```

A 60-second gap is not network latency. **`ts_event` was floored to the minute at
extraction.** The row labelled 08:15 is the book at **08:15:59.9** — the END of minute
08:15, not its start.

**Consequence: a decision at minute M that reads the row labelled M gets the book as it
stood ~60 seconds after the decision.** That is a lookahead, and it is invisible — the
timestamps look immaculate, the values are real quotes, and no downstream check can see
it. It is the same defect class as LDN-ATC-01's LTA gate and LDN-SWP-01's group P, with
one difference that matters: **the §2.5 window-causality bar does not catch this one.**
That check audits *declared* windows and takes `close_time(W)` from the declaration. A
declaration saying "book snapshot, closes at Rel(0)" is certified clean while the
underlying stamp lies. **A causality bar cannot detect a lying timestamp.** Catching this
needs a data-layer assertion against a second clock — which is what `ts_recv` is, and
what `src.engine.book.load_depth` now asserts on every load.

## Affected code

Four modules index the London book by `ts_event` and inherit the ~60s lookahead:

| file | how | note |
|---|---|---|
| `scripts/london_depth.py` | `depth_at(dep, minute)` takes `dep.ts <= minute`, `ts` from `ts_event` | **also anchored at the FILL** — line 115 passes `t.fill`, not the decision minute. A limit fill requires price to have travelled to the order, so the book read contains the answer. Two hazards stacked |
| `scripts/london_obk_flow.py` | `searchsorted(entry, "right") - 1` on a `ts_event` index | **FIXED** in this change — routed through `src.engine.book` |
| `scripts/depth_walls.py` | floors `ts_event` to the minute and indexes on it | feeds `output/depth_minutes.parquet` |
| `scripts/build_l3_features_london.py`, `scripts/run_intrade_replay.py` | read `ts_event` directly | not audited in detail |

Downstream artifacts carrying `dep_*` / `book_imb` / `wall_ratio_opp` columns
(`output/london_matrix.parquet`, `output/london_obk_depth.parquet`,
`output/london_obk_flow.parquet`, `output/depth_minutes.parquet`) inherit it.

`src/canon/features.py` has the same `depth_at` shape on the NY side. Stated as a fact;
not analysed here, which is London-scoped.

## What it does NOT invalidate

- **No graded London verdict rests on it.** The six graded families are LDN-SWP-01,
  TRAP-01, VWAP-01, VT-01, DEF-01 and FLOW-01, plus ATC-01 at L1. Of these, only
  **LDN-DEF-01** reads the book — and it reads the *footprint*, not the depth snapshots,
  with its own `assert max(mins) <= t` on every event. DEF-01 is unaffected and remains
  the worked example for causal construction.
- **The sealed span is untouched.** `depth_london_2023_24` was not opened.
- **It is a lookahead, so it can only INFLATE apparent edge**, never suppress it. Every
  depth-conditioned result that came back null stays null; a depth-conditioned result
  that looked good is the one that needs re-measuring. As it happens, none of the graded
  families have one.

## The other thing this settles

Measured against the *label*, `close(ts_event=T) ≈ mid(label T)` at median 0.375 pts,
which reads as the bar master being END-labelled and directly contradicts both
`data/reference/parity_slice_feb2026.md` and the LDN-ATC-01 bar-label correction.

**Against the true time the contradiction dissolves.** Label T is the book at the close
of the bar covering [T, T+1), so the bars are **START-labelled exactly as documented**.
Two independent anchors agree once the floor is undone:

- footprint trades stamped `ts_minute=T` fall inside bar `ts_event=T` on **98.1%** of
  42,230 minutes, against **17.5%** for the alternative;
- `open(ts_event=T) ≈ mid(label T-1)` at median 0.500 pts.

**The prose was right and the depth timestamp was the liar.** The LDN-ATC-01 bar-label
correction stands unchanged, and so does its verdict.

## Fix

`src/engine/book.py` is the chokepoint. It indexes by `ts_recv - ts_in_delta` (true
observation time), refuses any extraction whose label/recv lag is not the ~60s floor
signature — because on a genuine per-instant sample the correction would itself be a
60-second error — and `features_at()` raises rather than returns when handed a
label-indexed frame. Pinned by `tests/test_book_construction.py`.

Remaining migration, not done here because it would change committed artifacts:
`scripts/london_depth.py` (and its at-fill anchor), `scripts/depth_walls.py`,
`scripts/build_l3_features_london.py`, `scripts/run_intrade_replay.py`.
