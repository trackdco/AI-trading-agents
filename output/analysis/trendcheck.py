"""Tag every fill WITH or AGAINST the prevailing higher-timeframe direction, and split R.

WHY THIS EXISTS
He put it directly: the stack "should be trend-conscious", and w49 scored strongly
positive while j49 scored clearly negative on the same contract. The obvious suspect is
that the agents can see where price sits inside a RANGE (`chop_state` gives them
zone_now / in_middle / range_width) but nothing in the briefing tells them whether that
range is DRIFTING. In a trending week the upper edge of a range is not an edge to fade,
it is a waypoint - and "fade the edge, pass the middle" then loses on exactly the trades
it is most confident about.

That is a hypothesis, and this file exists to make it a number instead of a story.

METHOD - deliberately crude, and stated so
Trend is measured on the 15-minute chart at the fill minute, from bars STRICTLY BEFORE it
(so nothing here is hindsight):
  - slope: linear fit through the last N 15m closes, expressed in points per hour
  - structure: whether the last three 15m swing highs and lows are rising, falling, or mixed
A fill is WITH trend if its side agrees with both, AGAINST if it opposes both, and MIXED
otherwise. The two-signal rule is what keeps a single noisy slope from deciding it.

This does NOT feed the run. It reads the finished books and reports. Nothing here changed
any verdict - every trade was adjudicated before this file existed.

usage: trendcheck.py [run ...]
"""
import sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
import pandas as pd
from scripts.replay_tools import book, htf
from reconcile import DEAD

NEXT = {"2026-06-21": "2026-06-22", "2026-06-22": "2026-06-23", "2026-06-23": "2026-06-24",
        "2026-06-24": "2026-06-25", "2026-06-25": "2026-06-26",
        "2026-05-31": "2026-06-01", "2026-06-01": "2026-06-02", "2026-06-02": "2026-06-03",
        "2026-06-03": "2026-06-04", "2026-06-04": "2026-06-05"}
