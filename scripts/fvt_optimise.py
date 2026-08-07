#!/usr/bin/env python3
"""Per-session optimisation of the FVT continuation framework, guarded, 2024-2026.

ANGUS 2026-08-06: *"lets optimise each session now and see if we can turn around. run a loss
diagnosis etc, rr variables, stop loss variables, entry time, lets see if we can turn it
around testing all available variables per session it traded, and we can apply what we
optimise in this 3 year period to 2023 to see if it holds."*

Fit on 2024-01-01 -> 2026-07-15 (793 sessions). **All of 2023 stays sealed** (310 sessions) as
the one-shot out-of-sample test for whatever survives.

WHY THIS IS FAST. Entries depend only on the entry rules; the stop and target affect ONLY the
exit. So each entry's forward path is walked ONCE and every (stop, RR) pair is then evaluated
exactly from that path. This is not an MAE/MFE approximation -- the path preserves ORDER, so
"which came first, stop or target" is answered correctly. An earlier MAE/MFE sweep in this
project got that wrong and had to be discarded, which is why it is spelled out here.

THE VARIABLE SPACE, per session:
    stop multiplier   on JJ's ATR tiers (50/25/16.5 pt)
    RR target         the multiple of the stop
    entry window      how many minutes into the session count as "continuation"
    attempt cap       how many entries per session-window are allowed

THE GUARD IS THE POINT. This is a large grid and a large grid is a machine for false
positives: the previous 20-cell session x RR sweep returned PBO 0.709, meaning the in-sample
best cell was usually a BELOW-median out-of-sample performer. So every session's grid is
scored as one family with CSCV/PBO and a Deflated Sharpe that knows the trial count, and the
per-session verdict is reported whether or not it is flattering.

CONSISTENCY BAR: positive in 2024, 2025 AND 2026 independently. Two eras was not enough --
it passed NY AM and 6PM, both of which collapse once 2024 is included.

    python -m scripts.fvt_optimise
"""

from __future__ import annotations

import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.fvt_model as F  # noqa: E402
from src.validation.overfit import cscv_pbo, deflated_sharpe, sharpe, walk_forward  # noqa: E402

FRICTION = 2.0
MAX_CONT = 45          # widest continuation window considered; narrower ones are subsets
BASE_TIERS = [(20.0, 50.0), (7.0, 25.0), (0.0, 16.5)]
STOP_MULTS = (0.75, 1.0, 1.25, 1.5)
RRS = (1.5, 2.0, 2.5, 3.0, 4.0)
CONTS = (10, 15, 25, 45)
CAPS = (1, 2)
WINDOWS = F.WINDOW_SETS["all"]
WEND = {w: hi for w, _, hi in WINDOWS}
LAB = {"AM": "NY AM", "PM": "NY PM", "E18": "6PM", "E20": "8PM", "LDN": "London"}


