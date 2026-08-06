# PRE-REGISTRATION — LDN-VT-01: value-traverse, leg (a) the naked-POC magnet

Filed per `docs/VALIDATION-PROCESS.md` §1, **BEFORE any census run**. Git timestamp is the
declaration. Trial family: **LDN-VT-01**.

Thesis: `research/candidates/london-value-traverse.md`, greenlit ANGUS 2026-08-04.
Feasibility done first on the **full gate stack** (`ldn_vt_profile_feasibility.py`), per the
LDN-DRIVE-01 lesson.

---

## 1. Scope — leg (a) only, and why

The candidate is three composable pieces. Feasibility settles which are testable:

| leg | claim | events 2025/2026 | status |
|---|---|---|---|
| **(a) Destination** | a naked POC beyond the Asian extreme is the rotation's magnet | 90 / 35 (reach ≤ 50pt) | **tested here** |
| (b) Verdict | Dalton's 80% rule — Asia outside prior value, London drives back in and holds | **4 / 1** | **UNTESTABLE**, reported below |
| (c) Path | LVN air pockets traverse fast to the next HVN | 72 / 38 (p10) | testable, **not** tested here |

**Leg (b) is dead on this sample and that is recorded now, not later.** Asia holds wholly
outside prior RTH value on 65/20 days, but a London close back *inside* the value area
happens on 4/1, and the thesis's ~45-minute hold on 2/0. This is mechanically explicable,
not a coding artifact: the median gap from the Asian edge to the value-area edge is
**43.8 points** against a median London range of **99.2 points**, so the traverse is a
genuine move that mostly does not complete inside our two hours.

Leg (c) is testable and deliberately left for a separate prereg — folding it in here would
double the trial count for a claim about a different mechanism.

Leg (a) is the thesis's headline: *"a naked POC ... holds resting two-sided interest and
demonstrably attracts price; when one sits within reach beyond the Asian extreme, it's the
rotation's magnet."*

## 2. Claim (falsifiable)

> On a day carrying a naked POC beyond the Asian extreme and within reach, once London
> prints a 1-minute close beyond that Asian extreme on the magnet side, price continues
> toward the magnet over the remainder of the session.

## 3. Specification — exactly this computation, no parameter searched

**Session window: 08:00–10:00 Europe/London**, converted per day via `london_window_et(day)`.
ET hours never hardcoded.

**Volume-at-price:** each 1-minute bar's volume spread uniformly across its `[low, high]`
range into **1-point buckets**. This is the approximation the thesis specifies and flags
("volume-at-price is an approximation from 1-min OHLCV — the fidelity question goes on the
trial ledger"). Profiles are built on RTH 09:30–16:00 ET.

**POC:** the highest-volume bucket of a session's profile.

**Naked POC:** a POC from one of the **20 sessions strictly before** the event day, whose
price has **not been traded through** by any session between its formation and the event
day. Nothing from the event day itself contributes to the naked list.

**Magnet:** the *nearest* naked POC lying beyond the Asian extreme — above `asia_hi` or
below `asia_lo`.

**Reach: 100 points.** Declared, not searched, and chosen on a stated principle: the median
London session range is **99.2 points**, so "within reach" is operationalised as *within one
typical London session's range*. Reach 50 and 200 run as a fragility ladder (§7), **not** as
alternative primaries.

**Event:** the first 1-minute **close** inside the window printing beyond the Asian extreme
**on the magnet side**. That close is `t`. One event per day.

**Direction:** toward the magnet. Magnet above → long; magnet below → short.

**Outcome:** `signed_ret` = (close at window end − close at `t`) × direction. Positive =
price continued toward the magnet. Measured strictly from `t` forward.

## 4. Causality audit (required, per `VERDICT-LDN-SWP-01.md` §4)

| variable | determined | before the outcome window? |
|---|---|---|
| daily profiles, POCs | sessions strictly before the event day | ✅ |
| naked status | traded-through check over sessions strictly before the event day | ✅ |
| Asia hi/lo | overnight, before the London open | ✅ |
| magnet identity & reach | fixed at the open from the above | ✅ |
| event minute `t` | the close that breaches the Asian extreme | ✅ |
| direction | by which side the magnet sits, known before `t` | ✅ |
| outcome | over (`t`, window close] | ✅ |

Nothing defining the event, direction or grouping is drawn from the interval measured. The
naked-POC list is the risk point in this candidate and is explicitly built from a strictly
prior window.

## 5. Eras

Discover 2025 / validate 2026-01..07, **plus the inverse pass** (§2.1); both directions must
agree. **2023/24 untouched** — asserted absent before computing. No holdout look.

## 6. Secondary — one, pre-specified: *do naked POCs actually attract?*

The thesis says naked POCs "demonstrably attract price". Tested directly with a
**distance-matched placebo**:

- **Magnet touch rate:** share of events where price reaches the naked POC over
  (`t`, window close].
- **Placebo touch rate:** the same measurement against a synthetic level placed at the
  **same distance** from the *opposite* Asian extreme, on the opposite side. Not a naked
  POC; identical distance.

If naked POCs attract, the magnet touch rate exceeds the placebo rate. If the two match,
the "magnet" is just distance — price reaches things that are close, POC or not. One
comparison, declared, no threshold tuned.

## 7. Fragility gate — runs FIRST

- Mean `signed_ret` recomputed with the 1, 3, 5, 10 largest-|signed_ret| events removed,
  plus 1/99-winsorised.
- Recomputed at **reach 50 and 200**.

**Sign flip at any trim depth ≤ 3 in either era, or across the reach ladder, kills the
family regardless of everything else** (§2.5).

## 8. Decision rules — three-way, declared in advance

Let `M` = mean `signed_ret`, `M₂₅` its 2025 estimate.

| outcome | condition |
|---|---|
| **PASS** | `M > 0` at p ≤ 0.05 one-sided in **both** eras, fragility clear, n ≥ 30 per era |
| **FAIL** | validate-era 95% CI on `M` **excludes** `M₂₅` and contains 0 or is negative — or fragility fires |
| **INCONCLUSIVE ON POWER** | neither; report minimum detectable `M` and events needed at 80% power |

Absence is an equivalence claim, never a bare failure to reject.

## 9. Mandatory reporting

Event counts per era at every rung of the reach ladder; the full fragility ladder whatever
it shows; power and minimum detectable `M`; magnet-vs-placebo touch rates; the `signed_ret`
distribution; and the **leg (b) counts** above so the untestable leg is on the record.

## 10. Trial accounting

**4 trials** into LDN-VT-01 (primary × 2 era directions, secondary × 2). London programme
running total: **28** (24 prior + 4). These count in the DSR denominator per §2.4. The reach
ladder adds no trials — it is the declared fragility check, not three primaries.

## 11. Known limits

- **L0 structure only.** No stops, targets or costs. The thesis's exits (scale out into the
  touch, runner into NY) are not modelled; holding to the window close is a measurement
  convention.
- **Volume-at-price is an approximation** from 1-minute OHLCV, as the thesis concedes. A
  footprint-derived profile (available 2025-06+) would move bucket volumes and hence which
  POCs exist. That fidelity question is real and untested.
- Leg (b) untestable on this sample; leg (c) untested and needs its own prereg.
- The thesis notes the full traverse "often finishes in NY" — our window closes at 10:00
  London, so a magnet reached after that is invisible here. This biases **against** the
  candidate and is stated up front rather than offered afterwards as an excuse.
- NY-canon input-family overlap: MEDIUM (overnight structure; NY reads daily POC in its
  reference set). The pairwise detector runs at validation, not here.
