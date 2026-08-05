# PRE-REGISTRATION — NYA-SB-01: ash10hazard silver-bullet model

Filed per `VALIDATION-PROCESS.md` §1, **BEFORE any outcome is computed**. Git timestamp is
the declaration. Trial family: **NYA-SB-01**. Programme NY, researcher brake.

Spec source: `research/candidates/ash10hazard-unicorn-silver-bullet.md` rev d (8 transcripts).
Feasibility on the full gate stack first (`scripts/nya_sb01_feasibility.py`): **73 / 72**
entries — clear of n ≥ 30 in both eras.

---

## 1. ⚠️ THIS IS NOT THE MODEL AS TAUGHT — read before interpreting any result

Three declared components **cannot** be computed here:

| component | why omitted |
|---|---|
| inverse **order block** pairing | he never defines how to identify an order block, in any of 8 videos |
| **ES leading trigger** | entry fires on ES tapping its FVG *before* NQ `[qngA8aIfV0M @ 08:01]`; **we hold no ES data** |
| multi-timeframe **bias** filter | per-timeframe rule stated, aggregation rule never stated |

**Consequence under §5.9.1** — which kills at census only when the claimed behaviour *"literally
does not happen — tested AS TAUGHT, mandatory triggers included"*:

> **A NULL RESULT HERE CANNOT KILL THIS CANDIDATE.** It would establish only that the
> mechanisable core is insufficient on its own. A PASS, conversely, *is* meaningful — it
> would mean the core works even stripped of three filters he considers necessary.

This asymmetry is declared now, not after seeing the number.

## 2. Claim (falsifiable)

> Inside his macro windows, after a liquidity sweep → market-structure shift → FVG, price
> returning to fill that FVG goes on to reach a 2R target before hitting a structural stop,
> at a rate above the 33% break-even required at 1:2.

His related claim, the only quantified one captured: *"Nine times out of 10 it's going to go
to that draw if the model does play out"* `[1cMWnAxElA0 @ 06:30]` — conditional, so not a
win-rate claim. `[trader-claimed, unverified]`

## 3. Specification — exactly this, nothing searched

**Windows (ET, mandatory per `qngA8aIfV0M @ 03:00`):** 09:45–10:15, 10:45–11:15,
11:45–12:15, 13:45–14:15. **12:45–13:15 excluded — he skips it.**

**Sweep:** price trades through a 15-min fractal swing high/low (k=2, frozen before the
window opens) or an Asia/London session extreme.
**MSS:** a 1-min close beyond the most recent opposite extreme in the 20 bars before the sweep.
**FVG:** 3-bar gap from the displacement leg — bearish `bar[j-2].low > bar[j].high`.
**Entry `t`:** price returns to the near edge of that FVG.
**Stop:** the swept extreme (the structural invalidation).
**Target:** 2R from entry. **One trade per macro window; max 4/day.**
**Daily stop:** after 2 losing trades the day ends `[qngA8aIfV0M @ 00:52]`.

Exit resolution uses 1-minute bars; if stop and target are touched in the same bar the
**stop is assumed first** (conservative, declared).

## 4. Causality audit

| variable | determined | before outcome? |
|---|---|---|
| macro window | clock, fixed in advance | ✅ |
| swing levels | frozen before the window opens | ✅ |
| session extremes | complete before 09:30 | ✅ |
| sweep / MSS / FVG / entry `t` | all at or before `t` | ✅ |
| stop, target | from levels known at `t` | ✅ |
| outcome | strictly after `t` | ✅ |

## 5. Eras

Discover **2025-07-01 → 2025-12-31**; validate **2026-01-01 → 2026-07-15**. Both directions
must agree. **Sealed 2023/24 untouched** — the span does not reach it.

## 6. Primary and decision rules

`WR` = share of entries reaching 2R before the stop.

| outcome | condition |
|---|---|
| **PASS** | `WR > 33%` at p ≤ 0.05 one-sided in **both** eras, fragility clear, n ≥ 30 each |
| **FAIL** | validate-era 95% CI excludes the discover estimate **and** lies at or below 33% |
| **INCONCLUSIVE ON POWER** | neither; report minimum detectable WR |

Per §1, a FAIL is **blocked from killing the candidate** by the §5.9.1 caveat in §1 above; it
would be recorded as "mechanisable core insufficient", not "model dead".

## 7. Fragility gate — runs FIRST

WR recomputed dropping the best/worst 1, 3, 5 trades; and per macro window. A result that
depends on a single window is reported as such.

## 8. Secondary — one, declared

**Does the macro gate earn its place?** Same stack run in the four 30-min windows *offset by
one hour* (10:45→11:45 etc. shifted to non-macro clock times). If the macro windows carry no
advantage, that is a finding about the framework, not about him. No threshold tuned.

## 9. Trial accounting

**4 trials** (primary × 2 eras, secondary × 2), appended to `output/trial_ledger.parquet`
with `programme=NY, researcher=brake`. Merged ledger moves **52 → 56**. Per §6.0 the bar
reads from the merged article.

## 10. Known limits

- L0/L1 structure only: fixed 2R, structural stop, **no costs**. Commission and slippage
  come at the next rung.
- Three components omitted (§1) — the binding limit on interpretation.
- The sweep gate accepts any of ~10 levels, so it fires on nearly every window; the binding
  gates are MSS → FVG → fill.
- Same-bar stop/target ambiguity resolved against the trade.
