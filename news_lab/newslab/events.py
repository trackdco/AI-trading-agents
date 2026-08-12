"""L0 event table — release dates & timestamps, vintage-safe by construction.

Three sources, in order of trust:
  1. STATIC SEEDS — FOMC decision dates (announced years ahead) and a small
     set of dates verified by hand. Never guessed.
  2. RULE GENERATORS — weekly claims Thursdays, ISM 1st/3rd business day.
     Rows carry needs_verification=True where holidays can shift them.
  3. SCHEDULE SCRAPERS — BLS/BEA official schedule pages (network required;
     run on the box, not the sandbox).

Nothing in this module invents a date. If a scraper fails, the pipeline
stops rather than filling gaps.
"""
from __future__ import annotations
import re
import datetime as dt
import pandas as pd

from .config import TZ_ET, RELEASES

# Window the L0 table is built and gated over (bars in repo end 2026-01-31).
WINDOW_START = "2023-01-01"
WINDOW_END = "2026-01-31"

_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/126.0.0.0 Safari/537.36")

# ---------------------------------------------------------------------------
# 1. STATIC SEEDS
# ---------------------------------------------------------------------------
# FOMC decision days (day 2 of each meeting), 14:00 ET statement.
# Source: federalreserve.gov/monetarypolicy/fomccalendars.htm — VERIFY there
# before first real run (task in RUNBOOK). SEP meetings flagged.
FOMC_DECISIONS = [
    # 2023
    ("2023-02-01", False), ("2023-03-22", True), ("2023-05-03", False),
    ("2023-06-14", True),  ("2023-07-26", False), ("2023-09-20", True),
    ("2023-11-01", False), ("2023-12-13", True),
    # 2024
    ("2024-01-31", False), ("2024-03-20", True), ("2024-05-01", False),
    ("2024-06-12", True),  ("2024-07-31", False), ("2024-09-18", True),
    ("2024-11-07", False), ("2024-12-18", True),
    # 2025
    ("2025-01-29", False), ("2025-03-19", True), ("2025-05-07", False),
    ("2025-06-18", True),  ("2025-07-30", False), ("2025-09-17", True),
    ("2025-10-29", False), ("2025-12-10", True),
    # 2026 (Jul 28-29 and Sep 15-16 confirmed against live reporting 08/2026)
    ("2026-01-28", False), ("2026-03-18", True), ("2026-04-29", False),
    ("2026-06-17", True),  ("2026-07-29", False), ("2026-09-16", True),
    ("2026-10-28", False), ("2026-12-09", True),
]

# Hand-verified odd rows (from primary reporting). Smoke-test seeds only —
# the scrapers are the real source for monthly release dates.
VERIFIED_SEEDS = [
    ("cpi", "2026-07-14"),   # June 2026 CPI (BLS archive, verified)
    ("cpi", "2026-08-12"),   # July 2026 CPI (BLS schedule, verified)
]


def build_fomc() -> pd.DataFrame:
    rows = [dict(family="fomc", date=d, time_et="14:00", sep=sep,
                 source="static_seed", needs_verification=False)
            for d, sep in FOMC_DECISIONS]
    return pd.DataFrame(rows)


# Federal Reserve's own calendar — the authority the seeds are checked against.
FOMC_CAL_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

# A meeting row links its statement as monetaryYYYYMMDDa; the 8 digits ARE the
# decision date, so nothing is inferred from the "31-1" style day-range text.
_FOMC_STMT_RE = re.compile(
    r"/(?:newsevents/pressreleases|monetarypolicy/files)/monetary(\d{8})a")