W49 = ["2026-06-21", "2026-06-22", "2026-06-23", "2026-06-24", "2026-06-25"]
J49 = ["2026-05-31", "2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]

LOOKBACK_15M = 8          # two hours of 15m bars
SWINGS = 3


def live(r):
    return not any(r.get(k) for k in DEAD)


def trend_at(dn, minute, lookback=LOOKBACK_15M):
    """(label, slope_pts_per_hour, structure) from 15m bars strictly BEFORE `minute`."""
    b = htf.bars()
    t = pd.Timestamp(f"{dn} {minute}", tz=htf.NY)
    w = b[b.index < t]
    if w.empty:
        return None, None, None
    t15 = w.resample("15min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    t15 = t15.tail(lookback)
    if len(t15) < 4:
        return None, None, None

    # slope: points per hour, from a least-squares fit through the closes
    ys = t15.close.to_numpy(dtype=float)
    xs = list(range(len(ys)))
    n = len(ys)
    mx = sum(xs) / n
    my = sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    slope_per_bar = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / den if den else 0.0
    slope = slope_per_bar * 4.0          # 4 fifteen-minute bars per hour

    # structure: are the recent swing highs AND lows both rising, or both falling?
    hi = t15.high.tail(SWINGS).to_list()
    lo = t15.low.tail(SWINGS).to_list()
    rising = all(hi[i] > hi[i - 1] for i in range(1, len(hi))) and \
             all(lo[i] > lo[i - 1] for i in range(1, len(lo)))
    falling = all(hi[i] < hi[i - 1] for i in range(1, len(hi))) and \
              all(lo[i] < lo[i - 1] for i in range(1, len(lo)))
    structure = "up" if rising else "down" if falling else "mixed"

    # a slope under this is noise, not a trend, on an instrument that ranges tens of points
    NOISE = 10.0
    if slope > NOISE and structure != "down":
        label = "up"
    elif slope < -NOISE and structure != "up":
        label = "down"
    else:
        label = "flat"
    return label, round(slope, 1), structure


def fills(run, days):
    out = []
    for sd in days:
        rows = book.read(run, sd)
        if not rows:
            continue
        ex = {r["candidate_id"]: r for r in rows if r.get("row") == "exit" and live(r)}
        for f in rows:
            if f.get("row") != "fill" or not live(f):
                continue
            cid = f["candidate_id"]
            e = ex.get(cid)
            if not e:
                continue
            dn = NEXT[sd]
            label, slope, structure = trend_at(dn, f.get("fill_minute") or f.get("filled_at"))
            side = f.get("side")
            if label in ("up", "down"):
                agree = (side == "long" and label == "up") or (side == "short" and label == "down")
                stance = "WITH" if agree else "AGAINST"
            else:
                stance = "FLAT"
            out.append({
                "run": run, "sd": sd, "cid": cid, "window": f.get("window"), "side": side,
                "entry": f.get("entry"), "r": float(e.get("r_blended") or 0.0),
                "trend": label, "slope_pts_per_hr": slope, "structure": structure,
                "stance": stance,
            })
    return out


def report(runs=("w49", "j49")):
    days = {"w49": W49, "j49": J49}
    allf = []
    for run in runs:
        rs = fills(run, days[run])
        allf += rs
        print(f"\n=== {run} - {len(rs)} fills ===")
        print(f"{'day':<12}{'cid':<5}{'win':<8}{'side':<7}{'stance':<9}"
              f"{'trend':<7}{'slope/hr':>9}{'struct':>8}{'R':>10}")
        for f in rs:
            print(f"{f['sd']:<12}{f['cid']:<5}{f['window']:<8}{f['side']:<7}{f['stance']:<9}"
                  f"{str(f['trend']):<7}{str(f['slope_pts_per_hr']):>9}{str(f['structure']):>8}"
                  f"{f['r']:>+10.4f}")
        for st in ("WITH", "AGAINST", "FLAT"):
            g = [x for x in rs if x["stance"] == st]
            if g:
                tot = sum(x["r"] for x in g)
                wins = len([x for x in g if x["r"] > 0])
                print(f"   {st:<8} {len(g):>2} fills  {tot:>+9.4f}R  "
                      f"avg {tot/len(g):>+7.4f}R  {wins}W/{len(g)-wins}L")

    print("\n=== BOTH RUNS COMBINED ===")
    for st in ("WITH", "AGAINST", "FLAT"):
        g = [x for x in allf if x["stance"] == st]
        if g:
            tot = sum(x["r"] for x in g)
            wins = len([x for x in g if x["r"] > 0])
            print(f"   {st:<8} {len(g):>2} fills  {tot:>+9.4f}R  "
                  f"avg {tot/len(g):>+7.4f}R  {wins}W/{len(g)-wins}L")
    print("\nMethod: trend read on 15m bars STRICTLY BEFORE each fill minute - slope over the "
          f"last {LOOKBACK_15M} bars (points/hour, |slope| <= 10 counts as flat) AND swing "
          f"structure over the last {SWINGS}. WITH/AGAINST requires both to agree; anything "
          "else is FLAT. Nothing here fed the run - every verdict was made before this "
          "file existed.")


if __name__ == "__main__":
    report(tuple(sys.argv[1:]) or ("w49", "j49"))


# ---------------------------------------------------------------------------
# SECOND HORIZON - added after the first result came back NEGATIVE.
#
# The 2-hour 15m slope above does NOT separate the two weeks: in w49 the
# AGAINST-trend bucket was the BEST performer (+11.9R over 11 fills), which is
# the opposite of the hypothesis. A fade strategy fading into a 2-hour push is
# apparently fine - that is what fading IS.
#
# So the 2-hour window is the wrong horizon to test his question against. The
# claim worth testing is about the SESSION's direction, not the last two hours:
# is the day drifting one way underneath the ranges the agents are reading? That
# needs a measure anchored at the session open (18:00 the prior evening), which
# is the same anchor the briefings' own session levels use.
#
# Reporting both is the point. A measure that fails is evidence too, and hiding
# it would leave a story standing that the data does not support.
# ---------------------------------------------------------------------------

def session_drift(dn, minute):
    """Net move from the session open (18:00 prior evening) to `minute`, in points,
    plus the same as a fraction of the session's range so far. Strictly backward-looking."""
    b = htf.bars()
    t = pd.Timestamp(f"{dn} {minute}", tz=htf.NY)
    open_ts = t.normalize() - pd.Timedelta(hours=6)      # 18:00 the prior evening
    w = b[(b.index >= open_ts) & (b.index < t)]
    if len(w) < 30:
        return None, None
    net = float(w.close.iloc[-1] - w.open.iloc[0])
    rng = float(w.high.max() - w.low.min())
    return round(net, 2), (round(net / rng, 3) if rng else None)


def report2(runs=("w49", "j49")):
    days = {"w49": W49, "j49": J49}
    allf = []
    for run in runs:
        rs = fills(run, days[run])
        for f in rs:
            net, frac = session_drift(NEXT[f["sd"]], None) if False else session_drift(
                NEXT[f["sd"]], _fill_minute(run, f["sd"], f["cid"]))
            f["session_net_pts"] = net
            f["session_frac_of_range"] = frac
            if net is None:
                f["session_stance"] = "?"
            elif abs(frac or 0) < 0.25:
                f["session_stance"] = "FLAT"
            else:
                up = net > 0
                f["session_stance"] = ("WITH" if (up and f["side"] == "long") or
                                       (not up and f["side"] == "short") else "AGAINST")
        allf += rs
        print(f"\n=== {run} - session-drift horizon ===")
        print(f"{'day':<12}{'cid':<5}{'side':<7}{'stance':<9}{'net_pts':>9}{'frac':>7}{'R':>10}")
        for f in rs:
            print(f"{f['sd']:<12}{f['cid']:<5}{f['side']:<7}{f['session_stance']:<9}"
                  f"{str(f['session_net_pts']):>9}{str(f['session_frac_of_range']):>7}"
                  f"{f['r']:>+10.4f}")
        for st in ("WITH", "AGAINST", "FLAT"):
            g = [x for x in rs if x["session_stance"] == st]
            if g:
                tot = sum(x["r"] for x in g)
                w_ = len([x for x in g if x["r"] > 0])
                print(f"   {st:<8} {len(g):>2} fills {tot:>+9.4f}R  avg {tot/len(g):>+7.4f}R  {w_}W/{len(g)-w_}L")
    print("\n=== BOTH RUNS, session-drift horizon ===")
    for st in ("WITH", "AGAINST", "FLAT"):
        g = [x for x in allf if x["session_stance"] == st]
        if g:
            tot = sum(x["r"] for x in g)
            w_ = len([x for x in g if x["r"] > 0])
            print(f"   {st:<8} {len(g):>2} fills {tot:>+9.4f}R  avg {tot/len(g):>+7.4f}R  {w_}W/{len(g)-w_}L")


def _fill_minute(run, sd, cid):
    for r in book.read(run, sd):
        if r.get("row") == "fill" and r.get("candidate_id") == cid:
            return r.get("fill_minute") or r.get("filled_at")
    return None
