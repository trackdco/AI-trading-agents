#!/usr/bin/env python3
"""ENTRY-PRICE GATE for the LTF CONJUNCTION CENSUS (declaration precondition).

"The entry-price gate must PASS at every TF before any row is read."

Both arms enter at the next 1m open here (the trader's market order), so
the level census's T3 fill-bar probe has no analogue — the fill bar IS the
next-open bar and T2 already pins it. In its place this gate probes the
NEW and previously untested object: condition (B).

  T1 FLATTEN   flatten every 1m bar from the decision candle's close
               onward to the previous close; the row's entry must equal
               that flat value, and must MOVE relative to the real run on
               some probes (if it never moves, entry is read off the
               decision candle itself)
  T2 NEXT-OPEN both arms: entry == open(first 1m bar at/after the candle's
               close stamp)
  T3B COND-(B) perturbing bars STRICTLY AFTER the decision candle must not
               flip condB. (B) reads that TF's own BB(20) middle band with
               the developing bucket included, which is exactly the place
               a careless as-of would pull in the next candle.

    python -m scripts.htf_ltf_entry_gate [--stride N] [--tf N]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_level_census import LOCI                        # noqa: E402
from scripts.htf_ma_ltf_census import (FIT_END, FIT_START, TFS,     # noqa: E402
                                       day_triggers)
from src.htf_ma.levels import NY                                    # noqa: E402

EPS = 1e-9


def main() -> None:
    stride = 40
    tfs = TFS
    if "--stride" in sys.argv:
        stride = int(sys.argv[sys.argv.index("--stride") + 1])
    if "--tf" in sys.argv:
        tfs = [int(sys.argv[sys.argv.index("--tf") + 1])]
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    days = [d for d in sess_days if FIT_START <= d <= FIT_END][::stride]

    stats = {tf: {"t1n": 0, "t1bad": 0, "t1moved": 0, "t2n": 0, "t2f": 0,
                  "t3n": 0, "t3f": 0} for tf in tfs}
    examples: list[str] = []

    def match(rows, r):
        return [x for x in rows if x["t"] == r["t"] and x["arm"] == r["arm"]
                and x["side"] == r["side"] and x["locus"] == r["locus"]
                and x["n_attempts"] == r["n_attempts"]]

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
        for tf in tfs:
            S = stats[tf]
            for locus in LOCI:
                rows = day_triggers(win, day, tfs=[tf], loci=[locus],
                                    entry_only=True)
                if not rows:
                    continue
                # three probes per (tf, locus): first / middle / last
                pick = [rows[i] for i in
                        sorted({0, len(rows) // 2, len(rows) - 1})]
                for r in pick:
                    t = pd.Timestamp(r["t"])
                    j0 = int(np.searchsorted(idx.values, t.to_datetime64()))
                    prior = win[win.index < t]
                    if prior.empty:
                        continue
                    prev_close = float(prior.close.iloc[-1])

                    # ---- T2: next 1m open, both arms --------------------
                    S["t2n"] += 1
                    if j0 >= len(idx) or abs(r["entry"] - op[j0]) > EPS:
                        S["t2f"] += 1
                        if len(examples) < 12:
                            nxt = op[j0] if j0 < len(idx) else np.nan
                            examples.append(
                                f"  T2 tf={tf} {locus} {day} {t} {r['arm']}: "
                                f"entry={r['entry']:.2f} next_open={nxt:.2f}")

                    # ---- T1: flatten everything from t onward -----------
                    S["t1n"] += 1
                    wf = win.copy()
                    m = wf.index >= t
                    wf.loc[m, ["open", "high", "low", "close"]] = prev_close
                    wf.loc[m, "volume"] = 1
                    mt = match(day_triggers(wf, day, tfs=[tf], loci=[locus],
                                            entry_only=True), r)
                    if mt and np.isfinite(mt[0]["entry"]):
                        ef = mt[0]["entry"]
                        if abs(ef - prev_close) > EPS:
                            S["t1bad"] += 1
                            if len(examples) < 12:
                                examples.append(
                                    f"  T1 tf={tf} {locus} {day} {t} "
                                    f"{r['arm']}: flat-run entry {ef:.2f} != "
                                    f"flat value {prev_close:.2f}")
                        if abs(ef - r["entry"]) > EPS:
                            S["t1moved"] += 1

                    # ---- T3B: condition (B) must not see the future -----
                    # perturb bars STRICTLY AFTER the decision candle by a
                    # large shift; condB is a property of the candle and
                    # must be invariant.
                    wf2 = win.copy()
                    m2 = wf2.index >= t
                    if m2.sum() == 0:
                        continue
                    S["t3n"] += 1
                    wf2.loc[m2, ["open", "high", "low", "close"]] += 50.0
                    mt2 = match(day_triggers(wf2, day, tfs=[tf], loci=[locus],
                                             entry_only=True), r)
                    if mt2 and bool(mt2[0]["condB"]) != bool(r["condB"]):
                        S["t3f"] += 1
                        if len(examples) < 12:
                            examples.append(
                                f"  T3B tf={tf} {locus} {day} {t}: condB "
                                f"flipped {r['condB']} -> {mt2[0]['condB']} "
                                f"when POST-decision bars shifted +50pt")

    print(f"LTF entry gate over {len(days)} fit days (stride {stride}), "
          f"per trigger timeframe:")
    ok_all = True
    for tf in tfs:
        S = stats[tf]
        ok = (S["t1bad"] == 0 and S["t1moved"] > 0 and S["t2f"] == 0
              and S["t3f"] == 0 and S["t3n"] > 0)
        ok_all &= ok
        print(f"  TF={tf:2d}m  T1 {S['t1n']:4d} probes (bad {S['t1bad']}, "
              f"moved {S['t1moved']:4d}) | T2 {S['t2f']}/{S['t2n']} fail | "
              f"T3B {S['t3f']}/{S['t3n']} fail  -> "
              f"{'PASS' if ok else 'FAIL'}")
    for e in examples:
        print(e)
    print(f"LTF ENTRY GATE: {'PASS' if ok_all else 'FAIL'}")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
