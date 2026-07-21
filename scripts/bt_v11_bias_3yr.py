#!/usr/bin/env python3
"""Champion v1.1 x HTF-bias governance — full-dataset backtest (2023-01 -> 2026-07).

SETUP SELECTION = Champion v1.1, mirrored from scripts/year_suite.py:
  war day (regime imbal_share_20 >= 0.5) -> E4 book: |close - stop_ref| <= 15pt triggers
  balance day -> E3 book (fade); CUT2: no B-pattern triggers in the 09h; CUT3: E3 book
  skips with_trend (fade book only fades); pattern != unclassified.

GOVERNANCE (user spec): bias in force at trigger time drives every trade.
  aligned (BULLISH&long / BEARISH&short) -> allowed. NEUTRAL -> no trade.
  counter-bias -> only "extremely high execution": mechanical bar = confluence_count >= 3
  (the top-confluence A+ tier); tagged counter=True.

WINDOWS/CAPS: fill in [08:00,09:30) -> premarket, max 2/day; [09:40,10:15) -> in-time,
  max 2/day; gap 09:30-09:40 and >=10:15 -> no entry. One position at a time.

STOPS: premarket -> v1.1 logic: stop_ref (wick extreme), skip risk<5 (CUT1), skip >100
  (pathological). in-time -> wick far end; skip if wick dist > 70; pad to 20 when < 15;
  dist > 40 -> DE-RISK to 5 MNQ ($10/pt) else normal 1 NQ ($20/pt).

TARGET: nearest bias-file draw beyond entry in trade direction, capped at 4R; no draw in
  direction -> 4R. Full exit. Resolution: stop-first conservative intrabar, target needs
  trade-through by 1 tick, EOD flatten 15:55. Entry next-1m-bar open +1 tick adverse slip;
  stop exits +1 tick adverse; commission $5.00 RT full / $2.50 RT de-risk.

NO LOOKAHEAD: bias reads use candles closed <= read time (built separately); entries use
  the bar after the trigger candle closes; draws/stops fixed at entry; forward walk only.
"""
import ast
import sys
from datetime import time as dtime

import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
NY = "America/New_York"
TICK = 0.25
SLIP = 1 * TICK                    # 1 tick per side, adverse
PV_FULL, PV_DERISK = 20.0, 10.0    # $/pt: 1 NQ vs 5 MNQ
COMM_FULL, COMM_DERISK = 5.00, 2.50  # $ round-turn
FLAT = dtime(15, 55)

# ---------------------------------------------------------------- load
print("loading ...", flush=True)
bars = pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars = bars.sort_values("ts").reset_index(drop=True)
bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")
day_bars = {d: g.reset_index(drop=True) for d, g in bars.groupby("day")}

TL = pd.read_csv(f"{S}/bias_timelines_3yr.csv", dtype={"day": str, "time": str})
TL = TL.sort_values(["day", "time"])
tl_map = {d: list(zip(g["time"], g["bias"], g["tier"], g["draws"].fillna("")))
          for d, g in TL.groupby("day")}
print(f"timelines: {TL.day.nunique()} days", flush=True)

trig_frames = []
for p in ["/home/user/gs/output/triggers_hist2326_ob.csv",
          "/home/user/gs/output/triggers_feb_ob.csv",
          "/home/user/gs/output/triggers_marjul_ob.csv"]:
    trig_frames.append(pd.read_csv(p))
T = pd.concat(trig_frames, ignore_index=True)
T = T[T.pattern != "unclassified"].copy()
T["day"] = T.ts.str.slice(0, 10)
T["hm"] = T.ts.str.slice(11, 16)
T = T.sort_values("ts").reset_index(drop=True)
V = pd.read_csv("/home/user/gs/output/regime_vector.csv")
WAR = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
print(f"triggers: {len(T)} ({T.day.min()} -> {T.day.max()})", flush=True)


def bias_at(day, hm):
    tl = tl_map.get(day)
    if not tl:
        return None
    cur = None
    for tm, b, tier, dws in tl:
        if tm <= max(hm, "08:00"):
            cur = (b, tier, dws)
        else:
            break
    return cur


