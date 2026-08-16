# CALIBRATION — FRESHNESS, and what the two weeks actually say

**Worked overnight 2026-08-16→17 on his explicit authorisation:** *"do a full
diagnostic and figure out what you think would be best to calibrate agents
around that'll help them where they are leaking… remember the gap to bridge
is thinking like me… run our week period that i narrated over, and run it
over the out of fit week with adjustments made. see if it gets better."*

Both weeks of complete data:

| | span | status |
|---|---|---|
| **wk1** | 2026-06-21…25 | the NARRATED week — the doctrine was built on it, so in-sample twice over |
| **jn1** | 2026-05-31…06-04 | UNSEEN June week 1, frozen stack |

---

## 1. THE DIAGNOSIS — freshness sorts the book better than anything else

40 deduped graded takes across both weeks. Split them by whether the level
being rejected was **FRESH** — first trade at that level this session, and at
most 2 tests on the 15m in the trailing 60 minutes:

| | n | total | mean | WR |
|---|---|---|---|---|
| **FRESH** | 20 | **+18.81R** | **+0.94R** | 55% |
| STALE | 20 | +0.86R | +0.04R | 45% |

**Essentially the entire book is the first touch.**

It replicates independently on each week — this is not one week's artifact:

| | fresh | stale |
|---|---|---|
| jn1 (unseen) | +10.10R (n=11) | **−2.42R** (n=10) |
| wk1 (narrated) | +8.71R (n=9) | +3.28R (n=10) |

And it survives leave-one-day-out. Dropping any single one of the ten days
leaves the fresh/stale gap between **+0.62R and +1.32R** — it never collapses
onto one session, including the churning 06-02 that dominates the loss column.

**Decomposed, the VISIT count does the work; the test count is secondary:**

| | n | total | mean |
|---|---|---|---|
| first visit to the level | 25 | +20.62R | +0.82R |
| second or later visit | 15 | −0.95R | −0.06R |
| ≤2 tests on 15m | 29 | +17.54R | +0.60R |
| ≥3 tests on 15m | 11 | +2.14R | +0.19R |

### Where it bites hardest: the A-grade

| A-grades only | n | total | mean | WR |
|---|---|---|---|---|
| fresh A | 4 | **+8.87R** | +2.22R | 75% |
| stale A | 7 | **−1.78R** | −0.25R | 29% |

**A is his largest size ($250 vs $150 for a C).** The worst-performing
population in the book was carrying the most money per trade. That is the
leak, stated precisely.

### Why this is HIS reasoning, not a fitted parameter

This is the part that matters under the anchor. The rule was not searched
for — it was read off the agents' own words:

- The **best trade of either week** (+6.37R, graded A) justified itself:
  *"weekly-low/daily-VAL confluence (top tier) tested once at session low,
  **no repeated failures**, sharp reversal."*
- The **four worst A-grades** (2026-06-02, −3.28R between them) justified
  themselves: *"tested 3-4x since 03:15, no decisive close beyond"* — reading
  repetition as **strength**.

His own doctrine already says the opposite, in three places: conviction
rubric point 4 (*"a level price already sliced earlier in the session"*
grades lower), THE RANGE FRAME (*"the middle is dead"* — a level revisited
all session **is** the middle of a range), and his review of the narrated
Wednesday, where repeatedly fading one level was the thing he disliked most
("generational curse"). The agents had the principle and were applying it
backwards.

---

## 2. THE CHANGE — `tv-trigger` 0.4.8

**Only a FRESH level may grade A. A third or later visit caps at C.**

It caps the **grade**, never the **licence**. Every trade that was taken is
still taken; T48 same-level re-entry remains fully licensed. What it no
longer does is come at A size.

**Flagged in-contract for his ruling, not decided here:** T48 says of a
same-level re-entry *"if anything, I'm actually more confident."* The
measured second-visit mean is **−0.06R over 15 trades**. The licence is
preserved and only the size cut, but the tension is real and his to settle.
(Working-forward rule T66: surface the conflict, never re-litigate silently.)

Supporting mechanics, both mechanical facts under §0c, never judgements:
`scripts/level_visits.py` computes the visit and test counts; the runbook now
requires them in every trigger briefing.

---

## 3. DID IT GET BETTER? — the deterministic answer

Regrade every take under the cap, then price both grade-sets through the
**same** fixed policy on committed bars (partial at TP1 by grade, break-even
only after TP1 per his ruling, runner to the final target, touch model). The
difference isolates the regrade.

**In R: almost nothing (+0.41R across both weeks).** This is the honest and
initially disappointing result, and the reason is instructive: grade drives
the *partial split*, and the split only matters on trades that reach TP1 —
which stale trades mostly do not. Regrading a full stop-out changes nothing.

**In dollars at his stated sizing (A $250 / B $200 / C $150), it matters,
because grade drives risk per trade:**

| | logged grades | 0.4.8 grades | delta |
|---|---|---|---|
| jn1 (unseen) | +$134 | **+$349** | **+$214** |
| wk1 (narrated) | +$2,678 | +$2,588 | −$90 |
| **both weeks** | +$5,089* | +$4,955* | **+$124** |

\* totals include all priced takes, not only regraded ones.

**On the unseen week every one of the five regrades was a loser being
downsized** — the rule fired exactly where it was designed to. On the
narrated week two of five were small winners (+0.71R, +0.79R) that got
downsized, which is the cost of the rule and is real.

**Honest verdict: the change is directionally right, cheap, and small.** It
roughly triples the unseen week's dollar result off a small base and costs
3% of the narrated week's. It is a risk-allocation fix, not a P&L fix, and
n=40 keeps it directional.

