"""NQ — New York Session Higher-Timeframe Bias (premarket 08:00 -> 10:15 ET).

Implements the instruction set faithfully and DETERMINISTICALLY. Prime directive #1 = NO
LOOKAHEAD: for a target day D we fix T = 08:00 ET and use ONLY candles fully closed <= T
(the day's own daily candle is still forming, so it is excluded; the last usable intraday
bars close at 08:00). Same data in -> same bias out. NQ-only, so SMT = n/a.

Timeframes: Daily + 4H (context/draws), 1H + 15m (order-flow confirmation). 5m/1m are only
referenced to describe expected session mechanics, never to form the premarket bias.

    python htf_bias.py 2026-07-15            # one day
    python htf_bias.py 2026-07-10 2026-07-15 # inclusive range (replay)

Deterministic proxies (documented, faithful to the definitions): swings are 3-candle;
trend = last two swing highs AND lows both rising (up) / falling (down) else range;
FVG = 3-candle gap, disrespected when a later body closes through the far side, inversion
when it then holds from the other side; origin = most recent swept-then-displaced pool;
draws = nearest unswept pools in the bias direction, unprotected preferred; premium/discount
= fib of the current daily dealing range. Session anchors are computed from data <= T.
"""
from __future__ import annotations

import io
import sys
from datetime import time as dtime

import numpy as np
import pandas as pd

NY = "America/New_York"
DATA = "/home/user/gs/data/reference/nq_1m_master.parquet"
NEWS = ["/home/user/gs/config/news_calendar.csv", "/home/user/gs/config/news_calendar_hist.csv"]
EQ_TOL = 5.0          # points: "relatively equal" highs/lows cluster within this
DISP_ATR_MULT = 1.5   # a displacement candle body exceeds this * recent avg body


# ------------------------------------------------------------------ data

def load_bars() -> pd.DataFrame:
    b = pd.read_parquet(DATA)
    b["ts"] = pd.to_datetime(b["ts_event"], utc=True).dt.tz_convert(NY)
    return b[["ts", "open", "high", "low", "close", "volume"]].sort_values("ts").reset_index(drop=True)


def load_news() -> pd.DataFrame:
    frames = []
    for f in NEWS:
        try:
            rows = [l for l in open(f) if not l.startswith("#")]
            frames.append(pd.read_csv(io.StringIO("".join(rows))))
        except Exception:
            pass
    if not frames:
        return pd.DataFrame(columns=["dt", "event", "impact"])
    n = pd.concat(frames, ignore_index=True).drop_duplicates(["datetime_ET", "event"])
    n = n[n["datetime_ET"] != "impact"]
    n["dt"] = pd.to_datetime(n["datetime_ET"]).dt.tz_localize(NY)
    return n[["dt", "event", "impact"]]


def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    o = (df.set_index("ts").resample(rule, closed="left", label="left")
         .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
         .dropna(subset=["open"]).reset_index())
    return o


def frames_asof(bars: pd.DataFrame, T: pd.Timestamp, D: pd.Timestamp) -> dict:
    """Build Daily/4H/1H/15m using only candles fully closed <= T (no lookahead)."""
    intr = bars[bars["ts"] < T]                       # up to 07:59 on D -> intraday bins close <= 08:00
    daily = resample(bars, "1D")
    daily = daily[daily["ts"] < D]                    # exclude the still-forming day-D daily candle
    return {"D": daily.reset_index(drop=True),
            "4H": resample(intr, "4h"), "1H": resample(intr, "1h"), "15m": resample(intr, "15min")}


# ------------------------------------------------------------------ primitives

def swings(df: pd.DataFrame):
    """3-candle swing highs/lows on closed candles. Returns (highs, lows) as lists of (idx, price)."""
    h = df["high"].to_numpy(); l = df["low"].to_numpy(); n = len(df)
    sh = [(i, h[i]) for i in range(1, n - 1) if h[i] > h[i - 1] and h[i] > h[i + 1]]
    sl = [(i, l[i]) for i in range(1, n - 1) if l[i] < l[i - 1] and l[i] < l[i + 1]]
    return sh, sl


