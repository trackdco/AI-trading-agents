#!/usr/bin/env python3
"""SUBSTRATE READOUT — the target-band curve his acceptance bar is judged on.

    python -m scripts.substrate_readout

For every candidate in the v2 full-day corpus: re-walk the bars with an
UNCAPPED favourable tracker (the corpus's mech model stops counting at 2R)
and record the maximum favourable R reached BEFORE the mechanical stop
prints, over a 240-minute horizon. From that, the curve his ruling needs:

    P(reach X R before stop)  for X in 1.0 / 1.5 / 2.0 / 2.5 / 3.0

split overall, by session, by year, and by chop state. His bar: the
selection layer must lift the chosen band to >=50% — this readout is the
unselected floor it lifts FROM.

Writes output/analysis/substrate_readout.json and prints the tables.
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402

BANDS = (1.0, 1.5, 2.0, 2.5, 3.0)
HORIZON_MIN = 240


def main() -> int:
    src = ROOT / "output/analysis/candidate_corpus_fullday_v2.jsonl.gz"
    rows = [json.loads(l) for l in gzip.open(src, "rt")]
    rows = [r for r in rows if r.get("mech_entry") is not None]
    bars = OB.get_bars()

    out_rows = []
    byday = defaultdict(list)
    for r in rows:
        byday[r["sess_day"]].append(r)
    for i, (day, lst) in enumerate(sorted(byday.items())):
        for r in lst:
            try:
                _, t = OB.session_bounds(day, r["minute"])
            except Exception:
                continue
            seg = bars[(bars.index >= t) & (bars.index < t + pd.Timedelta(minutes=HORIZON_MIN))]
            entry, stop, rpts = r["mech_entry"], r["mech_stop"], r["mech_rpts"]
            side = r["side"]
            best = 0.0
            stopped = False
            for _, b in seg.iterrows():
                if side == "short":
                    if b.high >= stop:
                        stopped = True
                        break
                    best = max(best, (entry - float(b.low)) / rpts)
                else:
                    if b.low <= stop:
                        stopped = True
                        break
                    best = max(best, (float(b.high) - entry) / rpts)
            out_rows.append({"sess_day": day, "window": r["window"],
                             "year": day[:4], "chop": r.get("chop_state"),
                             "best_r": round(best, 3), "stopped": stopped})
        if i % 100 == 0:
            print(f"[{i}/{len(byday)}] {day}", flush=True)

    def curve(rs):
        n = len(rs)
        return {f"{x}R": (sum(1 for r in rs if r["best_r"] >= x) / n if n else 0.0)
                for x in BANDS} | {"n": n}

    report = {"overall": curve(out_rows)}
    for key in ("window", "year", "chop"):
        report[key] = {}
        vals = sorted({r[key] for r in out_rows if r[key]})
        for v in vals:
            report[key][v] = curve([r for r in out_rows if r[key] == v])

    dst = ROOT / "output/analysis/substrate_readout.json"
    dst.write_text(json.dumps(report, indent=1))

    def show(label, c):
        print(f"  {label:12}" + "".join(f"{c[f'{x}R']:>9.1%}" for x in BANDS)
              + f"  (n={c['n']})")
    print("\n=== reach-XR-before-stop, unselected substrate ===")
    print(f"  {'':12}" + "".join(f"{x:>8}R" for x in BANDS))
    show("OVERALL", report["overall"])
    for v, c in report["window"].items():
        show(v, c)
    for v, c in report["year"].items():
        show(v, c)
    for v, c in report["chop"].items():
        show(v, c)
    print(f"\nDONE -> {dst}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
