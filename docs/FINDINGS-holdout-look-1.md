# HOLDOUT LOOK #1 — SPENT, plus the recorder fix and conviction sizing

2026-08-07. Look #1 executed against the committed declaration. Builder SHA
`13e79a2f`. Flow venue never touched. New York analysis untouched.

---

# ITEM 1 — THE LOOK

## Gate first (R4.2)

Entry gate on the **sealed build**, before any sealed row was read:
**T1 206 probes (0 bad, 119 moved) · T2 0/110 fail · T3 0/96 fail → PASS.**

## Results

| claim | Block A | Block B | verdict |
|---|---|---|---|
| **H1** LONDON base rate | n=296, EV **+0.183**, ×5 CI [−0.074,+0.458] | n=419, EV **+0.116**, ×5 CI [−0.073,+0.305] | **VOID — see below** |
| **H2** NY_PRE base rate | n=192, EV +0.022, [−0.229,+0.306] | n=261, EV +0.028, [−0.226,+0.287] | **FAIL** |
| **H3** NY_AM base rate | n=275, EV +0.110, [−0.136,+0.371] | n=444, EV **+0.284**, [+0.090,+0.511] ✓ | **FAIL** (one-block pass is a miss, R3) |
| **H4** sweep_b LONDON | n=**0** | n=**0** | **NOT EVALUABLE — see below** |
| **H5** closeloc cut | n=958, lift **+0.096**, ×5 CI [+0.027,+0.164] ✓ | n=1428, lift **+0.096**, ×5 CI [+0.037,+0.155] ✓ | **PASS** |

## TWO INTEGRITY PROBLEMS, both found after the run and both mine

### H4 is not evaluable, and H1 was not tested as declared

`scripts/htf_ma_sweep_locus.py` **line 192**:

```python
# prior stopped attempts, from the seven-locus census (fit rows only)
L = pd.read_parquet(ROOT / "output/htf_ma_census/levels_fit_v1.parquet")
```

sweep_b is defined as *a sweep of a prior stopped attempt's own stop*. Its
source of prior stopped attempts is the **fit** levels file. On sealed days
there are no fit rows, so **sweep_b can never be emitted outside the fit
span**. Confirmed directly: `sweep_sealed.parquet` holds 7,232 rows, **all
`sweep_a`, zero `sweep_b`**. (It also stops at 2024-12 — the builder
computes a `gray` list and never writes it, so 2025-01..05 has no sweep rows
at all.)

Consequences:

1. **H4: NOT EVALUABLE.** The sealed artifact structurally cannot contain
   the cell the claim names. Zero rows were read for H4, so no look was
   spent on it. Neither pass nor fail.
2. **H1 is VOID, not FAIL.** R1 defines the LONDON book as **composite +
   sweep_b**. What ran was **composite only** — because sweep_b is absent.
   On fit, sweep_b is **367 of 664 rows, 55% of the London book.** The
   number reported above is a valid test of a *different* claim (London
   composite-only base rate, which failed) and **is not a test of H1.**

**I am not re-running either.** R8 says one look, no re-runs, and your
standing instruction is no further holdout contact beyond item 1. Whether a
mis-executed claim may be re-executed after a build fix is a question about
the declaration, and it is yours, not mine. Recorded and left open.

## WHAT THE VALID RESULTS MEAN

**H2 and H3 failing was predicted in the declaration** and is recorded as
declared: *"A NY_PRE or NY_AM fail on the holdout is therefore predicted,
and will be recorded as confirmation of a known fit-side weakness, not as
new information."* NY_PRE came back at essentially zero (+0.022 / +0.028) —
that is a cleaner refutation than the fit weakness implied. NY_AM's Block B
(+0.284) actually cleared; Block A did not, and a one-block pass is a miss.

**H5 PASSING is the substantive result, and it is the one nobody expected.**
The closeloc cut delivered **+0.096R of lift in Block A and +0.096R in
Block B** — identical to three decimal places across two disjoint
multi-year blocks, both clearing a ×5-corrected 99% interval, against a
declared bar of +0.04R. Threshold taken from **fit** (Q1 = 0.3721), not
re-derived on the holdout.

**The shape of the outcome inverts the programme's expectation.** R0's
whole architecture assumes the base population is the thing worth
validating and selection layers ship on fit plus forward data. What came
back is the opposite: **every base-rate claim failed or could not be
tested, and the one selection layer passed cleanly in both blocks.**

**R5 governs how the failures are read**, and was pre-committed: the sealed
span is bull-heavy and the book carries a measured −0.0155R-per-1%-NQ
slope, so a FAIL "cannot separate 'no edge' from 'edge, wrong regime'". It
does not kill the population; it sends it to forward validation with the
regime caveat attached, permanently for this venue.

