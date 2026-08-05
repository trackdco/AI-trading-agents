---
date: 2026-08-08
kind: PROGRAMME VERDICT — status memo
audience: Angus
scope: everything tested to 2026-07-15
---

# Programme verdict, August 2026

> **The thesis was: mine public trading content for testable edges, mechanise them faithfully, and
> validate them statistically. Within the scope actually tested, that thesis is FALSIFIED.**
>
> Eighteen carded or swept strategies from three sources. **One is positive and unconfirmed.
> Everything else is negative, null, untestable, or blocked.** The single positive card sits below
> the multiple-testing bar it must clear, on a sample below its own floor, and is missing a
> component its author says is required.

---

## 1 · Where every strategy stands

| source | carded | baselined | positive | confirmed |
|---|---|---|---|---|
| ash10hazard | 1 | 1 | **1** | 0 |
| zxcked / Powell | 27 candidates | 4 | 0 | 0 |
| anonymous ORB post | 1 | 1 | 0 | 0 |
| **synthesis sweep (ours)** | 12 trials | 12 | 0 | 0 |

**Every baselined result, one locked exit, ranked:**

| card | n | win/BE/loss | expectancy | t | verdict |
|---|---|---|---|---|---|
| **`ash-unicorn-sb`** | **23** | 43.5/26.1/30.4 | **+0.516R** | +2.02 | plausible, **unconfirmed** |
| `zxck-cisd` | 40 | 22.5/22.5/45.0 | +0.044R | +0.35 | **is the null** |
| `zxck-10am-keyopen` | 115 | 22.6/24.3/53.0 | −0.162R | −0.70 | **is the null** |
| `zxck-ifvg-50` | 186 | 19.9/3.8/76.3 | −0.616R | −4.17 | **loses reliably** |
| `zxck-wick-ce` | 38 | 13.2/2.6/84.2 | −0.745R | −3.46 | **loses reliably** |
| `orb-fvg-nyopen` | 1558 | 26.3/24.6/49.0 | bound [−0.043, −0.015] | +0.93 | **retired** |
| 12 sweep trials | 40–215 ea | — | best +0.097R | max +1.06 | **nothing survived** |

Random-walk null for this exit is **25/25/50**. Note how many rows sit on it.

---

## 2 · The one unconfirmed card, stated without flattery

`ash-unicorn-sb` — sweep → structure shift → FVG entry → order-block stop, 09:45–10:15 ET.

| | |
|---|---|
| expectancy | **+0.516R** net, +13.0R total, maxDD **5.0R** *(rev 2026-08-08)* |
| effect (t/√n) | **+0.421** gross, +0.383 net |
| **deflation bar at N=293 trials** | **+0.6978** — it reaches **60%** of it |
| n | **23 — below the n≥30 floor**, after two defect fixes cut it from 37 |
| direction | **17 long / 6 short** on a market that rose 21,304 → 29,690 |
| missing component | the **ES leading trigger**, which its author states is part of the entry. Never implemented. No ES data. |
| flow enhancement | **VOID** as of 2026-08-08 — the feature was not computable at entry |

**It is on forward trial, not in use.** Forward log: 0 rows, first eligible 2026-08-08. At ~1.5
trades/month, LOOK 2 (n=46) is roughly **20 months** away.

**The one-sidedness is the honest worry.** 21 of 24 trades long, in a rising market, is not a
property its author claims. Whether the edge survives a market that falls is untested and
untestable on this data.

---

## 3 · The searched-out window

08:00–10:30 ET was searched **twelve ways** in one pre-registered sweep — sweeps, gap reversion,
opening drive, CVD divergence, participation surprise, VPOC migration, the 08:30 release second
leg, the cash-open backlog — plus 12 more mechanisms discarded pre-test on measured grounds.

**Nothing survived.** Best discovery candidate **+0.097R** against a best-of-12 noise floor whose
**median is +0.310R** — the **1.5th percentile**. All three promoted candidates failed a one-shot
holdout; two flipped sign.

**The transferable number: at these sample sizes a 12-way search manufactures +0.31R half the
time.** Any future candidate reporting ~+0.3R on 50–150 events should be read against that first.

**The binding arithmetic**, measured: median 1-min range **6.8pt** at 08:00–08:29 against **55.5pt**
on the 08:30 release bar and **46.0pt** at 09:30. A pre-09:30 entry needs ≥40pt of travel for 2R.
**Every calendar *return* anomaly is 5–25pt on NQ — an order of magnitude too small for this
exit.** Only liquidity events qualify, and the window holds exactly two.

---

## 4 · Defect catalogue — every one was live in shipped numbers

**This is the most important section, because none of these was found by a result looking wrong.**

| # | defect | where | what it cost |
|---|---|---|---|
| D1 | **Sweep gate tested position, not crossing** | `ash_raw_baseline.py` | 30 of 37 trades took the broken path; **n 37 → 24**. Two of six stated conditions did not bind on most of the sample. |
| D2 | **Same-bar fill-and-stop** | 5 scripts | `zxck-10am-keyopen` −5.0R; a +2R win was really −1R. 0 of 24 on ash. |
| D3 | **Look-ahead via minute aggregation** | every F2 computation | **Voided the programme's flagship flow finding.** Feature not computable at entry. |
| D4 | **`cap_rules` gated on an outcome** | `orb_fvg_baseline.py` | 70% of deletions removed already-open positions. **Falsified a stated conclusion**; t −3.68 → −0.41. |
| D5 | **Roll contamination via day-level banding** | shared data layer | 4.14% of rows off-band; **2025-09-15's raw VPOC was 239.90 — a calendar-spread price**. Fixed 2026-08-08. |
| D6 | **Prior session = previous calendar key** | `orb_fvg_baseline.py` | Levels silently NaN on 61 of 290 sessions, correlated with day-of-week. |
| D7 | **Docs disagreeing with their own CSVs** | 7 documents | Stale tables, a p-value on a stale n *and* a stale base rate, a withdrawn claim left standing in the index. |

