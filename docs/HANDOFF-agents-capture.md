# HANDOFF — chained-agents capture test on the NEW canon

ANGUS 2026-07-30, switching accounts at the weekly limit. Next session picks up here.

**The mission:** run a chained-agents test to see whether an agent layer can capture more of
each trade than the mechanical V8 exits do — **on the rebuilt canon**, which for the first
time means the agents are working from honest data. The last time this was tried it sat on
the broken substrate (shared trade cap starving gold), so every conclusion from that round is
void along with the rest of the old canon.

**Why this is worth doing — the mandate is quantified, not a vibe.** The exit study measured
real headroom above V8: on pre-market the hold-to-ceiling gap is roughly **+0.4R per trade**
of MFE the mechanical exits leave on the table. And the reason mechanics can't reach it is
known: the deep-target menu's median target sits **10.6R away** — no fixed rule bridges that;
only in-trade judgment might. That gap is the agents' entire hunting ground.

**Why the deck is better than last time:** the entry stream is validated (uncapped, W/D
gates, wall-quality cut, all conformance-tested), and the **sealed 2023/24 holdout exists**
— 122 days the discovery process never touched, where the canon runs *better* than fit
(61% WR pre, book +$56,409). Any agent policy that improves fit must survive holdout
untouched, and this time there is a real holdout to demand that of.

---

## 1. State of the world (read once, trust it)

- **The canon is shipped and law.** `docs/CANON.md` is the orientation doc;
  `scripts/funded_book.py`'s docstring is the spec. Reference results: `lucid` fit
  **+$90,015** / holdout **+$56,409**; `scaled600` fit **+$320,662** / holdout **+$188,325**;
  every month green in both spans. The old canon is deleted — do not resurrect anything from
  git history.
- **The live re-arm is Pat's parallel track** (`docs/HANDOVER-pat-arming.md`,
  `docs/ARMING-REFERENCE.md`). It does not block this work and this work must not touch it:
  `src/canon/scorer_ny.py`, `src/canon/ny_lane.py`, `src/live/ny_runner.py` and their tests
  are conformance-locked. The agent layer sits ON TOP of canon entries — it never changes
  which trades are taken, only how they are managed after the fill.
- **Branch:** `claude/random-days-validation-sgjprr`, pushed through `039f086`. Suite: 756
  pass, 2 long-standing unrelated failures (`test_holdout_forward_pipeline`,
  `test_holdout_london_depth_integrity`) — not yours, don't chase them.
- London is Brake's rebuild. Not yours either.

## 2. The data you work from (all committed or regenerable)

| Artifact | What it is |
|---|---|
| `output/aikido_{fit,holdout}.parquet` | **The canon dataset** — every validated trade, scores, tiers, elite flag, L1 events (`struct_event`, `max_away_before_fill`), fill/exit stamps, `dollars_1lot`, `win`. Committed. |
| `output/l3_scored_{fit,holdout}.parquet` | The full scored candidate population (including refused trades — useful context features). Committed. |
| `output/l2_mfe_fit.parquet` | **The capture ceiling** — MFE / MAE / hold-to-close per fill (stop-first same-bar convention). Regenerate holdout with `python -m scripts.l2_mfe_walk --span holdout` if it accepts a span; read the script first, it's small. |
| `output/fp_minutes.parquet` | Minute footprint tape (delta/vol/vwp), **2025-06 → 2026-07 ONLY** — no 2023/24 tape. Any in-trade flow feature is fit-span-only evidence; holdout confirmation of flow-based exit rules is NOT possible at minute-tape granularity. Plan around this from day one. |
| `data/reference/nq_1m_master.parquet` + `nq_1m_feb_jul2026.parquet` | 1m bars, both spans (`scripts.build_l2_outcomes.load_bars`). |
| `data/reference/depth_*` | Per-minute top-10 book snapshots, both spans. |
| `src/backtest/engine.py` | `simulate()` with the V8 management — the baseline the agents must beat. V8 = 50% partial at first structure, prior-5m swing trail, BE, 3-min cut, EOD flatten. |
| Agent infra | `.claude/agents/trade-manager.md`, `trade-manager-replay.md`; `scripts/run_intrade_replay.py`, `scripts/trail_policies.py`, `scripts/intrade_matrix.py` (kept desk infra). |

## 3. The rules of the test (non-negotiable, each one has a corpse behind it)

1. **Causality or it doesn't count.** An exit decision at minute t may use ONLY information
   with timestamps ≤ t. The last chained-agents attempt on the old canon produced a
   beautiful uncapped result that **collapsed the moment it was tested causally** — the
   agents were leaking exit timing. Build the causal harness FIRST, then let agents play
   inside it; never bolt causality on after seeing a good number.
2. **The baseline is V8 on the SAME fills.** Compare per-trade, same entries, same stops:
   agent-managed R vs V8 R, trade by trade. Book-level totals hide per-trade leakage.
   Metric: **capture ratio = realized R / MFE R** per trade, plus mean ΔR vs V8 and the
   effect on worst-day / maxDD under the shipped sizing (`funded_book.run` with the agent
   exits substituted).
