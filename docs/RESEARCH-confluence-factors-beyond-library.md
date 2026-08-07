# RESEARCH — confluence factors beyond the current library

**2026-08-07. Research report. No trial charged, no candidate proposed, no claim about
this desk's setups.** The desk holds 28 hand-logged trades and no backtest run, so nothing
below is or can be evidence about which of our setups win more. Every effect size quoted
is a *source's* claim about *their* data, reproduced so it can later be tested, not
believed.

Already in the library and therefore out of scope: VWAP, Bollinger Bands, volume profile,
session levels, prior-day levels, MA stacks, volume behaviour, time-of-day windows,
higher-timeframe alignment, and the ICT set (liquidity sweeps, FVGs, SMT divergence).

---

## 0. The data constraint, applied first

Available: **1-minute NQ bars** plus **MBP-10 order-book snapshots**. Everything below is
triaged against that before its merits are discussed, using the
`orderflow-construction` taxonomy:

- **VALID** — computable from held data without bias.
- **BIASED** — computable, but measures something other than its name.
- **NOT CONSTRUCTIBLE** — requires data we do not hold.

**A caution learned on this desk's own depth archive and worth carrying into any new
factor:** an MBP-10 "snapshot" is not automatically an instantaneous read. Our London
archive retains one row per minute out of a median 23,654 book events, and its `ts_event`
is floored to the minute — the row labelled T is the book at ~T+59.9s
(`docs/FINDING-london-depth-timestamp-lookahead.md`). Any factor below that reads the book
inherits both problems. Assume the same of any new depth pull until a second clock proves
otherwise.

### Triage summary

| factor | class | blocker |
|---|---|---|
| Gap classification | **VALID** | — |
| Day-type classification | **VALID** | — |
| Initial balance & extension | **VALID** | — |
| Overnight inventory | **VALID** | — |
| Economic-calendar filter | **VALID** | needs a calendar file (static, cheap) |
| Depth imbalance / book pressure / microprice | **VALID** | instantaneous reads only |
| Cumulative delta / CVD | **NOT CONSTRUCTIBLE** from bars+MBP-10 | needs aggressor-tagged trades |
| Order-flow imbalance (OFI) | **BIASED** at snapshot resolution | needs event-level MBP-10 |
| ES/NQ divergence | **NOT CONSTRUCTIBLE** | needs an ES 1-min feed |
| NYSE TICK | **NOT CONSTRUCTIBLE** | separate breadth feed |
| Advance/Decline (ADD) | **NOT CONSTRUCTIBLE** | separate breadth feed |
| VIX / VIX3M term structure | **NOT CONSTRUCTIBLE** | separate index feed |
| Open interest | **NOT CONSTRUCTIBLE intraday** | CME publishes T+1 |

---

# PART A — factors constructible from held data

## A1. Gap classification

**What it measures.** The relationship between today's open and the prior session's
close/range, treated as a regime label rather than a signal.

**Mechanical freeze.** Practitioner convention splits gaps four ways — common, breakaway,
runaway/continuation, exhaustion — with the discriminators being location relative to a
consolidation range, and volume. Common gaps form inside a trading range on low relative
volume; breakaway gaps escape a consolidation on high volume. A workable mechanisation
that needs no news feed: `gap_pts = open − prior_close`; `gap_atr = gap_pts / ATR(14, daily)`;
`inside_prior_range = prior_low ≤ open ≤ prior_high`. Tier by `|gap_atr|` quantile computed
on an **expanding** window (see failure modes).

**Paired with, and claimed effect.** Two directly opposed families are both documented and
both popular: gap **fill/fade**, which exploits the tendency of weak gaps to return to the
prior close, and **gap-and-go** continuation, which trades the gap's direction. Sources
report SPY gap fills at **59% for gap-ups and 69% for gap-downs** over a six-month sample,
attributing the asymmetry to equity drift; other sources put common-gap fill at **70–75%
within 5 sessions** and breakaway-gap fill at **under 30% within a month**.

