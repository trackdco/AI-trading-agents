# March 2026 replay — regime-agent scoreboard (arm A vs arm B)

**Question.** Does the regime-context agent layer improve on the static champion
(Blend v1.1) when replayed walk-forward over a real month?

**Answer for March 2026: no.** Agent v0.2: **−$5,365**. After the two Pat-directed
revisions (v0.3.0, below): **−$1,715** — better, still negative, and the retest
surfaced a new failure mode. All numbers reported straight (anti-tuning discipline).

---

## v0.3.0 retest (2026-07-18)

Two revisions were made to `.claude/agents/regime-context.md` (Pat-directed,
pending Angus ratification) and the full month re-run from scratch (fresh emits,
22 fresh zero-context verdicts, new agent hash `6cbfd786de69`):

1. **Structure-exclusion rule** — a regime label (e.g. war) no longer removes a
   structure by itself; exclusion now requires briefing evidence against THAT
   structure. This fixes the 03-19 class of error (war ⇒ continuation-only vetoing
   the champion's winning fade).
2. **Hard length caps in the prompt** — rationale ≤600 / notes ≤1500 stated as
   verdict-voiding, with a target under each.

**Validity caveat: this retest is in-sample.** The revisions were designed by
looking at March's failures, so March can no longer certify the agent. The result
below measures whether the fixes *behave as intended*; certification needs a month
the v0.3 agent has never influenced (e.g. April–July).

### v0.3 result — 22/22 days ruled, 0 schema failures

| metric | v0.2 | v0.3 |
|---|--:|--:|
| arm A — static champion | +$4,276 (18d) | **+$3,356 (22d — full March, matches frozen baseline)** |
| arm B — champion + regime agent | −$1,089 | **+$1,641** |
| agents' effect | **−$5,365** | **−$1,715** |
| schema-failed verdicts | 3 of 21 | **0 of 22** |

Both fixes did what they were built to do:
- **No structure vetoes fired.** 03-19 went from −$132 (fade blocked, losers kept)
  to +$895 — exactly the half-sized champion trade. The wiring bug is gone.
- **No verdicts died on length.** 03-06 (NFP quintuple cluster) now stands down
  validly and saves its −$75.

### The new finding: the agent has collapsed into "always half-size"

Every one of the 22 days got `size_multiplier: 0.5` (or the one stand-down).
Arm B ≈ arm A × 0.5 almost line-for-line (+$1,641 ≈ half of +$3,356). The verdicts
justify it the same way each day: March's shock-bar counts and 300–1000pt ranges
read as "elevated volatility ⇒ 0.5x" every single morning. With the structure veto
removed, the agent's only remaining lever is size — and it never uses 1.0.

A de-risk layer that outputs a constant is not exercising judgment; it is a static
position-size cut, which needs no LLM. **For Angus:** the agent needs either
(a) calibration guidance for what "normal" volatility looks like (its briefing has
no baseline to compare shock counts against, so everything looks elevated), or
(b) an explicit instruction that 1.0 is the default and 0.5 must cite a
day-specific trigger, not the month's ambient volatility. Not tuned here.

### Bottom line after v0.3

On a green month the honest expectation for a pure de-risk layer is now
≈ −(half the month's profit), and that is exactly what we got. The two real
questions remaining are (1) does it save more than it costs in a **drawdown month**
(the fair test, still unrun), and (2) can it learn to size 1.0 on clean days
(the new finding above). 

---

## Multi-month replay (2026-07-18, second session): April + May out-of-sample

The v0.3 revisions were designed on March, so March can't certify them. April and
May were then replayed **fully out-of-sample** (fresh emits, fresh zero-context
verdicts, playbook notes chained walk-forward month to month).

First, the champion's own monthly record (full-history run — note this scores
March +$2,710 vs the sliced harness's +$3,356; the engine's history-dependent
vetoes shift with warm-up, but arm A vs arm B always share one harness so the
agent deltas are unaffected):

| month | champion | character |
|---|--:|---|
| Feb | +$4,455 | green |
| Mar | +$2,710 | green (in-sample retest month) |
| Apr | +$2,635 | green (OOS test 1) |
| May | **+$50** | flat/chop (OOS test 2 — the stress test) |
| Jun | +$3,535 | green |
| Jul (9d) | −$650 | partial, only red stretch |

### April (OOS, green month): agent effect −$1,776 on ruled days

Arm A +$3,645 / arm B +$1,869 over 17 ruled days. Two findings:
- **New contract bug:** the agent sized 0.75 on five war-long days
  (04-15/16/20/22/29) — the schema only accepts {0.0, 0.5, 1.0} and the prompt
  never said so; all five died fail-closed (traded as champion). Fixed as v0.3.1
  (prompt now states the allowed values — contract alignment, not tuning).
- The always-half-size collapse is **not absolute**: 04-10 got a full-size 1.0
  call (delta $0) and the 0.75 attempts show graded judgment the contract
  couldn't accept.

### May (OOS, flat month): agent effect **+$840** — first agent win

Arm A **+$50** / arm B **+$890** over 21 ruled days, v0.3.1 (all 21 valid, plus
a correct stand-down on the 05-25 Bank Holiday). The discrimination thesis
held: full-size 1.0 on the clean war-long days — **including 05-11, the month's
biggest winner (+$1,935), left completely untouched** — and half-size across the
chop, which cut eight losing days roughly in half. The one blemish: 05-06 was
sized 1.0 and lost −$580 in full; sizing is judgment, not clairvoyance.

### The cross-month picture

| month | champion (ruled days) | agent effect | agent version | sample |
|---|--:|--:|---|---|
| Mar | +$3,356 | −$1,715 | v0.3.0 | in-sample (revisions designed on it) |
| Apr | +$3,645 | −$1,776 | v0.3.0 | out-of-sample |
| May | +$50 | **+$840** | v0.3.1 | out-of-sample |

The layer now behaves like what it is — insurance: it costs roughly half the
profit in months the champion wins anyway, and pays out in flat/choppy months.
Whether it's worth carrying depends on (a) cutting the green-month premium —
the agent still defaults to 0.5 on most days; with 0.75 now legal, that should
improve — and (b) June + the partial July as further out-of-sample evidence.
All still regime-agent-only; HTF layer unrun; no news (arm C).

---

## v0.4 June (analog block + fresh-eyes panel) — first grade, 2026-07-18

Re-ran the full June chain under agent v0.4.0 (analog block in the briefing), same
May-29 seed as the v0.3 June run — apples-to-apples on one month. Reads first (D1).
All grading uses Angus's $0-best-book = FLAT rule.

| metric | v0.3 chained | **v0.4 chained** | v0.4 fresh-eyes |
|---|--:|--:|--:|
| reads (3-way) | 38% (8/21) | **38% (8/21)** | 45% (9/20) |
| dollar capture | $802 = 7% | **$2,472 = 22%** | $2,359 = 21% |
| regret vs ceiling | — | −$8,789 | −$8,691 |

**Three honest findings:**

1. **The analog block tripled dollar-capture (7% → 22%) but did NOT move 3-way read
   accuracy (38%, unchanged).** Same hit *count*, 3× the captured dollars — the
   agent's read-implied book choices landed on higher-value days and cut negative
   wrong-book bets. Real improvement in call *quality*, none in label accuracy.
2. **It did NOT fix the marquee miss (06-08).** The analogs for that day voted
   8 FLAT / 6 ROTATION / 1 MOMENTUM, so v0.4 followed the plurality to FLAT and stood
   down — but the oracle was ROTATION (+$3,131). The plurality vote was itself wrong,
   and FLAT captured $0 vs v0.3's momentum call (+$475). Following the analog majority
   hurt here. The aggregate capture gain came from *other* days, not this one.
3. **Fresh-eyes edged the incumbent on reads (45% vs 38%), and on the 5 days they
   diverged the fresh mind was right more often (2) than the chained mind (1), with 2
   both-wrong.** On a 21-day sample this is directional, not conclusive — but it is the
   first *measured* sign that inherited memory is a net drag on reads, exactly the
   frame lock-in June flagged. The chained agent stood FLAT on 06-24 and 06-26 where
   the no-memory twin correctly took ROTATION — memory carrying a stale defensive frame.

### What this means for the campaign

- Keep the analog block: 3× capture is worth having, and it's inside the contract.
- The 60%+ read target is NOT reached by the analog block alone (reads flat at 38%) —
  so per docs/FOR-ANGUS-c1c2-contract-question.md, "option 3 (analog alone closes it)"
  is falsified. But the fresh-eyes result points somewhere other than C1/C2: the drag
  may be *memory itself*, not missing feedback. The cleaner next experiment is likely
  **reducing/quarantining memory** (fresh-eyes-led reads + analog retrieval, notes used
  only for continuity not framing) rather than adding a self-referential loop. Flagged
  for Angus alongside the C1/C2 question.
- Full fresh-vs-chained ledger: output/v04/jun_divergence.csv, jun_ledger.csv.

---

## Oracle benchmark (Pat directive, 2026-07-18): all scoreboards now graded vs oracle + stand-down

The objective metric is Angus's oracle + stand-down ceiling (scripts/
score_regime_reads.py): per day, perfectly pick the better book at full size, or
stand down when both books lose — `oracle_pl = max(E3, E4, 0)`. Full-dataset
ceiling $37,014 vs champion $14,022 (Gates ledger). The campaign goal is to
close the agent→oracle gap month over month; champion-relative deltas are
secondary color.