**One caveat on H5 I want on the record:** closeloc is Law-2 contaminated
(BR-43 — `risk ≈ closeloc × range`, so it is partly the R denominator).
A holdout pass does not clear that. It says the cut generalises; it does
not say the mechanism is behavioural rather than mechanical.

---

# ITEM 2 — THE FLOW RECORDER

**Asked and answered by inspection before touching it, not assumed.**

**What it was logging:** `scripts/htf_flow_recorder.py` called
`htf_ma_level_census.day_rows` with the seven loci — the **15-minute
grammar only**. Its output columns are the level-census schema: no
`next_lvl_R`, no ceiling flags, **no trigger-timeframe field at all**.

**What open-space needs:** `next_lvl_R` undefined, at a **3m or 5m**
trigger. **Neither was present.** Every session recorded so far is
uncontaminated forward data on a grammar that cannot validate the strongest
candidate on the book.

**Fixed and re-certified today.** LTF rows now come from
`htf_ma_ltf_census.day_triggers` (imported, not reimplemented), which
already emits `next_lvl_R` and the ceiling flags through its
`admissibility()` path — parity with the research build is structural
rather than asserted. Replay on 2026-06-03:

```
REPLAY 2026-06-03: 243 triggers across 7 loci
  15m rows 132 | LTF rows 111 ([3, 5])
  flow coverage (15m): 100.0% | next_lvl_R coverage (LTF): 100.0%
  OPEN-SPACE rows today: 14
  bbma15 rows checked vs M-TABLE: 21 | PARITY PASS
```

The 15m parity gate against the M-TABLE still passes, so the existing
stream is unchanged. LTF rows carry **no flow features yet** and say so on
the row (`has_flow: false`) rather than leaving it inferred from a missing
key. The certification gate now requires both streams.

**Deploying it to the VPS remains your action, not one I can perform.**

---

# ITEM 3 — CONVICTION SIZING ON OPEN-SPACE (report-only)

**Open-space is binary**, so there is no 3+ tier ladder and the Phase-2
precondition does not apply — this is a single multiplier on a binary
condition, a weaker object, and it is not claimed otherwise.

## Law 7 arithmetic, from the real loss distribution

| | 3m | 5m |
|---|---|---|
| stream R/day contribution | +0.452 (base book +0.813) | +0.471 |
| days the stream lost | 24 of 292 (8.2%) | 24 of 292 (8.2%) |
| its loss days: mean / worst | −1.048R / −2.110R | −0.936R / −4.071R |
| **contribution to the book's worst day** | **+0.000R** | **+0.000R** |

**That last row is the whole finding.** The book's worst day (−5.413R,
2026-01-08) contains **no open-space trade at all**. The stream's losing
days do not coincide with the book's bad days, which is why size can be
added to it almost for free.

| M | R/day (3m) | worst day | vs base |
|---|---|---|---|
| 1.5 | +1.491 (+17.9%) | −5.413R | **+0.0% deeper** |
| 2.0 | +1.718 (+35.8%) | −5.576R | +3.0% deeper |
| 3.0 | +2.170 (+71.5%) | −7.089R | +31.0% deeper |

## The sweep, and the only fair comparison

Raising M raises R/day *and* eventually deepens the worst day, which cuts
the max non-breaching size. **$/day = R/day × max size** holds both ends.

| | M=1.0 | M=1.25 | M=1.5 | **M=2.0** | M=2.5 | M=3.0 |
|---|---|---|---|---|---|---|
| 3m $/day | $443 | $482 | $522 | **$601** | $583 | $542 |
| 5m $/day | $449 | $491 | $532 | **$614** | $597 | $557 |

**M = 2.0 is the peak on both timeframes, and it is a genuine interior
optimum** — not a sweep edge. Below it, size is unconstrained and R/day
rises linearly; above it, the worst day starts to bite and max size falls
from $350 to $300 to $250 faster than R/day grows.

At M=2.0, 5m: R/day **1.755**, worst day −5.63R, max size still **$350**,
graduation **100.0%**, live **$38,293**.

**Nothing is adopted.** This is a fit-side optimisation on a binary
condition whose own out-of-sample status is untested — and the venue that
could have tested it has now been spent on other claims.

---

## STANDING AFTER THIS

- **Holdout look #1 is spent.** No further contact. H1 void, H2/H3 fail,
  H4 not evaluable, H5 pass.
- **The bar-only venue is gone.** Anything else bar-only — including
  open-space — now has only forward validation available. That is precisely
  why item 2 mattered today.
- Flow venue unspent. New York untouched.
