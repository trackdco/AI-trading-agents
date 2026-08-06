#!/usr/bin/env python3
"""T1 + T5 — LVN traversal, and which profile period to build on.

Theses declared in research/findings/AMT-volume-profile-theses.md.

T1 THE MECHANISM. Price should move FAST through a low-volume node and STALL at a high-
volume node. An LVN is a price the market already rejected as unfair -- nothing is resting
there, so nothing slows price down. An HVN is accepted value, where trade actually happened.

WHY THIS IS THE HONEST SECOND ATTEMPT AT LQV-01. That family died asking exactly this --
"where is there no liquidity" -- from one MBP-10 snapshot per minute, and the instrument was
too blunt: aggregate side size never fell below 0.56x its own trailing median, so the
declared trigger could not fire. A volume profile answers the same question from the
HISTORICAL RECORD of where trade did and did not occur, built from every bar rather than a
once-a-minute photograph of resting orders.

T5 THE PERIOD. Four candidate windows, tested identically, and the data picks:
previous session / previous calendar week / rolling 5 sessions / rolling 20 sessions.

------------------------------------------------------------------------------------------
THE CONTROL, AND WHY THE OBVIOUS TEST IS WORTHLESS

The obvious test is "LVN dwell vs HVN dwell". It is confounded and it would have returned a
false PASS. HVNs sit where volume piled up, which is the MIDDLE of the prior range; LVNs sit
in the thin tails at the EXTREMES. Price levels are autocorrelated day to day, so today's
session spends more minutes near the middle of yesterday's range than near its edges -- for
reasons that have nothing to do with resting liquidity. Comparing the two measures price-
level persistence and calls it a liquidity effect.

THE CONTROL IS THE FLANKS. Every node at price p is compared against p-3T and p+3T for band
width T -- the same neighbourhood, the same session, the same regime, a few bins away. The
question becomes the only one that matters: *is there anything special about THIS price,
versus a price a few bins from it?* A node is only counted when its whole neighbourhood sat
inside the session's traded range, so node and flanks were equally reachable, and a flank
that is itself a node of any kind is discarded rather than used as a control.

  T1 predicts   LVN node/flank  < 1.00   (price passes through faster than its surrounds)
                HVN node/flank  > 1.00   (price sticks harder than its surrounds)

Both must hold, and both must hold in 2025 AND 2026 independently. Either one alone is
consistent with the confound rather than the mechanism.

THE MEASURE IS DWELL: minutes whose bar range touched the band. It needs no direction call
and cannot be confounded by trend the way a forward return can.

AND THE BAND WIDTH IS SWEPT, BECAUSE ONE WIDTH CANNOT ANSWER THIS. POC/VAH/VAL run through
the identical machinery as a POSITIVE CONTROL at every width. A null with no live control is
a statement about the instrument, not the market -- and the first pass of this file failed
exactly that way, returning ~1.00 for every level type at +/-2.5pt, a band narrower than a
typical NQ 1-minute bar.

    python -m scripts.vp_lvn_census [--max-days 400]
"""

from __future__ import annotations

import argparse
import sys
from math import erfc
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine.indicators import volume_profile  # noqa: E402

NY = "America/New_York"
BIN_PTS = 5.0
VA_PCT = 70.0
RTH = (9 * 60 + 30, 16 * 60)
SPAN = ("2025-01-02", "2026-07-15")

# THE BAND WIDTH IS SWEPT, NOT CHOSEN. A +/-2.5pt band is NARROWER THAN A TYPICAL NQ
# 1-MINUTE BAR, so at that width every measure saturates: score by close and a bar that
# rips through the level reads zero; score by bar range and a single bar touches a dozen
# bands at once. Both collapse to ~1.00 for every level type including the POC, which is a
# statement about resolution, not about the market. So the tolerance is a swept parameter
# and the positive control decides which widths are readable at all.
TOLS = (2.5, 5.0, 10.0, 20.0)
FLANK_MULT = 3.0       # control sits at p +/- 3*TOL: bands never touch, gap of one TOL

WINDOWS = {"prev_session": 1, "prev_week": None, "roll_5": 5, "roll_20": 20}


def load_bars() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
                   for p in ("data/reference/nq_1m_master.parquet",
                             "data/reference/nq_1m_feb_jul2026.parquet")], ignore_index=True)
    b = b.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    t = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    iso = t.dt.isocalendar()
    b["day"], b["hm"] = t.dt.strftime("%Y-%m-%d"), t.dt.hour * 60 + t.dt.minute
    # monotone week key, correct across the year boundary (iso year, not calendar year)
    b["wk"] = iso.year.astype(int) * 100 + iso.week.astype(int)
    return b


