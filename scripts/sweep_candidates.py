#!/usr/bin/env python3
"""SYNTHESIS SWEEP — candidate detectors. 08:00-10:30 ET entries only.

Each detector returns Events; scripts/sweep_harness.py owns everything downstream of the stop
(the locked exit, the features, the split, the clustering, the noise floor). Specs and provenance
live in research/_shared/trials-ledger.md — this file is the mechanisation, not the record.

⚠️ THE WINDOW IS A THIRD CONVENTION AND IT IS OURS. Every existing card is scored on 09:45-10:15
(zxck-*, ash-unicorn-sb) or 09:30-10:30 (orb-fvg). 08:00-10:30 matches none of them, so nothing
here pools like-for-like with the existing logs. Tag every result [stated-by-user].

Shared conventions used by more than one candidate, stated once:

  RISK FLOOR 15pt, APPLIED BY WIDENING THE STOP, NEVER BY SKIPPING THE EVENT.
      Skipping would cut the sample and would do it non-randomly — the skipped set is the
      tight-stop end, which is systematically the quiet sessions. Widening only makes R harder
      to earn, so it is the conservative direction. The floor itself comes from the measured
      failure of tight stops in this session: zxck-ifvg-50's fixed 5pt stop is smaller than 99%
      of individual 1-minute bars here and put 0.250R/trade into costs (n=186, t=-4.165).

  BUFFER 5pt beyond the reference extreme, so a stop sits outside the level rather than on it.
      [A] ours. Powell's stop rule is "beyond the PD array" (COMPONENTS D1) without a number.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.sweep_harness import (  # noqa: E402
    RTH_END, RTH_OPEN, WIN_LO, Ctx, Event, flow_frame,
)

BUF = 5.0            # points beyond the reference extreme
RISK_FLOOR = 15.0    # points; enforced by widening
GLOBEX_OPEN = 18 * 60


def _floor_stop(entry: float, stop: float, side: int) -> float:
    """Widen a stop to the risk floor. Never skips, never tightens."""
    risk = (entry - stop) * side
    return entry - side * RISK_FLOOR if risk < RISK_FLOOR else stop


# =============================================================== LENS A
def sw_onx_reclaim(ctx: Ctx) -> list[Event]:
    """A1 — overnight-extreme sweep, reclaimed after the cash open.

    Levels frozen at 09:30. The unswept test uses the 09:30 OPEN, and the sweep test is a strict
    CROSSING. Note this candidate CANNOT repeat the 2026-08-07 sweep-gate defect: the overnight
    span ends one minute before 09:30 on a continuously traded contract, so the 09:30 open is
    inside the overnight range by construction (measured: 289/289, the 2 exceptions being
    open == ONH exactly, which a strict inequality still rejects).
    """
    on = pd.concat([ctx.prev[ctx.prev.mins >= GLOBEX_OPEN], ctx.g[ctx.g.mins < RTH_OPEN]])
    if not len(on):
        return []
    onh, onl = float(on.high.max()), float(on.low.min())
    w = ctx.w
    scan = w[(w.mins >= RTH_OPEN) & (w.mins <= 10 * 60 + 15)]
    if not len(scan):
        return []
    o930 = float(w.open.iloc[RTH_OPEN - WIN_LO])
    out = []
    for lv, side, opp in ((onh, -1, onl), (onl, +1, onh)):
        if (o930 > lv) if side < 0 else (o930 < lv):
            continue                                    # already beyond it -> not a sweep
        hit = (scan.high > lv) if side < 0 else (scan.low < lv)
        if not hit.any():
            continue
        i0 = int(hit.idxmax())
        post = w.loc[i0 + 1:].loc[lambda x: x.mins <= 10 * 60 + 15]
        rec = (post.close < lv) if side < 0 else (post.close > lv)
        if not len(post) or not rec.any():
            continue
        j = int(rec.idxmax())
        seg = w.loc[i0:j]
        ext = float(seg.high.max()) if side < 0 else float(seg.low.min())
        entry = float(w.close.iloc[j])
        stop = _floor_stop(entry, ext - side * BUF, side)
        risk = (entry - stop) * side
        if risk <= 0:
            continue
        if abs(entry - opp) < 2 * risk:                 # the draw must reach the locked target
            continue
        out.append(Event(t=j, side=side, entry=entry, stop=stop, intrabar=False,
                         tag="onh" if side < 0 else "onl"))
    return out


def _pre_cash(ctx: Ctx):
    p = ctx.w[ctx.w.mins < RTH_OPEN]
    return (float(p.high.max()), float(p.low.min())) if len(p) else (np.nan, np.nan)


_ONVOL: dict[str, float] = {}


def _onvol_ratio(ctx: Ctx) -> float:
    """Overnight participation vs its own trailing median. UNSIGNED volume only.

    Window ends 09:29, entry is the 09:30 bar, so the last minute read is entry_minute - 1.
    This is deliberately NOT the banned feature: no delta, no sign, no confirmation of a
    structurally-defined move.
    """
    return _ONVOL.get(ctx.day, np.nan)


def build_onvol(ctxs: list[Ctx]) -> None:
    """Precompute each session's overnight volume ratio against its trailing 20-session median.

    The median is shifted so TODAY IS EXCLUDED from its own reference.
    """
    fp = flow_frame()
    vol = fp.vol
    tot = {}
    for ctx in ctxs:
        pv = ctx.prev.ts.iloc[0].normalize() + pd.Timedelta(minutes=GLOBEX_OPEN)
        cut = ctx.w.ts.iloc[RTH_OPEN - WIN_LO] - pd.Timedelta(minutes=1)
        tot[ctx.day] = float(vol[(vol.index >= pv) & (vol.index <= cut)].sum())
    s = pd.Series(tot).sort_index()
    med = s.rolling(20, min_periods=10).median().shift(1)
    _ONVOL.clear()
    _ONVOL.update((s / med).to_dict())


def sw_gap_nopart(ctx: Ctx) -> list[Event]:
    """A2 — overnight relocation on LOW participation, reverted at the cash open.

    Gate is participation, never sign: it asks whether inventory moved, not which way.
    """
    r = _onvol_ratio(ctx)
    if not (r == r) or r >= 1.0:
        return []
    if ctx.prev_rth is None:
        return []
    rth = ctx.prev_rth[(ctx.prev_rth.mins >= RTH_OPEN) & (ctx.prev_rth.mins <= RTH_END)]
    if not len(rth):
        return []
    pdc = float(rth.close.iloc[-1])
    i = RTH_OPEN - WIN_LO
    bar = ctx.w.iloc[i]
    entry = float(bar.close)
    if entry == pdc:
        return []
    side = -1 if entry > pdc else +1
    pch, pcl = _pre_cash(ctx)
    ref = max(pch, float(bar.high)) if side < 0 else min(pcl, float(bar.low))
    stop = _floor_stop(entry, ref - side * BUF, side)
    risk = (entry - stop) * side
    if risk <= 0 or abs(entry - pdc) < 2 * risk:
        return []
    return [Event(t=i, side=side, entry=entry, stop=stop, intrabar=False, tag="gap_nopart")]


def sw_gap_nopart_inv(ctx: Ctx) -> list[Event]:
    """A2-DIAGNOSTIC — the SAME rule with the participation gate INVERTED (ratio >= 1.0).

    Declared by the generator as the only honest falsification of A2's mechanism: if the high-
    participation arm does as well or better, the gate does nothing and A2 is gap-fade folklore
    wearing a mechanism. It is a TRIAL and is counted as one in the ledger.
    """
    r = _onvol_ratio(ctx)
    if not (r == r) or r < 1.0:
        return []
    saved, _ONVOL[ctx.day] = _ONVOL[ctx.day], 0.0        # pass A2's own gate, keep everything else
    try:
        evs = sw_gap_nopart(ctx)
    finally:
        _ONVOL[ctx.day] = saved
    for e in evs:
        e.tag = "gap_highpart"
    return evs


def sw_open_drive_pcr(ctx: Ctx) -> list[Event]:
    """A3 — the 09:30 auction closing OUTSIDE the 90-minute pre-cash range. Continuation.

    The sweep's only continuation candidate. If every candidate is a reversion, a positive sweep
    result cannot be told apart from the window simply mean-reverting.
    """
    pch, pcl = _pre_cash(ctx)
    if not (pch == pch):
        return []
    i = RTH_OPEN - WIN_LO
    bar = ctx.w.iloc[i]
    c = float(bar.close)
    if c > pch:
        side, ref = +1, float(bar.low)
    elif c < pcl:
        side, ref = -1, float(bar.high)
    else:
        return []
    stop = _floor_stop(c, ref - side * BUF, side)
    if (c - stop) * side <= 0:
        return []
    return [Event(t=i, side=side, entry=c, stop=stop, intrabar=False, tag="open_drive")]


LENS_A = {
    "sw-onx-reclaim": sw_onx_reclaim,
    "sw-gap-nopart": sw_gap_nopart,
    "sw-gap-nopart-INV": sw_gap_nopart_inv,
    "sw-open-drive-pcr": sw_open_drive_pcr,
}

ALL = {**LENS_A}


# =============================================================== shared flow infrastructure
_ATR15: dict = {}
_FPMIN: dict = {}
_PROFILE: dict = {}
_BASE: dict = {}


def build_flow_infra(ctxs: list[Ctx]) -> None:
    """Precompute ATR15, per-minute vol/delta, cleaned volume-at-price profiles, and the
    clock-minute volume baselines. All strictly from data available before each use."""
    from scripts.nya_sb01_feasibility import load_bars

    bars = load_bars()
    tr = pd.concat([bars.high - bars.low,
                    (bars.high - bars.close.shift()).abs(),
                    (bars.low - bars.close.shift()).abs()], axis=1).max(axis=1)
    # shift(1) so bar t's ATR uses the 15 bars ENDING AT t-1... no: spec says the 15 COMPLETED
    # bars ending at t, i.e. inclusive of t. t is always <= entry_minute-1, so this is clean.
    _ATR15.clear()
    _ATR15.update(dict(zip(bars.ts, tr.rolling(15, min_periods=10).mean())))

    fp = flow_frame()
    _FPMIN.clear()
    _FPMIN.update({k: v for k, v in fp.groupby(fp.index.strftime("%Y-%m-%d"))})

    # ---- clock-minute volume baseline, prior sessions only (candidate B2) ----
    days = [c.day for c in ctxs]
    piv = {}
    for c in ctxs:
        f = _FPMIN.get(c.day)
        if f is None:
            continue
        m = f.index.hour * 60 + f.index.minute
        piv[c.day] = pd.Series(f.vol.to_numpy(), index=m)
    P = pd.DataFrame(piv).T.reindex(days)
    _BASE.clear()
    _BASE.update({d: P.loc[:d].iloc[-21:-1].median() for d in days})   # excludes today

    # ---- volume-at-price profiles, MINUTE-LEVEL band clean (candidate B3) ----
    # ⚠️ REQUIRED. The shipped README describes a DAY-level band clean, which cannot separate
    # contracts during a quarterly roll because the continuous 1-min series switches contract
    # inside the day and the day band spans both. Measured on 06:00-11:00: 4.53% of rows and
    # 2.42% of volume fall outside their OWN minute's bar range, concentrated on roll dates
    # (2025-09-15 54.4%, 2025-12-15 51.1%, 2025-06-16 50.3%). Un-cleaned, a roll-week profile is
    # ~half back-month and its VPOC can land hundreds of points outside the session's own range.
    import glob
    keep = {c.day for c in ctxs}
    key = bars.set_index("ts")[["low", "high"]]
    parts = []
    for p in sorted(glob.glob(str(ROOT / "data/reference/cvd/footprint_*.parquet"))):
        if "holdout" in p:                                   # sealed 2023/24 — never opened
            continue
        d = pd.read_parquet(p, columns=["ts_minute", "price", "volume"])
        d["ts"] = pd.to_datetime(d.ts_minute, utc=True).dt.tz_convert("America/New_York")
        d["day"] = d.ts.dt.strftime("%Y-%m-%d")
        d = d[d.day.isin(keep)]
        mm = d.ts.dt.hour * 60 + d.ts.dt.minute
        parts.append(d[(mm >= WIN_LO) & (mm < RTH_OPEN)][["ts", "day", "price", "volume"]])
    prof = pd.concat(parts, ignore_index=True).join(key, on="ts", how="inner")
    prof = prof[(prof.price >= prof.low - 0.25) & (prof.price <= prof.high + 0.25)]
    prof["mins"] = prof.ts.dt.hour * 60 + prof.ts.dt.minute
    _PROFILE.clear()
    for day, d in prof.groupby("day"):
        _PROFILE[day] = d


def _vpoc(day: str, lo: int, hi: int) -> float:
    d = _PROFILE.get(day)
    if d is None:
        return np.nan
    x = d[(d.mins >= lo) & (d.mins <= hi)]
    if not len(x):
        return np.nan
    g = x.groupby("price").volume.sum()
    return float(g.idxmax())


def _atr(ts) -> float:
    return _ATR15.get(ts, np.nan)


# =============================================================== LENS B
def sw_cvd_div_reclaim(ctx: Ctx) -> list[Event]:
    """B1 — session-CVD divergence at a swept extreme, entered on the reclaim.

    NOT the banned rule: this compares CVD at TWO SEPARATE EXTREMES rather than checking that
    delta agrees with a move already defined as directional. The generator measured the gate
    removing 61% of sweep-and-reclaim events (1185 -> 458), so it binds.

    Look-ahead: last flow minute read is the swept-extreme bar t; entry is the OPEN of bar j+1
    with j >= t+1, so flow ends at worst at entry_minute - 2. Strictly stronger than the boundary
    that killed retrace_ratio.
    """
    f = _FPMIN.get(ctx.day)
    if f is None:
        return []
    w = ctx.w
    mm = f.index.hour * 60 + f.index.minute
    dl = pd.Series(f.delta.to_numpy(), index=mm.to_numpy())
    cvd = {}
    run = 0.0
    for m in w.mins.to_numpy():
        run += float(dl.get(m, 0.0))
        cvd[int(m)] = run

    out, seen = [], set()
    for sgn in (+1, -1):                       # +1 = low side (long), -1 = high side (short)
        px = w.low.to_numpy() if sgn > 0 else w.high.to_numpy()
        ext_i = 0
        ext = px[0]
        armed = False
        for i in range(1, len(w)):
            if not armed:
                back = w.high.iloc[i] if sgn > 0 else w.low.iloc[i]
                if (back >= ext + 20) if sgn > 0 else (back <= ext - 20):
                    armed = True
            new = (px[i] < ext) if sgn > 0 else (px[i] > ext)
            if new and armed and (i - ext_i) >= 5:
                c0, c1 = cvd[int(w.mins.iloc[ext_i])], cvd[int(w.mins.iloc[i])]
                diverge = (c1 > c0) if sgn > 0 else (c1 < c0)
                lvl0, lvl1 = ext, px[i]
                if diverge and sgn not in seen:
                    hi_j = min(i + 20, len(w) - 2)
                    for j in range(i + 1, hi_j + 1):
                        ok = (w.close.iloc[j] > lvl0) if sgn > 0 else (w.close.iloc[j] < lvl0)
                        if not ok:
                            continue
                        a = _atr(w.ts.iloc[j])
                        entry = float(w.open.iloc[j + 1])
                        stop = lvl1 - sgn * 0.25
                        if a == a and (entry - stop) * sgn < a:
                            stop = entry - sgn * a
                        if (entry - stop) * sgn <= 0:
                            break
                        out.append(Event(t=j + 1, side=sgn, entry=entry, stop=float(stop),
                                         intrabar=False,
                                         tag="cvd_div_lo" if sgn > 0 else "cvd_div_hi"))
                        seen.add(sgn)
                        break
            if new:
                ext, ext_i, armed = px[i], i, False
    return out


def sw_thinbook_surprise(ctx: Ctx) -> list[Event]:
    """B2 — clock-normalised participation surprise in the pre-cash book.

    Direction is the sign of the surprise minute's delta. This is NOT the banned rule: the event
    is defined purely by volume MAGNITUDE and one-sidedness, and no directional price structure
    is defined anywhere, so there is nothing for delta to circularly confirm.

    Look-ahead: surprise, delta and the stop all come from minute t, which closes at t+1:00.
    Entry is the OPEN of minute t+1, so the last flow minute is exactly entry_minute - 1.
    """
    f, base = _FPMIN.get(ctx.day), _BASE.get(ctx.day)
    if f is None or base is None or base.isna().all():
        return []
    w = ctx.w
    mm = f.index.hour * 60 + f.index.minute
    vol = pd.Series(f.vol.to_numpy(), index=mm.to_numpy())
    dl = pd.Series(f.delta.to_numpy(), index=mm.to_numpy())
    news = set()
    for r in ctx.news_mins:
        news.update(range(r, r + 5))
    for i in range(len(w) - 1):
        m = int(w.mins.iloc[i])
        if m in news:                                   # release-driven surprise -> lens C
            continue
        b, v = base.get(m, np.nan), vol.get(m, np.nan)
        if not (b == b and v == v) or b <= 0 or v / b < 3.0:
            continue
        d = float(dl.get(m, 0.0))
        if v <= 0 or abs(d) / v < 0.20:
            continue
        side = 1 if d > 0 else -1
        entry = float(w.open.iloc[i + 1])
        stop = (float(w.low.iloc[i]) - 0.25) if side > 0 else (float(w.high.iloc[i]) + 0.25)
        a = _atr(w.ts.iloc[i])
        if a == a and (entry - stop) * side < 1.5 * a:
            stop = entry - side * 1.5 * a
        if (entry - stop) * side <= 0:
            continue
        return [Event(t=i + 1, side=side, entry=entry, stop=float(stop), intrabar=False,
                      tag="thin_surprise")]                # first per session = primary arm
    return []


def _value_migration(ctx: Ctx, price_arm: bool) -> list[Event]:
    va = _vpoc(ctx.day, WIN_LO, 8 * 60 + 44)
    vb = _vpoc(ctx.day, 8 * 60 + 45, RTH_OPEN - 1)
    if not (va == va and vb == vb):
        return []
    if price_arm:
        w = ctx.w
        c1 = float(w.close.iloc[(8 * 60 + 44) - WIN_LO])
        c2 = float(w.close.iloc[(RTH_OPEN - 1) - WIN_LO])
        mig = c2 - c1
    else:
        mig = vb - va
    if abs(mig) < 15:
        return []
    side = 1 if mig > 0 else -1
    w = ctx.w
    i930 = RTH_OPEN - WIN_LO
    o930 = float(w.open.iloc[i930])
    if (o930 <= va) if side > 0 else (o930 >= va):
        return []                                        # thesis pre-invalidated at the open
    scan = w.iloc[i930:]
    touch = (scan.low <= vb) & (scan.high >= vb)
    if not touch.any():
        return []
    k = int(touch.idxmax())
    if k + 1 >= len(w):
        return []
    entry = float(w.open.iloc[k + 1])
    stop = va - side * 0.25
    if (entry - stop) * side <= 0:
        return []
    return [Event(t=k + 1, side=side, entry=entry, stop=float(stop), intrabar=False,
                  tag="vpoc_mig" if not price_arm else "price_mig")]


def sw_precash_value_migration(ctx: Ctx) -> list[Event]:
    """B3 — pre-cash VPOC migration, entered on the retest after the cash open.

    Every input closes at 09:29:59 and the entry cannot occur before 09:31, so the look-ahead
    boundary is unreachable rather than merely satisfied. The |mig| >= 15 gate and the stop are
    the SAME number, so R >= 15pt is structural — no arbitrary floor parameter.
    """
    return _value_migration(ctx, price_arm=False)


def sw_precash_price_migration(ctx: Ctx) -> list[Event]:
    """B3-CONTROL — identical, but direction from PRICE change instead of VPOC migration.

    MANDATORY. The two agree in sign on only 72% of sessions, so they are distinguishable.
    Without this arm a positive B3 result cannot be attributed to order flow at all.
    """
    return _value_migration(ctx, price_arm=True)


LENS_B = {
    "sw-cvd-div-reclaim": sw_cvd_div_reclaim,
    "sw-thinbook-surprise": sw_thinbook_surprise,
    "sw-precash-value-migration": sw_precash_value_migration,
    "sw-precash-price-migration-CTL": sw_precash_price_migration,
}

ALL = {**LENS_A, **LENS_B}


# =============================================================== LENS C
# ⚠️ DECLARED DEVIATION FROM LEDGER §0.5, recorded rather than done silently.
# §0.5 says a release-mechanism candidate must key on the canonical whitelist. Both Lens C
# candidates key on the TAPE instead, because the canonical-only version is untestable
# (17 discovery / 11 holdout events) and because the whitelist is itself an intersection of two
# incomplete files — the newer one carries PPI, Unemployment Claims, Philly Fed, Empire State and
# Durable Goods at 08:30 and the older carries NONE of them.
# The tape gate is also MORE split-stable than the canonical flag (26.6% -> 30.9% across the
# boundary, against 13.5% -> 19.6% for canonical) and is computed strictly from 08:00-08:30 bars,
# so it cannot carry a calendar-file artefact by construction.
# External validation that it detects releases and not noise: it fires on 16 of 37 discovery
# Thursdays (weekly jobless claims, 08:30, calendar-certain) and 1 of 39 discovery Mondays
# (no Monday 08:30 release exists).
# Both candidates carry a pre-registered CANONICAL-ONLY consistency arm, reported alongside and
# explicitly underpowered.

M0830, M0834, M0829 = 8 * 60 + 30, 8 * 60 + 34, 8 * 60 + 29


def _release_gate(ctx: Ctx):
    """G1 tape-detected release + the scale unit. Returns (m30, origin, ok) or None."""
    w = ctx.w
    pre = w[(w.mins >= WIN_LO) & (w.mins <= M0829)]
    if len(pre) < 30:
        return None
    m30 = float((pre.high - pre.low).median())
    v30 = float(pre.volume.median())
    b = w[w.mins == M0830]
    if not len(b) or v30 <= 0 or m30 <= 0:
        return None
    if float(b.volume.iloc[0]) / v30 < 2.5:              # G1
        return None
    return m30, float(pre.close.iloc[-1])


def _sw_0830_secondleg(ctx: Ctx, canon_only: bool) -> list[Event]:
    g = _release_gate(ctx)
    if g is None:
        return []
    if canon_only and not any(M0830 <= r <= M0830 for r in ctx.news_mins):
        return []
    m30, origin = g
    w = ctx.w
    imp_leg = w[(w.mins >= M0830) & (w.mins <= M0834)]
    if len(imp_leg) < 5:
        return []
    s = 1 if float(imp_leg.close.iloc[-1]) >= origin else -1
    ext = float(imp_leg.high.max()) if s > 0 else float(imp_leg.low.min())
    imp = abs(ext - origin)
    if imp < 2.5 * m30:                                   # G2 scale-free displacement floor
        return []
    buf = max(10.0, m30)
    E = origin + s * 0.5 * imp
    X = origin - s * buf
    risk = (E - X) * s
    if risk < 20.0:                                       # G3 absolute floor, from zxck-ifvg-50
        return []
    scan = w[(w.mins >= 8 * 60 + 35) & (w.mins <= RTH_OPEN - 1)]
    hit = (scan.low <= E) if s > 0 else (scan.high >= E)
    if not len(scan) or not hit.any():
        return []
    t = int(hit.idxmax())
    return [Event(t=t, side=s, entry=float(E), stop=float(X), intrabar=True,
                  tag="0830_2ndleg" + ("_canon" if canon_only else ""))]


def _sw_0930_carry(ctx: Ctx, canon_only: bool) -> list[Event]:
    g = _release_gate(ctx)
    if g is None:
        return []
    if canon_only and not any(M0830 <= r <= M0830 for r in ctx.news_mins):
        return []
    m30, origin = g
    w = ctx.w
    imp_leg = w[(w.mins >= M0830) & (w.mins <= M0834)]
    if len(imp_leg) < 5:
        return []
    s0 = 1 if float(imp_leg.close.iloc[-1]) >= origin else -1
    ext = float(imp_leg.high.max()) if s0 > 0 else float(imp_leg.low.min())
    if abs(ext - origin) < 2.5 * m30:                     # G2, same gate as C1
        return []
    c929 = float(w[w.mins == RTH_OPEN - 1].close.iloc[0])
    rs = 1 if c929 >= origin else -1
    cons = w[(w.mins >= 9 * 60) & (w.mins <= RTH_OPEN - 1)]
    if not len(cons):
        return []
    chi, clo = float(cons.high.max()), float(cons.low.min())
    L = chi if rs > 0 else clo
    X = clo if rs > 0 else chi
    scan = w[w.mins >= RTH_OPEN]
    br = (scan.close > L) if rs > 0 else (scan.close < L)
    if not br.any():
        return []
    t = int(br.idxmax())
    entry = float(w.close.iloc[t])
    if (entry - X) * rs < 20.0:
        return []
    return [Event(t=t, side=rs, entry=entry, stop=float(X), intrabar=False,
                  tag="0930_carry" + ("_canon" if canon_only else ""))]


def sw_0830_secondleg(ctx):      return _sw_0830_secondleg(ctx, False)
def sw_0830_secondleg_canon(ctx): return _sw_0830_secondleg(ctx, True)
def sw_0930_cashopen_carry(ctx):  return _sw_0930_carry(ctx, False)
def sw_0930_carry_canon(ctx):     return _sw_0930_carry(ctx, True)


LENS_C = {
    "sw-0830-secondleg": sw_0830_secondleg,
    "sw-0930-cashopen-carry": sw_0930_cashopen_carry,
    "sw-0830-secondleg-CANON": sw_0830_secondleg_canon,
    "sw-0930-carry-CANON": sw_0930_carry_canon,
}

ALL = {**LENS_A, **LENS_B, **LENS_C}