**Disagreement to record, not adjudicate.** The fade and continuation camps use the same
raw event and claim opposite edges. Neither is refuted by the other in the sources — they
differ on the *conditioning* (gap size, volume, prior structure). Any test must therefore
specify which conditioning it is testing, or it is testing neither.

**Failure modes.** (i) Fill rates are quoted on SPY/equities and on multi-month windows;
NQ futures gap definitions differ because the overnight session trades. Decide explicitly
whether "gap" means RTH-open vs prior RTH-close, or something spanning Globex. (ii) Any
quantile tiering computed over the whole sample is the era-local-quantile defect this desk
has already hit once (`LDN-INV-01`) — a January day cut by a boundary that includes
December is not tradeable. Expanding window or an absolute threshold declared in advance.
(iii) Fill statistics are unconditional; conditioning on gap size changes them and the
sources rarely publish the conditioned table.

## A2. Day-type classification (Market Profile)

**What it measures.** Whether the session is *balancing* (rotational, two-sided) or
*trending* (one-timeframe, directional) — a regime label that plausibly determines which
setup family should be active at all.

**Mechanical freeze.** Dalton's taxonomy is Normal, Normal Variation, Trend, Double
Distribution Trend, Neutral and Nontrend. The mechanisable discriminators:
- **Trend day** — narrow IB, obvious one-timeframing (each period's extreme extends the
  prior in one direction), minimal horizontal development.
- **Normal day** — wide IB that holds all session.
- **Normal Variation** — starts as Normal, then extends beyond the IB on one side.
- **Neutral day** — range extension on **both** sides of IB, close typically **inside** IB.
- **Nontrend** — narrow IB that holds; low volume, D-shaped profile.

**Frequency claim from sources.** Neutral days at **30.21%**. Note this is one source's
count on an unstated instrument and sample; treat as a prior for feasibility only.

**Paired with, and claimed effect.** Mean-reversion and rotation setups are claimed to work
on Normal/Neutral days and to fail on Trend days; breakout/continuation setups the reverse.
This is the single most commonly asserted regime filter in the profile literature.

**The causality problem, which is the real issue.** *Day type is a
close-of-session classification.* "Trend day" is only knowable once one-timeframing has
persisted. Using it as an entry filter at 10:15 requires a **partial, causal** variant —
e.g. classify on IB width + extension state as of the decision minute — and that variant is
a different feature with different statistics from the one the books describe. Under this
desk's §2.5 window-causality bar the full-session label fails outright: its window closes
at the session close, and the decision time is earlier.

**Failure modes.** (i) The lookahead above, which is fatal if not respecified. (ii) The
taxonomy was developed on pit-session CBOT/CME products; the 23-hour Globex session makes
"the open" and "the IB" definitional choices rather than givens. (iii) Classifications are
discretionary in the source material — different practitioners label the same day
differently, so any mechanisation is *a* mechanisation, not *the* one.

## A3. Initial balance and IB extension

**What it measures.** The first hour's range as a proxy for the session's accepted value,
and breakouts from it as evidence of other-timeframe participation.

**Mechanical freeze.** IB = high−low of the first 60 minutes of RTH (09:30–10:30 ET for US
index futures). Extension measured as a multiple of IB range: 1×, 1.5×, 2×, 3× beyond the
IB high/low.

**Claimed statistics.** On the largest sample located: across **2,686 ES sessions only
2.2%** stayed entirely inside IB; NQ **3.8%** across 2,833 sessions. Both-direction
breakout ("rotation day") **28.7% ES / 22.6% NQ**; single-direction breakout **~69% ES /
~74% NQ**. A separate source claims an IB-breakout win rate of **76.8% on YM**, rising to
**87.5% on Thursdays**.

