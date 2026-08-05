---
date: 2026-08-05
status: greenlit — L0 passed, both branches to L1
tags: [ny-am, failed-auction, amt, dual-sourced]
sources: ["docs/PREREG-failed-auction.md", "research/findings/orochi-diagnosis.md", "research/findings/fabervaale-diagnosis.md"]
---

# nya-failed-auction — balance-break fail/succeed event tree (NYA-FA-01)

## Thesis (for Angus)

Price breaks out of a multi-day balance. Half the time the break holds and
trends; half the time it fails, traps the chasers, and their forced exit
fuels a move back through the range. Both intake gurus teach both trades and
neither defines what separates them — that discriminator is our program.

## Trial ledger — NYA-FA-01

### Trial 1 — L0 census (2026-08-05) — PASSED, folklore corrected, both branches advance
scripts/nya_composites.py + scripts/nya_fa_census.py (committed; outputs
force-added). 457 break events on 549 composite-live sessions, 2023-2026.
FINDINGS:
1. FAIL RATE era-consistent: 48-54% fail within 30 min, 59-60% within 120 —
   the picture really does resolve both ways near-evenly. No era flip.
2. THE "80% RULE" IS DEAD AS TAUGHT: after a fail, price traverses to the
   composite's FAR edge only 12-21% of the time (era-split 12/21/20). Even
   reaching the composite POC is only 46-57%. The published falsification
   (27-67%) was generous — on honest multi-day composites the far-edge
   target is folklore. CONSEQUENCE: the fail-branch L1 expressions target
   POC (not the far edge) and get judged on geometry, per prereg.
3. "TIME AND SPACE" IS VIBES: minutes-spent-outside shows ZERO
   discrimination of traverse odds (16/19/12% across terciles). The
   load-bearing discretionary concept of both gurus fails its first
   mechanical test.
4. DEPTH IS SIGNAL: max extension beyond the edge before re-entry
   discriminates cleanly — deep excursions that then fail traverse to the
   far edge 23% vs 8% for shallow (POC-traverse 55% vs 43%). Directionally
   confirms the trapped-mass mechanism: the further they chased, the harder
   they unwind. This is the declared discriminator search's first live wire.
5. ACCEPT SIDE IS BIG: accept days run a median 1.26 composite-widths of
   continuation; 91% reach 0.5 widths. CAVEAT logged: partially definitional
   (accept = no re-entry, so extension is survivorship-tinted); the honest
   L1 test is entry on the broken-edge retest AFTER the window expires.
STATUS: census PASSED for the family premise (both resolutions frequent,
era-stable, mechanism-consistent conditioning signal exists). ADVANCING to
L1 mechanics: fail-branch (enter on re-entry close, target POC, stop beyond
excursion extreme) and accept-branch (edge-retest continuation) — each with
declared cost stacks. Flow-at-entry discriminator search (delta at break,
absorption at edge on re-entry, CVD divergence outside, trapped-volume
estimate) follows L1, on the flow span. Family arm count: 1 (census).

### Trial 2 — L1 mechanics + depth cut (2026-08-05) — raw ugly as expected, depth separates
scripts/nya_fa_l1.py (window-partition bug found and fixed mid-trial —
first run mis-assigned late re-entries to the fail branch; corrected run is
the record). Raw fail branch (n=248, full span): PF 0.80-0.88, negative all
eras — NO KILL LEGAL (§3.2; raw substrate expected ugly). Accept branch raw
(n=62): flat (PF 1.02-1.04). Depth tercile on F2: WR 12% shallow → 59% deep;
deep points-positive but fixed-risk dollars negative — the euro-handoff
geometry disease (natural stop at the excursion extreme too wide). Declared
cures queued: tighter-stop arms + flow gates. Arms this trial: F1, F2, A1
(+3; family count 4).

### Trial 3 — flow-at-entry discriminator search (2026-08-05, flow span) — LIVE CELLS FOUND
scripts/nya_fa_flow.py (events in output/nya_fa_flow_events.parquet). 71
fail events, 2025-06..2026-07. Gates as declared: G1 edge-absorption fires
1% — dead as defined (looser variants would be NEW declared arms, not
silent retuning); G2 excursion-delta-opposes-break fires 66% and improves
every stop; G3 CVD-divergence fires 89%, mild help. Depth again the
strongest single conditioner. Stop geometry: S2 (0.5x excursion) fixes the
dollars. LEADING CELLS: deep+G2/S2 — n=28, WR 46%, +647 pts, $+984,
PF 2.06, survives strict friction (PF 1.99); deep+G3/S2 — n=34, +755 pts,
$+1,893, PF 2.14. Halves −109/+364..373/+392..492: the negative leg is
June-2025 only (partial month, tiny n) — flagged, not hidden. CAVEATS: n=28-34
(§2.2); flow gates exist only on the 13.5-month flow span; depth replicates
on the full candle span (census trial 1) which is the family's structural
anchor. Arms this trial: G1/G2/G3 x S1/S2/S3 + deep-combos = 9 (family
count 13; all count in DSR). NEXT: exit-arm tournament on the leading
cells, accept-branch conditioning, then grading.
