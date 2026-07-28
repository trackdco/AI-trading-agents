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
