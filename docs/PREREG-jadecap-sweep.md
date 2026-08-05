# PREREG — jadecap-daily-sweep (NYA-DS-01), as taught

Committed BEFORE any census touches data. Source:
research/transcripts/jadecap/SPEC-as-taught.md (Model 1, the flagship);
credibility: research/findings/intake2-credibility.md (Kyle Ng; the $2.55M
Apex single-payout record is industry-corroborated; no independent
certifier; sells a course + Apex affiliate). Program: NY-AM/PM. Owner:
Claude; verdicts to Angus. §5.9/§5.11/§5.12.1 law in force from birth.

## Thesis (plain language)

Overnight and prior-day trading leaves stop clusters just beyond obvious
hourly swing highs/lows. A push through one of those levels consumes the
stops (trapped: stopped-out longs, breakout chasers on the wrong side);
when the raiding hour CLOSES back inside, the raid has failed and the book
is one-sided — ride the reversal. "No raid, no trade."

## Declared universe

- Bars: 1H (:00-anchored, his platform default) + 1-min for the trade sim,
  from nq_1m_master, full span 2023-2026.
- BIAS (primary, his only stated mechanical rule): prior RTH close vs the
  close before → bullish = hunt swing-LOW raids only; bearish = swing-HIGH
  raids only. Structural-bias variant declared, not run at census.
- LEVELS: prior-gday 1H swing points (3-bar fractal, confirmed at the 3rd
  bar's close), marked as of 09:00 ET, UNTAPPED since formation; if price
  sits beyond the prior day's range, extend one more day back.
- RAID + SFP: during AM window (1H bars 09/10/11:00) or PM window (13/14/
  15:00), a bar trades beyond a marked level and CLOSES back inside = the
  confirmation. Wrong-color-close wait-one-bar variant declared, not run.
- ENTRY (as-taught reading, declared): at the confirming bar's close. His
  words make the LTF entry model interchangeable ("fair value gaps,
  inverted fair value gaps, order blocks... VWAP, moving averages,
  whatever — the context and narrative is already in place"), so
  confirmation-close is a legal as-taught expression; the 5m-FVG execution
  refinement is an L1 arm, not the census.
- STOP: the SFP bar's extreme (his quoted HTF fallback: "the candle that
  created the swing failure"). 5m candle-2 stop = L1 arm.
- TARGET: fixed 2R (his card: "fixed one or two R"; 1R arm declared).
  Opposing-liquidity target declared as L1 arm.
- TIME EXITS (taught, mandatory): AM entries flat by 12:00; PM entries
  flat by 16:00.
- FREQUENCY CAP: first confirmed SFP per day only (his 1-2 attempts/day;
  second-attempt-half-risk arm declared, not run).
- Costs: base 1pt / strict 2pt. Report per YEAR: n/WR/pts/$/PF.

## Declared variables (searched before any expectancy judgment)

Candles: raid penetration depth; SFP close strength (close position within
bar range); level age; distance of level from open; AM vs PM window; gap
context. Flow (flow span): delta of the raid bar (stop-run absorption
signature); CVD divergence at the raid; absorption at the level. Depth
(morning overlap): book state at the raided level.

## Kill classes

K1 structural absence only (§5.9.1): raids with close-back-inside must
exist at teachable frequency. K2 era-flip per arm after search. K3
expectancy only after the complete declared search. Permnull (§5.12-9) on
any state/gate cell before it's called real. Basis-stamp (§5.12.1-13):
census basis = confirmation-close entry, SFP-bar stop, 2R target, time
exits, first-signal-only.

## Promotion rule (§6.0)

Default spec = the census expression above. Displacement only via PBO<0.5
AND holdout adjudication. Trials: merged machine ledger +
research/candidates/nya-daily-sweep.md. Redundancy gate owed vs Brake's
sweep-reclaim / london-level-trap-fade (same raid family, different
sessions) before any book admission.

## AMENDMENT 2026-08-05b — exit/stop tournament arms (declared BEFORE the lab runs)

Basis (§5.12.1-13): L1b population (gap-against + deep-pen cuts), n=117,
confirmation-close entry, base 1pt friction, $160-risk sizing. Default =
census expression (SFP-bar stop, 2R target, 12:00/16:00 time exits).
Arms (10, bounded):
1. default  2. target 1R  3. target 3R  4. no-target (time+stop only)
5. BE@0.5R (the §5.12-6 null — must be defeated, never defaulted to)
6. BE@1R  7. partial 50%@1R + 50%@2R
8. stop-cap 20pt (§5.11-3 class; R normalized to arm risk)
9. stop-cap 30pt
10. hold-to-15:55 (tests the taught time-exit rule mechanically)
Scoring: day-level R matrix -> PBO CSCV (S=16). Displacement of the
default requires PBO < 0.5 AND holdout adjudication (none is declared for
this family yet — so today's tournament can only BANK challengers, not
displace; §6.0). All arms to the merged ledger.
