# HANDOFF — BRAKE: the London program is yours · written 2026-08-04

Self-contained by design — paste this into a Claude Code session as context, same
as the briefs. **ANGUS ruling 2026-08-04: London is Brake's responsibility. You
own the diagnosis of every London test, and VERDICTS route through you** — you
grade, you write the verdict, you bring it to Angus for rulings. This document
tells you exactly what exists, what ran, what it means, and what's yours.

---

## 0. What you own now

1. **Diagnosis** of every London trial: read the ledger entries, decide what runs
   next inside each pre-registration, direct (or run) the refinement.
2. **Verdicts**: PASS / FAIL / INCONCLUSIVE per docs/VALIDATION-PROCESS.md §5,
   with the numbers, what died and why, what runs next. INCONCLUSIVE blocks like
   FAIL. Verdicts go from you to Angus.
3. **Your DSR/PBO models are the grading stage** for everything here. Two
   refinements waiting for you in VALIDATION-PROCESS §2.4 (from the education
   round): trial counts deflate to *effective* trials by clustering correlated
   configurations, and abandoned trials count in N. Also §2.2's effective-N note
   for overlapping trades, and the proposed two-tier FDR/FWER gate policy.
4. **The statistical knobs** are yours to review before Angus ratifies: all
   [PROPOSED] numbers in VALIDATION-PROCESS §2 and the correlation thresholds in
   docs/REPORT-correlation-2026-08-04.md.

**What stays with Angus:** rulings, holdout-look declarations (the six sealed
months are opened only by his written go), input-family veto waivers, bar
ratifications, thesis-gate picks on new candidates.

**What the Claude research lane keeps doing:** sourcing/deep-dive research,
building infrastructure, running trials under your direction, writing everything
to the ledger. Think of it as your research staff; you are the desk head for
London.

---

## 1. Read these, in this order

1. **research/LONDON-PROGRESS.md** — the one-page live tracker (Angus reads this
   too; keep it current when you run things).
2. **docs/VALIDATION-PROCESS.md** — the law. §1 prereg template, §2 bars (your
   knobs), §3.1 refinement disciplines (trial ledger; the refiner never grades
   itself), §5 verdict format, §7 kill criteria + live decay monitoring, §9
   5-day-loop law. Appendix A is the London bars sheet awaiting Angus.
3. **docs/PREREG-london-inventory-fade.md** + the trial ledger at the bottom of
   research/candidates/london-inventory-fade.md — the first candidate through
   the pipe, live now, kill-criterion-2 question open (see §3 below).
