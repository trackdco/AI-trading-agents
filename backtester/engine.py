"""Execution & risk layer. Turns candidate signals into trades under one config, one CVD
mode, one min-confluence, one target mode. Enforces every risk rule the user set:

  * HTF bias mandatory (a candidate without htf_bias in its factor set is skipped).
  * min-confluence (3/4/5) gate.
  * Setup-B SHORT needs an extra confirm: 5m agreement OR CVD divergence present.
  * HARD max stop 70pt — if the logical stop is wider, the trade is SKIPPED. No exception.
  * Sizing tiers: 0–40pt -> 1 contract (10 micros); 41–70pt -> 0.5 contract (5 micros).
  * One trade at a time; no re-entry at the same level after a stop-out in the same session.
  * 1 tick slippage per side (adverse) + commission per micro per side.

Entries: A/B enter at market on the NEXT 1m bar's open after the rejection candle closes
(you cannot fill at the close you just observed — no lookahead). B2 rests a limit at POC and
fills when a later 1m bar trades through it.
"""
from __future__ import annotations

from datetime import time as dtime

import numpy as np
import pandas as pd

from . import indicators as ind
from .cvd import mode_gate


def _t(s):
    h, m = s.split(":"); return dtime(int(h), int(m))


def _levels_asof(ctx, ts):
    """Structural levels known at ts: vwap bands, poc/vah/val, prior-day H/L."""
    vw = ctx.vwl.reindex([ts - pd.Timedelta(minutes=1)]).iloc[0]
    lv = {"vwap": vw["vwap"]}
    for k in ctx.vwap_bands:
        lv[f"vwap+{k}"] = vw[f"upper_{k}"]; lv[f"vwap-{k}"] = vw[f"lower_{k}"]
    prof = ctx.prof_at.get(ts, {})
    for kk in ("poc", "vah", "val"):
        if kk in prof:
            lv[kk] = prof[kk]
    cme = _t(ctx.cfg["indicators"]["vwap"]["anchor"])
    sd = str(ind.session_date_scalar(ts, cme))
    pdh, pdl = ctx.liq_pdhl[0].get(sd, (np.nan, np.nan))
    lv["pdh"] = pdh; lv["pdl"] = pdl
    return {k: float(v) for k, v in lv.items() if v is not None and not pd.isna(v)}


def _liquidity_draws(levels, ent, direction):
    """Liquidity targets in the trade direction (prior-day H/L, VAH/VAL as draw-of-liquidity)."""
    keys = ("pdh", "pdl", "vah", "val")
    out = []
    for k in keys:
        if k in levels:
            v = levels[k]
            if (direction == "long" and v > ent) or (direction == "short" and v < ent):
                out.append(v)
    return sorted(out) if direction == "long" else sorted(out, reverse=True)


def _opposing_levels(levels, ent, direction):
    out = [v for v in levels.values()
           if (v > ent if direction == "long" else v < ent)]
    return sorted(out) if direction == "long" else sorted(out, reverse=True)


def sizing(stop_pts, cfg):
    for tier in cfg["risk"]["sizing_tiers"]:
        if stop_pts <= tier["max_stop"]:
            return tier["contracts"], tier["micros"]
    return None, None  # beyond hard cap — caller must have already skipped


def attach_cvd(cands: pd.DataFrame, cfg: dict, tf: str, cvd_book) -> pd.DataFrame:
    """Precompute CVD divergence / initiative per candidate ONCE (config-independent), so the
    grid of simulate() calls doesn't recompute the footprint reads 120 times."""
    if not len(cands):
        return cands
    div, init = [], []
    for s in cands.to_dict("records"):
        ts = s["ts"]; d = s["dir"]
        div.append(cvd_book.divergence_ok(ts, d))
        init.append(cvd_book.initiative_ok(ts - pd.Timedelta(tf), ts, d))
    cands = cands.copy()
    cands["_div_ok"] = div; cands["_init_ok"] = init
    return cands


