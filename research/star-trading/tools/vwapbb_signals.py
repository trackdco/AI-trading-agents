#!/usr/bin/env python3
"""SIGNAL COUNT for the VWAP/BB frozen spec. NOT a backtest.

Entry logic only: detect trigger events that pass the entry filters. No stops,
no targets, no P&L, no equity. Workbench only; the holdout is never addressed.

Frozen parameters (gate 4): VWAP typical price HLC/3, volume-profile bin 1.00pt,
HTF 15m fractal N=2, stop buffer 1 tick (unused here - no outcomes), volatility
stand-down DISABLED.
"""
from __future__ import annotations

import collections
import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from alpha_data import load

NY = ZoneInfo("America/New_York")
WORKBENCH_END = "2025-01-31"
RTH_OPEN, FIRST_SIG, RTH_CLOSE = 9 * 60 + 31, 9 * 60 + 36, 16 * 60
NY_VWAP_ANCHOR = 9 * 60 + 30
TFS = (1, 2, 3, 5)

CLUSTER_TOL = 10.0          # §3, CALIBRATE start ~10 NQ pts
BB_N = 20                   # §2
B_MIN = 0.6                 # §3, CALIBRATE start
QUARTILE = 0.75             # §3 close in extreme quartile
POC_BIN = 1.00              # gate 4 [FIAT]
FRACTAL_N = 2               # gate 4 [FIAT]


# ---------------------------------------------------------------- sessions
def build_sessions():
    """{session_end_date: [(minute_index 0..1379, o,h,l,c,v)]}, plus roll info."""
    d = load()
    bars, front = d["bars"], d["front"]
    sess: dict[str, dict] = collections.defaultdict(dict)
    sym_of: dict[str, set] = collections.defaultdict(set)
    for ud in sorted(bars):
        base = datetime.fromisoformat(ud).replace(tzinfo=timezone.utc)
        for m, (o, h, l, c, v) in bars[ud].items():
            t = (base + timedelta(minutes=m)).astimezone(NY)
            mm = t.hour * 60 + t.minute
            sd = (t.date() + timedelta(days=1)) if t.hour >= 18 else t.date()
            idx = (mm - 1080) if t.hour >= 18 else (mm + 360)
            sess[sd.isoformat()][idx] = (o, h, l, c, v)
            sym_of[sd.isoformat()].add(front[ud])
    return sess, sym_of


def minute_of_day(idx: int) -> int:
    """session index 0..1379 -> ET minute-of-day."""
    return (idx + 1080) % 1440


# ---------------------------------------------------------------- helpers
class RunningVWAP:
    """Volume-weighted VWAP + volume-weighted sigma, HLC/3 typical price."""
    __slots__ = ("pv", "pv2", "vol")

    def __init__(self):
        self.pv = self.pv2 = self.vol = 0.0

    def add(self, h, l, c, v):
        tp = (h + l + c) / 3.0
        self.pv += tp * v
        self.pv2 += tp * tp * v
        self.vol += v

    def value(self):
        if self.vol <= 0:
            return None, None
        m = self.pv / self.vol
        var = self.pv2 / self.vol - m * m
        return m, math.sqrt(var) if var > 0 else 0.0


def cluster_levels(levels, tol=CLUSTER_TOL):
    """levels = [(price, type)]. Return list of clusters with >=2 levels:
    (lo, hi, {types}, n_levels). Greedy chain grouping on sorted price."""
    if len(levels) < 2:
        return []
    ls = sorted(levels)
    out, cur = [], [ls[0]]
    for p, t in ls[1:]:
        if p - cur[-1][0] <= tol:
            cur.append((p, t))
        else:
            if len(cur) >= 2:
                out.append(cur)
            cur = [(p, t)]
    if len(cur) >= 2:
        out.append(cur)
    return [(c[0][0], c[-1][0], {t for _, t in c}, len(c)) for c in out]


def htf_flag(bars15):
    """15m fractal swings, N=2 each side. HH+HL up, LH+LL down, else range."""
    n = FRACTAL_N
    if len(bars15) < 2 * n + 1:
        return "range"
    hs, lo = [], []
    for i in range(n, len(bars15) - n):
        h = bars15[i][1]
        l = bars15[i][2]
        if all(h > bars15[j][1] for j in range(i - n, i)) and \
           all(h > bars15[j][1] for j in range(i + 1, i + n + 1)):
            hs.append(h)
        if all(l < bars15[j][2] for j in range(i - n, i)) and \
           all(l < bars15[j][2] for j in range(i + 1, i + n + 1)):
            lo.append(l)
    if len(hs) >= 2 and len(lo) >= 2:
        if hs[-1] > hs[-2] and lo[-1] > lo[-2]:
            return "uptrend"
        if hs[-1] < hs[-2] and lo[-1] < lo[-2]:
            return "downtrend"
    return "range"


