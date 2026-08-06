# HANDOFF — London, displacement-entry rebuild

**From:** the 2026-08-05/06 canon rebuild session · **Sponsor:** Angus
**Scope of this handoff:** LONDON ONLY. New York is being optimised in a parallel session —
do not touch NY files or NY output.

Read this whole file before running anything. Everything in §2 was learned the hard way, and
§8 is a list of things already tried that do not work — repeating them wastes days.

---

## 0. Angus, in his own words — the objective

He is the program owner and **not a quant**. Explain in plain language, never in jargon.

> *"my objective is profit factor and optimisation to rinse prop firms"*

then, decisively refining it:

> *"id rather something that can do 50 points a day consistently year on year as opposed to
> something that does 200 points once or twice a week, and perhaps loses the other days or
> doesnt trade at all."*

> *"the reason [big-win/low-frequency] isnt good is because on a probability basis a streak
> could kill everything. when youre copy trading 10 accounts and u go through one of those
> rough phases, u can literally end up back in eval jail."*

**Therefore: the objective is NOT profit factor.** It is `src/validation/prop_score.py` —
green-day %, max-day share ≤30% (the prop consistency rule), net points/trade after 2pt
friction, T≥2, N≥200, worst rolling 10 days. **Score every book on that scoreboard.** A book
with a great PF and 35% green days is useless to him.

**End-of-day trailing drawdown means intraday heat is free.** Only the closing balance
counts. Do not optimise away intraday drawdown.

Other standing instructions:

- *"One stage at a time, I make the calls at each gate."* — do not run three stages then
  present a conclusion. Report at each gate and wait.
- *"look at all we tested to get the IB fade model shipped… if u arent testing jack shit and
  just sending it off, its obviously not gonna do well."*
- *"the point is what we want to do is see if we can find the substrate from the raw triggers
  where it IS profitable… dont jump to conclusions off of raw triggers."*
- *"its not just about singular concepts either… its about killing overlapping entries… its
  also looking at how the flow comes together, when 4 things positively align with a trade."*
- A **zero result is a bug until proven otherwise**, never a finding on first sight. Three
  separate silent zeros in one day all turned out to be parsing bugs.

---

## 1. What London IS now (the strategy, in Angus's words)

His canon geometry, applied to the London session. Confluence clusters of **Bollinger basis
+ daily-VWAP bands + POC**, with three patterns:

| pattern | definition (his words) |
|---|---|
| **B** | *"there is vwap -1 and a bb ma on the 3 minute time frame close to it. price closes through both of them. i enter on the retest of whatever is closest to price"* |
| **A** | *"touches +2, and then closes through vwap +1 and a bb ma"* — over-extension reversal |
| **B2** | rejection block — **REMOVED, see §3** |

**A VWAP band must be touched or closed through for every setup.** (*"nah vwap needs to be
closed through or touched for all setups"*.) That is the ruling that produced the 1,426
"VWAP-ruled" setups in the funnel below.

**THE ENTRY MECHANISM CHANGED.** The original canon entered on a *limit at the retest*. Angus
moved it to **market order on the displacement candle that closes through the level**:

> *"maybe we re build it around the displacement through the level straight up instead of a
> retest. this would make sense because you can see the flow upon the candle you are entering
> off basically"*

This matters beyond convenience — it is what makes order-flow validation honest (see §2.1).

---

## 2. The two defects that shaped everything — do not re-introduce them

### 2.1 The depth read was one bar late (`research/findings/LDN-depth-read-one-bar-late.md`)

`scripts/london_depth.py:101` read `depth_at(dep, fill.floor("min"))` — that is the fill
bar's **CLOSE**. Bars are close-labeled and fills land *inside* their stamped bar (100% of
London fills, 94.8% of the shipped matrix). So every depth feature was reading the book
*after* the decision it was supposed to inform.

Effect on the two headline London checks:

