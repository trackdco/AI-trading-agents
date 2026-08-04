---
date: 2026-08-04
status: greenlit
tags: [ny-pre, session-structure, news]
sources: ["articles/sweep-2026-08-04-nypre-structure.md#S3", "articles/sweep-2026-08-04-nypre-stats.md#T8", "articles/sweep-2026-08-04-nypre-macro.md#M6"]
---

# nypre-gap-engine — gap logic done with the conditioning retail skips

## Thesis (for Angus)

Gap-fading is the most crowded idea in futures — and the published aggregate
hides three conditionals that change everything: (1) LOCATION — inside
yesterday's range fills at high rates, outside + large fills ~8–21% (fade one,
never the other); (2) CAUSE — a gap minted by an 08:30 print that held resists
filling; a flow-gap on an empty morning reverts; the decomposition (how much
gap existed at 08:25 vs 09:29) appears in no public study; (3) TIME — 34% of
fills happen in the first 5 minutes and only 39% of fills start after the first
half hour, so a gap surviving to 10:00 flips to continuation. The wrong side is
the mechanical fader pricing size but not location, cause, or clock. Includes
the pre-fill variant: entering from the pre-market extreme 08:30–09:25 before
the 09:30 fade crowd.

## Skeleton

At 09:25: classify {size, in/out prior range, pre-vs-post-08:30 components}.
Inside+small+no-news → fade toward prior close (pre-bell entry on PM-extreme
failure), time-stop 10:00. Survival at 10:00 unfilled → flip with the gap.
Outside-range/news-held → no fade, optionally join.

## Flags

- Candles + release calendar. Event tree: fade ↔ survival-flip, one family.
- **Holds through 09:30** in most branches — semantics ruling needed.
- Canon redundancy: LOW (different logic entirely).
- Expect much of the value as AVOIDED losses (not fading the wrong gaps).

## Trial ledger — NYP-GAP-01
### Trial 1 — L0 census (2026-08-04)
LOCATION leg PASSES both eras: inside-prior-range opens fill-by-EOD 70%/72%
(2025 n=143 / 2026 n=75) vs outside 47%/35%. CLOCK leg PASSES: fill-by-10:00
37%/39%; gaps unfilled at 10:00 fill later only 36%/26% — the survival flip is
real. CAUSE leg (event-day conditioning) ERA-FLIPS (2025: 44% vs 62% as
claimed; 2026: 67% vs 54% inverted, n=12) → dropped per prereg kill 2; may
only return via the calendar build with proper n and a fresh declaration.
Status: ADVANCING on location+clock to L1 mechanics.

### Trial 2 — L1 mechanics (2026-08-04) — PROFITABLE both eras (base friction)
Inside-range small-gap fade to prior close, stop 1×gap, TS 10:00: 2025 +78 pts
(n=87, +0.89/t, WR 54%; dies at 2pt strict friction −9); 2026 +461 pts (n=34,
+13.55/t, WR 68%; robust at strict +427). Concentration OK (top-3 = 33% of
gross). Era-consistent positive at base; 2025 marginal at the strict bar —
refinement targets 2025 (size/vol conditioning) before grading. Status:
ADVANCING — strongest gap result.

### Trial 3 — flow conditioning, naive pre-open delta (2026-08-04)
Flow span only: 2026 flow-yes +425 pts vs flow-no −50 (helps); 2025H2 no
discrimination and negative overall (−168 pts; full-2025 +78 was carried by
Jan–May). Same two conclusions as the inventory fade: naive delta overlay
era-inconsistent (dies as tested); half-year decomposition shows a losing
H2-2025. Status: to grading with the H2-2025 hole on the label; deeper flow
features optional future trials.

### Trial 4 — MANDATORY loser autopsy (2026-08-04, §3.2)
Losers vs winners indistinguishable on declared features. The one cut that
"fixes" H2-25 (far-stop tercile: kept H2-25 +82) REMOVES +264 pts of 2026
profit and its cut-cohort is not bad in both eras → REFUSED per the
wall-quality-cut precedent (that is what fitting the hole away looks like).
METHODOLOGY NOTE: the cold-streak de-risk quick-test for this candidate was
built WITHOUT the inside-prior-range condition — invalid, not evidence, rerun
required if de-risk is pursued. AUTOPSY VERDICT: same as inventory — the hole
is environmental; priced, not cut. To grading with it on the label.

### Trial 5 — flow-at-entry autopsy per §3.2 (2026-08-04) — CONFIRMATION GATE FOUND
Last-5-min pre-open delta leaning toward the fill (the tape already selling a
gap-up / buying a gap-down at 09:25–09:29): CONFIRMED n=51 WR 63% avg +9.8
pts vs UNCONFIRMED n=34 WR 44% avg −8.6. Era test on the flow span: confirmed
+20 pts in H2-2025 (the hole REMOVED) and +468 in 2026H1; unconfirmed −256
and −96 — **the excluded cohort is bad in BOTH eras → passes the
wall-quality-cut precedent cleanly.** Mechanism prior: canon W-gate pattern —
at-entry flow confirmation as quality filter. Declared spec upgrade: gap fade
ships WITH the d5-confirmation gate. Caveats on the label: flow span only
(14 mo), n=51 confirmed, found under §3.2 while investigating H2-25 (era
consistency of BOTH cohorts + mechanism prior are the defense); family arm
count incremented for DSR.
