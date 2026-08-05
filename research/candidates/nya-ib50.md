# NYA-IB50-01 — MrZincx IB50 continuation (as taught)

Prereg: docs/PREREG-ib50-continuation.md. Card: research/FUNNEL.md.
Opposite vector to nya-ivb-fadeB; conflict routed to PREREG-selector.

### Trial 1 — census + BE arms (2026-08-05, scripts/nya_ib50_census.py)
Lookahead-clean (front-run entries use developing IB levels). 432 trades
(~2.5/wk) + 455 day-death skips; ties 0.
- DEFAULT (no BE): WR 51%, -232pts, $+6, PF 0.98 — dead-flat coin flip at
  ~1:1. Years 0.93/0.90/1.26/0.78 — only 2025 positive.
- AS-TAUGHT BE+trail (+0.35R BE, 0.3R trail): PF 0.74, $-4,423 — his own
  management mechanics make it WORSE every year. BE null holds (4th
  family). His 62%-WR December ledger does not survive translation to
  full-span NQ.

### Trial 2 — declared search rounds (2026-08-05)
- ARM 1 (his 8% weekday-deviation rule, trailing 26-wk weekday rates, no
  lookahead): does NOTHING — pass-cohort PF 0.99 vs skip-cohort 1.00.
- ARM 1b (weekday trailing rate >= 70% floor, same class): n=247, PF
  1.17, +1,320pts, $+2,960 — positive ALL FOUR years (1.13/1.02/1.19/
  1.36) BUT permnull p=0.096 — MARGINAL, does not clear 0.05. Evidence
  banked, not a gate. Would need ~2x span or an independent condition to
  decide.
- FLOW (flow span n=132): null — delta-agreement PF 0.89 vs against 0.88;
  conviction tape worse (0.80); absorption fires 1x (structural absence).
- DEPTH (front-run entries only, n=56 covered — archive ends 10:29):
  book-leans-with n=12 WR 83% PF 3.00 both years positive — the §5.12-9
  tiny-n shape, EVIDENCE ONLY; structurally this gate can never cover
  post-10:30 entries (archive window). Canon-prior-consistent tease.
- STATE (trailing-5 own P&L): drawdown PF 1.14 vs profit 0.90 — NOT
  era-consistent (2024/2026 negative in drawdown cohort); no gate.
- STILL OWED before any verdict (declared, unrun): arm 2 calendar/gap
  gates (pre-NFP-Thu, first-15-min, gap>1.5%), arm 3 strict 10:23-10:30
  window, arm 4 25%-retracement entry. No bin until complete (§5.9.1).
Ledger rows 228-231.

### Trial 3 — §5.11-9 deep round, FIT SPAN 2025-06→2026-07 (2026-08-05, scripts/nya_ib50_deep.py)
n=138 fit-span trades, base WR 52%, mean R +0.013 (flat). THE DEPTH ROUND
CHANGES THE PICTURE:
- IN-TRADE SIGNATURES (canon grammar TRANSFERS on this minutes-clock
  trade): PRESS 86-87% WR at t+5/15/30 (n=14-23) vs 52% base; DYING 6-21%
  — sharp, matches canon shape.
- IN-TRADE FLOW IS DECISIVE (canon class prior confirmed AGAIN: flow
  near-worthless AT entry — trial 2 null — decisive INSIDE): cvd-since-
  entry WITH the trade: 63-67% WR; AGAINST: 33-35%. n=36-57 per cell.
- MFE/MAE: losers die clean (median MFE 0.31R, only 17% ever saw +0.5R);
  winners' median MAE 0.21R.
- CONVICTION SIZING (declared score: weekday-floor + entry-delta + book
  lean; units = 1+score): monotone — score-0 cohort NEGATIVE (n=24, WR
  33%, meanR -0.333); score-3 +0.191. Conviction-sized $+2,604 vs flat
  $+278 (risk-normalized $+1,175) on the fit span.
CAVEATS: all fit-span optimization surface (§5.11-9a); cells searched;
score-0-as-cut and the cvd-management overlay need the OOF adjudication
(six sealed months, single look, written declaration) before any freeze.
Remaining declared arms (2/3/4) still owed. Ledger row 232.

