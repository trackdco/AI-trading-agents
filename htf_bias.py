"""NQ — New York Session Higher-Timeframe Bias (premarket 08:00 -> 10:15 ET), spec v2.

Implements the instruction set faithfully and DETERMINISTICALLY, including §6 intraday
re-evaluation. Prime directive #1 = NO LOOKAHEAD with a LIVE, PROVISIONAL `T`:

  * The first read is premarket at T = 08:00 ET, using ONLY candles fully closed <= T
    (day D's daily candle is still forming all day, so it is always excluded).
  * `T` then advances through the session. Re-reads recompute Steps 1-6 FROM SCRATCH at the
    new `T` (never anchored to the old bias) and may use only candles closed <= that new `T`.
    Any resampled bin still forming at `T` (e.g. the 08:00-12:00 4H bin at 09:45) is DROPPED.

§6 monitoring implemented mechanically (checked on each 15m close, 08:15 -> 10:15):
  * 09:30 ET — MANDATORY checkpoint, always re-read ("confirmed at open" if unchanged).
  * Invalidation hit — a 15m CLOSE through the invalidation level (close-through, not a
    wick touch: per §6 "a single wick ... is not a trigger", wick-only = the expected
    manipulation, close-through = structure change).
  * Primary draw reached — 15m candle touches the primary draw (edge spent -> fresh read).
  * CISD against the bias on 15m — close beyond the open of the last run (>=2) of
    consecutive opposite-close candles.
  * NEUTRAL days — a 15m close through either stated flip level triggers the re-read.
  Each trigger type fires at most once per governing read (no thrash); the 09:30 checkpoint
  resets the trigger budget. Every UPDATE emits a fresh full block stamped UPDATE @ time
  with a one-line CHANGE reason, and the new bias governs from that moment.

News gate (§5 factor 7 "untraded ... news"): only releases still UPCOMING at `T` block the
read; releases already printed before `T` are noted but do not force NEUTRAL — the 09:30
update on a CPI morning is precisely the post-news read the spec wants.

NQ-only, so SMT = n/a. Same data in -> same output out.

    python htf_bias.py 2026-06-17                 # one day: full blocks (INITIAL + all UPDATEs)
    python htf_bias.py 2026-06-01 2026-06-30      # range: per-day digest lines
    python htf_bias.py 2026-06-01 2026-06-30 --full   # range with full blocks
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
MIN_DRAW_DIST = 10.0  # a draw must be at least this far from price (else "already there")
WIN_END = dtime(10, 15)


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
    return (df.set_index("ts").resample(rule, closed="left", label="left")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
            .dropna(subset=["open"]).reset_index())


def frames_asof(bars: pd.DataFrame, T: pd.Timestamp, D: pd.Timestamp) -> dict:
    """Daily/4H/1H/15m using only candles FULLY CLOSED <= T. Trailing partial bins (bin end
    > T) are dropped — at an intraday T the current 4H/1H/15m candle is still forming."""
    intr = bars[bars["ts"] < T]
    daily = resample(bars, "1D")
    daily = daily[daily["ts"] < D]                    # day D's daily candle is still forming
    out = {"D": daily.reset_index(drop=True)}
    for name, rule in [("4H", "4h"), ("1H", "1h"), ("15m", "15min")]:
        f = resample(intr, rule)
        f = f[f["ts"] + pd.Timedelta(rule) <= T]      # closed bins only — no forming candle
        out[name] = f.reset_index(drop=True)
    return out


# ------------------------------------------------------------------ primitives

def swings(df: pd.DataFrame):
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
    """3-candle FVGs with status as of the last candle: unfilled/respected/disrespected/inverted."""
    h = df["high"].to_numpy(); l = df["low"].to_numpy(); c = df["close"].to_numpy()
    n = len(df); out = []
    for i in range(n - 2):
        if h[i] < l[i + 2]:
            lo, hi, kind = h[i], l[i + 2], "bull"
        elif l[i] > h[i + 2]:
            lo, hi, kind = h[i + 2], l[i], "bear"
        else:
            continue
        far = lo if kind == "bull" else hi
        status = "unfilled"; touched = False
        for j in range(i + 3, n):
            if l[j] <= hi and h[j] >= lo:
                touched = True
            body_through = (c[j] < far) if kind == "bull" else (c[j] > far)
            if body_through and touched:
                status = "disrespected"
                for k in range(j + 1, n):
                    held = (c[k] < lo) if kind == "bull" else (c[k] > hi)
                    if held:
                        status = "inverted"; break
                break
        else:
            status = "respected" if touched else "unfilled"
        out.append(dict(kind=kind, lo=lo, hi=hi, mid=(lo + hi) / 2, idx=i + 2, status=status))
    return out


def displacement_recent(df: pd.DataFrame, lookback=30) -> str:
    body = (df["close"] - df["open"]).abs()
    avg = body.rolling(10).mean()
    sub = df.tail(lookback)
    disp = sub[body.loc[sub.index] > DISP_ATR_MULT * avg.loc[sub.index].fillna(1e9)]
    if not len(disp):
        return ""
    last = disp.iloc[-1]
    return "up" if last["close"] > last["open"] else "down"


def cisd_last(df: pd.DataFrame, kind: str) -> bool:
    """Does the LAST closed candle of df print a CISD of `kind`? Bearish CISD = close below
    the open of the last run (>=2) of consecutive up-close candles; bullish mirrored."""
    o = df["open"].to_numpy(); c = df["close"].to_numpy(); n = len(df)
    if n < 3:
        return False
    i = n - 1; j = i - 1
    if kind == "bearish":
        while j >= 0 and c[j] > o[j]:
            j -= 1
        run = (i - 1) - j
        return run >= 2 and c[i] < o[j + 1]
    else:
        while j >= 0 and c[j] < o[j]:
            j -= 1
        run = (i - 1) - j
        return run >= 2 and c[i] > o[j + 1]


# ------------------------------------------------------------------ liquidity pools

def liquidity_pools(bars: pd.DataFrame, T: pd.Timestamp, D: pd.Timestamp) -> dict:
    p = {}
    day = bars["ts"].dt.normalize()
    k = 1
    prevday = bars[day == (D - pd.Timedelta(days=1))]
    while prevday.empty and k < 6:
        k += 1; prevday = bars[day == (D - pd.Timedelta(days=k))]
    if not prevday.empty:
        p["PDH"] = float(prevday["high"].max()); p["PDL"] = float(prevday["low"].min())
    iso = bars["ts"].dt.isocalendar()
    curwk = D.isocalendar()
    prevwk = (iso["year"] * 100 + iso["week"]).to_numpy() == (curwk.year * 100 + curwk.week - 1)
    pw = bars[prevwk & (bars["ts"] < T)]
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
    sh, sl = swings(df)
    pts = [v for _, v in (sh if side == "high" else sl)]
    eqs = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if abs(pts[i] - pts[j]) <= EQ_TOL:
                eqs.append(round((pts[i] + pts[j]) / 2, 2))
    return sorted(set(eqs))


def pd_location(daily: pd.DataFrame, price: float):
    sh, sl = swings(daily)
    if not sh or not sl:
        hi, lo = float(daily["high"].tail(20).max()), float(daily["low"].tail(20).min())
    else:
        hi, lo = sh[-1][1], sl[-1][1]
        if hi <= lo:
            hi, lo = float(daily["high"].tail(20).max()), float(daily["low"].tail(20).min())
    if hi <= lo:
        return "equilibrium", hi, lo, 0.5
    pct = (price - lo) / (hi - lo)
    loc = "premium" if pct > 0.55 else "discount" if pct < 0.45 else "equilibrium"
    return loc, hi, lo, pct


def origin(frames: dict, pools: dict):
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


def draws_for(direction: str, price: float, pools: dict, frames: dict):
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
    uniq = []
    for c in sorted(cands, key=lambda x: abs(x[0] - price)):
        if not any(abs(c[0] - u[0]) <= EQ_TOL for u in uniq):
            uniq.append(c)
    uniq.sort(key=lambda x: (not x[2], abs(x[0] - price)))
    return uniq[:3]


def news_split(news: pd.DataFrame, D: pd.Timestamp, T: pd.Timestamp):
    """(upcoming, printed) high-impact events for the window. Only UPCOMING (dt >= T) block —
    'untraded news' per the conviction spec; already-printed news is noted, not blocking."""
    if news.empty:
        return None, None
    lo = pd.Timestamp.combine(D.date(), dtime(7, 30)).tz_localize(NY)
    hi = pd.Timestamp.combine(D.date(), WIN_END).tz_localize(NY)
    w = news[(news["dt"] >= lo) & (news["dt"] <= hi) & (news["impact"].astype(str).str.lower() == "high")]
    if w.empty:
        return None, None
    up = w[w["dt"] >= T]; pr = w[w["dt"] < T]
    fmt = lambda x: list(zip(x["dt"].dt.strftime("%H:%M"), x["event"])) if len(x) else None
    return fmt(up), fmt(pr)


# ------------------------------------------------------------------ one read at time T

def read_at(bars: pd.DataFrame, news: pd.DataFrame, D: pd.Timestamp, T: pd.Timestamp,
            run_type: str, prev_bias: str | None = None, trigger: str | None = None):
    """Recompute Steps 1-6 from scratch at clock time T. Returns (block_text, state)."""
    frames = frames_asof(bars, T, D)
    if len(frames["D"]) < 5 or frames["1H"].empty:
        return f"=== NQ HTF BIAS — {D.date()} — insufficient data <= T ===", None
    price = float(bars[bars["ts"] < T]["close"].iloc[-1])
    pools = liquidity_pools(bars, T, D)

    # Step 1
    dt_, ht = trend(frames["D"]), trend(frames["4H"])
    loc, rhi, rlo, pct = pd_location(frames["D"], price)
    d_fvgs = [f for f in fvgs(frames["4H"].tail(60))
              if f["status"] in ("unfilled", "respected", "inverted") and abs(f["mid"] - price) <= 400]
    unfilled = [f for f in d_fvgs if f["status"] == "unfilled"]
    s1_lean = ("bearish" if dt_ == "downtrend" else "bullish" if dt_ == "uptrend" else "neutral")
    s1 = (f"Daily {dt_}, 4H {ht}. Price {price:.2f} sits in {loc} of the current daily range "
          f"[{rlo:.0f}-{rhi:.0f}] ({pct*100:.0f}%). {len(unfilled)} unfilled 4H FVG(s) in play. "
          f"Lean: {s1_lean} (trend + location).")

    # Step 2
    o_dir, o_txt, o_conf = origin(frames, pools)
    s2 = f"{o_txt}. Origin lean: {o_dir}{' (displacement-confirmed)' if o_conf else ' (UNCONFIRMED)'}. SMT: n/a (NQ-only)."

    direction = o_dir if o_dir != "neutral" else s1_lean
    hard_conflict = (o_dir != "neutral" and s1_lean != "neutral" and o_dir != s1_lean)

    # Step 3
    dws = draws_for(direction, price, pools, frames) if direction != "neutral" else []
    s3 = ("; ".join(f"{v:.0f} ({k}{'/unprotected' if unp else ''})" for v, k, unp in dws)
          if dws else "no clean unswept draw in the bias direction")

    # Step 4 — recent 15m order flow near price
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

    # Step 5
    nw_up, nw_printed = news_split(news, D, T)
    mo = pools.get("MidnightOpen")
    if direction == "bullish":
        po3 = f"Bullish PO3: expect manipulation LOWER (sweep session low / PDL{f' below the {mo:.0f} midnight open' if mo else ''}), then expand UP toward the draw; confirm on a 5m/15m bullish CISD after the sweep."
    elif direction == "bearish":
        po3 = f"Bearish PO3: expect manipulation HIGHER (sweep session high / PDH{f' above the {mo:.0f} midnight open' if mo else ''}), then expand DOWN toward the draw; confirm on a 5m/15m bearish CISD after the sweep."
    else:
        po3 = "No directional PO3 — wait for a clean sweep + CISD to define one."
    already = bool(dws) and abs(dws[0][0] - price) < MIN_DRAW_DIST
    s5 = po3
    s5 += f" UPCOMING high-impact news: {nw_up} — wait for post-news." if nw_up else " No upcoming high-impact news in-window (verify manually)."
    if nw_printed:
        s5 += f" (Already printed: {nw_printed}.)"
    if already:
        s5 += " Primary draw already ~reached — conviction reduced."

    factors = {
        "daily trend agrees": (dt_ == "uptrend" and direction == "bullish") or (dt_ == "downtrend" and direction == "bearish"),
        "4H trend agrees": (ht == "uptrend" and direction == "bullish") or (ht == "downtrend" and direction == "bearish"),
        "premium/discount supports": (loc == "discount" and direction == "bullish") or (loc == "premium" and direction == "bearish"),
        "origin agrees + confirmed": o_dir == direction and o_conf,
        "FVG order flow agrees": of_ok,
        "clean unprotected draw exists": any(unp for _, _, unp in dws),
        "timing clear": (nw_up is None) and not already,
    }
    score = sum(factors.values())
    if direction == "neutral" or hard_conflict or score <= 2 or (already and score < 4) or nw_up:
        tier, bias = "NEUTRAL", "NEUTRAL"
        if nw_up and direction != "neutral":
            reason = "untraded high-impact news dominates the window"
        elif hard_conflict:
            reason = "trend (Step 1) and origin (Step 2) conflict, unresolved"
        elif already:
            reason = "primary draw already reached"
        else:
            reason = f"only {score}/7 aligned"
    else:
        bias = "BULLISH" if direction == "bullish" else "BEARISH"
        tier = "HIGH" if score >= 6 and not inv_against else "MEDIUM" if score >= 4 else "LOW"
        reason = f"{score}/7 aligned"

    manip = ("sweep of session low / PDL below the open, then reject" if direction == "bullish"
             else "sweep of session high / PDH above the open, then reject" if direction == "bearish"
             else "await a sweep to define direction")
    conf_trig = ("5m/15m bullish CISD after the sweep; counter (bearish) FVG disrespected" if direction == "bullish"
                 else "5m/15m bearish CISD after the sweep; counter (bullish) FVG disrespected" if direction == "bearish"
                 else "a CISD in either direction after a sweep")
    # invalidation must sit on the FAR side of current price (a bearish invalidation is a
    # reclaim ABOVE, bullish a loss BELOW). When price trades outside the daily dealing range
    # the range edge can be on the wrong side — pick the nearest structural level beyond price.
    if direction == "bullish":
        below = [v for v in (pools.get("LondonL"), pools.get("AsiaL"), pools.get("PDL"), rlo)
                 if v is not None and v < price - 1.0]
        inval_px = max(below) if below else price - 100.0
        inval = f"15m close back below {inval_px:.0f} (nearest structural low / origin side)"
        flip = f"acceptance below {pools.get('PDL', rlo):.0f} (PDL) flips bearish toward {rlo:.0f}"
        primary = f"manipulation lower, then expansion up toward {dws[0][0]:.0f}" if dws else "expansion up once a low is swept"
    elif direction == "bearish":
        above = [v for v in (pools.get("LondonH"), pools.get("AsiaH"), pools.get("PDH"), rhi)
                 if v is not None and v > price + 1.0]
        inval_px = min(above) if above else price + 100.0
        inval = f"15m close back above {inval_px:.0f} (nearest structural high / origin side)"
        flip = f"acceptance above {pools.get('PDH', rhi):.0f} (PDH) flips bullish toward {rhi:.0f}"
        primary = f"manipulation higher, then expansion down toward {dws[0][0]:.0f}" if dws else "expansion down once a high is swept"
    else:
        inval_px = None
        inval = "n/a — no active bias"
        flip = f"break+accept above {pools.get('PDH', rhi):.0f} -> bullish; below {pools.get('PDL', rlo):.0f} -> bearish"
        primary = "no primary until a sweep + CISD prints"

    change_line = ""
    if run_type.startswith("UPDATE"):
        if prev_bias == bias:
            change_line = f"CHANGE: none — {bias} confirmed ({trigger})."
        else:
            change_line = f"CHANGE: {prev_bias} -> {bias} ({trigger})."

    s6 = (f"Primary: {primary}. Score {score}/7 -> {tier}."
          + (" Hard trend/origin conflict -> NEUTRAL." if hard_conflict else ""))

    drawstr = "; ".join(f"{v:.0f} ({k})" for v, k, _ in dws) if dws else \
        f"if {pools.get('PDH', rhi):.0f} breaks -> bullish; if {pools.get('PDL', rlo):.0f} breaks -> bearish"
    tstamp = "08:00 ET premarket" if run_type.startswith("INITIAL") else f"{T.strftime('%H:%M')} ET update"
    timing = []
    if nw_up:
        timing.append(f"UPCOMING NEWS {nw_up}")
    if nw_printed:
        timing.append(f"printed {nw_printed}")
    if not nw_up and not nw_printed:
        timing.append("no in-window high-impact news (verify manually)")
    if already:
        timing.append("draw already ~reached")

    block = f"""=== NQ HTF BIAS — {D.date()} — NY SESSION 08:00–10:15 ET ===
