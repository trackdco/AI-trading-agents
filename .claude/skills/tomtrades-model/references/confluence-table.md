# Confluence table — every rule resolved into testable predicates

**Evidence version: v2** — 58 extracted sources (@TomTradesJournal 18/18,
@itstomtrades main 40/53, course 0/13 segments). v1 was built on 17 sources and is
superseded. Read `citations.md` for the verbatim quote behind every rule ID.

Evidence classes: **A** = verbatim spoken quote; **B** = asserted in the audit, quote
in the corpus, not yet re-attached; **C** = chart-read only, not spoken; **D** = named
but never defined.

Discipline for this file: his definition is quoted; the ambiguity is named; the
formalisations are **researcher candidates**, not his rules; every number a
formalisation introduces is a sweep, and any surviving region must re-confirm on a
sealed holdout. "Standalone edge" always means: hold everything else at defaults,
toggle only this gate, compare matched populations.

---

## What changed from v1 — read this first

The wider corpus **closed three gaps v1 recorded as unspecified**, and one v1 filter is
now contradicted by his own numbers. Anything built against v1 needs revisiting.

| Item | v1 status | v2 status |
|---|---|---|
| **C2 "overextension"** | "the single biggest gap — no magnitude stated" | **Defined by DURATION, not magnitude** — class A |
| **C2 invalidation** | `oe_max_pullback_frac` 0.33, researcher-chosen | **0.50, his number**, class A |
| **C1 "range"** | "no width test, no compression measure" | **Defined as mean correction depth** — class A |
| **C5 AOI construction** | "no construction rule exists anywhere" | **AOI = the C1 range boundaries** — class A |
| **C7 nested shift** | "class D for definition; a label, not a gate" | **Class A definition + claimed +18pp uplift** — promote to gate |
| **X3 impulse** | three candidate definitions | **"the hourly extension"** — one candidate strongly favoured |
| **F3 avoid first 15 min** | hard filter, class A | **Contradicted by his own win-rate table** — becomes a graded prior |
| Session conflict (Asia vs London) | logged as contradiction | **Partly resolved** — he trades both, at session opens |

---

## C1 — Middle-timeframe range condition (context gate) — class A, NOW DEFINED

**He says:** *"I identify a range as whether on average over those past 5 to 12 plus
hours how much we correct the previous move"* — and *"I identify that by looking at the
past 5 hours of price action"*. Instrument-level skip [F1]: *"very directional, very
trendy... I only trade reversals in range-bound conditions"*.

**This is a mean-retracement definition, not a width definition.** All four v1
formalisations measured the wrong thing — range width, efficiency, slope, dispersion.
His test is: *when price moves, how much does it typically give back?*

**Never specified:** the threshold correction fraction, how legs are identified, and
whether "on average" is mean or median.

**Candidate formalisations (1h bars over `range_lookback_hours` = N, default 8,
sweep 5-12 per his stated bounds):**
1. **Mean retracement depth (his definition, primary)**: identify swing legs via
   `pivot_k`-bar pivots on 1h; `mean(retrace_i / leg_i) >= range_retrace_min`.
   Default 0.50, sweep 0.35-0.70. A market that gives back half of every leg is
   "rangey" in his sense.
2. **Median retracement** — same, median instead of mean, robust to one deep leg.
3. **Kaufman efficiency ratio** `<= range_efficiency_max` (default 0.30, sweep
   0.15-0.50) — retained from v1 as a cheap proxy; test whether it correlates with (1).
4. **Range/ATR width** `(max(H)-min(L))/ATR(1h,24) <= range_width_atr_max` (default
   3.0, sweep 2.0-6.0) — retained only as a control; his words do not support it.

**Standalone edge:** run the trigger [C6] with all other gates at defaults; compare
expectancy and 50%-target hit rate inside vs outside the range condition, per
formalisation, matched on time-of-day. **Also test (1) against (3)/(4) directly** — if
the cheap proxies track his definition, use them; if not, his definition is doing
distinct work.

