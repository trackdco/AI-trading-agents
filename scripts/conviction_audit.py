#!/usr/bin/env python3
"""CONVICTION AUDIT — which as-of features sort the certified trades into
higher-conviction and lower-conviction cells?

    python -m scripts.conviction_audit

His ask (2026-09-03): "run an audit and variable test and see what
provides higher confluence/conviction setups, and what may be lower
conviction and worse WR."

Populations (both the certified cell: 1m, >=3pt, 1R, SAR, honest fills,
news gate, 30pt cap):
  A  8-level book   output/analysis/pd_va_trades_lvall_xr30_sar_through_tf1_ng.jsonl.gz
  B  session VWAP   output/analysis/vwap_rev_tf1_retest_xr30.jsonl.gz (depth 3 / 1R)

Every feature is computable AT SIGNAL TIME or AT FILL TIME (marked),
never after. Fill-time features are legal because the pending can be
pulled before it fills (an expiry rule), not because the trade can be
un-taken.

PREREGISTERED VERDICT RULE (written before any result was read; same
shape as rounds 1-3 so the bar does not move):
  split by session-day at MID = 2024-10-21 (IS < MID <= OOS)
  SURVIVOR  extreme-bucket EV ordering identical in both halves,
            EV spread between extremes >= 0.05R in BOTH halves,
            n >= 400 per half in each extreme bucket
  WATCH     same ordering both halves, spread >= 0.03R both, n >= 400
  NULL      anything else
  CUT       any bucket with EV < 0 in BOTH halves, n >= 400 per half
            (the only thing that licenses a skip rule)
Buckets are fixed below, not tuned. ~14 features x 2 books = ~28 cells;
expect ~1 spurious WATCH by chance, so a WATCH is a hypothesis, not a
rule. Per-feature results are reported for all buckets regardless.

Features (bucket edges in brackets):
  wait      fill-time  minutes from signal close to fill    [<=2 | 3-5 | 6-15 | 16-45 | 46+]
  excur     fill-time  furthest run beyond the level before the retest, in R
                       (how far the break displaced before pulling back)  [<0.5 | 0.5-1 | 1-2 | 2+]
  sig_vol   signal     signal candle volume / median of prior 20 1m bars [<1 | 1-2 | 2-4 | 4+]
  stop_atr  signal     structural stop / median 1m range of prior 20 bars [<1 | 1-2 | 2-3 | 3+]
  body      signal     signal candle body / range                        [<0.4 | 0.4-0.7 | 0.7+]
  near_stat signal     pts to the nearest OTHER static level (8-level set) [<10 | 10-25 | 25-50 | 50+]
  near_vwap signal     pts to the nearest vwap band (excl. own band)     [<5 | 5-15 | 15-30 | 30+]
  room      signal     another static level sits between entry and 1R target [blocked | clear]
  pd_shape  signal     prior-day close in its range x direction
                       [with_pd_trend | against_pd_trend | pd_range]
  day_r     signal     this book's cumulative R today before the trade  [<-1 | -1..0 | first | 0..2 | 2+]
  sess_pct  signal     session range so far / prior-day range           [<0.25 | .25-.5 | .5-1 | 1+]
  agree     signal     the OTHER book's open position at signal time
                       [same_dir_le5 (G3 zone) | same_dir_gt5 | opp_dir | flat]
  excur_x_stop         two-way check that excur is not stop width in disguise (reference)
  hour      signal     ET hour of the signal (reference ladder, already known)
  family    -          level family / vwap band (reference ladder, already known)

WR = TARGET/(TARGET+STOP); EV = mean NET R over ALL trades (SAR/FLAT in),
net = the receipts' 0.5pt/RT cost against each trade's own stop.
Output: printed tables + output/analysis/conviction_audit.json
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402
from scripts.agent_context import (anchored_weekly_profile,       # noqa: E402
                                   volume_profile)
from scripts.pd_va_backtest import merge_levels                   # noqa: E402
from src.htf_ma.levels import vwap_bands                          # noqa: E402

MID = "2024-10-21"
TICK = 0.25
FLOOR = 5.0
BANDS = ("vwap", "vwap_p1", "vwap_p2", "vwap_m1", "vwap_m2")
LV_DUMP = ROOT / "output/analysis/pd_va_trades_lvall_xr30_sar_through_tf1_ng.jsonl.gz"
VW_DUMP = ROOT / "output/analysis/vwap_rev_tf1_retest_xr30.jsonl.gz"
OUT = ROOT / "output/analysis/conviction_audit.json"

# ---- fixed buckets -------------------------------------------------------
def b_wait(m):
    return "<=2" if m <= 2 else "3-5" if m <= 5 else "6-15" if m <= 15 \
        else "16-45" if m <= 45 else "46+"


def b_excur(x):
    return "<0.5R" if x < 0.5 else "0.5-1R" if x < 1 else "1-2R" if x < 2 else "2R+"


def b_vol(x):
    return "<1x" if x < 1 else "1-2x" if x < 2 else "2-4x" if x < 4 else "4x+"


def b_atr(x):
    return "<1x" if x < 1 else "1-2x" if x < 2 else "2-3x" if x < 3 else "3x+"


def b_body(x):
    return "<0.4" if x < 0.4 else "0.4-0.7" if x < 0.7 else "0.7+"


def b_stat(x):
    return "<10" if x < 10 else "10-25" if x < 25 else "25-50" if x < 50 else "50+"


def b_vw(x):
    return "<5" if x < 5 else "5-15" if x < 15 else "15-30" if x < 30 else "30+"


def b_dayr(x, first):
    if first:
        return "first"
    return "<-1" if x < -1 else "-1..0" if x < 0 else "0..2" if x < 2 else "2+"


def b_sess(x):
    return "<0.25" if x < 0.25 else ".25-.5" if x < 0.5 else ".5-1" if x < 1 else "1+"


# extreme-bucket pairs the verdict rule compares (low side, high side)
EXTREMES = {
    "wait": ("<=2", "46+"), "excur": ("<0.5R", "2R+"), "sig_vol": ("<1x", "4x+"),
    "stop_atr": ("<1x", "3x+"), "body": ("<0.4", "0.7+"),
    "near_stat": ("<10", "50+"), "near_vwap": ("<5", "30+"),
    "room": ("blocked", "clear"), "pd_shape": ("against_pd_trend", "with_pd_trend"),
    "day_r": ("<-1", "2+"), "sess_pct": ("<0.25", "1+"),
    "agree": ("opp_dir", "same_dir_gt5"),
}


COST_PTS = 0.5      # per round trip per contract, as in every receipt


def load(path, filt=None):
    """Trades with the receipts' cost overlay: r_net = r - 0.5pt / stop."""
    out = []
    with gzip.open(path, "rt") as fh:
        for line in fh:
            t = json.loads(line)
            if filt is None or filt(t):
                t["r_raw"] = t["r"]
                t["r"] = round(t["r"] - COST_PTS / t["risk"], 4)
                out.append(t)
    return out


