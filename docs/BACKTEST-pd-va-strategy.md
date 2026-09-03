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


## 18. Level calibration against his chart (2026-09-03): PASSED

Four sessions read off his TradingView SVP (VA70) vs the computed
profile, 8 edges: mean error -1.6pt (NO systematic bias), median -2.5pt,
5/8 within 12pt, 8/8 within 25pt. VA widths match to 1pt on the 450pt
session. Worst day ~20pt on both edges (Tue16->Wed17). Errors are
day-specific volume-modeling noise, not an offset.

Jitter receipt: champion config re-run with levels perturbed by the
MEASURED error distribution (N(0,12) clipped +/-25, 3 seeds): +1,027 /
+985 / +1,001R vs +1,150R baseline - the strategy keeps ~86-89%% of its
edge under the level noise; months positive 98%% (worst month ~-5R).
The edge lives in the level's NEIGHBORHOOD, not tick placement. And
since the computed levels are themselves ~one noise-draw off his
chart-true levels, the backtest most likely UNDERSTATES the chart-level
version by roughly the same ~10-14%%.

Remaining gate: the June 10 TRADE tagging (crossing/retest/flip
language), levels now calibrated.


## 19. TRADE-LANGUAGE ALIGNMENT: CERTIFIED (2026-09-03) + the news gate

His June-10 tagging (session 2026-06-09, 1m chart, 1R, SAR live) vs the
sim, same session: **7/7 of his NY trades found within 1-2 minutes, 6/7
same result** (9:35 L, 11:00-fill W, 11:09 W, 11:26 SAR-scratch ->
11:28 flip W, 11:45 same-candle-ambig L booked exactly as he books it,
12:02 W; only the 11:57 fill diverged W/L). Asia empty in both. His
"first break ~6:42, 7:02 to-the-tick fill, 6.5pt prior-candle stop,
~20R run" trade exists in the sim shifted by ONE POINT of level: his
VAL 28,845 vs computed 28,846 - the sim's version filled at the 08:30
news candle instead and died. Individual trades can flip on 1pt; the
aggregate cannot (S18 jitter receipt). HIS RULING: within-a-point
levels "not going to affect the statistics much" - tolerance accepted.

**Pre-market defined: 08:00-09:30 ET (his ruling).**

**News gate implemented** (`--news-gate`, news_archive.csv, 172
high-impact pre-market dates 2023-2026): on those days no entries
08:00-09:30 and pendings pulled at 08:00 (the June-10 stale-limit-
filled-by-the-8:30-candle case is exactly what it deletes). Effect on
the champion: +1,131R -> +1,133R, maxDD -9.7 -> -10.8R - a WASH on
totals, removing 191 trades that were sim-positive (+0.09R/trade avg)
but whose news-candle fills are the least trustworthy prices in the
whole dataset. Zero measured cost, real model-risk removed. RULE IN.

With the Aug/Sep forward days included the gated profile reads 45/45
months positive, worst month +2.5R.

STATUS: spec certified against his eyes end to end - levels (S18),
grammar and results (this section). Ready for the seven-gate hand-off.


## 20. Final-spec breakdown + loss anatomy (2026-09-03)

News-gated champion, risk-normalized, honest fills, costs in. Yearly:
2023 +234R (67.2%% WR, +1.11R/day) / 2024 +350R (68.7%%, +1.67) /
2025 +323R (67.1%%, +1.48) / 2026 +226R (66.2%%, +1.81). Green days
68-73%% every year; per-year maxDD never past -10.8R. Monthly: 45/45
positive, median +25.3R, worst +2.5R, best +47.3R.

Loss anatomy - nine pre-entry features, split-half: **no loss filter
exists.** Nothing knowable before entry consistently marks losers.
Stable findings, both halves:
- Stop-size is the one gradient: 5pt-floored trades earn about half
  the EV of 5-10pt-stop trades (+0.09-0.15 vs +0.19-0.21) but remain
  clearly profitable - a size-of-edge gradient, not a filter.
- FLIP entries beat fresh entries (+0.19 both halves vs +0.13-0.16):
  his SAR rule's re-entry is the best entry type in the book.
- 4th+ attempts at a level trade as well as the 1st (no fatigue), and
  entries AFTER A LOSS at the level outperform entries after a win
  (+0.18/+0.18 vs +0.16/+0.14) - a failed attempt cleans the level.
