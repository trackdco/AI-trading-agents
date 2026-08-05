#!/usr/bin/env python3
"""P7 — absorption / effort-result feature library (frozen definitions).

Formalizes the flow grammar both intakes teach and our own canon already
exploits (W-gate, d5-gate), as committed per-minute features on the flow span
(output/fp_minutes.parquet joined to 1-min bars). Consumed by conditioning
searches and autopsies; not a strategy, no trials, no ledger entries.

Definitions (all baselines are SAME-MINUTE-OF-DAY medians over the prior 20
sessions — no lookahead, regime-adaptive):
  eff_z      volume effort: minute volume / baseline volume (ratio).
  res        result: |close - open| of the minute bar, in points.
  res_z      result vs baseline |close-open| for that minute-of-day.
  absorb     ABSORPTION flag: eff_z >= 2 and res_z <= 0.5 — big effort, no
             reward. Signed: absorb_side = -sign(delta) (the absorbed
             aggressor's side; delta>0 absorbed => sellers won the level).
  effortless EFFORTLESS-MOVE flag: eff_z <= 0.75 and res_z >= 2 — path of
             least resistance (book thin behind the move).
  dz         delta z-ratio: delta / baseline |delta| for that minute.
  cvd        session-cumulative delta from 18:00 session start.

    python -m scripts.flow_features   # writes output/flow_minute_features.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BASE_N = 20


def main() -> None:
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    fp = fp.assign(clock=fp.index.strftime("%H:%M"),
                   gday=(fp.index + pd.Timedelta(hours=6)).date)
    fp["gday"] = fp["gday"].astype(str)

    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(mi=ts.dt.floor("min"))
    bars = B.set_index("mi")[["open", "close", "high", "low"]]

    F = fp.join(bars, how="inner")
    F["res"] = (F.close - F.open).abs()

    # same-minute-of-day rolling baselines over prior BASE_N sessions
    F = F.sort_index()
    g = F.groupby("clock", group_keys=False)
    F["vol_base"] = g["vol"].apply(lambda s: s.shift(1).rolling(BASE_N, min_periods=5).median())
    F["res_base"] = g["res"].apply(lambda s: s.shift(1).rolling(BASE_N, min_periods=5).median())
    F["dabs_base"] = g["delta"].apply(lambda s: s.abs().shift(1).rolling(BASE_N, min_periods=5).median())

    F["eff_z"] = F["vol"] / F["vol_base"].clip(lower=1)
    F["res_z"] = F["res"] / F["res_base"].clip(lower=0.25)
    F["dz"] = F["delta"] / F["dabs_base"].clip(lower=1)
    F["absorb"] = (F.eff_z >= 2.0) & (F.res_z <= 0.5)
    F["absorb_side"] = np.where(F.absorb, -np.sign(F.delta), 0).astype(int)
    F["effortless"] = (F.eff_z <= 0.75) & (F.res_z >= 2.0)
    F["cvd"] = F.groupby("gday")["delta"].cumsum()

    out = F[["gday", "clock", "vol", "delta", "res", "eff_z", "res_z", "dz",
             "absorb", "absorb_side", "effortless", "cvd", "high", "low", "close"]]
    out.to_parquet(ROOT / "output/flow_minute_features.parquet")
    print(f"{len(out)} minutes, {out.gday.nunique()} sessions "
          f"{out.gday.min()} .. {out.gday.max()}")
    print(f"absorb rate {out.absorb.mean():.2%} | effortless rate {out.effortless.mean():.2%}")
    rth = out[(out.clock >= '09:30') & (out.clock < '16:00')]
    print(f"RTH: absorb {rth.absorb.mean():.2%}, effortless {rth.effortless.mean():.2%}")


if __name__ == "__main__":
    main()
