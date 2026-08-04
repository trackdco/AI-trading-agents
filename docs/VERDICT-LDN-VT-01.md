# VERDICT — LDN-VT-01 (value-traverse, leg (a) the naked-POC magnet)

**Drafted for Brake's signature.** Per `docs/VALIDATION-PROCESS.md` §5. Routes to Angus.
Reproduce: `python -m scripts.ldn_vt01_census`.

Declared `PREREG-london-value-traverse.md` at **16:42:52Z**, run unchanged.
**Sealed 2023/24 untouched. No holdout look.**

---

## VERDICT: **INCONCLUSIVE ON POWER** on the primary — the validate era is under-powered, and that is **my error, disclosed below**. But the declared secondary is decisive and it goes against the thesis's central claim.

---

## 1. Two defects in my own test, disclosed first

**Defect 1 — my feasibility count was not the full gate stack, despite the prereg saying it
was.** I counted days *carrying a magnet* (137/60 at reach 100) but never applied the entry
trigger — the close beyond the Asian extreme on the magnet side. Real event counts are
**53 / 23**. The validate era is **below the n ≥ 30 floor**, so the primary was
under-powered before it ran and I should have known.

This is the LDN-DRIVE-01 lesson repeating one document after I wrote it down. The amendment
I proposed for §2.2 — *count what you would actually trade* — must include the **entry
trigger**, not just the setup gates. A magnet you never get an entry against is not an
event.

**Defect 2 — my placebo was broken, and it produced a spectacular false result.** The
prereg declared a *distance-matched* placebo. I anchored it to the opposite Asian extreme,
which leaves it far further from the entry price than the magnet is. First run reported:

> magnet touched 49.1%, **placebo touched 0.0%**

That is not a finding, it is a bug — it measures "near things get touched more often than
far things", the exact confound the placebo exists to remove. Caught by inspection, because
a 0.0% rate is not a number the world produces.

Corrected to match distance **from the entry price**, opposite direction — which is what
the prereg declared. The result inverts, and §3 is the corrected version. **The fragility
gate did not catch this**, and could not: a specification defect is perfectly robust to
trimming. That is now the second time in this programme (after LDN-SWP-01) that a
spectacular result came from a defect and the gate stayed silent.

## 2. The primary

| era | n | mean signed_ret | p₁ | |
|---|---|---|---|---|
| 2025 (discover) | 53 | **+4.74 pts** | 0.121 | right sign, not significant |
| 2026 (validate) | 23 | **−6.62 pts** | 0.671 | **wrong sign, below n≥30** |

2026 CI **[−35.92, +22.68]** — contains zero and contains the 2025 estimate, so the
equivalence-form FAIL condition is not met. Verdict is INCONCLUSIVE and it blocks like FAIL
(§5).

**Power is the story.** Minimum detectable mean at 80%: **+10.07 pts** in 2025, **+37.17
pts** in 2026. A 37-point minimum detectable effect on a trade whose magnet sits a median
of 32–42 points away is no test at all.

Distribution: median +6.25, **55% of events positive**, sd 46.2.

**Fragility gate: CLEAR** — sign is stable within each era across every trim depth and every
reach rung. Worth naming the gate's blind spot: it checks stability *within* an era, and the
two eras disagree in sign at **every** rung of the reach ladder (2025 +5.49/+4.74/+3.01
against 2026 −19.04/−6.62/−11.11). The gate is silent on that by design; the primary catches
it.

## 3. Secondary — the finding that matters: **naked POCs do not attract price**

The thesis's central claim is that a naked POC *"holds resting two-sided interest and
demonstrably attracts price"*. Tested against a level the same distance from the entry, in
the opposite direction:

| era | magnet touched | placebo touched | difference | p₁ |
|---|---|---|---|---|
| 2025 | 49.1% | **50.9%** | **−1.9 pp** | 0.595 |
| 2026 | 60.9% | 52.2% | +8.7 pp | 0.285 |

**In 2025 the arbitrary level was touched slightly more often than the naked POC.** In 2026
the magnet leads by 8.7 points with a standard error of 15.3 — noise.

Price reaches a naked POC about half the time. It reaches *any* level at that distance about
half the time. **The naked POC is doing no work; the distance is.**

This does not depend on the primary's power, because it is a paired within-day comparison —
same day, same distance, opposite direction — so the small n hurts it far less than it
hurts the primary.

## 4. Leg (b) is untestable, and that is on the record

Recorded in the prereg before running, repeated here so it is not lost:

| gate | 2025 | 2026 |
|---|---|---|
| Asia held wholly outside prior RTH value | 65 | 20 |
| + a London close back inside the value area | **4** | **1** |
| + held inside ~45 min | 2 | 0 |

Mechanically explicable, not a coding artifact: median gap from the Asian edge to the
value-area edge is **43.8 points** against a median London range of **99.2 points**. The
80%-rule traverse is a real move that mostly does not complete inside our two hours.

## 5. Clean-run confirmation

- **Window:** derived per day via `london_window_et()`. No hardcoded ET.
- **Causality (prereg §4):** the naked-POC list is built from the 20 sessions **strictly
  before** the event day, and the traded-through check never sees the event day. Asia
  extremes precede the open; direction is fixed by which side the magnet sits, before `t`;
  outcome is measured over (`t`, window close]. Audit clear — this was the candidate's
  main circularity risk and it was handled.
- **Volume-at-price** is the thesis-authorised 1-minute approximation, 1-point buckets.

## 6. Trial accounting

**4 trials** into LDN-VT-01. London programme running total: **28**. These count in the DSR
denominator per §2.4. The reach ladder added no trials — declared fragility, not three
primaries.

## 7. Recommendation to Angus

**Do not extend leg (a). Do not run leg (c) on this evidence without a decision from you.**

Leg (a) is formally inconclusive and I will not dress that up — the validate era had 23
events and could not have detected anything under 37 points. But the secondary is a
**premise test**, it is properly controlled, and it says the naked POC has no measurable
pull over an arbitrary equidistant level. Legs (a) and (c) both rest on the profile map
marking places price is drawn to. If naked POCs do not attract, the map's authority is in
question and leg (c) inherits that doubt.

**Recommendation: shelve legs (a) and (b); hold leg (c) pending your call.** If the profile
family is revisited, the thing to establish first is whether *any* profile level — POC, VA
edge, HVN — attracts price beyond what distance alone explains. That is one properly
controlled measurement and it would settle the whole family, rather than three separate
legs each assuming the premise.

## 8. What this does not establish

- L0 structure only. No stops, targets or costs. The thesis's exits (scale out into the
  touch, runner into NY) are unmodelled.
- **The window truncates the thesis.** The candidate says the traverse "often finishes in
  NY"; our window closes at 10:00 London, so a magnet reached later is invisible here. This
  biases against the candidate and was declared in the prereg, not offered afterwards.
- Volume-at-price is a 1-minute approximation. A footprint-derived profile (available
  2025-06+) would move bucket volumes and change which POCs exist — untested, and the
  thesis itself flags it.
- The placebo controls distance and direction but not *path* — it does not ask whether
  price approached the magnet more slowly, or stalled at it. "Touched" is a blunt
  instrument for a magnet claim, and a level can matter as a reaction point without being
  reached more often.
- Leg (c) untested and needs its own prereg.
