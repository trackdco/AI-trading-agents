---
date: 2026-08-07
kind: SYNTHESIS SWEEP — 08:00–10:30 ET entries, 12 candidates, one-shot holdout
ledger: research/_shared/trials-ledger.md
harness: scripts/sweep_harness.py · candidates: scripts/sweep_candidates.py
logs: research/_shared/sweep-logs/
verdict: ⛔ NOTHING SURVIVED
---

# Synthesis sweep, 08:00–10:30 ET — **no candidate survived**

> ## ⛔ THE ANSWER
> **No candidate beat the noise floor, out-of-sample or in.**
>
> The best of 12 trials reached **+0.097R** in discovery against a best-of-12 noise floor whose
> **median is +0.310R**. It sits at the **1.5th percentile** — *98.5% of random-direction searches
> over the same events would have produced a better winner than ours.*
>
> All three promoted candidates then **failed the one-shot holdout**. Two flipped sign.
>
> **Order flow did not improve anything.** Every arm's clustered 95% CI straddles zero in both
> periods, and the flow-based group is *worse* than the price/structure group in both.

---

## 1 · What was actually run

| | |
|---|---|
| entry window | **08:00:00–10:30:00 ET**, exits to the 16:00 cap |
| span | 2025-06-01 → 2026-07-15, **289 complete sessions**, all flow-covered |
| **DISCOVERY** | 2025-06-02 → 2026-02-27, **192 sessions** |
| **HOLDOUT** | 2026-03-02 → 2026-07-15, **97 sessions** |
| exit | locked convention on every candidate, no exceptions |
| ledger N | **12** |
| pre-test discards | **12 more**, recorded at zero statistical cost |

**The split, the exit, the inference rules, the noise-floor design and the promotion rule were all
committed before any candidate was tested** (`3d975f4`, `5da3dbd`). The holdout directions were
committed before holdout was touched (`5c6aee0`).

**⚠️ This window is a THIRD convention and it is ours.** Every existing card is scored on
09:45–10:15 or 09:30–10:30. Nothing here pools like-for-like with the existing logs.

---

## 2 · Discovery — all 12 trials

| candidate | lens | n | sess | win/BE/loss/TO | avgR | cost | **exp** | totR | maxDD | t_clus |
|---|---|---|---|---|---|---|---|---|---|---|
| `sw-precash-value-migration` | B | 90 | 90 | 30/19/48/3 | +0.145 | 0.048 | **+0.097** | +13.0 | 5.0 | +1.06 |
| `sw-onx-reclaim` | A | 119 | 115 | 29/24/47/1 | +0.104 | 0.045 | **+0.059** | +12.4 | 11.0 | +0.92 |
| `sw-precash-price-migration-CTL` *arm* | B | 73 | 73 | 32/14/53/1 | +0.102 | 0.063 | +0.039 | +7.5 | 7.0 | +0.65 |
| `sw-open-drive-pcr` | A | 75 | 75 | 31/15/55/0 | +0.067 | 0.033 | **+0.033** | +5.0 | 7.0 | +0.43 |
| `sw-gap-nopart-INV` *arm* | A | 59 | 59 | 31/17/53/0 | +0.085 | 0.053 | +0.031 | +5.0 | 9.0 | +0.49 |
| `sw-cvd-div-reclaim` | B | 215 | 162 | 26/23/50/0 | +0.019 | 0.094 | **−0.075** | +4.0 | 20.0 | +0.24 |
| `sw-0930-cashopen-carry` | C | 45 | 45 | 24/13/60/2 | −0.085 | 0.025 | **−0.111** | −3.8 | 5.8 | −0.45 |
| `sw-gap-nopart` | A | 40 | 40 | 25/20/55/0 | −0.050 | 0.065 | **−0.115** | −2.0 | 12.0 | −0.25 |
| `sw-thinbook-surprise` | B | 132 | 132 | 24/20/56/0 | −0.076 | 0.101 | **−0.177** | −10.0 | 24.0 | −0.70 |
| `sw-0930-carry-CANON` *arm* | C | 18 | 18 | 17/11/67/6 | −0.269 | 0.023 | −0.291 | −4.8 | 8.0 | −0.96 |
| `sw-0830-secondleg` | C | 39 | 39 | 18/21/62/0 | −0.256 | 0.039 | **−0.296** | −10.0 | 11.0 | −1.40 |
| `sw-0830-secondleg-CANON` *arm* | C | 17 | 17 | 24/12/65/0 | −0.176 | 0.032 | −0.209 | −3.0 | 5.0 | −0.57 |

**Only 3 of 8 primaries are positive at all, and the largest is under +0.10R.** Not one |t_clus|
reaches 1.5. Control integrity: real R matched a precomputed direction on **100.00% of 922**
discovery events.

---

## 3 · The noise floor — the number that decides this sweep

