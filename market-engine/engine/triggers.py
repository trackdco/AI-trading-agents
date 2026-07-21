"""Trigger detection + pattern classification + structural order geometry.

Rejection block (§3): entry-TF candle trades into a cluster, CLOSES back on the
trade side of ALL cluster levels, leaves a wick through. Displacement (§3): body
closes through ≥2 cluster levels, body/range ≥ B_min, close in extreme quartile.
Pattern A/B/B2 per §4. Entry (E1=BB MA), stop (beyond wick), target (menu, §6)
are the structural order mechanics the Vault later risk-checks — no sizing here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import clusters


@dataclass
class Trigger:
    direction: str                 # 'long' | 'short'
    trigger_type: str              # 'rejection_block' | 'displacement'
    pattern: str                   # 'A' | 'B' | 'B2'
    htf_flag: str
    with_trend: bool
    cluster: dict
    zone_low: float
    zone_high: float
    entry: float
    invalidation: float
    stop: float
    target: float
    target_label: str
    rr: float
    over_extension: bool
    notes: list[str] = field(default_factory=list)


def _quartile_close(bar, direction: str, q: float) -> bool:
    rng = bar["high"] - bar["low"]
    if rng <= 0:
        return False
    if direction == "long":
        return bar["close"] >= bar["high"] - q * rng
    return bar["close"] <= bar["low"] + q * rng


def _pick_target(entry: float, direction: str, menu: list[dict], stop: float,
                 rr_floor: float, front_run: float) -> tuple[float, str, float]:
    """Nearest opposing menu level beyond entry that clears the RR floor."""
    risk = abs(entry - stop)
    if risk <= 0:
        return (float("nan"), "none", 0.0)
    cands = []
    for m in menu:
        price = m["price"]
        if price != price:
            continue
        if direction == "long" and price > entry:
            adj = price - front_run
        elif direction == "short" and price < entry:
            adj = price + front_run
        else:
            continue
        rr = abs(adj - entry) / risk
        cands.append((abs(adj - entry), adj, m["label"], rr))
    cands.sort()
    for _, adj, label, rr in cands:
        if rr >= rr_floor:
            return (round(adj, 2), label, round(rr, 2))
    return (float("nan"), "none", 0.0)


def evaluate(bar, levels: list[dict], ctx: dict) -> Trigger | None:
    """Evaluate a single CLOSED entry-TF candle for a trigger. Returns a
    Trigger if the mechanical setup + confluence minimum are met, else None."""
    tick = ctx["tick"]
    tol = ctx["tol"]
    htf = ctx["htf"]
    menu = ctx["target_menu"]
    rr_floor = ctx["rr_floor"]
    front = ctx["front_run"]

    body_hi = max(bar["open"], bar["close"])
    body_lo = min(bar["open"], bar["close"])
    rng = bar["high"] - bar["low"]
    body = abs(bar["close"] - bar["open"])

    trig = None

    # ---- Rejection block ----------------------------------------------------
    up_cl = clusters.cluster_at(levels, bar["high"], tol)
    if up_cl["count"] >= 2 and bar["high"] > max(l["price"] for l in up_cl["levels"]) \
            and bar["close"] < min(l["price"] for l in up_cl["levels"]):
        trig = ("short", "rejection_block", up_cl, body_hi, bar["high"])

    if trig is None:
        dn_cl = clusters.cluster_at(levels, bar["low"], tol)
        if dn_cl["count"] >= 2 and bar["low"] < min(l["price"] for l in dn_cl["levels"]) \
                and bar["close"] > max(l["price"] for l in dn_cl["levels"]):
            trig = ("long", "rejection_block", dn_cl, body_lo, bar["low"])

    # ---- Displacement (body closes through ≥2 levels) -----------------------
    if trig is None and rng > 0 and body / rng >= ctx["b_min"]:
        through = [l for l in levels if body_lo < l["price"] < body_hi]
        types = {l["type"] for l in through}
        if len(through) >= 2 and len(types) >= 2:
            direction = "long" if bar["close"] > bar["open"] else "short"
            if _quartile_close(bar, direction, ctx["extreme_q"]):
                cl = {"levels": through, "distinct_types": sorted(types),
                      "count": len(types),
                      "center": sum(l["price"] for l in through) / len(through)}
                if direction == "short":
                    trig = ("short", "displacement", cl, body_hi, bar["low"])
                else:
                    trig = ("long", "displacement", cl, body_lo, bar["high"])

    if trig is None:
        return None

    direction, ttype, cl, body_edge, wick_extreme = trig
    with_trend = (direction == "long" and htf == "uptrend") or \
                 (direction == "short" and htf == "downtrend")
    counter_trend = (direction == "long" and htf == "downtrend") or \
                    (direction == "short" and htf == "uptrend")

    # ---- Confluence minimum gate (§7) --------------------------------------
    required = 3 if counter_trend else 2
    if cl["count"] < required:
        return None

    # ---- Over-extension (§3) -----------------------------------------------
    over_ext = False
    oe = ctx.get("overext")
    if oe:
        if direction == "short" and oe.get("p2") is not None and bar["high"] >= oe["p2"]:
            over_ext = True
        if direction == "long" and oe.get("m2") is not None and bar["low"] <= oe["m2"]:
            over_ext = True

    # ---- Pattern classification (§4) ---------------------------------------
    if ttype == "displacement":
        pattern = "B"
    elif over_ext or counter_trend:
        pattern = "A"
    elif with_trend:
        pattern = "B2"
    else:
        pattern = "A"

    # ---- Structural order geometry (§5/§6) ---------------------------------
    bb = next((l["price"] for l in cl["levels"] if l["type"] == "bb"), None)
    entry = round(bb if bb is not None else cl["center"], 2)
    if direction == "short":
        zone_low, zone_high = body_edge, wick_extreme
        invalidation = wick_extreme
        stop = round(wick_extreme + tick, 2)
    else:
        zone_low, zone_high = wick_extreme, body_edge
        invalidation = wick_extreme
        stop = round(wick_extreme - tick, 2)

    target, tlabel, rr = _pick_target(entry, direction, menu, stop, rr_floor, front)
    if target != target:  # no target clears RR floor → skip (§6.5)
        return None

    return Trigger(
        direction=direction, trigger_type=ttype, pattern=pattern, htf_flag=htf,
        with_trend=with_trend, cluster=cl, zone_low=round(zone_low, 2),
        zone_high=round(zone_high, 2), entry=entry, invalidation=round(invalidation, 2),
        stop=stop, target=target, target_label=tlabel, rr=rr, over_extension=over_ext,
    )
