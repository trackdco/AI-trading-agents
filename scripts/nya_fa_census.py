#!/usr/bin/env python3
"""NYA-FA-01 — L0 census per docs/PREREG-failed-auction.md. Base rates only.

Event: first 1-min close outside the live composite's VAH/VAL (age >= 2 at
the open), RTH 09:30-15:00. FAIL = 1-min close back inside within the window
(30/60/120 min declared); ACCEPT = no re-entry close within the window.
Post-FAIL: does price traverse to the composite's other edge by 16:00 (the
"80% rule" measured honestly)? POC-interrupt and time-to-traverse recorded.
Post-ACCEPT: continuation excursion in composite-width units.

    python -m scripts.nya_fa_census   # writes output/nya_fa_census.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WINDOWS = (30, 60, 120)


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    C = pd.read_parquet(ROOT / "output/nya_composites.parquet").set_index("day")

    rows = []
    for d, r in R.groupby("gday"):
        if d not in C.index or not (C.loc[d, "comp_age"] >= 2):
            continue
        vah, val = float(C.loc[d, "comp_vah"]), float(C.loc[d, "comp_val"])
        poc = float(C.loc[d, "comp_poc"])
        width = vah - val
        if width <= 0:
            continue
        r = r.sort_values("ts").reset_index(drop=True)
        elig = r[r.clock < "15:00"]
        out_up = elig[elig.close > vah]
        out_dn = elig[elig.close < val]
        t_up = out_up.index[0] if len(out_up) else None
        t_dn = out_dn.index[0] if len(out_dn) else None
        if t_up is None and t_dn is None:
            continue
        if t_dn is None or (t_up is not None and t_up < t_dn):
            i0, side = t_up, 1
        else:
            i0, side = t_dn, -1
        edge = vah if side > 0 else val
        far = val if side > 0 else vah
        brk = r.loc[i0]
        after = r.loc[i0 + 1:]
        rec = dict(day=d, year=d[:4], side=side, width=width,
                   comp_age=int(C.loc[d, "comp_age"]),
                   brk_clock=brk.clock, ext_pre=0.0)
        # max extension beyond the edge before any re-entry (whole day)
        reent = after[(after.close < edge) if side > 0 else (after.close > edge)]
        i_re = reent.index[0] if len(reent) else None
        seg = after.loc[:i_re] if i_re is not None else after
        rec["ext_max"] = float((seg.high.max() - edge) if side > 0 else (edge - seg.low.min())) / width
        rec["mins_out"] = int((i_re - i0)) if i_re is not None else int(len(after))
        for w in WINDOWS:
            win = after.loc[: i0 + w]
            fail_rows = win[(win.close < edge) if side > 0 else (win.close > edge)]
            rec[f"fail{w}"] = int(len(fail_rows) > 0)
        # post-FAIL traverse (first re-entry any time before 15:00)
        if i_re is not None and r.loc[i_re].clock < "15:00":
            tail = r.loc[i_re + 1:]
            hit_far = ((tail.low <= far).any() if side > 0 else (tail.high >= far).any())
            hit_poc = ((tail.low <= poc).any() if side > 0 else (tail.high >= poc).any())
            rec.update(fail_any=1, trav_far=int(hit_far), trav_poc=int(hit_poc),
                       reent_clock=r.loc[i_re].clock)
            if hit_far:
                idx = tail[(tail.low <= far)].index[0] if side > 0 else tail[(tail.high >= far)].index[0]
                rec["trav_mins"] = int(idx - i_re)
        else:
            rec.update(fail_any=0, trav_far=np.nan, trav_poc=np.nan)
            cont = after
            rec["accept_ext"] = float((cont.high.max() - edge) if side > 0 else (edge - cont.low.min())) / width
        rows.append(rec)

    F = pd.DataFrame(rows)
    F.to_parquet(ROOT / "output/nya_fa_census.parquet", index=False)
    F["era"] = F.year.map(lambda y: "23-24" if y in ("2023", "2024") else y)
    print(f"break events: {len(F)} (long {int((F.side>0).sum())}/short {int((F.side<0).sum())})")
    for era, g in F.groupby("era"):
        line = f"  {era}: n={len(g)}"
        for w in WINDOWS:
            line += f" | fail{w} {g[f'fail{w}'].mean():.0%}"
        fa = g[g.fail_any == 1]
        line += (f" | after-fail: traverse-POC {fa.trav_poc.mean():.0%}, "
                 f"traverse-far {fa.trav_far.mean():.0%} (n={len(fa)})")
        print(line)
    acc = F[F.fail_any == 0]
    print(f"ACCEPT days: n={len(acc)}, median continuation {acc.accept_ext.median():.2f} widths, "
          f">=0.5 width {(acc.accept_ext>=0.5).mean():.0%}")
    fa = F[F.fail_any == 1]
    print(f"FAIL days: median mins outside {fa.mins_out.median():.0f}, median ext {fa.ext_max.median():.2f} widths")
    print("ext_max tercile → traverse-far (fail days):")
    for b, g in fa.groupby(pd.qcut(fa.ext_max, 3, labels=["shallow", "mid", "deep"]), observed=True):
        print(f"  {b}: n={len(g)} trav-far {g.trav_far.mean():.0%} trav-poc {g.trav_poc.mean():.0%}")
    print("mins_out tercile → traverse-far (fail days):")
    for b, g in fa.groupby(pd.qcut(fa.mins_out, 3, labels=["quick", "mid", "long"]), observed=True):
        print(f"  {b}: n={len(g)} trav-far {g.trav_far.mean():.0%} trav-poc {g.trav_poc.mean():.0%}")


if __name__ == "__main__":
    main()