### An informational number he did NOT authorise and I did not adopt

Passing every 3rd+ visit outright (rather than sizing it down) scores
**−$288 vs logged** across both weeks. Cutting those trades entirely is
worse than cutting their size. That is a point in favour of T48's spirit —
recorded because it argues against going further, not for it.

---

## 3b. THE CHECK THAT FAILED — and the bigger finding it produced

Before trusting the rule I tested its implied MECHANISM on data neither week
touched: **3,424 mechanical triggers across 87 session-days (2026-01…04)** —
the spendable fit span, not May, not the holdout.

**The mechanism is false.** Raw trigger outcome does NOT decay with visit
number:

| visit to that price level | n | mean MFE |
|---|---|---|
| 1st | 631 | 3.35R |
| 2nd | 499 | 3.69R |
| 3rd | 399 | 3.93R |
| 4th+ | 1,895 | 3.12R |

So "a level weakens each time it is tested" is not true on the tape. The
effect measured in the agent weeks is about the AGENTS, not about levels —
and at n=40 it could partly be noise.

**But the same data produced something stronger, at the DAY level:**

| days by ROTATION (how much price revisits its own trigger levels) | n | mean MFE | P(MFE≥2R) |
|---|---|---|---|
| least rotational quarter | 21 | **5.16R** | **42.0%** |
| most rotational quarter | 23 | **3.10R** | **30.8%** |

| days by TRIGGER COUNT | n | triggers/day | mean MFE | P(MFE≥2R) |
|---|---|---|---|---|
| fewest | 21 | 22.3 | **5.03R** | **39.0%** |
| most | 23 | 58.7 | **2.86R** | **29.8%** |

corr(rotation, day MFE) = −0.351.

**This is HIS pre-registered chop hypothesis, holding on data it was not
built from.** He wrote, before any measurement: *"In chop… a nothing candle
crosses two of them trivially… my trigger becomes structurally easier exactly
when it should be getting harder."* The trigger-count table is that sentence
measured — **the days that fire the most triggers are the days whose triggers
are worth the least.**

It also settles the fork his chop prereg §1 registered in advance: the damage
is **session-level, not trade-level**, so a day gate is the cheap fix and a
trigger gate is not. Per his own standing conditions on that prereg
(*"report-only… nothing adopted from this pass"*), **nothing was built from
it.** Recorded in `docs/PREREG-chop-regime-gate.md`.

**How this reframes 0.4.8, which the contract text now states honestly:**
finding yourself back at a level you already traded today is information
about the SESSION being rotational, not about the level decaying. That is
exactly why the rule caps size and never blocks — a stale level is not a
worse setup, it is the same setup on a worse day.

## 3c. THE AGENT RE-RUN — status, and two methodology findings

Re-adjudicating both weeks' takes through the real agent, baseline vs
amended, is running (52 candidates × 2 arms). It is the slowest and weakest
leg of the night and it is **not** what the conclusions above rest on. Two
things it has already established, both worth more than its headline number:

1. **Subagents hold the contract loaded at SESSION START.** The first A/B was
   killed because a probe graded a candidate **A** citing *"4th failed test
   since 03:15"* — the exact behaviour the amendment forbids — and, asked
   directly, reported its loaded contract had no such section. Both arms had
   been running the old contract against itself. Contract text must be
   delivered IN THE PROMPT. (Recorded in `docs/OFFLINE-HARNESS.md`.)
2. **The screenshot does real work.** Early results show candidates that were
   TAKES on the Mac coming back as PASSES offline at a high rate. Both arms
   carry the identical no-chart note so the A/B stays internally valid, but
   it corrects something I told him earlier: trigger briefings are
   numerically self-contained, and that is **not** the same as behaviourally
   self-contained. It raises the priority of the M3 chart renderer.

## 4. WHAT I DELIBERATELY DID NOT CHANGE

- **The management tier.** The counterfactual (`scripts/mech_manage_whatif.py`)
  says tier-3 is the single biggest edge in the stack: agent management beat
  every mechanical bracket on both weeks (+7.69R vs best-bracket +3.00R
  unseen; +11.99R vs +7.73R narrated), and its whole advantage sits on the
  loss side. Nothing here justified touching it.
- **The underwater holds** (6 of 10 rode to a full stop on the unseen week).
  His break-even-only-after-TP1 ruling *causes* longer holds by design, so
  this is partly the premium on a trade-off he chose. Three trades decide the
  question and they are his call, not mine — L8 (−0.63 → full stop), A8
  (−0.69 → full stop), L1 (−0.57 → recovered +1.78R).
- **The pass rate, stall-BE, C-grade no-trail.** Excluded from the
  optimisation surface in advance by the leak pre-registration, per his
  standing rulings.
- **Nothing on the thesis or manage contracts.** One change, one week of
  evidence behind it, one mechanism.

---

## 5. LIMITS, STATED PLAINLY

- **n = 40 graded takes.** Directional. The leave-one-day-out check is what
  makes it worth acting on at this size, not the totals.
- **June is diagnosing, and June must not ratify** (leak prereg §2). This
  rule is derived from June week 1 plus the narrated week, so it is now
  *fitted* to both. Its out-of-sample test is June weeks 2–3, and after that
  the untouched May span through the offline harness.
- **The dollar model** assumes his stated A/B/C sizing maps to risk per trade
  and that R is unaffected by size. True for a single account; not true if
  fills move.
- **The 15-point cluster tolerance** in `level_visits.py` is mine and
  unratified — his call whether a cluster should be matched by NAME instead.
