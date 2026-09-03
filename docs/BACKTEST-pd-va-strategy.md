# BACKTEST — PD VAH/VAL break-retest (his flight-note strategy)

His spec (2026-09-02): 3m close through prior-day VAH/VAL → limit the
retest, stop beyond the close-through candle (prior candle too if the
close-through candle's open is <5pt from the level), 5pt minimum stop,
fixed-R targets, Asia+London the strategy with full-day measured anyway.
His hand-test: one month in replay, ~800–1000pt at 1.5R, 50–75% WR day on
day, "0 trades or 5+" frequency, "probably won't work in NY."

Simulator: `scripts/pd_va_backtest.py` (interpretation decisions in its
docstring). Report: `scripts/pd_va_report.py`. Trades:
`output/analysis/pd_va_trades{,_through}.jsonl.gz`. 908 session-days,
2023-01-03 → 2026-07-14. No lookahead: prior-day levels, closed candles,
forward-only fills/exits, stop-before-target inside any single bar.

## 1. The strategy is REAL — and thin

Asia+London, touch fills, no costs (net R over 43 months):

| target | any-tick depth | ≥3pt depth |
|---|---|---|
| 1.0R | 56.0% WR, **+370R** | 59.0% WR, +389R |
| 1.5R | 43.1% WR, +207R | 44.5% WR, +224R |
| 2.0R | 35.6% WR, +168R | 36.3% WR, +168R |
| 2.5R | 30.2% WR, +133R | 31.1% WR, +163R |
| 3.0R | 26.3% WR, +120R | 27.0% WR, +147R |

Positive at every depth × target — the level genuinely means something.
Per-trade the edge is small: 56% at 1R against a 50% breakeven; 43% at
1.5R against 40%. Roughly +0.08–0.12R/trade before frictions, harvested
by volume (~3 trades/day). Median stop 8.8pt (20% of trades sit at the
5pt floor), median 2min from signal to fill, median 7min in the trade —
this is a scalping cadence, which is why frictions decide everything:

## 2. The two honesty haircuts

**Fill adverse-selection.** Touch fills credit every bounce-to-the-tick
winner a real resting limit might miss. Requiring price to trade one tick
THROUGH the level (guaranteed fill): 1R any-tick drops 56.0%→53.7% WR,
+370R→+222R. The classic limit-order tax is ~40% of the raw edge.

**Costs.** Per round-trip, subtracted in R against each trade's own stop:

| config (AL) | raw | fill-through | through + 0.5pt | through + 1.0pt |
|---|---:|---:|---:|---:|
| any-tick, 1.0R | +370R | +222R | **+36R** | −151R |
| any-tick, 1.5R | +207R | +102R | −59R | −219R |
| **≥3pt, 1.0R** | +389R | +277R | **+140R** | +2R |
| ≥3pt, 1.5R | +224R | +124R | −2R | −128R |

The only configuration that survives honest fills plus realistic costs is
**≥3pt close-through, 1R target**: ~+140R/43mo ≈ +3.3R/month, yearly
2023 ≈ 0 → 2024 +33R → 2025 +48R → 2026 +60R (improving, positive 3/4
years). Every 1.5R+ configuration is negative after the double haircut.

## 3. His hand-test month: found, and it was the best of 43

June 2026 (AL, any-tick): **1.5R → +661pt, 53.9% WR; 1R → +704pt, 67%
WR**. His claimed ~800pt / 50–75% WR is this month almost exactly — and
it is the **best month of 43** (next best +349pt; median month +59 to
+76pt; positive 30/43; worst −162pt). Under fill-through it still prints
+717pt at 1.5R — his eye-test was honest, the month was simply a 10× 
outlier, and it is also the tape he already knew (jl1/narration weeks
live in June 2026). One month of replay sampled the peak of 3.5 years.

## 4. Scoring the rest of the note's claims

- **"50–75% WR day on day" (1.5R):** median day-WR 44%; only 49% of days
  reach 50%. Not replicated at 1.5R. At 1R the aggregate is 54–59%.
- **"5 trades a day even on a bad day":** mean 3.0/day AL; 5+ on 27% of
  days; ZERO trades on 31% of days. Overstated.
- **"0 or 5+" bimodality:** half-true — zeros are common (282/908) but the
  1–4 middle is fatter than the note expects (385/908).
- **"Pump/dump prior day → 0 trades":** directionally right, weak — 
  zero-trade days 24% in the smallest PD-range quartile vs 35% in the
  largest.
- **"Won't work in NY":** WRONG in R-space. NY alone at 1R: 55.4% WR,
  +283R — the same edge. NY's close-through candles are huge (stops run
  30–80pt), so in POINTS it feels wild; in R, with size scaled down, it
  performs like Asia/London. Consistent with the substrate finding that
  R-quality is flat across vol regimes. (Asia is the best window:
  57.8% / +0.50R/day at 1R, vs London 54.5% / +0.32.)

