# WEEK SUMMARY — the narrated week replayed, 2026-08-12
tv-thesis 0.3.0→**0.3.2** / tv-trigger 0.3.1→**0.3.3**, sonnet. Orchestrator: Opus 5.
Every day's leak audit **exit 0**. Logs in `output/agent_runs/<sess_day>.jsonl`.

## Result

| session-day | his day | fills | **R** | agreement | character called |
|---|---|---|---|---|---|
| 2026-06-21 | Mon 22 | 3 | **+2.99** | 3/4 (75%) | — |
| 2026-06-22 (re-run) | Tue 23 | 1 (+1 no-fill) | **+2.16** | 1/3 (33%) | TREND |
| 2026-06-23 | Wed 24 | 3 | **−2.00** | 2/2 (100%)* | ROTATIONAL |
| 2026-06-24 | Thu 25 | 0 | **0.00** | see below | ROTATIONAL → self-corrected to TREND |
| 2026-06-25 | Fri 26 | 3 | **+2.45** | 0/3 (0%) | ROTATIONAL, re-judged every window |
| **total (5 days)** | | **10 fills** | **+5.60R** | | |

\* the 100% is not trustworthy — see the scorer defect below.

**Day 5 now ran in full**, but read its R with the contamination warning below firmly in mind.
Its 0.2.0 predecessor is archived at `superseded/2026-06-25_v0.2.0_pre-rulings.jsonl` and
predates every ruling below. Both are drawn on the chart — **grey boxes are 0.2.0, blue are 0.3.x**.

> ### ⚠ The most important finding of the week came from day 5, and it is not about R
>
> On the partial run the thesis agent opened its reasoning with: *"this is the contract's own
> worked example for this exact session."* **It was right.** `tv-thesis` 0.3.2, in its FIB LAYER section,
> contains a worked example naming this exact session-day: *"his 2026-06-25 London: day high
> 29,892.75, low 29,160.5 → 0.5 at 29,526.6, with the VWAP mid at 29,490.8 and price stalling
> across that band. Fib + VWAP + stalling = the short."* The agent recognised the day from its
> own prompt and reproduced the answer.
>
> On the full re-run it did **not** quote the example, and its reasoning at each window tracks the
> briefing facts. But the example is still in the prompt and this day's own high and low are still
> printed inside it. **Day 5's +2.45R is not evidence of anything out-of-sample** and must not be
> pooled with days 1–4 as though it were.
>
> This is **not** a replay leak — the briefings are clean and the audit passes, because nothing
> post-decision reached them. It is **prompt contamination**, and it is the sharpest possible
> instance of what T8 recorded abstractly. `tv-trigger` carries the same problem: its worked
> examples name the 29,369 POC limit, the Mon N1 market entry, and the −1.0R long.
>
> **Consequence:** day 5 is not a valid test of the thesis agent, and the other four days are
> softened by the same mechanism to a lesser degree. **Before any scored run that means
> anything, the worked examples must be restated abstractly or the named days excluded** — and
> the real proof still requires post-corpus days (bars run to 2026-07-15).

## Your rulings, and what each one did

| # | ruling | effect observed |
|---|---|---|
| **T11** | first target must sit in **1.5–2.5R** | Day 1's London trade: the identical setup that lost 1R under 0.3.0 (targets 2.7R/3.5R, neither reached) took prior-day VAH at **1.80R and paid**. Every subsequent take complied. |
| **T13** | pre-market carry: break-even if green, **flatten if red**, by 09:30 | Day 1's NY_PRE long logged **−0.44R** instead of the −1R its stop would have taken three minutes later. |
| **T14** | break-even is earned by **breaking** the band, not touching it | Day 3's NY_PRE long: the daily VAH was broken by 14.75pt, earning BE; the trade exited **flat where the raw stop was −1R**. |
| **T15** | trend-day exemption; the 15m MA is **one key level, not a gate** | Day 2 re-run: same session, same tape — **0 fills / 0.00R** under the old rule became **+2.16R** on the trade you named. Day 4: the thesis overturned its own character call mid-session and applied it unprompted. |
| **T16** | cash-open bar is ~5 min, not 15 | Removed the clock objection from your 09:38 long, leaving a purely directional pass. On day 5 it made 09:36 the session's first structural decision. |

**T11 also cost money on day 5, and the mechanism is worth your attention.** The 09:46 short had a
120pt stop. Every level in its path — weekly VAL, daily VAL, the 2m band, the session low, and the
weekly low itself — sat inside 0.8R, so the 1.5–2.5R band was **empty** and the fixed-1.5R fallback
set a target 180pt away with the weekly low square in the way at 0.80R. It stopped for −1R. This is
**disagreement 3 below, recurring**: a wide stop empties the band, and the fallback then licenses a
trade whose own structure argues against it.

**T12 (retest degeneracy) remains open** and now has evidence from both sides in one week:
day 1's limit sat **0.5pt** from the close — effectively a market order; day 2's sat **13pt**
away and expired unfilled on a conviction-A setup. Any minimum you set needs a maximum twin.

## Disagreements worth a ruling

1. **Reversal-bar threshold for forcing a Tier-1 re-read.** Day 2: your 09:38 long was passed on
   direction and the trigger did **not** escalate `thesis_stale` despite an 84pt bar closing at its
   high through three levels. On day 4 it *did* escalate on a 615pt collapse. Where is the line?
2. **Does a shallow bounce count as a rejection on a trend day?** Day 2 London: your L1 short was
   passed because the trend-day thesis named rejection levels 80pt above where the bounce stopped.
