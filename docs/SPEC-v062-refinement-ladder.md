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

## APPROVED (Angus, 19 Jul): rungs frozen as written; C2 confirmed. Build is live.

## PREDICTION P9 — Rung 1 outcome (filed while the verdicts run, before ingestion)

Central case: **PROMOTE, capture 22–30%** (bar: >21%), reads **48–54%** (bar: ≥49%
— this one is genuinely at risk), flat rate falling from v0.6.1's 78% to **50–62%**.
Mechanism: all three wires push the same direction in this era — the C2 bill shows
the v0.6.1 lineage its own mountain of read-regret from hiding; base rates price
the fear; event-family analogs + the floored ground truth make momentum the
retrieved answer on event days (floored momentum book 2026: +$7,285). The event-
risk wrong-FLAT class (52% of panel regret) should be cut by more than half.
Secondary predictions: 0.25 sizing on <25% of trading verdicts (prompt forbids
default-0.25); expected_value_usd present in >90% of valid verdicts; ≤3
fail-closed.

Named failure modes (P8's children), with tells:
- **Over-swing** (bill + anti-dilution prompt → trades chop): capture 12–18%,
  under-FLAT cost dominating the leak table → RUNG FAILS, fix is damping the
  bill's tone, not reverting the wires.
- **Prompt overload** (four new sections → confusion): fail-closed >5 or
  citations quoting sections without using them.
- **Reads flat while dollars jump** (the v0.4 analog-block pattern repeating):
  acceptable — the rung's capture bar decides, reads bar is the tiebreak.
Confidence in PROMOTE: ~55%. If it fails, the diagnosis order is: leak table
first, sizing histogram second, prompt third.

## RUNG 1 RESULT (run 19 Jul, 118 verdicts, 0 fail-closed, ~17 min via 3 parallel workflows)

**FAIL.** Official grade on floored books (106 graded days):
- reads 52/106 = **49%** (bar ≥49%: met exactly)
- capture full-size **+$4,059 = 9%** of the $45,419 ceiling (bar >21%: FAILED decisively)
- as-verdicted +$1,356 = 3%; FLAT rate **81%** vs oracle 50%
- champion switch on same floored books: +$13,188 = **29%** capture
- expected_value_usd present in 100% of verdicts; zero fail-closed

**P9 graded: MISS.** Central case was promote at 22-30% capture with flat rate
falling to 50-62%. Reality: flat rate ROSE to 81%. The failure mode was not the
over-swing I hedged 45% on — it was ANCHOR LOCK, which I did not name:

1. The v0.6.1 rule "stand down when analog majority_action==FLAT" survived into
   v0.6.2 (posture kept by design). The analog majority is FLAT on ~80% of days,
   so the anchor binds almost daily and OUTRANKS the new sections.
2. The base-rates topline ("47% of days FLAT; both books negative
   unconditionally") reads as a standing endorsement of hiding when presented
   without conditioning — the counterweight armed the fear it was built to price.
3. The C2 bill was sourced from the v0.6.1 lineage, whose rolling sizing regret
   was POSITIVE (its caution had been locally profitable) — the bill certified
   the anchor instead of fighting it. Evidence: 03-17 FOMC analogs voted
   6 FLAT / 2 MOMENTUM; the agent obeyed the cohort and missed +$3,485; top-8
   leaks are ALL FLAT-on-winners, again.

Per the frozen ladder: STOP, diagnose (done above), no rung re-sit until a v0.6.3
proposal is reviewed by Angus. The three wires are not disproven — they were
overruled by a rule that predates them. Proposed v0.6.3 delta (ONE change class):
demote the analog-majority-FLAT anchor from a RULE to one input among the
retrieval evidence, and present base rates conditionally only (no unconditioned
topline). Bill source switches to the config's own lineage as soon as it has one.

Standing fact worth its own line: **champion switch + R1/R2 floor = 29% capture
(+$13,188) on 2026** — the strongest verified whole-config on the board today,
fully mechanical. The bar for any agent lineage is now explicitly this number.
