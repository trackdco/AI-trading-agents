"""Bracket backtest — enter just before the print, fixed stop and target.

    python news_lab/bracket_test.py --stop 50 --target 150 --hold 60

Angus's structure: enter seconds before the release minute opens (entry =
close(T-1m), the last price you can actually get), 50pt stop = $1000 on 1 NQ,
150pt target = $3000. Walks the 1-minute bars forward and records which side
was touched first.

Two honesty rules, both from SPEC.md:

1. INTRABAR ORDER IS UNKNOWABLE from OHLC. If a bar touches both the stop and
   the target, this counts it as a STOP. That is the conservative reading and
   it matters enormously on the release bar, which routinely spans both.
2. FILLS ARE BRACKETED, never point-estimated. `best` fills a stop at the stop
   price; `worst` fills it at the adverse extreme of the bar that triggered it
   (the hole). Truth lies between. Expectancy is reported both ways.
"""
from __future__ import annotations
import sys
import os
import argparse
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from newslab.census import load_bars            # noqa: E402
from newslab.config import DOLLARS_PER_POINT    # noqa: E402

HIGH = ["cpi", "nfp", "fomc", "pce", "ppi"]


def simulate(bars: pd.DataFrame, T: pd.Timestamp, direction: int,
             stop: float, target: float, hold: int) -> dict | None:
    """One bracketed trade. direction +1 long, -1 short."""
    T = T.floor("min")
    ref_win = bars.loc[:T - pd.Timedelta(minutes=1)]
    if not len(ref_win) or T not in bars.index:
        return None
    if (T - pd.Timedelta(minutes=1)) - ref_win.index[-1] > pd.Timedelta(minutes=3):
        return None
    ref = float(ref_win["close"].iloc[-1])
    path = bars.loc[T: T + pd.Timedelta(minutes=hold)]
    if len(path) < 2:
        return None

    stop_px = ref - direction * stop
    targ_px = ref + direction * target

    for ts, b in path.iterrows():
        o, h, l = float(b["open"]), float(b["high"]), float(b["low"])
        # gapped straight through the stop at the open — no better fill exists
        if (direction > 0 and o <= stop_px) or (direction < 0 and o >= stop_px):
            adverse = (ref - o) if direction > 0 else (o - ref)
            return dict(outcome="stop_gap", pts_best=-adverse,
                        pts_worst=-adverse, minutes=int(
                            (ts - T).total_seconds() // 60))
        hit_stop = (l <= stop_px) if direction > 0 else (h >= stop_px)
        hit_targ = (h >= targ_px) if direction > 0 else (l <= targ_px)
        if hit_stop:
            # conservative: a bar touching both is scored a stop
            worst = (ref - l) if direction > 0 else (h - ref)
            return dict(outcome="stop", pts_best=-stop, pts_worst=-worst,
                        minutes=int((ts - T).total_seconds() // 60))
        if hit_targ:
            return dict(outcome="target", pts_best=target, pts_worst=target,
                        minutes=int((ts - T).total_seconds() // 60))
    last = float(path["close"].iloc[-1])
    pnl = direction * (last - ref)
    return dict(outcome="timeout", pts_best=pnl, pts_worst=pnl, minutes=hold)


def run(stop: float, target: float, hold: int) -> pd.DataFrame:
    bars = load_bars("glbx-mdp3-*.ohlcv-1m.csv.zst")
    ev = pd.read_parquet("news_lab/output/events.parquet")
    ev = ev[(ev["release_kind"] == "print") & (ev["family"].isin(HIGH))]
    ev = ev[ev["date"] < "2025-10-01"]          # unsealed only
    rows = []
    for _, e in ev.iterrows():
        for d, lab in ((1, "long"), (-1, "short")):
            r = simulate(bars, e["ts_release_et"], d, stop, target, hold)
            if r:
                rows.append({**r, "family": e["family"], "date": e["date"],
                             "side": lab})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stop", type=float, default=50)
    ap.add_argument("--target", type=float, default=150)
    ap.add_argument("--hold", type=int, default=60)
    a = ap.parse_args()
    df = run(a.stop, a.target, a.hold)
    dpp = DOLLARS_PER_POINT["NQ"]
    print(f"\nSTOP {a.stop:.0f}pt (${a.stop*dpp:,.0f})   "
          f"TARGET {a.target:.0f}pt (${a.target*dpp:,.0f})   "
          f"hold {a.hold}m   unsealed, high-impact\n")
    print(f"trades simulated: {len(df)} "
          f"({len(df)//2} events x both directions)\n")

    print("OUTCOME MIX (both directions — i.e. a coin flip on direction):")
    mix = df["outcome"].value_counts(normalize=True).mul(100).round(1)
    print(mix.to_string(), "\n")

    for bound in ("best", "worst"):
        col = f"pts_{bound}"
        ev_pts = df[col].mean()
        print(f"[{bound:5s} fill]  EV/trade = {ev_pts:+7.1f} pts "
              f"= ${ev_pts*dpp:+,.0f}   (R = {ev_pts/a.stop:+.2f})")
    print()

    # If you could pick the winning side every time — the ceiling for this
    # structure. Take the better of the two directions per event.
    piv = df.pivot_table(index=["family", "date"], columns="side",
                         values=["pts_best", "pts_worst"], aggfunc="first")
    for bound in ("best", "worst"):
        b = piv[f"pts_{bound}"]
        perfect = b.max(axis=1).mean()
        wrong = b.min(axis=1).mean()
        be = (0 - wrong) / (perfect - wrong) if perfect != wrong else np.nan
        print(f"[{bound:5s} fill]  perfect direction {perfect:+7.1f} pts "
              f"(${perfect*dpp:+,.0f}) | wrong {wrong:+7.1f} pts "
              f"| break-even acc {be*100:.1f}%")

    print("\nPER-FAMILY (worst fill, coin-flip direction):")
    g = df.groupby("family").agg(
        n=("pts_worst", "size"),
        p_target=("outcome", lambda s: round((s == "target").mean(), 3)),
        p_stop=("outcome", lambda s: round(
            s.isin(["stop", "stop_gap"]).mean(), 3)),
        ev_pts=("pts_worst", "mean"))
    g["ev_usd"] = (g["ev_pts"] * dpp).round(0)
    g["ev_pts"] = g["ev_pts"].round(1)
    print(g.to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
