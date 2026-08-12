---
name: tomtrades-model
description: >-
  Quote-grounded reconstruction of the tomtrades (@itstomtrades / @TomTradesJournal)
  "CBR" candle-behaviour-reversal method — a minute-of-hour-timed, counter-trend
  reversal against an hourly overextension, traded mainly on XAUUSD in the Asian
  session. Contains his vocabulary, every rule with its citation status, a sweepable
  parameter for every ambiguity he left, the known contradictions, and hard evidence
  limits. Consult this skill whenever working on the tomtrades detector, backtest, or
  ablations; anything involving CBR / candle behaviour reversal, Type 3 shifts,
  minute-of-hour reversal timing, hourly overextension fades, or DXY/Yen correlation
  gating; or whenever the user mentions "tomtrades", "Tom's strategy", or "the
  reversal model", even in passing. This encodes an UNVALIDATED hypothesis catalogue,
  not a measured edge.
---

# tomtrades-model — CBR (Candle Behaviour Reversal)

## EVIDENCE LIMITS — READ THIS FIRST

**Nothing in this skill is validated. No edge has been measured. This is a faithful
record of what one trader SAYS he does, structured so it can be falsified.** A future
session must not mistake any of it for a working strategy. Specifically:

1. **Coverage is partial (evidence version: audit v1.1).** @TomTradesJournal is
   18/18 videos (~5h) — complete. The main channel is **13/53** and the 8h30m course
   is **0/13 segments** — both still substantially UNREAD, halted by the Gemini
   free-tier cap of 20 requests/day/model. Most quotes trace to the journal channel.
   Do not describe coverage as complete.
2. **A model watched the videos; no human did.** Extraction was Gemini-mediated under
   free-tier quota, with model rotation per video. Quotes may be misheard — numbers
   especially ("22 to 52 minutes", "15-20 pips"). Spot-check any figure before it
   becomes a load-bearing parameter. Chart-read (non-spoken) detail is the softest
   evidence class.
3. **Provenance is now attached.** All 31 quoted rows in `references/citations.md`
   carry their source video ID and timestamp, matched back against
   `docs/CORPUS-tomtrades-extractions.md`. Rows still reading "asserted in audit" are
   class B and remain unupgraded. Re-derive anything load-bearing before use.
4. **His statistics are marketing claims.** "81% WR", "88% WR", "85% WR entry model",
   "75%" at the 30-minute mark, and all P&L figures are self-reported, on thumbnails
   engineered for clicks. A channel is a selected sample by construction (2 of 18
   journal videos are losses). Treat every number as unverified until this repo's own
   backtest says otherwise.
5. **A backtest cannot reproduce his results even if the edge is real.** He claims to
   skip 30-40% of his own setups discretionarily; a backtest takes every signal.
   Divergence from his claimed win rates is an expected finding to quantify, never a
   problem to tune away.

**Upstream source of record:** `docs/RESEARCH-tomtrades-audit.md`, with backing
evidence in `docs/CORPUS-tomtrades-extractions.md`. If that
document is re-issued with fuller coverage, this skill must be regenerated and its
evidence version bumped — do not patch it piecemeal against a moved source.

## What this skill is for

Use it to (a) speak his language correctly when reading or writing anything about this
method, (b) pull the rule set with citation status before writing detector code,
(c) get the sweepable parameterisation of every ambiguity instead of inventing a
number, and (d) keep the contradictions and evidence gaps in front of whoever is
working. The binding discipline, inherited from the pipeline that produced this skill:
**never invent precision the source did not state; a rule you cannot cite is a rule
you delete; use his words for his concepts.**

## Vocabulary — his terms, used his way

- **CBR / CBRA — "Candle Behaviour Reversal"**: his name for the whole method.
  *"CBR is called a candle behaviour reversal"*.
- **The container idea**: *"An hourly candle is 60 minutes of 1-minute market
  structure"* — position WITHIN the hour is itself a signal.
- **Overextension**: an hourly candle immediately driving one way on volume, without a
  meaningful pullback, beyond structure. Never defined numerically (see gaps).
- **AOI — area of interest**: a 1H/4H/daily level the overextension pushes into.
  Construction never mechanically specified.
- **Shift (Type 3 shift)**: his trigger — a sweep-then-break: price takes out a high
  and then breaks the low (or the mirror). A **W-shape swing break**.
