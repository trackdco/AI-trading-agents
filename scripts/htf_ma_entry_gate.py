#!/usr/bin/env python3
"""ENTRY-PRICE GATE — the fill-side lookahead test (Phase 0 item 1).

The perturbation gate proves FEATURES are as-of the decision bar; it is
structurally blind to the ENTRY PRICE itself (a price read off the decision
bar is unchanged when post-decision bars are perturbed — that invariance is
exactly the defect). This gate tests the price:

T1 FLATTEN   Every 1m bar strictly after the decision bar is flattened to the
             previous close. The row's entry_price must (a) equal that flat
             value in the flattened run, and (b) MOVE relative to the real run
             on a nonzero fraction of probes. If it never moves, the price is
             being read off the decision bar.
T2 ROW-LEVEL reject arm: entry_price == open(first 1m bar strictly after the
             decision bar) — the declared convention (prereg M-TABLE block:
             "entry at the NEXT open").
T3 FILL-BAR  break arm: perturbing the retest bar's CLOSE (within its range)
             must not move the fill price. A limit level must be computable
             from bars strictly before the bar that fills it; the as-of MA at
             the fill bar includes that bar's own close.

    python -m scripts.htf_ma_entry_gate [--stride N]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_mtable import FIT_END, FIT_START, day_rows      # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                        # noqa: E402

EPS = 1e-9


def day_window(bars: pd.DataFrame, sess_day: str):
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    return bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                & (bars.index < t1)], t0, t1


def pick_probes(rows: list[dict]) -> list[dict]:
    rej = [r for r in rows if r["arm"] == "reject"]
    brk = [r for r in rows if r["arm"] == "break" and r.get("retested")]
    take = lambda rs: [rs[i] for i in
                       sorted({0, len(rs) // 2, len(rs) - 1})] if rs else []
    return take(rej) + take(brk)


def main() -> None:
    stride = 30
    if "--stride" in sys.argv:
        stride = int(sys.argv[sys.argv.index("--stride") + 1])
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    fp_path = ROOT / "output/fp_minutes_full.parquet"
    fp = pd.read_parquet(fp_path) if fp_path.exists() else pd.DataFrame()
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    days = [d for d in sess_days if FIT_START <= d <= FIT_END][::stride]

    n_t1_flat_wrong = n_t1_probes = n_t1_moved = 0
    n_t2_fail = n_t2_probes = 0
    n_t3_fail = n_t3_probes = 0
    examples: list[str] = []

    for day in days:
        win, t0, t1 = day_window(bars, day)
        if win.empty:
            continue
        fpd = fp[(fp.index >= t0 - pd.Timedelta(hours=30))
                 & (fp.index < t1)] if len(fp) else fp
        rows = day_rows(win, fpd, day)
        if not rows:
            continue
        seg = win[(win.index >= t0) & (win.index < t1)]
        idx, op = seg.index, seg.open.to_numpy()
        hi, lo = seg.high.to_numpy(), seg.low.to_numpy()

        for r in pick_probes(rows):
            t = pd.Timestamp(r["t"])
            j0 = int(np.searchsorted(idx.values, t.to_datetime64()))
            prev_close = float(win[win.index < t].close.iloc[-1])

            # ---- T2: reject rows must enter at the next bar's open --------
            if r["arm"] == "reject":
                n_t2_probes += 1
                if j0 >= len(idx) or abs(r["entry"] - op[j0]) > EPS:
                    n_t2_fail += 1
                    if len(examples) < 8:
                        nxt = op[j0] if j0 < len(idx) else np.nan
                        examples.append(
                            f"  T2 {day} {t} reject: entry={r['entry']:.2f} "
                            f"next_open={nxt:.2f} decision_close={prev_close:.2f}")

            # ---- T1: flatten strictly-after bars to the previous close ----
            n_t1_probes += 1
            wf = win.copy()
            m = wf.index >= t
            wf.loc[m, ["open", "high", "low", "close"]] = prev_close
            wf.loc[m, "volume"] = 1
            rows_f = day_rows(wf, fpd, day)
            match = [x for x in rows_f
                     if x["t"] == r["t"] and x["arm"] == r["arm"]
                     and x["side"] == r["side"]
                     and x["n_attempts"] == r["n_attempts"]]
            if match:
                ef = match[0]["entry"]
                if np.isfinite(ef):
                    if abs(ef - prev_close) > EPS:
                        n_t1_flat_wrong += 1
                        if len(examples) < 8:
                            examples.append(
                                f"  T1 {day} {t} {r['arm']}: flat-run entry "
                                f"{ef:.2f} != flat value {prev_close:.2f}")
                    if abs(ef - r["entry"]) > EPS:
                        n_t1_moved += 1

            # ---- T3: break fill price must not depend on fill bar's close -
            if r["arm"] == "break" and np.isfinite(r["entry"]):
                jf = next((j for j in range(j0, len(idx))
                           if lo[j] - EPS <= r["entry"] <= hi[j] + EPS), None)
                if jf is None:
                    continue
                n_t3_probes += 1
                wf2 = win.copy()
                tsf = idx[jf]
                c_old = float(wf2.loc[tsf, "close"])
                c_new = float(wf2.loc[tsf, "open"])
                if abs(c_new - c_old) < EPS:
                    c_new = (float(wf2.loc[tsf, "high"])
                             + float(wf2.loc[tsf, "low"])) / 2.0
                if abs(c_new - c_old) < EPS:
                    n_t3_probes -= 1
                    continue
                wf2.loc[tsf, "close"] = c_new
                rows_p = day_rows(wf2, fpd, day)
                match = [x for x in rows_p
                         if x["t"] == r["t"] and x["arm"] == "break"
                         and x["side"] == r["side"]
                         and x["n_attempts"] == r["n_attempts"]]
                if match and np.isfinite(match[0]["entry"]) \
                        and abs(match[0]["entry"] - r["entry"]) > EPS:
                    n_t3_fail += 1
                    if len(examples) < 8:
                        examples.append(
                            f"  T3 {day} {t} break: entry moved "
                            f"{r['entry']:.4f} -> {match[0]['entry']:.4f} when "
                            f"fill bar close perturbed {c_old:.2f}->{c_new:.2f}")

    print(f"entry gate over {len(days)} fit days:")
    print(f"  T1 flatten: {n_t1_probes} probes | flat-run entry wrong: "
          f"{n_t1_flat_wrong} | entry moved vs real: {n_t1_moved} "
          f"({'FAIL — price read off decision bar' if n_t1_moved == 0 else 'ok'})")
    print(f"  T2 next-open (reject): {n_t2_fail}/{n_t2_probes} fail")
    print(f"  T3 fill-bar close (break): {n_t3_fail}/{n_t3_probes} fail")
    for e in examples:
        print(e)
    ok = (n_t1_flat_wrong == 0 and n_t1_moved > 0 and n_t2_fail == 0
          and n_t3_fail == 0)
    print(f"ENTRY GATE: {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
