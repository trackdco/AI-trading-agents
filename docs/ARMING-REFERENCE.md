# ARMING REFERENCE — rebuilt canon, NY pre-market + golden window

**Status: NOT ARMED. This document does not arm anything.** Arming requires Angus's token
against a certified commit (`src/live/arming.py`, two-party). What follows is the package
that has to be signed off *before* that step, plus an explicit list of what is still
unwired — read §5 before deciding anything.

Companion docs: `docs/CANON.md` (what the canon is), `scripts/funded_book.py` docstring
(the spec), `docs/CANON-QA-LOG.md` (why each rule exists).

---

## 1. What will run

| Layer | Module | Rule |
|---|---|---|
| Decision | `src/canon/scorer_ny.py::NYScorerV2` | pre 08:00–09:30 `W==1` · gold 09:40–10:30 `D==1` + wall-quality cut · risk 7–60pt |
| Scores | same | gold `2D+Tc+AGE+TRIG+T2` · pre `2W+G+F` (frozen; thresholds read from `config/live_thresholds.json`, never restated) |
| Tiers | same | gold ≤3→0.5 / 4→1.0 / ≥5→1.5 · pre 2→0.5 / 3→1.0 / 4→1.5 · **elite 2.0x** gold & TRIG & LONSLOPE & `struct_event=="broke"`, max 1/day |
| Budget | same | realized losses + in-flight risk + new risk ≤ budget · budget = base × 16/3 · soft de-risk at −35% of budget · half size below $1k buffer |
| Sizing | `src/canon/gate_evidence.py` | imports the profile from the scorer — one implementation, no drift |
| Order life | `src/canon/order_watch.py` | **no distance cancel**; each order dies at its own session end; struct event tracked bar-by-bar |
| Backstops | `src/live/risk.py`, `src/canon/spine.py` | account-level, above the canon budget (§3) |

Profiles: **`lucid`** (base $150 → $75/150/225/300, budget $800) and **`scaled600`**
(base $150 +$75 per $2k of buffer past +$3k, cap $600; budget and soft scale with the base).

---

## 2. Conformance evidence

`tests/test_canon_scorer_ny.py` — 18 tests, all passing. The live scorer is driven through
the real protocol (`start_day` / `evaluate` / `commit` / `on_exit`) over every row of
`output/aikido_{fit,holdout}.parquet` and must match `scripts/funded_book.py` **exactly**:
same trades, same tier, same risk dollars, same micros, same P&L, on both spans and both
profiles.

The check is strong because the scorer **re-derives** every gate from raw depth/flow columns
rather than reading the parquet's precomputed `valid` / `gold_score` / `pre_score`. Agreement
therefore proves the live re-derivation of W, D, the wall-quality cut, the scores and the
tiers — not merely the arithmetic downstream of them.

Reproduced from the live path: fit **+$90,015**, holdout **+$56,409** (lucid).

### Two defects this conformance work found

1. **`funded_book.load_book` sorted with an unstable sort.** Same-minute fills are common
   (sibling triggers off one cluster) and pandas' default quicksort ordered those ties
   arbitrarily — which silently decided *which* trade of a tied group received the day's
   single elite 2.0x slot. Fixed to a stable sort (ties resolve to detection order, which is
   what the live feed sees). Effect: +$90 fit / +$1 holdout on lucid, +$512 / +$1 on
   scaled600; **no risk metric moved at all** (worst day, maxDD, min buffer, green months all
   identical). The pre-fix figures $89,925 / $56,408 / $320,150 / $188,324 are superseded.
2. **Two thresholds were restated instead of read.** An early draft of the scorer hardcoded
   G at 0.107 (that is VWAPD's cut point, a different bit) and AGE at 3.0 (the real value is
   136.5). The conformance replay caught both immediately. The scorer now imports
   `scripts.live_thresholds.TH`, the same source the batch reads.

---

## 3. Behavioural changes vs the currently-deployed stack

Each of these is a live-visible change and is why this document exists.