3. **Discover on fit, confirm on holdout, frozen.** The holdout is sealed 2023/24. One shot,
   no refits after looking. Remember the tape constraint (§2): any rule needing minute flow
   cannot be holdout-confirmed — either restrict agent inputs to bar/level data that exists
   in both spans, or accept and STATE that flow-based components carry fit-only evidence.
4. **Permutation null on anything mined.** Shuffle outcomes, re-run the search, record the
   best apparent lift on noise. The old canon's top combo pick failed out-of-era; the null
   is what catches that in-house.
5. **Oracle ≠ policy.** A hindsight-optimal exit book does not generalize (measured, old
   canon era, lesson survives). The oracle is the CEILING for reporting, never the target.
6. **Stops are inviolate.** Agents may exit earlier or hold longer toward targets; they may
   never widen a stop, average down, or re-enter. The stop the engine placed is the stop.
7. **Every kill attributable.** Same standard as the rebuild: any trade the agent manages
   differently from V8 carries a reason readable in the journal.

## 4. Suggested shape (adapt freely, the rules above are the constraint)

- **Replay harness:** for each aikido fill, stream post-fill bars (+ tape where it exists,
  fit only) minute-by-minute to the agent; the agent emits hold/partial/exit; settle against
  the actual path; stop-first on same-bar conflicts (the L2 convention).
- **Chained = the desk pattern:** a reader summarising in-trade state, a manager deciding,
  each with bounded context — the prior intrade replay infra (`run_intrade_replay`,
  trade-manager agent specs) is the starting scaffold, now pointed at aikido fills.
- **Segment before averaging:** capture headroom is not uniform — pre vs gold, tier, elite,
  `struct_event`, risk band. A policy that only helps pre 1.5x trades and is neutral
  elsewhere is a finding, not a failure.
- **Report like the rebuild did:** verdict per stage, fit table + holdout table + the delta
  vs V8 under shipped sizing, and the honest list of what was excluded and why.

## 5. Things future-you will otherwise rediscover the hard way

- `aikido` timestamps are mixed-DST strings: always
  `pd.to_datetime(..., format="mixed", utc=True)`, never naive parsing. (Bit us three times.)
- `risk` in aikido is the ENGINE's bracket (`|limit − stop_initial|`), NOT
  `|entry − stop|` — those disagree on 28% of trades. Use `risk` for R math.
- Same-minute sibling fills exist everywhere: sort with `kind="mergesort"` and never key
  anything on (fill, direction) — use a sequence id.
- `dollars_1lot` is per 1 lot; the shipped book's P&L is `micros × dollars_1lot / 10`.
- The holdout has **no fp_minutes tape** — see §2. Fit-only flow evidence must be labeled.
- 756 tests pass; the 2 failures named in §1 are pre-existing. If your work breaks a third,
  that one IS yours.

## 6. Pre-measured terrain (2026-07-30, fit span — start here, don't re-derive)

`output/time_segments_fit.parquet` (per-trade minute-close R at t+2/3/5/8/10 for every canon
trade) and the MFE join both exist. Headlines:

- Realized +0.55R vs MFE +2.32R mean — giveback ~1.77R/trade (~$50k 1-lot over fit).
- Winners/losers separate on MAE instantly: winners' median MAE −0.28/−0.33R, losers'
  −1.19/−1.20R; losers peak at minute 0–1, winners at 4–9.
- ~60% of losers showed >=+1R MFE before dying (a quarter showed +2R) — the partial-banking
  pool.
- **The old canon's drawdown-at-t cut is INVERTED here**: still-open shallow-drawdown trades
  finish +0.01R (pre) / +0.32R (gold) at t+3, and the deep-drawdown bucket is nearly empty
  (V8 + wall gates already removed it). Era-unstable too. Do not resurrect the cut.
- The strong, monotone, era-worthy signal is IN-PROFIT persistence: gold still-open-and-green
  WR climbs 69%→85% from t+2 to t+10; pre 48%→61% with +1.47R mean at t+10. Agent alpha =
  pressing/holding green, banking partials on losers that flash +1R — NOT cutting red.
- Pre and gold need different management (pre winners run to 3.8R mean MFE and hold-to-close
  4.29R; gold peaks fast and shallower).

## 7. Definition of done

A frozen agent exit policy with: (a) per-trade fit results vs V8 on identical fills, (b) the
one-shot holdout confirmation, (c) permutation-null clearance for anything mined, (d) the
funded-sizing delta (net / worst day / maxDD, both profiles), and (e) a verdict honest enough
to ship or to kill. **"Agents don't beat V8" is a valid, valuable outcome** — it would close
the capture question with the same finality the rebuild closed the entry question, and it
protects the book from a discretionary layer that only looked good leaky. Do not torture the
data until it confesses.