def trend(df: pd.DataFrame) -> str:
    sh, sl = swings(df)
    if len(sh) < 2 or len(sl) < 2:
        return "range"
    hh = sh[-1][1] > sh[-2][1]; hl = sl[-1][1] > sl[-2][1]
    lh = sh[-1][1] < sh[-2][1]; ll = sl[-1][1] < sl[-2][1]
    if hh and hl:
        return "uptrend"
    if lh and ll:
        return "downtrend"
    return "range"


def fvgs(df: pd.DataFrame):
    """3-candle FVGs with status as of the last candle: unfilled / respected / disrespected / inverted."""
    o = df["open"].to_numpy(); h = df["high"].to_numpy(); l = df["low"].to_numpy(); c = df["close"].to_numpy()
    n = len(df); out = []
    for i in range(n - 2):
        if h[i] < l[i + 2]:      # bullish FVG (gap below): [c1.high, c3.low]
            lo, hi, kind = h[i], l[i + 2], "bull"
        elif l[i] > h[i + 2]:    # bearish FVG (gap above): [c3.high, c1.low]
            lo, hi, kind = h[i + 2], l[i], "bear"
        else:
            continue
        far = lo if kind == "bull" else hi    # far boundary a body must close through to disrespect
        status = "unfilled"; touched = False
        for j in range(i + 3, n):
            if l[j] <= hi and h[j] >= lo:
                touched = True
            body_through = (c[j] < far) if kind == "bull" else (c[j] > far)
            if body_through and touched:
                status = "disrespected"
                # inversion: after disrespect, does it hold from the opposite side?
                for k in range(j + 1, n):
                    held = (c[k] < lo) if kind == "bull" else (c[k] > hi)
                    react = (c[k] > c[k - 1]) if kind == "bull" else (c[k] < c[k - 1])
                    if held:
                        status = "inverted"; break
                break
        else:
            status = "respected" if touched else "unfilled"
        out.append(dict(kind=kind, lo=lo, hi=hi, mid=(lo + hi) / 2, idx=i + 2, status=status))
    return out


def displacement_recent(df: pd.DataFrame, lookback=30) -> str:
    """Direction of the most recent displacement candle (large body vs recent average). '' if none."""
    body = (df["close"] - df["open"]).abs()
    avg = body.rolling(10).mean()
    sub = df.tail(lookback)
    disp = sub[body.loc[sub.index] > DISP_ATR_MULT * avg.loc[sub.index].fillna(1e9)]
    if not len(disp):
        return ""
    last = disp.iloc[-1]
    return "up" if last["close"] > last["open"] else "down"


# ------------------------------------------------------------------ liquidity pools

def liquidity_pools(bars: pd.DataFrame, T: pd.Timestamp, D: pd.Timestamp) -> dict:
    """PDH/PDL, PWH/PWL, Asia/London H/L, midnight open, recent swing pools, equal H/L — all <= T."""
    p = {}
    day = bars["ts"].dt.normalize()
    prevday = bars[day == (D - pd.Timedelta(days=1))]
    # walk back to the most recent prior day that actually has bars (skip weekends/holidays)
    k = 1
    while prevday.empty and k < 6:
        k += 1; prevday = bars[day == (D - pd.Timedelta(days=k))]
    if not prevday.empty:
        p["PDH"] = float(prevday["high"].max()); p["PDL"] = float(prevday["low"].min())
    iso = bars["ts"].dt.isocalendar()
    curwk = D.isocalendar()
    prevwk_mask = (iso["year"] * 100 + iso["week"]).to_numpy() == (curwk.year * 100 + curwk.week - 1)
    pw = bars[prevwk_mask & (bars["ts"] < T)]
    if not pw.empty:
        p["PWH"] = float(pw["high"].max()); p["PWL"] = float(pw["low"].min())

    def sess(a_h, a_m, b_h, b_m, base):
        s = pd.Timestamp.combine(base.date(), dtime(a_h, a_m)).tz_localize(NY)
        e = pd.Timestamp.combine(base.date(), dtime(b_h, b_m)).tz_localize(NY)
        w = bars[(bars["ts"] >= s) & (bars["ts"] < e) & (bars["ts"] < T)]
        return (float(w["high"].max()), float(w["low"].min())) if not w.empty else (None, None)

    ah, al = sess(20, 0, 23, 59, D - pd.Timedelta(days=1))   # Asia 20:00-24:00 ET (prev)
    lh, ll = sess(2, 0, 8, 0, D)                              # London 02:00-08:00 ET
    if ah is not None:
        p["AsiaH"], p["AsiaL"] = ah, al
    if lh is not None:
        p["LondonH"], p["LondonL"] = lh, ll
    mo = bars[(bars["ts"] >= pd.Timestamp.combine(D.date(), dtime(0, 0)).tz_localize(NY))
              & (bars["ts"] < T)]
    if not mo.empty:
        p["MidnightOpen"] = float(mo["open"].iloc[0])
    return p


