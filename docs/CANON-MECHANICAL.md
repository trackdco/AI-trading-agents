# THE CANON (Angus 25-Jul ruling: default system — do not divert unless explicitly asked)

`scripts/canon_mechanical.py` → `output/canon_book.parquet`. Both books, every day, no book
choosing, no day forecasting. Validated out-of-fit: **2025 +$14,349 / 2026 +$30,343**,
maxDD $5.6k/$3.0k, ~2 trades/day, WR 38%/43%.

| layer | rule |
|---|---|
| 0 hard gates | stop ≥ 7 pts (pre) / post-open floor 10 (golden, after 09:40) |
| 1 validation | 5 checks at fill: W wall-behind absent · F fill-bar delta confirms · T not fighting 15-min tape · G VWAP-side geometry aligned · C window-correct CVD (PM→pre, LON→gold) |
| 2 sizing | score ≤2 → 0 · 3 → 0.5 · 4 → 1.0 · 5 → 1.5 |
| 3 governor | trailing-15 confirmed-trade WR < 0.35 → all sizes ×0.5 (results-based, no forecast) |

## Bleed-day diagnosis (25 Jul, canon book: 63 bleed days −$37.5k vs 75 winner days +$87.2k)

**Composition is NOT the problem.** Bleed and winner days are near-identical in score mix
(mean 3.7 both), %score≥4 (54 vs 57), window/setup mix, trades/day. Two modest tilts: bleed
days have fewer wall-behind-absent fills (43% vs 56%) and lean short (44% long vs 54%).

**The edge is binary by day.** On winner days the checks separate hugely (F 76% vs 56%,
C 78 vs 57, G 74 vs 42). On bleed days ALL five checks stop separating (W 8 vs 12, F 8 vs 13)
— confirmed trades lose at the same ~90% rate as everything else. Bleed days are a regime
where the edge is wholly offline, not days where bad trades slipped through.

**What bleed days share ex ante (modest, directional):** half the pre-market conviction
(|cvd_PM| median 315 vs 538), fresher overnight extreme (122 vs 184 min), stalling CVD accel,
choppier pre-market path — the same verified gold-red family, still too weak to hard-gate.

**Jul-Sep 2025 specifically = dead tape:** overnight range −40% (median 107 vs 177 pts),
volume −19%. In that tape the CVD checks degrade to noise (C inverts: on 28% vs off 32%) but
the **heatmap check keeps working** (W: 42% vs 23% WR, +$11 vs −$135/t) — book structure
survives thin tape; flow signals don't.

**Circuit-breaker candidates (tested, NOT shipped — canon unchanged):** stop-after-2-consecutive
-losses hurts (−$2.1k/−$2.4k). Day-stop at −$400 helps mildly (+$1.1k 2025 / +$0.1k 2026,
Jul-Sep −$4.6k → −$4.1k) — candidate for the 2023/24 holdout, not canon.

## Jul-Sep dissection round 2 (25 Jul): what held it back + mechanical candidates