### Trial 4 — winner-vs-loser diagnosis, fit span (2026-08-05, scripts/nya_ib50_diagnosis.py)
ANGUS mandate: "there has to be something that distinguishes winners from
losers... see if we can see losers before they happen."
(A) STAT PACK: n=138, WR 52.2%, -435pts, $+278, PF 0.93, payoff 0.85
(median win +68 / loss -86), mean risk 92.9pts, maxDD $1,831, streak 5.
Halves: 25H1 0.43 (n=11) / 25H2 1.27 (+566) / 26H1 0.89 / 26H2 0.25 (n=7).
(B) DISCRIMINANT TABLE (Welch t + rank AUC): AT ENTRY, near-nothing —
risk 0.44 / frontrun 0.53 / weekday 0.53 / delta 0.51 / dz 0.51 /
conviction 0.57 AUC. ONLY book imbalance separates (AUC 0.66, t +1.79,
n=56 covered — the depth tease, best at-entry read). EARLY IN-TRADE,
MASSIVE: r15 AUC 0.85, MFE15 0.85, MAE15 0.84, cvd15 0.81; already
0.71-0.77 at t+5. The trade identifies itself within 5-15 minutes.
CANON PROFILE REPRODUCED: entry = population, management = edge.
(C) EARLY-CUT POLICY ARMS (causal, exit at t close; 6 declared):
- cut t+5 if dying: cut-cohort baseline WR 6% (16 trades) -> $+1,295.
- cut t+15 if dying OR cvd-against: cuts 50, cohort WR 32% -> $+1,590
  (vs $+278 baseline, delta +$1,312 — 5.7x).
- cut t+15 red AND cvd-against: $+1,575 on 32 cuts (cohort WR 19%).
CAVEATS: fit-span searched cells (6 policies); freeze requires the
remaining declared arms + OOF adjudication — and the OOF is LEGAL here:
the sealed months' flow is unburned, so a flow-conditioned early-cut spec
can be adjudicated there (single look, written declaration to Angus).
PATH: the early-cut rule can be MECHANICAL spec (not agent discretion),
making the mechanical baseline the managed walk — then agents must beat
THAT (§5.11-8). Ledger row 233.

### Trial 5 — remaining declared arms 2-4 (2026-08-05) — SEARCH COMPLETE
- ARM 2 (calendar/gap): pre-NFP-Thursday cohort negative (PF 0.71) but
  n=21 with 2023 positive — weak evidence, no gate; gap>1.5% nothing
  (n=26, wild year swings). His calendar rules add ~nothing here.
- ARM 3 (entry window) — THE STRUCTURAL SPLIT: strict front-run entries
  (10:23-10:29, before IB completes) n=257, PF 1.15, +1,101pts, positive
  2023/2024/2025 (2026 0.77); post-completion entries n=175, PF 0.81,
  -1,332pts, no positive year. Mechanism-coherent (front-run = pre-break
  positioning; post-10:30 = chasing). Permnull p=0.112 — MARGINAL again
  (evidence, not proven gate; third marginal on this family).
- ARM 4 (25%-retrace, fit span): KILLED as an entry — n=80, WR 21%, PF
  0.61 — the deep pullback mostly fills on days going to the stop.
DECLARED SEARCH NOW COMPLETE (arms 1-4 + flow/depth/state/in-trade + BE
+ conviction). FAMILY SHAPE: raw flat; every single gate marginal alone
(weekday p=.096, front-run p=.112); the REAL structure is in-trade
(t+15 AUC 0.81-0.85, early-cut 5.7x) + conviction sizing (monotone).
PROPOSED FROZEN SPEC (for Angus + OOF declaration): front-run-only entry,
no BE, early-cut at t+15 (dying OR cvd-against), conviction-sized
(declared score). OOF: the six sealed months — flow unburned there, so
the flow-conditioned cut IS adjudicable; single look on written
declaration after Angus approves the freeze. NO SHIP without it.
Ledger rows 234-236.
