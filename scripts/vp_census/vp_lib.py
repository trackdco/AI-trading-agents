"""Job 1 — Value-Area Excursion Census. Core library.

Spec: docs/SPEC-vp-excursion-census.md. Everything here is L0/L1
measurement machinery: profiles, excursions, outcomes. No entries, no
stops-as-policy, no P&L.

Conventions locked here (assistant rulings, logged in the trial ledger):
- Bars are Databento OHLCV-1m, ts_event OPEN-labeled (empirical probe
  scripts/check_bar_label.py). A bar stamped T covers [T, T+1min); its
  close is an event at T+1min. Every "close" comparison in this module
  uses close_ts = ts_event + 1min.
- Bins are aligned to absolute price: bin index = floor(price / width).
  Bin center = (idx + 0.5) * width; VAH/VAL are bin EDGES.
- poc_before_stop_S running extreme is initialised at the trigger bar's
  beyond-side extreme (the wick that produced the breaching close). A
  bar that both touches POC and re-extends >= S ticks is scored as NOT
  poc-first (conservative against the hypothesis; intrabar order is
  unknowable at 1m).
- Cluster collapse rule: the cluster's FIRST excursion represents it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TICK = 0.25
ET = "America/New_York"

# ---------------------------------------------------------------- loading

def load_master_bars(path: str = "data/reference/nq_1m_master.parquet") -> pd.DataFrame:
    df = pd.read_parquet(path)
    ts = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(ET)
    df = df.assign(ts_event=ts).sort_values("ts_event", kind="mergesort").reset_index(drop=True)
    # CME trading day: 18:00 (D-1) -> 17:00 (D). Label each bar with the
    # RTH calendar date it belongs to: bars at/after 18:00 belong to the
    # NEXT calendar day's session.
    t = df["ts_event"]
    session = t.dt.normalize() + pd.Timedelta(days=1) * (t.dt.hour >= 18)
    # weekend handling: Friday 18:00+ bars -> Saturday label; there is no
    # Saturday session. Sunday 18:00+ -> Monday (correct). Saturday-labelled
    # bars are Friday-evening Globex; roll them to the next Monday.
    wd = session.dt.weekday
    session = session + pd.to_timedelta(np.where(wd == 5, 2, np.where(wd == 6, 1, 0)), unit="D")
    df["session"] = session.dt.date
    return df


def load_footprint(paths: list[str]) -> pd.DataFrame:
    parts = [pd.read_parquet(p) for p in paths]
    fp = pd.concat(parts, ignore_index=True)
    ts = pd.to_datetime(fp["ts_minute"], utc=True).dt.tz_convert(ET)
    fp = fp.assign(ts_minute=ts)
    fp = fp.groupby(["ts_minute", "price"], as_index=False)["volume"].sum()
    fp = fp.sort_values(["ts_minute", "price"], kind="mergesort").reset_index(drop=True)
    t = fp["ts_minute"]
    session = t.dt.normalize() + pd.Timedelta(days=1) * (t.dt.hour >= 18)
    wd = session.dt.weekday
    session = session + pd.to_timedelta(np.where(wd == 5, 2, np.where(wd == 6, 1, 0)), unit="D")
    fp["session"] = session.dt.date
    return fp

# ---------------------------------------------------------- profile build

def _window_mask(ts: pd.Series, session_date, half_open_0930: bool = True) -> pd.Series:
    """Profile window: 18:00:00 ET prior CME day -> 09:29:59.999 ET on D.
    With open-labeled bars this is ts in [18:00 D-1eve, 09:30 D)."""
    d = pd.Timestamp(session_date, tz=ET)
    start = d - pd.Timedelta(days=1) + pd.Timedelta(hours=18)
    # weekend: Monday session opens Sunday 18:00 (2 days back from Monday? no:
    # Monday - 1 day = Sunday -> Sunday 18:00, correct). Tuesday..Friday: prior
    # calendar day. Monday: Sunday. Holiday-following sessions may span a dark
    # evening; the completeness flag catches those.
    if pd.Timestamp(session_date).weekday() == 0:
        start = d - pd.Timedelta(days=1) + pd.Timedelta(hours=18)
    end = d + pd.Timedelta(hours=9, minutes=30)
    return (ts >= start) & (ts < end), start, end


def expected_window_minutes(session_date) -> int:
    d = pd.Timestamp(session_date, tz=ET)
    start = d - pd.Timedelta(days=1) + pd.Timedelta(hours=18)
    end = d + pd.Timedelta(hours=9, minutes=30)
    return int((end - start).total_seconds() // 60)


def bar_histogram(bars: pd.DataFrame, bin_width: float) -> pd.Series:
    """Uniform distribution of each bar's volume across its high-low range,
    allocated to price bins proportionally to overlap. Index = bin idx."""
    lo = bars["low"].to_numpy(float)
    hi = bars["high"].to_numpy(float) + TICK  # price occupies [low, high+tick)
    vol = bars["volume"].to_numpy(float)
    acc: dict[int, float] = {}
    b0 = np.floor(lo / bin_width).astype(int)
    b1 = np.floor((hi - 1e-9) / bin_width).astype(int)
    for l, h, v, i0, i1 in zip(lo, hi, vol, b0, b1):
        if v == 0:
            continue
        span = h - l
        if i0 == i1:
            acc[i0] = acc.get(i0, 0.0) + v
            continue
        for i in range(i0, i1 + 1):
            seg_lo = max(l, i * bin_width)
            seg_hi = min(h, (i + 1) * bin_width)
            if seg_hi > seg_lo:
                acc[i] = acc.get(i, 0.0) + v * (seg_hi - seg_lo) / span
    s = pd.Series(acc, dtype=float)
    return s.sort_index()


def footprint_histogram(fp_win: pd.DataFrame, bin_width: float) -> pd.Series:
    idx = np.floor(fp_win["price"].to_numpy(float) / bin_width).astype(int)
    s = pd.Series(fp_win["volume"].to_numpy(float)).groupby(idx).sum()
    return s.sort_index()


def value_area(hist: pd.Series, bin_width: float, va_pct: float = 0.70,
               expansion: str = "paired") -> dict:
    """POC + VA from a binned histogram. Returns levels and tie count.

    POC tie rule (spec 2.6): centre bin closest to volume-weighted mean.
    paired expansion: compare the sum of the TWO bins above the region to
    the TWO below, add the larger pair; single: compare one bin each side.
    Tie between sides: the side whose nearest bin has more volume; still
    tied -> above (deterministic, logged via n_ties).
    """
    total = float(hist.sum())
    if total <= 0 or len(hist) == 0:
        return dict(poc=np.nan, vah=np.nan, val=np.nan, poc_ties=0)
    idxs = hist.index.to_numpy()
    vols = hist.to_numpy(float)
    vmax = vols.max()
    tie_mask = vols >= vmax - 1e-9
    n_ties = int(tie_mask.sum())
    if n_ties > 1:
        centers = (idxs + 0.5) * bin_width
        vwm = float((centers * vols).sum() / total)
        cand = idxs[tie_mask]
        poc_idx = int(cand[np.argmin(np.abs((cand + 0.5) * bin_width - vwm))])
    else:
        poc_idx = int(idxs[int(np.argmax(vols))])

    pos = {int(i): k for k, i in enumerate(idxs)}
    k_poc = pos[poc_idx]
    lo_k = hi_k = k_poc
    cum = vols[k_poc]
    step = 2 if expansion == "paired" else 1
    target = va_pct * total
    while cum < target - 1e-9:
        up = [vols[k] for k in range(hi_k + 1, min(hi_k + 1 + step, len(vols)))]
        dn = [vols[k] for k in range(max(lo_k - step, 0), lo_k)]
        s_up, s_dn = sum(up), sum(dn)
        if not up and not dn:
            break
        take_up = (s_up > s_dn) or (not dn)
        if abs(s_up - s_dn) <= 1e-9 and up and dn:
            take_up = up[0] >= dn[-1]
        if take_up:
            hi_k = min(hi_k + step, len(vols) - 1)
            cum += s_up
        else:
            new_lo = max(lo_k - step, 0)
            cum += s_dn
            lo_k = new_lo
    poc = (poc_idx + 0.5) * bin_width
    vah = (idxs[hi_k] + 1) * bin_width  # upper EDGE
    val = idxs[lo_k] * bin_width        # lower EDGE
    return dict(poc=poc, vah=vah, val=val, poc_ties=n_ties)


def build_profiles(bars: pd.DataFrame, sessions: list, bin_width: float = 1.0,
                   va_pct: float = 0.70, expansion: str = "paired",
                   construction: str = "bar_uniform",
                   fp: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    by_sess = dict(tuple(bars.groupby("session")))
    fp_by_sess = dict(tuple(fp.groupby("session"))) if fp is not None else {}
    for d in sessions:
        sb = by_sess.get(d)
        exp_min = expected_window_minutes(d)
        if sb is None:
            rows.append(dict(session_date=d, vah=np.nan, val=np.nan, poc=np.nan,
                             va_pct=va_pct, bin_width=bin_width, total_volume=0.0,
                             window_minutes=0, expected_minutes=exp_min,
                             profile_status="NO_BARS", poc_ties=0,
                             construction=construction, expansion=expansion,
                             win_high=np.nan, win_low=np.nan))
            continue
        mask, start, end = _window_mask(sb["ts_event"], d)
        win = sb.loc[mask]
        n_min = int(len(win))
        status = "OK" if n_min >= exp_min - 230 else "INCOMPLETE"
        if n_min == 0:
            rows.append(dict(session_date=d, vah=np.nan, val=np.nan, poc=np.nan,
                             va_pct=va_pct, bin_width=bin_width, total_volume=0.0,
                             window_minutes=0, expected_minutes=exp_min,
                             profile_status="NO_BARS", poc_ties=0,
                             construction=construction, expansion=expansion,
                             win_high=np.nan, win_low=np.nan))
            continue
        if construction == "bar_uniform":
            hist = bar_histogram(win, bin_width)
        elif construction == "footprint":
            fs = fp_by_sess.get(d)
            if fs is None:
                rows.append(dict(session_date=d, vah=np.nan, val=np.nan, poc=np.nan,
                                 va_pct=va_pct, bin_width=bin_width, total_volume=0.0,
                                 window_minutes=n_min, expected_minutes=exp_min,
                                 profile_status="NO_FOOTPRINT", poc_ties=0,
                                 construction=construction, expansion=expansion,
                                 win_high=np.nan, win_low=np.nan))
                continue
            fmask = (fs["ts_minute"] >= start) & (fs["ts_minute"] < end)
            fwin = fs.loc[fmask]
            if len(fwin) == 0:
                rows.append(dict(session_date=d, vah=np.nan, val=np.nan, poc=np.nan,
                                 va_pct=va_pct, bin_width=bin_width, total_volume=0.0,
                                 window_minutes=n_min, expected_minutes=exp_min,
                                 profile_status="NO_FOOTPRINT", poc_ties=0,
                                 construction=construction, expansion=expansion,
                                 win_high=np.nan, win_low=np.nan))
                continue
            hist = footprint_histogram(fwin, bin_width)
        else:
            raise ValueError(construction)
        lv = value_area(hist, bin_width, va_pct, expansion)
        rows.append(dict(session_date=d, vah=lv["vah"], val=lv["val"], poc=lv["poc"],
                         va_pct=va_pct, bin_width=bin_width,
                         total_volume=float(hist.sum()), window_minutes=n_min,
                         expected_minutes=exp_min, profile_status=status,
                         poc_ties=lv["poc_ties"], construction=construction,
                         expansion=expansion,
                         win_high=float(win["high"].max()),
                         win_low=float(win["low"].min())))
    out = pd.DataFrame(rows)
    out["frozen_at"] = "09:30:00 ET"
    return out

# ------------------------------------------------------------- excursions

REARM_MIN = 5
CLUSTER_MIN = 30
STOP_TICKS = (10, 20, 30, 40, 60, 80)
K_SWEEP = (5, 10, 15, 20, 30, 45, 60)


def census_session(rth: pd.DataFrame, vah: float, val: float, poc: float,
                   session_date) -> list[dict]:
    """All excursions for one session. rth = bars ts_event in [09:30,16:00),
    chronological. Close events occur at ts_event + 1min."""
    n = len(rth)
    if n == 0 or not np.isfinite(vah) or not np.isfinite(val):
        return []
    ts = rth["ts_event"].to_numpy()
    close = rth["close"].to_numpy(float)
    high = rth["high"].to_numpy(float)
    low = rth["low"].to_numpy(float)
    end_ts = pd.Timestamp(session_date, tz=ET) + pd.Timedelta(hours=16)
    out: list[dict] = []
    inside = (close <= vah) & (close >= val)

    for side, level, beyond in (("above", vah, close > vah), ("below", val, close < val)):
        armed = True
        i = 0
        while i < n:
            if armed and beyond[i]:
                start_i = i
                ret_i = None
                for j in range(i + 1, n):
                    if inside[j]:
                        ret_i = j
                        break
                out.append(_measure(rth, start_i, ret_i, side, vah, val, poc,
                                    session_date, ts, close, high, low))
                # re-arm: need >=REARM_MIN consecutive closes inside with no
                # close beyond THIS side, starting after the return close
                if ret_i is None:
                    break
                run = 0
                k = ret_i
                rearmed_at = None
                while k < n:
                    if inside[k] and not beyond[k]:
                        run += 1
                        if run >= REARM_MIN:
                            rearmed_at = k
                            break
                    elif beyond[k]:
                        run = 0
                    else:  # beyond the OTHER side: breaks the inside run
                        run = 0
                    k += 1
                if rearmed_at is None:
                    break
                i = rearmed_at + 1
                armed = True
            else:
                i += 1
    return out


def _measure(rth, start_i, ret_i, side, vah, val, poc, session_date,
             ts, close, high, low) -> dict:
    n = len(rth)
    sgn = 1.0 if side == "above" else -1.0
    level = vah if side == "above" else val
    start_ts = pd.Timestamp(ts[start_i]) + pd.Timedelta(minutes=1)  # close event
    entry_ref = float(close[start_i])
    last_i = n - 1
    fwd = slice(start_i + 1, n)          # bars after the trigger bar
    ret_end = ret_i if ret_i is not None else last_i

    # max beyond level before first close back inside (trigger bar included:
    # its wick created the breach)
    seg_hi = high[start_i: ret_end + 1]
    seg_lo = low[start_i: ret_end + 1]
    if side == "above":
        max_beyond = (seg_hi.max() - vah) / TICK
    else:
        max_beyond = (val - seg_lo.min()) / TICK

    def minutes_from_start(i):
        return float((pd.Timestamp(ts[i]) + pd.Timedelta(minutes=1) - start_ts)
                     .total_seconds() / 60.0)

    t_return = minutes_from_start(ret_i) if ret_i is not None else np.nan

    # POC touch / close-through, forward from trigger close (bars after trigger)
    touched_poc = False
    t_touch = np.nan
    closed_thru = False
    t_closed = np.nan
    reached_opp = False
    t_opp = np.nan
    for j in range(start_i + 1, n):
        crosses = (low[j] <= poc <= high[j])
        if not touched_poc and crosses:
            touched_poc = True
            t_touch = minutes_from_start(j)
        thru = (close[j] < poc) if side == "above" else (close[j] > poc)
        if not closed_thru and thru:
            closed_thru = True
            t_closed = minutes_from_start(j)
        opp = (low[j] <= val) if side == "above" else (high[j] >= vah)
        if not reached_opp and opp:
            reached_opp = True
            t_opp = minutes_from_start(j)
        if touched_poc and closed_thru and reached_opp:
            break

    # MFE / MAE in the rotation direction (rotation = back toward POC)
    if start_i + 1 <= last_i:
        f_hi = high[start_i + 1:]
        f_lo = low[start_i + 1:]
        if side == "above":
            mfe = (entry_ref - f_lo.min()) / TICK
            mae = (f_hi.max() - entry_ref) / TICK
        else:
            mfe = (f_hi.max() - entry_ref) / TICK
            mae = (entry_ref - f_lo.min()) / TICK
    else:
        mfe = mae = np.nan

    # poc_before_stop_S walk
    stop_res = {}
    for S in STOP_TICKS:
        run_ext = high[start_i] if side == "above" else low[start_i]
        verdict = False
        decided = False
        for j in range(start_i + 1, n):
            ext_hit = (high[j] >= run_ext + S * TICK) if side == "above" \
                else (low[j] <= run_ext - S * TICK)
            poc_hit = (low[j] <= poc <= high[j])
            if ext_hit:            # stop first (incl. same-bar ambiguity)
                verdict, decided = False, True
                break
            if poc_hit:
                verdict, decided = True, True
                break
            run_ext = max(run_ext, high[j]) if side == "above" else min(run_ext, low[j])
        stop_res[f"poc_before_stop_{S}"] = verdict if decided else False
        stop_res[f"resolved_stop_{S}"] = decided

    row = dict(session_date=session_date, side=side,
               excursion_start=start_ts, entry_ref_price=entry_ref,
               vah=vah, val=val, poc=poc,
               t_return_inside=t_return, max_beyond_ticks=float(max_beyond),
               touched_poc=touched_poc, t_touched_poc=t_touch,
               closed_through_poc=closed_thru, t_closed_through_poc=t_closed,
               reached_opposite_edge=reached_opp, t_reached_opposite_edge=t_opp,
               mfe_ticks=float(mfe) if np.isfinite(mfe) else np.nan,
               mae_ticks=float(mae) if np.isfinite(mae) else np.nan)
    row.update(stop_res)
    for K in K_SWEEP:
        row[f"failed_{K}"] = bool(np.isfinite(t_return) and t_return <= K)
    return row


def run_census(bars: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    by_sess = dict(tuple(bars.groupby("session")))
    rows: list[dict] = []
    ok = profiles[profiles["profile_status"] == "OK"]
    for _, pr in ok.iterrows():
        d = pr["session_date"]
        sb = by_sess.get(d)
        if sb is None:
            continue
        dts = pd.Timestamp(d, tz=ET)
        m = (sb["ts_event"] >= dts + pd.Timedelta(hours=9, minutes=30)) & \
            (sb["ts_event"] < dts + pd.Timedelta(hours=16))
        rth = sb.loc[m].sort_values("ts_event", kind="mergesort").reset_index(drop=True)
        rows.extend(census_session(rth, pr["vah"], pr["val"], pr["poc"], d))
    if not rows:
        return pd.DataFrame()
    ex = pd.DataFrame(rows)
    ex = ex.sort_values(["session_date", "side", "excursion_start"],
                        kind="mergesort").reset_index(drop=True)
    # clusters: same side, same session, starts < CLUSTER_MIN apart chain up
    gap = ex.groupby(["session_date", "side"])["excursion_start"].diff()
    new_cluster = gap.isna() | (gap > pd.Timedelta(minutes=CLUSTER_MIN))
    ex["cluster_id"] = new_cluster.cumsum().astype(int)
    ex["session_id"] = pd.to_datetime(ex["session_date"]).astype(str)
    return ex
