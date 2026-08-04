# London candidate programme — close-out, 9 of 9

**Drafted for Brake's signature.** Routes to Angus.
**Sealed 2023/24 untouched throughout. Zero holdout looks spent.**

All nine greenlit London candidates are resolved or formally determined. No survivor.
Total cost: **34 trials**, seven censuses, no deployment, no holdout burn.

---

## The table

| # | candidate | outcome | trials | why |
|---|---|---|---|---|
| 1 | london-inventory-fade | **FAIL** | 4 | fragility gate fired, both eras |
| 2 | london-asia-sweep-reversal | **FAIL** | 4 | one family with #3 |
| 3 | london-asia-sweep-continuation | **FAIL** | — | same family, same ledger |
| 4 | london-level-trap-fade | **FAIL** | 4 | well-powered null; refinement pointed the wrong way |
| 5 | london-vwap-sigma-rotation | **INCONCLUSIVE** | 4 | + three findings against, one attacking the premise |
| 6 | london-euro-open-drive | **NOT TESTABLE** | 0 | strict one-time-framing fires on 0 of 103 drive opens |
| 7 | london-value-traverse | **INCONCLUSIVE** | 4 | validate era n=23; naked POCs do not attract price |
| 8 | london-eu-macro-windows | **BLOCKED** | 0 | no European release calendar exists in our data |
| 9 | london-level-defense-flow | **FAIL** | 6 | absorption null at the resolution that can see it |
| | plus | | | |
| — | LDN-FLOW-01 (flow-as-filter) | **FAIL / INCONCLUSIVE** | 8 | minute-aggregate flow: AUC ~0.5 |

**Ledger: 34.** Two candidates cost zero trials because they were stopped before any outcome
was measured — the feasibility discipline working as intended.

## What actually killed them

Grouping by cause is more useful than by candidate:

**Three died of no signal.** Level-trap-fade, level-defense-flow, and the flow-filter work
all had adequate power and simply found nothing. These are the valuable nulls — we can say
"not there", not "we couldn't see".

**One died of fragility.** Inventory-fade's result lived in a handful of events.

**One died of my own specification defect.** Asia-sweep looked spectacular (Δ −39/−68,
p<0.001, robust to every trim) because group P's direction was set by a breach landing a
median 47 minutes *inside* the outcome window. Circular. The causal re-measurement collapsed
it to +2.84/+1.57.

**Two were never testable.** Euro-open-drive's own gate fires on zero days out of 103.
Value-traverse's 80%-rule leg produces 4 and 1 events.

**One is blocked on a missing input**, not on evidence.

**One had its premise contradicted.** VWAP-sigma-rotation assumes London is rotational;
London accepts beyond ±2σ on 37% of the days it gets there.

## The three things worth keeping

**1. Two eras are not a formality.** Three separate times a result looked tradeable on one
era and inverted on the other:

| | discover era | validate era |
|---|---|---|
| TRAPPED (flow filter) | −2.46 pts, 40.0% win | **+8.19 pts, 56.6% win** |
| ABSORB (level defense) | +3.06 pts | **−11.77 pts** |
| naked-POC magnet | +4.74 pts | −6.62 pts |

Each of these, presented alone, would have been a confident and wrong recommendation.

**2. The fragility gate cannot catch a specification defect.** Twice now — LDN-SWP-01's
circular direction, and my own broken placebo in LDN-VT-01, which reported a naked-POC touch
rate of 49.1% against a placebo of 0.0%. **Circularity is perfectly robust to trimming.**
Only the causality audit catches it, and it has to be run as code, not as a reading.

**3. Count the full gate stack — including the entry trigger — before writing a prereg.**
This failed twice. Euro-open-drive cleared a trigger-only count at 67/36 and dies at 0.
Value-traverse cleared a setup-only count at 137/60 and produced 53/23 events, putting the
validate era under the floor. **A trigger-only or setup-only count is an upper bound and
will clear candidates that cannot be tested.**

## Recommended amendments to `VALIDATION-PROCESS.md`

1. **§2.2** — the n-floor check must run on the candidate's **complete gate stack including
   the entry trigger**, not its setup conditions. State the count that survives everything.
2. **§2.4** — add a mandatory **causality audit as executable assertions**, not a prose
   section. Every census must assert that no input variable reads a timestamp after the
   event minute.
3. **Kill criterion 2** — restate in equivalence form. "Failure to reject" is not a kill;
   the CI must exclude the discover-era estimate.
4. **Sweep harnesses must record per-trial Sharpes.** The DSR denominator currently uses
   nominal trial counts because no sweep script writes the Sharpe distribution. This is the
   one piece of the gate still running on an approximation.

## What is actually left

Three live threads, none of them a candidate:

- **Get the EU release calendar.** One Forex Factory scrape on a machine FF permits (this
  container is Cloudflare-blocked), filtered to EUR/GBP, committed as
  `config/news_calendar_eu.csv`. This unblocks #8 — the only candidate with **LOW** NY-canon
  input-family overlap, which is what the diversity criterion wants. It also lets every
  London null so far be re-read with news conditioning, which none of them had.
- **Value-traverse leg (c)** (LVN air pockets) is testable at 72/38 events and untested. I
  recommend holding it: legs (a) and (c) both assume the profile map marks places price is
  drawn to, and the leg (a) secondary says naked POCs have no pull beyond distance.
- **Resting-book depth** (MBP-10 imbalance, size at level) is a genuinely untested
  information family. Caveat: our depth is one snapshot per minute, so pulled bids and
  iceberg refill cannot be measured from it at all.

## The honest summary

Nine candidates, no survivors, nothing deployed, no holdout burned. The nulls that came from
adequate power are real knowledge; the two untestable determinations cost nothing; one
candidate is waiting on a CSV.

Per the brief: **the machine is the deliverable, and survivors are a bonus.** The machine
ran, caught two of its operator's own errors on the record, and refused to promote anything.
There was no bonus.