def prepare(ctx, cands: pd.DataFrame, cfg: dict, tf: str, cvd_book) -> list:
    """Config-INDEPENDENT per-candidate work, done once: full factor set (incl. CVD), fill,
    logical stop, hard-cap/sizing, day-bar slice, and structural target levels. Candidates
    that can't fill, breach the 70pt hard stop, or fail the mandatory bias are dropped here.
    Returns a list of 'ready' dicts consumed by simulate() across every config."""
    if not len(cands):
        return []
    have_cvd = "_div_ok" in cands.columns
    risk = cfg["risk"]; instr = cfg["instrument"]; costs = cfg["costs"]
    tick = instr["tick"]; slip = costs["slippage_ticks_per_side"] * tick
    hardmax = risk["hard_max_stop_points"]; minstop = risk["min_stop_points"]
    flat_t = _t(cfg["session"]["flat_time"]); cme = _t(cfg["indicators"]["vwap"]["anchor"])
    ready = []
    for s in cands.sort_values("ts").to_dict("records"):
        ts = s["ts"]; d = s["dir"]; day = ts.normalize()
        fset = set(s["factors"])
        if cfg["confluence"]["htf_bias_mandatory"] and "htf_bias" not in fset:
            continue
        if s["setup"] == "B2" and not s["prior_reaction"]:
            continue
        init_ok = s["_init_ok"] if have_cvd else cvd_book.initiative_ok(ts - pd.Timedelta(tf), ts, d)
        div_ok = s["_div_ok"] if have_cvd else cvd_book.divergence_ok(ts, d)
        if div_ok:
            fset.add("cvd_divergence")
        if init_ok:
            fset.add("initiative_delta")

        # stop (logical) + fill
        if s["setup"] == "B2":
            ent_target = s["level"]
            stop = (min(s["l"], s["level"]) - tick) if d == "long" else (max(s["h"], s["level"]) + tick)
        else:
            stop = (s["l"] - tick) if d == "long" else (s["h"] + tick)
        db = ctx.day_bars.get(day)
        if db is None:
            continue
        flat = pd.Timestamp(f"{day.date()} {flat_t.strftime('%H:%M')}", tz=ctx.tz)
        dayb = db.loc[(db.index > ts) & (db.index <= flat)]
        if dayb.empty:
            continue
        if s["setup"] == "B2":
            hit = ((dayb["low"] <= ent_target) if d == "long" else (dayb["high"] >= ent_target)).to_numpy()
            if not hit.any():
                continue
            fi = int(hit.argmax())
            ent = ent_target + (slip if d == "long" else -slip)
            dayb = dayb.iloc[fi:]
        else:
            ent = float(dayb["open"].iloc[0]) + (slip if d == "long" else -slip)

        stop_pts = abs(ent - stop)
        if stop_pts > hardmax or stop_pts < minstop:
            continue
        if (d == "long" and ent <= stop) or (d == "short" and ent >= stop):
            continue
        contracts, micros = sizing(stop_pts, cfg)
        levels = _levels_asof(ctx, ts)
        draws = _liquidity_draws(levels, ent, d)
        opp = _opposing_levels(levels, ent, d)
        ready.append(dict(
            ts=ts, day=day, sd=str(ind.session_date_scalar(ts, cme)),
            setup=s["setup"], dir=d, level=s["level"], lname=s["lname"], bias=s["bias"],
            late=s["late_session"], fset=fset, n_conf=len(fset),
            div_ok=bool(div_ok), init_ok=bool(init_ok),
            ent=ent, stop=stop, stop_pts=stop_pts, contracts=contracts, micros=micros,
            lvl_key=round(s["level"] / 5.0), draws=draws, opp=opp,
            dhi=dayb["high"].to_numpy("float64"), dlo=dayb["low"].to_numpy("float64"),
            dcl=dayb["close"].to_numpy("float64"), dts=dayb.index,
        ))
    return ready