- Asia EV flips sign between halves (unstable, not actionable); leg,
  VA width, PD range, day-of-week: flat.
The edge is uniform across everything observable - the signature of a
real mechanical edge rather than a conditional one. Further filtering
is the path the killed experiments (S15, S16) already walked.


## 21. Loss anatomy round 2 - heavy machinery, prereg'd rule (2026-09-03)

His ask: more pre-entry features, using everything available; his own
caveat that high-frequency + low bounding makes a separator unlikely,
but the sample (n=7.6k) gives the power to know. Eleven bars-based
features (VWAP side + stretch, 15m MA alignment, weekly VA, session
position, chop v2, level touch count, time-since-touch, day density,
2h drift alignment, open-vs-VA gap), split-half, with the verdict rule
FIXED before results: survivor = same extreme ordering both halves +
>=0.05R spread both + n>=400 per extreme per half.

**ZERO SURVIVORS.** Three watch-items, all pointing the same mild way:
with_drift beats against_drift (+0.04R both halves), toward weekly
value beats inside (+0.03 both), and the 7th+ trade of the day beats
the 1st-2nd (+0.05, OOS misses the bar by 0.001). A faint with-trend/
toward-value tailwind, none of it actionable alone, and stacking
watch-items post hoc is the fishing the rule forbids.

The rule earned its keep visibly: vwap stretch z2+ printed +0.264R
in-sample and collapsed to +0.036 out-of-sample - the textbook
half-flip a naive screen would have shipped. touches 0-5 did the same
(0.179 -> 0.074). time-since-touch turned out degenerate by
construction (the crossing candle just touched the level) - a design
flaw owned, not data. VWAP-relative direction and 15m-MA alignment:
dead flat - remarkable in itself.

**Conclusion, with real power this time: the edge is unconditional.**
At this n, a >=0.05R conditional edge across these dimensions would
have been found. His instinct was right, and the mining stops here.

## 22. GOLD PORT (2026-09-03): the mechanics transfer; higher-R rejected

Databento GC raw batch (all instruments) -> volume-rolled continuous
(`scripts/gc_continuous.py`: outrights only, front by session volume,
19 rolls flagged and their day-pairs excluded). Constants derived from
GC's own tape at the NQ certification ratios (tick 0.10, floor 1.5pt,
depths 0/0.3/0.6/0.9, bin 0.3, cost 0.15/RT). `--instrument gc` swaps
everything; the pipeline is otherwise byte-identical.

**Structural confirmation:** WR at every target within ~1pt of NQ
(1R 62.2%% vs 63.9; 1.5R 47.9 vs 48.9; 2R 39.1 vs 39.4; 3R 28.9 vs
29.9) with zero behavioral re-tuning. The level grammar is auction
physics, not an NQ artifact.

**His higher-R hypothesis: REJECTED.** Gold's target frontier has the
same shape as NQ's - 1R dominates, everything >=1.5R negative after
honesty haircuts, big-target WRs marginally LOWER than NQ's.

**Regime split:** 2023-24 flat-to-negative (+17/-41R) - partly real
(quiet gold), partly constants-era mismatch (0.4-0.5pt candles vs the
2026-anchored 1.5pt floor; adaptive floors deliberately not fitted).
2025-26: **+224R over 20 months, +0.71R/day, WR 63-65%%, 14/20 green
months (median +9.7R, worst -6.2R), maxDD -14.6R.** Walk-forward
receipt: the 2023-24 grid picks the SAME cell (>=0.9/1R, the only
near-positive config), which then earns the +224R on unseen 2025-26.
Cost sensitivity: 0.10/0.15/0.20 per RT -> +285/+224/+163R.

Read: in the current regime GC runs the same machine at roughly half
NQ's daily rate, with heavier relative cost drag (0.15pt on ~1.7pt
stops) and 36%% floored trades. As a second, likely-uncorrelated
stream beside NQ it is additive; as a solo instrument it is the
lesser tape. His call.

**Timeframe + session anatomy re-derived on GC (his check, 2026-09-03):**
the tf gradient replicates independently — depth-analog 1R, honest,
gated, 2025-26: tf1 +224R > tf2 +117 > tf3 +98 > tf5 +16 (WR 62.2 ->
59.3%%), same monotone faster-wins shape as NQ. Session anatomy too: NY
is the best window on gold as well (67.4%% WR, half the total R), and
23:00 is a bottom-three hour on BOTH instruments (the Tokyo-lunch lull
is market structure, not an NQ artifact). Three structural patterns now
replicate cross-instrument with zero shared fitting: the 1R-dominant
target frontier, the faster-signal gradient, and the session/hour map.
GC's tf1 choice stands on gold's own evidence, not inheritance.

