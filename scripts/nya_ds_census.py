#!/usr/bin/env python3
"""NYA-DS-01 trial 1 — JadeCap Daily Sweep census per
docs/PREREG-jadecap-sweep.md. 1H swing-point raid + SFP close-back-inside,
bias-gated, confirmation-close entry, SFP-bar stop, 2R target, time exits,
first signal per day only.

    python -m scripts.nya_ds_census
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0
AM = ("09:00", "10:00", "11:00")
PM = ("13:00", "14:00", "15:00")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M")).set_index("ts").sort_index()
    B["gday"] = pd.Series((B.index + pd.Timedelta(hours=6)).date, index=B.index).astype(str)

    H1 = pd.DataFrame({
        "high": B.high.resample("1h").max(),
        "low": B.low.resample("1h").min(),
        "close": B.close.resample("1h").first().notna() * B.close.resample("1h").last(),
    }).dropna()
    H1["gday"] = pd.Series((H1.index + pd.Timedelta(hours=6)).date, index=H1.index).astype(str)
    H1["hour"] = H1.index.strftime("%H:%M")

    # daily bias: prior RTH close vs the close before
    rth_close = B[B.clock == "15:59"].groupby("gday").close.last()
    days = sorted(set(B.gday))
    bias = {}
    for i in range(2, len(days)):
        c1, c0 = rth_close.get(days[i - 1]), rth_close.get(days[i - 2])
        if c1 is not None and c0 is not None and not (pd.isna(c1) or pd.isna(c0)):
            bias[days[i]] = 1 if c1 > c0 else -1

    Hv = H1.reset_index(names="t")
    trades = []
    n_raid_days = 0
    for di in range(2, len(days)):
        d = days[di]
        if d not in bias:
            continue
        side = bias[d]  # 1 = hunt swing-low raids (longs)
        # levels from prior gday's 1H bars (confirmed fractals, untapped by 09:00 of d)
        prior = Hv[Hv.gday.isin(days[max(0, di - 2):di])].reset_index(drop=True)
        cur_mask = Hv.gday == d
        if not len(prior) or not cur_mask.any():
            continue
        mark_t = Hv[cur_mask].t.iloc[0].normalize() + pd.Timedelta(hours=9)
        levels = []
        arr = prior.reset_index(drop=True)
        for i in range(1, len(arr) - 1):
            if side > 0 and arr.low[i] < arr.low[i - 1] and arr.low[i] < arr.low[i + 1]:
                lvl, t_conf = arr.low[i], arr.t[i + 1]
            elif side < 0 and arr.high[i] > arr.high[i - 1] and arr.high[i] > arr.high[i + 1]:
                lvl, t_conf = arr.high[i], arr.t[i + 1]
            else:
                continue
            after = arr[arr.t > t_conf]
            after = after[after.t < mark_t]
            tapped = (after.low <= lvl).any() if side > 0 else (after.high >= lvl).any()
            if not tapped:
                levels.append(lvl)
        if not levels:
            continue
        # raid + SFP in the windows, first signal only
        day_bars = Hv[cur_mask]
        win = day_bars[day_bars.t.dt.strftime("%H:%M").isin(AM + PM)]
        sig = None
        for _, bar in win.iterrows():
            for lvl in levels:
                raided = bar.low < lvl if side > 0 else bar.high > lvl
                confirmed = bar.close > lvl if side > 0 else bar.close < lvl
                if raided and confirmed:
                    sig = (bar, lvl)
                    break
            if sig:
                break
        if sig is None:
            continue
        n_raid_days += 1
        bar, lvl = sig
        entry = bar.close
        stop = bar.low if side > 0 else bar.high
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        tgt = entry + side * 2 * risk
        is_am = bar.t.strftime("%H:%M") in AM
        cutoff = bar.t.normalize() + pd.Timedelta(hours=12 if is_am else 16)
        t0 = bar.t + pd.Timedelta(hours=1)
        fwd = B[(B.index >= t0) & (B.index < cutoff) & (B.gday == d)]
        pts = None
        for hi, lo, cl in fwd[["high", "low", "close"]].to_numpy():
            if side > 0:
                if lo <= stop: pts = stop - entry; break
                if hi >= tgt: pts = tgt - entry; break
            else:
                if hi >= stop: pts = entry - stop; break
                if lo <= tgt: pts = entry - tgt; break
        if pts is None:
            pts = (fwd.close.iloc[-1] - entry) * side if len(fwd) else 0.0
        trades.append(dict(day=d, year=d[:4], window="AM" if is_am else "PM",
                           pts=pts * 1.0, risk=risk,
                           pen=(lvl - bar.low) if side > 0 else (bar.high - lvl)))

    T = pd.DataFrame(trades)
    T.to_parquet(ROOT / "output/nya_ds_census.parquet", index=False)
    print(f"days with bias {len(bias)}, signal days {n_raid_days}, trades {len(T)} "
          f"(~{len(T)/max(len(bias),1)*5:.1f}/week)")
    net = T.pts - FR
    r_ = net / T.risk
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    print(f"ALL: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"${160*r_.sum():+,.0f} PF {gw/max(gl,1e-9):.2f}")
    for y, g in T.groupby("year"):
        gn = g.pts - FR
        yw, yl = gn[gn > 0].sum(), -gn[gn <= 0].sum()
        print(f"  {y}: n={len(g)} WR {(gn>0).mean():.0%} {gn.sum():+.0f}pts "
              f"${160*(gn/g.risk).sum():+,.0f} PF {yw/max(yl,1e-9):.2f}")
    for w, g in T.groupby("window"):
        gn = g.pts - FR
        ww, wl = gn[gn > 0].sum(), -gn[gn <= 0].sum()
        print(f"  {w}: n={len(g)} WR {(gn>0).mean():.0%} PF {ww/max(wl,1e-9):.2f}")


if __name__ == "__main__":
    main()
