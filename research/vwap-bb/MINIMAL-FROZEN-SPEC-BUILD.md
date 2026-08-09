# MINIMAL FROZEN SPEC — single stated build, population count only

> **SUPERSEDED, 2026-08-08.** "Minimal" here was read as "the 5 literal rows
> `STRUCTURAL-LEVELS-AUDIT.md` marked COMPUTED" — Angus corrected this: "minimal" means
> **everything genuinely implemented**, not that literal 5-row subset (which also, per that
> audit's own later errata, undercounted what's actually coded — daily VWAP's cluster-eligible
> band actually reaches ±3σ, not ±2σ as first reported). The corrected build, with the full
> current level set, is `IMPLEMENTED-LEVELS-LIMIT-FILL-BUILD.md`. **This document and its 988
> figure are kept, not deleted** — per standing practice, nothing gets discarded, and per Angus's
> own words: *"the earlier 988-trade build was a measurement under a misread instruction, not a
> rejected result. No outcome was computed, so nothing is consumed."* N_trials was, and remains,
> unaffected by either build.

**2026-08-08. Follow-up to Amendment 05 round 2, items 3-5.** A single build under one
explicitly declared reading of everything ambiguous, to answer one question: **how many trades
survive if the detector trusts only what is genuinely, fully implemented, entry fills the way the
spec's own words describe (a limit order), and the identity-churn forks are held at their current
code reading?** `minimal_frozen_spec_build.py`, `data/minimal_frozen_spec.json`.

**No outcome is computed.** Exit resolution (stop-vs-target) is used only to gate one-at-a-time
re-entry — the same instrumentation-without-exposure `invariants_2b._admit` already uses (its own
note: *"the release bar is recorded WITHOUT recording which side released it, so no outcome is
exposed"*). Nothing here is a win, a loss, a P&L, or an R-multiple outcome. **Not opened**: this
is a fresh build, not the discarded Stage 3 file.

---

## 1. Errata found while building this — FORK-SET-ENUMERATION.md's fork 1 had the wrong reading marked "(current)"

`vwapbb_signals.cluster_levels()` — the function both `spec_current.py` and `invariants_2b.py`
actually call — compares each new level only to the **last accepted member** of the running
cluster, not to every member. Direct test: `cluster_levels([(0,'a'),(4,'b'),(8,'c')], tol=5)`
returns one cluster spanning **0 to 8** (span 8, over the tolerance of 5) — mutual proximity could
never produce that. **The code is single-linkage chaining, not mutual proximity.**
`FORK-SET-ENUMERATION.md` row 1 had these backwards; corrected in place with an errata note
(§1-bis there). Nothing about the fork's existence or the 32-combination count changes, and no
prior admission list was built under the wrong reading — this only fixes a label.

## 2. What "the 5 implemented levels" was taken to mean, stated so the alternative isn't hidden

`STRUCTURAL-LEVELS-AUDIT.md` §2 marked exactly 5 rows **COMPUTED**: prior-day H/L, POC, 4h range
(recorded only — a covariate, not a menu entry; A9 already removed any gate on it), pullback
origin/B2 (a *selection rule* over the menu, not a level of its own — already subsumed by walking
the menu outward, which is what the code already does), BB MA.

**Taken literally, this restricts the two lists that matter to:**

| list | before | this build |
|---|---|---|
| `lv` (cluster-eligible) | BB MA, POC, daily VWAP mid/±1σ/±2σ/±3σ, NY VWAP mid/±1σ | **{BB MA, POC} only** |
| `menu` (target ladder) | daily VWAP mid/±1σ/±2σ, NY VWAP mid/±1σ/±2σ, POC, session hi/lo, prior-day H/L | **{POC, prior-day H/L} only** |

**Not restricted:** the §7 invalidation gate (NY VWAP ±1σ). That gate is fork 2, a validity check
using NY VWAP's σ, not a cluster/target candidate — one of the 18 audited *levels*. Fork 2 is
separately pinned to its current reading (same-side) by this build's own rule ("all 5 forks →
current"). Stripping it too would be a sixth, unrequested restriction, so NY VWAP's running mid
and σ are still computed and still gate candidates, exactly as today — they just never appear as a
cluster or target candidate.

**The alternative reading, NOT used here, flagged rather than silently rejected**: "implemented"
could instead mean "everything the code actually builds without qualification," which would keep
daily/NY VWAP mid and their ±1σ/±2σ tiers (genuinely computed, not gaps) and exclude only the
audit's seven newly-surfaced absences (weekly H/L, NY/daily VWAP ±3σ, the "structural" type,
pre-market H/L, 1h range, HTF-as-menu-level, "data extremes"). That build would look much closer
to the existing 1,472/1,423-trade populations and was **not** run — the literal 5-row reading was
used because it was the more precisely specified of the two and states its own restriction rule
without further judgement calls.

## 3. Fill semantics, declared explicitly (this is new — not inherited from PREREGISTRATION 4.2)

The one bar after the signal bar closes (`fill_bar`, same bar the current accounting rule already
uses) is checked for **single-bar true-limit reachability**, the same "reaches" test
`fill_fork_report.py` computed:

- long: fills **iff** `bar_low <= limit`; fill price = `min(bar_open, limit)` — the limit, or the
  open if the bar gapped through favourably (better than the limit)
- short: fills **iff** `bar_high >= limit`; fill price = `max(bar_open, limit)`
- **no fill → no trade**, full stop. No later bar is checked. `T_cancel` (§5.5) has no stated
  value and is disabled everywhere in this project (`FILL-MECHANICS-QUOTES.md` §2) — resting the
  order across more than one bar would require inventing a parameter the spec does not supply, so
  the single-bar window is the only reading available without fabricating one.

## 4. Forks — all five held at CURRENT, per the corrected `FORK-SET-ENUMERATION.md`

Cluster formation = single-linkage chaining (imported unmodified — not reimplemented, so this
build cannot silently drift from what the real code does). §7 invalidation = same-side band.
Range confluence minimum = 2. Front-run F = 2.0. Weekly H/L = absent (moot — already excluded by
§2's level restriction).

## 5. Result

```
workbench sessions 539   processed 501   excluded {'holiday / short session': 22,
                                                    'roll session': 8, 'session after roll': 8}

candidates reaching the fill decision : 2181
  filled (bar reached the limit)      : 988
  NOT filled (bar never reached it)   : 1193

ADMITTED-AND-FILLED TRADE COUNT: 988
clears 661? YES  (988 vs 661)
```

**988 trades. Clears 661.** Session accounting (539 total, 501 processed, same three exclusion
reasons in the same counts) matches `invariants_2b.build_trade_list()` exactly, confirming the
day-iteration and roll/mixed-contract handling was carried over unchanged — only the level lists
and the fill rule differ.

**No further reading given to this number.** Whether 988 is "enough," what population it should
be compared against besides the stated 661 threshold, and whether the literal or alternative
5-level reading is the one to build forward from are all decisions reserved, not made here.

## 6. N_trials

**Unaffected — this is a measurement, not a selection.** One configuration was built, under rules
stated in full before it ran (this document's §§2-4 were fixed before `main()` was called), and
one count was reported. No outcome was computed, no configuration was compared against another by
result, and nothing was chosen because of what it produced. This is the same kind of quantity the
original identity-churn admission-count sweep produced without consuming a trial. **N_trials: 1 of
5, unchanged.**
