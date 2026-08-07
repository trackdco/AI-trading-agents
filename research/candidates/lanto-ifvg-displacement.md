# NYA-IFD-01 — IFVG + FVG displacement entries (Lanto, as taught)

**STATUS: INTAKE ONLY, 2026-08-07 — no slot requested yet.** No prereg
written, no data touched, no census run, no holdout look spent. Program
mode is one-strategy-at-a-time [ANGUS 2026-08-05] with NYA-IBC-01
active; this card queues for a slate slot AND for its own two declared
blockers below.

Spec: `research/transcripts/lanto/SPEC-as-taught.md` — **PROVISIONAL**,
provenance-graded, no transcript read yet (bot-wall; manual paste
needed).
Credibility: `research/findings/lanto-credibility.md` — anonymous alias;
owns the prop-evaluation funnel he advertises into (SmartPropFirm);
headline P&L unverifiable and confounded by account stacking; offsets:
daily live execution before paying members, published losses, 22k-member
community at 4.4/5. **Test mechanics, ignore every dollar figure.**

## Raw trigger family (what an L0 census would draw)

Computable from 1m bars alone (resampled to trigger TFs), no depth/flow
required — deliberately bars-only after the depth-clock incident:

- **T1 — FVG creation:** 3-candle displacement gap on TF ∈ {1m, 5m,
  15m}: bullish `high(i−1) < low(i+1)`, bearish mirrored. Displacement
  strength recorded as candle-`i` body/ATR and body/range — NOT
  thresholded at L0 (his "displacement" quality knob becomes a measured
  column, not a gate).
- **T2 — inversion (IFVG):** a live FVG whose far edge is closed
  through by a subsequent candle. Close-through candle's body/ATR
  recorded (his "strong candle close" as a column, same treatment).
- **T3 — entry event:** first retest of the inverted zone after T2,
  direction = with the inversion. Stop reference = displacement-leg
  extreme. Alternative arm: same-direction FVG created by the inversion
  leg as the entry zone (the "+ FVG" reading — flagged [GAP] in the
  spec).
- Context columns per trigger, no gating at L0: session bucket, daily
  bias placeholder (see blocker 2), whether the inversion leg swept a
  reference extreme (ON H/L, PD H/L, OR H/L — reuse the reclaim
  family's reference-extreme code), distance to opposing liquidity /
  next unmitigated gap (= `room_ahead_R`, the one discriminator that
  survived the London autopsy).

## The trap, declared before anyone runs anything

**This is the most-tombstoned family in the repo.** Prior art that any
prereg must cite and differentiate against, or the census is a strawman:

- `zxck-ifvg-50` — iFVG entry at 50% CE: n=186, **−0.616R, t=−4.17,
  "loses reliably"** (program verdict 2026-08).
- **PB Blake inversion model** — sweep → structure → HTF-FVG inversion:
  712 trades, 48.2% vs a 50.4% per-trade random-walk null, negative
  every year and in all six stop×target configs
  (`research/findings/pb-blake-inversion-model.md`).
- **FVT tombstone** — FVG-based, optimized 2024–26, dead on sealed 2023.
- `the-geometry-frontier.md` — 33 variables, 93 buckets: every FVG-family
  "quality" variable tested so far is a proxy for target distance.
- `daxton-ifvg-continuation` — parked LOW on credibility.

The only content Lanto adds over that pile, per available evidence, is
(a) displacement-quality and close-strength as entry conditions, (b)
daily-bias gating, (c) whatever "$3M From 3 Steps" actually specifies.
(a) is measurable as L0 columns; (b) collides with the untested
`htf-bias-rules-extracted.md` variables — reconcile, don't duplicate;
(c) is unknown until transcripts. **If the transcripts reveal nothing
beyond the generic family model, the right call is NO SLOT — the family
verdict already exists and it is negative.**

## Blockers (in order)

1. **Transcripts** — manual paste of the three Blueprint videos (IDs in
   `research/transcripts/lanto/CATALOG.txt`); every as-taught knob is
   [GAP] until then, and the SPEC stays PROVISIONAL.
2. **Daily-bias definition** — either his taught bias rule (from
   transcripts) or an explicit decision to substitute a house bias
   variable; a census with an undefined bias column invites post-hoc
   gating.
3. **A slate slot** [ANGUS] — program mode; also the standing intake
   ruling from round 3 ("no strategies to test") sets the bar: this card
   needs a reason to be the exception, and today it does not have one.

## Reopen path

Transcripts land → SPEC upgraded from PROVISIONAL with real quotes →
differentiation vs the five tombstones argued explicitly → then, and
only then, a slot request with a prereg naming exact trigger TFs, the
sweep-required question, and both entry arms (IFVG retest / +FVG zone).
The trigger primitives (T1/T2 gap objects with displacement columns)
are reusable as FEATURES for other candidates regardless of this card's
fate — same salvage clause as NYA-OFC-01.
