# HANDOFF — London canon, session 3 → session 4

**Written 2026-07-30 at the end of session 3 (the "everything day"). Read top to
bottom before touching anything. Prior handoffs: `HANDOFF-london-rebuild.md` (the
L0→L4 rebuild), `HANDOFF-london-session2.md` (fit-side search → prereg). Assume the
reader has NO session's context.**

---

## 0. State of the repo

- **Branch: `claude/london-canon-strategy-xay1gz`** — everything committed and
  pushed. It was re-cut from session 2's `...-3p57jk` HEAD per that handoff's
  instruction; all session-3 work is on top. Develop and push here (or re-cut from
  its HEAD if the harness assigns a new branch — cherry-pick nothing).
- **Environment rebuild from cold** (containers die; this works): system Python is
  3.11, pins need ≥3.12 → `uv venv .venv --python 3.13 && uv pip install -r
  requirements.txt --python .venv/bin/python`. Then regenerate the one gitignored
  input: `.venv/bin/python -m scripts.funded_book --profile lucid` (must print the
  NY anchor 920/230/+$90,015/−$762/$1,603/13), then
  `.venv/bin/python -m scripts.london_combined_job --stage preflight` → PREFLIGHT
  PASS. The London L0–L3 fit artifacts are ALSO gitignored — rebuild:
  `build_l0_triggers_london --span fit` → `build_l1_fills_london --span fit` →
  `build_l2_outcomes_london --span fit --procs 3` → `build_l3_features_london
  --span fit` (~2h total; reproduced all 21 rev-2a anchors from raw data this
  session — that reproducibility is itself a verified result). Also rebuild the V1
  arm: `build_l2_outcomes_london --span fit --mgmt V1` (and V0 if wanted).
- **No scipy** — Spearman = Pearson-on-ranks; the t-test in the holdout runner is
  exact via incomplete beta.
- **Sealed 2023/24 span: NEVER read for outcomes.** Unchanged from session 2.

## 1. Where the strategy now stands (rev 3 proposed, rev 2a still of record)

**The decision package for Angus is `docs/LONDON-REV3-BUNDLE.md` — start there.**
Proposed rev 3 = window 08:00–09:45 + score-0 veto (FROZEN literals in
`src/canon/scorer.py`: LON_VETO_THICK 57 / RESIST 29 / TRIGDENS 8) +
one-position-at-a-time + V1 management (BE at +1R). Fit: **130 trades, +$22,665,
+0.758 mean R, maxDD $1,310** (rev 2a book: 187 / +$22,795 / +0.513 / $2,550 —
same money, 40% fewer trades, twice the quality, half the drawdown).

**The holdout runner (`scripts/london_holdout_report.py`) is dual-config and BOTH
rehearsals PASS byte-deterministically** (`--span fit --config rev2a|rev3`).
Whichever config Angus signs, the sealed run is one command. The sealed report
writes once, whichever config; the runner refuses a second opening.

## 2. What session 3 established (chronological, each with its verdict doc)

1. **Rev-2a rehearsal machinery** built and passed after full pipeline rebuild
   (LONDON-HOLDOUT-REHEARSAL.md). Two defects found ON FIT: missing `session`
   column; **maxDD convention pinned** — prereg reference = TRADE-level ($2,550
   for 2026-fit), day-level ($2,440) is the late-bucket doc's convention.
2. **Conviction sweep** (LONDON-CONVICTION-SWEEP.md): nothing clears worst-of-22
   on 144 trades; structure that IS there: **B2 rejection-block 69%/+0.934 vs
   displacement 56%/+0.420**; both-wall 63%/+0.759 vs one 60%/+0.319; **A+ cell
   (B2 & both-wall): 48 tr, 69%, +1.007R both eras** — a third of the book, 58%
   of its net.
