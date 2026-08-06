#!/usr/bin/env python3
"""LONDON TASK #1 — score the next-structural-level book against the 2R-floor baseline.

ANGUS 2026-08-05: *"fuck why is the 2 r floor instated. that needs to get cut, that rule
should be implemented if feasible in the optimisation process"* ... *"btw it should be the
next structural level not 2r floor minimum etc"*.

`walkout_under_floor` does not merely enforce a minimum. It walks the §6 target menu OUTWARD
past the nearest structural level looking for one that clears 2R, and vetoes the trade
outright when nothing clears. So the shipped book was never trading "the next structural
level with a 2R check" — it was trading a target chosen for its R, whatever level that was.
`--rr-floor 0` with walkout off takes the first level in the menu, which is the ruling.

Both books are scored on `src.validation.prop_score` — the ONLY scoreboard (handoff §0):
green-day %, max-day share, net points/trade after 2pt friction, T, N, worst rolling 10d.
Profit factor is deliberately absent.

GREEN-DAY DENOMINATOR. `score_book` counts only days that carry a trade unless it is handed
`all_days`. The §5 baseline (32%) was computed the first way. Two books that trade different
numbers of sessions are not comparable that way, so BOTH are reported:

    as-published    days = days with a trade      reproduces §5 exactly, comparable to it
    all-264         days = every fit session      a no-trade day is a FLAT day, not absent

The second is the honest prop number and it is the one a payout is computed on.

    python -m scripts.l2_london_rrfloor_compare
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.prop_score import score_book  # noqa: E402

L0 = ROOT / "output/l0_triggers_london_fit_std.parquet"
BOOKS = [
    ("2R floor (shipped)", ROOT / "output/l2_outcomes_london_fit_EC.parquet"),
    ("next structural (rr0)", ROOT / "output/l2_outcomes_london_fit_EC_rr0.parquet"),
]
# fit = 2025-06-02 .. 2026-07-15. Discover on 2025, validate on 2026 (handoff §4).
ERAS = [("2025", "2025-01-01", "2025-12-31"), ("2026", "2026-01-01", "2026-12-31")]

METRICS = [
    ("N (setups)", lambda s, B: f"{s['n']:,}"),
    ("trades/day", lambda s, B: f"{s['tpd']:.2f}"),
    ("net pt/trade", lambda s, B: f"**{s['net_pts']:+.2f}**"),
    ("T", lambda s, B: f"{s['t']:.2f}"),
    ("green days", lambda s, B: f"**{s['green']:.0%}**"),
    ("median day", lambda s, B: f"{s['med_day']:+.1f} pt"),
    ("worst rolling 10d", lambda s, B: f"{s['worst10d']:+.0f} pt"),
    ("max-day share", lambda s, B: "n/a (net loss)" if s["maxday"] != s["maxday"]
                                   else f"{s['maxday']:.0%}"),
    ("total pts", lambda s, B: f"{s['total_pts']:+,.0f}"),
    ("target-hit (pure)", lambda s, B: f"**{_share(B, 'exit_reason', {'target'}):.1%}**"),
    ("target-hit (any)", lambda s, B: f"{_share(B, 'exit_reason', {'target', 'partial+target'}):.1%}"),
    ("mean R", lambda s, B: f"{B.R.mean():+.3f}"),
    ("median R", lambda s, B: f"{B.R.median():+.3f}"),
    ("median risk", lambda s, B: f"{B.risk.median():.1f} pt"),
    ("median RR at order", lambda s, B: f"{_rr(B).median():.2f}"),
]


def _share(B: pd.DataFrame, col: str, vals: set) -> float:
    return float(B[col].astype(str).isin(vals).mean()) if len(B) else float("nan")


def _rr(B: pd.DataFrame) -> pd.Series:
    """Reward:risk the engine actually ORDERED — the working target vs the entry, over the
    initial risk. This is the number the 2R floor was gating, so it is the direct read on
    what cutting the floor did to target distance."""
    sgn = (B.direction.astype(str).str.lower() == "long").map({True: 1.0, False: -1.0})
    return (B.working_target - B.entry) * sgn / B.risk


def book(path: Path) -> pd.DataFrame | None:
    """The deduped displacement book. B2 is removed (handoff §3.1) so `kind ==
    displacement` is the whole strategy; `vs_first` is the setup-first dedup arm, chosen on
    causality grounds — the first trigger is the one you could actually have taken."""
    if not path.exists():
        return None
    T = pd.read_parquet(path)
    # GUARD. `build_l2_outcomes_london` joins the setup flags straight off L1, which grouped
    # the E3 LIMIT walk. Every arm fills at a different moment and vetoes a different set, so
    # that grouping is not this arm's object. Its signature is `vs_first` sitting on rows the
    # arm never traded; the re-derived flags only ever mark an outcome. Refuse rather than
    # silently score a book deduped against another arm's population.
    stale = int(((T.status != "outcome") & T.vs_first).sum())
    if stale:
        raise SystemExit(
            f"{path.name}: {stale:,} non-outcome rows carry vs_first — these are L1's E3 "
            f"flags, not this arm's.\n  fix: python -m scripts.l2_london_dedup_arm "
            f"--entry EC" + ("" if "_rr" not in path.stem else " --rr-floor 0"))
    T = T[T.kind == "displacement"]
    if "size" in T.columns:                    # handoff §11 — canon books carry size-0 rows
        T = T[T["size"] > 0]
    return T


def sub(B: pd.DataFrame, lo: str, hi: str) -> pd.DataFrame:
    return B[(B.day >= lo) & (B.day <= hi)]


def table(label: str, cols: list[tuple[str, pd.DataFrame, list[str]]]) -> list[str]:
    """One metric-per-row table so the shipped and rr0 columns sit side by side."""
    scored = [(nm, score_book(B), B) for nm, B, _ in cols]
    scored = [(nm, s, B) for nm, s, B in scored if s]
    if not scored:
        return [f"### {label}", "", "_no data_", ""]
    L = [f"### {label}", "",
         "| metric | " + " | ".join(nm for nm, _, _ in scored) + " |",
         "|---|" + "---:|" * len(scored)]
    for mname, fn in METRICS:
        L.append(f"| {mname} | " + " | ".join(fn(s, B) for _, s, B in scored) + " |")
    # green-day % on the common all-sessions denominator
    row = []
    for (nm, _, B), (_, _, days) in zip(scored, cols):
        s2 = score_book(B, all_days=days)
        row.append(f"**{s2['green']:.0%}** ({s2['days']} sessions)" if s2 else "—")
    L += ["| green days · all-sessions | " + " | ".join(row) + " |", ""]
    return L


def exits(cols: list[tuple[str, pd.DataFrame]]) -> list[str]:
    reasons = ["stop", "partial+stop", "partial+target", "target"]
    seen = sorted({r for _, B in cols for r in B.exit_reason.astype(str).unique()})
    reasons += [r for r in seen if r not in reasons]
    L = ["### Exit mix", "",
         "| exit reason | " + " | ".join(nm for nm, _ in cols) + " |",
         "|---|" + "---:|" * len(cols)]
    for r in reasons:
        vals = [_share(B, "exit_reason", {r}) for _, B in cols]
        if max(vals) > 0:
            L.append(f"| {r} | " + " | ".join(f"{v:.1%}" for v in vals) + " |")
    return L + [""]


def funnel(rows: list[tuple[str, pd.DataFrame]]) -> list[str]:
    """Census completeness — a candidate the engine refuses to order is recorded WITH its
    veto, so the funnel must reconcile. A zero is a bug until proven otherwise (handoff §0)."""
    L = ["### Funnel and veto census — displacement candidates", "",
         "| stage / status | " + " | ".join(nm for nm, _ in rows) + " |",
         "|---|" + "---:|" * len(rows)]
    L.append("| candidates | " + " | ".join(f"{len(T):,}" for _, T in rows) + " |")
    for st in sorted({s for _, T in rows for s in T.status.unique()}):
        L.append(f"| · {st} | " + " | ".join(
            f"{int((T.status == st).sum()):,}" for _, T in rows) + " |")
    ok = [(nm, T[T.status == "outcome"]) for nm, T in rows]
    L.append("| **outcomes** | " + " | ".join(f"**{len(T):,}**" for _, T in ok) + " |")
    L.append("| **deduped setups (vs_first)** | " + " | ".join(
        f"**{int(T.vs_first.sum()):,}**" for _, T in ok) + " |")
    L.append("| walked target (working != level) | " + " | ".join(
        f"{(T.working_target != T.target_level).mean():.0%}" for _, T in ok) + " |")
    return L + [""]


def main() -> int:
    raw = [(nm, book(p)) for nm, p in BOOKS]
    missing = [nm for nm, T in raw if T is None]
    if missing:
        print(f"MISSING BOOK: {missing} — run build_l2_outcomes_london --rr-floor 0 first")
        return 1
    sessions = sorted(pd.read_parquet(L0).day.astype(str).unique())
    dedup = [(nm, T[(T.status == "outcome") & T.vs_first]) for nm, T in raw]

    L = ["# LONDON TASK #1 — the 2R floor vs the next structural level", "",
         "London, EC displacement entries, deduped `vs_first`, engine-simulated. Scored on "
         "`src/validation/prop_score.py` — the prop objective, not profit factor.", "",
         f"Fit span **{sessions[0]} → {sessions[-1]}**, **{len(sessions)} sessions**. "
         "Friction 2.0 pt round-trip charged inside the scoreboard.", ""]
    L += funnel(raw)
    L += table("Full fit span", [(nm, B, sessions) for nm, B in dedup])
    for era, lo, hi in ERAS:
        d = [s for s in sessions if lo <= s <= hi]
        L += table(f"Era {era} ({d[0]} → {d[-1]}, {len(d)} sessions)",
                   [(nm, sub(B, lo, hi), d) for nm, B in dedup])
    L += exits(dedup)

    text = "\n".join(L)
    print(text)
    (ROOT / "output/london_rrfloor_compare.md").write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
