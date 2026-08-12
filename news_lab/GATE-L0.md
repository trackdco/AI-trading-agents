# GATE L0 — event table verdict

Window **2023-01-01 → 2026-01-31** (bar coverage; bars in repo end 2026-01-31).
Seal boundary `NEWSLAB_SEAL_FROM` = **2025-10-01** — Angus's ruling, 12 Aug 2026.
Build: `FRED_API_KEY=… python news_lab/build_l0.py` → `news_lab/output/events.parquet`.

## VERDICT: **PASS**

453 events, 2023-01-03 → 2026-01-30. **444 prints + 9 revision-only.**
Every Tier-1 family is at **100.0%** of adjusted expected — not 95-and-rounded;
every count reconciles exactly, and every deviation from naive cadence is
named and sourced below. Zero duplicate `(family, date)` rows. Zero
`needs_verification` rows on any Tier-1 family.

| family | tier | naive exp | adj | prints | rev-only | % adj | needs_verif | gate |
|---|---|---|---|---|---|---|---|---|
| cpi     | 1 | 37  | 36  | 36  | 2 | 100.0 | 0  | **PASS** |
| nfp     | 1 | 37  | 36  | 36  | 1 | 100.0 | 0  | **PASS** |
| fomc    | 1 | 25  | 25  | 25  | 0 | 100.0 | 0  | **PASS** |
| ppi     | 1 | 37  | 36  | 36  | 2 | 100.0 | 0  | **PASS** |
| pce     | 1 | 37  | 35  | 35  | 1 | 100.0 | 0  | **PASS** |
| claims  | 2 | 161 | 154 | 154 | 0 | 100.0 | 0  | PASS |
| ism_mfg | 2 | 37  | 37  | 37  | 0 | 100.0 | 37 | PASS (rule) |
| ism_svc | 2 | 37  | 37  | 37  | 0 | 100.0 | 37 | PASS (rule) |
| retail  | 2 | 37  | 36  | 36  | 3 | 100.0 | 0  | PASS |
| gdp_adv | 2 | 13  | 12  | 12  | 0 | 100.0 | 0  | PASS |

Discovery-visible (unsealed) Tier-1 prints: **154**. Sealed rows: 38.

---

## 1. The two rulings that shaped the count

**An event is a NEWS RELEASE, not a data point.** When BLS published October
and November CPI together on 2025-12-18, that is *one* tradeable event, not
two. The naive-vs-adjusted column is entirely this distinction, and each
adjustment is evidenced by FRED `output_type=4` (which release date first
printed which reference period) cross-checked against the official notices.

**A revision-only release is not a red-folder event.** Nine dates on the
official calendars publish no new reference period: the February CPI/PPI
seasonal-factor recalculations (2023-02-10, 2024-02-09, 2023-02-14,
2024-02-14), the late-April Census retail benchmark (2023-04-24, 2024-04-23,
2025-04-25), 2024-01-10 (nfp) and 2025-12-23 (pce). They are real releases, so
they are kept and tagged `release_kind="revision_only"` rather than deleted —
but they carry no consensus and no surprise, and counting them toward coverage
would have inflated cpi to 102.7% by lying to the gate.

## 2. Every deviation from naive cadence, explained

| family | Δ | kind | evidence |
|---|---|---|---|
| cpi | −1 | folded | Oct+Nov 2025 both first-printed 2025-12-18. **Oct-2025 CPI was CANCELLED outright** — data never collected during the 43-day shutdown. |
| nfp | −1 | folded | Oct+Nov 2025 both first-printed 2025-12-16. **Oct-2025 Employment Situation CANCELLED**; the household survey was never collected and never will be. |
| ppi | −1 | folded | Oct+Nov 2025 both first-printed 2026-01-14. Oct-2025 PPI cancelled, folded into Nov. |
| pce | −2 | folded + window edge | Oct+Nov 2025 both first-printed 2026-01-22; Dec-2025 PCE fell after 2026-01-31 on BEA's post-shutdown backlog. |
| retail | −1 | window edge | Last in-window release 2026-01-14 covers Nov-2025. |
| gdp_adv | −1 | window edge | BEA **cancelled the Q3-2025 advance estimate outright**, issuing an initial estimate 2025-12-23 instead; that shifted the cadence right and pushed the Q4 advance past the window. |
| claims | −7 | suspended | DOL suspended the national release for the shutdown, 2025-10-02 → 2025-11-13; resumed 2025-11-20. |