3. **TF conviction** (LONDON-TF-CONVICTION.md): 1min is the weak leg everywhere
   (гate counterfactual +$751 at 42%); **INTEGRITY FINDING — same-order twins**
   (329 groups, TF grids converge on identical orders 1–4 min apart, backtest
   double-counts; doc §1 "simultaneous" can never fire — lowest TF triggers first
   290/329) + 26/144 overlapped entries (§5 violation) + 46 twin groups with
   DIVERGENT simulated exits from one order (engine flag, Pat).
4. **Confluence sizing** (LONDON-CONFLUENCE-SIZING.md): literal confluence-count
   ladder is an ERA CROSSING (89%→52% WR) — rejected; the same instinct on the
   wall/A+ axes works.
5. **Veto scan** (LONDON-VETO-SCAN.md): of 7 declared candidates, ONLY score-0
   passes all three bars (era-bad + net≤0 both eras + n≥10): 11 tr, 36% WR,
   −$415/−$28. Removing it RAISES net. Everything else is a profit trap
   (wrong-side-VWAP cell nets +$4,674!).
6. **Loser stats** (LONDON-LOSER-STATS.md): losses are fast (median 8 min), all
   stops, uniform across time/direction; counter-trend 46% loss rate vs
   with-trend 28% — **doc §8's counter-trend-raises-confluence was never
   implemented for London** (declared candidate, bar-raise not veto).
7. **Liquidity/pool/bias scan** (LONDON-LIQUIDITY-SCAN.md): no survivor — the
   wall gate already IS the liquidity-draw filter (LON_FAR_MIN comment: "magnet
   not choke"; only 4 stack trades have a wall behind, all 4 won).
8. **DOW** (LONDON-DOW-MFE.md, LONDON-DOW-CHARACTER.md): Mon best (73%/+0.880 —
   the market is different: 210pt weekend dislocation), Fri = composition (62% B2
   share; Fri A+ 86%/+1.44); Tue's weakness = its non-A+ junk. No weekday rule —
   the ladder subsumes it. **MFE: 42% of losers touch +1R before dying** (fill-bar
   exclusion bug found+fixed).
9. **MANAGEMENT TOURNAMENT** (LONDON-MGMT-TOURNAMENT.md) — the big one: **V1
   (BE at +1R) +$22,360 vs V8 +$17,941 vs V0 +$14,850**, era-consistent, real
   engine, pipeline gate exact. V1 = Angus's own declared priority tournament and
   his hand-log style. Bar-walk had predicted only +$1,194 — the partial haircut
   was the hidden cost.
10. **Exit lab** (LONDON-EXIT-LAB.md): fixed 4R ≈ menu (no fixed RR beats
    structure); **grade-scaled exits real** (A+ monotone to 5R, mid peaks at
    1.5R); wall-as-TP untestable (MBP-10 sees ~10 levels = 0.5R; targets live
    ~3R) — full-depth data = Angus purchase decision.
11. **Robustness** (LONDON-ROBUSTNESS.md): costs linear (+4 ticks/side → V1
    +$17.9k); perturbation plateaus except the window's early side; **MC eval**
    (LONDON-MC-EVAL.md, LONDON-MC-LADDER.md): full-edge P(bust) 0.2%, HALF-EDGE
    ~14–20%, zero-edge ~74% — the honesty ladder.
12. **Rev-3 boundary**: 09:30 → 09:45 (dominates: same maxDD $958 stack-level,
    +$1,000; the removed 15 min are net-negative alone). **Three-look disclosure
    on record; boundary CLOSED to fit-side moves** (LONDON-REV3-BASELINE.md).

## 3. Traps burned this session (append to the standing list)

1. **The fill bar's extreme predates a limit fill** — MFE/excursion walks must
   exclude it (a long limit at support fills as price falls INTO it).
2. **maxDD has two conventions in the docs** — trade-level (prereg reference) vs
   day-level (late-bucket doc). State which, always.
3. **`risk` on lon_book output is DOLLARS (×20)**; on the population it is POINTS.
   Bit us again this session (spot-check sheet).
4. **Fill price improvement**: on 41/129 stack trades the fill improved through
   the limit, so |fill−stop| < risk/20. Sizing basis = order-time limit-to-stop.
   Not a bug; document or it looks like one.
5. **Bar-walks understate engine effects 3×** (V1: bar-walk +$1,194, engine
   +$4,419 — the partial haircut was invisible to the walk). Rank with walks,
   confirm with the engine.
6. **A "veto" that removes positive money is a risk trade, not a loss-avoider** —
   price the removed cell's NET per era before believing any filter (three
   profit-traps dodged this session).