**Within Jul-Sep:** A-setups were GREEN (gold A +$597/60%, pre A +$262/75% — reversals thrive in
chop); the bleed is B/B2. The structure checks kept working (W +19pp, T +11pp — better than in
good months); the flow checks died (F −5pp, C −4pp — CVD/delta = noise in dead tape). Trades
with BOTH W and T: 48% WR, +$662. Without both: 23% WR, −$5,276 = the entire bleed. And trade #2
of the day carried −$3,831 of the −$4,614 (trade #1 was flat). Within-period trap: the BAD
Jul-Sep days were the bigger-range/bigger-gap "fake start" days, not the quietest ones.

**Universal rule candidates (no regime detection needed), tested full-span:**

| rule | 2025 | 2026 | Jul-Sep | good mo | months green |
|---|---|---|---|---|---|
| canon | +14,349 | +30,343 | −4,614 | +49,307 | 9/13 |
| **A: trade#2+ requires W+T=2** | +15,612 | +27,589 | **−102** | +43,303 | **11/13** (worst mo −$892) |
| **E: trade#2+ requires score≥4** | +14,371 | +30,862 | −4,004 | +49,237 | strict upgrade, small |

Rule E is a free ~+$1.1k (never worse anywhere). Rule A is a consistency trade: erases the
bleed months (worst month −$892 vs −$3,438) for ~$1.5k/2yr of total P&L, cost sitting in 2026
good months. NOT shipped — canon unchanged pending Angus's ruling / 2023-24 holdout.

## 25-Jul: Layer 2b SHIPPED + within-day escalation ladder (candidate V5)

**Layer 2b now canon** (Angus ruling): trade #2+ of the day requires score ≥ 4.
Canon = +$14,371 / +$30,862.

**Escalation ladder tested (results-based, zero forecasting — reacts only to realized losses):**
day running P&L < 0 → subsequent entries require BOTH structure checks (W wall-behind-absent +
T not-fighting-tape), A-setups exempt (reversals thrive in bad tape) → day P&L ≤ −$400 → sit
out the rest of the day.

| | 2025 | 2026 | Jul-Sep | good months | green | worst month |
|---|---|---|---|---|---|---|
| canon-E | +14,371 | +30,862 | −4,004 | +49,237 | 9/13 | −2,591 |
| **V5 full ladder** | **+18,171** | +29,716 | **−1,038** | +48,925 | 10/13 | **−789** |

V5: +$2.7k total over canon, Jul-Sep bleed −$4.0k → −$1.0k, good months give up only $312,
worst month −$789. **SHIPPED into canon 25-Jul (Angus ruling) as Layer 2c.** Canon full stack:
**+$18,171 / +$29,716**, maxDD $2.8k/$3.3k, worst month −$789, ~1.3 tr/day.

## 25-Jul: stop-size ruling + MAE study

**SHIPPED (Angus ruling): hard stop cap ≤ 60pts** (Layer 0). 29 trades carried 60-136pt stops;
0 of their 12 wins ever reached 2R — invalid under the min-2R doctrine. Canon now:
**+$18,011 / +$25,560**, maxDD $2.5k/$3.0k.

**MAE study (275 canon trades, fill→exit, 1m bars):** winners barely use their stops —
median MAE 5.6pts = **37% of stop**; 64% of winners never see half the stop; even 40-60pt-stop
winners median just 17pts (35%). Confirms the retest-entry thesis: a working retest never goes
deep. First-order tightening sweep (stop = k× current): k=0.8 IMPROVES total P&L
(+$41.4k vs +$38.5k baseline) losing only 10/118 winners; k=0.7 roughly break-even; below that
it degrades. **Stops are ~20-25% too wide across the board.** NOT shipped — true stop
placement changes trade evolution (needs engine re-sim, and holdout confirmation to avoid
tuning on two years). Logged as holdout candidate #2 behind the dead-tape W-weighting.

## 25-Jul: IN-TRADE order-flow autopsy (3 workflows, 22 agents, all verified 4/4)

Question: what do losers look like IN FLIGHT that winners never do? (Winners' median MAE = 37%
of stop — they never get stressed.) Matrix: 713 trades, features at 3/5/10min after fill, no
hindsight. Every finding below verified by independent recompute + half-period stress.

**The loser-in-flight signature (readable at 3 minutes):**
- Underwater at 3min: 18%/15% WR vs 49%/55% if in profit — the single strongest in-flight read.
- Deep red (≤−0.36R) at 3min: **5%/11% WR** (Jul-Sep: 3%) — near-certain loss.
- MAE ever ≥0.7R by 3min: 13%/19% even if price recovered — excursion depth itself is the tell.
- Net delta against the position (fw_3<0): 22%/23% vs 47%/51%; the combo **underwater AND flow
  against = 11–18% WR** (Jul-Sep h5: 8%). Sellers pressing while underwater corroborates.
- FAILED ABSORPTION: price adverse + flow "with us" = loser flag (18%/26%), NOT defence. Depth
  appearing behind the position after entry likewise. Comforting microstructure is the trap.
- Winner mirror: in profit early, MAE <0.37R, book building — winners are never stressed.
- Nulls: path efficiency dead; book-imbalance rotation dead; absorption does not rescue.

**PRICED EXIT RULE — SHIPPED 25-Jul as Layer 2d (Angus ruling): at 3min, if r ≤ −0.11R AND fw ≤ −13 → exit.**
On the TRUE sized-canon basis (correction 25-Jul: the agents' first pricing used raw 1-lot
dollars): +$1,494 (2025: 18,011→19,505) / +$2,369 (2026: 25,560→27,929); Jul-Sep −$1,157 → −$91
(flat). Note: shipped canon Jul-Sep is −$1,157, not the pre-ship +$257 estimate — the Layer-0
cap re-orders the daily ladder. Over 2yrs the rule cuts 47 losers, falsely cuts 6 winners.
Flagged trades win 7%/11%. CRITICAL: only h=3 works — the same rule at 5/10min LOSES money
(late exits lock in drawdown + forfeit recoveries). Exit P&L approximated as r_3-at-market;
true engine implementation + holdout confirmation before full trust.

## CANON AS SHIPPED (final stack, 25-Jul)

Stop 7-60pt → 5-check validation → ladder sizing → trade#2+ needs ≥4 → **3-min in-trade cut**
→ within-day escalation (structure required when red, A exempt; −$400 day stop) → governor.

**2025 +$19,375 · 2026 +$27,711 · Jul-Sep −$91 · 11/13 months green · worst month −$981 ·
maxDD $2.0k/$2.2k · WR 41%/46%.** In-trade cut fired 54 times. All layers results-based or
2025-frozen; 2023/24 random-day holdout is the standing validation gate for everything.

## 26-Jul: bad-PA judgement layer — the full test (3 workflows, 20 agents, verified)

Question: can a mechanical bad-price-action layer add selectivity on top of canon? 18 new
pre-fill features (whipsaw, level churn, wick structure, indecision, squeeze, two-sided tape,
trigger density, CVD divergence, sequencing) on 713 trades / 275 canon.

**ECONOMIC VERDICT: NOTHING SHIPS — and that is the finding.** 18 rules cleared the win-rate
bar on canon; ZERO corroborated on the full universe both years; every 2025-attractive veto
lost $2-5k frozen on 2026. Structural reason: canon sizing concentrates P&L in a few large
winners and WR-based vetoes clip exactly those. Half-size never rescues (linear). The canon
has already consumed the mechanically recoverable losses; Jul-Sep's residual −$91 is not
explained by any PA flag (flagged P&L there is positive).

**Real (verified) bad-PA markers — WR-level, kept as inputs not vetoes:**
- wicky_10 LOW (full-bodied bars driving into the level — the "retest" is a freight train,
  not a rotation): −14/−16pp canon, −14/−8pp universe, sign-stable q10-q30. Strongest PA marker.
- indec_30 HIGH (indecision bars): canon-confirmed, universe plausible; flagged = dead money.
- BADFLOW-B (aggressive 15m delta into wicky bars = buy-climax into absorption): the only flag
  with net-NEGATIVE flagged P&L both years (−$496/−$1,149); mostly longs.
- GOOD-PA inverse: netpath_30 ≥ q90 (efficient path into fill) = +12-14pp everywhere,
  39 canon trades +$15.4k — a SIZE-UP holdout candidate (1.5x would have added ~+$4.5k/2yr).

**Hypotheses killed:** level churn (REJECTED — canon WR rises with churn), engine over-firing
as chop (over-firing is a WINNER tell), whipsaw path (only the positive extreme matters), vwap
crosses/slope, squeeze state, two-sided tape (sign flips), loss-stops (post-loss = best cell,
66.7% WR — actively contraindicated), yesterday-red vetoes.

**Disposition:** the verified WR markers become the chop/PA agent's designated INPUTS if it
ever activates (dormant, A/B-gated), and netpath-high size-up + BADFLOW-B veto + cvddiv_30 go
to the 2023/24 holdout. Canon unchanged.

## 26-Jul: Layer 2e SHIPPED (Angus ruling — both rules)

RULE 1 (cold-grind cut): trailing-20 canon WR < 0.40 AND one-sided 30m flow → size ×0.5.
RULE 2 (good-PA boost): netpath_30 ≥ 0.3328 (2025-q90), not R1-flagged → size ×1.5.

**CANON FULL STACK: 2025 +$22,532 · 2026 +$28,844 · Jul-Sep +$754 (GREEN) · 11/13 months
green · worst month −$312 · maxDD $1.7k/$2.3k.** The chop quarter that began this campaign
at ~−$10k is now positive. Rule 1 is the lowest-evidence layer (state-conditional, post-hoc
searched) — first to pull if the 2023/24 holdout disputes it; Rule 2 carries full verification.

## 27-Jul: THE GOLDEN CAMPAIGN — window-native canon SHIPPED (Angus ruling)

Trigger: "pre-market is optimized; go back to the raw trade data and qualify each trade,
trade by trade, specifically in the golden window. Test every single variable."

**Step 1 — the inherited ladder was pre-market's ladder.** Tested each shipped check on the
218-trade gold universe (111/107 by yr): C (London CVD conf) DEAD (+4/+3pp), G weak (fails
2026), F weak; only W and T carried. Gold was wearing pre's clothes.

**Step 2 — gold-native rediscovery sweep** (every at-fill/pre-fill var, 2025-GOLD-frozen
thresholds, both-years ≥10pp, 4-halves): 23 survivors collapse to 5 orthogonal checks:
- **D** wall exists AHEAD (not pre's wall-behind-absent!). Toxic state = only wall is behind
  you: WR 14%/12%, avg −$282/−$281 both years independently.
- **Tc** d15_conf; **X** bbw_state ≥ g-q75 (vol expansion); **AGE** on_extreme_age ≥ g-q50;
  **PAQ** netpath_30 ≥ g-q25. Ladder monotone both years; reject pile (≤2) = −$31k/2yr bleed.

**Step 3 — the full 8-family campaign** (8 workflows, 37 agents, screen→adversarial-verify,
must-ADD-beyond-incumbents rule). Confirmed: WALLSZ (wall ≥7 contracts ABSOLUTE — relative
sign-flips), BIGFD (|fill-min delta|≥173; only reject-pile rescue found), FDCONF+BP5OPP=T2
(fill-minute aligned OR absorption fill into counter-flow), TRIG (>11 trigs/30m GOOD in gold —
inverts pooled chop lore), VWAPD (dir-signed ≥0.107 — the real signal inside weak G),
LONSLOPE (London cum-delta OLS slope — London matters as trend+veto, not conf).
Negatives confirmed but NOT shipped as vetoes: dollar decomposition showed the gscore ladder
already rejects nearly all their damage; within sized g≥3 their fail cells are EV-neutral
(payoff ratio carries 35% WR). Hard-vetoing all of them flags 80% of universe and destroys
$12k — the great veto trap.
Honest nulls: entire RTH-open-flow family, session voting, sweeps, calendar (DOM_EARLY
soft/paper-track only), fill-time within window, all in-trade cuts (gold self-scratches at
−0.5R; 3-min cut is EV-neutral in gold; 5-min time-stop → holdout).

**Layer 2q SHIPPED:** Q = count{WALLSZ, BIGFD, T2, TRIG, VWAPD, LONSLOPE}.
Q≤1 → NO TRADE (Angus: "why are we even taking them" — 12/16 losers incl. every 53-56pt
monster; WATCH ITEM: 16-trade cell, first re-test on 2023/24 holdout).
Q≥3 → one ladder step up, cap 1.5 (boost cell WR 83%/82%, avg +$805/+$699).

**WINDOW-NATIVE CANON FULL STACK: 2025 +$31,175 · 2026 +$40,189 · Jul-Sep +$2,034/−$98 ·
12/13 months green · worst month −$98 · maxDD $2,492/$1,872.** vs prior canon
+$22,532/+$28,844: +$20k/2yr, better in all 4 half-periods independently, threshold-grid
stable (±$3k band across all Q boost/demote cut combos). Gold contribution 13k→33k.
Superseded: the gold-B div15 veto (harmful under native ladder — same disease, worse cure).
Holdout list: Q-tier mapping (esp Q≤1 cut), gold 5-min time-stop, DOM_EARLY, dead-tape
W-weighting, 0.8x stops, netpath size-up replication, BADFLOW-B, cvddiv_30.

## 28-Jul: THE LONDON CANON SHIPPED (third canon — Angus ruling)

Doctrine settled: sessions are structurally different; each window gets its own
mechanically-derived book (pre / gold / London), one skeleton, agents execute per session.

**Build**: 8,669 DST-correct triggers (first 2h London, 08:00-10:00 UK) -> 749-fill
both-books substrate (raw −$842/+$502 ≈ breakeven blind — best raw start of any window)
-> 30-feature matrix + 295-day MBP-10 heatmap depth (100% coverage) -> 8-family
screen->adversarial-verify campaign -> integration.

**THE LONDON BOOK**: gates risk>=9.5pt NO CAP (sub-7 kill; NY's 7-60 not inherited);
checks W (no wall behind — pre-like), FAR (wall ahead >4.5pt), ROOM (2.48-9.56R to the
target-side ON extreme — flagship construct), ASIA (dir*cvd_ASIA >= −748); ladder
0/0.5/1/1.5; B needs score>=3 (4/4 halves); OF stack (ASIA + clean tape opp5<2):
both->x1.5 boost (76%/80% cell), zero->x0.5 and score-2-zero-OF = NO TRADE (Angus:
"remove it, we are trading more than enough"); trade #2+ needs >=3; NO in-trade layer
(loss-cuts EV-null; stall exits EV-NEGATIVE — London stalls recover 31-52%; gold's
5-min time-stop LOSES −$2.3k/−$1.3k here — three windows, three in-trade answers).

**SHIPPED: 2025 +$21,825 · 2026 +$13,394 · WR 59%/60% · PF 3.33/2.55 · maxDD
$1,578/$1,488 · all 4 halves positive.** Jul-Sep 2025 GREEN (+$2.3k) while NY bled —
London skips the US summer doldrums. COMBINED with NY canon: ~+$106k/2yr, day-corr
+0.11, combined maxDD $2,230 < NY alone ($2,492) — adding London REDUCES peak DD.

**Laws re-confirmed (3rd window)**: micro-stops toxic; winners-run-immediately (82%
never see −0.75R); veto trap (all scoped vetoes +EV inside the sized book — findings
become checks, never vetoes, unless fail cell is dollar-negative INSIDE the book);
depth is a top family everywhere but the DETAILS invert (pre: nothing-behind; gold:
big wall ahead; London: nothing-behind + far wall + room). Signals invert across
windows: aligned-flow chase is a boost in gold, a fade in London; extension good in
gold-B2, veto in London-B2. Nothing universal but the skeleton and the method.

**Holdout list (2023/24)**: B>=3 + OF-stack recalibration, TAPE ablation, W/FAR
collapse (r=0.86), ROOM band edges, DST weeks, early+tight-stop timing rule.
