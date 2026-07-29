# JOURNAL — sweep_2026_07 (append-only, advisory; no write access to any bot/config/threshold)

## 2026-07-28 · Phase 0 gate — run and reported
Data version: baseline_book_clean.parquet regenerated (404 / +$52,522.81, to the cent).
Verdict: gate does NOT cleanly pass. 0a NO-DATA (zero .scid); 0c FAIL (40/161 columns leak,
incl. W depth check flipping 41.6% of trades re-read pre-fill; cvd_conf = undocumented conf_PM
sibling); 0d clock PASS / contract FAIL (23/216 pre-market trades = 46.5% of window P&L on
wrong-contract days); 0e census binding (OOS 69/24/16). Ruled out for ever: nothing yet.

## 2026-07-28 · Phase 1 descriptive — run and reported
Excursion: continuation hazard flat (0.569/0.642/0.582/0.565); 26 trades = 98.1% of P&L.
Fast losers: NOT a population (de-tie dip p=0.945; BIC 1-component; hazard rises, not spikes).
Falsified: any fast-loser filter premise. Time-of-day: all 15 pairwise CIs include zero;
09:00 cell sign-flips by year. Falsified (at this n): resolvable intra-window ToD structure.
Bias-of-day: knowable 216/216 at 08:00:00; canon indifferent (55.0% with-bias, CI spans 50%);
with-bias worst group (2026-only). Cost/sizing: halts inert on the slice; standalone bootstrap
bust 12.85% naked / 5.91% halts / 0.00% DD-scaled.

