"""Ambient trade-context instrumentation (Angus 24 Jul CANON ruling, §RULING priority-three).

The ruling FROZE engine/detector behavior and deliberately RETIRED three live-desk vetoes:
sweep-then-enter sequencing (Q-30), spread/fill-quality gating (Q-31), and the forward
news buffer (Q-33). In their place it mandated exactly one thing — journal the state each
retired veto used to read, on EVERY trade, so the dropped rules can later be re-evaluated
on live evidence instead of re-litigated blind. In the ruling's words: "Journal EVERYTHING,
gate NOTHING new."

This module computes those three ambient fields from data already on hand at journal time —
the streaming bar buffer and the news calendar — with ZERO influence on what the engine
fires or when. Nothing here can veto, resize, or reorder a trade; it only DESCRIBES a
trade's surroundings. (The one value here that CAN stop something is spread_at_fill, reused
by the order-time spread guard in src/live/spread_guard.py — but that is execution
engineering the ruling explicitly moved to Python, not a strategy veto.)

Every field's definition is a judgment call the ruling text left open. All choices are
enumerated in docs/ambient-instrumentation-choices.md for Angus to veto. In brief:

  * spread_at_fill      — the live Bar feed is OHLCV-only (no bid/ask), so absent a quote
                          source the proxy is the fill bar's high-low RANGE in points. A
                          real top-of-book `spread_fn` overrides it the moment a quote feed
                          lands (the MBP-10 condensed_*.csv already carries bid_px/ask_px).
  * news_calendar_state — signed minutes from the fill to the NEAREST high-impact release.
  * sweep_state         — did price sweep the relevant prior-session extreme (sell-side for
                          longs, buy-side for shorts) before / at-or-after the fill — a
                          proxy for the retired hydra POOL_SWEPT + ENTRY_AFTER_GRAB pair.

Everything is fail-soft: any internal error yields None/"unknown" for that one field and is
never allowed to raise into the trading loop.
"""

from __future__ import annotations

from datetime import time as dtime

import pandas as pd

from src.engine.data import _session_date

NY = "America/New_York"
_SESSION_BOUNDARY = dtime(18, 0)      # CME maintenance-break session roll (engine convention)

# --- tunables that double as documented interpretation choices (see the choices doc) -----
NEWS_IMPACT = "high"                  # C-2: only high-impact releases are counted as "news"
SPREAD_WINDOW = 30                    # C-5: trailing bars the guard baselines spread against


# --------------------------------------------------------------------------- helpers
def _to_et(ts) -> pd.Timestamp | None:
    """Coerce anything timestamp-ish to a tz-aware ET Timestamp; None on failure. A
    tz-naive input is ASSUMED ET (the engine's native tz), never silently UTC."""
    if ts is None:
        return None
    try:
        t = pd.Timestamp(ts)
    except Exception:
        return None
    if t.tz is None:
        return t.tz_localize(NY)
    return t.tz_convert(NY)


def _et_series(ts) -> pd.Series:
    """A bar frame's ts_event column as tz-aware ET (tz-naive assumed ET)."""
    s = pd.to_datetime(ts)
    if s.dt.tz is None:
        return s.dt.tz_localize(NY)
    return s.dt.tz_convert(NY)


def _has_bars(bars_df) -> bool:
    return bars_df is not None and len(bars_df) > 0 and "ts_event" in bars_df


def _bar_at(bars_df, ts):
    """The bar AT the given timestamp (exact ts_event match preferred, else the last bar
    at-or-before it — the bar an order would have filled on). None if nothing qualifies."""
    if not _has_bars(bars_df):
        return None
    target = _to_et(ts)
    if target is None:
        return None
    te = _et_series(bars_df["ts_event"])
    exact = bars_df[(te == target).to_numpy()]
    if len(exact):
        return exact.iloc[-1]
    prior = bars_df[(te <= target).to_numpy()]
    return prior.iloc[-1] if len(prior) else None


# --------------------------------------------------------------------------- spread
def range_spread(bars_df, fill_ts) -> float | None:
    """DEFAULT spread proxy: the fill bar's (high - low) range, in points. OHLCV carries no
    bid/ask, so this range stands in for a true top-of-book spread until a quote-bearing
    feed supplies a real `spread_fn`. None when no bar matches the fill timestamp."""
    row = _bar_at(bars_df, fill_ts)
    if row is None:
        return None
    return round(float(row["high"]) - float(row["low"]), 4)


def recent_spreads(bars_df, fill_ts, window: int = SPREAD_WINDOW,
                   spread_fn=None) -> list[float]:
    """Per-bar spread proxy for up to `window` bars STRICTLY BEFORE the fill bar, within
    the fill's own session. This is the RELATIVE baseline the order-time guard trips
    against — recent local conditions only, never a look-ahead past the fill."""
    if not _has_bars(bars_df):
        return []
    fill = _to_et(fill_ts)
    if fill is None:
        return []
    te = _et_series(bars_df["ts_event"])
    sess = _session_date(te, _SESSION_BOUNDARY)
    fill_sess = _session_date(pd.Series([fill]), _SESSION_BOUNDARY).iloc[0]
    mask = ((te < fill) & (sess == fill_sess)).to_numpy()
    win = bars_df[mask]
    if len(win) > window:
        win = win.iloc[-window:]
    if spread_fn is not None:
        vals = [spread_fn(bars_df, r["ts_event"]) for _, r in win.iterrows()]
    else:
        vals = [round(float(r["high"]) - float(r["low"]), 4) for _, r in win.iterrows()]
    return [float(v) for v in vals if v is not None]


