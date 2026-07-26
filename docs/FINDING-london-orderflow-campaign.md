# FINDING — the London 10:00–13:00 order-flow campaign: no check survives (26 Jul 2026)

**TL;DR.** Six workflows, 25 miners, **~3,300 variables** mined for Angus-style binary checks on
the London 10–13 UK book. **Zero survive their own family's multiplicity null.** One check (PBAL)
clears its family's null but not a campaign-wide one. Along the way the campaign found two
lookahead bugs in shipped code, and an out-of-sample test showing the **base setup itself loses**.
Nothing here should be sized on.

---

## 1. Result by family

| family | variables tried | best lift | its own best-of-N null (median) | verdict |
|---|---|---|---|---|
| depth (MBP-10) | ~240 | +1.71 | — | none |
| tape (aggressor delta) | 482 | +2.03 (ABSORB) | **+1.68** | none, p=0.075 |
| footprint (per-price) | 1,405 | +1.37 | **+1.88** | none, **p=1.00** |
| geometry (ROOM/VWAP/gates) | 1,711 | +2.21 (GEOM-BAND) | **+1.87** | none — **inverts OOS** |
| context (news/pre-window/regime) | 104 | **+2.20 (PBAL)** | +1.50 (q95 +2.02) | clears family null only |
| price action (bar/profile/path) | 554 | +1.53 | **+1.535** | none |

The footprint line is the cleanest: searching 1,405 ways on 65 signals, the *expected* best find
under a null where the tape carries **zero** information is **+1.88R**. They found **+1.37R** —
below the null **median**, p = 1.0000. Every one of the eighteen.

## 2. Four method findings that invalidate parts of the protocol

**Sign-stability is a coin flip.** Under the pure null, **50%** of variants pass "same lift sign
in H1 and H2" (tape: 44% observed vs 50% null). An earlier negative control found
P(stable | p<0.05) = **0.97**. This gate rejects almost nothing and was over-weighted throughout.

**Score ladders are produced more strongly by noise.** Best 3-check score spread on real data
**+3.20** vs null median **+3.50** for the same pipeline — **p = 0.943**. A monotone ladder that
holds in the held-out half is reproduced *more strongly by shuffled outcomes 94% of the time*.

**The January 2026 CVD gap is biased, not merely missing.** `footprint_q4_2025` ends 2026-01-01,
`footprint_feb_mar2026` starts 2026-02-01. Five signals affected (2026-01-13 ×1, 2026-01-29 ×4).
**All five are losers. All five sit in H2.** So H2 baseline avgR reads **+1.168 against a true
+0.867**, and "count uncomputable rows as FAIL" is *anti*-conservative — it gifts five guaranteed
losers to every fail bucket, worth +0.12 to +0.32R of fake lift per check.

**Signals cluster in days.** 65–70 signals sit on 39–41 days; **81.5% of R variance is
between-day** and same-day pairs agree on win/loss 75% of the time. Effective n is ~40, not ~70.
Collapsed to one row per day, only two checks in the whole tape family clear a clustered t of 2.

## 3. The falsifiers fired

- **Direction-blind beats direction-aware.** A footprint activity count that *discards the trade
  direction entirely* read as well as or better than every direction-aware check.
- **No tape at all beats the tape.** From a control bank of 1-minute OHLCV only: *30-minute bar
  volume above the H1 80th percentile — n=17, WR 82%, avgR +2.28 vs +0.56, lift +1.71R*, stable
  across windows. That beats every published footprint check, from ~300 rules instead of 1,405,
  using a column off a bar chart. **5.3M rows/quarter of per-price, per-aggressor, trade-counted
  footprint adds nothing over the volume column.** (Also below the null median, so not proposed.)
- **A placebo window is as strong as the real one.** ABSORB computed on the 15-minute bar **30
  minutes earlier** — no relationship to the signal — gives lift **−1.603**, sign-stable in both
  halves (H1 −1.58, H2 −1.59). If an arbitrary window throws ±1.5R sign-stable, +2.03R at the
  real window is not evidence.

## 4. Angus's checks do not port, for structural reasons