## 5. Verdict against his own acceptance bar

His mechanical bar: **≥50% WR to target in the 1.5–2.5R band**. Measured:
41.5–44.5% at 1.5R (fills either way), ~35% at 2R. **The strategy fails
his bar in his band.** It holds ≥50% only at 1R, outside the band he
declared. Either the bar moves (accept a 1R strategy) or the strategy
needs a selection layer on top — which is exactly the agent-judgement
architecture already ruled.

## 6. Caveats and the one check only he can run

- The certified `volume_profile` carries a documented residual vs
  TradingView's own rows (worst case ~30pt on wide profiles). His
  hand-test used chart-marked levels; ours are computed. The June result
  (+661 vs his ~800) suggests the residual is not fatal, but the clean
  check is his: screenshot TV's PD VAH/VAL for any week, diff against
  `output/analysis/pd_va_days.json`.
- No order-expiry rule in the note: pendings here rest until the next
  signal replaces them or 16:00 (median fill comes in 2min; P90 44min).
- Same-bar stop+target ambiguity resolved AS LOSS throughout
  (~1–3% of trades), and fill-bar stop-outs are taken — both conservative.
- One month of hand-testing cannot distinguish 43-month regimes; this is
  not a criticism of the eye, it is why the corpus exists.

## 7. Stop-and-reverse rule + frequency + fill-wait (added 2026-09-02)

His additions: *"if at any point the 3 min closes through in the opposing
direction mid trade, flatten it, take the flip trade"*; why is frequency
low; does performance degrade when the retest takes long to fill.

**SAR implemented** (`--sar`): opposing crossing close mid-trade exits at
that 3m close (res="SAR", partial R), and the opposing signal is worked
as the normal retest entry. WR convention still TARGET/(TARGET+STOP).

**The frequency mystery is the in-position skips.** Funnel at any-tick
1.5R, 908 days: 11,242 crossings → base rules skipped 5,783 in-position,
575 never filled, 5,084 traded. With SAR the skips become flips: 10,473
traded. Asia+London goes 3.0 → **6.5 trades/day**, 48% of days print 5+,
and zero-trade days stay 282/908 (31%) — days price never touches either
level; no rule changes those. His "0 or 5+" claim describes the SAR
system, and it reproduces. So does his WR band: SAR 1.5R WR = 58.3%
(SAR scratches, netting −0.29R avg, no longer count as losses).

**SAR economics** (AL, any-tick):

| config | net raw | R/day | after 0.5pt costs |
|---|---:|---:|---:|
| base 1.0R | +370R | +0.59 | +180R |
| SAR 1.0R | **+566R** | **+0.90** | +149R |
| base 1.5R | +207R | +0.33 | +43R |
| SAR 1.5R | +325R | +0.52 | **−89R** |

