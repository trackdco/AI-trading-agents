#!/usr/bin/env python3
"""RAW BASELINE — `orb-fvg-nyopen`. NY opening-range breakout into a 1-minute FVG.

⚠️ LOW PROVENANCE. The entire source is ONE social-media post (research/orb-fvg/SOURCE-POST.md).
There is no transcript, no worked example, and nothing to re-read, so NOTHING here can be
self-resolved. Every rule the post leaves blank is filled by US and tagged below.

THIS IS AN ADAPTATION OF A POSTED TEMPLATE, NOT A TEST OF THE POSTER'S METHOD. No number this
file produces is evidence for or against what he posted.

============================== THE POST, VERBATIM ==========================================
"Mark NY session high/low and overnight high/low. Wait for the first 5-minute candle of the NY
 open to close. Drop to the 1-minute chart, watch for a clean breakout. Look for an FVG forming
 in the direction of the break. Enter on confirmation, stop above/below that candle, target
 1.5-2R. Management: move stop to BE once internal liquidity is taken; max 2 trades/day; stop
 for the day after a win; one more attempt after a BE or loss."
============================================================================================

[S]=stated in the post  [U]=stated-by-user (Brake)  [A]=OUR assumption  [LOCK]=locked convention

O0  WINDOW [U]        09:30-10:30 ET, span 2025-06-01 -> 2026-07-15.
                      The post gives a START and NO END. The 60-minute span is Brake's.
                      ⚠️ This deliberately breaks the standing 09:45-10:15 macro rule that binds
                      every ash-*/zxck-* card. Windows therefore OVERLAP but are NOT identical.

O1  OPENING RANGE [S] the first 5-minute candle of the NY open = the 09:30, 09:31, 09:32, 09:33
                      and 09:34 one-minute bars. High/low frozen at 09:35. Unambiguous.

O2  BREAKOUT [S/A]    "a clean breakout" -- CLEAN IS NEVER DEFINED and no disqualifier is given.
                      [A] PRIMARY: a 1-minute bar CLOSES beyond the opening range.
                      [A] SENSITIVITY: a 1-minute bar merely TRADES beyond it (wick-through).
                      The close reading has a useful property: a single bar cannot close both
                      above and below, so it produces NO ambiguous sessions. The wick reading can,
                      and those sessions are counted and excluded from that arm.

O3  FVG [S/A]         "an FVG forming in the direction of the break". [A] standard 3-bar FVG on
                      the 1-minute, third bar at or after the breakout bar:
                        long : bar[j-2].high < bar[j].low   -> gap (bar[j-2].high, bar[j].low)
                        short: bar[j-2].low  > bar[j].high  -> gap (bar[j].high,  bar[j-2].low)
                      The post does not say how long the FVG search stays open; [A] it stays open
                      until the window ends or the opposite side of the range breaks.

O4  ENTRY [S/UNDEFINED -> BOUNDED]
                      "Enter on confirmation" -- CONFIRMATION OF WHAT? No antecedent exists.
                      Both live readings are RUN, neither is chosen:
                        RETRACE   limit at the gap's NEAR edge, first return after the gap closes
                        FORMATION market entry at the CLOSE of the FVG's third bar
                      A third reading (close THROUGH the gap) is a strict subset of RETRACE on
                      event count and is not run.

O5  STOP [S/UNDEFINED -> BOUNDED]
                      "stop above/below that candle" -- WHICH candle? Both are run:
                        BREAKOUT  beyond the breakout candle's extreme
                        FVG       beyond the 3-bar FVG pattern's extreme
                      SENSITIVITY only: GAPEDGE, beyond the far edge of the gap itself. This is
                      the literal single-candle reading; zxck-ifvg-50 already showed a stop of
                      that size on NQ here is inside single-bar noise (n=186, t=-4.165). Run so
                      the claim is MEASURED on this card rather than asserted.
                      NOTE: the strictly literal "displacement candle" reading is DEGENERATE --
                      for a long entering at the gap top, that candle's low IS the gap top, so
                      risk = 0. Arithmetically impossible, and itself evidence of under-spec.

O6  TARGET [LOCK]     2R. The post says "1.5-2R", which is a RANGE, i.e. two strategies. 2R is
                      the top of his range and matches every other card, fixed BEFORE the run.
                      The 1.5R arm is NOT tested here.

O7  BREAK-EVEN [LOCK] at 1R. ⛔ THIS REPLACES HIS RULE. He says "move stop to BE once internal
                      liquidity is taken" and NEVER defines internal liquidity. Not implementable.

O8  no trailing [LOCK]   O9 stop-first on a same-bar conflict [LOCK]   O10 16:00 ET cap [LOCK]

O11 SAMPLE [U]        PRIMARY = EVERY qualifying setup. The post's "max 2/day, stop after a win,
                      one more after a BE or loss" is bankroll and tilt management, not edge, and
                      applying it destroys sample. Reported SEPARATELY as a secondary line.

O12 NO FILTERS        The post states none, so we add none. FOMC sessions are NOT excluded
                      (unlike the zxck-* cards, where Powell states the rule himself). `fomc` and
                      `news_day` are LOGGED so the slice stays available to a future prereg.

O13 THE FOUR LEVELS   "Mark NY session high/low and overnight high/low" -- and then NO RULE EVER
                      USES THEM. Declared DECORATIVE AS POSTED. Computed and logged as context
                      features; READ BY NO RULE. Inventing a role would be writing his strategy.

O14 ORDER FLOW        retrace_ratio and disp_delta_magnitude computed on the IDENTICAL
                      definitions used by ash-unicorn-sb and zxck-10am-keyopen. COMPUTED ONLY.
                      No order-flow filter is applied in this pass.
                      Displacement leg = breakout bar -> FVG third bar; retracement = that bar ->
                      entry. NOTE: under FORMATION entry the retracement window is EMPTY BY
                      CONSTRUCTION, so F2 does not exist for that arm. That is a property of the
                      reading, not a data gap.

    python -m scripts.orb_fvg_baseline
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.f2_oos_test import flow_frame  # noqa: E402
from scripts.nya_sb01_feasibility import load_bars  # noqa: E402
from scripts.zxck_keyopen_baseline import FOMC, calendar  # noqa: E402

OPEN_MIN = 9 * 60 + 30           # 09:30 O1
OR_END = 9 * 60 + 34             # 09:34 inclusive -> the first 5-minute candle
WIN_END = 10 * 60 + 30           # 10:30 O0 [U]
RTH_END = 16 * 60                # O10
LO, HI = "2025-06-01", "2026-07-15"
TARGET_R = 2.0                   # O6
COST_USD, PT = 25.0, 20.0
OUT = ROOT / "research/orb-fvg/strategies"

ENTRY_READINGS = ("retrace", "formation")          # O4
STOP_READINGS = ("breakout", "fvg")                # O5 — the bound
STOP_SENSITIVITY = ("gapedge",)                    # O5 — reported apart, not in the bound
BRK_READINGS = ("close", "wick")                   # O2 — "close" is primary


# ------------------------------------------------------------------- levels (O13, decorative)
def marked_levels(g: pd.DataFrame, prev: pd.DataFrame) -> dict:
    """The four levels the post says to mark and then never uses again.

    [A] "NY session high/low" is read as the PREVIOUS session's RTH range, because today's has
    not happened yet at 09:30. "Overnight" is the Globex session into this open.
    COMPUTED AND LOGGED. NO RULE IN THIS FILE READS THEM.
    """
    out = {}
    pdh = prev[(prev.mins >= OPEN_MIN) & (prev.mins <= RTH_END)]
    on = pd.concat([prev[prev.mins > RTH_END], g[g.mins < OPEN_MIN]])
    if len(pdh):
        out["pdh"], out["pdl"] = float(pdh.high.max()), float(pdh.low.min())
    if len(on):
        out["onh"], out["onl"] = float(on.high.max()), float(on.low.min())
    return out


# ------------------------------------------------------------------- events (no outcomes)
def scan_events(w: pd.DataFrame, brk: str) -> tuple[list[dict], dict]:
    """Every (breakout, FVG) event in one session. COUNTS AND GEOMETRY ONLY — no R, no outcome.

    Returns (events, flags). `flags` records the session-level gate state for the funnel.
    """
    flags = {"or_ok": False, "broke": False, "fvg": False, "ambiguous": False}
    if len(w) < 40:
        return [], flags
    orb = w[w.mins <= OR_END]
    if len(orb) != 5:
        return [], flags
    flags["or_ok"] = True
    orh, orl = float(orb.high.max()), float(orb.low.min())

    events, side, b = [], 0, -1
    start = int(orb.index[-1]) + 1
    for i in range(start, len(w)):
        bar = w.iloc[i]
        if brk == "close":
            up, dn = bar.close > orh, bar.close < orl
        else:
            up, dn = bar.high > orh, bar.low < orl
        if up and dn:                       # undecidable from OHLC — only possible on "wick"
            flags["ambiguous"] = True
            return [], flags
        new = +1 if up else (-1 if dn else 0)
        if new and new != side:             # first break, or a break of the opposite side
            side, b = new, i
            flags["broke"] = True
        if not side or i < 2 or i < b:
            continue
        a, c = w.iloc[i - 2], w.iloc[i]     # O3 the 3-bar FVG completing at bar i
        if side > 0 and a.high < c.low:
            near, far = float(c.low), float(a.high)
        elif side < 0 and a.low > c.high:
            near, far = float(c.high), float(a.low)
        else:
            continue
        flags["fvg"] = True
        events.append({"b": b, "j": i, "side": side, "near": near, "far": far,
                       "orh": orh, "orl": orl,
                       "pat_lo": float(w.iloc[i - 2:i + 1].low.min()),
                       "pat_hi": float(w.iloc[i - 2:i + 1].high.max())})
    return events, flags


def resolve(w: pd.DataFrame, ev: dict, entry_reading: str, stop_reading: str):
    """Geometry for one event under one (entry, stop) reading. None if the trade cannot exist."""
    side, j, b = ev["side"], ev["j"], ev["b"]
    if entry_reading == "formation":
        t, entry = j, float(w.iloc[j].close)
        same_bar = False        # entry is AT THE CLOSE — bar j's range is already spent
    else:
        entry = ev["near"]
        fwd = w.iloc[j + 1:]
        hit = (fwd.low <= entry) if side > 0 else (fwd.high >= entry)
        if not len(fwd) or not hit.any():
            return None                       # limit never filled inside the window
        t = int(hit.idxmax())
        same_bar = True         # a limit fills intrabar, so bar t can still reach the stop
    if stop_reading == "breakout":
        stop = float(w.iloc[b].low) if side > 0 else float(w.iloc[b].high)
    elif stop_reading == "fvg":
        stop = ev["pat_lo"] if side > 0 else ev["pat_hi"]
    else:                                     # gapedge — sensitivity only
        stop = ev["far"]
    risk = (entry - stop) * side
    if risk <= 0:
        return None                           # stop on the wrong side of entry -> no trade
    return t, entry, stop, risk, same_bar


def walk_exit(day, t, entry, stop, side, risk, same_bar):
    """LOCKED convention: 2R target, BE at 1R, no trailing, stop-first same bar, 16:00 cap.

    `day` is the PRECOMPUTED contiguous 09:30 -> 16:00 array bundle for this session, so index
    `t` (the entry bar, positioned inside the 09:30-10:30 window) indexes straight into it and
    the tail is simply everything after t. Identical semantics to the pandas version it replaced;
    numpy only because 12 arms x every event was too slow to iterate rows.
    """
    lo, hi, cl, ts = day["low"], day["high"], day["close"], day["ts"]
    target, half = entry + side * TARGET_R * risk, entry + side * risk
    if same_bar:
        if (lo[t] <= stop) if side > 0 else (hi[t] >= stop):
            return -1.0, stop, False, ts[t]
    cur, be = stop, False
    for i in range(t + 1, len(lo)):
        if side > 0:
            if lo[i] <= cur:
                return (0.0 if be else -1.0), cur, be, ts[i]
            if hi[i] >= target:
                return TARGET_R, target, be, ts[i]
            if not be and hi[i] >= half:
                cur, be = entry, True
        else:
            if hi[i] >= cur:
                return (0.0 if be else -1.0), cur, be, ts[i]
            if lo[i] <= target:
                return TARGET_R, target, be, ts[i]
            if not be and lo[i] <= half:
                cur, be = entry, True
    if len(lo) <= t + 1:
        return 0.0, entry, be, ts[t]
    last = float(cl[-1])
    return float(side * (last - entry) / risk), last, be, ts[-1]


def flow_feats(fpd, w, ev, t, side):
    """O14 — IDENTICAL definitions to ash-unicorn-sb / zxck-10am-keyopen.

    displacement = breakout bar -> FVG third bar;  retracement = that bar -> entry bar.
    F1 is normalised by the session's median minute volume up to the entry, exactly as there.
    Reads NOTHING after the entry minute; asserted.
    """
    t0, t1, te = w.ts.iloc[ev["b"]], w.ts.iloc[ev["j"]], w.ts.iloc[t]
    disp = fpd[(fpd.index >= t0) & (fpd.index <= t1)]
    ret = fpd[(fpd.index > t1) & (fpd.index <= te)]
    sess = fpd[(fpd.index >= w.ts.iloc[0]) & (fpd.index <= te)].vol
    assert not len(disp) or disp.index.max() <= te
    assert not len(ret) or ret.index.max() <= te
    med = float(sess.median()) if len(sess) else np.nan
    f1 = float(disp.delta.sum()) * side / med if (len(disp) and med) else np.nan
    dv, rv = float(disp.vol.sum()), float(ret.vol.sum())
    f2 = rv / dv if dv > 0 and len(ret) else np.nan
    return f1, f2


# ------------------------------------------------------------------------------- the run
def run(bars, fp, cal):
    fomc = set(cal[cal.event.str.contains("|".join(FOMC), case=False, na=False)]
               .dt.dt.strftime("%Y-%m-%d"))
    news = set(cal.dt.dt.strftime("%Y-%m-%d"))
    dly = bars.groupby("day").agg(high=("high", "max"), low=("low", "min"))
    atr = (dly.high - dly.low).rolling(14).mean().shift(1).rank(pct=True)

    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    days = sorted(by_day)
    # Pre-slice the footprint by session date. Slicing the full ~500k-row frame once per event
    # per arm was the bottleneck; the per-day frame is ~1.4k rows and the semantics are identical
    # because every window this file reads lies inside one session date.
    fp_by_day = {d: x for d, x in fp.groupby(fp.index.strftime("%Y-%m-%d"))}
    rows = []
    funnel = {brk: {"sessions": 0, "or_ok": 0, "broke": 0, "fvg": 0, "ambiguous": 0,
                    "events": 0} for brk in BRK_READINGS}

    for k, day in enumerate(days):
        if not k or day < LO or day > HI:
            continue
        g, prev = by_day[day], by_day[days[k - 1]]
        # ONE contiguous 09:30 -> 16:00 block. `w` is its leading 09:30-10:30 slice, so an entry
        # index inside `w` indexes straight into `dayarr` and the exit tail is everything after.
        post = g[(g.mins >= OPEN_MIN) & (g.mins <= RTH_END)].reset_index(drop=True)
        w = post[post.mins <= WIN_END].reset_index(drop=True)
        if len(w) < 40 or not len(post):
            continue
        dayarr = {"low": post.low.to_numpy(), "high": post.high.to_numpy(),
                  "close": post.close.to_numpy(), "ts": post.ts.to_numpy()}
        fpd = fp_by_day.get(day, fp.iloc[:0])
        lv = marked_levels(g, prev)
        pre = g[g.mins < OPEN_MIN]
        h1 = float(pre.close.iloc[-1] - pre.close.iloc[-120]) if len(pre) > 120 else np.nan
        phi = float(pre.high.max()) if len(pre) else np.nan
        plo = float(pre.low.min()) if len(pre) else np.nan

        for brk in BRK_READINGS:
            funnel[brk]["sessions"] += 1
            events, flags = scan_events(w, brk)
            for key in ("or_ok", "broke", "fvg", "ambiguous"):
                funnel[brk][key] += int(flags[key])
            funnel[brk]["events"] += len(events)
            for n_ev, ev in enumerate(events):
                for er, sr in itertools.product(
                        ENTRY_READINGS, STOP_READINGS + STOP_SENSITIVITY):
                    res = resolve(w, ev, er, sr)
                    if res is None:
                        continue
                    t, entry, stop, risk, same_bar = res
                    side = ev["side"]
                    R, ex, be, ex_ts = walk_exit(dayarr, t, entry, stop, side, risk, same_bar)
                    f1, f2 = flow_feats(fpd, w, ev, t, side)
                    rows.append({
                        "arm_brk": brk, "arm_entry": er, "arm_stop": sr,
                        "date": day, "time": f"{w.ts.iloc[t]:%H:%M}",
                        "seq_in_day": n_ev,
                        "direction": "long" if side > 0 else "short",
                        "entry": round(entry, 2), "stop": round(stop, 2),
                        "target": round(entry + side * TARGET_R * risk, 2),
                        "exit": round(float(ex), 2),
                        "exit_time": f"{pd.Timestamp(ex_ts):%H:%M}",
                        "risk_pts": round(risk, 2), "R": round(R, 3),
                        "outcome": "win" if R >= TARGET_R else ("BE" if R == 0 else
                                   ("loss" if R <= -1 else "timeout")),
                        "be_moved": be,
                        # ---- context features, identical names to the other logs ----
                        "dow": pd.Timestamp(day).day_name()[:3],
                        "entry_min_into_window": int(w.mins.iloc[t] - OPEN_MIN),
                        "atr_pct": float(atr.get(day, np.nan)),
                        "htf_aligned": int((h1 > 0) == (side > 0)) if h1 == h1 else np.nan,
                        "dist_to_level_R": (round(min(abs(entry - phi), abs(entry - plo)) / risk,
                                                  3) if phi == phi else np.nan),
                        "news_day": int(day in news), "fomc": int(day in fomc),
                        "risk_pts_v": round(risk, 2), "direction_long": int(side > 0),
                        "F1_disp_delta": round(f1, 3) if f1 == f1 else np.nan,
                        "disp_delta_magnitude": round(abs(f1), 3) if f1 == f1 else np.nan,
                        "F2_retrace_ratio": round(f2, 3) if f2 == f2 else np.nan,
                        "retrace_ratio": round(f2, 3) if f2 == f2 else np.nan,
                        # ---- O13 decorative levels: logged, read by no rule ----
                        "or_high": round(ev["orh"], 2), "or_low": round(ev["orl"], 2),
                        **{f"dist_to_{n}_R": (round(abs(entry - lv[n]) / risk, 3)
                                              if n in lv else np.nan)
                           for n in ("pdh", "pdl", "onh", "onl")},
                    })
    return pd.DataFrame(rows), funnel


# ------------------------------------------------------------------------------- reporting
def cap_rules(d: pd.DataFrame) -> pd.DataFrame:
    """O11 SECONDARY — his management: max 2/day, stop after a win, one more after BE/loss."""
    keep = []
    for _, day in d.sort_values(["date", "time", "seq_in_day"]).groupby("date"):
        taken = 0
        for i, r in day.iterrows():
            if taken >= 2:
                break
            keep.append(i)
            taken += 1
            if r.R >= TARGET_R:          # "stop for the day after a win"
                break
    return d.loc[keep]


def summarise(d: pd.DataFrame, label: str) -> dict:
    """⚠️ `t` here is the SESSION-CLUSTERED t, not the naive one.

    This card produces ~6-7 setups per session, all inside one 60-minute window, mostly in the
    same direction, overlapping in time. Those are NOT independent draws, so the ordinary
    t = mean/(sd/sqrt(n)) is badly overstated -- it would treat 1,900 correlated observations as
    1,900 independent ones. `t_naive` is kept only so the size of that overstatement is visible.

    The clustered SE is the standard cluster-robust variance for a mean, clustering on session
    date:  SE = sqrt( sum_c ( sum_{i in c} (R_i - Rbar) )^2 ) / n.
    """
    n = len(d)
    if not n:
        return {"arm": label, "n": 0}
    cost = float((COST_USD / (d.risk_pts * PT)).mean())
    eq = d.R.cumsum()
    mean = float(d.R.mean())
    sd = float(d.R.std(ddof=1))
    t_naive = mean / (sd / np.sqrt(n)) if sd and n > 1 else np.nan
    dev = d.R - mean
    cl = dev.groupby(d.date).sum().to_numpy()
    nc = len(cl)
    se_cl = np.sqrt((cl ** 2).sum()) / n if nc > 1 else np.nan
    # small-cluster correction, the usual nc/(nc-1) finite-cluster adjustment
    se_cl = se_cl * np.sqrt(nc / (nc - 1)) if nc > 1 else np.nan
    t_cl = mean / se_cl if se_cl and se_cl == se_cl else np.nan
    res = 100 * float(((d.R > -1) & (d.R < TARGET_R) & (d.R != 0)).mean())
    return {"arm": label, "n": n, "sessions": nc, "per_session": n / nc if nc else np.nan,
            "win%": 100 * float((d.R >= TARGET_R).mean()),
            "BE%": 100 * float((d.R == 0).mean()),
            "loss%": 100 * float((d.R <= -1).mean()), "timeout%": res,
            "avgR": mean, "cost": cost, "exp": mean - cost,
            "totR": float(d.R.sum()), "maxDD": float((eq.cummax() - eq).max()),
            "med_stop": float(d.risk_pts.median()), "t": t_cl, "t_naive": t_naive,
            "effect": t_cl / np.sqrt(nc) if t_cl == t_cl else np.nan}


def show(rows: list[dict], title: str) -> None:
    print(f"\n{title}")
    hdr = (f"  {'arm':<32}{'n':>6}{'/sess':>6}{'win/BE/loss/TO':>24}{'avgR':>8}{'cost':>7}"
           f"{'exp':>9}{'totR':>9}{'DD':>7}{'stop':>7}{'t_clus':>8}{'t_naive':>9}")
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for r in rows:
        if not r["n"]:
            print(f"  {r['arm']:<32}{0:>6}   no trades"); continue
        mix = "%.1f/%.1f/%.1f/%.1f" % (r["win%"], r["BE%"], r["loss%"], r["timeout%"])
        flag = "" if r["n"] >= 30 else "   <30 UNTESTABLE"
        print(f"  {r['arm']:<32}{r['n']:>6}{r['per_session']:>6.1f}{mix:>24}"
              f"{r['avgR']:>+8.3f}{r['cost']:>7.3f}"
              f"{r['exp']:>+9.3f}{r['totR']:>+9.1f}{r['maxDD']:>7.1f}"
              f"{r['med_stop']:>7.1f}{r['t']:>+8.2f}{r['t_naive']:>+9.2f}{flag}")


def main() -> None:
    bars = load_bars()
    fp = flow_frame()
    d, funnel = run(bars, fp, calendar())
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "orb-fvg-nyopen-raw-trades.csv"
    d.to_csv(p, index=False)

    print("RAW BASELINE — orb-fvg-nyopen.  ⚠️ LOW PROVENANCE: one social post, no corpus.")
    print("ADAPTATION of a posted template under OUR conventions — NOT a test of his method.\n")
    print(f"instrument NQ 1-min   window 09:30-10:30 ET [stated-by-user]   span {LO} -> {HI}")
    print("exit: LOCKED convention (2R, BE at 1R, no trailing, stop-first, 16:00 cap)")
    print("his BE trigger ('internal liquidity is taken') was UNDEFINED and is REPLACED.\n")

    print("GATE FUNNEL — counts only, no outcomes")
    print(f"  {'gate':<46}{'close-brk':>12}{'wick-brk':>12}")
    print("  " + "-" * 70)
    for key, lab in (("sessions", "0. sessions in span"),
                     ("or_ok", "1. + a complete 5x1min opening range"),
                     ("broke", "2. + the range broke"),
                     ("fvg", "3. + an FVG formed in the break direction"),
                     ("events", "   => (breakout, FVG) EVENTS generated"),
                     ("ambiguous", "   sessions dropped: both sides on one bar")):
        print(f"  {lab:<46}{funnel['close'][key]:>12}{funnel['wick'][key]:>12}")

    prim = d[d.arm_brk == "close"]
    bound = [summarise(prim[(prim.arm_entry == er) & (prim.arm_stop == sr)],
                       f"entry={er:<9} stop={sr}")
             for er, sr in itertools.product(ENTRY_READINGS, STOP_READINGS)]
    show(bound, "PRIMARY BOUND — every qualifying setup, close-through breakout (4 arms)")
    lo_, hi_ = min(r["exp"] for r in bound), max(r["exp"] for r in bound)
    print(f"\n  BOUND ON EXPECTANCY: [{lo_:+.3f}R, {hi_:+.3f}R]"
          f"   -> {'ENTIRELY NEGATIVE' if hi_ < 0 else ('ENTIRELY POSITIVE' if lo_ > 0 else 'STRADDLES ZERO')}")

    show([summarise(cap_rules(prim[(prim.arm_entry == er) & (prim.arm_stop == sr)]),
                    f"entry={er:<9} stop={sr}")
          for er, sr in itertools.product(ENTRY_READINGS, STOP_READINGS)],
         "SECONDARY — his management applied (max 2/day, stop after a win)")

    def first_per_session(a):
        """The first TRADE of each session, not the first EVENT index -- an event that produced
        no trade in this arm (limit unfilled, or stop on the wrong side) must not consume the
        slot, or the arms would be sampling different sessions."""
        return a.sort_values(["date", "time", "seq_in_day"]).groupby("date", as_index=False).head(1)

    show([summarise(first_per_session(prim[(prim.arm_entry == er) & (prim.arm_stop == sr)]),
                    f"entry={er:<9} stop={sr}")
          for er, sr in itertools.product(ENTRY_READINGS, STOP_READINGS)],
         "SECONDARY — FIRST trade of each session only (ONE per session: independent draws)")

    show([summarise(prim[(prim.arm_entry == er) & (prim.arm_stop == "gapedge")],
                    f"entry={er:<9} stop=gapedge")
          for er in ENTRY_READINGS],
         "SENSITIVITY — the literal gap-far-edge stop (zxck-ifvg-50's failure mode)")

    wick = d[d.arm_brk == "wick"]
    show([summarise(wick[(wick.arm_entry == er) & (wick.arm_stop == sr)],
                    f"entry={er:<9} stop={sr}")
          for er, sr in itertools.product(ENTRY_READINGS, STOP_READINGS)],
         "SENSITIVITY — wick-through breakout instead of close-through")

    print("\nFLOW COVERAGE (computed, applied to nothing)")
    for er in ENTRY_READINGS:
        a = prim[prim.arm_entry == er]
        print(f"  entry={er:<10} n={len(a):>4}   F1 present {int(a.F1_disp_delta.notna().sum()):>4}"
              f"   F2 present {int(a.F2_retrace_ratio.notna().sum()):>4}")
    print("  F2 is EMPTY BY CONSTRUCTION under formation entry — there is no retracement to "
          "measure.\n")
    print(f"trades -> {p}  ({len(d)} rows across all arms)")


if __name__ == "__main__":
    main()