| month | oracle+SD ceiling | agent read-capture | read accuracy | arm B actual |
|---|--:|--:|--:|--:|
| Mar (v0.3.0, in-sample) | +$11,485 | +$1,980 = **17%** | 43% (9/21) | +$1,641 |
| Apr (v0.3.0, OOS) | +$6,090 | +$1,535 = **25%** | 44% (7/16) | +$1,869 |
| May (v0.3.1, OOS) | +$6,552 | +$1,778 = **27%** | 35% (7/20) | +$890 |

(Read-capture = full-size follow-the-reads P&L ÷ oracle P&L — Angus's primary
metric. Arm B actual is the half-size-damped engine result; different lens.)

Capture is trending the right way (17% → 25% → 27%) but read ACCURACY is not
(43% → 44% → 35%): May's better capture came from sizing luck, not better
regime reads. The May confusion matrix shows the v0.3 revision traded one miss
class for another — event_risk over-call persists (FLAT on tradeable days:
05-12/13/19), and a NEW class appeared: **war-called chop** (six May days read
MOMENTUM where the oracle wanted FLAT — the structure-exclusion fix stopped
banning structures but the agent now over-trusts trend labels in chop).
Both are v0.4 material (docs/PROPOSED-AGENT-ADJUSTMENTS-v0.4.md): B2/B3
(event expiry + taxonomy split) target the first; the analog block (A1) and
health-conditioned default (B4) target the second.