2026-only SAR 1R: +1.18R/day raw. Read: SAR adds real gross edge (cuts
losers at −0.29R instead of −1R, flips catch the reversal) but DOUBLES
trade count, so friction decides — at 0.5pt/trade it is a wash at 1R and
clearly worse at 1.5R+. Live value depends on his actual costs.

**Fill-wait: his hypothesis INVERTS.** EV by minutes from signal to fill
(SAR, AL+NY, both targets): the 0–2m insta-fills are the WEAKEST bucket
(+0.02 to +0.09R/trade) and quality RISES with wait — fills after 30m run
+0.19R, after 60m +0.21R (1R), same shape in every session, strongest in
NY (>60m: +0.32R). An expiry rule would delete the best trades: cancelling
unfilled orders at 30min costs −130R of the 1R total. Mechanically it
reads right: an instant fill means price never left the level (chop at
the level); a slow fill means real displacement then a genuine retest —
the T76 shape from his own narrations. **No expiry rule.**

## 8. His marked-up days + run potential (added 2026-09-02)

He sent four annotated screenshots: Sunday 09 / Monday 10 August 2026,
3m chart, one SVP level at 29,847.75 (VA 70), ~10 executions Sunday
evening through Monday morning, net positive. What they settle without
any replay:

- **SAR was native to the system all along** — "long closed and then
  flipped short", plus two "small loss since candle closed other way"
  scratches: exactly the `--sar` exit-at-close mechanics.
- **The 20:30 candle "did both in same candle lol"** — the ambiguous
  same-bar case; the sim books those as losses (conservative), he
  couldn't call it by hand either.
- **One level, both directions, all session** — matches crossing logic.
- **His chart runs THIS repo's session convention**: the same PD level
  serves Sunday 18:00 through Monday morning — one session-day, prior
  day = Friday. And SVP VA 70 = `volume_profile(value_frac=0.70)`.
- Aug 9/10 is a Monday-anchor session trading high-frequency and net
  positive — the frequency the SAR sim shows (6.5/day mean).

**"Most of the winners would have run for 2r" — CONFIRMED at scale.**
`run_r` (uncapped favourable run before the stop, ignoring target/SAR)
now tracked per trade. Asia+London filled entries: of setups reaching 1R,
**64–65% run to 2R; the median 1R-reacher runs 2.77–2.81R** (identical in
2026). And yet the fixed-target EV frontier still slopes toward small
targets (all-history +0.141R/trade at 0.5R → +0.055 at 2R; 2026 near-flat
0.5–1.5R: +0.184/+0.170/+0.162): a bigger fixed target loses more on the
winners it converts to losers than it gains on the ones that run. Both
facts together are the T78 shape: fixed-target leaves the 2.8R median
tail on the table — the structure that prices it is partial-at-TP1 +
runner, which needs one more tracked field (post-1R pullback-to-entry)
to cost a breakeven-stop runner honestly. Not built until he asks.

**Exact trade-matching is gated on bars**: offline data ends 2026-07-15
and the TradingView MCP lives on the Mac. Protocol: Mac exports 1m NQ
bars 2026-07-15 → present as `data/reference/nq_1m_jul_sep2026.parquet`
(same schema as `nq_1m_feb_jul2026.parquet`) and pushes; this side adds
it to `BARFILES` (scripts/build_l2_outcomes.py) and runs
`scripts/pd_va_align.py --day 2026-08-09 --vah 29847.75 --sar` — the
harness overrides computed levels with his chart's, prints every
crossing/trade with clock times for annotation-by-annotation diff, and
reports the level residual (computed Friday profile vs his 29,847.75)
on the exact day that matters.

## 9. Signal-timeframe sweep + winner/loser features (added 2026-09-02)

His asks: try 1/2/5m signal candles against the 3m; mechanically find
what distinguishes winners from losers; test confluence on entries.

