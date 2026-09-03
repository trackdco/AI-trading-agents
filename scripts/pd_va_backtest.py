#!/usr/bin/env python3
"""PD VAH/VAL BREAK-RETEST — his flight-note strategy, mechanically, all history.

    python -m scripts.pd_va_backtest

His spec (2026-09-02, verbatim intent):
  * 3m candle CLOSES through prior-day VAH or VAL -> limit order at the retest
    of the level. Direction = the direction of the crossing close (stop goes
    beyond the candle that closed through, so it is a continuation entry).
  * Asia + London are the strategy; full day simulated anyway so NY's expected
    failure is measured, not assumed.
  * Stop: beyond the close-through candle. If the close-through candle's OPEN
    is < 5pt from the level, use the candle before it as well (stop beyond
    both). 5pt minimum risk floor after all of that. One tick of air (0.25).
  * Fixed-R targets, swept: 1.0 / 1.5 / 2.0 / 2.5 / 3.0.
  * Close-through depth swept: any tick / 1pt / 2pt / 3pt beyond the level.

Interpretation decisions (documented because the note is a note):
  - PD VAH/VAL from the certified `volume_profile` (agent_context) over the
    full prior session-day (prev 18:00 anchor -> this 18:00 anchor), exactly
    as `build_levels` computes `prior_day`, rounded to tick. KNOWN CAVEAT:
    that function carries a ~30pt worst-case residual vs TradingView's own
    profile rows; his hand-test marked levels off the chart. The depth sweep
    absorbs some of this, not all.
  - "Closes through" = a CROSSING close: previous 3m close on or inside the
    level, this close beyond it by >= max(depth, one tick).
  - Both levels, both directions, tagged per leg:
      VAH up-cross  = breakout_up      VAH down-cross = reversion_down
      VAL down-cross = breakout_down   VAL up-cross   = reversion_up
    so the report shows which legs carry it rather than presuming.
  - One position at a time. One resting limit at a time; a new signal while
    flat replaces an unfilled pending (latest signal wins). Signals while in
    a position are ignored. Pendings rest until 16:00 at the latest.
  - Fill = first 1m bar at/after the signal candle's end that touches the
    level (long: low <= L, short: high >= L), filled AT the level.
  - Exits walked on 1m bars from the fill bar inclusive; stop checked before
    target inside any single bar (conservative); same-bar stop+target counted
    and reported. Session end (t0+23h) force-flats at last close for partial R.
  - Signals accepted 19:00 -> 15:55 (full-day sim). The Asia/London strategy
    is the subset with signal AND fill before 09:30 (pending pulled at the
    bell) — provably identical to a separate AL-only sim because NY signals
    cannot affect earlier occupancy.

Outputs: printed progress + per-trade dump for the report layer
  output/analysis/pd_va_trades.jsonl.gz  (every config, every trade)
  output/analysis/pd_va_days.json        (per-day PD range / VA geometry)
No lookahead anywhere: levels are prior-day, signals are closed candles,
fills/exits read strictly forward bars.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402
from scripts.agent_context import volume_profile                  # noqa: E402

TICK = 0.25
MIN_RISK = 5.0
BIN_W = 1.0
DEPTHS = (0.0, 1.0, 2.0, 3.0)          # 0.0 -> any tick beyond
TARGETS = (1.0, 1.5, 2.0, 2.5, 3.0)

# per-instrument constants, each derived from that instrument's own tape
# (ratios anchored on the NQ certification: floor ~0.7x the recent median
# 1m candle, depth grid ~0.14/0.28/0.42x, profile bin ~1/7x)
INSTRUMENTS = {
    "nq": dict(tick=0.25, min_risk=5.0, bin_w=1.0,
               depths=(0.0, 1.0, 2.0, 3.0), bars=None, rolls=None),
    "gc": dict(tick=0.10, min_risk=1.5, bin_w=0.3,
               depths=(0.0, 0.3, 0.6, 0.9),
               bars="data/reference/gc_1m.parquet",
               rolls="data/reference/gc_roll_days.json"),
}
SIG_START_H = 1.0                      # 19:00 session-relative
SIG_END_H = 21 + 55 / 60               # signal candles must END by 15:55
PEND_CUT_H = 22.0                      # resting limits die at 16:00
SESS_H = 23.0

LEG = {("vah", 1): "breakout_up", ("vah", -1): "reversion_down",
       ("val", -1): "breakout_down", ("val", 1): "reversion_up"}


def window_of(hrs: float) -> str:
    if hrs < 9.0:
        return "ASIA"
    if hrs < 15.5:
        return "LONDON"
    return "NY"


def day_signals(c3, vah, val, depth, tf=3):
    """Crossing closes of either level on the signal-TF candles, chronological."""
    thr = max(depth, TICK)
    out = []
    cl = c3.close.to_numpy()
    op = c3.open.to_numpy()
    hi = c3.high.to_numpy()
    lo = c3.low.to_numpy()
    ends = c3.index + pd.Timedelta(minutes=tf)
    for name, L in (("vah", vah), ("val", val)):
        for i in range(1, len(c3)):
            d = 0
            if cl[i - 1] <= L and cl[i] >= L + thr:
                d = 1
            elif cl[i - 1] >= L and cl[i] <= L - thr:
                d = -1
            if not d:
                continue
            out.append({
                "t": ends[i], "dir": d, "level_name": name, "L": L,
                "ct_open": op[i], "ct_hi": hi[i], "ct_lo": lo[i],
                "pv_hi": hi[i - 1], "pv_lo": lo[i - 1], "close": cl[i],
            })
    # same-candle double-cross (huge candle, narrow VA): trade the level
    # nearest the close — sort so it comes first, keep-first on dedupe
    out.sort(key=lambda s: (s["t"], abs(s["close"] - s["L"])))
    ded = {}
    for s in out:
        ded.setdefault(s["t"], s)
    return [ded[t] for t in sorted(ded)]


def stop_for(sig):
    """His stop rule: beyond the close-through candle (+1 tick); if that
    candle's open is <5pt from the level, beyond the prior candle too;
    5pt minimum risk floor."""
    L, d = sig["L"], sig["dir"]
    use_prev = abs(sig["ct_open"] - L) < MIN_RISK
    if d == 1:
        ref = min(sig["ct_lo"], sig["pv_lo"]) if use_prev else sig["ct_lo"]
        stop = ref - TICK
        if L - stop < MIN_RISK:
            stop = L - MIN_RISK
    else:
        ref = max(sig["ct_hi"], sig["pv_hi"]) if use_prev else sig["ct_hi"]
        stop = ref + TICK
        if stop - L < MIN_RISK:
            stop = L + MIN_RISK
    return stop


def trend_flag(ts, hi, lo, cl, t0_ns, x_pct=0.35):
    """Per-bar trend-DAY flag, causal, LATCHED: the first close >= x_pct
    of the Asia open beyond that open marks the day trending in that
    direction from that minute onward (T74: the day has revealed itself);
    a later close through the opposite threshold re-latches the other way
    (V-day). 0 before any threshold prints.

    Design iterations, both amended before any aggregate filtered result
    was read: (1) a 10pt never-revisited grace failed to arm on known
    drive days — one median 1m candle of early wiggle killed it; (2) an
    unlatched "currently stretched" flag armed but never intersected the
    trades — signals fire at PD levels, and price AT a level is rarely
    stretched at that same minute (0-1 skips on known trend days). The
    latch is the operative form of his hypothesis: counter-trend fades
    at level touches ON revealed trend days are the bleed."""
    n = len(ts)
    flag = np.zeros(n, dtype=np.int8)
    a0 = np.searchsorted(ts, t0_ns + int(3.6e12))          # 19:00
    if a0 >= n:
        return flag
    ao = float(cl[a0])  # first Asia bar close as the open anchor's proxy
    X = ao * x_pct / 100.0
    net = cl[a0:] - ao
    s = np.zeros(n - a0, dtype=np.int8)
    s[net >= X] = 1
    s[net <= -X] = -1
    nz = np.flatnonzero(s)
    if len(nz):
        last = np.maximum.accumulate(np.where(s != 0, np.arange(n - a0), -1))
        flag[a0:][last >= 0] = s[last[last >= 0]]
    return flag


def simulate_day(ts, hi, lo, cl, sigs, pend_cut_idx, target_r,
                 fill_through=False, sar=False, counters=None,
                 entry_off=0.0, fixed_stop=None, tflag=None,
                 runner=False, runner_tp2=None, runner_stop="be",
                 block=None):
    """One forward pass, one position at a time, latest pending wins.

    fill_through=True is the adverse-selection sensitivity: a fill counts
    only if price trades one full tick THROUGH the level (guaranteed fill),
    still booked at the level. Kills the bounce-to-the-tick winners a real
    resting limit might miss; the honest lower bound on fill quality.

    sar=True is his 2026-09-02 rule: an opposing-direction crossing close
    printing MID-TRADE flattens the position at that 3m close, and the
    opposing signal is then worked as the next retest entry (the flip
    trade uses the normal entry mechanism). Exits booked res="SAR" with
    the mark-to-close partial R; WR convention elsewhere keeps counting
    only TARGET vs STOP.

    entry_off (points) is his front-run adjustment: the limit rests that
    far on the NEAR side of the level (long: above it, short: below it),
    so the fill is guaranteed whenever price merely approaches the level
    that closely, at the cost of a worse entry on every trade. With
    fill_through, off=0.25 buys the touch-fill fill set with certainty
    for one tick per trade. Stops stay structure-anchored, so risk widens
    by the offset too.

    runner=True is his 2026-09-03 partial+runner build: when the target
    prints, HALF banks at target_r and the other half free-rolls with the
    stop at breakeven (entry). The runner dies on the first of: BE touch
    (0R), an opposing crossing close (SAR mark — chop kills it fast,
    drives keep it alive), runner_tp2 if given, or session end. The
    runner does NOT occupy — new signals trade normally (prop frequency
    preserved) — and at most one runner is alive at a time (a target
    print while one rides banks in full at target_r). Stopped-before-
    target trades are unchanged at −1R full size. Trade r is the blend:
    0.5*target_r + 0.5*runner_r; fields r_run/run_res carry the detail.

    counters, if a dict, accumulates the signal funnel:
    sig / skip_in_pos / replaced / expired / filled."""
    trades = []
    i = 0
    t_free = ts[0] - 1
    n = len(ts)
    thru = TICK if fill_through else 0.0
    runner_until = -1                      # bar idx the live runner dies at

    def bump(k):
        if counters is not None:
            counters[k] = counters.get(k, 0) + 1

    while i < len(sigs):
        s = sigs[i]
        t_sig = s["t"].value
        if t_sig <= t_free:
            bump("skip_in_pos")
            i += 1
            continue
        if tflag is not None:
            fi = np.searchsorted(ts, t_sig) - 1
            if 0 <= fi < n and tflag[fi] * s["dir"] < 0:
                bump("skip_counter_trend")   # regime on, signal against it
                i += 1
                continue
        sig_idx0 = np.searchsorted(ts, t_sig)
        if block is not None and block[0] <= sig_idx0 < block[1]:
            # his 2026-09-03 news rule: high-impact release in pre-market
            # (08:00-09:30) -> no new entries in that window. SAR flattens
            # still fire (this skip is entry-only); open positions ride.
            bump("skip_news")
            i += 1
            continue
        bump("sig")
        start = np.searchsorted(ts, t_sig)
        if start >= n:
            break
        nxt = sigs[i + 1]["t"].value if i + 1 < len(sigs) else None
        nxt_idx = np.searchsorted(ts, nxt) if nxt is not None else n
        cancel = min(nxt_idx, pend_cut_idx, n)
        if block is not None and start < block[0]:
            # sit out entirely: a resting limit from before 08:00 is pulled
            # at the window open (the June-10 case: stale pending filled by
            # the 08:30 news candle and stopped same minute)
            cancel = min(cancel, block[0])
        L, d = s["L"], s["dir"]
        E = L + d * entry_off
        seg_lo, seg_hi = lo[start:cancel], hi[start:cancel]
        touch = (seg_lo <= E - thru) if d == 1 else (seg_hi >= E + thru)
        if not touch.any():
            bump("replaced" if cancel == nxt_idx and nxt_idx < min(pend_cut_idx, n)
                 else "expired")
            i += 1
            continue
        bump("filled")
        fill = start + int(np.argmax(touch))
        # fixed_stop: his 2026-09-02 experiment — a flat S-point bracket off
        # the level, structure ignored entirely (no escalation, no floor)
        stop = (L - d * fixed_stop) if fixed_stop else stop_for(s)
        risk = abs(E - stop)
        tgt = E + d * target_r * risk
        w_lo, w_hi = lo[fill:], hi[fill:]
        if d == 1:
            s_hit = w_lo <= stop
            t_hit = w_hi >= tgt
        else:
            s_hit = w_hi >= stop
            t_hit = w_lo <= tgt
        s_idx = fill + int(np.argmax(s_hit)) if s_hit.any() else n
        t_idx = fill + int(np.argmax(t_hit)) if t_hit.any() else n
        # uncapped favourable run before the stop prints, ignoring the target
        # and any SAR exit — the setup's potential, for target-band selection
        # (his "most of the winners would have run for 2r" check). The stop
        # bar itself is excluded: intrabar order there is unknowable.
        s_rel = (s_idx if s_idx < n else n) - fill
        if s_rel > 0:
            run_r = ((float(w_hi[:s_rel].max()) - E) if d == 1
                     else (E - float(w_lo[:s_rel].min()))) / risk
        else:
            run_r = 0.0
        sar_idx, sar_px = n + 1, None
        if sar:
            for j in range(i + 1, len(sigs)):
                if sigs[j]["dir"] == -d and sigs[j]["t"].value > ts[fill]:
                    # close prints at the candle boundary: it pre-empts any
                    # stop/target touch in bars at/after that boundary
                    sar_idx = int(np.searchsorted(ts, sigs[j]["t"].value))
                    sar_px = sigs[j]["close"]
                    break
        ambig = s_idx == t_idx and s_idx < n
        first = min(s_idx, t_idx)
        r_run, run_res = None, None
        if sar_idx <= first and sar_idx <= n:     # flatten on opposing close
            exit_idx = min(sar_idx, n - 1)
            r = d * (sar_px - E) / risk
            res = "SAR"
        elif s_idx <= t_idx and s_idx < n:        # stop first (ties -> stop)
            exit_idx, r = s_idx, -1.0
            res = "STOP"
        elif t_idx < s_idx:
            exit_idx, r = t_idx, target_r
            res = "TARGET"
            if runner and t_idx >= runner_until:
                # half banks at target; half free-rolls from the TP1 bar.
                # runner_stop "be": stop at entry (0R stop-out);
                # runner_stop "orig": the structural stop stays (-1R
                # stop-out, blended 0.0 worst case — his 50/50 doctrine).
                # Conservative: the TP1 bar itself can stop the runner.
                rs_px = E if runner_stop == "be" else stop
                rs_r = 0.0 if runner_stop == "be" else -1.0
                w2_lo, w2_hi = lo[t_idx:], hi[t_idx:]
                be_hit = (w2_lo <= rs_px) if d == 1 else (w2_hi >= rs_px)
                be_idx = t_idx + int(np.argmax(be_hit)) if be_hit.any() else n
                opp_idx, opp_px = n + 1, None
                for sj in sigs:
                    if sj["dir"] == -d and sj["t"].value > ts[t_idx]:
                        opp_idx = int(np.searchsorted(ts, sj["t"].value))
                        opp_px = sj["close"]
                        break
                tp2_idx = n + 1
                if runner_tp2:
                    tgt2 = E + d * runner_tp2 * risk
                    t2 = (w2_hi >= tgt2) if d == 1 else (w2_lo <= tgt2)
                    tp2_idx = t_idx + int(np.argmax(t2)) if t2.any() else n + 1
                if opp_idx <= min(be_idx, tp2_idx, n - 1):
                    r_run, run_res = d * (opp_px - E) / risk, "SAR"
                    runner_until = opp_idx
                elif be_idx <= min(tp2_idx, n - 1):
                    r_run, run_res = rs_r, "BE" if runner_stop == "be" else "RSTOP"
                    runner_until = be_idx
                elif tp2_idx <= n - 1:
                    r_run, run_res = runner_tp2, "TP2"
                    runner_until = tp2_idx
                else:
                    r_run, run_res = d * (cl[-1] - E) / risk, "EOD"
                    runner_until = n - 1
                r = 0.5 * target_r + 0.5 * r_run
            elif runner:
                run_res = "BANKED_FULL"    # a runner already rides; full out
        else:
            exit_idx, r = n - 1, d * (cl[-1] - E) / risk
            res = "FLAT"
        hrs = (t_sig - ts[0]) / 3.6e12
        trades.append({
            "t_sig_hrs": round(hrs, 3), "window": window_of(hrs),
            "fill_hrs": round((ts[fill] - ts[0]) / 3.6e12, 3),
            "leg": LEG[(s["level_name"], d)], "dir": d,
            "entry": E, "stop": round(stop, 2), "risk": round(risk, 2),
            "res": res, "r": round(r, 4), "pts": round(r * risk, 2),
            "run_r": round(max(run_r, 0.0), 3),
            "r_run": None if r_run is None else round(r_run, 4),
            "run_res": run_res,
            "ambig": bool(ambig), "hold_min": int((ts[exit_idx] - ts[fill]) / 6e10),
        })
        if res == "SAR":
            # free exactly AT the opposing close so that very signal is the
            # next one processed (the flip trade), not skipped as in-position
            t_free = ts[min(sar_idx, n - 1)] - 1
        else:
            t_free = ts[exit_idx]
        i += 1
    return trades


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fill-through", action="store_true",
                    help="fills require a tick THROUGH the level (adverse-"
                         "selection sensitivity); writes *_through dump")
    ap.add_argument("--sar", action="store_true",
                    help="his stop-and-reverse rule: opposing crossing close "
                         "mid-trade flattens at that close and works the flip")
    ap.add_argument("--tf", type=int, default=3,
                    help="signal candle timeframe in minutes (default 3)")
    ap.add_argument("--entry-offset", type=float, default=0.0,
                    help="rest the limit this many POINTS on the near side "
                         "of the level (0.25 = 1 tick front-run)")
    ap.add_argument("--fixed-stop", type=float, default=None,
                    help="flat S-point stop off the level, structure ignored")
    ap.add_argument("--trend-filter", action="store_true",
                    help="with-trend-only regime filter: skip counter-trend "
                         "signals while the drive flag is on (flatten still "
                         "fires; the flip is not taken)")
    ap.add_argument("--trend-x-pct", type=float, default=0.35,
                    help="drive threshold as %% of Asia open (default 0.35)")
    ap.add_argument("--runner", action="store_true",
                    help="partial+runner exit: half banks at target, half "
                         "free-rolls at breakeven until BE/opposing close/"
                         "TP2/EOD")
    ap.add_argument("--runner-tp2", type=float, default=None,
                    help="optional fixed R target for the runner half")
    ap.add_argument("--runner-stop", choices=("be", "orig"), default="be",
                    help="runner stop: breakeven (default) or the original "
                         "structural stop")
    ap.add_argument("--news-gate", action="store_true",
                    help="his 2026-09-03 rule: on days with a high-impact "
                         "USD release in pre-market (08:00-09:30 ET), take "
                         "no entries in that window and pull pendings at "
                         "08:00 (data/reference/news_archive.csv)")
    ap.add_argument("--instrument", choices=tuple(INSTRUMENTS), default="nq",
                    help="which tape: constants + bars swap per instrument")
    a = ap.parse_args()
    inst = INSTRUMENTS[a.instrument]
    global TICK, MIN_RISK, BIN_W, DEPTHS
    TICK, MIN_RISK = inst["tick"], inst["min_risk"]
    BIN_W, DEPTHS = inst["bin_w"], inst["depths"]
    suffix = ((f"_{a.instrument}" if a.instrument != "nq" else "")
              + ("_sar" if a.sar else "") + ("_through" if a.fill_through else "")
              + (f"_tf{a.tf}" if a.tf != 3 else "")
              + (f"_off{int(round(a.entry_offset / 0.25))}" if a.entry_offset else "")
              + (f"_fs{a.fixed_stop:g}" if a.fixed_stop else "")
              + (f"_twf{a.trend_x_pct:g}" if a.trend_filter else "")
              + ((f"_run{a.runner_stop}{f'tp{a.runner_tp2:g}' if a.runner_tp2 else ''}")
                 if a.runner else "")
              + ("_ng" if a.news_gate else ""))
    news_days = set()
    if a.news_gate:
        nf = pd.read_csv(ROOT / "data/reference/news_archive.csv")
        hi_pm = nf[(nf.impact == "high")
                   & (nf.time_et >= "08:00") & (nf.time_et < "09:30")]
        news_days = set(hi_pm.date)
        print(f"news gate: {len(news_days)} pre-market high-impact dates "
              f"({min(news_days)} -> {max(news_days)})", flush=True)
    if inst["bars"]:
        b = pd.read_parquet(ROOT / inst["bars"])
        b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(OB.NY)
        bars = b.set_index("mi").sort_index()[
            ["open", "high", "low", "close", "volume"]]
        roll_skip = set(json.loads((ROOT / inst["rolls"]).read_text()))
        print(f"{a.instrument}: {len(bars):,} bars, "
              f"{len(roll_skip)} roll days excluded", flush=True)
    else:
        bars = OB.get_bars()
        roll_skip = set()
    days = OB.all_session_days(bars)
    trades_out = gzip.open(
        ROOT / f"output/analysis/pd_va_trades{suffix}.jsonl.gz", "wt")
    per_day_meta = {}

    day_cache = []
    prev_t0 = None
    for day in days:
        t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
        if prev_t0 is None:
            prev_t0 = t0
            continue
        pseg = bars[(bars.index >= prev_t0) & (bars.index < t0)]
        sess = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=SESS_H))]
        prev_t0 = t0
        if len(pseg) < 300 or len(sess) < 600 or day in roll_skip:
            continue    # roll days: prior profile sits in the old contract
        _, val, vah = volume_profile(pseg, bin_w=BIN_W)
        if not (np.isfinite(val) and np.isfinite(vah)):
            continue
        vah = round(vah / TICK) * TICK
        val = round(val / TICK) * TICK
        c3 = sess.resample(f"{a.tf}min").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
        hrs3 = (c3.index - t0).total_seconds() / 3600
        # keep one pre-19:00 candle as the crossing's prev; ends by 15:55
        c3 = c3[(hrs3 >= SIG_START_H - a.tf / 60 - 0.02)
                & (hrs3 + a.tf / 60 <= SIG_END_H + 1e-6)]
        if len(c3) < 50:
            continue
        ts = sess.index.view("int64")
        pend_cut = int(np.searchsorted(ts, (t0 + pd.Timedelta(hours=PEND_CUT_H)).value))
        day_cache.append((day, ts, sess.high.to_numpy(), sess.low.to_numpy(),
                          sess.close.to_numpy(), c3, vah, val, pend_cut))
        per_day_meta[day] = {
            "pd_range": round(float(pseg.high.max() - pseg.low.min()), 2),
            "vah": vah, "val": val, "va_width": round(vah - val, 2)}

    print(f"{len(day_cache)} tradeable days "
          f"({day_cache[0][0]} -> {day_cache[-1][0]})", flush=True)

    n_cfg = 0
    funnel = {}
    for depth in DEPTHS:
        sig_cache = [day_signals(c3, vah, val, depth, tf=a.tf)
                     for (_, _, _, _, _, c3, vah, val, _) in day_cache]
        for tr in TARGETS:
            n_cfg += 1
            n_trades = 0
            cnt = funnel.setdefault(f"depth{depth:g}_R{tr:g}", {})
            for (day, ts, hi, lo, cl, _, _, _, pcut), sigs in zip(day_cache, sig_cache):
                if not sigs:
                    continue
                tfl = None
                if a.trend_filter:
                    t0_ns = pd.Timestamp(f"{day} 18:00", tz=OB.NY).value
                    tfl = trend_flag(ts, hi, lo, cl, t0_ns, x_pct=a.trend_x_pct)
                blk = None
                if a.news_gate:
                    t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
                    morning = str((t0 + pd.Timedelta(hours=15)).date())
                    if morning in news_days:
                        blk = (int(np.searchsorted(ts, (t0 + pd.Timedelta(hours=14)).value)),
                               int(np.searchsorted(ts, (t0 + pd.Timedelta(hours=15.5)).value)))
                for t in simulate_day(ts, hi, lo, cl, sigs, pcut, tr,
                                      fill_through=a.fill_through,
                                      sar=a.sar, counters=cnt,
                                      entry_off=a.entry_offset,
                                      fixed_stop=a.fixed_stop, tflag=tfl,
                                      runner=a.runner,
                                      runner_tp2=a.runner_tp2,
                                      runner_stop=a.runner_stop,
                                      block=blk):
                    t.update({"day": day, "depth": depth, "target_r": tr})
                    trades_out.write(json.dumps(t) + "\n")
                    n_trades += 1
            print(f"[{n_cfg}/{len(DEPTHS) * len(TARGETS)}] depth={depth} "
                  f"R={tr}: {n_trades} trades", flush=True)
    trades_out.close()
    days_name = ("pd_va_days.json" if a.instrument == "nq"
                 else f"pd_va_days_{a.instrument}.json")
    (ROOT / "output/analysis" / days_name).write_text(
        json.dumps(per_day_meta))
    (ROOT / f"output/analysis/pd_va_funnel{suffix}.json").write_text(
        json.dumps(funnel, indent=1))
    print(f"DONE -> output/analysis/pd_va_trades{suffix}.jsonl.gz", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
