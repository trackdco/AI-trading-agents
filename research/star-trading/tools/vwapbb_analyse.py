#!/usr/bin/env python3
"""Analyses over candidates.parquet. Measurement only — no selector adopted,
no configuration ranked, no threshold tuned."""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import statistics as st
from pathlib import Path

import pyarrow.parquet as pq

P = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "candidates.parquet"
PRIMARY_WARM = "prior"


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def load():
    t = pq.read_table(P).to_pydict()
    n = len(t["session_date"])
    rows = [{k: t[k][i] for k in t} for i in range(n)]
    # ranks are per (session, reading, warmup)
    grp = collections.defaultdict(list)
    for r in rows:
        grp[(r["session_date"], r["trigger_reading"], r["warmup_treatment"])].append(r)
    for key, g in grp.items():
        g.sort(key=lambda r: r["signal_minute"])
        for i, r in enumerate(g, 1):
            r["time_rank_in_session"] = i
            r["n_in_session"] = len(g)
        for i, r in enumerate(sorted(g, key=lambda r: (-r["conviction_score"],
                                                        r["signal_minute"])), 1):
            r["conviction_rank_in_session"] = i
        # concurrency under first-come + one-at-a-time
        open_until = -1
        blocker = None
        for r in g:
            if r["signal_minute"] < open_until:
                r["earlier_candidate_open"] = True
                r["would_trade_under_first_come"] = False
                r["blocked_by"] = blocker
            else:
                r["earlier_candidate_open"] = False
                r["would_trade_under_first_come"] = True
                r["blocked_by"] = None
                dur = r["minutes_to_resolution"]
                open_until = r["signal_minute"] + (dur if dur is not None else 10**6)
                blocker = f'{r["session_date"]}@{r["signal_minute"]}'
    return rows


def hr(lbl):
    print(f"\n{'='*78}\n{lbl}\n{'='*78}")


def prof(rows, lab):
    if not rows:
        return f"{lab:>18} {'—':>7}"
    n = len(rows)
    return (f"{lab:>18} {n:>7} "
            f"{pct([r['mfe_R'] for r in rows], .5):>7.2f} "
            f"{pct([r['mae_R'] for r in rows], .5):>7.2f} "
            f"{sum(r['reached_1R'] for r in rows)/n*100:>7.1f} "
            f"{sum(r['reached_1_5R'] for r in rows)/n*100:>7.1f} "
            f"{sum(r['reached_2R'] for r in rows)/n*100:>7.1f} "
            f"{sum(r['reached_3R'] for r in rows)/n*100:>7.1f} "
            f"{sum(r['hit_spec_stop'] for r in rows)/n*100:>7.1f}")


HDR = f"{'slice':>18} {'n':>7} {'medMFE':>7} {'medMAE':>7} {'>=1R%':>7} {'>=1.5R%':>7} {'>=2R%':>7} {'>=3R%':>7} {'stop%':>7}"


