"""REPAIR RUN — Task 1+2: MIN_LEG_HEIGHT x MIN_LEG_RETRACE geometry sweep.

Mechanical diagnostics only. NO fill simulation, NO exit battery, NO MFE/MAE,
NO R-multiple outcome. The one exception is a MINIMAL fill/stop-touch check
(fill boolean + same-bar stop touch only, nothing else retained) needed for
Task 2's "stop-touched-on-fill-bar rate" — explicitly called out in the repair
run's own report as a deliberate, narrow exception to the no-simulation rule,
because that specific metric is unobtainable without knowing the fill bar.

Per-TF (1/2/3/5m), per parameter cell: qualified count, triggers/session/day,
leg_height_pts / wick_width_pts / stop_dist_pts / r_available (median + p90),
stop-touched-on-fill-bar rate. Plus a session-level 1-minute TR noise floor
(computed once, not per cell) and stop_dist as a multiple of it.

Fit era only (2023-01-02..2025-05-31). Sealed rows are never touched.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date as Date

sys.path.insert(0, os.path.dirname(__file__))
from p_table_lib import (CONFIG, TICK, aggregate_tf, build_session_minutes,
                         run_tf_pipeline, session_window_utc, tick_round,
                         true_ranges)
from build_p_table import load_front_minutes, minute_map_for_day_window

CACHE = os.environ.get(
    "P_TABLE_CACHE",
    "/tmp/claude-0/-home-user-AI-trading-agents/a6ad12c8-81a9-57f1-b548-760dc4a1f9f9/scratchpad/cache")
FIT_END = CONFIG["FIT_END_DATE"]

HEIGHT_FRACS = [0.5, 1.0, 2.0, 3.0]
RETRACE_FRACS = [0.236, 0.382, 0.5]
CELLS = [(r, h) for h in HEIGHT_FRACS for r in RETRACE_FRACS]


def minimal_fill_stop_touch(direction, limit, stop, minutes, eligible_ts, session_end):
    """Fill boolean + same-bar stop-touch only. No MFE/MAE, no exit, no R."""
    tt = CONFIG["TRADE_THROUGH_TICKS"] * TICK
    live = [b for b in minutes if b.open_ts >= eligible_ts and b.open_ts < session_end]
    fill_cond = (lambda b: b.high >= limit + tt) if direction == -1 else \
                (lambda b: b.low <= limit - tt)
    stop_touch = (lambda b: b.high >= stop) if direction == -1 else \
                 (lambda b: b.low <= stop)
    for b in live:
        if fill_cond(b):
            return True, bool(stop_touch(b))
    return False, None


def stop_geo(cand, direction):
    buf = CONFIG["STOP_BUFFER_PTS"]
    stop = tick_round(cand.level_1 + buf) if direction == -1 else \
           tick_round(cand.level_1 - buf)
    limit = cand.fifty
    return stop, abs(limit - stop)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="")
    ap.add_argument("--partdir", default="")
    ap.add_argument("--merge", default="")
    args = ap.parse_args()

    if args.merge:
        merge(args.merge)
        return

    df, front = load_front_minutes(CACHE)
    dates = sorted({d for d in
                    __import__("pandas").to_datetime(list(front.keys()), utc=True)
                    .map(lambda ts: ts.tz_convert("America/New_York").date())})
    dates = [d for d in dates if d.isoformat() <= FIT_END]
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        dates = [d for k, d in enumerate(dates) if k % n == i]

    # cell -> tf -> list of per-event dicts (geometry only)
    events = {c: {tf: [] for tf in CONFIG["TFS_MIN"]} for c in CELLS}
    n_sessions = Counter()
    tr_pool = defaultdict(list)     # session -> [1m true ranges], noise floor

    for di, d in enumerate(dates):
        for session in CONFIG["SESSIONS"]:
            w_utc, s_utc, e_utc = session_window_utc(d, session)
            mm = minute_map_for_day_window(df, w_utc, e_utc)
            built = build_session_minutes(mm, d, session)
            if built is None:
                continue
            minutes, n_real, n_total = built
            n_sessions[session] += 1

            sess_bars = [b for b in minutes if b.open_ts >= s_utc and b.real]
            if sess_bars:
                tr_pool[session].extend(true_ranges(sess_bars))

            tf_bars_cache = {tf: aggregate_tf(minutes, tf) for tf in CONFIG["TFS_MIN"]}

            for cell in CELLS:
                retrace, height = cell
                for tf in CONFIG["TFS_MIN"]:
                    evs, _ = run_tf_pipeline(tf_bars_cache[tf], tf, retrace,
                                             s_utc, e_utc, height)
                    for e in evs:
                        if not e.qualified:
                            continue
                        cand = e.cand
                        stop, sd = stop_geo(cand, e.direction)
                        tdist = abs(cand.fifty - e.target_price) \
                            if not math.isnan(e.target_price) else float("nan")
                        r_avail = tdist / sd if sd > 0 and not math.isnan(tdist) \
                            else float("nan")
                        elig = next((b.open_ts for b in minutes
                                    if b.open_ts >= e.close_ts), e.close_ts)
                        filled, stop_touch = minimal_fill_stop_touch(
                            e.direction, cand.fifty, stop, minutes, elig, e_utc)
                        events[cell][tf].append(dict(
                            leg_height_pts=cand.pivot.leg_height,
                            wick_width_pts=cand.wick_width,
                            stop_dist_pts=sd, r_available=r_avail,
                            filled=filled, stop_touch_on_fill=stop_touch,
                            session=session))
        if (di + 1) % 50 == 0:
            print(f"  {di + 1}/{len(dates)} dates", flush=True)

    if args.shard:
        os.makedirs(args.partdir, exist_ok=True)
        tag = args.shard.replace("/", "_")
        out = dict(
            n_sessions={s: n for s, n in n_sessions.items()},
            tr_pool={s: v for s, v in tr_pool.items()},
            events={f"{r}|{h}": {str(tf): v for tf, v in tfd.items()}
                    for (r, h), tfd in events.items()})
        json.dump(out, open(f"{args.partdir}/part_{tag}.json", "w"))
        print(f"shard {args.shard} done -> {args.partdir}/part_{tag}.json")
        return
    write_report(events, n_sessions, tr_pool)


def merge(partdir):
    import glob
    n_sessions = Counter()
    tr_pool = defaultdict(list)
    events = {c: {tf: [] for tf in CONFIG["TFS_MIN"]} for c in CELLS}
    for p in sorted(glob.glob(f"{partdir}/part_*.json")):
        part = json.load(open(p))
        for s, n in part["n_sessions"].items():
            n_sessions[s] += n
        for s, v in part["tr_pool"].items():
            tr_pool[s].extend(v)
        for ck, tfd in part["events"].items():
            r, h = ck.split("|")
            cell = (float(r), float(h))
            for tfs, v in tfd.items():
                events[cell][int(tfs)].extend(v)
    write_report(events, n_sessions, tr_pool)


def _dist(vals):
    vals = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not vals:
        return None
    vals.sort()
    n = len(vals)
    return dict(n=n, median=round(statistics.median(vals), 3),
               p90=round(vals[int(0.9 * (n - 1))], 3))


def write_report(events, n_sessions, tr_pool):
    noise_floor = {s: round(statistics.median(v), 3) for s, v in tr_pool.items() if v}

    cells_out = {}
    for cell, tfd in events.items():
        retrace, height = cell
        cell_key = f"retrace={retrace}|height_atr={height}"
        all_ev = [e for tf in CONFIG["TFS_MIN"] for e in tfd[tf]]
        n_q = len(all_ev)
        by_sess = Counter(e["session"] for e in all_ev)
        tpd = {s: round(by_sess.get(s, 0) / max(1, n_sessions.get(s, 1)), 3)
              for s in n_sessions}
        per_tf = {}
        for tf in CONFIG["TFS_MIN"]:
            tf_ev = tfd[tf]
            fills = [e["filled"] for e in tf_ev]
            touches = [e["stop_touch_on_fill"] for e in tf_ev if e["filled"]]
            sd_dist = _dist([e["stop_dist_pts"] for e in tf_ev])
            per_tf_out = dict(
                n_qualified=len(tf_ev),
                leg_height_pts=_dist([e["leg_height_pts"] for e in tf_ev]),
                wick_width_pts=_dist([e["wick_width_pts"] for e in tf_ev]),
                stop_dist_pts=sd_dist,
                r_available=_dist([e["r_available"] for e in tf_ev]),
                fill_rate=round(sum(fills) / len(fills), 4) if fills else None,
                stop_touched_on_fill_bar_rate=(
                    round(sum(touches) / len(touches), 4) if touches else None),
            )
            if sd_dist:
                by_sess_sd = defaultdict(list)
                for e in tf_ev:
                    by_sess_sd[e["session"]].append(e["stop_dist_pts"])
                mult = {}
                for s, vs in by_sess_sd.items():
                    nf = noise_floor.get(s)
                    if nf:
                        mult[s] = round(statistics.median(vs) / nf, 3)
                per_tf_out["stop_dist_x_noise_floor_by_session"] = mult
                per_tf_out["mechanically_nonviable"] = bool(
                    mult and min(mult.values()) < 1.0)
            per_tf[str(tf)] = per_tf_out
        cells_out[cell_key] = dict(
            n_qualified_all_tf=n_q, triggers_per_session_per_day=tpd,
            per_tf=per_tf)

    out = dict(
        noise_floor_median_1m_TR_pts=noise_floor,
        cost_assumption_pts_round_trip=CONFIG["COST_RT_PTS"],
        cost_assumption_note="DECLARED constant, matching existing book "
                             "convention -- NOT measured (no book/spread data "
                             "exists in the fit era; all flow coverage lies in "
                             "the sealed span).",
        cells=cells_out)
    json.dump(out, open("output/p_table_geometry_sweep.json", "w"), indent=1)
    print("wrote output/p_table_geometry_sweep.json")
    print(json.dumps({k: v for k, v in out.items() if k != "cells"}, indent=1))


if __name__ == "__main__":
    main()
