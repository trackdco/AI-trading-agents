#!/usr/bin/env python3
"""NYIM — New York Intraday Momentum. A model built from scratch, not a filter on the canon.

ANGUS 2026-08-06: *"i am not telling you to optimise my shit man, im telling you to scour the
internet, become a master trader and literally build your own model."*

He is right that the canon is the wrong thing to keep filtering.
`research/findings/the-geometry-frontier.md` proved why: 33 variables, 93 buckets, ONE above
zero mean R and that one is +0.003, because every variable in that book is a proxy for target
distance. This model shares NOTHING with it -- no VWAP, no Bollinger basis, no POC, no
confluence cluster, no level stack. It is a time-and-direction rule.

THE PUBLISHED PREMISE
Gao, Han, Li & Zhou, "Market Intraday Momentum", Journal of Financial Economics 2018
(SSRN 2440866). On S&P 500 ETF high-frequency data 1993-2013, the first half-hour return
since the PREVIOUS CLOSE positively predicts the last half-hour return: scaled slope 6.94,
significant at 1%, R^2 1.6%. Present in ten other actively traded ETFs and in FTSE 100 and
EuroStoxx 50 index futures; APAC replications exist. Predictability is STRONGER on more
volatile days, higher volume days, recession days and macro-release days.

Proposed mechanism: informed and institutional flow initiates near the open, and late-day
rebalancing plus momentum traders complete the same direction into the close. That is a
liquidity/flow story, not a chart-pattern story, which is exactly why it is worth testing --
it can be wrong in ways our existing families cannot.

WHY IT SUITS THIS PROP OBJECTIVE SPECIFICALLY
Angus: *"End of day drawdown means we can afford small losing streaks day to day as long as
we end green"* and *"id rather something that can do 50 points a day consistently year on
year."* Every arm here is FLAT AT THE CLOSE by construction, so intraday heat -- which the
end-of-day trailing drawdown makes free -- is never carried overnight and never converts into
a drawdown breach.

TWO ARMS, and the difference matters:

  V1  the paper, unchanged. At 15:30 ET take the SIGN of the 09:30-10:00 return and hold to
      16:00. ZERO fitted parameters. It cannot overfit, which makes it the honest control:
      if V1 is dead, any V2 result is a parameter search finding a ghost.
  V2  the volatility-band variant that recent ES/NQ implementations use. Bound the day's open
      by a "noise area" from recent realised range; the first close outside it sets direction;
      hold to the close with the opposite band as the stop. This has parameters, so the WHOLE
      SWEEP is reported, never the best cell alone.

DISCOVER ON 2025, VALIDATE ON 2026. The 2023/24 holdout stays sealed.

    python -m scripts.nyim_model
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
BARS = ("data/reference/nq_1m_master.parquet", "data/reference/nq_1m_feb_jul2026.parquet")
OPEN_M, CLOSE_M = 9 * 60 + 30, 16 * 60
FRICTION = 2.0          # points per round trip, the standing bar
PT = 20.0               # $ per NQ point, 1 contract


def load() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
                   for p in BARS], ignore_index=True)
    b = b.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    t = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b["day"] = t.dt.strftime("%Y-%m-%d")
    b["hm"] = t.dt.hour * 60 + t.dt.minute
    return b[(b.hm >= OPEN_M) & (b.hm < CLOSE_M)].reset_index(drop=True)


def sessions(b: pd.DataFrame) -> pd.DataFrame:
    g = b.groupby("day")
    S = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
              close=("close", "last"), vol=("volume", "sum"))
    # first half hour: 09:30 through 09:59 inclusive
    fh = b[b.hm < OPEN_M + 30].groupby("day").agg(fh_close=("close", "last"))
    # last half hour opens at 15:30
    lh = b[b.hm >= CLOSE_M - 30].groupby("day").agg(lh_open=("open", "first"))
    S = S.join(fh).join(lh)
    S["prev_close"] = S.close.shift(1)
    S["r_first"] = S.fh_close / S.prev_close - 1.0          # the paper's r1
    S["r_last"] = S.close / S.lh_open - 1.0                 # the paper's r13
    S["pts_last"] = S.close - S.lh_open
    S["range"] = S.high - S.low
    S["era"] = S.index.str[:4]
    return S.dropna(subset=["r_first", "r_last"])


def stat(daily: pd.Series, n_trades: pd.Series | None = None) -> dict:
    """Prop-shaped read on a daily net-points series."""
    d = daily.dropna()
    act = d[d != 0]
    if len(act) < 20:
        return {}
    sh = d.mean() / d.std() * np.sqrt(252) if d.std() > 0 else np.nan
    return {"days": len(act), "net_pt_day": act.mean(), "total": d.sum(),
            "green": (act > 0).mean(), "sharpe": sh,
            "worst10": d.rolling(10).sum().min(),
            "maxday_share": (act.max() / d.sum()) if d.sum() > 0 else np.nan}


def show(title: str, rows: list[tuple[str, dict]]) -> list[str]:
    L = [f"### {title}", "",
         "| arm | days | net pt/day | total pt | green | Sharpe | worst 10d | max-day share |",
         "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for nm, s in rows:
        if not s:
            L.append(f"| {nm} | — | — | — | — | — | — | — |")
            continue
        L.append(f"| {nm} | {s['days']} | **{s['net_pt_day']:+.2f}** | {s['total']:+,.0f} | "
                 f"{s['green']:.0%} | {s['sharpe']:.2f} | {s['worst10']:+,.0f} | "
                 f"{s['maxday_share']:.0%} |" if np.isfinite(s.get('maxday_share', np.nan))
                 else f"| {nm} | {s['days']} | **{s['net_pt_day']:+.2f}** | {s['total']:+,.0f} "
                      f"| {s['green']:.0%} | {s['sharpe']:.2f} | {s['worst10']:+,.0f} | — |")
    L.append("")
    return L


def main() -> int:
    b = load()
    S = sessions(b)
    L = [f"# NYIM — New York Intraday Momentum", "",
         "A model built from the published premise, sharing nothing with the canon: no VWAP,",
         "no Bollinger basis, no POC, no confluence. Flat at the close every day by",
         "construction, which is what the end-of-day trailing drawdown rewards.", "",
         f"**{len(S)} sessions, {S.index.min()} → {S.index.max()}.** "
         f"Friction {FRICTION:g} pt/round trip. 1 contract, points.", "",
         "---", "", "## The premise itself, before any strategy", "",
         "Does the first half-hour return predict the last half-hour return on NQ?", "",
         "| period | n | corr(r_first, r_last) | slope | same-sign rate |",
         "|---|---:|---:|---:|---:|"]
    for nm, X in [("ALL", S), ("2025", S[S.era == "2025"]), ("2026", S[S.era == "2026"])]:
        if len(X) < 30:
            continue
        c = X.r_first.corr(X.r_last)
        sl = np.polyfit(X.r_first, X.r_last, 1)[0]
        ss = (np.sign(X.r_first) == np.sign(X.r_last)).mean()
        L.append(f"| {nm} | {len(X)} | **{c:+.3f}** | {sl:+.3f} | {ss:.1%} |")
    L += ["", "A positive correlation and a same-sign rate above 50% is the paper's claim.", ""]

    # ---- V1: the paper, no parameters ------------------------------------------------
    sig = np.sign(S.r_first)
    v1 = sig * S.pts_last - FRICTION
    v1 = v1.where(sig != 0, 0.0)
    L += ["---", "", "## V1 — the paper, unchanged. Zero fitted parameters.", "",
          "At 15:30 ET take the sign of the 09:30–10:00 return; hold to the 16:00 close.",
          "Nothing here can be overfitted, which makes it the honest control.", ""]
    L += show("V1", [("ALL", stat(v1)), ("2025", stat(v1[S.era == "2025"])),
                     ("2026", stat(v1[S.era == "2026"]))])

    # conditioning the paper says should help: volatile / high-volume days
    rq = S.range.rolling(20).median()
    volq = S.vol.rolling(20).median()
    L += ["The paper says predictability is stronger on volatile and high-volume days. "
          "Testing that claim rather than assuming it:", ""]
    L += show("V1 conditioned", [
        ("range > 20d median", stat(v1[S.range > rq])),
        ("range < 20d median", stat(v1[S.range <= rq])),
        ("volume > 20d median", stat(v1[S.vol > volq])),
        ("volume < 20d median", stat(v1[S.vol <= volq]))])

    # ---- V2: noise-area breakout, full sweep -----------------------------------------
    L += ["---", "", "## V2 — noise-area breakout. Parameters, so the WHOLE sweep is shown.", "",
          "Bound the open by a band from recent realised range; the first close outside it",
          "sets direction; hold to the close, opposite band as the stop. Reporting every cell",
          "so the surface is visible rather than its best corner.", "",
          "| lookback | mult | days | net pt/day | total | green | Sharpe | 2025 | 2026 |",
          "|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    day_open = b.groupby("day").open.first()
    excursion = pd.concat([(S.high - S.open).abs(), (S.open - S.low).abs()], axis=1).max(axis=1)
    grid = []
    for lb in (5, 10, 14, 20):
        base = excursion.rolling(lb).mean().shift(1)
        for mult in (0.25, 0.5, 0.75, 1.0):
            band = base * mult
            pnl = {}
            for day, g in b.groupby("day"):
                if day not in band.index or not np.isfinite(band.get(day, np.nan)):
                    continue
                o, w = float(day_open[day]), float(band[day])
                hi, lo = o + w, o - w
                c = g.close.to_numpy(float)
                up = np.flatnonzero(c > hi)
                dn = np.flatnonzero(c < lo)
                if not len(up) and not len(dn):
                    pnl[day] = 0.0
                    continue
                iu = up[0] if len(up) else 10**9
                idn = dn[0] if len(dn) else 10**9
                if iu < idn:
                    ent, d_, stop = c[iu], 1, lo
                else:
                    ent, d_, stop = c[idn], -1, hi
                rest = g.iloc[(min(iu, idn) + 1):]
                if len(rest) == 0:
                    pnl[day] = -FRICTION
                    continue
                hit = (rest.low <= stop) if d_ == 1 else (rest.high >= stop)
                ex = float(stop) if hit.any() else float(rest.close.iloc[-1])
                pnl[day] = (ex - ent) * d_ - FRICTION
            P = pd.Series(pnl).reindex(S.index).fillna(0.0)
            s = stat(P)
            s25, s26 = stat(P[S.era == "2025"]), stat(P[S.era == "2026"])
            if not s:
                continue
            grid.append((lb, mult, s, s25, s26))
            L.append(f"| {lb} | {mult:g} | {s['days']} | **{s['net_pt_day']:+.2f}** | "
                     f"{s['total']:+,.0f} | {s['green']:.0%} | {s['sharpe']:.2f} | "
                     + " | ".join(f"{x['net_pt_day']:+.2f}" if x else "—" for x in (s25, s26))
                     + " |")

    pos = [g for g in grid if g[3] and g[4] and g[3]["net_pt_day"] > 0 and g[4]["net_pt_day"] > 0]
    L += ["", f"**{len(pos)} of {len(grid)} cells are positive in BOTH eras independently.** "
          "A parameter surface where only a corner works is a ghost; one where most of the "
          "surface works in both eras is a mechanism.", ""]

    text = "\n".join(L)
    print(text)
    (ROOT / "output/nyim_model.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
