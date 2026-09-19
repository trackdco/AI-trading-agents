#!/usr/bin/env python3
"""PHASE 2 — the PRECONDITION, reported with numbers whether it passes or not.

Question, exactly as posed: does any variable from Phase 1's magnitude
analysis show REAL TIER-TO-TIER DIFFERENTIATION ACROSS 3+ TIERS — not a
top-vs-rest step, and not a bottom-bin cut like CONCORD?

Candidates are Phase 1's ENTRY-USABLE day-clustered survivors: excluded are
anything POST-ENTRY (not knowable at the decision bar) and anything on
PARTIAL COVERAGE. LAW2-MECHANICAL variables are carried into the test but
reported separately, because a ladder built on the R denominator is a
restatement of BR-29, not a behavioural edge.

Declared test, before the numbers are read:

  T1 ARITY      >= 3 distinct tiers are possible at all (binaries fail here)
  T2 SPREAD     top tier - bottom tier, day-clustered CI clear of zero
  T3 LADDER     >= 2 of the 4 adjacent-tier steps individually positive,
                AND the middle tiers separate: Q4 - Q2 day-clustered CI
                clear of zero. This is what distinguishes a LADDER from a
                top-vs-rest step.
  T4 NOT-TOP-ONLY   the spread from Q1..Q4 (excluding the top tier) must be
                >= 30% of the full Q1..Q5 spread. If nearly all the
                separation is Q5, it is a cut, not a ladder.

A variable must pass T1-T4 to earn a sizing ladder.

    python -m scripts.phase2_precondition
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.htf_ltf_report import (PAIRS as LP, assign as lassign,  # noqa: E402
                                    book as lbook, era)
from scripts.htf_room_gate import FLOOR, admissible                  # noqa: E402
from scripts.phase1_diagnose import dboot_diff                       # noqa: E402

OUT = ROOT / "output/htf_ma_census"
NTIER = 5


def main() -> None:
    A = pd.read_parquet(OUT / "phase1_diagnosis.parquet")
    E = A[A.clust_sig & ~A.post & ~A.partial].copy()
    E = E.sort_values("d_ev", key=abs, ascending=False)

    INC = pd.read_parquet(OUT / "incumbent_london.parquet")
    INC["t"] = pd.to_datetime(INC.t)
    T = pd.read_parquet(OUT / "ltf_fit.parquet")
    T["t"] = pd.to_datetime(T.t)
    FL = pd.read_parquet(OUT / "ltf_flow.parquet")
    FL["t"] = pd.to_datetime(FL.t)
    T = T.merge(FL, on=["sess_day", "t", "tf", "locus", "arm", "side"],
                how="left")
    T["era"] = era(T)
    T["scid"] = lassign(T, pd.read_parquet(LP), 0.5)
    B = lbook(T)
    ROOM = B[(B.risk >= FLOOR) & admissible(B) & (B.session == "LONDON")
             & (B.arm == "reject")]
    books = {"INCUMBENT LONDON (composite+sweep_b)": INC,
             "ROOM-GATED LONDON reject 3m": ROOM[ROOM.tf == 3],
             "ROOM-GATED LONDON reject 5m": ROOM[ROOM.tf == 5]}
    for tf in (3, 5):
        books[f"COMBINED incumbent + room {tf}m"] = pd.concat(
            [INC, ROOM[ROOM.tf == tf]], ignore_index=True)

    print("=" * 96)
    print("PHASE 2 — PRECONDITION. Reported with numbers whether it passes "
          "or not.")
    print("Candidates: Phase 1 ENTRY-USABLE day-clustered survivors "
          f"({len(E)} rows, {E.col.nunique()} distinct variables)")
    print("=" * 96)
    print("\nDeclared tests: T1 arity>=3 | T2 top-bottom spread CI clear | "
          "T3 >=2 positive steps AND Q4-Q2 CI clear | T4 non-top spread >=30%"
          " of total")

    res = []
    for r in E.itertuples():
        D = books[r.book].copy()
        D["risk_w"] = D.risk / D.w15
        c = r.col
        if c not in D.columns:
            continue
        d = D[D[c].notna()].copy()
        nun = d[c].nunique()
        print("\n" + "-" * 96)
        print(f"{r.book}  |  {c}   (dEV {r.d_ev:+.3f}, "
              f"{'LAW2-MECHANICAL' if r.mech else 'non-mechanical'})")
        if nun < 3:
            print(f"  T1 ARITY: FAIL — only {nun} distinct values "
                  f"(binary). A ladder is impossible by construction.")
            res.append((r.book, c, r.mech, False, "binary"))
            continue
        try:
            d["q"] = pd.qcut(d[c], NTIER, labels=False, duplicates="drop")
        except ValueError:
            print(f"  T1 ARITY: FAIL — cannot form {NTIER} tiers")
            res.append((r.book, c, r.mech, False, "no tiers"))
            continue
        nt = d.q.nunique()
        if nt < 3:
            print(f"  T1 ARITY: FAIL — only {nt} usable tiers")
            res.append((r.book, c, r.mech, False, f"{nt} tiers"))
            continue
        g = d.groupby("q").agg(ev=("out_ship", "mean"),
                               mfe=("mfe_r", "mean"),
                               wr=("out_ship", lambda x: (x > 0).mean()),
                               n=("out_ship", "size"),
                               med=(c, "median"))
        print(f"  T1 ARITY: pass ({nt} tiers, n/tier~{int(g.n.mean())})")
        print(f"     tier  " + "  ".join(f"Q{int(i)+1}" for i in g.index))
        print(f"     med   " + "  ".join(f"{g.med[i]:6.2f}" for i in g.index))
        print(f"     EV    " + "  ".join(f"{g.ev[i]:+6.3f}" for i in g.index))
        print(f"     MFE   " + "  ".join(f"{g.mfe[i]:6.2f}" for i in g.index))
        print(f"     win   " + "  ".join(f"{g.wr[i]*100:5.1f}%" for i in g.index))
        lo_i, hi_i = g.index.min(), g.index.max()
        # T2 spread
        m_top = d.q == hi_i
        sub = d[(d.q == hi_i) | (d.q == lo_i)]
        l2, h2 = dboot_diff(sub, "out_ship", sub.q == hi_i)
        t2 = np.isfinite(l2) and (l2 > 0 or h2 < 0)
        print(f"  T2 SPREAD  Q{int(hi_i)+1}-Q{int(lo_i)+1} = "
              f"{g.ev[hi_i]-g.ev[lo_i]:+.3f}  clustered CI "
              f"[{l2:+.3f},{h2:+.3f}]  -> {'pass' if t2 else 'FAIL'}")
        # T3 ladder
        steps = np.diff(g.ev.to_numpy())
        npos = int((steps > 0).sum())
        mid = d[d.q.isin([lo_i + 1, hi_i - 1])]
        if lo_i + 1 < hi_i - 1 and len(mid) > 40:
            l3, h3 = dboot_diff(mid, "out_ship", mid.q == hi_i - 1)
        else:
            l3 = h3 = np.nan
        t3 = (npos >= 2) and np.isfinite(l3) and (l3 > 0 or h3 < 0)
        print(f"  T3 LADDER  steps " + " ".join(f"{s:+.3f}" for s in steps)
              + f"  ({npos}/{len(steps)} positive) | mid-tier "
              f"Q{int(hi_i)}-Q{int(lo_i)+2} CI [{l3:+.3f},{h3:+.3f}] "
              f"-> {'pass' if t3 else 'FAIL'}")
        # T4 not-top-only
        full = abs(g.ev[hi_i] - g.ev[lo_i])
        nontop = abs(g.ev[hi_i - 1] - g.ev[lo_i]) if hi_i - 1 in g.index else 0.0
        frac = nontop / full if full > 0 else 0.0
        t4 = frac >= 0.30
        print(f"  T4 NOT-TOP-ONLY  non-top spread {nontop:+.3f} of full "
              f"{full:+.3f} = {frac*100:.0f}%  -> {'pass' if t4 else 'FAIL'}")
        ok = t2 and t3 and t4
        print(f"  ===> {'PASSES the precondition' if ok else 'does not pass'}")
        res.append((r.book, c, r.mech, ok, f"T2{'+' if t2 else '-'}"
                                           f"T3{'+' if t3 else '-'}"
                                           f"T4{'+' if t4 else '-'}"))

    print("\n" + "=" * 96)
    print("PRECONDITION VERDICT")
    print("=" * 96)
    P = [x for x in res if x[3]]
    Pn = [x for x in P if not x[2]]
    print(f"   candidates tested: {len(res)}")
    print(f"   passing all of T1-T4: {len(P)}")
    for b, c, m, _, tag in P:
        print(f"      {b[:40]:40s} {c:14s} "
              f"{'LAW2-MECHANICAL' if m else 'non-mechanical'}")
    print(f"   of those, NON-MECHANICAL (a behavioural ladder rather than a "
          f"restatement of BR-29): {len(Pn)}")
    if not Pn:
        print("\n   PHASE 2 STOPS HERE. No non-mechanical variable shows real "
              "tier-to-tier\n   differentiation across 3+ tiers. A sizing "
              "ladder is not forced onto binary\n   or mechanically-coupled "
              "signal.")
    else:
        print("\n   Proceed to Law 7 arithmetic on: "
              + ", ".join(f"{c} ({b})" for b, c, _, _, _ in Pn))


if __name__ == "__main__":
    main()
