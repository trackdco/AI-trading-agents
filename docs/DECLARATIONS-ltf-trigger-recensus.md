# DECLARATION — LTF TRIGGER RE-CENSUS (the conjunction), declared before any row is built

Written 2026-08-07. **Nothing has been built or measured under this
design.** Holdout look #1 remains HALTED and unspent; no sealed row has
been read.

## Why everything downstream of the trigger is being rebuilt

The programme fixed the trigger candle at 15m. That came from the original
census spec and was re-defended in the E1 declaration on "comparability
with the incumbent" — which is a reason to keep a convention, not a reason
to believe it. The trader's recorded grammar is an LTF candle (1m in setup
6, 2m in setups 1 and 7), and the consequence is not cosmetic:

- **Flow has never been tested, only attenuated.** `flow_features`
  computes delta over `[bar_start, bar_end)`. At 15m that pools the
  approach, the failed pokes and the break itself into one number —
  signal-to-noise ~1:15 around an event that occupies one minute. At a 1m
  trigger the decision bar IS the event minute. `thru_delta_conf` was the
  near-miss: the final minute of an arbitrary 15m window, not the minute
  the level was crossed.
- **Depth was sampled at the wrong moment.** A book snapshot at a 15m
  close is up to fifteen minutes from the break, against an MBP-10 book
  that reaches 2.25pt. At 1m it is at most one minute stale. The
  wall-quality inversion (BR-20) and the six null depth features (BR-21)
  were measured at a moment unrelated to the event.

**Invalidated pending re-measurement:** S1, CONCORD (BR-19), the
wall-quality cut (BR-20), the depth six (BR-21), in-trade (BR-22), the
MFE-in-R table, the 75%-at-3R partial placement, the per-session books
(BR-23/24), the risk spine (BR-25), the per-session selection table
(BR-26), sweep_b (BR-15 — its 8-bar lookback is 15m-bar-based), and the
locus ranking (BR-11/12). **Plausibly surviving:** BR-1..BR-4 (level-touch
base rates and the scale law — not trigger-candle constructs) and
CONSTRAINT-mbp10-reach (a fact about the feed).

---

## D1 — THE TRIGGER IS A CONJUNCTION (corrected)

The locus set is **UNCHANGED**: 15m BB MA, VAL, VAH, VWAP, VWAP−1,
VWAP+1, POC. Only the **trigger candle** changes.

**VAH is retained** — all seven loci run, VAH included. It was the weakest,
symmetry-only cell all-session and it earned no follow-up in the 15m
per-session re-census, but it is not dropped: the publication rule requires
every cell, nulls included. **The 15m-only POC/VAH per-session census run
two turns ago is SUPERSEDED by this pass, not abandoned** — its results are
on the record (POC-reject London +0.419 vs +0.084 pooled, H1 clears and H2
does not; VAH-reject NY_PRE +0.470, same pattern; twelve cells, twelve
parks) and every one of them is re-measured here at all four TFs.

**An LTF BB MA is NOT a locus.** Censusing bbma1 as a locus would test
rejections of the 1-minute Bollinger middle band — a fast line price
crosses constantly — and generate a mountain of meaningless triggers. The
LTF BB MA is **momentum confirmation on the entry candle**, a different
object.

Setup 6 is the explicit form: price retested the **15m BB MA**, rejected
**POC**, then closed through the **1m BB MA** — market order there.

**Trigger, at timeframe TF ∈ {1, 2, 3, 5} minutes:**

> **(A) LOCUS CONDITION** — the TF candle interacts with locus L by the
> existing grammar: REJECT = the candle reaches L intrabar and closes back
> on the approach side; BREAK = the candle closes through L, after ≥1
> prior attempt in the same cycle.
>
> **AND**
>
> **(B) MOMENTUM CONDITION** — that same TF candle **closes through its
> own TF BB(20) middle band in the trade direction**.

Both must hold on the same candle. **The 15m census only ever had (A).**
Condition (B) is a momentum filter that has never been measured and is
plausibly where a large part of the trader's selectivity lives.