| check | as measured (late) | at an honest read |
|---|---:|---:|
| `W` | +19.0 pp | **+8.2 pp** |
| `FAR` | +20.5 pp | **+6.3 pp** |

**Rule: features are read at the TRIGGER bar, never the fill bar.** `scripts/build_l3_features_london.py`
now carries three explicitly-named anchors and only one is legal:

- `dep_*` — fill-bar close · **BARRED**
- `p1_*` — fill-bar open · **BARRED**
- `t_*` — order placement · **THIS IS THE FEATURE**

Angus's own read on why the retest entry was hopeless for flow validation:

> *"on a limit order, of course the minute before entry, flow will probably be against us
> because it is opposing our direction to get filled before running the way we want it to."*

Displacement entry fixes this: you measure the candle you actually enter on.

### 2.2 The NY news veto was silently deleting London trades

`no_premarket_high_impact` blocks the entire pre-market on a US high-impact release day. It
was written for NY and London (03:00–05:00 ET) satisfies `tod < 09:30`, so London was being
stood down for events hours in its future.

Measured: **408 of 409** high-impact pre-09:30 releases land at 08:15 ET or later; exactly
**1 of 409** could touch a London window. The veto deleted **1,086 candidates over 34
sessions — 11.8% of all ruled setups.**

Angus: *"bruh it can trade before high impact news days. CPI is not gonna affect london,
thats stupid."*

**`no_premarket_high_impact: False` is set for London and must stay off.**
**OPEN DEBT:** London now has *no* news stand-down at all. A correct one needs a UK/EU
calendar (an 08:30 London release is 03:30 ET, squarely inside the window). We do not hold
one. Declared as owed at L4 — do not silently ship without flagging it.

---

## 3. Two rulings from Angus that are NOT yet fully executed

### 3.1 B2 is removed

> *"lets remove b2 entirely."*

With B2 gone the entry-variant question collapses: `EC` and `E4` both market-enter
displacements, so they are the same book. Filter `kind == "displacement"` everywhere.

### 3.2 The 2R floor is cut — targets go to the NEXT STRUCTURAL LEVEL

> *"fuck why is the 2 r floor instated. that needs to get cut, that rule should be implemented
> if feasible in the optimisation process."* … *"btw it should be the next structural level
> not 2r floor minimum etc"*

**Why the floor is so destructive:** `walkout_under_floor` does not merely enforce a minimum —
it walks the target menu **OUTWARD past the nearest structural level** to find one clearing
2R, and vetoes the trade outright when nothing clears. Measured on the shipped London book:

- `working_target != target_level` on **100%** of outcomes — the walkout moved the target on
  every single trade
- **142 trades vetoed** by `rr_floor` with no entry and no path at all
- **target-hit rate 2.9%**

**`scripts/build_l2_outcomes_london.py` now has `--rr-floor`** (added 2026-08-06, mirrors the
NY script; floor 0 with walkout off takes the first level in the menu). **The rr0 London book
has NOT been built yet — that is task #1 in §5.**

---

## 4. State of the pipeline — all four layers built and GATED

| layer | artifact (committed) | gate result |
|---|---|---|
| **L0** census | `output/l0_triggers_london_fit_std.parquet` | parity **byte-identical** vs cached stream, 39/39, 53/53, 16/16 |
| **L1** fills | `output/l1_fills_london_fit_dedup.parquet` | engine subset-reproduction, **20/20 fills exact** on minute + tick-rounded price |
| **L2** outcomes | `output/l2_outcomes_london_fit_EC.parquet` (**2R floor**) | lookback **7d ≡ 30d** on 105 outcomes |
| **L3** features | `output/l3_features_london_fit_EC.parquet` | reproduces `london_matrix` to **1e-6 on 39 columns** |
| context | `output/daily_context.parquet` | see §6 |

**Funnel:** 8,723 triggers → 7,239 filled → 1,426 VWAP-ruled setups → 1,239 outcomes.

