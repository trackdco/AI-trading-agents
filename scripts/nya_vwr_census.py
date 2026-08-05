#!/usr/bin/env python3
"""NYA-VWR-01 stage 1 — UNCAPPED raw census of the Orochi VWAP-sd2 rotation
fade on RTH, per docs/PREREG-vwap-rotation.md (committed before this ran).

Band machinery adapted from scripts/nyo_rotation_respec.py (extended to
+/-2 sigma); uncapped sequential re-entry pattern from
scripts/nya_ibc_census_uncapped.py.

CAUSALITY (the thing that makes or breaks this census). The developing VWAP
at bar k includes bar k's own price and volume. Resting a limit at a band
computed WITH bar k and filling it INSIDE bar k is lookahead. So every
decision for bar k reads bands and gate state as of the close of bar k-1:
the trader stands at the close of k-1, knows the bands, rests the order,
and bar k either reaches it or does not.

FILL REALISM (VALIDATION-PROCESS §2.5). A limit fills only when price
trades THROUGH the level, never on a touch. The touch still counts as the
EVENT (the taught claim is that price "reaches" the band); the difference
between reached and filled is carried as a terminal status, so the funnel
has no silent drops (§5.12-1).

    python -m scripts.nya_vwr_census
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
FR = 1.0           # base friction, points round-turn (house convention)
FR_STRICT = 2.0    # strict-cost reporting
BASE = 160.0       # $ per 1R (house sizing base)
FIT0, FIT1 = "2025-06-02", "2026-07-15"
RTH0, RTH1 = "09:30", "16:00"
FLAT = "15:55"
CHECKPOINTS = (2, 3, 5, 8, 10, 15, 30)   # §5.12-5 grid + brief's t+15/30

# Minimum risk, applied to EVERY stop arm (prereg amendment 1, declared
# before the corrected census ran). A stop narrower than this sits inside
# the noise of a single 1-minute bar, so its R multiple is an artifact of
# a degenerate fill rather than an outcome -- the failure mode that got
# rr_floor 1.5 RETRACTED in this shop (docs/RULING-mechanical-only.md).
# 8.0 pts = the 25th percentile of RTH 1-min bar range on the fit span
# (7.5 pts, rounded up); median is 12.0. Instrument property, not a
# performance choice.
RISK_FLOOR = 8.0


# ----------------------------------------------------------------- bands
def bands(r):
    """Developing session VWAP + volume-weighted sigma (TradingView standard)."""
    tp = (r.high + r.low + r.close) / 3
    v = r.volume.clip(lower=0).astype(float)
    cv = v.cumsum().clip(lower=1)
    vwap = (tp * v).cumsum() / cv
    var = ((tp ** 2 * v).cumsum() / cv - vwap ** 2).clip(lower=0)
    return vwap.to_numpy(), np.sqrt(var).to_numpy()


def half_label(day: str) -> str:
    y, m = day[:4], int(day[5:7])
    return f"{y[2:]}H{1 if m <= 6 else 2}"


# ------------------------------------------------------- gate / regime
def gate_alive(C, up1, dn1, mode, n_accept=2, t_accept=15, start=0):
    """Acceptance beyond EITHER 1-sigma edge kills the session's gate.

    Returns a bool array: is the session still 'rotational within value' as
    of the CLOSE of each bar (so bar k reads index k-1).

    THE REGIME CLOCK STARTS AT THE WARM-UP BOUNDARY (`start`). At 09:30
    sigma is exactly 0 and the band is a single line, so every close is
    trivially 'beyond the edge'; left unguarded, two such closes kill the
    gate before the strategy is eligible to trade and the census returns
    n=0 on every session. This is his own warning made mechanical -- "the
    bracket's really small, it's a bit less usable at that point".
    """
    n = len(C)
    alive = np.ones(n, dtype=bool)
    run_up = run_dn = 0
    cum_out = 0
    dead = False
    for k in range(n):
        if k < start:
            continue
        if dead:
            alive[k] = False
            continue
        above, below = C[k] > up1[k], C[k] < dn1[k]
        run_up = run_up + 1 if above else 0
        run_dn = run_dn + 1 if below else 0
        cum_out = cum_out + 1 if (above or below) else cum_out
        if mode in ("G1", "G2"):
            if run_up >= n_accept or run_dn >= n_accept:
                dead = True
        elif mode == "G3":
            if cum_out >= t_accept:
                dead = True
        alive[k] = not dead
    return alive


def inside_and_both_sides(C, vwap, up1, dn1, start=0):
    """G4 classifier: currently inside +/-1 sigma AND has traded both sides
    of VWAP this session (as of each bar's close). Same warm-up rule."""
    n = len(C)
    seen_up = seen_dn = False
    out = np.zeros(n, dtype=bool)
    for k in range(n):
        if k < start:
            continue
        if C[k] > vwap[k]:
            seen_up = True
        elif C[k] < vwap[k]:
            seen_dn = True
        out[k] = (dn1[k] <= C[k] <= up1[k]) and seen_up and seen_dn
    return out


# ------------------------------------------------------------- the sim
def resolve(side, entry, stop, k0, H, L, C, vwap, up1, dn1, target, developing):
    """Walk forward from bar k0+1. Stop is checked before target within a
    bar (pessimistic). Returns (pts, exit_idx, reason)."""
    risk = abs(entry - stop)
    for j in range(k0 + 1, len(C)):
        # stop first
        if (side < 0 and H[j] >= stop) or (side > 0 and L[j] <= stop):
            return -risk, j, "stop"
        # target: developing reads the level as of j-1 (causal resting limit)
        ref = j - 1 if developing else k0
        if target == "T1":
            lvl = vwap[ref]
        else:  # T2 — opposite 1-sigma edge
            lvl = dn1[ref] if side < 0 else up1[ref]
        # limit fills only on trading THROUGH the level
        if (side < 0 and L[j] < lvl) or (side > 0 and H[j] > lvl):
            pts = abs(lvl - entry) * (1 if (side < 0) == (lvl < entry) else -1)
            # the developing mean can rise to meet a short (or fall to meet a
            # long): price and mean still converged, but the exit books a
            # loss. Labelled separately so it is visible, not buried in
            # "target".
            return pts, j, ("target" if pts >= 0 else "mean_cross")
    return side * (C[-1] - entry), len(C) - 1, "time"


def run_session(r, day, cfg):
    """One RTH session -> list of trade dicts under one arm config."""
    r = r.sort_values("ts").reset_index(drop=True)
    if len(r) < 200:
        return []
    H, L, C = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy()
    clock = r.clock.to_numpy()
    vwap, sd = bands(r)
    up1, dn1 = vwap + sd, vwap - sd
    up2, dn2 = vwap + 2 * sd, vwap - 2 * sd

    warm = cfg["warmup"]
    wi = int(np.argmax(clock >= warm)) if (clock >= warm).any() else len(r)

    if cfg["gate"] == "G4":
        alive = inside_and_both_sides(C, vwap, up1, dn1, start=wi)
    elif cfg["gate"] == "G5":
        slope = pd.Series(vwap).diff(15).to_numpy()
        alive = gate_alive(C, up1, dn1, "G1", 2, start=wi) & (
            np.abs(np.nan_to_num(slope)) < cfg["slope_max"])
    else:
        alive = gate_alive(C, up1, dn1, cfg["gate"], start=wi,
                           n_accept=3 if cfg["gate"] == "G2" else 2)

    slope15 = pd.Series(vwap).diff(15).to_numpy()
    out, k, seq = [], 1, 0
    tap = {-1: 0, 1: 0}
    while k < len(r):
        if clock[k] < warm or clock[k] >= FLAT:
            k += 1
            continue
        # everything decided for bar k reads k-1
        p = k - 1
        if not alive[p]:
            k += 1
            continue
        lvl_up, lvl_dn = up2[p], dn2[p]
        side = -1 if H[k] >= lvl_up else (1 if L[k] <= lvl_dn else 0)
        if not side:
            k += 1
            continue
        lvl = lvl_up if side < 0 else lvl_dn
        tap[side] += 1
        seq += 1
        rec = dict(
            day=day, year=day[:4], half=half_label(day), arm=cfg["name"],
            side=side, clock=clock[k], seq=seq, tap_n=tap[side],
            band_w_pts=float(2 * sd[p]),
            sd2_dist_sigma=float(abs((H[k] if side < 0 else L[k]) - vwap[p]) / max(sd[p], 1e-9)),
            vwap_slope15=float(np.nan_to_num(slope15[p])),
            gap_pts=float(r.gap_pts.iloc[0]),
        )

        # ---- entry arm
        ent = cfg["entry"]
        through = (H[k] > lvl) if side < 0 else (L[k] < lvl)
        if ent == "E-a":
            if not through:
                rec.update(status="cancelled_no_through"); out.append(rec); k += 1; continue
            entry, k_ent = lvl, k
        elif ent == "E-b":
            # wick beyond sd2 + close back inside sd2, entry at that close
            if not ((side < 0 and C[k] < lvl) or (side > 0 and C[k] > lvl)):
                rec.update(status="vetoed_no_close_back_inside"); out.append(rec); k += 1; continue
            entry, k_ent = C[k], k
        elif ent == "E-c":
            # his sweep-case literal: entry only on re-entry into the 1-sigma band
            j = k + 1
            k_ent = None
            while j < len(r) and clock[j] < FLAT:
                if dn1[j] <= C[j] <= up1[j]:
                    k_ent = j; break
                j += 1
            if k_ent is None:
                rec.update(status="cancelled_no_reentry"); out.append(rec); k += 1; continue
            entry = C[k_ent]
        else:  # E-d — SPEC 3 two-tranche grammar, handled separately
            entry, k_ent = lvl, k

        # ---- stop arm (all capped; stop is OUR invention, never taught)
        cap = cfg["cap"]
        if cfg["stop"] == "S1":
            raw = abs((H[k] if side < 0 else L[k]) - entry) + 1.0
        elif cfg["stop"] == "S2":
            raw = abs(lvl - entry) + 0.5 * sd[p]
        else:
            raw = cap
        risk = float(min(max(raw, RISK_FLOOR), cap))
        stop = entry - side * risk

        if ent == "E-d":
            trades = spec3(side, k, entry, stop, risk, H, L, C, clock,
                           vwap, up1, dn1, sd, cfg)
            if trades is None:
                rec.update(status="cancelled_no_retest"); out.append(rec); k += 1; continue
            net_r, jx, reason, mfe, mae, ck = trades
        else:
            pts, jx, reason = resolve(side, entry, stop, k_ent, H, L, C,
                                      vwap, up1, dn1, cfg["target"], cfg["developing"])
            net_r = (pts - FR) / risk
            mfe, mae, ck = excursions(side, entry, risk, k_ent, jx, H, L, C)

        rec.update(status="filled", entry=float(entry), stop=float(stop),
                   risk_pts=risk, exit_reason=reason,
                   net_r=float(net_r),
                   net_r_strict=float(net_r - (FR_STRICT - FR) / risk),
                   mfe_r=mfe, mae_r=mae, **ck)
        out.append(rec)
        k = jx + 1          # uncapped: resume scanning after resolution
    return out


def excursions(side, entry, risk, k0, jx, H, L, C):
    """MFE/MAE in R plus the §5.12-5 time-segment checkpoints."""
    hi = H[k0 + 1:jx + 1]; lo = L[k0 + 1:jx + 1]
    if not len(hi):
        mfe = mae = 0.0
    else:
        fav = (hi.max() - entry) if side > 0 else (entry - lo.min())
        adv = (entry - lo.min()) if side > 0 else (hi.max() - entry)
        mfe, mae = float(fav / risk), float(-adv / risk)
    ck = {}
    for t in CHECKPOINTS:
        idx = min(k0 + t, len(C) - 1)
        ck[f"r_t{t}"] = float(side * (C[idx] - entry) / risk)
    return mfe, mae, ck


def spec3(side, k, entry1, stop, risk, H, L, C, clock, vwap, up1, dn1, sd, cfg):
    """SPEC 3 grammar: 1/3 risk on the RETEST of the extreme, remaining 2/3
    on acceptance-back-inside after a shallow (<0.5 sigma) poke back out.
    Target for both tranches: the opposite 1-sigma edge (his stated 'final
    TP is value area low of DVA'). Stop shared."""
    lvl = entry1
    # phase 1: price must pull AWAY from the band (a close back inside sd2)
    j = k + 1
    while j < len(C) and clock[j] < FLAT:
        if (side < 0 and C[j] < lvl - 0.25 * sd[j]) or (side > 0 and C[j] > lvl + 0.25 * sd[j]):
            break
        j += 1
    else:
        return None
    if j >= len(C):
        return None
    # phase 2: the RETEST — second approach back to the band
    t = j + 1
    while t < len(C) and clock[t] < FLAT:
        if (side < 0 and H[t] >= lvl) or (side > 0 and L[t] <= lvl):
            break
        t += 1
    else:
        return None
    if t >= len(C):
        return None
    e1, k1 = lvl, t
    # tranche 1 resolves against the shared stop / opposite edge target
    pts1, jx1, why1 = resolve(side, e1, stop, k1, H, L, C, vwap, up1, dn1,
                              "T2", cfg["developing"])
    # phase 3: the ADD — acceptance back inside 1 sigma, shallow poke out, back in
    add = None
    a = k1 + 1
    accepted = False
    while a < min(jx1 + 1, len(C)) and clock[a] < FLAT:
        inside = dn1[a] <= C[a] <= up1[a]
        if inside and not accepted:
            accepted = True
        elif accepted and not inside:
            excursion = (C[a] - up1[a]) if C[a] > up1[a] else (dn1[a] - C[a])
            if excursion > 0.5 * sd[a]:
                accepted = False          # not "slightly" — grammar broken
        elif accepted and inside and a > k1 + 1:
            add = a
            break
        a += 1
    r1 = (pts1 - FR) / risk
    if add is None:
        net = (1 / 3) * r1
        mfe, mae, ck = excursions(side, e1, risk, k1, jx1, H, L, C)
        return net, jx1, why1 + "_notrancheB", mfe, mae, ck
    e2 = C[add]
    risk2 = max(abs(e2 - stop), 2.0)
    pts2, jx2, why2 = resolve(side, e2, stop, add, H, L, C, vwap, up1, dn1,
                              "T2", cfg["developing"])
    r2 = (pts2 - FR) / risk2
    net = (1 / 3) * r1 + (2 / 3) * r2
    jx = max(jx1, jx2)
    mfe, mae, ck = excursions(side, e1, risk, k1, jx, H, L, C)
    return net, jx, f"{why1}+{why2}", mfe, mae, ck


# ------------------------------------------------------------- reporting
def card(df, label, per_half=True):
    if not len(df):
        print(f"  {label:26s} n=0")
        return
    f = df[df.status == "filled"]
    if not len(f):
        print(f"  {label:26s} events={len(df)} filled=0")
        return
    r = f.net_r
    gw, gl = r[r > 0].sum(), -r[r <= 0].sum()
    print(f"  {label:26s} events={len(df):4d} filled={len(f):4d} "
          f"WR {(r>0).mean():5.1%} {f.pts_net.sum():+8.0f}pts "
          f"${BASE*r.sum():+9,.0f} PF {gw/max(gl,1e-9):5.2f} mean {r.mean():+.3f}R")
    if per_half:
        for h, g in f.groupby("half"):
            gr = g.net_r
            gwh, glh = gr[gr > 0].sum(), -gr[gr <= 0].sum()
            print(f"       {h}: n={len(g):3d} WR {(gr>0).mean():5.1%} "
                  f"${BASE*gr.sum():+8,.0f} PF {gwh/max(glh,1e-9):5.2f}")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["day"] = B.ts.dt.date.astype(str)
    R = B[(B.clock >= RTH0) & (B.clock < RTH1)].copy()

    # overnight gap context: 09:30 open vs prior RTH close
    firsts = R.groupby("day").first()
    lasts = R.groupby("day").last()
    gap = (firsts.open - lasts.close.shift(1)).rename("gap_pts")
    R = R.merge(gap, left_on="day", right_index=True, how="left")
    R["gap_pts"] = R.gap_pts.fillna(0.0)

    days = [d for d in sorted(R.day.unique()) if FIT0 <= d <= FIT1]
    print(f"NYA-VWR-01 stage 1 — uncapped raw census")
    print(f"span {FIT0} -> {FIT1} | {len(days)} RTH sessions | "
          f"prereg docs/PREREG-vwap-rotation.md\n")

    default = dict(name="DEFAULT E-a/S1cap20/T1/dev/G1/09:30/15m",
                   entry="E-a", stop="S1", cap=20.0, target="T1",
                   developing=True, gate="G1", warmup="09:45", slope_max=3.0)
    arms = [default]
    for e in ("E-b", "E-c", "E-d"):
        arms.append({**default, "name": f"entry {e}", "entry": e})
    for s, c in (("S2", 20.0), ("S3", 20.0), ("S4", 30.0)):
        arms.append({**default, "name": f"stop {s}cap{int(c)}", "stop": s, "cap": c})
    arms.append({**default, "name": "target T2 (far edge)", "target": "T2"})
    arms.append({**default, "name": "target T1 frozen", "developing": False})
    for g in ("G2", "G3", "G4", "G5"):
        arms.append({**default, "name": f"gate {g}", "gate": g})
    arms.append({**default, "name": "warm-up 10min", "warmup": "09:40"})

    sessions = {d: g for d, g in R[R.day.isin(days)].groupby("day")}
    allrows = []
    for cfg in arms:
        rows = []
        for d in days:
            rows.extend(run_session(sessions[d], d, cfg))
        df = pd.DataFrame(rows)
        if len(df):
            df["pts_net"] = df.net_r * df.risk_pts
            allrows.append(df)
        print(f"\n--- {cfg['name']}")
        card(df, "raw", per_half=(cfg is default))

    E = pd.concat(allrows, ignore_index=True)
    E.to_parquet(ROOT / "output/nya_vwr_events.parquet", index=False)

    d = E[E.arm == default["name"]]
    print("\n" + "=" * 72)
    print("DEFAULT ARM — funnel view (§5.12-1 terminal statuses, no silent drops)")
    print(d.status.value_counts().to_string())
    f = d[d.status == "filled"]
    print(f"\nfrequency: {len(d)/len(days):.2f} events/session, "
          f"{len(f)/len(days):.2f} fills/session")
    print(f"taps: {d.tap_n.value_counts().sort_index().head(6).to_dict()}")
    if len(f):
        print(f"strict cost (2pt): ${BASE*f.net_r_strict.sum():+,.0f} "
              f"PF {f.net_r_strict[f.net_r_strict>0].sum()/max(-f.net_r_strict[f.net_r_strict<=0].sum(),1e-9):.2f}")
        print(f"MFE median {f.mfe_r.median():+.2f}R | MAE median {f.mae_r.median():+.2f}R")
        print("checkpoints (mean R): " +
              " ".join(f"t+{t}={f[f'r_t{t}'].mean():+.3f}" for t in CHECKPOINTS))
        print("\nby year:")
        for y, g in f.groupby("year"):
            gr = g.net_r
            print(f"  {y}: n={len(g)} WR {(gr>0).mean():.1%} ${BASE*gr.sum():+,.0f} "
                  f"PF {gr[gr>0].sum()/max(-gr[gr<=0].sum(),1e-9):.2f}")
    print(f"\nevents -> output/nya_vwr_events.parquet ({len(E)} rows, {E.arm.nunique()} arms)")


if __name__ == "__main__":
    main()
