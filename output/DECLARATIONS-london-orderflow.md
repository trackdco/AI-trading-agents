# DECLARATIONS — order flow on the reconstructed London book

Written **before any flow result was measured**. Substrate built (per-minute
b/a/vol/delta from the committed footprint files, their `aggregate()` verbatim,
convention `delta = b − a`, positive = SELL aggression) and coverage confirmed
— 400,488 minutes, 2025-06-01 → 2026-07-19, 35,039 minutes inside the London
window across 292 session days — but no outcome conditioned on flow has been
computed at declaration time.

**Venue status.** This is a **fit-era measurement**, not a holdout look. The
bar-only holdout is permanently closed. Nothing below can "confirm" in the
holdout sense; the strongest available verdict is *replicates on fit* or
*fails on fit*. Anything that survives queues for forward validation.

**Confirmability.** Flow coverage here is the whole fit era (292 London days,
~686 book trades), not the ~6-month venue the earlier flow work was priced
against. So the resolution problem that forced their "interesting but
unconfirmable" clause does not bind this particular measurement — but the
sample is still only ~2.8 fights/day, and any cut that halves the book leaves
~340 trades, which resolves a mean R difference of roughly ±0.15R at best.
Effects smaller than that are not readable here regardless.

---

## A. Already recorded dead — NOT re-proposed, NOT re-tested as findings

These carry recorded verdicts from the programme's own pre-declared work
(`DECLARATIONS-orderflow-five.md`, BR-104, BR-21, the cut study). Re-running
them as fresh hypotheses would be re-litigating settled nulls. They are
reported below only where they fall out of a table I am already computing,
and never promoted to a finding.

| Construct | Recorded verdict |
|---|---|
| WALL_AHEAD / wall size | **Significantly NEGATIVE** (M3 −0.356; WALLSZ −0.406) — contradicts the old canon's `D` gate which *required* it |
| All six MBP-10 depth features | Dead (BR-21) |
| CVD_CONF as confirmation | **Worst single construct** in M2 |
| Stacking 2+ flow constructs | Degrades **monotonically** (M2 24.7% → 23.2% → 19.4%) |
| `delta_z` declared low=bad direction | **Inverted** on both arms — recorded, not flipped |
| `thru_delta_conf`, `d15_conf`, `cvd_slope30` (break arm) | Killed on the pre-registered second half |
| Confluence/affirmation counts | Anti-predictive (winners had *fewer* in 7/9 cells) |

Standing conclusion being respected, not retested: **"more confirmation =
worse"** now has four independent demonstrations in this programme.

## B. REPLICATION — their two live flow findings, on my reconstruction

Both were derived on their own build. My reconstruction is independent
(rebuilt clustering, ~0.5 more fights/day). Replication here is a check on
*my* build as much as on their finding.

- **R1 — S1 flow-confirmation cut (reject arm).** Declared direction:
  removing fights whose decision-bar delta DISAGREES with trade direction
  raises EV. Their figure: +0.175R lift on the pre-registered half, full-fit
  +0.149 → +0.257R, removing ~54.5% of fights. **London-specific it was weak
  (+0.062R)**, versus +0.157R in NY_PRE. Declared bar for "replicates":
  positive lift in the same direction on the London book, reported with a
  day-block CI and with frequency alongside.
- **R2 — CONCORD < 7 (London sizing).** Declared direction: **LOW** flow
  concordance is *better* — the counterintuitive direction is the declared
  one. Their figure: lift +0.239R, London EV +0.357 → +0.596, worst day
  −5.41 → −4.18R, at the cost of halving frequency to ~1.01/day. Declared
  bar: same sign, and reported on both axes (EV and frequency) because the
  frequency cost is what made them call it a sizing rather than a gating
  opportunity.

## C. NEW — genuinely untested

- **N1 — flow × sweep_b.** sweep_b is **55% of the London book** and the
  component that passed the sealed holdout on its own (+0.251/+0.223R). It
  was discovered *after* the bulk of the flow work, and no flow construct has
  ever been scored against it. Declared question: does decision-bar flow
  confirmation/disagreement separate sweep_b outcomes at all? **No declared
  direction** — this is exploratory, so its output is a hypothesis, not a
  finding, and it re-enters as a pre-declared cut on data it did not touch.
- **N2 — delta DIVERGENCE, as distinct from delta confirmation.** Everything
  tested so far is *confirmation* (does delta agree with direction). The
  divergence construct is different: price makes a new extreme while
  cumulative delta does not. Declared as its own column computed from the
  same substrate; exploratory, no declared direction.

## D. Reporting rules accepted in advance

1. Every result in **R and in points**, never hit rate alone — the stop-width
   law applies (risk ≈ close_dist × range) and hit-rate passes are known
   unreliable in this programme.
2. **Both axes always**: EV and frequency together. A cut that raises EV while
   halving trade count can reduce qualifying days, and under the payout cap
   frequency is what manufactures them.
3. Day-block bootstrap for every interval (their seed convention, 20260807).
4. Exploratory outputs (N1, N2) are labelled **hypotheses**, not findings, and
   do not license any change to the book.
5. Any construct in section A that appears in a table is reported as
   *consistent/inconsistent with the recorded verdict* and is not promoted.
