# AMBIGUITIES — decisions taken while implementing SPEC.md blind

One entry per decision. Each quotes the governing spec text, states the readings available,
the reading taken, and why. Entries marked **[HIGH IMPACT]** are the ones most likely to
account for a divergence against the other implementation.

Four independent checks fell out of the build and are recorded first, because they pin
several of these decisions harder than argument could:

| check | spec says | this implementation |
|---|---|---|
| A13 NY σ̂ census, 7 rows (n = 6/10/20/30/35/50/90) | 9.23 / 11.12 / 16.00 / 19.48 / 20.91 / 24.69 / 30.10 | **identical to 0.01 on all seven**, over 537 sessions (A13 also says 537) |
| A10 fractal worked example, 2025-01-22 | 08:30 and 08:45 both print 21934.25; strict `>` falls back to 21905.00 at 06:15; A10 admits 08:30 and the flag becomes **uptrend** | 15m bars reproduce both prints and 21905.00 at 06:15; A10 rule admits 08:30; **flag at 09:50 = uptrend** |
| A5 "the 29.6% of triggers whose E1 entry falls on the wrong side of the wick extreme" | 29.6% | **29.54%** (18,154 of 61,457 triggers reaching that test) |
| A8 "completed bars behind the NY anchor at 09:50: 1m 20 · 2m 10 · 3m ~6 · 5m 4" | — | consistent only with **fixed grids anchored on 09:30**; the non-integer 3m count rules out rolling windows (see A-02) |

---

## A-01 — `signal_minute`: which minute is "the trigger bar's CLOSE"? **[HIGH IMPACT]**

> TASK.md: `"signal_minute": <int, ET minute-of-day of the trigger bar's CLOSE>`
> bars_api.py: *"Bars are OPEN-LABELLED at source: the bar stamped 09:47 covers 09:47:00-09:47:59."*

Three readings, for a TF-`k` bar whose slot is `[s, s+k-1]`:

1. **label** — `s` (the open minute)
2. **last constituent minute** — `s+k-1`, the minute during which the closing print occurs
3. **close timestamp** — `s+k`, the instant the bar completes

**Taken: reading 2.** The bars_api docstring says the 09:47 bar covers up to **09:47:59** — the
close therefore *occurs inside minute 09:47*, so the "ET minute-of-day of the close" of a 1m bar
is its own label, and reading 2 is the only one that generalises that to k>1. It is also the
direct expression `bars_api.minute_of_day(last_index_of_bar)`.

Reading 3 has a real argument on the other side: A8/A13's own convention labels an instant by the
clock time at which the preceding bars have completed ("at 09:50, 20 1m bars are complete", i.e.
bars 09:30–09:49). Under that house convention the 09:49 bar "closes at 09:50".

**Reading 3 is exactly reading 2 plus one, on every timeframe and every trade.** So if the two
implementations disagree by a uniform +1 on every `signal_minute` and agree on everything else,
this entry is the whole explanation and it should be adjudicated as one decision, not 1,583.

Reading 1 is ruled out for k>1 by the word CLOSE being emphasised at all.

## A-02 — entry-TF bar construction and grid anchor

> §1 *"Entry TFs: 1m, 2m, 3m, 5m."* — no aggregation rule stated.

Session index 930 (09:30 ET) is divisible by 1, 2, 3, 5 **and 15**, so a fixed grid anchored at
18:00 ET (index 0), at midnight ET, or at the 09:30 RTH open are all **the same grid**; that fork
does not exist. The live fork was fixed grid vs *rolling* k-minute windows recomputed every
minute. **Taken: fixed grid**, decided by A8's "completed bars behind the NY anchor at 09:50:
1m 20 · 2m 10 · **3m ~6** · 5m 4" — under rolling windows every timeframe would read 20, and the
`~` in front of 6 only makes sense for 20/3 on a fixed grid.

Bars are aggregated over the **whole Globex session from 18:00**, not just RTH, confirmed by A1's
open item (*"BB(20) and ATR(20) evaluated at 09:36 reach back into pre-open bars"*) and by A10's
worked example using 15m bars at 06:15 and 08:30.