**Timeframe: faster is better, monotone everywhere.** SAR, AL, raw net at
1R: tf1 +900R > tf2 +679 > tf3 +566 > tf5 +301 (WR 77.2/72.9/71.1/66.7%).
The 1m close-through fires earlier in the same move: tighter stops
(median 6.0pt vs 8.2pt at ≥3pt depth), earlier flips, more setups. At
any-tick depth the extra trades die to costs (tf1: 11.4/day, +21R after
0.5pt); the depth filter is what makes speed pay.

**The champion cell: 1m signals, ≥3pt close-through, 1R target, SAR.**
3.3 trades/day. It survives BOTH honesty haircuts:

| fills | WR | raw | after 0.5pt | 2026 after 0.5pt |
|---|---:|---:|---:|---:|
| touch | 66.8% | +666R | **+443R** | +152R |
| tick-through | 63.9% | +501R | **+280R** | **+118R** |

(+118R cost-adjusted honest-fill in 2026 alone ≈ +15R/month. Same cell at
1.5R: 48.9% WR honest-fill — brushing his 50% bar — +99R 2026 adjusted.)

**Features (n=5,919 SAR AL trades, split-half by day), stated honestly:**

- NULL: **attempt number** — the 5th+ crossing of the level trades as well
  as the 1st (58–60% WR both halves). No same-edge fatigue in this
  strategy; the level stays live all day.
- NULL: **his vwap/bb confluence count** at this granularity (IS says 1
  co-closed level best, OOS says 2+; no stable ordering). The hypothesis
  isn't dead — this counts levels inside the candle body, a crude proxy —
  but as measured it sorts nothing.
- NULL: VA width quartile, day-of-week. Notably **Monday trading (Sunday
  anchor) is fine mechanically** (57.9%/60.2% WR) — more evidence the
  agents' Monday problem is a thesis problem, not a tape problem.
- SURVIVES: **close-through depth** (avgR +0.01→+0.10/+0.03→+0.12 from
  <3pt to 6pt+, both halves) — independently re-confirms the depth
  filter, the one lever already in the champion config.
- MODERATE: **displacement quality** — close-through candle ≥2× the
  median recent range: 61.2%→66.1% WR, avgR +0.13 OOS (IS avgR flat).
- MILD: **leg tilt** — reversion_down (short back through VAH into value)
  best in both halves (61.3/61.1%); reversion_up weakest and degrades
  OOS (58.5→51.1%). OOS favors shorts generally — regime risk, flagged.
- MILD: small prior-day range (Q1) slightly better, consistent sign.

Read: after tf/depth/target/SAR, the remaining filters are thin —
structure beats selection in this strategy so far. Displacement-quality
and the reversion_down/reversion_up asymmetry are the two prereg
candidates worth carrying into a walk-forward pass; nothing here earns a
rule tonight. Multiple-comparisons caveat applies to all of it.

**Overfit challenge (his, 2026-09-02) and the three receipts.** "3.3
from 11 trades a day seems like a massive overfit... extracted a small
winning substrate in a broad dataset." Conceded in part: ~40 configs were
swept and one was named, so the full-sample +280R carries winner's-curse
bias — treat it as the optimistic end. But every swept axis was HIS
pre-registered question (depth is in the flight note verbatim, the tf
sweep was his ask, SAR his rule), and three checks say ridge, not spike:

1. **Monotone gradients, no isolated cell** (honest fills, cost-adj, tf1):
   depth −12 → +189 → +280R at 1R; the same ordering at 1.5R and 2R; the
   same depth/target gradients at tf3. Noise-mined winners sit alone;
   this cell is the corner of four smooth slopes.
2. **Positive every year** honest-fill cost-adjusted: 2023 +111pt, 2024
   +155pt, 2025 +648pt, 2026 +1,033pt (through July).
3. **Walk-forward config selection**: scored on 2023–24 ONLY, the grid
   picks the SAME cell (≥3pt/1R is the only clearly positive config:
   +54R; all others negative). That frozen choice then earns **+225.6R /
   +1,681pt on 2025–26 it never saw**. The evaluation period did not
   choose the config.

