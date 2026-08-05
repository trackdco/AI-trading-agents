---
date: 2026-08-07
kind: TRIALS LEDGER — synthesis sweep, 08:00–10:30 ET entries
status: PRE-REGISTRATION — written BEFORE any candidate was tested
---

# Trials ledger — synthesis sweep (08:00–10:30 ET)

**Every candidate proposed goes in this file, including any discarded before testing, with the
reason. The ledger count is the N for all multiplicity math. There are no silent discards.**

---

## PART 0 — PRE-REGISTRATION, fixed before any test was run

### 0.1 The entry window

> **Every entry occurs in 08:00:00–10:30:00 ET. Entries outside the window do not exist.**
> Exits follow the locked convention and MAY run past 10:30, up to the 16:00 ET cap.

### 0.2 The locked exit convention — binds every candidate

Target **2R** · break-even at **1R** · **no trailing** · **stop fills first** on a same-bar
conflict · horizon capped **16:00 ET** · R signed by direction · costs **$25/round-turn NQ at
$20/pt reported separately, never baked into R**.
Source: `research/zxcked/strategies/EXIT-CONVENTION-LOCKED.md`.

Each candidate keeps its **own stop rule** — the stop defines R and is part of the strategy.
Everything downstream of the stop is shared.

### 0.3 Data feasibility — measured, not assumed

| | |
|---|---|
| instrument | NQ 1-minute, `data/reference/nq_1m_master.parquet` |
| span | **2025-06-01 → 2026-07-15** (the footprint-covered window) |
| sessions with a **complete 151-bar** 08:00–10:30 window | **289** |
| sessions with **≥140 flow minutes** in the same window | **289** |
| flow coverage by month | complete, **including January 2026** |

Flow is read via `scripts.f2_oos_test.flow_frame()`, which rebuilds from the raw footprint files.
`output/fp_minutes.parquet` is **defective** (1 day for 2026-01 against 26) and is not used.

### 0.4 ⛔ THE SPLIT — declared here, never moves

| period | dates | sessions | share |
|---|---|---|---|
| **DISCOVERY** | 2025-06-02 → 2026-02-27 | **192** | 66.4% |
| **HOLDOUT** | 2026-03-02 → 2026-07-15 | **97** | 33.6% |

Boundary **2026-03-01**. Contiguous, non-overlapping, holdout is the most recent segment, both
periods are fully flow-covered. **This boundary is now fixed and may not be moved for any reason.**

### 0.5 ⚠️ A DATA TRAP FOUND WHILE SETTING THE SPLIT — and how it is handled

The repo holds two news calendars with **different inclusion criteria**, and they change over
exactly at the split boundary:

| file | span | contents |
|---|---|---|
| `config/news_calendar_hist.csv` | 2023-01-04 → 2026-01-28 | **529 rows, ALL tagged `high`** |
| `config/news_calendar.csv` | 2026-02-02 → 2026-07-16 | 236 rows — 116 `high`, 116 `medium`, 4 `holiday` |

Concatenating them naively (which is what `zxck_keyopen_baseline.calendar()` does) produces a
**fake regime change at 2026-02**: news-day rate in the 08:00–10:30 window jumps from **29% in
discovery to 74% in holdout**. That is an artefact of the source, not of the market, and it sits
directly on the split boundary. Any candidate conditioning on `news_day` would have been poisoned.

**Filtering to `impact == 'high'` is not enough** (26% → 51%): the newer file simply lists more
events.

**RESOLUTION — a canonical event whitelist, fixed here:**

```
Advance GDP q/q · Average Hourly Earnings m/m · CPI m/m · CPI y/y · Core CPI m/m
Core PCE Price Index m/m · Core Retail Sales m/m · FOMC Economic Projections
FOMC Meeting Minutes · FOMC Press Conference · FOMC Statement · Federal Funds Rate
ISM Manufacturing PMI · ISM Services PMI · Non-Farm Employment Change
Retail Sales m/m · Unemployment Rate
```

These 17 events are the **intersection of the two files' vocabularies** — every one appears in
both, so the definition does not change at the boundary. In-window releases: **137**, of which
**106 at 08:30** and **29 at 10:00**.