def equal_levels(df: pd.DataFrame, side: str):
    """Relatively-equal highs/lows (clustered within EQ_TOL) — unprotected liquidity."""
    sh, sl = swings(df)
    pts = [v for _, v in (sh if side == "high" else sl)]
    eqs = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if abs(pts[i] - pts[j]) <= EQ_TOL:
                eqs.append(round((pts[i] + pts[j]) / 2, 2))
    return sorted(set(eqs))


# ------------------------------------------------------------------ premium / discount

def pd_location(daily: pd.DataFrame, price: float):
    """Fib of the current daily dealing range (most recent daily swing high & low)."""
    sh, sl = swings(daily)
    if not sh or not sl:
        hi, lo = float(daily["high"].tail(20).max()), float(daily["low"].tail(20).min())
    else:
        hi, lo = sh[-1][1], sl[-1][1]
        if hi <= lo:      # ensure a valid range using recent extremes
            hi, lo = float(daily["high"].tail(20).max()), float(daily["low"].tail(20).min())
    if hi <= lo:
        return "equilibrium", hi, lo, 0.5
    pct = (price - lo) / (hi - lo)
    loc = "premium" if pct > 0.55 else "discount" if pct < 0.45 else "equilibrium"
    return loc, hi, lo, pct


# ------------------------------------------------------------------ origin (delivering FROM)

def origin(frames: dict, pools: dict):
    """Most recent swept-then-displaced pool -> bullish (from sellside) / bearish (from buyside)."""
    df = frames["1H"]
    if len(df) < 6:
        df = frames["15m"]
    disp = displacement_recent(df)
    lows = [v for k, v in pools.items() if k in ("PDL", "PWL", "AsiaL", "LondonL")]
    highs = [v for k, v in pools.items() if k in ("PDH", "PWH", "AsiaH", "LondonH")]
    recent = df.tail(20)
    swept_low = any(recent["low"].min() < lo for lo in lows) if lows else False
    swept_high = any(recent["high"].max() > hi for hi in highs) if highs else False
    if disp == "up" and swept_low:
        return "bullish", "swept sellside (a prior low) then displaced up — delivering from sellside", True
    if disp == "down" and swept_high:
        return "bearish", "swept buyside (a prior high) then displaced down — delivering from buyside", True
    if swept_low and not swept_high:
        return "bullish", "sellside taken but displacement not yet clean", False
    if swept_high and not swept_low:
        return "bearish", "buyside taken but displacement not yet clean", False
    return "neutral", "no clean swept-then-displaced origin visible", False


# ------------------------------------------------------------------ draws (targets)

MIN_DRAW_DIST = 10.0   # a draw must be at least this far from price (else it's "already there")