Monthly POINTS, champion, honest fills, after 0.5pt/trade: every 2026
month positive (+162/+152/+160/+30/+7/+284/+238 Jan–Jul); all-43-month
median +23pt (touch +50pt), positive 30/43, worst −67pt, best +284pt.
The typical month is a grinder; 2026 is where it pays ~+150pt/month per
contract.

**Front-run offset (his idea, 2026-09-02): tested, a wash — and that is
good news.** `--entry-offset` rests the limit N points on the near side
of the level (guaranteed fill whenever price approaches that closely,
worse entry every trade). Champion config, guaranteed-fill ladder,
cost-adjusted at 1R: through-at-level +1,947pt, 1-tick front +1,887pt,
2-tick front +1,929pt — identical within noise, all ~1,000pt below the
touch ceiling (+2,996pt). The toll exactly cancels the regained
bounce-to-the-tick winners; the touch premium is queue-position money,
harvestable only by placing at the level the instant the signal prints.
Implication: the floor does not depend on execution cleverness, and the
1-tick front-run is a legitimate live choice (same EV, zero fill
uncertainty). At 1.5R the toll bites the thinner edge (2-tick: +84pt).

## 10. The 5pt floor at 1m + first true forward test (2026-09-02)

**His floor question:** MIN_RISK=5.0 is enforced at every signal TF — no
3–4pt stops can exist. At 1m it binds hard: **41% of champion-config
trades sit exactly at the 5pt floor** (vs 20% at 3m; median stop 6.0pt).
Floored cohort: 60.3% WR, +390pt cost-adjusted — profitable but weaker
than structural stops (66.9%, +1,556pt; the 5–8pt structural bucket is
the sweet spot at 68.1%). The floor value is load-bearing at 1m; a
4/5/6/7pt sensitivity pass is queued behind the calibration work.

**Data status:** the Mac's TradingView export could only reach 1m bars
back to 2026-08-23 (`nq_1m_aug_sep2026.parquet`, wired into BARFILES;
the 07-15→08-22 hole self-guards via the day-prep minimums). His Aug
9–10 annotated days remain out of 1m reach — the June 10 calibration
day is the primary alignment path; backfilling the hole needs the
deeper-history source that built `nq_1m_master.parquet`.

**Forward test — 7 sessions no sweep ever saw** (Aug 24 → Sep 1, the
champion config frozen beforehand, honest fills, after 0.5pt/trade):
70 trades, **73.7% WR, +152pt**, six of seven sessions non-negative,
one textbook zero-trade day (Aug 26 — price never came back to PD
value). Pace ≈ +22pt/session — at or above the 2026 backtest rate.
Seven days prove nothing alone; they are simply the first evidence of
the right kind, on tape that postdates every parameter choice.

## 11. Fixed stops (his question, 2026-09-02): work at ~8pt, but the
## optimum drifts with regime — structure self-adjusts

`--fixed-stop S` = flat S-point bracket off the level, structure ignored.
Champion frame (tf1, ≥3pt, 1R, SAR, honest fills), cost-adjusted:

| stop | ALL 43mo AL | 2026 AL | ASIA opt | LONDON opt |
|---|---:|---:|---|---|
| structural | **+1,947pt** | +1,033pt | — | — |
| fixed 4pt | +372 | −157 | | |
| fixed 5pt | +1,148 | +325 | | |
| fixed 6pt | +1,688 | +723 | | London best all-hist (+1,129) |
| fixed 8pt | +1,911 | +1,171 | Asia best all-hist (+817) | |
| fixed 10pt | +1,351 | **+1,284** | Asia best 2026 (+736) | London best 2026 (+548) |