**Residual imbalance, stated as a limitation rather than papered over:** news-day rate is
**22.9% in discovery vs 35.1% in holdout**. Monthly counts show 3–6 canonical news days per month
through 2025 and 7–8 from 2026-03, which is more consistent with **under-coverage in the older
file** (2025-10 has 3, 2025-11 has 4, 2026-02 has 3 — implausibly few for a set containing CPI,
NFP, retail sales, PCE and two ISMs) than with a real change in release frequency.

**Consequences, binding on this sweep:**
1. Every candidate must state its news handling explicitly — **trade / skip / split, never silent**.
2. The news-day vs non-news split is **reported for every candidate** and read with this caveat.
3. **No candidate may use `news_day` as a tuned filter**, because the flag's own reliability
   differs across the split. A candidate whose *mechanism* is a release (lens C) must key on the
   canonical whitelist and say so.

### 0.6 Inference rules

- **Session-clustered** everywhere. Cluster-robust SE on session date with the finite-cluster
  correction. **Raw n AND effective n (sessions) reported for every candidate.**
- The 08:00–10:30 window is 151 minutes and will produce **overlapping setups**. Sessions, not
  trades, are the independent unit.
- **Bound-both-orderings** wherever intrabar sequence matters (`COMPONENTS §F00`). We hold no tick
  sequence. Never guess, never silently drop sessions.
- **Look-ahead audit on every flow feature before it is used** — the exact time boundary must be
  proven. `research/_shared/f2-h1-oos-test.md` records why: `retrace_ratio` failed this test on
  2026-08-07 and the pooled F2/H1 test was halted at Step 0.
- **BANNED: same-instrument delta SIGN confirmation of a structurally-defined move.** Circular —
  it removed 0 of 29 on `ash-unicorn-sb`. Magnitude is a separate question; sign is not a feature.
- **No fabricated data, no fabricated trades. BLOCKED is a valid result.**

### 0.7 The noise floor — design fixed before running

The search itself is simulated. The same 12-candidate selection procedure is run on
**mechanism-free controls**: random-direction entries matched for time-of-day, event count per
session, and the identical locked exit. Repeated enough times to estimate the distribution of
**"best-of-12 discovery expectancy"** under the null.

**Our best candidate's discovery expectancy is reported as a percentile of that distribution.**
If it sits inside the envelope, that is stated **before** any candidate is discussed on its merits.

### 0.8 Holdout protocol — one shot

Top **K=3** by discovery expectancy, subject to an **effective-n floor** (a candidate with a
single-digit session count does not qualify regardless of expectancy). Their pre-registered
directions are written to this ledger **before holdout is touched**. Run once. **Holm across the
3.** A candidate SURVIVES only if:

1. holdout expectancy is **positive after costs**, and
2. direction **matches the prereg**, and
3. the clustered result is **not attributable to the noise floor**.

**No re-runs. No tweaks after seeing holdout. No swapping in candidate #4 because #3
disappointed.** Failures are reported with the same prominence as survivors.

Survivors are promoted to **forward accumulation**, not declared edges.

---

## PART 1 — CANDIDATES

**LEDGER N = 12.** Three generator agents, distinct lenses, capped at 4 each. Every proposal is
listed, including the 12 discarded before testing — those cost no statistical power but they are
recorded so nobody rediscovers them.

### 1.1 The 12 trials