**Disagreement, recorded.** The 76.8%/87.5% figures come from a vendor blog with no stated
sample size, cost model or exit rule, and a day-of-week effect of that size on a single
instrument is exactly the shape of a data-mined artifact — this desk has already killed
weekday effects once for era-flipping. The ES/NQ session-count statistics are internally
consistent and sample-sized; the win-rate claims are not. Record both; believe neither
without testing.

**Useful structural note.** Sources converge that **IB size is the strongest predictor of
breakout behaviour** — narrow IB implies stored energy — which makes IB width a
*conditioner* rather than IB breakout a *signal*.

**Failure modes.** (i) "Only 2.2% stay inside IB" makes raw IB breakout nearly
unconditional and therefore nearly information-free; the edge, if any, is in the
conditioning. (ii) IB is RTH-defined; for a desk trading other sessions the analogue must be
declared, not assumed. (iii) Extension multiples are unbounded targets — an extension
statistic without a stop model is not a P&L statement.

## A4. Overnight inventory

**What it measures.** Whether the overnight session has left participants net long or short
relative to the prior settlement, creating a correction risk at the RTH open.

**Mechanical freeze.** Dalton's definition is explicitly mechanical and is the cleanest in
this report: **measure against the prior pit-session close. If overnight price traded
mostly above it, inventory is net long; mostly below, net short.** A percentage form is in
common use ("95+ long", "100% short") — the fraction of overnight minutes (or volume)
trading above the prior settlement.

**Paired with, and claimed effect.** The claim is that extreme inventory (near 100% one
way) favours a **counter-auction** early in the RTH session — a long-liquidation break or
short-covering rally — as inventory rebalances. Pairs naturally with open-drive fades and
first-hour reversal setups.

**Why this one is attractive here.** It is fully derivable from 1-minute bars, it is
**settled before the RTH open** so it passes window causality with room to spare, and it is
a *day-level* conditioner, which means one observation per session and no overlapping-sample
inflation.

**Failure modes.** (i) "Prior pit-session close" needs a definition on a 23-hour product —
settlement vs 16:00 ET vs 17:00 ET are different anchors and give different labels. (ii) The
percentage is a smooth variable being used as a categorical; the threshold ("extreme")
is a free parameter and must be declared, not searched. (iii) The concept is discretionary
in its source material and is usually combined with profile context; isolating it may test
something the practitioners never claimed.

## A5. Economic-calendar filter

**What it measures.** Scheduled macro releases as a volatility-regime and stand-aside
condition.

**Mechanical freeze.** A release calendar (FOMC / CPI / NFP at minimum), tiered, plus a
window: e.g. no new entries in [T−30min, T+30min] around a Tier-1 release, or a size
reduction rather than a veto.

**Claimed effects, with the academic sources being unusually good here.** The **pre-FOMC
announcement drift** — significant positive equity returns in the ~24h before scheduled
FOMC announcements — is documented in a Federal Reserve Bank of New York staff report
(Lucca & Moench) and remains significantly positive when restricted to announcements
followed by a press conference. Pre-announcement drift is also reported for **NFP and CPI**.
Explanations divide: one strand attributes it to **information leakage** and preferential
access; the NBER "Solving the FOMC Puzzle" line argues otherwise. **Record the
disagreement — the effect is better evidenced than its cause.**

On intraday volatility, CME data is cited for **2–4× baseline volatility in the 30 minutes
around NFP**, with the first 5 minutes least predictable, and volatility *compressing* in
the hours before a release then expanding at the announcement.

**Failure modes.** (i) Release calendars are revised; a calendar assembled after the fact
can contain corrected timestamps that were not knowable live. Version and freeze the
calendar file. (ii) The pre-announcement drift literature is on *equity index returns over
hours*, not on intraday futures setups — transferring it is an assumption. (iii) A
stand-aside rule cannot be evaluated on P&L alone: it removes trades, so it will almost
always reduce gross profit and may still be correct on risk grounds.

## A6. Instantaneous book features — depth imbalance, book pressure, microprice

**What they measure.** The resting-liquidity state at one instant: how lopsided the book
is, how that mass is distributed by distance, and where the size-weighted price sits
relative to the mid.