def scrape_fomc(session=None) -> pd.DataFrame:
    """FOMC decision days from federalreserve.gov. Raises on parse failure.

    Two traps this parser handles, both found live:
      * NOTATION VOTES share the monetaryYYYYMMDDa URL shape but are not rate
        decisions (e.g. 2025-08-22, the Longer-Run Goals statement). There is
        no 14:00 statement, so they must not enter the event table.
      * Meetings still in the future have no statement PDF yet, so they are
        absent here by construction — this returns DECIDED meetings only.
    """
    import requests
    s = session or requests.Session()
    s.headers.update({"User-Agent": _UA})
    r = s.get(FOMC_CAL_URL, timeout=30)
    r.raise_for_status()
    rows = []
    for chunk in re.split(r'<div class="[^"]*row fomc-meeting"', r.text)[1:]:
        if "notation vote" in chunk.lower():
            continue
        m = _FOMC_STMT_RE.search(chunk)
        if not m:
            continue                       # future meeting: no statement yet
        d = m.group(1)
        rows.append(dict(family="fomc", date=f"{d[:4]}-{d[4:6]}-{d[6:]}",
                         time_et="14:00",
                         sep=("fomcprojtabl" in chunk
                              or "Projection Materials" in chunk),
                         source="fed_calendar", needs_verification=False))
    if not rows:
        raise RuntimeError(
            "FOMC calendar parse produced 0 rows — page layout changed; "
            "fix parser, do not guess dates.")
    return pd.DataFrame(rows).drop_duplicates("date")


# ---------------------------------------------------------------------------
# 2. RULE GENERATORS
# ---------------------------------------------------------------------------
def build_claims(start: str, end: str) -> pd.DataFrame:
    """Every Thursday 08:30 ET. Weeks containing a federal holiday are
    flagged needs_verification (DOL occasionally shifts the release)."""
    from pandas.tseries.holiday import USFederalHolidayCalendar
    cal = USFederalHolidayCalendar()
    hols = set(cal.holidays(start=start, end=end).date)
    thursdays = pd.date_range(start, end, freq="W-THU")
    rows = []
    for t in thursdays:
        week = {(t + pd.Timedelta(days=k)).date() for k in range(-3, 4)}
        rows.append(dict(family="claims", date=t.strftime("%Y-%m-%d"),
                         time_et="08:30", sep=False, source="rule_thursday",
                         needs_verification=bool(week & hols)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2b. DOL CLAIMS — official release dates, not the Thursday rule
# ---------------------------------------------------------------------------
# ETA publishes each weekly claims news release at a URL whose FILENAME IS THE
# RELEASE DATE: oui.doleta.gov/press/<yyyy>/<mmddyy>.pdf. So a HEAD probe is an
# existence oracle: 200 = the release happened that day, 404 = it did not. The
# date is never transcribed by anything, it is the key we probed. That resolves
# every holiday shift AND every suspension without a rule or a guess.
DOL_PRESS_URL = "https://oui.doleta.gov/press/{year}/{mmddyy}.pdf"


def scrape_dol_claims(start: str = WINDOW_START, end: str = WINDOW_END,
                      workers: int = 8, session=None) -> pd.DataFrame:
    """Probe every weekday in [start, end] for a DOL claims news release.

    Returns one row per confirmed release, 08:30 ET, needs_verification=False —
    the probe IS the verification. Raises if the probe finds essentially
    nothing (network/layout break) rather than returning a thin table that
    would silently read as "no releases happened".
    """
    import requests
    from concurrent.futures import ThreadPoolExecutor
    s = session or requests.Session()
    s.headers.update({"User-Agent": _UA})

    def probe(d: pd.Timestamp):
        url = DOL_PRESS_URL.format(year=d.year, mmddyy=d.strftime("%m%d%y"))
        r = s.head(url, timeout=25, allow_redirects=True)
        ok = (r.status_code == 200
              and "pdf" in r.headers.get("Content-Type", "").lower())
        return d, ok, url

    days = [d for d in pd.date_range(start, end) if d.weekday() < 5]
    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(probe, days))

    rows = [dict(family="claims", date=d.strftime("%Y-%m-%d"), time_et="08:30",
                 sep=False, source="dol_press_probe", needs_verification=False,
                 source_url=url)
            for d, ok, url in results if ok]
    weeks = len(pd.date_range(start, end, freq="W-THU"))
    if len(rows) < weeks * 0.5:
        raise RuntimeError(
            f"DOL claims probe found only {len(rows)} releases across {weeks} "
            f"weeks — the press-release URL pattern or network changed; fix "
            f"the probe, do not fall back to the Thursday rule.")
    return pd.DataFrame(rows)


def _nth_business_day(year: int, month: int, n: int) -> dt.date:
    """FIXED 12 Aug 2026: pd.bdate_range is weekday-only and counts federal
    holidays as business days, which put ISM Manufacturing on New Year's Day
    in both 2024 and 2025 (14 of 74 rows wrong over the window). The business
    calendar must exclude federal holidays."""
    from pandas.tseries.holiday import USFederalHolidayCalendar
    from pandas.tseries.offsets import CustomBusinessDay
    cbd = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    d = pd.Timestamp(year=year, month=month, day=1)
    bdays = pd.bdate_range(d, d + pd.offsets.MonthEnd(0), freq=cbd)
    return bdays[n - 1].date()


def build_ism(start: str, end: str) -> pd.DataFrame:
    """ISM Manufacturing = 1st business day 10:00 ET; Services = 3rd.
    Rule-generated → always needs_verification=True (holiday exceptions)."""
    months = pd.period_range(start, end, freq="M")
    rows = []
    for p in months:
        for fam, n in (("ism_mfg", 1), ("ism_svc", 3)):
            rows.append(dict(family=fam,
                             date=str(_nth_business_day(p.year, p.month, n)),
                             time_et="10:00", sep=False,
                             source="rule_business_day",
                             needs_verification=True))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3. SCHEDULE SCRAPERS (network — run on the box)
# ---------------------------------------------------------------------------
# FIXED 12 Aug 2026: the old news_release/{year}_sched.htm path is dead (404 —
# confirmed live, not a guess). BLS now publishes per-MONTH schedule pages.
# Separately, www.bls.gov Akamai-403s datacenter egress IPs, so this scraper
# runs on a residential box; from a blocked host use fred_release_dates().
BLS_YEAR_URL = "https://www.bls.gov/schedule/{year}/{month:02d}_sched.htm"
BLS_YEAR_URL_LEGACY = "https://www.bls.gov/schedule/news_release/{year}_sched.htm"
BLS_NAMES = {  # substrings on the BLS schedule pages → family
    "Consumer Price Index": "cpi",
    "Producer Price Index": "ppi",
    "Employment Situation": "nfp",
}
_DATE_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{1,2}),\s+(\d{4})")


