---
date: 2026-08-04
status: greenlit
tags: [ny-pre, overnight-structure, amt]
sources: ["articles/sweep-2026-08-04-nypre-structure.md#S2", "articles/sweep-2026-08-04-nypre-stats.md#T3"]
---

# nypre-inventory-correction — the 09:30 inventory flush, mechanized

## Thesis (for Angus)

The academic and the profile-school stories converge here: overnight returns
NEGATIVELY predict the first half-hour of RTH (published), and Dalton's
doctrine says 100% one-sided overnight inventory gets corrected at the open —
weak-handed overnight holders finally have the liquidity to exit, and
short-covering gets misread as new buying by the crowd that pays. Everyone
TEACHES this; nobody has published hard NQ numbers — the quantification is the
edge. Plus our novel question: does the pre-market front-run its own
correction as cash-linked flow arrives from 09:00? If yes, the entry is
09:00–09:25, not 09:30, and the naive at-open fade gets a worse price.

## Skeleton

Inventory = % of ETH closes above prior settlement (measured 08:55 AND 09:25 —
the difference tests front-running). ≥95% one-sided, not a true outside-range
gap: counter-inventory entry on first 1-min structure failure after 09:00,
target settlement, stop at new ON extreme, hard exit 09:50.

## Flags

- Candles-only. Interacts with gap-engine and euro-handoff on overlapping days —
  the day-classification matrix keeps the fades on disjoint slices.
- **May hold through 09:30** — semantics ruling needed.
- Canon redundancy: LOW-MEDIUM (fade logic vs the canon's with-trend pullbacks).
- Post-2021 re-verification mandatory (the regime the academic result predates).

## Trial ledger — NYP-INV-01
### Trial 1 — L0 census (2026-08-04)
Relative to mixed-day base (+12.1/+23.4 pts first 30 min): 90%-LONG overnight
days open weak BOTH eras (−3.8/−24.1 raw; ≈−16/−48 vs base) — the long-side
correction is consistent. 90%-SHORT days ERA-FLIP (−8.3 in 2025 = continuation,
+18.3 in 2026 = correction) → short side DEAD per kill 2. Status: SPLIT —
long-side sub-claim only proceeds to refinement (fade one-sided-LONG overnights
at the open); short side closed.

### Trial 2 — L1 mechanics (2026-08-04) — PROFITABLE both eras INCL. strict friction
Long-side fade as directed by trial 1: short 09:30 open when overnight ≥90%
above settlement, stop ON high, exit 10:00. 2025: +910 pts (n=111, WR 37%,
+$573 at $160-risk strict). 2026: +1409 pts (n=58, +$3,344 strict). Positive
BOTH eras at BOTH friction levels; survives drop-top-3 (gross +2488 → +1017).
Low WR / big-win profile as expected for a fade. Status: STRONGEST CANDIDATE —
to grading (permutation/DSR, Brake's stage) + portfolio checks.

### Trial 3 — flow conditioning, naive pre-open delta (2026-08-04)
Flow span only (2025-06..2026-07). Two findings: (1) the naive condition
(pre-open delta ≤ 0) ERA-FLIPS — 2025H2 flow-yes −640 pts vs flow-no +190;
2026 flow-yes +1071 vs +106 — the simple overlay dies as tested (more
sophisticated flow features remain untried options, each a fresh ledgered
trial). (2) MORE IMPORTANT: the span restriction exposes time-clustering the
calendar-year split hid — 2025H2 is NEGATIVE overall (−451 pts, n=69; the
full-2025 +910 was carried by Jan–May). True shape: profitable H1-2025 and
2026, losing H2-2025. Not a kill (both calendar years positive full-span;
losing half-years are a real feature to price) but the verdict must carry the
half-year decomposition and grading must weigh it. Status: to grading with the
H2-2025 hole on the label.

### Trial 4 — MANDATORY loser autopsy (2026-08-04, §3.2)
Halves: H1-25 +1321 / H2-25 −411 / H1-26 +1294 pts. Losers vs winners on the
declared features: statistically indistinguishable (t20 +.018/+.026, ext
.72/.75, event 7%/11%, skew .990/.995; only far-stop trades win slightly
more). NO cut passes the every-era precedent; none fixes H2-25. Cold-streak
de-risk (half size on trailing-10 R<0): WORSE everywhere (total $4,782→$2,930,
H2-25 unimproved) — the streak signal lags the regime. AUTOPSY VERDICT: the
losing stretch is environmental, not conditional on the trade's own features —
the hole gets PRICED, not explained away. Ship decision rests on the funded-
shell MC carrying a −411pt six-month stretch inside the $2k trailing line at
target sizing. To Brake's grading as-is.

### Trial 5 — flow-at-entry autopsy per §3.2 (2026-08-04) — ABSORPTION SIGNAL, TRADE-OFF
Absorption at the overnight high (net selling delta on 08:00–09:29 minutes
tagging ONH): CONFIRMED n=22 WR 41% avg +15.6 pts vs UNCONFIRMED n=67 WR 25%
avg +0.7. H2-2025: confirmed +186 vs unconfirmed −473 — the hole again lives
in the unconfirmed cohort. BUT unconfirmed 2026H1 = +556 → the excluded
cohort is NOT bad in both eras → fails the strict exclusion precedent. Honest
framing: this is a QUALITY-vs-QUANTITY trade-off (steadier small book vs
bigger era-dependent book), i.e. the funded-risk-shape decision — same class
as the agent-layer ship call. n=22 is thin (§2.2 warning). Both variants go
to grading; the confirmation variant is the risk-shape candidate.

### Trial 6 — full metrics pack, gated spec (2026-08-04, flow span)
GATED (absorption): n=22, WR 41%, +344 pts, $+753 @$160-risk, PF 1.59,
sequence DD $575 (vs ungated $196 / DD $2,437 — 4× the money at a quarter of
the drawdown; the risk-shape argument in numbers). MFE/MAE: winners' median
MAE 8.0 pts vs losers' 42.8 — the starkest stop-asymmetry yet; stop sits at
ONH (median risk ~60-80 pts) while winners never see 10 pts of heat → a
tighter-stop arm (~15-20 pts) is the obvious declared next trial; 69% of
losers showed ≥5 pts favorable first → BE-family arm declared too. n=22
remains the caveat on everything.

### Trial 7 — declared exit arms (2026-08-04, 5 arms, gated spec, flow span)
A0 current (ONH stop): $+753, PF 1.59. A1 20pt stop no BE: **$+2,362, PF 1.94,
halves +23/+271/+1 (era-clean)** — the MAE finding converts: winners' 8pt
median heat means a 20pt stop keeps the economics and triples $-at-fixed-risk
(1/risk sizing). A4 20pt+BE@15: $+2,452, PF 2.41, DD $520 but 2025H1 −22.
A2/A3 inferior. LEADING SPEC: A1 (simpler, era-consistent); A4 alternative.
HONESTY: 5 arms selected on n=22 — the arm choice itself is in-sample; the
sealed holdout adjudicates it out-of-fit and all 5 arms count in DSR. NOTE:
sims standardized to conservative intrabar tie-break (stop checked before
target within a bar) from this trial forward.
