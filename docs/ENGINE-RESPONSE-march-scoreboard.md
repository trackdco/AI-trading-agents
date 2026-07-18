# Engine-lane response to the March regime scoreboard (pass 33)

Pat's finding (docs/REPLAY-MARCH-REGIME-SCOREBOARD.md): agent effect −$5,365 on a green
month — saved $3,776 on losers, clipped $9,158 off winners (2.4x premium), and the
war⇒continuation-only rule vetoed the book's pattern-A fade edge (03-19).

## Hypotheses for the asymmetry (Angus + engine lane)
H1 Brakes-only action space: the verdict vocabulary is purely defensive; the oracle's
   edge is ~half opportunity-seizure. A subtractor can only subtract in green months.
H2 Uncertainty defaults to defense ("medium confidence -> half size") — a caution tax on
   every ambiguous day. AMENDED (Angus, pass 33): the fix is NOT "default to champion" —
   the champion is only healthy in 2026 (it lost $6k/$14k/$15k in 2023/24/25). Correct
   default is HEALTH-CONDITIONED: defer to baseline only when the baseline is locally
   alive (trailing-20d arm-A expectancy > 0, or analog-conditional expectancy > 0 for
   today's vector). Baseline healthy -> unsure = don't interfere. Baseline sick -> unsure
   = defend, and TRADING requires the conviction instead. Computable daily from the
   journal (arm A runs as the permanent control).
H3 One 08:00 verdict rules the whole day — no release valve when the day proves itself
   (03-17: +$3,485 -> +$450 with the brake left on all session).
H4 Structure bans encode narrative, not the book's measured conditionals (war book earns
   via pattern-A fades; the ban came from folklore, not the journal).
H5 The prompt's job description shapes P&L: an agent told to de-risk will over-de-risk.
   It was never told the measured 2.4x clip-to-save exchange rate. It should reason with it.

## Bridge plan — ORDER MATTERS (anti-tuning)
1. FAIR EXAM FIRST (no agent changes): rerun the SAME agent on a red month (May 2026
   and/or a 2025 stretch). March = the premium; we need the payout side before any
   redesign, or we are tuning on one green month.
2. Then ONE design pass (Angus ruling, Pat build):
   a. Symmetric action space: add press/confirm verdict; DEFAULT = health-conditioned
      (see amended H2); brake AND throttle both require cited conviction.
   b. 09:30 second look (one extra call/day), narrow authority: may only RELEASE an
      08:00 brake, never add mid-day brakes.
   c. Permitted-structures must cite data: engine lane wires L2 analog conditionals into
      the briefing ("on the K nearest days: fades $X, continuations $Y"); no ban without
      a conditional stat behind it.
   d. Regret ledger: both arms run daily anyway -> log each intervention's counterfactual
      cost; feed the agent its own regret history via playbook notes (it learns the
      insurance asymmetry itself).
   e. (Already filed) schema: rationale cap fix; playbook-note compaction.

Engine-lane deliverable for (c): analog-conditional briefing block, buildable now from
output/allyears_book_trades.csv + regime vectors.

## Addendum (pass 33): scope + v0.3.0 caution
- Coverage so far: March 2026 only (22 verdict days) + the 3-day pilot. No red month or
  other year has faced the agent yet.
- Pat's v0.3.0 March retest (-$5,365 -> -$1,715) is real progress AND is now one
  iteration deep on the same month — the improvement must be confirmed on a month the
  agent was not shaped by (May 2026 / a 2025 stretch) before it counts. Same anti-tuning
  rule the engine lane lives under.