**Falsified if:** conditional expectancy inside "range" is indistinguishable from
outside across the whole sweep for all formalisations — "range-bound only" adds
nothing and the population definition collapses to "all hours".

---

## C2 — Hourly overextension — class A, NOW DEFINED BY DURATION

**He says:** *"20 to 30 minutes of price action moving in one direction without a
pullback"*, and elsewhere *"at least 15 to 30 minutes of price action... push in one
direction"*. Invalidation is explicit: *"I define a pullback that invalidates an
overextension by pulling back to around 50% or more."* Framing: the elastic band.

**This reframes the concept.** v1 called magnitude "the single biggest gap" and
proposed four magnitude-based formalisations. He never gives a magnitude because
**magnitude is not his criterion — persistence is.** A move is overextended when it has
gone one way for 15-30 minutes without giving back half.

**Never specified:** what counts as "a pullback" below the 50% invalidation level, and
whether the clock starts at the hour open or at the move's origin.

**Candidate formalisations (1m bars, hour anchored per `tz_anchor`):**
1. **Duration + invalidation (his definition, primary)**: a directional run of
   `oe_min_duration_min` (default 20, sweep 15-35) minutes from the hour open, during
   which max adverse retrace stays `< oe_invalidation_frac` (**default 0.50 — his
   number**, sweep 0.35-0.65) of the run's displacement.
2. **Duration + one-sidedness**: as (1) plus fraction of 1m closes beyond hour_open on
   the drive side `>= oe_onesided_frac` (default 0.75, sweep 0.60-0.90).
3. **Duration + magnitude floor (hybrid control)**: as (1) plus
   `|price - hour_open| >= oe_atr_mult * ATR(1h,24)` (default 1.0, sweep 0.5-2.0).
   **Retained specifically to test whether magnitude adds anything to duration** — if
   it does not, that is a finding about his method, not a bug.
4. **Volume qualifier**: any of the above plus hour-so-far volume z-score vs
   same-hour-of-day baseline `>= oe_volume_z_min` (default 1.0, sweep 0.5-2.0). Tick
   volume on spot — caveat inherited.

**Standalone edge:** mark every hour meeting each definition; measure frequency and
size of a snap-back to 50% of the run within the same and next hour, against
**displacement-matched** hours that fail the definition. The match is essential or you
measure move size rather than overextension.

**Falsified if:** snap-back statistics conditional on the label do not beat the
displacement-matched base rate — "overextension" is just "a big move". A second, more
interesting falsification: if (3) beats (1), his own stated criterion is worse than the
one he never gave.

---

## C3 — Minute-of-hour window — class A, with a CLAIMED WIN-RATE PROFILE

**He says**, in one video, a complete profile:
- *"when in the first 0 to 10 minutes of the hour, I have around a 66% win rate"*
- *"from around 10 to 30 minutes into the hour, I have around a 50% win rate"*
- *"around the halfway point of the hour, I have the highest win rate on reversals, a 75% win rate"*

Elsewhere: *"the best reversals happen around 30 minutes into the hour... from 30 to 45
minutes"*; *"around 15 or 30 minutes into an hourly candle"*; *"I like taking trades
reversals around 37 minutes into the hour"*; and *"if I go onto a 30 minute reversal,
that goes onto a 90% win rate"*.

**This is now a testable prediction, not just a window.** The claimed profile is
**non-monotonic** — good early, worst in the middle, best at the halfway mark. That is
a specific, falsifiable shape, and it is far more informative than a pass/fail window.

**It also contradicts F3.** v1 encoded *"you're more likely to be stopped out taking a
reversal around 15 minutes in"* as a hard early-hour skip. His own table puts 0-10
minutes at 66% — better than the 10-30 bucket. **Demote F3 from a gate to a prior**
and let the sweep decide.

