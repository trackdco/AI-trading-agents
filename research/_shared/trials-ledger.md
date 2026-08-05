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

*(populated at Stage 2; every proposal listed, including pre-test discards with reasons)*

---

## PART 2 — PRE-REGISTERED HOLDOUT DIRECTIONS

*(written before holdout is touched)*

---

## PART 3 — OUTCOMES

*(written after the single holdout run)*