| # | Change | Why | Risk if wrong |
|---|---|---|---|
| A | **Entries uncapped.** No 2/day slot, no nth-escalation, no day ladder, no governor, no cold trail. | The shared cap was the original defect; uncapped measured strictly better once the wall cut landed. | More trades/day than the old stack ever placed. Capacity is now the budget. |
| B | `RiskLimits.max_trades_per_day` default **3 → None**. | The old 3 was a backstop above a 2/day engine cap that no longer exists. Against a ~4/day book it would announce a halt on most days and stand the account down mid-session. | **This was the single most dangerous stale default.** |
| C | Spine `daily_loss_halt_r` **−4R → −8R**. | −4R against the $150 base is −$600, *below* the canon's own $800 budget — an outer guard that front-runs the inner one truncates the measured book. −8R is exactly 1.5× the budget at every base. | A halt inside the budget silently trades a smaller book than the one validated. |
| D | **No distance cancel.** Orders live until their session window ends. | The 22pt `t_cancel` measured inverted: kept −0.180R, killed +0.015R. | Orders rest longer; more fills. |
| E | **Per-session window end** (pre 09:30, gold 10:30). | One global window cannot serve both. | An order outliving its session is an unmeasured trade. |
| F | Gold window **09:40–10:30** (was 09:40–10:00); **no 09:55–10:00 dead zone**. | The rebuilt canon was validated without one. | — |
| G | Sizing base **$200 → $150**, ladder is now tier × base. | The $200 schedule belonged to the broken canon. | Every order size changes. |
| H | DD ramp: **half size below $1k buffer**, instead of a linear taper to zero between $1,500 and $100. | The half-size ramp is what the rebuilt book was validated with (and it is dormant across all 19 months). | **Needs your ruling — see §5.** |

---

## 4. Pre-arm gate checklist

| Gate | Requirement | State |
|---|---|---|
| R1 | Live scorer reproduces the shipped book on both spans, both profiles | ✅ 18/18 |
| R2 | Sizing schedule has exactly one implementation | ✅ `gate_evidence` imports the profile |
| R3 | No trade-count cap anywhere in the risk path | ✅ pinned by test |
| R4 | Account backstops sit above the canon budget | ✅ pinned by test, both profiles |
| R5 | No distance cancel by default | ✅ pinned in `order_watch` and `trade_lifecycle` |
| R6 | Micros never round to zero | ✅ |
| R7 | Absent `struct_event` never escalates size | ✅ |
| R8 | Full suite green | ⚠️ 720 pass, 2 fail — both long-standing and unrelated (`london_depth.DIR`, `build_ny_substrate.canon_config` attribute drift), confirmed failing before any of this work |
| R9 | **Runner cut over to the new scorer** | ❌ **NOT DONE — see §5.1** |
| R10 | Angus's token against a certified commit | ❌ yours to issue |

---

## 5. What is NOT done

### 5.1 The runner still sources verdicts from the OLD canon — blocking

`src/desk/canon_runtime.py` shells out to the old canon scripts and reads
`output/canon_book.parquet`. `route_b` consumes those verdicts. **Nothing in the live path
calls `NYScorerV2` yet.** The decision core is built and proven; the cut-over is not written.

Until that lands, arming would arm the *old* canon. The stack must stay disarmed.

Remaining work: a `VerdictSource` that runs `NYScorerV2` off the live feature stream, plus
per-day `start_day(buffer)` from the account's trailing line, plus `commit` / `on_exit` wired
to fills and exits.

### 5.2 The elite tier will not fire until `struct_event` is plumbed through

`OrderWatch` now tracks it (mirroring L1 expression-for-expression, tested), but nothing
passes it into the verdict the scorer sees. Degradation is safe and deliberate — absent
evidence sizes at the trade's own tier, never 2.0x — but the live book will be slightly
smaller than the validated one until this is connected. ~6% of trades.

### 5.3 Your ruling needed: the deep-buffer ramp (change H)

Between **$100 and $1,000** of remaining drawdown the rebuilt canon takes **half-size**
trades; the old canon tapered to zero and refused. Below $100 the spine hard-halts either
way. The half-size rule is what was validated — but it is untested in that region because it
never fired in 19 months of history. If you want the old refusal behaviour near the floor,
say so and it becomes a one-line floor in `base_dollar`.

### 5.4 London

Still the old canon, still Brake's rebuild. `LondonScorer` is untouched and must not be
armed. If the live stack would trade London, it stays disarmed until Brake's book lands.

---

## 6. Arming procedure (unchanged, for reference)

1. Pat confirms in writing, per PROMOTION-GATE.
2. Angus commits `config/arming.yaml` with the token SHA-256, the certified commit, and the
   account string.
3. On the box: `canon_run --arm`, present the phrase.
4. `verify_for_arming` enforces that HEAD *is* the certified commit (or differs only in
   `config/arming.yaml`). Any other file in that diff refuses the arm.

Every check fails closed, and a refused arm never falls back to a shadow run.
