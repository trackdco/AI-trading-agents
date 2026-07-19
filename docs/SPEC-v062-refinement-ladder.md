# v0.6.2 SPEC + the refinement ladder to the 60% target (Angus directive, 19 Jul)

Context: Pat runs the live PAPER stack on the frozen champion (pipes-proving; his
parity gate + day_gate seam mean the driver swaps in later with zero engine work).
Research lane refines the agent; nothing pushes to the live gate without climbing
the full ladder below. Target: 60% of oracle+SD efficiency; current best honest
marks — 2026: 19% (v0.6), Q2 2025: 2% (v0.6.1, bar-passing).

## v0.6.2 — one config, zero new ideas, three PROVEN wires

Start from the v0.6.1 posture (the only config that has ever passed a
pre-registered bar) and attack its measured leak (FLAT on momentum winners:
18 days / $12k+ of its Q2-2025 regret) with things already measured to work:

1. **R1/R2 timing floor ACTIVE** in both the grading books and the live config
   (engine: src/backtest/event_timing.py, measured +$13,018/4yr on event days).
   Grading ground truth becomes "books as the engine will actually trade them" —
   requires one dump_daily_books rerun with the floor on (engine lane, ~10 min).
2. **Priced retrieval in the briefing** (desk wiring of built tables):
   base-rates block (today's-features slices, --asof for replays) + event-family
   analog filter ("last 8 CPI mornings, what paid post-release"). This is the
   direct counter to BOTH residual leak classes: v0.6.1's hidden momentum winners
   and v0.6's wrong-book picks (base rates: event days 54% FLAT, rotation −$84/d,
   momentum −$24/d).
3. **Dollar feedback (C2 contract)** via src/desk/briefing_v05.feedback_block —
   mechanical ground truth, NOT self-authored narrative (fresh-eyes stays
   memory-free; the bill is computed by the driver). Requires Angus's formal
   contract-relaxation confirmation to Pat (docs/FOR-ANGUS-c1c2-contract-question.md
   — recommended: option 1-modified, dollars with the rolling-20d damper).
4. **Sizing tied to stated expectancy**: keep {0, 0.25, 0.5, 1.0} but the prompt
   requires expected_value_usd and forbids 0.25-as-default (v0.6 used 0.25 on
   44/62 days — dilution, not judgment). Graded on score_sizing discrimination.

Explicitly NOT in v0.6.2: new prompt philosophies, memory experiments, analog-
majority anchoring beyond v0.6.1's current rule. One bump, attributable.

## The ladder (each rung pre-registered BEFORE its run; fail = stop, diagnose)

- **RUNG 1 — 2026 whole-year re-sit** (~108 verdicts, minutes-to-an-hour).
  Directly comparable to the existing table (v0.5 15% / v0.6 19% / v0.6.1 11% /
  champion 21%). PROMOTE if: capture > 21% (beats always-trade champion in its
  home era) AND reads ≥ analog majority (49%).
- **RUNG 2 — fresh red-era holdout: a 2024 quarter** (Q2 2025 is SPENT — seen by
  us, retired to regression duty). Both arms (v0.6.2 vs v0.6.1) sit it blind.
  PROMOTE if: v0.6.2 ≥ $0 AND ≥ v0.6.1 on the quarter AND ≥ 10% capture
  (2× the Q2-2025 pass, still far under the 30% distinction bar — honest ramp).
- **RUNG 3 — full-history fresh-eyes** (~890 verdicts, the anti-overfit grade).
  PROMOTE if: beats v0.6.1 baseline on 4-year capture AND in ≥3 of 4 years
  individually (no single-era heroes) AND every-year ≥ $0 at as-verdicted sizing.
- **RUNG 4 — live paper A/B**: agent gate on the day_gate seam next to the
  champion paper account, same feed, ≥ 20 trading days, Telegram-visible.
  Only after Rung 4 does any go-live conversation exist.
- Regression duty: every promoted config re-sits Q2 2025 + June 2026 silently;
  a regression on a spent holdout is a stop-the-line event.

## The two gates only Angus can open

1. C2 contract relaxation — formal "confirmed" to Pat (dollars in the briefing).
2. Rung definitions above — approve or amend the thresholds; then they freeze.

## The feature runway behind v0.6.2 (gated on data, not opinions)

- A2 AMT features into the briefing + vector distance (built: value_position,
  open_vs_value, inventory_pts) — Pat's own "richer features" requirement.
- April 2026 mbp-10 (Angus, post-Starlink) → order-book confirmation features —
  the last leg toward the 60% ambition per the fork-test finding that current
  features cap the read.
- Historical-analog K-NN upgrade: distance metric now includes real red_folder;
  event-family conditional analogs are the A3 completion.
