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
import math
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402
from scripts.agent_context import (anchored_weekly_profile,       # noqa: E402
                                   volume_profile)

TICK = 0.25
PX_DP = 2          # price decimals in the dump; recomputed per instrument
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
    # ES (e-mini S&P), constants at the same ratios off its own tape.
    # Median active-session 1m candle 1.75pt = 7.0 TICKS (NQ 28, GC 21):
    # FAILS the >=20-tick screen in docs/FINDINGS-6e-euro-port.md S5. Run
    # anyway because ES sits between GC (works) and 6E (dead) and locates
    # the boundary.
    "es": dict(tick=0.25, min_risk=1.25, bin_w=0.25,
               depths=(0.0, 0.25, 0.5, 0.75),
               bars="data/reference/es_1m.parquet",
               rolls="data/reference/es_roll_days.json"),
    # 6E (euro FX future), constants at the same ratios off its own tape.
    # Median active-session 1m candle is 3.0 TICKS (NQ 28, GC 21), so the
    # ratio-derived profile bin lands sub-tick and is floored at one tick -
    # the first sign the grid is too coarse for this grammar.
    "6e": dict(tick=0.00005, min_risk=0.0001, bin_w=0.00005,
               depths=(0.0, 0.00005, 0.0001, 0.00015),
               bars="data/reference/6e_1m.parquet",
               rolls="data/reference/6e_roll_days.json"),
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



def conviction_tier(run_hi, run_lo, hi, lo, si, fill, L, d, pd_range):
    """Excursion + session progress at FILL time (2026-09-03 audit).

    ex   = furthest the tape ran PAST the level between the signal
           candle's last bar (si) and the bar BEFORE the fill, in points.
           The fill bar is excluded: its intrabar order is unknowable, and
           a live executor amending a resting order can only have acted on
           bars that already closed.
    sess = session range so far at the signal bar / prior-day range.
    """
    seg_hi, seg_lo = hi[si:max(fill, si + 1)], lo[si:max(fill, si + 1)]
    ex = (float(seg_hi.max()) - L) if d == 1 else (L - float(seg_lo.min()))
    sess = ((float(run_hi[si]) - float(run_lo[si])) / pd_range
            if pd_range and pd_range > 0 else float("nan"))
    return max(ex, 0.0), sess


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


def merge_levels(fams, floor):
    """His 2026-09-03 proximity rule: levels within one stop-floor of each
    other MERGE at session start - the stronger family keeps the level,
    the weaker book skips it for the day. Priority = measured standalone
    strength (S25). Deterministic, ex-ante, no knobs."""
    PRI = ("va", "wva", "pdhl", "poc", "wpoc")
    pts = []
    for f, (v1, v2) in fams.items():
        for slot, v in (("hi", v1), ("lo", v2)):
            if v is not None and np.isfinite(v):
                pts.append((float(v), f, slot))
    dropped = 0
    changed = True
    while changed:
        changed = False
        pts.sort()
        for i in range(len(pts) - 1):
            if pts[i + 1][0] - pts[i][0] <= floor:
                a_, b_ = pts[i], pts[i + 1]
                drop = a_ if PRI.index(a_[1]) > PRI.index(b_[1]) else b_
                pts.remove(drop)
                dropped += 1
                changed = True
                break
    keep = {(f, slot) for _, f, slot in pts}
    out = {}
    for f, (v1, v2) in fams.items():
        k1 = v1 if (f, "hi") in keep and v1 is not None else np.nan
        k2 = v2 if (f, "lo") in keep and v2 is not None else np.nan
        if np.isfinite(k1) or np.isfinite(k2):
            out[f] = (k1, k2)
    return out, dropped


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
                 block=None, max_risk=None, pd_range=None,
                 conviction=False, arm_after=None, thru_ticks=1,
                 arm_delay=0):
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