class BLSBlocked(RuntimeError):
    """www.bls.gov refused the request (Akamai bot filter), as opposed to the
    page layout changing. Distinct class because the remedies differ: run from
    a residential IP, or take the dates from fred_release_dates() instead."""


def scrape_bls_year(year: int, session=None) -> pd.DataFrame:
    """Parse the official BLS schedule pages for `year` into event rows.

    Walks the 12 monthly pages (list variant first, calendar variant second).
    Raises BLSBlocked on a 403 bot-block and RuntimeError on a parse failure —
    never fabricates a date.

    NOTE (12 Aug 2026): this parser could NOT be validated against live HTML in
    the build container — www.bls.gov Akamai-403s its egress IP for every
    bls.gov path. The URL structure below was confirmed live via an independent
    fetch path; the row parsing is written to the documented table layout and
    is the FIRST thing to check when running on the box. The L0 table shipped
    from this container sourced BLS dates via fred_release_dates() instead.
    """
    import requests
    s = session or requests.Session()
    s.headers.update({"User-Agent": _UA})
    rows, blocked, tried = [], 0, []
    for month in range(1, 13):
        html = None
        for tmpl in (BLS_YEAR_URL.replace("_sched", "_sched_list"),
                     BLS_YEAR_URL):
            url = tmpl.format(year=year, month=month)
            tried.append(url)
            r = s.get(url, timeout=30)
            if r.status_code == 403:
                blocked += 1
                continue
            if r.status_code == 404:
                continue
            r.raise_for_status()
            html = r.text
            break
        if html is None:
            continue
        for chunk in re.split(r"<tr[^>]*>", html):
            for name, fam in BLS_NAMES.items():
                if name not in chunk:
                    continue
                m = _DATE_RE.search(chunk)
                if not m:
                    continue
                date = pd.Timestamp(f"{m.group(1)} {m.group(2)} {m.group(3)}")
                if date.year != year:
                    continue
                rows.append(dict(family=fam, date=str(date.date()),
                                 time_et=RELEASES[fam]["time_et"],
                                 sep=False, source=f"bls_sched_{year}",
                                 needs_verification=False))
    if blocked and not rows:
        raise BLSBlocked(
            f"www.bls.gov returned 403 for {blocked} schedule pages in {year} "
            f"(Akamai bot filter on this egress IP, not a layout change). "
            f"Run from a residential IP, or use fred_release_dates().")
    if not rows:
        raise RuntimeError(
            f"BLS schedule parse produced 0 rows for {year} — page layout "
            f"changed; fix parser, do not guess dates. Tried: {tried[:4]}")
    return pd.DataFrame(rows).drop_duplicates(["family", "date"])