def simulate(ctx, cands, cfg: dict, tf: str, mode: str, min_conf: int,
             target_mode: str, cvd_book, ready=None) -> pd.DataFrame:
    """Run one configuration over prepared candidates. Pass `ready` (from prepare()) to reuse
    the config-independent work across the grid; otherwise it is computed here."""
    if ready is None:
        ready = prepare(ctx, cands, cfg, tf, cvd_book)
    if not ready:
        return pd.DataFrame()
    risk = cfg["risk"]; tgtc = cfg["targets"]; costs = cfg["costs"]; instr = cfg["instrument"]
    micro_pv = instr["micro_point_value"]; comm = costs["commission_per_micro"]
    slip = costs["slippage_ticks_per_side"] * instr["tick"]
    rt_comm_pts = 2 * comm / micro_pv
    open_until = pd.Timestamp.min.tz_localize(ctx.tz)
    stopped_levels = {}
    trades = []
    for s in ready:
        # --- config-dependent gates -------------------------------------------
        if s["n_conf"] < min_conf:
            continue
        if not mode_gate(mode, s["div_ok"], s["init_ok"]):
            continue
        if cfg["confluence"]["b_short_needs_extra"] and s["setup"] == "B" and s["dir"] == "short":
            if not (tf == "5min" or s["div_ok"]):
                continue
        if s["ts"] <= open_until:
            continue
        if risk["no_reentry_same_level_after_stop"] and s["lvl_key"] in stopped_levels.get(s["sd"], set()):
            continue

        d = s["dir"]; ent = s["ent"]; stop = s["stop"]; stop_pts = s["stop_pts"]
        tgt, trail = _resolve_target(target_mode, ent, d, stop_pts, s["draws"], s["opp"], tgtc)
        pnl_pts, reason, rr_planned, exit_ts = _walk(
            s["dhi"], s["dlo"], s["dcl"], s["dts"], d, ent, stop, tgt, trail, slip, tgtc, stop_pts)
        net_pts = pnl_pts - rt_comm_pts
        dollars_micro = net_pts * s["micros"] * micro_pv
        if reason == "stop":
            stopped_levels.setdefault(s["sd"], set()).add(s["lvl_key"])
        open_until = exit_ts

        trades.append(dict(
            ts=s["ts"], day=str(s["day"].date()), mo=str(s["day"])[:7], tf=tf, setup=s["setup"], dir=d,
            level=s["level"], lname=s["lname"], bias=s["bias"], late=s["late"],
            n_conf=s["n_conf"], factors="|".join(sorted(s["fset"])), div=s["div_ok"], init=s["init_ok"],
            stop_pts=round(stop_pts, 2), contracts=s["contracts"], micros=s["micros"],
            tier=("0-40" if stop_pts <= 40 else "41-70"),
            target_mode=target_mode, cvd_mode=mode, min_conf=min_conf,
            rr_planned=round(rr_planned, 2), net_pts=round(net_pts, 2),
            rr_real=round(net_pts / stop_pts, 3), dollars=round(dollars_micro, 2),
            liq_override=bool(tgt is not None and s["draws"] and abs(tgt - s["draws"][0]) < 1e-6
                             and abs(tgt - ent) < tgtc["min_points"]),
            reason=reason, entry_min=s["ts"].strftime("%H:%M"),
        ))
    return pd.DataFrame(trades)


def _resolve_target(mode, ent, d, stop_pts, draws, opp, tgtc):
    """Return (target_price or None, trail_dict or None)."""
    cap = tgtc["cap_points"]; floor = tgtc["min_points"]
    if mode == "trail80":
        return None, dict(activate=tgtc["trail_activate_points"], dist=tgtc["trail_distance_points"])
    if mode.startswith("fixed"):
        pts = float(mode.replace("fixed", ""))
        base = ent + pts if d == "long" else ent - pts
    elif mode == "dynamic":
        # nearest opposing structural level, clamped to [floor, cap]
        if opp:
            dist = abs(opp[0] - ent); dist = max(floor, min(cap, dist))
        else:
            dist = 100.0
        base = ent + dist if d == "long" else ent - dist
    else:
        raise ValueError(mode)
    # liquidity override: a draw within reach (closer than base) -> target it even if <floor
    if tgtc["liquidity_override"] and draws:
        draw = draws[0]
        if (d == "long" and draw < base) or (d == "short" and draw > base):
            return draw, None
    return base, None


def _walk(hi, lo, cl, ts_arr, d, ent, stop, tgt, trail, slip, tgtc, stop_pts):
    """Bar-walk the 1m bars (numpy arrays) from fill to exit.
    Returns (pnl_pts, reason, rr_planned, exit_ts). Stop is checked before target within a
    bar (conservative worst-case intrabar ordering)."""
    rr_planned = (abs(tgt - ent) / stop_pts) if tgt is not None else np.nan
    n = len(hi); peak = ent
    for i in range(n):
        if d == "long":
            if lo[i] <= stop:
                return (stop - ent - slip), "stop", rr_planned, ts_arr[i]
            if trail is None and tgt is not None and hi[i] >= tgt:
                return (tgt - ent - slip), "target", rr_planned, ts_arr[i]
            if trail is not None:
                peak = peak if peak > hi[i] else hi[i]
                if peak - ent >= trail["activate"] and lo[i] <= peak - trail["dist"]:
                    return (peak - trail["dist"] - ent - slip), "trail", rr_planned, ts_arr[i]
        else:
            if hi[i] >= stop:
                return (ent - stop - slip), "stop", rr_planned, ts_arr[i]
            if trail is None and tgt is not None and lo[i] <= tgt:
                return (ent - tgt - slip), "target", rr_planned, ts_arr[i]
            if trail is not None:
                peak = peak if peak < lo[i] else lo[i]
                if ent - peak >= trail["activate"] and hi[i] >= peak + trail["dist"]:
                    return (ent - (peak + trail["dist"]) - slip), "trail", rr_planned, ts_arr[i]
    last = cl[-1]
    return ((last - ent) if d == "long" else (ent - last)), "eod", rr_planned, ts_arr[-1]
