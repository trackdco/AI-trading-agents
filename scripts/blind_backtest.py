#!/usr/bin/env python3
"""Clean-room implementation of /tmp/blind/SPEC.md (NQ value-area retest strategy)."""
import json
import math
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

TZ = "America/New_York"
BARS = "/tmp/blind/nq_1m.parquet"
NEWS = "/tmp/blind/news_archive.csv"
OUT_TRADES = "/tmp/blind/trades.jsonl"
OUT_SUMMARY = "/tmp/blind/summary.txt"

H = 3_600_000_000_000  # ns per hour
MIN = 60_000_000_000   # ns per minute


def first_true(mask, offset=0, default=None):
    """Index (in absolute terms) of first True in mask, else default."""
    if mask.size == 0:
        return default
    i = int(np.argmax(mask))
    if mask[i]:
        return i + offset
    return default


def compute_levels(lo_arr, hi_arr, vol_arr):
    """Volume profile with 1.0-point bins; returns (VAL, VAH) or None."""
    fl = np.floor(lo_arr).astype(np.int64)
    fh = np.floor(hi_arr).astype(np.int64)
    bmin = int(fl.min())
    bmax = int(fh.max())
    nb = bmax - bmin + 1
    k = (fh - fl + 1).astype(np.float64)
    per = vol_arr.astype(np.float64) / k
    diff = np.zeros(nb + 1, dtype=np.float64)
    np.add.at(diff, fl - bmin, per)
    np.add.at(diff, fh - bmin + 1, -per)
    prof = np.cumsum(diff)[:nb]
    total = prof.sum()
    if not np.isfinite(total) or total <= 0:
        return None
    poc = int(np.argmax(prof))  # lowest index on tie
    lo = hi = poc
    top = nb - 1
    bottom = 0
    cum = prof[poc]
    thresh = 0.70 * total
    while cum < thresh:
        up = float(prof[hi + 1:hi + 3].sum()) if hi < top else -1.0
        dn = float(prof[max(lo - 2, bottom):lo].sum()) if lo > bottom else -1.0
        if up >= dn and hi < top:
            nh = min(hi + 2, top)
            cum += prof[hi + 1:nh + 1].sum()
            hi = nh
        elif lo > bottom:
            nl = max(lo - 2, bottom)
            cum += prof[nl:lo].sum()
            lo = nl
        else:
            break
    val = (lo + bmin) * 1.0
    vah = (hi + bmin + 1) * 1.0
    val = round(val * 4.0) / 4.0
    vah = round(vah * 4.0) / 4.0
    if not (math.isfinite(val) and math.isfinite(vah)):
        return None
    return val, vah


