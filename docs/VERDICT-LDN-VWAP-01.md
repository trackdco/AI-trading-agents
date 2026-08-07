# VERDICT — LDN-VWAP-01 (vwap-sigma-rotation, leg 1)

**Drafted for Brake's signature.** Per `docs/VALIDATION-PROCESS.md` §5. Routes to Angus.
Reproduce: `python -m scripts.ldn_vwap01_census`.

Declared `PREREG-london-vwap-sigma-rotation.md` at **15:35:56Z**, run unchanged.
**Sealed 2023/24 untouched. No holdout look.**

---

## VERDICT: **INCONCLUSIVE ON POWER** on the declared primary — but three independent findings point against the candidate, and one attacks its premise directly.

I am **not** overriding the declared rule. The primary statistic does not meet the FAIL
condition, so the verdict is INCONCLUSIVE and it blocks like FAIL (§5). What follows is
reported separately because it does not depend on that statistic.

---

## 1. The declared primary

| era | n | mean signed_ret | p₁ | |
|---|---|---|---|---|
| 2025 | 77 | **−3.81 pts** | 0.694 | wrong sign |
| 2026 | 38 | **−12.15 pts** | 0.823 | wrong sign |

The claim was reversion — `mean > 0`. It is negative in both eras. 2026 CI [−37.87, +13.57]
contains both zero and the 2025 estimate, so the equivalence-form FAIL condition is not met:
**the sample cannot separate "slightly negative" from "zero"**. Fragility gate is clear
(signs stay negative at every trim depth), so this is not an outlier story.

Distribution: median **−6.00**, **42% of events positive**, sd 70.9.

## 2. Finding A — the power is better than it looks

| | min detectable mean @80% |
|---|---|
| 2025 (n=77) | +18.65 pts |
| 2026 (n=38) | +32.63 pts |

The trade fades from 2σ back toward the VWAP. Median overnight σ is **33.8 pts**, so the
trade's *own target move is ~68 points*. We could have detected an edge **28% the size of
what the candidate is trying to capture** — and measured −3.81.

This is not a well-powered null in the formal sense (the CI is wide), but it is far from
blind. A reversion worth trading would have been visible.

## 3. Finding B — the regime gate earns nothing

The declared secondary. The thesis stakes leg 1 on this gate: *"The regime split (rotation
vs trend) IS the hard part — misclassify and leg 1 fades a trend day."*

| era | gated (drive-opens excluded) | ungated |
|---|---|---|
| 2025 | −3.81 (n=77) | −3.09 (n=110) |
| 2026 | −12.15 (n=38) | −11.92 (n=58) |

**The gate makes no difference whatsoever.** It removes a third of the events and moves the
mean by under a point in both eras. The component the thesis identifies as the hard part —
and the thing that would justify the candidate's complexity — does no work.

## 4. Finding C — the rotational premise is contradicted

This is the one I would put in front of Angus.

The candidate rests on: *"outside catalyst days, London on NQ is rotational — US
institutional flow is absent, so nobody active has the size to relocate value."* If that is
true, price should rarely **accept** beyond 2σ.

Day disposition across the fit span:

| | days |
|---|---|
| never touched ±2σ | 128 |
| touched, then **accepted** (two consecutive closes beyond) | **100** |
| touched, then rejected → tradeable event | 168 |

**London accepts beyond 2σ on 37% of the days it gets there.** That is not a rotational
session with an occasional breakout; that is a session that relocates value more than a
third of the time it stretches. The premise is not a small-sample artifact — it is measured
on 268 touch days.

Note this cuts against the candidate's own defence. Acceptance days were *excluded* per the
thesis's stand-down rule, so they are not counted as losses. But their frequency is itself
the evidence: the stand-down rule is firing on a third of opportunities, which means the
regime the strategy needs is not the regime London is in.

## 5. What I recommend

**Do not run the pre-committed refinement, and do not extend to legs 2–3 on this evidence.**

The formal verdict is INCONCLUSIVE, so the candidate is not tombstoned by rule. But:
direction is wrong in both eras; the gate the thesis leans on does nothing; and the
rotational premise is contradicted on 268 days of data. Three independent strikes, only one
of which depends on the primary statistic's power.

**Recommendation to Angus: shelve leg 1 with a tombstone-pending note.** If it is revisited,
it needs the premise re-established first — a direct measurement of whether London is
rotational at all — not another pass at leg 1's parameters. Testing entry mechanics inside a
regime assumption that the data contradicts is the expensive way to reach the same answer.

**Legs 2 and 3 remain untested and are not covered by this verdict.** Leg 3 additionally
sits at 05:00–06:30 ET = **10:00–11:30 London — outside the session** — and cannot be a
London candidate at all without a window ruling from Angus.

## 6. Clean-run confirmation

- **Window:** derived per day via `london_window_et()`. No hardcoded ET; mismatch days
  handled by the converter, not excluded.
- **Anchor:** VWAP and σ computed 18:00 ET → the actual London open and frozen there — not
  the substrate's `on_vwap_0255`/`on_sigma_0255`, which hardcode 02:55 and are an hour stale
  on mismatch days.
- **Causality (prereg §4):** all six variables determined at or before `t`; outcome measured
  over (`t`, window close]. Audit clear.
- **Acceptance honoured as specified** — excluded, not scored as losses.

## 7. Trial accounting

**4 trials** into LDN-VWAP-01. London programme running total: **16**. These count in the
DSR denominator per §2.4.

## 8. What this does not establish

- L0 structure only. No stops (the candidate's is ~2.5–3σ), no targets, no costs. Holding to
  the window close is a measurement convention, not the exit.
- σ from volume-weighted dispersion about the overnight VWAP is one estimator; a different
  σ definition moves the band and hence the event set.
- Only the drive-open component of the regime gate was tested. The thesis also lists
  bottom-quintile Asia range and "no VWAP cross since 02:00"; folding those in would be a
  search and was not authorised.
- The acceptance-rate finding (§4) is a **descriptive measurement**, not a registered test.
  It is strong enough to act on as a prior, and it should be re-registered properly if it
  is going to carry a decision about the wider rotational premise.
