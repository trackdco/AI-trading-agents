# Strategy Research & Validation Protocol v1.0

**What this is for.** Angus finds a strategy — a video, a thread, a trader he
trusts. This document is the conveyor belt that turns that into either a signed
entry in the strategy book or a documented rejection. Same track every time, so
that ten strategies later we can still say why each one is in or out.

**The one rule that outranks the rest:** every stage produces an artifact with a
**Plain English** block at the top. If Angus can't read that block and say
"yes, that's what I thought we were testing" or "no, that's not the setup" —
the stage is not finished. A stage that only a quant can audit is a stage nobody
audits.

**Companion documents**
- `context/validation-gate-v1.md` — the numbers a strategy must hit to pass.
- `context/quant-in-plain-english.md` — every statistical term used here,
  translated into order-flow language.
- `context/data-inventory.md` — what data exists. **Read before Stage 3.**
- `strategies/_TEMPLATE/` — the artifact templates for each stage.

---

## The pipeline at a glance

```
  0  INTAKE          Angus brings a strategy + a source
  1  RESEARCH        YouTube sweep + web → dossier of what the source actually claims
  2  MECHANISM       One paragraph, plain English: WHY should this make money?
                     ├─ no mechanism → REJECT here, cheaply
  3  SPECIFICATION   Rules pinned down until code could execute them blind
  4  SUBSTRATE       Run the raw rules over 2025-07 → 2026-06. No filters. Ugly on purpose.
                     ├─ fewer than 60 triggers → REJECT (not enough to learn from)
  5  REFINEMENT      Cut the losers, keep the winners. Every cut logged. Budget enforced.
  6  FREEZE          Rules locked, version-stamped, committed. No edits after this line.
  7  OUT-OF-SAMPLE   One run on untouched data. One. Looking twice burns the sample.
  8  VERDICT         Against the gate. Plus correlation vs the strategies already in the book.
  9  PROMOTION       Into the book with a "when to use" tag, or into the graveyard with a reason.
```

Stages 0–3 are cheap and reject most candidates. Stage 4 onward costs real
compute. **The point of the early stages is to kill bad ideas before they get
expensive.**

---

## Stage 0 — Intake

Angus supplies:

- The strategy's name, and the source (video URL, transcript, thread).
- Why he trusts this source. One line. "He posts his losers too" is a reason.
  "It's got 400k views" is not.
- Which session and instrument he thinks it belongs to (Asia/gold,
  London/NQ, NY/NQ).

Create the folder:

```
/youtube_start_dossier "Strategy Name"
```

→ produces `strategies/<slug>/00-source.md`.

---

## Stage 1 — Research

Goal: know what the source *actually claims*, separately from what it *sounds
like* it claims, and find out whether anyone else has tested it.

```
youtube_research_sweep("<strategy name> nasdaq futures", max_videos=12)
youtube_research_sweep("<strategy name> backtest results", max_videos=8, label="<slug>-evidence")
youtube_grep_transcripts(r"stop.?loss|invalidat|entry|risk to reward|win rate|session")
```

Then WebSearch for the same terms plus `site:reddit.com`, `site:elitetrader.com`,
and any published backtest. **Actively look for the disconfirming version** —
"why X doesn't work" is worth more than the tenth tutorial.

Output: `01-research-dossier.md`. It must contain:

| Section | What goes in it |
|---|---|
| Stated rules | Verbatim quotes, with video ID and timestamp. Quotes, not paraphrase. |
| Contradictions | Where two sources give different rules for the same setup. |
| Unstated rules | What the source does on the charts but never says. Usually the actual edge, and usually the hardest part. |
| Claimed performance | Win rate / RR as claimed, with the source. Flag when it's unverifiable. |
| Prior art | Anyone who has tested it. What they found. |
| Discretion inventory | Every place the source says "you'll get a feel for it". Each one is a parameter we'll have to invent. |

**The discretion inventory is the most important section.** A strategy with two
discretionary points can be mechanised. One with nine cannot — it is a style,
not a strategy, and it should be rejected at Stage 2 with that written down.