| check | result |
|---|---|
| **W** (no wall behind) | 0/67 fire — his 08:00–10:00 CSVs dropped empty levels; these don't |
| **FAR** (wall ahead > 4.5pt) | 0/67 — max observed ahead-distance is **3.25pt** |
| **WALLONSTOP** | 0/67 at every width |
| **ROOM** | **inverts** — more overnight room is *worse* (−0.685R) |
| **F** (fill-bar delta confirms) | F_SIGN1 lift −0.22, sign-unstable |

The reason is one number: **the entire 20-level NQ book spans a median 5.5 points** (max 8.75).
Stops are 5–70 points. **The visible book never reaches the stop or the target.** MBP-10 cannot
see the levels that decide these trades. This is a data-depth limit, not a tuning problem.

## 5. PBAL — the one that came closest, and why it still isn't enough

`PASS if mean|book imbalance| over the 120 snapshots of 08:00–09:59 UK ≤ 0.1056`
(unsigned; low = the pre-window book stayed genuinely two-sided).

For it: 24 signals / 14 days, **83% vs 28% WR**, lift +2.20R, H1 +2.02 → H2 **+2.45** (strengthens),
day-level permutation p=0.013 on 41 days, day-bootstrap CI **[+0.36, +2.66]**, threshold on a
**plateau** (q20–q67 all positive), reproduced independently from the raw wide CSVs, and
structurally lookahead-proof (last snapshot 09:59, earliest fill 10:00; reads sizes only, so the
contract roll cannot touch it).

Against it: it cleared a **best-of-104/239** null (FWER p 0.004–0.008), but the campaign searched
**~3,300** variables. Against a best-of-1,405 null (median +1.88, p99 +2.42) — still conservative
— +2.20R is roughly **p ≈ 0.10–0.15**, not 0.004. Its evidence base is **14 days**. And depth
begins 2025-06-02, so it **can never be validated out-of-sample**.

**It is the best-supported check in the campaign and it is also permanently unfalsifiable.**

## 6. What outranks all of it

`scripts/london_holdout_2023.py`. The book was built on 2025-07 → 2026-07; bars go back to
2023-01 and the entry geometry needs neither CVD nor depth, so the pre-sample is a true holdout.

| window | n | days | WR | netR | $@300 | maxDD |
|---|---|---|---|---|---|---|
| in-sample (book C) | 41 | 41 | 49% | +38.15 | +$11,445 | $1,256 |
| **HOLDOUT (book C)** | 120 | 120 | **20%** | **−27.49** | −$8,248 | **$13,480** |

Per half-year on book C: 2023H1 +4.21, 2023H2 −7.23, **2024H1 −27.00 at a 3% win rate**,
2024H2 −3.48, 2025H1 +6.00, then 2025H2 +11.48 and 2026H1 +28.69. **The measured edge is confined
to the twelve months the book was built on.** Holdout drawdown is $13,480 against a $2,000
trailing limit — the account blows several times over.

A conviction ladder grades trades *within* a setup. It cannot manufacture an edge the setup does
not have.

## 7. Two bugs found and fixed

- **Day-stop lookahead** (`london_daystop_lookahead.py`): the published book declined trades using
  a prior trade's *final net* while that trade was still open. 55 trades → **41**.
- **CVD-confirm lookahead** (`london_cvd_lookahead.py`): `em = uts[i+1]` is the next bar's *close*,
  the fill is its *open*, so the "3-minute pre-entry delta" read **13–15 min after the fill**.
  Honest flag: 49% vs 46% WR, p=0.666. Fixed in ten scripts; §3 of the trade plan voided.

## 8. Recommendation

**Stop mining these 65–70 rows.** Five independent search programs have now spent the sample; the
best-of-k nulls say another pass manufactures ~+1.9R of "edge" for free.

Three things have positive expected information, in order:

1. **Establish whether the base setup has any cross-regime edge at all.** That is answerable on
   bars alone over 275 signals since 2023, and it is the only question that matters.
2. **Backfill January 2026 from Databento.** You are currently validating on an H2 with five
   clustered losers silently deleted.
3. **Widen the trade universe backwards.** The footprint covers from 2025-06-01, but the book was
   cut to 2025-07-01 by the *depth* file span — and none of the tape checks need depth.

**Nothing in this campaign should be sized on today.**