**Mechanical freeze.**
- Depth imbalance: `(Q_bid − Q_ask)/(Q_bid + Q_ask)` over the first *k* levels, in [−1,1].
- Book pressure: distance-weighted depth, `Σ Q_i / dist_i^α`.
- Weighted mid: `(Q_ask·P_bid + Q_bid·P_ask)/(Q_ask+Q_bid)` — note the **cross**
  weighting; a large bid pulls the price toward the ask, because size is what must be
  consumed before price travels that way. Weighting each price by its own size is a
  classic inversion and is invisible to R².
- Microprice (Stoikov 2018) adds a martingale correction `G(imbalance, spread)` which must
  be **fitted** — and fitted on an expanding window, or it is the era-local-quantile defect
  again.

**Class: VALID.** These are pure functions of the book at an instant, which is the class
that survives coarse sampling.

**This desk has already measured them, and the result belongs here.** On 34,800 minutes
across 290 London sessions
(`docs/FINDING-book-state-has-no-forward-content-at-1min.md`): tape delta clears its
contemporaneous check at **r = +0.6029** (the positive control, proving the harness can see
a real relationship), while **every book-state feature sits inside the shuffle null on the
forward probe** and is **residual-dominant on the time-shifted placebo** — `imb_L10` scores
−0.164 against the minute it sits at the end of and −0.007 against the next. Nothing clears
at any ladder depth, in either era.

**That is a measurement on this desk's own London window, not a general law**, and it says
these features are honest columns carrying mostly memory at 1-minute resolution. A new
candidate proposing them should either use a different resolution or explain why its window
differs.

**Failure modes.** (i) **The post-trade residual** — the book at T is what aggressive flow
*left behind*, and depth replenishes fast (Large 2007: ~20s half-life where replenishment
occurs), so joining a snapshot to a *past* or *containing* window produces a strong,
meaningless relationship. (ii) **At-fill reads** — a book read at the moment a limit order
fills contains the answer, because a fill requires price to have travelled to the order.
Anchor at the decision. (iii) NQ's book is thin — median ~3 contracts a level, ten levels
spanning ~2.25 points — so level-1 imbalance has a tiny denominator, and raw contract
counts load on the activity regime rather than on imbalance. Normalise, then check the
normalisation has not induced a volatility correlation.

---

# PART B — factors that are BIASED or NOT CONSTRUCTIBLE

Recorded explicitly rather than dropped, with what each would need.

## B1. Order-flow imbalance (OFI) — **BIASED**, not merely noisy

**What it measures.** Cont, Kukanov & Stoikov (2014) define OFI as a sum of per-event
contributions from *successive* best-quote changes.

**Why it is biased at snapshot resolution.** CKS's own identity is that **a market sell and
a cancelled buy of the same size are equivalent to OFI** — identical effect on the bid
queue. Differencing two snapshots recovers only the *net* change across everything in
between, so it (a) understates gross flow, (b) conflates cancellation with execution, and
(c) **can carry the opposite sign** to true integrated OFI. A sign flip leaves R² unchanged,
so nothing downstream catches it.

On this desk's archive the interval spans a **median 23,654 book events**. CKS operate at
10-second resolution; FX order-book work at 0.1s notes reconstruction is sound there only
because "in most cases nothing happens within a time-slice", which fails completely at 60s.

**What would move it to VALID.** Event-level MBP-10 — the same schema, unsampled. A
purchase, not a code change. The delivery acceptance test is `ts_recv − ts_event` in
**microseconds, not ~60 seconds**.

**Note for the agents:** the desk already carries `src/engine/book.ofi_proxy`, which
refuses to run without an explicit `i_know_this_is_biased=True` flag and returns a column
named `ofi_PROXY`. Do not route around it.

## B2. Cumulative delta / CVD — **NOT CONSTRUCTIBLE from bars + MBP-10**