def day_levels(bars, day, t0):
    """The 8-level static set exactly as the sim builds it (post-merge)."""
    prev_t0 = t0 - pd.Timedelta(days=1)
    # the sim uses the previous SESSION day; walk back over weekends
    for back in (1, 2, 3, 4):
        prev_t0 = t0 - pd.Timedelta(days=back)
        pseg = bars[(bars.index >= prev_t0) & (bars.index < t0)]
        if len(pseg) >= 300:
            break
    if len(pseg) < 300:
        return None, None
    poc_, val, vah = volume_profile(pseg, bin_w=1.0)
    if not (np.isfinite(vah) and np.isfinite(val)):
        return None, None
    fams = {"va": (vah, val),
            "pdhl": (float(pseg.high.max()), float(pseg.low.min())),
            "poc": (poc_, np.nan)}
    try:
        aw = anchored_weekly_profile(bars, day, upto=t0 + pd.Timedelta(hours=1))
        fams["wva"] = (float(aw["awVAH"]), float(aw["awVAL"]))
        fams["wpoc"] = (float(aw["awPOC"]), np.nan)
    except Exception:
        pass
    fams = {f: (round(v1 / TICK) * TICK if np.isfinite(v1) else np.nan,
                round(v2 / TICK) * TICK if np.isfinite(v2) else np.nan)
            for f, (v1, v2) in fams.items()}
    fams, _ = merge_levels(fams, FLOOR)
    levels = [v for pair in fams.values() for v in pair if np.isfinite(v)]
    pd_meta = {"pd_hi": float(pseg.high.max()), "pd_lo": float(pseg.low.min()),
               "pd_close": float(pseg.close.iloc[-1])}
    return np.array(sorted(levels)), pd_meta


