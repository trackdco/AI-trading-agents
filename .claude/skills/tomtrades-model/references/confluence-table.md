# Confluence table — every rule resolved into testable predicates

Evidence version: audit v1 (journal channel only, 18/18 videos). Read
`citations.md` for the verbatim quote behind every rule ID. Evidence classes:
**A** = verbatim spoken quote in the audit; **B** = audit assertion whose quote lives
in the extraction corpus but was not reproduced in audit v1 (re-attach before
load-bearing use); **C** = chart-read only, not spoken; **D** = named but undefined.

Discipline for this file: his definition is quoted; the ambiguity is named; the
formalisations are **researcher candidates**, not his rules; every number a
formalisation introduces is a sweep, and any surviving region must re-confirm on a
sealed holdout. "Standalone edge" always means: hold everything else at defaults,
toggle only this gate, compare matched populations.

Contents: C1 range condition · C2 hourly overextension · C3 minute-of-hour window ·
C4 correlation check · C5 AOI touch · C6 Type 3 shift · C7 nested shift · C8 candle
flip · C9 volume behaviour · X1-X5 execution mechanics · F1-F9 filter mapping.

---

## C1 — Middle-timeframe range condition (context gate) — class A

**He says:** *"You always want to have a middle timeframe sort of rangey condition...
over the past 5-12 plus hours."* Also, as a hard instrument-level skip [F1]: *"very
directional, very trendy... I only trade reversals in range-bound conditions"*.

**Never specified:** what "rangey" means — no width test, no compression measure, no
trend statistic; the lookback is open-ended ("5-12 plus").

**Candidate formalisations (1h bars over `range_lookback_hours` = N):**
1. **Range/ATR ratio**: `(max(H) - min(L)) / ATR(1h, 24) <= range_width_atr_max`.
   Params: N default 8 sweep 4-16; `range_width_atr_max` default 3.0 sweep 2.0-6.0.
2. **Kaufman efficiency ratio**: `|C_t - C_{t-N}| / sum(|C_i - C_{i-1}|) <=
   range_efficiency_max`. Default 0.30, sweep 0.15-0.50. Directly operationalises
   "not trendy".
3. **Normalised regression slope**: `|OLS slope of 1h closes over N| * N / ATR(1h,24)
   <= range_slope_max`. Default 1.0, sweep 0.5-2.0.
4. **Close dispersion**: `stdev(1h closes over N) / ATR(1h,24) <= range_disp_max`.
   Default 1.5, sweep 0.75-3.0.

**Standalone edge:** run the trigger [C6] with all other gates at defaults; compare
expectancy and 50%-target hit rate for signals inside vs outside the range condition,
per formalisation, matched on time-of-day.

**Falsified if:** conditional expectancy inside "range" is statistically
indistinguishable from outside across the whole sweep for all four formalisations
(bootstrap CIs overlap) — then "range-bound only" adds nothing and the population
definition collapses to "all hours".

---

## C2 — Hourly overextension — class A (magnitude: none stated)

**He says:** *"All my trades is when the hourly candle is immediately pushing in one
direction with high volume... overextending in one direction."* Best when *"beyond
structure"* — prior highs/lows or all-time highs. Framing: *"think of price like an
elastic band: the more you stretch it, the more likely you'll have a snap back."*

**Never specified:** the audit's single biggest gap — no ATR multiple, point distance
or body ratio for "overextending"; "immediately" and "high volume" and "meaningful
pullback" all unquantified.

**Candidate formalisations (evaluated intra-hour on 1m bars, hour anchored per
`tz_anchor`):**
1. **Displacement + pullback cap**: `|price_now - hour_open| >= oe_atr_mult *
   ATR(1h, 24)` AND max adverse retrace so far `<= oe_max_pullback_frac` of
   displacement. Defaults 1.0 / 0.33; sweeps 0.5-2.0 / 0.20-0.50.
2. **One-sidedness**: fraction of 1m closes beyond hour_open on the drive side
   `>= oe_onesided_frac` (default 0.75, sweep 0.60-0.90), with formalisation-1's
   displacement floor. Operationalises "immediately pushing".
3. **Body dominance + volume**: forming hourly body/range `>= oe_body_frac` (default
   0.7, sweep 0.5-0.9) AND hour-so-far volume z-score vs same-hour-of-day baseline
   `>= oe_volume_z_min` (default 1.0, sweep 0.5-2.0). Volume is tick volume on spot —
   caveat inherited.