Slots holding no 1-minute bar are skipped; a slot with a partial set is aggregated from what is
there (o = first present, h/l = extremes, c = last present). `signal_minute` always uses the
slot's **nominal** last index so signal minutes stay on a clean grid.

## A-03 — signal-window bounds

> §1/A1 *"Entry window: RTH 09:31–16:00 ET, entry blackout 09:31–09:35, first tradeable signal bar 09:36."*

**Taken: `576 <= signal_minute <= 959`** (09:36 … 15:59). The lower bound is A1 verbatim under
reading A-01.2. For the upper bound, RTH bars are those labelled 09:30…15:59 and the window
"ends at 16:00" is the close of the 15:59 bar; a trigger bar is required to lie inside RTH.
Under this bound all four timeframes share the same last signal minute (959) and the same first
grid, which is a mild independent argument for it. The alternative `<= 960` adds only bars that
begin after the cash close.

## A-04 — what "within proximity tolerance" makes a cluster **[HIGH IMPACT]**

> §3 *"Confluence cluster: ≥2 of {BB MA, NY VWAP middle/±1σ (post-9:30 only), daily VWAP middle/±1σ/±2σ/±3σ, daily POC} within proximity tolerance."*

Two standard readings: **single-linkage chaining** (consecutive sorted gap ≤ tol, yields a
partition, but a cluster can span far more than the tolerance) and **mutual proximity** (every
member within tol of every other, i.e. span ≤ tol, yields possibly-overlapping maximal windows).

**Taken: mutual proximity, maximal windows.** Under chaining, levels 30 points apart end up in
one "cluster" and are demonstrably *not* "within proximity tolerance" of each other, which
contradicts the sentence. Sensitivity to this fork is reported in NOTES.md.

Note this fork is largely invisible in the *output*: two clusters firing on the same bar and
timeframe in the same direction produce identical entry (BB MA), stop (wick extreme) and target
(ladder from entry), so §10.1(4)'s duplicate collapse merges them. That is also why tie-break
levels 3, 4 and 5 never fire here — matching A7's measurement exactly.

## A-05 — tolerance value

> §3 *"Tolerance: CALIBRATE (start ~10 NQ pts / 0.04%)."*

The two given forms disagree (0.04% of NQ ≈ 21,000 is 8.4 pts). **Taken: 10.00 points**, because
A13 pins it: *"1.95996 · σ̂ / √(2(n−1)) ≤ 5.00 points"* described as *"HALF the §3 cluster
tolerance"*. Recorded as a CALIBRATE start value used as given.

## A-06 — confluence minimum when the HTF flag is `range`

> §7 *"Confluence minimum: 3 counter-trend; 2 with-trend at reduced risk."*
> §4 *"Counter-trend raises confluence requirement (§8)."*

§7 names only two of the three flags §4 defines. **Taken: `range` requires 2.** §4 states the
relationship as counter-trend *raising* the requirement, which makes 2 the base and 3 the raised
case; `range` is not counter-trend. The alternative (only with-trend gets the relaxed 2) is
switchable as `OPT["range_conf"]`.

## A-07 — §7 invalidation: *which* ±1σ is "the opposing" one **[HIGH IMPACT]**

> §7 *"Invalidation-at-entry: trigger candle simultaneously touching the opposing ±1σ → stand down. [Hypothesis — test]"*

Two questions. **Which VWAP:** A8/A13 settle it — *"the σ bands ... may not serve as the §7
invalidation reference"* is said of the **NY** VWAP bands, so §7's reference is the NY ±1σ.
**Which sign:** taken as the band the trade is heading *into* (+1σ for a long, −1σ for a short),
on the strength of §6 rule 1 using "opposing" in exactly that sense — *"List **opposing**
structural levels **beyond entry**"*. Buying into overhead resistance is also the reading that
makes "stand down" mean something. Switchable as `OPT["invalidation"]`.

Kept as a live gate despite the `[Hypothesis — test]` tag, because A8 and A13 both describe it as
an operative rule whose *reference level* they are restricting; a rule that did not run would not
need its reference restricting. It rejects 24,837 triggers (28.8% of those reaching it), which is
large — the NY σ bands are eligible on ~71% of RTH minutes.

## A-08 — front-run F: *"start 2–3 NQ pts"* is a range, not a value **[HIGH IMPACT]**

