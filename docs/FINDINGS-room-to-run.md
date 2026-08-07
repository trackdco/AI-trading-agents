# FINDINGS — ROOM-TO-RUN AS A STANDALONE GATE (3m and 5m)

Run 2026-08-07 against `DECLARATIONS-room-to-run.md`, written first. No
CONCORD, no flow features, no frequency matching, no holdout contact. Fit
span only; holdout look #1 remains **HALTED**.

## THE VERDICT, IN ORDER OF STRICTNESS

| bar | result |
|---|---|
| **Bar 1** — lift ≥ +0.05R, paired lift-CI clear of zero in both eras, per session × TF × arm | **2 of 12** cells pass at 95%: **LONDON reject at 3m (+0.466) and at 5m (+0.366)**. |
| **Bar 1, Bonferroni ×12** (the α declared in §2) | **0 of 12.** The gate does **not** confirm on fit. |
| **Bar 2** — account layer, must lose on neither axis | **2 of 6** at the declared matched size — **LONDON at both TFs**. |
| **Bar 3** — frequency | **0 of 6** too thin. Every gated cell runs 1.27–2.41/day. |

**Reporting correction:** the runner's summary line counted only the
combined-arm cells and reported "0 of 6". The declaration's Bar 1 unit is
"per session, per TF, **per arm**" — 12 cells, of which 2 pass at 95%. The
combined-arm cells miss because the break arm dilutes a reject-arm effect.

**So: the gate screens through in one session on both candidate
timeframes, and dies under its own family-wise correction.** That is a
screening result, not a confirmation, and it is recorded as one.

## WHAT PASSED, AND WHY IT IS WORTH CARRYING

Two candidate timeframes independently select the same cell:

| cell | n_keep | lift | H2 CI | H1 CI | win kept/cut |
|---|---|---|---|---|---|
| LONDON reject 3m | 334 | **+0.466** | [+0.044,+0.716] | [+0.281,+0.855] | 39.8% / 27.1% |
| LONDON reject 5m | 308 | **+0.366** | [+0.054,+0.728] | [+0.013,+0.665] | 38.0% / 26.5% |

Dual currency **agrees** — the kept set wins more often *and* pays more, so
this is not the BR-20 inversion. And the two rows are a replication across
an independent trigger timeframe, which is worth more than either row alone.

The break arm does not carry it: LONDON break 3m is +0.051, 5m +0.222,
neither clearing. **Prediction 3 of the declaration — "the gate will look
better on the break arm" — is REFUTED.** The reasoning was that a break
already has direction and only needs room. What the data says is the
opposite: rejections are where room-to-run discriminates, presumably
because a rejection's whole thesis is the distance it can travel before the
next obstacle, while a break's is momentum through one.

## THE ACCOUNT LAYER — prediction 4 refuted, in the favourable direction

The declaration predicted: *"room-rich trades run further, so their losers
run further too… worst-day R may worsen and shrink the max size. If that
happens, that is the finding."*

**It did not happen. The opposite happened.** Worst-day R improved in every
one of the six cells, and max non-breaching size rose everywhere:

| cell | worst day R, ungated → gated | max size |
|---|---|---|
| LONDON 3m | −20.48 → **−6.79** | $50 → **$250** |
| LONDON 5m | −15.71 → **−7.65** | $100 → **$250** |
| NY_PRE 3m | −13.07 → −6.76 | $150 → $250 |
| NY_PRE 5m | −11.63 → −4.56 | $150 → $400 |
| NY_AM 3m | −21.44 → −10.81 | $50 → $150 |
| NY_AM 5m | −18.31 → −12.10 | $100 → $150 |

The gate roughly **halves worst-day R** and therefore lets the book carry
**2–5× the contract size** inside the same $2,000 drawdown.

**The real cost is frequency, and it is what hurt graduation.** The gate
keeps 22–27% of rows: LONDON 3m falls 6.53 → 1.47 fights/day. At the
declared *matched* size ($150 flat) that made P(graduate) *worse* in four
of six cells — fewer trades is less time to reach the target.