**Span:** fit = 2025-06-02 → 2026-07-15, 264 sessions. **Discover on 2025, validate on 2026.**
Holdout = sealed 2023/24 days (`data/reference/holdout_2023_24_days.csv`) — **run ONCE, at
the very end, frozen.**

### The overlapping-entry rule (Angus was emphatic)

> *"if it broke the 1 minute bb ma, and then 3 minute as well after the 1 minute filled, it
> should not double up on the same trade… i dont scale my entry just because it broke the MA
> on multiple time frames sequentially."*

Dedup is implemented and **verified working**: 2,139 displacement outcomes → **719 setups**
(3.0× compression). Multi-trigger setups span a median of 3 minutes across 2 timeframes with
entries 5.25pt apart — i.e. they really are the same trade.

Use `vs_first` (setup-first, chosen on causality grounds — the first trigger is the one you
could actually have taken). `scripts/l1_london_dedup.py` applies eligibility **BEFORE**
grouping; `scripts/l2_london_dedup_arm.py` re-derives dedup per entry arm. Do not group first
and filter after — that silently merges ineligible triggers into setups.

---

## 5. THE BASELINE, and task #1

Everything is measured against this. London EC, **2R floor**, displacement only, deduped:

| metric | value |
|---|---:|
| N (setups) | 719 |
| trades/day | 3.20 |
| **net pt/trade** | **−3.69** |
| T | −6.06 |
| **green days** | **32%** |
| median day | −12.1 pt |
| worst rolling 10d | −368 pt |
| **target-hit** | **2.9%** |
| mean R | −0.146 |
| median risk | 11.8 pt |

Exit mix — **note that 50.3% of trades take a partial before exiting**, and the partial level
is `min(rr_floor, 1.5)`, so changing the floor changes the partial, which moves the stop:

| exit reason | share |
|---|---:|
| stop | 46.7% |
| partial+stop | 40.1% |
| partial+target | 10.3% |
| target | 2.9% |

**This is why the floor change cannot be re-priced from the existing book and needs a real
rebuild.**

### TASK #1 — build and score the next-structural-level book

```bash
python -m scripts.build_l2_outcomes_london --span fit --entry EC --rr-floor 0 --procs 4
# -> output/l2_outcomes_london_fit_EC_rr0.parquet     (~40-60 min on 4 cores)
```

Then score it on the prop scoreboard against the table above, split by era.

**Expected direction** — a 3-session smoke test through the real engine gave:

| arm | outcomes | rr_veto | target-hit | median R | net |
|---|---:|---:|---:|---:|---:|
| 2R floor (shipped) | 245 | 4 | 13% | −0.73 | **−273 pt** |
| next structural level | 227 | 24 | 35% | −0.27 | **+243 pt** |

Three sessions is not a result. It is a reason to run the full book.

⚠️ **Runtime warning.** L2 is ~19k independent `simulate()` calls for NY / ~8.7k for London;
each replays a 7,868-bar lookback window **one row at a time via pandas `.iloc`** (58% of
runtime). ~690 ms per trigger. Run it with `nohup … &` and a watcher — never block on it.
**Never use `pkill -f <pattern>` where the pattern matches your own command line** — it has
killed its own shell three separate times in this project.

---

## 6. The market-context layer (new, 2026-08-06, untested)

`scripts/build_daily_context.py` → `output/daily_context.parquet`, one row per session.
Angus asked for this directly:

> *"i guess next thing to look at is market context and shit like that too, if youre shorting
> a heavy bull market its probably not gonna go best for you."*

**Causality guarantee:** every column is computed from sessions **strictly before** its own
date — the per-session table is built first and shifted once at the end. This is structural,
not per-column discipline, *because London trades at 03:00 ET, hours before the RTH session
opens*, so anything touching the same day's cash session would be unusable there.

Columns: `trend_state` (daily trend vs 20-session mean in ATR units, trailing-percentile
bucketed), `vol_state` (VIX regime, trailing percentile), `balance_state` (value-area overlap
vs the prior session — balance/edge/imbalance), `poc_streak` (value migration), `trend_sign`,
plus **levels**: `poc_prev/vah_prev/val_prev`, `poc_week/…`, `roll5`, `roll20`.

