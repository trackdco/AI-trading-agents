# POSTMORTEM — j49, against the pre-registration

**Written after the book landed** (−4.1589R blended, 16 fills, 77/77
candidates). Companion to `docs/PREREG-j49-postmortem.md` (registered
mid-run) and `docs/PREREG-j49-SCORED.md` (the Mac session's honest scoring:
three of five predictions failed). This document runs the registered order
of operations — certify first, then diff, then attribute — and reports where
the money actually went. The pre-registration's prime suspect was wrong;
what the diff found instead is sharper.

---

## 1. H1 EXCLUDED — the briefings are clean

The stock certifier initially read **82.1% clean / 1,306 leaf mismatches**
against j49 (w49's era certified 100.0%), with 2m-bar deltas up to 1,913 —
which would have voided the whole measurement. It does not survive
inspection. The mismatches are **serving-convention differences introduced
by the mid-run fast path**, not corruption:

- The fast path includes the **in-progress 15m candle as of the decision
  minute** (causally correct); the offline generator serves only completed
  candles. At off-grid escalation minutes the window lists shift by one.
- Window anchoring on 2m lists differs the same way; index-aligned diffing
  then compares different windows and produces huge, meaningless deltas.

The decisive test: **every served bar that carries its own timestamp label,
checked against the tape at that label.** 494 labeled bars across all 129
j49 briefings: **zero volume disagreements, three price flags — and all
three are the partial current 15m candle, verified exact** (e.g. 05-31
03:12: served low 30571.50 / close 30577.50 = the true 03:00–03:12 partial
to the tick; the "true" value my ruler used included 03:12–03:15, which is
the future). Per-day: no day is worse than any other; there is no
slow-path/fast-path cliff.

**Verdict: every price the agents were shown was true to the tape and
causal. The j49 measurement stands.** Two follow-ups, neither blocking:
teach `certify_offline_briefings.py` the fast-path conventions so the
current era certifies exact again; and freeze serving conventions going
forward — w49 matched the offline generator bit-for-bit, j49 doesn't, and a
convention that moves mid-era costs a day of forensics every time.

## 2. Where the money went — the same tape, run twice

| day | jn1 (0.4.7 era) | j49 (0.4.10) | delta |
|-----|----------------:|-------------:|------:|
| 05-31 | +7.071 | +0.191 | **−6.880** |
| 06-01 | +2.254 | −1.500 | **−3.754** |
| 06-02 | −1.558 | −1.700 | −0.142 |
| 06-03 | +0.117 | −0.187 | −0.303 |
| 06-04 | −0.195 | −0.964 | −0.768 |
| **week** | **+7.689** | **−4.159** | **−11.848** |

**Days 1 and 2 are −10.63R of the −11.85R delta — 89.7%.** Days 3–5 are
noise-level differences on what is substantially the same book: **eleven of
j49's sixteen fills are jn1's own trades** — same minutes, same sides,
entries within a tick or two, stops within a few points, same outcomes
(06-02 L6/L8/L10, 06-03 A3/A6/A8, 06-04 L2/P3/A6, 05-31 P2 among them).
The trigger tier did not start selecting a different, worse book. Two
decisions and one stop did the damage.

## 3. Day 1, −6.88R: the thesis tier, executing his own Monday rule

The book, in order:

- 03:00 thesis: `bias: stand_aside` — *"sitting out London per the Monday
  no-massive-gap rule."* That is **T40** (`tv-thesis.md` §MONDAY IS A GAP
  DAY), and T40 is his own sentence: *"I'll only trade London on a Monday
  if there's a massive new week opening gap."* There was no massive gap.
- 03:12 trigger: PASS on the week's engine trade (jn1: short 30579.5,
  10.5pt stop, **+6.57R**) — then **escalated, flagging `thesis_stale=true`**.
- 03:12 thesis escalation: **REAFFIRMED** stand_aside.
- 03:18 (leg 2): PASS — `direction_mismatch, chop_edge_mismatch` — the chop
  map's only real appearance in the miss, and secondary: the chain was
  already dead at the thesis.

So the pre-registration's prime suspect (the 0.4.9 map) did not kill the
runner. **The Monday gate did, twice, working exactly as written.** The
question this puts to him is the acceptance test itself: a 43pt overnight
coil, no new-week gap, his rule says sit out — and the coil broke and ran
150 points. **Would he have taken 03:12, or is that a trade he genuinely
skips on a gapless Monday?**

- If he skips it: jn1's +7.69R was flattered by a trade he would not take.
  The honest baseline for this tape is **≈ +1.12R** (jn1 minus L1), and
  j49's real gap is ≈ −5.3R, most of it day 2.
- If he takes it: T40 needs its exception stated (what a tradeable gapless
  Monday looks like), and the escalation path needs a way to carry that
  argument, because `thesis_stale=true` was raised and declined.

## 4. Day 2, −3.75R: a short thesis that never let go

06-01 was an upward grind, and three defects stack in the book:

**(a) Bias anchoring.** v1 03:00 short → v2 08:00 short → v3 09:30 short —
three window-open reads, one inherited story, the same 30580–586 zone
numbers carried through all three, on a day that ground upward from 08:00
on. jn1's stack, on the same tape, was long by 09:46. Five long candidates
were passed against that bias — P3 08:36, P5 08:42, A2 09:46, A3 09:51,
A5 10:34 — **A2 09:46 and A5 10:34 being jn1's two winners on the day,
minute-for-minute.** (Fairness note: P3/P5/A3 passed substantially on the
licence alone; A2 and A5 also raised their own headroom objections, so a
fresh thesis alone might not have flipped every one of them.) The licensed
side produced L4 (−1.00) and A4 (−1.00); the day's only green was the late
flip, A6 (+0.50).

**(b) Condition semantics.** The relicense bar DID print — 15m closes
30601.75 at 10:00 and 30633.75 at 10:15 — then the 10:30 close dipped back
to 30559.5. At 10:34 one trigger read the test as instantaneous (*"unmet —
last complete 15m closed ~30557"*) and passed; at 10:45 another read it as
a preponderance (*"3/4 of last 4 15m closes sit above… condition met"*)
and took the flip. **Same sentence, opposite readings, 11 minutes apart.**
Neither agent is wrong; the sentence is — it never said whether a decisive
close latches or evaporates.

**(c) Frozen numbers.** The thesis's 30580–586 was stale against the live
VAH (30616) by mid-morning; two triggers said so in their own reasons —
*"the TRUE current daily/weekly VAH (30616, not thesis's stale
30580–586)"* — and had no lane to act on it, because obeying the standing
thesis is their contract. Escalation, the lane built for exactly this, was
never invoked on day 2 — five thesis-licence passes, zero escalations.

## 5. Days 3–5, −1.21R: the same book, one stop apart

The single meaningful divergence is **06-03 03:22** — the trade P2
predicted would be map-passed and was instead taken by both runs:

|     | entry | stop | width | outcome |
|-----|------:|-----:|------:|--------:|
| jn1 | 30499.0 | 30548.0 | **49pt** | survived the push to ~30523, **+1.78R** |
| j49 | 30493.0 | 30523.0 | **30pt** | stopped at 30523 at 03:30, **−1.00R** |

Same tape, same minute, same direction, entries 6pt apart: **the stop
decided it, worth −2.78R of swing.** Offset by j49 skipping jn1's two
losing 06-03 pre-market shorts (+1.92R avoided) and adding one Friday
London fade (−1.00R). Entry *selection* at 03:22 was identical across
eras; entry *geometry* wasn't. Stop widths overall are statistically alike
(j49 mean 32.7pt / jn1 33.7pt) — this is not a systematic tightening, it is
one placement call at the one minute where it mattered.

## 6. What this does to the standing findings

- **The MFE finding** (`docs/FINDING-j49-entries-not-management.md`) is
  arithmetically right and its exonerations hold (management +0.45R,
  trend filter dead at two horizons). But "the entry criteria selected
  setups with no follow-through" needs its composition read: the
  no-follow-through fills are largely **jn1's own fills**, which died both
  times. jn1's mean was lifted by the two thesis-blocked winners. This
  tape, under either stack, mostly didn't travel — **regime is doing most
  of the w49-vs-j49 MFE gap, and jn1-sans-runner (+1.12R) is what this
  week looks like without its one Monday trade.**
- **The chop map**: the SCORED verdicts stand (it did not bar 03:22; the
  06-02 churn was reproduced; the red fills were middle-zone TRENDING, not
  edge-CHOP). Its measured j49 role: co-signature on 05-31 leg 2, and five
  CHOP-labelled London fills at −2.51R which are substantially jn1's own
  churn repeated. It neither authored the week nor prevented it.
- **Conviction tiers**: 06-03 03:22 was `take_light` at conviction **A** —
  the grade/size split surviving 0.4.5's "the grade and the size must
  agree." One more row for his standing instinct that the tier system
  isn't doing what it claims; decision deferred to the sheet read as he
  ruled.

## 7. Open ruling logged by the run (not blocking)

**May a manager trail past breakeven before TP1?** Three did, one refused
as illegal — the contract currently supports both readings, which is the
actual defect. The book's own evidence cuts both ways: the week's only two
greens were pre-TP1 trails locking profit; the week's one management
giveback (06-01 A6, −1.60R unrealised) was a by-the-book trail. The ruling
is his, with the sheet; the fix either way is one unambiguous sentence in
`tv-manage`.

## 8. What NOT to conclude

- **Not "the stack is overfit and broken."** Data clean (§1), eleven of
  sixteen fills identical to the pre-doctrine run, NY_AM +2.06R under the
  same contracts that built w49. The damage is two named decisions and one
  stop width.
- **Not "add a trend filter"** — measured dead twice, at two horizons.
- **Not "revert the chop map"** on this evidence — it isn't what fired.
- **No contract edits** until he has read the sheet. Three minutes ARE the
  week, and all three are his calls to make: **05-31 03:12** (the Monday
  rule — take or skip?), **06-01 09:46** (the stale relicense bar — unlock,
  refresh, or stand?), **06-03 03:22** (30pt or 49pt — which stop is his?).