> §6.4 *"working target = level ∓ F points (level minus F for longs). F: CALIBRATE (start 2–3 NQ pts)."*

**Taken: F = 2.5**, the midpoint, as the only neutral single value. F = 2.0 and F = 3.0 are equally
defensible; both are measured in NOTES.md. F shifts every reported `target` by the difference and
can change which ladder rung first clears the floor.

## A-09 — T_cancel is CALIBRATE with **no** start value

> §5.5 *"No fill → no chase. Order cancels if price runs T_cancel points beyond entry without filling. T_cancel: CALIBRATE."*

TASK.md instructs using the start value "where the spec ... gives a start value". §5.5 gives none.
**Taken: the cancel rule is DISABLED**, following A2's explicit precedent for an under-specified
rule (*"volatility stand-down = DISABLED for v1 [FIAT, §7 was marked OPEN with no definition]"*)
and A9's doctrine (*"A rule nobody can state is not a filter; it is a free parameter with a gate's
authority"*). Inventing a number would have been the larger sin.

**Consequence, recorded rather than hidden:** a working order therefore lives until the entry
window closes. Fill latency is 1 minute for 918 of 1,583 trades and ≤ 5 minutes for 1,251, but
**120 trades (7.6%) fill more than 30 minutes after their signal**, and those are exactly the
stale fills §5.5 exists to prevent. Any T_cancel would remove some of them.

## A-10 — fill accounting for the entry limit **[HIGH IMPACT]**

> TASK.md: *"`entry` is the price the trade actually fills at under the spec's accounting, not the intended limit."*
> §6.4 (the only fill-accounting sentence in the spec): *"Backtest counts target touched-minus-F as filled."*

**Taken: standard limit accounting — if a bar opens through the limit the fill is the (better)
open, otherwise the fill is the limit itself.** TASK.md's explicit "not the intended limit" is
otherwise inert, since a touch-fills-at-the-limit convention would make entry ≡ limit always.

This is not a rare correction: **302 of 1,583 fills (19.1%) beat the limit, median 7.52 pts.**
All 302 occur on the very next bar, and 284 of them are cases where the BB MA sits on the *far*
side of the trigger close, i.e. the E1 limit is already marketable when placed. That is a real
property of the spec, not of this implementation: §5.3 E1 says *"limit at the BB MA"* with no
requirement that the BB MA belong to the firing cluster, and A5 calls the pairing *"degenerate at
both ends"* — one end being the 29.6% wrong-side cases it declines to rescue, the other being
exactly these.

## A-11 — stop and target are computed from the **limit**, not from the fill

> §5.4/A5 *"Effective stop = max(structural stop, 10.00 pt). **The floor applies at order placement only**; once placed the stop is never widened."*

Decisive: at order placement the fill price is not yet known, so the floor — and therefore the
stop price, and therefore R, and therefore the §6.5 target ladder and the RR-floor admission test
— are all evaluated against the intended limit. **Taken: stop and target fixed at placement from
the limit; `entry` reports the fill.**

Consequence: on the 19.1% of trades that fill better than the limit, `|entry − stop|` is *not*
10.00 pt and can be as low as 0.75. That is arithmetically implied by A5's own wording and is
recorded, not smoothed over. The alternative (re-derive the bracket from the fill) would make the
pre-trade RR-floor gate and the post-fill geometry disagree instead.

## A-12 — Vault occupancy: what blocks, and what consumes the 3/session cap **[HIGH IMPACT]**

> §10.1 header: *"The Vault admits **at most one candidate at a time**, in signal-time order."*
> §10.1(2): *"**While a position is open**, later candidates are NOT admitted and are NOT queued."*
> §10.1(3): *"At most **3** candidates are admitted per session."*

The header and (2) differ on whether a *working, unfilled order* holds the slot, and (3) does not
say whether an admission that never fills burns a cap slot.

**Taken:** candidates are walked in ascending signal index with `busy_until` = the exit index of
the last *filled* trade. A candidate is discarded if `signal_index <= busy_until`; otherwise, if
fewer than 3 trades have filled, its order is simulated. A candidate whose order never fills
produces nothing, holds nothing and burns no cap slot.