## 2026-07-28 · CONTAINER LOSS x2
Both restarts wiped uncommitted research/ artefacts (per Brake's no-commit instruction).
Deliverables were already in-chat. Clean book re-regenerated to the cent both times.

## 2026-07-28 · Phase 2 approved with six amendments (Brake) — registration v2 written
A1 H2/H4 relabelled IN-SAMPLE (selection contamination; H4 theta from a max that includes OOS).
A2 H0 conditionality headers everything (leaky columns SELECTED the trades).
A3 effective sample computed exactly: +4R cohort 26; 15 in OOS half; top-5 = 56.0% of OOS P&L.
A4 resolved: 138 was total bucket n; OOS census 69/24/16 correct; H1 window-wide OOS n=108.
A5 H3 moved to not-tested; comparisons 20 -> 17.
A6 floor sourced to Brake's brief, applied to OOS n; refuse-to-report threshold, not validation.

## 2026-07-28 · Phase 2 run (commit 14ac690 canon branch; runner phase2/run_phase2.py)
Parameters: targets {1.5,2,2.5,3,4}R; theta {0.6,0.7,0.8,0.9}; costs $1.24RT + 1-tick mkt slip;
funded rules EOD-DD $2,000 / -$800 day halt / 40-micro clamp; NBOOT 5,000; split day = first
trade of OOS half (chronological 50/50); H1 walk-forward expanding monthly, select on train
terminal funded P&L. Results: phase2/phase2_results.json (see dashboard for verdicts).

## 2026-07-28 · Phase 2 engine correction (pre-report)
Found before reporting: the funded-account DD line was allowed to TRAIL ABOVE the $50k start
balance, contradicting the documented Lucid rule ("floor locks at $50k once balance hits $52k"
— HANDOFF §3). Symptom: all four H6 bootstrap cells at ~51-54% bust, absurd against the whole
book's ~2%. Fixed: line = min(max(line, EOD_equity - 2000), 50000) in funded_series and both
bootstraps; full re-run. The unpatched run's outputs were never reported. Also validated en
route: H2 alignment counts from the committed artefact reproduce the Phase-1 lane exactly
(no_bias 105 / with 61 / against 50), and the H4 falsifier FIRED — winner close-MAE max is
0.704R in-sample but 0.912R out-of-sample, so every theta in the pre-registered grid would have
cut at least one OOS winner, exactly the contamination Amendment 1 predicted.

## 2026-07-28 · H6 engine completion (second correction, pre-report)
After the DD-lock fix, floor/no-halt reproduced the Phase-1 lane (12.16% vs 12.85% — different
seeds) but the halt/ddscale cells did not (11.44%/12.54% vs lane 5.91%/0.00%). Cause: my Tier-1
implementation had only the daily-loss halt — it was missing the DD-PROXIMITY halt ($100
buffer, SAFETY-SPINE Tier-1 rule 1) — and my DD-scaling had only the growth steps, missing the
ADOPTED down-ramp (base -> $0 at $100 available; RULING-daily-loss-limit, commit 3d7a9e2),
which is precisely the bust-killer. Both added; final re-run. Verdict text uses only the
completed engine. Lesson recorded: "Tier-1 halts" is TWO rules and "DD-scaled" is a ramp in
BOTH directions; implementing the halves that are easy to remember reproduces neither number.

## 2026-07-28 · Phase 2 VERDICTS (final engine; commit 14ac690; 17 comparisons)
H1 FAIL — every fixed target loses to canon OOS (best 4R $11,771 vs incumbent $15,670); the
  walk-forward picked 4R every month and still lost; drop-5 worse in every cell ($5,861 vs
  $6,891); bust 23.04% vs 2.92%. This REVERSES the leaky-book RR-sweep suggestion of 2026-07-28
  morning — that ran on the superseded book at 1-lot in R-space; funded + walk-forward + clean
  book, the canon's V8 management wins. Ruled out: flat pre-market targets 1.5R-4R.
H2 NOT ESTABLISHED — skip-with-bias raises mean R (+0.523 vs +0.370) but LOSES funded dollars
  in BOTH halves (2025 $2,593 vs $3,691; 2026 $14,427 vs $14,685). Composition effect, no gate.
H4 FAIL — falsifier fired exactly as A1 predicted: winner close-MAE max is 0.704R in-sample but
  0.912R out-of-sample; every theta cuts >=1 winner; best cell $17,090 < incumbent $18,376;
  drop-5 also worse. Ruled out: bar-close MAE cuts 0.6-0.9R on this book.
H5 INCONCLUSIVE, uncomfortable — the 23 wrong-contract trades are the BEST in the window (mean
  R +1.568 vs +0.227 clean); day-block CI on the difference [-2.90, +0.10] includes zero only
  barely. 46.5% of window P&L sits on trades selected by features computed against the wrong
  instrument, and they outperform ~7x. n=23: cannot resolve; must not be ignored.
H6 CONFIRMED naked / OVERTURNED with the full spine — 12.16% -> 5.12% -> 0.00%/0.00%. Engine
  validated against the independent Phase-1 lane (12.85/5.91/0.00).
Net: 0 tradeable rules produced; 2 rule-outs locked; 1 integrity flag (H5) escalated to Brake.

## 2026-07-28 · Brake's four pre-scoring tasks resolved (no outcomes examined)
T1 census: the 138/47/31 vs 139/47/30 split is bin-edge convention; exactly TWO boundary
trades move (2025-10-08 08:30:00 b2->b1; 2025-12-26 09:00:00 b3->b2), summing to the observed
(+1,0,-1). Standardized to Phase-1 half-open bins: 138/47/31. My earlier "one 08:30 trade"
explanation was arithmetically impossible — Brake caught it; resolved at trade level.
T2 stamps: FLOORED, proven by limit-price containment — 215/216 entries trade inside their
stamped minute's bar. The exception (2026-03-13 08:31 ET, long 24673.00; stamped bar high
24672.00; prior bar spans it) is a boundary-instant print stamped next-minute: flagged
stamp_edge=1, primary scoring excludes it (n=215), fixed in Amendment 1 BEFORE scoring.
T3 rebuild: all features rebuilt from a SOURCE-band-cleaned tape (row outside its ET-day bar
band +/-25 dropped before ANY aggregation): 458,178 rows / 2,075,486 contracts = 1.325% of
volume; IS(2025h) 320,894 rows vs OOS(2026h) 137,284 — the contaminated half loses ~2.3x more.
Footprint on features: cvd_15 changes on 95/216 trades, vol_15 and absorp_15 on 105/216.
Stacks demoted to BINARY (frozen 3:1 x >=3 constant; no tercile edge ever calibrated).
two_sided_share_30 dropped (DEGENERATE). v2 supersedes v1. Clean-build shift table: 12/12 PASS
both twins; delta_div_15 28/79 carries its LOW-POWER tag.
T4b stack asymmetry: the v1 "backwards" gap (ask differs 176 under +1 vs 168 under +15)
REPLICATES EXACTLY on the clean build — and the near-trap is journaled: I almost wrote
"cleaning touched none of the stack minutes"; a direct check found 582 dropped rows sitting in
the 621 stack minutes. The true reason is that v1's stacked() already band-cleaned internally,
so v1 and v2 compute stacks on identical data — exact match is cross-implementation agreement,
not absence of change. Mechanics of the asymmetry: ask-stack present rate is 69.9% at fill-1,
70.8% at the fill minute, but 63.4% at fill+14 (se ~2.7pp) — approaching the open, one-sided
ask stacks thin out, so the +15 twin gets more both-absent agreements. The differ gap (81.5% vs
77.8%, ~3.7pp) is ~1 se of a paired difference: compositional drift plus noise, NOT a leakage
signature — leakage would make a twin agree suspiciously with strict, and both twins differ
>70%. Both control twins move the data hard; the shift test's purpose is served.
Book extension over Jul 13-15 REJECTED by Brake (recorded in Amendment 1). STOPPED after these
four per instruction: baseline ruling first, then H0. Nothing scored.

