"""First-print actuals via ALFRED (St. Louis Fed vintage database).

THE POINT: economic series get revised; today's FRED download is a lookahead.
ALFRED lets you ask "what did series X say ON date D" — the number the market
actually traded. Every actual in this lab comes through this module or the
calendar scrape; nothing is ever read from a current-vintage series.

Requires a free FRED API key: env FRED_API_KEY.
Network required — runs on the box.
"""
from __future__ import annotations
import os
import time
import pandas as pd

from .config import RELEASES, MIN_SURPRISE_HISTORY

API = "https://api.stlouisfed.org/fred/series/observations"


def _fred(series: str, obs_start: str, obs_end: str, vintage: str,
          session=None) -> pd.DataFrame:
    """Observations for `series` AS PUBLISHED ON `vintage` (YYYY-MM-DD)."""
    import requests
    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise RuntimeError("FRED_API_KEY not set — get a free key at "
                           "fred.stlouisfed.org, export it, rerun.")
    s = session or requests.Session()
    r = s.get(API, params=dict(
        series_id=series, api_key=key, file_type="json",
        observation_start=obs_start, observation_end=obs_end,
        realtime_start=vintage, realtime_end=vintage), timeout=30)
    r.raise_for_status()
    obs = r.json().get("observations", [])
    df = pd.DataFrame(obs)
    if df.empty:
        return df
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])
    return df[["date", "value"]]


def first_print(series: str, transform: str, ref_period: str,
                release_date: str, session=None) -> float | None:
    """The value for `ref_period` as first published on `release_date`.

    pch     : MoM % from SAME-VINTAGE index levels (ref vs prior period)
    diff_k  : month-over-month change, thousands (payrolls)
    level   : as published
    """
    ref = pd.Timestamp(ref_period)
    prior = (ref - pd.offsets.MonthBegin(1)).strftime("%Y-%m-%d")
    if transform == "level":
        df = _fred(series, ref_period, ref_period, release_date, session)
        return None if df.empty else float(df["value"].iloc[-1])
    df = _fred(series, prior, ref_period, release_date, session)
    if len(df) < 2 or df["value"].isna().any():
        return None
    a, b = float(df["value"].iloc[-2]), float(df["value"].iloc[-1])
    if transform == "pch":
        return round(100.0 * (b / a - 1.0), 4)
    if transform == "diff_k":
        return round(b - a, 1)  # PAYEMS already in thousands
    raise ValueError(transform)


def infer_ref_period(family: str, release_date: str) -> str:
    """Reference period covered by a release on `release_date`.
    Monthly 08:30 releases cover the PRIOR month; claims cover the prior
    week (level series — ALFRED handles by date); GDP advance covers the
    prior quarter (use quarter-start date for FRED quarterly series)."""
    d = pd.Timestamp(release_date)
    if family == "claims":
        # ICSA observation dated the Saturday ending the reference week
        return (d - pd.Timedelta(days=d.weekday() + 2)).strftime("%Y-%m-%d")
    if family == "gdp_adv":
        q = (d - pd.offsets.QuarterBegin(startingMonth=1)).normalize()
        return q.strftime("%Y-%m-%d")
    return (d - pd.offsets.MonthBegin(1)).strftime("%Y-%m-01")


def fill_actuals(events: pd.DataFrame, throttle_s: float = 0.6,
                 session=None) -> pd.DataFrame:
    """Adds actual_<field> columns per family's ALFRED map. Skips families
    with no ALFRED mapping (fomc, ism_*) — those come from the calendar."""
    ev = events.copy()
    for fam, spec in RELEASES.items():
        for field, (series, transform) in spec["alfred"].items():
            col = f"actual_{field}"
            if col not in ev:
                ev[col] = pd.NA
    for i, row in ev.iterrows():
        spec = RELEASES[row["family"]]
        if not spec["alfred"]:
            continue
        ref = infer_ref_period(row["family"], row["date"])
        for field, (series, transform) in spec["alfred"].items():
            try:
                v = first_print(series, transform, ref, row["date"], session)
            except Exception as e:  # noqa: BLE001 — log & continue, never fill
                v = None
                ev.loc[i, "fetch_error"] = str(e)[:120]
            ev.loc[i, f"actual_{field}"] = v
            time.sleep(throttle_s)  # FRED rate limit: 120 req/min
    return ev


# ---------------------------------------------------------------------------
# Causal surprise z — uses ONLY past events of the same family. No lookahead.
# ---------------------------------------------------------------------------
def causal_z(events: pd.DataFrame, surprise_col: str = "surprise") -> pd.Series:
    out = pd.Series(index=events.index, dtype=float)
    for fam, grp in events.sort_values("ts_release_et").groupby("family"):
        s = grp[surprise_col].astype(float)
        mu = s.expanding().mean().shift(1)
        sd = s.expanding().std(ddof=1).shift(1)
        n = s.expanding().count().shift(1)
        z = (s - mu) / sd
        z[n < MIN_SURPRISE_HISTORY] = float("nan")
        out.loc[grp.index] = z
    return out
