# HANDOVER — Pat: arming the rebuilt NY canon

Angus 2026-07-30. You are receiving the rebuilt canon (NY pre-market + golden window),
calibrated and conformance-tested, to take to a live arm. **Nothing is armed.** The stack is
structurally disarmed (`_NoBroker`) and the two-party token has not been issued.

Read §3 before anything else: the rebuilt canon behaves *materially differently* from what is
deployed, and two of those differences would have hurt you on day one if left as they were.

| | |
|---|---|
| The spec | `scripts/funded_book.py` — the docstring IS the specification |
| What the canon is / is not | `docs/CANON.md` |
| Why each rule exists | `docs/CANON-QA-LOG.md` |
| Arming state, gate checklist, open items | `docs/ARMING-REFERENCE.md` |

The old canon is **deleted**, not deprecated: its substrate shared a 2-trade cap across
pre-market and gold instead of 2 per session, starving gold on 56% of day-books. Do not
reconstruct anything from git history and treat it as truth. Any number produced before
2026-07-28 is void.

---

## 1. What runs

| Layer | Module |
|---|---|
| Decision core | `src/canon/scorer_ny.py::NYScorerV2` |
| Live lane (features → verdict) | `src/canon/ny_lane.py::NYLane` |
| **Live orchestrator (what you wire)** | `src/live/ny_runner.py::NYRunner` — detector → orders → lane → verdicts, decided per bar |
| Order lifecycle | `src/canon/order_watch.py` |
| Sizing schedule | `src/canon/gate_evidence.py` (imports the profile — never restates it) |
| Account backstops | `src/live/risk.py`, `src/canon/spine.py` |

**Entries (uncapped).** pre 08:00–09:30 requires `W==1` (no depth wall behind the trade);
gold 09:40–10:30 requires `D==1` (wall ahead) **and** passes the wall-quality cut
(`dep_wall_below_d >= 2.75` and `WALLSZ==1`). Risk band 7–60pt. No fixed target — the exit is
managed (V8). Red-folder news blackout.

**Conviction ladder** (× the profile base): gold score ≤3 → 0.5, 4 → 1.0, ≥5 → 1.5;
pre score 2 → 0.5, 3 → 1.0, 4 → 1.5. **Elite 2.0×** when gold **and** TRIG **and** LONSLOPE
**and** `struct_event=="broke"` — max one per day, and the slot is spent on a FILL, not on a
refusal.

**Profiles.** `lucid` = base $160 flat (ladder $80/160/240/320, budget $853.33) — base
$150→$160 ANGUS 2026-07-31, row N. `scaled600` = base $160, +$75 per full $2k of buffer past
+$3k, capped $600, with budget and soft de-risk scaling *with* the base. Pick one at
construction and give the spine the same one (`SpineConfig.profile`) or the backstop is
indexed to a base the sizer never uses.

**Risk spine.** Daily budget: `realized losses + in-flight risk + new risk ≤ budget`, where
budget = base × 16/3. Soft de-risk to half at −35% of budget. **De-risk ladder near the line
(Angus 2026-07-30): half size below $1,000 of remaining drawdown, half again below $500** —
tightest applicable step wins, and the spine's $100 hard halt sits underneath. Micros =
`round(risk$ / (stop × $2))`, floored at 1, clamped to 40.

---

## 2. What is already proven — and how to re-run it

```bash
python -m pytest tests/test_canon_scorer_ny.py tests/test_ny_lane.py -q   # 35 tests
python -m scripts.funded_book --span fit --profile lucid       # +$82,543 (3 rules, $160)
python -m scripts.ny_lane_replay --span fit --days 25                     # 25/25 days
python -m scripts.depth_parity --day 2026-04-20 --self-test               # PASS
```

- **The live scorer reproduces the shipped book exactly** — every row of both spans, both
  profiles, same trades / tiers / risk dollars / micros / P&L. It re-derives the gates from
  raw depth and flow columns rather than reading the book's precomputed verdicts, so this also
  proves the live re-derivation of W, D, the wall cut, the scores and the tiers.
- **The live lane reproduces the book on 25/25 real fit days** — real bars and tape streamed
  through `CanonIngestor`, features built by the live code path, scored live.
- **The runner orchestration is pinned by 16 tests** — the resting rule, gap dormancy and
  gold revival, replace-with-freshest sizing, the struct-event→elite join, budget-gates-fills
  semantics, the scratch race, and the hard drop at 10:30.
- **The depth harness is clean on both book models** — 180 archive minutes through
  `DepthBook`, and an MBO capture through `OrderBook`, both at 100% gate agreement. MBO
  aggregated to price levels *does* reproduce the archive's wall features.
