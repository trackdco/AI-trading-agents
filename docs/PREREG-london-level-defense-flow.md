# PRE-REGISTRATION — LDN-DEF-01: level-defense-flow (absorption at a defended level)

Filed per `docs/VALIDATION-PROCESS.md` §1, **BEFORE any census run**. Git timestamp is the
declaration. Trial family: **LDN-DEF-01**.

Thesis: `research/candidates/london-level-defense-flow.md`, greenlit ANGUS 2026-08-04.
Feasibility done first: price-level footprint spans 2025-06-01 → 2026-07-19 (24.8M rows, 6
files, **sealed holdout files excluded by name**), covering **~99 / 76** events per era —
clear of the n ≥ 30 floor.

---

## 1. Why this candidate's event set is the trap-fade event set

The thesis's entry is *"enter with the defense on the first rejection close away"* from the
level. That is, minute for minute, the **LDN-TRAP-01 event**: price trades ≥ 4 ticks beyond
a level frozen at the open, then a 1-minute close prints back through it within 15 minutes.

The candidate is therefore **not a different event** — it is the same event with an added
requirement: that order flow shows the level was *defended* rather than merely poked. The
thesis says so itself: *"Sibling: `london-level-trap-fade` (candles expression, bigger
sample) — one family."*

So this is tested as what it is: **does the absorption signature separate the winners from
the losers inside a level-reclaim population we have already measured?** That framing is
honest about the family relationship rather than dressing the candidate up as independent
evidence, and it reuses an event set already asserted against a signed-off verdict.

**LDN-TRAP-01 failed as a well-powered null.** That is the prior. It is also exactly why
this test is worth running: if absorption is real, it should carve a winning subset out of
a population whose average is zero. If it cannot, the candidate has no mechanism left.

**This is not covered by LDN-FLOW-01.** That verdict tested *minute-aggregate* flow and
stated explicitly that price-level absorption — heavy volume at one price that will not
move — is invisible at that resolution. This prereg tests the resolution that can see it.

## 2. Claim (falsifiable)

> Among London level-reclaim events, those where price-level footprint shows aggressive
> volume absorbed at the defended level go on to work better than those where it does not.

## 3. Specification — exactly this computation, no parameter searched

**Substrate:** the LDN-TRAP-01 event set, rebuilt verbatim and **asserted** to reproduce the
published verdict counts and means (161/−2.30, 89/−2.64) before anything proceeds, then
restricted to the footprint span. Each event carries its level price, the entry minute `t`,
and the fade direction.

**Data:** `data/reference/cvd/footprint_*.parquet` — per (minute, price, aggressor side)
volume. `side='B'` = buyer-aggressor, `'A'` = seller-aggressor. **Holdout files excluded by
filename**; the loader must assert none are read.

**The absorbed aggressors** are those who pushed *into/through* the level — buyers on an
upside break, sellers on a downside break. In event terms that is the side opposite the
fade direction, and it is fixed by the event, not chosen.

**Window: `[t−3, t]`** — the three minutes before the reclaim close plus the reclaim minute.
Declared. `[t−2, t]` and `[t−5, t]` run as a fragility ladder (§6), not as alternatives.

**Level proximity: within 2 ticks (0.5 pts)** of the level price. Declared. 1 and 4 ticks run
in the same ladder.

**Normaliser:** the session's median per-minute volume, so a measure is not just reading
"busy day".

| # | measure | definition | mechanism | declared sign |
|---|---|---|---|---|
| 1 | **ABSORB** | absorbed-aggressor volume at prices within 2 ticks of the level over `[t−3,t]`, ÷ session median minute volume | heavy aggression met at the level and stopped | **positive** ρ |
| 2 | **PIN** | the same volume ÷ (max excursion beyond the level in ticks + 1) | effort ÷ result — the literal definition of absorption | **positive** ρ |
| 3 | **ICEBERG** | max single (minute, price) volume within 2 ticks of the level over `[t−3,t]`, ÷ session median minute volume | the thesis's reload signature: volume at one price far exceeding what was displayed | **positive** ρ |

