# BASE-RATE LIBRARY

Every number here is a NULL: a future idea claiming edge on a related
mechanism must beat these, not zero. Fit span 2025-06..2026-07 unless noted.

| # | mechanism | base rate | source |
|---|---|---|---|
| BR-1 | Price displaced ≥0.5W from the 15m BB MA touches it before session close | **89%** (87-91% all side×era cells) | Census A, VERDICT-htf-ma-census |
| BR-2 | ...touch arrives before 1.0W of further extension | **64-66%** (62-66% all cells) — proximity-matched placebo achieves 60-63%, so a "level near price" gets most of this for free | Census A NEXT test |
| BR-3 | True collectable at touch (price's share of the gap) | **69% of the naive gap**; mean +0.38W per touched event | Convergence decomposition |
| BR-4 | Adverse-before-touch | median **0.43-0.44W**, era-stable in W units, NOT in points (the scale law) | Census A |
| BR-5 | **Persistence null (M2):** consecutive failed attempts at the 15m BB MA (n=1→4) do NOT raise the 1W continuation rate — cells wobble 47-65% with no monotone rise, both eras | continuation ≈ **55-60%** regardless of n_attempts | Census B first read; accepted per ANGUS ruling, no encoding search |
| BR-6 | **M2 reject:** first structural target reached before 20t past the trigger-candle extreme | **60-66%** (era-consistent, cluster-collapsed) | Census B verdict |
| BR-7 | **M2 break-and-retest:** retrace to MA after chain-resolving cross **80-82%** (a RACE: retest before the break runs 1W; ever-retest before session close is **93.5%** [92.4,94.6] — Phase 2 item 9); target-before-extreme-stop from the retest entry | **68-75%** — ⚠ the "stronger branch" comparison was computed on a future-conditioned population and is VOID until re-measured arm-separated (cut study) | Census B verdict + Phase 2 restatement |
| BR-8 | **M2 travel skew:** distance travelled away from the 15m MA per rejection | p50 ~1.1-1.3W, p95 3.7-5.3W — tail economics, both eras | Census B verdict |

| BR-9 | **Unselected reject book, adopted exit, executable (first trigger per structural fight):** | **+0.139R / +0.162R by era** (day-boot 95% CIs clear zero both eras AT X=0.5W; pooled +0.149R [+0.076,+0.224]); median fight −0.53R, tail pays. A1 qualifier (2026-08-07): point estimate positive at every clustering width incl. the row limit (+0.10..+0.15 pooled), but era-level CI significance is 0.5W-specific — H2-2025's CI includes zero at all other X | Phase 0 restatement + FINDINGS-A-validation A1 |
| BR-10 | **Collapse-convention sensitivity:** the same book reads −0.04R (cross-cycle collapse, H2) to +0.20R (structural collapse) — any future book claim must name its trade-selection convention or it is not a number | Phase 0 restatement |

| BR-11 | **LEVEL-FAMILY CENSUS — reject arm, executable first-of-fight book, shipped exit, X=0.5W** (no selection). Every locus published, nulls included | bbma15 **+0.149** (both eras clear) · val +0.132 · vwap_m1 +0.122 · vwap +0.111 · vwap_p1 +0.110 · poc +0.084 · vah +0.042 — only the incumbent clears both-era CIs | E1, FINDINGS-E-level-census |
| BR-12 | **LEVEL-FAMILY CENSUS — break arm, same convention** | **vwap_m1 +0.248** and **val +0.234** (both eras clear; vwap_m1 clears at ALL four X) · bbma15 +0.105 · vwap +0.096 · poc +0.094 · vah +0.068 · vwap_p1 +0.054. Union(val,vwap_m1) = **+0.230R at 5.16 fights/day**, both eras clear | E1 |
| BR-13 | **Break arm AT THE INCUMBENT LOCUS (bbma15)** — the arm's own null | **+0.105R/fight**, 4.39/day, positive at all four X but H2-2025 CI never clears zero → fails the BR-9 bar. Combined both-arm book at this locus: **+0.131R at 10.70/day**, both eras clear | E2 |
| BR-14 | **Re-entry after a stop (M2 reject):** unconditional, and under the declared sweep+reclaim filter | unconditional **−0.168R**/attempt; sweep-filtered **−0.143R** [−0.376,+0.107] (12% of 998 candidates) — the filter does not separate. NOTE: the declared sweep definition does not capture the trader's own reference example, so this nulls the DEFINITION, not the concept | E3, A2 |

| BR-15 | **Sweep-reclaim census (item 6), X=0.5W, no selection** — the trader's own definition (reference extreme = the trader's own stop) | (a) standalone sweep+reclaim **+0.070R** (7.81/day, neither era clears — NULL) · (b) **sweep of the OWN STOP after a stopped attempt +0.175R** (12.79/day, both eras clear at ALL four X) → the prior stopped attempt is load-bearing; E3's contrary null was about the definition, not the concept | Item 6, FINDINGS-F |
| BR-16 | **Composite book (union-break VAL/VWAP−1 + reject arm), executable, shipped exit, X=0.5W** | **+0.186R at 11.42 fights/day**, both eras clear (H2 +0.177, H1 +0.196). P(graduate) 100.0% vs 92.3% reject-alone; time-to-first-dollar 31d vs 62d | Item 2 |
| BR-17 | **Direction-skew of the union break book** | EV vs monthly NQ return: slope **−0.0155R per 1% NQ**, CI [−0.0207,−0.0063] — a real downside premium. Still positive in up months (+0.183 [+0.076,+0.290]) as well as down (+0.323). Long side +0.166 [+0.002,+0.329], MDE 0.230 = absence of evidence | Item 1 |
| BR-18 | **Concurrency of the composite book** (the risk-spine null) | peak simultaneous R-at-risk p95 **4.0R**, max 5.0R, **0 of 291 days** exceed the canon's 5.33R budget. Worst days are sequential grind (18 losers of 20 trades at peak 3.0R), NOT overlapping clusters — the old canon's failure mode does not recur here | Item 3 |

