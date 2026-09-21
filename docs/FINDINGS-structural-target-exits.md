# FINDINGS — STRUCTURAL-TARGET EXITS, four variants

2026-08-07. Target reconstructed to a price: `target_px = entry + d ×
next_lvl_R × risk`. First-passage scoring throughout, same-bar → stop wins.
Primary population: room-gated LONDON reject 3m/5m. Incumbent as reference
only. **Report-only.**

## 0 — THE AUDIT YOU ASKED FOR, answered directly

**No prior report was touched by the missing-stop defect.** Three
independent confirmations:

1. **It was a persistence bug, not a computation bug.** sweep_b's
   `out_ship` in the London feature frame is **identical to the sweep
   census's** (393/393 rows, atol 1e-9) — and the census *has* the stop
   column. The outcome was always computed with a real stop; only the
   column failed to survive the write into the feature frame.
2. **`scripts/fixed_target.py` was the only report-time consumer of a
   `stop` column on those frames.** Every other hit in the codebase is a
   *builder* working on its own upstream substrate (`stop_initial`), not on
   the London feature frame. The defect had no other reader.
3. **The published numbers reproduce exactly from the current frames.**
   Incumbent LONDON: EV **+0.357** (BR-23 published +0.357), worst day
   **−5.41** (BR-25 published −5.41). Frequency reads 2.27/day against a
   published 2.28 — that is a 291-vs-292 day-count convention, not a data
   difference.

And this run adds a fourth, stronger check: **control C2 recomputes V1 from
raw bars and matches the stored `out_ship` column to `0.00e+00` on every
incumbent row.** The shipped pipeline is intact. FINDINGS-H, the
combination run, and everything upstream stand as published.

## CONTROLS

| control | result |
|---|---|
| **C1** For the incumbent the trigger TF *is* 15m, so V2 must reproduce V1 exactly | max \|V1−V2\| = **0.00e+00** — PASS |
| **C2** V1 recomputed from bars vs the stored `out_ship` | max diff **0.00e+00** — PASS |
| **C3** worst single trade ≥ −(1 + max cost_R), all three books | passes exactly at the bound |

## 1 — THE FLOOR SWEEP IS DEGENERATE ON THE PRIMARY POPULATION

The room-gated book is *already* gated on `next_lvl_R ≥ 3R OR open`, so
every non-open row is ≥3R by construction and the 1.5R / 2R / 3R floors
select **the identical 247 (3m) / 208 (5m) rows**. The sweep has no range
there. Re-run on the **ungated** London reject population, where it does:

| TF | floor | n | shipped EV | day-boot 95% |
|---|---|---|---|---|
| 3m | 1.0R | 743 | −0.033 | [−0.178,+0.114] |
| 3m | 1.5R | 549 | +0.026 | [−0.143,+0.205] |
| 3m | 2.0R | 430 | +0.062 | [−0.139,+0.267] |
| 3m | **3.0R** | 247 | **+0.203** | [−0.080,+0.495] |
| 3m | 4.0R | 159 | +0.002 | [−0.324,+0.334] |
| 3m | 5.0R | 110 | −0.088 | [−0.426,+0.312] |
| 5m | every floor 1.0–5.0R | — | **−0.15 to −0.43** | never clears |

**Non-monotone, peaks at exactly the declared 3.0R, then collapses — and
does not replicate at 5m at all.** That shape is what a tuned threshold
looks like, not a gradient.

## 2 — THE FINDING: the room gate was two claims bundled, and only one works

`next_lvl_R ≥ 3R OR open space` is not one condition. Priced separately:

| book | component | n | EV | H2-2025 | H1-2026 |
|---|---|---|---|---|---|
| ROOM 3m | **open space** | 87 | **+1.518** | +1.294 [+0.571,+2.031] **!** | +1.852 [+0.853,+2.847] **!** |
| ROOM 3m | ≥3R room | 247 | +0.203 | −0.005 [−0.394,+0.435] | +0.403 [+0.031,+0.779] ! |
| ROOM 5m | **open space** | 100 | **+1.376** | +1.248 [+0.621,+1.955] **!** | +1.526 [+0.866,+2.103] **!** |
| ROOM 5m | ≥3R room | 208 | −0.053 | −0.072 | −0.034 |

**Open space clears both eras on both timeframes. The ≥3R threshold clears
neither era at 5m and only H1 at 3m.**

The gate's value is **"is there an obstacle at all"**, not "how much room".
That also explains the non-monotone sweep: there is no gradient in room,
only a binary. It is 5.8–7.0% of the ungated population carrying the whole
effect.