---

## Stage 2 — Mechanism

One paragraph. Plain English. Why should this make money — who is on the other
side, and why do they keep taking that trade?

Good: *"Europe's open leaves a stack of resting orders above the Asian high.
Price runs them at London open because that's where the liquidity is, then the
move fails because the buyers who lifted it were stop-driven, not real. We're
selling the failure."*

Bad: *"When the 21 EMA crosses the 50 EMA momentum is confirmed."* That is a
description of an indicator, not a reason anyone loses money to us.

Write it in `02-hypothesis.md` alongside:

- **What would have to be true** for the mechanism to hold.
- **What would falsify it** — the observation that would make us drop it. Write
  this *before* seeing any results. It's the difference between a test and a
  search for confirmation.
- **Which session and why** — the mechanism should imply the session. If it
  works equally well at all hours, it's probably not a mechanism.

**Gate: no plausible mechanism → reject.** Cheapest rejection available. A rule
that works with no reason why is a coincidence that hasn't expired yet.

---

## Stage 3 — Specification

Turn prose into something code can execute with zero judgement. Every one of
these has a number or an explicit rule, no exceptions:

- Instrument, session window, entry timeframe(s)
- Trigger condition — exact, candle-close-confirmed
- Entry price and order type
- Stop placement rule
- Target rule
- Invalidation / cancel rule
- What happens on overlapping signals

For every item in the discretion inventory, pick a default **and record that we
invented it.** Those are the variables Stage 5 gets to tune — and *only* those,
plus the ones listed in the refinement ledger.

Check `context/data-inventory.md` now: if the spec needs CVD or 2023/24 book
data, say so here and pick the fallback explicitly. Don't discover it at Stage 7.

Output: `03-mechanical-spec.md`.

---

## Stage 4 — Substrate

Run the raw spec over the **in-sample window: 2025-07-01 → 2026-06-30**. No
filters, no refinements, take every trigger.

This is the "raw substrate" step — the same thing we did before. It is supposed
to look mediocre. A raw trigger set that is already highly profitable usually
means the spec has a lookahead bug; check that before celebrating.

Record, per trigger: timestamp, direction, entry, stop, target, R outcome, MAE,
MFE, plus the context tags that Stage 5 will slice on — session, time bucket,
HTF trend flag, ATR regime, day of week, news proximity, and the order-flow tags
where data exists (book imbalance at entry, resting size within N ticks, CVD
slope if/when we have it).

**Hard floor: fewer than 60 triggers → stop.** You cannot learn a filter from
40 trades; you can only memorise them. Either widen the spec (and note that you
did) or reject.

Output: `04-substrate/` with the trigger table and a one-page baseline summary —
expectancy, win rate, profit factor, max drawdown, all in R, all net of assumed
costs.

---

## Stage 5 — Refinement

The DeCanon step: **cut the losers while keeping the winners.**

Made numeric, because "it looks better" is how backtests lie:

> **Filter efficiency** = (share of gross *losses* the filter removes) ÷
> (share of gross *wins* the filter removes).
>
> A filter is only adopted if efficiency ≥ **2.0** — it must cut at least twice
> as much bad as good — **and** it leaves ≥ 40 trades standing.

A filter that removes 60% of losses and 30% of wins scores 2.0: adopt. One that
removes 50% of losses and 40% of wins scores 1.25: reject, it's noise-fitting.

### The refinement ledger

Every variable tested goes in `04-refinement-ledger.md` — **including the ones
that didn't work.** This is not bookkeeping ceremony. The number of things you
tried determines how impressed you're allowed to be by the thing that worked.

Test 40 filters on random data and roughly two will look "significant" at the
usual thresholds. If we don't count our attempts, we can't tell our best filter
from those two. So:

| Filters tested | What the winner has to clear |
|---|---|
| ≤ 5 | expectancy > 0.15R |
| 6 – 15 | expectancy > 0.20R |
| 16 – 40 | expectancy > 0.30R |
| > 40 | stop. Go back to Stage 2 — this is a search, not a test. |