Standing rule going forward: every month replayed gets its reads scored vs the
oracle BEFORE its P&L is discussed, per the v0.4 process guard (D1).

---

## June 2026 — first SEQUENTIAL month (driver-chained, v0.3.1, OOS)

June ran through scripts/run_sequential_replay.py: 22/22 verdicts valid, each
day's briefing carrying the prior day's playbook notes. Reads first (D1):

**Reads: 5/21 = 24% — the worst month yet, below 3-way random (33%).**
Capture $802 / $11,261 = **7%**. Arm B P&L: arm A +$3,535 → arm B +$1,815,
effect −$1,720 (the familiar ~half-profit premium on a green month).
Binary trade/no-trade (new E4 metric): 62% — TRADE precision 85%, but FLAT
precision only 25%; over-FLAT cost $1,216 (6 days), under-FLAT $992 (2 days).

Two findings, both v0.4 evidence:

1. **The dominant June miss is MOMENTUM-called-ROTATION (6 days,** incl. 06-08
   where the rotation book made +$3,131). The agent's war/short reads were
   often directionally right about the tape — but the champion's rotation
   book was what actually paid. This is the day-vs-regime mismatch (E5) at
   full strength: regime label ≠ which book profits today. Because v0.3
   permits both structures, the gate only half-sized these days rather than
   banning the winner — the READS metric is rightly harsher than the P&L.
2. **Chaining improved discipline, not reads.** The sequential agent executed
   inherited plans, built standing rules (never 1.0 on red-folder mornings /
   at range_pctl≥0.85; holidays = 0.0), stood down the 06-19 Bank Holiday,
   and audited the L1 vector daily. But read accuracy FELL — and the notes
   chain shows why: the war framing adopted early in June propagated day to
   day through a rotation-rich stretch. **Memory can entrench a wrong frame**
   (frame lock-in) — a genuine risk register item for v0.4's C1/C2: feedback
   must be able to BREAK a frame, not just carry it.

### Cross-month ledger (regime-only, no HTF, no news)

| month | reads | capture | arm B effect | sample |
|---|--:|--:|--:|---|
| Mar | 43% | 17% | −$1,715 | in-sample, parallel |
| Apr | 44% | 25% | −$1,776 | OOS, parallel |
| May | 35% | 27% | +$840 | OOS, parallel |
| Jun | **24%** | **7%** | −$1,720 | OOS, **sequential** |

The blunt conclusion for the v0.4 pass: the v0.3.x prompt sizes more sanely
than v0.2 but does NOT read regimes better — accuracy is drifting DOWN while
the sizing discipline carries the P&L. The read problem is exactly where
Angus's A1 analog block aims, and June is the strongest evidence yet that
inference-from-one-morning (plus chained priors) cannot hit the 60%+ target —
retrieval over the 850-day library is the missing input.

---

## v0.2 run (original) — detail below

## The number

Regime-only run (HTF agent not yet run; its layer left permissive). One 08:00-ET
cutoff, no-hindsight. 18 agent-ruled March days (the 3 fail-closed days are absent by
construction — see below):

| metric | dollars |
|---|---|
| arm A — static champion (Blend v1.1) | **+$4,276** |
| arm B — champion + regime agent | **−$1,089** |
| **regime agent's effect** | **−$5,365** |

