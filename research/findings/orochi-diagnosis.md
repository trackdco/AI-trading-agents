---
date: 2026-08-05
kind: intake diagnosis (dossier)
status: AWAITING ANGUS GREENLIGHT
tags: [orochi, intake, amt, tpo, vwap, orderflow, overnight]
sources:
  - research/transcripts/orochi/ (22 transcripts + CATALOG.txt)
  - research/transcripts/orochi/EXTRACTION-A-core-nq.md
  - research/transcripts/orochi/EXTRACTION-B-foundations-combos.md
  - research/findings/orochi-credibility.md
  - research/findings/orochi-toolkit-evidence.md
---

# Orochi Trading — full diagnosis and proposed test slate

First intake under the trader-sources / quant-validates model. Angus supplied
the channel; this dossier is the diagnosis; the funnel runs on whatever he
greenlights below. Nothing in this file has been tested yet — no trials, no
ledger entries, no looks.

## Verdict in one paragraph

The man is unverified; the material is worth testing. The channel is a
~10-month-old anonymous paid-community operation with zero independent
reputation and zero execution evidence — every performance number is
marketing until proven on our data. But the framework itself is coherent
auction-market doctrine (value areas, balance/imbalance, trapped-trader
mechanics) rather than indicator soup, several of his setups have real
trapped-counterparty stories of exactly the kind our seven pre-market kills
lacked, his order-flow doctrine independently converges on our own
flow-at-entry law, and his NQ trading window (overnight Globex) fills the one
session where our book has nothing. The published evidence on his toolkit
splits cleanly: some parts have large-sample support worth replicating, some
are folklore whose canonical percentages are vendor copy, and one family
(fib/Elliott) is published-negative. The test slate below is built on that
split.

## 1. The man (full file: orochi-credibility.md)

- Discord Oct 2025 → YouTube Jan 2026 (2.66K subs) → Whop store Feb 2026.
  Front-man "Emir" (TikTok @44emirr), staffer "Spencer"; no legal names, no
  location (hidden), community skews Turkish.
- Sells: $65-545 membership, three $100 indicators, upsold 20hr course.
  No prop-firm affiliation or referral links anywhere.
- Zero footprint on Reddit / futures forums / X — for or against. The only
  reviews are 13 on his own sales page (4.9/5).
- The "5R / 4.6R / 7R" recaps: R-multiples appear ONLY in video titles, never
  in audio; both videos are post-hoc chart markups uploaded days later; the
  WTI one carries a static "REALIZED P/L $4,932" banner identical in every
  frame. No DOM, no fills, no statements anywhere on the channel.
- The channel is probably two presenters: the AMT/TPO/NQ-overnight voice
  (most videos, incl. the funded-payout NQ session) and a crypto-swing
  ORB/fib voice (ddx0UwM2MIk). Treated as two sub-styles in extraction.

Intake consequence: his claims carry ZERO evidential weight. Only the
mechanism stories and our own measurements count. This changes nothing about
the pipeline — it is how we treat everyone.

## 2. The framework, in plain language

One idea, applied everywhere: markets alternate between agreement (balance —
price rotates inside a "value area" where most business was done) and
disagreement (imbalance — price trends to find a new area). His trades are
all live at the same three moments: fade the edges while balance holds; go with a
break that gets accepted; and — his flagship — catch the break that FAILS,
because the traders who chased it are trapped and their forced exit powers
the trip back across the range. Order flow (delta, absorption) is used only
to time entries at levels the framework already chose — "order flow is 10%
of trading, it forms no trades alone" — which is independently the same law
Angus made us instate for validation.

Load-bearing discretion he never defines (each becomes a declared variable in
our preregs, not a vibe): "acceptance" vs "deviation", "time and space",
"momentum rounding out", balanced-vs-imbalanced classification, which
composite/balance area is "the relevant one".

## 3. Setup families × published evidence × our data

Families merged from both extractions (A/B lists unified). Evidence tiers
from orochi-toolkit-evidence.md: [A] peer-reviewed/SSRN, [B] large-sample
practitioner backtest, [C] folklore/vendor copy.