Sources: [BLS revised release dates](https://www.bls.gov/bls/2025-lapse-revised-release-dates.htm),
[BEA schedule updates](https://bea.gov/news/blog/2025-11-24/economic-release-schedule-updates),
DOL probe (404 across the whole span).

## 3. Sources — what each family's dates actually come from

**fomc — federalreserve.gov calendar.** The parser reads the *statement URL*
(`monetaryYYYYMMDDa`), so the decision date is the lookup key itself; no
day-range text like "31-1" is ever interpreted. 25 decisions (8 in each of
2023–25, plus 2026-01-28) and 12 SEP meetings (4/yr). **All 25 dates and all
25 SEP flags independently confirm the hand-entered `FOMC_DECISIONS` seeds** —
the seeds are verified, not assumed.

> **Anomaly — 2025-08-22.** Carries the same `monetary20250822a` URL shape as a
> real decision but is a **notation vote** publishing the Statement on
> Longer-Run Goals, with no 14:00 statement. Excluded by the parser; correctly
> absent from the seeds. Regression-tested.

**claims — oui.doleta.gov press probe.** The filename *is* the release date
(`press/<yyyy>/<mmddyy>.pdf`), so a HEAD probe is an existence oracle: 200
means it published that day, 404 means it did not. Every weekday in the window
was probed (810 requests, 0 errors). Nothing transcribed, no rule applied —
holiday shifts resolve themselves. 147 Thursdays + 7 Wednesdays.

**cpi/ppi/nfp/pce/retail/gdp_adv — FRED release dates.** Release ids are
resolved **by name** and asserted (`Consumer Price Index`→10, `Producer Price
Index`→46, `Employment Situation`→50, `Personal Income and Outlays`→54,
`Advance Monthly Sales…`→9, `Gross Domestic Product`→53), so a rename fails
loudly instead of silently pulling the wrong release. Same house as ALFRED, so
L0 dates and L0b first prints share one source of truth.

For `gdp_adv` the first-print test is what **isolates the advance estimate**:
FRED bundles advance/second/third under release 53, and only the advance is a
first print. That resolved the flag rather than carrying it forward.

## 4. All 8 non-Thursday claims releases, explained

Each is the Wednesday before a Thursday the federal government was closed:

| release | replaced | reason |
|---|---|---|
| 2023-11-22 | 2023-11-23 | Thanksgiving |
| 2024-07-03 | 2024-07-04 | Independence Day |
| 2024-11-27 | 2024-11-28 | Thanksgiving |
| **2025-01-08** | **2025-01-09** | **National Day of Mourning, President Carter** |
| 2025-06-18 | 2025-06-19 | Juneteenth |
| 2025-11-26 | 2025-11-27 | Thanksgiving |
| 2025-12-24 | 2025-12-25 | Christmas |
| 2025-12-31 | 2026-01-01 | New Year's Day |

2025-01-09 is the one that justifies the method. The Day of Mourning was a
one-off executive-order closure and appears in **no** federal holiday
calendar, so the shipped Thursday rule could not have flagged it — and neither
could a holiday-aware rule. Only probing the source finds it.

## 5. Release times — one correction

`config.RELEASES` holds each family's standard time, but a release displaced by
a shutdown can move, and **a bar stamped 08:30 that actually printed at 10:00
would silently corrupt the entire L1 census.**

- **pce 2025-12-05 → 10:00 ET**, not 08:30. BEA's own news release:
  *"EMBARGOED UNTIL RELEASE AT 10:00 a.m. EST, Friday, December 5, 2025"*.
  Applied via `RELEASE_TIME_OVERRIDES`, which raises if an entry ever stops
  matching a row.
- **Every revised BLS date kept 8:30 a.m. ET** — checked against the BLS
  revised-dates page, not assumed. No BLS override needed.

Final distribution: 353 @ 08:30, 75 @ 10:00 (74 ISM + the PCE correction),
25 @ 14:00 (FOMC).

## 6. ISM — the one thing still flagged

74 rows on the 1st/3rd federal business day, 10:00 ET, **all still
`needs_verification=True`**, deliberately.

ISM is a private body. `ismworld.org` 302-redirects its report pages to
`ecommerce.ismworld.org/SSO/Login.aspx` and gates the rest behind reCAPTCHA;
ISM series were withdrawn from FRED years ago over licensing. **There is no
official source reachable by any route available here**, so these rows stay
flagged rather than quietly blessed. Tier-2, so the gate is unaffected.

Resolution path, already the design (README known-gap #3): ISM dates and values
arrive at **L0b** from the consensus-calendar scrape, which carries its own
timestamp per row. The flag clears there, against that source.

> **Bug found and fixed.** The shipped rule used `pd.bdate_range`, which is
> weekday-only and counts federal holidays as business days. It placed ISM
> Manufacturing on **New Year's Day in both 2024 and 2025** and was wrong on
> **14 of 74 rows (19%)**. Now uses a federal-holiday business calendar.

## 7. Bugs found and fixed

All found against live pages, not by inspection:

1. **BLS schedule URL dead.** `schedule/news_release/{year}_sched.htm` 404s;
   BLS publishes per-month pages now.
2. **BLS block vs layout change conflated.** A 403 bot-block and a redesign
   need different remedies → `BLSBlocked` is a distinct exception.
3. **BEA parser could never return a row.** Its date cell is `August 26` with
   no year, so the `Month D, YYYY` regex matched nothing and it raised on
   *every* call. Years now reconstructed by walking months forward.
4. **BEA family matching broken.** Titles read `GDP (Advance Estimate)`, so the
   `"Gross Domestic Product" and "Advance"` test could never fire. Retail is
   Census and never appears on the BEA schedule at all.
5. **ISM holiday bug** (§6).

Also corrected: BEA's schedule page is **forward-looking only** (today it
starts at 2026-08-26), so it is not a historical source for this window —
`pce`/`gdp_adv` history comes from FRED.

**Tests: 7 pass** — the 3 shipped (census math, `causal_z` lookahead gate,
Wilson) plus 4 new L0 regressions covering the notation vote, the ISM holiday
rule, and raise-don't-return-empty.

## 8. Rulings recorded (12 Aug 2026)

- **Seal**: `NEWSLAB_SEAL_FROM = 2025-10-01`.
- **FOMC surprise**: **out of L3 entirely.** FOMC rows stay in the event table
  and the L1 reaction census, carry no surprise, and never enter the direction
  test.

## 9. Carried forward — read before L0b/L3

1. **The sealed era is not a clean holdout.** Seal 2025-10-01 opens directly
   into the shutdown: its first six weeks contain no claims events at all, the
   Oct-2025 CPI and Employment Situation releases **do not exist**, and the
   Q3-2025 GDP advance was cancelled. Only 38 of 453 events are sealed. Worth
   re-ruling before PREREG-L3 is frozen — a holdout this thin and this weird
   will struggle to confirm or refute anything.
2. **Two reference months in one print** (cpi 2025-12-18, ppi 2026-01-14,
   nfp 2025-12-16, pce 2026-01-22). At L0b the surprise for these is ambiguous:
   consensus was quoted per-month, but the market traded one combined event.
   Needs a ruling — suggest scoring against the *later* month's consensus and
   tagging the row, but that is Angus's call.
3. **`revision_only` rows must be excluded from L1/L3** unless deliberately
   studied. They are tagged, not deleted; the filter is `release_kind ==
   "print"`.
4. **Core-PPI FRED id is still TO-VERIFY** in `config.py` (README gap #2).
   Headline `PPIFIS` is confirmed; core is not, and must not be guessed.
5. **The 2026 lapse** moved Feb-2026 BLS releases (CPI 02-11→02-13, PPI
   02-12→02-27, Employment Situation 02-06→02-11). Outside this window, but it
   matters the moment the Feb–Jul 2026 bar top-up lands.
