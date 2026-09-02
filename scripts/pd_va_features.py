#!/usr/bin/env python3
"""PD VA WINNERS vs LOSERS — which as-of features sort the retest trades?

    python -m scripts.pd_va_features

His ask (2026-09-02): "i am very sure we can mechanically find a way to see
things that distinguish winners from losers, even find some other thing on
top to put on entries." Nine candidate features, every one computable AT
SIGNAL TIME (no lookahead), scored on the SAR any-tick 1.5R Asia+London
population, split-half validated by day — a feature earns nothing unless
its spread holds in BOTH halves. Same discipline as the NY variable test.

Features:
  leg       breakout vs reversion, per side (from the dump)
  attempt   nth crossing of that level today (1 / 2 / 3-4 / 5+) — T82 shape
  x_depth   how far the candle CLOSED through (pts)
  disp      close-through candle range vs median of prior 20 candles
  conf      his confluence hypothesis: how many vwap-band/BB-MA levels the
            close-through candle ALSO closed through (0 / 1 / 2+)
  va_w      prior-day value-area width percentile (trailing 120 sessions)
  pd_r      prior-day range percentile (trailing 120 sessions)
  tod       early/late half of Asia / London
  dow       session-day anchor weekday (Sun anchor = Monday trading)

WR = TARGET/(TARGET+STOP) per bucket; avg_r includes SAR scratches/flats.
Output: printed table + output/analysis/pd_va_features.json
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402
from scripts.pd_va_backtest import (day_signals, SESS_H,           # noqa: E402
                                    SIG_START_H, SIG_END_H)
from src.htf_ma.levels import bb_ma_asof, vwap_bands              # noqa: E402

DEPTH, TARGET = 0.0, 1.5
BB_TFS = (2, 3, 15)
VWAP_COLS = ("vwap", "vwap_p1", "vwap_p2", "vwap_p3",
             "vwap_m1", "vwap_m2", "vwap_m3")


def day_feature_map(bars, day, prev_day):
    """signal t_sig_hrs (3dp) -> feature dict, for one session day."""
    t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
    pa = pd.Timestamp(f"{prev_day} 18:00", tz=OB.NY)
    pseg = bars[(bars.index >= pa) & (bars.index < t0)]
    sess = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=SESS_H))]
    if len(pseg) < 300 or len(sess) < 600:
        return {}
    from scripts.agent_context import volume_profile
    _, val, vah = volume_profile(pseg)
    if not (np.isfinite(val) and np.isfinite(vah)):
        return {}
    vah = round(vah * 4) / 4
    val = round(val * 4) / 4
    c3 = sess.resample("3min").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    hrs3 = (c3.index - t0).total_seconds() / 3600
    c3 = c3[(hrs3 >= SIG_START_H - 0.07) & (hrs3 + 0.05 <= SIG_END_H + 1e-6)]
    sigs = day_signals(c3, vah, val, DEPTH)
    if not sigs:
        return {}

    rng = (c3.high - c3.low).to_numpy()
    end2idx = {(t + pd.Timedelta(minutes=3)).value: i
               for i, t in enumerate(c3.index)}
    vw = vwap_bands(sess)
    bbs = {tf: bb_ma_asof(sess, tf)[0] for tf in BB_TFS}

    out = {}
    n_at_level = defaultdict(int)
    for s in sigs:
        n_at_level[s["level_name"]] += 1
        tval = s["t"].value
        hrs = (tval - t0.value) / 3.6e12
        # candle index for displacement ratio
        ci = end2idx.get(tval)
        disp = np.nan
        if ci is not None and ci >= 5:
            base = np.median(rng[max(0, ci - 20):ci])
            if base > 0:
                disp = rng[ci] / base
        # confluence: other levels the ct candle also closed through, as-of
        lo_c, hi_c = sorted((s["ct_open"], s["close"]))
        conf = 0
        vrow = vw[vw.index < s["t"]]
        if len(vrow):
            r = vrow.iloc[-1]
            for cname in VWAP_COLS:
                if cname in vrow.columns and lo_c < float(r[cname]) < hi_c:
                    conf += 1
        for tf in BB_TFS:
            b = bbs[tf]
            bv = b[b.index < s["t"]]
            if len(bv) and lo_c < float(bv.iloc[-1]) < hi_c:
                conf += 1
        out[round(hrs, 3)] = {
            "attempt": n_at_level[s["level_name"]],
            "x_depth": abs(s["close"] - s["L"]),
            "disp": disp, "conf": conf,
        }
    return out


def main() -> int:
    rows = [json.loads(l) for l in
            gzip.open(ROOT / "output/analysis/pd_va_trades_sar.jsonl.gz", "rt")]
    pop = [t for t in rows if t["depth"] == DEPTH and t["target_r"] == TARGET
           and t["t_sig_hrs"] < 15.5 and t["fill_hrs"] < 15.5]
    days_meta = json.loads((ROOT / "output/analysis/pd_va_days.json").read_text())
    days_sorted = sorted(days_meta)
    va_hist, pd_hist, va_pct, pd_pct = [], [], {}, {}
    for d in days_sorted:
        vw_, pr_ = days_meta[d]["va_width"], days_meta[d]["pd_range"]
        if len(va_hist) >= 40:
            va_pct[d] = (np.array(va_hist[-120:]) < vw_).mean()
            pd_pct[d] = (np.array(pd_hist[-120:]) < pr_).mean()
        va_hist.append(vw_)
        pd_hist.append(pr_)

    bars = OB.get_bars()
    all_days = OB.all_session_days(bars)
    prev_of = {all_days[i]: all_days[i - 1] for i in range(1, len(all_days))}
    pop_days = sorted({t["day"] for t in pop})
    fmap = {}
    for i, d in enumerate(pop_days):
        if d in prev_of:
            fmap[d] = day_feature_map(bars, d, prev_of[d])
        if i % 100 == 0:
            print(f"[{i}/{len(pop_days)}] features {d}", flush=True)

    def q4(x):
        return None if x is None else f"Q{min(3, int(x * 4)) + 1}"

    def buckets(t):
        f = fmap.get(t["day"], {}).get(t["t_sig_hrs"])
        h = t["t_sig_hrs"]
        b = {"leg": t["leg"],
             "tod": ("asia_early" if h < 5 else "asia_late") if h < 9
                    else ("london_early" if h < 12.5 else "london_late"),
             "dow": str(pd.Timestamp(t["day"]).dayofweek),
             "va_w": q4(va_pct.get(t["day"])),
             "pd_r": q4(pd_pct.get(t["day"]))}
        if f:
            a = f["attempt"]
            b["attempt"] = "1" if a == 1 else "2" if a == 2 else \
                "3-4" if a <= 4 else "5+"
            x = f["x_depth"]
            b["x_depth"] = "<1pt" if x < 1 else "1-3pt" if x < 3 else \
                "3-6pt" if x < 6 else "6pt+"
            if np.isfinite(f["disp"]):
                b["disp"] = "<1x" if f["disp"] < 1 else "1-2x" \
                    if f["disp"] < 2 else "2x+"
            b["conf"] = "0" if f["conf"] == 0 else "1" if f["conf"] == 1 else "2+"
        return b

    mid = pop_days[len(pop_days) // 2]
    print(f"\npopulation: {len(pop)} SAR AL trades (depth any-tick, {TARGET}R), "
          f"split at {mid}\n")
    report = {}
    for feat in ("leg", "attempt", "x_depth", "disp", "conf",
                 "va_w", "pd_r", "tod", "dow"):
        agg = defaultdict(lambda: {"iw": 0, "il": 0, "ir": [], "ow": 0, "ol": 0,
                                   "or": []})
        for t in pop:
            b = buckets(t).get(feat)
            if b is None:
                continue
            first = t["day"] < mid
            a = agg[b]
            a["ir" if first else "or"].append(t["r"])
            if t["res"] == "TARGET":
                a["iw" if first else "ow"] += 1
            elif t["res"] == "STOP":
                a["il" if first else "ol"] += 1
        print(f"-- {feat}")
        report[feat] = {}
        for b in sorted(agg):
            a = agg[b]
            iwr = a["iw"] / (a["iw"] + a["il"]) if a["iw"] + a["il"] else 0
            owr = a["ow"] / (a["ow"] + a["ol"]) if a["ow"] + a["ol"] else 0
            ir = np.mean(a["ir"]) if a["ir"] else 0
            orr = np.mean(a["or"]) if a["or"] else 0
            report[feat][b] = {"is_wr": iwr, "oos_wr": owr,
                               "is_n": len(a["ir"]), "oos_n": len(a["or"]),
                               "is_avg_r": ir, "oos_avg_r": orr}
            print(f"   {b:14} IS WR {iwr:6.1%} (n={len(a['ir']):4}, "
                  f"avgR {ir:+.3f})   OOS WR {owr:6.1%} "
                  f"(n={len(a['or']):4}, avgR {orr:+.3f})")
        print()
    (ROOT / "output/analysis/pd_va_features.json").write_text(
        json.dumps(report, indent=1))
    print("DONE -> output/analysis/pd_va_features.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