def intervals(trades):
    """(fill_hrs, end_hrs, dir) per day for the cross-book 'agree' feature."""
    by = defaultdict(list)
    for t in trades:
        by[t["day"]].append((t["fill_hrs"], t["fill_hrs"] + t["hold_min"] / 60.0,
                             t["dir"], t["entry"]))
    return by


def other_state(ivs, hrs, own_dir, own_px):
    """Position the OTHER book holds at this signal. same_dir is split by
    entry distance: <=5pt is the zone G3 already bans; >5pt is new."""
    for f, e, d, px in ivs:
        if f <= hrs <= e:
            if d != own_dir:
                return "opp_dir"
            return "same_dir_le5" if abs(px - own_px) <= FLOOR else "same_dir_gt5"
    return "flat"


CHECK = defaultdict(int)


def featurize(book, trades, other, bars):
    """Attach feature buckets to each trade in place. book: 'lv' | 'vw'."""
    by_day = defaultdict(list)
    for t in trades:
        by_day[t["day"]].append(t)
    other_iv = intervals(other)
    n_done = 0
    for day, tl in by_day.items():
        t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
        sess = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=23))]
        if len(sess) < 600:
            continue
        ts = sess.index.view("int64")
        op = sess.open.to_numpy(); hi = sess.high.to_numpy()
        lo = sess.low.to_numpy(); cl = sess.close.to_numpy()
        vol = sess.volume.to_numpy().astype(float)
        rng = hi - lo
        levels, pdm = day_levels(bars, day, t0)
        vw = vwap_bands(sess)
        vwa = {b: vw[b].to_numpy() for b in BANDS}
        pd_range = (pdm["pd_hi"] - pdm["pd_lo"]) if pdm else np.nan
        pd_pos = ((pdm["pd_close"] - pdm["pd_lo"]) / pd_range
                  if pdm and pd_range > 0 else np.nan)
        cum_r = 0.0
        tl.sort(key=lambda t: t["t_sig_hrs"])
        for k, t in enumerate(tl):
            d = t["dir"]; L = t["entry"]; risk = t["risk"]
            # the dump rounds hrs to 3dp (+-1.8s): snap to the exact minute
            # or half the trades index one bar late - and for a next-bar
            # fill that late bar IS the fill bar (lookahead). Verified below.
            t_sig = t0.value + int(round(t["t_sig_hrs"] * 60)) * 60_000_000_000
            t_fill = t0.value + int(round(t["fill_hrs"] * 60)) * 60_000_000_000
            si = int(np.searchsorted(ts, t_sig)) - 1        # bar ENDING at t_sig
            fi = int(np.searchsorted(ts, t_fill))           # bar STARTING at t_fill
            si = max(min(si, len(ts) - 1), 0); fi = max(min(fi, len(ts) - 1), si + 1)
            CHECK["n"] += 1
            if ts[si] != t_sig - 60_000_000_000:
                CHECK["sig_gap"] += 1        # missing bar before the signal end
            if ts[fi] != t_fill:
                CHECK["fill_mis"] += 1
            if fi <= si:
                CHECK["fill_le_sig"] += 1
            f = {}
            # fill-time
            f["wait"] = b_wait((t["fill_hrs"] - t["t_sig_hrs"]) * 60)
            seg_hi, seg_lo = hi[si:fi], lo[si:fi]         # signal bar .. bar before fill
            ex = (seg_hi.max() - L) if d == 1 else (L - seg_lo.min())
            f["excur"] = b_excur(max(ex, 0.0) / risk)
            # signal-time
            lo20 = max(si - 20, 0)
            mv = np.median(vol[lo20:si]) if si > lo20 else np.nan
            mr = np.median(rng[lo20:si]) if si > lo20 else np.nan
            f["sig_vol"] = b_vol(vol[si] / mv) if mv and mv > 0 else None
            f["stop_atr"] = b_atr(risk / mr) if mr and mr > 0 else None
            f["body"] = b_body(abs(cl[si] - op[si]) / rng[si]) if rng[si] > 0 else None
            if levels is not None and len(levels):
                dist = np.abs(levels - L)
                others = dist[dist > 0.5] if book == "lv" else dist
                f["near_stat"] = b_stat(others.min()) if len(others) else "50+"
                tgt = L + d * risk
                lo_p, hi_p = (min(L, tgt), max(L, tgt))
                between = levels[(levels > lo_p + 0.5) & (levels < hi_p - 0.5)]
                f["room"] = "blocked" if len(between) else "clear"
            else:
                f["near_stat"] = None; f["room"] = None
            bv = np.array([vwa[b][si] for b in BANDS])
            bv = bv[np.isfinite(bv)]
            if book == "vw":
                own = np.abs(bv - L)
                bv = bv[own > 0.5]
            f["near_vwap"] = b_vw(np.abs(bv - L).min()) if len(bv) else None
            if np.isfinite(pd_pos):
                if pd_pos > 0.7:
                    f["pd_shape"] = "with_pd_trend" if d == 1 else "against_pd_trend"
                elif pd_pos < 0.3:
                    f["pd_shape"] = "with_pd_trend" if d == -1 else "against_pd_trend"
                else:
                    f["pd_shape"] = "pd_range"
            else:
                f["pd_shape"] = None
            f["day_r"] = b_dayr(cum_r, k == 0)
            sr = hi[:si + 1].max() - lo[:si + 1].min()
            f["sess_pct"] = b_sess(sr / pd_range) if pd_range and pd_range > 0 else None
            f["agree"] = other_state(other_iv.get(day, []), t["t_sig_hrs"], d, L)
            f["excur_x_stop"] = f"{f['excur']} | stop {f['stop_atr']}" if f["stop_atr"] else None
            h = int((t["t_sig_hrs"] + 18) % 24)
            f["hour"] = f"{h:02d}"
            f["family"] = t.get("family") or t.get("band")
            t["feat"] = f
            cum_r += t["r"]
            n_done += 1
    return n_done