def parse_draws(s):
    out = []
    for part in (s or "").split("|"):
        if ":" in part:
            px, kind = part.rsplit(":", 1)
            try:
                out.append((float(px), kind))
            except ValueError:
                pass
    return out


# ---------------------------------------------------------------- walk
trades = []
open_until = {}          # day -> exit hh:mm blocking (one position at a time)
counts = {}              # (day, window) -> fills

for t in T.itertuples():
    day = t.day
    db = day_bars.get(day)
    if db is None:
        continue
    # --- v1.1 book selection -------------------------------------------------
    is_war = day in WAR
    if is_war:
        if abs(t.close - t.stop_ref) > 15.0:      # E4 tight-stop book
            continue
        branch = "E4war"
    else:
        if t.htf_flag == "with_trend":            # CUT3: fade book only fades
            continue
        branch = "E3bal"
    hour = int(t.hm[:2])
    if t.pattern == "B" and hour == 9:            # CUT2
        continue

    # --- governance: bias in force at trigger time ---------------------------
    g = bias_at(day, t.hm)
    if g is None:
        continue
    b, tier, dws_s = g
    if b == "NEUTRAL":
        continue
    aligned = (b == "BULLISH" and t.direction == "long") or (b == "BEARISH" and t.direction == "short")
    counter = not aligned
    if counter and t.confluence_count < 3:        # "extremely high execution" bar
        continue

    # --- fill: next 1m bar open after trigger close --------------------------
    arr = db[db.ts >= pd.Timestamp(t.ts)]
    if arr.empty:
        continue
    fb = arr.iloc[0]
    ft = fb.ts.strftime("%H:%M")
    if "08:00" <= ft < "09:30":
        window = "premarket"
    elif "09:40" <= ft < "10:15":
        window = "intime"
    else:
        continue
    if counts.get((day, window), 0) >= 2:
        continue
    if ft < open_until.get(day, "00:00"):         # one position at a time
        continue
    sgn = 1 if t.direction == "long" else -1
    entry = float(fb.open) + sgn * SLIP

    # --- stop ---------------------------------------------------------------
    wick_dist = abs(entry - t.stop_ref)
    padded = False
    if window == "premarket":                     # v1.1's own stop logic
        if wick_dist < 5.0 or wick_dist > 100.0:
            continue
        stop_dist = wick_dist
        derisk = False
    else:                                         # in-time: 15 / pad-20 / 70 / 40-derisk
        if wick_dist > 70.0:
            continue
        stop_dist = wick_dist
        if stop_dist < 15.0:
            stop_dist = 20.0
            padded = True
        derisk = stop_dist > 40.0
    stop_px = entry - sgn * stop_dist

    # --- target: nearest bias draw in direction, cap 4R ----------------------
    draws = parse_draws(dws_s)
    in_dir = [(px, k) for px, k in draws if (px > entry if sgn == 1 else px < entry)]
    cap_dist = 4.0 * stop_dist
    if in_dir:
        draw_px, draw_kind = min(in_dir, key=lambda x: abs(x[0] - entry))
        d_dist = abs(draw_px - entry)
        if d_dist <= cap_dist:
            tgt_dist, tgt_kind = d_dist, f"draw:{draw_kind}"
        else:
            tgt_dist, tgt_kind = cap_dist, "4R cap"
    else:
        tgt_dist, tgt_kind = cap_dist, "4R cap (no draw in dir)"
    tgt_px = entry + sgn * tgt_dist

    # --- resolve forward (stop-first conservative; target needs trade-through) ---
    fut = db[db.ts >= fb.ts]
    fut = fut[fut.ts.dt.time <= FLAT]
    exit_px = None; reason = None; exit_ts = None
    for r_ in fut.itertuples():
        stop_hit = (r_.low <= stop_px) if sgn == 1 else (r_.high >= stop_px)
        if stop_hit:
            worse = min(stop_px, r_.open) if sgn == 1 else max(stop_px, r_.open)
            exit_px = worse - sgn * SLIP; reason = "stop"; exit_ts = r_.ts; break
        tgt_hit = (r_.high >= tgt_px + TICK) if sgn == 1 else (r_.low <= tgt_px - TICK)
        if tgt_hit:
            exit_px = tgt_px; reason = tgt_kind; exit_ts = r_.ts; break
    if exit_px is None:
        last = fut.iloc[-1]
        exit_px = float(last.close) - sgn * SLIP; reason = "eod"; exit_ts = last.ts

    pts = sgn * (exit_px - entry)
    pv = PV_DERISK if derisk else PV_FULL
    comm = COMM_DERISK if derisk else COMM_FULL
    dollars = pts * pv - comm
    R = pts / stop_dist
    counts[(day, window)] = counts.get((day, window), 0) + 1
    open_until[day] = exit_ts.strftime("%H:%M")
    trades.append(dict(
        day=day, weekday=pd.Timestamp(day).day_name(), fill=ft, window=window, branch=branch,
        bias=b, conviction=tier, counter=counter, dir=t.direction, pattern=t.pattern,
        entry=round(entry, 2), stop_dist=round(stop_dist, 2), padded=padded, derisk=derisk,
        target_kind=tgt_kind, tgt_dist=round(tgt_dist, 2), reason=reason,
        exit=round(exit_px, 2), exit_t=exit_ts.strftime("%H:%M"),
        pts=round(pts, 2), R=round(R, 3), dollars=round(dollars, 2),
    ))

