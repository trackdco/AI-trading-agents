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

from src.validation.prop_score import FRICTION_PTS as FRICTION, score_book  # noqa: E402

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
    ("RR at order · min", lambda s, B: f"{_rr(B).min():.2f}"),
    ("RR at order · median", lambda s, B: f"**{_rr(B).median():.2f}**"),
    ("ordered under 2R", lambda s, B: f"{(_rr(B) < 2).mean():.1%}"),
    ("value of a target hit", lambda s, B: _tgt_value(B)),
]


def _share(B: pd.DataFrame, col: str, vals: set) -> float:
    return float(B[col].astype(str).isin(vals).mean()) if len(B) else float("nan")


def _sgn(B: pd.DataFrame) -> pd.Series:
    return (B.direction.astype(str).str.lower() == "long").map({True: 1.0, False: -1.0})


def _rr(B: pd.DataFrame) -> pd.Series:
    """Reward:risk as the ENGINE gated it: working target vs the LIMIT price, over risk.

    Not vs `entry`. `entry` is the fill, and an EC displacement is a market order that slips
    a median 0.75pt (p90 7.25) past its reference — measuring against it reports negative RR
    on trades the engine ordered at a legitimate positive one. `risk` is stored as
    |limit - stop_initial|, so the limit is recoverable as stop + sgn*risk.

    This is the number the floor gated, so it is the direct read on what cutting it did.
    Sanity: the 2R arm floors at exactly 2.00 and the rr0 arm at 0.00, both exact."""
    s = _sgn(B)
    return (B.working_target - (B.stop + s * B.risk)) * s / B.risk


def _tgt_value(B: pd.DataFrame) -> str:
    """Mean NET points a pure-target exit books. A target-hit RATE means nothing without
    it: the rate can be raised to anything at all by pulling the target nearer."""
    t = B[B.exit_reason.astype(str) == "target"]
    return f"{(t.pts - FRICTION).mean():+.2f} pt" if len(t) else "—"


def buckets(cols: list[tuple[str, pd.DataFrame]]) -> list[str]:
    """The book cut by the distance of the target the engine ordered. This is where the
    floor question is actually settled: if nearer targets paid, the near buckets would be
    where the money is."""
    edges = [-0.01, 0.5, 1, 1.5, 2, 3, 1e9]
    names = ["<0.5R", "0.5-1R", "1-1.5R", "1.5-2R", "2-3R", ">3R"]
    L = ["### Net points/trade by the RR the engine ORDERED", "",
         "Share of book in brackets. Friction charged.", "",
         "| ordered RR | " + " | ".join(nm for nm, _ in cols) + " |",
         "|---|" + "---:|" * len(cols)]
    for lo, hi, nm in zip(edges[:-1], edges[1:], names):
        cells = []
        for _, B in cols:
            r = _rr(B)
            g = B[(r > lo) & (r <= hi)]
            cells.append(f"{(g.pts - FRICTION).mean():+.2f} ({len(g)/len(B):.0%})"
                         if len(g) else "—")
        L.append(f"| {nm} | " + " | ".join(cells) + " |")
    return L + [""]


def paired(a_col: tuple[str, pd.DataFrame], b_col: tuple[str, pd.DataFrame]) -> list[str]:
    """The population changes between arms, so the headline difference mixes a policy effect
    with a composition effect. Restricting to setups BOTH arms traded isolates the policy,
    and each trade is its own control.

    Across a CENSUS arm (`_pp`) the overlap is partial by construction — adding levels
    changes which candles cluster at all, so the arm can both gain and lose triggers. The
    paired set is then "the trades the change left alone", and the trades outside it are
    the change's actual product; both counts are reported."""
    (na, A), (nb, B) = a_col, b_col
    common = sorted(set(A.ts) & set(B.ts))
    a = A[A.ts.isin(common)].sort_values("ts")
    b = B[B.ts.isin(common)].sort_values("ts")
    d = b.pts.to_numpy(float) - a.pts.to_numpy(float)
    t = d.mean() / (d.std(ddof=1) / (len(d) ** 0.5)) if len(d) > 1 and d.std(ddof=1) else 0.0
    return [f"### Paired: {nb} vs {na} — {len(common):,} setups in common", "",
            f"Of {len(A):,} ({na}) and {len(B):,} ({nb}). "
            f"{len(set(B.ts) - set(A.ts)):,} setups exist only in {nb}; "
            f"{len(set(A.ts) - set(B.ts)):,} only in {na}.", "",
            "| | value |", "|---|---:|",
            f"| per-trade delta (rr0 − 2R) | **{d.mean():+.2f} pt** |",
            f"| paired T | **{t:+.2f}** |",
            f"| outcome identical in both arms | **{(d == 0).mean():.1%}** |",
            f"| rr0 better / worse | {(d > 0).mean():.1%} / {(d < 0).mean():.1%} |", ""]


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
    # NOT a walkout metric. `working = level - sgn*front_run` unconditionally, so
    # working != level on 100% of outcomes in BOTH arms — it is the 2.5pt front-run, not
    # evidence the menu was walked. Verified: |working - level| sits within half a tick of
    # front_run on every outcome in both books. The walkout's real signature is the RR
    # distribution below, where the arms genuinely separate.
    L.append("| working != target_level (front-run, both arms) | " + " | ".join(
        f"{(T.working_target != T.target_level).mean():.0%}" for _, T in ok) + " |")
    return L + [""]


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", nargs="*", default=[],
                    help="extra census arms to score alongside the baselines, e.g. `_pp`")
    a = ap.parse_args()
    books = list(BOOKS) + [
        (f"prior-profile{arm} (rr0)",
         ROOT / f"output/l2_outcomes_london_fit{arm}_EC_rr0.parquet") for arm in a.arms]

    raw = [(nm, book(p)) for nm, p in books]
    missing = [nm for nm, T in raw if T is None]
    if missing:
        print(f"MISSING BOOK: {missing} — run build_l2_outcomes_london --rr-floor 0 first")
        return 1
    # each arm has its OWN census, so the session denominator comes from that arm's L0
    sessions = sorted(pd.read_parquet(L0).day.astype(str).unique())
    for arm in a.arms:
        p = ROOT / f"output/l0_triggers_london_fit_std{arm}.parquet"
        if p.exists():
            sessions = sorted(set(sessions) | set(pd.read_parquet(p).day.astype(str)))
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
    L += buckets(dedup)
    # 2R -> rr0 is the target-policy change; rr0 -> each census arm is a menu change
    L += paired(dedup[0], dedup[1])
    for extra in dedup[2:]:
        L += paired(dedup[1], extra)

    text = "\n".join(L)
    print(text)
    (ROOT / "output/london_rrfloor_compare.md").write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