**Formalisation (one, parameterised — reconciliation is forbidden):**
Signal minute `m` passes iff `window_start_min <= m <= window_end_min`, `m` not within
`boundary_buffer_min` of a 15-minute boundary. Defaults 30/45/2; sweeps start 15-40,
end 30-59, buffer 0-5. His named variants — 22-52, 30-45, 20-30, 15-or-30, {37} — are
points in the sweep and must each be reported.

**Standalone edge:** bucket trigger outcomes into 5-minute minute-of-hour bins and plot
the expectancy profile. **Overlay his claimed 66/50/75 profile.** Agreement is strong
evidence the clock effect is real; a flat profile falsifies the entire "hourly candle
as container" premise.

**Falsified if:** the per-bin profile is flat, or its shape is uncorrelated with his
claimed one. Note 12 bins × a sweep is heavy multiplicity — any surviving window
re-confirms on holdout. All of it is meaningless until `tz_anchor` matches the clock
his charts use.

---

## C4 — Correlation check (DXY / Yen basket / Gold Spread) — class A, with a CLAIMED EFFECT SIZE

**He says (hard veto):** *"If both dollar and yen are moving in the same direction with
high volume, I should not be taking a trade."* Gold Spread: *"we have Gold Spread and
DXY both moving in the same direction"* explains consolidation. And a quantified claim:
***"DXY correlation increase my WR by 17%"***.

**Never specified:** what "moving" means (lookback, magnitude), how inverse is inverse
enough, which instruments form "the yen basket", what "Gold Spread" is, and whether the
17% is percentage points or relative. **Do not guess the Gold Spread ticker — identify
the instrument or leave F6 uncoded and say so.**

**Candidate formalisations (`corr_lookback_min` = L, default 30, sweep 10-60):**
1. **Sign check**: sign of DXY return over L opposite the intended direction ⇒ pass.
   Cheapest and closest to how he talks.
2. **Rolling correlation**: corr(1m returns vs DXY over L) `<= -corr_min` (default 0.3,
   sweep 0.1-0.6).
3. **Veto-only**: block iff DXY and JPY-basket returns share sign AND both `|z| >=
   corr_veto_z` (default 1.0, sweep 0.5-2.0) — the literal quote, nothing more.

Mode switch `corr_mode ∈ {off, veto_only, required}`; default `veto_only`, the only
version he states as a hard rule.

**Standalone edge:** expectancy of signals passing vs failing each mode, matched on C2
magnitude. **Report the win-rate delta directly against his claimed +17%** — this is
the cleanest single number in the corpus to check him against.

**Falsified if:** pass/fail expectancy is indistinguishable in every mode and lookback,
or the measured delta is nowhere near +17% in any configuration.

---

## C5 — AOI touch — class A for existence, NOW PARTLY CONSTRUCTED

**He says:** *"waiting for price to overextend into the higher low of that range"*, and
*"either overextend into the highs of this range or overextend into the lows of this
range to look for a reversal around the halfway point of the hour"*. Separately he
references *"a 4 hour AOI... 4 hour, daily level"*.

**The primary AOI is the C1 range boundary.** v1 stated flatly that no construction
rule existed; it does — the level being hit is the extreme of the middle-timeframe
range he already requires. This makes C5 largely **derived from C1** rather than
independent, which is itself a testable structural claim.

**Never specified:** how the HTF (4h/daily) levels are picked when he uses those
instead, and how close counts as "into".

**Candidate formalisations (proximity band `aoi_proximity_atr`, default 0.25 ×
ATR(1h,24), sweep 0.10-0.50):**
1. **Range boundary (his primary)**: the high/low of the C1 `range_lookback_hours`
   window, including its interior higher-low/lower-high pivots.
2. **Swing pivots on 1H/4H**: `pivot_k`-bar fractal pivots, optionally untested-only.
3. **Calendar extremes**: prior day / prior week / session high-low.
4. **Beyond-structure binary**: price beyond the prior N-day extreme (N default 5,
   sweep 3-20), ATH as the limiting case.