**What it measures.** The running sum of signed (aggressor-tagged) trade volume — a
scoreboard of net aggression. Delta divergence: price makes a new high while delta flattens
or turns, read as thinning aggressive flow.

**Why not constructible from the stated data.** It requires **aggressor-tagged trades**.
MBP-10 book snapshots contain no trades. Inferring the aggressor from the tick rule is the
alternative and it is poor: classic studies put tick-rule accuracy at 72–85%, and
Panayides et al. report a fall from 79–92% (2007–08) to **39–65% (2017)**. Inference error
propagates — Andersen & Bondarenko found VPIN predicts volatility *solely* because
volatility induces classification errors in the bulk-volume procedure.

**What it needs.** Aggressor-tagged trades (CME MDP 3.0 tag 5797; Databento's `side`).
Usually far cheaper than book data. **This desk already holds such a tape for part of its
span** (`data/reference/cvd/`), where the convention is `B` = buyer-aggressor and signed
delta is **B − A**, settled empirically at r = +0.7293 over 287 sessions. Two consumers had
it inverted. Use `src.engine.footprint.signed_delta`; do not hand-roll the subtraction.

**Related, and also not constructible:** absorption and iceberg detection at a price level
need per-price-per-side footprint; **VPIN** needs equal-*volume* buckets over the trade
sequence, which snapshots cannot form; sweep/ordered-multi-level-consumption needs the
event stream; queue position, order lifetimes and cancel-vs-execution attribution need
**MBO/L3 with order IDs** and stay out of reach at *any* MBP-10 sampling rate.

## B3. ES/NQ divergence — **NOT CONSTRUCTIBLE without an ES feed**

**What it measures.** One index future making a higher high while a correlated one fails to
confirm — the SMT-divergence idea generalised to correlated-market confirmation, and
separately the **NQ/ES ratio** as a real-time tech-vs-broad-market rotation measure.

**Mechanical freeze.** On a chosen swing lookback, flag bearish divergence when ES prints a
higher high and NQ a lower high (and the mirror for bullish). Sources place it on 5-minute
to 1-hour intraday charts.

**Blocker.** Requires synchronised ES 1-minute bars. Not in the stated data — but this is
the **cheapest gap on the list to close**, since ES bars come from the same vendor and
venue as the NQ bars already held, with no new schema.

**Failure modes.** (i) The desk's library already contains SMT divergence; this is
adjacent, so redundancy against the existing vocabulary must be measured, not assumed.
(ii) Divergence detection is swing-definition-dependent, and swing definitions are usually
confirmed retrospectively — a live-realisable swing rule is a different object from a
charted one. (iii) The "institutional manipulation" causal story in the practitioner
sources is an interpretation, not a measurement; the divergence event can be tested without
adopting it.

## B4. NYSE TICK — **NOT CONSTRUCTIBLE**

**What it measures.** The net count of NYSE stocks last trading on an uptick vs downtick —
breadth of instantaneous participation.

**Mechanical freeze (recorded for a future purchase decision).** Readings beyond **±1000**
are treated as extreme institutional participation. A specific and unusually well-specified
mechanical rule found in the sources: **five or more extreme readings in one direction with
zero in the other during the first hour identifies a trend day, claimed at 82% accuracy.**
Also: fade extremes; and a price/TICK divergence rule — a new price high *with* a
simultaneous new TICK high may mark the day's high, whereas a TICK high *without* a
simultaneous price high suggests continuation.

**Blocker.** A separate NYSE breadth feed. Not derivable from NQ bars or MBP-10 at any
resolution.

**Failure modes.** (i) The 82% figure has no published sample size or out-of-sample split
in the located source. (ii) TICK is an *NYSE* breadth measure being applied to a
*Nasdaq-100* future — the constituent mismatch is a real objection and the sources do not
address it. (iii) TICK's distribution has shifted with market structure (ETF and basket
trading), so thresholds calibrated in one era may not transfer.

## B5. Advance/Decline (ADD) — **NOT CONSTRUCTIBLE**

