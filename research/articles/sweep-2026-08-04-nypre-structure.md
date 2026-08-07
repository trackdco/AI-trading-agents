---
date: 2026-08-04
status: reference
tags: [ny-pre, amt, session-structure, research-sweep]
sources: ["see per-concept lists below"]
---

# Sweep record — NY pre-market structure/AMT angle (agent sweep, 2026-08-04)

Sourcing: WebSearch extracts; direct fetches 403-blocked. URLs = deep-dive leads.

## Shared evidence base (documented facts)

- **Pre-market grew and shifted earlier**: NYSE research 2025 — 04:00–09:30 is now
  >55% of extended-hours share volume; 04:00–05:00 alone ~8% (6× its 2019 share).
  The 04:00 ET pre-open is a real participation event now.
- **Overnight levels are near-certain to be engaged**: TradingStats NQ, 2,827
  days 2015–2025 — 94.2% of days break ≥1 overnight level; open above ON midpoint
  → ONH breaks first 76.2% (below → ONL first 75.6%); +aligned large gap → 82–84%.
  A third of first breaks in the first 5 min of RTH; 68.7% by 10:00.
- **Gap-fill is fast and conditioned**: 34% of NQ gap fills in the first 5-min
  RTH bar, ~61% by 10:00; inside-prior-range opens fill at high rates; outside +
  large + high-vol → ~21%. NQStats: open outside prior RTH range → 83.3% the
  other side of prior range never trades.
- **Dalton inventory correction at 09:30**: taught everywhere, hard NQ numbers
  published nowhere — the quantification gap is itself the opportunity.
- **09:25–09:30 is a distinct regime**: Nasdaq opening-cross imbalance (NOII)
  disseminates from 09:28 (EOII 09:25), MOO cutoff 09:28; cash-linked flow
  arrives 09:00+ and pre-open reversals are documented.

## Concepts (8)

**S1 on-midpoint-polarity-entry** — price location vs ON midpoint at 09:20 +
gap agreement → enter toward the ON extreme BEFORE the bell; the published
76–84% first-break stat converted to an approach-window trade. Payer: the
counter-side overnight positioner whose stops sit at the extreme. Candles-only;
depth used INVERSELY vs the incumbent (skip if wall blocks path).
Crowding: stat published Dec 2025 — decay check 2026 mandatory.

**S2 dalton-inventory-mechanized** — ≥95% one-sided overnight inventory vs
settle (not a true gap outside prior range) → counter-inventory entry 09:00–
09:25, target settlement. The NOVEL sub-question nobody has published: does the
pre-market FRONT-RUN its own correction as cash flow arrives 09:00+? Taught
discretionary everywhere, mechanized nowhere. Candles-only.

**S3 inside-range-gap-prefill** — small gap + inside prior RTH range → fade
from the pre-market extreme 08:30–09:25 toward prior close, capturing the
documented first-minutes fill before the 09:30 gap-fade crowd. Abort per gap
rules (outside-range/large = go-with). Most crowded idea here; the conditioning
is what retail doesn't apply. Candles-only.

**S4 0830-impulse-pm-extreme** — on 08:30 release days: does the data impulse
BREAK the 04:00–08:29 pre-market extreme (continuation — trapped pre-market
counter-positioners cover into 09:30) or POKE-and-fail it (reversion — trapped
breakout chasers)? Trades minutes 4–60 post-release, not the HFT seconds.
Unpublished conditioning; slippage on release days is the honest risk.
Candles + release calendar.

**S5 hourly-range-false-break** ("Magic Hours" family) — published NQ backtest
(1,287 days): pre-market hour-range false-breaks revert to hour midpoint at
76–83.5%, best 06:00–08:00 ET. Thin-book failed-breakout reversion. WARNING:
actively popularized 2025 (dashboards, TradingView scripts) — split pre/post-2025
to measure decay before trusting. Candles-only.

**S6 opening-cross-echo** — Nasdaq NOII from 09:28 → index-arb pre-hedging
should print as a signed drift/CVD burst in NQ 09:28–09:30, visible in our tape
without the feed. Two branches: continuation 09:30–09:35 (hedge completes) vs
fade-if-against-inventory (uninformed MOO flow reverts — "The Quote Not Taken",
SSRN 2025). Event study first, strategy second. Needs CVD (Jun 2025+, ~270
sessions).

**S7 euro-derisking-handoff** — 08:00–09:30 ET is Europe's afternoon squaring
window; after a one-sided 03:00–08:00 Euro session, European profit-taking +
arriving US flow → partial retrace/stall before RTH judges it. "Inventory
correction, European edition" — anchored to the 03:00 Euro open, not settle
(different signal than S2). Folklore on every prop floor, no public backtest.
Candles-only.

**S8 0400-mini-open** — the 04:00 pre-market open as a structural anchor: does
04:00–05:00 disproportionately set the eventual PM extreme; price vs
04:00-anchored VWAP at 08:00 as bias for how the approach window resolves.
Youngest, least documented (volume shift is post-2019, accelerating post-2023);
short effective sample, possibly strengthening rather than decaying. Candles-only.

## Cross-cutting

- Decay landmarks: Euro-hours unconditional drift dead post-2021; Magic Hours
  popularized 2025; ON-midpoint stats published late 2025; gap stats fresh.
- Distinctness from the incumbent canon pre leg: none require depth walls; where
  depth appears it's an exclusion filter or the INVERSE of the incumbent's use.
- Interaction warning: S2/S3/S7 fire on overlapping days (one-sided overnight ⇒
  gap ⇒ one-sided Euro session). Build a day-classification matrix FIRST so the
  fade concepts are evaluated on disjoint conditional slices, not triple-counted.

Sources: tradingstats.net (ON breakout, gap timing/fill, Magic Hours, ORB) ·
nqstats.com/rth_breaks · NY Fed SR917 + Disappearing Overnight Drift ·
NYSE early-bird + night-moves research · Cboe extended-hours · Nasdaq
opening-cross/NOII + Federal Register rule · SSRN 5498938 "The Quote Not Taken" ·
marketcalls/ShadowTrader/Axia (Dalton inventory, gap rules) · QuantifiedStrategies
gap fills · TradeThatSwing gap stats · edgeful PM-range report · TradingSim ·
Darden open/close procedures WP.
