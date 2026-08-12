# GATE L0 — event table verdict

Window **2023-01-01 → 2026-01-31** (bar coverage; bars in repo end 2026-01-31).
Seal boundary `NEWSLAB_SEAL_FROM` = **2025-10-01** — Angus's ruling, 12 Aug 2026.
Build: `python news_lab/build_l0.py` → `news_lab/output/events.parquet`.

## VERDICT: **NOT PASSED — blocked, 4 of 5 Tier-1 families absent**

Two Tier-1 families are closed and pass on their own terms. The other three
(cpi, ppi, nfp) plus pce could not be sourced from this container: every
bls.gov path Akamai-403s the egress IP, BEA's archive is JS-rendered, and the
agreed replacement door (FRED release dates) needs `FRED_API_KEY`, which is
still unset here. **No dates were guessed to fill the hole.** See §7.

| family | tier | expected | got | % | gate ≥95% | needs_verification |
|---|---|---|---|---|---|---|
| fomc    | 1 | 25  | 25  | 100.0 | **PASS** | 0 |
| cpi     | 1 | 37  | 0   | 0.0   | **BLOCKED** | — |
| ppi     | 1 | 37  | 0   | 0.0   | **BLOCKED** | — |
| nfp     | 1 | 37  | 0   | 0.0   | **BLOCKED** | — |
| pce     | 1 | 37  | 0   | 0.0   | **BLOCKED** | — |
| claims  | 2 | 161 | 154 | 95.7  | **PASS** | 0 |
| ism_mfg | 2 | 37  | 37  | 100.0 | PASS (rule) | 37 |
| ism_svc | 2 | 37  | 37  | 100.0 | PASS (rule) | 37 |
| retail  | 2 | 37  | 0   | 0.0   | BLOCKED | — |
| gdp_adv | 2 | 13  | 0   | 0.0   | BLOCKED | — |

Duplicate `(family, date)` rows: **0**.

---

## 1. fomc — PASS, 25/25

Source: `federalreserve.gov/monetarypolicy/fomccalendars.htm`. The parser reads
the **statement URL** (`monetaryYYYYMMDDa`), so the decision date is the key
itself — no day-range text like "31-1" is ever interpreted. SEP meetings are
flagged by the presence of projection materials.

- 8 decisions in each of 2023, 2024, 2025 + 2026-01-28 = **25**.
- **12 SEP meetings** (4 per year, 2023–2025) and 13 non-SEP. Correct.
- All 25 dates and all 25 SEP flags match the hand-entered `FOMC_DECISIONS`
  seeds exactly. The seeds are confirmed, not merely assumed.

**Anomaly — 2025-08-22.** The Fed page carries a row with the same
`monetary20250822a` URL shape as a real decision. It is a **notation vote**
publishing the Statement on Longer-Run Goals and Monetary Policy Strategy, not
a rate decision, and has no 14:00 ET statement. It is excluded by the parser
and correctly absent from the seeds. Regression-tested
(`test_scrape_fomc_excludes_notation_votes_and_flags_sep`).

Out-of-window note: the 2026-09-16 / 2026-10-28 / 2026-12-09 seeds are future
meetings with no statement published yet, so the scraper cannot confirm them.
They fall outside this window and do not affect the gate.

## 2. claims — PASS, 154/161 naive (100% of the 154 that exist)

Source: `oui.doleta.gov/press/<yyyy>/<mmddyy>.pdf`. **The filename is the
release date**, so a HEAD probe is an existence oracle — 200 means ETA
published that day, 404 means it did not. Every weekday in the window was
probed (810 requests, 0 errors). Nothing was transcribed and no rule was
applied, so holiday shifts resolve themselves.

Raw 161 Thursdays → 154 confirmed releases: 147 Thursdays + 7 Wednesdays.
Adjusted for the suspensions below, coverage is **154/154 = 100%**.

### 2a. All 8 non-Thursday releases, explained

Every one is the Wednesday before a Thursday the federal government was shut:

| release | replaced Thursday | reason |
|---|---|---|
| 2023-11-22 | 2023-11-23 | Thanksgiving |
| 2024-07-03 | 2024-07-04 | Independence Day |
| 2024-11-27 | 2024-11-28 | Thanksgiving |
| **2025-01-08** | **2025-01-09** | **National Day of Mourning, President Carter** |
| 2025-06-18 | 2025-06-19 | Juneteenth |
| 2025-11-26 | 2025-11-27 | Thanksgiving |
| 2025-12-24 | 2025-12-25 | Christmas |
| 2025-12-31 | 2026-01-01 | New Year's Day |

2025-01-09 is the one that matters for method: the Day of Mourning was a
one-off executive-order closure and is **not in any federal holiday calendar**,
so the shipped Thursday rule could not have flagged it and a holiday-aware
rule would still have missed it. Only probing the source finds it.

### 2b. The 7 missing weeks, explained

2025-10-02, 10-09, 10-16, 10-23, 10-30, 11-06, 11-13 — a contiguous run.

Cause: the **2025 federal government shutdown** (2025-10-01 → 2025-11-12, 43
days). DOL suspended the national weekly claims news release for its duration;
publication resumed 2025-11-20. These events **did not happen** — they are
correctly absent, not missing data, and must not be back-filled.

