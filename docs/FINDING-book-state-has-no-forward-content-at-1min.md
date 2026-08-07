# FINDING — resting-liquidity state carries no forward content at 1-minute snapshot resolution

**2026-08-06. A finding, not a trial.** No prereg, no charged trial, no rule proposed, no
P&L, no holdout look. Sealed span untouched. This is a **construction** result: it says
what a measurement layer can and cannot support, which is the question that has to be
settled before an edge question is worth asking.

Reproduce: `python -m scripts.book_feature_validation`.

---

## The result

| check | outcome |
|---|---|
| **Positive control** — tape delta (aggressor-tagged, a true flow measure) vs same-minute return | **r = +0.6029**, n = 34,438, null p95 0.0105, **p = 0.000** |
| **Shuffle placebo** — five book-state features vs the forward minute | **all five INSIDE the null.** \|r\| 0.0059–0.0097 against null p95 0.0102–0.0111; p = 0.063–0.262 |
| **Time-shifted placebo** | **all five residual-dominant.** `imb_L10`: −0.1641 against the minute the snapshot sits at the end of, −0.0069 against the next. Ratio 0.04 |
| **Parameter ladder** L1 · L2 · L3 · L5 · L10 | **nothing clears the null at any depth.** −0.0075 / −0.0088 / −0.0060 / −0.0081 / −0.0069 |
| **Era stability** | neither era clears its own null — no sign claim is available in either direction |

Features tested: `imb_L1`, `imb_L3`, `imb_L10`, `press_imb`, `wmid_tilt` — multi-level
depth imbalance, distance-weighted book pressure, and the size-weighted mid's tilt away
from the arithmetic mid. All are pure functions of the book at one instant, which is the
class that survives coarse sampling.

**The positive control is what makes the nulls readable.** A harness that finds nothing
might be broken. This one finds r = +0.60 on the tape in the same join, on the same
minutes, with the same code path — so the nulls are readings, not silence. It also
re-confirms the `B − A` footprint convention a third independent way.

**The features are correctly constructed.** They pass every construction guard in
`tests/test_book_construction.py`: buy-side-positive imbalance matching the footprint
delta convention, cross-weighted mid (a large bid tilts price toward the ask), near size
weighted above far size, bounded imbalance, order-count-derived average size. This is not
a null produced by a broken column. It is a null produced by a correct one.

## What it closes

**It closes the resting-liquidity question that `VERDICT-LDN-DEF-01.md` left open.**

The chain of open questions ran like this, and it is now complete:

1. **LDN-FLOW-01** tested *minute-aggregate* flow and stated its own limit explicitly:
   *"Real absorption reads at a price level within the minute — 400 contracts hitting one
   price that does not move. That signature is invisible at this resolution and is not
   tested here."*
2. **LDN-DEF-01** retired that limit. It read per-(minute, price, aggressor-side)
   footprint — 24.8M rows — and measured absorption at the defended level directly.
   **FAIL on all three measures**, ρ +0.040/−0.144, +0.063/−0.012, +0.037/−0.116,
   AUC 0.451–0.515, on a null of evidence rather than power. What DEF-01 could not speak
   to was **resting** liquidity: it measured what *traded* at the level, not what was
   *showing* on the book.
3. **This finding closes that.** The book state itself — how much is resting, where, how
   lopsided, how the weighted mid leans — carries no measurable forward content at this
   resolution, on 34,800 minutes across 290 sessions, with a working positive control in
   the same harness.

So the order-flow question for the London window is answered in both halves. **Traded
flow at a price level: measured, null (DEF-01). Resting liquidity state: measured, null
(here).** Neither cost a prereg or a charged trial to establish, because neither is a
strategy — they are statements about what the substrate contains.

**What it does NOT close.** The *event-resolution* question is untouched and remains open,
because the data cannot address it (see the purchase scope below). The residual −0.164 is
itself a real and strong relationship — the book at the end of a minute is substantially
determined by that minute's move. That is the post-trade residual, it is memory, and it is
exactly why a snapshot joined to a *past* or *containing* window produces a convincing
result that means nothing.

## What this predicts about future depth work

Any depth-conditioned London result that comes back *strong* at 1-minute resolution should
be treated as a construction defect until proven otherwise, because this measurement says
there is nothing there to find. The two live candidates for such a defect are both now
documented: the post-trade residual (join direction) and the floored timestamp
(`docs/FINDING-london-depth-timestamp-lookahead.md`).