def table(trades, feat):
    agg = defaultdict(lambda: {"iw": 0, "il": 0, "ir": [], "ow": 0, "ol": 0, "or": []})
    for t in trades:
        b = t.get("feat", {}).get(feat)
        if b is None:
            continue
        a = agg[b]
        oos = t["day"] >= MID
        if t["res"] == "TARGET":
            a["ow" if oos else "iw"] += 1
        elif t["res"] == "STOP":
            a["ol" if oos else "il"] += 1
        a["or" if oos else "ir"].append(t["r"])
    rep = {}
    for b, a in agg.items():
        def wr(w, l):
            return round(w / (w + l), 3) if (w + l) else None
        rep[b] = {"is_n": len(a["ir"]), "is_wr": wr(a["iw"], a["il"]),
                  "is_ev": round(float(np.mean(a["ir"])), 4) if a["ir"] else None,
                  "oos_n": len(a["or"]), "oos_wr": wr(a["ow"], a["ol"]),
                  "oos_ev": round(float(np.mean(a["or"])), 4) if a["or"] else None,
                  "n": len(a["ir"]) + len(a["or"]),
                  "ev": round(float(np.mean(a["ir"] + a["or"])), 4) if (a["ir"] or a["or"]) else None,
                  "wr": wr(a["iw"] + a["ow"], a["il"] + a["ol"])}
    return rep


def verdict(rep, feat):
    """The preregistered rule, applied mechanically."""
    cuts = [b for b, v in rep.items()
            if v["is_n"] >= 400 and v["oos_n"] >= 400
            and v["is_ev"] is not None and v["oos_ev"] is not None
            and v["is_ev"] < 0 and v["oos_ev"] < 0]
    if feat not in EXTREMES:
        return "REFERENCE", cuts
    lo, hi = EXTREMES[feat]
    if lo not in rep or hi not in rep:
        return "NULL (bucket missing)", cuts
    a, b = rep[lo], rep[hi]
    if min(a["is_n"], a["oos_n"], b["is_n"], b["oos_n"]) < 400:
        return "NULL (n<400)", cuts
    d_is = b["is_ev"] - a["is_ev"]
    d_oos = b["oos_ev"] - a["oos_ev"]
    if np.sign(d_is) != np.sign(d_oos) or d_is == 0:
        return "NULL (sign flips)", cuts
    m = min(abs(d_is), abs(d_oos))
    tag = "SURVIVOR" if m >= 0.05 else "WATCH" if m >= 0.03 else "NULL (spread<0.03)"
    side = hi if d_is > 0 else lo
    return f"{tag} (better: {side}; spread IS {d_is:+.3f} / OOS {d_oos:+.3f})", cuts


