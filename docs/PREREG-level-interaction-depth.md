# PRE-REGISTRATION — NYA-LVL-01 — the depth pass

**Committed BEFORE any depth column is joined.** Authorised by Angus 2026-08-05.
Fit span only. **Sealed 2023/24 not touched. Holdout look: NO.**

## Why

Bar-only variables are measured and exhausted: base 56.9% at 1.0R, best single
lift **+2.7pp**, ceiling ~60%. §5.12.10 says where the edge actually lives in this
programme: **depth carried the ENTIRE canon edge (+0.5 to +1.3R); flow at entry was
a rounding error.** Depth has never been tested on this family.

## Objective — win rate at a payoff worth having

**Scored on win rate at FIXED R, not profit factor.** PF rewards a trivially-close
target (S40/T15 scored 79% and was 0.375R). Two objectives, both reported:

- **1.0R** — stop 15, target 15. Break-even 50%. Base **56.9%**.
- **1.5R** — stop 15, target 22.5. Break-even 40%. Base **44.9%**.

## Data and its limit, stated before use

`data/reference/depth_2025/*_ny.csv` + `depth_2026/*_ny.csv` — 253 days, long form
(ts, side, price, size), **08:00–10:29 ET only**. Our entries run 09:45–15:45, so
**only the 09:00 and 10:00 hours are covered — ~1,936 of 4,548 events (43%)**.
Everything after 10:29 is uncovered and **stands down** (NaN), never counted as a fail.
Any result here is a statement about the first ninety minutes of RTH, and the card
says so.

## The checks — canon definitions, canon thresholds, nothing fitted here

Direction-resolved first (§4.2): `behind`/`ahead` are relative to the trade.

| check | definition | threshold source |
|---|---|---|
| `W` | no wall behind | canon, as shipped |
| `D` | a wall ahead exists | canon, as shipped |
| `WALLSZ` | `D` and ahead size ≥ 7 | canon, as shipped |
| `IMBWITH` | book imbalance favours the trade | sign test at 0 |
| `THICKHI` | total thickness above the **2025** median | split frozen on discover era |

**§5.12.10 v2 correction carried:** `W`/`D` are **displacement geometry, not wall
detection** — `W=1` means the entry sits beyond the visible ladder. That is how they
will be described, not as "no big resting order".

## Protocol — §5.12.2

Each check **ALONE** at its frozen threshold. **NaN stands down.** Fewer than 30 a side
in an era = `thin`, no verdict. **Survival requires a positive win-rate lift in BOTH
eras at BOTH objectives.**

## Null, budgeted from the start

Placebo levels, identical grammar, the **whole 5-check × 2-objective search** re-run,
100 permutations, family-wise max. Bar **p ≤ 0.01**. A depth result that cannot clear
its own selection correction does not count — the `W` result on London died exactly
that way today.

## What this may not do

May not promote. May not kill the family. May not add checks — list closed.

## Artifacts

`scripts/nya_lvl_depth.py` · `output/nya_lvl_depth.md` · ledger rows · FUNNEL card.