Same class and same blocker as TICK: a breadth feed. Slower-moving than TICK and usually
used as a trend-day confirmation rather than a fade trigger. Recorded so that a future
market-internals purchase can be scoped as one decision covering TICK and ADD together.

## B6. VIX / VIX3M term structure — **NOT CONSTRUCTIBLE**

**What it measures.** The volatility curve. `VIX/VIX3M < 1` is contango (calm, the normal
state ~80% of the time); `> 1` is backwardation (acute stress).

**Mechanical freeze.** The **VIX/VIX3M ratio** is the standard pairing; sources
specifically warn that **VIX/VIX9D is too noisy for regime detection**. One source reports
VIX closing above VIX3M on roughly **8% of trading days** across a 16-year sample — the
rarity being what makes it informative.

**Blocker.** A separate index feed. Cheap and widely available, but not held.

**Failure modes.** (i) VIX is an S&P-500 volatility measure applied to a Nasdaq-100
product. (ii) 8% of days means a regime flag that fires rarely — any conditioned sample
will be small, and this compounds with the sample-size problem in the protocol document.
(iii) Term structure is a *daily* signal; using it intraday means holding yesterday's value
or accepting an intraday index feed.

## B7. Open interest — **NOT CONSTRUCTIBLE INTRADAY**

**What it measures.** Total open contracts; rising OI with rising price is read as new
money committing, falling OI as position closing.

**The hard blocker, and it is a timing one.** CME publishes a **preliminary** volume and OI
report at end of day, updating at approximately **00:00 CT the following business day**,
with the **final** Daily Bulletin at **10:00 CT the next business day**. All preliminary
values except OI are final for that trade date — **open interest specifically is the field
that gets revised**.

**Consequence for us.** OI cannot be an intraday confluence at all. It can only ever be a
**prior-day, T+1 conditioner**, and any backtest using same-day OI is using a number that
did not exist at decision time. Worse, a backtest using the *final* figure is using a
number that did not exist until the following morning — a subtle 34-hour lookahead that
looks like a clean daily join.

**Failure modes.** Beyond the above: OI is contract-specific, so the roll produces
mechanical OI collapse and rebuild that is not a market signal.

---

## Cross-cutting failure modes — these apply to every factor above

1. **Circularity is robust.** A lookahead survives drop-top-3, every trim depth and every
   winsorisation, and emerges large, stable and significant. This desk's LDN-SWP-01 leaky
   primary came back p<0.001 in both eras and passed every robustness check run.
   Fragility testing cannot substitute for a causality audit.
2. **The clock is a claim.** Every timestamped source needs a second clock at load time.
   Our own depth archive looked immaculate — every stamp exactly on the minute — and was
   60 seconds early. A careful audit reached the wrong conclusion about it once already.
3. **Era-local normalisation is a lookahead.** Any quantile, median or z-score computed
   over the whole sample and then applied within it is the LDN-INV-01 defect.
4. **Overlapping observations inflate n.** Day-level factors (gap, day type, IB, overnight
   inventory, VIX regime) give **one observation per session** regardless of how many
   trades are taken that day. Counting trades as independent draws overstates the sample,
   sometimes by a large factor.
5. **Redundancy with the existing library.** Several factors here are near-relatives of
   things already in the vocabulary — IB extremes vs session levels, day type vs
   higher-timeframe alignment, ES/NQ divergence vs SMT. Correlation against the existing
   inputs must be measured before a factor is treated as new information.
6. **Vendor and blog sources rarely publish cost models.** A win rate without a fill model
   and a cost stack is not a tradeable claim. A published falsification study on MNQ found
   zero naive OHLCV signals surviving honest friction.

---

## Sources

