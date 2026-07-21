"""Heatmap (resting depth) + price-resolved footprint readers for the golden-window study.

HONEST SCOPE NOTE (the data limits what these can mean):
  * The depth CSVs are TOP-10 MBP snapshots — one book state per minute, ~10 levels each side,
    spanning only ~2.5 points around the inside. They therefore show the NEAR-TOUCH book at the
    level, NOT resting walls 100pt away. So the "liquidity magnet" here is an at-the-level book
    IMBALANCE (is size stacked toward the target side or against it), not a far draw-of-liquidity
    target. Coverage is 08:00–10:29 ET only, which fully contains the 09:40–10:15 entry window.
  * The footprint is true aggressor-side (B=buy, A=sell) resolved by PRICE, so we can read what
    aggressors are doing in the price band AT the level during the entry candle.
"""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd


class HeatBook:
    """Per-minute top-10 resting depth. Answers the near-touch book imbalance at an entry."""

    def __init__(self, depth_dir: str, tz: str):
        self.d = {}
        for f in sorted(glob.glob(os.path.join(depth_dir, "nq_depth_*_ny.csv"))):
            day = os.path.basename(f).split("_")[2]           # YYYY-MM-DD
            df = pd.read_csv(f)
            df["ts"] = pd.to_datetime(df["ts"])
            if df["ts"].dt.tz is None:
                df["ts"] = df["ts"].dt.tz_localize(tz)
            # normalize to ns resolution so min_i (int64 ns) matches Timestamp.value (ns) —
            # the CSVs parse to microsecond dtype, which otherwise mismatches by 1000x.
            df["min_i"] = pd.DatetimeIndex(df["ts"].dt.floor("min")).as_unit("ns").asi8
            self.d[day] = df

    def imbalance(self, ts: pd.Timestamp, entry: float, direction: str, near_pts: float):
        """Resting size stacked toward the target side vs against, within near_pts of entry.

        long : target side = ASKS above entry (price is drawn up toward them); against = BIDS below.
        short: target side = BIDS below entry; against = ASKS above.
        Returns dict(target, against, ratio) or None if no book that minute.
        ratio = target / (target+against): > 0.5 means the book leans toward the target.
        """
        day = str(ts.date())
        df = self.d.get(day)
        if df is None:
            return None
        mi = ts.floor("min").value
        m = df[df["min_i"] == mi]
        if not len(m):
            m = df[df["min_i"] == mi - 60_000_000_000]        # fall back one minute
            if not len(m):
                return None
        asks = m[(m["side"] == "ask") & (m["price"] > entry) & (m["price"] <= entry + near_pts)]
        bids = m[(m["side"] == "bid") & (m["price"] < entry) & (m["price"] >= entry - near_pts)]
        a = float(asks["size"].sum()); b = float(bids["size"].sum())
        target, against = (a, b) if direction == "long" else (b, a)
        tot = target + against
        return dict(target=target, against=against, ratio=(target / tot if tot > 0 else np.nan))


class FootprintBook:
    """Price-resolved aggressor footprint, sliced to the study window for at-level reads."""

    def __init__(self, cvd_glob: str, tz: str, win_start="09:35", win_end="10:20"):
        files = sorted(glob.glob(cvd_glob))
        parts = []
        for f in files:
            fp = pd.read_parquet(f, columns=["ts_minute", "price", "side", "volume"])
            fp["ts"] = pd.to_datetime(fp["ts_minute"], utc=True).dt.tz_convert(tz)
            t = fp["ts"].dt.time
            fp = fp[(t >= pd.Timestamp(win_start).time()) & (t <= pd.Timestamp(win_end).time())]
            parts.append(fp[["ts", "price", "side", "volume"]])
        fp = pd.concat(parts, ignore_index=True).sort_values("ts")
        self.ts_i = fp["ts"].astype("int64").to_numpy()
        self.price = fp["price"].to_numpy("float64")
        self.signed = np.where(fp["side"].to_numpy() == "B", fp["volume"], -fp["volume"]).astype("float64")
        self.vol = fp["volume"].to_numpy("float64")

    def at_level(self, open_ts: pd.Timestamp, close_ts: pd.Timestamp, level: float,
                 tol: float, direction: str):
        """Net aggressor delta in the price band [level-tol, level+tol] over [open_ts, close_ts).

        Oriented to the trade: for a long at support, positive oriented-delta = aggressive BUYING
        being done at the level (demand stepping in / sellers absorbed). Returns dict or None.
        """
        lo = int(np.searchsorted(self.ts_i, open_ts.value, "left"))
        hi = int(np.searchsorted(self.ts_i, close_ts.value, "left"))
        if hi <= lo:
            return None
        pr = self.price[lo:hi]
        band = (pr >= level - tol) & (pr <= level + tol)
        if not band.any():
            return dict(delta=0.0, oriented=0.0, vol=0.0)
        net = float(self.signed[lo:hi][band].sum())
        vol = float(self.vol[lo:hi][band].sum())
        return dict(delta=net, oriented=(net if direction == "long" else -net), vol=vol)