arm_after (points as a MULTIPLE of the trade's own risk) is his
    2026-09-03 arm-after-displacement rule: the limit rests but is NOT
    live until price has traded arm_after x risk BEYOND the level. Only
    then can it fill. Unlike conviction sizing (which leaves the trade set
    untouched) this changes occupancy: a pending that never displaces
    expires without filling, freeing the book for the next signal, and a
    pending that displaces late fills later than it otherwise would.
    Conservative on intrabar order: the arming bar must be STRICTLY
    before the touch bar, because within one bar it is unknowable whether
    the run past the level came before or after the pullback to it. The
    signal candle's own last bar counts toward arming (its high/low is
    known at the signal close, so it is legal information).

    counters, if a dict, accumulates the signal funnel:
    sig / skip_in_pos / replaced / expired / filled."""
    trades = []
    i = 0
    t_free = ts[0] - 1
    n = len(ts)
    # thru_ticks is the queue proxy (2026-09-03): a resting limit is only
    # counted filled once price trades this many ticks THROUGH the level.
    # 1 tick is the certified honest-fill rule; larger values stand in for
    # a queue that needs more volume through the price to clear.
    thru = TICK * thru_ticks if fill_through else 0.0
    # conviction tagging changes NOTHING about which trades are taken, when
    # they exit, or their R — it only labels them (2026-09-03 audit).
    run_hi = np.maximum.accumulate(hi) if conviction else None
    run_lo = np.minimum.accumulate(lo) if conviction else None
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
        if max_risk is not None and not fixed_stop:
            # his stop-cap rule (2026-09-03): a signal whose structural stop
            # exceeds the cap is never placed. Risk-on gated only - SAR
            # flattens still fire; same pending-replacement semantics as the
            # other entry-time skips.
            if abs((s["L"] + s["dir"] * entry_off) - stop_for(s)) > max_risk:
                bump("skip_stop_cap")
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
        if arm_after is not None and not fixed_stop:
            # the limit is dark until price has run arm_after x risk past
            # the level; arming must COMPLETE strictly before the touch bar
            stop_p = stop_for(s)
            risk_p = abs(E - stop_p)
            si0 = max(start - 1, 0)
            if si0 >= cancel:
                bump("unarmed")
                i += 1
                continue
            thr_px = L + d * arm_after * risk_p
            seg = hi[si0:cancel] if d == 1 else lo[si0:cancel]
            armed = (seg >= thr_px) if d == 1 else (seg <= thr_px)
            if not armed.any():
                bump("unarmed")
                i += 1
                continue
            live = si0 + int(np.argmax(armed)) + 1 + arm_delay   # strictly after
            if live >= cancel:
                bump("unarmed")
                i += 1
                continue
            seg_lo, seg_hi = lo[live:cancel], hi[live:cancel]
            touch = (seg_lo <= E - thru) if d == 1 else (seg_hi >= E + thru)
            if not touch.any():
                bump("replaced" if cancel == nxt_idx and nxt_idx < min(pend_cut_idx, n)
                     else "expired")
                i += 1
                continue
            bump("filled")
            fill = live + int(np.argmax(touch))
        else:
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
            "entry": round(E, PX_DP), "stop": round(stop, PX_DP),
            "risk": round(risk, PX_DP),
            "res": res, "r": round(r, 4), "pts": round(r * risk, PX_DP),
            "run_r": round(max(run_r, 0.0), 3),
            "r_run": None if r_run is None else round(r_run, 4),
            "run_res": run_res,
            "ambig": bool(ambig), "hold_min": int((ts[exit_idx] - ts[fill]) / 6e10),
        })
        if conviction:
            ex_pts, sess_pct = conviction_tier(
                run_hi, run_lo, hi, lo, max(start - 1, 0), fill, L, d, pd_range)
            ex_r = ex_pts / risk
            hi_ex, hi_ss = ex_r >= 1.0, sess_pct >= 0.5
            trades[-1].update({
                "excur_r": round(ex_r, 3),
                "sess_pct": None if sess_pct != sess_pct else round(sess_pct, 3),
                "tier": ("A" if hi_ex and hi_ss else "B" if hi_ex
                         else "C" if hi_ss else "D")})
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
    ap.add_argument("--levels",
                    choices=("va", "pdhl", "poc", "wva", "wpoc", "all"),
                    default="va",
                    help="level family: PD value area (default), PD high/low, "
                         "PD POC, weekly VA, weekly POC - identical grammar, "
                         "levels swapped")
    ap.add_argument("--min-risk", type=float, default=None,
                    help="override the stop floor (also the escalation "
                         "trigger), in instrument points")
    ap.add_argument("--max-risk", type=float, default=None,
                    help="stop cap in points: signals with wider structural "
                         "stops are never placed")
    ap.add_argument("--arm-delay", type=int, default=0,
                    help="latency stress: extra 1m bars between arming and "
                         "the order going live (the sim already withholds "
                         "the arming bar itself, i.e. up to 60s of implicit "
                         "latency; this adds whole minutes on top)")
    ap.add_argument("--thru-ticks", type=int, default=1,
                    help="queue proxy: ticks price must trade THROUGH the "
                         "level before a resting limit counts as filled "
                         "(1 = the certified honest-fill rule)")
    ap.add_argument("--targets", default=None,
                    help="override the target grid (comma-separated R), "
                         "including in --levels all mode where it is "
                         "otherwise pinned to the certified 1R cell")
    ap.add_argument("--arm-after", type=float, default=None,
                    help="arm-after-displacement: the resting limit is not "
                         "live until price trades this multiple of the "
                         "trade's own risk BEYOND the level. Changes the "
                         "trade set (unfilled pendings free the book)")
    ap.add_argument("--conviction", action="store_true",
                    help="tag each trade with the 2026-09-03 audit tier "
                         "(A/B/C/D from run-past-the-level x session "
                         "progress) for the sizing test. LABELS ONLY: the "
                         "trade set, R and dump filename are unchanged")
    ap.add_argument("--depths", default=None,
                    help="override the close-through depth grid, "
                         "comma-separated points")
    a = ap.parse_args()
    inst = INSTRUMENTS[a.instrument]
    global TICK, MIN_RISK, BIN_W, DEPTHS, PX_DP
    TICK, MIN_RISK = inst["tick"], inst["min_risk"]
    # enough decimals to represent one tick: 2 for NQ (0.25) and GC (0.10),
    # 6 for 6E (0.00005). Without this every FX risk rounds to 0.0 and the
    # cost overlay (cost/risk) divides by zero.
    PX_DP = max(2, math.ceil(-math.log10(TICK)) + 1)
    BIN_W, DEPTHS = inst["bin_w"], inst["depths"]
    if a.min_risk is not None:
        MIN_RISK = a.min_risk
    if a.depths is not None:
        DEPTHS = tuple(float(x) for x in a.depths.split(","))
    targets = TARGETS
    if a.levels == "all":
        DEPTHS = (inst["depths"][-1],)
        targets = (1.0,) if a.targets is None else tuple(
            float(x) for x in a.targets.split(","))
        print(f"levels=all: depth {DEPTHS[0]}, targets {targets}, "
              f"proximity merge at {MIN_RISK}pt", flush=True)
    suffix = ((f"_{a.instrument}" if a.instrument != "nq" else "")
              + (f"_lv{a.levels}" if a.levels != "va" else "")
              + (f"_mr{a.min_risk:g}" if a.min_risk is not None else "")
              + (f"_xr{a.max_risk:g}" if a.max_risk is not None else "")
              + ("_sar" if a.sar else "") + ("_through" if a.fill_through else "")
              + (f"_tf{a.tf}" if a.tf != 3 else "")
              + (f"_off{int(round(a.entry_offset / 0.25))}" if a.entry_offset else "")
              + (f"_fs{a.fixed_stop:g}" if a.fixed_stop else "")
              + (f"_twf{a.trend_x_pct:g}" if a.trend_filter else "")
              + ((f"_run{a.runner_stop}{f'tp{a.runner_tp2:g}' if a.runner_tp2 else ''}")
                 if a.runner else "")
              + ("_ng" if a.news_gate else "")
              + (f"_arm{a.arm_after:g}" if a.arm_after is not None else "")
              + ("_tg" if a.targets else "")
              + (f"_q{a.thru_ticks}" if a.thru_ticks != 1 else "")
              + (f"_lag{a.arm_delay}" if a.arm_delay else ""))
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
    MERGE_DROPS = []
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
        if a.levels == "all":
            poc_, val, vah = volume_profile(pseg, bin_w=BIN_W)
            if not (np.isfinite(vah) and np.isfinite(val)):
                continue
            fams = {"va": (vah, val),
                    "pdhl": (float(pseg.high.max()), float(pseg.low.min())),
                    "poc": (poc_, np.nan)}
            try:
                aw = anchored_weekly_profile(
                    bars, day, upto=t0 + pd.Timedelta(hours=1))
                fams["wva"] = (float(aw["awVAH"]), float(aw["awVAL"]))
                fams["wpoc"] = (float(aw["awPOC"]), np.nan)
            except Exception:
                pass
            fams = {f: (round(v1 / TICK) * TICK if np.isfinite(v1) else np.nan,
                        round(v2 / TICK) * TICK if np.isfinite(v2) else np.nan)
                    for f, (v1, v2) in fams.items()}
            fams, ndrop = merge_levels(fams, MIN_RISK)
            MERGE_DROPS.append(ndrop)
            vah, val = fams, np.nan          # dict rides the vah slot
        elif a.levels == "va":
            _, val, vah = volume_profile(pseg, bin_w=BIN_W)
        elif a.levels == "pdhl":
            vah, val = float(pseg.high.max()), float(pseg.low.min())
        elif a.levels == "poc":
            vah, val = volume_profile(pseg, bin_w=BIN_W)[0], np.nan
        else:
            try:
                aw = anchored_weekly_profile(
                    bars, day, upto=t0 + pd.Timedelta(hours=1))
            except Exception:
                continue
            if a.levels == "wva":
                vah, val = float(aw["awVAH"]), float(aw["awVAL"])
            else:
                vah, val = float(aw["awPOC"]), np.nan
        if not isinstance(vah, dict):
            if not np.isfinite(vah):
                continue
            if a.levels not in ("poc", "wpoc") and not np.isfinite(val):
                continue
            vah = round(vah / TICK) * TICK
            val = round(val / TICK) * TICK if np.isfinite(val) else np.nan
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
                          sess.close.to_numpy(), c3, vah, val, pend_cut,
                          float(pseg.high.max() - pseg.low.min())))
        if not isinstance(vah, dict):
            per_day_meta[day] = {
                "pd_range": round(float(pseg.high.max() - pseg.low.min()), 2),
                "vah": vah, "val": val, "va_width": round(vah - val, 2)}

    print(f"{len(day_cache)} tradeable days "
          f"({day_cache[0][0]} -> {day_cache[-1][0]})", flush=True)

    n_cfg = 0
    funnel = {}
    for depth in DEPTHS:
        sig_cache = []
        for (_, _, _, _, _, c3, vah, val, _, _) in day_cache:
            if isinstance(vah, dict):
                sig_cache.append({f: day_signals(c3, v1, v2, depth, tf=a.tf)
                                  for f, (v1, v2) in vah.items()})
            else:
                sig_cache.append({a.levels: day_signals(c3, vah, val, depth,
                                                        tf=a.tf)})
        for tr in targets:
            n_cfg += 1
            n_trades = 0
            cnt = funnel.setdefault(f"depth{depth:g}_R{tr:g}", {})
            for (day, ts, hi, lo, cl, _, _, _, pcut, pdr), sigmap in zip(day_cache, sig_cache):
                if not any(sigmap.values()):
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
                for fam, sigs in sigmap.items():
                    if not sigs:
                        continue
                    for t in simulate_day(ts, hi, lo, cl, sigs, pcut, tr,
                                          fill_through=a.fill_through,
                                          sar=a.sar, counters=cnt,
                                          entry_off=a.entry_offset,
                                          fixed_stop=a.fixed_stop, tflag=tfl,
                                          runner=a.runner,
                                          runner_tp2=a.runner_tp2,
                                          runner_stop=a.runner_stop,
                                          block=blk, max_risk=a.max_risk,
                                          pd_range=pdr,
                                          conviction=a.conviction,
                                          arm_after=a.arm_after,
                                          thru_ticks=a.thru_ticks,
                                          arm_delay=a.arm_delay):
                        t.update({"day": day, "depth": depth, "target_r": tr,
                                  "family": fam})
                        trades_out.write(json.dumps(t) + "\n")
                        n_trades += 1
            print(f"[{n_cfg}/{len(DEPTHS) * len(targets)}] depth={depth} "
                  f"R={tr}: {n_trades} trades", flush=True)
    trades_out.close()
    if a.levels == "va":
        days_name = ("pd_va_days.json" if a.instrument == "nq"
                     else f"pd_va_days_{a.instrument}.json")
        (ROOT / "output/analysis" / days_name).write_text(
            json.dumps(per_day_meta))
    (ROOT / f"output/analysis/pd_va_funnel{suffix}.json").write_text(
        json.dumps(funnel, indent=1))
    if MERGE_DROPS:
        print(f"proximity merge: {sum(MERGE_DROPS)} levels dropped across "
              f"{len(MERGE_DROPS)} days (avg {np.mean(MERGE_DROPS):.2f}/day)",
              flush=True)
    print(f"DONE -> output/analysis/pd_va_trades{suffix}.jsonl.gz", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