def entries(b: pd.DataFrame) -> list[dict]:
    """Every continuation-phase entry within MAX_CONT minutes of each window open, each with
    its forward adverse/favourable excursion path to the window end."""
    b = b.copy()
    b["atr"] = F.atr_series(b, 1)
    rng = (b.high - b.low).to_numpy()
    upw = (b.high - np.maximum(b.open, b.close)).to_numpy()
    dnw = (np.minimum(b.open, b.close) - b.low).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        d_up = (b.close > b.open).to_numpy() & (np.where(rng > 0, dnw / rng, 1.0) <= F.WICK_MAX)
        d_dn = (b.close < b.open).to_numpy() & (np.where(rng > 0, upw / rng, 1.0) <= F.WICK_MAX)
    b["d_up"], b["d_dn"] = d_up, d_dn

    out = []
    for day, g in b.groupby("day"):
        g = g.reset_index(drop=True)
        hi, lo, cl = (g.high.to_numpy(float), g.low.to_numpy(float), g.close.to_numpy(float))
        hm, atr = g.hm.to_numpy(), g.atr.to_numpy(float)
        du, dd = g.d_up.to_numpy(), g.d_dn.to_numpy()

        sw_hi = np.full(len(g), np.nan)
        sw_lo = np.full(len(g), np.nan)
        lh = ll = np.nan
        for i in range(len(g)):
            if i >= 2:
                if hi[i - 1] > hi[i - 2] and hi[i - 1] > hi[i]:
                    lh = hi[i - 1]
                if lo[i - 1] < lo[i - 2] and lo[i - 1] < lo[i]:
                    ll = lo[i - 1]
            sw_hi[i], sw_lo[i] = lh, ll

        for wn, wlo, whi in WINDOWS:
            seg = np.flatnonzero(hm >= wlo)
            if not len(seg):
                continue
            fv = float(g.open.iloc[seg[0]])
            start = wlo + (F.SKIP_FIRST_MIN if wn == "AM" else 0)
            idx = np.flatnonzero((hm >= start) & (hm < min(whi, wlo + MAX_CONT)))
            for i in idx:
                if not np.isfinite(atr[i]):
                    continue
                above = cl[i] > fv
                d_ = 0
                if above and np.isfinite(sw_hi[i]) and cl[i] > sw_hi[i] and du[i]:
                    d_ = 1
                elif (not above) and np.isfinite(sw_lo[i]) and cl[i] < sw_lo[i] and dd[i]:
                    d_ = -1
                if d_ == 0:
                    continue
                fwd = np.flatnonzero((hm > hm[i]) & (hm < whi))
                if not len(fwd):
                    continue
                e = cl[i]
                adv = (e - lo[fwd]) if d_ == 1 else (hi[fwd] - e)
                fav = (hi[fwd] - e) if d_ == 1 else (e - lo[fwd])
                out.append({"day": day, "era": day[:4], "win": wn, "dir": d_, "entry": e,
                            "atr": float(atr[i]), "mins_in": int(hm[i] - wlo),
                            "adv": np.maximum.accumulate(adv),
                            "fav": np.maximum.accumulate(fav),
                            "last": float(cl[fwd[-1]])})
    return out


def evaluate(E: list[dict], stop_mult: float, rr: float, cont: int, cap: int) -> pd.DataFrame:
    tiers = [(a, s * stop_mult) for a, s in BASE_TIERS]
    rows = []
    seen: dict = {}
    for e in E:
        if e["mins_in"] >= cont:
            continue
        k = (e["day"], e["win"])
        n = seen.get(k, 0) + 1
        seen[k] = n
        if n > cap:
            continue
        sd = next(s for a, s in tiers if e["atr"] > a)
        tgt = sd * rr
        ts = np.argmax(e["adv"] >= sd) if (e["adv"] >= sd).any() else 10**9
        tt = np.argmax(e["fav"] >= tgt) if (e["fav"] >= tgt).any() else 10**9
        if ts == 10**9 and tt == 10**9:
            pts = (e["last"] - e["entry"]) * e["dir"] - FRICTION
        elif ts <= tt:
            pts = -sd - FRICTION
        else:
            pts = tgt - FRICTION
        rows.append({"day": e["day"], "era": e["era"], "win": e["win"], "pts": pts, "risk": sd})
    return pd.DataFrame(rows)