Analysis timestamp (T): {tstamp}  |  Data used: candles closed ≤ T only
Run type: {run_type}
{change_line + chr(10) if change_line else ''}
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
TIMING NOTES:              {'; '.join(timing)}
SMT:                       n/a (NQ-only)
"""
    state = dict(bias=bias, tier=tier, score=score, direction=direction,
                 inval_px=inval_px, draw_px=(dws[0][0] if dws else None),
                 draws=[(float(v), k) for v, k, _ in dws],   # all draws (≤3) for target selection
                 pdh=pools.get("PDH"), pdl=pools.get("PDL"))
    return block, state


# ------------------------------------------------------------------ §6 session monitor

def monitor_day(bars: pd.DataFrame, news: pd.DataFrame, D: pd.Timestamp):
    """INITIAL 08:00 read, then walk 15m closes to 10:15: mandatory 09:30 checkpoint +
    event-triggered UPDATEs (invalidation close-through, draw reached, CISD against,
    NEUTRAL flip-level break). Returns (blocks, digest_line)."""
    T0 = pd.Timestamp.combine(D.date(), dtime(8, 0)).tz_localize(NY)
    block, state = read_at(bars, news, D, T0, "INITIAL premarket")
    if state is None:
        return [block], f"{D.date()}  (insufficient data)"
    blocks = [block]
    digest = [f"08:00 {state['bias']}/{state['tier']}({state['score']}/7)"]
    fired: set = set()

    t = T0 + pd.Timedelta(minutes=15)
    end = pd.Timestamp.combine(D.date(), WIN_END).tz_localize(NY)
    while t <= end:
        candle = bars[(bars["ts"] >= t - pd.Timedelta(minutes=15)) & (bars["ts"] < t)]
        if t.time() == dtime(9, 30):
            blk, new_state = read_at(bars, news, D, t, "UPDATE @ 09:30 ET — mandatory open checkpoint",
                                     prev_bias=state["bias"], trigger="09:30 open checkpoint")
            blocks.append(blk)
            digest.append(f"09:30 {'confirmed ' if new_state['bias'] == state['bias'] else ''}"
                          f"{new_state['bias']}/{new_state['tier']}({new_state['score']}/7)")
            state = new_state; fired = set()
        elif len(candle):
            hi = float(candle["high"].max()); lo = float(candle["low"].min())
            cl = float(candle["close"].iloc[-1])
            reasons = []
            d = state["direction"]
            if d in ("bullish", "bearish"):
                ip = state["inval_px"]
                if ip is not None and "inval" not in fired and \
                        ((d == "bullish" and cl < ip) or (d == "bearish" and cl > ip)):
                    reasons.append(f"15m close through invalidation {ip:.0f}"); fired.add("inval")
                dp = state["draw_px"]
                if dp is not None and "draw" not in fired and \
                        ((d == "bullish" and hi >= dp) or (d == "bearish" and lo <= dp)):
                    reasons.append(f"primary draw {dp:.0f} reached — edge spent"); fired.add("draw")
                if "cisd" not in fired:
                    f15 = frames_asof(bars, t, D)["15m"]
                    against = "bearish" if d == "bullish" else "bullish"
                    if cisd_last(f15.tail(30), against):
                        reasons.append(f"15m {against} CISD against the bias — delivery flipped"); fired.add("cisd")
            else:
                if "flip" not in fired:
                    if state["pdh"] is not None and cl > state["pdh"]:
                        reasons.append(f"15m close above PDH {state['pdh']:.0f} — bullish break of the neutral box"); fired.add("flip")
                    elif state["pdl"] is not None and cl < state["pdl"]:
                        reasons.append(f"15m close below PDL {state['pdl']:.0f} — bearish break of the neutral box"); fired.add("flip")
            if reasons:
                trig = "; ".join(reasons)
                blk, new_state = read_at(bars, news, D, t, f"UPDATE @ {t.strftime('%H:%M')} ET — trigger: {trig}",
                                         prev_bias=state["bias"], trigger=trig)
                blocks.append(blk)
                digest.append(f"{t.strftime('%H:%M')} [{trig.split(' — ')[0]}] -> "
                              f"{new_state['bias']}/{new_state['tier']}({new_state['score']}/7)")
                state = new_state
        t += pd.Timedelta(minutes=15)
    return blocks, f"{D.date()}  " + "  ->  ".join(digest)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    full = "--full" in sys.argv
    if not args:
        print("usage: python htf_bias.py YYYY-MM-DD [YYYY-MM-DD] [--full]"); return
    bars = load_bars(); news = load_news()
    start = pd.Timestamp(args[0], tz=NY)
    end = pd.Timestamp(args[1], tz=NY) if len(args) > 1 else start
    single = start == end
    d = start
    while d <= end:
        if d.weekday() < 5:
            blocks, digest = monitor_day(bars, news, d)
            if single or full:
                for b in blocks:
                    print(b); print()
            else:
                print(digest)
        d += pd.Timedelta(days=1)


if __name__ == "__main__":
    main()
