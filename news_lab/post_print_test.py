"""Post-print reaction lane — enter AFTER the release bar, no gap risk.

    python news_lab/post_print_test.py

The pre-print lane died on fill quality, not on prediction (CEILING-TEST.md):
a stop resting through the release bar is a 2.4-5.1R risk, not 1R. This lane
sidesteps that entirely by never being in the market during the violent bar.

Sequence, strictly causal:
  T-1m close   reference price
  T            the release bar prints (we are FLAT — this is the whole point)
  T+1m open    ENTRY. The release bar has closed, so its direction and size
               are known facts, not forecasts.

Signal = the release bar's own direction. Two hypotheses, both tested:
  continuation — trade WITH the release bar
  fade         — trade AGAINST it

No actuals, no consensus, no predictor. Nothing here needs to know what the
number was, only how price responded to it.

Fills: entry at T+1 open is an ordinary fill in a normal minute, so the
best/worst bracket that dominated the pre-print lane mostly collapses. Stops
are still reported at the WORST bound (filled at the triggering bar's adverse
extreme) per SPEC.md.
"""
from __future__ import annotations
import sys
import os
import argparse
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from newslab.census import load_bars, wilson    # noqa: E402
from newslab.config import DOLLARS_PER_POINT    # noqa: E402

HIGH = ["cpi", "nfp", "fomc", "pce", "ppi"]


def simulate(bars: pd.DataFrame, T: pd.Timestamp, mode: str,
             stop: float, target: float, hold: int) -> dict | None:
    T = T.floor("min")
    prev = bars.loc[:T - pd.Timedelta(minutes=1)]
    if not len(prev) or T not in bars.index:
        return None
    if (T - pd.Timedelta(minutes=1)) - prev.index[-1] > pd.Timedelta(minutes=3):
        return None
    ref = float(prev["close"].iloc[-1])
    rel = bars.loc[T]
    rel_dir = np.sign(float(rel["close"]) - ref)
    if rel_dir == 0:
        return None
    rel_range = float(rel["high"]) - float(rel["low"])

    entry_ts = T + pd.Timedelta(minutes=1)
    if entry_ts not in bars.index:
        return None
    entry = float(bars.at[entry_ts, "open"])
    d = int(rel_dir) if mode == "continuation" else -int(rel_dir)

    stop_px = entry - d * stop
    targ_px = entry + d * target
    path = bars.loc[entry_ts: entry_ts + pd.Timedelta(minutes=hold)]

    out = dict(family=None, rel_range=rel_range, rel_dir=int(rel_dir),
               entry=entry)
    for ts, b in path.iterrows():
        o, h, l = float(b["open"]), float(b["high"]), float(b["low"])
        if (d > 0 and o <= stop_px) or (d < 0 and o >= stop_px):
            adv = (entry - o) if d > 0 else (o - entry)
            return {**out, "outcome": "stop_gap", "pts": -adv}
        hit_stop = (l <= stop_px) if d > 0 else (h >= stop_px)
        hit_targ = (h >= targ_px) if d > 0 else (l <= targ_px)
        if hit_stop:                       # conservative on a both-touched bar
            worst = (entry - l) if d > 0 else (h - entry)
            return {**out, "outcome": "stop", "pts": -worst}
        if hit_targ:
            return {**out, "outcome": "target", "pts": target}
    last = float(path["close"].iloc[-1])
    return {**out, "outcome": "timeout", "pts": d * (last - entry)}


def run(stop: float, target: float, hold: int) -> pd.DataFrame:
    bars = load_bars("glbx-mdp3-*.ohlcv-1m.csv.zst")
    ev = pd.read_parquet("news_lab/output/events.parquet")
    ev = ev[(ev["release_kind"] == "print") & (ev["family"].isin(HIGH))]
    ev = ev[ev["date"] < "2025-10-01"]                 # unsealed only
    rows = []
    for _, e in ev.iterrows():
        for mode in ("continuation", "fade"):
            r = simulate(bars, e["ts_release_et"], mode, stop, target, hold)
            if r:
                r.update(family=e["family"], date=e["date"], mode=mode)
                rows.append(r)
    return pd.DataFrame(rows)


def summarise(df: pd.DataFrame, stop: float, label: str) -> None:
    dpp = DOLLARS_PER_POINT["NQ"]
    print(f"\n=== {label} ===")
    for mode, g in df.groupby("mode"):
        n = len(g)
        wins = int((g["pts"] > 0).sum())
        lo, hi = wilson(wins, n)
        ev = g["pts"].mean()
        print(f"  {mode:13s} n={n:3d}  win={wins/n*100:4.1f}% "
              f"CI[{lo*100:4.1f},{hi*100:4.1f}]  "
              f"EV={ev:+6.1f}pt (${ev*dpp:+,.0f})  R={ev/stop:+.2f}  "
              f"tot=${g['pts'].sum()*dpp:+,.0f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stop", type=float, default=50)
    ap.add_argument("--target", type=float, default=50)
    ap.add_argument("--hold", type=int, default=60)
    a = ap.parse_args()
    df = run(a.stop, a.target, a.hold)
    dpp = DOLLARS_PER_POINT["NQ"]
    print(f"POST-PRINT LANE — entry at T+1m open, stop {a.stop:.0f}pt "
          f"(${a.stop*dpp:,.0f}), target {a.target:.0f}pt "
          f"(${a.target*dpp:,.0f}), hold {a.hold}m")
    print(f"unsealed, high-impact, {df['date'].nunique()} events\n")
    print("outcome mix:")
    print(df.groupby("mode")["outcome"].value_counts(normalize=True)
            .mul(100).round(1).to_string())
    summarise(df, a.stop, "ALL EVENTS")
    big = df[df["rel_range"] >= df["rel_range"].median()]
    summarise(big, a.stop, "BIG release bars only (>= median range)")
    small = df[df["rel_range"] < df["rel_range"].median()]
    summarise(small, a.stop, "SMALL release bars only (< median)")
    print("\nper-family (continuation, all events):")
    c = df[df["mode"] == "continuation"]
    g = c.groupby("family").agg(n=("pts", "size"),
                                win=("pts", lambda s: round((s > 0).mean(), 3)),
                                ev_pts=("pts", "mean")).round(2)
    g["ev_usd"] = (g["ev_pts"] * dpp).round(0)
    print(g.to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
