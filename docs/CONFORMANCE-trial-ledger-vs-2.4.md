# Conformance — trial ledger vs `VALIDATION-PROCESS.md` §2.4

**For Angus.** What the implementation does, what it does not, and the one missing artifact
that blocks three mandated checks at once.

Coordination points from ANGUS 2026-08-05 are implemented: candidate write-ups to
`research/candidates/`, transcripts to `research/transcripts/`, **ledgers merged**.

---

## Merged, not per-programme — my earlier advice was wrong

I had told Brake that London and NY should deflate independently. **That is wrong**, and
Angus's instruction is right. Whatever goes live is selected from the pool of everything
tested, so the go-live bar must see the whole pool — and two researchers on one session
double the search without doubling any single ledger.

`programme` and `researcher` are now scope tags for slicing only. **They are never applied
as filters before deflation.** `deflation_bar()` uses the merged ledger by default and any
narrowing must be passed explicitly and justified on the verdict.

Angus's arms merge by appending rows with `researcher="angus"`. Nothing else changes.

## What conforms

| §2.4 requirement | status |
|---|---|
| Ledger is mandatory, records **everything** including abandoned arms | ✅ 34 rows, matching the declared count |
| DSR via the **variance-of-Sharpes** form, not nominal counting | ✅ `expected_max_sharpe(N, V)` with V from recorded effects |
| PSR / DSR / expected-max-Sharpe maths | ✅ `src/validation/dsr.py`, 26 tests |
| PBO via CSCV | ✅ implemented, `src/validation/pbo.py` |
| Search-program audit — "is the BEST of everything we searched distinguishable from noise?" | ⚠️ in spirit (`london_programme_grade.py`), not SPA proper |

## Gap 1 — effective-N is an approximation, and it is a dangerous one

§2.4 mandates deflating nominal N to **effective** independent trials. The canon
(`quant-math-canon.md` §1.6) is specific: *cluster the trial return series (ONC) and use
the number of clusters as effective N, with V computed across cluster representatives.*

**The ledger stores summary statistics, not return series, so it cannot cluster on series.**
`cluster` currently defaults to `family` — arms inside one prereg treated as one search.

**This is not a harmless approximation:**

| | bar | best observed (+0.1608) |
|---|---|---|
| nominal N = 34 | **+0.1724** | **fails** |
| family-clustered N = 7 | **+0.1126** | **clears** |

A crude clustering choice flips the programme's best result from *below the luck bar* to
*above it*. `n_effective()` carries that warning in its docstring and `summary()` prints it
next to the number. **Nothing may be promoted on the effective-N bar until series-based
clustering exists.**

## Gap 2 — PBO has never been run on the London programme

PBO is implemented and calibrated, but CSCV needs a **T × N trial-returns matrix**. The
verdicts published summary statistics only, so no matrix exists and PBO was never computed
for any of the nine candidates. The §2.4 bar (PBO ≤ 0.25 pass, 0.25–0.50 inconclusive,
≥ 0.50 condemns the *selection procedure*) has therefore not been applied.

## Gap 3 — one error philosophy was used, not two

§2.4 mandates a **two-tier gate policy**: Benjamini–Hochberg FDR (q = 0.10) at the
discover→validate promotion, family-wise-grade evidence at validate→holdout→live.

Every London verdict used **Holm–Bonferroni (FWER) throughout**. That is the *stricter*
error philosophy applied at both gates — conservative rather than permissive, so no result
was wrongly promoted. But it costs power at the discovery gate, which is exactly what the
two-tier policy exists to preserve. Verdicts should also **state which philosophy applies**,
and none did.

## The single root cause

Gaps 1, 2 and 3's first half all reduce to one missing artifact: **the ledger records
summary statistics, not per-trial return series.**

Recording, per trial, the vector of per-event outcomes would unlock all three at once —
ONC clustering for honest effective-N, the CSCV matrix for PBO, and a proper SPA/Reality
Check family audit with a stationary bootstrap.

**Recommendation: add a `series_path` column and have every census write its per-event
outcome vector to `output/trials/{family}_{trial}_{era}.parquet`.** Cheap at write time,
and it is the difference between a ledger that counts trials and one that can actually
deflate them.

Until then the honest position is: **use nominal N, state that effective-N is unavailable,
and treat the DSR grade as conservative.**

## What this does not change

Nothing above alters any of the nine verdicts. All nine failed, were inconclusive, or were
untestable, and every one of those calls rests on its own pre-registered decision rule
rather than on a DSR bar. The gaps here would matter the moment something **passes** — which
is precisely when they must already be closed.
