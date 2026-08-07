#!/usr/bin/env python3
"""The out-of-fit verdict, assessed the way Angus asked: each session on its own criteria.

*"i would want it to trade based off of our canon ny and canon london, adhering to the
criteria per session. london, pre market, ny etc."*

Three books, three sets of checks, three separate verdicts — never a blended total, because a
blended total hides which session broke. For each session this prints the fit span beside the
holdout span, and then the per-check pass rate in both. That second table is the diagnostic
that matters: if a check fires at 47% in fit and 14% out of fit, either the regime genuinely
changed under it or the feature was assembled wrong, and either way the P&L below it is
uninterpretable until that is settled.

  LONDON      W / FAR / ROOM / ASIA        (Layer 0 stop >= 9.5, no upper cap)
  PRE-MARKET  W / F / Tp / G / C           (Layer 0 stop 7-60)
  GOLD        D / Tc / X / AGE / PAQ       (Layer 0 stop 7-60, + Layer 2q quality tier)

Nothing here re-derives a threshold. It reads the books the scorers already wrote.

    python -m scripts.holdout_verdict
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.baseline_dollar_risk import size_book  # noqa: E402

NY_CHECKS = {"pre": ["W", "F", "Tp", "G", "C"], "gold": ["D", "Tc", "X", "AGE", "PAQ"]}
LON_CHECKS = ["W", "FAR", "ROOM", "ASIA"]

BOOKS = {
    "fit": {"ny": "output/ny_canon_fit.parquet", "lon": "output/london_canon_book.parquet"},
    "holdout": {"ny": "output/ny_canon_holdout.parquet",
                "lon": "output/london_canon_book_holdout.parquet"},
}


def funded(C: pd.DataFrame, session: str) -> pd.DataFrame:
    """Restate a canon book in FUNDED dollars — the sizing the account actually trades.

    ANGUS: *"make sure its going off of the conviction based sizing things too like the 0.25
    trades shouldnt be sized off the same static sizing as the 2.25."* `size_book` does exactly
    that: risk_$ = min($400, conviction x $200), micros = round(risk_$ / (stop_pts x $2)),
    so a 0.25-conviction trade risks $50 and a 2.25 risks the $400 cap. Every arm and every
    span uses the identical rule, which is what keeps the P&L comparable.
    """
    C = C.copy()
    if "yr" not in C.columns:
        C["yr"] = pd.to_datetime(C.day.astype(str).str[:10]).dt.year
    b = size_book(C, session)
    b["day"] = b.day.astype(str).str[:10]
    return b


def stats(C: pd.DataFrame) -> dict:
    """Session summary from a canon book. `size` 0 means the ladder declined the trade."""
    t = C[C["size"] > 0]
    if not len(t):
        return {"n": 0, "cand": len(C), "pl": 0.0}
    cum = t.groupby("day").pl.sum().cumsum()
    gw, gl = t[t.pl > 0].pl.sum(), -t[t.pl < 0].pl.sum()
    mo = C.groupby(C.day.astype(str).str[:7]).pl.sum()
    return {
        "n": len(t), "cand": len(C), "days": t.day.nunique(), "pl": C.pl.sum(),
        "wr": (t.dollars > 0).mean() * 100,
        "avgR": t.R.mean() if "R" in t else float("nan"),
        "pf": gw / gl if gl else float("inf"),
        "dd": (cum.cummax() - cum).max() if len(cum) else 0.0,
        "green": f"{int((mo > 0).sum())}/{len(mo)}",
        "permo": C.pl.sum() / max(len(mo), 1),
    }


def line(tag: str, s: dict) -> str:
    if not s["n"]:
        return f"  {tag:<12} — no trades taken ({s['cand']} candidates)"
    return (f"  {tag:<12} ${s['pl']:>+10,.0f}  {s['n']:>4} trades / {s['cand']:>4} cand  "
            f"WR {s['wr']:>3.0f}%  avgR {s['avgR']:>+5.2f}  PF {s['pf']:>4.2f}  "
            f"maxDD ${s['dd']:>7,.0f}  green {s['green']:>6}  ${s['permo']:>+8,.0f}/mo")


def check_table(frames: dict, checks: list[str], title: str) -> None:
    """Pass rate of each Layer-1 check, fit vs holdout, over the SAME candidate universe.

    Computed on candidates, not on taken trades — the checks are what decides `size`, so
    conditioning on `size > 0` would make every rate look healthy by construction.
    """
    have = {k: v for k, v in frames.items() if v is not None and len(v)}
    cols = [c for c in checks if all(c in v.columns for v in have.values())]
    if len(have) < 2 or not cols:
        return
    print(f"\n    {title} check pass-rate (share of candidates where the check fires)")
    print(f"      {'check':<6}" + "".join(f"{k:>10}" for k in have) + f"{'delta':>9}")
    for c in cols:
        rates = {k: v[c].astype(float).mean() * 100 for k, v in have.items()}
        d = rates.get("holdout", float("nan")) - rates.get("fit", float("nan"))
        flag = "  <-- broken?" if abs(d) >= 20 else ""
        print(f"      {c:<6}" + "".join(f"{r:>9.0f}%" for r in rates.values())
              + f"{d:>+8.0f}pp{flag}")


def main() -> None:
    books: dict[str, dict[str, pd.DataFrame | None]] = {}
    for span, paths in BOOKS.items():
        books[span] = {}
        for k, p in paths.items():
            f = ROOT / p
            books[span][k] = pd.read_parquet(f) if f.exists() else None
            if books[span][k] is None:
                print(f"missing {p} — {span}/{k} will be skipped")

    print("\n" + "=" * 108)
    print("OUT-OF-FIT VERDICT — each session on its own criteria, 1-lot dollars x canon size")
    print("=" * 108)

    for name, win in (("PRE-MARKET (08:00-09:30)", "pre"), ("GOLD (09:40-10:15)", "gold")):
        print(f"\n{name}")
        frames = {}
        for span in ("fit", "holdout"):
            C = books[span]["ny"]
            if C is None:
                continue
            d = C[C.win_ == win]
            frames[span] = d
            print(line(span, stats(d)))
        check_table(frames, NY_CHECKS[win], win.upper())

    print("\nLONDON (08:00-10:00 Europe/London)")
    frames = {}
    for span in ("fit", "holdout"):
        C = books[span]["lon"]
        if C is None:
            continue
        frames[span] = C
        print(line(span, stats(C)))
    check_table(frames, LON_CHECKS, "LONDON")

    print("\n" + "-" * 108)
    print("COMBINED (NY + London, the way the two canons are actually run together)")
    for span in ("fit", "holdout"):
        parts = [b for b in (books[span]["ny"], books[span]["lon"]) if b is not None]
        if not parts:
            continue
        cols = ["day", "size", "pl", "dollars"]
        C = pd.concat([p[[c for c in cols if c in p.columns]] for p in parts], ignore_index=True)
        C["R"] = float("nan")
        print(line(span, stats(C)))

    print("\n" + "=" * 108)
    print("READ THIS BEFORE THE NUMBERS: the fit column is NOT the armed +$55,989.81. That figure")
    print("came from output/trade_matrix.parquet, which no single engine config reproduces. The")
    print("fit column here is the same forward pipeline as the holdout column, so the two are")
    print("comparable to each other — which is the only comparison the holdout question needs.")


if __name__ == "__main__":
    main()