**Standalone edge:** reversal quality with vs without AOI proximity, matched on C2 and
time-of-day. **Critically, test whether (1) adds anything once C1 is already gating** —
if the AOI is just the range edge, it may be fully redundant with C1.

**Falsified if:** no construction × band beats the no-AOI baseline, or (1) is
statistically redundant with C1 — in which case delete C5 and fold it into C1.

---

## C6 — The shift (the trigger) — class A, best-defined concept in the corpus

**He says:** sweep-then-break — takes out a high then breaks the low, or the mirror. A
shift is a **W-shape swing break**; a change of character is a **V-shape minor break**
and is a no-trade: *"it wouldn't technically be a shift, it would be more of a change of
character."* Trigger chart: *"I mainly use the 5 second chart for fractal shifts"*, but
also *"we can just wait for a break of these 1-minute candle lows here"* — **1m is an
acceptable fallback in his own words**, which matters given data availability.

**Taxonomy is incomplete.** He names a *"Type 3 shift"* and separately a *"1 minute
type 2 shift"*. Types 1 and 2 are never defined in extracted material. **Do not invent
them.** Code the sweep-then-break pattern he describes and label it; leave the
numbering alone.

**Never specified:** swing definition, sweep depth, completion window, W-vs-V threshold.

**Candidate formalisations (on `trigger_tf`, default 1m):**
1. **Fractal sweep-break**: swing = `pivot_k`-bar pivot; short signal when a bar trades
   above the last swing high by `>= sweep_min_ticks` (default 1, sweep 0-2) and price
   then closes below the last swing low within `shift_window_bars` (default 10,
   sweep 3-20).
2. **W-required**: (1) plus an intervening pullback pivot between sweep and break.
   `shift_shape ∈ {W_required, any_break}`, default `W_required`. `any_break`
   deliberately admits his invalid V so the distinction is testable.
3. **Stop-size discriminator (his own tell)**: valid only if implied stop (entry to
   pattern extreme) `<= stop_atr_max * ATR(trigger_tf, 20)`, default 2.5, sweep 1-4.

**Standalone edge:** trigger-only backtest (all context gates off) vs trigger inside
gates; and W_required vs any_break vs V-only directly.

**Falsified if:** W and V populations are indistinguishable — his sharpest stated
distinction carries nothing; or trigger-only expectancy `<= 0` everywhere and gating
never rescues it.

---

## C7 — Fractal shift (shift within a shift) — class A, PROMOTED TO GATE

**He says, now with a definition:** *"What a fractal shift is, is that you simply just
look for a shift within that shift. You wait for price to come into this 50% area, and
on this lower timeframe... "* and the full sequence: *"I will take a one-minute fractal
shift... looking to enter on the pullback after that shift to around 50%... and I wait
for a second shift within that one-minute shift."*

**And a claimed effect size:** *"using a simple market structure shift for my entry
model I have just under a 70% win rate"* → *"adding in a little bit extra refinement
looking for these fractal shifts, I now have around an 88% win rate."*

**This is the largest claimed single improvement in the corpus (+18pp)** and v1 had it
as an unparameterised label. It is now the highest-priority ablation after C3.

**Formalisation:** outer shift on `trigger_tf`; price retraces into the
`entry_retrace_frac` zone of the outer shift leg; inner shift (same C6 definition) on
the next finer TF, completing inside that zone within `nest_window_bars` (default =
outer `shift_window_bars`). `nested_required ∈ {off, label, gate}` — **default `gate`,
changed from v1**, because he states it as his refinement rather than an observation.

**Standalone edge:** nested vs plain shift expectancy in identical context.
**Report the win-rate delta against his claimed 70% → 88%.**

**Falsified if:** no difference, or the delta is far short of +18pp — then the
refinement he attributes his edge to is noise, which would be the single most
consequential negative finding available here.