- **Change of character**: a **V-shape minor break**. He does NOT take it:
  *"it wouldn't technically be a shift, it would be more of a change of character."*
  His stated tell for the invalid pattern: it forces an oversized stop.
- **Shift within a shift**: nested shift on a finer timeframe — his higher-confidence
  variant.
- **Candle flip**: 30m/15m confirmation referenced in his timeframe stack. Mechanism
  never defined in extracted material — thinnest concept in the corpus.
- **Gold Spread**: an instrument he watches alongside DXY for Gold. Its exact identity
  is unresolved — identify it before coding; do not guess a ticker.
- **Pendulum / elastic band**: his mean-reversion framing. *"Price is a push and a
  pull, it's like a pendulum..."*; *"think of price like an elastic band: the more you
  stretch it, the more likely you'll have a snap back."*

Do not relabel these with ICT/SMC vocabulary he did not use (no "liquidity sweep",
"CHoCH", "FVG"). "Change of character" is fine — that phrase is his.

## The trade, as he states it

One repeating trade: a counter-trend reversal against a short-term overextension,
timed to the clock. Not trend-following. Rule IDs key into
`references/citations.md` and `references/confluence-table.md`.

1. **[C1] Context**: middle-timeframe rangey condition over roughly the prior 5-12+
   hours.
2. **[C2] Overextension**: the hourly candle opens and immediately drives one way on
   volume, no meaningful pullback, pushing beyond structure into a 1H/4H/daily AOI
   **[C5]**. Best *"beyond structure"* — prior highs/lows or all-time highs.
3. **[C3] Clock window**: reversal timed to minutes-into-the-hour. Stated 22-52,
   preferred 30-45, favourite *"37 minutes into the hour"*. A 20-30 variant with a
   75% figure also appears. **These conflict — sweep, do not pick** (see
   Contradictions).
4. **[C4] Correlation check**: for Gold, DXY moving inversely; for USDJPY, the Yen
   basket; Gold Spread watched alongside. Hard veto when dollar and yen move together
   on high volume. Required in some videos, optional in others — encode as a mode
   switch.
5. **[C6] Trigger**: drop to 1m, then 15s/5s/1s — *"I mainly use the 5 second chart
   for fractal shifts"* — and take a Type 3 shift (W-shape sweep-then-break). Nested
   variant **[C7]** is higher confidence. A V-shape change of character is a no-trade
   **[F8]**.
6. **[X1] Entry**: break of the 5s/1m candle low (or high), typically after a retrace
   into the 50% of the shift leg.
7. **[X2] Stop**: beyond the local swing/wick that formed the shift, or tight above
   the 50% zone; one note gives 15-20 pips (class B — unverified number). Trails on
   new extremes in his favour **[X4]**.
8. **[X3] Target**: **50% of the prior impulse** — the most consistent rule in the
   corpus (stated in seven extracted videos). Gold runs a sized-up 1-1.5R variant
   instead (see Instruments).
9. **[X5] Discretionary exit**: cuts before target on fading volume **[C9]**. This is
   the judge-layer candidate — the one part that belongs to a discretionary agent
   rather than Python.

Timeframe stack, as stated: Daily/Weekly for directional context and candle behaviour;
4H/1H for AOIs and the overextension being faded; 30m/15m for candle-flip confirmation
and exit reference; 5m/1m for shift location; 15s/5s/1s for the entry trigger.

## Instruments and session

- **XAUUSD is primary, USDJPY second; DXY and "Gold Spread" are read, not traded.**
- Traded mostly in the **Asian session**, frequently the second or third hour of it
  (class B). Session claims conflict — he also says *"Especially London session, I've
  been trading London session now"* while demonstrating the identical setup in Asia.
- **Hard regime filter on Gold**: when Gold is *"very directional, very trendy"* he
  does not touch it — *"I only trade reversals in range-bound conditions."* A backtest
  run on ALL Gold data misrepresents the method badly; the range gate [C1] is part of
  the population definition, not an optional filter.
- **Gold is sized up at lower R:R**: *"around 1 1.5 risk to reward trades"* with more
  size. Sizing and target are coupled — do not sweep them independently without
  noting the coupling.
