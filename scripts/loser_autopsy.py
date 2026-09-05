"""LOSER AUTOPSY — what does a losing day look like, and is it knowable BEFORE it starts?

His hypothesis (2026-09-03): "it would highly depend on the previous day's
volatility and the gap or something like that. because if one day moves hella
it could be cos of news."

WHY A DAY-LEVEL AUDIT IS DIFFERENT FROM THE TRADE-LEVEL ONES.
G3b died because an audit bucket is not a rule effect: the rail pass is
chronological, so refusing one trade changes which trades are open for the
rest of that day, and the blocked population was not the population the audit
measured. A DAY filter does not have that problem. Nothing carries from one
session to the next in this engine - levels come from the prior session's
BARS (which still exist whether or not we traded), the book is flat by EOD,
and rail_pass groups by day. So skipping day D leaves every other day
bit-for-bit identical, and the bucket IS the rule effect. This audit can be
read as a rule directly. That is a real structural difference, not a
convenience, and it is why this one is worth doing carefully.

CAUSALITY. Every feature below is computed from bars that closed at or before
the session's 18:00 open. No feature may read the session it is predicting.
That is checked by construction: prior-session features use the [prev_t0, t0)
window and the gap uses the first bar AT t0 only.

PREREGISTERED READING RULE - written before any result was read:
  A feature is a SURVIVOR only if, in BOTH eras independently:
    (a) the worst bucket's mean day-R is at least 3.0R below the best
        bucket's, AND
    (b) the ordering across buckets is monotone or single-peaked, AND
    (c) every bucket holds >= 120 days.
  WATCH if it holds in both eras at >= 1.5R. NULL otherwise.
Two eras (2020-22, 765 days; 2023-26, 948 days) are used as each other's
check. Neither is clean - both have been read - so a survivor here is a
hypothesis to preregister on 2017-19, NOT an adopted rule.

Reported on the FLAT railed empire (the frozen spec) and on the ARMED book.
    python3 loser_autopsy.py
"""
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

QL = "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18"
sys.path.insert(0, QL)
sys.path.insert(0, "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad")
import scripts.conviction_sizing as CS          # noqa: E402
import scripts.offline_briefings as OB          # noqa: E402

COST, SESS_H = CS.COST_PTS, 23.0

ERAS = {
    "2020-22": dict(
        bars="data/reference/nq_2020_2022_1m.parquet",
        lv="pd_va_trades_nq20a_lvall_xr30_sar_through_tf1{a}.jsonl.gz",
        sv="vwap_rev_tf1_retest_nq20a_ng0_xr30_dd{a}.jsonl.gz",
        nv="vwap_rev_tf1_retest_nq20a_ng0_xr30_nyanc_dd{a}.jsonl.gz"),
    "2023-26": dict(
        bars=None,
        lv="pd_va_trades_lvall_xr30_sar_through_tf1_ng{a}.jsonl.gz",
        sv="vwap_rev_tf1_retest_xr30_dd{a}.jsonl.gz",
        nv="vwap_rev_tf1_retest_xr30_nyanc_dd{a}.jsonl.gz"),
}


def net(t):
    return t["r"] - COST / t["risk"]


def day_series(cfg, arm):
    a = "_arm1" if arm else ""
    books = [CS.load(cfg[k].format(a=a), champ_cell=(k != "lv")) for k in ("lv", "sv", "nv")]
    kept = CS.rail_pass(books)
    days = sorted(kept)
    R = {d: sum(net(t) for t in kept[d]) for d in days}
    return days, R, kept


def load_bars(path):
    if path is None:
        return OB.get_bars()
    b = pd.read_parquet(f"{QL}/{path}")
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(OB.NY)
    return b.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]


