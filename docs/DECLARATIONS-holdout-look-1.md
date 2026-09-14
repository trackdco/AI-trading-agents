# DECLARATION — HOLDOUT LOOK #1 (bar-only venue)

**AMENDED 2026-08-07** to the PER-SESSION WINDOW BOOK, before any sealed
row was read. The superseded version (commit 13e79a2f) declared the
all-session composite; that is not the book the trader would trade, and
validating a population you will not trade is the same component-vs-
composite error R1 exists to prevent, on a different axis. The original
text is preserved in git history.

Items 1–3 and the per-session re-scoring are committed and on the record.
**No sealed row has been read.** This look spends the bar-only venue
(23 months, ~±4pp); the flow venue remains unspent.

---

## R0 — the UNSELECTED base population is what gets tested

Unchanged. No selection layer goes to the holdout — not S1, not CONCORD,
not a depth cut. A pass or fail on a selected book cannot separate the
POPULATION from the CUT, and there is no second venue afterwards. Selection
layers ship on fit + forward validation via the seven-locus recorder.

## R1 — per-session books, declared separately, never pooled

The trader's tradeable windows are **London 03:00–04:59** and
**NY 08:00–10:30 NY**, and each session is scored, selected and
risk-budgeted on its own. **Three separate claims. No pooled window book,
no averaging across sessions.**

Fit-side base rates (unselected, X=0.5W, shipped exit):

| book | composition | fights/day | EV | H2-2025 | H1-2026 |
|---|---|---|---|---|---|
| **LONDON** 03:00–04:59 | composite + sweep_b | 2.28 | **+0.357** | +0.347 ! | +0.370 ! |
| **NY_PRE** 08:00–09:29 | composite only | 0.86 | +0.286 | +0.343 ! | +0.221 |
| **NY_AM** 09:30–10:30 | composite only | 1.36 | +0.171 | +0.115 | +0.237 |

`!` = day-boot CI clear of zero. **sweep_b is included in LONDON ONLY**, on
two grounds declared before this look: its NY cell is era-asymmetric
(H2-2025 +0.247 clears, H1-2026 +0.095 does not) while its London cell
clears both, and it is conditioned on a prior stop-out — a conditionality
not carried into the session that would otherwise supply most of the
frequency.

**Declared expectation, stated now so a fail is not rationalised later:**
LONDON is the only one of the three whose base rate clears both eras on
fit. NY_PRE clears one era, NY_AM clears neither. A NY_PRE or NY_AM fail on
the holdout is therefore **predicted**, and will be recorded as
confirmation of a known fit-side weakness, not as new information.

## R2 — registered claims and the multiplicity correction

| # | claim | population | bar (per block) |
|---|---|---|---|
| H1 | LONDON base rate | London window book, unselected | EV > 0, ×5-corrected day-boot lower bound > 0, each block |
| H2 | NY_PRE base rate | NY_PRE book, unselected | same |
| H3 | NY_AM base rate | NY_AM book, unselected | same |
| H4 | sweep_b LONDON base rate | London sweep_b component alone | same |
| H5 | closeloc cut (queued since D1) | reject-arm first-of-fight book | lift ≥ +0.04R, ×5-corrected CI excluding zero, each block |

**Bonferroni ×5**, stated now. H4 is carried separately because sweep_b is
the newest population and the one whose inclusion is a live decision; if
H1 passes and H4 fails, the London book is re-declared without it.

## R3 — two blocks, both must pass

- **Block A:** 2023 bar-only months (2023-01..06, 08, 10, 12 — 9 months)
- **Block B:** 2024-01..2025-05 bar-only months (14 months)

A claim passes only if it clears in Block A **and** Block B independently.
One-block passes are misses.

⚠ **Power caveat, declared in advance.** These books are 0.86–2.28
fights/day. Across 23 bar-only months the NY_PRE book will carry on the
order of a few hundred fights split across two blocks. **NY_PRE and NY_AM
may be UNDERPOWERED to clear a ×5-corrected two-block bar even if their
true edge equals the fit estimate.** That outcome is recorded as
UNDERPOWERED, not as a fail, and the threshold for calling it is declared
here: fewer than 100 fights in a block ⇒ that block reports
UNDERPOWERED and the claim is neither passed nor failed.

## R4 — aggregation rule, fixed in advance

1. Sealed tables built by the SAME committed builders
   (`htf_ma_level_census.py`, `htf_ma_sweep_locus.py`), same commit, no
   variant; SHA recorded in the look's log.
2. Entry gate must PASS on the sealed build before any row is read.
3. Unit: the 18:00-anchored session day. Windows applied by NY clock time
   exactly as on fit (London 180–299, NY_PRE 480–569, NY_AM 570–630
   minutes).
4. Fights: structural, X = 0.5W — **not re-tuned on the holdout**, and the
   X-sensitivity is not re-run there.
5. Point estimate: mean out_ship over first-of-fight rows, per session.
6. Interval: day-level bootstrap, 2,000 draws, seed 20260807, percentile,
   widened to the ×5-corrected level.
7. Named builder exclusions only.
8. **One look. No re-runs.** A failed claim is a miss.

## R5 — what a pass and a fail each MEAN (declared before seeing either)

The sealed span is **bull-heavy** and the book's components carry a
measured negative EV-vs-market slope (−0.0155R per 1% NQ month, CI
[−0.0207,−0.0063]).

- **PASS** is strong: the book cleared in the regime least favourable to
  it, and no regime caveat survives.
- **FAIL** is ambiguous and is pre-committed to be recorded as such — it
  cannot separate "no edge" from "edge, wrong regime". It does not kill the
  population; it sends it to forward validation with the regime caveat
  attached, and the fail is permanent for this venue.

## R6 — the risk budget is per session, and it is part of the declaration

Measured on fit: the daily total R per session book against the $2,000 EOD
drawdown expressed in R at each size. **Maximum non-breaching size per
session, declared:**

| book | worst fit day | $150 | $300 | $450 | $600 | **max safe size** |
|---|---|---|---|---|---|---|
| LONDON | −5.41R | ok | ok | 2 breach days | 10 breach days | **$300** |
| NY_PRE | −3.48R | ok | ok | ok | 1 breach day | **$450** |
| NY_AM | −3.07R | ok | ok | ok | ok | **$600** |

These caps are fit-derived and are **not** validated by this look; they are
recorded so that a holdout pass is not read as licence to size beyond the
fit-measured single-session breach point.

## R7 — standing constraints

Flow venue unspent. Break-arm candidate sets still wait on the base
population. Funded-layer optimisation parked. Selection layers (S1,
CONCORD, closeloc, depth) do **not** enter this look except H5, which was
queued before the per-session work and is carried to pay its multiplicity
here rather than separately.