Best-of-12 discovery expectancy under **random direction**, matched for time-of-day, event count
per session, session clustering, stop geometry and the identical locked exit. 6,000 replications.

| | best-of-12 null |
|---|---|
| median | **+0.3097** |
| p75 | +0.3956 |
| p90 | +0.4971 |
| p95 | +0.5611 |
| p99 | +0.7088 |

> ### Our best candidate: **+0.0968R → the 1.5th percentile.**

**This is not "failed to clear significance". It is far below the median of what pure chance
produces when you search twelve times.**

The floor moved from **+0.1401 at best-of-4** (lens A alone) to **+0.3097 at best-of-12** — exactly
as it must. **Searching wider raises the bar the winner has to clear, and this sweep made that
cost visible instead of hiding it.** A sweep of 12 candidates needs a much better winner than a
sweep of 4 to mean the same thing.

For scale: `ash-unicorn-sb`, the programme's only positive card, sits at **+0.655R**.

---

## 4 · Holdout — one shot, three candidates, Holm-corrected

| candidate | disc exp | **hold exp** | n | sess | win/BE/loss/TO | t_clus | p_raw | p_holm | **verdict** |
|---|---|---|---|---|---|---|---|---|---|
| `sw-precash-value-migration` | +0.097 | **−0.068** | 51 | 51 | 20/31/45/4 | −0.18 | 0.573 | 1.000 | **FAILED** — sign flipped |
| `sw-onx-reclaim` | +0.059 | **+0.064** | 53 | 52 | 26/28/43/2 | +0.56 | 0.286 | 0.858 | **FAILED** |
| `sw-open-drive-pcr` | +0.033 | **−0.217** | 26 | 26 | 23/12/65/0 | −0.77 | 0.781 | 1.000 | **FAILED** |

**Nothing survived.** Two of three flipped sign between discovery and holdout.

`sw-onx-reclaim` is the only one that held its sign (+0.059 → +0.064, remarkably stable), **and it
still fails**: t_clus +0.56, p_holm 0.858, and +0.064R is **a fifth of the noise floor's median**.
Stability is not edge. It is the most interesting of the three and it is not a candidate.

---

## 5 · Does order flow measurably improve them? **No.**

### 5.1 The two older flow hypotheses were not run, and why

| hypothesis | status | why not run |
|---|---|---|
| **F2-stall** (`retrace_ratio < 1.0`) | **HALTED** | The feature is **not computable at the entry instant** (`f2-h1-oos-test.md`). Applying it here would reproduce the defect, not test it. |
| **H1-magnitude** | **RETIRED** | Failed out-of-sample on 115 independent trades — Cliff's δ +0.178 against an in-sample +0.596, p_holm 0.1895. |

### 5.2 The pre-registered flow-vs-price test — identical rules, direction from VPOC vs from price

| arm | period | n | exp | **95% clustered CI** | maxDD |
|---|---|---|---|---|---|
| **FLOW** (VPOC migration) | discovery | 90 | +0.097 | **[−0.172, +0.366]** | 5.0 |
| **FLOW** (VPOC migration) | holdout | 51 | −0.068 | **[−0.381, +0.245]** | 8.9 |
| PRICE-ONLY control | discovery | 73 | +0.039 | [−0.269, +0.348] | 7.0 |
| PRICE-ONLY control | holdout | 49 | −0.242 | [−0.574, +0.090] | 9.9 |

**Every interval straddles zero, in both periods, in both arms.** The flow arm is nominally ahead
in both periods (+0.058 discovery, +0.174 holdout), which satisfies the generator's pre-registered
condition for the flow claim to be *supported at all* — **but the intervals overlap almost
completely and neither arm is distinguishable from zero.** The comparison decides nothing.

### 5.3 Flow-based vs price/structure-based, pooled (descriptive, not a test)

| group | discovery | holdout |
|---|---|---|
| flow-based (3 candidates) | n=437, exp **−0.070** | n=210, exp **−0.111** |
| price/structure (5 candidates) | n=318, exp **−0.037** | n=152, exp **−0.102** |

**The flow group is worse in both periods.**

### 5.4 ⚠️ What our flow data CANNOT test — so this answer is not over-read

- **Sub-minute sequence.** Footprint is (minute × price × side). Volume-at-price is identical
  whether price went up-then-down or down-then-up. This is why F2 is not computable at entry, and
  it is the only thing that would settle H2.
- **Resting liquidity / heatmap / refill.** Depth is one snapshot per minute **and** mis-stamped —
  100% of rows land >30s into their labelled minute.
- **Cross-instrument (SMT).** No ES. Two independent traders in this corpus require it.

**"Flow did not help" here means: the aggregate minute tape, read strictly before entry, did not
help.** It says nothing about book dynamics we cannot see.

---

## 6 · Verdict per candidate

