---
name: gold-orb-models
description: Opening Range Breakout (ORB) models for gold futures (GC/MGC), extracted from three source videos and tiered by evidence. RETIRED as an entry family on GC as of 19 Aug 2026 — see references/null-result.md before proposing any ORB work. The exit, risk and sizing layer is validated and reusable. Use this skill whenever the task involves implementing, backtesting, coding, evaluating, or discussing ORB on gold or any futures — including any mention of "opening range", "ORB", "15-minute range", the 9:30 open range, value-area/volume-profile ORB variants, fakeout fades, breakout-pullback-continuation, or Toby Crabel — even if the user doesn't say "ORB" explicitly. Also use for gold risk-parameter design, where the ATR-normalisation finding applies regardless of signal.
---

# Gold ORB Models

> ## STATUS — 19 Aug 2026
>
> **The plain opening-range-breakout ENTRY family on GC is RETIRED.** Four independent
> falsifications; train expectancy −0.000R, PF 0.98; no configuration reached the +0.10R
> promotion gate. **Read `references/null-result.md` before proposing, coding, or
> backtesting any ORB variant on gold.** Do not re-run the anchor, Crabel, participation or
> OR-window sweeps — they are settled and the results are recorded there.
>
> **The EXIT, RISK and SIZING layer is validated and reusable**, and is not implicated in
> the null: a calibrated engine (89.0% day match against a live TradingView export, 100%
> direction agreement), 32 constructed-bar self-tests, hard risk cap, profit ratchet,
> time-stop and circuit breakers. The **candidate generator is the only piece retired.**
> A replacement signal drops into the same harness — see the engine README for the interface.
>
> **Sealed data:** 2025-09-01 → 2026-03-01 is UNSPENT and reserved for the next gold
> hypothesis. It must not be spent re-testing ORB. 2026-03-02 → 2026-08-11 is permanently
> disclosed; treat it as in-sample.

Three ORB variants extracted from source transcripts (17 Aug 2026), specified for direct
backtest implementation on gold futures. The models were taught on NQ/ES/S&P and gold —
none was validated on gold by its author. M2 and M3 have now been measured here and
refuted; M1 remains unmeasured.

## Non-negotiable rules when implementing or reporting

1. **Report in R-multiples and points first.** GC: 1 point = $100/contract, tick 0.1 = $10. MGC: 1/10th ($10/point, $1/tick). Never headline a result in normalised or derived units; R leads, points alongside.
2. **Never fill an UNDEFINED parameter silently.** Every parameter in `references/models.md` is tagged STATED, INFERRED, or UNDEFINED. UNDEFINED parameters are sweep variables — enumerate the values tested and report per-value. Filling a gap with a plausible default and not flagging it is a defect.
3. **Absent is not unknown, and unknown is not "no rule".** If a source doesn't state a rule, the finding is "unstated", never "the rule is X" and never "there is no rule".
4. **Model costs.** ≥1 tick per side slippage (2 ticks in the first minute after the range completes and around 8:30 a.m. ET releases) plus commission. If an edge dies going 1→2 ticks, it was microstructure noise — report that explicitly.
5. **Data.** Continuous back-adjusted GC (or native MGC), volume-based roll a few days before First Notice. A single un-rolled contract distorts range sizes near expiry — do not use one.
6. **~~The range anchor is itself a sweep variable.~~ SETTLED — do not re-sweep.** All three sources anchor to 9:30 a.m. ET by stock-market convention, and the gold-native candidates (08:20 ET COMEX, 03:00 ET London) were tested and **lost**. 09:30 was best in R; London 03:00 is refuted with a 2-tick interval clear of zero on the wrong side. See `references/null-result.md`.
7. **Holdout discipline.** Reserve an untouched out-of-sample segment before any parameter sweep. Report train and OOS separately; a result quoted without its OOS counterpart is not a result.
8. **Express every risk parameter in ATR units — never points, never percent of price.** Measured on GC: a 30-point cap fires on 0.6% of 2023–25 trades and 29.5% of 2026 days; 0.5% of price fires 19.4% vs 52.7%; **0.5 × prior-day ATR14 fires 8.8% vs 7.1%** and is the only form that transfers. Gold's 2023→2026 shift is a *volatility* regime change, not a price-level change. This rule applies to any gold work, ORB or not.

## Model index (full specs in `references/models.md`)

**Entry models — status after the 19 Aug 2026 programme:**