| BR-19 | **Flow concordance count** (unweighted count of the 12 flow features agreeing with trade direction, 0-12; ONE candidate, zero free parameters) | Real ranking signal, **no gate value**: Spearman **+0.093 break / +0.129 reject**; bottom bin (CONCORD<=4) **+0.038/+0.049R** vs book +0.186. Max whole-book gate lift **+0.046R** (below the +0.05 bar) and every half-1 survivor dies on half 2. Fails because the WORST flow bin is still profitable (+0.045R at CONCORD<5) | FINDINGS-G B1 |
| BR-20 | **Wall-quality cut** `dep_wall_below_d<2.75 OR WALLSZ==0`, uncontaminated measurement | **Dual-currency inversion (Law 3), the cleanest on record.** Cut-set win rate **37.5%/41.5%** — reproducing the canon's claimed 37-41% almost exactly — but cut-set EV **+0.324R vs kept +0.256R**. All lifts negative (elig −0.032, book −0.017). The canon selected on hit rate and paid in R. **Refuted as an EV gate** | FINDINGS-G B2 |
| BR-21 | **MBP-10 book features at the decision bar** (thickness_vs_day, imbalance, support−resist, wall dist/size, thickness_delta_5m), bottom-quartile cuts | **All null**: best +0.020R eligible / +0.000R book (support_wall_dist); five of six negative. Every removed bin profitable. Scope: a 2.25pt-deep book on 24% of the population — not a statement about depth in general | FINDINGS-G B3 |
| BR-22 | **In-trade flow for recovery** — trades underwater at t+N, P(recover)=P(out_ship>0) | Base P(recover) **23.4% (t+1) -> 12.4% (t+10)**. Cumulative-delta-sign flag lifts precision to **31.0%** (t+1) and **17.4%** (t+10) at **~25% recall** — real but too thin for a hold rule. The in-trade CONCORD count **does NOT beat the single best signal** (28.2% vs 31.0%) — counting helps at the trigger, dilutes in-trade | FINDINGS-G C1 |

**Standing principle (2026-08-07):** three raw mechanisms measured (failed
auction, M1 rebalance, M2 rejection/continuation) — all fairly priced under
every entry/stop/exit configuration tested. New level-based ideas must locate
their claimed edge in SELECTION against these nulls, not in mechanism
existence.

**Restatement note (2026-08-07, Phase 0):** the −0.047R "gap to close"
headline was the cross-cycle-collapsed H2-era reading; under the structural
fight definition and the executable first-of-fight convention the unselected
reject book is +0.14/+0.16R by era (BR-9). Stop 0.17W and the MFE-in-R table
survived the entry-price fix unmoved. Selection's target is account-level
concentration, not per-trade rescue.
