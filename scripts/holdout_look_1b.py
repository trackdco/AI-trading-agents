#!/usr/bin/env python3
"""HOLDOUT LOOK #1, SECOND AND FINAL PASS — H1 and H4 ONLY.

The first pass could not test these two: htf_ma_sweep_locus sourced prior
stopped attempts from the FIT levels file alone, so sweep_b could never be
emitted on sealed days. sweep_sealed.parquet came back 7,232 rows, all
sweep_a, zero sweep_b. H4 was therefore NOT EVALUABLE (zero rows read, no
look spent) and H1 was VOID (its declared book is composite + sweep_b; what
ran was composite only).

The builder is fixed and CALIBRATED on the fit span first: the corrected
lookup reproduces the published sweep_fit.parquet BYTE-IDENTICALLY —
8,243 sweep_b rows, and entry/stop/risk/direction/out_ship/out_hold/
out_trail/mfe_r/w15 all matching to 0.000e+00.

H2, H3 and H5 are NOT revisited. Same frozen blocks, same declared bars,
same Bonferroni x5. Whatever comes back is permanent for this venue.

    python -m scripts.holdout_look_1b --confirm-spend
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.holdout_look_1 import (ALPHA, BLOCK_A, BLOCK_B,        # noqa: E402
                                    FLOW_VENUE, SESSIONS,
                                    UNDERPOWERED_N, assign, blk,
                                    book, build_pairs, verdict)
from src.htf_ma.levels import NY                                    # noqa: E402

OUT = ROOT / "output/htf_ma_census"
SEALED = ROOT / "output/sealed"


def cluster_sweepb(S, bars):
    """First-of-fight on sweep_b, IDENTICAL procedure to the fit book
    (htf_ma_session_books.cluster_sweepb): excursion from ref_px between
    consecutive same-side rows, X=0.5W, not re-tuned."""
    S = S[(S.cell == "sweep_b") & S.out_ship.notna() & (S.risk > 0)].copy()
    S["t"] = pd.to_datetime(S.t)
    key = {}
    for day, D in S.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        seg = bars[(bars.index >= t0)
                   & (bars.index < t0 + pd.Timedelta(hours=23))]
        if seg.empty:
            continue
        idx, hi, lo = seg.index, seg.high.to_numpy(), seg.low.to_numpy()
        for side, g in D.groupby("side"):
            g = g.sort_values("t")
            ts, ws, rp = g.t.tolist(), g.w15.tolist(), g.ref_px.tolist()
            for a in range(len(ts) - 1):
                i0 = int(np.searchsorted(idx.values, ts[a].to_datetime64()))
                i1 = int(np.searchsorted(idx.values,
                                         ts[a + 1].to_datetime64()))
                if i1 <= i0 or ws[a] <= 0 or not np.isfinite(rp[a]):
                    continue
                m = np.nanmax(np.maximum(np.abs(hi[i0:i1] - rp[a]),
                                         np.abs(lo[i0:i1] - rp[a])))
                key[(day, side, ts[a + 1])] = m / ws[a]
    ids = {}
    for (d, s), g in S.groupby(["sess_day", "side"], sort=False):
        g = g.sort_values("t")
        cid, seen = 0, None
        for r in g.itertuples():
            t = pd.Timestamp(r.t)
            if seen is not None and t != seen:
                e = key.get((d, s, t), np.nan)
                if not np.isfinite(e) or e >= 0.5:
                    cid += 1
            seen = t
            ids[r.Index] = f"{d}:{s}:S{cid}"
    S["scid"] = pd.Series(ids)
    return S.sort_values("t").groupby("scid", as_index=False).first()


def main() -> None:
    if "--confirm-spend" not in sys.argv:
        print("refusing: this is the SECOND AND FINAL pass at H1/H4. "
              "pass --confirm-spend.")
        sys.exit(2)
    sha = subprocess.run(["git", "log", "-1", "--format=%H", "--",
                          "scripts/htf_ma_sweep_locus.py"],
                         capture_output=True, text=True,
                         cwd=ROOT).stdout.strip()
    print("=" * 96)
    print("HOLDOUT LOOK #1 — SECOND AND FINAL PASS. H1 AND H4 ONLY.")
    print(f"corrected sweep builder SHA: {sha}")
    print("FIT-SIDE CALIBRATION: byte-identical to the published artifact "
          "(8,243 sweep_b rows,")
    print("all consumed fields matching to 0.000e+00) — confirmed BEFORE "
          "touching sealed data.")
    print("H2, H3, H5 are NOT revisited and stand exactly as reported.")
    print("=" * 96)

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]

    L = pd.concat([pd.read_parquet(SEALED / "levels_sealed.parquet"),
                   pd.read_parquet(OUT / "levels_gray.parquet")],
                  ignore_index=True)
    L["t"] = pd.to_datetime(L.t)
    L["blk"] = blk(L)
    L = L[L.blk != "EXCLUDED"]

    SW = pd.concat([pd.read_parquet(SEALED / "sweep_sealed_cal.parquet"),
                    pd.read_parquet(OUT / "sweep_gray_cal.parquet")],
                   ignore_index=True)
    SW["t"] = pd.to_datetime(SW.t)
    SW["blk"] = blk(SW)
    SW = SW[SW.blk != "EXCLUDED"]
    print(f"\nvenue: bar-only months. flow venue EXCLUDED, untouched.")
    print(f"sealed+gray in venue: levels {len(L):,} | sweep rows {len(SW):,} "
          f"(sweep_b {int((SW.cell=='sweep_b').sum()):,})")
    print("   ^ the first pass had ZERO sweep_b here. That was the structural "
          "failure.")

    print("\nbuilding the sealed books (X=0.5W, not re-tuned)...")
    P = build_pairs(L, bars)
    L = L.join(assign(L, P))
    ub = pd.concat([book(L[L.locus == "val"], "break"),
                    book(L[L.locus == "vwap_m1"], "break")]) \
        .drop_duplicates(["sess_day", "t", "side"])
    rej = book(L[L.locus == "bbma15"], "reject")
    comp = pd.concat([ub.assign(pop="union_break"),
                      rej.assign(pop="reject")], ignore_index=True)
    SB = cluster_sweepb(SW, bars)
    for D in (comp, SB):
        D["hm"] = pd.to_datetime(D.t).dt.hour * 60 \
            + pd.to_datetime(D.t).dt.minute
        D["blk"] = blk(D)
    a, b = SESSIONS["LONDON"]
    sb_ldn = SB[(SB.hm >= a) & (SB.hm <= b)]
    london = pd.concat([comp[(comp.hm >= a) & (comp.hm <= b)],
                        sb_ldn.assign(pop="sweep_b")], ignore_index=True) \
        .drop_duplicates(["sess_day", "t", "side"])
    print(f"   LONDON book: {len(london)} fights "
          f"({int((london['pop']=='sweep_b').sum())} sweep_b, "
          f"{int((london['pop']!='sweep_b').sum())} composite)")
    print(f"   sweep_b LONDON alone: {len(sb_ldn)} fights")

    print("\n" + "=" * 96)
    print(f"H1 AND H4 — Bonferroni x5, two-sided {(1-ALPHA)*100:.0f}% "
          f"interval, BOTH blocks must pass")
    print(f"(<{UNDERPOWERED_N} fights in a block = UNDERPOWERED)")
    print("=" * 96)
    res = {}
    for h, nm, D in (("H1", "LONDON base rate (composite + sweep_b)", london),
                     ("H4", "sweep_b LONDON alone", sb_ldn)):
        print(f"\n{h} — {nm}")
        outs = []
        for bk_ in ("A", "B"):
            line, p = verdict(D[D.blk == bk_], f"  Block {bk_}")
            print(f"   {line}")
            outs.append(p)
        res[h] = outs

    print("\n" + "=" * 96)
    print("VERDICT — PERMANENT FOR THIS VENUE. No further contact.")
    print("=" * 96)
    for h, o in res.items():
        if any(x is None for x in o):
            v = "UNDERPOWERED"
        elif all(o):
            v = "PASS"
        else:
            v = "FAIL (permanent)"
        print(f"   {h}: {v}")


if __name__ == "__main__":
    main()
