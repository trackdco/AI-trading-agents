#!/usr/bin/env python3
"""PD VA ALIGNMENT — replay one session with HIS chart levels, print the log.

    python -m scripts.pd_va_align --day 2026-08-09 --vah 29847.75 [--val N]
    python -m scripts.pd_va_align --day 2026-08-09 --vah 29847.75 --sar --target 1.5

The trade-matching harness for his marked-up days: overrides the computed
prior-day profile with the SVP levels read off his TradingView chart, runs
the simulator on that one session, and prints every signal and trade with
clock times — lined up against his annotations by eye.

Give --vah and/or --val (either alone is fine — only given levels are
scanned). Without an override it falls back to the computed profile and
says so, printing both so the level residual on that day is visible.

Requires bars covering the session (data/reference parquets; extend via
the Mac's export pipeline for recent days).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402
from scripts.agent_context import volume_profile                  # noqa: E402
import scripts.pd_va_backtest as BT                               # noqa: E402
from scripts.pd_va_backtest import (day_signals, simulate_day,     # noqa: E402
                                    SESS_H, PEND_CUT_H, SIG_START_H, SIG_END_H)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", required=True, help="session day (18:00 anchor)")
    ap.add_argument("--vah", type=float, default=None, help="his chart PD VAH")
    ap.add_argument("--val", type=float, default=None, help="his chart PD VAL")
    ap.add_argument("--depth", type=float, default=0.0)
    ap.add_argument("--target", type=float, default=1.5)
    ap.add_argument("--tf", type=int, default=3,
                    help="signal candle timeframe in minutes")
    ap.add_argument("--sar", action="store_true")
    ap.add_argument("--fill-through", action="store_true")
    ap.add_argument("--instrument", choices=tuple(BT.INSTRUMENTS), default="nq")
    a = ap.parse_args()

    inst = BT.INSTRUMENTS[a.instrument]
    BT.TICK, BT.MIN_RISK, BT.BIN_W = inst["tick"], inst["min_risk"], inst["bin_w"]
    if inst["bars"]:
        b = pd.read_parquet(ROOT / inst["bars"])
        b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(OB.NY)
        bars = b.set_index("mi").sort_index()[
            ["open", "high", "low", "close", "volume"]]
    else:
        bars = OB.get_bars()
    days = OB.all_session_days(bars)
    if a.day not in days:
        print(f"{a.day} not in bars ({days[0]} -> {days[-1]}); "
              f"extend data/reference first")
        return 1
    i = days.index(a.day)
    t0 = pd.Timestamp(f"{a.day} 18:00", tz=OB.NY)
    pa = pd.Timestamp(f"{days[i - 1]} 18:00", tz=OB.NY)
    pseg = bars[(bars.index >= pa) & (bars.index < t0)]
    sess = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=SESS_H))]
    _, c_val, c_vah = volume_profile(pseg, bin_w=BT.BIN_W)
    print(f"computed PD profile (prior sess {days[i-1]}): "
          f"VAH {c_vah:.2f} / VAL {c_val:.2f}")
    vah = a.vah if a.vah is not None else round(c_vah / BT.TICK) * BT.TICK
    val = a.val if a.val is not None else round(c_val / BT.TICK) * BT.TICK
    if a.vah is not None or a.val is not None:
        print(f"using chart override: VAH {vah if a.vah else '(unused)'} / "
              f"VAL {val if a.val else '(unused)'}"
              + (f"   residual vs computed: "
                 f"vah {vah - c_vah:+.2f} " if a.vah else "")
              + (f"val {val - c_val:+.2f}" if a.val else ""))

    c3 = sess.resample(f"{a.tf}min").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    hrs3 = (c3.index - t0).total_seconds() / 3600
    c3 = c3[(hrs3 >= SIG_START_H - a.tf / 60 - 0.02)
            & (hrs3 + a.tf / 60 <= SIG_END_H + 1e-6)]
    ts = sess.index.view("int64")
    pcut = int(np.searchsorted(ts, (t0 + pd.Timedelta(hours=PEND_CUT_H)).value))

    # only the given side(s) when overriding: a NaN level can never cross
    use_vah = vah if (a.vah is not None or a.val is None) else np.nan
    use_val = val if (a.val is not None or a.vah is None) else np.nan
    sigs = []
    if np.isfinite(use_vah):
        sigs += [s for s in day_signals(c3, use_vah, -1e12, a.depth, tf=a.tf)
                 if s["level_name"] == "vah"]
    if np.isfinite(use_val):
        sigs += [s for s in day_signals(c3, 1e12, use_val, a.depth, tf=a.tf)
                 if s["level_name"] == "val"]
    sigs.sort(key=lambda s: s["t"])

    trades = simulate_day(ts, sess.high.to_numpy(), sess.low.to_numpy(),
                          sess.close.to_numpy(), sigs, pcut, a.target,
                          fill_through=a.fill_through, sar=a.sar)
    tset = {t["t_sig_hrs"] for t in trades}
    print(f"\n{len(sigs)} crossings, {len(trades)} trades "
          f"(target {a.target}R, depth {a.depth}, sar={a.sar})")
    print(f"{'signal':7}{'fill':7}{'win':7}{'lvl':5}{'side':6}"
          f"{'entry':>10}{'stop':>10}{'risk':>6}  {'result':18}{'run_r':>6}")
    for s in sigs:
        hrs = (s["t"].value - ts[0]) / 3.6e12
        clock = (t0 + pd.Timedelta(hours=hrs)).strftime("%H:%M")
        tr = next((t for t in trades if t["t_sig_hrs"] == round(hrs, 3)), None)
        if tr is None:
            print(f"{clock:7}{'':7}{'':7}{s['level_name']:5}"
                  f"{'buy' if s['dir'] == 1 else 'sell':6}"
                  f"{s['L']:>10.2f}{'':>10}{'':>6}  (no trade: skipped/unfilled)")
            continue
        fillc = (t0 + pd.Timedelta(hours=tr["fill_hrs"])).strftime("%H:%M")
        res = f"{tr['res']} {tr['r']:+.2f}R {tr['pts']:+.1f}pt"
        if tr["ambig"]:
            res += " AMBIG"
        print(f"{clock:7}{fillc:7}{tr['window']:7}{s['level_name']:5}"
              f"{'buy' if s['dir'] == 1 else 'sell':6}"
              f"{tr['entry']:>10.2f}{tr['stop']:>10.2f}{tr['risk']:>6.1f}  "
              f"{res:18}{tr['run_r']:>6.2f}")
    net = sum(t["r"] for t in trades)
    pts = sum(t["pts"] for t in trades)
    print(f"\nday net: {net:+.2f}R  {pts:+.1f}pt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