def print_table(name, feat, rep, verd):
    print(f"\n[{name}] {feat}  ->  {verd[0]}" + (f"   CUT candidates: {verd[1]}" if verd[1] else ""))
    print(f"  {'bucket':<18}{'n':>7}{'WR':>7}{'EV':>8} | {'IS n':>6}{'IS WR':>7}{'IS EV':>8} | {'OOS n':>6}{'OOS WR':>7}{'OOS EV':>8}")
    order = sorted(rep, key=lambda b: -rep[b]["n"])
    for b in order:
        v = rep[b]
        fmt = lambda x, w: f"{x:>{w}}" if x is None else f"{x:>{w}.3f}"
        print(f"  {b:<18}{v['n']:>7}{fmt(v['wr'],7)}{fmt(v['ev'],8)} | {v['is_n']:>6}{fmt(v['is_wr'],7)}{fmt(v['is_ev'],8)} | {v['oos_n']:>6}{fmt(v['oos_wr'],7)}{fmt(v['oos_ev'],8)}")


def main() -> int:
    bars = OB.get_bars()
    lv = load(LV_DUMP)
    vw = load(VW_DUMP, lambda t: t["depth"] == 3.0 and t["target_r"] == 1.0)
    print(f"level book: {len(lv):,} trades   vwap book: {len(vw):,} trades", flush=True)
    n1 = featurize("lv", lv, vw, bars)
    n2 = featurize("vw", vw, lv, bars)
    print(f"featurized {n1:,} level trades, {n2:,} vwap trades", flush=True)
    print(f"index sanity: {dict(CHECK)}  (sig_gap = the bar before the signal end "
          f"is missing; fill_mis = fill bar start != dump fill time; both must be ~0)", flush=True)
    feats = ["wait", "excur", "sig_vol", "stop_atr", "body", "near_stat",
             "near_vwap", "room", "pd_shape", "day_r", "sess_pct", "agree",
             "excur_x_stop", "hour", "family"]
    report = {}
    for name, trades in (("8-LEVEL", lv), ("VWAP", vw)):
        for feat in feats:
            rep = table(trades, feat)
            verd = verdict(rep, feat)
            print_table(name, feat, rep, verd)
            report.setdefault(name, {})[feat] = {"verdict": verd[0], "cuts": verd[1],
                                                 "buckets": rep}
    # ---- POST-HOC what-ifs (estimates only; the in-engine run is the receipt)
    print("\nPOST-HOC WHAT-IF (chronological, no re-simulation; a skipped trade")
    print("frees the book so in-engine numbers will differ - see S34 for how much)")
    for name, trades in (("8-LEVEL", lv), ("VWAP", vw)):
        tot = sum(t["r"] for t in trades)
        for label, keep in (
            ("arm limit only after price runs >=1R past the level (excur>=1R)",
             lambda t: t["feat"].get("excur") in ("1-2R", "2R+")),
            ("skip when other book holds same-dir position at ANY distance",
             lambda t: not str(t["feat"].get("agree", "")).startswith("same_dir")),
            ("skip when other book holds same-dir position >5pt away only",
             lambda t: t["feat"].get("agree") != "same_dir_gt5"),
        ):
            kept = [t for t in trades if keep(t)]
            kr = sum(t["r"] for t in kept)
            is_d = sum(t["r"] for t in trades if t["day"] < MID and not keep(t))
            oos_d = sum(t["r"] for t in trades if t["day"] >= MID and not keep(t))
            print(f"  {name:<8} {label}")
            print(f"           keeps {len(kept):,}/{len(trades):,} trades, net R {tot:+.0f} -> {kr:+.0f} "
                  f"(dropped trades: IS {is_d:+.0f}R, OOS {oos_d:+.0f}R); "
                  f"EV/trade {tot/len(trades):+.4f} -> {kr/len(kept):+.4f}")
    OUT.write_text(json.dumps(report, indent=1))
    print(f"\n-> {OUT}")
    # summary
    print("\nSUMMARY (preregistered rule)")
    for name in report:
        for feat, v in report[name].items():
            if v["verdict"].startswith(("SURVIVOR", "WATCH")) or v["cuts"]:
                print(f"  {name:<8} {feat:<10} {v['verdict']}" + (f"  CUTS={v['cuts']}" if v["cuts"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
