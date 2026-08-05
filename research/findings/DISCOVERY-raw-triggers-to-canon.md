# FROM 19,137 RAW TRIGGERS TO A 763-TRADE LIVE BOOK
## The discovery methodology, with the real numbers

Written 2026-08-05 by the rebuild chat. Every number here was **recomputed from the
committed artifacts today**, not quoted from memory or from prose. Where a shipped
document disagrees with the artifact, the artifact wins and the disagreement is flagged.

Companion to `FRAMEWORK-validation-methodology.md` (the gate architecture). That
document says *how to be disciplined*. This one says *what we actually searched, what
survived, what died, and how we told the difference*.

---

# PART 1 — THE FUNNEL

The depth benchmark every future candidate gets held to. Recomputed from
`output/l0_triggers_*.parquet`, `l2_outcomes_*.parquet`, `l3_scored_*.parquet`,
`aikido_*.parquet`, `aikido_cr_*.parquet`.

| stage | gate applied | FIT | HOLDOUT |
|---|---|---|---|
| **L0 census** | none — every structural trigger | **19,137** | **10,397** |
| L2 filled | the limit actually filled | 12,131 (63.4%) | 7,513 (72.3%) |
| in canon windows | pre 08:00–09:30 / gold 09:40–10:30 | 8,347 | 5,128 |
| risk band | stop 7–60pt | **3,714** (−4,633) | **1,722** (−3,406) |
| L3/L4 valid | W / D gates + score thresholds | **1,874** | **929** |
| wall-quality cut | `dep_wall_below_d ≥ 2.75` AND `WALLSZ` | **956** (−918) | **637** (−292) |
| one-per-level | rule L (3pt / same-stop dedupe) | **763** (−193) | **515** (−122) |

**Survival: 4.0% fit, 5.0% holdout.**

**L0 composition (fit):** 10,382 long / 8,755 short · by timeframe 3min 5,329 / 5min
4,838 / 2min 4,756 / 1min 4,214 · by kind `rejection_block` 13,569 / `displacement`
5,568.

**Why the 36.6% that never filled matters.** They are not discarded — they are recorded
with a *reason*, and the reason distribution is itself a diagnostic:

| L2 status | fit | holdout |
|---|---|---|
| `outcome` (filled, walked to exit) | 12,131 | 7,513 |
| `vetoed_bb_vwap` | 3,790 | 1,061 |
| `cancelled_window_end` | 1,860 | 1,022 |
| `vetoed_news_preopen` | 869 | 490 |
| `vetoed_bad_geometry` | 193 | 146 |
| `vetoed_rr_floor` | 158 | 98 |
| `vetoed_window` | 136 | 67 |

**Framework requirement:** a candidate never silently disappears. Every trigger carries
a terminal status, and the status distribution is reported at every stage. A funnel that
only reports survivors cannot tell you whether your gate is selective or your data is
broken.

**The two brutal stages.** The **risk band alone kills 55%** of in-window fills
(8,347 → 3,714), and the **wall-quality cut halves it again** (1,874 → 956). If a
strategy cannot survive that attrition and still leave a tradeable book, it had volume,
not edge.

---

# PART 2 — THE COMPLETE VARIABLE LIST, BY CLASS, WITH VERDICTS

16 checks were put on trial. **Three carry the edge. Thirteen are noise or worse.**

## 2.0 How the trial was run (reproduce this exactly)

Source: `scripts/l3_check_trial.py`. Recomputed here on `output/l3_scored_{span}.parquet`.

- **Population:** all L3 candidates in the **risk band 7–60pt**, split by session.
- **Each check is evaluated ALONE**, with its **frozen threshold** from
  `config/live_thresholds.json` — never a threshold re-derived during the trial.