# ---------------------------------------------------------------------------
# 3b. FRED RELEASE DATES — the machine-readable door to the same schedules
# ---------------------------------------------------------------------------
# FRED records the official release date of every vintage it ingests, which is
# exactly the BLS/BEA/Census publication calendar in JSON. Same house as ALFRED
# (vintage.py), so L0 dates and L0b first prints come from one source of truth.
# Release IDs are LOOKED UP BY NAME, never hardcoded, and the resolved name is
# asserted against the expected string — a renamed release fails loudly.
FRED_RELEASES_API = "https://api.stlouisfed.org/fred/releases"
FRED_RELEASE_DATES_API = "https://api.stlouisfed.org/fred/release/dates"

# family -> exact FRED release name
FRED_RELEASE_NAMES = {
    "cpi":     "Consumer Price Index",
    "ppi":     "Producer Price Index",
    "nfp":     "Employment Situation",
    "pce":     "Personal Income and Outlays",
    "retail":  "Advance Monthly Sales for Retail and Food Services",
    "gdp_adv": "Gross Domestic Product",
}


def _fred_key() -> str:
    import os
    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise RuntimeError("FRED_API_KEY not set — get a free key at "
                           "fred.stlouisfed.org, export it, rerun.")
    return key


def fred_release_id(family: str, session=None) -> int:
    """Resolve a family's FRED release_id by exact name match."""
    import requests
    want = FRED_RELEASE_NAMES[family]
    s = session or requests.Session()
    r = s.get(FRED_RELEASES_API, params=dict(
        api_key=_fred_key(), file_type="json", limit=1000), timeout=30)
    r.raise_for_status()
    hits = [x for x in r.json().get("releases", []) if x["name"] == want]
    if len(hits) != 1:
        raise RuntimeError(
            f"FRED release name {want!r} matched {len(hits)} releases — "
            f"resolve by hand, do not guess an id.")
    return int(hits[0]["id"])


def fred_release_dates(family: str, start: str = WINDOW_START,
                       end: str = WINDOW_END, session=None) -> pd.DataFrame:
    """Official release dates for `family` from FRED. Raises on empty."""
    import requests
    s = session or requests.Session()
    rid = fred_release_id(family, s)
    r = s.get(FRED_RELEASE_DATES_API, params=dict(
        release_id=rid, api_key=_fred_key(), file_type="json",
        realtime_start=start, realtime_end=end, sort_order="asc",
        include_release_dates_with_no_data="false", limit=10000), timeout=30)
    r.raise_for_status()
    dates = [d["date"] for d in r.json().get("release_dates", [])]
    if not dates:
        raise RuntimeError(
            f"FRED returned 0 release dates for {family} (release_id={rid}) "
            f"over {start}..{end} — investigate, do not guess dates.")
    return pd.DataFrame([
        dict(family=family, date=d, time_et=RELEASES[family]["time_et"],
             sep=False, source=f"fred_release_{rid}",
             # GDP bundles advance/second/third estimates under ONE release id,
             # so those rows are NOT yet identified as the advance print.
             needs_verification=(family == "gdp_adv"))
        for d in sorted(set(dates))])