4. **Band stretch (elastic band)**: `|price - MA(1h, 20)| / stdev(1h, 20) >=
   oe_band_z` (default 2.0, sweep 1.5-3.0).

**Standalone edge:** mark every hour meeting each definition; measure frequency and
magnitude of a snap-back to 50% of the intra-hour move within the same + next hour,
vs matched hours with equal displacement that fail the definition (the match on
displacement is essential — otherwise you measure move size, not "overextension").

**Falsified if:** snap-back statistics conditional on the label do not beat the
displacement-matched base rate for any definition — then "overextension" is just
"a big move" and the concept carries no information of its own.

---

## C3 — Minute-of-hour window — class A, internally contradictory

**He says:** *"My favourite time to take reversals is 37 minutes into the hour"* —
reasoned as *"the second half of the hour and it's approaching the second half of a
15-minute candle."* Stated range 22-52; preferred 30-45; one video attaches 75% to a
20-30 window. Early-hour skip [F3] and 15m-boundary skip [F4] are separate quotes.

**Never specified:** which window is THE rule — they cannot all be. Also unanchored:
whose clock (see tz note in SKILL.md).

**Formalisation (one, parameterised — reconciliation is forbidden):**
Signal minute `m` passes iff `window_start_min <= m <= window_end_min` and `m` is not
within `boundary_buffer_min` before any 15-minute boundary, and `m >=`
`early_hour_min` (default 15 from [F3], sweep 10-22). Defaults 30/45/2; sweeps
start 15-40, end 30-59, buffer 0-5. His four variants (22-52, 30-45, 20-30, {37}) are
named points in the sweep and must be reported individually.

**Standalone edge:** with all other gates fixed, bucket trigger outcomes by 5-minute
minute-of-hour bins; test expectancy per bin against uniform (bootstrap), and each
named variant against the all-minutes baseline.

**Falsified if:** the per-bin expectancy profile is flat — the clock carries nothing
and the entire "container" idea [his hourly-candle framing] loses its mechanism. Note
12 bins x a sweep = multiplicity; a surviving window must re-confirm on holdout
before it is believed. Any result is meaningless until `tz_anchor` is pinned to the
clock his charts actually use.

---

## C4 — Correlation check (DXY / Yen basket / Gold Spread) — class A, mode contradictory

**He says (hard veto):** *"If both dollar and yen are moving in the same direction
with high volume, I should not be taking a trade."* Gold Spread: *"You see the
consolidation on Gold simply because we have Gold Spread and DXY both moving in the
same direction."* Required in some videos, optional in others; he took a Gold long
against DXY and said afterwards he should have waited.

**Never specified:** what "moving" means (lookback, magnitude), how inverse is
inverse enough, which instruments form "the yen basket", and what "Gold Spread" is.
**Do not guess the Gold Spread ticker — identify the instrument first or leave F6
uncoded and say so.**

**Candidate formalisations (`corr_lookback_min` = L, default 30, sweep 10-60):**
1. **Sign check**: sign of DXY return over L opposite the intended trade direction ⇒
   pass. Cheapest, closest to how he talks.
2. **Rolling correlation**: corr(1m returns of instrument vs DXY over L) `<=
   -corr_min` (default 0.3, sweep 0.1-0.6).
3. **Veto-only**: block iff DXY and JPY-basket returns share sign AND both
   `|z| >= corr_veto_z` (default 1.0, sweep 0.5-2.0) — the literal quote, nothing
   more.
Mode switch `corr_mode ∈ {off, veto_only, required}` encodes the contradiction;
default `veto_only` because the veto is the only version he states as a hard rule.

**Standalone edge:** expectancy of signals passing vs failing each mode, matched on
C2 magnitude.

**Falsified if:** pass/fail expectancy is indistinguishable in every mode and
lookback — the correlation layer is decoration.

---

## C5 — AOI touch — class A for existence, class D for construction

**He says:** the overextension pushes *"beyond structure"* into a 1H/4H/daily area of
interest — prior highs/lows or all-time highs.

**Never specified:** how a level is chosen. No construction rule exists anywhere in
the extracted material.

**Candidate formalisations (proximity band `aoi_proximity_atr`, default 0.25 x
ATR(1h,24), sweep 0.10-0.50):**
1. **Calendar extremes**: prior day / prior week / session highs-lows.
2. **Swing pivots**: k-bar fractal pivots on 1H and 4H (`pivot_k` default 3, sweep
   2-5), optionally untested-only (touch count 0 since formation).
