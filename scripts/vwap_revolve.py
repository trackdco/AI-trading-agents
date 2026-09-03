#!/usr/bin/env python3
"""VWAP-REVOLVENT — his 2026-09-03 idea: the certified grammar on VWAP bands.

    python -m scripts.vwap_revolve --tf 3 --style retest
    python -m scripts.vwap_revolve --tf 1 --style market

"candle close through vwap band, market order and target x r. other
thing is enter on retest. try this on the 1,3 and 5 min timeframes."

Levels = session VWAP and its +/-1, +/-2 sigma bands (the certified
`vwap_bands`, per-1m, causal, 18:00 anchor). Bands MOVE, so the level is
FROZEN at the signal close: crossings are detected against the moving
series (prev close vs prev band value, close vs current), and the frozen
value anchors the retest limit, the stop rule, and the floor exactly as
the PD-level engine does. One book across all five bands, one position
at a time, SAR on any opposing band crossing, structural stops with the
prior-candle escalation and 5pt floor, news gate, pendings die at 16:00,
EOD force-flat. NQ only for now.

Entry styles:
  retest  - limit at the frozen band value; fills honest (one tick
            through) like the certified spec
  market  - filled at the signal candle's close price on the next bar
            (no pending phase; always filled)

Depth grid {0, 3}pt x targets {1.0, 1.5, 2.0, 2.5, 3.0}. Output:
  output/analysis/vwap_rev_tf{N}_{style}.jsonl.gz
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
from src.htf_ma.levels import vwap_bands                          # noqa: E402

TICK = 0.25
MIN_RISK = 5.0
DEPTHS = (0.0, 3.0)
TARGETS = (1.0, 1.5, 2.0, 2.5, 3.0)
BANDS = ("vwap", "vwap_p1", "vwap_p2", "vwap_m1", "vwap_m2")
SIG_START_H = 1.0
SIG_END_H = 21 + 55 / 60
PEND_CUT_H = 22.0
SESS_H = 23.0


def window_of(hrs):
    return "ASIA" if hrs < 9.0 else ("LONDON" if hrs < 15.5 else "NY")


def day_signals(c3, band_at, depth, tf):
    """Crossing closes of any band; the band value at the signal candle's
    last bar is FROZEN as the trade's level."""
    thr = max(depth, TICK)
    cl = c3.close.to_numpy()
    op = c3.open.to_numpy()
    hi = c3.high.to_numpy()
    lo = c3.low.to_numpy()
    ends = c3.index + pd.Timedelta(minutes=tf)
    out = []
    for name in BANDS:
        B = band_at[name]
        for i in range(1, len(c3)):
            b_prev, b_now = B[i - 1], B[i]
            if not (np.isfinite(b_prev) and np.isfinite(b_now)):
                continue
            d = 0
            if cl[i - 1] <= b_prev and cl[i] >= b_now + thr:
                d = 1
            elif cl[i - 1] >= b_prev and cl[i] <= b_now - thr:
                d = -1
            if not d:
                continue
            L = round(b_now / TICK) * TICK
            out.append({"t": ends[i], "dir": d, "band": name, "L": L,
                        "ct_open": op[i], "ct_hi": hi[i], "ct_lo": lo[i],
                        "pv_hi": hi[i - 1], "pv_lo": lo[i - 1],
                        "close": cl[i]})
    out.sort(key=lambda s: (s["t"], abs(s["close"] - s["L"])))
    ded = {}
    for s in out:
        ded.setdefault(s["t"], s)          # nearest band to the close wins
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


