# PRE-REGISTRATION ADDENDUM — LDN-OBK-01 / LDN-PO3-01 — conditioning search

**Committed BEFORE the conditioning run.** L1 is done
(`docs/PREREG-london-open-break-L1.md`, `output/london_obk_l1.md`): raw is negative,
the tight-stop claim failed 0/4, and the first declared variable (minimum
displacement) did not lift. Under §5.9.2 an expectancy kill is illegal at that stage
and the family earns the full variable search on its census-passed premise. This
declares that search.

## The rule I am binding myself to

Each variable below carries a **directional prediction stated before the run**,
derived from the mechanism, not from the data. This exists so the search can fail
informatively:

- A variable that lifts **in its predicted direction, in both eras** is evidence.
- A variable that lifts **in the opposite direction to its mechanism** is a
  **warning**, not a win. It will be recorded as a curiosity and explicitly NOT
  carried forward as a gate, because a gate whose story is written after the split is
  the definition of the thing this programme exists to avoid.
- A variable that lifts in one era only is a negative result.

**Nothing here promotes anything.** The declared default specs (A/S1 and F1) stay the
frozen specs regardless of what the conditioning shows, per the promotion rules
already in both candidate files. Conditioning identifies where the edge lives; it does
not re-open the arm tournament.

---

## V1 — Time of break within the window

**Split:** London-local hour of the break. **Open hour** 08:00–08:59 vs **macro hour**
09:00–09:59. (Declared in London time so DST does not smear it.)

**Mechanism.** `LDN-WIN-01` measured two peaks in this session, 03:00 and 04:00 ET =
08:00 and 09:00 London, holding in both eras. The 04:00/09:00 bucket carries the
**highest directional efficiency in the entire profile** (0.574 in 2026) — efficiency
being how much of the bar's range is net travel rather than churn. It is also
09:00 London / 10:00 CET, the main European data slot. No candidate in the book
currently uses it; every trader we have read is crowded on the 03:00/08:00 open.

**Prediction, declared:**
- **Continuation (A/S1) does BETTER in the macro hour** — a continuation trade needs
  net travel, which is exactly what efficiency measures.
- **Fade (F1) does BETTER in the open hour** — the fade needs churn and reversion,
  which is the lower-efficiency condition.

This is the sharpest test in the set because the two branches are predicted to move in
**opposite** directions on the same split. A variable that improves both branches at
once would be measuring trade frequency or volatility, not the mechanism.

## V2 — Pre-open range width vs recent normal

**Split:** pre-open range width divided by its own trailing 20-session median. Terciles:
narrow / normal / wide.

**Mechanism.** The published initial-balance work is consistent on this: narrow
initial balances break and extend (narrow IB → 98.7% break; IB direction → break side
74–81%), wide ones have already expressed the move. A wide pre-open range means the
day has done its work before the open and a break of it is exhaustion rather than
initiation.

**Prediction, declared:**
- **Continuation does BETTER on narrow ranges.**
- **Fade does BETTER on wide ranges.**

Again opposite directions, for the same reason as V1.

## V3 — Break direction vs the pre-open drift

**Split:** where the last pre-open close sits inside the pre-open range —
`(close − low) / (high − low)`. Drift is **up** above 0.66, **down** below 0.33,
**neutral** between. A break is **with-drift** if it breaks the side the drift was
already heading toward, **against-drift** otherwise.

**Mechanism — this is the trapped-counterparty story stated precisely, and it is the
one I would bet on.** The candidate's thesis names the loser as "whoever committed to
the pre-open drift". If price has drifted *up* into the open and then breaks *up*,
those people are already long and there is nobody left to trap — the break is running
out of fuel, not into it. If price drifted *down* and then breaks *up*, the break runs
directly into positioned shorts who must cover.

**Prediction, declared:**
- **Continuation does BETTER against-drift.**
- **Fade does BETTER with-drift.**

**If V3 fails, the candidate's own stated mechanism is not visible in the data**, and
that is a much more serious result than a failed filter. It is the closest thing to a
direct test of the story both branches are built on, and it is recorded as such.

---

## What is NOT in this search, and why

- **Minimum displacement** — already run at L1, negative in every cell. Not repeated.
- **Exit arms / target choice.** F2 (far-edge) beat F1 (midpoint) in 2026 and not in
  2025. That question is genuinely open and it is an **exit tournament**, a separate
  rung with its own declared default. Folding it into a conditioning search would let
  a target choice be made on conditioned in-sample data, which is precisely the
  procedure §6.0 condemns. Deliberately excluded.
- **Interactions between V1/V2/V3.** Not run. Three variables on ~250 trades per era
  is already thin; a 3-way interaction would be fitting noise and would inflate the
  DSR denominator for nothing. If any single variable survives both eras, its
  interaction with the others becomes a declared follow-up.
- **Flow, depth, CVD.** These are L3 and need the flow span. Not available to a
  bar-only search.

## Accounting

Unchanged from L1 and matched to the NY lane: 1 pt base / 2 pt strict cost, $160 risk
sizing, conservative intrabar, era split 2025 discover / 2026 validate, never pooled
for the headline. Applied to the **declared default arms only** (A/S1 and F1) so the
search costs 3 variables × 2 branches × 2 eras, not the full arm matrix.

## Spans

2025 + 2026. **Holdout look: NO.** 2023/24 untouched; sealed flow months untouched.

## Kill criteria

None. §5.9.2 forbids an expectancy kill until the search is complete; this run is part
of that search, not its conclusion. What this run *can* establish is whether the
family's own mechanism story (V3) is visible at all — and if it is not, that goes in
the verdict in those words.

## Artifacts

`scripts/london_obk_cond.py`, `output/london_obk_cond.md`, trials to
`output/trial_ledger.parquet` at trial time, `research/FUNNEL.md` cards refreshed.
