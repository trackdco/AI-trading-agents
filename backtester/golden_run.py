"""Golden-window study (09:40–10:15 entries, Feb–Jun 2026).

The user's ask, faithfully:
  * Base = the usual VWAP + Bollinger strategy (rejections at VWAP bands / BB / POC), HTF bias
    mandatory, my established risk rules (70pt hard stop, sizing tiers, one trade at a time).
  * Confirmation stack ADDED and TESTED: CVD divergence (required — the proven edge) + the
    heatmap near-touch book imbalance ("liquidity magnet") + price-resolved footprint at the
    level. Magnet + footprint are LOGGED on every entry so the journal can learn whether they
    actually help — rather than assumed.
  * Entries ONLY 09:40–10:15; a trade open at 10:15 keeps running to its stop/target/flat (winners
    run past the window). One trade at a time, globally across 3m and 5m.
  * Journal every entry chronologically with running expectancy, then synthesise what worked.

HONESTY: the depth is top-10 (near-touch, ~2.5pt), so the "magnet" is a book imbalance at the
level, not a far draw-of-liquidity target. Targets use the established structural rules. Feb–Jun
2026 is in-sample. Nothing here is fabricated — every number comes from the run.

    python -m backtester.golden_run
"""
from __future__ import annotations

import os
from datetime import time as dtime

import numpy as np
import pandas as pd
import yaml

from . import data as D, signals as S, engine as E, report as R
from .cvd import CVDBook
from .heatmap import HeatBook, FootprintBook


def _t(s):
    h, m = s.split(":"); return dtime(int(h), int(m))


def load_cfg(path="backtester/config.yaml"):
    return yaml.safe_load(open(path))


def build(cfg):
    tz = cfg["data"]["tz"]
    bars = D.load_bars(cfg["data"]["bars_1m"], tz)
    bars = bars[bars["ts_event"] < pd.Timestamp("2026-07-01", tz=tz)].reset_index(drop=True)  # Feb–Jun
    delta = D.load_footprint_delta(cfg["data"]["cvd_glob"], tz)
    total = D.load_footprint_totals(cfg["data"]["cvd_glob"], tz)
    csig = D.session_cvd(delta, _t(cfg["cvd"]["anchor"]))
    book = CVDBook(delta, total, csig, cfg["cvd"]["swing_lookback_min"], cfg["cvd"]["initiative_delta_pct"])
    ctx = S.Context(bars.copy(), cfg)
    book.bind_price(ctx.close_1m)
    heat = HeatBook(cfg["heatmap"]["depth_dir"], tz)
    fpb = FootprintBook(cfg["data"]["cvd_glob"], tz)
    return bars, ctx, book, heat, fpb