def draws_for(direction: str, price: float, pools: dict, frames: dict):
    """1-3 unswept liquidity draws in the bias direction. Named HTF pools (PDH/PDL/PWH/PWL/
    session H/L) are the backbone; recent relatively-equal highs/lows mark UNPROTECTED draws
    (preferred). A draw must sit >= MIN_DRAW_DIST from price (a level at price isn't a draw)."""
    named = {"PDH", "PDL", "PWH", "PWL", "AsiaH", "AsiaL", "LondonH", "LondonL"}
    eq_hi = equal_levels(frames["1H"].tail(80), "high")
    eq_lo = equal_levels(frames["1H"].tail(80), "low")
    unp_set = set(eq_hi) | set(eq_lo)

    def unprotected(v):
        return any(abs(v - e) <= EQ_TOL for e in unp_set)

    cands = []
    for k, v in pools.items():
        if v is None or k not in named:
            continue
        if direction == "bullish" and v >= price + MIN_DRAW_DIST:
            cands.append((round(v, 2), k, unprotected(v)))
        if direction == "bearish" and v <= price - MIN_DRAW_DIST:
            cands.append((round(v, 2), k, unprotected(v)))
    for e in (eq_hi if direction == "bullish" else eq_lo):
        if direction == "bullish" and e >= price + MIN_DRAW_DIST:
            cands.append((round(e, 2), "equal-highs", True))
        if direction == "bearish" and e <= price - MIN_DRAW_DIST:
            cands.append((round(e, 2), "equal-lows", True))
    # dedupe near-identical levels, then unprotected-first, nearest-first, cap 3
    uniq = []
    for c in sorted(cands, key=lambda x: abs(x[0] - price)):
        if not any(abs(c[0] - u[0]) <= EQ_TOL for u in uniq):
            uniq.append(c)
    uniq.sort(key=lambda x: (not x[2], abs(x[0] - price)))
    return uniq[:3]


# ------------------------------------------------------------------ news timing

def news_in_window(news: pd.DataFrame, D: pd.Timestamp):
    if news.empty:
        return None
    lo = pd.Timestamp.combine(D.date(), dtime(7, 30)).tz_localize(NY)
    hi = pd.Timestamp.combine(D.date(), dtime(10, 15)).tz_localize(NY)
    w = news[(news["dt"] >= lo) & (news["dt"] <= hi) & (news["impact"].astype(str).str.lower() == "high")]
    return None if w.empty else list(zip(w["dt"].dt.strftime("%H:%M"), w["event"]))


# ------------------------------------------------------------------ orchestrate one day