All three declared **positive**. A significantly negative one is a finding and will be
reported, not dropped.

## 4. Threshold-free primary — same commitment as LDN-FLOW-01

Primary is **Spearman ρ** between each measure and the event outcome, plus **AUC** for
winner/loser separation. If ρ ≈ 0, no absorption threshold can filter losers and the
question is closed without a threshold search.

A **median split** is reported for readability — mean points and win rate in the
high-absorption vs low-absorption half. The median is the least-searched threshold that
exists. It adds no trials.

**Multiplicity:** three measures, so any PASS must survive **Holm–Bonferroni across the
three**, declared now rather than after seeing which one wins.

## 5. Causality audit (required, per `VERDICT-LDN-SWP-01.md` §4)

| variable | determined | before the outcome window? |
|---|---|---|
| level prices | frozen at the London open | ✅ |
| event, direction, `t` | LDN-TRAP-01, unchanged | ✅ |
| absorbed-aggressor side | by which side of the level broke, ≤ `t` | ✅ |
| ABSORB, PIN, ICEBERG | footprint minutes `t−3 … t` | ✅ |
| session median volume | minutes ≤ `t` only | ✅ |
| outcome | over (`t`, window close] | ✅ |

Every footprint minute read is at or before `t`; the outcome is measured strictly after. The
test must **assert** that no footprint minute used exceeds `t`. This is the defect that
killed LDN-SWP-01 and the one my own placebo re-created in LDN-VT-01 — it is checked in
code, not by eye.

## 6. Fragility gate — runs FIRST

- ρ recomputed with the 1, 3, 5, 10 largest-|outcome| events removed.
- Recomputed at windows `[t−2,t]` and `[t−5,t]`, and at level proximity 1 and 4 ticks.

**Sign flip at trim depth ≤ 3, or across either ladder, kills that measure regardless of its
p-value.**

## 7. Eras

Discover 2025 (Jun–Dec, footprint span) / validate 2026 (Jan–Jul). Sign must agree in both.
**2023/24 sealed and untouched** — the holdout footprint files exist on disk and are
excluded by name; no holdout look.

## 8. Decision rules — declared in advance

| outcome | condition |
|---|---|
| **PASS** | ρ positive at p ≤ 0.05 in **both** eras, fragility clear, Holm survived, n ≥ 30 per era |
| **FAIL** | validate-era 95% CI on ρ excludes the 2025 estimate **and** contains 0 |
| **INCONCLUSIVE ON POWER** | neither; report minimum detectable ρ at 80% power |

Absence is an equivalence claim, never a bare failure to reject.

## 9. Mandatory reporting

Event counts before and after the footprint-span restriction; the full fragility ladder
whatever it shows; ρ, CI, AUC and median-split means and win rates for **all three**
measures in **both** eras — none dropped; minimum detectable ρ.

## 10. Trial accounting

**6 trials** into LDN-DEF-01 (3 measures × 2 era directions). London programme running
total: **34** (28 prior + 6). These count in the DSR denominator per §2.4. Median splits and
ladders add no trials.

## 11. Known limits

- **L0 structure only.** No stops, targets or costs. The candidate's stop ("a few ticks
  beyond the defended extreme — defender pulls, out fast") is where it claims much of its
  edge, and holding to the window close cannot represent that.
- **Out of scope, declared:** the flip rule (reverse on a post-detection close beyond the
  level), and the CVD-divergence variant that fades new session extremes. Both are separate
  events needing their own preregs.
- **Iceberg is a proxy, not a measurement.** The thesis defines it as volume at one price
  exceeding *displayed depth*. Our depth is one book snapshot per minute, which cannot
  support a true displayed-depth comparison; ICEBERG here is volume concentration alone.
- Family relationship with LDN-TRAP-01 is real: a PASS here does not overturn that verdict,
  it identifies a subset within it.
- **NY-canon input-family overlap: HIGH.** Depth and order flow are the canon's core input
  families; the same-account veto will very likely trip even on a PASS. This is tested for
  knowledge, and any deployment question goes to Angus with the correlation battery first.
