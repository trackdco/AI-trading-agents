#!/usr/bin/env python3
"""ROOM-TO-RUN AS A STANDALONE GATE — DECLARATIONS-room-to-run.md.

Runs exactly what §1-§4 declare, and nothing else:

  1  the gate, both declared constructions (floor-isolated, as-traded),
     per session x TF x arm, with the Law-7 marginal lift and the PAIRED
     day-boot CI on the LIFT in both eras
  2  natural frequency — reported, never targeted (§3)
  3  threshold sensitivity {2,3,4,5}R — reported, never selected on
  4  X sensitivity {0.25,0.5,1.0,2.0}W, and costs at 0.5/1.0/1.5pt
  5  the ACCOUNT LAYER: daily-R distribution, worst-day R, max
     non-breaching size against the $2,000 EOD trailing drawdown, then
     P(graduate) / P(death) against the book's OWN ungated baseline

NO CONCORD. NO FLOW FEATURES. NO FREQUENCY MATCHING. NO HOLDOUT CONTACT.
This is a bar-only claim; it never touches the flow venue.

    python -m scripts.htf_room_gate
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.htf_ma_account_lab as AL                             # noqa: E402
from scripts.htf_ltf_report import (PAIRS, SESS, XS, assign,        # noqa: E402
                                    book, boot_lift, boot_mean, era)

FIT = ROOT / "output/htf_ma_census/ltf_fit.parquet"
CAND_TF = [3, 5]                 # candidates
CTRL_TF = [2, 15]                # reported controls, never candidates
XDEC, FLOOR, THR = 0.5, 2.0, 3.0
THRS = [2.0, 3.0, 4.0, 5.0]      # sensitivity only
BAR_LIFT, BAR_FREQ = 0.05, 0.5
DD = 2000.0                      # the EOD trailing drawdown, in dollars
SEED, DRAWS, YEAR = 20260807, 1500, 250
NCELL = 12                       # 2 TF x 3 sessions x 2 arms


def admissible(d: pd.DataFrame, thr: float = THR) -> pd.Series:
    """The declared gate: room >= thr R ahead, OR open space (no level
    ahead — a category, not missing data)."""
    return d.next_lvl_R.isna() | (d.next_lvl_R >= thr)


def grad(day_r: np.ndarray, pol: dict) -> tuple:
    rng = np.random.default_rng(SEED)
    seqs = [rng.integers(0, len(day_r), YEAR) for _ in range(DRAWS)]
    runs = [AL.run_account(day_r, s, pol, payout_at=6000.) for s in seqs]
    return (float(np.mean([r["end_state"] == "graduated" for r in runs])),
            float(np.mean([len(r["funded_deaths"]) > 0 for r in runs])),
            float(np.mean([sum(w for _, w in r["wd"]) - r["fees"]
                           for r in runs])))


def main() -> None:
    F = pd.read_parquet(FIT)
    F["t"] = pd.to_datetime(F.t)
    F["era"] = era(F)
    F["scid"] = assign(F, pd.read_parquet(PAIRS), XDEC)
    B = book(F)
    nd = F.sess_day.nunique()
    all_days = sorted(F.sess_day.unique())

    print("ROOM-TO-RUN GATE — DECLARATIONS-room-to-run.md")
    print(f"fit {F.sess_day.min()}..{F.sess_day.max()}, {nd} days, "
          f"X={XDEC}W, floor={FLOOR}pt, threshold={THR}R")
    print("NO concord, NO flow, NO frequency matching, NO holdout contact.\n")

    print("=" * 78)
    print("§0 RESTATEMENT (already on the record — NOT a test)")
    print("=" * 78)
    for tf in CAND_TF + CTRL_TF:
        g = B[(B.tf == tf) & (B.risk >= FLOOR)]
        k = g[admissible(g)]
        lift = k.out_ship.mean() - g.out_ship.mean()
        print(f"   TF={tf:2d} pooled-over-sessions lift {lift:+.3f}  "
              f"(published: 3m +0.212, 5m +0.214, 2m +0.185)")
    print("   ^ reproduced only to prove the harness matches; carries no "
          "evidential weight.")

    # ---------------------------------------------------------- §1 + §2 --
    print("\n" + "=" * 78)
    print("1. THE GATE, PER SESSION x TF x ARM — the declared unit")
    print(f"   Bar: lift >= {BAR_LIFT:+.2f}R AND paired day-boot CI on the "
          f"LIFT clear of zero in BOTH eras")
    print(f"   Bonferroni on the candidate family: alpha = 0.05/{NCELL} "
          f"= {0.05/NCELL:.4f}")
    print("=" * 78)
    rows = []
    for mode, label in (("primary", "PRIMARY — floor on BOTH sides, "
                                    "isolates room-to-run"),
                        ("astraded", "AS-TRADED — floor is part of the gate")):
        print(f"\n### {label}")
        print(f"   {'sess':7s} {'tf':>3s} {'arm':6s} {'n_base':>7s} "
              f"{'n_keep':>7s} {'keep/day':>9s} {'EV_base':>8s} {'EV_keep':>8s} "
              f"{'lift':>8s} {'H2 lift CI':>19s} {'H1 lift CI':>19s} "
              f"{'win k/c':>13s}  bar")
        for tf in CAND_TF + CTRL_TF:
            for s in SESS:
                for arm in ("reject", "break", "BOTH"):
                    d = B[(B.tf == tf) & (B.session == s)]
                    if arm != "BOTH":
                        d = d[d.arm == arm]
                    base = d[d.risk >= FLOOR] if mode == "primary" else d
                    keep = base[admissible(base)] if mode == "primary" else \
                        d[(d.risk >= FLOOR) & admissible(d)]
                    cut = base.drop(keep.index, errors="ignore")
                    if len(base) < 40 or len(keep) < 15 or len(cut) < 15:
                        continue
                    lift = keep.out_ship.mean() - base.out_ship.mean()
                    cis, ok = [], []
                    for e in ("H2-2025", "H1-2026"):
                        lo, hi = boot_lift(base[base.era == e],
                                           keep[keep.era == e])
                        cis.append(f"[{lo:+.3f},{hi:+.3f}]"
                                   + ("!" if lo > 0 else " "))
                        ok.append(np.isfinite(lo) and lo > 0)
                    passed = (lift >= BAR_LIFT) and all(ok)
                    cand = tf in CAND_TF
                    if mode == "primary" and arm == "BOTH":
                        rows.append({"tf": tf, "sess": s, "lift": lift,
                                     "pass": passed, "cand": cand,
                                     "n": len(keep), "fpd": len(keep) / nd})
                    print(f"   {s:7s} {tf:3d} {arm:6s} {len(base):7d} "
                          f"{len(keep):7d} {len(keep)/nd:9.2f} "
                          f"{base.out_ship.mean():+8.3f} "
                          f"{keep.out_ship.mean():+8.3f} {lift:+8.3f} "
                          f"{cis[0]:>19s} {cis[1]:>19s} "
                          f"{(keep.out_ship>0).mean()*100:5.1f}/"
                          f"{(cut.out_ship>0).mean()*100:5.1f}% "
                          f" {'PASS' if passed else 'miss'}"
                          + ("" if cand else "  [control]"))
    npass = sum(1 for r in rows if r["pass"] and r["cand"])
    print(f"\n   CANDIDATE cells (2 TF x 3 sessions, both arms combined) "
          f"clearing the bar: {npass} of {sum(1 for r in rows if r['cand'])}")

    # ------------------------------------------------------------ §3 ----
    print("\n" + "=" * 78)
    print("2. NATURAL FREQUENCY — reported, never targeted (§3)")
    print(f"   Bar 3: a book below {BAR_FREQ} fights/day IN ITS OWN SESSION "
          f"is too thin to run standalone")
    print("=" * 78)
    print(f"   {'sess':7s} {'tf':>3s} {'gated/day':>10s} {'ungated/day':>12s} "
          f"{'kept share':>11s}  admissible?")
    for tf in CAND_TF + CTRL_TF:
        for s in SESS:
            d = B[(B.tf == tf) & (B.session == s) & (B.risk >= FLOOR)]
            k = d[admissible(d)]
            f_ = len(k) / nd
            print(f"   {s:7s} {tf:3d} {f_:10.2f} {len(d)/nd:12.2f} "
                  f"{len(k)/max(len(d),1)*100:10.1f}%  "
                  f"{'yes' if f_ >= BAR_FREQ else 'TOO THIN'}"
                  + ("" if tf in CAND_TF else "  [control]"))

    print("\n   threshold sensitivity (reported, NEVER selected on):")
    print(f"   {'sess':7s} {'tf':>3s} " + " ".join(
        f"{f'{t:.0f}R':>16s}" for t in THRS))
    for tf in CAND_TF:
        for s in SESS:
            d = B[(B.tf == tf) & (B.session == s) & (B.risk >= FLOOR)]
            cells = []
            for t_ in THRS:
                k = d[admissible(d, t_)]
                cells.append(f"{k.out_ship.mean():+.3f}({len(k)/nd:.2f}/d)"
                             if len(k) >= 15 else "thin")
            print(f"   {s:7s} {tf:3d} " + " ".join(f"{c:>16s}" for c in cells))

    print("\n   X sensitivity of the gated book (pooled sessions, per TF):")
    print(f"   {'X':>5s} " + " ".join(f"{f'TF={t}':>17s}" for t in CAND_TF))
    for xx in XS:
        Fx = F.copy()
        Fx["scid"] = assign(Fx, pd.read_parquet(PAIRS), xx)
        Bx = book(Fx)
        cells = []
        for tf in CAND_TF:
            d = Bx[(Bx.tf == tf) & (Bx.risk >= FLOOR)]
            k = d[admissible(d)]
            cells.append(f"{k.out_ship.mean():+.3f} ({len(k)/nd:.2f}/d)")
        print(f"   {xx:5.2f} " + " ".join(f"{c:>17s}" for c in cells))

    print("\n   costs (D6) on the gated book:")
    print(f"   {'sess':7s} {'tf':>3s} {'@0.5pt':>9s} {'@1.0pt':>9s} "
          f"{'@1.5pt':>9s}")
    for tf in CAND_TF:
        for s in SESS:
            d = B[(B.tf == tf) & (B.session == s) & (B.risk >= FLOOR)]
            k = d[admissible(d)]
            if len(k) < 15:
                continue
            print(f"   {s:7s} {tf:3d} {k.out_ship.mean():+9.3f} "
                  f"{(k.out_ship - 0.5/k.risk).mean():+9.3f} "
                  f"{(k.out_ship - 1.0/k.risk).mean():+9.3f}")

    # ------------------------------------------------------------ §4 ----
    print("\n" + "=" * 78)
    print("3. THE ACCOUNT LAYER — Bar 2, declared before these numbers "
          "existed")
    print(f"   (a) P(graduate) at MATCHED size   (b) max non-breaching size "
          f"vs the ${DD:,.0f} DD")
    print("   The gate passes only if it loses on NEITHER axis vs its own "
          "ungated baseline.")
    print("=" * 78)
    print(f"   {'sess':7s} {'tf':>3s} {'book':8s} {'/day':>6s} {'EV':>7s} "
          f"{'worst day R':>11s} {'p05 day R':>10s} {'max size':>9s} "
          f"{'GRAD@150':>9s} {'death':>7s} {'net':>9s}")
    verdict = []
    for tf in CAND_TF:
        for s in SESS:
            d = B[(B.tf == tf) & (B.session == s) & (B.risk >= FLOOR)]
            k = d[admissible(d)]
            if len(k) < 15:
                continue
            out = {}
            for nm, bk in (("ungated", d), ("gated", k)):
                dr = bk.groupby("sess_day").out_ship.sum().reindex(
                    all_days, fill_value=0.0).to_numpy()
                worst = float(dr.min())
                # largest whole-$50 size whose worst day stays inside the DD
                msize = 50.0 * np.floor((DD / abs(worst)) / 50.0) \
                    if worst < 0 else np.inf
                g_, dth, net = grad(dr, {"s_pre": 150., "s_post": 150.})
                out[nm] = (worst, float(np.percentile(dr, 5)), msize,
                           g_, dth, net)
                print(f"   {s:7s} {tf:3d} {nm:8s} {len(bk)/nd:6.2f} "
                      f"{bk.out_ship.mean():+7.3f} {worst:11.2f} "
                      f"{np.percentile(dr,5):10.2f} "
                      f"{('$'+format(msize,'.0f')) if np.isfinite(msize) else 'n/a':>9s} "
                      f"{g_*100:8.1f}% {dth*100:6.1f}% {net:9,.0f}")
            wg, _, mg, gg, _, _ = out["gated"]
            wu, _, mu, gu, _, _ = out["ungated"]
            ok = (gg >= gu) and (mg >= mu)
            verdict.append((s, tf, ok, gg - gu, mg - mu))
            print(f"   {'':7s} {'':>3s} -> GRAD {(gg-gu)*100:+.1f}pp, "
                  f"max size {mg-mu:+,.0f}  => "
                  f"{'PASSES Bar 2' if ok else 'FAILS Bar 2'}")

    print("\n" + "=" * 78)
    print("VERDICT SUMMARY")
    print("=" * 78)
    print(f"   Bar 1 (gate, per session x TF, both arms): "
          f"{npass} of {sum(1 for r in rows if r['cand'])} candidate cells")
    thin = [(r['sess'], r['tf']) for r in rows if r['cand']
            and r['fpd'] < BAR_FREQ]
    print(f"   Bar 3 (frequency): {len(thin)} candidate cells below "
          f"{BAR_FREQ}/day -> too thin to run standalone {thin if thin else ''}")
    ap = sum(1 for v in verdict if v[2])
    print(f"   Bar 2 (account layer): {ap} of {len(verdict)} cells lose on "
          f"neither axis")


if __name__ == "__main__":
    main()
