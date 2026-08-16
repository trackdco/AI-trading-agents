#!/usr/bin/env python3
"""ENTRY-PRICE GATE for the LEVEL-FAMILY CENSUS (E1 precondition).

Same three tests as scripts/htf_ma_entry_gate.py, run PER LOCUS. This
matters more here than for the incumbent: VWAP accumulates the current
bar's price x volume and the developing profile accumulates the current
bar's volume, so a careless as-of alignment would let a fill price be set
by the very bar it fills in — the exact defect class that killed the canon.

  T1 FLATTEN   flatten every 1m bar strictly after the decision bar to the
               previous close; the row's entry must equal that flat value
               and must MOVE relative to the real run on some probes (if it
               never moves, the price is read off the decision bar)
  T2 NEXT-OPEN reject rows: entry == open(first 1m bar after the decision)
  T3 FILL-BAR  break rows: perturbing the FILL bar's own close must not
               move the fill price

    python -m scripts.htf_level_entry_gate [--stride N] [--locus NAME]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_level_census import (FIT_END, FIT_START,        # noqa: E402
                                         LOCI, day_rows)
from src.htf_ma.levels import NY                                    # noqa: E402

EPS = 1e-9


def main() -> None:
    stride = 40
    loci = LOCI
    if "--stride" in sys.argv:
        stride = int(sys.argv[sys.argv.index("--stride") + 1])
    if "--locus" in sys.argv:
        loci = [sys.argv[sys.argv.index("--locus") + 1]]
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    days = [d for d in sess_days if FIT_START <= d <= FIT_END][::stride]

    stats = {l: {"t1n": 0, "t1bad": 0, "t1moved": 0, "t2n": 0, "t2f": 0,
                 "t3n": 0, "t3f": 0} for l in loci}
    examples: list[str] = []

    for day in days:
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        win = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                   & (bars.index < t1)]
        if win.empty:
            continue
        seg = win[(win.index >= t0) & (win.index < t1)]
        if seg.empty:
            continue
        idx, op = seg.index, seg.open.to_numpy()
        hi, lo = seg.high.to_numpy(), seg.low.to_numpy()
        for locus in loci:
            rows = day_rows(win, day, [locus])
            if not rows:
                continue
            rej = [r for r in rows if r["arm"] == "reject"]
            brk = [r for r in rows if r["arm"] == "break" and r["retested"]]
            pick = ([rej[i] for i in sorted({0, len(rej) // 2, len(rej) - 1})]
                    if rej else []) + \
                   ([brk[i] for i in sorted({0, len(brk) // 2, len(brk) - 1})]
                    if brk else [])
            S = stats[locus]
            for r in pick:
                t = pd.Timestamp(r["t"])
                j0 = int(np.searchsorted(idx.values, t.to_datetime64()))
                prev_close = float(win[win.index < t].close.iloc[-1])

                if r["arm"] == "reject":
                    S["t2n"] += 1
                    if j0 >= len(idx) or abs(r["entry"] - op[j0]) > EPS:
                        S["t2f"] += 1
                        if len(examples) < 10:
                            nxt = op[j0] if j0 < len(idx) else np.nan
                            examples.append(
                                f"  T2 {locus} {day} {t}: entry={r['entry']:.2f}"
                                f" next_open={nxt:.2f}")

                S["t1n"] += 1
                wf = win.copy()
                m = wf.index >= t
                wf.loc[m, ["open", "high", "low", "close"]] = prev_close
                wf.loc[m, "volume"] = 1
                rf = day_rows(wf, day, [locus])
                mt = [x for x in rf if x["t"] == r["t"] and x["arm"] == r["arm"]
                      and x["side"] == r["side"]
                      and x["n_attempts"] == r["n_attempts"]]
                if mt and np.isfinite(mt[0]["entry"]):
                    ef = mt[0]["entry"]
                    if abs(ef - prev_close) > EPS:
                        S["t1bad"] += 1
                        if len(examples) < 10:
                            examples.append(
                                f"  T1 {locus} {day} {t} {r['arm']}: flat-run "
                                f"entry {ef:.2f} != flat value {prev_close:.2f}")
                    if abs(ef - r["entry"]) > EPS:
                        S["t1moved"] += 1

                if r["arm"] == "break" and np.isfinite(r["entry"]):
                    # perturb the ACTUAL fill bar, recorded by the builder.
                    # (Scanning for the first bar whose range contains the
                    # entry price is wrong for a drifting level: it can land
                    # on a PRE-fill bar, whose close legitimately moves the
                    # level and so fails T3 spuriously.)
                    if pd.isna(r.get("t_fill")):
                        continue
                    jf = int(np.searchsorted(
                        idx.values, pd.Timestamp(r["t_fill"]).to_datetime64()))
                    if jf >= len(idx) or idx[jf] != pd.Timestamp(r["t_fill"]):
                        continue
                    wf2 = win.copy()
                    tsf = idx[jf]
                    c_old = float(wf2.loc[tsf, "close"])
                    c_new = float(wf2.loc[tsf, "open"])
                    if abs(c_new - c_old) < EPS:
                        c_new = (float(wf2.loc[tsf, "high"])
                                 + float(wf2.loc[tsf, "low"])) / 2.0
                    if abs(c_new - c_old) < EPS:
                        continue
                    S["t3n"] += 1
                    wf2.loc[tsf, "close"] = c_new
                    rp = day_rows(wf2, day, [locus])
                    mt2 = [x for x in rp if x["t"] == r["t"]
                           and x["arm"] == "break" and x["side"] == r["side"]
                           and x["n_attempts"] == r["n_attempts"]]
                    if mt2 and np.isfinite(mt2[0]["entry"]) \
                            and abs(mt2[0]["entry"] - r["entry"]) > EPS:
                        S["t3f"] += 1
                        if len(examples) < 10:
                            examples.append(
                                f"  T3 {locus} {day} {t}: entry moved "
                                f"{r['entry']:.4f} -> {mt2[0]['entry']:.4f} "
                                f"when fill-bar close {c_old:.2f}->{c_new:.2f}")

    print(f"entry gate over {len(days)} fit days, per locus:")
    ok_all = True
    for locus in loci:
        S = stats[locus]
        ok = (S["t1bad"] == 0 and S["t1moved"] > 0 and S["t2f"] == 0
              and S["t3f"] == 0)
        ok_all &= ok
        print(f"  {locus:9s} T1 {S['t1n']:3d} probes (bad {S['t1bad']}, "
              f"moved {S['t1moved']:3d}) | T2 {S['t2f']}/{S['t2n']} fail | "
              f"T3 {S['t3f']}/{S['t3n']} fail  -> "
              f"{'PASS' if ok else 'FAIL'}")
    for e in examples:
        print(e)
    print(f"LEVEL ENTRY GATE: {'PASS' if ok_all else 'FAIL'}")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