Reproduce:
```
python -m scripts.run_regime_replay ingest
python -m scripts.build_regime_gate_schedule --start 2026-03-01 --end 2026-03-31
python -m scripts.score_replay_arms --start 2026-03-01 --end 2026-03-31
```

Per-day (book = E3 balance / E4 war, picked by the frozen pre-open imbal switch):

| day | book | arm A $ | arm B $ | Δ$ | what the agent did |
|---|---|--:|--:|--:|---|
| 03-02 | E3 | +1564 | 0 | **−1564** | trap → reversion-only blocked the continuation winner |
| 03-04 | E3 | −595 | −302 | +292 | half-size cut a loss |
| 03-05 | E3 | −285 | −128 | +158 | half-size cut a loss |
| 03-09 | E4 | −465 | −235 | +230 | half-size cut a loss |
| 03-10 | E4 | +742 | 0 | **−742** | CPI stand-down skipped a winner |
| 03-11 | E4 | +575 | 0 | **−575** | event stand-down skipped a winner |
| 03-12 | E4 | −805 | −202 | +602 | half-size cut a loss |
| 03-13 | E4 | −805 | −222 | +582 | half-size cut a loss |
| 03-17 | E4 | +3485 | +450 | **−3035** | reversion-only + half-size gutted the month's biggest winner |
| 03-18 | E4 | −600 | 0 | +600 | stand-down avoided a loss |
| 03-19 | E4 | +1800 | −132 | **−1932** | war→continuation-only **vetoed the +$2,060 fade, kept the losers** |
| 03-20 | E4 | +1310 | 0 | **−1310** | stand-down / block skipped a winner |
| 03-23 | E4 | 0 | 0 | 0 | shock stand-down (champion already flat) |
| 03-25 | E4 | −780 | 0 | +780 | stand-down avoided a loss |
| 03-26 | E4 | −700 | −168 | +532 | half-size cut a loss |
| 03-27 | E4 | 0 | 0 | 0 | — |
| 03-30 | E4 | 0 | 0 | 0 | — |
| 03-31 | E4 | −165 | −150 | +15 | half-size |

## Why it hurt — two distinct failure modes

**1. It was insurance in a green month.** The agent's half-sizing and stand-downs
*did* work as designed on losing days (03-04/05/09/12/13/18/25/26 all improved:
+$3,776 saved). But March was a **green** month for the champion, and the agent
clipped the winners far harder than it saved on losers. On a defensive tool, a green
month is the worst case: you pay the premium (clipped upside) and collect little
payout (few losses to avoid). The single biggest line, 03-17 (+$3,485 → +$450), is
half-size × reversion-only applied to the month's best day.

**2. Structure mismatch — the more serious one.** On war days the agent says
"ride continuation, block reversion." But the champion's E4 (war-book) edge is
*frequently a counter-trend fade* (pattern A = reversion). 03-19 is the clean proof:
the champion's entire +$2,060 came from a pattern-A fade at 09:49; the agent called
the day war/short and permitted **continuation only**, so it vetoed that fade and kept
the pattern-B2 continuation trades — which lost. The regime read was directionally
reasonable and still destroyed the day, because "war ⇒ continuation-only" contradicts
how the champion actually makes money in a war regime.

This second mode is not fixable by loosening size. It's a wiring question:
either the `_trigger_class` mapping (pattern A→reversion) is too coarse, or the
regime→permitted-structure logic ("war ⇒ continuation-only") is wrong for this
book. **Flagged for Angus**, not tuned here.

## Caveats on the number (all push arm B the same direction — down)

- **Regime-only.** The HTF agent was not run; its layer is permissive. Adding it can
  only *remove* more trades, so the combined gate would be ≤ this, not better.
- **3 days fail-closed.** 03-06, 03-16, 03-24 produced valid *judgments* but their
  rationale ran 627–665 chars over the 600-char schema cap, so the parser rejected
  them (fail-closed → those days trade as champion, unprotected). All three were
  de-risk calls (one stand-down, two half-size), so honoring them would have pushed
  arm B *further down*, not up. **This is a prompt/schema finding:** the agent needs a
  hard brevity instruction, or the cap needs raising — I did **not** hand-trim the
  rationales to force them through (that would be tampering with agent output).
- **No news (arm C).** Verdicts were built from price + ex-ante calendar only. The
  news archive (Brake's lane) could change some event-risk calls.

## What this does and doesn't tell us

It does **not** say the agent layer is worthless. It says: *tested on a month the
champion already won, a defensive de-risk agent loses, and the current war⇒continuation
rule actively fights the champion's fade edge.* The fair test of a defensive layer is a
**drawdown month** — where the stand-downs and half-sizes it applied to 03-04/12/13/25/26
would be the whole month, not the exception. The regime read (mode 2) must be fixed
regardless of month. Both are inputs for the next agent-design pass, not tuning targets.
