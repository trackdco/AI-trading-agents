#!/usr/bin/env python3
"""Screen — is there a flow signal at the RETEST BAR'S CLOSE?

ANGUS 2026-08-06:

    "yk how the limit order was foreshadowing 30 seconds or whatever in the future. what if
     we looked as a matter of if we market ordered at the end of when that limit got filled.
     so we wait for the retest, and we wait for order flow confirmation FROM that retest.
     itll mess the rr a bit and everything"

WHY THIS IS THE IDEA THAT UNBLOCKS FLOW VALIDATION. Two entry mechanisms have been tried and
each fails one half of the problem:

  E3, limit at the retest      GOOD R (entry sits on the level) but flow CANNOT be read. The
                               order fills passively mid-bar, so every book read at that bar's
                               close lands AFTER the decision. `research/findings/
                               LDN-depth-read-one-bar-late.md` is that discovery: reading one
                               bar late took `W` from +19.0pp to +8.2pp and `FAR` from +20.5
                               to +6.3. Angus's own read on why it can never work: "on a limit
                               order, of course the minute before entry, flow will probably be
                               against us because it is opposing our direction to get filled".
  EC, market on displacement   HONEST flow (the entry candle has closed) but WRECKED R --
                               median stop 26.5pt vs 16.2pt, and mean R stayed ~0.

Angus's mechanism keeps both: wait for the retest to be touched, let that bar CLOSE, then
market in at the close with the flow of that closed bar as the confirmation. The decision
point becomes the bar close -- which is exactly where the depth read already sits. **The
barred `dep_*` anchor becomes the legal one.** The entry is not being worked around the
contaminated measurement; the entry is being moved to where the measurement already was.

THE COST GATE, RUN FIRST AND PASSED: entering at the retest bar's close instead of the limit
costs a mean of **+0.09 pt**, and the close is BETTER than the limit **49.2%** of the time
(the retest candle often closes back through the level). Median risk 13.8 -> 13.0pt, median R
x1.03. Angus expected "itll mess the rr a bit"; measured, it does not.

WHAT THIS SCRIPT IS, AND IS NOT. It is a SCREEN, not a result (§5.9.1 -- no expectancy claim).
It reads the book at the retest bar's close and asks whether that separates outcomes. It is
measured on E3 outcomes, whose entry is the limit, so **the numbers do not transfer to the new
entry** -- outcomes shift when the entry shifts. What transfers is whether the signal exists
at that anchor at all, which decides whether the engine work is worth doing.

    python -m scripts.retest_close_flow_screen
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
DEPTH = ROOT / "output/depth_minutes.parquet"
BOOK = ROOT / "output/l2_outcomes_fit.parquet"
BARS = ("data/reference/nq_1m_master.parquet", "data/reference/nq_1m_feb_jul2026.parquet")


def load() -> pd.DataFrame:
    d = pd.read_parquet(DEPTH)
    O = pd.read_parquet(BOOK)
    D = O[(O.status == "outcome") & (O.kind == "displacement")].copy()
    D["mi"] = pd.to_datetime(D.fill_ts, utc=True, format="mixed").dt.tz_convert(NY).dt.floor("min")
    D = D.merge(d, left_on="mi", right_index=True, how="inner")
    lng = D.direction.astype(str).str.lower().str.startswith(("l", "b"))
    D["era"] = D.day.str[:4]
    # Directional forms. "ahead" = the side price must consume to reach target; "behind" =
    # the side supporting the position. Sign conventions matter more than the raw columns:
    # a raw bid_total means nothing until it is stated relative to trade direction.
    D["flow_with"] = np.where(lng, D.imb, 1 - D.imb)
    D["wall_ahead_rat"] = np.where(lng, D.ask_wall_ratio, D.bid_wall_ratio)
    D["wall_ahead_dist"] = np.where(lng, D.ask_wall_dist, D.bid_wall_dist)
    D["wall_behind_rat"] = np.where(lng, D.bid_wall_ratio, D.ask_wall_ratio)
    return D


def entry_cost() -> str:
    """The gate: what entering at the bar close instead of the limit actually costs."""
    B = pd.concat([pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
                   for p in BARS], ignore_index=True).drop_duplicates("ts_event")
    B["mi"] = pd.to_datetime(B.ts_event, utc=True).dt.tz_convert(NY).dt.floor("min")
    bc = dict(zip(B.mi, B.close))
    O = pd.read_parquet(BOOK)
    D = O[(O.status == "outcome") & (O.kind == "displacement")].copy()
    D["mi"] = pd.to_datetime(D.fill_ts, utc=True, format="mixed").dt.tz_convert(NY).dt.floor("min")
    D["bc"] = D.mi.map(bc)
    D = D.dropna(subset=["bc"])
    sgn = np.where(D.direction.astype(str).str.lower().str.startswith(("l", "b")), 1, -1)
    adv = (D.bc - D.entry) * sgn
    rn = (D.bc - D.stop).abs()
    return (f"n={len(D):,} | mean adverse {adv.mean():+.2f}pt | close better than limit "
            f"{(adv < 0).mean():.1%} | median risk {D.risk.median():.1f} -> {rn.median():.1f}pt")


def main() -> int:
    D = load()
    L = ["# Screen — flow at the retest bar's close", "",
         "**Census/screen only (§5.9.1) — no expectancy claim.** Measured on E3 outcomes",
         "(entry at the limit); under the proposed entry the outcomes shift, so these numbers",
         "do NOT transfer. What transfers is whether a signal exists at this anchor.", "",
         f"**Entry-cost gate:** {entry_cost()}", "",
         f"**{len(D):,} fills with a book read at the retest bar's close.** "
         f"Base mean R {D.R.mean():+.3f}, net {D.pts.mean():+.2f} pt/trade.", ""]

    for f in ("flow_with", "wall_ahead_dist", "wall_behind_rat", "wall_ahead_rat"):
        q = D[f].quantile([1 / 3, 2 / 3]).values
        L += [f"## `{f}`", "",
              "| tercile | n | mean R | net pt | 2025 R | 2026 R | eras agree |",
              "|---|---:|---:|---:|---:|---:|---|"]
        rows = [("LOW", D[D[f] <= q[0]]), ("MID", D[(D[f] > q[0]) & (D[f] < q[1])]),
                ("HIGH", D[D[f] >= q[1]])]
        mono = []
        for nm, S in rows:
            rs = [S[S.era == e].R.mean() if len(S[S.era == e]) > 40 else np.nan
                  for e in ("2025", "2026")]
            ag = (all(np.isfinite(x) for x in rs) and np.sign(rs[0]) == np.sign(rs[1]))
            mono.append(S.R.mean())
            L.append(f"| {nm} | {len(S):,} | **{S.R.mean():+.3f}** | {S.pts.mean():+.2f} | "
                     + " | ".join(f"{x:+.3f}" if np.isfinite(x) else "—" for x in rs)
                     + f" | {'**yes**' if ag else 'no'} |")
        m = (all(a >= b for a, b in zip(mono[:-1], mono[1:]))
             or all(a <= b for a, b in zip(mono[:-1], mono[1:])))
        L += ["", f"Monotonic across terciles: **{'yes' if m else 'no'}**.", ""]

    L += ["---", "", "## Read", "",
          "`flow_with` is the one that behaves: monotonic across all three terciles, and the",
          "favourable end is era-consistent with **2026 stronger than 2025** — the opposite of",
          "the decay pattern that usually means noise was fitted to the discovery era.", "",
          "**And the sign is inverted from the textbook.** A book already leaning *your way* at",
          "the retest predicts a WORSE outcome. That is mechanically sensible for a retest: if",
          "the book agrees with you by the time price comes back, you are late and the displayed",
          "liquidity gets pulled. The edge is in absorption — going in against displayed size",
          "that then gets eaten.", "",
          "**Owed before this is anything more than a lead:** a family-wise permutation null",
          "(§2.3) over all four features and three terciles, and a re-measurement on the real",
          "entry rather than E3's. The effect is ~+1.1 pt/trade against a 4.0 bar — a selection",
          "signal, not a strategy.", ""]

    text = "\n".join(L)
    print(text)
    (ROOT / "output/retest_close_flow_screen.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