def run(cfg, ctx, book, heat, fpb):
    tol = cfg["confluence"]["proximity_points"]
    near = cfg["heatmap"]["near_points"]; band = cfg["heatmap"]["footprint_band"]
    tick = cfg["instrument"]["tick"]; micro_pv = cfg["instrument"]["micro_point_value"]
    slip = cfg["costs"]["slippage_ticks_per_side"] * tick
    comm = cfg["costs"]["commission_per_micro"]; rt_comm_pts = 2 * comm / micro_pv
    hardmax = cfg["risk"]["hard_max_stop_points"]; minstop = cfg["risk"]["min_stop_points"]
    flat_t = _t(cfg["session"]["flat_time"]); tgtc = cfg["targets"]

    # candidates from both entry TFs, base setups only (VWAP/BB/POC rejections), merged + chronological
    cands = []
    for tf in cfg["timeframes"]["entry"]:
        c = S.detect(ctx, tf, cfg)
        if len(c):
            c = c[c["setup"].isin(["A", "B"])]          # usual VWAP/BB reversal + continuation
            cands.append(c)
    C = pd.concat(cands, ignore_index=True).sort_values("ts").reset_index(drop=True)

    open_until = pd.Timestamp.min.tz_localize(ctx.tz)
    stopped_levels = {}
    jr = []
    for s in C.to_dict("records"):
        ts = s["ts"]; d = s["dir"]; day = ts.normalize(); tf = s["tf"]
        # --- mandatory gate: HTF bias + a base confluence floor (the usual strategy). The three
        #     tools (CVD div, magnet, footprint) are LOGGED per entry so the journal can learn
        #     their marginal value rather than pre-filtering the sample to nothing. ---
        if "htf_bias" not in set(s["factors"]):
            continue
        if s["n_conf"] < 3:
            continue
        div_ok = bool(book.divergence_ok(ts, d))
        if ts <= open_until:
            continue
        sd = str(S.ind.session_date_scalar(ts, _t(cfg["indicators"]["vwap"]["anchor"])))
        lvl_key = round(s["level"] / 5.0)
        if lvl_key in stopped_levels.get(sd, set()):
            continue

        # --- risk: stop beyond rejection wick, hard cap, sizing ---
        stop = (s["l"] - tick) if d == "long" else (s["h"] + tick)
        db = ctx.day_bars.get(day)
        if db is None:
            continue
        flat = pd.Timestamp(f"{day.date()} {flat_t.strftime('%H:%M')}", tz=ctx.tz)
        dayb = db.loc[(db.index > ts) & (db.index <= flat)]
        if dayb.empty:
            continue
        ent = float(dayb["open"].iloc[0]) + (slip if d == "long" else -slip)
        stop_pts = abs(ent - stop)
        if stop_pts > hardmax or stop_pts < minstop:
            continue
        if (d == "long" and ent <= stop) or (d == "short" and ent >= stop):
            continue
        contracts, micros = E.sizing(stop_pts, cfg)

        # --- confirmation features (logged; learn what helps) ---
        init_ok = book.initiative_ok(ts - pd.Timedelta(tf), ts, d)
        dp = book.candle_delta_pct(ts - pd.Timedelta(tf), ts)
        imb = heat.imbalance(ts, ent, d, near)
        fp = fpb.at_level(ts - pd.Timedelta(tf), ts, s["level"], band, d)
        magnet_ratio = imb["ratio"] if imb else np.nan            # >0.5 = book leans to target
        fp_oriented = fp["oriented"] if fp else np.nan            # >0 = aggressors with the trade at level

        # --- target: established structural rules (dynamic + liquidity-draw override) ---
        levels = E._levels_asof(ctx, ts)
        draws = E._liquidity_draws(levels, ent, d)
        opp = E._opposing_levels(levels, ent, d)
        tgt, trail = E._resolve_target("dynamic", ent, d, stop_pts, draws, opp, tgtc)

        hi = dayb["high"].to_numpy("float64"); lo = dayb["low"].to_numpy("float64")
        cl = dayb["close"].to_numpy("float64"); dts = dayb.index
        pnl_pts, reason, rr_planned, exit_ts = E._walk(hi, lo, cl, dts, d, ent, stop, tgt, trail,
                                                       slip, tgtc, stop_pts)
        net_pts = pnl_pts - rt_comm_pts
        dollars = net_pts * micros * micro_pv
        if reason == "stop":
            stopped_levels.setdefault(sd, set()).add(lvl_key)
        open_until = exit_ts
        held_past_window = exit_ts.time() > _t(cfg["session"]["entry_end"])

        jr.append(dict(
            ts=ts, day=str(day.date()), mo=str(day)[:7], tf=tf, setup=s["setup"], dir=d,
            level=round(s["level"], 2), lname=s["lname"], bias=s["bias"],
            entry=round(ent, 2), stop_pts=round(stop_pts, 1), micros=micros,
            tier=("0-40" if stop_pts <= 40 else "41-70"),
            cvd_div=bool(div_ok), initiative=bool(init_ok), delta_pct=(round(dp, 1) if dp is not None else np.nan),
            magnet_ratio=(round(magnet_ratio, 2) if magnet_ratio == magnet_ratio else np.nan),
            magnet_favor=(magnet_ratio > 0.5 if magnet_ratio == magnet_ratio else False),
            fp_at_level=(round(fp_oriented, 0) if fp_oriented == fp_oriented else np.nan),
            fp_confirm=(fp_oriented > 0 if fp_oriented == fp_oriented else False),
            reason=reason, net_pts=round(net_pts, 1), dollars=round(dollars, 0),
            rr_planned=round(rr_planned, 2), exit_min=exit_ts.strftime("%H:%M"),
            held_past_window=bool(held_past_window),
        ))

    J = pd.DataFrame(jr)
    if len(J):
        J["cum_dollars"] = J["dollars"].cumsum()
        J["cum_win_rate"] = (J["net_pts"] > 0).expanding().mean().round(3) * 100
    return J


# ------------------------------------------------------------------ journal & synthesis

def _grp(J, mask, label):
    x = J[mask]
    if not len(x):
        return f"  {label:34s}   0t"
    w = x[x.net_pts > 0].net_pts.sum(); l = -x[x.net_pts <= 0].net_pts.sum()
    pf = w / l if l > 0 else np.inf
    return (f"  {label:34s} {len(x):3d}t  win {(x.net_pts>0).mean()*100:4.0f}%  PF {pf:5.2f}  "
            f"net ${x.dollars.sum():+8,.0f}  avgR {(x.net_pts/x.stop_pts).mean():+.2f}")