def scrape_bea_schedule(session=None) -> pd.DataFrame:
    """BEA release schedule (PCE = 'Personal Income and Outlays',
    GDP advance = 'Gross Domestic Product ... (Advance Estimate)').
    FORWARD-LOOKING ONLY — the page lists upcoming releases from today, so it
    is NOT a source for the 2023-01→2026-01 census window; PCE/GDP history
    comes from fred_release_dates(). Kept for scheduling future events.

    FIXED 12 Aug 2026, three real parse bugs found against live HTML:
      * the date cell is "August 26" with NO year, so the Month D, YYYY regex
        matched nothing and the scraper raised on every call;
      * titles read "GDP (Advance Estimate), 3rd Quarter 2026" — the old
        "Gross Domestic Product" + "Advance" test could never fire;
      * retail is Census, not BEA, and never appears here.
    Years are reconstructed by walking the months forward (the schedule is
    ascending from today), never assumed to be the current year.
    """
    import requests
    s = session or requests.Session()
    s.headers.update({"User-Agent": _UA})
    r = s.get("https://www.bea.gov/news/schedule", timeout=30)
    r.raise_for_status()
    # rows are <td class="scheduled-date ..."><div class="release-date">Month D
    # ...<td class="release-title ...">Title
    cells = re.findall(
        r'class="release-date">([^<]+)</div>.*?'
        r'class="release-title[^"]*"[^>]*>([^<]+)', r.text, re.S)
    rows, year, prev_month = [], None, 0
    for raw_date, title in cells:
        m = re.match(r"\s*([A-Z][a-z]+)\s+(\d{1,2})", raw_date)
        if not m:
            continue
        month = pd.Timestamp(f"{m.group(1)} 1 2000").month
        if year is None:
            year = pd.Timestamp.today().year
            if month < pd.Timestamp.today().month:
                year += 1
        elif month < prev_month:          # wrapped past December
            year += 1
        prev_month = month
        t = title.strip()
        if t.startswith("Personal Income and Outlays"):
            fam = "pce"
        elif t.startswith("GDP (Advance Estimate)"):
            fam = "gdp_adv"
        else:
            continue
        rows.append(dict(family=fam,
                         date=f"{year}-{month:02d}-{int(m.group(2)):02d}",
                         time_et=RELEASES[fam]["time_et"], sep=False,
                         source="bea_schedule", needs_verification=False))
    if not rows:
        raise RuntimeError(
            "BEA schedule parse produced 0 rows — fix parser. Expected "
            "'release-date' + 'release-title' cells on bea.gov/news/schedule.")
    return pd.DataFrame(rows)


# NOTE: historical BLS pages exist per year (2023_sched.htm etc.). BEA/Census
# historical release dates are also recoverable from the consensus calendar
# scrape (consensus.py) — every FF row carries its timestamp, so the calendar
# join both dates the event AND supplies forecast/actual. Where the two
# sources disagree on a date, the pipeline flags, never picks silently.


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def assemble(frames: list[pd.DataFrame]) -> pd.DataFrame:
    ev = pd.concat(frames, ignore_index=True)
    ev["ts_release_et"] = pd.to_datetime(
        ev["date"] + " " + ev["time_et"]).dt.tz_localize(TZ_ET)
    ev = ev.sort_values("ts_release_et").reset_index(drop=True)
    ev["event_id"] = ev["family"] + "_" + ev["date"]
    dup = ev.duplicated(["event_id"], keep="first")
    ev = ev[~dup].reset_index(drop=True)
    return ev


def build_static_and_rules(start="2023-01-01", end="2026-07-31") -> pd.DataFrame:
    seeds = pd.DataFrame([dict(family=f, date=d,
                               time_et=RELEASES[f]["time_et"], sep=False,
                               source="verified_seed", needs_verification=False)
                          for f, d in VERIFIED_SEEDS])
    return assemble([build_fomc(), build_claims(start, end),
                     build_ism(start, end), seeds])