Reads: (1) a fixed stop DOES work — 8pt ties structural over 43 months —
but 4–5pt sits inside single-candle noise (2026 median 1m candle: Asia
6.8pt, London 8.5pt) and dies. (2) His session instinct is directionally
right (Asia and London optima differ by ~2pt within an era) but the ERA
dominates: the optimum was ~6–8pt all-history and is ~10pt+ in 2026 —
any fixed number is an implicit volatility bet that goes stale. (3)
Structural stops are the only variant that wins across both eras with no
parameter, because they scale with the candles automatically.

**HIS RULING (2026-09-02): "yeah structural makes more sense" — stops
stay structural** (candle extreme → prior-candle escalation → 5pt floor).
Fixed and vol-scaled stop variants CLOSED; `--fixed-stop` remains in the
sim as an experiment flag only.

**Per-session fixed-R check (his question, same day):** no target beats
1R static in either session over 43 months (Asia: 1R +720pt vs 1.5R
+318; London: 1R +1,226pt vs 1.5R +28, 2R+ −700 to −900 — London
punishes patience in every era). 2026 wrinkle: Asia 1.5R noses ahead
(+632 vs +599, 57% WR) and even 3R prints +544 — the Asia tail is real
in the current regime, but +33pt over ~400 trades in one era is a
watch-item, not a switch. The data keeps pointing at partial+runner
(§8), not bigger fixed targets. Spec stays 1R static both sessions.

## 12. Trend-month hypothesis (his, 2026-09-02): half-confirmed, mechanism found

His claim: the strategy "did shit in May" because the month trended, and
a second trend-specific strategy could complement this one.

Measured: May 2026 WAS the 3rd-most-trending of 42 months (one-way
efficiency 0.51) — but the strategy did not starve there (167 trades,
its most active month). Decomposition: with-trend longs +73pt
(breakout_up 32W/16L), counter-trend shorts −66pt, SAR flip churn
−181pt, costs −84pt. In a one-way tape the always-flip rule pays the
trend tax, not the entry.

Across 42 months, trendiness vs monthly P&L corr = −0.08 (top trending
tercile +44pt/mo vs +50 bottom) — the strategy is roughly regime-neutral
in aggregate, so a trend strategy diversifies by edge type, not by
anti-correlated timing.

HYPOTHESIS (one month of evidence, untested): in trending regimes, take
only with-trend crossings and flatten-without-reversing on opposing
closes. Testable across all trending months, split-half, on his word.
For his separate trend-strategy search the substrate facts stand: CHOP >
TRENDING reach at every band, breakout-continuation is the worst
measured bucket, pullback-continuation with HTF bias (T71–T74, his
narration shape) is the supported form.

## 13. Drive-day engine seed (his ask, 2026-09-02): the stretch is real,
## the trigger must be intraday

His memory: ~3 weeks from late April where "press buy on Asia open, hold
EOD" printed, price supposedly never visiting PD levels — the regime to
build a second engine around.

**Day-by-day, Apr 14 – May 14 2026, confirmed:** up-drives of +364,
+367, +366, +398, +455, +337, +718, +394pt from Asia open to EOD. Two
assumptions corrected: PD levels WERE visited on 21/23 stretch days
(87% of all drive days vs 90% normal — an up-day's VAH sits near its
high; the next Asia dips into it), and the champion strategy earns MORE
on drive days (+7.4pt/day vs +1.5 normal) — no cannibalization.

**Follow-yesterday is dead:** P(drive | yesterday drive) = 20% vs 10%
base, but direction persists only 28% — consecutive drives REVERSE more
than continue. Buy-Asia-open after an up-drive day: −937pt total; sell
after a down-drive: −4,602pt. Yesterday's drive is exhaustion, not
momentum, at day granularity.