- Reference results (50k account, $2k EOD-trailing; ALL THREE rules, base $160 — rows
  J/K/L/N): `lucid` fit **+$82,543** / holdout **+$48,211**; `scaled600` fit **+$272,847**
  / holdout **+$142,565**. Every month green in both spans under both profiles. The de-risk
  ladder is dormant across all 19 months (min buffer $1,642 fit / $1,698 holdout), so it
  changes no measured number. WITH the shipped agent management layer (rows M/N), fit:
  `lucid` **+$100,297** (worst day −$542, maxDD $878), `scaled600` **+$327,421**.

---

## 3. Behavioural changes from the deployed stack — read before arming

| # | Change | Consequence if you miss it |
|---|---|---|
| A | **Entries are uncapped.** No 2/day slot, no nth-escalation, no day ladder, no governor, no cold trail. Capacity is the BUDGET. | The book averages ~4 trades/day and legitimately runs into double digits. |
| B | `RiskLimits.max_trades_per_day` **3 → None** | The old 3 backstopped a 2/day engine cap that no longer exists. Left at 3 it would announce a halt and stand the account down mid-session on most days. This was the most dangerous stale default in the repo. |
| C | Spine `daily_loss_halt_r` **−4R → −8R** | At the $150 base, −4R is −$600 — *below* the canon's own $800 budget. An outer guard that fires before the inner one truncates the validated book. −8R is exactly 1.5× the budget at every base. |
| D | **No distance cancel.** Orders live to their session window end. | The 22pt `t_cancel` measured inverted: it kept −0.180R and killed +0.015R. `OrderWatch.t_cancel` now defaults to `None`; setting a float trades a book nobody measured. |
| E | **The resting rule** supersedes fixed per-order windows: an order rests exactly while a fill right now would be admissible — dormant through the 09:30–09:40 gap, may revive in gold (the book counts a pre trigger's gold fill as a gold trade), hard-dropped at 10:30. | `NYRunner` enforces this; do not re-impose a birth-window cutoff, it removes trades the book counted. |
| F | Gold window **09:40–10:30**, and **no 09:55–10:00 dead zone** | The rebuilt canon was validated without one. |
| G | Sizing base **$200 → $150** (superseded by row N: **$150 → $160**, ANGUS 2026-07-31) | Every order size changes. |
| H | De-risk ladder replaces the linear taper to zero | Between $100 and $1,000 of buffer the canon now takes half/quarter-size trades where the old canon refused. Angus's ruling; the spine's $100 halt is the floor. |
| I | **The legacy 3-minute cut must NOT fire** (`CUT_R3`/`CUT_FW3` in the exit manager / lifecycle `maybe_cut`). | The rebuilt book was measured WITHOUT it, and the time-segment study (`output/time_segments_fit.parquet`, 2026-07-30) shows the trades it would cut finish breakeven-to-POSITIVE on this canon (+0.01R pre, +0.32R gold at t+3) — armed as-is it silently underperforms the measured book. Disable it on the canon lane, or re-certify with it and accept a different book. |
| J | **CLOSE-AND-REVERSE is canon execution semantics** (ANGUS 2026-07-30). When a validated opposing signal's limit FILLS while a position is open, that fill flattens the position at the fill price and the reversal runs as its own trade — size the opposing order to close + open in one ticket. An opposing signal that never fills changes nothing; every trade keeps its own full bracket; same-direction adds stack as before. | The book's references are measured UNDER this. A runner that blocks the opposing entry while in a position, or that only flattens without reversing, silently trades a DIFFERENT and worse book (flatten-only measured $49,880 holdout). 86 fit / 97 holdout trades flip; the flip is the book's strongest exit signal. Overlay: `output/aikido_cr_{span}.parquet`. |
| K | **TWO SESSIONS: every pre-market position is FLATTENED at 09:30** (ANGUS 2026-07-30: "i want all pre market trades to be flattened by market open. 2 different sessions basically"). Market order on the first bar at/after 09:30 for any position filled before 09:30; the engine knob is `pre_flatten_at`. The legacy premarket BE-at-09:29 is subsumed (one minute of BE, then flat). | The references are measured UNDER this. A runner that lets pre positions ride into RTH trades a richer but DIFFERENT book than the one validated — and re-opens the open-volatility exposure ANGUS ruled out. |
| L | **ONE PER LEVEL** (ANGUS 2026-07-30: "im all for trades in the same direction and all but not double entering off the same level"). Do NOT place a same-direction order while an open same-direction position's entry sits within 3pt of the new limit, or shares the same stop. Multi-TF sibling triggers off one cluster are ONE position, first by detection order; adds at genuinely different levels still stack. | The references (+$77,202/+$44,844 lucid) are measured UNDER this. A runner that stacks siblings trades a ~18% richer but DIFFERENT book with ~21% deeper maxDD than the one validated — 193 fit / 122 holdout entries do not exist in the canon. |
| M | **THE AGENT MANAGEMENT LAYER IS SHIPPED** (ANGUS 2026-07-31: "whatever we gave the agents here id be happy to ship to the live agents, i've seen enough"). In-trade management of every canon fill is delegated to the frozen `trade-manager-v3` spec (Sonnet), under the desk-live semantics of `scripts/capture_desk_run.py::manage_trade`: event-driven turns (position open, press check at fill+3m, whole-R touches, flow flips on green positions, giveback ≥0.75R off a ≥1R peak, EOD warning), MAX_TURNS 10, next-bar-open execution with 1-tick slip, the engine stop an INVIOLATE floor (the agent may tighten, never widen; press-state doctrine advises against protecting winners but is NOT a lockout — full discretion stands), rows J/K/L remain law above the agent. The agent reads/appends `runs/live/journal.jsonl`, SEEDED with the full 763-row fit-span history — live day one starts with 13 months of its own decision memory (ANGUS: "thats what i want"; 2026-07-31: "they can see a year of their own decisions, decision-making outcomes"). MEMORY PIPELINE — this is how the seeded year reaches each live decision: the 07:45 day thesis and the 09:30 re-read are built WITH `journal_digest()` over the full journal (totals, defense/offense gauges, flow-conditioned exit scorecard, last-trades tail), and every trade's opening turn carries that thesis. TO KEEP THE JOURNAL ALIVE the live desk MUST run the V8 exit logic in shadow on every trade and record the counterfactual (`v8_R`, plus MFE/flow-at-exit/post-exit settle) in each appended row — without the shadow, the digest's gauges go blind and the learning loop is severed. ENTRIES REMAIN 100% MECHANICAL (ANGUS 2026-07-31: "mechanical, mechanical, mechanical") — the agent has ZERO entry authority; its discretion begins at the fill and ends at the flat, inside the guardrails. | Graded book UNDER this layer (fit, desk run 2): agent $95,194 vs mech $77,202 lucid, **maxDD $810 vs $1,268, worst day −$479 vs −$670**, WR 59% vs 56%, avg winner unchanged. The ship rationale is the funded risk shape — loss prevention, not winner capture. Running the canon lane WITHOUT the agent layer is the measured mech book — legal but leaves the validated improvement unarmed. Grading + caveats (conviction-shuffle null; gold-only edge; no learning trend): `docs/REPORT-desk-run-2.md`. |
| N | **SIZING BASE $150 → $160** (ANGUS 2026-07-31, on the agent-layer ship: "the agents are very good at doing this"). One value, THREE conformance-locked homes, all updated together: `funded_book.PROFILES` (both profiles), `scorer_ny.LUCID`/`SCALED600`, and the test pins. The daily budget scales WITH the base by design ($853.33/day now); the −8R spine halt is base-relative so it stays exactly 1.5× budget; the de-risk ladder stays dormant on all validated history (min buffers $1,642 fit / $1,698 holdout). | New references, ALL rules, base $160 — mech canon: lucid fit +$82,543 (worst day −$690, maxDD $1,375), holdout +$48,211 (−$737, $1,548), 19/19 months green; scaled600 +$272,847 / +$142,565. WITH the shipped agent layer (fit): lucid +$100,297 (worst day −$542, maxDD $878), scaled600 +$327,421 (maxDD $3,158). Arming with $150 sizing now trades an unmeasured book — the conformance suite will catch it. |

---

## 4. Your runbook to arming

Do these in order. Each is a gate; a red gate stops the sequence.

1. **Capture one live session's depth** and normalise it to JSONL. Schemas are not
   interchangeable — see `read_events` in `scripts/depth_parity.py`:
   - per-level (`.depth`): `{ts, action: R|B|A|b|a, price, size, ct}`
   - MBO: `{ts, action: R|A|C|M, order_id, side, price, size}`
2. **Run the depth parity gate** against a day that also has archive coverage:
   `python -m scripts.depth_parity --day <d> --events capture.jsonl --book mbo`
   Requires **100% gate agreement** and wall distances within a tick. This is the one gate
   that cannot be satisfied offline, and it is the one that fails *silently* if skipped — a
   wrong wall distance still produces a plausible verdict, so nothing alerts.
3. **Wire `NYRunner` to your loop.** The orchestration is BUILT and tested
   (`src/live/ny_runner.py`, 16 tests) — the struct-event join included, so the elite 2.0×
   fires without further work. Your side is four calls plus executing the actions it returns
   (`place` / `cancel` / `modify_size` / `scratch`), each through the spine as today:
   ```python
   runner = NYRunner(lane=NYLane(ingestor=ing, profile=LUCID, news_gate=gate))
   runner.start_day(day, buffer=equity - trailing_line)   # once per session
   acts = runner.on_trigger(t)          # every LiveDetector.on_bar trigger
   acts = runner.on_bar(ts, high, low)  # every closed 1m bar, after the ingestor ate it
   res  = runner.on_fill(ref, fill_ts, filled_size)       # broker fill event
   runner.on_position_closed(ref, pl=realized)            # exit manager's realized $
   ```
   Contracts you must honour, all pinned by tests: a `scratch` result means CLOSE THE
   POSITION NOW and journal it (the fill-minute evaluation refused a fill that landed —
   the book gated at fill with zero cost; the scratch is that idealisation's honest live
   price). Orders rest exactly while a fill right now would be admissible — they go dormant
   through the 09:30–09:40 gap and may revive in gold, because the book counts a pre
   trigger's gold fill as a gold trade. The budget gates FILLS, not resting orders — that is
   the book's own semantics, so do not "fix" jointly-over-budget resting orders; the runner
   pulls survivors after each fill and scratches the race.
4. ~~Join `struct_event`~~ — **done inside `NYRunner`** (`watch.struct_event(ref)` feeds the
   fill-minute verdict; a scratched elite fill does not burn the day's 2.0× slot).
5. **Shadow a full session** disarmed. Confirm against `docs/ARMING-REFERENCE.md` §4: no
   trade-count halt, no distance cancels, per-session expiry, sizes matching
   `check_sizing(..., risk_dollars=v["risk_dollars"])`.
6. **Then, and only then**, the two-party arm: Pat's written confirmation → Angus commits
   `config/arming.yaml` (token SHA-256, certified commit, account) → `canon_run --arm` on the
   box. `verify_for_arming` enforces that HEAD *is* the certified commit; any other file in
   that diff refuses the arm. Every check fails closed and a refused arm never falls back to
   a shadow run.

---

## 5. Traps — every one of these has already bitten

1. **`risk` is NOT `|entry − stop|`.** They disagree on **28% of validated trades**, by up to
   tens of points: `entry`/`stop` are the trigger's *reference* levels, while the canon sized
   on the engine's realized bracket. Risk drives **both** the 7–60pt gate and the micros
   count. Pass `risk_pts=` from the bracket as PLACED. The verdict records
   `risk_source="explicit"|"bracket"` so the journal shows which was used.
2. **Whatever places the live bracket must place the stop the engine would have.** Same root
   cause as (1) and still unproven end-to-end. If the live stop differs, the gate and the
   sizing both shift.
3. **`on_extreme_age` is two different features sharing one name.** Gold's AGE is
   `on_extreme_age_day` (the completed 18:00–08:00 overnight tape); `on_extreme_age_trade` is
   London's per-trade form. The lane maps the day form. Mapping the other silently changes a
   score component.
4. **Trigger stamps must be naive-UTC `datetime64`.** `badpa_features` compares against
   `fill.to_datetime64()`; tz-aware input raises or miscounts silently, and `trigdens_30` is a
   score component. The lane normalises this — do not bypass it. An empty census leaves the
   key ABSENT so TRIG stands down, rather than asserting a zero density.
5. **Never key verdicts on (fill, direction).** Sibling triggers off one cluster share a fill
   minute *and* a direction routinely. Keying on those dropped the first of a colliding pair,
   and its risk then never left the budget — a leak that grows all session. Use `v["vid"]`.
6. **Thresholds come from `config/live_thresholds.json`, never restated.** An early draft
   hardcoded G at 0.107 (that is VWAPD's cut point) and AGE at 3.0 (the real value is 136.5).
7. **Same-minute fills must sort stably.** `funded_book.load_book` used pandas' default
   quicksort, which ordered ties arbitrarily and silently decided which trade of a tied group
   got the day's elite slot.
8. **A missing feature must refuse, never default.** The ingestor omits keys it cannot
   compute; those read NaN and stand their check down. W and D are NaN-guarded, so absent
   depth means the gate cannot be satisfied. Do not "helpfully" fill a default in.
9. **The 2023/24 holdout has no footprint tape** in `output/fp_minutes.parquet` (2025-06
   onward only), so replaying those days understates every tape-derived score.
   `ny_lane_replay` SKIPS them rather than printing meaningless DIFFs — keep that behaviour.
10. **Suite state:** 739 pass, 2 fail. Both failures are long-standing and unrelated
    (`london_depth.DIR`, `build_ny_substrate.canon_config` attribute drift) and were failing
    before this work. Do not treat a green-except-those run as new breakage.

---

## 6. Not in scope

**London** is still the old canon and is Brake's rebuild (`docs/HANDOFF-london-rebuild.md`).
`LondonScorer` is untouched and **must not be armed**. If the live stack would trade London,
it stays disarmed until Brake's book lands.

The **agent discretion layer** is quantified but unbuilt: measured MFE headroom above V8 is
roughly +0.4R/trade on pre-market. That is a mandate for a later layer, not something to
improvise at the execution boundary.
