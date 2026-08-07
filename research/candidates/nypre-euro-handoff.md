---
date: 2026-08-04
status: killed
tags: [ny-pre, session-structure]
sources: ["articles/sweep-2026-08-04-nypre-stats.md#T2", "articles/sweep-2026-08-04-nypre-structure.md#S7"]
---

# nypre-euro-handoff — trade the Europe→US handoff the ALN numbers describe

## Thesis (for Angus)

The best-measured concept in the entire pre-market file: classify how London
treated the Asia range, at 08:00 ET. When London broke the Asia high but held
the Asia low ("partial engulf up" — 41% of sessions), NY goes on to break that
pattern high 80.8% of the time; the mirror runs 75% — two independent datasets
(2,542 and 4,262 days) agree, and the edge degrades ~30 points if the wrong
side breaks first, giving a built-in invalidation. Meanwhile 08:00–09:30 is
Europe's afternoon squaring window, so the handoff often starts with a partial
retrace as European desks book profits — that retrace is the entry location,
not a contradiction. Wrong side: the US pre-market fader calling a
Europe-established trend "extended" at 08:30. This is also the candidate most
likely to twin with your canon's pre entries (with-trend pullbacks, same
clock) — the redundancy check against the canon's actual fills decides whether
it's a strategy or a rediscovery.

## Skeleton

08:00: ALN classification from session boxes. Engulf-up → buy 08:00–09:30
pullbacks toward London mid / premarket VWAP, target the pattern-high break;
stop under London low; invalidate/flip if the wrong side breaks first.

## Flags

- Candles-only. Target break often lands post-09:30 — semantics ruling needed
  for the carry variant; a flat-by-09:29 variant tests separately.
- Canon redundancy: **HIGHEST of the nine** — pairwise vs canon pre fills is
  the first gate, before any other work.
- Stats are public with TradingView tooling (2024–26 audience growth) —
  recency-weighted decay check mandatory.

## Trial ledger — NYP-EUR-01
### Trial 1 — L0 census (2026-08-04)
ALN base rates re-based on 2025–26: engulf-up → pattern-high first 68.6%
(n=105) / 76.9% (n=65) — PASSES both eras. Engulf-down → 66.2% (n=74) / 60.5%
(n=38) — 2026 marginal, survives the 60% kill by half a point. Published
80.8/75.0 → measured lower but well above coin. Status: census PASSED →
MANDATORY next gate: pairwise redundancy vs the canon's actual pre fills
before any L1 work (highest-overlap candidate by design).

### Trial 2 — canon-redundancy gate (2026-08-04) — PASSED
Against the canon's actual 227 pre fills (fit span): canon trades on only
44/126 engulf-up and 34/85 engulf-dn days (the handoff fires ~3× more often);
on engulf-up days canon long-share is 40% vs 47% base (leans AGAINST the
pattern, not with it); engulf-dn short-share 66% (moderate alignment — flag
for concurrent-risk check at L1). The handoff is NOT the canon rediscovered.
Status: ADVANCING to L1 mechanics (both flat-by-09:29 and carry variants).

### Trial 3 — L1 mechanics, first expression (2026-08-04)
08:00 entry, target pattern extreme, stop opposite extreme, carry: WR 66/69%
and POSITIVE POINTS (+130/+164) but NEGATIVE R and dollars (−$871/−$1,184 at
$160-risk) — wins are small relative to the enormous far-extreme stop. The
race odds are real; this expression's geometry is uneconomic. Status:
REFINING — next trials: stop at London mid (not far extreme), pullback
entries, partial targets. Expectancy kill fires if geometry trials fail.

### Trial 4 — geometry refit (2026-08-04) — FAMILY KILLED
London-mid stop, on-side entries: −$1,261/−$1,885 at $160-risk base friction —
negative dollars both eras again (second failed expression). Declared
expectancy kill fires. TOMBSTONE: the 66–77% pattern-side race odds are real
but priced at any post-08:00 entry; wins pay too little per unit risk under
every geometry tried. Same lesson as polarity: published base rates without a
trapped counterparty don't convert. Reopening burden: a fresh-declared
expression positive in both eras net of costs (family trial count stands).

### Trial 5 — KILL VACATED, process correction (ANGUS 2026-08-04)
Trial-4 expectancy kill predated the flow cross-check — premature under the
amended §3.2 kill-class rule. PREMISE stands (68–77% engulf-up both eras;
redundancy gate passed). Status: REOPENED — owed search: flow-at-entry
conditioning (does the 08:00 tape confirm the pattern side?) × geometry.

### Trial 6 — flow search complete (2026-08-04) — FINAL KILL, legally earned
London-delta flow gate finds REAL signal: far-stop confirmed n=143, WR 78%,
+1,765 pts, PF 1.52 (against: PF 0.58) — but R-economics stay ~zero ($+465 at
$160-risk; avg R +0.02) because the pattern's natural stop is the far side of
a wide two-session range. Mid-stop confirmed: $−422. Risk-capped final arm:
n=5 (structurally empty). Search complete → expectancy kill executes.
TOMBSTONE (final): the handoff is a fact, not a trade — its natural geometry
cannot pay per unit risk. Residue worth keeping: London-delta pattern
agreement (78% WR as a FACT) is a candidate FEATURE for other strategies'
conditioning, not a standalone system. Family arm count (8) stands.