**Join-mid-flight is alive (prototype):** if by a checkpoint price sits
≥X beyond Asia open with the open never revisited, enter at market, hold
EOD (no stop). All-history: 22:00/50pt +2,456pt (n=83, 53% win);
03:00/100–150pt +1,800–2,000pt (n=20–40). 2026: 03:00/100pt = +1,753pt
on 13 events (mean +135, median −27 — tails carry, the trend-engine
signature). This is T72 open-drive doctrine mechanized at day scale.
Prototype-grade: 9 cells eyeballed, no stop, no exit design —
his spec to write if he wants the engine. Complementary to PD-VA by
construction: ~10–40 events/year vs ~800 trades, hours-long holds vs
7 minutes, tail-shaped vs grind-shaped.

## 14. The prop lens (his frame, 2026-09-02): EOD drawdown -> daily
## distribution is the metric, full day is the frequency answer

His point: Lucid drawdown marks at EOD, so intraday excursion is free
and frequency drives prop EV (his BB MA did 1–2/day; London/pre-market
were frequency hunts). Champion config, honest fills, cost-adjusted,
daily P&L profile:

| | tr/active day | green | mean/day | worst day | max EOD DD |
|---|---|---|---|---|---|
| AL, 43mo | 5.2 | 56% | +3.4pt | −80pt | −203pt |
| FULL day, 43mo | 10.1 | 67% | +14.1pt | −108pt | −168pt |
| AL, 2026 | 7.9 | 65% | +9.8pt | −49pt | −81pt |
| FULL day, 2026 | 13.6 | 69% | +26.6pt | −82pt | −168pt |

Adding NY raises every prop-relevant stat (frequency, green-day rate,
mean day) — the NY_PRE/NY cuts were agent-stack rulings, not mechanical
ones; his call whether NY runs live here.

Drive-day MFE (his "would be crazy" — confirmed): median champion entry
runs 1.51R before stop on drive days (vs 1.15R normal); 29% reach 3R,
19% reach 5R. The 1R target amputates the entire tail. With EOD-only
drawdown, partial-at-1R + breakeven-runner is the account-shaped exit —
the third independent argument for the runner structure (run-potential
distribution §8, Asia 2026 tail §11, prop rules here). Still un-built;
his word.

**Daily-loss-cutoff receipt (his DD complaint, 2026-09-03): cutoffs make
the drawdown WORSE.** Stop-at-−20/−30/−40pt on the full-day champion:
max EOD DD −168 → −217/−227/−248pt, total −1,000 to −2,800pt. Mechanism
= his own EOD principle: red mornings routinely heal by the close;
a daily stop realizes intraday lows into EOD prints. NO daily stop.
The −168pt episode: 2026-05-26 → 06-02 (trend-churn tail), recovered
06-09. Working levers: MNQ sizing until buffer > DD envelope ($336/MNQ);
AL-only as the eval-phase variant (2026 DD −81pt at +9.8/day); and the
§12 with-trend-only hypothesis, which targets this exact episode —
untested, his word.

## 15. With-trend-only filter (§12 hypothesis): TESTED AND KILLED (2026-09-03)