- **M1-A — Fakeout fade** (source 1): **UNTESTED on GC.** Liquidity resting just outside the range → skip the breakout, wait for the liquidity hit, enter on 5-min close back inside the 70% value area, reversal direction. Zero data shown by source. *Not refuted — never measured.* It is a reversal keyed to a value area and external liquidity, a different trade population from the breakout family that was retired, so the null does not reach it.
- **M1-B — With-trend value-area breakout** (source 1): **UNTESTED on GC.** Only with clear trend or after a pre-range liquidity sweep; enter on 5-min close outside value area; stop 2 ticks past POC; fixed 2R. Zero data shown by source. Keyed to the **value area**, not the raw price range — the retired family used the raw range throughout, so this is also unmeasured rather than refuted. Note the prior is now worse than it was.
- **M2 — Plain 15-min ORB + context filters** (source 2): **REFUTED on GC.** Close-outside entry, opposite-side stop, 1.5R. The author's own 8-day gold sample was ≈ net −0.5% (2W/5L); measured properly here it is EV −0.000R at PF 0.98 on 2023–25, negative at two ticks. His proposed fixes (HTF bias, re-entry fades, confluence) were not individually rescued by anything in the sweeps. See `references/null-result.md`.
- **M3-base — Fully specified plain ORB** (source 3): **REFUTED on GC.** Was the designated baseline and is the configuration that carries the null. Close-outside entry filled at next candle open, opposite-side stop, 1.5R, no entries after the 12:00 ET candle, ATR min/max range filter. The 12:00 cutoff is genuine and was recovered independently during calibration; the entry edge is not. See `references/null-result.md`.
- **M3-BPC — Breakout-pullback-continuation**: **REFUTED TWICE** — by its own author on S&P (5 years, ~130 trades, unprofitable) and now by the family null on GC. Do not build it.

## Test priority

**The breakout-entry priority list is closed.** M3-base, M2 and M3-BPC are refuted; do not
re-test them, and do not re-sweep the anchor, contraction, participation or OR-window axes.

What remains open, in order:

1. **M1-A (fakeout fade)** — the novel claim, a *reversal* conditioned on external liquidity,
   distinct from everything that was retired. Requires pinning the liquidity definitions from
   the sweep list in `references/models.md`. Weight the prior down: it comes from the
   weakest-evidence source in the set (two winning walkthroughs and an account claim).
2. **M1-B (value-area breakout)** — tests whether the *value area* carries information the
   raw price range does not. Cheapest way to find out is to log both boundaries per trade.
3. **The two leads from the null**, and only on data that is not the 2023–25 train set:
   OR window 30–35 min, and breakout-bar range ≥ 1.5 × ATR14.

Anything promoted must clear the gates below on data that is not the train set. The sealed
2025-09 → 2026-02 window is the one out-of-sample resource left and is reserved for a
hypothesis that has already cleared train elsewhere.

## Validation gates (go/no-go)

- **Advance to demo** only if OOS expectancy ≥ +0.10R/trade, profit factor ≥ 1.3, n ≥ 200 trades, and performance is stable across neighbouring parameter cells (a single spiking cell = curve fit).
- **Kill or re-test** if OOS expectancy ≤ 0, PF < 1.1, or the edge collapses at 2-tick slippage.
- **Check the dose-response, not just the interval.** The decisive rejection in this programme was not a confidence interval — it was ID/NR4, the *strictest* form of a contraction filter, being the *worst* cell in the study. A real precondition strengthens as you tighten it.
- **Run the cost-denominator control on any cell whose stop is wider than the control's.** Fixed costs enter as `cost/risk`, so a wider stop lifts EV arithmetically. Compare pre-cost EV before believing the cell.
- Live sizing decisions are out of scope for this skill; it produces measurements, not trade recommendations.

## References

- **`references/null-result.md` — READ FIRST.** The 19 Aug 2026 programme: verdict, all four falsifications with provenance, every sweep with the reasoning that settled it, the ATR-normalisation finding, seal status, and the two surviving leads.
- `references/models.md` — full parameter tables for M1-A, M1-B, M2, M3-base, M3-BPC with STATED/INFERRED/UNDEFINED tiers, source conflicts, and the consolidated sweep list. Still the reference for M1, which is unmeasured.
- `references/gc-mechanics.md` — GC/MGC contract math, Globex sessions (ET + AEST), settlement, rollover, slippage modelling, and the anchor question. Read before touching data. Note the anchor question is now settled — see rule 6.
- `references/tv-findings.md` — the 18 Aug 2026 live TradingView v1 test (116 trades). **Historical context only.** Its diagnoses motivated the v3 mechanism set, and the null showed that set to be fitted to that same window: it lifts PF by +0.54 there and +0.01 on train. Read it to understand where v3 came from, not as evidence for it.