def triggers(o, h, l, c, cl_lo, cl_hi, n_levels_in_body):
    """Return set of directions triggered on this bar for this cluster."""
    out = set()
    rng = h - l
    if rng <= 0:
        return out
    body_lo, body_hi = min(o, c), max(o, c)
    # --- rejection block (§3) ---
    if l <= cl_hi and c > cl_hi and l < body_lo:
        out.add(("long", "rejection"))
    if h >= cl_lo and c < cl_lo and h > body_hi:
        out.add(("short", "rejection"))
    # --- displacement (§3) ---
    if n_levels_in_body >= 2 and (body_hi - body_lo) / rng >= B_MIN:
        if (c - l) / rng >= QUARTILE and c > cl_hi:
            out.add(("long", "displacement"))
        if (h - c) / rng >= QUARTILE and c < cl_lo:
            out.add(("short", "displacement"))
    return out


# ---------------------------------------------------------------- main scan
def scan(rth_only_warmup: bool):
    sess, sym_of = build_sessions()
    days = sorted(d for d in sess if d <= WORKBENCH_END)

    # roll detection + skip-after-roll
    rolls, prev_sym = set(), None
    for d in days:
        s = sorted(sym_of[d])[0]
        if prev_sym and s != prev_sym:
            rolls.add(d)
        prev_sym = s
    skip_after = set()
    for i, d in enumerate(days):
        if d in rolls and i + 1 < len(days):
            skip_after.add(days[i + 1])

    per_session, skipped, bucket, by_year = {}, collections.Counter(), collections.Counter(), collections.Counter()
    total = 0

    for d in days:
        bars = sess[d]
        if d in rolls:
            skipped["roll session"] += 1
            continue
        if d in skip_after:
            skipped["session after roll"] += 1
            continue
        if len(sym_of[d]) > 1:
            skipped["mixed contract"] += 1
            continue
        rth_idx = [i for i in sorted(bars) if RTH_OPEN <= minute_of_day(i) < RTH_CLOSE]
        if len(rth_idx) < 300:
            skipped["holiday / short session"] += 1
            continue

        dv = RunningVWAP()
        nv = RunningVWAP()
        poc_bins: dict[int, float] = collections.defaultdict(float)
        bb: dict[int, collections.deque] = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
        tfacc: dict[int, list] = {tf: [] for tf in TFS}
        b15: list = []
        acc15: list = []
        fired_minutes: dict[int, int] = {}      # close_minute -> best TF fired

        for i in sorted(bars):
            o, h, l, c, v = bars[i]
            mm = minute_of_day(i)
            dv.add(h, l, c, v)                                   # daily VWAP: 18:00 anchor
            if mm >= NY_VWAP_ANCHOR or mm < 60 * 17:             # NY VWAP: 09:30 anchor
                if mm >= NY_VWAP_ANCHOR and mm < RTH_CLOSE + 1:
                    nv.add(h, l, c, v)
            # volume profile, volume spread uniformly across the bar's range
            nb = max(1, int((h - l) / POC_BIN) + 1)
            share = v / nb
            for k in range(nb):
                poc_bins[int((l + k * POC_BIN) / POC_BIN)] += share

            # accumulate 15m context bars
            acc15.append((o, h, l, c))
            if (mm + 1) % 15 == 0:
                b15.append((acc15[0][0], max(x[1] for x in acc15),
                            min(x[2] for x in acc15), acc15[-1][3]))
                acc15 = []

            for tf in TFS:
                tfacc[tf].append((o, h, l, c))
                if (mm + 1) % tf != 0:
                    continue
                g = tfacc[tf]
                tfacc[tf] = []
                to_, th_, tl_, tc_ = g[0][0], max(x[1] for x in g), min(x[2] for x in g), g[-1][3]
                close_min = mm + 1
                in_rth_bar = minute_of_day(i) >= RTH_OPEN
                # BB feed: variant B only feeds RTH bars
                if (not rth_only_warmup) or in_rth_bar:
                    bb[tf].append(tc_)
                if close_min < FIRST_SIG or close_min > RTH_CLOSE:
                    continue
                if len(bb[tf]) < BB_N:
                    continue

                basis = sum(bb[tf]) / BB_N
                dmid, dsig = dv.value()
                nmid, nsig = nv.value()
                if dmid is None:
                    continue
                poc = max(poc_bins.items(), key=lambda kv: kv[1])[0] * POC_BIN if poc_bins else None

                lv = [(basis, "bb")]
                for k in (0, 1, 2, 3):
                    lv.append((dmid + k * dsig, "vwap"))
                    if k:
                        lv.append((dmid - k * dsig, "vwap"))
                if nmid is not None and nv.vol > 0:
                    lv += [(nmid, "vwap"), (nmid + nsig, "vwap"), (nmid - nsig, "vwap")]
                if poc is not None:
                    lv.append((poc, "poc"))

                flag = htf_flag(b15)
                for cl_lo, cl_hi, types, _n in cluster_levels(lv):
                    body_lo, body_hi = min(to_, tc_), max(to_, tc_)
                    n_in_body = sum(1 for p, _ in lv if body_lo <= p <= body_hi)
                    for direction, _kind in triggers(to_, th_, tl_, tc_, cl_lo, cl_hi, n_in_body):
                        counter = (flag == "uptrend" and direction == "short") or \
                                  (flag == "downtrend" and direction == "long")
                        need = 3 if counter else 2
                        if len(types) < need:
                            continue
                        if fired_minutes.get(close_min, 0) < tf:
                            fired_minutes[close_min] = tf          # MTF: highest TF wins

        n = len(fired_minutes)
        per_session[d] = n
        total += n
        by_year[d[:4]] += n
        for cm in fired_minutes:
            bucket[f"{cm//60:02d}:{(cm%60)//30*30:02d}"] += 1

    return per_session, total, skipped, bucket, by_year