**Every one was found by reading code against cards, or by an adversarial audit — never by the
numbers looking suspicious.** The pre-fix flagship looked *fine*.

**Three of these (D3, D4, and the F2 window) are the same class: a correct signal about the wrong
interval.** A look-ahead is perfectly robust to trimming, so no fragility test can catch it. The
only defence that worked was executable assertions about time boundaries.

---

## 5 · ⚠️ Scope conditions — what "nothing survived" does NOT mean

Stated so the verdict is not over-read. Every result above is conditional on:

1. **A fixed 2R target with break-even at 1R, no trailing.** This is **ours**, chosen for
   poolability. Powell's own stated band is **1:3 minimum, 1:4–1:6 typical**, and every R-multiple
   he quotes comes from a *trailed* exit. **A fixed-target backtest is not measuring the same
   object as his numbers.** Nothing here tests his exits.
2. **NQ only.** No instrument where the geometry differs was tested. The clearest failure —
   `zxck-ifvg-50`'s 5pt stop — is a statement about *NQ's* 09:45–10:15 volatility (median 1-min
   range 21pt), not about the concept.
3. **~13 months, 2025-06 → 2026-07, one regime**, in which NQ rose ~39%. No bear phase, no
   volatility shock.
4. **Two clock windows** (09:45–10:15 and 08:00–10:30), both **ours**, neither stated by any
   trader for most cards.
5. **No ES, no tick sequence, no usable depth.** Four stated components across two independent
   traders are unimplementable. `ash-unicorn-sb` has **never been tested as taught**.
6. **Small samples throughout.** The winner has n=24. Most cards detect only large effects; the
   autopsy's power floor was Cohen's d = 1.33.

**"These specific mechanisations, on NQ, in this window, on this exit, over 13 months, did not
work."** That is the claim. It is not "ICT concepts don't work", and it is not "order flow doesn't
help".

---

## 6 · The data fork — the actual decision

Everything left is blocked on data. Three options.

### A · Wait — forward accumulation
**Cost: nothing. Time: ~20 months** to `ash-unicorn-sb`'s LOOK 2 at n=46.
Raises t without raising N, so it is the only route that does not further inflate the deflation
bar. It is also the only route that produces genuinely out-of-sample data, since the entire owned
span is now in-sample.
**Risk:** 20 months to a possible "no", and one card's forward set tests one hypothesis.

### B · Buy history — deeper span
**Cost: a Databento GLBX.MDP3 pull. Time: days.**
More sessions for every existing detector at once. **But it does not fix the binding problem:**
history is still in-sample once we look at it, and a bigger in-sample set does not confirm
anything. Its real value is **power for pre-registered hypotheses** — if a hypothesis is
registered *first*, older data it has never seen is a legitimate test bed.
**Only worth buying against a registered slate**, which is what tonight's Stage 3 is for.

### C · Buy resolution — tick/trades sequence
**Cost: a GLBX.MDP3 *trades* pull, ~280 sessions × the relevant minutes. Time: days.**
This is the one that unblocks *classes* of question rather than adding rows:
- **Settles H2/H2′ properly** — the only thing that can, since minute aggregation is precisely
  what broke it.
- **Resolves the 73 ambiguous `zxck-10am-keyopen` sessions** currently handled by bounding.
- **Makes every intrabar-ordering bound in the programme collapse to a point estimate.**

### Recommendation
**C, then A.** Tick resolution removes a whole defect class and is cheap; forward accumulation
runs in parallel at zero cost. **B is worth buying only against tonight's registered hypothesis
slate**, never speculatively — buying history to search it again would just raise the deflation
bar with our own money.

---

## 7 · What the programme actually produced

Since nothing was confirmed, the return is in what is now closed, measured, or built.

- **A validated defect catalogue and the discipline that catches them.** Seven defect classes, all
  found by code-vs-card reading and adversarial audit. The executable-time-boundary assertion is
  now standard.
- **Negative knowledge with mechanisms.** Not "it didn't work" but *why*: a 5pt stop is inside
  99% of 1-min bars here; a midpoint entry with a tip stop puts the stop where price just was;
  10:00 is not a liquidity event once the cash market is open.
- **A noise floor for this programme's sample sizes** — a 12-way search manufactures +0.31R half
  the time.
- **Reusable machinery**: one locked exit, a session-clustered inference harness, a matched
  random-direction control, a roll-clean data layer, and a trials ledger with **N counted
  honestly** rather than counted only when convenient.
- **Two data defects fixed at source** (January 2026 flow gap, roll contamination) that affected
  every flow result in the repo.

**The honest summary: the programme did not find an edge, and it is now very good at proving it
hasn't.** That second thing is worth more than the first would have been if it were wrong.
