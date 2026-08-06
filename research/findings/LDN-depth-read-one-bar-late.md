---
date: 2026-08-05
status: FINDING — the London depth read is one bar late. Affects LDN-CAN-01 L3 AND the shipped London canon book.
tags: [london, canon, depth, lookahead, self-correction]
sources: ["output/l3_london_trial.md", "scripts/london_depth.py", "output/london_matrix.parquet"]
---

# The London depth features read the book at the END of the fill bar

## What is wrong

`scripts/london_depth.py` line 101:

```python
f = pd.Timestamp(t.fill).tz_convert(NY).floor("min")
rows.append(depth_at(dep, f, t.entry, t.direction))
```

`depth_at` takes the newest snapshot with `ts <= f`. Three facts, each measured rather
than assumed:

1. **The condensed London MBP-10 carries one snapshot per minute, stamped on the minute
   boundary, and it is an INSTANTANEOUS book at that instant.** Verified against
   close-labeled 1-minute bars on 2025-06-10: depth mid at T vs close of bar T gives a
   median error of **0.25 pt with 96% inside 1 pt**; against the open of bar T it is
   3.62 pt, and against the close of bar T+1 it is 3.75 pt. One tick. It is the book at T.

2. **Engine bars are CLOSE-labeled** (`src/engine/triggers.py` docstring: *"engine bars are
   CLOSE-labeled"*). A bar stamped T covers `(T−1min, T]`.

3. **Fills land inside their stamped bar.** On the L2 London outcomes the entry price sits
   inside the bar stamped `fill_ts` on **100.0%** of trades; on the shipped
   `london_matrix.parquet` it is **94.8%**. Every fill stamp is on a minute boundary.

Put together: the fill happened somewhere inside `(T−1min, T]`, and the book being read is
the one at instant **T** — the end of that window. **The depth is read at or after the
fill, not before it.**

The causal book is the one at **T−1min**: the state at the *start* of the bar the fill
occurred in.

## What it is worth

`vs_first` population, 1,239 trades, no risk gate, no caps:

| check | book | n pass | WR pass | WR fail | gap | 2025 | 2026 |
|---|---|---:|---:|---:|---:|---:|---:|
| `W` | fill-bar CLOSE (as shipped) | 250 | 42.8% | 23.8% | **+19.0pp** | +20.4pp | +18.0pp |
| `W` | **fill-bar OPEN (causal)** | 541 | 32.9% | 23.5% | **+9.4pp** | +13.1pp | **+4.1pp** |
| `FAR` | fill-bar CLOSE (as shipped) | 189 | 45.0% | 24.5% | **+20.5pp** | +23.2pp | +18.4pp |
| `FAR` | **fill-bar OPEN (causal)** | 339 | 32.2% | 25.9% | **+6.3pp** | +11.2pp | **+0.6pp** |

**`W` loses half its edge. `FAR` loses two thirds, and its 2026 edge goes to +0.6pp —
nothing.**

## This is NYA-LVL-01 again, at one bar's resolution

That family died because `W` was computed from the book at the fill minute, which included
post-entry price action: **+19.5pp → +4.2pp** when recomputed one minute earlier. This is
the same feature, the same failure, the same magnitude — in a different session, in code
written by someone else, months earlier.

The standing check adopted from that kill is what caught it: *any depth feature whose lift
exceeds the baseline by more than ~5pp is recomputed one bar earlier BEFORE it is
reported.* It was built into the L3 trial harness as an automatic column, so it fired on
the first run rather than after someone got suspicious.

## My own error inside this, stated plainly

Hours before this, I checked the depth timestamps, confirmed the snapshot is instantaneous
at T, and told Angus **the shipped London book was clean on this axis**. That was wrong.
I verified the snapshot semantics correctly and then got the *fill* timing backwards — I
assumed the fill happened after its stamp when close-labeling means it happened before.

I even wrote the conclusion into a commit message: *"reading at T is causal — and so is
the shipped London canon, which reads the same way."* The second half of that sentence is
true and the first half is false, which makes the whole claim exactly backwards.

**The lesson is not "check the data".** I did check the data. The lesson is that a
causality argument has two ends — when the feature is observed, and when the decision is
made — and I verified one end and assumed the other. Both ends need a measurement.

## Consequences

**For `LDN-CAN-01`:** the L3 default depth read moves to the `p1_*` (fill-bar open)
columns. Every depth number reported before this correction is withdrawn. No promotion had
occurred, so nothing downstream is contaminated.

**For the shipped London canon — this is the part that matters.**
`scripts/london_canon.py` advertises 2025 +$22,219 / 2026 +$13,000 at PF 3.3/2.4, on a
Layer-1 built from four checks of which **`W` and `FAR` are two**. Both are computed by
`london_depth.py` at the fill-bar close. On this evidence their contribution is roughly
half to one third of what the book's calibration credits them with, and `FAR` has
essentially no 2026 edge once read causally.

`docs/CANON.md` already calls that book *"a reference to beat, not a book to trade"*, and
`docs/HANDOFF-london-rebuild.md` was written precisely because *"its checks were never
honestly trialed"*. **This is what that distrust was for.** It is not trading, so nothing
live is exposed — but any decision that leans on those numbers should stop leaning.

**Not affected:** the NY canon. `scripts/trade_matrix.depth_at` is a separate call path on
separate data and has not been checked here. **That check is now owed** and should not be
assumed either way — assuming is what produced this finding.

## What is NOT claimed

That `W` and `FAR` are worthless. Read causally they are still **+9.4pp** and **+6.3pp**
against a 27.6% baseline, era-consistent in sign. That is a real residual and it is the
honest starting point for L3. It is simply not the +19/+20pp that was on the page.

---

## THE NY CANON HAS THE SAME BACKTEST READ — checked, not assumed (2026-08-05)

The finding above flagged this as owed. It is now measured, on the same three tests:

1. **NY depth is the same shape.** `data/reference/depth_2025/*_ny.csv`: one snapshot per
   minute, 0.0% off the minute boundary, and instantaneous at T — depth mid vs close of
   bar T gives median error **0.25 pt, 96% within 1 pt**; vs the open of bar T, 2.88 pt.
2. **NY fills land inside their stamped bar.** `output/canon_book.parquet`, 713 trades:
   every fill stamp on a minute boundary, entry inside the bar stamped `fill` on
   **95.8%**.
3. **The backtest reads at that stamp.** `scripts/score_canon_span.py:196` —
   `depth_at(dep_cache[day], fill, entry, direction)`.

**So the NY canon's depth features are computed from the book at the fill bar's CLOSE,
at or after the fill. Same defect, same call, different session.**

### But the LIVE bot is honest — and this distinction is the whole finding

`src/canon/ingestor.py:150-153`:

```python
book = pd.DataFrame(self.book.long_form())
if not book.empty:
    book["ts"] = fill                        # current snapshot is as-of the fill
    f.update(depth_at(book, fill, entry, direction))
```

Live reads `self.book` — the **actual current order book at the moment of decision**. It
does not and cannot see the rest of the bar. **The live bot is not cheating.**

The asymmetry is one-directional and it is the thing to understand:

| | book used | relative to the fill |
|---|---|---|
| live | the true book at decision time | somewhere inside the fill bar |
| backtest / calibration | the archived snapshot at the bar's close | **at or after** the fill |

The backtest is strictly later than live, therefore strictly better informed, therefore
**optimistic**.

### What that costs, and what it does not

**It does not mean the canon is fake or that live results are misattributed.** It means the
canon's depth thresholds (`Q_WALLSZ_MIN = 7.0`, the `W`/`D` gates) were fitted, and its
expected edge measured, on a feature carrying information the live bot will not have.
§5.12.10 records that **depth carried the canon's entire edge, +0.5 to +1.3R**, while flow
at entry was a rounding error. That is the number this touches.

For scale, the same correction in London halved `W` (+19.0 → +9.4pp) and took two thirds
off `FAR` (+20.5 → +6.3pp, and its 2026 edge to +0.6pp). Live sits *between* the bar's open
and its close, so the live-realisable share is between those bounds rather than at either —
but it is below the calibrated figure, not above it.

**This is a calibration finding, not a correctness incident.** Nothing in the live path
needs an emergency change. What needs re-running is the measurement of what depth is worth,
against a book read at the fill bar's OPEN — the conservative bound — so the canon's
expected edge is stated on information the bot will actually hold.

### Owed

- Re-run the canon's depth calibration at the fill-bar-open read and restate the depth
  contribution as a range (open-read = floor, close-read = the current, optimistic figure).
- Until that exists, **treat the +0.5 to +1.3R depth attribution in §5.12.10 as an upper
  bound**, not a point estimate.
- This is Angus's call, not a unilateral change to a live-adjacent artifact.