Two properties this buys, both of which the spec demands:
* **no overlap is possible** — a fill is always strictly after its own signal, which is strictly
  after the previous exit, so §5.6's *"No overlapping trades ever"* holds by construction;
* an order that is still working when a later candidate fires *does* block that candidate
  (because `busy_until` is set from the eventual exit), which is the header's "one candidate at a
  time" — while a candidate that never fills cannot deadlock the rest of the session, which the
  header taken literally would allow.

The cap counting fills rather than admissions is chosen because A7 and A9 tabulate the capped
quantity as "**ADMITTED trades** / session" at 2.33–2.90 against a cap of 3.

## A-13 — target menu: which entries are computable **[HIGH IMPACT]**

> §6 *"Menu: VWAP middle; VWAP ±1σ/±2σ; POC; session extremes (Asia/London/pre-market); data extremes; prior-day H/L; weekly H/L; pullback origin (B2); HTF range extremes."*

**Included** (no invented constant needed): daily VWAP mid/±1σ/±2σ; NY VWAP mid/±1σ/±2σ; session
POC; prior-day high/low (= the preceding Globex session, which this data model makes exact);
prior-week high/low (preceding ISO week of session_end_date).

**Excluded, each for a stated reason:**
* *session extremes (Asia/London/pre-market)* — §2 names the boxes but the spec nowhere states
  their ET boundaries, and the common conventions differ by hours. A9's doctrine applies.
* *data extremes* — A13: *"The project holds no economic calendar."* Also kills §6 rule 3.
* *pullback origin (B2)* — A4: *"The A/B/B2 taxonomy of §4 is not implemented in the detector at all."*
* *HTF range extremes* — §1 assigns these to 1h/4h and states *"The 4h/1h range is RECORDED, NOT
  GATED ON"*; no lookback window for "the range" is ever defined.

Note the menu is listed under "VWAP ±1σ/±2σ" only — daily ±3σ is a §3 cluster level but **not** a
§6 target. Implemented as written.

Because A4 makes the target *the nearest rung clearing the floor*, menu membership moves targets
monotonically: a shorter menu can only push targets further out. This is the single most likely
source of `target` divergence after A-08.

## A-14 — does A13's ineligibility also bar NY σ bands from being *targets*?

> A13/§2.1 *"Below that the NY **mid** is usable and the **σ bands are not**: they may not enter a cluster (§3) and may not serve as the §7 invalidation reference."*

The general clause says "are not usable"; the colon then enumerates exactly two prohibitions,
neither of which is §6. **Taken: the restriction binds cluster membership and the §7 invalidation
only; NY σ bands remain in the §6 target menu.** The enumeration is not exhaustive of the bands'
uses (§3's over-extension test is also unlisted), so it reads as the operative specification
rather than as a gloss. The opposite reading is tenable and would push some targets outward.

## A-15 — A13's criterion carries no band multiple

> A13: *"eligible(σ̂, n) ⟺ 1.95996 · σ̂ / √(2(n−1)) ≤ 5.00"*

The stated quantity is the CI on *the ±1σ band's* distance from the mid; the ±2σ band's distance
is 2σ̂ and its CI half-width would be twice as wide. The formula as written has no k.
**Taken: one eligibility flag for all NY σ bands, exactly as written.** In practice only ±1σ is a
§3 cluster level and only ±1σ is the §7 reference, so this bites only through A-14.

`n` is the count of 1-minute bars from the 09:30 anchor **through the trigger bar inclusive**.
This is the same convention A13's own census table uses (its "n=30 / 10:00" row is bars
09:30–09:59), and reproducing that table to 0.01 on all seven rows confirms it.

## A-16 — ATR(20) smoothing

> §3 *"Optional size floor range ≥ k×ATR(20)"* — no smoothing convention given.

**Taken: simple mean of the last 20 true ranges.** The spec's house convention for a 20-period
average is SMA (§2 table: *"Bollinger Bands | 20, SMA, close, 2σ"*), and no Wilder/RMA seeding
rule is stated anywhere. Wilder's is switchable as `OPT["atr"]`; sensitivity in NOTES.md.

## A-17 — is the ATR size floor on?

> §3 *"**Optional** size floor range ≥ k×ATR(20): CALIBRATE (start k=1.0)."*