---

## C8 — Candle flip (30m/15m confirmation) — class D, still the thinnest concept

**He says:** nothing quotable, across 58 sources. It appears only in the timeframe
stack. The expanded corpus **did not** close this gap, which is itself informative.

**Candidate formalisations (explicitly researcher-invented):**
1. Prior completed 15m candle closes against the drive direction before the trigger.
2. Same on 30m.
3. Engulfing variant.

`candle_flip_gate` default **off** — class D does not gate by default.

**Falsified if:** it does not improve matched expectancy — delete it. With class D
evidence the bar for keeping it is higher, not lower.

---

## C9 — Volume behaviour — class A in four roles, thresholds unstated

**He says:** the drive comes *"with high volume"* [C2]; exit when *"volume started to
decrease"* [X5]; the correlation veto requires high volume [F5]; an instrument can be
disqualified as *"just low volume kind of shit, rangy"* [F9]; and *"Obviously low volume
stuff like this, I'm not looking to trade it"*.

**Never specified:** baseline, lookback, threshold. Spot volume is tick volume.

**Candidate formalisations:**
1. **Entry-side**: hour-so-far volume z vs same-hour-of-day baseline over
   `vol_baseline_days` (default 20, sweep 10-60) `>= oe_volume_z_min`.
2. **Exit-side (X5 mechanisation)**: rolling 5m volume slope `< 0` for `vol_fade_bars`
   (default 3, sweep 2-6) consecutive bars once `>= vol_fade_min_r` (default 0.5R,
   sweep 0-1R) in profit ⇒ exit. A candidate mechanisation of a discretionary
   behaviour — label it as such in every report.
3. **Instrument floor (F9)**: skip instrument-days below `adv_percentile_min` (default
   20th percentile of trailing 60-day tick volume, sweep 10-40).

**Falsified if:** (2) especially — if the volume-fade exit does not beat
hold-to-target [X3] on expectancy or drawdown, his exit either isn't volume-driven or
isn't mechanisable this way. Report which.

---

## X1-X5 — Execution mechanics

**X1 Entry — class A, retrace zone WIDENED.** *"Took the entry at the break of the
candle low targeting that 50%."* Entry = stop order at the break of the trigger-TF
candle low/high after a retrace into the shift leg. **New evidence widens the zone:**
*"a pullback into, you know, around 50% or even more towards 70%"*. `entry_retrace_frac`
default 0.50, **sweep 0.38-0.70** (was 0.38-0.62). `entry_retrace_required ∈ {yes, no}`,
default no — he says "typically".

**X2 Stop — class A placement.** *"I can place it below this lower timeframe high"*;
*"you can enter at the 50% area with your stop below the most recent low"*; *"put our
stop above the previous high"*. Consistent across sources: beyond the local structure
that formed the shift. `stop_mode ∈ {pattern_extreme, retrace_zone}` default
`pattern_extreme`; `stop_buffer_ticks` default 1, sweep 0-3. The v1 "15-20 pips" note
remains class B and is an FX unit — re-derive per instrument, do not port it to Gold.

**X3 Target — class A, IMPULSE NOW RESOLVED.** Converging across sources: *"The take
profit is always going to be set at 50% of the previous higher timeframe move"*;
*"targeting like the 50% of the hourly candle extension"*; *"we can target 50% of this
hourly overextension here"*. **`impulse_def` default = `hour_open_to_extreme`** — the
C2 run itself — rather than v1's three-way toss-up. Keep `last_pivot_leg` and
`day_extreme_leg` as ablations only.

Competing target variants exist and must be tested as alternatives, not merged:
*"Target around a 1:1"*; *"target a 1 to 2 at around this previous 1 minute structure
lows"*; Gold override *"around 1 1.5 risk to reward trades"* with increased size.
`target_mode ∈ {impulse_50, fixed_rr, ltf_structure}`, default `impulse_50`. Sizing and
target are coupled on Gold — never sweep independently without flagging.