7. **StructuredOutput workflow agents failed en masse once** (8/8 schema
   retries) — plain-text agents or direct reads were fine. Don't over-schema.
8. **The V0 arm has one unresolvable trade** (2025-11-27 Thanksgiving 5min short
   — set-and-forget never exits before the holiday close). Disclosed, dropped
   V0-only.

## 4. Open items, in order

1. **Brake**: re-confirm the rev-2a draft changes (rev-1 signature doesn't carry).
2. **ANGUS**: the bundle (`docs/LONDON-REV3-BUNDLE.md`) — sign rev 2a OR rev 3;
   rule the three engine questions (twins, day-stop units, far-target rule);
   optional sealed-span session-ranges yes/no; the 22-trade spot-check sheet
   (`docs/FOR-ANGUS-spot-check-sheet.md`).
3. **Sealed run**: build holdout artifacts (`--span holdout`, + `--mgmt V1` L2 arm
   if rev 3), then `london_holdout_report --span holdout --config <signed>
   --authorized-by "ANGUS, <date>"`. Once. Read at the declared resolution:
   near-miss on +0.48 is not decay; a sign flip is.
4. **Post-holdout, if primary validates**: sizing decision (ladder menu in the
   bundle §4 — flat vs Brake ladder vs wall-only; MC says ladder=faster,
   flat=safer at half-edge); grade-scaled exit engine variant; NY profile
   decision (lucid vs scaled600 — still the biggest dollar lever in the project).
5. **Pat's engine lane** (needed for live parity regardless of signatures): twin
   divergent-exit fix; live one-position-at-a-time enforcement; day-stop unit per
   Angus's ruling; L2 column semantics doc (entry=fill px vs sizing basis).
6. **Parked for forward data** (do not reopen on fit): S3 mild VWAP cut, late/
   window profile, counter-trend bar-raise, post-loss escalation, backing≥2,
   Monday-dislocation conviction input, range-scaled targets, full-depth
   wall-as-TP (data purchase), 10:00+ window (data purchase).

## 5. Standing user instructions (verbatim, still in force)

- "Fit spans only. Holdout stays sealed — fail loudly if any code path touches a
  sealed span." · "Write a verdict file per stage, commit and push between
  stages, assume this context won't survive." · "Report every null as a null." ·
  "Floor stays 9.5 if it survives." · "Causally implementable priority rules
  only." · No independent resampling of correlated books in MC. · NY sanity
  anchors: +$90,015 / 920 / 230 / maxDD $1,603; preflight must PASS before
  trusting anything downstream.
- NEW this session: sizing stays flat 1 lot until the holdout validates volume
  (standing ANGUS ruling, reaffirmed); the window boundary is CLOSED on fit data;
  declared forward expectation stays +0.48 under either config.

## 6. How to resume in one command

```bash
git fetch origin claude/london-canon-strategy-xay1gz && \
git checkout claude/london-canon-strategy-xay1gz && \
.venv/bin/python -m scripts.london_combined_job --stage preflight && \
.venv/bin/python -m scripts.london_holdout_report --span fit --config rev3
# expect: PREFLIGHT PASS, then REHEARSAL PASS [rev3]
```

Immediate conversation state at handoff: all five finalization deliverables are
committed (frozen veto literals, dual-config runner with both rehearsals passing,
spot-check sheet, the bundle, this handoff). **The project is
finalized-pending-signatures. The next concrete action is §4.1–4.2: the two
sign-offs, then the sealed run.**