**Gold-native floor/depth calibration (his push-back, 2026-09-03):**
"we can't base it on a ratio of NQ" — swept natively: floors 1.0-3.0pt
x depths 0.3-1.5pt, picked on 2025, verified on 2026. Result: gold's
own grid lands ON the ratio-derived cell. The ridge is floor 1.0-1.5 x
depth 0.9-1.5, flat across it (2025 best 1.0/0.9 +138R vs analog
1.5/0.9 +130R; on unseen 2026 the analog VERIFIES BETTER, +93R vs
+84R, with floor-1.5 the best row: d1.2 +99, d1.5 +108). Both
gradients are monotone and mechanical: floors >=2pt bleed in every era
(oversized bracket vs a 2.1pt candle), depth 0.3 bleeds everywhere
(sub-noise closes). Even 2023-24 prefers the same corner shape - it
just cannot clear costs. RULING KEPT: floor 1.5 / depth 0.9 stays;
moving to a neighbor on this sweep would be picking noise off a flat
ridge. The ratio method is hereby validated as a starting prior that
native calibration confirmed rather than overturned.

## 23. Gold alignment: his Aug 23-24 walkthrough vs the sim (2026-09-03)

His 3m narration of the Sunday-23 -> Monday-24 GC session, replayed with
his chart levels (his VAH 4,690.0 vs computed 4,689.9 - 0.1pt; his VAL
16pt off but untouched all day): every narrated event maps to the log
with 1-3min candle-label shifts - the 20:09 early cut, the 20:18 short
that ran hours, the 10:45/10:48 fill-to-TP-in-one-candle, the 11:09
fill that ran multi-R, the 1:33 not-full-loss, the 3:48-4:27 scratch
cluster, and the 4:36->5:33 winner via the prior-candle escalation
(ran 12.4R). One disagreement: the 01:51 long he hedged on. Day net at
1R: -2.91R - an honest red day. His two observations confirmed at
scale (GC 3m 2025-26): 23%% of trades scratch at avg -0.46R (not -1),
and 35%% of entries run >=2R / 20%% >=4R before their stop - yet the
target frontier still votes 1R (+98R) over 1.5R (-23) and 2R (-84):
the tail is real and mechanically unharvestable, third combination in
a row. Discretionary runner management stays the agent stack's job.

## 24. NQ x GC correlation + the rotation question (2026-09-03)

Daily correlation between the two certified books: **-0.018** (monthly
-0.053) - not the negative coupling his eye suggested, but zero, which
is the diversification jackpot anyway: 894 shared days, both-green 19%%,
both-red 28%%, split 53%%.

Combined-book receipts (risk-normalized): 50/50 blend +0.73R/day, 63%%
green days, maxDD -7.2R (vs NQ alone -10.8R, GC alone -46.1R) - a third
less drawdown at NQ's Sharpe. Both at full risk each: +1.45R/day, 63%%
green, maxDD -14.3R.

**Day-rotation: KILLED on the fair baseline.** Trailing-5-day P&L
picking today's instrument beats the half-size blend in both halves -
but that was a sizing artifact (picker rides full risk); against
ALWAYS-NQ at full risk it loses in both halves (0.891 vs 1.095 IS,
1.081 vs 1.344 OOS). No daily classifier beats simply owning the
better instrument. Caught pre-ship by the fair-baseline check.

**The real classifier is GC's own vol dial, not rotation:** GC trades
only when its trailing-20-day median 1m candle >= 1.0pt. That keeps GC
on for just 29%% of days yet captures +201R of its +203R total, and
zeroes the 2023-24 bleed. Mechanism-backed (the friction arithmetic of
S22), receipt-shaped as same-money-less-exposure. At 1.5pt the dial is
too tight (-39R).

RULING CANDIDATE: NQ always on; GC on its vol dial; both at full
per-instrument risk. "Which is better today" has a boring answer - NQ,
every day - and a useful one - GC earns its seat only when its tape is
big enough to clear its costs.

## 25. THE GRAMMAR IS GENERAL: four new level families, all pass (2026-09-03)

