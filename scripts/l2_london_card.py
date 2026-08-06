#!/usr/bin/env python3
"""LDN-CAN-01 L2 — the outcomes data card (§5.10 transparency rule).

Authorised by docs/PREREG-london-canon-rebuild.md. Reports the first honest P&L on the
canon geometry in London: every candidate walked through the REAL engine, one
simulate() per trigger, V8 management, hard 2R floor, NO risk gate and NO caps.

COSTS ARE ALREADY IN. The engine charges $2.50/contract/side commission and 1 tick of
adverse slippage per side (4 ticks within 15 min of a release), so `dollars_1lot` is net.
This is the same cost model the NY canon's numbers use — these figures are directly
comparable to it, and NOT to the crude 1pt/2pt bar-sim stack used on the candidate lane.

L2 RANKS NOTHING AND PROMOTES NOTHING (§5.9.2). It produces numbers. The risk-band table
exists so L4 can decide the 9.5pt London floor on evidence rather than importing it.

    python -m scripts.l2_london_card
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-canon-rebuild.md"
IN = ROOT / "output/l2_outcomes_london_fit.parquet"
OUT_MD = ROOT / "output/l2_london_card.md"
DEFAULT = "vs_first"          # the ruled population (ANGUS: VWAP touched/closed through)


def stat(T: pd.DataFrame) -> dict | None:
    """1-lot economics. `dollars_1lot` is already net of commission and slippage."""
    if T.empty:
        return None
    d = T["dollars_1lot"].to_numpy(float)
    r = T["R"].to_numpy(float)
    w, l = d[d > 0], d[d <= 0]
    gw, gl = w.sum(), -l.sum()
    T = T.sort_values("fill_ts")
    eq = np.concatenate([[0.0], np.cumsum(T["dollars_1lot"].to_numpy(float))])
    dd = float(np.max(np.maximum.accumulate(eq) - eq))
    return {"n": len(d), "wr": float((d > 0).mean()), "usd": float(d.sum()),
            "pf": float(gw / max(gl, 1e-9)), "r": float(np.nanmean(r)),
            "maxdd": dd,
            "payoff": float(w.mean() / abs(l.mean())) if len(w) and len(l) else np.nan}


def row(label: str, s: dict | None, extra: str = "") -> str:
    if not s:
        return f"| {label} | 0 | — | — | — | — | — |{extra}"
    return (f"| {label} | {s['n']:,} | {s['wr']:.0%} | {s['pf']:.2f} | "
            f"${s['usd']:+,.0f} | {s['r']:+.3f} | ${s['maxdd']:,.0f} |{extra}")


HDR = ("| cut | n | WR | **PF** | $ 1-lot | R/trade | maxDD |\n"
       "|---|---:|---:|---:|---:|---:|---:|")


def main() -> int:
    O = pd.read_parquet(IN)
    nd = O["day"].nunique()
    ok = O[O.status == "outcome"].copy()
    ok["era"] = ok["day"].str[:4]
    ok["half"] = ok["day"].str[:4] + ok["day"].str[5:7].astype(int).map(
        lambda m: "H1" if m <= 6 else "H2")
    D = ok[ok[DEFAULT]].copy()

    L = ["# LDN-CAN-01 — L2 outcomes data card", "",
         f"Authorised by `{PREREG}`. Every candidate through the **real engine**, one",
         "`simulate()` call each, V8 management, hard 2R floor at order time, **no risk",
         "gate and no trade caps** — those are L4 policy.", "",
         "**Costs are already in.** The engine charges $2.50/contract/side and 1 tick of",
         "adverse slippage per side (4 ticks within 15 min of a release). `$ 1-lot` is net.",
         "These are directly comparable to the NY canon's numbers, which use the same",
         "engine and cost model.", "",
         "**L2 ranks nothing and promotes nothing** (§5.9.2). It produces numbers.", "",
         "**Sealed and untouched:** 2023/24, the six sealed months, `depth_london_2023_24`.",
         "", "## 1. Funnel", "",
         "| rung | n | /session |", "|---|---:|---:|",
         f"| L0 triggers | {len(O):,} | {len(O)/nd:.1f} |",
         f"| L1 filled | {int(O.arm_none.sum()):,} | {O.arm_none.sum()/nd:.1f} |",
         f"| L1b setups, VWAP-ruled (`{DEFAULT}`) | {int(O[DEFAULT].sum()):,} | "
         f"{O[DEFAULT].sum()/nd:.2f} |",
         f"| **L2 with an engine outcome** | **{len(D):,}** | **{len(D)/nd:.2f}** |", "",
         "Engine statuses across the whole census:", "",
         "| status | n |", "|---|---:|"]
    for k, v in O.status.value_counts().items():
        L.append(f"| `{k}` | {v:,} |")

    L += ["", "## 2. The headline — ruled population, 1 lot, no selection", "", HDR,
          row("**ALL**", stat(D))]
    for e in ("2025", "2026"):
        L.append(row(f"{e}", stat(D[D.era == e])))
    for h in ("2025H2", "2026H1"):
        L.append(row(f"  {h}", stat(D[D.half == h])))
    L += ["", "_Era and half rows are mandatory (§5.11.5) — aggregates mask holes._", ""]

    L += ["## 3. By pattern", "", HDR]
    for p in ("B2", "B", "A"):
        L.append(row(f"`{p}`", stat(D[D.pattern == p])))
    L += ["", "By pattern and era (does any pattern hold up in both?):", "",
          "| pattern | 2025 PF | 2026 PF | 2025 n | 2026 n | both > 1.0 |",
          "|---|---:|---:|---:|---:|---|"]
    for p in ("B2", "B", "A"):
        a, b = stat(D[(D.pattern == p) & (D.era == "2025")]), stat(D[(D.pattern == p) & (D.era == "2026")])
        both = a and b and a["pf"] > 1.0 and b["pf"] > 1.0
        L.append(f"| `{p}` | {a['pf']:.2f} | {b['pf']:.2f} | {a['n']:,} | {b['n']:,} | "
                 f"{'**YES**' if both else 'no'} |" if a and b else f"| `{p}` | — | — | — | — | — |")

    L += ["", "## 4. By entry timeframe", "", HDR]
    for t in ("1min", "2min", "3min", "5min"):
        L.append(row(f"`{t}`", stat(D[D.tf == t])))

    L += ["", "## 5. Risk bands — the 9.5pt London floor, measured not imported (§5.11.3)", "",
          "The handoff is explicit that `LON_RISK_MIN = 9.5` is a **hypothesis to re-test on",
          "the honest population**, not a rule to carry in. This is that test.", "", HDR]
    bands = [(0, 3), (3, 5), (5, 7), (7, 9.5), (9.5, 15), (15, 25), (25, 1e9)]
    for lo, hi in bands:
        m = (D.risk >= lo) & (D.risk < hi)
        lbl = f"{lo:g}–{hi:g} pt" if hi < 1e9 else f"{lo:g}+ pt"
        L.append(row(lbl, stat(D[m])))
    a, b = stat(D[D.risk < 9.5]), stat(D[D.risk >= 9.5])
    L += ["", HDR.replace("cut", "the floor itself"),
          row("**below 9.5 pt**", a), row("**9.5 pt and above**", b), ""]

    L += ["## 6. How trades ended", "", "| exit | n | share |", "|---|---:|---:|"]
    for k, v in D.exit_reason.value_counts().items():
        L.append(f"| `{k}` | {v:,} | {v/len(D):.0%} |")

    L += ["", "## 7. What the declared arms are worth — reported, NOT selected on", "", HDR]
    for lbl, col in ((f"`{DEFAULT}` (ruled default)", "vs_first"),
                     ("`vs_htf` (challenger — causality unproven)", "vs_htf"),
                     ("`setup_first` (superseded, pre-VWAP-ruling)", "setup_first"),
                     ("`setup_htf` (superseded)", "setup_htf")):
        L.append(row(lbl, stat(ok[ok[col]])))
    L += ["", "**Nothing here promotes anything** (§6.0.1). `vs_htf` needs its causality",
          "proven before it can trade at all, and no arm displaces the default on in-sample",
          "rank. The superseded rows are shown so the VWAP ruling's effect is auditable.", ""]

    text = "\n".join(L)
    print(text)
    OUT_MD.write_text(text)

    s = stat(D)
    rows = [{"family": "LDN-CAN-01", "era": "fit", "prereg": PREREG,
             "trial": f"L2 outcomes, {DEFAULT}, 1-lot, no selection",
             "stat_type": "mean", "estimate": round(s["r"], 4), "n": s["n"],
             "t_stat": 0.0, "effect": 0.0,
             "verdict": (f"L2 honest baseline: n={s['n']} WR {s['wr']:.0%} PF {s['pf']:.2f} "
                         f"${s['usd']:+,.0f} R {s['r']:+.3f} maxDD ${s['maxdd']:,.0f}; "
                         f"no risk gate, no caps, costs in")}]
    ex = trial_ledger.load()
    already = set(zip(ex["family"], ex["trial"], ex["era"]))
    fresh = [r for r in rows if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"\nrecorded {len(fresh)} trials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