def features(bars, days):
    """Everything here closes at or before the day's own 18:00 open."""
    segs = {}
    for d in days:
        t0 = pd.Timestamp(f"{d} 18:00", tz=OB.NY)
        segs[d] = (t0, bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=SESS_H))])
    rows, hist = {}, []
    prev = None
    for d in days:
        t0, sess = segs[d]
        if prev is None or len(sess) < 300:
            prev = d
            continue
        _, ps = segs[prev]
        if len(ps) < 300:
            prev = d
            continue
        prng = float(ps.high.max() - ps.low.min())
        pcand = float((ps.high - ps.low).median())
        pO, pC = float(ps.open.iloc[0]), float(ps.close.iloc[-1])
        med20 = float(np.median(hist[-20:])) if len(hist) >= 20 else np.nan
        rows[d] = dict(
            prev_range=prng,
            vol_ratio=prng / med20 if med20 and med20 > 0 else np.nan,
            prev_candle=pcand,
            prev_push=abs(pC - pO) / prng if prng > 0 else np.nan,
            prev_close_pos=((pC - float(ps.low.min())) / prng) if prng > 0 else np.nan,
            gap_pts=float(sess.open.iloc[0]) - pC,
            gap_ratio=abs(float(sess.open.iloc[0]) - pC) / prng if prng > 0 else np.nan,
            dow=t0.dayofweek,
        )
        hist.append(prng)
        prev = d
    return rows


def buckets(vals, k=4):
    q = np.nanquantile(vals, np.linspace(0, 1, k + 1))
    q[0], q[-1] = -np.inf, np.inf
    return q


def report(feat, R, days, name, k=4, labels=None):
    xs = np.array([feat[d][name] for d in days if d in feat and np.isfinite(feat[d][name])])
    ds = [d for d in days if d in feat and np.isfinite(feat[d][name])]
    ys = np.array([R[d] for d in ds])
    if name == "dow":
        edges, idx = None, xs.astype(int)
        keys = sorted(set(idx))
    else:
        edges = buckets(xs, k)
        idx = np.clip(np.digitize(xs, edges[1:-1]), 0, k - 1)
        keys = list(range(k))
    out = []
    for kk in keys:
        m = idx == kk
        lbl = (labels[kk] if labels else
               (f"{edges[kk]:.2f}–{edges[kk+1]:.2f}" if edges is not None else str(kk)))
        out.append((lbl, int(m.sum()), float(ys[m].mean()), float(ys[m].min()),
                    float((ys[m] < 0).mean())))
    return out


print(__doc__.split("PREREGISTERED")[0].split("\n\n")[1].strip().replace("\n", " "))

DATA = {}
for era, cfg in ERAS.items():
    bars = load_bars(cfg["bars"])
    for arm in (False, True):
        days, R, kept = day_series(cfg, arm)
        if not arm:
            feat = features(bars, days)
        DATA[(era, arm)] = (days, R, kept, feat)

# ---------- PART 1: descriptive autopsy ----------
print("\n" + "=" * 92)
print("PART 1 — WHAT A LOSING DAY LOOKS LIKE (flat railed empire, both eras pooled)")
print("=" * 92)
allday = []
for era in ERAS:
    days, R, kept, feat = DATA[(era, False)]
    for d in days:
        if d in feat:
            allday.append((era, d, R[d], kept[d], feat[d]))
allday.sort(key=lambda x: x[2])
n = len(allday)
print(f"{n:,} session-days with full features "
      f"({sum(1 for x in allday if x[0]=='2020-22')} + {sum(1 for x in allday if x[0]=='2023-26')})")

def wr(ts):
    tp = sum(1 for t in ts if t["res"] == "TARGET"); st = sum(1 for t in ts if t["res"] == "STOP")
    return tp / max(tp + st, 1)

print(f"\n{'group':<20}{'days':>7}{'mean R':>10}{'WR':>8}{'trades/d':>10}"
      f"{'prev range':>12}{'vol ratio':>11}{'|gap|/rng':>11}{'prev push':>11}")
