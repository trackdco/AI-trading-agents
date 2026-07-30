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

**Profiles.** `lucid` = base $150 flat (ladder $75/150/225/300, budget $800).
`scaled600` = base $150, +$75 per full $2k of buffer past +$3k, capped $600, with budget and
soft de-risk scaling *with* the base. Pick one at construction and give the spine the same
one (`SpineConfig.profile`) or the backstop is indexed to a base the sizer never uses.

**Risk spine.** Daily budget: `realized losses + in-flight risk + new risk ≤ budget`, where
budget = base × 16/3. Soft de-risk to half at −35% of budget. **De-risk ladder near the line
(Angus 2026-07-30): half size below $1,000 of remaining drawdown, half again below $500** —
tightest applicable step wins, and the spine's $100 hard halt sits underneath. Micros =
`round(risk$ / (stop × $2))`, floored at 1, clamped to 40.

---

## 2. What is already proven — and how to re-run it

```bash
python -m pytest tests/test_canon_scorer_ny.py tests/test_ny_lane.py -q   # 35 tests
python -m scripts.funded_book --span fit --profile lucid                  # +$90,015
python -m scripts.ny_lane_replay --span fit --days 25                     # 25/25 days
python -m scripts.depth_parity --day 2026-04-20 --self-test               # PASS
```

- **The live scorer reproduces the shipped book exactly** — every row of both spans, both
  profiles, same trades / tiers / risk dollars / micros / P&L. It re-derives the gates from
  raw depth and flow columns rather than reading the book's precomputed verdicts, so this also
  proves the live re-derivation of W, D, the wall cut, the scores and the tiers.
- **The live lane reproduces the book on 25/25 real fit days** — real bars and tape streamed
  through `CanonIngestor`, features built by the live code path, scored live.
- **The depth harness is clean on both book models** — 180 archive minutes through
  `DepthBook`, and an MBO capture through `OrderBook`, both at 100% gate agreement. MBO
  aggregated to price levels *does* reproduce the archive's wall features.
- Reference results (50k account, $2k EOD-trailing): `lucid` fit **+$90,015** / holdout
  **+$56,409**; `scaled600` fit **+$320,662** / holdout **+$188,325**. Every month green in
  both spans under both profiles. The de-risk ladder is dormant across all 19 months
  (min buffer $1,621 fit / $1,720 holdout), so it changes no measured number.

---

## 3. Behavioural changes from the deployed stack — read before arming

| # | Change | Consequence if you miss it |
|---|---|---|
| A | **Entries are uncapped.** No 2/day slot, no nth-escalation, no day ladder, no governor, no cold trail. Capacity is the BUDGET. | The book averages ~4 trades/day and legitimately runs into double digits. |
| B | `RiskLimits.max_trades_per_day` **3 → None** | The old 3 backstopped a 2/day engine cap that no longer exists. Left at 3 it would announce a halt and stand the account down mid-session on most days. This was the most dangerous stale default in the repo. |
| C | Spine `daily_loss_halt_r` **−4R → −8R** | At the $150 base, −4R is −$600 — *below* the canon's own $800 budget. An outer guard that fires before the inner one truncates the validated book. −8R is exactly 1.5× the budget at every base. |
| D | **No distance cancel.** Orders live to their session window end. | The 22pt `t_cancel` measured inverted: it kept −0.180R and killed +0.015R. `OrderWatch.t_cancel` now defaults to `None`; setting a float trades a book nobody measured. |
| E | **Per-order session window** (pre 09:30, gold 10:30) | One global window cannot serve both; an order outliving its session is an unmeasured trade. Pass `win_end=` per order. |
| F | Gold window **09:40–10:30**, and **no 09:55–10:00 dead zone** | The rebuilt canon was validated without one. |
| G | Sizing base **$200 → $150** | Every order size changes. |
| H | De-risk ladder replaces the linear taper to zero | Between $100 and $1,000 of buffer the canon now takes half/quarter-size trades where the old canon refused. Angus's ruling; the spine's $100 halt is the floor. |

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
3. **Wire the runner to the lane.** `NYLane` is event-driven by necessity: the budget, the
   elite slot and `struct_event` only exist at fill time. `RouteBLive._load_verdicts` loads a
   whole day up front, which is the wrong shape — you need a per-candidate hook:
   ```python
   lane.start_day(day, buffer=equity - trailing_line)     # once per session
   v = lane.on_candidate(fill_ts=..., entry=..., stop=..., direction=...,
                         risk_pts=<the PLACED bracket's stop distance>,
                         trigger_times=<the day's census stamps>,
                         struct_event=watch.struct_event(ref))
   if v["take"]: route it, then lane.confirm(v)           # on FILL
   lane.on_exit(v, pl=realized)                           # on CLOSE
   ```
   `evaluate` is pure, so re-ask it on every bar while an entry rests — budget room consumed
   by an earlier fill **must** cancel a resting order, and that is the only way to notice.
4. **Join `struct_event` through.** `OrderWatch` tracks it (L1-mirrored, tested) and the lane
   accepts it, but nothing connects them yet. Until it is joined the elite 2.0× never fires:
   safe degradation (absent evidence never escalates size) at the cost of ~6% of trades
   sizing below the validated book.
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
