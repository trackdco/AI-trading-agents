# PRE-REGISTRATION — NYA-LVL-01 — the level-interaction family, seeded with London 50

**Committed BEFORE any data is touched or scored.** Authorised by
`docs/BRIEF-london50-chat.md` (Angus, 2026-08-05). Source spec:
`research/transcripts/mrzincx/SPEC-as-taught.md` MODEL 3. Credibility file read:
`research/findings/intake2-credibility.md` — his 71–82% win-rate claims are
self-reported and unverified; **we test the mechanics and ignore the marketing.**

Stage 1 only: **build the raw uncapped trigger set on the fit span, then stop.**
No optimisation, no filters, no cuts, no verdict beyond the raw card.

---

## PLAIN LANGUAGE — what we are testing (for Angus)

There are six lines on the chart every day. Three come from the overnight/pre-market
session — its high, its low, and the halfway point between them. Three come from
yesterday — the same three. They are fixed and known before the market opens, so
nothing here is hindsight.

The claim is simple: **price keeps coming back to these six lines, and when it gets
there it usually bounces.** Whoever chased the move into the line is the one who gets
hurt. So the trade is: when price touches a line, take the other side for a small,
quick scalp.

That is it. He trades it dozens of times a day.

**What stage 1 does:** find every single one of those touches over 13 months, write
down what happened after each one, and hand you the raw numbers. **Nothing is filtered
and nothing is optimised.** The law says raw is expected to look ugly, and that ugly raw
does not kill anything (§5.9.1) — the canon itself looked bad at this stage. You read
the raw card and decide what happens next.

---

## Family identity

**ONE family, two layers**, per Angus 2026-08-05:

1. **The taught core (this run):** MrZincx's exact six levels and taught mechanics. This
   is the as-taught anchor required by §5.9.1.
2. **The substrate generalisation (declared here, run only after Angus reads the core
   card):** the same event grammar applied to further lookahead-clean reference levels.
   **Declared extension list, frozen now so it cannot grow later:** overnight 18:00–04:00
   ET high and low; prior RTH close (16:00 ET); prior-week high and low. **Five
   additional levels. No others without a new prereg.**

**Level TYPE is recorded on every event from birth** — Angus expects it to be the first
great discriminator.

## Mechanism

These six lines are the only structure that is both visible to everyone and fixed before
the session starts. Resting orders and stops cluster there because that is where
everyone can see to put them. Price is drawn to that liquidity, and the traders who
chased the move into it are the ones with no one left to sell to.

**The trapped counterparty is explicit:** whoever bought the push into the level, or
chased the breakout of it without waiting for a retest.

**Mechanism family:** structural events / level interaction (new vault family).

---

## The six levels — lookahead-clean, computed on NQ

| level | definition | fixed at |
|---|---|---|
| `PM_HIGH` | high of 04:00 → 09:15 ET | 09:15 ET same day |
| `PM_LOW` | low of 04:00 → 09:15 ET | 09:15 ET same day |
| `PM_50` | midpoint of the above | 09:15 ET same day |
| `PD_HIGH` | high of 04:00 → 20:00 ET **prior** day | prior 20:00 ET |
| `PD_LOW` | low of 04:00 → 20:00 ET **prior** day | prior 20:00 ET |
| `PD_50` | midpoint of the above | prior 20:00 ET |

**Declared spec translation (§5.12.15).** He charts **QQQ** extended hours and executes
**NQ**. We hold no QQQ data, so all six levels are computed on **NQ candles directly**.
A QQQ-derived variant is a future arm, not this run. This is a real deviation and it goes
in the card, not in a footnote — QQQ and NQ ranges are correlated but not identical, and
a level computed on the wrong instrument is a different level.

---

## Event grammar — every touch, uncapped

**UNCAPPED is the standing convention (Angus 2026-08-05):** every touch of every level,
sequential re-entries permitted, **no per-day cap, no trading-window cap**. Time of day
is a *recorded variable*, never a filter, at this stage.

**Touch window:** all of RTH, **09:30 → 16:00 ET**. His own habits (skip the opening
candle, stop around 11:00, skip the closing candle) are **arms to be tested later**, not
assumptions applied now.

**Touch (Version B, current teaching):** a 15-minute bar whose range contains the level.

**Fill model — §2.5, and it bites here.** *"Limit fills count only when price trades
THROUGH the level, never on a touch."* A touch entry is a resting limit at the level, so
it is recorded as filled **only if the bar trades at least one tick (0.25) beyond the
level**. A bar that reaches the level exactly and reverses is recorded as a touch with
`filled = False`. Both counts are reported; the economics use filled events only.

**Direction — fade, because that is the thesis.** The approach side is taken from the
prior 15-minute bar's close: closed **below** the level → price is arriving from
underneath → the level is resistance → **short**. Closed above → **long**. His 80/20
trend-side bias is a declared arm for a later stage, not applied here.

