# PRE-REGISTRATION ADDENDUM — LDN-OBK-01 / LDN-PO3-01 — L1 mechanics

**Committed BEFORE any P&L is computed.** The census prereg
(`docs/PREREG-london-open-break-tree.md`) declared counting only and explicitly
computed no P&L. This addendum declares the L1 expressions. It is committed before
`scripts/london_obk_l1.py` exists.

Census result that this builds on (`output/london_obk_census.md`): both branches
passed their §5.9.1 premise line; the event is bimodal (failed breaks run ~10 pts,
continued breaks 64–97 pts); the pre-open range beats a placebo range by +12/+14pp on
fail rate; the far-edge traverse target is **not** supported by its own base rate.

## What L1 answers

Whether the geometry pays per unit of risk. This is the question that killed
`nypre-euro-handoff` at a 78% win rate and +0.02R, and it is the only reason this
family was worth testing: both sources arrive with a **tighter stop** as their stated
fix, and that claim is now measurable.

---

## Continuation branch (LDN-OBK-01) — 2×2, four arms

Trigger is the census trigger, unchanged: the first 1-minute close beyond the
06:00–08:00 London pre-open range, inside 08:00–10:00 London. That candle is the
**trigger candle**.

**Entry axis** — the live disagreement between the two sources:

- **A — close-confirmed (Tradesharpe).** Resting stop order at the trigger candle's
  extreme in the break direction. Fills only if a later bar trades through it; if
  price never takes out the trigger candle, **there is no trade**. This is the
  declared default.
- **B — immediate (Brandan).** Enter at the trigger candle's close. Always fills.

*Honest note on arm B.* The candidate file describes Brandan's entry as "on the
reaction at the level, no close required". Taken literally that is not implementable
as a directional trade — before the break resolves, the direction is unknown, so a
touch entry has no side. Arm B therefore operationalises the same disagreement —
**wait for further confirmation, or don't** — in the only form the data can express.
Declared here rather than quietly substituted.

**Stop axis** — this is the actual experiment:

- **S1 — trigger-candle stop (default).** Opposite extreme of the trigger candle.
  The tight stop both sources name as the fix.
- **S2 — structural stop.** The opposite side of the pre-open range. This is the
  "running stops below that whole open candle" version Tradesharpe calls wasteful.
  It is here as the control that makes S1's claim falsifiable.

**Declared default arm = A + S1.** Named on mechanism before any numbers, per §6.0.1:
the thesis is that the open *resolves* a level test, so a close beyond the level plus
a push through the trigger candle is what resolution looks like; and the trigger
candle is the only stop the tight-stop claim can mean.

Target **2R** on all four arms. Flat at **10:00 London**.

## Failure branch (LDN-PO3-01) — two arms

Trigger: the first 1-minute close back inside the pre-open range after a break
(the census's `fail` event). Direction is against the break.

- **F1 — midpoint target (default).** Entry at the fail-bar close, stop beyond the
  sweep extreme, target the **pre-open range midpoint**. The midpoint replaces the
  far edge because the census measured far-edge traverse at only ~20%.
- **F2 — far-edge target (as taught).** Identical but targeting the opposite edge.
  Run so the census's implied correction is **measured rather than assumed**. If F2
  beats F1 the census read was wrong and the file will say so.

Arm A of the PO3 candidate (IFVG) remains **barred** — its promotion rule requires a
mechanical definition committed in advance and it does not have one. The
SMT-divergence confluence remains **dropped** for want of ES data.

## Declared variable — minimum displacement

The census found 27% (2025) / 9% (2026) of breaks extend under 5 points: bare
touches, admitted because the as-taught definition states no minimum. One declared
variable, two levels, applied to the **default arms only** so it costs two trials and
not sixteen:

- none (as taught) — default
- **≥ 0.10 × range width** — a fraction, not a point count, because 2026's ranges are
  ~75% wider than 2025's and a fixed point threshold would mean different things in
  the two eras.

## Accounting — matched to the NY lane so the numbers compare

- Costs: **1.0 pt (base)** and **2.0 pt (strict)**, both always reported.
- Conservative intrabar tie-break: stop is checked before target within a bar.
- Dollars at **$160 risk per trade** (1/risk sizing), alongside points.
- **Minimum risk 2.0 pts** — a sub-2pt trigger candle makes 2R smaller than the cost
  stack. Inherited from `scripts/nya_fa_l1.py` rather than chosen here.
- Era split 2025 discover / 2026 validate, reported separately, never pooled for the
  headline.

## Spans consumed

2025 + 2026 only. **Holdout look: NO.** 2023/24 untouched; the sealed flow months
untouched.

## Acceptance bars — what L1 can and cannot do

L1 does **not** certify anything. Per §5.9.2 a candidate cannot be denied the deep
variable search on ugly raw P&L, so **no arm dies at L1 on expectancy**. L1 exists to
produce the numbers and to rank nothing.

What L1 *can* establish, and the pre-committed reading:

- **The tight-stop claim is supported** if S1 beats S2 in R-per-trade in **both** eras
  at **both** cost levels. Anything less and the claim is unsupported — which is a
  real finding either way, because that geometry is the whole reason this family was
  greenlit.
- **Promotion still cannot happen here.** The declared default (A+S1, F1) stays the
  spec regardless of in-sample rank; displacement requires PBO < 0.5 on the arm
  matrix plus holdout adjudication, per the rules already in both candidate files.

## Kill criteria

None at this stage, by law. The family already passed the only kill line a census
carries. Arms that lose money are ledgered as declared negative results and the
family proceeds to the conditioning search.

## Known limits

- Bars only. No absorption, delta or depth — those enter at L3 and are where a break
  that "should" have been read as absorbed becomes distinguishable.
- First break per side per day, as at census. Re-break behaviour is not tested.
- 2R is a declared placeholder, not an optimised target. Exit arms are a later rung
  under §6.0, with the default declared first.

## Artifacts

`scripts/london_obk_l1.py`, `output/london_obk_l1.md`, trials to
`output/trial_ledger.parquet` at trial time, data cards refreshed in
`research/FUNNEL.md` per §5.10.
