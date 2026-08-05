#!/usr/bin/env python3
"""NYA-FA-01 hours-clock §3.2 autopsy — MFE/MAE + time segments on the
taught-clock population (>=4h outside). Minute-resolution walk against the
census stop/target (intrabar ordering may differ marginally from the 30-min
sim — declared). Checkpoints adapted to the multi-hour clock:
t+30/60/120/240/480 min.

    python -m scripts.nya_fa_hc_autopsy
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0
CHECKS = (30, 60, 120, 240, 480)


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts).set_index("ts").sort_index()
    H, L_, C = B.high.to_numpy(), B.low.to_numpy(), B.close.to_numpy()
    IDX = B.index

    E = pd.read_parquet(ROOT / "output/nya_fa_hoursclock.parquet")
    S = E[E.out_bars >= 8].reset_index(drop=True)

    rows = []
    for _, tr in S.iterrows():
        t0 = pd.Timestamp(tr.entry_t)
        i0 = IDX.searchsorted(t0)
        i1 = min(i0 + 5 * 1380, len(IDX))
        side, entry = tr.side, tr.entry
        stop = tr.ext
        tgt = tr.vah if side > 0 else tr.val
        risk = max(abs(entry - stop), 1e-9)
        rec = dict(day=tr.day, year=tr.year, net_r=(tr.pts - FR) / risk,
                   win=int(tr.pts - FR > 0), out_bars=tr.out_bars)
        mfe = mae = 0.0
        done = False
        exit_kind, exit_m = "cap", i1 - i0
        for m in range(1, i1 - i0):
            j = i0 + m
            hi, lo, cl = H[j], L_[j], C[j]
            fav = (hi - entry) if side > 0 else (entry - lo)
            adv = (entry - lo) if side > 0 else (hi - entry)
            if not done:
                mfe, mae = max(mfe, fav), max(mae, adv)
                if (side > 0 and lo <= stop) or (side < 0 and hi >= stop):
                    done, exit_kind, exit_m = True, "stop", m
                elif (side > 0 and hi >= tgt) or (side < 0 and lo <= tgt):
                    done, exit_kind, exit_m = True, "target", m
            if m in CHECKS:
                r_now = ((cl - entry) if side > 0 else (entry - cl)) / risk
                rec[f"open{m}"] = int(not done)
                rec[f"r{m}"] = r_now if not done else np.nan
                rec[f"mf{m}"] = mfe / risk
                rec[f"ma{m}"] = -mae / risk
            if done and m >= max(CHECKS):
                break
        rec.update(mfe=mfe / risk, mae=-mae / risk, exit_kind=exit_kind, exit_m=exit_m)
        rows.append(rec)

    A = pd.DataFrame(rows)
    A.to_parquet(ROOT / "output/nya_fa_hc_autopsy.parquet", index=False)
    W, Lo = A[A.win == 1], A[A.win == 0]
    print(f"taught-clock n={len(A)} | winners {len(W)} losers {len(Lo)}")
    print(f"exit kinds (minute-walk): {A.exit_kind.value_counts().to_dict()}")
    print(f"LOSERS: median MFE {Lo.mfe.median():.2f}R | ever>=+0.5R {(Lo.mfe>=0.5).mean():.0%} | "
          f"ever>=+1R {(Lo.mfe>=1.0).mean():.0%} | median exit {Lo.exit_m.median():.0f}min")
    print(f"WINNERS: median MAE {-W.mae.median():.2f}R | p10 worst {-W.mae.quantile(0.10):.2f}R | "
          f"median time-to-target {W.exit_m.median():.0f}min")
    base = A.win.mean()
    print(f"\nsegments (still-open-at-t; base WR {base:.0%}):")
    for t in (60, 120, 240):
        op = A[A[f"open{t}"] == 1]
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
