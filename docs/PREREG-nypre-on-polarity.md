# PRE-REGISTRATION — nypre-on-polarity + nypre-open-sweep-fade (family NYP-POL-01)

Filed per docs/VALIDATION-PROCESS.md §1, before any census. Theses:
research/candidates/nypre-on-polarity.md, nypre-open-sweep-fade.md (greenlit
ANGUS 2026-08-04). One trigger event, two branches → ONE trial family.

## Claims (falsifiable)

1. **Polarity**: the 09:30 open's position vs the overnight midpoint predicts
   which overnight extreme (ONH/ONL) breaks first in RTH, at a base rate
   materially above 50% on 2025–2026 data (published claim: ~76% on 2015–2025;
   our census re-bases it post-regime-change).
2. **Sweep**: when the first 15 min of RTH instead break the NON-predicted
   extreme by a small increment (<25% of ON range) and close back inside, price
   subsequently rotates back through the pre-market VWAP at an elevated rate —
   the unpublished conditional.

## Family / inputs / session

Family: overnight-structure. Inputs: ON range/midpoint (18:00→09:29), 09:30
open location, first-break side and time, PM VWAP. Session: ny-pre approach +
RTH first hour (BOTH variants tested: flat-by-09:29 entry and carry-through;
the carry variant needs Angus's execution-semantics ruling BEFORE ship, not
before test). Entry type at L0: none — base-rate census only.

## Eras / census spec

2025 and 2026 (Jan–Jul) separately; 2023/24 untouched (holdout = six sealed
months, declared look only). Census: per day, ON range and midpoint; open
location (half and third); first ON extreme broken in 09:30–16:00 and minute;
P(predicted side first | location); sweep sub-census per claim 2 with reversal
magnitude. Windows × location-buckets = one ledgered family.

## Bars / kills

§2 defaults. Kills: (1) polarity base rate < 60% in either era (materially
below the published 76% = the stat didn't survive the regime/publication);
(2) era flip; (3) sweep-reversal rate not distinguishable from the
all-first-breaks base rate; (4) fragility per §2.5.

## Known limits

No costs at L0. The published stat's sample (2015–2025) overlaps its own
publication (late 2025) — our 2026 era is the only clean post-publication read;
weight it accordingly.
