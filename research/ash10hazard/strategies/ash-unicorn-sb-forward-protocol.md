---
date: 2026-08-07
kind: PRE-REGISTRATION — forward out-of-sample confirmation test
strategy: ash-unicorn-sb (AM1 09:45–10:15 ET only)
status: LOCKED. Written before any forward trade exists.
log: ash-unicorn-sb-forward.csv
logger: scripts/ash_forward_log.py
in-sample set being confirmed: 29 flow-covered trades, 2025-06-10 → 2026-07-15
---

> ## PROGRESS
> **forward setups logged: 0 · flow-covered: 0 · toward LOOK 1: 0/20 (need +20) · toward LOOK 2: 0/46**
>
> ### ⛔ 2026-08-08 — H1 and H2 STRUCK. H2′ registered as untested. See the amendment below.
> The looks and the Bonferroni schedule below were written for **two** hypotheses. With H1 and H2
> struck there is currently **one** registered hypothesis (H2′) and **no confirmatory test is
> scheduled** until its look-ahead proof passes and its threshold is set from future data.
> *No test may be run until a look trigger is reached. Nothing has been tested.*

# Forward protocol — putting H1 and H2 on trial

## Why this document exists

The historical sample is **terminal at 29 flow-covered trades** (see
`ash-unicorn-sb-orderflow.md`, revision 2026-08-07). Both live hypotheses, **H1** and **H2**,
were *generated* on those 29 trades. Testing them there measures the fit that created them.

**The only thing that can confirm them is data that did not exist when they were written.**
This document is timestamped in git before that data exists. That timestamp — not any
procedural care taken later — is what makes the forward set out-of-sample.

**Forward span begins 2026-08-08**, the day after this pre-registration is committed. The
logger refuses any earlier date. No trade from data that existed when the plan was written can
enter the forward set, even by accident.

---

## THE LOCKED HYPOTHESES

Both directions are stated **now**, in advance. A result in the opposite direction is a
**failure**, not a discovery — it may not be re-read as "the effect is real, just inverted."

> # ⛔ AMENDMENT 2026-08-08 — BOTH ORIGINAL HYPOTHESES ARE STRUCK
>
> Made **before any forward trade accumulated** (forward log: 0 rows). Nothing below was
> influenced by forward data, because none exists.

### ~~H1 — displacement-delta magnitude separates winners from losers~~ · **STRUCK**

**Reason: failed out-of-sample.** Tested on 115 independent trades from a different trader and
a different setup with identical feature definitions: direction held (win median 0.080 vs loss
0.072) but Cliff's δ came in at **+0.178 against an in-sample +0.596** — under a third the size —
with **p_holm = 0.1895**. The sample had the power to see the claimed effect (it detects d ≥ 0.58;
the effect claimed was d ≈ 0.596). **The power was there. The effect was not.**

**H1 is retired and may not be resurrected on this forward set.**

### ~~H2 — retracement participation predicts a STALL, not a loss~~ · **STRUCK**

**Reason: the feature is not computable at entry.** `F2_retrace_ratio`'s retracement window ends
at *and includes* the entry minute. Footprint data is minute-aggregated and the entry is an
intrabar limit fill, so the feature contains **up to 59 seconds of post-fill tape**. On 73% of
`zxck-10am-keyopen` trades and 50% of `orb-fvg-nyopen` trades the retracement is a **single
minute — the entry minute** — so 100% of the numerator is exposed. Full audit:
`research/_shared/f2-h1-oos-test.md`.

A rule of the form *"take the trade if F2 < 1.0"* is **not implementable**: at the fill you do
not yet know the entry minute's volume.

> ### ⚠️ THIS RETROACTIVELY VOIDS THE ORIGINAL STAGE-4 F2 FINDING ON THE CARD.
> The 52.6% → 72.7% win-rate improvement was a **positive discrimination result on a
> contaminated feature**, and the contamination biases *toward* false positives — the entry
> minute's volume is mechanically related to what price did immediately after the fill, hence to
> the outcome. **It is not evidence. Treat it as void, not as weakened.**

H2 also **failed out-of-sample independently** (ordering not observed, JT p = 0.9105, Cliff's δ
**+0.235** against an in-sample **−0.635** — the sign reversed). That failure *stands and stands
more firmly*: the contamination should have helped it succeed.

**H2 is retired and may not be resurrected on this forward set.**

---

### ✅ H2′ — REGISTERED HERE AS A NEW, UNTESTED HYPOTHESIS

The stall idea may still be true; the *measurement* was broken. H2′ is the same idea with a
boundary that is provably pre-entry.