3. **Beyond-structure binary**: price beyond the prior N-day extreme (N default 5,
   sweep 3-20) — the strongest reading of "beyond structure", ATH as limiting case.

**Standalone edge:** reversal quality with vs without AOI proximity, matched on C2
magnitude and time-of-day.

**Falsified if:** no construction x band beats the no-AOI baseline — then "AOI" as
he uses it is unfalsifiable as stated and mechanically empty; the skill's gap section
already predicts this is possible.

---

## C6 — Type 3 shift (the trigger) — class A, best-defined concept in the corpus

**He says:** sweep-then-break — price takes out a high and then breaks the low (or
mirror); a shift is a **W-shape swing break**, a change of character is a **V-shape
minor break** and is a no-trade: *"if we were to enter here on the break, it would be
a pretty big stop loss... it wouldn't technically be a shift, it would be more of a
change of character."* Trigger chart: *"I mainly use the 5 second chart for fractal
shifts"*.

**Never specified:** the swing definition (what qualifies as the high that gets swept
and the low that breaks), sweep depth, completion window, and the W-vs-V
discrimination threshold.

**Candidate formalisations (on `trigger_tf`, default 1m — 5s if data exists):**
1. **Fractal sweep-break**: swing = `pivot_k`-bar pivot; short signal when a bar
   trades above the last swing high by `>= sweep_min_ticks` (default 1, sweep 0-2 x
   tick) and price then closes below the last swing low within `shift_window_bars`
   (default 10, sweep 3-20).
2. **W-required**: formalisation 1 plus an intervening pullback pivot between sweep
   and break (for shorts: swept high → pullback low → lower high → break of pullback
   low). `shift_shape ∈ {W_required, any_break}`; default W_required. `any_break`
   deliberately includes his invalid V-pattern so his distinction is testable.
3. **Stop-size discriminator (his own tell)**: pattern valid only if implied stop
   (entry to pattern extreme) `<= stop_atr_max * ATR(trigger_tf, 20)`; default 2.5,
   sweep 1-4. This encodes "it would be a pretty big stop loss" as the V-detector.

**Standalone edge:** trigger-only backtest (all context gates off) vs trigger inside
gates; and the direct comparison W_required vs any_break vs V-only.

**Falsified if:** (a) W and V populations have indistinguishable outcomes — his
single sharpest stated distinction carries no edge; or (b) trigger-only expectancy
<= 0 everywhere and gating never rescues it — the trigger is noise.

---

## C7 — Shift within a shift (nested) — class A for existence, class D for definition

**He says:** *"a shift within a shift"* — his higher-confidence variant.

**Never specified:** what nests in what — timeframes, containment window, whether the
inner shift must complete inside the outer leg.

**Candidate formalisation:** outer shift on `trigger_tf`; inner shift (same
definition) on the next finer available TF, completing within the outer shift's
retrace leg (between sweep extreme and break level) within `nest_window_bars`
(default = outer `shift_window_bars`). Binary confidence tier `nested ∈ {0,1}`; not a
gate by default — a label.

**Standalone edge:** nested vs plain shift expectancy, same context.

**Falsified if:** no difference — the confidence tier is noise and should not exist
in the config.

---

## C8 — Candle flip (30m/15m confirmation) — class D, thinnest concept

**He says:** nothing quotable. The concept appears only in his timeframe stack
(30m/15m listed for candle-flip confirmation and exit reference) — no definition was
ever spoken.

**Never specified:** everything. There is no definition to formalise faithfully.

**Candidate formalisations (explicitly researcher-invented, flagged as such):**
1. Prior completed 15m candle closes against the drive direction before the trigger.
2. Same on 30m.
3. Engulfing variant: that candle's body engulfs the previous body.

`candle_flip_gate` default **off** — evidence class D items do not gate by default.
If Phase 1 re-extraction produces a definition, replace these candidates with his.

**Standalone edge:** as a toggled gate vs off, matched populations.

**Falsified if:** it does not improve matched expectancy — delete it — with class D evidence the bar for keeping it is higher, not
lower.

---

## C9 — Volume behaviour — class A in three roles, thresholds unstated

**He says:** the drive comes *"with high volume"* [C2]; exits when *"volume started
to decrease"* [X5]; the correlation veto requires "high volume" [F5]; and an
instrument can be disqualified as *"just low volume kind of shit, rangy"* [F9].

**Never specified:** baseline, lookback, threshold — and spot volume is tick volume.