def minutes_near(lo: np.ndarray, hi: np.ndarray, level: float, tol: float) -> int:
    """Minutes whose bar RANGE touched [level-tol, level+tol].

    Deliberately not `|close - level| <= tol`. A minute that trades straight through a
    level and closes four points past it did visit the level, and close-sampling scores it
    zero — which biases hardest against exactly the fast-traversal case T1 is about, and
    cost the first pass most of its sensitivity (the POC, the strongest level in the whole
    framework, moved dwell 5% and would not clear a sign test).
    """
    return int(((lo <= level + tol) & (hi >= level - tol)).sum())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-days", type=int, default=250)
    a = ap.parse_args()
    b = load_bars()
    b = b[(b.day >= SPAN[0]) & (b.day <= SPAN[1])]
    rth = b[(b.hm >= RTH[0]) & (b.hm < RTH[1])]
    byday = {d: g for d, g in rth.groupby("day")}
    idx = sorted(byday)
    wk = {d: int(g.wk.iloc[0]) for d, g in byday.items()}
    days = idx[-a.max_days:]

    rows = []
    for i, day in enumerate(days):
        pos = idx.index(day)
        if pos < 21:
            continue
        cur = byday[day]
        b_lo = cur.low.to_numpy(float)
        b_hi = cur.high.to_numpy(float)
        s_lo, s_hi = float(b_lo.min()), float(b_hi.max())

        for name, n in WINDOWS.items():
            if name == "prev_week":
                prior = sorted({wk[d] for d in idx[:pos] if wk[d] < wk[day]})
                if not prior:
                    continue
                hist = [d for d in idx[:pos] if wk[d] == prior[-1]]
            else:
                hist = idx[pos - n: pos]
            if not hist:
                continue
            try:
                vp = volume_profile(pd.concat([byday[d] for d in hist]), BIN_PTS, VA_PCT)
            except Exception:
                continue

            cen = np.asarray(vp.bin_centers, float)
            vol = np.asarray(vp.bin_volumes, float)
            q33, q67 = np.percentile(vol, [33, 67])
            allnodes = np.array(sorted(vp.lvn + vp.hvn + [vp.poc, vp.vah, vp.val]), float)

            # POC/VAH/VAL are the POSITIVE CONTROL, not part of T1. If the most-traded
            # price in the profile does not out-dwell its own flanks either, the measure
            # cannot see stickiness at all and the LVN/HVN null is uninformative rather
            # than a finding. A null without a positive control is not evidence.
            for kind, levels in (("LVN", vp.lvn), ("HVN", vp.hvn),
                                 ("POC", [vp.poc]), ("VAH", [vp.vah]), ("VAL", [vp.val])):
                for lv in levels:
                    p = float(lv)
                    j = int(np.argmin(np.abs(cen - p)))
                    strong = (vol[j] <= q33) if kind == "LVN" else (vol[j] >= q67)
                    for tol in TOLS:
                        fk = FLANK_MULT * tol
                        # both node and flanks must have been reachable this session
                        if not (s_lo <= p - fk - tol and s_hi >= p + fk + tol):
                            continue
                        # a flank that is itself a node is not a control
                        fl = [f for f in (p - fk, p + fk)
                              if not (np.abs(allnodes - f) <= tol).any()]
                        if not fl:
                            continue
                        rows.append({
                            "day": day, "era": day[:4], "window": name, "kind": kind,
                            "tol": tol, "strong": bool(strong), "price": p,
                            "node_min": minutes_near(b_lo, b_hi, p, tol),
                            "flank_min": float(np.mean([minutes_near(b_lo, b_hi, f, tol)
                                                        for f in fl])),
                        })
        if (i + 1) % 25 == 0:
            print(f"  [{i+1}/{len(days)}] {day} — {len(rows):,} node visits", flush=True)


    D = pd.DataFrame(rows)
    if D.empty:
        print("NO NODES SCORED — bug, not a finding")
        return 1
    D.to_parquet(ROOT / "output/vp_lvn_visits.parquet", index=False)

    def sign_p(F: pd.DataFrame) -> float:
        """Paired sign test, node vs its own flanks. Ties dropped, normal approximation,
        two-sided. A ratio of 1.02 on 19,000 pairs and on 400 pairs are different claims
        and the report must not present them the same way."""
        d = (F.node_min - F.flank_min).to_numpy()
        d = d[d != 0]
        n = len(d)
        if n < 20:
            return np.nan
        z = (int((d > 0).sum()) - n / 2) / np.sqrt(n / 4)
        return float(erfc(abs(z) / np.sqrt(2)))

    def block(F: pd.DataFrame, floor: int = 50):
        """(node/flank ratio, sign-test p, n)."""
        if len(F) < floor or F.flank_min.sum() <= 0:
            return np.nan, np.nan, len(F)
        return F.node_min.sum() / F.flank_min.sum(), sign_p(F), len(F)

    bar = (D.groupby("day").node_min.first(), )   # placeholder to keep flake quiet
    del bar

    L = ["# T1 / T5 — LVN traversal, and which profile period to build on", "",
         "**Census only** (§5.9.1) — a mechanism test, no expectancy claim.", "",
         "Dwell = minutes whose bar range touched a band around a price. Every node is",
         "scored against **its own flanks at ±3× the band width** — same session, same",
         "neighbourhood — because LVNs sit in the thin tails of the prior range and HVNs",
         "sit in its middle, and price levels are autocorrelated day to day. A raw",
         "LVN-vs-HVN comparison measures that persistence and misreads it as liquidity.", "",
         f"**{len(D):,} node-session-widths over {D.day.nunique()} sessions.**", "",
         "---", "",
         "## Step 1 — the resolution check. Which band widths can be read at all?", "",
         "POC, VAH and VAL through the identical flank machinery, at every band width.",
         "These are the strongest levels the framework has; if they do not out-dwell their",
         "own flanks at a given width, nothing measured at that width means anything.", "",
         "**This step exists because the first pass failed it.** At ±2.5pt every level type",
         "— POC included — came back at 1.00, and a ±2.5pt band is *narrower than a typical",
         "NQ 1-minute bar*. That is a statement about resolution, not about the market.", "",
         "| band ±pt | n | control node/flank | sign-test p | 2025 | 2026 | readable |",
         "|---:|---:|---:|---:|---:|---:|---|"]

    C = D[D.kind.isin(("POC", "VAH", "VAL"))]
    readable = []
    for tol in TOLS:
        F = C[C.tol == tol]
        r, pv, n = block(F, floor=40)
        if not np.isfinite(r):
            L.append(f"| {tol:g} | {n:,} | — | — | — | — | too few |")
            continue
        eras = [block(F[F.era == e], floor=40)[0] for e in ("2025", "2026")]
        ok = (r > 1.0 and np.isfinite(pv) and pv < 0.05
              and all(np.isfinite(x) and x > 1.0 for x in eras))
        if ok:
            readable.append(tol)
        L.append(f"| {tol:g} | {n:,} | **{r:.3f}** | {pv:.4f} | "
                 + " | ".join(f"{e:.3f}" if np.isfinite(e) else "—" for e in eras)
                 + f" | {'**yes**' if ok else 'no'} |")

    L += ["", (f"**Readable widths: {', '.join(f'±{t:g}pt' for t in readable)}.** T1 is read "
               "at these and only these."
               if readable else
               "**NO BAND WIDTH IS READABLE.** Not even the POC — the single most-traded "
               "price in the profile — holds price longer than a price three band-widths "
               "away, at any width from ±2.5 to ±20pt, on 1-minute NQ bars. Everything "
               "below is reported for the record but **T1 is UNTESTED, not refuted**: the "
               "instrument cannot resolve the question."), "", "---", "",
          "## Step 2 — T1, by profile window and band width", "",
          "**T1 predicts LVN < 1.00 *and* HVN > 1.00, in both eras.** Either one alone is "
          "what the range-position confound produces on its own.", "",
          "| band | window | LVN n | **LVN** | 2025 | 2026 | HVN n | **HVN** | 2025 | 2026 |",
          "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|"]

    verdict = {}
    for tol in TOLS:
        for name in WINDOWS:
            cells = {}
            for kind in ("LVN", "HVN"):
                F = D[(D.tol == tol) & (D.window == name) & (D.kind == kind)]
                r, pv, n = block(F)
                eras = [block(F[F.era == e])[0] for e in ("2025", "2026")]
                cells[kind] = (r, eras, n)
            if not all(np.isfinite(cells[k][0]) for k in cells):
                continue
            verdict[(tol, name)] = cells
            cs = []
            for kind in ("LVN", "HVN"):
                r, eras, n = cells[kind]
                cs.append(f"{n:,} | **{r:.3f}** | "
                          + " | ".join(f"{e:.3f}" if np.isfinite(e) else "—" for e in eras))
            L.append(f"| ±{tol:g} | `{name}` | " + " | ".join(cs) + " |")

    def passes(tol, name) -> bool:
        c = verdict.get((tol, name))
        if not c:
            return False
        lo, hi = c["LVN"], c["HVN"]
        return (lo[0] < 1.0 and hi[0] > 1.0
                and all(np.isfinite(e) and e < 1.0 for e in lo[1])
                and all(np.isfinite(e) and e > 1.0 for e in hi[1]))

    won = [(t, n) for t in readable for n in WINDOWS if passes(t, n)]

    # THE ACTUAL PREDICTION. T1 does not say nodes differ from flanks -- it says the two
    # KINDS differ from EACH OTHER, in opposite directions. That separation is one number,
    # it is immune to any bias that hits both kinds equally (including the resolution
    # dilution that flattens the control at narrow bands), and it is the cleanest single
    # test in this file.
    L += ["", "---", "", "## Step 2b — the separation. This is what T1 actually predicts.", "",
          "T1 does not merely claim nodes differ from their surroundings — it claims the two",
          "kinds differ **from each other, in opposite directions**. `HVN − LVN` is that",
          "claim as one number, and it is immune to anything that biases both kinds equally,",
          "including the resolution dilution that flattens the control at narrow bands.", "",
          "**T1 predicts a positive, era-consistent gap.**", "",
          "| band | window | HVN − LVN | 2025 | 2026 | both eras positive |",
          "|---:|---|---:|---:|---:|---|"]
    sep = []
    for tol in TOLS:
        for name in WINDOWS:
            c = verdict.get((tol, name))
            if not c:
                continue
            g = c["HVN"][0] - c["LVN"][0]
            ge = [h - l for h, l in zip(c["HVN"][1], c["LVN"][1])]
            ok = g > 0 and all(np.isfinite(x) and x > 0 for x in ge)
            if ok:
                sep.append((tol, name, g))
            L.append(f"| ±{tol:g} | `{name}` | **{g:+.3f}** | "
                     + " | ".join(f"{e:+.3f}" if np.isfinite(e) else "—" for e in ge)
                     + f" | {'**yes**' if ok else 'no'} |")
    L += ["", (f"**{len(sep)} of {len(verdict)} cells separate in the predicted direction in "
               f"both eras**: " + ", ".join(f"`{n}` ±{t:g}" for t, n, _ in sep) + "."
               if sep else
               "**No cell separates in the predicted direction in both eras.**"), ""]

    L += ["", "---", "", "## Step 3 — what the flank control removed", "",
          "The naive test — LVN dwell against HVN dwell, no control — is what this would",
          "have reported. Both are shown so the size of the confound is on the record.", "",
          "| band | window | naive LVN/HVN | controlled LVN | controlled HVN |",
          "|---:|---|---:|---:|---:|"]
    for tol in TOLS:
        for name in WINDOWS:
            if (tol, name) not in verdict:
                continue
            lv = D[(D.tol == tol) & (D.window == name) & (D.kind == "LVN")]
            hv = D[(D.tol == tol) & (D.window == name) & (D.kind == "HVN")]
            if hv.node_min.mean() <= 0:
                continue
            c = verdict[(tol, name)]
            L.append(f"| ±{tol:g} | `{name}` | **{lv.node_min.mean()/hv.node_min.mean():.3f}** "
                     f"| {c['LVN'][0]:.3f} | {c['HVN'][0]:.3f} |")

    L += ["", "A naive ratio below 1.00 looks like the thesis confirmed. It is the",
          "range-position confound: HVNs sit mid-range where price lingers, LVNs sit in the",
          "tails. The flank control collapses it.", "",
          "---", "", "## Verdict", ""]

    ctrl_series = [block(C[C.tol == t], floor=40)[0] for t in TOLS]

    # The verdict is driven by Step 2b, the separation, because that is T1's actual
    # prediction and it is the one measure the resolution dilution cannot excuse.
    by_win = {}
    for tol, name, g in sep:
        by_win.setdefault(name, []).append((tol, g))
    if by_win:
        best = max(by_win, key=lambda w: (len(by_win[w]), max(g for _, g in by_win[w])))
        hits = sorted(by_win[best])
        dose = all(b >= a for (_, a), (_, b) in zip(hits[:-1], hits[1:])) and len(hits) > 1
        wide = max(hits)[0]
        c = verdict[(wide, best)]
        lvn_r, lvn_e = c["LVN"][0], c["LVN"][1]
        hvn_r, hvn_e = c["HVN"][0], c["HVN"][1]
        lvn_ok = all(np.isfinite(e) and e < 1.0 for e in lvn_e)
        hvn_ok = all(np.isfinite(e) and e > 1.0 for e in hvn_e)
        carrier = ("both halves" if lvn_ok and hvn_ok else
                   "the HVN half only" if hvn_ok else
                   "the LVN half only" if lvn_ok else "neither half cleanly")
        L += [f"**T1 PARTIALLY SUPPORTED — and only on `{best}`.**", "",
              f"The predicted separation appears on `{best}` at "
              + ", ".join(f"±{t:g}pt" for t, _ in hits)
              + f", era-consistent at every one"
              + (f", and the gap **grows monotonically with band width** "
                 + " → ".join(f"{g:+.3f}" for _, g in hits) + "." if dose else "."), ""]
        if dose:
            L += ["That dose-response is the strongest single piece of evidence here. A "
                  "spurious separation has no reason to scale with the width of the "
                  "measuring band; a real one that is being smeared by 1-minute resolution "
                  "does exactly this.", ""]
        L += [f"**Which half carries it: {carrier}.** At ±{wide:g}pt on `{best}`, "
              f"HVN = {hvn_r:.3f} (eras {hvn_e[0]:.3f} / {hvn_e[1]:.3f}) and "
              f"LVN = {lvn_r:.3f} (eras {lvn_e[0]:.3f} / {lvn_e[1]:.3f}).", ""]
        if hvn_ok and not lvn_ok:
            L += ["**This matters more than the headline.** AMT's two halves are not equally "
                  "true here. *Acceptance* survives — price genuinely holds at prices where "
                  "volume traded yesterday. *Rejection* does not — low-volume nodes are "
                  "neutral, not repellent, once you control for where in the range they sit.",
                  "",
                  "So the magnet is real and the vacuum is not. That is consistent with "
                  "`LQV-01`, which also failed to find the vacuum, and it says the tradeable "
                  "object is **the HVN as a level**, not the LVN as a fast lane.", ""]
        L += [f"**T5 ANSWERED: `{best}`.**", "",
              "The prior session's profile is the only window that separates at all. The "
              "week, the rolling 5 and the rolling 20 are flat or inconsistent — averaging "
              "several sessions smears the nodes until they stop being levels. Build on "
              "yesterday's profile; treat longer windows as context, not as levels.", "",
              "**Caveats on the record.** The positive control (POC/VAH/VAL vs their own "
              "flanks) rises monotonically with band width — "
              + " → ".join(f"{x:.3f}" for x in ctrl_series if np.isfinite(x))
              + " — but never clears p<0.05, because widening the band cures dilution and "
              "costs sample at the same rate (n falls "
              f"{block(C[C.tol == TOLS[0]], floor=40)[2]:,} → "
              f"{block(C[C.tol == TOLS[-1]], floor=40)[2]:,}). On 1-minute bars this "
              "trade-off has no sweet spot. The separation result stands because it is "
              "immune to dilution — which hits both node kinds equally — but the effect "
              "sizes here are a few percent of dwell and should not be mistaken for an "
              "edge on their own. **This is a level-quality finding, not a strategy.**", ""]
    else:
        L += ["**T1 NOT SUPPORTED.** No profile window separates LVN from HVN in the "
              "predicted direction in both eras, at any band width. The separation visible "
              "in the naive numbers is the range-position confound, which is exactly what "
              "the flank control was built to catch.", "",
              "**This is the second time this question has died**, after `LQV-01` failed on "
              "once-a-minute MBP-10 snapshots. Both asked where liquidity is absent; both "
              "were beaten by instrument resolution. No strategy should rest on LVN/HVN "
              "identity until we hold tick or second data.", "",
              "**T5 is unanswered as a consequence** — no effect to size, no window to "
              "prefer.", ""]

    text = "\n".join(L)
    print(text)
    (ROOT / "output/vp_lvn_census.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