| # | id | lens | role | events | disc | hold | med stop | intrabar |
|---|---|---|---|---|---|---|---|---|
| 1 | `sw-onx-reclaim` | A | **primary** | 172 | 119 (115s) | 53 (52s) | 34.0pt | close |
| 2 | `sw-gap-nopart` | A | **primary** | 66 | 40 | 26 | 23.4pt | close |
| 3 | `sw-gap-nopart-INV` | A | *diagnostic* — the gate INVERTED | 86 | 59 | 27 | 29.9pt | close |
| 4 | `sw-open-drive-pcr` | A | **primary** | 101 | 75 | 26 | 51.5pt | close |
| 5 | `sw-cvd-div-reclaim` | B | **primary** | 312 | 215 (162s) | 97 (76s) | 16.7pt | close |
| 6 | `sw-thinbook-surprise` | B | **primary** | 194 | 132 | 62 | 17.2pt | close |
| 7 | `sw-precash-value-migration` | B | **primary** | 141 | 90 | 51 | 42.2pt | close |
| 8 | `sw-precash-price-migration-CTL` | B | *control* — price instead of VPOC | 122 | 73 | 49 | 39.4pt | close |
| 9 | `sw-0830-secondleg` | C | **primary** | 64 | 39 | 25 | 31.9pt | **limit** |
| 10 | `sw-0930-cashopen-carry` | C | **primary** | 67 | 45 | 22 | 61.5pt | close |
| 11 | `sw-0830-secondleg-CANON` | C | *consistency arm* | 28 | 17 | 11 | 41.6pt | limit |
| 12 | `sw-0930-carry-CANON` | C | *consistency arm* | 25 | 18 | 7 | 63.5pt | close |

Every count above was produced independently twice — once by the generator during design, once by
the harness implementation — and they agree exactly, including median stops to 0.1pt.

### 1.2 ⛔ PROMOTION RULE — fixed here, before any discovery outcome was computed

