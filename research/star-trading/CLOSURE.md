# StarTrading research branch — CLOSED

**Closed 2026-08-07. Verdict: the model this branch was opened to evaluate is DEAD on
position sizing. Nothing here needs re-deriving.**

---

## What was asked

Mine a YouTube trading channel (@StarTrading-n8t, 117 videos, ~45 hours) that teaches
"negative risk-to-reward" — targets smaller than the stop, carried by a claimed 90–95% win
rate — and determine whether there is a real, mechanisable edge worth porting to our NQ
system.

## What was done

1. Pulled captions against an IP-level bot check, 7 of 20 priority videos recovered
2. Extracted 7 videos into structured records under a fixed schema
3. Ran a model census across the records
4. Ran a cheap-kill feasibility test on the best-documented model, over 772 NQ sessions

## What was found

**The channel does not teach one strategy. It teaches at least three**, sharing a vocabulary
and a channel identity. The session anchor partitions them with no overlap: 00:00 UTC
(cluster α), a broad undefined window (β), and 08:30 on futures (γ). The author confirms the
split himself in one livestream — *"These are two separate models... barely anything to do
with the previous one."* Cluster γ is the only positive-RR model on a channel whose entire
public identity is negative RR.

**Cluster α — the best-documented model — is DEAD on position sizing.**

RR 0.2 against a level-based target forces `stop = 5 × (entry-to-target distance)`. The
median distance from the 00:00 UTC open to the previous day's high or low, over 772 NQ
sessions, is 85 points. So the median stop is **424 points**.

| contract | median loss | p95 loss |
|---|---|---|
| NQ | $8,475 | $40,020 |
| MNQ (smallest listed) | $848 | $4,002 |

Against a $2,000 trailing drawdown, at the minimum size of the smallest contract: the median
loss is **42% of the entire allowance**, the p95 loss is **200%** of it, and the account
busts in **2.4 median losses**. There is no smaller contract, so there is no size that fits.

This is arithmetic, not a parameter choice. **No exit rule, bias rule, or win rate — not even
100% — changes it**, because the disqualifier is the size of one loss, not the frequency of
losses.

**Scope, stated precisely.** What died is *α on NQ inside a trailing-drawdown account*. What
did **not** die is α as taught: it is a forex and gold model, those markets have fractional
lot sizing, so position scales continuously with the stop and the quantisation that kills it
on futures never arises. **We did not test it there and claim nothing about it there.**
Reading this as "negative RR doesn't work" is a conclusion this study cannot support.

## What it cost

Roughly one working session. Two days of compute would have been wasted had the sizing check
been left until after a full backtest — it was a five-line calculation available on day one.

**The cheapest thing in the whole study killed it.** Worth remembering when scoping the next
one.

## What is reusable

Kept deliberately. All of it survives the branch closing.

**Testing runbook** — [`star-testing-runbook.md`](star-testing-runbook.md). The staged
process, with a PRE-FLIGHT stage of six gates that need no data work: sizing, session
overlap, breakeven, specifiability, data feasibility, sample sufficiency. Every one of them
was answerable on day one of this branch, and at least three would have flagged it. Run
them before acquiring anything.

**Caption pull pipeline that works against a bot check** — `tools/pull_captions.py`.
Manifest-driven and resumable, per-run cap, sleep with jitter, exponential backoff, hard stop
after 3 consecutive failures, atomic manifest write after every video so a kill loses at most
one. Diagnosed the block as IP reputation rather than velocity (a cold isolated request
failed identically to the hundredth) and still recovered 7 videos by exploiting the ~1-in-8
intermittency. Add `--cookies-from-browser` from a home connection to finish any channel.

**Extraction schema** — one record per video: rules with timestamps, concepts, claimed
numbers, contradictions, discretion markers. The decisive field was **`costs_included`**,
which returned **NO** on record 1 (*"we're not going to be including spread and
commissions"*) and **UNKNOWN** on all six others; commission is never mentioned in any of the
seven videos. That single field set the weight every claimed number could carry, and it is
why the cost gate came first in the test. Put it first again next time.

**Model-census method** — tabulate a small set of hard fields (instrument, anchor, filter, RR
sign, management) across every record before synthesising anything. It caught three distinct
models hiding under one identity, which no amount of reading would have surfaced, and it
prevented merging contradictory rules into one incoherent strategy.

**Cheap-kill test structure** — run in this order. The numbering *is* the instruction; a note
saying "do step 6 first" is the kind that gets skipped under pressure, which is exactly when
it matters. Sizing was step 6 in the first draft of this document, and sizing is what killed
the branch.

1. **Sizing.** Does one loss fit in the account? For a fixed reward:risk against a
   level-based target, `stop = (1/R) x target distance` — forced, not chosen. Convert to
   dollars at the smallest available contract and compare to the drawdown allowance. Needs no
   entry rule, no exit rule, no win rate, no backtest. **This ends more studies than
   everything below it combined.**
2. **Cost gate.** Compute breakeven from the geometry before any backtest:
   `p0 = (s + c) / (s x (R + 1))`, at three cost levels, costed for the session actually
   traded. Ends the study for the price of a distribution. Beware the inverse trap — α passed
   this because its stops were so large that costs rounded to nothing against them, which is
   the same property that killed it at step 1.
3. **Unconditional both-directions base rate.** When the discretionary core is not codable,
   delete it and measure the base rate instead of guessing it.
4. **Stop-first resolution, always.** At low RR the target sits inside far more bars than the
   stop; target-first accounting inflates win rate systematically. Non-negotiable.
5. **Required lift.** State the gap between base rate and breakeven in win-rate points. Above
   ~10 points from a rule the author cannot put into words, that is a verdict, not a
   research question.
6. **Hindsight ceiling.** Win rate with perfect direction choice. Below breakeven, no bias
   rule of any kind can rescue the model.

Steps 1–2 need no data acquisition at all and belong in PRE-FLIGHT — see
[`star-testing-runbook.md`](star-testing-runbook.md), which puts them alongside four other
gates answerable before any corpus is built.

**Two structural findings** worth carrying to any similar candidate — full statements in
[`ledger/README.md`](ledger/README.md):

- *A signal that fires every session performs no selection.* The 00:00 open sat inside the
  prior day's range in **all 1,544 legs**, so the undocumented bias rule was doing 100% of
  the work.
- *When a result depends on a parameter the source never states, the finding is that the
  strategy is underspecified.* α has no exit for the ~32% of trades that do not resolve
  same-session, and their treatment swings expectancy from **+0.076R to −0.337R** — wider
  than the whole margin over breakeven, and straddling zero.

## Where everything lives

| Path | What |
|---|---|
| [`CLOSURE.md`](CLOSURE.md) | This file |
| [`star-testing-runbook.md`](star-testing-runbook.md) | Staged process for the next candidate, incl. PRE-FLIGHT gates |
| [`ledger/README.md`](ledger/README.md) | Cluster verdicts, model census, structural findings |
| [`alpha-feasibility.md`](alpha-feasibility.md) | DEAD verdict, plus the retained inconclusive-on-win-rate evidence trail |
| [`negative-rr-model.md`](negative-rr-model.md) | First-pass reading of the model (early, superseded by the ledger) |
| [`channel-index.md`](channel-index.md) | All 117 videos with metadata |
| [`manifest.json`](manifest.json) | Pull state; #6 deprioritised with reason |
| `transcripts/*.txt` | 7 timestamped transcripts — **retained** |
| [`tools/`](tools/) | Puller, converter, manifest builder, feasibility scripts |

Nothing was deleted. A closed branch with its evidence intact is the deliverable.
