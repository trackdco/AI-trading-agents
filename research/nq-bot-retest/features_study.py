#!/usr/bin/env python3
"""
PREREGISTRATION-3 feature study.

  --build OUT.parquet   compute the twelve features (§2) for every sealed C1a×C3a / C1a×C3b trade,
                        using only bars up to the signal bar; writes one row per trade
  --report fit|test     the §3 tables for the given half (test is read ONCE, after the fit report
                        is committed); --config C1a_C3a (primary) or C1a_C3b (robustness)

Sessions are CME days (18:00 ET → 17:00 ET). Bars: the prepared 1-minute series each run was
replayed on. 2-minute closes for the EMAs are built exactly as the bot builds them.
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ET = ZoneInfo("America/New_York")
HERE = __file__.rsplit("/", 1)[0]
sys.path.insert(0, HERE)
from analyze_retest import block_bootstrap_lb  # noqa: E402

TRADES = {
    "C1a_C3a": [("data/holdout2/h2_ctl_C1a_C3a_capped.json", date(2018, 9, 1), date(2021, 8, 31)),
                ("data/dev/dev_C1a_C3a.json", date(2021, 9, 1), date(2024, 12, 31)),
                ("data/holdout/hold_C1a_C3a.json", date(2025, 1, 1), date(2026, 9, 2))],
    "C1a_C3b": [("data/holdout2/h2_ctl_C1a_C3b_capped.json", date(2018, 9, 1), date(2021, 8, 31)),
                ("data/dev/dev_C1a_C3b.json", date(2021, 9, 1), date(2024, 12, 31)),
                ("data/holdout/hold_C1a_C3b.json", date(2025, 1, 1), date(2026, 9, 2))],
}
BARS = [("data/holdout2_input/prepared/combined_1min.csv", date(2018, 8, 1), date(2021, 8, 31)),
        ("data/holdout_input/prepared/combined_1min.csv", date(2021, 9, 1), date(2026, 9, 3))]
FIB = (0.236, 0.382, 0.5, 0.618, 0.786)
TICK = 0.25


def tday(ts):
    return (ts + timedelta(days=1)).date() if ts.hour >= 18 else ts.date()


def load_bars(path, a, b):
    ts, o, h, l, c, v = [], [], [], [], [], []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            t = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S%z").astimezone(ET)
            d = tday(t)
            if d < a or d > b:
                continue
            ts.append(t); o.append(float(r["open"])); h.append(float(r["high"])); l.append(float(r["low"]))
            c.append(float(r["close"])); v.append(float(r["volume"]))
    df = pd.DataFrame({"ts": ts, "o": o, "h": h, "l": l, "c": c, "v": v})
    df["day"] = [tday(t) for t in df["ts"]]
    return df


def value_area(day_df):
    """POC / VAH / VAL from 1-minute bars: each bar's volume spread uniformly over [low, high] at 0.25."""
    lo = int(round(day_df["l"].min() / TICK)); hi = int(round(day_df["h"].max() / TICK))
    prof = np.zeros(hi - lo + 1)
    for L, H, V in zip(day_df["l"].values, day_df["h"].values, day_df["v"].values):
        a = int(round(L / TICK)) - lo; b = int(round(H / TICK)) - lo
        prof[a:b + 1] += V / (b - a + 1)
    if prof.sum() <= 0:
        return None
    poc = int(np.argmax(prof))
    target = 0.70 * prof.sum(); acc = prof[poc]; up = poc + 1; dn = poc - 1
    while acc < target and (up < len(prof) or dn >= 0):
        vu = prof[up] if up < len(prof) else -1; vd = prof[dn] if dn >= 0 else -1
        if vu >= vd:
            acc += vu; up += 1
        else:
            acc += vd; dn -= 1
    return ((poc + lo) * TICK, (dn + 1 + lo) * TICK, (up - 1 + lo) * TICK)   # POC, VAL, VAH


