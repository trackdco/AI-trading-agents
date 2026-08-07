#!/usr/bin/env python3
"""NYA-DS-01 trial 4 — §3.2 loser autopsy + MFE/MAE + time-segment schema
on the L1b expression. Checkpoints adapted to the hourly clock (declared in
the candidate file): t+5/15/30/60/120 minutes from entry. Population
semantics per §5.12-5: signature stats condition on still-open-at-t.

    python -m scripts.nya_ds_autopsy
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0
CHECKS = (5, 15, 30, 60, 120)


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts).set_index("ts").sort_index()
    B["gday"] = pd.Series((B.index + pd.Timedelta(hours=6)).date, index=B.index).astype(str)

    T = pd.read_parquet(ROOT / "output/nya_ds_census.parquet")
    pen_t = pd.qcut(T.pen, 3, labels=["shallow", "mid", "deep"])
    gapc = pd.cut(T.gap, [-1e9, -20, 20, 1e9], labels=["against", "flat", "with"])
    L = T[(gapc != "against") & (pen_t != "deep")].reset_index(drop=True)

    rows = []
    for _, tr in L.iterrows():
        t0 = pd.Timestamp(tr.bar_t) + pd.Timedelta(hours=1)
        is_am = tr.window == "AM"
        cutoff = pd.Timestamp(tr.bar_t).normalize() + pd.Timedelta(hours=12 if is_am else 16)
        fwd = B[(B.index >= t0) & (B.index < cutoff) & (B.gday == tr.day)]
        side, entry, stop, risk = tr.side, tr.entry, tr.stop, tr.risk
        tgt = entry + side * 2 * risk
        rec = dict(day=tr.day, year=tr.year, net_r=(tr.pts - FR) / risk,
                   win=int(tr.pts - FR > 0))
        mfe = mae = 0.0
        done, exit_m, exit_kind = False, None, "time"
        for m, (hi, lo, cl) in enumerate(fwd[["high", "low", "close"]].to_numpy(), start=1):
            fav = (hi - entry) if side > 0 else (entry - lo)
            adv = (entry - lo) if side > 0 else (hi - entry)
            if not done:
                mfe, mae = max(mfe, fav), max(mae, adv)
                if (side > 0 and lo <= stop) or (side < 0 and hi >= stop):
                    done, exit_m, exit_kind = True, m, "stop"
                elif (side > 0 and hi >= tgt) or (side < 0 and lo <= tgt):
                    done, exit_m, exit_kind = True, m, "target"
            if m in CHECKS:
                r_now = ((cl - entry) if side > 0 else (entry - cl)) / risk
                rec[f"open{m}"] = int(not done)
                rec[f"r{m}"] = r_now if not done else np.nan
                rec[f"mf{m}"] = mfe / risk
                rec[f"ma{m}"] = -mae / risk
            if done and m >= max(CHECKS):
                break
        rec["mfe"] = mfe / risk
        rec["mae"] = -mae / risk
        rec["exit_m"] = exit_m if exit_m else len(fwd)
        rec["exit_kind"] = exit_kind
        rows.append(rec)

    A = pd.DataFrame(rows)
    A.to_parquet(ROOT / "output/nya_ds_autopsy.parquet", index=False)
    W, Lo = A[A.win == 1], A[A.win == 0]
    print(f"L1b n={len(A)} | winners {len(W)} losers {len(Lo)}")
    print(f"exit kinds: {A.exit_kind.value_counts().to_dict()}")
    print(f"LOSERS: median MAE {-Lo.mae.median():.2f}R (they die at -1R) | "
          f"median MFE {Lo.mfe.median():.2f}R | ever>=+0.5R: {(Lo.mfe>=0.5).mean():.0%} | "
          f"ever>=+1R: {(Lo.mfe>=1.0).mean():.0%} | median time-to-exit {Lo.exit_m.median():.0f}min")
    print(f"WINNERS: median MAE {-W.mae.median():.2f}R | worst survived "
          f"{-W.mae.min():.2f}R | median time-to-target {W.exit_m.median():.0f}min")
    base = A.win.mean()
    print(f"\ntime-segment signatures (still-open-at-t conditioning; base WR {base:.0%}):")
    for t in (15, 30, 60):
        op = A[A[f"open{t}"] == 1]
        if not len(op):
            continue
        press = op[(op[f"mf{t}"] >= 0.5) & (op[f"r{t}"] > 0) & (op[f"mf{t}"] - op[f"r{t}"] <= 0.25)]
        dying = op[op[f"ma{t}"] <= -0.5]
        give = op[(op[f"r{t}"] > 0) & (op[f"mf{t}"] - op[f"r{t}"] > 0.25)]
        print(f" t+{t}: open {len(op)}")
        for lbl, g in (("PRESS", press), ("DYING", dying), ("GIVEBACK", give)):
            if len(g) >= 10:
                yr = " ".join(f"{y}:{gg.win.mean():.0%}(n={len(gg)})"
                              for y, gg in g.groupby("year") if len(gg) >= 4)
                print(f"   {lbl}: n={len(g)} WR {g.win.mean():.0%} | {yr}")
            else:
                print(f"   {lbl}: n={len(g)} — thin")


if __name__ == "__main__":
    main()
