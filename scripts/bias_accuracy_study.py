#!/usr/bin/env python3
"""HTF-bias ACCURACY STUDY — Jul 2025 -> Jul 2026. No trading: grade the bias itself.

Per day, two reads from the cached timelines (built by the no-lookahead engine):
  * 08:00 premarket read
  * 09:30 open-checkpoint read (PRIMARY — the bias in force when NY trades)

GRADING ("correct only if the New York session follows the bias"):
  net = NY session close(16:00) - open(09:30); thr = 0.10% of the open (~20-25pt).
  BULLISH: net > +thr CORRECT | net < -thr WRONG | else FLAT (counts as not-correct).
  BEARISH mirrored. NEUTRAL: CORRECT iff |net| <= thr (the day really was directionless);
  a NEUTRAL read on a trending day is graded WRONG-missed (note says which way it ran).

LEARNING LOOP (causal, walk-forward): each (bias x conviction) cell keeps its trailing-60
graded-day accuracy. Before reading day D, cells with accuracy < 40% (n >= 10) are DEMOTED
to NEUTRAL — the adapted read distrusts its own historically-unreliable cells. Raw vs
adapted accuracy is tracked monthly; demotion events are logged. Only prior days feed the
stats — day D never sees its own outcome.

Extra per-day diagnostics: primary-draw touched, manipulation->expansion (PO3) shape,
high-impact news in the morning, 08:00->09:30 flip, morning-leg (09:30->12:00) direction.
"""
import io
from collections import deque
from datetime import time as dtime

import numpy as np
import pandas as pd

import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
NY = "America/New_York"
START, END = "2025-07-01", "2026-07-15"
THR_PCT = 0.0010          # 0.10% of session open = flat band
TRAIL, MIN_N, DEMOTE_ACC = 60, 10, 0.40

# ---------------- data ----------------
bars = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")
bars = bars[(bars.day >= START) & (bars.day <= END)]

TL = pd.read_csv("/home/user/AI-trading-agents/analysis/bias_timelines_3yr.csv",
                 dtype={"day": str, "time": str})
TL = TL[(TL.day >= START) & (TL.day <= END)].sort_values(["day", "time"])

news_frames = []
for f in ["/home/user/gs/config/news_calendar.csv", "/home/user/gs/config/news_calendar_hist.csv"]:
    try:
        rows = [l for l in open(f) if not l.startswith("#")]
        news_frames.append(pd.read_csv(io.StringIO("".join(rows))))
    except Exception:
        pass
NEWS = pd.concat(news_frames, ignore_index=True)
NEWS = NEWS[NEWS["datetime_ET"] != "impact"]
NEWS["dt"] = pd.to_datetime(NEWS["datetime_ET"])
NEWS["day"] = NEWS["dt"].dt.strftime("%Y-%m-%d")
NEWS = NEWS[NEWS["impact"].astype(str).str.lower() == "high"]
news_days = {d: ", ".join(g["dt"].dt.strftime("%H:%M") + " " + g.get("event", "").astype(str))
             for d, g in NEWS[(NEWS.dt.dt.time >= dtime(7, 30)) & (NEWS.dt.dt.time <= dtime(12, 0))].groupby("day")}

def parse_draws(s):
    out = []
    for part in str(s or "").split("|"):
        if ":" in part:
            px, kind = part.rsplit(":", 1)
            try:
                out.append((float(px), kind))
            except ValueError:
                pass
    return out

# per-day session stats
rows = []
for day, g in bars.groupby("day"):
    ses = g[(g.ts.dt.time >= dtime(9, 30)) & (g.ts.dt.time < dtime(16, 0))]
    if len(ses) < 100:
        continue
    o = float(ses.open.iloc[0]); c = float(ses.close.iloc[-1])
    hi = float(ses.high.max()); lo = float(ses.low.min())
    t_hi = ses.ts[ses.high.idxmax()].strftime("%H:%M")
    t_lo = ses.ts[ses.low.idxmin()].strftime("%H:%M")
    noon = ses[ses.ts.dt.time < dtime(12, 0)]
    rows.append(dict(day=day, o=o, c=c, hi=hi, lo=lo, t_hi=t_hi, t_lo=t_lo,
                     noon=float(noon.close.iloc[-1]) if len(noon) else c))
