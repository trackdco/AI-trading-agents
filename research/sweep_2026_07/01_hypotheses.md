# Phase 2 — pre-registered hypotheses (v2, Brake's six amendments applied 2026-07-28)

**Status: APPROVED WITH AMENDMENTS. This version supersedes the draft. Tests RUN — results in
`phase2/phase2_results.json` and the dashboard.**

---

## H0 FIRST — every result below is conditional (Amendment 2)

The 40 leaky columns did not merely score features — **they selected the trades**. Every one of
the 216 trades in this population was chosen by a canon that consulted `C`, `W`, `D`, `WALLSZ`,
`score`, `Q`, `size` and the rest of the FAIL list. Excluding those columns from Phase-2 feature
sets does **not** clear the problem: the population itself may not survive re-derivation with
clean inputs.

**Therefore every result in this study is conditional on H0** — "does the canon's edge survive
dropping the 40 leaky columns?" — which requires re-deriving the book and is a rulebook call for
Brake/Pat, not a research decision. Every results section is headered with this caveat.

## Effective sample (Amendment 3, exact numbers)

The 30-trade floor is not the real constraint. Computed on this book:

* **26 trades** (12.0%) touched +4R and carry **98.1%** of the window's +$18,376.
* Under the chronological 50/50 split, **15 of those 26 are in the OOS half** (Brake's estimate
  of ~13 was close; the exact figure is 15).
* The **top 5 OOS trades alone are 56.0% of OOS P&L**.
* So every criterion scored on terminal funded P&L is effectively a **~15-observation test**,
  and the 5-largest fragility check removes a third of it.

This number appears next to every funded-P&L headline on the dashboard.

## The 30-OOS floor, sourced (Amendment 6)

The floor is **Brake's own brief**, §Phase-2: *"no rule is reported as viable on fewer than 30
out-of-sample trades in the bucket it applies to"* — applied to **OOS n**, not total n. It is not
my invention and it is not a validation bar: at sd(R) ≈ 2.0, n=30 gives SE ≈ 0.37R, so only
effects above ~0.7R/trade are even detectable at the floor. It functions as a **refuse-to-report
threshold** (below it → INCONCLUSIVE), consistent with the promotion gate's deletion of sample
minimums: 30 does not separate edge from luck either, and nothing above the floor is thereby
certified — it merely earns the right to be reported with its uncertainty stated.

## The H1 inconsistency, resolved (Amendment 4)

**69/24/16 is correct.** The draft's "n=138 OOS-capable at 08:00" conflated the bucket's TOTAL n
(138) with its OOS half (69). Correct statements: the 08:00–08:29 bucket has 138 trades total, of
which 69 are OOS — the only bucket clearing the 30-OOS floor. **H1 itself applies to the whole
window**, so its OOS n is 108 (216 − 108 IS), which clears the floor comfortably; the per-bucket
census constrains bucket-specific rules only.

---

## Hypotheses as run (17 comparisons — Amendment 5)

| ID | Cells | Heading | Status at registration |
|---|---|---|---|
| H1 fixed targets {1.5, 2, 2.5, 3, 4}R vs canon | 5 | **OOS-legitimate** (walk-forward, expanding monthly, select on train only) | open |
| H2 bias gate {no gate, skip-with, skip-against} | 3 | **IN-SAMPLE** (Amendment 1) | 2026-only contrast |
| H4 MAE cut θ∈{0.6, 0.7, 0.8, 0.9} at bar close | 4 | **IN-SAMPLE** (Amendment 1) | falsifier partly pre-answered |
| H5 contract stratum clean vs exposed | 1 | integrity test | open |
| H6 standalone viability, sizing × halts | 4 | constraint test | open |
| **Total** | **17** | expected min p under global null ≈ 0.06 | |

**Amendment 1, in full.** H2 was selected because the pooled bias contrast was visible in Phase-1
results computed on all 216 trades; H4's θ range descends from the 0.98R global maximum winner
heat, which **includes the OOS winners** — so its "no winner ever dug past θ" falsifier is partly
pre-answered by construction. Both are therefore **in-sample findings**. Their tables never
appear under an OOS heading; their OOS columns are labelled "descriptive split, NOT
confirmation". Confirmation for either requires **sessions after 2026-07-10** (fresh data), which
does not exist in this repo.

**Amendment 5.** H3 (time-split vs universal) is moved to the NOT-TESTED table with its original
reasoning: the OOS census (69/24/16) makes two of three buckets structurally incapable of
clearing the floor, so running it would spend 3 comparisons to confirm a known INCONCLUSIVE. The
universal rule wins by default until a bigger book exists.

## Not tested, and why

| Idea | Reason |
|---|---|
| H3 time-split rules | INCONCLUSIVE by construction (OOS 69/24/16 vs floor 30) — Amendment 5 |
| Fast-loser filter | Phase 1: left tail of one distribution, not a population (de-tie dip p=0.945; BIC prefers 1 component; 0 trades above 0.75 posterior) |
| Order-flow conviction | 0 `.scid` files; Databento substitute awaiting ruling; 2025 half price-contaminated |
| Depth / wall rules | entire `dep_*` family failed 0c; `W` flips on 41.6% re-read pre-fill |
| Anything 09:00-specific | 16 OOS trades; sign flips by year |
| Spread / VWAP-distance filters | Phase 1: no separation (medians identical; p=0.63/0.60) |

## Binding rules (unchanged from draft)

Walk-forward expanding window for anything fitted; funded rules binding (EOD-trailing $2,000 DD,
Tier-1 −$800 day halt, 40-micro clamp); costs stated ($1.24 RT/micro commission, 1-tick slippage
on marketable exits, none on limit fills; incumbent uses recorded pl — cost models differ at the
margin and this is stated wherever compared); leaky columns excluded from all feature sets;
contract stratum reported both ways; 5-largest fragility on every exit result; drops reported.
