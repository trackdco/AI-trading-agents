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