"Optional" pulls one way; a stated CALIBRATE start value pulls the other, and TASK.md says to use
start values where given. **Taken: ENABLED at k = 1.0**, decided by A1's open item, which lists
*"BB(20) **and ATR(20)** evaluated at 09:36"* among the quantities the detector actually computes
on the first tradeable bars. It applies to displacement only, which is where §3 puts it.

## A-18 — volume profile construction

> §2 *"Volume profile | Session + daily ... POC, VAH/VAL, HVN/LVN"*; A2 *"volume-profile bin = 1.00 pt"*; A8 *"The volume profile likewise uses 1-minute bars."*

Bin size, feed and anchor are given; the *distribution rule* is not. **Taken: each 1-minute bar's
volume spread uniformly across the 1.00-pt bins its [low, high] spans**, which is what a volume
profile built from OHLCV normally means; the alternative (all volume at the bar's typical price)
would make the profile a histogram of typical prices instead. POC is reported at the **bin
midpoint** (`floor(p) + 0.5`); ties go to the **lowest bin** for determinism. In this data model
the Globex session *is* the day, so "session profile" and "daily POC" (§3) are the same object,
accumulated from index 0 to the trigger bar.

## A-19 — the exact geometry of a rejection block

> §3 *"entry-TF candle that (a) trades into the cluster, (b) CLOSES back on the trade side of all cluster levels, (c) leaves a wick through/into them."*

**Taken**, for a long against a cluster spanning `[lmin, lmax]`, with `body_low = min(o,c)`:
`low <= lmax` (a) **and** `close > lmax` (b, "all cluster levels") **and** `low < body_low`
(a wick exists) **and** `body_low >= lmin` (c, the wick — not the body — is what penetrated).
Mirrored for shorts. The last condition is what "**a wick** through/into them" adds beyond (a):
if the body's own low is below the whole cluster, the wick lies entirely below the cluster and
penetrates nothing. This is corroborated indirectly: the wrong-side rate it produces is 29.54%
against A5's 29.6%.

## A-20 — displacement: "body closes through ≥2 cluster levels"

**Taken:** the candle must be in the trade's direction (`close > open` for a long) and a level
counts as crossed when `open < level < close` (strict both sides; mirrored for shorts). Strictness
matters only for a level exactly at the open or the close, which is essentially unreachable for a
VWAP level and rare for a 1.00-pt-binned POC. Body/range uses `|close − open| / (high − low)` and
requires `high > low`. "Extreme quartile" is `close >= low + 0.75·range` for longs.

## A-21 — "wrong side of the wick extreme"

> A5 *"A trigger whose E1 entry falls on the wrong side of the wick extreme remains invalid — the floor does not rescue it."*

**Taken:** invalid unless `entry > low` for a long / `entry < high` for a short — compared against
the **wick extreme itself**, not the buffered structural stop. Equality is treated as invalid
(an entry exactly on the extreme carries no structural stop distance at all); it is unreachable in
practice. Rate produced: 29.54% vs A5's stated 29.6%.

## A-22 — HTF fractal series scope

> A2 *"HTF classification = 15m fractal swings N=2, HH+HL ⇒ uptrend / LH+LL ⇒ downtrend / else range."*

**Taken: the 15m series is session-local**, built from index 0 (18:00 ET) of the session being
processed, with no carry-over from the previous session. A10's worked example is entirely inside
one session (06:15 and 08:30 on 2025-01-22) and reproduces exactly under this scope. A swing is
usable only once bar `i+N` has completed, i.e. from 1-minute index `last(i+N)`. Trend uses the
last two confirmed highs and the last two confirmed lows; fewer than two of either ⇒ `range`.

This is *not* the same object as A9's `range_pos_swing`, whose quoted 1,733-point width on
2025-01-22 cannot come from a single session. A9 makes that a recorded covariate and gates on
nothing, and TASK.md's output schema has no column for it, so it is not computed here.

## A-23 — §6 rules the amendments leave unimplemented

Rule 2's pattern-conditioned defaults are **not** implemented — A4 states plainly that they
*"remain unimplemented and ambiguous ... **Open, needs Angus**"* and that the A/B/B2 taxonomy is
*"not implemented in the detector at all"*. Rule 3 (news-day override) is unimplementable without
a calendar (A13). Rule 6 (alignment bonus) is a *"prefer"* with no rule attached and is
contradicted by A4's "take the **first** level that clears the floor"; not implemented.
Target selection is therefore rule 1 + rule 4 + rule 5-as-amended, only.

## A-24 — out of scope by TASK.md, implemented as no-ops

§8 management variants (V0/V1/V2/V4) — TASK.md forbids computing outcomes. §9 sizing/conviction —
no output column. §10.2 daily halt after 2 losses / −2R — **requires outcomes**, so it cannot be
applied without violating TASK.md; not applied. A9's `range_pos_swing` / `range_pos_blocks` and
A11's `entry_tf_1m` boolean are output-only fields the JSON schema does not carry (`entry_tf`
already records 1m). §7 volatility stand-down: DISABLED per A2.

