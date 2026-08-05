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