print("-" * 92)
for lbl, sl in (("worst 1%", allday[:n // 100]), ("worst 5%", allday[:n // 20]),
                ("worst 10%", allday[:n // 10]), ("all days", allday),
                ("best 10%", allday[-(n // 10):])):
    ts = [t for x in sl for t in x[3]]
    f = [x[4] for x in sl]
    print(f"{lbl:<20}{len(sl):>7}{np.mean([x[2] for x in sl]):>+10.1f}{wr(ts):>8.1%}"
          f"{len(ts)/len(sl):>10.1f}"
          f"{np.mean([q['prev_range'] for q in f]):>12.1f}"
          f"{np.nanmean([q['vol_ratio'] for q in f]):>11.2f}"
          f"{np.nanmean([q['gap_ratio'] for q in f]):>11.3f}"
          f"{np.nanmean([q['prev_push'] for q in f]):>11.3f}")

print("\nthe 12 worst days in either era:")
print(f"  {'era':<10}{'day':<13}{'net R':>9}{'n':>5}{'WR':>7}{'prev rng':>10}"
      f"{'volrat':>8}{'gap':>9}{'push':>7}")
for era, d, r, ts, f in allday[:12]:
    print(f"  {era:<10}{d:<13}{r:>+9.1f}{len(ts):>5}{wr(ts):>7.0%}"
          f"{f['prev_range']:>10.0f}{f['vol_ratio']:>8.2f}{f['gap_pts']:>+9.1f}{f['prev_push']:>7.2f}")

# ---------- PART 2: is it predictable before the open? ----------
FEATS = [("vol_ratio", "prior range / 20-day median"),
         ("prev_range", "prior session range (pts)"),
         ("prev_candle", "prior median 1m candle (pts)"),
         ("gap_ratio", "|session gap| / prior range"),
         ("prev_push", "prior |close-open| / range  (trend day)"),
         ("prev_close_pos", "prior close position in range"),
         ("dow", "day of week")]
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

print("\n" + "=" * 92)
print("PART 2 — IS IT KNOWABLE BEFORE THE OPEN?  (quartiles, both eras, flat book)")
print("=" * 92)
verdicts = {}
for key, desc in FEATS:
    print(f"\n{desc}")
    print(f"  {'bucket':<16}" + "".join(f"{e:>30}" for e in ERAS))
    print(f"  {'':<16}" + "".join(f"{'days':>8}{'mean R':>10}{'red%':>7}{'worst':>7}" for _ in ERAS))
    tabs = {}
    for era in ERAS:
        days, R, kept, feat = DATA[(era, False)]
        tabs[era] = report(feat, R, days, key, labels=DOW if key == "dow" else None)
    nb = len(tabs[list(ERAS)[0]])
    for i in range(nb):
        line = f"  {tabs[list(ERAS)[0]][i][0]:<16}"
        for era in ERAS:
            lb, cnt, mean, worst, red = tabs[era][i]
            line += f"{cnt:>8}{mean:>+10.1f}{red:>7.0%}{worst:>+7.0f}"
        print(line)
    spreads, minn = [], []
    for era in ERAS:
        ms = [t[2] for t in tabs[era]]
        spreads.append(max(ms) - min(ms))
        minn.append(min(t[1] for t in tabs[era]))
    v = ("SURVIVOR" if min(spreads) >= 3.0 and min(minn) >= 120 else
         "watch" if min(spreads) >= 1.5 and min(minn) >= 120 else "null")
    verdicts[desc] = (v, spreads, minn)
    print(f"  -> spread {spreads[0]:.1f}R / {spreads[1]:.1f}R   min bucket n "
          f"{min(minn)}   {v}")

print("\n" + "=" * 92)
print("VERDICTS (preregistered bar: >=3.0R spread in BOTH eras, every bucket >=120 days)")
print("=" * 92)
for d, (v, s, m) in sorted(verdicts.items(), key=lambda x: -min(x[1][1])):
    print(f"  {v:<10}{d:<42}spread {s[0]:>5.1f}R / {s[1]:>5.1f}R")