def main() -> int:
    b = F.load()
    fit = b[b.day >= "2024-01-01"]
    print(f"fit {fit.day.min()} -> {fit.day.max()} ({fit.day.nunique()} sessions); "
          f"2023 sealed ({b[b.day.str[:4]=='2023'].day.nunique()} sessions)", flush=True)
    E = entries(fit)
    print(f"{len(E):,} raw continuation entries within {MAX_CONT}m of a window open", flush=True)
    days = sorted(fit.day.unique())
    di = {d: i for i, d in enumerate(days)}

    grid = list(product(STOP_MULTS, RRS, CONTS, CAPS))
    print(f"grid: {len(grid)} combos x 5 sessions = {len(grid)*5} cells", flush=True)
    store: dict = {w: {"cols": [], "names": [], "rows": []} for w in LAB}
    for n, (sm, rr, ct, cap) in enumerate(grid):
        D = evaluate(E, sm, rr, ct, cap)
        if D.empty:
            continue
        for w in LAB:
            S = D[D.win == w]
            if len(S) < 150:
                continue
            es = [S[S.era == y].pts.mean() if (S.era == y).sum() > 30 else np.nan
                  for y in ("2024", "2025", "2026")]
            v = np.zeros(len(days))
            for d, g in S.groupby("day"):
                v[di[d]] = g.pts.sum()
            dd = S.groupby("day").pts.sum()
            store[w]["cols"].append(v)
            store[w]["names"].append(f"s{sm}/rr{rr}/c{ct}/cap{cap}")
            store[w]["rows"].append({"cfg": f"stop×{sm} RR{rr} cont{ct}m cap{cap}",
                                     "n": len(S), "per_day": len(S) / len(days),
                                     "net": S.pts.mean(), "win": (S.pts > 0).mean(),
                                     "green": (dd > 0).mean(),
                                     "e24": es[0], "e25": es[1], "e26": es[2],
                                     "all3": all(np.isfinite(x) and x > 0 for x in es)})
        if (n + 1) % 20 == 0:
            print(f"  [{n+1}/{len(grid)}]", flush=True)

    L = ["# FVT per-session optimisation, 2024-2026 (2023 sealed)", "",
         f"Fit span {fit.day.min()} → {fit.day.max()}, {fit.day.nunique()} sessions. "
         f"**All of 2023 held back.**", "",
         f"Grid per session: stop×{STOP_MULTS}, RR{RRS}, continuation window {CONTS}m, "
         f"attempt cap {CAPS} — {len(grid)} combos.", "",
         "Consistency bar: **positive in 2024, 2025 and 2026 independently.** Two eras was not "
         "enough — it passed NY AM and 6PM, both of which collapse once 2024 is added.", ""]

    survivors = {}
    for w in LAB:
        R = pd.DataFrame(store[w]["rows"])
        if R.empty:
            continue
        M = np.column_stack(store[w]["cols"])
        srs = np.array([sharpe(M[:, i]) for i in range(M.shape[1])])
        best = int(np.nanargmax(srs))
        p = cscv_pbo(M, S=16)
        dd = deflated_sharpe(M[:, best], M.shape[1], srs)
        wf = walk_forward(M, train=180, test=30)
        n3 = int(R.all3.sum())
        L += [f"## {LAB[w]}", "",
              f"{len(R)} cells scored. **{n3} positive in all three years.**", "",
              "| config | n | /day | net pt | win% | green | 2024 | 2025 | 2026 | 3/3 |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|"]
        for _, r in R.sort_values("net", ascending=False).head(6).iterrows():
            L.append(f"| {r.cfg} | {r.n:,.0f} | {r.per_day:.2f} | **{r.net:+.2f}** | "
                     f"{r['win']:.1%} | {r.green:.0%} | "
                     + " | ".join(f"{r[k]:+.2f}" if np.isfinite(r[k]) else "—"
                                  for k in ("e24", "e25", "e26"))
                     + f" | {'**yes**' if r.all3 else ''} |")
        ok = p["pbo"] < 0.10 and wf["mean"] > 0
        survivors[w] = (ok, n3, p["pbo"], dd["dsr"], wf["mean"])
        L += ["", f"**Guard** — PBO **{p['pbo']:.3f}** (bar <0.10), DSR **{dd['dsr']:.3f}** "
              f"(bar >0.95), walk-forward **{wf['mean']:+.3f}** pt/day over {wf['n_windows']} "
              f"windows. Best cell by Sharpe: `{store[w]['names'][best]}`.", "",
              ("**Survives PBO and walk-forward.**" if ok else
               "**Fails the guard** — the in-sample best is not reliably an out-of-sample "
               "winner here."), ""]

    L += ["---", "", "## Verdict", "",
          "| session | cells 3/3 | PBO | DSR | walk-forward | |", "|---|---:|---:|---:|---:|---|"]
    for w, (ok, n3, pbo, dsr, wfm) in survivors.items():
        L.append(f"| {LAB[w]} | {n3} | {pbo:.3f} | {dsr:.3f} | {wfm:+.3f} | "
                 f"{'**candidate**' if ok else 'fails'} |")
    live = [w for w, v in survivors.items() if v[0]]
    L += ["", (f"**Take to the 2023 holdout: {', '.join(LAB[w] for w in live)}.**" if live else
               "**Nothing clears PBO and walk-forward. Do not spend the 2023 holdout.**"), ""]

    text = "\n".join(L)
    print(text)
    (ROOT / "output/fvt_optimise.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
