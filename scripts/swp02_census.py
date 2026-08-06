#!/usr/bin/env python3
"""SWP-02 L0 census — JadeCap's sweep premise, ICT entry stripped out.

Authorised by docs/PREREG-sweep-noict.md.

KEPT: D1 bias, 1-hour untapped swing points, the raid, and the hourly close back inside.
THROWN AWAY: the 5-minute FVG / order-block entry and the "stop below candle two" — his own
words call the entry model interchangeable ("VWAP, moving averages, volume profiles,
whatever... because the context and narrative is already in place"), so testing his
specific one as load-bearing would be a category error.

THE CONTROL IS THE POINT. Confirmed raids are compared against raids that did NOT confirm,
same day, same bias, same levels. If those two behave the same, the swing-failure
confirmation adds nothing and the premise is decoration. A forward move measured without
that control only proves that price moves.

    python -m scripts.swp02_census [--session ny|london]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
PREREG = "docs/PREREG-sweep-noict.md"
BARFILES = ["data/reference/nq_1m_master.parquet",
            "data/reference/nq_1m_feb_jul2026.parquet"]
SPAN = ("2025-01-01", "2026-07-15")
HORIZONS = (30, 60, 120)          # minutes after confirmation

SESSIONS = {                       # ET hour windows in which a confirmation may trade
    "ny": (9, 12),
    "london": (3, 6),
}


def load_bars() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(ROOT / f).drop(columns=["roll"], errors="ignore")
                   for f in BARFILES], ignore_index=True)
    b = b.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    return b.set_index("mi")


def hourly(b: pd.DataFrame) -> pd.DataFrame:
    h = b.resample("1h", label="right", closed="right").agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last")).dropna()
    return h


def swings(h: pd.DataFrame) -> tuple[list, list]:
    """3-candle fractals, confirmed only on the third candle's close (his definition).

    Returned with the CONFIRMATION time, not the pivot time, so nothing is usable before
    the market could have known it.
    """
    hi, lo = h.high.to_numpy(), h.low.to_numpy()
    sh, sl = [], []
    for i in range(1, len(h) - 1):
        if hi[i] > hi[i - 1] and hi[i] > hi[i + 1]:
            sh.append((h.index[i + 1], float(hi[i])))     # confirmed at i+1's close
        if lo[i] < lo[i - 1] and lo[i] < lo[i + 1]:
            sl.append((h.index[i + 1], float(lo[i])))
    return sh, sl


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="ny", choices=sorted(SESSIONS))
    a = ap.parse_args()
    lo_h, hi_h = SESSIONS[a.session]
    b = load_bars()
    b = b[(b.index >= pd.Timestamp(SPAN[0], tz=NY)) & (b.index <= pd.Timestamp(SPAN[1], tz=NY))]
    H = hourly(b)
    H["day"] = H.index.strftime("%Y-%m-%d")

    # D1 bias: yesterday's daily close vs the day before. Strictly prior information.
    d = b.resample("1D").agg(close=("close", "last")).dropna()
    d["bias"] = np.sign(d.close.diff())
    bias = {k.strftime("%Y-%m-%d"): v for k, v in d.bias.items()}

    days = sorted(H.day.unique())
    rows = []
    for i, day in enumerate(days):
        prev = days[i - 1] if i else None
        if prev is None:
            continue
        bi = bias.get(prev, 0.0)                    # yesterday's completed daily candle
        if not bi:
            continue
        ph = H[H.day == prev]
        if len(ph) < 6:
            continue
        sh, sl = swings(ph)
        # bullish bias -> hunt raids of swing LOWS (and mirror)
        levels = [p for _, p in (sl if bi > 0 else sh)]
        if not levels:
            continue
        dh = H[(H.day == day) & (H.index.hour >= lo_h) & (H.index.hour < hi_h)]
        tapped = set()
        for ts, bar in dh.iterrows():
            for lv in levels:
                if lv in tapped:
                    continue
                raided = (bar.low < lv) if bi > 0 else (bar.high > lv)
                if not raided:
                    continue
                tapped.add(lv)
                confirmed = (bar.close > lv) if bi > 0 else (bar.close < lv)
                strong = (bar.close > bar.open) if bi > 0 else (bar.close < bar.open)
                fwd = b[b.index > ts]
                r = {"day": day, "era": day[:4], "ts": ts, "bias": bi, "level": lv,
                     "confirmed": bool(confirmed), "strong_close": bool(strong),
                     "hour": ts.hour,
                     "sweep_ext": float(bar.low if bi > 0 else bar.high)}
                for hz in HORIZONS:
                    w = fwd.iloc[:hz]
                    r[f"f{hz}"] = (float((w.close.iloc[-1] - bar.close) * bi)
                                   if len(w) == hz else np.nan)
                rows.append(r)
        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{len(days)}] raids {len(rows):,}", flush=True)

    E = pd.DataFrame(rows)
    if E.empty:
        print("NO RAIDS — check the trigger, this is a bug not a finding")
        return 1
    nd = E.day.nunique()
    C = E[E.confirmed]
    U = E[~E.confirmed]

    L = [f"# SWP-02 — L0 census ({a.session})", "",
         f"Authorised by `{PREREG}`. **Census only** — the event and its forward path",
         "against unconfirmed raids as the control. No expectancy claim (§5.9.1).", "",
         f"**{len(E):,} raids of untapped 1H swing points over {nd} sessions "
         f"({len(E)/nd:.2f}/session).**",
         f"**{len(C):,} confirmed** by an hourly close back inside "
         f"({len(C)/max(len(E),1):.0%}) = **{len(C)/nd:.2f}/session.**", "",
         "| period | sessions | raids | confirmed | confirmed/session |",
         "|---|---:|---:|---:|---:|"]
    for era in sorted(E.era.unique()):
        s, sc = E[E.era == era], C[C.era == era]
        L.append(f"| {era} | {s.day.nunique()} | {len(s):,} | {len(sc):,} | "
                 f"{len(sc)/s.day.nunique():.2f} |")

    L += ["", "## The mechanism test — confirmed vs UNCONFIRMED raids", "",
          "Forward move in the bias direction, points. If these match, the swing-failure",
          "confirmation adds nothing and the premise is decoration.", "",
          "| horizon | confirmed | unconfirmed | **edge** | 2025 edge | 2026 edge |",
          "|---|---:|---:|---:|---:|---:|"]
    ok = False
    for hz in HORIZONS:
        c, u = C[f"f{hz}"].dropna(), U[f"f{hz}"].dropna()
        if len(c) < 30 or len(u) < 30:
            continue
        eras = []
        for era in ("2025", "2026"):
            ce, ue = C[C.era == era][f"f{hz}"].dropna(), U[U.era == era][f"f{hz}"].dropna()
            eras.append(ce.mean() - ue.mean() if len(ce) > 20 and len(ue) > 20 else np.nan)
        if np.isfinite(eras[0]) and np.isfinite(eras[1]) and eras[0] > 0 and eras[1] > 0:
            ok = True
        L.append(f"| t+{hz}min | {c.mean():+.2f} | {u.mean():+.2f} | "
                 f"**{c.mean()-u.mean():+.2f} pt** | {eras[0]:+.2f} | {eras[1]:+.2f} |")

    per = len(C) / nd
    L += ["", "## Declared kill line", "", "| test | bar | observed | verdict |",
          "|---|---|---:|---|",
          f"| confirmed setups/session | ≥ 0.5 | {per:.2f} | "
          f"{'**PASS**' if per >= 0.5 else '**FAIL**'} |",
          f"| confirmed beats unconfirmed, both eras | any horizon | "
          f"{'yes' if ok else 'no'} | {'**PASS**' if ok else '**FAIL**'} |", "",
          ("**L0 PASSES.** The setup occurs at usable frequency and the confirmation "
           "carries information beyond the raid itself."
           if (per >= 0.5 and ok) else
           "**L0 FAILS its declared line — the family dies here.**"), ""]
    text = "\n".join(L)
    print(text)
    (ROOT / f"output/swp02_census_{a.session}.md").write_text(text)
    E.to_parquet(ROOT / f"output/swp02_events_{a.session}.parquet", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
