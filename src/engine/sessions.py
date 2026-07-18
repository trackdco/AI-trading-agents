"""Resampler, session classifier, and level extractors (Spec 1, Step 3).

Builds on the validated 1-minute parquet from ``data.py`` and provides the higher-timeframe
and contextual inputs the indicator/snapshot layers consume:

  * ``resample_ohlcv`` / ``resample_all`` — 1m -> 2m/3m/5m/15m OHLCV, stamped by CLOSE time;
  * ``session_of`` / ``add_session`` — Asia/London/NY box per bar (§2 session boxes);
  * ``running_session_extremes`` — high/low so far within the current session box;
  * ``prior_day_levels`` / ``prior_week_levels`` — prior completed session/week H/L (targets, §6);
  * ``data_levels`` — extremes printed within N minutes of a scheduled release (§2 data levels).

Conventions (documented; flagged in progress-tracker for Angus):
  * Databento 1m bars are START-labeled (ts_event = interval open). Resampling realizes the
    spec's "right-closed, label=close time" by binning left-closed ``[t, t+rule)`` and labeling
    by the right edge — so a 5m bar stamped 09:35 aggregates the 1m bars 09:30..09:34 and is
    fully closed (actionable, no lookahead) at 09:35. pandas: ``closed='left', label='right'``.
  * Session/trade dates use the CME 18:00-ET boundary (``data._session_date``). All timestamps
    stay tz-aware America/New_York; DST is handled by the tz library.
  * "prior week" = prior completed ISO week (Mon-start). Trading-week (Sun 18:00 -> Fri 17:00)
    is a possible refinement, flagged.
"""
from __future__ import annotations

from datetime import time
from pathlib import Path

import pandas as pd
import yaml
from pydantic import BaseModel

from src.engine.data import _session_date

TZ_DEFAULT = "America/New_York"
_OHLCV_AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}


# ---------------------------------------------------------------- config

class SessionBox(BaseModel):
    """One session box (§2). Times are wall-clock ET; a box may wrap midnight (start > end)."""

    name: str
    start: time
    end: time

    def _mins(self) -> tuple[int, int]:
        return self.start.hour * 60 + self.start.minute, self.end.hour * 60 + self.end.minute


def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def load_session_boxes(config_path: Path = Path("config/strategy.yaml")) -> list[SessionBox]:
    boxes = yaml.safe_load(open(config_path))["session"]["boxes"]
    return [SessionBox(name=k, start=_parse_hhmm(v["start"]), end=_parse_hhmm(v["end"]))
            for k, v in boxes.items()]


def load_data_level_window(config_path: Path = Path("config/strategy.yaml")) -> int:
    return int(yaml.safe_load(open(config_path))["indicators"]["data_levels"]["window_min"])


# ---------------------------------------------------------------- resampling

def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Aggregate start-labeled 1m OHLCV into ``rule`` bars stamped by CLOSE time.

    See module docstring for the labeling convention. Empty bins (market closed) are dropped.
    A ``roll`` flag, if present, propagates (True if any constituent 1m bar is a roll bar).
    """
    agg = dict(_OHLCV_AGG)
    if "roll" in df.columns:
        agg["roll"] = "max"
    out = (df.set_index("ts_event").resample(rule, closed="left", label="right").agg(agg)
             .dropna(subset=["open"]).reset_index())
    out["volume"] = out["volume"].astype("int64")
    if "roll" in out.columns:
        out["roll"] = out["roll"].astype(bool)
    return out


def resample_all(df: pd.DataFrame, rules: list[str]) -> dict[str, pd.DataFrame]:
    """Resample to each rule (e.g. ['2min','3min','5min','15min']); returns {rule: frame}."""
    return {r: resample_ohlcv(df, r) for r in rules}


# ---------------------------------------------------------------- session classification

def session_of(ts: pd.Series, boxes: list[SessionBox] | None = None) -> pd.Series:
    """Box name ('asia'/'london'/'ny'/…) per tz-aware timestamp; '' when outside every box."""
    boxes = boxes if boxes is not None else load_session_boxes()
    idx = pd.DatetimeIndex(ts)
    mod = idx.hour * 60 + idx.minute
    label = pd.Series([""] * len(idx), index=ts.index if hasattr(ts, "index") else None)
    for b in boxes:
        s, e = b._mins()
        in_box = (mod >= s) & (mod < e) if s <= e else (mod >= s) | (mod < e)
        label = label.mask((label == "") & pd.Series(in_box, index=label.index), b.name)
    return label


def add_session(df: pd.DataFrame, boxes: list[SessionBox] | None = None) -> pd.DataFrame:
    out = df.copy()
    out["session"] = session_of(out["ts_event"], boxes).to_numpy()
    return out


def running_session_extremes(df: pd.DataFrame,
                             boxes: list[SessionBox] | None = None) -> pd.DataFrame:
    """Add session, session_high, session_low: running high/low within the current box instance.

    A new session instance begins whenever the box label changes (so each Asia/London/NY
    occurrence accumulates its own extremes). Rows outside every box get NaN extremes.
    """
    out = df.reset_index(drop=True).copy()
    box = session_of(out["ts_event"], boxes)
    instance = (box != box.shift()).cumsum()
    out["session"] = box.to_numpy()
    out["session_high"] = out["high"].groupby(instance).cummax().where(box != "").to_numpy()
    out["session_low"] = out["low"].groupby(instance).cummin().where(box != "").to_numpy()
    return out


# ---------------------------------------------------------------- prior day / week levels

def _session_hl(df: pd.DataFrame) -> pd.DataFrame:
    sd = _session_date(df["ts_event"], time(18, 0))
    g = df.assign(_sd=sd.to_numpy()).groupby("_sd")
    return pd.DataFrame({"high": g["high"].max(), "low": g["low"].min()}), sd


def prior_day_levels(df: pd.DataFrame) -> pd.DataFrame:
    """Add prior_day_high / prior_day_low = the PRIOR completed CME session's H/L (no lookahead)."""
    hl, sd = _session_hl(df)
    prior = hl.shift(1)
    out = df.copy()
    out["prior_day_high"] = sd.map(prior["high"]).to_numpy()
    out["prior_day_low"] = sd.map(prior["low"]).to_numpy()
    return out


