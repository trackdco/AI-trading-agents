"""Confluence cluster detection (§3).

A cluster = ≥2 of {BB MA, NY VWAP mid/±1σ (post-9:30 only), daily VWAP
mid/±1/2/3σ, daily POC, structural extreme} within the proximity tolerance.
Confluence COUNT is by distinct level TYPE: vwap_family ×1, bb ×1, poc ×1,
structural ×1 (§3).
"""
from __future__ import annotations

TYPES = ("vwap_family", "bb", "poc", "structural")


def build_levels(ind: dict, structural: dict, pre_930: bool) -> list[dict]:
    """Flatten the current indicator/structure snapshot into typed levels.

    ``ind`` carries daily_vwap/{mid,p1,m1,...}, ny_vwap/{...} (or None pre-9:30),
    bb_ma, daily_poc. ``structural`` carries session/prior-day extremes + swings.
    """
    lv: list[dict] = []

    dv = ind.get("daily_vwap") or {}
    for label, key in [("daily VWAP mid", "mid"), ("daily VWAP +1σ", "p1"),
                       ("daily VWAP -1σ", "m1"), ("daily VWAP +2σ", "p2"),
                       ("daily VWAP -2σ", "m2"), ("daily VWAP +3σ", "p3"),
                       ("daily VWAP -3σ", "m3")]:
        v = dv.get(key)
        if v is not None and v == v:  # not NaN
            lv.append({"type": "vwap_family", "label": label, "price": float(v)})

    if not pre_930:
        nv = ind.get("ny_vwap") or {}
        for label, key in [("NY VWAP mid", "mid"), ("NY VWAP +1σ", "p1"),
                           ("NY VWAP -1σ", "m1")]:
            v = nv.get(key)
            if v is not None and v == v:
                lv.append({"type": "vwap_family", "label": label, "price": float(v)})

    if ind.get("bb_ma") is not None and ind["bb_ma"] == ind["bb_ma"]:
        lv.append({"type": "bb", "label": "BB basis (MA)", "price": float(ind["bb_ma"])})

    if ind.get("daily_poc") is not None and ind["daily_poc"] == ind["daily_poc"]:
        lv.append({"type": "poc", "label": "daily POC", "price": float(ind["daily_poc"])})

    for label, v in structural.items():
        if v is not None and v == v:
            lv.append({"type": "structural", "label": label, "price": float(v)})
    return lv


def cluster_at(levels: list[dict], ref_price: float, tol: float) -> dict:
    """Levels within ``tol`` of ``ref_price`` → cluster with distinct-type count."""
    near = [l for l in levels if abs(l["price"] - ref_price) <= tol]
    types = sorted({l["type"] for l in near})
    return {
        "levels": near,
        "distinct_types": types,
        "count": len(types),
        "center": (sum(l["price"] for l in near) / len(near)) if near else ref_price,
    }