def run_day(bars: pd.DataFrame, news: pd.DataFrame, D: pd.Timestamp) -> str:
    T = pd.Timestamp.combine(D.date(), dtime(8, 0)).tz_localize(NY)
    frames = frames_asof(bars, T, D)
    if len(frames["D"]) < 5 or frames["1H"].empty:
        return f"=== NQ HTF BIAS — {D.date()} — insufficient data <= T ==="
    price = float(bars[bars["ts"] < T]["close"].iloc[-1])
    pools = liquidity_pools(bars, T, D)

    # Step 1
    dt, ht = trend(frames["D"]), trend(frames["4H"])
    loc, rhi, rlo, pct = pd_location(frames["D"], price)
    # only RECENT FVGs matter (last ~10 days of 4H), and only those still near price ("in play")
    d_fvgs = [f for f in fvgs(frames["4H"].tail(60))
              if f["status"] in ("unfilled", "respected", "inverted") and abs(f["mid"] - price) <= 400]
    unfilled = [f for f in d_fvgs if f["status"] == "unfilled"]
    s1_lean = ("bearish" if dt == "downtrend" else "bullish" if dt == "uptrend" else "neutral")
    s1 = (f"Daily {dt}, 4H {ht}. Price {price:.2f} sits in {loc} of the current daily range "
          f"[{rlo:.0f}-{rhi:.0f}] ({pct*100:.0f}%). {len(unfilled)} unfilled 4H FVG(s) in play. "
          f"Lean: {s1_lean} (trend + location).")

    # Step 2
    o_dir, o_txt, o_conf = origin(frames, pools)
    s2 = f"{o_txt}. Origin lean: {o_dir}{' (displacement-confirmed)' if o_conf else ' (UNCONFIRMED)'}. SMT: n/a (NQ-only)."

    # resolve direction: origin leads (it is 'where price is delivering from'); trend must not hard-contradict
    direction = o_dir if o_dir != "neutral" else s1_lean
    hard_conflict = (o_dir != "neutral" and s1_lean != "neutral" and o_dir != s1_lean)

    # Step 3
    dws = draws_for(direction, price, pools, frames) if direction != "neutral" else []
    s3 = ("; ".join(f"{v:.0f} ({k}{'/unprotected' if unp else ''})" for v, k, unp in dws)
          if dws else "no clean unswept draw in the bias direction")

    # Step 4 — recent 15m order flow only (last ~1.5 days), near price
    of = [f for f in fvgs(frames["15m"].tail(60)) if abs(f["mid"] - price) <= 300]
    with_resp = sum(1 for f in of if f["status"] == "respected" and
                    ((direction == "bullish" and f["kind"] == "bull") or (direction == "bearish" and f["kind"] == "bear")))
    counter_disp = sum(1 for f in of if f["status"] in ("disrespected", "inverted") and
                       ((direction == "bullish" and f["kind"] == "bear") or (direction == "bearish" and f["kind"] == "bull")))
    inv_against = any(f["status"] == "inverted" and
                      ((direction == "bullish" and f["kind"] == "bull") or (direction == "bearish" and f["kind"] == "bear"))
                      for f in of)
    of_ok = (with_resp >= 1 and counter_disp >= 1) or (with_resp >= 1 and not inv_against)
    s4 = (f"15m: {with_resp} with-trend FVG(s) respected, {counter_disp} counter FVG(s) disrespected"
          f"{'; WARNING: fresh inversion against the lean' if inv_against else ''}. "
          f"Order flow {'confirms' if of_ok else 'does not confirm'} {direction}.")

    # Step 5 (PO3 + timing)
    nw = news_in_window(news, D)
    mo = pools.get("MidnightOpen")
    if direction == "bullish":
        po3 = f"Bullish PO3: expect manipulation LOWER (sweep session low / PDL{f' below the {mo:.0f} midnight open' if mo else ''}), then expand UP toward the draw; confirm on a 5m/15m bullish CISD after the sweep."
    elif direction == "bearish":
        po3 = f"Bearish PO3: expect manipulation HIGHER (sweep session high / PDH{f' above the {mo:.0f} midnight open' if mo else ''}), then expand DOWN toward the draw; confirm on a 5m/15m bearish CISD after the sweep."
    else:
        po3 = "No directional PO3 — wait for a clean sweep + CISD to define one."
    already = bool(dws) and abs(dws[0][0] - price) < 10
    s5 = po3 + (f" NEWS in window: {nw} — wait for post-news." if nw else " No high-impact news in-window (verify manually).") \
        + (" Primary draw already ~reached before 08:00 — conviction reduced." if already else "")

    # Step 6 + conviction
    factors = {
        "daily trend agrees": (dt == "uptrend" and direction == "bullish") or (dt == "downtrend" and direction == "bearish"),
        "4H trend agrees": (ht == "uptrend" and direction == "bullish") or (ht == "downtrend" and direction == "bearish"),
        "premium/discount supports": (loc == "discount" and direction == "bullish") or (loc == "premium" and direction == "bearish"),
        "origin agrees + confirmed": o_dir == direction and o_conf,
        "FVG order flow agrees": of_ok,
        "clean unprotected draw exists": any(unp for _, _, unp in dws),
        "timing clear": (nw is None) and not already,
    }
    score = sum(factors.values())
    if direction == "neutral" or hard_conflict or score <= 2 or (already and score < 4) or nw:
        tier, bias = "NEUTRAL", "NEUTRAL"
        if nw and direction != "neutral":
            reason = "high-impact news dominates the window"
        elif hard_conflict:
            reason = "trend (Step 1) and origin (Step 2) conflict, unresolved"
        elif already:
            reason = "primary draw already reached before 08:00"
        else:
            reason = f"only {score}/7 aligned"
    else:
        bias = "BULLISH" if direction == "bullish" else "BEARISH"
        tier = "HIGH" if score >= 6 and not inv_against else "MEDIUM" if score >= 4 else "LOW"
        reason = f"{score}/7 aligned"

    manip = ("sweep of session low / PDL below the open, then reject" if direction == "bullish"
             else "sweep of session high / PDH above the open, then reject" if direction == "bearish"
             else "await a sweep to define direction")
    conf_trig = (f"5m/15m bullish CISD after the sweep; counter (bearish) FVG disrespected" if direction == "bullish"
                 else "5m/15m bearish CISD after the sweep; counter (bullish) FVG disrespected" if direction == "bearish"
                 else "a CISD in either direction after a sweep")
    if direction == "bullish":
        inval = f"1H close back below {rlo:.0f} (range low) or below the origin low"
        flip = f"acceptance below {pools.get('PDL', rlo):.0f} (PDL) flips bearish toward {rlo:.0f}"
        primary = f"manipulation lower, then expansion up toward {dws[0][0]:.0f}" if dws else "expansion up once a low is swept"
    elif direction == "bearish":
        inval = f"1H close back above {rhi:.0f} (range high) or above the origin high"
        flip = f"acceptance above {pools.get('PDH', rhi):.0f} (PDH) flips bullish toward {rhi:.0f}"
        primary = f"manipulation higher, then expansion down toward {dws[0][0]:.0f}" if dws else "expansion down once a high is swept"
    else:
        inval = "n/a — no active bias"
        flip = f"break+accept above {pools.get('PDH', rhi):.0f} -> bullish; below {pools.get('PDL', rlo):.0f} -> bearish"
        primary = "no primary until a sweep + CISD prints"

    s6 = (f"Primary: {primary}. Score {score}/7 -> {tier}."
          + (" Hard trend/origin conflict -> NEUTRAL." if hard_conflict else ""))

    drawstr = "; ".join(f"{v:.0f} ({k})" for v, k, _ in dws) if dws else \
        f"if {pools.get('PDH', rhi):.0f} breaks -> bullish; if {pools.get('PDL', rlo):.0f} breaks -> bearish"
    return f"""=== NQ HTF BIAS — {D.date()} — NY SESSION 08:00–10:15 ET ===
Analysis timestamp (T): 08:00 ET  |  Data used: candles closed ≤ T only

NARRATIVE
  Step 1 — HTF trend & location: {s1}
  Step 2 — Delivering from (origin): {s2}
  Step 3 — Draw(s) on liquidity: {s3}
  Step 4 — Order-flow (FVG respect/disrespect): {s4}
  Step 5 — PO3 + timing: {s5}
  Step 6 — Synthesis: {s6}

--- SUMMARY ---
BIAS:            {bias}
CONVICTION:      {tier}  ({score}/7 — {reason})
DRAW(S) (≤3):    {drawstr}
MANIPULATION TO WAIT FOR:  {manip}
CONFIRMATION TRIGGER:      {conf_trig}
PRIMARY SCENARIO:          {primary}
ALTERNATE / FLIP:          {flip}
INVALIDATION LEVEL:        {inval}
TIMING NOTES:              {('NEWS ' + str(nw)) if nw else 'no in-window high-impact news (verify manually)'}{'; draw already ~reached' if already else ''}
SMT:                       n/a (NQ-only)
"""


def main():
    args = sys.argv[1:]
    if not args:
        print("usage: python htf_bias.py YYYY-MM-DD [YYYY-MM-DD]"); return
    bars = load_bars(); news = load_news()
    start = pd.Timestamp(args[0], tz=NY)
    end = pd.Timestamp(args[1], tz=NY) if len(args) > 1 else start
    d = start
    while d <= end:
        if d.weekday() < 5:
            print(run_day(bars, news, d)); print()
        d += pd.Timedelta(days=1)


if __name__ == "__main__":
    main()
