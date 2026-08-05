#!/usr/bin/env python3
"""NYA-LVL-01 REBUILD — corrected fills. Supersedes stages 1(P&L)/2/3a/3b.

Void notice: research/findings/NYA-LVL-01-VOID-entry-bar-skipped.md

THE FIX. The old build detected the touch on the 15-minute bar and then started the
simulated path at the NEXT bar — a median 12 minutes after the fill, by which time a
10pt stop had already been hit on 72.9% of trades. Here the entry is what it actually
is: a resting limit at a pre-computed level. It fills the minute price reaches it and
**risk is live from that same minute**.

What did NOT change, so the fix is isolated and attributable:
  - the six levels and how they are computed
  - one entry per level per 15-minute bar (so event counts stay comparable)
  - direction from the PREVIOUS 15m close (causal — it closed before this bar opened)
  - the §2.5 through-the-level fill rule, the cost stack, the arm grid

Conservative choice, stated: the stop is checked from the fill minute onward, including
the fill bar itself. Intrabar order is unknowable, and this is the opposite error from
the one being corrected.

    python -m scripts.nya_lvl_rebuild [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_lvl_census import (LEVELS, PM_WINDOW, PD_WINDOW, RTH, TICK,  # noqa: E402
                                    load_bars, m15)
from scripts.nya_lvl_geometry import STOPS, TARGETS, TRAIL_GAP, run_cell  # noqa: E402
from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-level-interaction-stage2.md"
OUT_MD = ROOT / "output/nya_lvl_rebuild.md"
OUT_PARQUET = ROOT / "output/nya_lvl_rebuild.parquet"

FIT_START, FIT_END = "2025-06-02", "2026-07-15"
COSTS = ((1.0, "base"), (2.0, "strict"))
SEED = 20260805
MAX_HOLD = 240
DEF_STOP, DEF_TGT = 20.0, 30.0


def build(bars: pd.DataFrame, rng: np.random.Generator | None = None):
    """Corrected event set: fill at the level, path starts at the fill MINUTE."""
    days = [d for d in sorted(bars["day"].unique()) if FIT_START <= d <= FIT_END]
    prior = None
    recs, paths_ = [], []
    for day in days:
        db = bars[bars["day"] == day]
        pm = db[(db["min"] >= PM_WINDOW[0]) & (db["min"] < PM_WINDOW[1])]
        pdw = db[(db["min"] >= PD_WINDOW[0]) & (db["min"] < PD_WINDOW[1])]
        rth = db[(db["min"] >= RTH[0]) & (db["min"] < RTH[1])].reset_index(drop=True)
        if len(pm) >= 60 and len(rth) >= 200 and prior is not None:
            if rng is None:
                lv = {"PM_HIGH": float(pm["high"].max()), "PM_LOW": float(pm["low"].min()),
                      "PD_HIGH": prior["hi"], "PD_LOW": prior["lo"]}
                lv["PM_50"] = (lv["PM_HIGH"] + lv["PM_LOW"]) / 2
                lv["PD_50"] = (lv["PD_HIGH"] + lv["PD_LOW"]) / 2
            else:
                lo = min(float(pm["low"].min()), prior["lo"])
                hi = max(float(pm["high"].max()), prior["hi"])
                lv = dict(zip(LEVELS, rng.uniform(lo, hi, size=6)))
            b15 = m15(rth)
            if len(b15) >= 4:
                atr15 = float((b15["high"] - b15["low"]).median())
                ro = float(rth.iloc[0]["open"])
                gap = ro - prior["close"]
                mb = rth[["high", "low", "close"]].to_numpy(float)
                tse = rth["ts_event"]
                taps = {k: 0 for k in LEVELS}
                for bi in range(len(b15)):
                    bar, bts = b15.iloc[bi], b15.index[bi]
                    prev_c = float(b15.iloc[bi - 1]["close"]) if bi else ro
                    # 1-minute bars inside this 15m bar
                    sel = np.flatnonzero(((tse > bts - pd.Timedelta(minutes=15))
                                          & (tse <= bts)).to_numpy())
                    if len(sel) == 0:
                        continue
                    for name in LEVELS:
                        level = lv[name]
                        if not (float(bar["low"]) <= level <= float(bar["high"])):
                            continue
                        taps[name] += 1
                        d = -1 if prev_c < level else 1
                        # FILL MINUTE: first 1m bar inside this 15m bar to reach the
                        # level. §2.5 -> it must trade through, not merely touch.
                        fill_i = None
                        for k in sel:
                            if mb[k, 1] <= level <= mb[k, 0]:
                                through = ((mb[k, 0] >= level + TICK) if d < 0
                                           else (mb[k, 1] <= level - TICK))
                                if through:
                                    fill_i = int(k)
                                break
                        if fill_i is None or fill_i >= len(mb) - 2:
                            continue
                        recs.append({
                            "day": day, "era": day[:4],
                            "half": day[:4] + ("H1" if int(day[5:7]) <= 6 else "H2"),
                            "level_type": name, "side": d, "tap": taps[name],
                            "hour": int(tse.iloc[fill_i].hour), "atr15": atr15,
                            "level": level,
                            "dist_atr": (level - ro) * d / max(atr15, 1e-9),
                            "gap_atr": gap / max(atr15, 1e-9),
                            "skipped_min_old": int(len(sel) - (fill_i - sel[0])),
                            "entry_ts": tse.iloc[fill_i],
                        })
                        paths_.append(mb[fill_i:fill_i + MAX_HOLD])
        if len(pdw) >= 100:
            prior = {"hi": float(pdw["high"].max()), "lo": float(pdw["low"].min()),
                     "close": float(pdw.iloc[-1]["close"])}
    return pd.DataFrame(recs), paths_


def arms() -> list[tuple]:
    out = []
    for s in STOPS:
        for t in TARGETS:
            out.append((f"S{s:.0f}/T{t:.0f}", s, t, False))
        out.append((f"S{s:.0f}/TRAIL", s, None, True))
    return out


def score(D: pd.DataFrame, P: list, arm) -> np.ndarray:
    _, s, t, tr = arm
    return np.array([run_cell(int(D["side"].iloc[i]), float(D["level"].iloc[i]), P[i],
                              s, (None if t is None else D["level"].iloc[i]
                                  + D["side"].iloc[i] * t), tr, None)
                     for i in range(len(D))])


def stat(net: np.ndarray, stop: float, cost: float) -> dict:
    n = net - cost
    gw, gl = n[n > 0].sum(), -n[n <= 0].sum()
    return {"n": len(n), "wr": float((n > 0).mean()), "pts": float(n.sum()),
            "pf": float(gw / max(gl, 1e-9)), "r": float((n / stop).mean())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    bars = load_bars()
    D, P = build(bars)
    print(f"{len(D):,} corrected events")

    A = arms()
    res = {a[0]: score(D, P, a) for a in A}
    stops = {a[0]: a[1] for a in A}

    L = ["# NYA-LVL-01 — REBUILD on corrected fills", "",
         "**Supersedes stages 1(P&L)/2/3a/3b.** Void notice:",
         "`research/findings/NYA-LVL-01-VOID-entry-bar-skipped.md`.", "",
         "The fix: the entry is a resting limit at a pre-computed level, so it fills the",
         "minute price reaches it and **risk is live from that minute**. The old build",
         "started the path at the next 15-minute close, a median 12 minutes later.", "",
         f"**{len(D):,} corrected events** over {D['day'].nunique()} sessions "
         f"({len(D)/D['day'].nunique():.1f}/session) — comparable to the 4,759 of the",
         "old build, because the trigger definition did not change, only the fill timing.",
         "", "## 1. The declared default (S20/T30), old vs new", "",
         "| cost | n | WR | net pts | PF | R/trade |", "|---|---:|---:|---:|---:|---:|"]
    for cost, cl in COSTS:
        s = stat(res["S20/T30"], DEF_STOP, cost)
        L.append(f"| {cl} | {s['n']:,} | {s['wr']:.0%} | {s['pts']:+,.0f} | "
                 f"{s['pf']:.2f} | {s['r']:+.3f} |")
    L += ["", "_Old (void) figures were PF 1.07 base / 0.99 strict._", "",
          "## 2. Every arm, base cost — nothing selected", "",
          "| arm | n | WR | net pts | PF | R base | R strict | 2025 R | 2026 R |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    rows, ledger = [], []
    for label, s, t, tr in A:
        net = res[label]
        b, st = stat(net, s, 1.0), stat(net, s, 2.0)
        e = {}
        for era in ("2025", "2026"):
            m = (D["era"] == era).to_numpy()
            e[era] = float(((net[m] - 1.0) / s).mean()) if m.sum() else np.nan
        rows.append({"arm": label, "stop": s, "pf": b["pf"], "r": b["r"],
                     "r_strict": st["r"], "r25": e["2025"], "r26": e["2026"],
                     "n": b["n"], "wr": b["wr"], "pts": b["pts"]})
    R = pd.DataFrame(rows).sort_values("r", ascending=False)
    for _, r in R.iterrows():
        L.append(f"| `{r.arm}` | {r.n:,} | {r.wr:.0%} | {r.pts:+,.0f} | {r.pf:.2f} | "
                 f"{r.r:+.3f} | {r.r_strict:+.3f} | {r.r25:+.3f} | {r.r26:+.3f} |")
        ledger.append({
            "family": "NYA-LVL-01", "era": "fit", "prereg": PREREG,
            "trial": f"REBUILD {r.arm} R per trade",
            "stat_type": "mean", "estimate": round(float(r.r), 4), "n": int(r.n),
            "t_stat": 0.0, "effect": 0.0,
            "verdict": (f"corrected-fill rebuild: WR {r.wr:.0%} PF {r.pf:.2f} "
                        f"R {r.r:+.3f} strict {r.r_strict:+.3f} "
                        f"(25 {r.r25:+.3f} / 26 {r.r26:+.3f})"),
        })
    pos = R[(R.r25 > 0) & (R.r26 > 0) & (R.r_strict > 0)]
    L += ["", f"**{len(pos)} of {len(R)} arms are positive in both eras AND at strict "
          f"cost** (old build: 24 of 51).", ""]

    L += ["## 3. What the old bug was worth", "",
          f"Median minutes the old build skipped after the fill: "
          f"**{D['skipped_min_old'].median():.0f}**. That window is now inside the trade.",
          ""]
    text = "\n".join(L)
    print(text)
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    OUT_MD.write_text(text)
    D.to_parquet(OUT_PARQUET, index=False)
    existing = trial_ledger.load()
    already = set(zip(existing["family"], existing["trial"], existing["era"]))
    fresh = [r for r in ledger if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"recorded {len(fresh)} trials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