## 2026-07-28 · Three pre-ruling checks (Brake) — band fixed, stamps hold, drift flag raised
C1: zero-tol containment 207/216; the 8 new misses are all EXACTLY one tick outside the stamped
bar (rounding predicts ~50% outside; observed 3.7%) — FLOORED stands, tolerance convention
recorded, exclusion set unchanged. C2: the +/-25 band was a chosen constant, so it was swept at
+/-10/+/-50 with the materiality line stated BEFORE the numbers (>5% of trades changing bin =>
free parameter): worst bin movement 4/215 = 1.9%, band registered FIXED; the +/-25 rebuild
reproduced committed v2 exactly. C3 is the finding: the IS/OOS halves are exchangeable for all
normalized/signed features (KS p 0.41-0.82) but NOT for level features — absorp_15 (p=0.000,
OOS tercile occupancy 63/22/15), vol_15 (0.001, 15/32/53), vol_30 (0.000, 12/28/60), and both
binary stacks (+17pp present-rate, p 0.008-0.012). v1-vs-v2 KS attribution shows the drift
lives in the RAW tape (market: price 21k->30k inflates point ranges; 2026 volume ~+50%), not in
the cleaning. IS-calibrated terciles would mis-bin OOS on exactly those five features —
manufacturing or destroying an edge on their own — so their Q1 scoring is BLOCKED in Amendment
2 pending Brake's remedy ruling; the seven exchangeable features are unaffected. Also recorded:
fp_imb_15 == cvd_norm_15/2 exactly — counts as ONE test for family-wise pricing. No outcomes
examined; still stopped.

