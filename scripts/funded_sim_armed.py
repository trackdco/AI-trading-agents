"""FUNDED-ACCOUNT MONTE CARLO for the ARMED book vs the frozen spec.

Python port of docs/artifacts/funded_sim.html (S33), mechanics matched
line for line so the two are comparable:
  day $ = sum over trades of  micros * $2 * (gross_r * stop_pts - 0.5)
  haircut: every day draw is reduced by haircut x mean daily $
  eval:   bal from 0; peak tracked; floor = peak - dd, clamped to 0 once
          ahead (the start-balance lock); breach on bal <= floor; pass on
          bal >= target after minDays
  funded: fresh balance, same rule, run to ftarget after minFunded days
  5-day block bootstrap over the day series
Defaults from the artifact: dd 2000, target 3000, ftarget 4000,
minDays 1, minFunded 10, maxDays 120, haircut 30%, 1 micro flat.

WHY RERUN: arming changes trade frequency 78.1 -> 63.4/day and reshapes
the stop distribution, so the S33 artifact describes the pre-arming book.
"""
import sys
import numpy as np
sys.path.insert(0, ".")
import scripts.conviction_sizing as CS

DD, TGT, FTGT = 2000., 3000., 4000.
MINDAYS, MINFUNDED, MAXDAYS = 1, 10, 120
SIMS, HAIRCUT = 20000, 0.30


def day_dollars(kept, micros=1, scap=1e9):
    days = sorted(kept)
    out, stops = np.zeros(len(days)), []
    for i, d in enumerate(days):
        s = 0.0
        for t in kept[d]:
            st = t["risk"]
            if st > scap:
                continue
            s += micros * 2.0 * (t["r"] * st - 0.5)
            stops.append(st)
        out[i] = s
    return out, np.array(stops)


def run(dayv, haircut, seed=1, sims=SIMS):
    rng = np.random.default_rng(seed)
    shift = haircut * dayv.mean()
    ND = len(dayv)
    passd, breachd, timeouts = [], [], 0
    fpay, fbreach, fcap, total = [], 0, 0, []
    for _ in range(sims):
        starts = rng.integers(0, ND, size=2 * MAXDAYS // 5 + 4)
        seq = np.concatenate([np.take(dayv, np.arange(s, s + 5), mode="wrap")
                              for s in starts]) - shift
        p = 0
        def phase(target, mind):
            nonlocal p
            bal = peak = 0.0
            d = 0
            while d < MAXDAYS:
                bal += seq[p]; p += 1; d += 1
                peak = max(peak, bal)
                fl = peak - DD
                if fl > 0: fl = 0.0
                if bal <= fl: return 2, d
                if bal >= target and d >= mind: return 1, d
            return 0, d
        r1, d1 = phase(TGT, MINDAYS)
        if r1 == 2: breachd.append(d1); continue
        if r1 == 0: timeouts += 1; continue
        passd.append(d1)
        r2, d2 = phase(FTGT, MINFUNDED)
        if r2 == 1: fpay.append(d2); total.append(d1 + d2)
        elif r2 == 2: fbreach += 1
        else: fcap += 1
    return dict(passd=passd, breachd=breachd, timeouts=timeouts,
                fpay=fpay, fbreach=fbreach, fcap=fcap, total=total, sims=sims)


def report(tag, kept, haircut=HAIRCUT):
    dayv, stops = day_dollars(kept)
    ntr = sum(len(v) for v in kept.values())
    r = run(dayv, haircut)
    n = r["sims"]
    med = lambda a: np.median(a) if len(a) else float("nan")
    print(f"\n{tag}")
    print(f"  {ntr:,} trades / {len(dayv)} days = {ntr/len(dayv):.1f} per day   "
          f"stops: median {np.median(stops):.1f}pt  p95 {np.percentile(stops,95):.0f}pt  max {stops.max():.0f}pt")
    print(f"  mean day ${dayv.mean():+.2f} (1 micro flat)   after {haircut:.0%} haircut "
          f"${dayv.mean()*(1-haircut):+.2f}")
    print(f"  EVAL   pass {len(r['passd'])/n:>6.1%}   breach {len(r['breachd'])/n:>6.1%}   "
          f"timeout {r['timeouts']/n:>6.1%}   median days to pass {med(r['passd']):>5.0f}")
    print(f"  FUNDED reach payout {len(r['fpay'])/n:>6.1%} of all starts   "
          f"breach {r['fbreach']/n:>6.1%}   median funded days {med(r['fpay']):>5.0f}")
    print(f"  START -> FIRST PAYOUT: {len(r['total'])/n:>6.1%}   median {med(r['total']):>5.0f} days")
    return dict(pass_=len(r["passd"])/n, breach=len(r["breachd"])/n,
                dpass=med(r["passd"]), payout=len(r["total"])/n,
                dtotal=med(r["total"]), mean=dayv.mean())


base = CS.empire(""); arm = CS.empire("_arm1")
print("=" * 78)
a = report("FROZEN SPEC (the S33 artifact's book)", base)
b = report("ARMED 1R (the adopted layer)", arm)
print("\n" + "=" * 78)
print(f"  {'metric':<28}{'frozen':>12}{'armed':>12}{'delta':>12}")
for lab, k, f in (("eval pass rate", "pass_", "{:.1%}"),
                  ("eval breach rate", "breach", "{:.1%}"),
                  ("median days to pass", "dpass", "{:.0f}"),
                  ("start->payout odds", "payout", "{:.1%}"),
                  ("median days to payout", "dtotal", "{:.0f}"),
                  ("mean $/day, 1 micro", "mean", "${:+.2f}")):
    d = b[k] - a[k]
    ds = ("{:+.1%}".format(d) if "%" in f else "{:+.0f}".format(d) if k.startswith("d")
          else "${:+.2f}".format(d))
    print(f"  {lab:<28}{f.format(a[k]):>12}{f.format(b[k]):>12}{ds:>12}")

print("\nHAIRCUT SENSITIVITY (start -> first payout odds)")
print(f"  {'haircut':<10}{'frozen':>10}{'armed':>10}")
for h in (0.0, 0.15, 0.30, 0.50):
    ra = run(day_dollars(base)[0], h, seed=7, sims=8000)
    rb = run(day_dollars(arm)[0], h, seed=7, sims=8000)
    print(f"  {h:<10.0%}{len(ra['total'])/8000:>10.1%}{len(rb['total'])/8000:>10.1%}")