J = pd.DataFrame(trades)
J.to_csv(f"{S}/bt_v11_bias_3yr_trades.csv", index=False)

# ---------------------------------------------------------------- headline
def pf(x):
    w = x[x.dollars > 0].dollars.sum(); l = -x[x.dollars <= 0].dollars.sum()
    return w / l if l > 0 else np.inf

def streaks(x):
    wmax = lmax = w = l = 0
    for v in x.sort_values(["day", "fill"]).dollars > 0:
        if v: w += 1; l = 0
        else: l += 1; w = 0
        wmax = max(wmax, w); lmax = max(lmax, l)
    return wmax, lmax

eq = J.sort_values(["day", "fill"]).dollars.cumsum()
dd = float((eq - eq.cummax()).min())
ws, ls = streaks(J)
print("\n=== HEADLINE (2023-01 -> 2026-07) ===")
print(f"trades {len(J)} | win {(J.dollars>0).mean()*100:.1f}% | avgR {J.R.mean():+.3f} | "
      f"totR {J.R.sum():+.1f} | pts {J.pts.sum():+.0f} | ${J.dollars.sum():+,.0f} | "
      f"PF {pf(J):.2f} | maxDD ${dd:,.0f} | streaks W{ws}/L{ls}")
for c, lab in [(J.window == "premarket", "premarket"), (J.window == "intime", "in-time 09:40-10:15"),
               (~J.counter, "with-bias"), (J.counter, "counter-bias"),
               (J.derisk, "de-risked (>40pt)")]:
    x = J[c]
    if len(x):
        print(f"  {lab:22s} {len(x):5d}t  win {(x.dollars>0).mean()*100:4.1f}%  avgR {x.R.mean():+.3f}  ${x.dollars.sum():+11,.0f}  PF {pf(x):.2f}")
print("\nby year:")
for y, g in J.groupby(J.day.str.slice(0, 4)):
    print(f"  {y}  {len(g):5d}t  win {(g.dollars>0).mean()*100:4.1f}%  ${g.dollars.sum():+11,.0f}  PF {pf(g):.2f}")
print("\nby conviction:")
for cv, g in J.groupby("conviction"):
    print(f"  {cv:8s} {len(g):5d}t  win {(g.dollars>0).mean()*100:4.1f}%  avgR {g.R.mean():+.3f}  ${g.dollars.sum():+11,.0f}")
print("\nexit reasons:", J.reason.str.split(":").str[0].value_counts().to_dict())
print("saved bt_v11_bias_3yr_trades.csv")
