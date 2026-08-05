---
date: 2026-08-05
kind: intake diagnosis (dossier)
status: AWAITING ANGUS GREENLIGHT (slate additions P5-P7)
tags: [fabervaale, intake, orderflow, ny-am, pre-market, ivb, absorption]
sources:
  - research/transcripts/fabervaale/ (13 transcripts + CATALOG.txt)
  - research/transcripts/fabervaale/EXTRACTION-A-models.md
  - research/transcripts/fabervaale/EXTRACTION-B-sessions-risk.md
  - research/findings/fabervaale-verification.md
---

# Fabervaale (Fabio Valentini) — full diagnosis and proposed slate additions

Second intake under the trader-sources / quant-validates model. This dossier
is written to serve TWO consumers: this chat's NY-AM optimization program, and
the pre-market program in Angus's other chat (pull the sections marked
PRE-MARKET). Nothing here has been tested; no trials, no ledger entries.

## Verdict in one paragraph

This is the strongest intake source we have diagnosed — and the first with a
genuinely broker-verified core. Fabio Valentini, Italian, Dubai-based, trades
NQ essentially exclusively, New York session essentially exclusively, and has
FOUR real-money podium finishes in the official World Cup Trading
Championships quarterly futures day-trading division (2nd/3rd/2nd/3rd,
2023Q4-2025Q1, best quarter +218.3%, ~546% cumulative — the organizer's own
standings database confirms it). The honest caveats: he has never actually
WON ("world's #1 scalper" is thumbnail inflation; his own site says "Multiple
Vice World Champion"), competition percentages ride on small accounts, and he
sells a $999/quarter room plus fronts the DeepCharts platform, so his
tool-specific numbers are marketing-adjacent. But unlike every other educator
we've assessed, the man demonstrably does the thing he teaches, on camera,
live, for hours, including a published −$9k drawdown day. His framework is
auction theory + order flow with a fully explicit hierarchy (Direction →
Location → Aggression), his flagship model is a quantified NY-AM opening-
range system, and his risk protocol is the most mechanical document either
intake has produced.

## 1. The man (full file: fabervaale-verification.md)

| Claim | Status |
|---|---|
| 4x WCC quarterly podiums, real money, broker-tracked | VERIFIED (organizer database) |
| "Scalping world champion / #1 in the world" | FALSE as stated — never won; repeated runner-up |
| CME Equity Cup top ~0.6%, +54.6% net, 0.42% maxDD | his claim on video; plausible, not independently checked |
| Trades what he teaches | VERIFIED live multi-hour sessions (3.78M-view Chart Fanatics stream etc.) |
| Seven-figure wealth / account sizes | unverified marketing gravity |
| Sells | $999/quarter "Blood, Sweat & Scalps" room (791 members, 5.0★), DeepCharts partner, free Telegram + masterclass |

Intake consequence: his MECHANISM claims earn a real prior. His NUMBERS still
get zero evidential weight until our data reproduces them — same law as
everyone.

## 2. The framework in plain language

Markets alternate between balance and imbalance (same auction doctrine as the
Orochi intake). His hierarchy, stated verbatim in the transcripts: "direction
point 1, location 2 and confirmation of order flow point 3." Direction comes
from statistics (his IVB opening model) or profile framing; location is a
volume-derived level (value-area edge, POC, low-volume shelf, liquidity
wall); the trigger is always the same physical event — one side's aggression
getting ABSORBED (huge effort, no price result = "punching the wall") or
rewarded effortlessly (path of least resistance). Management is a ladder:
break-even fast → risk-free → trail behind aggression prints → exit when the
other side's aggression returns. Order flow never forms trades alone —
independent convergence, again, with our flow-at-entry law.

## 3. Setup families (deduped across both extractions)

- FAB-1 IVB (initial balance breakout) — flagship, NY-AM native. First 30 min
  of NY cash (09:30-10:00) = the day's battle; first side to break it wins
  the day with a claimed +13.5%-over-coinflip skew at 1:1 (long side; short
  side "stronger but gamma-regime-dependent"). Entry = retrace into the IB
  volume profile's POC-to-value-edge zone ("block of orders"), invalidation =
  candle close through the far value edge, TP1 at a statistical excursion
  level (claimed 65-70% hit), RR 1:2-1:2.5 recommended. Model 2 adds an
  absorption/exhaustion trigger at the retrace zone.
- FAB-2 IVB range fade — before the break, fade IB extremes on absorption,
  mean-reverting; stop once broken.
- FAB-3 Effort/result area retest ("deep effort") — absorption or effortless-
  move zones marked, traded ONLY on retest, bias-gated (profile framing or
  IVB), stop beyond zone, ~1:3 + runner; skip never-retested momentum zones,
  late-session prints, and counter-bias prints.
- FAB-4 Deep-trades absorption entry — the generic execution template: big-
  participant aggression absorbed at a qualified level → enter against the
  absorbed side, stop behind level, BE on range break, trail on aggression.
- FAB-5 Value-area fake-out / failed auction — hook of VAH from outside after
  a failed opposite break → traverse to the other side. **CONVERGES EXACTLY
  with the Orochi flagship family (P1). Two independent practitioners, same
  trade, same trapped-counterparty story.**
- FAB-6 LVN / "real FVG" rejection — his redefinition: a fair value gap is
  the minimum-volume shelf INSIDE the fixed profile's value area, not the
  3-candle gap; rebalance pivot, footprint-confirmed.
- FAB-7 Profile-framing daily bias — cash-session-only profiles (overnight
  volume deliberately excluded), P-shape → next-day directional bias, merged
  multi-day balances, value-migration warnings.
- FAB-8 Heatmap reload / break-and-protect family — fresh passive liquidity
  ADDED at a level while aggression fires = fueled move; stop beyond the NEXT
  liquidity area; partials into stacked clusters ("the grill"); iceberg
  completions explain reversals BEFORE the obvious sweep level. Needs depth
  data — we have it (heatmap files).
- FAB-9 Breakout anticipation via double absorption — both range extremes
  absorbed + record-volume candle absorbed → next move is the breakout;
  protected areas don't get revisited.
- FAB-10 CVD pressure filter — never trade against the dominant CVD side;
  CVD lower-low with flat price = absorption (reversal fuel); **pre-market
  version is the Dec-30 competition pattern: CVD distribution visible against
  balanced price from ~06:00 ET, entries at/after the open.** [PRE-MARKET]
- FAB-11 Risk protocol layer (the most mechanical content): prop geometry =
  win rate >60-70% with RR 1:0.75-1:1.5 (low variance passes evals — "you
  are trading the rules, a synthetic market"); flat same-dollar risk per
  execution; platform-enforced daily circuit breaker; day-profit-funded
  scaling (initial risk tiny → adds funded ONLY by the day's realized
  profit → worst day bounded, best day 2.5× worst); A/B/C setup-graded
  sizing; session stop at break-even-of-the-day; evening/fatigue stop;
  journal-driven session pruning (he cut London because his own journal
  showed low profit factor).

## 4. NY-AM relevance (this chat's program)

His entire edifice IS an NY-AM system: IB defined 09:30-10:00, entries
09:30-11:00, "the first battle of the day defines the direction," late
setups discarded even when they'd have paid. The mechanical skeleton of
FAB-1 is fully codable on our bars + fp_minutes today, and our substrate
already computes the IB and day types. Numbers to test rather than trust:
+13.5% skew at 1:1; 65-70% excursion-level hit rate; independent literature
cross-check already in the vault (IB direction → break side 74-81%,
TradingStats; but ALSO the MNQ friction-ceiling negative result — cost
realism will decide this family, per §2.5).

## 5. PRE-MARKET relevance (for the other chat to pull)

1. His doctrine EXCLUDES pre-market entries ("I wait for the 9:30 shakeout
   then I start my session"; off-hours setups get downgraded a full grade,
   "win rate around 40%"). The deepest verified orderflow practitioner aims
   everything at 09:30-11:00. Weigh accordingly.
2. What pre-market IS for him: the reading window. Cash-session-only levels
   built from PRIOR days, heatmap walls built overnight, and the Dec-30
   pattern — pre-market CVD/delta pressure against balanced price as the
   directional gate for open entries. That gate is a directly testable
   FEATURE for: (a) the other chat's pre-market candidates, (b) our shipped
   canon's pre leg (its measured weak spot), (c) any IVB-family candidate.
3. His journal-driven session-pruning method is the honest template for the
   pre-market program's own go/no-go: measure profit factor by session, cut
   what the data doesn't pay.

## 6. Proposed slate additions — Angus picks

(Orochi slate P1-P4 stands as proposed; these add.)

### P5 — fab-ivb (FAB-1 + FAB-2 as one event-tree family) — RECOMMENDED
The quantified NY-AM flagship: IB break direction + retrace-to-IB-profile
entry + pre-break range fade as the tree's other branch. Census his +13.5%
claim and the 65-70% excursion stat on our full span; flow-confirmation arms
on the flow span; strict cost realism (the MNQ negative result is the bar to
clear). REDUNDANCY WARNING: same clock as the canon's gold leg (09:40-10:30)
— correlation battery vs canon fills is a mandatory early gate, like the
euro-handoff precedent.

### P6 — fab-premarket-cvd-gate (FAB-10 pre-market variant) — study + feature
Not a standalone strategy: an L0/L1 study of pre-market CVD pressure vs
balanced price as a direction gate, graded by what it adds to (a) canon pre
leg, (b) IVB direction call, (c) the other chat's pre-market candidates.
Cheap, high-leverage, dual-program. [PRE-MARKET]

### P7 — absorption grammar formalization (FAB-3/4/9 + Orochi F8) — feature library
One committed feature module: per-minute effort/result metrics (volume high,
|delta| high, displacement low, near-level flags), absorption/effortless-move
zone detection, zone-retest events. Powers every current and future
conditioning search and both P1 and P5. Engineering, not trials — no prereg
needed, but built to the same frozen-definition standard as amt_substrate.

### Risk-protocol adoptions (process, for Angus to ratify as rulings)
- FUNDED-SHELL GEOMETRY: his prop law (high win rate, RR 1:0.75-1:1.5, low
  variance) is a design target for what we arm on eval/funded accounts —
  aligns with what the funded-book MC already rewards; propose stating it in
  VALIDATION-PROCESS §2.5 as a funded-deployment preference, not a kill rule.
- DAY-PROFIT-FUNDED SCALING: candidate rule for the live agent desk (adds
  funded only by realized day profit; worst day bounded). Needs Pat's review
  against the arming contract before anything changes live.
- JOURNAL-DRIVEN SESSION PRUNING: adopt as standing analytics on every live
  book (profit factor by session/hour, reviewed at the 5-day loop).

## 7. Cross-guru convergence (the synthesis that matters)

Two independent intakes + our own canon now agree on four things: (1) the
edge source is TRAPPED TRADERS forced to unwind — every surviving setup
family in both dossiers has that story; (2) order flow CONFIRMS at levels,
never generates trades alone — our flow-at-entry law, three times over;
(3) value/balance structure is the map — auction theory in both, our
substrate already speaks it; (4) the NY-AM open battle is the main event —
where the verified performer aims everything, where our canon already lives,
and where P1/P5 point. Where they disagree: Fabervaale excludes pre-market
and overnight; Orochi's NQ evidence is an overnight session. Both can be
right — different edges live in different windows — and the funnel decides,
not the doctrine.

## 8. Honesty box

- The IVB quantified claims come from his own platform's research
  (DeepCharts "protection level" etc.) — marketing-adjacent until our census
  reproduces them. His "audited by an ex-market-maker" claim is unverifiable.
- Competition returns rode small accounts (min $2,500) and the organizer's
  own disclaimer notes competitors may run multiple accounts.
- His room's terms disclose replay/simulated material may appear in
  educational content.
- Every discretion gap in his corpus ("aggressive enough", "clear bias",
  filter thresholds raised on high-volume days) becomes a declared variable
  in our preregs — the extractions list them exhaustively.
- Trial-ledger law: every arm tested from this slate counts toward program
  DSR deflation, same as always. Sparse sleeves certify at book level.
