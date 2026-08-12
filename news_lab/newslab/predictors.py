"""L2 predictors — everything here must be knowable BEFORE the print.

Four families (pre-release drift is computed in census.py from the bars):

  1. Cleveland Fed inflation nowcast  → nowcast_gap = nowcast − consensus
  2. Feeder chain                      → e.g. CPI+PPI-implied core PCE
  3. Kalshi implied distribution skew  → kalshi_skew vs consensus
  4. Pre-release drift                 → drift_60/30/5 (from census)

Vintage rule for ALL of them: the value attached to an event must be the
value published strictly BEFORE the release timestamp. Each fetcher stores
an as-of date column so the join can enforce it.
"""
from __future__ import annotations
import os
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Cleveland Fed inflation nowcast (CPI + core CPI + PCE + core PCE)
# ---------------------------------------------------------------------------
# The Cleveland Fed publishes DAILY nowcasts and a downloadable history.
# The file URL drifts with site redesigns — set env CLEV_NOWCAST_URL after
# grabbing the current "download the data" link from:
#   https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting
# The parser below expects columns like: date, series, period, nowcast.
CLEV_URL = os.environ.get("CLEV_NOWCAST_URL", "")


def fetch_cleveland(session=None) -> pd.DataFrame:
    if not CLEV_URL:
        raise RuntimeError(
            "Set CLEV_NOWCAST_URL to the current Cleveland Fed nowcast "
            "history download (find it on the inflation-nowcasting page). "
            "Do not proceed without it — this is predictor family #1.")
    import requests
    r = (session or requests.Session()).get(CLEV_URL, timeout=60)
    r.raise_for_status()
    from io import BytesIO
    if CLEV_URL.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(r.content))
    else:
        df = pd.read_csv(BytesIO(r.content))
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def nowcast_gap(events: pd.DataFrame, nc: pd.DataFrame,
                fam_map: dict | None = None) -> pd.DataFrame:
    """nowcast_gap = (latest nowcast strictly BEFORE release ts) − forecast.
    fam_map: {family: nowcast-series-name-in-file}. Enforces as-of."""
    fam_map = fam_map or {"cpi": "core_cpi", "pce": "core_pce"}
    ev = events.copy()
    date_col = "date" if "date" in nc else nc.columns[0]
    nc = nc.copy()
    nc[date_col] = pd.to_datetime(nc[date_col])
    for i, row in ev.iterrows():
        series = fam_map.get(row["family"])
        if not series:
            continue
        cand = nc[(nc.get("series", series) == series) &
                  (nc[date_col] < pd.Timestamp(row["date"]))]
        if cand.empty:
            continue
        val_col = "nowcast" if "nowcast" in cand else cand.columns[-1]
        ev.loc[i, "nowcast"] = float(cand.sort_values(date_col)[val_col].iloc[-1])
    fc = ev.get("forecast_core_mom")
    if fc is not None and "nowcast" in ev:
        ev["nowcast_gap"] = ev["nowcast"] - fc.astype(float)
    return ev


# ---------------------------------------------------------------------------
# 2. Feeder chain (pure arithmetic on already-fetched first prints)
# ---------------------------------------------------------------------------
def pce_from_cpi_ppi(events: pd.DataFrame) -> pd.DataFrame:
    """For each PCE event, attach the same-month CPI core and PPI headline
    first prints (both released BEFORE PCE for the same reference month) —
    the market's own PCE model inputs. The census then tests whether the
    residual surprise after these is even nonzero."""
    ev = events.copy()
    cpi = ev[ev.family == "cpi"].set_index(ev[ev.family == "cpi"]["date"].str[:7])
    ppi = ev[ev.family == "ppi"].set_index(ev[ev.family == "ppi"]["date"].str[:7])
    for i, row in ev[ev.family == "pce"].iterrows():
        # PCE released ~2 wks after CPI/PPI covering the SAME prior month:
        ref_month = (pd.Timestamp(row["date"]) -
                     pd.offsets.MonthBegin(1)).strftime("%Y-%m")
        # CPI/PPI for ref_month were released in ref_month+1 == PCE month
        rel_month = row["date"][:7]
        if rel_month in cpi.index:
            ev.loc[i, "feeder_cpi_core"] = cpi.loc[rel_month].get("actual_core_mom")
        if rel_month in ppi.index:
            ev.loc[i, "feeder_ppi_head"] = ppi.loc[rel_month].get("actual_headline_mom")
    return ev


# ---------------------------------------------------------------------------
# 3. Kalshi (scaffold — ticker discovery is a documented step, not a guess)
# ---------------------------------------------------------------------------
KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"


def kalshi_discover(keyword: str = "CPI", session=None) -> pd.DataFrame:
    """List Kalshi series/markets matching a keyword so the correct tickers
    are recorded in config BY HAND after inspection. Public endpoints; no
    auth needed for market data reads."""
    import requests
    s = session or requests.Session()
    r = s.get(f"{KALSHI_API}/series", params={"category": "economics"},
              timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json().get("series", []))
    if not df.empty and "title" in df:
        df = df[df["title"].str.contains(keyword, case=False, na=False)]
    return df

# After discovery: pull candlesticks/trades for the chosen series with
# GET /markets and GET /series/{ticker}/markets/{mticker}/candlesticks,
# snapshot the implied distribution at T-minus-X, and compute skew vs the
# survey consensus. Wire into the predictor table with an as-of timestamp.
# Coverage caveat: depth of Kalshi history varies by series — measure
# coverage per family before leaning on it.
