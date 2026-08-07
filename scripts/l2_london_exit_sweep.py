#!/usr/bin/env python3
"""LONDON EXIT LAB — sweep the target RR, and the break-even / partial / runner policies.

ANGUS 2026-08-07: *"Can you run variables test to see what target RR is the best, and maybe
test having it go to BE after 1 RR or sum shit."*

WHAT THIS CAN AND CANNOT DO, said once so no arm gets over-read. Every arm here changes what
happens AFTER entry. None of them changes how many trades London produces (~3.2 setups/day
on a 2-hour window), so none can move the session ceiling: even if every London setup earned
what the best-behaved population earns, the session tops out near 26 pt/day against a 50
pt/day objective. What a sweep CAN do is fix per-trade edge, which is the thing that is
actually broken (−3.64 pt/trade against a +4 bar). That is why it is worth running.

TWO SUB-SWEEPS, sharing one control (`min 2R` = the shipped book):

  TARGET     what to aim at. `nearest` takes the first level in the menu; `min XR` walks the
             menu OUTWARD to the first level clearing X (the shipped `walkout_under_floor`
             semantics, which is what "target RR" actually means in this engine).
  MANAGEMENT what to do on the way. BE-at-1R, fixed-R partials, and the runner policies the
             engine already carries as the exit-lab family (`v8_partial_at_r`,
             `v8_be_at_partial`, `v8_runner`), queued by Angus on 2026-07-30 and never run.

DISPLACEMENT-ONLY, which is what makes this affordable. `simulate()` is called once per
trigger with that trigger alone, so dropping rejection_block candidates is EXACTLY
equivalent to keeping them and filtering after — and B2 is removed anyway (handoff §3.1).
2,657 candidates instead of 8,723 cuts each arm from ~48 min to ~15.

EVERY ARM IS SCORED IN BOTH ERAS AND ON BOTH POPULATIONS. Both eras because the burn list's
signature failure is a 2025 winner that dies in 2026. Both populations — trades price never
retraced to vs trades it did — because that split is where the last finding landed: the
floor change was redistributive, taking 386 pt off the runners and handing 614 back to the
retracers. An arm that only helps the retracers is buying the wrong thing.

    python -m scripts.l2_london_exit_sweep [--procs 4] [--arms nearest,min2R,...]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.build_l2_outcomes_london as L2  # noqa: E402
from scripts.l1_london_dedup import assign  # noqa: E402
from src.validation.prop_score import FRICTION_PTS as FRICTION  # noqa: E402
from src.validation.prop_score import score_book  # noqa: E402

OUT_DIR = ROOT / "output/london_exit_sweep"
REPORT = ROOT / "output/london_exit_sweep.md"
ERAS = [("2025", "2025-01-01", "2025-12-31"), ("2026", "2026-01-01", "2026-12-31")]

# `walkout_under_floor: True` + rr_floor X == "walk the menu outward to the first level
# clearing X". That IS the target-RR question. Floor 0 + walkout off == "take the nearest",
# which is the rr0 book already built.
_V8 = {"mgmt_variant": "V8"}


def _tgt(x, walkout=True):
    return {"rr_floor": x, "rr_floor_partial": min(x, 1.5),
            "walkout_under_floor": walkout, **_V8}


ARMS: list[tuple[str, str, dict]] = [
    # --- TARGET SWEEP (shipped V8 management: 50% partial at first structure, runner trails)
    ("nearest",      "target", _tgt(0.0, walkout=False)),
    ("min 1R",       "target", _tgt(1.0)),
    ("min 1.5R",     "target", _tgt(1.5)),
    ("min 2R",       "target", _tgt(2.0)),          # CONTROL — the shipped book
    ("min 2.5R",     "target", _tgt(2.5)),
    ("min 3R",       "target", _tgt(3.0)),
    # --- MANAGEMENT SWEEP, all on the control's 2R target so the comparison is clean
    ("2R + BE@1R (no partial)", "mgmt",
     {**_tgt(2.0), "mgmt_variant": "V1", "v1_be_at_r": 1.0}),
    ("2R + partial@1R",         "mgmt", {**_tgt(2.0), "v8_partial_at_r": 1.0}),
    ("2R + partial@1R + BE",    "mgmt",
     {**_tgt(2.0), "v8_partial_at_r": 1.0, "v8_be_at_partial": True}),
    ("2R + partial 1st + BE",   "mgmt", {**_tgt(2.0), "v8_be_at_partial": True}),
    ("2R + runner holds",       "mgmt", {**_tgt(2.0), "v8_runner": "hold"}),
    ("2R + runner to EOD",      "mgmt", {**_tgt(2.0), "v8_runner": "eod"}),
]


def build(name: str, overrides: dict, trigs: pd.DataFrame, procs: int) -> pd.DataFrame:
    """One arm, through the real engine, deduped on its OWN eligible population.

    The re-derive is not optional: each arm vetoes a different set, so a setup's first
    eligible trigger differs between arms. Inheriting one arm's grouping into another lets a
    candidate that arm never traded claim a setup and block the one behind it."""
    slug = name.replace(" ", "_").replace("@", "at").replace("+", "").replace("__", "_")
    cache = OUT_DIR / f"{slug}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    t0 = time.time()
    L2._RRFLOOR, L2._CFG_OVERRIDES = None, overrides
    O = L2.run(trigs, procs=procs, quiet=True, entry="EC", overrides=overrides)
    O["arm_none"] = O["status"] == "outcome"
    O["fill_px"] = O["entry"]
    O = O.sort_values(["day", "fill_ts"]).reset_index(drop=True)
    O = assign(O, "vs", eligible=O["vwap_touched"].fillna(False).astype(bool))
    O = O.drop(columns=["fill_px"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    O.to_parquet(cache, index=False)
    ok = O[O.status == "outcome"]
    print(f"  {name:26s} {len(ok):5,} outcomes  {int(O.vs_first.sum()):4,} setups  "
          f"[{time.time()-t0:5.1f}s]", flush=True)
    return O


def row(name: str, O: pd.DataFrame, days: list[str], e3: pd.DataFrame) -> dict | None:
    B = O[(O.status == "outcome") & O.vs_first]
    s = score_book(B, all_days=days)
    if not s:
        return None
    d = {"arm": name, "n": s["n"], "net": s["net_pts"], "t": s["t"], "green": s["green"],
         "med_day": s["med_day"], "worst10": s["worst10d"], "total": s["total_pts"],
         "tpd": s["tpd"]}
    for era, lo, hi in ERAS:
        g = B[(B.day >= lo) & (B.day <= hi)]
        es = score_book(g, all_days=[x for x in days if lo <= x <= hi])
        d[f"net{era}"] = es["net_pts"] if es else float("nan")
        d[f"grn{era}"] = es["green"] if es else float("nan")
    M = B.merge(e3, on="ts", how="left")
    for lab, sel in (("ran", M.e3 == "expired"), ("ret", M.e3 == "filled")):
        g = M[sel]
        d[f"{lab}_n"] = len(g)
        d[f"{lab}_net"] = float((g.pts - FRICTION).mean()) if len(g) else float("nan")
        d[f"{lab}_tot"] = float((g.pts - FRICTION).sum()) if len(g) else float("nan")
    x = B.exit_reason.astype(str)
    d["flat_stop"] = float((x == "stop").mean())
    return d


def table(rows: list[dict], cols: list[tuple[str, str, str]], title: str) -> list[str]:
    L = [f"### {title}", "",
         "| " + " | ".join(h for h, _, _ in cols) + " |",
         "|" + "---|" * len(cols)]
    for r in rows:
        cells = []
        for _, k, f in cols:
            v = r.get(k)
            cells.append("—" if v is None or v != v else format(v, f))
        L.append("| " + " | ".join(cells) + " |")
    return L + [""]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--arms", default="", help="comma-separated subset of arm names")
    a = ap.parse_args()

    T = pd.read_parquet(L2.in_l0(""))
    trigs = T[T.kind == "displacement"].reset_index(drop=True)   # see docstring: exact
    days = sorted(T.day.astype(str).unique())
    e3 = pd.read_parquet(L2.in_l1(""))[["ts", "status"]].rename(columns={"status": "e3"})
    want = [x.strip() for x in a.arms.split(",") if x.strip()]
    arms = [x for x in ARMS if not want or x[0] in want]
    print(f"exit sweep — {len(arms)} arms x {len(trigs):,} displacement candidates "
          f"over {len(days)} sessions", flush=True)

    rows = []
    for name, kind, ov in arms:
        O = build(name, ov, trigs, a.procs)
        r = row(name, O, days, e3)
        if r:
            r["kind"] = kind
            rows.append(r)

    base = next((r for r in rows if r["arm"] == "min 2R"), None)
    for r in rows:
        r["d_vs_2R"] = r["net"] - base["net"] if base else float("nan")
        r["both_eras"] = r["net2025"] > 0 and r["net2026"] > 0

    MAIN = [("arm", "arm", "s"), ("N", "n", ",d"), ("/day", "tpd", ".2f"),
            ("net pt", "net", "+.2f"), ("vs 2R", "d_vs_2R", "+.2f"), ("T", "t", "+.2f"),
            ("green", "green", ".0%"), ("med day", "med_day", "+.1f"),
            ("worst10d", "worst10", "+.0f"), ("flat stop", "flat_stop", ".0%"),
            ("2025 net", "net2025", "+.2f"), ("2026 net", "net2026", "+.2f")]
    POP = [("arm", "arm", "s"),
           ("RAN n", "ran_n", ",d"), ("RAN net", "ran_net", "+.2f"),
           ("RAN total", "ran_tot", "+.0f"),
           ("RETRACED n", "ret_n", ",d"), ("RETRACED net", "ret_net", "+.2f"),
           ("RETRACED total", "ret_tot", "+.0f")]

    L = ["# LONDON EXIT LAB — target RR, break-even and runner policies", "",
         f"{len(rows)} arms, displacement-only, deduped per arm, engine-simulated over "
         f"**{len(days)} sessions**. Friction 2.0 pt charged. Control = **min 2R** "
         "(the shipped book).", "",
         "> Every arm changes what happens AFTER entry, so none changes how many trades "
         "London produces. The session ceiling (~26 pt/day even if every setup behaved like "
         "the best population, against a 50 pt/day objective) is untouched by anything "
         "here. What these can fix is per-trade edge.", "",
         "**Bar: net ≥ +4 pt, T ≥ 2, N ≥ 200, green ≥ 55%, positive in BOTH eras.**", ""]
    L += table([r for r in rows if r["kind"] == "target"], MAIN,
               "Target RR — what to aim at")
    L += table([r for r in rows if r["kind"] == "mgmt"], MAIN,
               "Management — what to do on the way (all on the 2R target)")
    L += ["### Split by population", "",
          "`RAN` = price never retraced to the trigger level (the population that pays); "
          "`RETRACED` = it did. An arm that only helps RETRACED is buying the wrong thing.",
          ""]
    L += table(rows, POP, "Per-trade net and total by population")

    win = [r for r in rows if r["both_eras"]]
    L += ["### Verdict", "",
          (f"**{len(win)} of {len(rows)} arms are net-positive in both eras**: "
           + ", ".join(f"`{r['arm']}` ({r['net']:+.2f})" for r in win)) if win else
          "**No arm is net-positive in both eras.** Every one fails the burn-list bar "
          "(§8.1) before the prop bar is even reached.", ""]
    best = max(rows, key=lambda r: r["net"])
    L += [f"Best full-span net: **`{best['arm']}` at {best['net']:+.2f} pt/trade** "
          f"({best['net2025']:+.2f} in 2025, {best['net2026']:+.2f} in 2026) — "
          f"{'clears' if best['net'] >= 4 else 'still short of'} the +4 bar.", ""]

    text = "\n".join(L)
    print("\n" + text)
    REPORT.write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