---

## Purchase scope — what would move the BIASED features to VALID

The gap is **resolution, not schema**. Everything below is the same instrument, the same
dataset, the same ten levels already held.

**Specification**

| field | value |
|---|---|
| Vendor / dataset | Databento **GLBX.MDP3** |
| Schema | **`mbp-10`, unsampled (event-level)** — not `mbp-10-1m`, not `bbo-1m`, not `ohlcv-1m` |
| Symbol | `NQ.v.0` (continuous front-month by volume, as the current pull) |
| Window | **08:00–10:00 Europe/London**, extracted in London local time so DST needs no handling downstream — matching the existing 295-day pull exactly |
| Required fields | `ts_event` **unfloored** (this is the whole point), `ts_recv`, `ts_in_delta`, `sequence`, `action`, `side`, `depth`, `price`, `size`, `flags`, and the ten-level ladder including `*_ct_*` |
| Critical acceptance test on delivery | `ts_recv − ts_event` must be **microseconds, not ~60 seconds**. That single check distinguishes a genuine event feed from another floored extraction, and it is the check the current archive fails |

**Span options.** The fit span already has depth (2025-06-02 → 2026-07-22, 295 sessions).
The decision is whether to re-buy it at event resolution, and whether to extend.

| option | span | sessions | note |
|---|---|---|---|
| A — validate the method | one quarter, e.g. 2026-04 → 2026-06 | ~64 | Cheapest way to answer "does event-resolution OFI do anything here at all". If it is null too, stop |
| B — match the fit span | 2025-06-02 → 2026-07-22 | 295 | Enables discover-2025 / validate-2026 and the inverse pass on event-resolution features |
| C — B plus the sealed span | + 128 sealed 2023/24 days | 423 | **Do not buy this without a declared holdout protocol first.** Buying the sealed days at higher resolution does not unseal them, and the temptation to look is the risk |

**Recommendation: A, then B if A is not null.** The prior from this finding is that
instantaneous state is empty at 60s; that says nothing about whether *event-sequenced*
flow is empty, which is a genuinely different question and the one CKS answer positively
at 10-second resolution (R² ≈ 65%).

**Cost.** Event-level MBP-10 on a single CME instrument for a 2-hour daily window is
priced by the volume of book messages, and at a median ~23,654 messages per minute that
is roughly **2.8M messages per session** and **~840M for the 295-session span**. I do not
have Databento's current rate card and will not invent a figure — the shape of the
question is "per-message historical pricing × 840M for option B, or ×180M for option A",
and the quote should be requested against the exact specification table above. Note the
asymmetry recorded in the reference material: aggressor-tagged **trades** are usually far
cheaper than book data, and we already hold those.

**What the purchase would move, and what it would not**

| feature | now | after event-level MBP-10 |
|---|---|---|
| **OFI (level 1)**, Cont-Kukanov-Stoikov | BIASED | **VALID** — per-event contributions become directly computable; the market-sell / cancelled-buy conflation disappears because the events are individually observed |
| **Multi-level OFI (MLOFI)**, Xu-Gould-Howison | BIASED | **VALID** |
| **`dep_thick_d5m`** / net depth change as flow | BIASED | **VALID** as a genuine integrated quantity, though OFI supersedes it |
| Sweep / ordered multi-level consumption | NOT CONSTRUCTIBLE | **VALID** — the ordered event stream is exactly what this needs |
| VPIN | NOT CONSTRUCTIBLE | **VALID** — equal-volume buckets need the trade sequence, which comes with it |
| Depth imbalance, book pressure, weighted mid, microprice | VALID (and null at 60s) | Still VALID, and testable at the resolution where the literature finds them to work |
| **Queue position** | NOT CONSTRUCTIBLE | **STILL NOT CONSTRUCTIBLE** — needs MBO/L3 with order IDs |
| **Order lifetimes, cancel-vs-execution attribution** | NOT CONSTRUCTIBLE | **STILL NOT CONSTRUCTIBLE** — needs L3 |
| **Iceberg / hidden liquidity detection** | NOT CONSTRUCTIBLE | **STILL NOT CONSTRUCTIBLE** — needs L3 + millisecond stamps |

Three features stay out of reach at MBP-10 however finely it is sampled, because they are
properties of individual orders rather than of the aggregated book. Those need L3, which
is a separate and larger purchase, and nothing measured so far argues for it.