def simulate(ts, hi, lo, cl, sigs, pend_cut_idx, target_r, style, block,
             book_pos=None, max_risk=None, pd_range=None,
             conviction=False, arm_after=None, thru_ticks=1):
    """book_pos: list of (fill_hrs, end_hrs, dir, entry) level-book
    positions for the cross-book dedupe rule (2026-09-03): a VWAP entry
    is skipped when a level-book position is open at the fill moment,
    same direction, entries within one stop-floor.

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

    max_risk: his stop-cap rule (2026-09-03) — a signal whose structural
    stop exceeds the cap in points is never placed (risk-on gated only;
    SAR flattens unaffected; same pending-replacement semantics as the
    other entry-time skips)."""
    trades = []
    i = 0
    t_free = ts[0] - 1
    n = len(ts)
    thru = TICK * thru_ticks          # queue proxy, see pd_va_backtest
    run_hi = np.maximum.accumulate(hi) if conviction else None
    run_lo = np.minimum.accumulate(lo) if conviction else None
    while i < len(sigs):
        s = sigs[i]
        t_sig = s["t"].value
        if t_sig <= t_free:
            i += 1
            continue
        start = int(np.searchsorted(ts, t_sig))
        if start >= n:
            break
        if block is not None and block[0] <= start < block[1]:
            i += 1
            continue
        L, d = s["L"], s["dir"]
        stop = stop_for(s)
        if max_risk is not None:
            e_pros = float(s["close"]) if style == "market" else L
            if abs(e_pros - stop) > max_risk:
                i += 1
                continue
        if style == "market":
            fill = start
            E = float(s["close"])
        else:
            nxt = sigs[i + 1]["t"].value if i + 1 < len(sigs) else None
            nxt_idx = int(np.searchsorted(ts, nxt)) if nxt is not None else n
            cancel = min(nxt_idx, pend_cut_idx, n)
            if block is not None and start < block[0]:
                cancel = min(cancel, block[0])
            lo_w, hi_w = start, cancel
            if arm_after is not None:
                si0 = max(start - 1, 0)
                thr_px = L + d * arm_after * abs(L - stop)
                seg = hi[si0:cancel] if d == 1 else lo[si0:cancel]
                armed = ((seg >= thr_px) if d == 1 else (seg <= thr_px)) \
                    if si0 < cancel else np.zeros(0, bool)
                if not armed.any():
                    i += 1
                    continue
                lo_w = si0 + int(np.argmax(armed)) + 1     # strictly after
                if lo_w >= cancel:
                    i += 1
                    continue
            seg_lo, seg_hi = lo[lo_w:hi_w], hi[lo_w:hi_w]
            touch = (seg_lo <= L - thru) if d == 1 else (seg_hi >= L + thru)
            if not touch.any():
                i += 1
                continue
            fill = lo_w + int(np.argmax(touch))
            E = L
        risk = abs(E - stop)
        if risk <= 0:
            i += 1
            continue
        if book_pos:
            fh = (ts[fill] - ts[0]) / 3.6e12
            if any(f2 <= fh < e2 and d2 == d and abs(p2 - E) <= MIN_RISK
                   for f2, e2, d2, p2 in book_pos):
                i += 1
                continue
        tgt = E + d * target_r * risk
        w_lo, w_hi = lo[fill:], hi[fill:]
        s_hit = (w_lo <= stop) if d == 1 else (w_hi >= stop)
        t_hit = (w_hi >= tgt) if d == 1 else (w_lo <= tgt)
        s_idx = fill + int(np.argmax(s_hit)) if s_hit.any() else n
        t_idx = fill + int(np.argmax(t_hit)) if t_hit.any() else n
        sar_idx, sar_px = n + 1, None
        for sj in sigs[i + 1:]:
            if sj["dir"] == -d and sj["t"].value > ts[fill]:
                sar_idx = int(np.searchsorted(ts, sj["t"].value))
                sar_px = sj["close"]
                break
        first = min(s_idx, t_idx)
        if sar_idx <= first and sar_idx <= n:
            exit_idx = min(sar_idx, n - 1)
            r = d * (sar_px - E) / risk
            res = "SAR"
        elif s_idx <= t_idx and s_idx < n:
            exit_idx, r = s_idx, -1.0
            res = "STOP"
        elif t_idx < s_idx:
            exit_idx, r = t_idx, target_r
            res = "TARGET"
        else:
            exit_idx, r = n - 1, d * (cl[-1] - E) / risk
            res = "FLAT"
        hrs = (t_sig - ts[0]) / 3.6e12
        trades.append({"t_sig_hrs": round(hrs, 3), "window": window_of(hrs),
                       "band": s["band"], "dir": d, "entry": round(E, 2),
                       "risk": round(risk, 2), "res": res, "r": round(r, 4),
                       "pts": round(r * risk, 2),
                       "fill_hrs": round((ts[fill] - ts[0]) / 3.6e12, 3),
                       "hold_min": int((ts[min(exit_idx, n - 1)] - ts[fill]) / 6e10)})
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
        t_free = ts[min(sar_idx, n - 1)] - 1 if res == "SAR" else ts[exit_idx]
        i += 1
    return trades


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tf", type=int, required=True, choices=(1, 3, 5))
    ap.add_argument("--style", required=True, choices=("retest", "market"))
    ap.add_argument("--anchor", choices=("session", "ny"), default="session",
                    help="vwap anchor: 18:00 session open (default) or the "
                         "09:30 NY open (fresh accumulation, signals from "
                         "09:45 after a 15-min sigma warmup)")
    ap.add_argument("--dedupe", action="store_true",
                    help="cross-book rule: skip entries duplicating an open "
                         "level-book position (same dir, within one floor)")
    ap.add_argument("--thru-ticks", type=int, default=1,
                    help="queue proxy: ticks price must trade THROUGH the "
                         "band before a resting limit counts as filled")
    ap.add_argument("--arm-after", type=float, default=None,
                    help="arm-after-displacement: the resting limit is not "
                         "live until price trades this multiple of the "
                         "trade's own risk BEYOND the frozen band value")
    ap.add_argument("--conviction", action="store_true",
                    help="tag each trade with the 2026-09-03 audit tier "
                         "(LABELS ONLY; trade set, R and filename unchanged)")
    ap.add_argument("--max-risk", type=float, default=None,
                    help="stop cap in points: signals with wider structural "
                         "stops are never placed (dedupe then reads the "
                         "matching capped level-book dump)")
    a = ap.parse_args()
    book_by_day = {}
    if a.dedupe:
        import collections
        bb = collections.defaultdict(list)
        xr = f"_xr{a.max_risk:g}" if a.max_risk is not None else ""
        am = f"_arm{a.arm_after:g}" if a.arm_after is not None else ""
        qq = f"_q{a.thru_ticks}" if a.thru_ticks != 1 else ""
        for l in gzip.open(ROOT / "output/analysis/"
                           f"pd_va_trades_lvall{xr}_sar_through_tf1_ng{am}{qq}.jsonl.gz", "rt"):
            t = json.loads(l)
            bb[t["day"]].append((t["fill_hrs"],
                                 t["fill_hrs"] + t["hold_min"] / 60,
                                 t["dir"], t["entry"]))
        book_by_day = dict(bb)
        print(f"dedupe: level-book positions loaded for {len(book_by_day)} days",
              flush=True)

    nf = pd.read_csv(ROOT / "data/reference/news_archive.csv")
    news_days = set(nf[(nf.impact == "high") & (nf.time_et >= "08:00")
                       & (nf.time_et < "09:30")].date)
    bars = OB.get_bars()
    days = OB.all_session_days(bars)
    out = ROOT / (f"output/analysis/vwap_rev_tf{a.tf}_{a.style}"
                  + (f"_xr{a.max_risk:g}" if a.max_risk is not None else "")
                  + ("_nyanc" if a.anchor == "ny" else "")
                  + ("_dd" if a.dedupe else "")
                  + (f"_arm{a.arm_after:g}" if a.arm_after is not None else "")
                  + (f"_q{a.thru_ticks}" if a.thru_ticks != 1 else "")
                  + ".jsonl.gz")
    fh = gzip.open(out, "wt")
    n_all = 0
    prev_t0 = None
    for di, day in enumerate(days):
        t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
        # prior SESSION segment, same anchor convention as the level engine
        pseg = (bars[(bars.index >= prev_t0) & (bars.index < t0)]
                if prev_t0 is not None else bars.iloc[:0])
        prev_t0 = t0
        pdr = (float(pseg.high.max() - pseg.low.min())
               if len(pseg) >= 300 else None)
        sess = bars[(bars.index >= t0)
                    & (bars.index < t0 + pd.Timedelta(hours=SESS_H))]
        if len(sess) < 600:
            continue
        if a.anchor == "ny":
            nyseg = sess[sess.index >= t0 + pd.Timedelta(hours=15.5)]
            if len(nyseg) < 120:
                continue
            vw = vwap_bands(nyseg).reindex(sess.index)   # NaN before 09:30
        else:
            vw = vwap_bands(sess)
        c3 = sess.resample(f"{a.tf}min").agg(
            {"open": "first", "high": "max", "low": "min",
             "close": "last"}).dropna()
        hrs3 = (c3.index - t0).total_seconds() / 3600
        sig_start = 15.75 if a.anchor == "ny" else SIG_START_H
        keep = (hrs3 >= sig_start - a.tf / 60 - 0.02) \
            & (hrs3 + a.tf / 60 <= SIG_END_H + 1e-6)
        c3 = c3[keep]
        if len(c3) < 50:
            continue
        # band value at each candle's LAST bar (known at candle close)
        last_idx = np.searchsorted(sess.index.view("int64"),
                                   (c3.index + pd.Timedelta(minutes=a.tf)
                                    ).view("int64")) - 1
        last_idx = np.clip(last_idx, 0, len(sess) - 1)
        band_at = {b: vw[b].to_numpy()[last_idx] for b in BANDS}
        ts = sess.index.view("int64")
        pcut = int(np.searchsorted(
            ts, (t0 + pd.Timedelta(hours=PEND_CUT_H)).value))
        blk = None
        if str((t0 + pd.Timedelta(hours=15)).date()) in news_days:
            blk = (int(np.searchsorted(ts, (t0 + pd.Timedelta(hours=14)).value)),
                   int(np.searchsorted(ts, (t0 + pd.Timedelta(hours=15.5)).value)))
        hi_ = sess.high.to_numpy()
        lo_ = sess.low.to_numpy()
        cl_ = sess.close.to_numpy()
        for depth in DEPTHS:
            sigs = day_signals(c3, band_at, depth, a.tf)
            if not sigs:
                continue
            for tr in TARGETS:
                for t in simulate(ts, hi_, lo_, cl_, sigs, pcut, tr,
                                  a.style, blk,
                                  book_pos=book_by_day.get(day),
                                  max_risk=a.max_risk, pd_range=pdr,
                                  conviction=a.conviction,
                                  arm_after=a.arm_after,
                                  thru_ticks=a.thru_ticks):
                    t.update({"day": day, "depth": depth, "target_r": tr})
                    fh.write(json.dumps(t) + "\n")
                    n_all += 1
        if di % 100 == 0:
            print(f"[{di}/{len(days)}] {day} - {n_all} rows", flush=True)
    fh.close()
    print(f"DONE {n_all} -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