def report(tag, per_session, total, skipped, bucket, by_year, tripwire=0.486):
    ns = len(per_session)
    freq = total / ns if ns else 0.0
    print(f"\n{'='*74}\n{tag}\n{'='*74}")
    print(f"sessions scanned: {ns}   signals: {total}   "
          f"SIGNALS/SESSION = {freq:.3f}   tripwire {tripwire}")
    print(f"  -> {'CLEARS' if freq >= tripwire else 'BELOW TRIPWIRE'}")
    dist = collections.Counter(min(v, 3) for v in per_session.values())
    print("\ndistribution of signals per session:")
    for k in (0, 1, 2, 3):
        lab = "3+" if k == 3 else str(k)
        print(f"   {lab:>3} signals: {dist.get(k,0):4d} sessions ({dist.get(k,0)/ns*100:5.1f}%)")
    print(f"   max in one session: {max(per_session.values()) if per_session else 0}")
    print("\nby year:")
    for y in sorted(by_year):
        yn = sum(1 for d in per_session if d[:4] == y)
        print(f"   {y}: {by_year[y]:5d} signals over {yn:3d} sessions = {by_year[y]/yn:.3f}/session")
    print("\nby time-of-day (30-min buckets, ET):")
    for b in sorted(bucket):
        print(f"   {b}  {bucket[b]:5d}  {'#'*min(60,bucket[b]//max(1,total//300))}")
    print(f"\nsessions skipped: {dict(skipped)}  (total {sum(skipped.values())})")
    top = sorted(per_session.items(), key=lambda kv: -kv[1])[:8]
    print(f"anomaly candidates (highest counts, for eyeball): {top}")
    return freq


if __name__ == "__main__":
    print("SIGNAL COUNT — VWAP/BB frozen spec. Entry logic only, no outcomes.")
    print("Workbench 2023-01-03..2025-01-31. Holdout never addressed.")
    a = scan(rth_only_warmup=False)
    fa = report("VARIANT A — warm-up from prior bars (as currently specified)", *a)
    b = scan(rth_only_warmup=True)
    fb = report("VARIANT B — BB warmed from RTH bars only (later first signal)", *b)
    print(f"\n{'='*74}\nWARM-UP DELTA: A {fa:.3f} vs B {fb:.3f} signals/session "
          f"({(fb-fa)/fa*100:+.1f}%)\n{'='*74}")