**This qualifies BR-32 and BR-35.** The room-to-run finding stands as a
finding, but its *mechanism* is not the one stated — and the component that
works is a much smaller, much stronger population than the gate implied.

**It also constrains this pass structurally:** V3 and V4 need a level to
target, so **the structural variants are only defined on the weaker half**
of the population. Stated before the verdict, not after.

## 3 — THE FOUR VARIANTS, on the level-ahead half

| | ROOM 3m (n=247) | ROOM 5m (n=208) |
|---|---|---|
| V1 shipped 75%@3R + 15m trail | +0.203 | −0.053 |
| **V2 3R + trail on trigger TF** | **+0.285** [+0.023,+0.546] | +0.032 |
| V3 structural, full close | +0.154 | −0.222 |
| **V4 structural 75% + TF trail** | **+0.406** [+0.092,+0.731] | +0.025 |

Decomposition at 3m, which isolates what each change does:

- **trail re-anchor alone** (V2 − V1) = **+0.082**
- **structural target on top of it** (V4 − V2) = **+0.121**
- **structural target WITHOUT a trail** (V3 − V1) = **−0.049**

> **The level is a good place to take size off, not a good place to be
> flat.** Full-close-at-the-level is *worse* than shipped. The structural
> target only pays when the trail is kept for the remainder.

## 4 — THE WHOLE BOOK, and the change that actually earns its place

Open-space rows have no structural target, so the practical rule is: V4
where a level exists, V2 where it does not. Scored on the full book:

| book | variant | EV | R/day | worst | max size | SIM grad | LIVE $/yr |
|---|---|---|---|---|---|---|---|
| ROOM 3m | V1 shipped | +0.546 | 0.624 | −4.60 | $400 | 87.7% | $17,318 |
| ROOM 3m | **V2 3R + TF trail** | +0.555 | 0.635 | −4.60 | $400 | **94.0%** | **$19,463** |
| ROOM 3m | HYBRID (V4/V2) | **+0.644** | 0.737 | −4.60 | $400 | 94.4% | $18,766 |
| ROOM 5m | V1 shipped | +0.411 | 0.434 | −6.65 | $300 | 57.7% | $9,262 |
| ROOM 5m | **V2 3R + TF trail** | +0.462 | 0.487 | **−5.65** | **$350** | **74.1%** | **$12,832** |
| ROOM 5m | HYBRID (V4/V2) | +0.458 | 0.483 | −5.65 | $350 | 67.3% | $11,288 |
| INCUMBENT (ref) | V2 ≡ V1 | +0.357 | 0.813 | −5.41 | $350 | 98.5% | $28,613 |
| INCUMBENT (ref) | HYBRID | +0.161 | 0.366 | −3.32 | $600 | 58.4% | $11,249 |

**V2 is the change that earns its place.** Same trades, same frequency, no
new parameter — just the trail referencing the timeframe that generated the
trigger. It improves *every* axis on both room books: 3m graduation
87.7% → **94.0%** and live +12%; 5m graduation 57.7% → **74.1%**, live
+38%, and worst-day R improves enough to lift max size $300 → $350.

**The hybrid does not survive its own test.** Paired day-clustered CI on the
per-trade difference vs shipped: 3m **+0.099 [−0.049,+0.249]**, 5m **+0.047
[−0.083,+0.164]** — neither clears. And it *costs* graduation at 5m
(74.1% → 67.3%) because full-sizing off at a nearer level truncates the
tail that carries the book.

**On the incumbent the hybrid is clearly worse** — −0.196 [−0.276,−0.121],
clearing *negative*. Expected, and a good sanity check: the incumbent's
median `next_lvl_R` is **0.54R**, so a structural target there is a
half-R target. Structural targets are only coherent when levels are far in
R terms, which is the tight-stop regime.

## VERDICT

1. **Re-anchor the trail to the trigger's timeframe.** It is free, it is the
   only change that improves every axis on both room books, and the
   incumbent control confirms it is a no-op where the trigger already is
   15m. This is the answer to the BR-50 inconsistency.
2. **The structural target is not adopted.** It adds EV at 3m but fails its
   paired test, hurts 5m graduation, and is strictly worse on the incumbent.
3. **The room gate needs restating.** Its value is the open-space subset
   (+1.4 to +1.5R, both eras, both timeframes), not the ≥3R threshold —
   which is non-monotone, peaks at the declared value, and does not
   replicate across timeframes.

Nothing is adopted from this pass. Item 3 in particular deserves its own
declaration before anything is built on it — it is a fit-side decomposition
of a gate I had already published.
