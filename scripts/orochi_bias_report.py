#!/usr/bin/env python3
"""Apply the S41 pre-registered verdict rule to the bias census.

Day-clustered: each state's minutes are collapsed to one mean per session
day, then t-tested across days. Eras reported separately; edge is always
measured against the SAME-ERA unconditional baseline, never against zero.
"""
from __future__ import annotations

import json
from collections import defaultdict
from math import sqrt
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "analysis"
FRICTION = 2.0
ERAS = (("2020-22", "2020", "2022"), ("2023-24", "2023", "2024"),
        ("2025-26", "2025", "2026"))


def load():
    rows = defaultdict(lambda: defaultdict(list))   # state -> era -> [day means]
    base = defaultdict(lambda: defaultdict(list))
    for f in ("orochi_bias_nq20a.json", "orochi_bias_nq.json"):
        p = OUT / f
        if not p.exists():
            continue
        for day, d in json.loads(p.read_text()).items():
            era = next((e[0] for e in ERAS if e[1] <= day[:4] <= e[2]), None)
            if era is None:
                continue
            for k, (mean, n) in d.items():
                st, h = k.split("@@")
                rows[(st, int(h))][era].append(mean)
                if st == "ALL":
                    base[int(h)][era].append(mean)
    return rows, base


def tstat(v):
    v = np.asarray(v, float)
    if len(v) < 5 or v.std(ddof=1) == 0:
        return 0.0
    return float(v.mean() / (v.std(ddof=1) / sqrt(len(v))))


def main():
    rows, base = load()
    base_mean = {(h, e): float(np.mean(v)) for h, d in base.items()
                 for e, v in d.items()}
    print("UNCONDITIONAL BASELINE (mean forward move, pts) — NQ drifts, so "
          "this is the number every state is judged against\n")
    print(f"{'horizon':>8}" + "".join(f"{e[0]:>12}" for e in ERAS))
    for h in (5, 15, 30, 60):
        print(f"{h:>6}m " + "".join(
            f"{base_mean.get((h,e[0]),float('nan')):>+12.3f}" for e in ERAS))

    results = []
    for (st, h), per in sorted(rows.items()):
        if st == "ALL":
            continue
        if not all(e[0] in per and len(per[e[0]]) >= 30 for e in ERAS):
            continue
        # excess over the same-era unconditional baseline
        exc = {e[0]: np.array(per[e[0]]) - base_mean[(h, e[0])] for e in ERAS}
        pooled = np.concatenate([exc[e[0]] for e in ERAS])
        signs = {np.sign(exc[e[0]].mean()) for e in ERAS}
        same = len(signs) == 1 and 0 not in signs
        t = tstat(pooled)
        m = float(pooled.mean())
        if same and abs(t) >= 2 and abs(m) >= FRICTION:
            v = "SIGNAL"
        elif same and abs(t) >= 2:
            v = "WEAK"
        else:
            v = "null"
        results.append((v, st, h, m, t, [float(exc[e[0]].mean()) for e in ERAS],
                        len(pooled)))

    order = {"SIGNAL": 0, "WEAK": 1, "null": 2}
    results.sort(key=lambda r: (order[r[0]], -abs(r[3])))
    print(f"\n\nSTATE EDGE vs SAME-ERA BASELINE (pts, day-clustered)\n")
    print(f"{'verdict':>8}  {'state':<26}{'h':>4}{'excess':>9}{'t_day':>7}"
          f"{'20-22':>9}{'23-24':>9}{'25-26':>9}{'days':>7}")
    shown = 0
    for v, st, h, m, t, per, n in results:
        if v == "null" and shown > 26:
            continue
        shown += 1
        print(f"{v:>8}  {st:<26}{h:>4}{m:>+9.3f}{t:>+7.2f}"
              + "".join(f"{x:>+9.3f}" for x in per) + f"{n:>7}")
    ns = sum(1 for r in results if r[0] == "SIGNAL")
    nw = sum(1 for r in results if r[0] == "WEAK")
    print(f"\n{ns} SIGNAL / {nw} WEAK / {len(results)-ns-nw} null "
          f"out of {len(results)} state-horizon cells tested")
    print(f"(SIGNAL needs same sign in all 3 eras, |t_day|>=2, and "
          f"|excess| >= {FRICTION}pt friction ceiling)")


if __name__ == "__main__":
    main()