His go-ahead ran the experiment. Regime flag (prereg'd, two mechanism
amendments made before reading any aggregate result, both in the
`trend_flag` docstring): a day LATCHES trending the first minute its
close sits ≥0.35% of the Asia open beyond that open (T74 "revealed
day"); opposite threshold re-latches. While latched: counter-trend
crossings skipped, SAR flattens but never flips counter-trend.
Flag-off days verified byte-identical to baseline.

Result — worse everywhere that matters, BOTH halves (champion frame,
honest fills, cost-adj):

| FULL day | total | mean/day | maxDD |
|---|---:|---:|---:|
| baseline | +10,766pt | +14.1 | −168pt |
| filtered 0.35% | +5,492pt | +7.3 | −206pt |
| filtered 0.50% | +6,159pt | +8.2 | −204pt |

Split-half: IS +3,987→+1,876, OOS +6,778→+3,616 — degrades in both.
The one thing it fixed is the thing it was built from: the May26–Jun2
hole (−52 → +68pt). Everywhere else it skipped 3,474 of ~8,400 signals
and most of those counter-trend fades were WINNERS — the latch fires on
~most 2026 days (0.35% ≈ 100pt), and fading a stretched tape at a PD
level is a large share of the strategy's whole edge. May was an outlier
month, exactly what the one-month-of-evidence caveat warned.

**Hypothesis killed at this operationalization. Baseline stands
unchanged; the −168pt DD is managed by sizing / the AL eval variant
(§14).** The kill is logged as loudly as a confirm, per register
discipline.

## 16. Partial+runner: TESTED AND KILLED. The DD answer is sizing (2026-09-03)

**Runner build** (`--runner`, `--runner-stop be|orig`, `--runner-tp2`):
half banks at 1R, half free-rolls; runner dies on BE-or-orig stop /
opposing close / TP2 / EOD; does not occupy (frequency preserved); one
runner at a time. Risk-normalized, cost-adjusted, champion frame:

| exit | total | R/day | green | maxDD |
|---|---:|---:|---:|---:|
| **full out at 1R (baseline)** | **+1,131R** | +1.48 | 69% | **−9.7R** |
| runner, BE stop | −428R | −0.56 | 38% | −433R |
| runner, BE + TP2 2.5 | −420R | −0.55 | 44% | −427R |
| runner, orig stop | +485R | +0.63 | 39% | −115R |
| runner, orig + TP2 2.5 | +677R | +0.88 | 58% | −26R |

Mechanism: entries sit AT the most-retested price on the chart, so the
BE runner dies on 4,203 of 4,318 spawns (the ~115 tails average +10R
but pay for nothing); the orig-stop runner rides 2,232 halves back to
the full stop. The run-potential distribution (§8) measured what price
does AFTER entries; the runner must survive the level being retested,
and it can't. **Every variant loses to the plain 1R full exit. The
"three arrows" argument is falsified — the exit was already right.**
Second consecutive kill; logged per register discipline.

**The real DD answer — the −168pt was a sizing artifact.** Fixed 1
contract puts 5–10x the dollar risk on wide-stop (NY) days, and the DD
lived there. RISK-NORMALIZED (fixed $ per R; MNQ makes it practical:
contracts = budget / stop):

- FULL day, 43mo: **+1.48R/day, 69% green, max EOD DD −9.7R**
  (2026: +1.80R/day, −9.5R). Total +1,131R.
- Full-day is SMOOTHER than AL-only in R (−9.7R vs −20.7R maxDD) —
  session diversification works.
- Mapping: $/R = 60% of trailing buffer ÷ 9.7 → $154/R on $2.5k,
  $215/R on $3.5k, $308/R on $5k. At $215/R: ~$320/day average,
  historical worst EOD DD ≈ −$2,090.


## 17. Hour-of-day breakdown (his ask, 2026-09-03)

Champion frame, risk-normalized, split-half checked per hour. No hour
heavily underperforms (worst ~-0.04R/trade vs +0.18 average). Exactly
two hours are negative in BOTH halves: 23:00 and 02:00 - the two
lowest-liquidity transition hours (Tokyo lunch; pre-Frankfurt dead
hour). Cutting them: -267 trades (~3%), ~+10R saved - logged as an
OPTIONAL TRIM, not doctrine (22 buckets tested; some consistency is
expected by chance). NY 09:00-15:00 is the best block - every hour
positive in both halves, ~77%% of total R. 01:00 is the single best
hour (+0.32R/trade, 75%% WR, n=123).

## OPEN (his word needed)

1. Which month was the hand-test? (If June 2026: confirmed found.)
2. Does a 1R-target, ≥3pt-depth version interest him despite sitting
   below his 1.5R band, or does this fold into the v2/Pat grading queue
   as a condition family (PD-VA break-retest) for the selection layer?
3. Aug bars from the Mac (see §8) → run the alignment on his 09–10 Aug
   annotations. Was the 29,847.75 line Friday's VAH or VAL?
4. Whether to price the partial+runner exit structure (§8) against the
   fixed targets.