| candidate | lens | verdict | why |
|---|---|---|---|
| `sw-onx-reclaim` | A | **FAILED** | Held its sign across the split (+0.059 → +0.064) — the only one that did — but t_clus +0.56, p_holm 0.858, and a fifth of the noise floor |
| `sw-precash-value-migration` | B | **FAILED** | Best in discovery, **sign-flipped** in holdout |
| `sw-open-drive-pcr` | A | **FAILED** | Sign-flipped, −0.217R in holdout |
| `sw-cvd-div-reclaim` | B | **FAILED** | Negative in discovery (−0.075); not promoted |
| `sw-thinbook-surprise` | B | **FAILED** | −0.177R; the 0.101R cost on a 13pt median stop is a third of the damage |
| `sw-gap-nopart` | A | **FAILED — and falsified by its own diagnostic** | Gate −0.115R, **gate INVERTED +0.031R**. The participation gate is not inert, it points the wrong way |
| `sw-0830-secondleg` | C | **FAILED** | Worst in the sweep, −0.296R; its canonical-only arm agrees in sign, so the tape gate is not the problem — the mechanism is |
| `sw-0930-cashopen-carry` | C | **FAILED** | −0.111R; canonical arm −0.291R |
| — | — | **BLOCKED** | SMT/cross-instrument (no ES), sub-minute sequence, book depth/refill |

**No candidate is promoted to forward accumulation.** There is nothing to write a forward protocol
for, and writing one anyway would be dressing a null as a pipeline.

---

## 7 · What this sweep actually bought

Nothing survived, so the return is entirely in what is now closed or measured.

1. **The 08:00–10:30 window has been searched twelve ways and yields nothing.** Sweeps, gap
   reversion, opening drive, CVD divergence, participation surprise, value migration, the 08:30
   second leg, the cash-open backlog. That is a real negative about a window this programme had
   never touched.

2. **The binding arithmetic, measured.** Median 1-min range: **6.8pt at 08:00–08:29**, 8.2pt at
   08:35–09:29, 20.8pt at 09:30–10:30, but **55.5pt on the 08:30 release bar** and **46.0pt on the
   09:30 bar**. A pre-09:30 entry needs ≥40pt of travel for 2R; post-09:30 with a noise-respecting
   stop needs ≥90pt. **Every calendar *return* anomaly is 5–25pt on NQ — an order of magnitude too
   small for this exit.** Only liquidity events displace price enough, and the window contains
   exactly two: 08:30 and 09:30.

3. **Why `zxck-10am-keyopen` landed on the null, independently explained.** Tape detection of a
   release *fails* at 10:00 — volume ratio **2.24 on non-release days vs 2.64 on release days**, no
   separation, because the release is drowned by ambient RTH volume. **10:00 is not a liquidity
   event once the cash market is open.** That was derived here without reference to that card's
   result.

4. **A second data defect found and confirmed.** The shipped day-level price-band clean cannot
   separate contracts during a quarterly roll. **4.53% of footprint rows / 2.42% of volume** sit
   outside their own minute's bar range, concentrated on roll dates (2025-09-15 **54.4%**). A
   roll-week volume profile is ~half back-month and its VPOC can land hundreds of points outside
   the session's own range. Every volume-at-price computation here applies a minute-level clean.

5. **A news-calendar trap caught before it could poison the split.** Two calendars with different
   inclusion criteria change over at 2026-02, exactly on the boundary; naive concatenation makes
   the in-window news rate jump **29% → 74%**. Resolved with a 17-event intersection whitelist.

6. **The pre-cash thin-book sweep is structurally incompatible with a fixed 2R exit** — 54.9pt
   median overshoot forces either a sub-15pt stop or a draw at only 1.9× risk.

7. **The noise floor itself is the most transferable output.** At these sample sizes a 12-way
   search manufactures **+0.31R half the time**. Any future candidate in this programme reporting
   ~+0.3R on ~50–150 events should be read against that number first.

---

## 8 · New hypotheses logged — UNTESTED, for a future cycle

Recorded so nothing found here leaks into a test it was not pre-registered for. **All untested.**

- **N-S1 · `sw-onx-reclaim` sign stability.** It is the only candidate whose expectancy held sign
  across the split (+0.059 → +0.064) on 167 sessions. That is *not* a finding — it fails on every
  pre-registered criterion. It is the one thing here worth a fresh look on **new** data, and it
  must not be re-tested on any data used above.
- **N-S2 · The same-bar sweep-and-reclaim arm of `sw-onx-reclaim`** (51% of the permissive
  reading's events), deliberately excluded here because it is the `zxck-wick-ce` geometry.
- **N-S3 · The 08:30 second leg with a directional gate.** Both Lens C candidates supply WHEN and
  a mechanism but their direction rule is the release's own sign, which is the weakest part.
- **N-S4 · Retracement DURATION as a feature**, noted during the F2 audit, never a hypothesis.

**None of these may be tested on the 289 sessions used above.**
