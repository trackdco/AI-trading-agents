# DECLARATIONS — sealed-span partition and holdout protocol

Declared 2026-08-07, BEFORE any holdout contact and before any Phase 2/3
compute. These four declarations are the Phase 1 block of the cold-start
handoff. No sealed or gray row has been read at declaration time; the sealed
files remain written-unread. Any holdout look that violates a clause below
is void regardless of its result.

## D1 — partition of the sealed span (venue exclusivity)

The sealed+gray span is 2023-01-01 .. 2025-05-31 (sealed 2023-24 by the
original criterion; gray 2025-01..05 assigned to the holdout pool by this
declaration — the band is unlooked, see PHASE0-verification.md item 2).

- **Flow venue (6 months), exclusively for the flow-feature family:**
  2023-07, 2023-09, 2023-11, 2024-03, 2024-04, 2024-10 — the six
  flow-covered blocks fixed in HOLDOUT-2023-24-PREREGISTRATION.md (day-list
  SHA pinned there). Bar-only claims may NEVER be evaluated on these months;
  a bar-only claim that has touched them is void.
- **Bar-only venue (23 months), exclusively for the bar-variable family:**
  every other month in the span — 2023-01..2023-06, 2023-08, 2023-10,
  2023-12, 2024-01, 2024-02, 2024-05..2024-09, 2024-11, 2024-12,
  2025-01..2025-05. Flow claims may never be evaluated here (no flow tape
  exists here anyway — the exclusivity is still declared, not assumed).

Rationale recorded: whichever family looked first at a shared venue would
contaminate the other's only confirmation set.

## D2 — bar-only holdout: two blocks, BOTH must pass

- **Block A:** the 2023 bar-only months (2023-01..06, 08, 10, 12 — 9 months).
- **Block B:** the 2024-01..2025-05 bar-only months (14 months).
- A pre-registered bar-only claim passes ONLY if it clears its declared sign
  and magnitude bar in Block A AND in Block B independently. One pooled look
  is not a pass; a one-block pass is recorded as a miss.

The chronological split is deliberate: it catches internal era-flips that a
pooled look averages away.

## D3 — flow holdout: one look, resolution honestly stated

The flow venue is ~6 months. At the observed event cadence that resolves a
proportion to roughly ±10pp (95%). Therefore, declared now:

- The flow family gets ONE look, batched: every pre-registered flow claim is
  evaluated in a single run; the claim list and their bars are frozen in an
  appendix to this file BEFORE that run.
- Only effects whose declared size is >= +20pp (or the R-metric equivalent
  declared per claim) can be CONFIRMED here. A smaller observed effect —
  whatever its direction — is recorded verbatim as INTERESTING,
  UNCONFIRMABLE AT THIS RESOLUTION and is not argued over, re-binned, or
  re-run.

## D4 — aggregation rule for ANY holdout look (both families)

Declared before either look, applying to every claim:

1. **Substrate:** the holdout table is built by the SAME fixed builder that
   produced the fit table (post entry-price fix, structural clustering) —
   never a variant. Builder SHA recorded in the look's log.
2. **Unit:** the 18:00-anchored session-day is the resampling unit.
3. **Point estimate:** mean of the claim metric, collapsed first within
   structural cluster (Phase 0 item 3 criterion), equally weighted across
   clusters within the block.
4. **Interval:** day-level bootstrap, 2,000 draws, seed 20260807, percentile
   CI. No Wilson-on-rows anywhere in a holdout verdict.
5. **Pass:** the claim's pre-declared sign holds AND the pre-declared
   magnitude bar is cleared at the pre-declared quantile, per required block
   (both blocks for bar-only; the single look for flow).
6. **Boundary convention:** non-enterable events (final-bar decisions,
   gap-through-stop) are excluded by the builder's named exclusions exactly
   as on fit — no holdout-specific handling.
7. **No rescues:** a failed claim is recorded as a miss. Population changes
   after a look are forbidden unless declared in advance and justified
   independently of the result (standing rule restated to bind here).

## Appendix — frozen claim lists (empty until Phase 3 pre-registration)

- Bar-only claims: (none yet — cut-study survivors land here with declared
  signs and bars before any Block A/B contact)
- Flow claims: (none yet — same)