> **`participation_to_touch` = (volume from the end of the displacement leg up to, but NOT
> including, the entry minute) ÷ (volume over the displacement leg).**

> **Direction (locked, pre-stated): WINNERS carry a LOWER `participation_to_touch` than losers.**

| | |
|---|---|
| **time boundary** | last minute read is **entry_minute − 1**. The entry minute is excluded entirely. |
| **why that is provably pre-entry** | the `entry_minute − 1` bar has **closed** before the entry minute begins. No part of the fill minute is read, so no post-fill tape can enter the value. |
| **look-ahead proof required before use** | recompute with all bars from the entry minute onward masked; the value must be **identical** on every historical event. Asserted in code — `research/_shared/flow-features/`. |
| **threshold** | **NONE IS SET.** It will be fixed at a percentile of the feature's own distribution **in the future data**, never chosen to suit a result. |
| **status** | **UNTESTED.** Registered, not confirmed, not promoted. |

**⚠️ H2′ IS NOT H2 REBUILT TO PASS.** It is a strictly *smaller* window than H2 — it discards
the entry minute rather than including it — so where H2's retracement was a single minute, H2′ is
**undefined**, not merely different. On the historical sample that was 73% of one card and 50% of
another. **A large fraction of any future sample will have no H2′ value at all, and that is a
property of the idea, not a data problem.** If most events are undefined, H2′ is untestable and
must be reported that way rather than run on the surviving minority, which is a biased subset
(it selects slow retracements).

**H2′ may not be tested on any data used before 2026-08-08.** The entire owned span through
2026-07-15 is in-sample for this programme.

### Nothing else is on trial

**No feature and no filter may be added to this test later.** The ten autopsy context features
are logged so forward rows pool with the historical set — they are **not** part of this
confirmation and no p-value from them counts toward it. Anything discovered forward is a
**separate, future hypothesis** requiring its own pre-registration and its own forward set.

---

## THE ANALYSIS PLAN

### Two pre-planned looks — and why there are two

| look | trigger | expected split | smallest detectable d (H1) |
|---|---|---|---|
| **LOOK 1** | n_forward = **20** | ~9W / 6L / 6BE | **1.67** |
| **LOOK 2** | n_forward = **46** | ~21W / 13L / 13BE | **1.10** |

*(80% power, one-sided, α = 0.0125; expected splits use the in-sample mix 44.8% win / 27.6%
loss / 27.6% BE.)*

**Read the LOOK 1 row carefully. It is underpowered for the very effect it is testing.** The
in-sample H1 effect is d ≈ 1.48; LOOK 1 can only reliably detect d ≥ 1.67. A null at LOOK 1
is therefore **uninformative**, and the decision rule below says so in advance rather than
after the fact. LOOK 2 is the first look that can actually see the observed effect.

Both looks are declared **now**, which is what makes this a planned group-sequential design
rather than peeking. **No analysis of any kind may be run between looks.**

### Multiplicity

- **Across looks and hypotheses:** flat Bonferroni, **α = 0.05 / 4 = 0.0125** per
  (hypothesis × look). Chosen for auditability — anyone can check it without a spending
  function.
- **Within a look:** Holm across {H1, H2}.
- Reported alongside: **Cliff's δ**, the **power floor**, and the **best-of-k noise
  simulation** — the same three checks the autopsy ran, so the forward result is read on the
  same terms as the in-sample one.

### THE DECISION RULE — written before any data

| outcome | ruling |
|---|---|
| p ≤ 0.0125, **in the locked direction**, after Holm | **CONFIRMED** at that look. Stop; the hypothesis is promoted for grading. |
| p > 0.0125 at **LOOK 1** | **NOT CONFIRMED — UNDERPOWERED.** The hypothesis is *not* retired. Continue to LOOK 2. |
| p > 0.0125 at **LOOK 2** | **RECORDED AS NOISE.** The hypothesis is retired. It may not be resurrected on a later slice of the same forward set. |
| effect in the **opposite** direction, any look | **FAILED.** Retired immediately. Not re-read as an inverted finding. |
| n stalls below a trigger | **Nothing is run.** "Still underpowered, needs forward accumulation." |

**A confirmed hypothesis is still not a promoted strategy.** It goes to the merged trial
ledger and faces the deflation bar (+0.5636 at N=58) like anything else. Confirmation here
ends the circularity problem; it does not end the certification.

### Analysis is on FORWARD TRADES ONLY

The 29 in-sample trades are **excluded from the test statistic**. Pooling them back in would
re-import the fit. They appear in the write-up only as the prior being tested against.

---

## THE LOG