### Rules of the stage

1. **One axis at a time.** Test entry variants with management fixed, then
   management with entry fixed. No grid searches — a grid over five parameters
   is 3,000 experiments and will always produce a winner.
2. **Cap the filter stack at 3.** A strategy needing five conditions to be
   profitable is five conditions of curve-fitting.
3. **Plateau, not spike.** After picking a threshold, check the neighbours. If
   "at least 3 confluences" works and "2" and "4" both lose money, the 3 is
   noise. Real edges are broad — that's the single most useful robustness check
   there is, and it's free.
4. **Split-half check before OOS.** Does the refined rule work in 2025-H2 *and*
   2026-H1 separately? If it only works in one half, it's a regime artifact.
   Find this out now, while it's still cheap.

---

## Stage 6 — Freeze

Commit the final spec with a version stamp. From this line onward, **any change
means the out-of-sample test restarts on a different, unused window.**

The freeze is what makes Stage 7 meaningful. Without it, "out-of-sample" just
means "the data I haven't overfit to yet".

---

## Stage 7 — Out-of-sample

Run the frozen rules on data that has never informed a single decision:

- **Primary OOS:** three months of 2023 + three months of 2024, picked *before*
  looking at them (see `validation-gate-v1.md` for the selection rule).
- **Flow-based rules:** if the strategy uses heatmap or CVD filters, 2023/24
  can't test them — we don't have book data that far back. Use the fallback in
  `data-inventory.md` §4 and **state which one** in the verdict.

**You get one run.** Not "one run, then a tweak, then another run" — that is
just Stage 5 with extra steps and it destroys the only clean evidence we have.
If the OOS fails, the strategy fails. Going back to refine is allowed, but the
next OOS must use a *different* untouched window, and the verdict records that
this was attempt #2.

Track the OOS budget in `04-refinement-ledger.md`. Three attempts and the
strategy is dead regardless of what the third run says.

---

## Stage 8 — Verdict

Score against `context/validation-gate-v1.md`. Every criterion gets PASS/FAIL
with the number that produced it. No "borderline".

Plus the two book-level checks that a single strategy's own numbers can't show:

- **Correlation.** Daily R-series vs every strategy already in the book. Two
  strategies that lose on the same days are one strategy with two names — they
  double the drawdown without doubling the edge.
- **Capacity conflict.** Does it fire in the same session, same window, as
  something we already trade? One-position-at-a-time means the book has to
  choose, and a strategy that only ever fires when a better one is already
  running adds nothing.

Output: `05-verdict.md`, ending in one of exactly three words: **ADOPT**,
**REJECT**, or **PARK** (mechanism is sound, data or sample is insufficient —
revisit when the missing data arrives).

---

## Stage 9 — Promotion

An ADOPT verdict earns an entry in `strategies/BOOK.md`:

- Name, one-line mechanism, session, instrument
- Trigger summary in plain English
- **When to prefer it** — the regime tags where it scored best
- **When to stand down** — the regimes where it lost
- Mechanical baseline: expectancy, PF, max DD, trade frequency

That last line is load-bearing. When the agents get discretion over which
strategy to take, the mechanical baseline is the benchmark they have to beat.
Agent discretion is itself an unvalidated layer — the only way to know it helps
is to keep the number it's supposed to improve on. That's exactly how we
established that agent grading beat the mechanical baseline last time, and it
only worked because the baseline was written down first.

---

## What this protocol deliberately refuses to do

- **It won't optimise into a corner.** The filter cap, the efficiency ratio and
  the plateau check exist to keep strategies broad. A strategy that survives
  this process will look *worse* in-sample than one that didn't — and will
  still be making money in six months.
- **It won't let the OOS window get reused quietly.** The attempt counter is in
  the ledger, in git, with the strategy.
- **It won't accept a strategy nobody can explain.** Stage 2 is a real gate.
  Angus has to be able to say what the trade *is*. If the only justification is
  "the numbers were good", we've built a machine for finding coincidences.
