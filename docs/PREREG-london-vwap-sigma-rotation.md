# PRE-REGISTRATION — LDN-VWAP-01: vwap-sigma-rotation (leg 1)

Filed per `docs/VALIDATION-PROCESS.md` §1, **BEFORE any census run**. Git timestamp is the
declaration. Trial family: **LDN-VWAP-01**.

Thesis: `research/candidates/london-vwap-sigma-rotation.md`, greenlit ANGUS 2026-08-04.
Feasibility first (`london_feasibility_scan.py`): ±2σ is touched on 180 days in 2025 and 96
in 2026 — clear of the n ≥ 30 floor before further gates.

**Bars caveat:** §2 numbers remain `[PROPOSED]`; the fragility gate (§7) is bar-independent.

---

## 1. Scope — leg 1 only

The candidate has three legs. This prereg tests **leg 1 only**:

- **Leg 1 (here):** on rotational days, a ±2σ touch of the overnight-anchored VWAP reverts
  toward the mean.
- **Leg 2 (out of scope):** trend-day pullback to an origin-anchored AVWAP. Different
  event, different anchor — needs its own prereg.
- **Leg 3 (out of scope, and out of session):** the 05:00–06:30 ET stall. That is
  10:00–11:30 London — **outside the 08:00–10:00 session entirely**. It cannot be tested as
  a London candidate without Angus first ruling on a window extension.

Leg 1 is the core claim and the one the thesis leans on. If it fails, legs 2–3 are a
different strategy wearing the same name.

## 2. Claim (falsifiable)

Outside catalyst days London is rotational — no participant has the size to relocate value.
Price stretched to ±2σ of the overnight VWAP is the marginal chaser paying the worst price
with no follow-on buyer behind them; absent acceptance, inventory reverts.

> **After a first ±2σ touch followed by a rejection close, on a day that passes the
> rotational regime gate, price moves back toward the VWAP over the remainder of the
> session.**

## 3. Specification — exactly this computation, no parameter searched

**Session window: 08:00–10:00 Europe/London**, converted per day via `london_window_et(day)`.
ET hours never hardcoded.

**Anchor, frozen at the London open:** VWAP over 18:00 ET (D−1) → the London open, computed
per day from 1-minute bars; σ = the realised standard deviation of 1-minute closes about
that VWAP over the same span. **Not** the substrate's `on_vwap_0255`/`on_sigma_0255`, which
hardcode 02:55 and are an hour stale on DST-mismatch days.

**Regime gate (the candidate's own, declared):** the day is excluded if the London open
prints **outside the Asia range** — the thesis's drive-open exclusion. The thesis names the
regime split as the hard part, so leg 1 is tested *as specified*, gated.

**Event:**
1. First 1-minute bar inside the window whose high ≥ VWAP + 2σ, or low ≤ VWAP − 2σ.
2. Scanning forward from that bar: if a 1-minute **close** prints back inside the ±2σ band
   before **two consecutive closes** print beyond it, the event fires at that close, `t`.
3. If two consecutive closes beyond 2σ come first → **acceptance**; the thesis says stand
   down all session, so the day is excluded (not counted as a loss).

**Direction:** the fade, toward VWAP. Touched +2σ → short; touched −2σ → long.

**Outcome:** `signed_ret` = (close at window end − close at `t`) × direction. Positive =
reversion worked. Measured strictly from `t` forward.

One event per day (the first). σ multiple 2.0, acceptance = 2 consecutive closes — both
declared here, neither optimised.

## 4. Causality audit (required section, per `VERDICT-LDN-SWP-01.md` §4)

| variable | determined | before the outcome window? |
|---|---|---|
| VWAP, σ | 18:00 ET → London open, frozen at open | ✅ |
| Asia range / regime gate | prior to the open | ✅ |
| ±2σ touch | at the touch bar, ≤ `t` | ✅ |
| rejection close / acceptance | at `t` | ✅ |
| direction | by which band was touched, known at `t` | ✅ |
| outcome | over (`t`, window close] | ✅ |

Nothing defining the event, direction or grouping is drawn from the interval measured.

## 5. Eras

Discover 2025 / validate 2026-01..07, **plus the inverse pass** (§2.1); both directions must
agree. **2023/24 untouched** — asserted absent before computing. No holdout look.

## 6. Secondary — one, pre-specified

**Does the regime gate earn its place?** Compare gated vs ungated event populations. The
thesis stakes leg 1 on the gate ("misclassify and leg 1 fades a trend day"), so a gate that
adds nothing is itself a finding. One comparison, declared. No threshold is tuned.

## 7. Fragility gate — runs FIRST

Mean `signed_ret` recomputed with the 1, 3, 5 and 10 largest-|signed_ret| events removed,
plus 1/99-winsorised. **Sign flip at any trim depth ≤ 3 in either era kills the family
regardless of everything else** (§2.5). Bar-independent — a FAIL here is final.

## 8. Decision rules — three-way, declared in advance

Let `M` = mean `signed_ret`, `M₂₅` its 2025 estimate.

| outcome | condition |
|---|---|
| **PASS** | `M > 0` at p ≤ 0.05 one-sided in **both** eras, fragility clear, n ≥ 30 per era |
| **FAIL** | validate-era 95% CI on `M` **excludes** `M₂₅` and contains 0 or is negative — or fragility fires |
| **INCONCLUSIVE ON POWER** | neither; report minimum detectable `M` and events needed at 80% power |

Absence is an equivalence claim, never a bare failure to reject.

## 9. Mandatory reporting

Event counts per era before and after the gate and after acceptance exclusions; the full
fragility ladder whatever it shows; power and minimum detectable `M`; the gated-vs-ungated
comparison; the `signed_ret` distribution; and **how many days were excluded by acceptance**
— that count is itself informative about whether London is rotational at all.

## 10. Trial accounting

**4 trials** into LDN-VWAP-01 (primary × 2 era directions, secondary × 2). London programme
running total: **16** (4 each for LDN-INV-01, LDN-SWP-01, LDN-TRAP-01, and here). These
count in the DSR denominator per §2.4.

## 11. Known limits

- **L0 structure only.** No stops, targets or costs. The candidate's stop is ~2.5–3σ and its
  target the mean; holding to window close is a measurement convention, not the exit.
  Nothing here is tradeable evidence.
- σ from realised 1-minute dispersion about a session VWAP is one estimator among several;
  a different σ definition could move the band and hence the event set.
- The regime gate tested is the drive-open exclusion only. The thesis also lists
  bottom-quintile Asia range and "no VWAP cross since 02:00" as gate components; folding
  those in would be a search and is **not** authorised here.
- Legs 2 and 3 untested, per §1. Leg 3 additionally needs a window ruling from Angus.
- NY-canon input overlap: MEDIUM-LOW (bars + session VWAP, no depth/flow). The pairwise
  detector and correlation battery run at validation, not here.
