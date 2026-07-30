# Determinism audit — London pipeline (Stage 1 gate)

**Fit only. Sealed 2023/24 never loaded.**

## Verdict

**The London dedup IS order-dependent. It does NOT currently change any number.**
The invariance is incidental, not structural — it holds by a coincidence of which columns are
excluded downstream, and one added feature would make it a live bug that silently moves the book.

## The site

`scripts/build_l3_features_london.py:105` — `S.drop_duplicates("_k")` with **no ordering key**.
`drop_duplicates` retains whichever row is first in current order, so input row order decides
which sibling survives. Structurally identical to the NY bug fixed in `6edbd3a` (quicksort on
tied fills deciding the day's elite 2.0x slot).

### The key does not identify a trade

Across **581 tied groups / 1,321 rows** sharing `(day, fill-minute, direction, entry)`:

| column | groups differing within the group |
|---|---|
| risk | 335 of 581 |
| dollars | 327 of 581 |
| stop | 325 of 581 |
| exit_price | 306 of 581 |
| exit | 222 of 581 |

The L3 docstring asserted "features depend only on (day, fill, exit, direction, entry)" — but the
key was built WITHOUT `exit`, and that claim was never verified. It was reasoning presented as
fact. This audit is what verification looks like.

## Why no number moves — verified, not argued

The feature loop reads exactly five per-row columns: `day`, `fill`, `exit`, `direction`, `entry`.
Four are in the key. The only non-key read is `exit`, which feeds only `hold_min` — and
`hold_min` is in `PASSTHRU`, so it is **excluded from the 40 carried feature columns** (checked:
`hold_min in fcols` -> False).

`london_depth.depth_at` reads `day`, `fill`, `entry`, `direction` — all in the key.

`risk`, `dollars`, `R`, `stop` are carried **per-row from `S`**, not from the deduped frame, so
each row keeps its own outcome. That is why the L4 book, the 9.5pt floor and `room_R` are
unaffected.

## Other reachable tie-break sites

| site | class | status |
|---|---|---|
| `london_depth.py:68,72` | `above["size"].idxmax()` / `below[...].idxmax()` — wall level by max size, ties by position | REACHABLE, tie frequency unmeasured |
| `london_matrix.py:125` | `w.high.idxmax()` / `w.low.idxmin()` on equal extremes | REACHABLE, tie frequency unmeasured |
| `funded_book.py:160` | `groupby("day").base.first()` | SAFE — line 99 sorts stably first |
| `l4_select.py:67` | `sort_values([...], kind="stable")` | SAFE — already explicit |
| `build_l1/l2` sorts on `mi`/`ts_event` | unique per bar, no ties | SAFE |

## Required fix before stages 2-4 consume these features

1. Add `exit` and `stop` to `_k` so the key identifies a trade.
2. Make the dedup explicitly ordered: `sort_values(key_cols + ["ts"], kind="mergesort")` before
   `drop_duplicates`, so survivor selection is defined rather than incidental.
3. Resolve the two `idxmax`/`idxmin` sites with an explicit secondary sort key.

This changes the unique-input count from 4,848 and requires re-running L3 features for both
spans. Every downstream number then reproduces under permutation by construction instead of by
luck.

## Scope not completed

The full 20-seed x varying-`--procs` end-to-end permutation test was NOT run: each permutation
requires a complete L3 rebuild (~10 min/span). The analysis above establishes invariance by
tracing every column the loops read against the key, which is stronger than a sample of 20
permutations would be for the dedup specifically — but it does NOT cover the two `idxmax` sites,
whose tie frequency remains unmeasured. Reported as incomplete rather than passed.