His push: "built only on 2 levels... surely there must be a way we can
add some mechanical counterparts... maybe ur just not testing the right
mechanisms." He was right - the answer was never filters (subtraction),
it was more level families (addition). Four new families ran the FROZEN
certified spec untouched - PD high/low, PD POC, weekly VAH/VAL, weekly
POC - prereg gates: positive both halves, daily corr <0.5 vs VA, DD.

| family | n | WR | net R | IS/OOS | corr vs VA |
|---|---|---|---|---|---|
| PD VA (certified) | 7,623 | 67.3%% | +1,133 | +515/+618 | - |
| PD HIGH/LOW | 5,647 | 65.5%% | +705 | +320/+384 | +0.06 |
| PD POC | 4,490 | 65.0%% | +549 | +260/+289 | +0.03 |
| WEEKLY VA | 7,091 | 66.9%% | +964 | +409/+555 | +0.31 |
| WEEKLY POC | 3,720 | 66.3%% | +496 | +191/+305 | +0.09 |

ALL FIVE positive in both halves at 65-67%% WR with zero re-tuning and
near-zero cross-correlation. No selection occurred - every family
tested passed. The close-through -> retest grammar prices ANY structural
reference level; PD VAH/VAL was one instance of a general edge.

**The five-book answers his DD complaint:** equal-risk five-stream book
= +0.84R/day, 71%% green days, **maxDD -4.6R**, 45/45 months positive,
worst month +3.0R. DD-efficiency 18.4%% of maxDD earned per day vs
11.5%% for VA alone - any sizing on the dial dominates the single book
(at VA-alone's +1.24R/day rate the five-book carries ~-7R DD vs -10.8).
Full-risk-each: +4.2R/day at -22.8R, ~31 trades/day - automation
territory. GC families and the live wiring are the open ends.

## 26. THE 8-LEVEL BOOK: proximity rule + full picture (2026-09-03)

**His proximity rule, concrete:** at session start, levels within one
stop-floor of each other (5pt NQ) MERGE - the stronger family keeps the
level (priority PD VA > weekly VA > PD H/L > PD POC > weekly POC), the
weaker book skips it that day. Ex-ante, deterministic, no knobs.
It binds 1.32 levels/day (1,204 drops over 915 days) and removes ~700R
of double-counted overlap vs the naive five-book sum.

**Full picture (--levels all, certified cell, honest fills, gated):**
23,102 trades, WR 66.4%%, expectancy +0.137R/trade, 17%% scratches,
**+3,154R total, +3.60R/day at full risk per stream, maxDD -14.6R** -
the drawdown is now four average days deep (vs 8.7 for the single
book). Yearly: 2023 +652R / 2024 +942R / 2025 +951R / 2026 +609R
(R/day rising +2.67 -> +4.38; green days 69-76%%; no yearly maxDD worse
than -14.6R). Frequency: 19 -> 38 trades/day across the era.

**45/45 months positive. Median month +72.4R. WORST MONTH +9.8R.**
The book has never printed a losing month, and its worst month clears
most funded-account monthly targets on its own.

Sizing dial: 1/5 risk per stream = +0.72R/day at maxDD **-2.9R** (73%%
green days); half risk = ~+1.8R/day at ~-7.3R. Every point dominates
the single-stream book. Per-family post-merge: va +1,133R (keeps its
levels by priority), wva +662, pdhl +626, poc +518, wpoc +216.

## 27. Gold 8-level book (2026-09-03)

Same --levels all machinery, gold constants (merge floor 1.5pt).
2023-24: dead as expected (+12/-24R - the friction era; the vol dial
owns this). **2025-26: +307R / +351R, +1.69R/day, 62%% green days,
18/20 months positive (median +25.1R, worst -7.0R), maxDD -16.9R,
30.5 trades/day in 2026.** All five families positive on gold too -
second instrument, same generality.

## 28. VWAP-REVOLVENT (his idea, 2026-09-03): retest passes, market dies

His spec: "candle close through vwap band, market order and target x r.
other thing is enter on retest. try 1, 3 and 5 min." Implemented in
`scripts/vwap_revolve.py`: bands = certified session VWAP +/-1/2 sigma,
MOVING levels frozen at the signal close (limit rests at the frozen
value), same stop waterfall / SAR-across-bands / news gate / honest
fills / EOD conventions. Prereg: judged at depth 3 / 1R; pair-in needs
positive both halves + corr <0.5 vs the 8-level book.

Grid verdict (net R, cost-adj, depth 3):
- **MARKET ENTRY: NEGATIVE at every tf and every target** (tf1 -1,624R
  at 1R). Chasing the close-through pays the displacement; killed.
- **RETEST: positive both halves at all three tfs at 1R**, and the two
  gradients replicate AGAIN (4th/5th independent time): tf1 +3,949R >
  tf3 +1,522 > tf5 +798; 1R > 1.5R > 2R everywhere; depth-0 negative
  everywhere (noise closes at moving bands are worse than at static
  levels).

**VWAP champion (tf1 retest depth3 1R): +3,949R over 34,166 trades,
64.5%% WR, +0.116R/trade, all four years +815 to +1,148R, 45/45 months
positive (median +78.9R, worst +0.1R), +4.29R/day, 75%% green days,
maxDD -17.8R.** Bigger than the entire 8-level book, every band
positive (vwap +923, +/-1 sigma ~+1,000 each, +/-2 thinner).

**Pairing: PASSES ALL GATES.** Daily corr vs the 8-level book +0.104.
Combined NQ book (8 levels + VWAP bands, full risk each): **+7.71R/day,
83%% green days, maxDD -22.7R (3 average days deep), 45/45 months
positive, median month +157.3R, worst month +10.0R.** ~70 trades/day -
automation only.

**Overlap measured (his ask, 2026-09-03):** 8%% of VWAP trades overlap
a level-book position in time; 6%% same direction; **3.7%% (1,261
trades) are true double-risk** (same direction, entries within one
floor). Combined-book concurrency peaks at 2 positions on most days
(635/921), 3 on 98, 4 on 22, never more. The double-risk trades net
**-120R at 57.5%% WR** - so the CROSS-BOOK DEDUPE RULE (skip a VWAP
entry when a level-book position is open same-direction within 5pt) is
free on both axes: removes the double exposure AND adds +120R. RULE IN
for the live spec (implemented in-sim as --dedupe; official champion is
now the deduped book: 33,340 trades, +3,932R). Remaining open: gold
VWAP variant.

**Band-direction asymmetry (his hypothesis, 2026-09-03): REJECTED on
the retest book - and his instinct is vindicated elsewhere.** Prereg:
cut extending-at-outer-band trades if negative both halves. Measured:
ALL TEN band x direction cells positive in BOTH halves; extend_2sig
runs +0.121 EV at 65.6%% WR - indistinguishable from reverting trades -
and his exact example, SHORT at -2 sigma, is the single BEST cell in
the book (67.8%% WR, +0.157 EV, +0.191/+0.135 by half). Weakest cell:
LONG at +2 sigma, still +0.073 and positive both halves. NOTHING
qualifies for a cut.

The mechanism: the RETEST converts the trade he fears into the trade he
loves. Shorting a -2 sigma close-through via retest means waiting for
price to pull back UP to the band and shorting the bounce - a
with-trend pullback entry (the T76 shape), not a chase. The chase
version of his intuition IS real and IS dead: it is exactly the
market-order style, negative at every tf and target (S28). The loser-
cutting he wants is already structural - the limit at the frozen band
is the filter.

## 29. VWAP diagnosis: band x year + loss anatomy round 3 (2026-09-03)

His ask: per-band per-year breakdown and a pre-entry loser-classifier
hunt. Prereg: cut only buckets NEGATIVE both halves, n>=400/half.

Band x year: ALL 20 cells positive (EV +0.057 to +0.179, WR 59-67%%),
every band positive every year - stationary through both regimes.

Nine-feature screen on 33,340 trades: **ZERO cut candidates.** Notable
gradients, all positive-both-halves and therefore not cuttable:
- WINDOW is the big sort: NY +0.173/+0.137 per trade vs ASIA
  +0.027/+0.091 and LONDON +0.056/+0.104. VWAP-band trades earn 2-4x
  more in NY; overnight is thin but real.
- Stop-floor trades weakest again (+0.097/+0.095) - same gradient as
  the level books, still profitable.
- Post-loss entries outperform AGAIN (+0.141/+0.124) - third
  independent book showing prevL > prevW; first-trade-of-day weakest
  (sign flips, tiny n). The grammar warms up with the tape.
- Slope alignment, band width, dow, flip: null. No hour negative both
  halves (overnight hours thin +0.02-0.09, NY hours rich +0.12-0.20).

**Verdict: the WR boost does not exist as a subtraction.** Fifty-plus
cells, nothing negative twice. The honest lever is ALLOCATION: at full
automation take everything; a leaner human-watched variant is NY-only
VWAP (n=17,045, EV ~+0.15/trade), the concentrate. Recorded as an
option, not a rule.

## 30. NY-ANCHORED VWAP (his ask, 2026-09-03): a new independent family

09:30-anchored VWAP (fresh accumulation at the equity open, certified
band math on the sliced frame, 15-min sigma warmup, NY signals only,
--anchor ny, cross-book dedupe on):

**Champion (tf1 retest depth3 1R): 20,183 trades, 66.7%% WR, +0.154
exp/trade, +3,108R, IS/OOS +1,541/+1,567, every year +464 to +930R.**
Per-band uniform (+0.137 to +0.169; +2 sigma the best band here). Even
1.5R holds 52.5%% WR / +0.090 exp on this family - the strongest
1.5R cell in the program - though 1R still dominates.

Head-to-head vs the session-anchored book's NY trades: identical
per-trade quality (+0.154 vs +0.154) but 18%% more trades, and daily
corr between them is just **+0.096** - different anchor, different band
locations, different trades. NOT a replacement: a THIRD near-independent
NQ stream (~+3.4R/day NY hours). Both anchors work; the 09:30 anchor
he does not even chart is additive to the one he does.

Open for the live spec: vwap-vs-vwap cross-anchor dedupe (same rule
shape as S28) and the full-empire joint DD recompute with all dedupes -
executor-stage work.

## 31. THE GUARD RAILS - live-spec risk stack (2026-09-03)

His frame: all streams together is a lot of trades that will overlap;
build the rails. Measured first, designed second.

New receipts: NY-vwap entries duplicating an open session-vwap position
= 5.0%% of that book and net **-78R** (the level-vwap pair was -120R) -
the dedupe principle is now receipt-backed on both measured pairs, and
both times the duplicate entries were net LOSERS. Empire concurrency
(all three NQ books): daily peak is 2 positions on 68%% of days, 3 on
20%%, 4 on 3.7%%, 5 on 0.2%%; same-direction stacks peak at 2 on 74%%
of days, 4 on 0.3%%.

THE STACK (each rule mechanical, most already receipted):
G1  Per-book: max 1 position + 1 working limit; newest own-book signal
    replaces an unfilled pending. (as certified)
G2  18:00 static-level merge: levels within one stop-floor collapse to
    the stronger family (S26 priority order). (as certified)
G3  FIRST-IN WINS, universal: no book opens a same-direction position
    within one stop-floor of ANY open position, across all books.
    (Receipts: +120R and +78R saved on the two measured pairs.)
G4  Pending hygiene: a resting limit is PULLED the moment a same-
    direction position opens within one floor of its price - the
    order-level form of G3, so duplicates die before they fill.
G5  Global concurrency cap: 4 open positions empire-wide (p99.8 of the
    measured distribution; binds ~2 days in 921). Signals at cap are
    skipped.
G6  Same-direction cap: 3 (binds ~0.3%% of days).
G7  Open-risk cap: total open risk <= 4R equivalent - explicit form of
    G5 for when per-stream sizing varies.
G8  News gate 08:00-09:30 on high-impact days; pendings die 16:00;
    flat by session end. (as certified)
G9  Executor health (wiring-stage): 18:00 level sanity check vs price;
    stale-feed rule (no bar for 2min -> pull pendings, manage-only);
    order-reject or fill-mismatch -> halt new entries, alert; daily
    position reconcile against the broker.
G10 Instrument dials: GC trades only with its vol dial on (S24);
    NQ undialed.

His closing arithmetic, confirmed: ~+0.10-0.15R expectancy is the whole
business model - it only needs to be real and repeatable at 40-70
pulls/day, and three books x four years say it is.

## 32. THE RAILED EMPIRE - closing statement (2026-09-03)

All three NQ books under the G-stack (post-hoc chronological rail pass;
exact joint sim is executor-stage). G3 removed 2,009 duplicate entries;
the G5/G6 caps never once bound - they are pure insurance.

**74,616 trades / 81.0 per day / WR 65.6%% / expectancy +0.1347R /
+10,052R total / +10.91R per day / 89%% green days / worst day -19.8R
/ maxDD -19.8R (the deepest drawdown in four years is one single day)
/ 45 of 45 months positive / median month +213R / worst month +8.1R /
best +381R.** Monthly WR pinned at 63-70%% for 45 straight months.
Yearly: 2023 +2,181R / 2024 +2,820R / 2025 +2,972R / 2026 +2,079R
(through Sep 1), R/day rising +8.45 -> +14.14 with frequency.

Scaling dial: x0.50 = +5.46R/day at -9.9R maxDD; x0.33 = +3.64R/day at
-6.6R. Standing caveats unchanged: winner's-curse shaving on swept
cells, sim-vs-live gap, 81 trades/day is automation-only, and the
whole edifice awaits Pat's seven gates and the paper-trading bridge.

## 33. OVERFIT AUDIT: PBO + DEFLATED SHARPE + MONTE CARLO (2026-09-03)

His ask: "lets run a PBO test, deflated sharpe, etc. also a monte carlo
sim... i heavily suspect we have not overfitted shit but better safe
than sorry." Receipt: `scripts/validation_pbo_dsr.py` (reruns both
tests end to end from the trade dumps).