Every threshold is a **trailing** percentile, never a full-sample quantile — a full-sample cut
peeks at the future.

**Untested.** Join it to the rr0 book on `day` and score with/against trend. That is the
obvious first use and nobody has run it.

---

## 7. What the volume-profile research says you should use

`research/findings/T1-T5-volume-profile-nodes.md` (32,014 node-session-widths, 354 sessions):

- **Yesterday's high-volume nodes hold price** ~7% longer than prices 20pt either side.
  Era-consistent (1.078 / 1.058), and the effect **grows with band width** (+0.027 → +0.057 →
  +0.107 at ±5/±10/±20pt), which is the signature of a real effect blurred by 1-minute bars.
- **Low-volume nodes do nothing.** The "liquidity vacuum" half fails (2026 = 1.004, wrong
  direction). **Do not build an LVN-traversal family** — that question has now died twice,
  after `LQV-01` failed on MBP-10 snapshots.
- **Only the PREVIOUS SESSION's profile works.** Previous week, rolling 5 and rolling 20 are
  flat or era-inconsistent. Longer windows are context, not levels.
- The naive uncontrolled test reads 0.899–0.973 — apparent confirmation, pure confound. HVNs
  sit mid-range, LVNs sit in the tails, and price hangs around where it was yesterday.

**Actionable:** `_gather_levels` (`src/engine/snapshot.py:246`) exposes **only the current
session's POC**. VAH/VAL are computed and discarded every bar; yesterday's profile is absent
entirely. The levels with the only measured holding power we own **are not in the level menu.**

Caveat to keep honest: ~7% of dwell is a *level-quality* finding, not an edge.

---

## 8. THE BURN LIST — already tried on London, does not work

Do not spend days rediscovering these.

1. **92 single-variable displacement filter cells** — not one is net-positive in both eras.
2. **An 8-check alignment score** ("how many things agree") — `corr(score, net) = +0.032`,
   non-monotonic, **every bucket negative**. Stacking confluence counts does not work as
   posed. (This does *not* close Angus's §0 point about things aligning — it closes the naive
   count-them-up version.)
3. **99 filter cells scored for green-day %** — **zero clear 50%**; ceiling is 42%.
4. **`corr(trades/day, green%) = +0.88`; `corr(PF, green%) = −0.46`.** More trades per day
   buys green days; higher PF costs them. This is the central tension of the whole objective
   and it is measured, not theoretical.
5. **L3 permutation null:** only `room_ahead_R` beat the family-wise null (24.7% vs null
   median 7.7%, p=0.0000 / p26=0.0050). **`W` (8.2%) and `FAR` (7.6%) sit ON the null median
   — they are noise** once the depth read is honest.
6. **`trig_delta_conf` +14.2pp** was the family-wise max but **p=0.065**, failing its declared
   0.01 bar. It was not promoted. Do not move a declared bar to rescue a result.
7. **Entry head-to-head (with B2 still in):** E3 PF 0.91 / EC 0.80 / E4 0.76. But: trades E3
   never filled (n=109) ran **82% WR, PF 5.42, ~+9.9 pt/trade**, while re-priced trades
   (n=1,290) ran PF 0.63. The displacement entry recovers a genuinely good population and
   re-prices a bad one — that tension is unresolved and is the real question.
8. **LDN-PO3-01 is a tombstone** (`research/findings/LDN-PO3-01-TOMBSTONE.md`). Note the
   corrected figure: median risk is **14.0 pt**, not the ~5 pt an earlier candidate file
   claimed (that was the OBK branch).
9. **The 80% rule fails at ~20%** on our data (both NY and London), against a claimed 80%.
   *But* our test had no acceptance condition and no regime filter, so the rule *as
   originally specified* is untested. Declared arm, not a settled kill.