- **Verdict basis:** WR and mean R with the check **ON** vs **OFF**, plus **lift_R =
  R_on − R_off**, and **fire rate** (how often it's ON).
- **NaN = "stood down" is excluded from BOTH arms.** A check that cannot be evaluated on
  a row contributes to neither side. This is essential — counting NaN as a fail turns
  "no data" into "bad signal".
- **Thinness guard:** fewer than 15 rows on either side → reported as `thin`, no verdict.
- **Era split:** 2025 vs 2026 within fit, then the sealed holdout separately.
  *(Note: the holdout frame labels its era column "2026" — an artifact of
  `era = 2025 if day[:4]=="2025" else 2026`. The holdout rows are 2023/2024 days.)*

**The survival rule: a check must point the same way in EVERY era.**

## 2.1 THE FULL TABLE — lift_R by era (positive = the check adds value)

### PRE-MARKET checks

| check | what it measures | fit 2025 | fit 2026 | HOLDOUT | verdict |
|---|---|---|---|---|---|
| **W** | **no depth wall BEHIND the trade** | **+0.488** | **+1.272** | **+0.836** | **SHIPPED — carries pre-market** |
| F_ | fill-minute delta confirms direction | +0.041 | +0.338 | +0.001 | weak; kept in score |
| Tp | 15-min delta, direction-signed ≥ −61.0 | −0.005 | +0.371 | +0.177 | era-unstable; NOT in shipped score |
| G | entry vs VWAP in SD, signed ≥ −0.768 | −0.011 | +0.184 | **−0.228** | **in score despite negative holdout — see §2.4** |
| C | session CVD confirmation | −0.083 | −0.262 | −0.144 | **KILLED — negative in every era** |

W's WR on/off: **38.5%/24.1%** (2025), **46.9%/26.2%** (2026), **61.2%/32.3%** (holdout).

### GOLD checks

| check | what it measures | fit 2025 | fit 2026 | HOLDOUT | verdict |
|---|---|---|---|---|---|
| **D** | **a depth wall EXISTS AHEAD** | **+0.875** | **+0.810** | **+0.806** | **SHIPPED — carries gold** |
| **WALLSZ** | **wall ahead ≥ 7 contracts** | **+0.667** | **+0.495** | **+0.749** | **SHIPPED — the wall-quality cut** |
| Tc | 15-min delta confirmation bit | −0.022 | +0.096 | +0.183 | weak; in score |
| AGE | minutes since the extreme ≥ 136.5 | +0.034 | +0.155 | −0.007 | marginal; in score |
| TRIG | trigger density (30m) > 11 | +0.016 | +0.312 | +0.261 | weak in 2025; elite limb |
| T2 | fill-delta conf OR 5-level book opposition | +0.050 | +0.158 | −0.014 | marginal; in score |
| BIGFD | \|fill delta\| ≥ 173 | +0.054 | +0.183 | −0.027 | marginal |
| VWAPD | entry vs VWAP SD ≥ 0.107 | +0.138 | +0.026 | **−0.201** | negative on holdout |
| LONSLOPE | London cum-delta OLS slope ≥ −0.0961 | **−0.086** | +0.257 | **−0.117** | **negative in 2 of 3 — yet an elite limb, see §2.4** |
| X | Bollinger band-width state ≥ 4.117 | +0.014 | **−0.179** | −0.031 | **KILLED — era-flip** |
| PAQ | net path efficiency (30m) ≥ 0.0607 | −0.001 | −0.025 | −0.110 | **KILLED — flat-to-negative everywhere** |

D's WR on/off: **46.9%/12.1%** (2025), **41.8%/16.8%** (2026), **50.6%/20.4%** (holdout).

## 2.2 The headline result, stated bluntly

**Three variables out of sixteen produce a lift above 0.4R in any era: W, D, WALLSZ.
All three are DEPTH variables. Every one of the thirteen others sits inside ±0.32R and
most flip sign across eras.**

The strategy's entire edge is: *is there resting liquidity where it matters?*
- **Gold** wants a wall **ahead** — something for price to reject off / a magnet to trade into.
- **Pre-market** wants **no wall behind** — nothing to stop the trade running back through you.

**Raw structure alone breaks even.** The trigger logic (rejection blocks, displacements,
multi-timeframe confluence) generates the *population*; it does not generate the *edge*.
That distinction is the single most transferable finding in this document.

## 2.3 Kill/keep precedent record

| variable | fate | reason class | the numbers |
|---|---|---|---|
| C | **killed** | every-era-bad | −0.083 / −0.262 / −0.144 |
| PAQ | **killed** | every-era-bad | −0.001 / −0.025 / −0.110 |
| X | **killed** | era-flip + thin fire rate (8–13%) | +0.014 / −0.179 / −0.031 |
| Tp | **not scored** | era-flip (flat 2025) | −0.005 / +0.371 / +0.177 |
| LONSLOPE | **demoted, retained as elite limb** | era-flip, negative 2 of 3 | −0.086 / +0.257 / −0.117 |
| VWAPD | **demoted** | holdout-negative | +0.138 / +0.026 / −0.201 |
| BIGFD | **demoted** | holdout-negative, marginal | +0.054 / +0.183 / −0.027 |
| AGE, T2, Tc, F_ | **retained, weak** | small positive, mostly consistent | all < ±0.2R |
| G | **retained in score** | **holdout-negative — flagged** | −0.011 / +0.184 / −0.228 |
| **W, D, WALLSZ** | **shipped, load-bearing** | large + every-era-consistent | +0.5 to +1.3R |

**The four reason classes worth encoding in a framework:** *every-era-bad* (kill),
*era-flip* (kill or demote — never ship), *too-thin* (no verdict, fire rate or n too
low), *holdout-negative* (demote; retain only with an explicit stated reason).

## 2.4 Two honest tensions in the shipped canon

These are real and were surfaced by recomputation today. Neither is fatal; both should
be known.

1. **LONSLOPE is a required limb of the ELITE 2.0× sizing combo** (`gold AND TRIG AND
   LONSLOPE AND struct_event=="broke"`) **but as a standalone check it is negative in
   2025 (−0.086) and negative on the holdout (−0.117).** It survived as part of a
   *combination* that was validated jointly, not as a solo check. That is defensible —
   interactions can be real where main effects aren't — but it means the elite tier rests
   partly on a variable that fails the standalone survival rule.
2. **G sits in the pre-market score (2W + G + F) but is negative on the holdout
   (−0.228).** The pre score is dominated by the doubled W term, which is why the pre
   book still validated; G is contributing noise at best.

**Framework requirement:** when a variable enters via a *combination* rather than
standalone survival, record that explicitly and hold the combination to a permutation
null. Otherwise a failed variable enters through the back door and nobody remembers.

---

# PART 3 — ORDER-FLOW CONFIRMATION (and the honest verdict on it)

## 3.1 The variables

All computed **as-of clean** — truncated at the fill minute, nothing after it.

| variable | definition |
|---|---|
| `fill_delta` | signed volume delta on the fill minute |
| `fill_delta_conf` | bit: fill-minute delta confirms trade direction |
| `d5`, `d15`, `d30` | cumulative signed delta over the 5 / 15 / 30 min before the fill |
| `d5_conf`, `d15_conf`, `d30_conf` | direction-confirmation bits for each window |
| `pm_sofar_cvd`, `pm_sofar_conf` | pre-market session CVD to the fill, and its confirm bit |
| `pm_sofar_eff`, `pm_sofar_patheff`, `pm_sofar_crosses` | session efficiency / path / sign-crossings |
| `cvd_LON`, `conf_LON` | London-session CVD and confirm bit |
| `cvd_PM`, `conf_PM` | pre-market CVD variants |
| `op_sofar_*` | opening-session equivalents |
| `lon_slope_d` | OLS slope of London cumulative delta, direction-signed |
| `bp5opp` | 5-level book pressure opposing the trade |
| `fill_vol_rel` | fill-minute volume relative to recent norm |
| `churn_flow_30` | 30-min churn measure |

## 3.2 The verdict: order flow is the WEAKEST of the four classes

Look at the lift table again with only the flow checks:
F_ (+0.041 / +0.338 / +0.001), Tc (−0.022 / +0.096 / +0.183), Tp (−0.005 / +0.371 /
+0.177), C (−0.083 / −0.262 / −0.144), T2 (+0.050 / +0.158 / −0.014), BIGFD (+0.054 /
+0.183 / −0.027), LONSLOPE (−0.086 / +0.257 / −0.117).

**Not one flow check exceeds +0.34R in any era, and the session-CVD check (C) is
negative in all three.** Against depth's +0.5 to +1.3R, order flow is a rounding error
on entries.

This was genuinely surprising and it is the finding most likely to generalise wrongly if
you assume it. **What it means precisely:** *at the moment of entry*, on this strategy,
tape confirmation adds ~nothing once you know the depth picture. It does **not** mean
flow is useless — flow was decisively useful **inside the trade** (Part 6: flow-flip
exits were where the agent layer's defensive edge came from). Right variable, wrong
moment.

## 3.3 The provenance failure — the reason "recompute from raw" is a rule

One inherited confirmation column (`pm_sofar_conf`, the C check's input) **matched no
clean definition of itself.** Attempts to reproduce it from raw tape failed against every
plausible definition — meaning the column in the cached matrices was computed by code
that no longer existed, or from inputs that had since changed.

**How it was caught:** by trying to reproduce cached features from raw and gating on
1e-6 agreement — the same gate that passed for `d15` and `fill_delta` (byte-exact) failed
for this one. The passing cases are what made the failure interpretable: it wasn't our
pipeline, it was that column.

**The rule:** recompute every feature from raw; gate against cached artifacts only where
your own computation provably matches byte-exact on a known-good subset. A cached column
that cannot be reproduced is not evidence, it is folklore.

---

# PART 4 — DEPTH / WALL VARIABLES (where the edge actually lives)

## 4.1 The raw depth family

From an MBP-10 book (10 price levels per side), per candidate, at the fill minute:

| variable | meaning |
|---|---|
| `dep_thick` | total book thickness — **NaN means no depth data for that minute** |
| `dep_wall_below_d` | distance (points) from entry **down** to the largest resting level |
| `dep_wall_above_d` | distance (points) from entry **up** to the largest resting level |
| `dep_wall_below_sz` / `dep_wall_above_sz` | the size (contracts) of that wall |
| `dep_imb`, `dep_spread`, `dep_support`, `dep_resist`, `dep_sup_m_res` | imbalance / spread / support-resistance family |
| `dep_thick_d5m` | thickness change over 5 minutes |

**"The wall" is `argmax(size)` over the visible levels on that side.** This is what makes
the feature knife-edge sensitive to sampling instant — a one-contract difference can move
the identified wall by tens of points, which is exactly what the depth-parity noise-floor
work (framework doc §5.2) had to account for.

## 4.2 Direction resolution — the part that's easy to get wrong

```
behind_d = dep_wall_below_d  if long else dep_wall_above_d
ahead_d  = dep_wall_above_d  if long else dep_wall_below_d
ahead_sz = dep_wall_above_sz if long else dep_wall_below_sz
```

Below/above are **absolute**; behind/ahead are **relative to the trade**. Every wall
feature must be resolved through direction before use.

## 4.3 The gates, exactly as shipped

```python
W = NaN if isna(dep_thick) else float(isna(behind_d))     # pre: NO wall behind
D = NaN if isna(dep_thick) else float(notna(ahead_d))     # gold: a wall AHEAD exists
WALLSZ = (D == 1) and (ahead_sz >= 7)                     # the wall is real, not a wisp
wall_quality_cut (gold) = dep_wall_below_d >= 2.75 AND WALLSZ == 1
```

**The NaN semantics are load-bearing and subtle.** `W` is *"there is no wall behind"* —
so a **missing wall distance means the check PASSES** (nothing behind). But if
`dep_thick` itself is NaN, the whole depth family is unknown and W becomes NaN → the row
**stands down** and is excluded from both arms of the trial. Conflating "no wall" with
"no data" would corrupt both the trial and the live gate.

## 4.4 Why these two, in these two sessions

- **Gold (09:40–10:30) needs a wall AHEAD (D).** Post-open, price is trending into
  resting liquidity. The wall is both a target and the thing that stops the move against
  you. Without one ahead, the gold book is 12–20% WR and −0.44 to −0.61 mean R — *the
  trade is structurally broken, not merely unprofitable.*
- **Pre-market (08:00–09:30) needs NO wall BEHIND (W).** Thin overnight liquidity means a
  wall behind you is where price returns to and through. With a wall behind: 24–32% WR.
  Without: 38–61%.

Note the asymmetry — **the same instrument, hours apart, wants opposite depth
conditions.** A framework that tests one global depth rule across a whole day would find
nothing, because the two effects cancel. **This is the strongest argument for
session-native gates in the entire study.**

---

# PART 5 — CONTEXT / MARKET-STATE VARIABLES

Variables describing the *state of the market* rather than the trade.

| variable | definition | fate |
|---|---|---|
| `ent_vs_vwap_sd_dir` | entry distance from session VWAP in SDs, direction-signed | G / VWAPD checks — retained weak, holdout-negative |
| `bbw_state` | Bollinger band-width regime state | **X check — KILLED** |
| `netpath_30` | net path efficiency over 30 min | **PAQ — KILLED** |
| `trigdens_30` | count of triggers in the prior 30 min (density/activity) | TRIG — weak solo, elite limb |
| `on_extreme_age` | minutes since the session extreme was set | AGE — marginal, in score |
| `churn_flow_30` | 30-min churn | studied, not shipped as a gate |
| `pathpos`, `ent_on_pos` | position within the session's path/range | context only |
| `lon_hi_swept`, `lon_lo_swept` | whether London's high/low was taken out | context only |
| `struct_event` | structural event label (`"broke"` etc.) | **elite limb — shipped** |
| `htf_flag`, `confluence_count`, `cluster_members`, `level_stack` | multi-timeframe confluence structure | population/context, not gates |
| news blackout | red-folder event windows | **hard veto — shipped** (`vetoed_news_preopen`: 869 fit / 490 holdout) |
| day types, regime vectors, shock rulers | `build_daytypes.py`, `build_regime_vector.py`, `build_shock_ruler.py` | **studied for the desk/agent system — NEVER gates in the canon** |

**Verdict on the class:** context variables performed like flow — small, unstable, mostly
killed. The two that shipped (`struct_event` in the elite combo, the news blackout as a
hard veto) are both **categorical/event** variables, not continuous regime measures.

---

# PART 6 — SEPARATING WINNERS FROM LOSERS *INSIDE* THE TRADE

This is where the real value was, and it is a **different question** from entry
selection. Entry gates decide *whether to be in*. This decides *what to do once you are*.

## 6.1 The instrument: the time-segment walk

`output/time_segments2_{span}.parquet` — one row per book trade, recording at
**t+2, 3, 5, 8, 10 minutes**:

| field | meaning |
|---|---|
| `open{t}` | was the trade still open at that minute |
| `r{t}` | R at that minute's close |
| `mf{t}` | maximum favourable excursion so far (R) |
| `ma{t}` | maximum adverse excursion so far (R) |

Plus `win`, `held`, `dollars_1lot`, `tier`, `sess`, `era`. **956 fit rows / 637 holdout.**

That schema is the whole trick: **at every checkpoint you know where the trade is, the
best it has been, and the worst it has been — and nothing about the future.** Everything
below falls out of it.

## 6.2 THE WINNER SIGNATURE — the "press state"

Definition as shipped: **reached ≥ +0.5R by minute 3–5, still green, and currently
within 0.25R of its own peak** (i.e. going up, not giving back).

| era | n | WR | base WR |
|---|---|---|---|
| fit 2025 | 118 | 75.4% | 50.2% |
| fit 2026 | 48 | **64.6%** | 50.2% |
| holdout 2023 | 65 | 86.2% | 56.8% |
| holdout 2024 | 64 | 90.6% | 56.8% |
| **fit overall** | 166 | **72.3%** | 50.2% |
| **holdout overall** | 129 | **88.4%** | 56.8% |

**Lift: +22pp on fit, +32pp on holdout.** Direction-stable in all four era-slices.

Looser variants (≥0.5R and still open, ignoring the peak-proximity term), showing the
lift is robust to definition:

| checkpoint | fit press WR / all-open WR | holdout press WR / all-open WR |
|---|---|---|
| t+2 | 69.7% / 59.0% (+10.7pp) | 76.3% / 67.3% (+9.0pp) |
| t+3 | 71.2% / 60.3% (+10.9pp) | 81.3% / 72.8% (+8.5pp) |
| t+5 | 72.8% / 62.5% (+10.3pp) | 87.1% / 77.0% (+10.1pp) |
| t+8 | 74.9% / 65.2% (+9.7pp) | 88.2% / 84.0% (+4.2pp) |
| t+10 | 76.4% / 65.8% (+10.6pp) | 90.5% / 84.4% (+6.1pp) |

> ⚠️ **CORRECTION TO A LIVE ARTEFACT.** The shipped `trade-manager-v3` spec — currently
> in the live agent's system prompt — states this cohort "wins **79–88% in every era
> measured**." On the exact stated definition it is **72.3% on fit**, and **fit/2026 is
> 64.6% (n=48)**. Only the holdout years reach 86–91%. The *lift* is real and large; the
> *quoted range* overstates the fit era by 7–15pp. Should be corrected at the next
> certification cycle.

## 6.3 THE LOSER SIGNATURE

| condition at checkpoint | fit WR | holdout WR |
|---|---|---|
| MAE ≤ −0.5R by t+3 | **46.4%** (n=97) | **50.7%** (n=71) |
| MAE ≤ −0.5R by t+5 | 47.5% (n=99) | 55.0% (n=60) |
| green but **giving back > 0.25R off peak** at t+3–5 | 64.3% (n=387) | 77.4% (n=265) |

**Read the first row carefully: a trade that has already been half a unit of risk
underwater by minute 3 is a coin flip.** All the selection work that got it into the
book — 19,137 → 956 — has been undone by three minutes of price action.

Supporting distributions — **computed today, with a measurement caveat that is itself a
lesson**:

| statistic (fit) | winners | losers |
|---|---|---|
| median MFE across checkpoints | **+1.697R** | **+1.076R** |
| median MAE across checkpoints *(while open)* | −0.250R | −0.361R |

The shipped spec's terrain section quotes **winners −0.30R / losers −1.19R** for median
MAE. **Those are FINAL MAE including the stop-out; mine are MAE-so-far at surviving
checkpoints.** They measure different things, and the difference is instructive: a loser
that stops at t+4 has no `ma8`/`ma10` value, so any "MAE at checkpoints" statistic
**systematically understates losers by censoring the trades that already died.** That is
survivorship bias inside a single trade's timeline, and it is very easy to introduce
accidentally.

**Framework requirement:** when computing conditional statistics on in-trade state,
state explicitly whether the population is *"trades still open at t"* (conditioning set,
correct for decision-making) or *"all trades"* (outcome set, correct for describing the
book). Mixing them produces numbers that are individually true and jointly misleading.

The **MFE separation is the cleaner unbiased signal**: winners reach +1.70R at some point,
losers +1.08R. Losers do go green — they just don't stay.

- **Losers peak at minutes 0–1; winners peak at minutes 4–9** (gold ~4, pre ~9). A trade
  that made its high in the first minute and has been drifting since is telling you what
  it is.
- **Reach ladder:** 95% of trades touch +0.5R, 75% touch +1R, 48% touch +2R, 23% touch 3R.
- **Post-peak giveback on winners: ~1.25R median.** Which is why holding past a
  mechanical exit must be *a plan with a stop*, never a naked hold.

## 6.4 The three diagnostic signatures, condensed

| signature | evidence | what it licenses |
|---|---|---|
| **Pressing winner** | ≥0.5R by t+3–5, green, within 0.25R of peak | Hold. 72–88% win. Protective action here costs money. |
| **Dying trade** | MAE ≤ −0.5R by t+3, peak at minute 0–1, flow flipped against | Cut. Back to coin-flip; the graded defensive edge lives entirely here. |
| **Giving back** | green but >0.25R off peak | Ambiguous — 64–77%. Manage with a plan, don't hold naked. |

## 6.5 What this bought — the measured result

The agent management layer, given exactly these signatures, over 763 trades:
**avg winner unchanged (+1.464R vs mechanical +1.462R), avg loser cut −0.708R → −0.576R,
27 mechanical losers converted to wins, WR 56.1% → 59.2%.** Decomposition:
**defense +231.4R** on mechanical losers, **offense −131.3R** on mechanical winners.

**Cutting losers earlier was worth ~2.3× more than anything done to winners.**

---

# PART 7 — THE EXIT ENGINE AND THE ARM HISTORY

## 7.1 V8, as frozen

- **rr_floor 2.0, hard, every trade** — no target closer than 2R.
- **Structural target menu** — targets are real levels from the level stack, not fixed
  multiples. `working_target` / `target_level` recorded per trade.
- **First-leg partial at the structural target** (25% at structure is the measured best of
  the family; base V8 shipped by ruling — see below).
- **Trail** on the runner; EOD flatten; and post-ruling: 09:30 pre-flatten, close-and-reverse.

## 7.2 What was tried before V8 froze — the arm history

**The rr_floor ladder (TOMBSTONED).** Hypothesis: "a structural target but minimum X R".
Monotone worse at every step:

| floor | n entries | funded net | win-days | win meanR |
|---|---|---|---|---|
| **2.0** | 956 | **$90,015** | **150** | 1.75 |
| 2.5 | 944 | $88,893 | 144 | 1.78 |
| 3.0 | 922 | $86,248 | 139 | 1.82 |
| 4.0 | 884 | $81,463 | 136 | 1.89 |

Deeper floors *do* pay more per winner (1.75 → 1.89) but the reach ladder caps it (only
48% touch 2R, 23% touch 3R) and **veto contamination grows 12 → 34 → 72 entries** — a
higher exit floor is increasingly an **entry change wearing an exit costume**.
Reopening burden: a triple-era result at least as strong as this monotone ladder.

**The profit-taking family — 25 arms, all closed.** Static-R first legs (1.0/1.5/2.0/3.0R
× 25/50%), structural-min-R floors (1.5/2.0 × 25/50/75%), BE-at-partial, no-trail hold,
hold-to-2R runners, no-target trail-only. **Every uniform variant lost to 25%-at-structure
($93,310).** Mechanisms measured, not guessed:
- static/deep first legs **tax the 494 no-structure trades** that would have run whole,
  AND convert insured trades into full stop-outs (**stops 407 → 471 at a 2R leg**);
- min-R structural walks book *beyond* the floor and pay the spread twice;
- the no-target trail-only runner posts **the best win meanR in the entire study (4.07)**
  and **the worst funded result ($55,008, maxDD $4,131)** — the structural target is
  load-bearing.

**THE BE LESSON.** Break-even stops were tested twice and lost twice:
- as a standalone arm: **be1r $135,449 vs base $148,766 — "BE kills runners", an old
  lesson re-confirmed**;
- as 25%+BE-at-partial: 51% WR / 148 win-days / maxDD $1,586 / $92,833 — *era-stable in
  all four cells, and still not shipped.*

The mechanism: BE converts a normal retrace into a scratch, and the trades it "saves"
were disproportionately the ones that go on to win. It is the most intuitive exit
improvement in trading and it has now failed on this book in two independent studies.
**Any framework should treat BE as a null hypothesis to be defeated, not a default.**

**The legacy 3-minute cut (`CUT_R3` / `CUT_FW3`) — must NOT fire.** Thresholds
`r3 ≤ −0.1106`, `fw3 ≤ −13` are still in `config/live_thresholds.json` from the old
canon. The time-segment study showed the trades it would cut finish
**breakeven-to-POSITIVE on the rebuilt canon (+0.01R pre, +0.32R gold at t+3)**. Armed
as-is it silently underperforms the measured book. **A stale-but-plausible rule inherited
from a dead architecture is the most dangerous artefact in any repo** — it doesn't error,
it just quietly makes you poorer.

## 7.3 Angus's ruling on the family, and why it matters methodologically

The 25% partial **passed the holdout** and was **not shipped**: *"im happy with base v8
because of the win rate and winning days. the profit difference is negligible."*

A validation framework produces *evidence*, not *decisions*. Win rate and green-day count
were worth more to the operator than +$3.3k of expectancy. The framework's job is to make
that trade-off **visible and quantified** — not to auto-ship the highest-net arm.

---

# PART 8 — CONVICTION SIZING, DERIVED NOT IMPOSED

## 8.1 The process ruling

**1-lot first, always.** No sizing until the validated trade volume is visible at
standard size. Sizing multiplies; laid over an unexamined population it hides frequency
and concurrency problems inside dollar totals that look fine.

## 8.2 Score composition

```
gold_score = 2·D + Tc + AGE + TRIG + T2
pre_score  = 2·W + G + F
```

**The load-bearing check is doubled in each session** — D in gold, W in pre. That is not
an arbitrary weight: it is the trial's answer (D and W are the only checks with lifts
above +0.8R) encoded into the score.

The remaining terms are the weak-but-not-negative survivors. Their contribution is
**tie-breaking within a session, not signal** — and §2.4 flags that G is holdout-negative
and probably contributing nothing but noise.

## 8.3 Score → conviction tier

| session | score | tier |
|---|---|---|
| gold | ≤3 | 0.5× |
| gold | 4 | 1.0× |
| gold | ≥5 | 1.5× |
| pre | 2 | 0.5× |
| pre | 3 | 1.0× |
| pre | 4 | 1.5× |
| either | elite combo | **2.0×** |

Frozen in `config/live_thresholds.json` under `sizing.pre_gold_ladder`
(`le2: 0.0, s3: 0.5, s4: 1.0, s5: 1.5`) with `size_cap: 1.5` for the non-elite ladder.
**Cut points were chosen where the observed WR/meanR ladder actually stepped**, not on
round numbers.

Shipped tier mix on the fit book (from `python -m scripts.funded_book --span fit
--profile lucid`): **{1.5: 42%, 1.0: 33%, 0.5: 18%, 2.0: 7%}**. *(The pre-elite candidate
frame shows {1.5: 46.9%, 1.0: 35.4%, 0.5: 17.8%} with no 2.0 tier — the elite slot is
assigned during the funded walk, not in the candidate scoring. Quote the funded-run
figures for anything book-level.)*

## 8.4 The ELITE 2.0× combo

```
gold AND TRIG AND LONSLOPE AND struct_event == "broke"     — max ONE per day
```

Two design details that are easy to get wrong and both matter:

1. **The slot is spent on a FILL, not on a refusal.** If an elite candidate is evaluated
   and *not taken* (budget, gate), the day's elite slot is still available for the next
   one. Spending it on a refusal would silently downgrade the book.
2. **Max one per day** caps the tail: the 2.0× tier is 7% of trades but carries
   disproportionate risk, and an unlimited elite tier turns one bad regime day into an
   account event.

**Honest note (see §2.4):** LONSLOPE is standalone-negative in 2025 and holdout. The
combo was validated jointly; the limb was not.

## 8.5 The risk spine — every element earned by a failure

| element | value | the failure that produced it |
|---|---|---|
| daily budget | `base × 16/3` ($853.33 at $160) | realized-loss halts don't bound worst-day under overlapping positions — losses aren't realized when the next fills hit |
| budget test | `realized + in-flight + new ≤ budget` | same |
| soft de-risk | half size at −35% of budget | measured, both spans |
| de-risk ramp | half below $1,000 buffer, half again below $500 | Angus ruling; **dormant across all 19 months** (min buffer $1,642 fit / $1,698 holdout) — changes no measured number, pure insurance |
| outer halt | −8R = **1.5× budget at every base** | a −4R halt sat *below* the strategy's own budget and would have truncated the validated book |
| micro clamp | 40 | — |
| micros | `round(risk$ / (stop_pts × $2))`, min 1 | **never round to zero** — a 0-micro "trade" is a phantom fill in the journal and a divergence from the book |

## 8.6 The scaling profile, and the attempt that failed

**First attempt FAILED and was reported as a failure:** base $150 → cap $450, +$75 per
$1k, against a **fixed** $800 budget. Result: **holdout net down 20%, a red month
returned.** Diagnosis: a bigger base against a fixed budget strangles itself — an elite
trade at $900 no longer fits, and even two 1.0× trades exceed the budget.

**Angus's fix, which was the right one:** *"with more buffer, we have more of a daily
budget. max DLL should scale with the increased cap."* With budget scaling proportionally
(`budget = base × 16/3`, soft = 35% of it), **every month went green in both spans**
under both profiles.

Shipped: `scaled600` = base $160, +$75 per full $2k of buffer past +$3k, cap $600, budget
and soft de-risk scaling **with** the base.

**The generalisable lesson: sizing and risk-capacity are ONE system.** Scaling either
alone produces a worse strategy than scaling neither.

---

# PART 9 — STATE-CONDITIONING: WHAT WE DID AND DIDN'T DO

Checked directly in `scripts/l3_check_trial.py` today.

**What we DID condition on:**
- **session** (pre vs gold) — and this was decisive: the same instrument wants *opposite*
  depth conditions hours apart (§4.4).
- **era** (2025 / 2026 / sealed holdout) — the survival rule.
- **in-trade state** — the press-state / time-segment study (Part 6). This is
  state-conditioning of the *exit* decision and it produced the largest single behavioural
  finding in the project.
- **account buffer**, for sizing only — the de-risk ramp (dormant across all history).

**What we did NOT do — an honest gap:**
- **Entry gates were never tested inside drawdown states.** No "does D still work when the
  account is $800 from the line?"
- **Entry gates were never tested inside market-regime states.** Regime machinery exists
  (`build_regime_vector.py`, `build_daytypes.py`, `build_shock_ruler.py`, `regime_gates.csv`)
  but belongs to the **desk/agent system, never to the canon gate trial**. The only
  "state" inside the trial is `bbw_state`, and that is the X check itself — a feature
  under test, not a conditioning variable.

**So if state-conditioning proved decisive in the other chat's work, that is an extension
beyond what we did, not a replication of it.** A framework should treat *"evaluate each
surviving gate inside drawdown and regime states"* as a stage we never ran — with the
obvious caveat that it multiplies the search space and therefore needs its own
permutation null, or it will manufacture regime-specific edges out of noise.

---

# PART 10 — THE TRANSFERABLE PROCEDURE

For any new strategy, in order:

1. **Census everything.** Production detection code, zero selection, parity-checked
   against an independent stream. Report the composition (direction / timeframe / kind).
2. **Walk every limit** with no cancel policy enforced. Cancels are derived columns.
3. **Walk every fill** through the real exit engine, one candidate per call. Record the
   full MFE/MAE/checkpoint schema from §6.1 — *build this at L2, not later.* It is the
   single highest-value artefact in the whole pipeline and it costs nothing extra to
   record at the time.
4. **Report the funnel with a terminal status for every candidate.** No silent drops.
5. **Trial every check alone**, frozen threshold, NaN excluded from both arms, split by
   era, per session. Expect most to die. Publish the lift table.
6. **Classify each kill:** every-era-bad / era-flip / too-thin / holdout-negative. Record
   the precedent.
7. **Compose the score from the survivors, weighting by measured lift** (double the
   load-bearing check). Anything entering via a combination rather than standalone
   survival gets flagged and permutation-tested.
8. **Derive tiers where the observed WR/meanR ladder steps.** 1-lot first.
9. **Build the risk spine from the failures** — budget counts in-flight risk; outer guards
   above inner ones; sizing and capacity scale together.
10. **Mine the in-trade state** for the winner/loser signatures. This is where the
    management edge is, and it's a different question from entry selection.
11. **Declare execution semantics before validating** (opposing signals, same-direction
    stacking, concurrency, forced flattens).
12. **Tombstone every dead idea** with its reopening burden.

## The one-line version

> **19,137 triggers → 763 trades. Sixteen checks tested, three carried the edge, all
> three were depth. Order flow was near-worthless at entry and decisive inside the trade.
> The biggest single win was not a better entry or a better target — it was recognising a
> dying trade by minute 3 and cutting it.**

---

*All figures recomputed 2026-08-05 from committed artifacts. Two discrepancies with
shipped documents are flagged in §2.4 and §6.2 — in both cases the artifact is
authoritative and the shipped prose is optimistic.*
