#!/usr/bin/env python3
"""SYNTHESIS SWEEP — shared harness. 08:00-10:30 ET entries only.

Every candidate in the sweep plugs into THIS file, so no convention can drift between them.
The pre-registration that governs it is research/_shared/trials-ledger.md, committed BEFORE any
candidate was tested.

A candidate is a function  detect(ctx) -> list[Event]  where Event carries the entry bar index,
the direction, the entry price and the stop price. The harness owns everything else: the locked
exit, the features, the split, the clustering and the noise floor. A candidate CANNOT
accidentally use a different exit or a different cost basis.

=============================== WHAT IS FIXED HERE, AND WHY ================================
W1  ENTRY WINDOW [U]      08:00:00-10:30:00 ET. Entries outside it DO NOT EXIST.
                          Exits run on past 10:30 to the 16:00 cap. Brake's instruction.
W2  SPAN                  2025-06-01 -> 2026-07-15, the flow-covered window.
W3  SPLIT [PREREG]        DISCOVERY <= 2026-02-27 | HOLDOUT >= 2026-03-02. Boundary 2026-03-01.
                          Declared in the ledger before any test. NEVER MOVES.
W4  EXIT [LOCK]           2R target, BE at 1R, no trailing, STOP-FIRST on a same-bar conflict,
                          16:00 ET cap, R signed by direction.
W5  COSTS                 $25/round-turn at $20/pt, per trade, reported SEPARATELY.
W6  CLUSTERING            session date is the independent unit. Raw n and effective n both.
W7  NEWS                  the canonical 17-event whitelist (ledger 0.5) — the INTERSECTION of the
                          two calendars' vocabularies, so the definition cannot change at the
                          split boundary. Naive concatenation makes the news rate jump 29% -> 74%
                          across the boundary, which is the source changing, not the market.

------------------------------- FLOW FEATURES: THE HARD RULE -------------------------------
Every flow feature here ends STRICTLY BEFORE THE ENTRY MINUTE — the last minute read is te-1.

This is not caution, it is the lesson of 2026-08-07: `retrace_ratio` ended its window AT the
entry minute, and because footprint data is minute-aggregated while entries fill intrabar, it
contained up to 59 seconds of POST-FILL tape. On 73% of zxck-10am-keyopen trades the retracement
was a single minute, so 100% of the feature's numerator was the entry minute. That halted the
pooled F2/H1 test at Step 0. See research/_shared/f2-h1-oos-test.md.

Ending at te-1 is provably computable at the entry instant: the te-1 bar has closed.

BANNED, and not implemented anywhere in this file: same-instrument delta SIGN confirmation of a
structurally-defined move. It is circular — it removed 0 of 29 on ash-unicorn-sb.
============================================================================================
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.f2_oos_test import flow_frame  # noqa: E402
from scripts.nya_sb01_feasibility import load_bars  # noqa: E402

WIN_LO, WIN_HI = 8 * 60, 10 * 60 + 30        # W1  08:00 -> 10:30
RTH_END = 16 * 60                            # W4
SPAN_LO, SPAN_HI = "2025-06-01", "2026-07-15"
SPLIT = "2026-03-01"                         # W3  PREREG — never moves
TARGET_R = 2.0
COST_USD, PT = 25.0, 20.0
RTH_OPEN = 9 * 60 + 30

# W7 — the canonical whitelist. Intersection of both calendars' vocabularies.
CANON_EVENTS = (
    "Advance GDP q/q", "Average Hourly Earnings m/m", "CPI m/m", "CPI y/y", "Core CPI m/m",
    "Core PCE Price Index m/m", "Core Retail Sales m/m", "FOMC Economic Projections",
    "FOMC Meeting Minutes", "FOMC Press Conference", "FOMC Statement", "Federal Funds Rate",
    "ISM Manufacturing PMI", "ISM Services PMI", "Non-Farm Employment Change",
    "Retail Sales m/m", "Unemployment Rate",
)


@dataclass
class Event:
    """One candidate setup. The harness supplies everything downstream of the stop."""
    t: int              # entry bar index INTO the window frame `w`
    side: int           # +1 long, -1 short
    entry: float
    stop: float
    intrabar: bool = True   # True if the fill is a limit touch (its own bar can still stop it);
    #                         False if the entry is AT a bar's close, whose range is already spent
    tag: str = ""
    ambiguous: bool = False  # set when intrabar ordering was undecidable and had to be bounded


@dataclass
class Ctx:
    """Everything a candidate may read. Nothing here extends past the window."""
    day: str
    g: pd.DataFrame          # the whole session, 1-min
    w: pd.DataFrame          # 08:00-10:30 only, reset index
    pre: pd.DataFrame        # everything strictly BEFORE 08:00 today
    prev: pd.DataFrame       # the previous calendar session
    prev_rth: pd.DataFrame   # the most recent PRIOR day that actually has an RTH block
    news_mins: tuple         # minutes-of-day of today's canonical releases inside the window
    is_news: bool
    atr_pct: float


# ------------------------------------------------------------------ data
def canonical_calendar() -> pd.DataFrame:
    c = pd.concat([pd.read_csv(ROOT / f, comment="#")
                   for f in ("config/news_calendar_hist.csv", "config/news_calendar.csv")],
                  ignore_index=True)
    c["dt"] = pd.to_datetime(c.datetime_ET, errors="coerce")
    c = c.dropna(subset=["dt"]).reset_index(drop=True)
    c["ev"] = c.event.str.strip()
    c = c[c.ev.isin(CANON_EVENTS)].copy()
    c["mins"] = c.dt.dt.hour * 60 + c.dt.dt.minute
    c["day"] = c.dt.dt.strftime("%Y-%m-%d")
    return c


def build_contexts() -> list[Ctx]:
    """One Ctx per qualifying session. Sessions without a complete window are dropped, counted."""
    bars = load_bars()
    bars = bars[(bars.day >= SPAN_LO) & (bars.day <= SPAN_HI)]
    cal = canonical_calendar()
    news_by_day = (cal[(cal.mins >= WIN_LO) & (cal.mins <= WIN_HI)]
                   .groupby("day").mins.apply(tuple).to_dict())
    dly = bars.groupby("day").agg(high=("high", "max"), low=("low", "min"))
    atr = (dly.high - dly.low).rolling(14).mean().shift(1).rank(pct=True)

    by_day = {d: x.reset_index(drop=True) for d, x in bars.groupby("day", sort=False)}
    days = sorted(by_day)
    out, last_rth = [], None
    for k, day in enumerate(days):
        g = by_day[day]
        w = g[(g.mins >= WIN_LO) & (g.mins <= WIN_HI)].reset_index(drop=True)
        rth = g[(g.mins >= RTH_OPEN) & (g.mins <= RTH_END)]
        if len(w) == (WIN_HI - WIN_LO + 1) and k:
            out.append(Ctx(day=day, g=g, w=w,
                           pre=g[g.mins < WIN_LO], prev=by_day[days[k - 1]],
                           prev_rth=last_rth,
                           news_mins=news_by_day.get(day, ()),
                           is_news=day in news_by_day,
                           atr_pct=float(atr.get(day, np.nan))))
        if len(rth):
            last_rth = g
    return out


def flow_by_day(ctxs: list[Ctx]) -> dict:
    fp = flow_frame()
    keep = {c.day for c in ctxs}
    d = {k: v for k, v in fp.groupby(fp.index.strftime("%Y-%m-%d")) if k in keep}
    return d


# ------------------------------------------------------------------ the locked exit (W4)
def walk_exit(g: pd.DataFrame, w: pd.DataFrame, ev: Event):
    """LOCKED. Returns (R, exit_px, be_moved, exit_ts).

    The tail is w[t+1:] followed by the rest of the session to 16:00, so nothing is skipped and
    nothing is double-counted. On an intrabar fill the ENTRY BAR ITSELF is checked against the
    stop first — the same-bar fill-and-stop defect that was live in four sibling scripts before
    2026-08-07 and mis-scored a +2R win as a -1R loss on zxck-10am-keyopen.
    """
    side, entry, stop = ev.side, ev.entry, ev.stop
    risk = (entry - stop) * side
    target, half = entry + side * TARGET_R * risk, entry + side * risk
    if ev.intrabar:
        fb = w.iloc[ev.t]
        if (fb.low <= stop) if side > 0 else (fb.high >= stop):
            return -1.0, stop, False, fb.ts
    tail = pd.concat([w.iloc[ev.t + 1:], g[(g.mins > WIN_HI) & (g.mins <= RTH_END)]])
    cur, be = stop, False
    for b in tail.itertuples():
        if side > 0:
            if b.low <= cur:
                return (0.0 if be else -1.0), cur, be, b.ts
            if b.high >= target:
                return TARGET_R, target, be, b.ts
            if not be and b.high >= half:
                cur, be = entry, True
        else:
            if b.high >= cur:
                return (0.0 if be else -1.0), cur, be, b.ts
            if b.low <= target:
                return TARGET_R, target, be, b.ts
            if not be and b.low <= half:
                cur, be = entry, True
    if not len(tail):
        return 0.0, entry, be, w.ts.iloc[ev.t]
    last = float(tail.close.iloc[-1])
    return float(side * (last - entry) / risk), last, be, tail.ts.iloc[-1]


# ------------------------------------------------------------------ features
def features(ctx: Ctx, ev: Event, fpd: pd.DataFrame, risk: float) -> dict:
    """Context + flow. EVERY FLOW FEATURE ENDS AT te-1 — strictly before the entry minute.

    Asserted at runtime. See the module docstring for why this rule exists.
    """
    w = ctx.w
    te = w.ts.iloc[ev.t]
    cut = te - pd.Timedelta(minutes=1)          # last minute readable at the entry instant
    sess = fpd[(fpd.index >= w.ts.iloc[0]) & (fpd.index <= cut)]
    assert not len(sess) or sess.index.max() < te, "flow window must end strictly before entry"
    med = float(sess.vol.median()) if len(sess) else np.nan
    last5 = fpd[(fpd.index > cut - pd.Timedelta(minutes=5)) & (fpd.index <= cut)]
    last15 = fpd[(fpd.index > cut - pd.Timedelta(minutes=15)) & (fpd.index <= cut)]

    def norm(x):
        return float(x) / med if med and med == med else np.nan

    prehi = float(ctx.pre.high.max()) if len(ctx.pre) else np.nan
    prelo = float(ctx.pre.low.min()) if len(ctx.pre) else np.nan
    h1 = (float(ctx.pre.close.iloc[-1] - ctx.pre.close.iloc[-120])
          if len(ctx.pre) > 120 else np.nan)
    return {
        "dow": pd.Timestamp(ctx.day).day_name()[:3],
        "entry_min": int(w.mins.iloc[ev.t]),
        "entry_min_into_window": int(w.mins.iloc[ev.t] - WIN_LO),
        "after_rth_open": int(w.mins.iloc[ev.t] >= RTH_OPEN),
        "atr_pct": ctx.atr_pct,
        "htf_aligned": int((h1 > 0) == (ev.side > 0)) if h1 == h1 else np.nan,
        "dist_to_level_R": (round(min(abs(ev.entry - prehi), abs(ev.entry - prelo)) / risk, 3)
                            if prehi == prehi and risk else np.nan),
        "news_day": int(ctx.is_news),
        "mins_since_release": (int(min([w.mins.iloc[ev.t] - m for m in ctx.news_mins
                                        if m <= w.mins.iloc[ev.t]], default=-1))
                               if ctx.news_mins else -1),
        # ---- FLOW, all ending at te-1 ----
        "f_sess_minutes": int(len(sess)),
        "f_cvd_pre": norm(sess.delta.sum()) if len(sess) else np.nan,
        "f_cvd_5m": norm(last5.delta.sum()) if len(last5) else np.nan,
        "f_cvd_15m": norm(last15.delta.sum()) if len(last15) else np.nan,
        "f_part_5m": norm(last5.vol.mean()) if len(last5) else np.nan,
        "f_part_15m": norm(last15.vol.mean()) if len(last15) else np.nan,
        "f_absorb_5m": (float(abs(last5.delta.sum()) / last5.vol.sum())
                        if len(last5) and last5.vol.sum() > 0 else np.nan),
        "f_cvd_align": (int((sess.delta.sum() > 0) == (ev.side > 0))
                        if len(sess) else np.nan),   # LOGGED ONLY — never a gate (banned as a
        #                                              sign-confirmation filter; see docstring)
    }


# ------------------------------------------------------------------ run one candidate
def run_candidate(name: str, detect, ctxs: list[Ctx], fpd_all: dict) -> pd.DataFrame:
    rows = []
    for ctx in ctxs:
        fpd = fpd_all.get(ctx.day)
        if fpd is None or not len(fpd):
            continue
        try:
            evs = detect(ctx) or []
        except Exception as exc:                      # a broken candidate must not fake zero
            raise RuntimeError(f"{name} failed on {ctx.day}: {exc}") from exc
        for i, ev in enumerate(evs):
            risk = (ev.entry - ev.stop) * ev.side
            if risk <= 0 or not np.isfinite(risk):
                continue
            R, ex, be, ex_ts = walk_exit(ctx.g, ctx.w, ev)
            rows.append({
                "candidate": name, "date": ctx.day, "seq": i,
                "time": f"{ctx.w.ts.iloc[ev.t]:%H:%M}",
                "direction": "long" if ev.side > 0 else "short",
                "entry": round(ev.entry, 2), "stop": round(ev.stop, 2),
                "target": round(ev.entry + ev.side * TARGET_R * risk, 2),
                "exit": round(float(ex), 2), "exit_time": f"{pd.Timestamp(ex_ts):%H:%M}",
                "risk_pts": round(risk, 2), "R": round(R, 3),
                "outcome": "win" if R >= TARGET_R else ("BE" if R == 0 else
                           ("loss" if R <= -1 else "timeout")),
                "be_moved": be, "tag": ev.tag, "ambiguous": ev.ambiguous,
                "intrabar": ev.intrabar,
                "period": "discovery" if ctx.day < SPLIT else "holdout",
                **features(ctx, ev, fpd, risk)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ statistics (W6)
def clustered(d: pd.DataFrame) -> dict:
    """Session-clustered summary. `t` is ALWAYS the clustered one; the naive one is shown so the
    overstatement is visible, never as the headline."""
    n = len(d)
    if not n:
        return {"n": 0, "sessions": 0}
    R = d.R.astype(float)
    mean = float(R.mean())
    cost = float((COST_USD / (d.risk_pts * PT)).mean())
    eq = R.cumsum()
    sd = float(R.std(ddof=1)) if n > 1 else np.nan
    dev = R - mean
    cl = dev.groupby(d.date).sum().to_numpy()
    nc = len(cl)
    se = (np.sqrt((cl ** 2).sum()) / n * np.sqrt(nc / (nc - 1))) if nc > 1 else np.nan
    t_cl = mean / se if se and se == se and se > 0 else np.nan
    return {
        "n": n, "sessions": nc, "per_session": n / nc if nc else np.nan,
        "win%": 100 * float((R >= TARGET_R).mean()),
        "BE%": 100 * float((R == 0).mean()),
        "loss%": 100 * float((R <= -1).mean()),
        "TO%": 100 * float(((R > -1) & (R < TARGET_R) & (R != 0)).mean()),
        "avgR": mean, "cost": cost, "exp": mean - cost, "totR": float(R.sum()),
        "maxDD": float((eq.cummax() - eq).max()),
        "med_stop": float(d.risk_pts.median()),
        "t_clus": t_cl, "t_naive": mean / (sd / np.sqrt(n)) if sd and n > 1 else np.nan,
        "se_clus": se,
    }


def show(rows: list[tuple[str, dict]], title: str) -> None:
    print(f"\n{title}")
    hdr = (f"  {'candidate':<26}{'n':>6}{'sess':>6}{'/s':>5}{'win/BE/loss/TO':>23}"
           f"{'avgR':>8}{'cost':>7}{'exp':>9}{'totR':>9}{'DD':>7}{'stop':>7}{'t_clus':>8}")
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for name, s in rows:
        if not s.get("n"):
            print(f"  {name:<26}{0:>6}   no events"); continue
        mix = "%.0f/%.0f/%.0f/%.0f" % (s["win%"], s["BE%"], s["loss%"], s["TO%"])
        print(f"  {name:<26}{s['n']:>6}{s['sessions']:>6}{s['per_session']:>5.1f}{mix:>23}"
              f"{s['avgR']:>+8.3f}{s['cost']:>7.3f}{s['exp']:>+9.3f}{s['totR']:>+9.1f}"
              f"{s['maxDD']:>7.1f}{s['med_stop']:>7.1f}{s['t_clus']:>+8.2f}")


# ------------------------------------------------------------------ noise floor (ledger 0.7)
def both_directions(ctxs_by_day: dict, d: pd.DataFrame) -> pd.DataFrame:
    """For every logged event, score the SAME entry and the SAME stop DISTANCE in BOTH directions.

    This is the matched control. It preserves time-of-day, event count per session, session
    clustering, stop geometry and the locked exit, and destroys ONLY the directional mechanism —
    which is the thing under test. Precomputing both outcomes once turns each noise replication
    into a coin flip per event instead of a fresh backtest, so thousands of reps are cheap.
    """
    out = []
    for r in d.itertuples():
        ctx = ctxs_by_day[r.date]
        ti = int(ctx.w.index[ctx.w.ts.dt.strftime("%H:%M") == r.time][0])
        risk = float(r.risk_pts)
        vals = {}
        for side in (+1, -1):
            # ⚠️ The control MUST carry the real event's intrabar semantics. Hardcoding
            # intrabar=True applied the same-bar stop check to close-entry candidates that never
            # face it, so 4 of 293 controls could not reproduce their own real R. Caught by the
            # assertion that a real R must equal one of its two precomputed directions.
            ev = Event(t=ti, side=side, entry=float(r.entry),
                       stop=float(r.entry) - side * risk, intrabar=bool(r.intrabar))
            vals[side] = walk_exit(ctx.g, ctx.w, ev)[0]
        # `seq` disambiguates sessions that produce more than one event — joining on
        # (candidate, date) alone pairs them crosswise.
        out.append({"candidate": r.candidate, "date": r.date, "seq": int(r.seq),
                    "R_long": vals[+1], "R_short": vals[-1], "risk_pts": risk})
    return pd.DataFrame(out)


def noise_floor(both: pd.DataFrame, reps: int = 2000, seed: int = 20260807) -> dict:
    """Distribution of BEST-OF-K discovery expectancy under random direction.

    Simulates the SEARCH, not a single strategy: each rep re-randomises every candidate, takes
    the best of them, and that best is the statistic. This is what our own best has to beat.
    """
    rng = np.random.default_rng(seed)
    names = sorted(both.candidate.unique())
    parts = {c: both[both.candidate == c] for c in names}
    best, per = np.empty(reps), {c: np.empty(reps) for c in names}
    for i in range(reps):
        vals = []
        for c in names:
            x = parts[c]
            pick = rng.random(len(x)) < 0.5
            R = np.where(pick, x.R_long.to_numpy(), x.R_short.to_numpy())
            cost = float((COST_USD / (x.risk_pts.to_numpy() * PT)).mean())
            e = float(R.mean()) - cost
            per[c][i] = e
            vals.append(e)
        best[i] = max(vals)
    return {"best": best, "per": per, "names": names}


if __name__ == "__main__":
    ctxs = build_contexts()
    disc = [c for c in ctxs if c.day < SPLIT]
    hold = [c for c in ctxs if c.day >= SPLIT]
    print("SYNTHESIS SWEEP HARNESS — 08:00-10:30 ET entries only\n")
    print(f"  span {SPAN_LO} -> {SPAN_HI}   qualifying sessions {len(ctxs)}")
    print(f"  DISCOVERY {len(disc):>4}  {disc[0].day} -> {disc[-1].day}")
    print(f"  HOLDOUT   {len(hold):>4}  {hold[0].day} -> {hold[-1].day}")
    print(f"  canonical news sessions: discovery {sum(c.is_news for c in disc)}"
          f"   holdout {sum(c.is_news for c in hold)}")
    f = flow_by_day(ctxs)
    print(f"  sessions with flow: {len(f)} of {len(ctxs)}")
