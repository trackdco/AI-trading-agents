---
date: 2026-08-07
status: FINDING — yesterday's POC/VAH/VAL change nothing for London (−3.64 → −3.66 net
  pt/trade, paired −0.01 at T −0.09), and the reason is structural rather than statistical:
  Angus's §9 rule requires BOTH a BB basis and a VWAP band in the crossed cluster, so a
  POC-family level can never be the reason a trade happens. 75.7% of the triggers the new
  levels generate are vetoed by that rule. Testing §7 properly requires changing §9 — an
  ANGUS decision, not an implementation detail.
tags: [london, canon, volume-profile, level-menu, confluence, era-consistency, open-question]
sources: ["output/l2_outcomes_london_fit_pp_EC_rr0.parquet", "output/l0_triggers_london_fit_std_pp.parquet",
          "output/london_rrfloor_compare.md", "research/findings/T1-T5-volume-profile-nodes.md",
          "src/backtest/engine.py:942", "src/engine/snapshot.py"]
---

# Yesterday's levels can't trade, because the entry rule doesn't recognise them

Handoff §12 step 3. `research/findings/T1-T5-volume-profile-nodes.md` measured that
yesterday's high-volume nodes hold price ~7% longer than prices 20pt either side,
era-consistent (1.078 / 1.058), growing with band width. `_gather_levels` exposed only the
CURRENT session's POC; VAH/VAL reached the target menu but never the cluster candidates, and
yesterday's profile was absent from both. So the levels with the only holding power we have
measured were not levels we could ever trade off. This adds them to both, as a new arm.

## The answer: nothing moves

| metric | 2R floor (shipped) | next structural (rr0) | **+ prior profile** |
|---|---:|---:|---:|
| N setups | 719 | 667 | **680** |
| **net pt/trade** | −3.69 | −3.64 | **−3.66** |
| T | −6.06 | −6.01 | −6.28 |
| green days | 32% | 35% | **35%** |
| worst rolling 10d | −368 | −414 | −399 |
| target-hit (pure) | 2.9% | 29.2% | 28.4% |
| value of a target hit | +21.14 pt | +2.99 pt | **+2.54 pt** |

**Paired on the 636 setups both arms traded: −0.01 pt, T −0.09, 96.7% of outcomes
identical.** By era: 2025 −1.72 → −1.88, 2026 −6.78 → −6.62. Neither direction, neither era,
nothing.

## Why — and this is the part worth keeping

The census change was real and clean. L0 went from 8,723 to **9,805 triggers over the same
264 sessions (+12.4%)**, 97.6% of baseline triggers survived, and **96.8% of the 1,291 new
triggers cite a prior_ level**. The levels genuinely produce triggers.

Then the engine throws three quarters of them away. Of the **371 new displacement
candidates**:

| cluster types | n | passes §9? |
|---|---:|---|
| `bb+poc` | 178 | **no — no VWAP** |
| `poc+vwap` | 104 | **no — no BB** |
| `bb+poc+vwap` | 83 | yes |
| `bb+vwap` | 6 | yes |

**Only 24.0% carry both a BB basis and a VWAP band, and 75.7% are vetoed `vetoed_bb_vwap`.**
Just 67 of the 371 (18.1%) ever reach an outcome. On the whole displacement census the veto
count nearly doubles, 348 → 651, while outcomes move 1,953 → 1,963.

`src/backtest/engine.py:942` is Angus's own §9 v1.1 ruling:

```python
# §9 v1.1 (ANGUS): NO TRADE unless BOTH BB and VWAP are in the crossed cluster.
if cfg.require_bb_vwap and t.cluster_types and not {"bb", "vwap"}.issubset(t.cluster_types):
```

A prior-session level is typed `poc` — deliberately, so it extends the POC family rather
than inventing a confluence axis (see `prior_profile_levels`). But that means it is neither
a `bb` nor a `vwap`, so **it can never be the reason a trade happens.** It can only ride
along inside a cluster that already had a BB and a VWAP in it — where, by construction, it
was never needed.

The target side says the same thing more quietly. Only **154 of 5,659 outcomes (2.7%)**
actually aimed at a prior-profile level (82 VAH, 67 VAL, 5 POC), and where they did, the
value of a target hit *fell* (+2.99 → +2.54). With the floor at 0 the resolver takes the
nearest level in the menu, and yesterday's profile is rarely the nearest.

## What this does and does not settle

**It does not falsify §7.** T1–T5 measured that these levels hold price, and nothing here
contradicts that. What is measured here is that **the current entry rule cannot express
them.** Those are different claims and conflating them would kill a live idea on evidence
that does not bear on it.

**It does settle §12 step 3 as posed.** Adding the levels to the menu, with the strategy
otherwise unchanged, is worth −0.01 pt/trade. That question is closed.

**The open question is now §9, and it is Angus's call, not an implementation detail.** The
rule says BB *and* VWAP. Yesterday's POC/VAH/VAL are a third thing. To find out whether §7's
holding power is tradeable, the rule would have to admit a POC-family level as one of the
two required types — e.g. "any two distinct types" instead of "bb and vwap specifically",
which the 178 `bb+poc` and 104 `poc+vwap` clusters would then make available. That changes
the entry definition of the whole strategy, so it is not something to slip in behind a flag.

Recorded, not actioned. The arm is built and gated; flipping §9 is one config line and one
re-run away whenever he wants it.

## Gate record

- **L0 parity, flag OFF:** re-detected 2025-06-10 / 2025-11-05 / 2026-05-13 — census
  CONTENT-IDENTICAL to the committed baseline, 108/108 triggers, every column. NY cannot
  move; `include_prior_profile` defaults false.
- **Full suite:** 406 passed. The one failure (`build_ny_substrate.canon_config`) is NY-side
  and pre-existing — verified failing identically on a stashed pristine tree.
- **Arm is genuinely active:** 154 `prior_profile_*` targets in the book, 0 in the baseline.
- **Dedup re-derived per arm:** 1,334 VWAP-ruled setups (vs rr0's 1,347, baseline's 1,399).

### One that nearly shipped as a null

The first L2 run of this arm returned **100.0% identical on all 636 common setups**. Two
thirds identical is plausible; every single shared trade is not, so it was treated as a bug
rather than a finding — and it was one. `--arm _pp` selected the arm's census, but L2 forced
nothing, so `default_target_resolver` → `build_snapshot` read the config default and built
the SHIPPED menu: zero `prior_profile_*` targets across 5,683 outcomes. The arm was testing
half its own hypothesis and would have read as a clean negative. `--arm _pp` without
`--prior-profile` is now a hard error.
