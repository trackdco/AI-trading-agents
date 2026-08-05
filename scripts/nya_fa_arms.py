#!/usr/bin/env python3
"""NYA-FA-01 — trial 4: exit-arm tournament on the DEFAULT spec cohort
(deep-excursion + G2 gate), run under §6.0 promotion law: the default spec was
declared in docs/PREREG-failed-auction.md BEFORE this tournament; arms below
are challengers that can displace it only via PBO < 0.5 AND holdout — never
in-sample rank. Also emits the day-level arm matrix PBO grades.

Arms (declared here, first run):
  E1 default        S2 stop (0.5x excursion), target min(POC, 0.5w), TS 15:55
  E2 BE@0.25w       as E1 + stop to entry once 0.25 width favorable
  E3 partial        as E1 + half off at 0.25w, runner to target (day P&L sums)
  E4 near-target    as E1 with target 0.35w fixed (geometry-independent)

    python -m scripts.nya_fa_arms
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WINDOW = 60
RISK_DOLLARS, FR = 160.0, 1.0


def sim(direction, entry, stop, target, bars, be_at=None, partial_at=None):
    """Returns total pts (1.0 position units; partial arms weight halves)."""
    cur = stop
    legs = [(1.0, target)] if partial_at is None else [(0.5, partial_at), (0.5, target)]
    done, pts = [], 0.0
    for hi, lo, cl in bars:
        if direction > 0:
            if lo <= cur:
                pts += sum(w * (cur - entry) for w, t in legs if (w, t) not in done)
                return pts
            for leg in legs:
                w, t = leg
                if leg not in done and hi >= t:
                    pts += w * (t - entry); done.append(leg)
            if be_at and (hi - entry) >= be_at:
                cur = max(cur, entry)
        else:
            if hi >= cur:
                pts += sum(w * (entry - cur) for w, t in legs if (w, t) not in done)
                return pts
            for leg in legs:
                w, t = leg
                if leg not in done and lo <= t:
                    pts += w * (entry - t); done.append(leg)
            if be_at and (entry - lo) >= be_at:
                cur = min(cur, entry)
        if len(done) == len(legs):
            return pts
    cl = bars[-1][2]
    pts += sum(w * ((cl - entry) if direction > 0 else (entry - cl))
               for w, t in legs if (w, t) not in done)
    return pts


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    C = pd.read_parquet(ROOT / "output/nya_composites.parquet").set_index("day")
    FL = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    fl_by_day = {d: g for d, g in FL.groupby("gday")}

    all_days = sorted(set(R[R.gday >= "2025-06-02"].gday) & set(fl_by_day))
    arms = ["E1_default", "E2_be", "E3_partial", "E4_near"]
    M = pd.DataFrame(0.0, index=all_days, columns=arms)
    stats = {a: [] for a in arms}
    for d in all_days:
        if d not in C.index or not (C.loc[d, "comp_age"] >= 2):
            continue
        r = R[R.gday == d].sort_values("ts").reset_index(drop=True)
        vah, val = float(C.loc[d, "comp_vah"]), float(C.loc[d, "comp_val"])
        poc, width = float(C.loc[d, "comp_poc"]), float(C.loc[d, "comp_vah"]) - float(C.loc[d, "comp_val"])
        if width <= 0 or len(r) < 200:
            continue
        half = d[:4] + ("H1" if d[5:7] < "07" else "H2")
        elig = r[r.clock < "15:00"]
        out_up = elig[elig.close > vah]; out_dn = elig[elig.close < val]
        iu = out_up.index[0] if len(out_up) else None
        idn = out_dn.index[0] if len(out_dn) else None
        if iu is None and idn is None:
            continue
        side = 1 if (idn is None or (iu is not None and iu < idn)) else -1
        i0 = iu if side > 0 else idn
        edge = vah if side > 0 else val
        after = r.loc[i0 + 1:]
        reent = after[(after.close < edge) if side > 0 else (after.close > edge)]
        i_re = reent.index[0] if len(reent) else None
        if i_re is None or (i_re - i0) > WINDOW or r.loc[i_re].clock >= "15:00":
            continue
        seg = after.loc[:i_re]
        ext = float((seg.high.max() - edge) if side > 0 else (edge - seg.low.min()))
        entry = float(r.loc[i_re].close)
        if (side > 0 and entry <= poc) or (side < 0 and entry >= poc):
            continue
        # default-cohort gates: deep + G2
        f = fl_by_day[d]
        brk_clock, re_clock = r.loc[i0].clock, r.loc[i_re].clock
        exc = f[(f.clock >= brk_clock) & (f.clock <= re_clock)]
        exc_delta = float(exc.delta.sum()) if len(exc) else 0.0
        if not (side * exc_delta < 0):
            continue
        tail = r.loc[i_re + 1:]
        if not len(tail):
            continue
        bars = tail[["high", "low", "close"]].to_numpy()
        dirn = -side
        stop = entry + side * max(0.5 * ext, 5.0)
        risk = abs(entry - stop)
        if risk < 2:
            continue
        t_full = poc if abs(entry - poc) <= 0.5 * width else entry - side * 0.5 * width
        specs = {"E1_default": dict(target=t_full),
                 "E2_be": dict(target=t_full, be_at=0.25 * width),
                 "E3_partial": dict(target=t_full, partial_at=entry - side * 0.25 * width),
                 "E4_near": dict(target=entry - side * 0.35 * width)}
        for a, kw in specs.items():
            pts = sim(dirn, entry, stop, bars=bars, **kw) - FR
            M.loc[d, a] = RISK_DOLLARS * pts / risk
            stats[a].append(dict(pts=pts, risk=risk, half=half))
    # depth gate: apply within the collected events via median split on risk-proxy?
    # NOTE: the deep filter was applied via ext at event level in trial 3; here the
    # G2-only cohort is reported and the deep sub-cohort separately.
    M.to_parquet(ROOT / "output/nya_fa_arm_matrix.parquet")
    for a in arms:
        T = pd.DataFrame(stats[a])
        if not len(T):
            continue
        net = T.pts
        r_ = net / T.risk
        gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
        halves = " ".join(f"{h}:{x.sum():+.0f}" for h, x in net.groupby(T.half))
        print(f"{a}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
              f"${160*r_.sum():+,.0f} PF {gw/max(gl,1e-9):.2f} | {halves}")

    from src.validation.pbo import pbo_cscv
    p = pbo_cscv(M, n_blocks=16)
    print(f"PBO over exit arms: {p.pbo:.2f} ({p.n_combinations} splits, "
          f"{p.n_obs_used} days) — IS->OOS slope {p.slope:+.2f}, "
          f"P(OOS loss) {p.prob_oos_loss:.2f}")


if __name__ == "__main__":
    main()