Consequence for later layers: this blackout sits **inside the sealed era**
(seal = 2025-10-01). The sealed sample is therefore not a clean holdout —
roughly its first six weeks contain no claims events at all. Flagged for
PREREG-L3.

## 3. ism_mfg / ism_svc — generated, still flagged

37 + 37 rows on the 1st/3rd federal business day, 10:00 ET. **All 74 keep
`needs_verification=True`** and are NOT verified against ISM.

ISM is a private body: `ismworld.org` puts its report pages behind a reCAPTCHA
and a member SSO wall, and ISM series were withdrawn from FRED years ago over
licensing. There is no programmatic official source reachable from here, so
these rows stay flagged rather than being silently blessed.

Resolution path (already the design in README known-gap #3): ISM dates and
values come from the consensus-calendar scrape at **L0b**, which carries its
own timestamp per row. The flag clears there, against that source.

**Bug found and fixed.** The shipped rule used `pd.bdate_range`, which is
weekday-only and treats federal holidays as business days. It placed ISM
Manufacturing on **New Year's Day in both 2024 and 2025**, and was wrong on
**14 of 74 rows (19%)**. The rule now uses a federal-holiday business calendar.
Regression-tested (`test_ism_never_lands_on_a_federal_holiday`).

## 4. Tier-1 `needs_verification` — resolved

Zero unresolved `needs_verification` rows exist for any **closed** Tier-1
family (fomc: 25 rows, all False). The claims family, which the shipped
generator flagged on every holiday week, is now sourced by probe and carries
**0 flagged rows** rather than resolved-by-assertion ones.

Remaining flags in the table are the 74 ISM rows (Tier-2, §3) and, once the
FRED door opens, `gdp_adv` — FRED bundles advance/second/third GDP estimates
under one release id, so those rows will land flagged until the advance print
is isolated. Tier-2, does not gate.

## 5. Bugs found and fixed

All five were found against live pages, not by inspection:

1. **BLS schedule URL dead.** `schedule/news_release/{year}_sched.htm` 404s.
   BLS publishes per-month pages now (`schedule/{year}/{MM}_sched.htm`).
2. **BLS block vs layout change conflated.** A 403 bot-block and a redesign
   need different remedies, so `BLSBlocked` is now a distinct exception.
3. **BEA parser could never return a row.** Its date cell is `August 26` with
   no year, so the `Month D, YYYY` regex matched nothing and the scraper
   raised on every call. Years are now reconstructed by walking months forward.
4. **BEA family matching wrong.** Titles read `GDP (Advance Estimate)`, so the
   `"Gross Domestic Product" and "Advance"` test could never fire. Also,
   retail is Census and never appears on the BEA schedule at all.
5. **ISM holiday bug** (§3).

Also corrected: the BEA schedule page is **forward-looking only** (today it
starts at 2026-08-26), so it is not a historical source for this window at all.

Tests: **7 pass** — the 3 shipped (census math, `causal_z` lookahead gate,
Wilson) plus 4 new L0 regressions.

## 6. Rulings recorded (12 Aug 2026)

- **Seal**: `NEWSLAB_SEAL_FROM = 2025-10-01` (shipped default, now ruled).
  Caveat in §2b: the sealed era opens with the shutdown blackout.
- **FOMC surprise**: **out of L3 entirely.** FOMC rows stay in the event table
  and the L1 reaction census, carry no surprise, and never enter the direction
  test. `config.SURPRISE_TO_NQ_SIGN["fomc"]` is now unused by L3 and left
  in place only for the reaction lane.

## 7. What is blocked, and exactly how to close it

`cpi`, `ppi`, `nfp`, `pce` (+ Tier-2 `retail`, `gdp_adv`).

- Every `www.bls.gov` and `download.bls.gov` path returns Akamai **403** to
  this container's egress IP. Not a layout change: the same URLs fetch fine
  through a different network path, and BEA / federalreserve.gov / DOL /
  Census all return 200 from here.
- BEA's `/news/archive` is JS-rendered — 0 release links in the raw HTML.
- Agreed door is **FRED release dates** (`fred_release_dates()`, already
  written and wired into `build_l0.py`). Release ids are resolved **by name**
  and asserted, so a rename fails loudly instead of silently pulling the wrong
  release. `api.stlouisfed.org` is reachable from here; only the key is
  missing. `fred.stlouisfed.org` (the website) times out, so there is no
  keyless fallback on that host.

To close:

```
export FRED_API_KEY=...
python news_lab/build_l0.py          # rewrites output/events.parquet
python -m pytest news_lab/tests -q
```

Then re-run this verdict's count table. Expect these to need explaining —
they are known-real, not parser faults:

- **cpi 36/37.** October 2025 CPI was **cancelled outright** (shutdown
  prevented collection); September CPI shifted to 2025-10-24 and November CPI
  to 2025-12-18. November 2025 therefore contains no CPI release.
- **nfp 36/37.** The October 2025 jobs report was **cancelled**; October
  payrolls were published with November on 2025-12-16, and the September
  report landed 2025-11-20. October 2025 contains no Employment Situation
  release.
- `ppi` and `pce` are delayed in the same window; confirm against the dates
  FRED returns rather than against the naive 37.

Both are ≥95% (36/37 = 97.3%), so the gate should still pass on the true
counts — but the verdict is only final once the numbers are real.