Entry: next 1m open (unchanged, entry-price gate enforced). Stop: the
trigger candle's extreme ± 1 tick — which at 1m is ~3–5pt rather than
~10pt, and that is the point.

Reported alongside every row: **(A)-only** and **(A)∧(B)** populations, so
condition (B)'s contribution is measured, not assumed.

### D1a — THE BAR FOR (B)'s MARGINAL CONTRIBUTION, declared before either population is read

Reporting (A)-only and (A)∧(B) each clearing its own bar **does not answer
the question**. Both can pass while (B) contributes nothing — the same
failure mode as closeloc validating itself while saying nothing about S1's
marginal value. The comparison is therefore declared directly, now:

(A)∧(B) is a strict subset of (A), so (B) is a **gate on the (A)
population** and is priced by the standing gate arithmetic:

> q = share of (A) rows that FAIL (B) · μ_fail = their mean out_ship
> **marginal lift of (B) = q · (EV_A − μ_fail) / (1 − q)**

**Declared bar for (B):** marginal lift **≥ +0.05R** (the programme's
standing Law-7 gate bar), with the **day-boot CI on the lift clear of zero
in BOTH eras**, at the declared X, per session and per TF. Dual currency
reported alongside (Law 3): win-rate of the kept vs failed sets, since a
momentum filter is exactly the kind of variable that can buy hit rate and
sell expectancy — which is how BR-20 died.

If (A)-only and (A)∧(B) both clear their own bars but the marginal lift
misses, the verdict recorded is **"(B) adds nothing"**, and the shipped
trigger stays (A)-only.

## D2 — W15 REMAINS THE SCALE RULER, and the reason is stated

W = the 15m BB band width, for every TF. **Reason:** W15 is what BR-4
validated as era-stable (adverse-before-touch 0.43–0.44W across eras in W
units and NOT in points). A 1m band width has **no established
era-stability**, and a per-TF W would make the 0.5W fight criterion a
different physical distance at each timeframe — which defeats the purpose
of comparable books. Stop-width is reported under **both** rulers (in W15
and in points) so the change is visible.

## D3 — TRIGGER TIMEFRAME IS A REPORTED DIMENSION, NOT A SELECTED PARAMETER

All four of {1, 2, 3, 5} are declared now and **all four are reported**,
per session, per locus, both arms. TF is never chosen.

**Cell count, up front: 4 TF × 3 sessions × 7 loci × 2 arms = 168 cells.**
That multiplicity is stated before any number exists, not discovered
afterwards.

- A **single-TF claim** (an effect present at one TF only) requires its
  **own confirmation** — split-half then holdout/forward — and is never
  read off this pass.
- A **pooled verdict** across TFs requires **sign agreement across all
  four TFs** in addition to the E1.4 bar (both-era day-boot CI clear of
  zero at the declared X, sign positive at ≥3 of 4 X values).

**Recorded:** the union across TFs is what the trader actually trades
("whichever looks cleanest"). Deferring the union this pass is therefore
correct — a cross-TF union requires a declared dedup rule, because the
same move fires at 1m, then 2m, then 3m, then 5m within minutes. **The
union with a declared dedup rule is the necessary next pass**, not an
optional one.

## D4 — THE FIGHT RULE IS RE-DERIVED PER (TF × SESSION)

X = 0.5W was a fallback adopted because a **pooled** valley procedure found
nothing. The structural fight rule carries far more weight at 1m than at
15m. The valley procedure is re-run per (TF, session) — 12 cells — and the
full X ∈ {0.25, 0.5, 1.0, 2.0}W sensitivity is reported per cell.

**A found valley overrides the X=0.5W fallback ONLY if it is present in
BOTH eras.** Otherwise a valley found on noise in one of twelve cells
becomes a tuned threshold, which is the failure mode this clause exists to
prevent.

## D5 — TRIGGER SEARCH IS WINDOW-RESTRICTED; LEVEL CONSTRUCTION IS NOT

Triggers are searched only in **LONDON 03:00–04:59**, **NY_PRE
08:00–09:29**, **NY_AM 09:30–10:30** NY. This is the correct population —
it is the book the trader trades — and not merely a compute saving.