def main():
    df = pd.read_parquet(BARS)
    df = df.sort_values("ts_event").reset_index(drop=True)
    ts_series = df["ts_event"]
    if ts_series.dt.tz is None:
        ts_series = ts_series.dt.tz_localize(TZ)
    else:
        ts_series = ts_series.dt.tz_convert(TZ)
    TS = ts_series.values.astype("datetime64[ns]").astype(np.int64)  # UTC epoch ns
    O = df["open"].to_numpy(np.float64)
    HI = df["high"].to_numpy(np.float64)
    LO = df["low"].to_numpy(np.float64)
    C = df["close"].to_numpy(np.float64)
    V = df["volume"].to_numpy(np.float64)

    # News days
    news = pd.read_csv(NEWS, dtype=str)
    news["impact"] = news["impact"].str.strip()
    news["time_et"] = news["time_et"].str.strip()
    m = (news["impact"] == "high") & (news["time_et"] >= "08:00") & (news["time_et"] < "09:30")
    news_days = set(pd.to_datetime(news.loc[m, "date"]).dt.date)

    # Session-days
    sess_dates = sorted(set((ts_series - pd.Timedelta(hours=18)).dt.date))
    t0s = [pd.Timestamp(f"{d} 18:00").tz_localize(TZ) for d in sess_dates]
    t0ns = np.array([t.value for t in t0s], dtype=np.int64)

    trades = []
    ambiguities = []

    for si in range(len(sess_dates)):
        if si == 0:
            continue
        D = sess_dates[si]
        t0 = t0ns[si]
        prior_t0 = t0ns[si - 1]
        p_a = int(np.searchsorted(TS, prior_t0, side="left"))
        p_b = int(np.searchsorted(TS, t0, side="left"))
        if p_b - p_a < 300:
            continue
        s_a = p_b
        s_b = int(np.searchsorted(TS, t0 + 23 * H, side="left"))
        n = s_b - s_a
        if n < 600:
            continue

        lv = compute_levels(LO[p_a:p_b], HI[p_a:p_b], V[p_a:p_b])
        if lv is None:
            continue
        VAL, VAH = lv

        ts = TS[s_a:s_b]
        o = O[s_a:s_b]
        h = HI[s_a:s_b]
        l = LO[s_a:s_b]
        c = C[s_a:s_b]

        # ---- signal candles ----
        hrs = (ts - t0) / H
        fmask = (hrs >= 0.9633) & ((hrs + 1.0 / 60.0) <= 21.9167)
        fidx = np.nonzero(fmask)[0]
        sig_by_time = {}
        sig_order = []
        for j in range(1, len(fidx)):
            i = fidx[j]
            ip = fidx[j - 1]
            cp = c[ip]
            ci = c[i]
            cands = []
            for L in (VAH, VAL):
                if cp <= L and ci >= L + 3.0:
                    cands.append((+1, L))
                if cp >= L and ci <= L - 3.0:
                    cands.append((-1, L))
            if not cands:
                continue
            t_sig = int(ts[i] + MIN)
            # nearest level to close[i]; ties -> first in (VAH, VAL) order
            best = None
            for d, L in cands:
                dist = abs(L - ci)
                if best is None or dist < best[0]:
                    best = (dist, d, L)
            _, d, L = best
            sig = dict(t=t_sig, d=d, L=L, o=o[i], h=h[i], l=l[i], c=ci, ph=h[ip], pl=l[ip])
            if t_sig not in sig_by_time:
                sig_order.append(t_sig)
            sig_by_time[t_sig] = sig
        sigs = [sig_by_time[t] for t in sorted(sig_order)]
        if not sigs:
            continue

        # precompute start indices
        for s in sigs:
            s["start"] = int(np.searchsorted(ts, s["t"], side="left"))
            # stop
            d, L = s["d"], s["L"]
            if d > 0:
                ref = s["l"]
                if abs(s["o"] - L) < 5.0:
                    ref = min(s["l"], s["pl"])
                stop = ref - 0.25
                if L - stop < 5.0:
                    stop = L - 5.0
            else:
                ref = s["h"]
                if abs(s["o"] - L) < 5.0:
                    ref = max(s["h"], s["ph"])
                stop = ref + 0.25
                if stop - L < 5.0:
                    stop = L + 5.0
            s["stop"] = stop
            s["risk"] = abs(L - stop)

        idx_1600 = int(np.searchsorted(ts, t0 + 22 * H, side="left"))
        news_day = (pd.Timestamp(t0 + 15 * H, tz="UTC").tz_convert(TZ).date() in news_days)
        if news_day:
            blk_a = int(np.searchsorted(ts, t0 + 14 * H, side="left"))
            blk_b = int(np.searchsorted(ts, int(t0 + 15.5 * H), side="left"))
        else:
            blk_a = blk_b = None

        t_free = t0 - 24 * H
        nsig = len(sigs)
        for k, s in enumerate(sigs):
            d, L, risk, stop = s["d"], s["L"], s["risk"], s["stop"]
            if s["t"] <= t_free:
                continue
            if risk > 30.0:
                continue
            start = s["start"]
            cancel = n
            if k + 1 < nsig:
                cancel = min(cancel, sigs[k + 1]["start"])
            cancel = min(cancel, idx_1600)
            if news_day:
                if blk_a <= start < blk_b:
                    continue
                if start < blk_a:
                    cancel = min(cancel, blk_a)
            # arming
            si0 = max(start - 1, 0)
            if si0 >= cancel:
                continue
            thr = L + d * 1.0 * risk
            if d > 0:
                a = first_true(h[si0:cancel] >= thr, si0)
            else:
                a = first_true(l[si0:cancel] <= thr, si0)
            if a is None:
                continue
            live = a + 1
            if live >= cancel:
                continue
            # fill
            if d > 0:
                f = first_true(l[live:cancel] <= L - 0.25, live)
            else:
                f = first_true(h[live:cancel] >= L + 0.25, live)
            if f is None:
                continue
            E = L
            target = E + d * risk
            if d > 0:
                s_idx = first_true(l[f:] <= stop, f, n)
                t_idx = first_true(h[f:] >= target, f, n)
            else:
                s_idx = first_true(h[f:] >= stop, f, n)
                t_idx = first_true(l[f:] <= target, f, n)
            # SAR
            sar_idx = None
            sar_px = None
            for s2 in sigs[k + 1:]:
                if s2["d"] == -d and s2["t"] > ts[f]:
                    sar_idx = int(np.searchsorted(ts, s2["t"], side="left"))
                    sar_px = s2["c"]
                    break
            if sar_idx is not None and sar_idx <= min(s_idx, t_idx) and sar_idx <= n:
                ex = min(sar_idx, n - 1)
                r = d * (sar_px - E) / risk
                res = "SAR"
                t_free = int(ts[ex]) - 1
            elif s_idx <= t_idx and s_idx < n:
                ex = s_idx
                r = -1.0
                res = "STOP"
                t_free = int(ts[ex])
            elif t_idx < s_idx:
                ex = t_idx
                r = 1.0
                res = "TARGET"
                t_free = int(ts[ex])
            else:
                ex = n - 1
                r = d * (c[n - 1] - E) / risk
                res = "FLAT"
                t_free = int(ts[ex])
            trades.append(dict(
                day=str(D), dir=int(d), level=float(L),
                t_sig=pd.Timestamp(s["t"], tz="UTC").tz_convert(TZ).isoformat(),
                t_fill=pd.Timestamp(int(ts[f]), tz="UTC").tz_convert(TZ).isoformat(),
                entry=float(E), stop=float(stop), risk=float(risk),
                res=res, r=float(r),
                t_exit=pd.Timestamp(int(ts[ex]), tz="UTC").tz_convert(TZ).isoformat(),
                _tsig_ns=s["t"], _tfill_ns=int(ts[f]), _texit_ns=int(ts[ex]),
            ))

    # ---- sanity checks ----
    problems = []
    n_fill_at_sig = 0
    last_by_day = {}
    for t in trades:
        if not (t["_tsig_ns"] <= t["_tfill_ns"] <= t["_texit_ns"]):
            problems.append(f"time order {t}")
        if t["_tsig_ns"] == t["_tfill_ns"]:
            n_fill_at_sig += 1
        if not (5.0 <= t["risk"] <= 30.0):
            problems.append(f"risk range {t}")
        if t["res"] in ("STOP", "TARGET") and not (-1.0 <= t["r"] <= 1.0):
            problems.append(f"r range {t}")
        prev = last_by_day.get(t["day"])
        if prev is not None and t["_tfill_ns"] < prev:
            problems.append(f"overlap {t}")
        last_by_day[t["day"]] = t["_texit_ns"]
    if problems:
        print("SANITY PROBLEMS:", len(problems))
        for p in problems[:20]:
            print(p)

    with open(OUT_TRADES, "w") as fh:
        for t in trades:
            out = {k: v for k, v in t.items() if not k.startswith("_")}
            fh.write(json.dumps(out) + "\n")

    # ---- summary ----
    ntr = len(trades)
    days_traded = len(set(t["day"] for t in trades))
    cnt = Counter(t["res"] for t in trades)
    net = [t["r"] - 0.5 / t["risk"] for t in trades]
    wins = cnt.get("TARGET", 0)
    losses = cnt.get("STOP", 0)
    wr = wins / (wins + losses) if (wins + losses) else float("nan")
    per_year = defaultdict(lambda: [0, 0.0])
    for t, nr in zip(trades, net):
        y = t["day"][:4]
        per_year[y][0] += 1
        per_year[y][1] += nr
    lines = []
    lines.append("NQ VALUE-AREA RETEST — CLEAN-ROOM BACKTEST SUMMARY")
    lines.append(f"session-days traded: {days_traded}")
    lines.append(f"trades: {ntr}")
    lines.append(f"win rate (TARGET/(TARGET+STOP)): {wr:.4f}")
    lines.append(f"mean net_r: {np.mean(net) if ntr else float('nan'):.4f}")
    lines.append(f"total net_r: {sum(net):.2f}")
    lines.append("count by res: " + ", ".join(f"{k}={cnt[k]}" for k in ("TARGET", "STOP", "SAR", "FLAT")))
    lines.append("per-year: trades / total net_r")
    for y in sorted(per_year):
        lines.append(f"  {y}: {per_year[y][0]} / {per_year[y][1]:.2f}")
    lines.append(f"sanity problems: {len(problems)}")
    lines.append(f"trades whose fill bar starts exactly at the signal time (t_fill == t_sig): {n_fill_at_sig}")
    lines.append("")
    lines.append("AMBIGUITIES")
    lines.append("- Session bounds t0+23h / t0+22h / t0+14h / t0+15.5h are absolute durations added to the wall-clock 18:00 ET of the session-day (no session spans a DST switch, so this matches wall-clock reading).")
    lines.append("- 'top'/'bottom' bins of the volume profile are taken as the highest/lowest bins touched by any prior-session bar (min floor(low) .. max floor(high)).")
    lines.append("- 'Same end time' signal dedup: nearest level to close[i]; an exact-distance tie keeps the first candidate in (VAH, VAL) order.")
    lines.append("- 'Previous bar i-1' is the previous element of the hour-filtered list (identical to the previous session bar except across data gaps).")
    lines.append("- The NEXT signal used for cancel, and the opposing signals used for SAR, are taken from the full signal list regardless of whether those signals were themselves skipped (occupancy, news, risk>30, unarmed).")
    lines.append("- t_free is initialised to t0 - 24h; per-year figures are grouped by the session-day's year.")
    lines.append("- t_fill == t_sig is allowed: the spec arms on the signal candle itself (si0 = start-1), so live = start and the fill can occur on the bar that starts at the signal time. The strict t_sig < t_fill check was relaxed to t_sig <= t_fill rather than altering the rule.")
    lines.append("- If VAH == VAL (degenerate profile) both levels are still tested; duplicate signals at one time collapse via the nearest-level rule.")
    with open(OUT_SUMMARY, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
