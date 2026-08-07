#!/usr/bin/env python3
"""LONDON — the two cheap splits on the rr0 book: market context, and entry selection.

Handoff §12 step 2, plus the §8.7 tension. Neither needs a rebuild: `daily_context` is
already built and causal, and L1 already records which candidates the E3 LIMIT walk caught.

WHAT THIS IS AND IS NOT. Both are FILTERS on a population that loses 3.64 pt/trade. The
burn list is emphatic about how that has gone: 92 single-variable cells with none
net-positive in both eras (§8.1), 99 cells scored for green days with a 42% ceiling (§8.3).
So every cell is reported in BOTH eras from the start, and the count of cells tested is
printed with the results — a cell that clears only in 2025 is the burn list repeating
itself, not a finding.

    ANGUS: "i guess next thing to look at is market context and shit like that too, if
    youre shorting a heavy bull market its probably not gonna go best for you."

CONTEXT IS CAUSAL BY CONSTRUCTION. `build_daily_context` shifts the whole per-session table
once at the end, so every column is computed from sessions strictly BEFORE its own date.
That matters more for London than anywhere else: it trades at 03:00 ET, hours before the
RTH session that would otherwise contaminate the same day's row.

ENTRY SELECTION. §8.7 measured, with B2 still in, that the setups E3 never filled ran
82% WR / PF 5.42 / ~+9.9 pt while the shared ones ran PF 0.63 — *"the displacement entry
recovers a genuinely good population and re-prices a bad one ... that tension is unresolved
and is the real question."* B2 is gone now and the floor is cut, so it is re-asked here on
displacements only. L1 `status` is the E3 walk's own verdict: filled, or expired unfilled.

    python -m scripts.l2_london_context_entry_splits
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.prop_score import BAR_N, score_book  # noqa: E402

BOOK = ROOT / "output/l2_outcomes_london_fit_EC_rr0.parquet"
CTX = ROOT / "output/daily_context.parquet"
L0 = ROOT / "output/l0_triggers_london_fit_std.parquet"
L1 = ROOT / "output/l1_fills_london_fit_dedup.parquet"
ERAS = [("2025", "2025-01-01", "2025-12-31"), ("2026", "2026-01-01", "2026-12-31")]


def cells(B: pd.DataFrame, col: str, days: list[str]) -> list[str]:
    """One row per value of `col`, scored full-span and in each era side by side."""
    L = [f"**{col}**", "",
         "| cell | N | net pt | green | T | 2025 net | 2025 green | 2026 net | 2026 green |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    vals = B[col].where(B[col].notna(), "no_context").astype(str)
    for v in sorted(vals.unique()):
        g = B[vals == v]
        s = score_book(g, all_days=days)
        if not s:
            continue
        era = []
        for _, lo, hi in ERAS:
            d = [x for x in days if lo <= x <= hi]
            e = score_book(g[(g.day >= lo) & (g.day <= hi)], all_days=d)
            era += ([f"{e['net_pts']:+.2f}", f"{e['green']:.0%}"] if e else ["—", "—"])
        flag = "" if s["n"] >= BAR_N else " ᴺ"        # under the declared N>=200 bar
        both = (era[0] != "—" and era[2] != "—"
                and float(era[0]) > 0 and float(era[2]) > 0)
        L.append(f"| {v}{flag} | {s['n']:,} | {'**' if both else ''}{s['net_pts']:+.2f}"
                 f"{'**' if both else ''} | {s['green']:.0%} | {s['t']:.2f} | "
                 + " | ".join(era) + " |")
    return L + ["", "ᴺ = under the N ≥ 200 bar; the cell is too small to carry a verdict.", ""]


def main() -> int:
    if not BOOK.exists():
        print(f"missing {BOOK.name} — build the rr0 arm first")
        return 1
    T = pd.read_parquet(BOOK)
    B = T[(T.kind == "displacement") & (T.status == "outcome") & T.vs_first].copy()
    days = sorted(pd.read_parquet(L0).day.astype(str).unique())

    # ---- context join. Causality is structural in build_daily_context, but verify the join
    # actually landed rather than trusting it: an all-NaN merge scores as one silent cell.
    C = pd.read_parquet(CTX)
    C["day"] = C["day"].astype(str)
    B["day"] = B["day"].astype(str)
    ctx_cols = ["trend_state", "vol_state", "balance_state", "trend_sign", "poc_streak"]
    B = B.merge(C[["day", *ctx_cols]], on="day", how="left")
    gone = sorted(set(B.day) - set(C.day))
    if gone:
        # Kept as an explicit `no_context` cell rather than dropped: a silently vanishing
        # day is how a book stops reconciling. 2026-04-03 is Good Friday.
        print(f"note — {len(gone)} of {B.day.nunique()} book days carry no context row "
              f"({', '.join(gone)}); scored as `no_context`", file=sys.stderr)

    # with-trend / against-trend, Angus's own framing
    sgn = (B.direction.astype(str).str.lower() == "long").map({True: 1, False: -1})
    ts_ = pd.to_numeric(B.trend_sign, errors="coerce").fillna(0).astype(int)
    B["trend_align"] = pd.Series(
        ["neutral" if t == 0 else ("with_trend" if s == t else "against_trend")
         for s, t in zip(sgn, ts_)], index=B.index)

    # ---- entry selection: did the E3 LIMIT walk ever catch this same trigger?
    F = pd.read_parquet(L1)[["ts", "status"]].rename(columns={"status": "e3"})
    B = B.merge(F, on="ts", how="left")
    B["e3_entry"] = B.e3.map({"filled": "e3_would_have_filled",
                              "expired": "e3_NEVER_filled"}).fillna("unknown")

    n_cells = sum(B[c].astype(str).nunique() for c in
                  ["trend_align", "trend_state", "vol_state", "balance_state", "e3_entry"])
    L = ["# LONDON — market context and entry selection on the rr0 book", "",
         f"Base book: **{len(B):,} deduped displacement setups**, rr0 (next structural "
         f"level), over {len(days)} fit sessions. Base rate **"
         f"{score_book(B, all_days=days)['net_pts']:+.2f} pt/trade**, "
         f"**{score_book(B, all_days=days)['green']:.0%} green days** "
         "(all sessions, flat days counted flat).", "",
         f"**{n_cells} cells tested.** Every cell is shown in both eras. A cell is bolded "
         "only if it is net-positive in 2025 AND 2026 — the burn-list bar (§8.1), not a "
         "full-span average that one good era can carry.", "",
         "The prop bar for reference: net ≥ 4 pt, T ≥ 2, N ≥ 200, green ≥ 55%.", ""]

    L += ["## Market context (handoff §6, §12 step 2)", ""]
    for c in ["trend_align", "trend_state", "vol_state", "balance_state"]:
        L += cells(B, c, days)

    e3f = pd.read_parquet(L1)
    lag = e3f.loc[e3f.status == "filled", "mins_to_fill"]
    L += ["## Entry selection — the §8.7 tension, B2 removed", "",
          "`e3_NEVER_filled` are setups the LIMIT entry would have missed entirely; the "
          "displacement entry is the only reason they exist as trades.", "",
          "> ⚠️ **THIS IS NOT A TRADEABLE FILTER — it is a lookahead split.** Whether the E3 "
          f"limit ever fills is settled AFTER the displacement entry: measured, E3 fills a "
          f"minimum of **{lag.min():.0f} minute** after its trigger (median {lag.median():.0f}, "
          f"max {lag.max():.0f}), and **{(lag <= 0).mean():.1%}** fill on the trigger bar "
          "itself. At the moment you enter the displacement you cannot know which side of "
          "this split you are on. Read it as a DIAGNOSTIC — it says *which* London "
          "displacements pay — never as a rule to trade.", ""]
    L += cells(B, "e3_entry", days)

    text = "\n".join(L)
    print(text)
    (ROOT / "output/london_context_entry_splits.md").write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
