#!/usr/bin/env python3
"""LQV-01 L0 census — the liquidity vacuum. Authorised by docs/PREREG-liquidity-vacuum.md.

Clean slate. No BB, no VWAP, no POC, no confluence, no level of any kind. The trigger does
not read a price level — it reads how much resting size is left on each side of the book
relative to that side's own recent norm.

RARE BY MECHANISM, NOT BY FILTERING. Every model in this repo fires on a common event and
filters down (33 triggers/session -> 5 setups -> 1 trade), which hands all the work to the
filter and is where overfitting lives. Here the population IS the edge.

NOTHING ABSOLUTE. Every threshold is a trailing quantile computed strictly before the
minute being judged, so the model adapts to volume regime by construction. The canon could
not adapt because its rules were frozen 2025 numbers (Q_WALLSZ_MIN = 7.0 and friends).

CENSUS ONLY. This measures the EVENT and the forward path against a random-minute control.
It can kill on the premise and it makes no expectancy claim (5.9.1).

    python -m scripts.lqv_census --session london [--procs 4]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_depth import load_day  # noqa: E402

NY = "America/New_York"
PREREG = "docs/PREREG-liquidity-vacuum.md"

BAND_PTS = 10.0        # depth band around mid, in points
WIN = 20               # trailing window (minutes) for each side's own norm
Q_THIN = 0.10          # thin side in the bottom DECILE of its OWN ratio distribution
QWIN = 60              # trailing window (minutes) that distribution is measured over
SEED = 20260805
HORIZONS = (5, 15, 30)

SESSIONS = {
    "london": {"dir": "data/reference/depth_london", "hours": (3, 6)},
    "ny": {"dir": "data/reference/depth_2025", "hours": (8, 11)},
}


def minute_book(dep: pd.DataFrame) -> pd.DataFrame:
    """Per-minute resting size within BAND_PTS of mid, per side. One row per snapshot."""
    b = dep[dep.side == "bid"].groupby("ts").agg(bb=("price", "max"))
    a = dep[dep.side == "ask"].groupby("ts").agg(ba=("price", "min"))
    m = b.join(a, how="inner")
    m["mid"] = (m.bb + m.ba) / 2.0
    d = dep.join(m["mid"], on="ts")
    near = d[(d.price - d.mid).abs() <= BAND_PTS]
    g = near.groupby(["ts", "side"])["size"].sum().unstack(fill_value=0.0)
    for c in ("bid", "ask"):
        if c not in g:
            g[c] = 0.0
    return g.join(m["mid"]).sort_index()


def events(g: pd.DataFrame) -> list[dict]:
    """VACUUM = one side collapses vs its OWN trailing norm while the other holds.

    Norms are shifted by one minute so the judgement at t uses only data strictly before t.
    Each episode is counted once (fires on the transition, not every minute it persists).
    """
    out = []
    for thin, thick in (("bid", "ask"), ("ask", "bid")):
        nt = g[thin].rolling(WIN, min_periods=WIN).median().shift(1)
        nk = g[thick].rolling(WIN, min_periods=WIN).median().shift(1)
        rt, rk = g[thin] / nt.replace(0, np.nan), g[thick] / nk.replace(0, np.nan)
        # Q_THIN IS A QUANTILE, NOT A RATIO. The first version compared rt to a fixed
        # 0.25 -- an absolute threshold, the exact defect this prereg exists to avoid --
        # and it was unreachable: aggregate side size never falls below 0.56x its own
        # trailing median (min 0.562, 1st pct 0.645 over five sample days), so the census
        # returned zero events. Judging rt against ITS OWN trailing distribution is both
        # what the prereg declared and adaptive by construction.
        cut = rt.rolling(QWIN, min_periods=QWIN // 2).quantile(Q_THIN).shift(1)
        cond = (rt <= cut) & (rk >= 1.0)
        fresh = cond & ~cond.shift(1, fill_value=False)
        for ts in g.index[fresh.fillna(False)]:
            out.append({"ts": ts, "thin": thin,
                        # thin BID -> nothing below -> price travels DOWN
                        "dirn": -1 if thin == "bid" else 1,
                        "mid": float(g.loc[ts, "mid"]),
                        "depletion": float(rt.loc[ts]), "other": float(rk.loc[ts])})
    return sorted(out, key=lambda r: r["ts"])


def forward(g: pd.DataFrame, ts, dirn: int) -> dict:
    """Directional move after the event, in points, signed by the thin direction."""
    fut = g.loc[g.index > ts]
    r = {}
    for h in HORIZONS:
        w = fut.iloc[:h]
        if len(w) < h:
            r[f"f{h}"] = np.nan
            continue
        r[f"f{h}"] = float((w.mid.iloc[-1] - g.loc[ts, "mid"]) * dirn)
        r[f"mfe{h}"] = float(((w.mid.max() - g.loc[ts, "mid"]) if dirn > 0
                              else (g.loc[ts, "mid"] - w.mid.min())))
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="london", choices=sorted(SESSIONS))
    ap.add_argument("--max-days", type=int, default=400)
    a = ap.parse_args()
    spec = SESSIONS[a.session]
    ddir = ROOT / spec["dir"]
    files = sorted(ddir.glob("*.csv"))[: a.max_days]
    print(f"LQV-01 census — {a.session}, {len(files)} depth days", flush=True)

    rng = np.random.default_rng(SEED)
    E, C = [], []
    for i, f in enumerate(files):
        # DO NOT scrape digits: 'glbx-mdp3-20250602...' yields '32025060' because the 3
        # in mdp3 comes first, which parsed every day as 3202-50-60 and silently returned
        # zero events across all 295 files. Match the date shape explicitly.
        m = re.search(r"(20\d{2})-?(\d{2})-?(\d{2})", f.name)
        if not m:
            continue
        day = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        dep = load_day(day, ddir)
        if dep is None or dep.empty:
            continue
        g = minute_book(dep)
        if len(g) < WIN + max(HORIZONS) + 5:
            continue
        ev = events(g)
        for e in ev:
            E.append({**e, "day": day, **forward(g, e["ts"], e["dirn"])})
        # CONTROL: same day, same count, random minutes, random side. Isolates the
        # vacuum from "the market moves after any minute in this session".
        elig = g.index[WIN: len(g) - max(HORIZONS) - 1]
        if len(elig) and ev:
            for ts in rng.choice(elig, size=min(len(ev), len(elig)), replace=False):
                d = int(rng.choice([-1, 1]))
                C.append({"day": day, "ts": ts, "dirn": d, **forward(g, ts, d)})
        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(files)}] events {len(E):,}", flush=True)

    E, C = pd.DataFrame(E), pd.DataFrame(C)
    if E.empty:
        print("NO EVENTS — premise kill line fires")
        return 1
    E["era"] = E.day.str[:4]
    C["era"] = C.day.str[:4]
    nd = E.day.nunique()

    L = [f"# LQV-01 — L0 census ({a.session})", "",
         f"Authorised by `{PREREG}`. **Census only** — measures the event and its forward",
         "path against a random-minute control. No expectancy claim (§5.9.1).", "",
         f"**{len(E):,} events over {nd} sessions = {len(E)/nd:.2f}/session.** "
         f"Depth band ±{BAND_PTS:.0f}pt, trailing norm {WIN}min, thin-side quantile "
         f"{Q_THIN:.2f}. Every threshold relative; nothing absolute.", "",
         "| period | sessions | events | /session |", "|---|---:|---:|---:|"]
    for era in sorted(E.era.unique()):
        s = E[E.era == era]
        L.append(f"| {era} | {s.day.nunique()} | {len(s):,} | "
                 f"{len(s)/s.day.nunique():.2f} |")
    L += ["", "## The mechanism test — forward move into the thin side vs control", "",
          "| horizon | vacuum mean | control mean | **edge** | vacuum med | 2025 edge | 2026 edge |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    ok_any = False
    for h in HORIZONS:
        c = f"f{h}"
        v, k = E[c].dropna(), C[c].dropna()
        if not len(v) or not len(k):
            continue
        eras = []
        for era in ("2025", "2026"):
            ve, ke = E[E.era == era][c].dropna(), C[C.era == era][c].dropna()
            eras.append(ve.mean() - ke.mean() if len(ve) > 30 and len(ke) > 30 else np.nan)
        edge = v.mean() - k.mean()
        if np.isfinite(eras[0]) and np.isfinite(eras[1]) and eras[0] > 0 and eras[1] > 0:
            ok_any = True
        L.append(f"| t+{h}min | {v.mean():+.2f} | {k.mean():+.2f} | **{edge:+.2f} pt** | "
                 f"{v.median():+.2f} | {eras[0]:+.2f} | {eras[1]:+.2f} |")
    per = len(E) / nd
    L += ["", "## Declared kill line", "",
          f"| test | bar | observed | verdict |", "|---|---|---:|---|",
          f"| events/session | ≥ 0.5 | {per:.2f} | "
          f"{'**PASS**' if per >= 0.5 else '**FAIL**'} |",
          f"| beats control, both eras | any horizon | "
          f"{'yes' if ok_any else 'no'} | {'**PASS**' if ok_any else '**FAIL**'} |", "",
          ("**L0 PASSES.** The event exists at usable frequency and price moves into the "
           "thin side more than after a random minute, in both eras."
           if (per >= 0.5 and ok_any) else
           "**L0 FAILS its declared line — the family dies here.**"), ""]
    text = "\n".join(L)
    print(text)
    (ROOT / f"output/lqv_census_{a.session}.md").write_text(text)
    E.to_parquet(ROOT / f"output/lqv_events_{a.session}.parquet", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