| # | Family | His version | Published evidence | Our data fit |
|---|--------|-------------|--------------------|--------------|
| F1 | Value-edge rotation fade | short VAH / long VAL of established balance while rotational; target POC → other edge | 80%-rule traverse measured 27-67% [B], never 80% [C]; VA-touch base rates strong (open-inside → prior VPOC touch 82-85% [B]); geometry alone fails costs in walk-forward falsification [B-neg] | full span (candles); flow gates on flow span |
| F2 | Failed auction / acceptance-back-inside ("80% rule") | break fails to trend → re-acceptance → traverse; trapped breakout traders are the fuel | the folklore number is vendor copy [C]; the trapped-trader MECHANISM is supported (forced-unwind flow moves price [A: Cont et al.]); nobody has published the failure-vs-continuation discriminator | full span; the discriminator (flow at the failure point) is OUR novel edge — L2 delta + L3 depth |
| F3 | Break + retest continuation | the mirror twin: break that holds, retest, go | IB/range-extension stats robust [B]: ≥1 IB break on 96-98% of days, narrow IB → 98.7% break; IB direction → break side 74-81% | full span |
| F4 | VWAP sd2 rotation fade | fade ±2σ ONLY in rotational regime; forbidden in trend | band-fade weak/regime-fragile [B]; VWAP TREND side is the strong result — NQ replication Sharpe 1.67, +6bps/trade net [A/B]; VWAP-as-benchmark mechanism solid [A] | full span |
| F5 | Trend pullback into developing value | when imbalanced, buy pullbacks into developing VAH-as-support | same evidence family as F4 trend side | full span |
| F6 | ORB / session-open setups | loss/reclaim of daily open with confluence stack (crypto voice) | best-evidenced family in print [A: 3 papers] BUT direct MNQ falsification at retail friction [A-neg: every ORB variant failed, 2-pt friction ceiling on bar-level signals] | full span; friction law §2.5 decisive here |
| F7 | Sweep & reclaim (SFP) at levels | let stops run, confirm absorption, enter on reclaim | absorption mechanism real [A: iceberg orders 12-20× displayed size, high volume + no progress = hidden liquidity]; signal grammar unquantified | flow span; L3 depth is the differentiator |
| F8 | Order-flow confirmation layer | absorption > OI-flush > exhaustion ranking; CVD result-for-effort dislocation; never standalone | mechanism tier-A (order-flow imbalance drives short-horizon returns); retail grammar unpublished; VPIN cautionary tale on classification sensitivity | flow span — our chance at novel numbers; OI leg is crypto-only, dropped |
| F9 | Regime/construction meta-rules | balance→profile edges, trend→developing VWAP; established-not-developing profiles; composite merging; pre-session hypothesis | day-type/IB conditioning quantified [B]; b/P-shape narratives folklore [C] | conditioning variables for every search; amt_days.parquet already built |
| F10 | Fib golden pocket / harmonics / Elliott | confluence layer on everything (crypto voice especially) | PUBLISHED-NEGATIVE [A: Batchelor & Ramyar — Fib ratios indistinguishable from random; 2021 algorithmic study concurs]; Elliott unfalsifiable as specified | PARK — candidate null-control family |
| F11 | Anchored VWAP | cost-basis line from swing/event anchors | FOLKLORE-ONLY [C: no backtest exists, incl. the CMT material] | park; mechanical-anchor variant (ON high/low, session open) may return as a feature |

## 4. Proposed test slate — Angus picks

Every candidate gets the full law: prereg before any test, L0 census with
declared kill classes, raw-triggers-look-bad expected, full conditioning
search before any expectancy kill, flow-at-entry mandatory, era discipline
(2025 discover / 2026 validate / inverse), loser autopsy, exit arms
tournament then freeze, MC/DSR/PBO grade, correlation battery vs the book,
sealed holdout untouched until a written look declaration.

### P1 — orochi-failed-auction (F2+F3 as ONE event-tree family) — RECOMMENDED FIRST
The flagship. One picture, two resolutions: balance-break that FAILS
(re-acceptance → traverse; trapped-side flow is the fuel) vs balance-break
that HOLDS (retest → continuation). Nobody in print has quantified the
discriminator; his is vibes ("time and space"). Ours will be declared arms:
time-outside thresholds, re-entry close counts, delta at the failure point,
absorption of the trapped side, depth-wall state at the broken edge. Full
span for candles; flow discriminator on flow span. Balance detection =
overlapping value areas per amt_days + composite merge rule (to be frozen in
the prereg). Trapped-counterparty story: explicit and strong.