- USDJPY is itself sometimes disqualified: *"just low volume kind of shit, rangy."*
  Note the tension with the range requirement — range is required at the higher
  timeframe but disqualifying at the instrument level. Encode as two independent
  gates (HTF range [C1] vs instrument-volume floor [C9c]) and let the data say
  whether that resolves it. That resolution is a hypothesis, not a fact.

## Explicit no-trade filters

The most directly codable rules in the corpus, and the most likely to carry real edge,
because they are the discretionary skips a naive backtest would take anyway. Each is
individually toggleable in the detector.

| ID | Filter | Basis |
|---|---|---|
| F1 | Instrument trending, not ranging | quote, class A |
| F2 | Setup not seen in prior 4-5 hours | quote, class A |
| F3 | Too early in the hour (~15 min in / near hour open) | quote, class A |
| F4 | Entering just before a 15m candle open | quote, class A |
| F5 | Dollar and yen moving same direction on high volume | quote, class A (hard veto) |
| F6 | Gold Spread and DXY same direction | quote, class A |
| F7 | No clean entry model on the traded pair | quote, class A |
| F8 | Pattern is a change of character, not a shift | quote, class A |
| F9 | Low-volume, rangy instrument | quote, class A |

Verbatim quotes for all nine are in `references/citations.md`.

## Parameters and defaults

Full definitions, candidate formalisations, sweep ranges, standalone-edge tests and
falsification criteria live in `references/confluence-table.md` — **read it before
writing any detector code.** Summary of the parameter surface:

| Param | Default | Sweep | Source |
|---|---|---|---|
| `range_lookback_hours` | 8 | 4-16 | quoted "5-12 plus hours"; default researcher-chosen inside his range |
| `range_efficiency_max` | 0.30 | 0.15-0.50 | researcher-chosen — he gave no width test |
| `oe_atr_mult` | 1.0 | 0.5-2.0 | researcher-chosen — "overextension" has no stated magnitude |
| `oe_max_pullback_frac` | 0.33 | 0.20-0.50 | researcher-chosen — "no meaningful pullback" unquantified |
| `oe_volume_z_min` | 1.0 | 0.5-2.0 | researcher-chosen — "high volume" unquantified |
| `window_start_min` / `window_end_min` | 30 / 45 | start 15-40, end 30-59 | quoted variants: 22-52, 30-45, 20-30, point 37 — conflict, sweep |
| `boundary_buffer_min` | 2 | 0-5 | quoted avoidance of 15m opens; buffer size researcher-chosen |
| `corr_mode` | veto_only | {off, veto_only, required} | required vs optional is an unresolved contradiction |
| `corr_lookback_min` | 30 | 10-60 | researcher-chosen — no stated lookback |
| `aoi_proximity_atr` | 0.25 | 0.10-0.50 | researcher-chosen — AOI construction unspecified |
| `pivot_k` (swing definition) | 3 | 2-5 | researcher-chosen — swing never defined |
| `shift_shape` | W_required | {W_required, any_break} | quoted W-vs-V distinction; sweep tests whether it matters |
| `stop_atr_max` (oversized-stop tell) | 2.5 | 1-4 | his stated tell; threshold researcher-chosen |
| `entry_retrace_frac` | 0.50 | 0.38-0.62 | quoted "targeting that 50%" of the shift leg |
| `target_impulse_frac` | 0.50 | fixed, ablate impulse definition | quoted, most consistent rule (7 videos) |
| `gold_rr_override` | 1.25 | 1.0-1.5 | quoted "1 1.5 risk to reward" on Gold |
| `setup_recency_hours` | 4.5 | 3-6 | quoted "4 to 5 hours" |
| `candle_flip_gate` | off | {off, on} | class D — mechanism undefined; off until evidence exists |
| `trigger_tf` | 1m | {1m, 15s, 5s} | he states 5s; data availability constrains — see below |

Every researcher-chosen default is a placeholder for a sweep, not a claim about the
method. Sweeps induce multiple comparisons: any surviving parameter region must
re-confirm on a sealed holdout before it is believed.

## Contradictions — encode, do not reconcile

1. **The timing window is not one number**: 22-52, 30-45, 30-37, 20-30, and "37" all
   appear, with a 75% figure attached to 20-30. Minute-of-hour is a parameter to
   sweep, not a constant.
2. **DXY confluence is required in some videos, optional in others.** He took a Gold
   long against DXY and said afterwards he should have waited. Hence `corr_mode`.