## A-25 — tie-break order, and duplicate collapse

> §10.1(4) *"Applied in order; the first level that separates them decides."*

**Taken literally:** level 1 (highest entry TF) runs first, and level 2 (long+short ⇒ stand down)
only arbitrates among candidates that *share* the top timeframe. A7's measured split (level 1
resolves 15.7–19.1% of admissions, level 2 fires on 0.2%) only makes sense in that order.
Duplicates are collapsed *before* tie-breaking, on `(entry_tf, direction, entry, stop, target)`
per §10.1(4). Levels 3, 4 and 5 are implemented and, exactly as A7 reports, **never fire** (0 of
6,917 ties here; 6,702 resolved at level 1, 215 stood down at level 2).

## A-26 — exit simulation (used **only** to release the one-position lock)

No outcome is recorded anywhere. For lock purposes a position ends on the first 1-minute bar
whose range reaches the stop or the target, **stop checked first** when a single bar spans both,
scanning from the fill bar inclusive; otherwise it is forced out at the §1 EOD flatten
(15:55 ET). Both conventions affect only *when the next candidate becomes eligible*.

## A-27 — the P3 hint cannot be reconciled with any bar grid

> A13 *"`2025-01-29 10:20` remains an admitted trade on 2m/3m/5m."*

Recorded because it looks like a checkable fact and is not. Under a fixed grid, 2m, 3m and 5m
bars share a boundary only every 30 minutes from 09:30 — at 09:59/10:29/10:59 under reading
A-01.2, and at 10:00/10:30/11:00 under readings A-01.1 and A-01.3. **10:20 is not one under any of
the three.** So "10:20" must be the wall-clock *parity instant* (as "2025-01-22 09:50" is for P2),
not a signal minute. It does not discriminate A-01, and no attempt was made to bend the grid to
fit it. For the record, this implementation's nearest qualified candidates on 2025-01-29 are
10:19 (2m long), 10:21 (2m long) and 10:22 (1m long), with a 3m at 10:11.

## A-28 — minor readings taken without much doubt, listed for completeness

* Only the **BB basis** is a §3 cluster level; §2's ±2σ bands are computed but are not levels,
  since §3's set names *"BB MA"*.
* **Confluence count** counts distinct *types* (§3: *"VWAP family ×1, BB ×1, POC ×1, structural
  ×1"*), so all VWAP levels in a cluster count once; "structural" has no computable definition in
  the spec, so the attainable maximum is 3.
* **VWAP σ** is the volume-weighted population SD of HLC/3 about the VWAP
  (`Σv·tp²/Σv − vwap²`) — confirmed exactly by the A13 census reproduction.
* **Stop buffer** 1 tick = 0.25 (A2; tick size implied by A5's *"10.00 points (40 ticks)"*).
* **RR floor = 1.5** — marked CALIBRATE but stated as 1.5R throughout §6.5 and confirmed by A5's
  *"the minimum target distance becomes 15.00 pts (10.00 × 1.5)"*.
* **CALIBRATE start values used as given:** cluster tolerance 10.00, B_min 0.6, ATR k 1.0,
  RR floor 1.5, F 2.5 (see A-08), session cap 3.
* Sessions are processed **only** for `session_end_date <= 2025-01-31` (539 of the 796 the store
  holds), asserted in `process_session`. Sessions after that date are never read; earlier
  sessions are read only for prior-day / prior-week highs and lows.