**X4 Trail — class A.** *"I trail my stop loss when we break a high in my favour."*
Trail to prior pivot on each new `pivot_k` swing in favour. `trail_tf ∈ {trigger_tf,
1m, 5m}`, default `trigger_tf`. The repo's exit work elsewhere shows trail-TF choice can
dominate results — treat as load-bearing.

**X5 Discretionary exit — class A behaviour, no rule.** Mechanised candidate = C9.2.
X5 is the judge-layer candidate. Backtests run `{X3 only}` and `{X3 + C9.2}` and report
both; neither is "his exit", because his exit is discretionary.

**Risk — class A, NEW.** *"Risking 0.5% to 1% per trade"*; *"1% risk per trade, always
use stop losses, max 2-3 trades per day"*. `risk_per_trade_pct` default 1.0, sweep
0.5-1.0; **`max_trades_per_day` default 3, sweep 1-5 — new in v2** and a genuine
constraint, since a signal-taking backtest will otherwise fire far more often than he
does. Scale-ins remain class B (second position 40-60%, re-entries 25%);
`scaling_enabled` default off.

---

## F1-F11 — filter mapping

| ID | Filter | Maps to | Note |
|---|---|---|---|
| F1 | Instrument trending, not ranging | C1 | population definition, not an option |
| F2 | Setup not seen in prior 4-5h | `setup_recency_hours` 4.5, sweep 3-6 | self-referential: needs the detector to define "setup seen" |
| F3 | Too early in the hour | C3 | **demoted to a prior** — his own table says 0-10 min is 66% |
| F4 | Just before a 15m candle open | C3 `boundary_buffer_min` | |
| F5 | Dollar and yen same direction | C4 veto | |
| F6 | Gold Spread and DXY same direction | C4 | **uncodable until the instrument is identified** — leave off, say so |
| F7 | No clean entry model | C6 validity | discretionary; flag the gap |
| F8 | Change of character, not a shift | C6 `shift_shape` | |
| F9 | Low-volume instrument | C9.3 | |
| **F10** | **Entering at 50% without LTF confirmation** | C7 `nested_required` | **new in v2** — *"by waiting for that extra shift, I avoided entering too early"* |
| **F11** | **Trend continuing / sideways too long** | C1 | **new in v2** — *"The trend is continuing. I'm not the biggest fan of that."* |

---

## His claimed numbers — the falsification scoreboard

Every figure he states becomes a prediction. Report measured against claimed, side by
side. All are self-reported and unverified; a channel is a selected sample.

| Claim | His number | Test |
|---|---|---|
| Minute 0-10 win rate | 66% | C3 bin profile |
| Minute 10-30 win rate | 50% | C3 bin profile |
| Halfway-point win rate | 75% (his best) | C3 bin profile |
| 30-minute reversal | 90% | C3 named variant |
| Simple structure shift | ~70% | C6 trigger-only |
| Fractal (nested) shift | ~88% | C7 ablation |
| DXY correlation gate | +17% win rate | C4 delta |
| Overall claimed | 76%, 81%, 85%, 88% across videos | headline backtest |
| Setups skipped discretionarily | 30-40% | take-every-signal gap |

If the measured profile broadly tracks the claimed one, that is meaningful evidence the
mechanism is real even where the absolute numbers are inflated. If the shape does not
track at all, the method is unsupported regardless of any single win rate.

## Reporting requirements (inherited, non-negotiable)

Per-confluence ablations with signal count, hit rate, expectancy and delta-from-removal;
rank by contribution; recommend the minimal surviving subset; say plainly if none
survives. Quantify the take-every-signal vs skips-30-40% gap rather than papering over
it. Divergences from his claimed win rates are findings, not problems. Headline
population = C1-gated hours. All sweeps re-confirm on a sealed holdout.
