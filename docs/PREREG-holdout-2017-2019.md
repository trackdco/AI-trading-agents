# PRE-REGISTRATION — the 2017–2019 NQ holdout (written 2026-09-03, before the data exists)

This is the second sealed holdout. The first (`PREREG-holdout-2020-2022.md`)
declared **one** configuration and so certified only the base grammar; the
8-level book, both VWAP books, the rails, **arming** and conviction sizing were
then *replicated* on 2020–22 (`FINDINGS-replication-2020-2022-empire.md`) but
that era had already been read, so none of them has ever met untouched data.

**This document declares every one of them, with its pass/fail rule, now.**
Once the data is pulled nothing here may be re-chosen. Verdicts are applied
mechanically by `scripts/run_holdout_2017_2019.sh`, which prints them.

## 1. The data

    dataset   GLBX.MDP3
    schema    ohlcv-1m
    symbols   ["NQ.FUT"]        (parent — NOT EURUSD-style; the 6E lesson)
    stype_in  parent
    start     2017-01-01
    end       2020-01-02        (one-day overlap with nq_2020_2022_1m)

Processed by `scripts/build_nq_2017_2019.py`, the same recipe as 2020–22:
calendar spreads dropped (`-` in the mapped symbol), volume-rolled to a
continuous front month by session-day volume, roll session-days excluded,
18:00 ET session anchor.

**Integrity gates — checked before any result is read; any failure voids the
run until fixed and reported:**
- no `:` symbols (EFP/basis contamination)
- price range plausible for NQ 2017–19: low in 4,500–5,500, high in 8,300–9,300
- ≥ 700 session-days survive the engine's completeness filter
- the 2020-01-01/02 overlap matches `nq_2020_2022_1m` bar for bar, or the
  boundary-continuity substitute from Amendment 1 of the first pre-reg
- all roll days fall in Mar / Jun / Sep / Dec

## 2. Gate 0 — the tick screen, measured and declared, not a pass/fail

The ≥20-tick screening law (median active-session 1m candle ≥ 20 ticks) is
what separated NQ (28) and GC (21) from ES (6–7) and 6E (3). NQ 2017–19 traded
at 5,000–9,000 in a low-volatility regime. **It may fail its own screen.**

The runner measures the median active-session 1m candle in ticks **per year**
and prints it before anything else. It is not a gate: the primary tests still
run on the whole period. It exists so the result can be read against a
prediction made now (P1 below) rather than explained after the fact.

## 3. Constants

**Run A — frozen.** floor 5.0, depth 3.0, cap 30.0, bin 1.0. The certified
values, untouched. **Every test in §4 is scored on Run A.**

**Run B — era-scaled**, value-area book only, reported for information and for
P2, exactly the first pre-reg's recipe:

    m_now = median 1m (high−low), full session, 2023-01-03 → 2026-09-02, rolls excluded
    m_era = same over 2017-01-01 → 2019-12-31
    k     = m_era / m_now
    floor = 5.0k   depth = 3.0k   cap = 30.0k   bin = 1.0k

Run B is added as instrument `nq17b` by formula once k is measured. That is a
mechanical step, not a choice.

**No news gate.** `news_archive.csv` starts 2023-01-04. Both eras before that
run without G8, stamped `ng0`. On 2023–26 the gate is worth +2R over four years.

## 4. The tests — all declared now, all scored on Run A

Costs 0.5pt/RT in R, honest fills (one tick through), ambiguity scored as a
loss, G3/G5/G6 rails, roll days excluded — the same code path as every other
result in this program. Split-half at the sample's own midpoint session-day.

**Test A — base grammar** (value-area book alone, the first holdout's cell)
PASS if all three years' net R > 0 AND pooled WR ≥ 60% AND pooled net EV ≥ +0.08R.
*Already passed once on 2020–22. This is a second confirmation, not the point.*

**Test B — the empire** (8-level + session-VWAP + NY-VWAP, railed, flat)
PASS if each of the three books standalone has net EV ≥ +0.08R AND the railed
empire has all three years' net R > 0 AND pooled WR ≥ 60%.
*First untouched-data test of the four extra level families and both VWAP books.*

**Test C — ARMING. The primary verdict of this holdout.**
Scale the armed empire so its max drawdown equals the flat empire's. PASS if
drawdown-matched R/day improves by ≥ +5% vs flat in BOTH halves.
This is the rule arming was adopted under on 2023–26 (+16–18%) and replicated
under on 2020–22 (+29% / +34%). It has never been applied to data nobody read.
*If C fails, arming reverts to "in-sample only" and the results page says so.*

**Test D — conviction sizing** (2:1 on displacement, same rule as C vs flat).
Secondary. Declared so it cannot be quietly dropped if it fails.

**Test E — the loser-autopsy claims** (`FINDINGS-loser-autopsy.md`)
E1 PASS if prior-session volatility quartiles show trades/day top-vs-bottom
   ≥ +25% while EV/trade top-vs-bottom differs by < 0.02R (count, not quality).
E2 PASS if the worst-1% days' mean prior-vol ratio lies within ±0.15 of the
   all-days mean (bad days are not marked in advance).

## 5. Predictions, declared now so they can be scored

P1  At least one of 2017/2018/2019 has a median active-session 1m candle
    **below 20 ticks**, and that year is the weakest of the three on net EV.
P2  Frozen constants (Run A) beat era-scaled (Run B) on net EV, as in 2020–22.
P3  Arming's drawdown-matched lift lands between **+10% and +40%** in both halves.
P4  Max drawdown exceeds the worst single day in at least one year
    (losses chain at least once — the 2022 lesson, not the 2023–26 one).
P5  The 1R target beats every larger target at every depth (fourth instrument
    in a row).
P6  Per-book EV ordering is NY-VWAP > 8-level > session-VWAP, as in both
    prior eras.

## 6. What happens after

The runner prints Gate 0, the integrity gates, Tests A–E and P1–P6 in that
order, mechanically. The findings doc records them as printed. Then 2017–19
is **spent**. If Test C passes, arming is out-of-sample validated and the
results page says so; if it fails, the arming section is re-scoped to
in-sample and stays on the page as a documented failure.

No further NQ history exists on Databento GLBX.MDP3 at 1m before mid-2010s
that this program has budget for; after this, validation is forward time.

---

## Amendment 1 (2026-09-03, written after the file arrived, before it was decompressed)

The delivered pull is `glbx-mdp3-20160902-20200101`, i.e. **2016-09-02 → 2020-01-01**,
wider at the front than the declared 2017-01-01 and one day shorter at the back.

Ruling, fixed now:
- **The scored period is unchanged: 2017-01-01 → 2019-12-31.** Every test in §4
  and every prediction in §5 is computed on trades whose session-day falls in
  that window. The scorer enforces this with a hard `SCORE_FROM` filter.
- **2016-09 → 2016-12 is warmup only** (weekly value-area and 20-day medians
  need history). It is reported as a separate information row, never pooled.
- `m_era` for Run B is measured on 2017–2019 only, as declared.
- The 2020-01-01 overlap day is absent (Databento end is exclusive), so the
  boundary check uses the Amendment-1 substitute from the first pre-reg: a
  clean join (<96h gap, no duplicated minutes) instead of bar-for-bar identity.
- Price-range gate unchanged (low 4,500–5,500; high 8,300–9,300); NQ in Sep 2016
  traded ~4,750, inside it.