**Version A (original teaching) is a separate declared arm, run in the same pass:**
break of the level, then entry on the first 15-minute **body close** back at the level
(within 0.25× the level's own 15m ATR). Never picked silently against Version B — both
are censused and both are ledgered.

---

## Stop arms — both taught readings, both run

- **`S_LEVEL` (current teaching, the default):** exit on a 15-minute **close** beyond the
  traded level. He measures this at ≈ 16 NQ points.
- **`S_FAR` (original teaching):** exit on a 15-minute close beyond the **far extreme**
  of the range the level belongs to. 3–5× larger.

**Angus considers oversized stops disqualifying**, so realised stop distance in points is
reported per arm on the card, honestly, not buried. `S_FAR` is run because he taught it,
not because we expect it to survive.

## Target arms — he never defines one, so the house declares three

His words: *"whatever tickles your fancy."* Declared here, before any run:

- **`T_LADDER`** — his stated ladder: from `PM_50` target `PM_HIGH`/`PM_LOW`; from
  `PD_50` target `PD_HIGH`/`PD_LOW`; from an outer level, the next level beyond it.
- **`T_SCALP` = 16.0 NQ points fixed.** Derived, and the derivation is stated because it
  is a translation: his TopStep record shows avg win **$64.24**, and he trades 2 MNQ
  against a level, so ≈ 16 NQ points. It also equals his own stated ~16-point stop
  scale, making the scalp arm ≈ 1R against `S_LEVEL`.
- **`T_TIME` = 30 minutes.** From his own record: avg win 11 min, avg loss 24 min.

All three run on every event. **No arm is preferred at this stage** and none may be
promoted from this run — §6.0.1 forbids promotion by in-sample rank, always.

---

## Recorded per event (§5.12-5 schema from birth)

`level_type` (6) · `side` · `tap_number` at that level today · `clock` (ET) ·
`touch_granularity` (15m bar vs 1m precision) · `distance_from_rth_open` ·
`level_age_minutes` · `gap_context` (RTH open vs prior close) · `filled` (per the §2.5
fill rule) · `stop_distance_pts` per stop arm · outcome under **each** exit arm ·
**MFE / MAE** · checkpoints at **t+5 / t+15 / t+30** minutes.

**Tap counting is ambiguous in the source and gets two declared arms:** `tap_15m`
(15-minute bars only — the execution timeframe, the default) and `tap_1m` (any touch at
1-minute precision — his looser reading, since he says he watches 5- and 3-minute too).
Both recorded on every event; neither filters anything at this stage.

---

## Span

**FIT = 2025-06-02 → 2026-07-15 only** (§5.11-9a: the 13 months with candles, flow and
depth all present).

**OUT-OF-FIT = the six sealed 2023/24 months. NOT TOUCHED. Holdout look: NO.**

Depth coverage note for the later stage: the archive covers **08:00–10:29 ET**, which
overlaps both the level-formation window and his prime trading hours.

## Costs

Reported at **1.0 pt (base)** and **2.0 pt (strict)**, both always, matching the rest of
the programme so the numbers compare across families. Conservative intrabar: stop checked
before target within a bar.

## Accounting

Points and dollars at **$160 risk per trade** (1/risk sizing), the programme standard.
His own **2 MNQ / 1 MNQ** sizing ladder at `PM_50` vs the outer levels is recorded but
**not applied** — sizing is a later declared arm (§5.11-9b conviction sizing).

---

## What can and cannot happen at this stage

- **Nothing dies here.** §5.9.1 as tightened: no bin decision is ever made off the raw
  trigger set. A census kill needs *structural absence* — the levels never being touched.
  Given ~10–15 touches/day is the design intent, that outcome is not expected.
- **Nothing is promoted, selected or optimised.** No arm comparison beyond reporting all
  of them side by side.
- **Ugly raw is the expected result and is not a problem** (§5.9.1: "the canon would
  have died at raw triggers under any other rule").

## Kill criterion — the only one legal at this stage

The family dies **only if the six levels are essentially never touched in RTH** — fewer
than **2 filled touches per session** on average in either era. That is a structural
statement about whether the trade exists at all.

## Known limits, stated up front

- **Levels computed on NQ, not his QQQ.** Stated above; it is a real deviation.
- **His win-rate claims are unverified marketing** and no bar in this document is set
  against them.
- **Overlapping trades.** Uncapped sequential entries mean many positions overlap in
  time. §2.2 requires effective-N (average-uniqueness) rather than raw trade count for
  any later significance claim. Overlap is recorded now so that correction is possible
  later; **no significance is claimed at this stage.**
- **The 45%-of-losses-from-the-opening-candle claim is his, unverified.** It is recorded
  as a declared arm to verify later, never assumed.

## Artifacts

`scripts/nya_lvl_census.py` · `output/nya_lvl_census.parquet` ·
`output/nya_lvl_census.md` · trials to `output/trial_ledger.parquet` · raw data card to
`research/FUNNEL.md` per §5.10.

## Branch

`claude/youtube-mcp-strategy-validation-1bf82c` — this chat's own branch, separate from
the canon-rebuild chat's, per the Brake precedent.