3. **Session claims conflict** — London claimed while demonstrating in Asia. Session
   is a parameter, not a fact.
4. **Counter-trend at extremes**: he shorts Gold at all-time highs while acknowledging
   the uptrend. "Beyond structure" and "range-bound only" are in tension at extremes.
5. **Published statistics are unverifiable** (see Evidence Limits #4).
6. **The 30-40% skipped-setup rate cuts both ways**: either the skips were losers (an
   unmodelled filter carries the edge) or the edge is robust to them. Only the
   journal-grounded decision comparison separates these — see How to use, item 4.

## What this method does NOT specify

Stated plainly so nobody fills these gaps silently:

- **"Overextension" has no numeric definition** — no ATR multiple, distance, or
  body ratio. The single biggest gap.
- **"Range condition"** over 5-12h has no width or compression test.
- **"Area of interest"** — level construction is never mechanically specified.
- **"Type 3 shift"** lacks a precise swing definition (what qualifies as the swept
  high and the broken low).
- **Correlation alignment** has no threshold — how inverse, over what lookback.
- **Timezone** — the Asia session, its second-or-third-hour habit, and hour
  boundaries are all clock-dependent and
  unanchored. He is AU-based; his charting platform's hour bars set the clock.
- **"Candle flip"** — named in the timeframe stack, never defined.
- **"Gold Spread"** — instrument identity unresolved.
- **The impulse for the 50% target** — which "previous move" is measured, from where.
- **Precise stop placement** — "beyond the swing/wick" without tick/buffer rules.

## Data and implementation constraints

- **Instrument data**: testing requires XAUUSD (plus DXY, a JPY basket, and — once
  identified — Gold Spread) at 1m or finer. This is a different instrument and
  session from the repo's NQ system; NQ data cannot proxy for it.
- **Sub-minute**: his stated trigger chart is 5 seconds. If only 1m data exists, run
  `trigger_tf=1m` and state the fidelity loss explicitly in every report — the tested
  strategy is then an approximation of his, by construction.
- **Volume**: on spot FX/CFDs volume is tick volume, broker-dependent. Any
  volume-gated rule inherits that caveat.
- **Clock anchoring**: minute-of-hour position is invariant across whole-hour-offset
  timezones, so the "37 minutes" family of rules survives most anchor choices — but
  half-hour-offset zones and, more importantly, session boundaries and "hour N of
  session" do not. `tz_anchor` must be explicit in config, and hourly bars must match
  the anchor his charts use, not an assumption.
- **No lookahead**: signals compute on closed candles only; orders activate next bar.
  Repo standard applies (`context/code-standards.md`).
- **Population definition**: the range-regime gate [C1] defines the tradeable
  population. Reporting results over all hours "with the filter off" is a valid
  ablation, but headline results must be over the gated population or they
  misrepresent the method.

## How to use this skill

1. **Before writing detector code**: read `references/confluence-table.md` end to
   end. Every gate must be individually toggleable; every config value carries the
   quote it came from (or an explicit "researcher-chosen" tag).
2. **Citation discipline**: any new rule added to the detector needs a verbatim quote
   in `references/citations.md` first. No quote, no rule. Never upgrade a class B/C/D
   item to load-bearing without re-deriving it from the corpus.
3. **Ablation mandate**: the point is finding which parts, if any, carry edge. Report
   per-confluence ablations; recommend the minimal surviving subset; say plainly if
   the answer is "none of it survives". Do not tune toward his marketing statistics —
   divergences are reported, not fixed.
4. **The discretionary layer**: after the mechanical detector exists, compare it
   trade-by-trade against his journal-channel reasoning. Where they diverge, he
   applied an unstated filter — that gap is the only part that belongs in an agent
   rather than in Python, and it is also the only way to resolve Contradiction #6.
5. **Scope**: research only. Do not touch the live/paper path. Any proposal against
   the strategy document needs a written hypothesis, out-of-sample results, and
   Angus's approval per the repo's non-negotiables.

## References

- `references/confluence-table.md` — every confluence resolved into testable
  predicates: quoted definition, named ambiguity, 2-4 candidate formalisations,
  parameters with sweeps, standalone-edge test, falsification criterion.
- `references/citations.md` — the full rule → verbatim quote table with evidence
  classes, keyed to the rule IDs used throughout.