def main():
    rows = load()
    prim = [r for r in rows if r["warmup_treatment"] == PRIMARY_WARM]
    print(f"records total {len(rows)}   primary warmup '{PRIMARY_WARM}': {len(prim)}")
    print(f"sessions {len({r['session_date'] for r in prim})}")

    hr("CORE DISTRIBUTIONS — by trigger reading")
    print(HDR)
    for m in "ABCD":
        print(prof([r for r in prim if r["trigger_reading"] == m], f"reading {m}"))

    R = "A"
    a = [r for r in prim if r["trigger_reading"] == R]
    hr(f"SLICES (reading {R}, warmup {PRIMARY_WARM}, n={len(a)})")
    for field, lab in (("time_rank_in_session", "time rank"),
                       ("conviction_rank_in_session", "conviction rank"),
                       ("conviction_score", "conviction score"),
                       ("cluster_size", "cluster size"),
                       ("year", "year"),
                       ("tod_bucket", "tod bucket")):
        print(f"\n-- by {lab} --"); print(HDR)
        keys = sorted({r[field] for r in a}, key=lambda x: (isinstance(x, str), x))
        for k in keys[:14]:
            print(prof([r for r in a if r[field] == k], f"{lab[:9]}={k}"))

    hr("OVERLAP — is the earliest candidate also the strongest?")
    for m in "ABCD":
        g = collections.defaultdict(list)
        for r in prim:
            if r["trigger_reading"] == m:
                g[r["session_date"]].append(r)
        ov = sum(1 for s in g.values()
                 if any(r["time_rank_in_session"] == 1 and r["conviction_rank_in_session"] == 1
                        for r in s))
        print(f"  reading {m}: time-rank-1 == conviction-rank-1 on "
              f"{ov}/{len(g)} sessions = {ov/len(g)*100:.1f}%")

    hr("A. CONCURRENCY AND BLOCKING (first-come + one-at-a-time)")
    for m in "ABCD":
        g = [r for r in prim if r["trigger_reading"] == m]
        tr = [r for r in g if r["would_trade_under_first_come"]]
        bl = [r for r in g if not r["would_trade_under_first_come"]]
        ns = len({r["session_date"] for r in g})
        print(f"\n  reading {m}: {len(g)} candidates over {ns} sessions "
              f"-> traded {len(tr)} ({len(tr)/ns:.2f}/sess), blocked {len(bl)} "
              f"({len(bl)/len(g)*100:.1f}%)")
        print(HDR)
        print(prof(tr, "TRADED"))
        print(prof(bl, "BLOCKED"))
    g = [r for r in prim if r["trigger_reading"] == R]
    blocked_per = collections.Counter()
    for r in g:
        if r["blocked_by"]:
            blocked_per[r["blocked_by"]] += 1
    d = collections.Counter(blocked_per.values())
    print(f"\n  reading {R}: how many candidates one open position blocks")
    for k in sorted(d)[:10]:
        print(f"     blocks {k:>3}: {d[k]:>5} positions")
    if blocked_per:
        print(f"     median {st.median(list(blocked_per.values())):.0f}  "
              f"max {max(blocked_per.values())}")

    hr("C. CONVICTION DISTRIBUTION")
    print("§9's score is 3-valued (confluence>=3, with-trend, target>=2R), not continuous,")
    print("so it is reported by level. Deciles are not defined on a 4-point scale.")
    for m in "ABCD":
        g = [r for r in prim if r["trigger_reading"] == m]
        c = collections.Counter(r["conviction_score"] for r in g)
        print(f"  reading {m}: " + "  ".join(f"score {k}: {c[k]/len(g)*100:5.1f}%" for k in sorted(c)))

    hr("D. TRUNCATED WINNERS — reached 1.5R but MAE deeper than the spec stop")
    print(f"{'reading':>10} {'reached 1.5R':>14} {'of those, MAE>stop':>20} {'%':>8}")
    for m in "ABCD":
        g = [r for r in prim if r["trigger_reading"] == m]
        w = [r for r in g if r["mfe_R"] >= 1.5]
        t = [r for r in w if r["mae_R"] >= 1.0]
        print(f"{m:>10} {len(w):>14} {len(t):>20} {len(t)/max(1,len(w))*100:>7.1f}%")

    hr("E. SURVIVAL CURVE — cumulative fraction resolved by elapsed minutes")
    g = [r for r in prim if r["trigger_reading"] == R]
    tot = len(g)
    print(f"  reading {R}, n={tot}")
    cum = 0
    for b in range(5, 65, 5):
        c = sum(1 for r in g if r["minutes_to_resolution"] is not None
                and r["minutes_to_resolution"] <= b)
        print(f"     <= {b:>3} min: {c/tot*100:>5.1f}%")
    for b in (90, 120, 180, 240, 390):
        c = sum(1 for r in g if r["minutes_to_resolution"] is not None
                and r["minutes_to_resolution"] <= b)
        print(f"     <= {b:>3} min: {c/tot*100:>5.1f}%")
    unres = sum(1 for r in g if r["minutes_to_resolution"] is None)
    print(f"     unresolved at session close: {unres/tot*100:.1f}%")

    hr("F. STABILITY AND HYGIENE")
    print("MAE distribution (reading A) — bounds how tight a stop can be:")
    mae = [r["mae_R"] for r in g]
    print("   " + "  ".join(f"p{int(q*100)}={pct(mae,q):.2f}R" for q in (.1,.25,.5,.75,.9,.95,.99)))
    print("\nunresolved at close, by reading:")
    for m in "ABCD":
        gg = [r for r in prim if r["trigger_reading"] == m]
        print(f"   {m}: {sum(1 for r in gg if r['minutes_to_resolution'] is None)/len(gg)*100:.1f}%")
    print("\nroll-contaminated candidates (lookback_spans_roll):")
    for m in "ABCD":
        gg = [r for r in prim if r["trigger_reading"] == m]
        rr = [r for r in gg if r["lookback_spans_roll"]]
        cl = [r for r in gg if not r["lookback_spans_roll"]]
        if rr:
            print(f"   {m}: {len(rr)} flagged ({len(rr)/len(gg)*100:.1f}%)   "
                  f"medMFE {pct([x['mfe_R'] for x in rr],.5):.2f} vs clean "
                  f"{pct([x['mfe_R'] for x in cl],.5):.2f}")
        else:
            print(f"   {m}: 0 flagged")
    print("\nwarm-up treatment comparison (reading A):")
    print(HDR)
    for w in ("prior", "rth"):
        print(prof([r for r in rows if r["trigger_reading"] == R
                    and r["warmup_treatment"] == w], w))


if __name__ == "__main__":
    main()