That matched-size comparison is also mis-scaled, and it is worth saying so:
$150 flat over-sizes every ungated book, whose own max non-breaching size
is $50–$150. Scored at each book's own carryable size, and under the
cushion policy BR-24 used:

| cell | GRAD @ own max size | GRAD @ cushion k=.05 | death (cushion) |
|---|---|---|---|
| LONDON 3m ungated | 8.3% | 51.7% | 82.3% |
| **LONDON 3m gated** | **91.2%** | **90.3%** | **17.5%** |
| LONDON 5m ungated | 56.9% | 62.9% | 74.5% |
| **LONDON 5m gated** | **84.7%** | **80.6%** | **20.2%** |
| NY_AM 3m gated | 58.5% | 58.5% | 58.8% |
| NY_PRE 5m gated | 22.1% | 19.1% | 44.3% |

At London the gate is not marginal — it takes graduation from 51.7% to
90.3% and cuts funded death from 82.3% to 17.5% under the same policy.

## BUT IT DOES NOT BEAT THE INCUMBENT ON THE OBJECTIVE THAT MATTERS

| book | EV | fights/day | P(graduate), cushion k=.05 |
|---|---|---|---|
| **incumbent** — LONDON 15m composite + sweep_b (BR-23/24) | +0.357R | 2.28 | **98.5%** |
| room-gated LONDON reject 3m | **+0.474R** | 1.47 | 90.3% |
| room-gated LONDON reject 5m | +0.459R | 1.39 | 80.6% |

**The gated book has the higher expectancy and the worse graduation rate**,
because it trades 35–40% less often and P(graduate) is a race against the
5-payout clock. This is the payout-cap dynamic the programme has been
pointing at since BR-24, showing up again: under a graduation objective,
frequency is not a nuisance parameter.

*(Caveat on comparability: the incumbent is a 2-locus union plus sweep_b;
this is the 7-locus reject arm under a room gate. Same policy and same
sizing, but not the same book — treat it as a scale reference, not a
head-to-head.)*

**Consequence:** room-to-run is a candidate for **combination with** the
incumbent, not replacement of it. The obvious next object is the incumbent
book *plus* room-gated 3m/5m London rejects as an additional stream — which
would raise frequency and EV together. That has not been measured and needs
its own declaration.

## SENSITIVITIES (reported, never selected on)

**Threshold.** Monotone in London — 2R +0.291, 3R +0.474, 4R +0.492, 5R
+0.528 at 3m — and the declared 3R operating point is *not* the best. It is
kept anyway, because it was read off the shipped partial and the sweep is
reported, not chosen from. Frequency falls 2.21 → 0.96/day across the
sweep, so the higher thresholds trade the Bar-3 margin away.

**Clustering X.** Gated book pooled: 0.25W +0.199, 0.5W +0.288, 1.0W
+0.339, 2.0W +0.215 at 3m. Positive at all four; the declared 0.5W is not
the peak.

**Costs.** LONDON survives all three assumptions (3m: +0.474 / +0.384 /
+0.294). **NY_PRE 3m goes negative at 1.5pt (−0.008)** — another reason the
London-only reading is the safe one.

## WHAT THIS CHANGES

- **Withdrawn:** the declaration's prediction 3 (break arm favoured) and
  prediction 4 (account layer as the likely failure point). Both refuted,
  and 4 refuted in the direction that helps.
- **Confirmed as the failure mode instead:** frequency. The gate's cost is
  that it trades a third as often, and under a graduation objective that
  costs more than the expectancy gain returns.
- **Not confirmed:** anything. Bonferroni takes all 12 cells to zero. This
  is a screening pass.
- **Holdout look #1 stays HALTED.** Room-to-run is a bar-only claim and
  joins look #1's frozen claim list per the partition declaration; the list
  now has a live candidate in it — LONDON reject, room ≥ 3R, at 3m and 5m —
  which is progress toward closing the list, not licence to open it.