4. **research/candidates/*.md** — nine greenlit theses with mechanics, flags,
   and NY-overlap ratings.
5. **research/findings/** — strategy-classes-evidence.md (decay statuses,
   the MNQ falsification study, the ranked shortlist), quant-math-canon.md
   (every method mapped to the pipeline, incl. your DSR/PBO section),
   how-elite-quants-operate.md, sweep-merge + session-clock notes (a measured
   correction lives there: mismatch-week euro open = 04:00 ET, not 02:00).
6. **docs/CONTRACT-strategy-emission.md** — the format every candidate emits so
   the correlation battery and baselines run with zero glue. Your 30-minute
   ratification conversation with Angus is §9; the reference implementation
   already runs (scripts/emit_strategy.py, interface parity proven against the
   committed battery series).

## 2. The instruments (all built, all self-tested)

| Instrument | Command | What it answers |
|---|---|---|
| Day substrate (912 days) | `python -m scripts.london_day_features` | causal session features all censuses read |
| Emissions | `python -m scripts.emit_strategy` | any book → contract format (+ --check drift) |
| Redundancy detector | `python -m scripts.pairwise_overlap A B` (`--demo`, `--self-test`) | "are these two candidates the same trade?" — run BEFORE expensive validation |
| Portfolio battery | `python -m scripts.correlation_battery` | day-corr, tail co-crash, timing, combined ruin vs the NY canon |
| Funded shell | `python -m scripts.funded_book`, `scripts/mc_funded_lab.py` | the NY reference accounting + MC (MC is never evidence of edge — §6.3) |

Environment note: pinned numpy needs Python ≥3.12; on 3.11 install unpinned
pandas/numpy/pyarrow — everything above runs (verified: conformance 19/19, suite
848 passed + 2 known unrelated fails).

## 3. State of play — the first trial, and the open question that's now yours

**LDN-INV-01 (inventory fade), trial 1, L0 census** (full numbers in the
candidate file's ledger): in 2025 the conditional inventory signature is
textbook — worst-quintile US days → +20.7 pts in the 02:00–06:00 window
(concentrated 03:00–04:00, t≈2.0), best-quintile ≈ flat/negative. In 2026 the
direction holds (+17.9) but **the asymmetry is absent** (best-quintile +42.0 —
everything drifted up). Kill criterion 2 (asymmetry or it's just drift) is live.

**Your first diagnosis call:** the prereg's declared refinement is joint
conditioning — inv_skew_0255 × σ-location (on_vwap/on_sigma at 02:55) on top of
the prior-return quantile — plus the mandatory inverse era pass
(discover-2026/validate-2025). If joint conditioning can't restore asymmetry in
both eras, criterion 2 executes and the candidate gets its tombstone. The
substrate columns exist; the census pattern is in the ledger entry. Direct it or
run it — your call, your verdict.

**Also confirmed in that census** (useful prior for candidates 2–4): the classic
02:00–03:00 drift hour is dead in our sample, matching the NY Fed's published
decay. Residual action sits after the 03:00 open.

## 4. Working rules (the ones that bite)

- **Prereg before test, committed, always.** The git timestamp is the
  declaration. No census runs without one.
- **Every trial hits the ledger** — including abandoned ones. Your DSR
  denominators come from that ledger; an unlogged trial rigs your own grade.
- **2023/24 untouched.** The holdout is the six sealed months (footprint data
  exists for all six), one look per candidate, declared by Angus in writing
  first. Building a sealed-span artifact IS a look.
- **Both era directions** must agree (discover-2025→validate-2026 and the
  inverse). Era-flips kill.
- **Costs are a bar**: taker default, trade-through fills only, slippage as a
  distribution, pessimistic-percentile reporting (a published MNQ falsification
  study is the reason — naive OHLCV signals are dead net of friction).
- **Same account as the NY canon (Angus ruling)**: every candidate runs the
  pairwise detector + battery against the NY book during validation; red-day
  overlap routes to a risk-reconfiguration question, not just a verdict; 3+
  shared input families = veto needing Angus's written waiver.
- **The refiner never grades itself**: whoever/whatever ran the conditioning
  search hands a frozen spec to a separate grading run.
- **Branches**: one per candidate at claude/london-<slug> once its testing
  starts; research memory stays centralized in research/ on
  claude/canon-rebuild-deployment-7m48yv (Obsidian-ready markdown — it becomes
  Pat's vault seed).
- **New strategy ideas** (yours included) go to Angus as a thesis first.

## 5. Suggested order of attack (yours to override)

1. Rule on LDN-INV-01's refinement (§3) — it's mid-flight.
2. Review the §2 knobs + Appendix A with Angus so the bars stop being
   [PROPOSED] — everything downstream grades against them.
3. Preregs for the sweep pair (candidates 2+3 — one family, one ledger) and
   euro-open-drive: cheap censuses off the substrate, highest structural
   priors.
4. eu-macro-windows calendar build — even a null upgrades everything else via
   event dummies (and its stand-aside rule is a spec layer you'll want early).
5. level-defense-flow last of the nine: flow-span only, smallest sample,
   guaranteed veto conversation.

---

*Everything above is committed on claude/canon-rebuild-deployment-7m48yv.
Questions the docs don't answer: the research lane session picks up where this
handoff leaves off — ask through Angus or continue the session thread.*