---

## 9. Session segmentation — required

> *"make sure we just section off between london, pre market and new york am when we optimise
> shit because the price action dynamics are just different."*

`scripts/session_scoreboard.py` implements LONDON 03:00–05:00 / PRE-MARKET 07:45–09:30 /
NY AM 09:30–11:00 by ET clock at the fill. **For this handoff only the LONDON row is yours.**
The repo already proves the point: the NY canon runs `pre` and `gold` as separate books with
different checks and thresholds. Pooling averages three different markets.

**Never hardcode London's ET hours** — use `scripts/build_l0_triggers_london.window_et(day)`.
London is 08:00–10:00 UK, which is 03:00–05:00 ET *or* 04:00–06:00 ET depending on UK/US DST
misalignment.

---

## 10. File map

**Build:**
`scripts/build_l0_triggers_london.py` · `build_l1_fills_london.py` · `l1_london_dedup.py` ·
`build_l2_outcomes_london.py` (**has `--rr-floor`**) · `l2_london_dedup_arm.py` ·
`build_l3_features_london.py` · `build_daily_context.py`

**Analyse:** `l3_london_trial.py` · `l3_london_null.py` · `l3_london_trigger_flow.py` ·
`l3_london_expand.py` · `session_scoreboard.py` · `src/validation/prop_score.py`

**Prereg (the authority):** `docs/PREREG-london-canon-rebuild.md` — LDN-CAN-01, with
amendments §3.1 setup dedup, §0.1.2 VWAP touch, §7 wide-band cancellation, §8 null bars,
§10 L4 arms.

**Law:** `docs/VALIDATION-PROCESS.md` — §5.9.1 census kill line, §5.9.2 earned-expectancy
kill, §5.10 transparency/data cards, §5.11 pre-ship checklist (9 items), §5.12 canon map,
§6.0 promotion law, §2.3 family-wise permutation null.

**Prior handoff (still valid on method):** `docs/HANDOFF-london-rebuild.md` — the L0→L4
layer discipline, data inventory, and the gates. Read §2 and §7 of it.

---

## 11. Gotchas that cost real time

- **`prop_score` scores size-0 rows.** Canon books carry size-0 signals; filter `size > 0` or
  you get nonsense (reported live NY canon at −3.52/trade; actual +9.38).
- **`cluster_types` from parquet is a numpy array.** `str()` drops commas, so
  `ast.literal_eval("['bb' 'vwap']")` concatenates to `'bbvwap'`. Handle all containers.
- **Date parsing from filenames:** use
  `re.search(r"(20\d{2})-?(\d{2})-?(\d{2})", f.name)`. A naive digit-scrape on
  `glbx-mdp3-20250602…` grabs the `3` from `mdp3` and yields `3202-50-60` (this produced a
  silent zero across 295 files).
- **`over_extension_sigma`** is documented as "NY VWAP ±2σ" but the code always reads
  `daily_vwap`. Load-bearing for London, where `ny_vwap` is NaN before 09:30. The config
  comment was corrected 2026-08-05; the behaviour was always daily.
- **Every output artifact is gitignored.** The London L0/L1/L2/L3 + context parquets were
  force-added for this handoff so you start warm. Anything new you build will need `git add -f`.

---

## 12. Suggested order of work

1. **Task #1 (§5)** — build `--rr-floor 0`, score on the prop scoreboard vs the −3.69 / 32% /
   2.9% baseline, split 2025 vs 2026. **Report and stop.** Angus makes the call.
2. Join `daily_context` (§6) and split the book with-trend vs against-trend, and by
   `balance_state`. Untested and cheap.
3. Add prior-session POC/VAH/VAL/HVN to the level menu (§7) and re-run L0. This changes the
   census, so it is a new arm, not an edit — re-gate L0 parity.
4. Only then revisit filters — and remember §8.3: no filter has ever cleared 50% green days.

**Do not open a PR unless Angus asks.** Commit and push to your designated branch.
