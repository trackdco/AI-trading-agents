#!/usr/bin/env python3
"""A1 — clustering sensitivity curve (Phase A, blocking).

The first-of-fight reject book and S1's lift at X in {0.25, 0.5, 1.0, 2.0}W
(plus the X->0 limit, every trigger its own fight), both eras, day-boot
CIs. The valley procedure found no valley, so X=0.5W is a fallback with no
empirical support of its own: if the positive book only exists at 0.5W it
is a bookkeeping artifact and S1 was measured against a moving baseline.

    python -m scripts.htf_ma_x_sensitivity
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.htf_ma_clustering import assign_structural             # noqa: E402
from scripts.htf_ma_restate import boot_ci                          # noqa: E402

XS = [0.25, 0.5, 1.0, 2.0]


def book_at(F: pd.DataFrame, ccol: str) -> pd.DataFrame:
    R = F[(F.arm == "reject") & F.out_ship.notna() & (F.risk > 0)]
    return R.sort_values("t").groupby(ccol, as_index=False).first()


def s1_lift(book: pd.DataFrame) -> tuple[float, float, float]:
    cut = book.flowconf == 0
    ev, mu, q = book.out_ship.mean(), book[cut].out_ship.mean(), cut.mean()
    return q * (ev - mu) / (1 - q), book[~cut].out_ship.mean(), q


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/mtable_fit.parquet")
    F["era"] = np.where(F.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    P = pd.read_parquet(ROOT / "output/htf_ma_census/cluster_pairs.parquet")
    uniq = F[["sess_day", "t", "side", "w15", "arm",
              "n_attempts"]].drop_duplicates(["sess_day", "side", "t"])
    days = F.sess_day.nunique()

    print(f"{'X':>6s} {'fights':>7s} {'/day':>5s} | "
          f"{'EV H2-2025':>22s} | {'EV H1-2026':>22s} | {'pooled':>7s} | "
          f"{'S1 lift':>8s} {'EVafter':>8s} {'rm%':>5s}")

    # X -> 0 limit: every trigger its own fight (= all rows)
    R0 = F[(F.arm == "reject") & F.out_ship.notna() & (F.risk > 0)].copy()
    R0["cid0"] = np.arange(len(R0))
    rows = [("0(rows)", R0, "cid0")]
    for x in XS:
        ids = assign_structural(uniq, P, x)
        u2 = uniq.join(ids)
        Fx = F.merge(u2[["sess_day", "side", "t", "structural_cluster_id"]],
                     on=["sess_day", "side", "t"], how="left")
        rows.append((f"{x:.2f}W", Fx, "structural_cluster_id"))

    for label, Fx, ccol in rows:
        bk = book_at(Fx, ccol) if ccol != "cid0" else R0
        cells = {}
        for era, g in bk.groupby("era"):
            lo, hi = boot_ci(g, "out_ship", lambda s: s.out_ship.mean())
            cells[era] = f"{g.out_ship.mean():+.3f} [{lo:+.3f},{hi:+.3f}]"
        lift, ev_after, q = s1_lift(bk)
        print(f"{label:>6s} {len(bk):7d} {len(bk)/days:5.1f} | "
              f"{cells.get('H2-2025','—'):>22s} | "
              f"{cells.get('H1-2026','—'):>22s} | "
              f"{bk.out_ship.mean():+7.3f} | {lift:+8.3f} {ev_after:+8.3f} "
              f"{q*100:5.1f}")


if __name__ == "__main__":
    main()