def journal_notes(J):
    """Chronological 'learning' notes — a running read every ~15 trades and at month ends,
    emulating journaling after entries so a picture builds by the end."""
    out = ["--- RUNNING JOURNAL (chronological; what's holding up as it accumulates) ---"]
    step = 15
    for i in range(step, len(J) + step, step):
        w = J.iloc[:min(i, len(J))]
        pf_w = w[w.net_pts > 0].net_pts.sum(); pf_l = -w[w.net_pts <= 0].net_pts.sum()
        pf = pf_w / pf_l if pf_l > 0 else np.inf
        best = w.groupby("lname").dollars.sum().sort_values(ascending=False)
        top = best.index[0] if len(best) else "-"; bot = best.index[-1] if len(best) else "-"
        out.append(f"  after {len(w):3d} trades ({w.ts.iloc[-1].date()}): cum ${w.dollars.sum():+8,.0f}  "
                   f"win {(w.net_pts>0).mean()*100:3.0f}%  PF {pf:4.2f}  | best level: {top}  worst: {bot}")
    return "\n".join(out)


def synthesis(J):
    out = ["=== WHAT WORKED — Feb–Jun golden window (09:40–10:15) ===", _grp(J, J.index >= 0, "ALL"), ""]
    out.append("by setup:")
    for s in ["A", "B"]:
        out.append(_grp(J, J.setup == s, f"setup {s}"))
    out.append("\nby level tapped:")
    for ln in J.groupby("lname").dollars.sum().sort_values(ascending=False).index:
        out.append(_grp(J, J.lname == ln, ln))
    out.append("\nby direction:")
    for d in ["long", "short"]:
        out.append(_grp(J, J.dir == d, d))
    out.append("\nby TF:")
    for tf in ["3min", "5min"]:
        out.append(_grp(J, J.tf == tf, tf))
    out.append("\ndoes CVD DIVERGENCE help?")
    out.append(_grp(J, J.cvd_div, "cvd divergence present"))
    out.append(_grp(J, ~J.cvd_div, "no cvd divergence"))
    out.append("\ndoes the HEATMAP book-imbalance (magnet) help?")
    out.append(_grp(J, J.magnet_favor, "magnet favours target (>0.5)"))
    out.append(_grp(J, ~J.magnet_favor, "magnet neutral/against"))
    out.append("\ndoes the FOOTPRINT-at-level help?")
    out.append(_grp(J, J.fp_confirm, "footprint confirms (aggressors with)"))
    out.append(_grp(J, ~J.fp_confirm, "footprint against"))
    out.append("\ndoes the INITIATIVE (entry-candle delta%) help?")
    out.append(_grp(J, J.initiative, "initiative delta present"))
    out.append(_grp(J, ~J.initiative, "no initiative"))
    out.append("\nstacked confirmations:")
    out.append(_grp(J, J.cvd_div & J.fp_confirm, "cvd div + footprint"))
    out.append(_grp(J, J.cvd_div & J.magnet_favor, "cvd div + magnet"))
    out.append(_grp(J, J.cvd_div & J.magnet_favor & J.fp_confirm, "FULL STACK (div+magnet+footprint)"))
    out.append("\nby month:")
    for m in sorted(J.mo.unique()):
        out.append(_grp(J, J.mo == m, m))
    return "\n".join(out)


def main():
    cfg = load_cfg()
    bars, ctx, book, heat, fpb = build(cfg)
    print(f"[data] Feb–Jun bars {bars.ts_event.min()} -> {bars.ts_event.max()} ({len(bars):,})")
    print(f"[heatmap] depth days loaded: {len(heat.d)}")
    J = run(cfg, ctx, book, heat, fpb)
    out_dir = cfg["reporting"]["out_dir"]; os.makedirs(out_dir, exist_ok=True)
    if not len(J):
        print("NO TRADES"); return
    J.to_csv(f"{out_dir}/golden_journal.csv", index=False)
    print(f"\n{journal_notes(J)}\n\n{synthesis(J)}")
    p = R.equity_curve(J.rename(columns={}), f"{out_dir}/golden_equity.png",
                       "Golden window 09:40–10:15, Feb–Jun (VWAP/BB + CVD div)")
    print(f"\nsaved: {out_dir}/golden_journal.csv" + (f", {p}" if p else ""))


if __name__ == "__main__":
    main()
