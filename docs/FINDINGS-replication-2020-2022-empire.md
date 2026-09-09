# FINDINGS — the full empire replicated on 2020–2022 (2026-09-03)

The 2020–22 holdout (`docs/FINDINGS-holdout-2020-2022.md`) tested **one**
book: prior-day value area, frozen constants. Everything else the program
ships — the other four level families, both VWAP books, the rails, and
**arming** — was validated on 2023–26 only. This run closes that gap.

**This is a replication check, not a holdout.** The 2020–22 value-area
result had already been read when this was run, so it cannot be evidence
against overfitting. It answers a narrower question: *do the extra books
and arming behave the same way in a crash year and a bear market?*

## 0. What had to be built, and the identity receipt

`vwap_revolve.py` had no way to price a tape other than the 2023–26
master — it called `OB.get_bars()` directly. Three changes:

- `--instrument`, reading bars / roll days / tick / stop floor from the
  **level engine's own `INSTRUMENTS` table**, so the two books cannot
  drift apart on constants.
- the `--dedupe` (G4) path now names the same tape *and* the same news
  setting as the run, instead of a hard-coded 2023-26 filename.
- `--no-news-gate`, which stamps the output filename. See §1.

**Identity receipt:** re-running the certified 2023–26 NY VWAP book after
the patch reproduces the pre-patch dump at **280,016 lines, 0 differing**.
The patch adds paths; it changes nothing that shipped.

## 1. The one real difference: no news gate

`data/reference/news_archive.csv` starts 2023-01-04. **Zero** of its 172
high-impact dates fall in 2020–22, so G8 cannot be applied to this tape
at all. Every output here is stamped `ng0`.

Size of the difference: on 2023–26 the gate is a wash on totals (§19,
+1,131R → +1,133R) and removes 191 sim-*positive* trades purely to delete
untrustworthy news-candle fills. So this is worth ~nothing in R — but the
comparison is not perfectly like-for-like and 2020–22 does trade through
pre-market prints that 2023–26 sits out. The same gap was present, and
unreported, in the original holdout; corrected there in commit `44fd481`.

## 2. The result

Frozen constants, honest fills, 0.5pt round-trip cost, G3/G5/G6 rails,
roll days excluded. 765 rail-pass days, 2020-01-02 → 2022-12-29.

| | trades | /day | WR | EV/trade | net R | R/day | maxDD | Sharpe | green |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flat (frozen spec) | 52,680 | 68.9 | 65.2% | +0.1348 | +7,101 | +9.28 | **−39.4** | 0.945 | 84% |
| **armed 1R** | 42,839 | 56.0 | 65.5% | **+0.1666** | +7,135 | +9.33 | **−30.1** | 0.962 | 86% |

**36/36 months positive on both books.** Worst month +26.3R flat,
+49.3R armed. By year, flat: 2020 +2,401 / 2021 +1,897 / 2022 +2,803.

G5 (global cap 4) and G6 (same-direction cap 3) **never bound once** in
765 days — the same result as 2023–26, where they bind ~2 days in 948.

## 3. Per book, standalone — the numbers that surprised me

| book | 2020–22 n | EV | 2023–26 n | EV | gap |
|---|---:|---:|---:|---:|---:|
| 8-level | 15,954 | +0.1312 | 23,320 | +0.1395 | −0.008 |
| vwap-session | 24,173 | +0.1184 | 34,100 | +0.1186 | **−0.0002** |
| vwap-ny | 13,900 | +0.1630 | 19,984 | +0.1571 | **+0.006** |

Win rates 65.6% / 64.3% / 66.6% against 66.1% / 64.3% / 66.3%. The
session-VWAP book lands within two ten-thousandths of an R on data from
a different decade, and the NY-anchored book is *better*. The four level
families that were never holdout-tested carry their weight: the 8-level
book earns +0.1312 against the value-area family's own +0.1354.

## 4. Arming: the preregistered rule, re-applied

The 2023–26 adoption rule, unchanged: *scale the armed book so its max
drawdown equals the flat book's, then require ≥ +5% R/day in BOTH
halves.* Split at this sample's own midpoint, 2021-07-01.

| half | flat R/day | armed R/day | armed, dd-matched | lift |
|---|---:|---:|---:|---:|
| IS (382 d) | +8.935 | +8.794 | +11.525 | **+29.0%** |
| OOS (383 d) | +9.629 | +9.858 | +12.920 | **+34.2%** |
| full | +9.282 | +9.327 | +12.224 | +31.7% |

**PASS, in both halves, by six times the bar** — and by a wider margin
than on the data it was derived from (+16–18% there). Raw EV/trade
+23.6%, drawdown −23.7%. Total R is nearly unchanged (+0.5%): arming
trades 19% less for the same money and a quarter less risk, which is the
same shape it showed in 2023–26.

## 5. What does NOT replicate — read this part

**The drawdown is more than twice as deep: −39.4R against −18.1R.**
Sharpe 0.945 against 1.153. Green days 84% against 89%.

Worse, the *mechanism* differs. The published claim on the results page
is that "losses never chain across days, so the max drawdown and the
worst day are the same figure." **That is a 2023–26 fact, not a property
of the strategy.** In 2020–22 they chained:

| | 2022-11-27 | 11-28 | 11-29 | 11-30 |
|---|---:|---:|---:|---:|
| flat | +18.7 | −4.1 | **−24.6** | −10.7 |
| armed | +11.1 | +0.0 | **−21.0** | −9.1 |

A three-day slide into month-end. The worst single day, −24.6R, is
itself worse than anything in the whole 2023–26 sample (−18.1R). Arming
softens it (−21.0R, two days) but does not remove it.

Per-year maxDD, flat: 2020 −14.3 / 2021 −16.6 / **2022 −39.4**. So the
tail is not a COVID artefact — the crash year was the *tamest* of the
three on drawdown. It is a late-2022 event.

**Consequence for position sizing.** `docs/FINDINGS-funded-sim-armed.md`
concludes 16 micros at ≥80% pass odds, computed against the armed book's
−14.0R drawdown. The armed 2020–22 drawdown is −30.1R, **2.2× deeper**.
Carryable size on that tape would be roughly half. The sizing conclusion
should be read as conditioned on the 2023–26 drawdown distribution, and
that distribution is the optimistic one of the two eras measured.

## 6. Verdict

- **The books replicate.** All three, at near-identical per-trade
  expectancy, on data from a different decade. The claim that the grammar
  prices *any* structural reference level survives its first real test.
- **Arming replicates, strongly.** +29% / +34% drawdown-matched, both
  halves. It was found in-sample and it holds out of era.
- **The risk numbers do not replicate.** Drawdown 2.2× deeper, losses
  chain across days, worst day beyond the 2023–26 range. Any statement
  of the form "max drawdown equals worst day" must be scoped to 2023–26,
  and the funded-account sizing needs re-deriving on the union of both
  eras before it is trusted.

Still outstanding: **none of this is out-of-sample**, because the era was
already seen. Arming's real test is 2017–2019, pre-registered before the
pull. That pre-registration is now the next honest step.

Scripts: `scripts/vwap_revolve.py` (patched), `hold_empire.py`,
`hold_verdict.py`. Dumps: `*_nq20a_*` under `output/analysis/`.