def prior_week_levels(df: pd.DataFrame) -> pd.DataFrame:
    """Add prior_week_high / prior_week_low = the PRIOR completed ISO week's H/L (no lookahead)."""
    sd = _session_date(df["ts_event"], time(18, 0))
    iso = pd.DatetimeIndex(pd.to_datetime(sd.astype("string"))).isocalendar()
    wk = (iso["year"].astype(int) * 100 + iso["week"].astype(int)).to_numpy()
    tmp = df.assign(_wk=wk)
    g = tmp.groupby("_wk")
    whl = pd.DataFrame({"high": g["high"].max(), "low": g["low"].min()}).sort_index()
    prior = whl.shift(1)
    out = df.copy()
    out["prior_week_high"] = pd.Series(wk).map(prior["high"]).to_numpy()
    out["prior_week_low"] = pd.Series(wk).map(prior["low"]).to_numpy()
    return out


# ---------------------------------------------------------------- data levels

def load_news_calendar(path: Path = Path("config/news_calendar.csv"),
                       tz: str = TZ_DEFAULT) -> pd.DataFrame:
    """Read config/news_calendar.csv (skipping '#' comments); localize datetime_ET to tz.

    If config/news_calendar_hist.csv exists (2023-25 backfill from
    scripts/scrape_ff_calendar.py, same schema) it is concatenated in, so every
    consumer — engine news rules, regime vector, briefings — sees the full history
    the moment the file lands. Overlapping (datetime_ET, event) rows prefer the
    hand-maintained primary file.
    """
    from io import StringIO

    def _read(p: Path) -> pd.DataFrame:
        rows = [ln for ln in open(p) if not ln.startswith("#")]
        return pd.read_csv(StringIO("".join(rows)))

    cal = _read(path)
    hist = path.with_name("news_calendar_hist.csv")
    if hist.exists():
        cal = pd.concat([cal, _read(hist)]).drop_duplicates(
            ["datetime_ET", "event"], keep="first")
    cal["datetime_ET"] = pd.to_datetime(cal["datetime_ET"]).dt.tz_localize(tz)
    return cal.sort_values("datetime_ET").reset_index(drop=True)


def data_levels(df: pd.DataFrame, calendar: pd.DataFrame, n_minutes: int) -> pd.DataFrame:
    """Extremes printed within ``n_minutes`` AFTER each scheduled release (§2 data levels).

    For each calendar event at time E, the data-level high/low are the max high / min low of
    1m bars in ``[E, E + n_minutes]``. Events with no bars in range (market closed / outside
    the data window) are skipped. Returns one row per matched event with hi/lo and bar count.
    """
    ts = df["ts_event"]
    recs = []
    for _, ev in calendar.iterrows():
        e = ev["datetime_ET"]
        win = df[(ts >= e) & (ts <= e + pd.Timedelta(minutes=n_minutes))]
        if win.empty:
            continue
        recs.append({"event_time": e, "event": ev["event"], "impact": ev["impact"],
                     "data_high": float(win["high"].max()), "data_low": float(win["low"].min()),
                     "n_bars": int(len(win))})
    cols = ["event_time", "event", "impact", "data_high", "data_low", "n_bars"]
    return pd.DataFrame(recs, columns=cols)