SES = pd.DataFrame(rows).set_index("day")

tl_map = {d: list(g.itertuples()) for d, g in TL.groupby("day")}

def read_at(day, hhmm):
    tl = tl_map.get(day)
    if not tl:
        return None
    cur = None
    for r in tl:
        if r.time <= hhmm:
            cur = r
        else:
            break
    return cur

# ---------------- walk forward, grade, learn ----------------
cell_hist = {}            # (bias,tier) -> deque of (keep_correct, flip_correct) tuples
demotions = []            # learning log (policy decisions)
policy_state = {}         # (bias,tier) -> current policy, to log changes only
out = []

def cell_policy(key):
    """Learned per-cell policy from trailing outcomes: keep / flip / drop.
    keep needs trailing acc >= 40%; flip needs >= 50% (higher bar - it inverts the read);
    if neither clears, drop to NEUTRAL. None until MIN_N graded days exist."""
    h = cell_hist.get(key)
    if not h or len(h) < MIN_N:
        return None, 0, 0.0, 0.0
    ak = sum(x[0] for x in h) / len(h)
    af = sum(x[1] for x in h) / len(h)
    if af > ak and af >= 0.50:
        return "flip", len(h), ak, af
    if ak >= DEMOTE_ACC:
        return "keep", len(h), ak, af
    return "drop", len(h), ak, af

def grade(bias, net, thr):
    if bias == "BULLISH":
        return "CORRECT" if net > thr else ("WRONG" if net < -thr else "FLAT")
    if bias == "BEARISH":
        return "CORRECT" if net < -thr else ("WRONG" if net > thr else "FLAT")
    return "CORRECT" if abs(net) <= thr else "WRONG"

for day in sorted(SES.index):
    if day not in tl_map:
        continue
    s = SES.loc[day]
    thr = THR_PCT * s.o
    net = s.c - s.o
    net_am = s.noon - s.o
    r8 = read_at(day, "08:00")
    r9 = read_at(day, "09:30")
    if r9 is None:
        continue
    b8 = r8.bias if r8 is not None else "NEUTRAL"
    b9, tier = r9.bias, r9.tier

    # adapted read: learned per-cell policy (keep/flip/drop) — uses ONLY prior days' outcomes
    adapted = b9
    policy = None; demoted = False
    if b9 != "NEUTRAL":
        policy, n, ak, af = cell_policy((b9, tier))
        if policy == "flip":
            adapted = "BEARISH" if b9 == "BULLISH" else "BULLISH"
        elif policy == "drop":
            adapted = "NEUTRAL"; demoted = True
        if policy and policy_state.get((b9, tier)) != policy:
            policy_state[(b9, tier)] = policy
            demotions.append(dict(day=day, cell=f"{b9}/{tier}", policy=policy,
                                  keep_acc=round(ak * 100), flip_acc=round(af * 100), n=n))

    v8 = grade(b8, net, thr)
    v9 = grade(b9, net, thr)
    va = grade(adapted, net, thr)

    # diagnostics
    draws = parse_draws(getattr(r9, "draws", ""))
    draw_hit = any((s.hi >= px) if b9 == "BULLISH" else (s.lo <= px)
                   for px, _ in draws) if (draws and b9 in ("BULLISH", "BEARISH")) else False
    po3 = ""
    if b9 == "BULLISH":
        po3 = "manip->expand shape" if s.t_lo < s.t_hi else "no PO3 shape (high first)"
    elif b9 == "BEARISH":
        po3 = "manip->expand shape" if s.t_hi < s.t_lo else "no PO3 shape (low first)"
    flip = (b8 != b9)
    news = news_days.get(day, "")

    # note ("describe if it was right / what went wrong")
    dirword = "up" if net > thr else ("down" if net < -thr else "flat")
    bits = [f"NY {net:+.0f}pt ({dirword})"]
    if v9 == "CORRECT":
        bits.append("session followed the bias")
        if draw_hit:
            bits.append("draw reached")
        if po3.startswith("manip"):
            bits.append("PO3 shape played out")
    else:
        if b9 == "NEUTRAL":
            bits.append(f"NEUTRAL read but the session trended {dirword} — missed day")
        elif v9 == "FLAT":
            bits.append("bias was directional but the session chopped flat")
        else:
            bits.append(f"session ran {dirword} AGAINST the {b9.lower()} read")
            if po3 and not po3.startswith("manip"):
                bits.append(po3)
        if flip:
            bits.append(f"(read flipped {b8}->{b9} at the open)")
        if news:
            bits.append(f"news: {news[:60]}")
    if policy == "flip":
        bits.append(f"[LEARNED: fading {b9}/{tier} — trailing keep {ak*100:.0f}% vs flip {af*100:.0f}%]")
    elif policy == "drop":
        bits.append(f"[LEARNED: {b9}/{tier} dropped to NEUTRAL — trailing acc {ak*100:.0f}%]")

    out.append(dict(day=day, weekday=pd.Timestamp(day).day_name(), bias8=b8, bias=b9, tier=tier,
                    adapted=adapted, demoted=demoted, net=round(net, 1),
                    net_pct=round(100 * net / s.o, 2), am_net=round(net_am, 1),
                    verdict8=v8, verdict=v9, verdict_adapted=va,
                    policy=policy or "", draw_hit=bool(draw_hit), po3=po3, flip=flip, news=bool(news),
                    note="; ".join(bits)))

    # update trailing cell history AFTER grading (day D feeds D+1 onward)
    if b9 in ("BULLISH", "BEARISH"):
        opp = "BEARISH" if b9 == "BULLISH" else "BULLISH"
        cell_hist.setdefault((b9, tier), deque(maxlen=TRAIL)).append(
            (1 if v9 == "CORRECT" else 0, 1 if grade(opp, net, thr) == "CORRECT" else 0))