### P2 — orochi-overnight-rotation (F1 in HIS window) — RECOMMENDED SECOND
His actual NQ trade: overnight Globex session, rotation inside a multi-day
composite, entries at the composite edge / sd2 of overnight VWAP confirmed
by developing-value shift, targets mean → far edge. Fills the empty overnight
shelf slot — zero clock overlap with canon (8:00-10:30), pre-market sleeves
(9:30-10:00), or London (3:00-6:00). Flow data covers overnight fully.
Redundancy prior: LOWEST possible (empty session).

### P3 — orochi-vwap-regime-pair (F4+F5) — the evidence-first candidate
The published NQ-replicated result is the TREND side (above VWAP = long
bias, Sharpe 1.67 replication) while his taught edge-fade is the fragile
side. Test both sides under one prereg with the regime gate (rotational vs
imbalanced day, day_type in amt_days) as the declared discriminator. Highest
prior of the slate by external evidence; least "his", most "the toolkit's".

### P4 — orochi-sweep-reclaim (F7) — HOLD, coordinate with Brake first
Real mechanism, our depth data is the differentiator — but structurally
adjacent to london-level-trap-fade (Brake's program) and the canon's
wall-logic. Correlation battery + input-family audit BEFORE prereg, and
Brake should rule whether it belongs in his London queue instead.

### Feature adoptions (no prereg needed — they enter existing law/searches)
- Absorption / delta-dislocation grammar → named flow-gate features for §3.2
  autopsies and conditioning searches (formalizes what the canon's W-gate and
  the gap fade's d5-gate already do).
- IB-size / day-type / open-type conditioning → declared conditioning
  variables (replicate the narrow-IB 98.7% break stat on our window as a
  census, not a strategy).
- Single-print fill clocks (63-67% by D+5, width-conditional) → target/level
  logic for any profile candidate.
- POC-interrupt rule (mean can stop a traverse) → exit-arm design input.

### Parked
- F10 fib/harmonic/Elliott: published-negative / unfalsifiable. Optional
  later use: null-control family to calibrate the funnel's false-positive
  rate. Not before the real slate ships.
- F11 anchored VWAP: no evidence, anchor-selection discretion unresolved.
  Mechanical-anchor variant may be declared later as a feature trial.
- OI reads: data doesn't exist for CME futures in our shelf (crypto-only
  construct as he uses it).

## 5. Honesty box (what could bite us)

- The MNQ friction-ceiling result [arXiv 2605.04004]: fourteen bar-level
  OHLCV signal families, max gross edge 0.07-1.50 pts vs 2.0-pt friction.
  Our slate must therefore win on the flow/depth layers and strict §2.5 cost
  realism — candle-only expressions of F1-F6 are expected to die at costs,
  and that is not a process failure.
- Every canonical percentage in this doctrine ("80% rule", "naked POC 80%",
  "poor highs 78%") is vendor copy; measured equivalents land lower and
  regime-conditional. Our censuses replace them all.
- His two mirror setups (F2 vs F3) resolve the same picture oppositely; if
  our discriminator search fails, the family dies honestly at the
  conditioning stage — the search itself is the test.
- 22 trades of "his" NQ evidence = one cherry-picked highlight night. Zero
  weight assigned.
- Trial-ledger discipline: every arm in every prereg counts toward program
  DSR deflation from day one. The pre-market program's lesson stands —
  sparse sleeves certify at BOOK level, so slate candidates are graded as
  portfolio components.

## 6. What happens on greenlight

Per candidate: prereg committed (docs/PREREG-orochi-*.md) → composite/balance
builder extension to scripts/amt_substrate.py where needed → L0 census → the
full ladder. Verdicts land in research/candidates/orochi-*.md with trial
ledgers, dashboard tracking, and Angus sees nothing until there is a verdict
to deliver — per standing instruction.