# --------------------------------------------------------------------------- news
def news_calendar_state(calendar, fill_ts, impact: str = NEWS_IMPACT) -> str:
    """Signed minutes from the fill to the NEAREST high-impact release, encoded
    `"{event}:T{+/-}{min}"`: `T-15` = 15 min BEFORE the release (release upcoming),
    `T+8` = 8 min AFTER it. `"none"` when no in-scope event / no calendar.

    Journal-only: the retired news buffer (Q-33) is NOT re-imposed — this records the
    state so a news bleed can later be ruled on with evidence."""
    fill = _to_et(fill_ts)
    if calendar is None or len(calendar) == 0 or fill is None or "datetime_ET" not in calendar:
        return "none"
    cal = calendar
    if "impact" in cal:
        cal = cal[cal["impact"].astype(str).str.lower() == impact.lower()]
    if len(cal) == 0:
        return "none"
    et = _et_series(cal["datetime_ET"])
    delta_min = (fill - et).dt.total_seconds() / 60.0     # +ve: release already passed
    i = delta_min.abs().idxmin()
    mins = int(round(delta_min.loc[i]))
    event = str(cal.loc[i, "event"]) if "event" in cal else "event"
    return f"{event}:T{mins:+d}"


# --------------------------------------------------------------------------- sweep
def sweep_state(bars_df, tr) -> str:
    """Liquidity-sweep context at the trade, a proxy for the retired hydra POOL_SWEPT +
    ENTRY_AFTER_GRAB pair (Q-30 veto DROPPED — journal-only).

    Pool = the immediately-prior session's extreme relevant to the trade direction
    (sell-side / low for longs, buy-side / high for shorts). Return, relative to the fill:

      * "swept_before_entry" — a bar earlier in the fill's session pierced the pool BEFORE
                               the fill (the sequence hydra required to PASS).
      * "swept_after_entry"  — the pool was pierced only at/after the fill bar.
      * "no_sweep"           — the pool was never pierced in the session up to the buffer end.
      * "unknown"            — no prior session in the buffer, or data insufficient.
    """
    direction = str(getattr(tr, "direction", "") or "").lower()
    fill = _to_et(getattr(tr, "fill_ts", None))
    if not _has_bars(bars_df) or fill is None or direction not in ("long", "short"):
        return "unknown"
    te = _et_series(bars_df["ts_event"])
    sess = _session_date(te, _SESSION_BOUNDARY)
    fill_sess = _session_date(pd.Series([fill]), _SESSION_BOUNDARY).iloc[0]
    prior_days = sorted({d for d in sess if d < fill_sess})
    if not prior_days:
        return "unknown"
    prior = bars_df[(sess == prior_days[-1]).to_numpy()]     # the immediately-prior session
    if len(prior) == 0:
        return "unknown"
    cur = bars_df[(sess == fill_sess).to_numpy()]
    cur_te = te[(sess == fill_sess).to_numpy()]
    if direction == "long":
        pool = float(prior["low"].min())
        before = cur[(cur_te < fill).to_numpy()]["low"]
        after = cur[(cur_te >= fill).to_numpy()]["low"]
        swept_before = len(before) and float(before.min()) < pool
        swept_after = len(after) and float(after.min()) < pool
    else:
        pool = float(prior["high"].max())
        before = cur[(cur_te < fill).to_numpy()]["high"]
        after = cur[(cur_te >= fill).to_numpy()]["high"]
        swept_before = len(before) and float(before.max()) > pool
        swept_after = len(after) and float(after.max()) > pool
    if swept_before:
        return "swept_before_entry"
    if swept_after:
        return "swept_after_entry"
    return "no_sweep"


# --------------------------------------------------------------------------- assembly
def compute_ambient(bars_df, calendar, tr, spread_fn=None) -> dict:
    """The three ruling-mandated ambient fields for one completed trade. Fully fail-soft:
    each field is computed independently and any error yields None/"unknown" for that
    field alone — this instrumentation can never raise into the trading loop."""
    fill_ts = getattr(tr, "fill_ts", None)
    out: dict = {}
    try:
        out["spread_at_fill"] = (spread_fn(bars_df, fill_ts) if spread_fn is not None
                                 else range_spread(bars_df, fill_ts))
    except Exception:
        out["spread_at_fill"] = None
    try:
        out["news_calendar_state"] = news_calendar_state(calendar, fill_ts)
    except Exception:
        out["news_calendar_state"] = None
    try:
        out["sweep_state"] = sweep_state(bars_df, tr)
    except Exception:
        out["sweep_state"] = None
    return out


def vault_ambient(tr, bars_df, calendar) -> dict:
    """Adapter matching the Vault's `ambient_fn(tr, bars_df, calendar)` contract, using the
    default range-based spread proxy. Swap in a quote-backed `spread_fn` via a partial when
    a top-of-book feed is wired."""
    return compute_ambient(bars_df, calendar, tr)