J = pd.DataFrame(out)
J.to_csv(f"{S}/bias_accuracy_days.csv", index=False)
pd.DataFrame(demotions).to_csv(f"{S}/bias_learning_log.csv", index=False)

# ---------------- summary ----------------
def acc(x, col="verdict"):
    return round(100 * (x[col] == "CORRECT").mean(), 1) if len(x) else 0.0

print(f"days graded: {len(J)}  ({J.day.min()} -> {J.day.max()})")
print(f"\nbias mix @09:30: {J.bias.value_counts().to_dict()}")
print(f"\nOVERALL accuracy (all days): 08:00 read {acc(J,'verdict8')}%  |  09:30 read {acc(J)}%  |  adapted {acc(J,'verdict_adapted')}%")
D = J[J.bias != "NEUTRAL"]
print(f"DIRECTIONAL reads only:      09:30 {acc(D)}%  |  adapted (same days) {acc(D,'verdict_adapted')}%")
print("\nby bias (09:30 read):")
for b in ["BULLISH", "BEARISH", "NEUTRAL"]:
    x = J[J.bias == b]
    if len(x):
        print(f"  {b:8s} {len(x):3d}d  correct {acc(x)}%  (wrong {(x.verdict=='WRONG').mean()*100:.0f}%, flat {(x.verdict=='FLAT').mean()*100:.0f}%)")
print("\nby conviction (directional):")
for t, x in D.groupby("tier"):
    print(f"  {t:8s} {len(x):3d}d  correct {acc(x)}%")
print("\nmonthly (raw -> adapted):")
J["mo"] = J.day.str.slice(0, 7)
for mo, g in J.groupby("mo"):
    print(f"  {mo}  {len(g):2d}d  raw {acc(g):5.1f}%  adapted {acc(g,'verdict_adapted'):5.1f}%")
h1, h2 = J.iloc[:len(J)//2], J.iloc[len(J)//2:]
print(f"\nLEARNING CHECK first half raw {acc(h1)}% adapted {acc(h1,'verdict_adapted')}%  ||  second half raw {acc(h2)}% adapted {acc(h2,'verdict_adapted')}%")
print(f"demotion events: {len(demotions)}")
print("saved bias_accuracy_days.csv, bias_learning_log.csv")