**PBO via CSCV (Bailey et al.)** — the informative test. Take the full
20-cell selection grid the tf1 champion came from (4 depths x 5
targets, daily P&L per cell, 796 days), split into S=16 blocks, and for
every one of the C(16,8) = 12,870 IS/OOS partitions ask: does the
config that looks best in-sample fall below the median out-of-sample?
**PBO = 0.000.** Not one split of 12,870. The champion cell (depth 3 /
1R) holds OOS relative rank 0.95 — median AND minimum. A strategy
family picked by overfitting scores PBO near 0.5; <0.1 is the
"excellent" bar. This is what "the ridge is monotone, the cell choice
barely matters" looks like in the formal test.

**Deflated Sharpe (Bailey & Lopez de Prado)** on the railed empire
daily series (§32 rail pass, cost overlay in): T=921 days, SR_daily
1.156 (~18.3 annualized), skew +0.39, kurt 3.3. DSR = 1.000000 for any
trial count up to 10,000 — the expected-max-SR haircut for even 10k
searched configs is 0.09, noise against 1.16. Flag kept attached: a
sim-level Sharpe this size mostly reflects the sim's idealizations
(limit-fill grammar, no cost shocks, no missed sessions); DSR here says
"not a selection fluke," not "expect 18 live." PBO carries the weight.