`ash-unicorn-sb-forward.csv` — **one row per QUALIFYING SETUP, taken or not.** Skipped setups
are logged so the forward base rate is honest and selection bias cannot enter through which
trades got recorded.

### Schema

| group | column | notes |
|---|---|---|
| identity | `date`, `time`, `session`, `window`, `direction`, `taken` | `taken` ∈ {y, n} |
| trade | `entry`, `stop`, `target`, `exit`, `exit_time`, `risk_pts`, `R`, `outcome`, `be_moved` | `outcome` ∈ {win, loss, BE, timeout} |
| **poolable (on trial)** | `F1_disp_delta`, `F2_retrace_ratio` | frozen definitions above |
| context (pool only) | `htf_aligned`, `atr_pct`, `dist_to_level_R`, `news_in_window`, `news_day`, `entry_min_into_window`, `risk_pts_v`, `dow`, `direction_long` | the autopsy ten; **not on trial** |
| provenance | `flow_source`, `logged_by`, `logged_at_utc`, `entry_hash`, `notes` | |

**Column names are the historical ones on purpose.** Forward rows must `concat` with
`ash-unicorn-sb-autopsy-features.csv` without a rename step, because a rename is where a
definition quietly drifts. The brief's names map as:

| brief's name | column used | why |
|---|---|---|
| `retrace_ratio` | `F2_retrace_ratio` | identical quantity; one header, one definition |
| `disp_delta_magnitude` | `F1_disp_delta` | already side-signed — see H1 above |
| `atr_regime` | `atr_pct` | percentile rank of prior-14-day range, shifted |
| `dist_to_level` | `dist_to_level_R` | in R units, so it is scale-free |
| `entry_minute` | `entry_min_into_window` | minutes past 09:45 |
| `stop_size` | `risk_pts` / `risk_pts_v` | points |
| `day_of_week` | `dow` | Mon…Fri |

The same numbers are **never stored twice under two headers** — two copies can disagree, and
the disagreement would surface only after the outcome is known.

---

## INTEGRITY RULES

1. **Append-only.** Rows are never overwritten or deleted. Corrections enter as a **new dated
   row** with the correction in `notes`; the original stays.
2. **Entry-time fields are frozen at entry** and hashed. `entry_hash` is a SHA-256 over
   `date, time, direction, entry, stop, target, risk_pts, F1_disp_delta, F2_retrace_ratio` and
   the context features. `scripts/ash_forward_log.py verify` recomputes every hash and
   **flags any row whose frozen fields changed after logging** as `CONTAMINATED`.
3. **Outcome fields are written after close** and are deliberately outside the hash — filling
   them is expected and does not break integrity.
4. **The logger refuses dates ≤ 2026-08-07.** The forward set cannot be back-filled from data
   that existed when this plan was written.
5. **No fabrication, no interpolation.** A field we cannot compute is left **blank with a note
   in `notes`**. A blank is data; a guess is contamination. Flow features are populated only
   where tick data covers the date; `flow_source` records which file supplied them.
6. **No peeking.** `verify` reports counts only — it computes no test statistic on H1 or H2 and
   cannot be used to see how the hypotheses are doing.

### What actually protects this test

Not procedural care during logging — **the git timestamp on this document.** The features are
computed mechanically from bars and tick data by a script whose definitions are frozen above;
mechanical computation cannot be swayed by knowing the outcome. Manual rows are permitted
(`logged_by = manual`) for discretionarily-taken trades, and are the only rows where
entry-time freezing depends on human discipline. They are marked so they can be excluded in a
sensitivity check if they ever diverge from the mechanical rows.

---

## TIMELINE

At the observed rate of **27.3 qualifying setups/year** on AM1:

| milestone | forward setups | expected |
|---|---|---|
| **LOOK 1** | 20 | **~9 months** (≈ 2027-05) |
| **LOOK 2** | 46 | **~20 months** (≈ 2028-04) |

The rate is measured on 37 setups over 16.3 months and is itself uncertain; these are
estimates, not commitments. **If the rate is lower than measured, the looks arrive later —
that is not a reason to lower the trigger.**

---

## WHAT THIS PROTOCOL CANNOT DO

- It cannot rescue the 8 pre-2025-06-01 trades. Those need a Databento `GLBX.MDP3` pull for
  2025-03-01 → 2025-05-31 and would still be **in-sample** for H1 and H2.
- It cannot test the ES leading trigger, which remains a declared component of the model as
  taught and is absent from every number in this programme.
- It cannot make LOOK 1 informative if it comes back null. That is priced in above, in advance.

**Nothing in this document has been tested. No trial has been recorded. No look has been run.**
