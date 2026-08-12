"""L0 regression tests — one per bug found against the live pages.

No network: the scraper tests run against inline fixtures cut from the real
HTML, so a layout regression is caught here rather than in a build.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
import pytest

from newslab.events import _nth_business_day, scrape_fomc, build_ism


# --- ISM business-day rule -------------------------------------------------
# pd.bdate_range is weekday-only, so it called New Year's Day a business day
# and put ISM Manufacturing on 2024-01-01 and 2025-01-01.
def test_ism_first_business_day_skips_federal_holidays():
    assert _nth_business_day(2024, 1, 1) == pd.Timestamp("2024-01-02").date()
    assert _nth_business_day(2025, 1, 1) == pd.Timestamp("2025-01-02").date()
    # 3rd business day of Jan 2025: 1st is a holiday, so 2,3,6 (6th is Monday)
    assert _nth_business_day(2025, 1, 3) == pd.Timestamp("2025-01-06").date()


def test_ism_never_lands_on_a_federal_holiday():
    from pandas.tseries.holiday import USFederalHolidayCalendar
    hols = set(USFederalHolidayCalendar().holidays(
        start="2023-01-01", end="2026-01-31").date)
    ism = build_ism("2023-01-01", "2026-01-31")
    landed = [d for d in ism["date"] if pd.Timestamp(d).date() in hols]
    assert not landed, f"ISM rows on federal holidays: {landed}"


# --- FOMC calendar parse ---------------------------------------------------
# A notation vote (2025-08-22, Longer-Run Goals statement) carries the same
# monetaryYYYYMMDDa URL shape as a decision but is NOT a rate decision.
FOMC_FIXTURE = """
<div class="row fomc-meeting" ><div class="fomc-meeting__month"><strong>March
</strong></div><div class="fomc-meeting__date">21-22*</div>
<div><strong>Statement:</strong>
<a href="/newsevents/pressreleases/monetary20230322a.htm">HTML</a></div>
<div><a href="/monetarypolicy/fomcpresconf20230322.htm">Press Conference</a>
<strong>Projection Materials</strong>
<a href="/monetarypolicy/fomcprojtabl20230322.htm">HTML</a></div></div>
<div class="fomc-meeting--shaded row fomc-meeting" ><div>August 22
(notation vote)</div><div>
<a href="/newsevents/pressreleases/monetary20250822a.htm">Statement on
Longer-Run Goals and Monetary Policy Strategy</a></div></div>
<div class="row fomc-meeting" ><div class="fomc-meeting__month"><strong>May
</strong></div><div class="fomc-meeting__date">2-3</div>
<div><strong>Statement:</strong>
<a href="/newsevents/pressreleases/monetary20230503a.htm">HTML</a></div></div>
"""


class _FakeResp:
    status_code = 200
    text = FOMC_FIXTURE

    def raise_for_status(self):
        pass


class _FakeSession:
    def __init__(self):
        self.headers = {}

    def get(self, *a, **k):
        return _FakeResp()


def test_scrape_fomc_excludes_notation_votes_and_flags_sep():
    df = scrape_fomc(session=_FakeSession())
    assert list(df["date"]) == ["2023-03-22", "2023-05-03"]
    assert "2025-08-22" not in set(df["date"])       # notation vote dropped
    sep = dict(zip(df["date"], df["sep"]))
    assert sep["2023-03-22"] is True or sep["2023-03-22"]   # projections
    assert not sep["2023-05-03"]


def test_scrape_fomc_raises_rather_than_returning_empty():
    class Empty(_FakeSession):
        def get(self, *a, **k):
            r = _FakeResp()
            r.text = "<html>redesigned page, no meeting rows</html>"
            return r
    with pytest.raises(RuntimeError, match="0 rows"):
        scrape_fomc(session=Empty())
