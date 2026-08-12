"""Consensus-as-of-the-morning — the other half of the surprise.

Primary: Forex Factory historical calendar (weekly pages carry forecast /
actual / previous per event with timestamps, in the red-folder taxonomy).
FF sits behind bot protection some days; this scraper is best-effort with a
raw-HTML cache, and the pipeline NEVER blocks on it: the manual fallback
(data/consensus_manual.csv) is a first-class source.

HONESTY NOTE: FF forecast is a proxy for the Bloomberg/Dow Jones survey the
market actually prices. Good enough for surprise z-scores; not the whisper.

UNTESTED IN SANDBOX (network locked). Test order on the box:
  1) fetch one week, eyeball parse vs the site
  2) run a month, spot-check 5 events against known prints
  3) only then run the full 2023→now sweep (polite: 1 req / 3s)
"""
from __future__ import annotations
import os
import re
import time
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ff_cache")

# FF event-title regexes → (family, field the forecast refers to)
FF_MAP = [
    (r"Core CPI m/m",                      ("cpi", "core_mom")),
    (r"CPI m/m",                           ("cpi", "headline_mom")),
    (r"Non-Farm Employment Change",        ("nfp", "payrolls_k")),
    (r"Unemployment Rate",                 ("nfp", "unrate")),
    (r"Average Hourly Earnings m/m",       ("nfp", "ahe_mom")),
    (r"Core PPI m/m",                      ("ppi", "core_mom")),
    (r"PPI m/m",                           ("ppi", "headline_mom")),
    (r"Core PCE Price Index m/m",          ("pce", "core_mom")),
    (r"Advance GDP q/q",                   ("gdp_adv", "real_gdp_saar")),
    (r"Retail Sales m/m",                  ("retail", "headline_mom")),
    (r"Unemployment Claims",               ("claims", "initial_k")),
    (r"ISM Manufacturing PMI",             ("ism_mfg", "pmi")),
    (r"ISM Services PMI",                  ("ism_svc", "pmi")),
    (r"Federal Funds Rate",                ("fomc", "decision_bps")),
]


def week_token(d: pd.Timestamp) -> str:
    """FF weekly URL token, e.g. 'aug10.2026' (the Monday of that week)."""
    mon = d - pd.Timedelta(days=d.weekday())
    return mon.strftime("%b%d.%Y").lower().replace(" 0", "")


def fetch_week(token: str, session=None) -> str:
    """Fetch one FF weekly calendar page; cache raw HTML. Tries plain
    requests first, then cloudscraper if installed."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{token}.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    url = f"https://www.forexfactory.com/calendar?week={token}"
    html = None
    try:
        import requests
        r = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (research; newslab)"})
        if r.ok and "calendar" in r.text:
            html = r.text
    except Exception:
        pass
    if html is None:
        try:
            import cloudscraper  # pip install cloudscraper
            html = cloudscraper.create_scraper().get(url, timeout=30).text
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                f"FF fetch failed for {token}: {e}. Options: install "
                f"cloudscraper, slow the crawl, or use the manual CSV "
                f"fallback (see load_manual).") from e
    open(path, "w", encoding="utf-8").write(html)
    time.sleep(3.0)  # be polite
    return html


_NUM = r"(-?\d+(?:\.\d+)?)\s*([%KMB]?)"


def _to_float(val: str, unit: str) -> float:
    x = float(val)
    return x * {"K": 1.0, "M": 1000.0, "B": 1e6}.get(unit, 1.0)  # claims in K


def parse_week(html: str) -> pd.DataFrame:
    """Best-effort parse of FF calendar rows (USD, high impact).
    FF markup drifts — if this returns 0 rows on a week that visibly has
    red-folder USD events, the layout changed: fix here, don't guess."""
    rows = []
    # crude row split; FF renders one <tr ... calendar__row ...> per event
    for chunk in re.split(r'<tr[^>]*calendar__row[^>]*>', html)[1:]:
        if "calendar__currency" not in chunk:
            continue
        cur = re.search(r'calendar__currency[^>]*>\s*([A-Z]{3})', chunk)
        if not cur or cur.group(1) != "USD":
            continue
        title = re.search(r'calendar__event-title[^>]*>([^<]+)<', chunk)
        if not title:
            continue
        name = title.group(1).strip()
        fam_field = next(((f, fld) for pat, (f, fld) in FF_MAP
                          if re.search(pat, name)), None)
        if fam_field is None:
            continue
        def cell(cls):
            m = re.search(cls + r'[^>]*>\s*(?:<span[^>]*>)?' + _NUM, chunk)
            return _to_float(m.group(1), m.group(2)) if m else None
        rows.append(dict(ff_title=name, family=fam_field[0],
                         field=fam_field[1],
                         actual_ff=cell("calendar__actual"),
                         forecast=cell("calendar__forecast"),
                         previous=cell("calendar__previous"),
                         raw_date=None))
    return pd.DataFrame(rows)


def load_manual(path: str = "data/consensus_manual.csv") -> pd.DataFrame:
    """Fallback / override source. Columns:
    family,date,field,forecast,actual_ff,previous,source
    One row per (event, field). 'source' e.g. 'ff_hand','bbg_terminal'.
    Manual rows WIN over scraped rows on conflict (they were hand-checked)."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=["family", "date", "field", "forecast",
                                     "actual_ff", "previous", "source"])
    df = pd.read_csv(path, dtype={"date": str})
    return df


def join_consensus(events: pd.DataFrame, cons: pd.DataFrame) -> pd.DataFrame:
    """Attach forecast_<field> columns; compute surprise on each family's
    surprise_field: surprise = actual − forecast, actual from ALFRED where
    available else the calendar's own actual (flagged)."""
    from .config import RELEASES
    ev = events.copy()
    for _, r in cons.iterrows():
        m = (ev["family"] == r["family"]) & (ev["date"] == r["date"])
        if not m.any():
            continue
        ev.loc[m, f"forecast_{r['field']}"] = r.get("forecast")
        ev.loc[m, f"calendar_actual_{r['field']}"] = r.get("actual_ff")
    # headline surprise per family
    for fam, spec in RELEASES.items():
        fld = spec["surprise_field"]
        m = ev["family"] == fam
        a = ev.loc[m].get(f"actual_{fld}")
        ca = ev.loc[m].get(f"calendar_actual_{fld}")
        f = ev.loc[m].get(f"forecast_{fld}")
        if f is None:
            continue
        actual = a.where(a.notna(), ca) if a is not None else ca
        if actual is None:
            continue
        ev.loc[m, "actual_used"] = actual
        ev.loc[m, "actual_source"] = pd.Series(
            ["alfred" if x else "calendar" for x in a.notna()] if a is not None
            else "calendar", index=ev.loc[m].index)
        ev.loc[m, "surprise"] = actual.astype(float) - f.astype(float)
    return ev
