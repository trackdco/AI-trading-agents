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