**Level construction still runs from the FULL session, unchanged.** The
developing profile is 18:00-anchored, VWAP is session-anchored, and the
15m BB MA needs 20 prior completed 15m bars. Windowing the level
computation would silently change every level. Outcome walks likewise run
to session close, not to the window edge.

## D6 — COSTS ARE RE-PRICED IN R (this can eat the entire gain)

The programme prices **0.5pt per round trip inside the R numerator**. On a
~10pt 15m stop that is 5% of R. **On a 3–5pt LTF stop it is 10–17% of R** —
roughly **0.14R of drag per trade** against a London book at +0.357R. And a
1m market entry during a fast break may slip **more than one tick**.

Declared reporting, before any EV is believed:
- `cost_R = cost_pts / risk` distribution per TF (median, p75, p90).
- EV at **three** cost assumptions: **0.5pt** (current), **1.0pt**
  (slippage-inclusive stress), **1.5pt** (adverse-fill stress).
- **If costs eat the tighter-stop advantage, THAT IS THE FINDING** and it
  is reported as the headline, not as a footnote.

## D7 — TARGET-ADMISSIBILITY BECOMES A REPORTED COLUMN

With a 2–3× tighter stop, targets sit 2–3× further away **in R**, so the
ceiling rule matters for the first time. It is in the trader's grammar and
has never been in a spec.

Reported per row, **as a column, never as a filter this pass**: distance
to the next level ahead in R; whether a 5m or 60m BB MA ceiling sits
between entry and that level; and the fresh-permission flag (ceiling
broken within K ≤ 1 bar of its own timeframe, per the Census C finding
that a break grants passage for about one bar).

## THE PREDICTION, DECLARED BEFORE THE RUN

If the trader's grammar is right, expect:

1. **fights/day UP** — more short-timeframe candles close through a level
   than 15-minute ones;
2. **stop width DOWN 2–3×** (~10pt → ~3–5pt);
3. **the MFE-in-R table shifted substantially UP** (same excursion, smaller
   denominator);
4. **the partial relocated** away from 3R;
5. **flow markedly STRONGER**, now that it is aligned to the event minute.

**If flow does NOT strengthen at 1m, that is a real finding**: it says the
flow family is genuinely weak rather than mis-measured, and it closes a
question that has been open since the beginning. That outcome is recorded
as a result, not as a failed run.

## D8 — PRE-FLIGHT: RAW TRIGGER COUNTS BEFORE THE OUTCOME WALK

The outcome walk is the expensive stage (~100k rows × up to a full session
of 1m bars each). **Raw trigger counts per (TF, locus, arm, session) are
printed FIRST**, from the trigger scan alone, before a single outcome walk
runs. Five minutes against a long background run.

**Declared pathology criterion — halt and diagnose, do not proceed:**
- any cell implying **> 50 triggers/day**, or
- a 1m or 2m rate that is not a **sane multiple** of the 15m rate for the
  same cell (candles scale ~15× from 15m to 1m; triggers should scale
  **sub-linearly**, because reaching a locus and closing through one's own
  BB MA both get rarer per-candle as the candle shrinks). A super-linear
  jump is a bug, not a discovery.
- (A)∧(B) count exceeding (A) count anywhere — an impossibility that would
  indicate the conjunction is mis-wired.

Counts are reported whatever they show, and the calibration control runs in
the same stage: **the (A)-only path at TF=15 must reproduce the existing
level census bit-for-bit** before any new number is trusted.

## Gates and standing constraints

- **The entry-price gate must PASS at every TF** before any row is read.
- Publication rule unchanged: every cell published, nulls included, into
  BASE-RATES.md.
- Fit-only. Sealed rows written unread. **Holdout look #1 stays halted**
  until the locus set AND the trigger set are both closed.
- Flow venue unspent. Break-arm candidate sets still wait. Funded-layer
  work parked. Selection layers ship on fit + forward validation via the
  seven-locus recorder — which is built and replay-certified but **not
  deployed; deploying it to the VPS is the trader's action, not one I can
  perform.**