3. **T11 vs the origin-proximity stop — a genuine collision.** Day 3, twice. A 171.7pt
   origin-proximity stop made *every* overhead level fall under 1.5R, so the empty-band fallback set
   a fixed 1.5R target **258pt away, above all structure**, on a session the thesis called rotational.
   Is the fixed target right, or is a too-wide stop the signal to pass or re-cut?
4. **Does the news blackout end at the print, or a few minutes after?** Day 4's 08:30 candidate closed
   through **five levels in one candle** — and it was the PCE release bar itself.
5. **A thesis that gates BOTH sides can veto its own reversal.** Day 5, 09:36 — the clearest
   single decision of the week. The 09:30 thesis flipped long, then wrote *"No entries until one
   resolves"* into `waiting_for`, keyed to a cluster 50pt overhead. Six minutes later the session
   printed its reversal bar: a 119.5pt bull body off 29,181.5, closing through three levels on
   5,941 contracts — the heaviest bar of the session — landing exactly in the 29,160.5–29,290 zone
   the **08:00** thesis had already licensed longs at. The trigger passed it, correctly, on the
   thesis's own embargo. **You took that bar.** Should a `waiting_for` gate apply to a location the
   standing view has already licensed, or only to entries outside it?
6. **The retest gate on a one-way collapse.** Day 4 NY_AM: the re-fired short wanted a relief-rally
   retest that never came because price simply kept falling. T15 fixed this shape for the *entry*
   side; the *retest* side has the same hole.

## Defects found and fixed during the run

- **A leak I caused** (day 1): a bug in my scan helper measured MFE over a 6-hour window instead of
  the trade's life, producing a phantom 30,968 high that I copied into two briefings as `session_high`.
  The 09:30 thesis reasoned from it. Whole NY_AM chain **voided and re-run**; voided rows preserved.
  Cost: the contaminated chain took a +2.92R trade the clean chain passes.
- **Trade drawings leaked the future** — position boxes extend right of the cursor with target/stop
  and closed-PnL. The trigger agent caught it and returned `leak_suspected`. Drawings are now
  end-of-day only.
- **The study reader was crosshair-dependent** — `dataWindowView` follows the crosshair, not the last
  bar, and returned a VWAP 166pt wrong after a re-land. Now reads the study's own series.
- **`two_level_check` ended NY_AM at 10:45**, not 11:00 — fixed.
- **Rejection-first shapes were undetectable** — the detector only pairs a rejection with a closure in
  the *same* candle. Your 10:36 Tuesday short was invisible to it. A supplementary scan built on your
  grammar now runs alongside, and it is the **only** reason day 2's winning trade exists.
- **The audit had a blind spot** — a future *price* inside a *briefing* was checked by neither check C
  nor E. Separately, check E false-positived on T11's fixed-R targets; it now **verifies the
  arithmetic**, which tightens rather than loosens it.
- **The parity gate failed on day 2** (VWAP 1.28pt vs 1.0 tolerance, BB MAs exact to 0.01). Diagnosed
  to volume differences between the research parquet and TradingView's feed. Resolved by **reading
  VWAP off your chart** at every decision minute — not by widening the gate.
- **The agreement scorer ignores direction** — it counted "his TAKE long" vs "agent take_full short"
  as AGREE at Δ10m. Flagged, deliberately **not** fixed mid-run so the days stay comparable.
  **Every agreement figure above should be read with this caveat.**

- **Two logging defects on day 5, both caught by the gates.** (a) Its trigger rows omitted the
  top-level `leak_check` field that days 1–4 carry, and **check A of the audit failed** — the check
  had been run at every decision and is recorded verbatim in each briefing, but the row-level field
  was missing. (b) Its trigger rows nested the verdict only under `output.decision`, and
  `score_replay_run` selects rows by a **top-level** `decision` key — so the first Friday score
  printed *"0 takes, all passes"* on a day that took three trades. Both were amended with the
  amendment itself logged as a row; no decision, price or outcome was touched. The second one is
  the more alarming of the two: **a silently wrong score is worse than a failed audit**, and only
  reading the report against the known fills caught it.
- **Archived position boxes were still on the chart when day 5 re-ran.** The four superseded 0.2.0
  Friday boxes and their caption ("*these 4 are the SUPERSEDED v0.2.0 run … −1.0R, +2.14R …*") were
  visible at the 08:00 and 08:36 lands. Not a price leak — they sit left of the cursor and the audit
  tests levels, not drawings — but it is precisely the hindsight you ruled out, since an agent could
  read a previous run's decisions off the chart. Removed before the 09:30 briefing and restored after
  11:00. **The runbook already said to remove them; I had not.**

## Honest reading

The R total is four days on the week the doctrine was distilled from — in-sample, and small. What the
week actually demonstrates is the loop: five rulings encoded and each visibly changing behaviour, two
detector defects and one real leak caught by the gates rather than by luck, and a thesis agent that
reversed its own day-character call when the tape contradicted it.

Day 5 sharpens both halves of that. Its two NY_AM trades are the **same level read twice** — short
its rejection at 09:46 for −1R, long its break at 09:58 for +1.91R, ten minutes apart — which is a
two-sided thesis working as designed, not an error. And its 09:36 pass is the week's cleanest
demonstration that the stack now fails in a **specific, nameable, fixable** way rather than a vague
one: not "it missed a trade", but "a `waiting_for` gate written by Tier 1 outranked a location Tier 1
had itself licensed ninety minutes earlier".
