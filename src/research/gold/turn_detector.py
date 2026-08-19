"""Second-derivative turn detector — Model B from the Reddit gold-EA thread audit.

Codifies the one testable claim in `docs/RESEARCH-reddit-gold-ea-thread.md`: a smoothed
price curve's second derivative "should compress and reverse, then hold for two 5 minute
candles." The source states no smoother, no numeric definition of "compress", no stop and
no target — every one of those is a declared interpretation, not a fact recovered from the
post, and is recorded as such in `docs/DECLARATIONS-gold-turn-detector.md`.

**The codification collapses "compress" and "reverse" into one event.** A second
derivative's magnitude shrinking toward zero and then changing sign are not two conditions
to detect separately — they are the same zero-crossing. So: a TURN CANDIDATE is a bar where
sign(d2) flips relative to the prior bar, and CONFIRMS if the new sign holds for the next
two 5-minute bars (the source's literal "hold for two 5 minute candles"). Direction: a flip
to positive curvature (concave-down -> concave-up, a decline decelerating into a base) is
long; the mirror is short. This is a physical reading of "acceleration reversing", not
something the source states outright, and is the single largest interpretive choice here.

**No day resets.** Gold trades ~23h/day with one maintenance gap. The EMA and its
derivatives are computed on ONE CONTINUOUS SERIES across the whole span passed in, never
reset at a calendar boundary — resetting daily would inject a fake discontinuity into the
smoother every single day. Candidates are precomputed once, then handed to the
`src.research.orb.engine` harness (day-grouped by construction) via a closure, exactly the
extension point that harness's README describes.

**5-minute bins are absolute, not session-anchored.** `_bars5` buckets by
(epoch minute // 5), not by an anchor time-of-day, so a bin never straddles the two
different session conventions the ORB work used (09:30 vs 08:20 vs 03:00) and is agnostic
to all of them — there is no "anchor" for a signal meant to run all session long.

**Known limitation, stated rather than fixed.** `engine.run()` looks up a candidate's fill
bar inside the SAME CALENDAR DAY's 1-minute slice (`day.tmin == fill_mod`, `tmin` bounded
0-1439). A candidate confirmed in the last few minutes before midnight, whose fill lands
after 00:00, will not be found and is silently dropped (the existing `break` — not a crash).
This affects a small, direction-neutral fraction of signals near the day boundary and is a
conservative bias (fewer candidates, not spurious ones) rather than a correctness bug, so it
is documented rather than patched into the shared harness for this single signal.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NY = "America/New_York"


def _bars5(bars: pd.DataFrame) -> pd.DataFrame:
    """Continuous 5-minute OHLCV, binned on absolute epoch time so no bin straddles the
    maintenance gap and nothing resets at a calendar-day boundary."""
    b = bars.copy()
    # int64-cast-then-divide silently breaks on non-nanosecond dtypes (pandas >= 2.x can
    # hand back datetime64[us, tz] from some sources, and 3.0's date_range defaults to it) --
    # this counted every row into ONE bin in that case, caught by
    # test_bars5_aggregates_ohlcv_correctly on synthetic (us-resolution) test data even
    # though real ns-resolution parquet data happened not to trigger it. Timedelta floor
    # division is resolution-agnostic and correct regardless of the column's internal unit.
    utc = b.ts_event.dt.tz_convert("UTC") if b.ts_event.dt.tz is not None else \
        b.ts_event.dt.tz_localize("UTC")
    epoch_min = (utc - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(minutes=1)
    b["bin5"] = epoch_min // 5
    g = b.groupby("bin5", sort=True)
    out = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                close=("close", "last"), volume=("volume", "sum"),
                ts=("ts_event", "first")).reset_index(drop=True)
    out["tmin"] = out.ts.dt.hour * 60 + out.ts.dt.minute
    out["cal"] = out.ts.dt.normalize()
    return out


def turn_candidates_all(bars5: pd.DataFrame, *, ema_span: int, hold_bars: int = 2,
                        cooldown_bars: int = 12, stop_lookback: int = 2,
                        vol_mult: float | None = None,
                        vol_lookback: int = 20) -> pd.DataFrame:
    """Every turn candidate on a continuous 5-minute frame. Row-index based throughout
    (bar count, not clock time) — the established convention in this repo for signals that
    must carry across a data gap (the iFVG detector does the same with its `age`/`i`)."""
    b = bars5.reset_index(drop=True)
    n = len(b)
    ema = b.close.ewm(span=ema_span, adjust=False).mean().to_numpy()
    d1 = np.diff(ema, prepend=np.nan)
    d2 = np.diff(d1, prepend=np.nan)
    sign2 = np.sign(d2)
    sign2[np.isnan(d2)] = 0.0

    hi = b.high.to_numpy(); lo = b.low.to_numpy()
    vol = b.volume.to_numpy()
    vol_base = pd.Series(vol).rolling(vol_lookback).mean().shift(1).to_numpy()

    rows, last_fire = [], {}
    for t0 in range(2, n - hold_bars - 1):        # needs d2[t0], hold_bars ahead, +1 to fill
        if sign2[t0] == 0.0 or sign2[t0 - 1] == 0.0 or sign2[t0] == sign2[t0 - 1]:
            continue                              # not a crossing (or the warm-up NaNs at
                                                    # the very start of the series, which
                                                    # read as sign2==0 and would otherwise
                                                    # register as a false first "flip")
        d_ = 1 if sign2[t0] > 0 else -1
        hold_end = t0 + hold_bars
        if not all(sign2[t0 + k] == sign2[t0] for k in range(1, hold_bars + 1)):
            continue                              # the new sign did not hold
        fill_i = hold_end + 1
        if fill_i >= n:
            continue

        if cooldown_bars > 0 and t0 - last_fire.get(d_, -10**9) < cooldown_bars:
            continue                              # BR-9/BR-10: one signal per fight

        if vol_mult is not None:
            vb = vol_base[hold_end]
            if not (np.isfinite(vb) and vb > 0 and vol[hold_end] >= vol_mult * vb):
                continue

        w0 = max(0, t0 - stop_lookback)
        stop = (lo[w0:hold_end + 1].min() - 0.10) if d_ > 0 else \
               (hi[w0:hold_end + 1].max() + 0.10)

        rows.append({"cal": b.cal.iloc[fill_i], "signal_tmin": int(b.tmin.iloc[hold_end]),
                     "fill_tmin": int(b.tmin.iloc[fill_i]), "direction": d_,
                     "stop_ref": float(stop), "t0": t0})
        last_fire[d_] = t0
    cols = ["cal", "signal_tmin", "fill_tmin", "direction", "stop_ref", "t0"]
    return pd.DataFrame(rows, columns=cols)      # explicit columns: a zero-candidate day
                                                   # must still produce a groupby-able frame


def build_signal(bars: pd.DataFrame, *, ema_span: int, hold_bars: int = 2,
                 cooldown_bars: int = 12, stop_lookback: int = 2,
                 vol_mult: float | None = None, vol_lookback: int = 20):
    """Precompute every candidate ONCE on the full continuous series, then return a
    `signal_fn(day, cfg, row, feat, anchor, or_end)` closure matching the harness interface
    (`src/research/orb/README.md`). `cfg`/`row`/`feat`/`anchor`/`or_end` are accepted for
    interface compatibility and ignored — this signal has no notion of an opening range."""
    from src.research.orb.engine import Candidate

    b5 = _bars5(bars)
    cands = turn_candidates_all(b5, ema_span=ema_span, hold_bars=hold_bars,
                                cooldown_bars=cooldown_bars, stop_lookback=stop_lookback,
                                vol_mult=vol_mult, vol_lookback=vol_lookback)
    by_day = {k: g.sort_values("fill_tmin") for k, g in cands.groupby("cal", sort=False)}

    def signal_fn(day, cfg, row, feat, anchor, or_end):
        cal = day.cal.iloc[0]
        g = by_day.get(cal)
        if g is None:
            return []
        return [Candidate(int(r.signal_tmin), int(r.fill_tmin), int(r.direction),
                          float(r.stop_ref),
                          {"sig_ema_span": ema_span, "sig_t0_tmin": int(r.signal_tmin)})
                for r in g.itertuples(index=False)]

    return signal_fn