def session_stats(df):
    """Per session: prior-day VA (from the previous session), prior-session H/L, overnight H/L, OR H/L."""
    out = {}
    days = sorted(df["day"].unique())
    prev = None
    for d in days:
        g = df[df["day"] == d]
        et_t = g["ts"]
        hours = np.array([t.hour + t.minute / 60 for t in et_t])
        on = g[(hours >= 18) | (hours < 9.5)]
        orr = g[(hours >= 9.5) & (hours < 10.0)]
        out[d] = {"prev_va": value_area(df[df["day"] == prev]) if prev is not None else None,
                  "prev_hl": (df[df["day"] == prev]["h"].max(), df[df["day"] == prev]["l"].min()) if prev is not None else None,
                  "on_hl": (on["h"].max(), on["l"].min()) if len(on) else None,
                  "or_hl": (orr["h"].max(), orr["l"].min()) if len(orr) else None}
        prev = d
    return out


def build(out_path):
    rows = []
    for path, a, b in BARS:
        print(f"bars {path} {a}..{b}", flush=True)
        df = load_bars(path, a, b)
        print(f"  {len(df):,} minutes, {df['day'].nunique()} sessions; session stats…", flush=True)
        sess = session_stats(df)
        # 2-minute closes for EMAs (bot's bucketing)
        bt = [t.replace(minute=(t.minute // 2) * 2, second=0, microsecond=0) for t in df["ts"]]
        two = df.assign(bt=bt).groupby("bt", sort=True)["c"].last()
        ema20 = two.ewm(span=20, adjust=False).mean(); ema50 = two.ewm(span=50, adjust=False).mean(); ema200 = two.ewm(span=200, adjust=False).mean()
        idx2 = {t: i for i, t in enumerate(two.index)}
        # session VWAP / sigma at each minute (cumulative within the session)
        df["pv"] = df["c"] * df["v"]; df["pv2"] = df["c"] ** 2 * df["v"]
        gv = df.groupby("day")
        cv = gv["v"].cumsum(); cpv = gv["pv"].cumsum(); cpv2 = gv["pv2"].cumsum()
        vwap = (cpv / cv.replace(0, np.nan)).values
        var = (cpv2 / cv.replace(0, np.nan)).values - vwap ** 2
        sig = np.sqrt(np.clip(var, 0, None))
        tindex = {t: i for i, t in enumerate(df["ts"])}
        for cfg, segs in TRADES.items():
            for tpath, ta, tb in segs:
                if tb < a or ta > b:
                    continue
                d = json.load(open(tpath))
                ent = {r["trade_id"]: r for r in d["records"] if r["action"] == "entry"}
                for r in d["records"]:
                    if r["action"] != "exit" or r["trade_id"] not in ent:
                        continue
                    e = ent[r["trade_id"]]
                    st = datetime.fromisoformat(e["signal_timestamp"]).astimezone(ET)
                    ed = datetime.fromisoformat(e["timestamp"]).astimezone(ET).date()
                    if ed < max(ta, a) or ed > min(tb, b):
                        continue
                    # signal bar = 2-minute bar starting at st; its last minute is st+1min
                    last_min = st + timedelta(minutes=1)
                    i = tindex.get(last_min, tindex.get(st))
                    if i is None:
                        continue
                    price = df["c"].iloc[i]; atr = e["atr"] or np.nan; day = df["day"].iloc[i]
                    long = e["direction"] == "long"; sgn = 1 if long else -1
                    s = sess.get(day, {})
                    row = {"config": cfg, "trade_id": r["trade_id"], "entry_ts": e["timestamp"], "signal_ts": e["signal_timestamp"],
                           "direction": e["direction"], "pnl": r["adjusted_pnl"], "stop": e["stop_distance"], "atr": atr,
                           "score": e["signal_score"], "htf": e.get("htf_bias"), "hour": st.hour + st.minute / 60,
                           "levels": ",".join(e.get("swept_levels") or []), "depth": e.get("sweep_depth_pts"), "vol_ratio": e.get("volume_ratio")}
                    # F1/F2 VWAP
                    vw, sd = vwap[i], sig[i]
                    z = (price - vw) / sd if sd and sd > 0 else np.nan
                    row["F1_vwap_z"] = z
                    row["F1"] = "inside ±1σ" if abs(z) < 1 else ("1–2σ" if abs(z) < 2 else "beyond 2σ") if np.isfinite(z) else None
                    row["F2"] = ("toward" if (vw - price) * sgn > 0 else "away") if np.isfinite(vw) else None
                    # F3–F6 prior-day VA
                    va = s.get("prev_va")
                    if va and np.isfinite(atr) and atr > 0:
                        poc, val, vah = va
                        row["F3"] = "inside VA" if val <= price <= vah else ("above VAH" if price > vah else "below VAL")
                        row["F4"] = "at edge" if min(abs(price - vah), abs(price - val)) <= 0.25 * atr else "not"
                        dp = abs(price - poc) / atr
                        row["F5"] = "<0.5" if dp < 0.5 else ("0.5–1.5" if dp <= 1.5 else ">1.5")
                        row["F6"] = "toward" if (poc - price) * sgn > 0 else "away"
                    # F7 prior-session fib, F8 overnight fib
                    for key, name, cond in (("prev_hl", "F7", True), ("on_hl", "F8", 9.5 <= st.hour + st.minute / 60 < 16)):
                        hl = s.get(key)
                        if hl and cond and np.isfinite(atr) and atr > 0 and hl[0] > hl[1]:
                            H, L = hl
                            dist = min(abs(price - (L + f * (H - L))) for f in FIB) / atr
                            row[name] = "≤0.25" if dist <= 0.25 else ("0.25–0.75" if dist <= 0.75 else ">0.75")
                    # F9–F11 EMAs at the signal bar (2-minute bar starting at st)
                    j = idx2.get(st)
                    if j is not None and j >= 210 and np.isfinite(atr) and atr > 0:
                        slope = (ema200.iloc[j] - ema200.iloc[j - 10]) / atr
                        row["F9"] = "flat" if abs(slope) < 0.05 else ("with" if slope * sgn > 0 else "against")
                        dd = (price - ema20.iloc[j]) / atr * sgn
                        row["F10"] = "< −0.5" if dd < -0.5 else ("−0.5–0.5" if dd <= 0.5 else "> 0.5")
                        row["F11"] = "with" if (price - ema50.iloc[j]) * sgn > 0 else "against"
                    # F12 opening range
                    orr = s.get("or_hl"); hh = st.hour + st.minute / 60
                    if hh < 10.0:
                        row["F12"] = "forming"
                    elif orr:
                        oh, ol = orr
                        row["F12"] = "inside OR" if ol <= price <= oh else (("beyond in direction" if (price > oh) == long else "beyond against"))
                    rows.append(row)
        print(f"  trades featured so far: {len(rows):,}", flush=True)
    out = pd.DataFrame(rows)
    out.to_parquet(out_path, index=False)
    print("written", out_path, len(out), "rows")


def report(feat_path, half, config, md=None):
    df = pd.read_parquet(feat_path)
    df = df[df["config"] == config].copy()
    df["ed"] = pd.to_datetime(df["entry_ts"], utc=True).dt.tz_convert(ET).dt.date
    lo, hi = (date(2018, 9, 1), date(2024, 12, 31)) if half == "fit" else (date(2025, 1, 1), date(2026, 9, 2))
    df = df[(df["ed"] >= lo) & (df["ed"] <= hi)]
    lines = [f"# PREREGISTRATION-3 — {half.upper()} half, {config}, {len(df):,} trades ({lo} → {hi})\n"]
    trades = lambda sub: [{"entry_ts": r.entry_ts, "adjusted_pnl": r.pnl} for r in sub.itertuples()]
    feats = {"F1": "session VWAP position", "F2": "VWAP direction", "F3": "prior-day value area", "F4": "VA edge", "F5": "POC distance",
             "F6": "POC direction", "F7": "prior-session Fibonacci", "F8": "overnight Fibonacci", "F9": "EMA200 trend", "F10": "EMA20 distance",
             "F11": "EMA50 side", "F12": "opening range"}
    summary = []
    for f, name in feats.items():
        if f not in df:
            continue
        sub = df[df[f].notna()]
        g = sub.groupby(f)
        lines.append(f"\n**{f} — {name}** (n={len(sub):,})\n\n| bucket | n | WR% | mean $ | LB95 | mean stop | mean ATR |\n|---|---|---|---|---|---|---|")
        stats = {}
        for b, x in g:
            lb, _ = block_bootstrap_lb(trades(x)) if len(x) >= 2 else (None, 0)
            stats[b] = (len(x), x["pnl"].mean())
            lines.append(f"| {b} | {len(x)} | {100*(x['pnl']>0).mean():.1f} | {x['pnl'].mean():+.2f} | {lb:+.2f} | {x['stop'].mean():.1f} | {x['atr'].mean():.1f} |" if lb is not None else f"| {b} | {len(x)} | | | | | |")
        ok = {b: v for b, v in stats.items() if v[0] >= 200}
        if len(ok) >= 2:
            best = max(ok, key=lambda b: ok[b][1]); worst = min(ok, key=lambda b: ok[b][1])
            xb = sub[sub[f] == best]; xw = sub[sub[f] == worst]
            # block bootstrap of the difference of means (blocks = trading days, joint resample)
            byday = defaultdict(lambda: [[], []])
            for r in xb.itertuples(): byday[tday(datetime.fromisoformat(r.entry_ts).astimezone(ET))][0].append(r.pnl)
            for r in xw.itertuples(): byday[tday(datetime.fromisoformat(r.entry_ts).astimezone(ET))][1].append(r.pnl)
            days = list(byday); rng = np.random.Generator(np.random.PCG64(20260907)); diffs = []
            sb = np.array([sum(byday[d][0]) for d in days]); nb = np.array([len(byday[d][0]) for d in days])
            sw = np.array([sum(byday[d][1]) for d in days]); nw = np.array([len(byday[d][1]) for d in days])
            for _ in range(10000):
                ix = rng.integers(0, len(days), len(days))
                if nb[ix].sum() and nw[ix].sum():
                    diffs.append(sb[ix].sum() / nb[ix].sum() - sw[ix].sum() / nw[ix].sum())
            gap = ok[best][1] - ok[worst][1]; glb = float(np.percentile(diffs, 5))
            cand = glb > 0
            lines.append(f"\ngap best−worst: **{best}** ({ok[best][1]:+.2f}, n={ok[best][0]}) minus **{worst}** ({ok[worst][1]:+.2f}, n={ok[worst][0]}) = {gap:+.2f}, LB95 {glb:+.2f} → {'**CANDIDATE**' if cand else 'not a candidate'}")
            summary.append((f, name, best, worst, gap, glb, cand))
        else:
            lines.append("\n(fewer than two buckets with n ≥ 200 — no gap test)")
    lines.append("\n## Summary\n\n| feature | best bucket | worst bucket | gap $ | gap LB95 | candidate |\n|---|---|---|---|---|---|")
    for f, name, b, w, gap, glb, cand in summary:
        lines.append(f"| {f} {name} | {b} | {w} | {gap:+.2f} | {glb:+.2f} | {'YES' if cand else 'no'} |")
    text = "\n".join(lines); print(text)
    if md:
        open(md, "w").write(text + "\n")
        json.dump([{"feature": f, "best": b, "worst": w, "gap": gap, "gap_lb95": glb, "candidate": cand} for f, name, b, w, gap, glb, cand in summary],
                  open(md.replace(".md", ".json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=None)
    ap.add_argument("--report", choices=["fit", "test"], default=None)
    ap.add_argument("--features", default="data/features/features.parquet")
    ap.add_argument("--config", default="C1a_C3a")
    ap.add_argument("--md", default=None)
    a = ap.parse_args()
    if a.build:
        build(a.build)
    if a.report:
        report(a.features, a.report, a.config, a.md)