**Candidate formalisations:**
1. **Entry-side (in C2.3)**: hour-so-far volume z vs same-hour-of-day baseline over
   `vol_baseline_days` (default 20, sweep 10-60) `>= oe_volume_z_min`.
2. **Exit-side (X5 mechanisation)**: rolling 5m volume slope < 0 for
   `vol_fade_bars` (default 3, sweep 2-6) consecutive bars after the trade is `>=
   vol_fade_min_r` (default 0.5R, sweep 0-1R) in profit ⇒ exit. This is a candidate
   mechanisation of a behaviour he performs discretionarily — label it as such in
   every report.
3. **Instrument floor (F9)**: skip instrument-days below `adv_percentile_min`
   (default 20th percentile of trailing 60-day tick volume, sweep 10-40).

**Standalone edge:** each role separately: (1) as C2 component ablation; (2) exit
rule vs hold-to-target on the same entries; (3) instrument-day filter on/off.

**Falsified if:** (2) especially — if the volume-fade exit does not beat
hold-to-target [X3] on expectancy or drawdown, the discretionary exit either isn't
volume-driven or isn't mechanisable this way; report which.

---

## X1-X5 — Execution mechanics

**X1 Entry — class A.** *"Took the entry at the break of the candle low targeting
that 50%."* Entry = stop order at break of the trigger-TF candle low/high following a
retrace into `entry_retrace_frac` (default 0.50, sweep 0.38-0.62) of the shift leg.
Ambiguity: whether the retrace is required or typical — `entry_retrace_required ∈
{yes, no}`, default no (he says "typically").

**X2 Stop — class A placement, class B size.** Beyond the local swing/wick that
formed the shift, or tight above the 50% zone; *one note gives 15-20 pips* (class B —
unverified number; also pips is an FX unit, re-derive per instrument). Params:
`stop_mode ∈ {pattern_extreme, retrace_zone}` default pattern_extreme;
`stop_buffer_ticks` default 1, sweep 0-3.

**X3 Target — class A, strongest rule in corpus (7 videos).** *"Normally I do target
50% of the previous move, but sometimes I can be a pussy and target less."* Fixed
`target_impulse_frac` = 0.50 of the prior impulse. The ambiguity is the impulse:
`impulse_def ∈ {hour_open_to_extreme, last_pivot_leg(pivot_k), day_extreme_leg}` —
ablate the definition, not the fraction. Gold override [class A]: `gold_rr_override`
1.0-1.5R with increased size — *"around 1 1.5 risk to reward trades"*; sizing and
target are coupled, never sweep independently without flagging.

**X4 Trail — class A.** *"I trail my stop loss when we break a high in my favour."*
Trail to prior pivot on each new `pivot_k` swing in favour. Ambiguity: trail TF
unstated — `trail_tf ∈ {trigger_tf, 1m, 5m}`, default trigger_tf. (The repo's exit
work elsewhere shows trail-TF choice can dominate results; treat this parameter as
load-bearing.)

**X5 Discretionary exit — class A behaviour, no rule.** *"once we took out this low
around here the previous 15 minute candle low I was looking for an exit, volume
started to decrease."* Mechanised candidate = C9.2. The honest framing: X5 is the
judge-layer candidate. Backtests run {X3 only}, {X3 + C9.2}, and report both;
neither is "his exit", because his exit is discretionary.

Scale-ins — class B: second position at 40-60% of initial, later re-entries at 25%.
Quotes live in the corpus, not audit v1; implement behind `scaling_enabled` default
off until re-attached.

---

## F1-F9 — filter mapping

Every filter from SKILL.md's table maps onto the machinery above: F1→C1 (instrument
regime), F2→`setup_recency_hours` (a prior C6-in-gates signal within 4-5h, default
4.5 sweep 3-6 — note self-reference: needs the detector to define "setup seen"),
F3/F4→C3 boundaries, F5→C4 veto, F6→C4 Gold-Spread leg (uncodable until the
instrument is identified — leave off and say so), F7→"clean entry model" =
discretionary, mechanised only as C6 validity (flag the gap), F8→C6 shape
discriminator, F9→C9.3.

## Reporting requirements (inherited, non-negotiable)

Per-confluence ablations with signal count, hit rate, expectancy, and delta-from-
removal; rank by contribution; recommend the minimal surviving subset; say plainly if
none survives. Quantify the take-every-signal vs skips-30-40% gap instead of papering
over it. Divergences from his claimed 81-88% are findings, not problems. Headline
population = C1-gated hours. All sweeps re-confirm on sealed holdout.