**Monte Carlo funded-account simulator** — interactive artifact:
https://claude.ai/code/artifact/8e20fbfe-4728-4120-9c8f-9de246ea9729
Bootstraps the 921-day empire R series (5-day blocks by default, iid
optional, seeded) through a Lucid-style account: EOD-trailing drawdown
(his frame: "drawdown is EOD"), floor lock at start balance, profit
target, min days, then a funded phase to first payout. Knobs: max DD $,
target $, $/R, payout figure, min funded days, sim count, and an
edge-haircut slider (removes X% of the mean, keeps the volatility —
the "live won't fill like the sim" dial, default 30%). Outputs: pass /
breach / timeout rates, days-to-pass distribution, equity fan vs
target and floor lines, start-to-first-payout odds and days. The daily
array regenerates via the validation script
(`output/analysis/empire_daily.npy`).

## STATUS (2026-09-03): ACCEPTED AND FROZEN

His verdict: "fully mechanical system, performs like this... we have a
65-70%% win rate high frequency strategy." The spec is frozen as
certified (S19): 1m close >=3pt through PD VAH/VAL, limit retest,
structural stop (5pt floor), 1R full exit, SAR flip, all sessions,
news gate 08:00-09:30, sized per R. Every proposed modification was
tested; the survivors are in, the kills are logged (S15, S16, S20,
S21).

Open threads, in his order:
1. GOLD PORT - DONE (S22-S27): constants re-derived from GC's own tape,
   gold-native sweep confirmed the ratios, walkthrough certified
   (S23), vol dial G10 keeps +201R of +203R on 29% of days.
2. Overfit audit - DONE (S33): PBO 0.000 across 12,870 CSCV splits,
   DSR 1.0, Monte Carlo funded-account artifact live.
3. Pat seven-gate treatment of the certified specs.
4. Executor-stage exact joint sim of the railed empire (S32 rail pass
   is post-hoc chronological), then paper days on the Mac against
   real-time TradingView.