## 2026-07-28 · JOB 1 (IS descriptives) + JOB 2 (H0 dual derivation) — Brake's two jobs
JOB 1, IS half only (108 trades, 2025-06-02..2025-12-10; OOS never loaded into a statistic).
Give-back: of the 11 IS trades that reached +4R, post-+1R-touch drawdown runs min +1.03 / med
+5.97 / max +12.15 R; floors after the +1R touch: 6/11 went below entry, 3 below -1R — the
sub- -1R floors are EXIT-BAR overshoot (the stop-out bar's low), not realized loss. BE@+1R
counterfactual (frictionless, active from the bar after the touch): 59/108 touch +1R; 27
BE-stop pre-exit and their ACTUAL outcomes sum to just +$1,140 (mean R +0.014: 20 losses
-$3,110 saved vs 7 winners +$4,249 forgone); 23 never touch entry again (mean R +2.324); 5
exit-bar-ambiguous; 4 exited on the touch bar; 9 same-bar ambiguity bound. Open split: only
11/108 IS exits land after 09:30 (mean R +0.641 vs -0.006 for the 97 before); fills 74/25/9
across the half-open buckets; the 09:00-09:29 fills are the weak cell (n=9, mean -0.184,
dragged by before-open exits at -0.593 over 7). DESCRIPTIVE ONLY — nothing scored or proposed.
JOB 2, H0 evidence. Pre-run report: certified book = baseline_book_clean.parquet 404 /
+$52,522.81, 2025-06-02 -> 2026-07-10, PM slice 216 / +$18,376.00; bars reach 2023-01-02 so
Jul-Sep 2025 is fully covered; the window carries the known Jan-2026 hole (no depth exists;
footprint_jan2026 never wired into FP_FILES). THE 40-COLUMN FAIL LIST DOES NOT EXIST — the
lane artifacts were destroyed with the containers and never committed (LANE-MAP.md); of the
named FAILs only C (conf_PM) has a committed clean counterpart (pm_sofar_conf,
leakage_clean_compare.py:45), so the two arms isolate the C leak, NOT all 40; W and the dep_*
family sit leaky in BOTH arms. Harness = build_canon/size_book/NewsGate verbatim; anchors
passed to the cent (A1 canon_book 713/+$71,364.83; A2 clean sized 404/+$52,522.81) BEFORE any
windowed number. Window 2025-07-01..2026-07-10 (884/970 candidates, 244 days, fresh state).
Mechanical layer: L_nonews 245 taken +$69,328.43 (PM 200/+$39,941.41) vs C_nonews 247 taken
+$46,526.08 (PM 200/+$22,809.69) — 43% of the leaky PM P&L is not there under pre-fill C.
Sized layer (dollar-risk + windowed London): L_nonews +$54,040.31 (PM +$21,151.75) vs
C_nonews +$50,347.93 (PM +$18,113.12) — sizing normalization compresses the gap (mech dollars
scale with stop width; size_book caps risk at $400). Overlap nonews: 204 shared of 245/247
(115 of the shared differ in size/pl through governor/cold-state cascade), only-L 32 trades
+$5,793, only-C 33 trades -$2,466 — the leaky book's EXCLUSIVE trades made money, the clean
book's exclusive trades lost. PM slice: 161 shared, 39 swapped each way. News produced BOTH
ways (certified clean book has NO news filter): with gate+deadzone, L 224/+$66,703 vs C
227/+$49,230, overlap 187 shared (102 differ), only-L 27/+$5,976, only-C 30/-$1,731.
Boundary-state check: fresh-start vs certified-slice = SAME 245 trades, pl differs only via
sizing state (+$69,328 vs +$67,689). OF features rebuilt v2-style against all four books:
union 229 unique PM fills, 229/229 full pre-fill coverage, exactly one stamp_edge (the known
2026-03-13 trade; the 13 new fills all pass containment). STOPPED — no scoring, per brief.

## 2026-07-29 · PARTS 0-3 SCORED (Brake: build and deliver, no stopping for rulings)
Third container wipe. Recovered: bars bit-exact from e6cc277, footprint_jan2026 from 71fbe5f
(tape contiguous 2025-06..2026-07 — the Jan-2026 hole is a BOOK hole, not a data hole),
books from the committed job2_books. UNRECOVERABLE: output/substrate_v2_signals.parquet, so
the canon's realized exit timestamps are gone; excursion moved to a rule-independent trade-life
window (fill -> first stop touch, else 15:55 ET), validated monotone vs the certified frame on
177/177 shared trades. Recorded as Amendment 3, not silently.
PART 0. Baseline = C_news, 182 PM trades, sized +$21,097.88, mech +$25,181.25, WR 46.2%,
meanR +0.543. NOT CLEAN — C only; W and dep_* still leaky. IS/OOS re-fixed 91/91 at 2025-12-23
(the certified 216-trade split and all its tercile edges VOID, not carried). Top 19 trades =
94.6% of P&L. Q1 re-registered threshold-free (the life-window +4R cohort was unusable: it
sweeps in trades that reached +4R only after the canon exited them at a loss, cohort share
>100%).
PART 1. Remedy 3/5. absorp_rel PASSES (KS .099 p .81); vol_15_rel/vol_30_rel PASS. Brake's
literal ATR spec absorp_atr FAILS (p .035) — reported, not hidden. Both stacks FAIL WORSE after
remedy (KS .462/.495) for a structural reason: a binary's distribution IS its base rate, which
moved ~17pp, so no monotone transform of 0/1 restores exchangeability; subtracting a drifting
baseline imports the drift. Would need redefining the frozen 3:1x>=3 constant = out of scope.
Carried with FAIL flags. M_eff 8.00 of 11 nominal (Li&Ji), per-test alpha 0.0064.
Q1 = NULL. Best OOS |rho| 0.093 (cvd_30); NO feature survives family-wise. Falsifier
essentially a tie: best signed 0.093 vs best direction-blind 0.091. Every tercile transfer
CI spans zero; delta_div_15 and both stacks insufficient. This is the honest re-test of
conf_PM — an OF entry-conviction signal that only worked because it leaked.
Q2 = NO. |gap| alone carries rho +0.153 (p .036) — LARGER than every order-flow feature. After
rank-residualising on |gap|, nothing survives family-wise. Gap terciles OOS: small n=14 +0.117,
mid n=25 +1.642, large n=47 +0.819. Expiry-week OOS still hot (n=11, +3.08 vs +0.62) — H5
unresolved, n too small.
PART 2 (pre-registered as Amendment 4 BEFORE scoring). 113/182 trades produced a retrace event;
shift tests PASS at every bar bucket (20/20). NULL: every OOS AUC on 0.5 (0.464-0.551), none
survives. BUT the base rate is the finding: 96/113 = 85% of retraces RESUME to a new peak.
Underpowered for anything smaller than |AUC-0.5| = 0.147 at n=59; absence is not evidence of
absence, and only 17 reversals exist in the whole sample.
PART 3 = THE ONE THAT SURVIVES. News filter, sized PM slice: partially-remediated arm
+$2,984.75 (day-clustered CI [+894, +4,970], p=0.005); leaky arm +$1,866.12 (CI [-294, +3,925],
p=0.088) — independent replication. Positive in BOTH halves of BOTH arms. Kill test passes
decisively: the single largest avoided trade is a WINNER (+$537), so removing it makes the delta
LARGER (+$3,521.75); 0 of 23 (C) and 0 of 26 (L) single removals flip the sign; jackknife range
stays [+$2,634, +$3,522]. The benefit is diffuse across many small avoided losses, not one day.
Dashboard: research/sweep_2026_07/orderflow/dashboard_premarket_of.html, regenerable from the
JSON artefacts, provenance + cost assumptions embedded, both dead numbers listed as forbidden.

## 2026-07-29 · Brake's four follow-ups — three corrections to what I reported
1. FRAMING CORRECTED. I called the leaky arm an "independent replication" of the news filter.
It is not: the two news-filtered arms share 152/183 trades (83%), the no-news arms share 82%,
they veto 20 of ~24 the same days (83%), and their largest avoided trade is THE SAME TRADE
(2026-02-19, +$537). The C arm is the L arm with one check re-sourced. It is a SENSITIVITY
CHECK on the C remediation, not independent evidence. The leaky arm's CI [-$294, +$3,925]
SPANS ZERO and on its own establishes nothing. Corrected on the dashboard.
2. DECOMPOSITION. C arm delta +$2,984.75 = +$2,743.75 avoided-trade P&L (92%) + $405.38
resizing of surviving trades through the nth/governor/day-ladder cascade (14%) - $164.38 from
5 trades newly appearing in freed nth slots (-6%); sums exactly. L arm: 118% / -13% / -5%.
The benefit is overwhelmingly the DIRECT avoided-trade effect, not cascade side-effects —
which is the cleaner mechanism and makes the result easier to trust, not harder.
3. FUNDED RISK. Full sized book. C arm: naked bust 0.98% -> 0.42%, maxDD $1,721 -> $1,569,
min available DD $1,572 -> $1,780, daily-loss breach days 0 -> 0. L arm: 0.92% -> 0.22%,
maxDD $1,511 -> $1,346. With the full safety spine both are 0.00% before and after, so the
filter's risk benefit is real but only visible on the naked account. The -$800 daily limit was
never breached in either book.
4. RESUME RATE CORRECTED — this materially changes Part 2's headline. Restricting to bars
at/before the canon's actual exit (lower-bounded by first touch of the recorded exit price,
exact for the 25% of trades exiting at the stop): 85.0% (96/113) over full trade life falls to
60.2% (68/113) TRADEABLE. 28 of 113 events fire after the canon had already closed the trade.
Of events that occur before the exit, 80.0% resume. The bound is conservative (biased low).
The honest statement is 60.2%, not 85% — a resume after the position is flat is not tradeable.
Registered AMENDMENT 5: gap size gets its own lane next round (G1/G2/G3), with the
non-monotone tercile pattern and the mid-cell overfitting trap flagged in advance.
