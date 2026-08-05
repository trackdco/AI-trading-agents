#!/usr/bin/env python3
"""NYA-FA-01 hours-clock re-census — the taught failed auction (RESPEC
Spec 6, prereg amendment 2026-08-05). 30-min Globex bars; break freezes the
live composite; episode tracked outside value with the structure bundle;
trigger = re-entry close(s); trade to the opposite frozen edge, stop beyond
the extension extreme, 5-day cap.

    python -m scripts.nya_fa_hoursclock
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0
MIN_OUT, VOID_OUT, CAP_FWD = 8, 72, 240


def rep(T, label):
    if not len(T):
        print(f"  {label}: n=0"); return
    net = T.pts - FR
    r_ = net / T.risk
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    print(f"  {label}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"${160*r_.sum():+,.0f} PF {gw/max(gl,1e-9):.2f}")
    for y, g in T.groupby("year"):
        gn = g.pts - FR
        yw, yl = gn[gn > 0].sum(), -gn[gn <= 0].sum()
        print(f"     {y}: n={len(g)} WR {(gn>0).mean():.0%} {gn.sum():+.0f}pts "
              f"PF {yw/max(yl,1e-9):.2f}")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts).set_index("ts").sort_index()
    b30 = pd.DataFrame({
        "open": B.open.resample("30min").first(),
        "high": B.high.resample("30min").max(),
        "low": B.low.resample("30min").min(),
        "close": B.close.resample("30min").last(),
    }).dropna()
    b30["gday"] = (b30.index + pd.Timedelta(hours=6)).date.astype("str") \
        if hasattr((b30.index + pd.Timedelta(hours=6)), "date") else None
    b30["gday"] = pd.Series((b30.index + pd.Timedelta(hours=6)).date, index=b30.index).astype(str)
    C = pd.read_parquet(ROOT / "output/nya_composites.parquet").set_index("day")
    live = {d: (float(C.loc[d, "comp_vah"]), float(C.loc[d, "comp_val"]))
            for d in C.index if C.loc[d, "comp_age"] >= 2}

    H, L, Cl = b30.high.to_numpy(), b30.low.to_numpy(), b30.close.to_numpy()
    G = b30.gday.to_numpy()
    n = len(b30)

    episodes = []
    ep = None
    prev_inside = False
    for k in range(n):
        c, h, l = Cl[k], H[k], L[k]
        if ep is None:
            lv = live.get(G[k])
            if lv is None:
                prev_inside = False
                continue
            vah, val = lv
            inside = val <= c <= vah
            if prev_inside and not inside:
                side = 1 if c < val else -1  # side = direction of the FAIL trade
                ep = dict(k0=k, side=side, vah=vah, val=val, ext=(l if side > 0 else h),
                          touches_far=0, touches_near=0, last_ext_k=k, exts=[],
                          swept=False, closes_in=0)
            prev_inside = inside
        else:
            side, vah, val = ep["side"], ep["vah"], ep["val"]
            edge = val if side > 0 else vah
            width = vah - val
            out_bars = k - ep["k0"]
            if out_bars > VOID_OUT:
                ep = None
                prev_inside = val <= c <= vah
                continue
            # extension tracking (down-break: ext = running low)
            if side > 0:
                if l < ep["ext"] - 1e-9:
                    if abs(l - ep["ext"]) <= 0.1 * width:
                        ep["exts"].append(l)
                    else:
                        ep["exts"] = [l]
                    ep["ext"], ep["last_ext_k"] = l, k
                rng_hi = max(H[max(ep["k0"], k - 8):k]) if k > ep["k0"] else h
                if out_bars > 4 and h > rng_hi:
                    ep["swept"] = True
                if h >= edge: ep["touches_near"] += 1
                if out_bars > 4 and l <= ep["ext"] + 0.1 * width: ep["touches_far"] += 1
            else:
                if h > ep["ext"] + 1e-9:
                    if abs(h - ep["ext"]) <= 0.1 * width:
                        ep["exts"].append(h)
                    else:
                        ep["exts"] = [h]
                    ep["ext"], ep["last_ext_k"] = h, k
                rng_lo = min(L[max(ep["k0"], k - 8):k]) if k > ep["k0"] else l
                if out_bars > 4 and l < rng_lo:
                    ep["swept"] = True
                if l <= edge: ep["touches_near"] += 1
                if out_bars > 4 and h >= ep["ext"] - 0.1 * width: ep["touches_far"] += 1
            # re-entry close
            back = (c > val) if side > 0 else (c < vah)
            if back:
                ep["closes_in"] += 1
            else:
                ep["closes_in"] = 0
            if ep["closes_in"] >= 1:
                d = G[k]
                rec = dict(day=d, year=d[:4], side=side, out_bars=out_bars,
                           entry=c, ext=ep["ext"], vah=vah, val=val,
                           entry_t=b30.index[k] + pd.Timedelta(minutes=30),
                           balance=int(ep["touches_near"] >= 2 and ep["touches_far"] >= 2),
                           rounding=int(k - ep["last_ext_k"] >= 8),
                           poor=int(len(ep["exts"]) >= 2), squeeze=int(ep["swept"]),
                           k=k)
                # trade sim: stop beyond extension, target opposite edge
                stop = ep["ext"]
                tgt = vah if side > 0 else val
                pts = None
                for j in range(k + 1, min(k + CAP_FWD, n)):
                    if side > 0:
                        if L[j] <= stop: pts = stop - c; break
                        if H[j] >= tgt: pts = tgt - c; break
                    else:
                        if H[j] >= stop: pts = c - stop; break
                        if L[j] <= tgt: pts = c - tgt; break
                if pts is None:
                    j = min(k + CAP_FWD, n - 1)
                    pts = (Cl[j] - c) * side
                rec["pts"] = pts
                rec["risk"] = max(abs(c - stop), 1e-9)
                episodes.append(rec)
                ep = None
                prev_inside = True

    E = pd.DataFrame(episodes)
    E.to_parquet(ROOT / "output/nya_fa_hoursclock.parquet", index=False)
    fast = E[E.out_bars < MIN_OUT]
    slow = E[E.out_bars >= MIN_OUT]
    print(f"episodes resolving to re-entry: {len(E)} "
          f"(fast <4h: {len(fast)}, taught-scale >=4h: {len(slow)})")
    wks = len(set(E.day.str[:7])) * 4.33
    print(f"taught-scale frequency: {len(slow)/ (len(set(E.day.str[:4]))*52):.2f}/week-ish "
          f"vs his 1-2/week")
    rep(fast, "FAST clock (<4h outside — the population we originally tested)")
    rep(slow, "TAUGHT clock (>=4h outside)")
    for lo, lbl in ((24, ">=12h outside"), (48, ">=1 day outside")):
        rep(E[E.out_bars >= lo], lbl)
    print("\n-- structure bundle on taught-scale (>=4h) --")
    for f in ("balance", "rounding", "poor", "squeeze"):
        rep(slow[slow[f] == 1], f"{f}=1")
    bundle = slow[(slow["balance"] == 1) & ((slow["poor"] + slow["squeeze"]) >= 1)]
    rep(bundle, "FULL BUNDLE (balance + poor-or-squeeze)")


if __name__ == "__main__":
    main()