**Only the 8 PRIMARY candidates are eligible for the top-K=3 holdout.** The 4 diagnostic/control/
consistency arms (#3, #8, #11, #12) exist to falsify or contextualise their parents; promoting one
would be meaningless. **They still count as trials** — all 12 enter the noise floor's best-of-K and
all 12 count toward multiplicity.

**Effective-n floor for promotion: ≥30 discovery SESSIONS.** Sessions, not trades. #2 (40 sessions)
and #9 (39) clear it narrowly; nothing is excluded by it a priori.

### 1.3 Declared deviations, recorded rather than done quietly

**Lens C keys on the TAPE, not the canonical whitelist**, against §0.5. Reasons, with numbers:
the canonical-only version yields 17 discovery / 11 holdout events and is untestable; the
whitelist is an intersection of two incomplete files (the newer carries PPI, Unemployment Claims,
Philly Fed, Empire State and Durable Goods at 08:30, the older carries **none** of them); and the
tape gate is **more** split-stable than the canonical flag (26.6%→30.9% across the boundary vs
13.5%→19.6%). It is computed strictly from 08:00–08:30 bars, so it cannot carry a calendar-file
artefact by construction. External validation that it detects releases and not noise: it fires on
**16 of 37 discovery Thursdays** (weekly jobless claims, 08:30, calendar-certain) and **1 of 39
discovery Mondays** (no Monday 08:30 release exists). Trials #11 and #12 are the canonical-only
consistency arms, reported alongside and explicitly underpowered.

### 1.4 ⚠️ #9 AND #10 ARE NOT INDEPENDENT — declared before testing

85 distinct sessions fire at least one; **46 fire both** (28 discovery / 18 holdout); on every
shared session the two take the **same directional side**. Their logs are not independent
evidence. **If both reach the top-3 they are one bet with two geometries, not two bets**, and must
be reported that way.

### 1.5 ⚠️ A SECOND DATA DEFECT, found by Lens B and independently confirmed

`data/reference/cvd/README.md` describes a **day-level** price-band clean. That cannot separate
contracts during a quarterly roll, because the continuous 1-minute master switches contract inside
the day and the day band spans both.

Measured independently on the 06:00–11:00 ET slice: **4.53% of footprint rows and 2.42% of volume
sit outside their own minute's bar range**, concentrated on quarterly roll dates —
**2025-09-15 54.4% · 2025-12-15 51.1% · 2025-06-16 50.3% · 2026-03-16 40.3%**; 107 of 291 sessions
exceed 1%. Un-cleaned, a roll-week volume profile is roughly half back-month and its VPOC can land
hundreds of points outside the session's own range.

**Every volume-at-price computation in this sweep applies a MINUTE-level band clean**
(`price ∈ [bar.low − 1 tick, bar.high + 1 tick]` of that same minute). Aggregate per-minute
vol/delta are affected by <1% of volume, so `flow_frame()` is NOT retroactively changed — that
would silently alter already-committed results.

### 1.6 Pre-test discards — 12 of them, zero statistical cost

**Lens A (1).** `sw-thinsweep-openreclaim` — sweep of an Asia/London/PDH-PDL level in the thin
08:00–09:29 book, reclaimed after the cash open. Good mechanism, adequate count (92 sessions).
**Dies on geometry**: the thin book permits a 54.9pt median overshoot, so a stop just beyond the
level puts 43% of events under 15pt (the `zxck-ifvg-50` failure mode), while a stop beyond the
post-open extreme leaves the overnight-range draw at only **1.9 × risk** — i.e. **the locked 2R
target sits beyond the mechanism's own draw**. Adding a ≥2R draw gate leaves 25 disc / 19 hold.
*The pre-cash thin-book sweep is structurally incompatible with a fixed 2R exit on NQ.*

**Lens B (4).** Thin-vs-thick pre-cash extreme break — **278 of 289 sessions (96%) close through a
pre-cash extreme**, so the break is the norm, not an event, and both directional readings are
available, which means neither is a hypothesis. · Low-volume-node traversal — median vacuum width
**8.75pt**, smaller than any viable stop. · Average trade size — mean 1.396, sd 0.149, **no dynamic
range at all**. · Absorption in any form — LDN-FLOW-01 (AUC 0.462–0.557) and LDN-DEF-01 (AUC
0.451–0.515, all three measures sign-flip on the band ladder) already killed it at both
resolutions; no differentiator beyond "different session".

**Lens C (7).** 10:00 releases — canonical 20 disc / **8 hold**, and tape detection *fails* at
10:00 (ratio 2.24 non-release vs 2.64 release — no separation, the release is drowned by ambient
RTH volume). **This also explains why `zxck-10am-keyopen` landed exactly on the null: 10:00 is not
a liquidity event once the cash market is open.** · 09:30 auction-concession fade — degenerates
into "be in the market at 09:35" (90% of fills in 3 minutes), the `zxck-10am-keyopen` null. ·
Opening-range continuation — `orb-fvg-nyopen` already sampled it at n=1558 across 4 arms; a new arm
is a filter search on a retired card. · PDH/PDL sweep 08:00–10:30 — 20 disc / 8 hold after a risk
floor. · Pre-release drift reversal — median |drift| 10.8pt, needs a sub-10pt stop. · Turn-of-month
— n is fine (36/20) but direction is a constant LONG while NQ ran 21,304 → 29,690; **against a
random-direction noise floor an always-long candidate earns the drift, not the mechanism**. · OPEX
/ quarter-end / FOMC / roll week — 4–9 sessions each, dead on count. Roll is also undetectable:
`nq_1m_master.parquet` carries **no contract identifier**.

### 1.7 The binding arithmetic Lens C found, which explains its thin yield

| sub-window | median 1-min range |
|---|---|
| 08:00–08:29 | **6.8 pt** |
| 08:35–09:29 | 8.2 pt |
| 09:30–10:30 | 20.8 pt |
| the 08:30 bar, release day | **55.5 pt** (8.8× volume) |
| the 09:30 bar | **46.0 pt** (13.6× volume) |

A pre-09:30 entry needs ≥40pt of travel to make 2R; a post-09:30 entry with a noise-respecting stop
needs ≥90pt. **Every calendar *return* anomaly is 5–25pt on NQ — an order of magnitude too small
for this exit.** Only liquidity events displace price enough, and there are exactly two in the
window: 08:30 and 09:30. That is why Lens C collapsed to 2 candidates rather than 4.

---

## PART 2 — PRE-REGISTERED HOLDOUT DIRECTIONS

**Written 2026-08-07 after the discovery run and BEFORE any holdout data was touched.**

### 2.1 The discovery result, stated first because it governs how the holdout is read

**Best primary: `sw-precash-value-migration`, discovery expectancy +0.0968R.**
**Best-of-12 noise floor: median +0.3097, p75 +0.3956, p90 +0.4971, p95 +0.5611, p99 +0.7088.**

> ## ⛔ OUR BEST CANDIDATE SITS AT THE **1.5th PERCENTILE** OF THE NOISE FLOOR.
> **98.5% of random-direction searches over the same events would produce a BETTER winner than
> ours.** Not "fails to clear p95" — it is below the *median* of what chance produces, by a wide
> margin. This is stated here, before the holdout, so that nothing downstream can be read as
> rescuing it.

Only 3 of 8 primaries have positive discovery expectancy at all, and the largest is under +0.10R.

### 2.2 The three promoted, and their pre-registered directions

Top 3 by discovery expectancy among the 8 primaries; all clear the ≥30-session floor.

| # | candidate | disc exp | sessions | **PRE-REGISTERED DIRECTION** |
|---|---|---|---|---|
| 1 | `sw-precash-value-migration` | +0.097 | 90 | **LONG** when the 08:45–09:29 VPOC sits ≥15pt **above** the 08:00–08:44 VPOC; **SHORT** when ≥15pt below. Entry on the first retest of the later VPOC after 09:30. Expect **positive** holdout expectancy after costs. |
| 2 | `sw-onx-reclaim` | +0.059 | 115 | **FADE** the swept overnight extreme: **SHORT** after the overnight HIGH is crossed and reclaimed, **LONG** after the LOW is. Expect **positive** holdout expectancy after costs. |
| 3 | `sw-open-drive-pcr` | +0.033 | 75 | **CONTINUATION**: **LONG** when the 09:30 bar closes above the 08:00–09:29 range, **SHORT** when below. Expect **positive** holdout expectancy after costs. |

**Holm correction across these 3.** One shot. No re-runs, no tweaks, no substitutions.

### 2.3 Kill conditions already triggered IN DISCOVERY — recorded before the holdout

**`sw-gap-nopart` is DEAD by its own pre-registered kill condition.** Its generator declared:
*"the same test with the gate INVERTED produces an equal or better discovery expectancy"* would
prove the participation gate does nothing. Measured: gate **−0.115R**, gate inverted **+0.031R**.
**The inverted arm is better.** The low-participation gate is not merely inert, it is pointing the
wrong way. The candidate is not promoted and would not be promoted on any holdout result.

**`sw-precash-value-migration` beats its mandatory price-only control, but weakly**: VPOC arm
+0.097 vs price-only control +0.039. The generator pre-registered that *"the flow claim is only
supported if the VPOC arm beats the price arm"*. It does, nominally. Both sit deep inside the
noise envelope, so the comparison decides nothing on its own.

**`sw-0830-secondleg` is the worst primary in the sweep** (−0.296R, t_clus −1.40) and its
canonical-only consistency arm agrees in sign (−0.209R, n=17), so the tape gate is not the
problem — the mechanism is.

**Both Lens C candidates are negative**, and their canonical-only arms are negative too. The
08:30-release second-leg thesis and the cash-open-backlog thesis both fail in discovery.

---

## PART 3 — OUTCOMES

Full report: **`research/_shared/synthesis-sweep-2026-08-07.md`**

### ⛔ NOTHING SURVIVED.

| candidate | disc exp | hold exp | t_clus | p_holm | verdict |
|---|---|---|---|---|---|
| `sw-precash-value-migration` | +0.097 | **−0.068** | −0.18 | 1.000 | FAILED — sign flipped |
| `sw-onx-reclaim` | +0.059 | **+0.064** | +0.56 | 0.858 | FAILED |
| `sw-open-drive-pcr` | +0.033 | **−0.217** | −0.77 | 1.000 | FAILED — sign flipped |

**Best-of-12 noise floor: median +0.3097, p95 +0.5611. Our best discovery candidate reached
+0.0968 — the 1.5th percentile.**

**Order flow: no improvement.** Every clustered 95% CI straddles zero in both periods, and the
flow-based group is worse than the price/structure group in both (disc −0.070 vs −0.037; hold
−0.111 vs −0.102).

**No candidate promoted to forward accumulation.** Four new hypotheses logged as UNTESTED, none
testable on the 289 sessions used here.