- [TradersMastermind — Short Term Trading Strategies Using The TICK Index](https://tradersmastermind.com/short-term-trading-strategies-using-the-tick-index/)
- [tosindicators — 2 Ways To Use NYSE $TICK To Spot Trend Days](https://tosindicators.com/research/nyse-tick-spot-trend-days-thinkorswim)
- [See It Market — How To Fade The NYSE Tick When Trading E-Mini S&P 500](https://www.seeitmarket.com/fade-nyse-tick-trading-e-mini-sp-500-16154/)
- [WindoTrader — Market Profile Glossary](https://www.windotrader.com/market-profile/market-profile-glossary-index/)
- [Vtrender — Day Types in Market Profile](https://vtrender.com/blog/day-types-in-market-profile)
- [FTMO — Market Profile: Types of Opens and the Anatomy of a Trading Day](https://ftmo.com/en/blog/market-profile-types-of-opens-and-the-anatomy-of-a-trading-day/)
- [Jim Dalton Trading — Overnight Inventory](https://jimdaltontrading.com/glossary/overnight-inventory/)
- [ShadowTrader — Overnight Inventory glossary](https://www.shadowtrader.net/glossary/overnight-inventory/)
- [tradingstats.net — Initial Balance Breakout Statistics: ES & NQ Futures 2015–2025](https://tradingstats.net/initial-balance-breakout-statistics/)
- [Noesis Analytics — Initial Balance Trading](https://noesisanalytics.io/blog/initial-balance-trading)
- [Trade That Swing — SPY/ES Gap Fill Strategy and Statistics](https://tradethatswing.com/sp-500-spy-es-gap-fill-strategy-and-statistics/)
- [SnappChart — Types of Gaps in Trading & Whether They Fill](https://www.snappchart.app/blog/pattern-library/types-of-gaps)
- [QuantifiedStrategies — Gap Fill Trading Strategies](https://www.quantifiedstrategies.com/gap-fill-trading-strategies/)
- [Federal Reserve Bank of New York — The Pre-FOMC Announcement Drift (Lucca & Moench)](https://www.bostonfed.org/-/media/Documents/conference/PDF/Lucca_preFOMCDrift.pdf)
- [Taylor & Francis — The pre-FOMC announcement drift: short-lived or long-lasting?](https://www.tandfonline.com/doi/full/10.1080/00036846.2024.2322573)
- [NBER — Solving the FOMC Puzzle](https://www.nber.org/system/files/working_papers/w25817/revisions/w25817.rev2.pdf)
- [Tradevea — Economic Calendar Trading: NFP, CPI & FOMC](https://tradevea.com/economic-calendar-trading-nfp-cpi-fomc/)
- [Bookmap — NQ vs ES: Why They Move Together, Until They Don't](https://bookmap.com/blog/nq-vs-es-why-they-move-together-until-they-dont)
- [SPXY Trader — NQ vs ES Futures: How Nasdaq and S&P 500 Futures Diverge](https://spxytrader.com/content/intro/nq-vs-es-futures)
- [Bookmap — Cumulative Volume Delta Trading Strategy](https://bookmap.com/blog/how-cumulative-volume-delta-transform-your-trading-strategy)
- [OrderFlow Labs — Footprint Charts Explained: Reading Delta, Bid/Ask, and Absorption](https://orderflowlabs.com/blogs/theblog/footprint-chart-guide)
- [thetrading.tools — VIX Term Structure tracker](https://www.thetrading.tools/vix-term-structure)
- [VolRadar — VIX Term Structure Explained: Contango vs Backwardation](https://volradar.com/learn/term-structure)
- [CME Group — Volume & Open Interest Reports](https://www.cmegroup.com/market-data/volume-open-interest.html)
- [CME Group Client Systems Wiki — Volume and Open Interest](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457092154)

---

## Provisional claims

Every claim in this report that could not be sourced — or that is sourced only to material
publishing no method, or that sits on a disagreement between sources — is enumerated in
**`docs/PROTOCOL-conviction-and-loss-autopsy.md` §6**, together with the same list for the
protocol. It is held in one place so it is read once rather than skimmed twice. Entries
§6.1(1)–(11) and §6.2(12)–(15) cover this document.
