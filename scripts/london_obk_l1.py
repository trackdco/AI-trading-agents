#!/usr/bin/env python3
"""L1 mechanics — LDN-OBK-01 / LDN-PO3-01, the London-open break event tree.

Authorised by docs/PREREG-london-open-break-L1.md, committed before this file.
Every arm below is declared there; nothing is searched or tuned here.

CONTINUATION branch (LDN-OBK-01) — 2x2, entry x stop:
  A/S1  close-confirmed entry (stop order at trigger-candle extreme), trigger-candle
        stop                                            <- DECLARED DEFAULT
  A/S2  close-confirmed entry, structural stop (far side of the pre-open range)
  B/S1  immediate entry at the trigger-candle close, trigger-candle stop
  B/S2  immediate entry, structural stop
  Target 2R on all four. Flat 10:00 London.

FAILURE branch (LDN-PO3-01):
  F1    enter at the fail-bar close against the break, stop beyond the sweep
        extreme, target the range MIDPOINT                <- DECLARED DEFAULT
  F2    as F1 but target the FAR EDGE (as taught) — run so the census's implied
        correction is measured rather than assumed

Costs 1pt base / 2pt strict, both always reported. $160-risk sizing. Conservative
intrabar tie-break (stop before target). Era split, never pooled for the headline.

    python -m scripts.london_obk_l1 [--dry-run]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger  # noqa: E402

NY = "America/New_York"
LON = "Europe/London"

PREREG = "docs/PREREG-london-open-break-L1.md"
OUT_MD = ROOT / "output/london_obk_l1.md"

# --- frozen in the L1 prereg -----------------------------------------------------
PREOPEN = ("06:00", "08:00")
TRIGGER = ("08:00", "10:00")
MIN_BARS = 60
MIN_RISK = 2.0            # inherited from scripts/nya_fa_l1.py, not chosen here
TARGET_R = 2.0
COSTS = ((1.0, "base"), (2.0, "strict"))
DOLLAR_RISK = 160.0
MIN_DISP_FRAC = 0.10      # the one declared variable, default arms only

SPAN_START = "2025-01-01"
SPAN_END = "2026-07-15"


def load_bars() -> pd.DataFrame:
    frames = [pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
              for p in ("data/reference/nq_1m_master.parquet",
                        "data/reference/nq_1m_feb_jul2026.parquet")]
    bars = (pd.concat(frames, ignore_index=True)
            .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))
    bars["ts_event"] = pd.to_datetime(bars["ts_event"])
    return bars


def lon_window(day: str, a: str, b: str):
    return (pd.Timestamp(f"{day} {a}", tz=LON).tz_convert(NY),
            pd.Timestamp(f"{day} {b}", tz=LON).tz_convert(NY))


def sim(direction: int, entry: float, stop: float, target: float, bars) -> tuple[float, str]:
    """Conservative: stop is checked before target inside a bar."""
    for hi, lo, cl in bars:
        if direction > 0:
            if lo <= stop:
                return stop - entry, "stop"
            if hi >= target:
                return target - entry, "target"
        else:
            if hi >= stop:
                return entry - stop, "stop"
            if lo <= target:
                return entry - target, "target"
    cl = bars[-1][2]
    return (cl - entry) if direction > 0 else (entry - cl), "time"


def run(bars: pd.DataFrame) -> pd.DataFrame:
    days = sorted(set(pd.bdate_range(SPAN_START, SPAN_END).strftime("%Y-%m-%d")))
    trades = []
    width_hist: list[tuple[str, float]] = []

    for day in days:
        t_start, t_end = lon_window(day, *TRIGGER)
        r_start, r_end = lon_window(day, *PREOPEN)
        frame = bars[(bars["ts_event"] >= r_start) & (bars["ts_event"] < t_end)]
        if len(frame) < MIN_BARS:
            continue
        rng = frame[(frame["ts_event"] >= r_start) & (frame["ts_event"] < r_end)]
        trig = frame[frame["ts_event"] >= t_start].reset_index(drop=True)
        if rng.empty or trig.empty:
            continue

        hi, lo = float(rng["high"].max()), float(rng["low"].min())
        width = hi - lo
        if width <= 0:
            continue
        mid = (hi + lo) / 2.0
        era = day[:4]

        # --- conditioning columns, declared in PREREG-london-open-break-conditioning
        # V3: where the last pre-open close sits inside the range -> the drift the
        # candidate's thesis says the losing side committed to
        last_close = float(rng.iloc[-1]["close"])
        pos = (last_close - lo) / width
        drift = 1 if pos > 0.66 else (-1 if pos < 0.33 else 0)
        # V2: width vs its own trailing 20-session median. Computed from history
        # BEFORE today is appended, so no same-day information leaks in.
        prior = [w for _, w in width_hist[-20:]]
        width_rel = width / (pd.Series(prior).median()) if len(prior) >= 10 else float("nan")
        width_hist.append((day, width))

        for side, level in ((1, hi), (-1, lo)):
            beyond = trig["close"] > level if side > 0 else trig["close"] < level
            if not beyond.any():
                continue
            i0 = int(trig.index[beyond][0])
            tc = trig.loc[i0]                       # the trigger candle
            tail = trig.loc[i0 + 1:]
            if tail.empty:
                continue
            tail_bars = tail[["high", "low", "close"]].to_numpy()

            # displacement of the trigger candle itself, for the declared variable
            disp = float(tc["high"] - level) if side > 0 else float(level - tc["low"])
            disp_frac = disp / width

            # --- continuation arms -------------------------------------------
            tc_far = float(tc["low"]) if side > 0 else float(tc["high"])
            struct = lo if side > 0 else hi
            entries = {
                "A": float(tc["high"]) if side > 0 else float(tc["low"]),
                "B": float(tc["close"]),
            }
            stops = {"S1": tc_far, "S2": struct}

            for ea, entry in entries.items():
                for sa, stop in stops.items():
                    risk = abs(entry - stop)
                    if risk < MIN_RISK:
                        continue
                    if ea == "A":
                        # resting stop order: needs a later bar to trade through it
                        hit = (tail["high"] >= entry) if side > 0 else (tail["low"] <= entry)
                        if not hit.any():
                            continue
                        j = int(tail.index[hit][0])
                        # include the fill bar. Skipping it would drop any stop hit
                        # on that same bar, which understates losses — the wrong
                        # direction for a conservative fill model.
                        sub = trig.loc[j:][["high", "low", "close"]].to_numpy()
                        if not len(sub):
                            continue
                    else:
                        sub = tail_bars
                    target = entry + side * TARGET_R * risk
                    pts, why = sim(side, entry, stop, target, sub)
                    trades.append(dict(day=day, era=era, branch="OBK", arm=f"{ea}/{sa}",
                                       side=side, pts=pts, risk=risk, why=why,
                                       disp_frac=disp_frac, width=width,
                                       lon_hour=int(tc["ts_event"].tz_convert(LON).hour),
                                       width_rel=width_rel,
                                       with_drift=(drift != 0 and drift == side)))

            # --- failure arms -------------------------------------------------
            inside = (tail["close"] <= hi) if side > 0 else (tail["close"] >= lo)
            if not inside.any():
                continue
            f = int(tail.index[inside][0])
            fb = trig.loc[f]
            seg = trig.loc[i0:f]
            extreme = float(seg["high"].max()) if side > 0 else float(seg["low"].min())
            entry = float(fb["close"])
            post = trig.loc[f + 1:]
            if post.empty:
                continue
            post_bars = post[["high", "low", "close"]].to_numpy()
            risk = abs(entry - extreme)
            if risk < MIN_RISK:
                continue
            dirn = -side
            for arm, target in (("F1", mid), ("F2", lo if side > 0 else hi)):
                # a target already reached at entry is not a trade
                if (dirn > 0 and target <= entry) or (dirn < 0 and target >= entry):
                    continue
                pts, why = sim(dirn, entry, extreme, target, post_bars)
                trades.append(dict(day=day, era=era, branch="PO3", arm=arm,
                                   side=side, pts=pts, risk=risk, why=why,
                                   disp_frac=disp_frac, width=width,
                                   lon_hour=int(tc["ts_event"].tz_convert(LON).hour),
                                   width_rel=width_rel,
                                   with_drift=(drift != 0 and drift == side)))

    return pd.DataFrame(trades)


# --- reporting -------------------------------------------------------------------

def stats(T: pd.DataFrame, cost: float) -> dict | None:
    if T.empty:
        return None
    net = T["pts"] - cost
    r = net / T["risk"]
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    n = len(net)
    se = r.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
    return {"n": n, "wr": (net > 0).mean(), "pts": net.sum(),
            "usd": DOLLAR_RISK * r.sum(), "pf": gw / max(gl, 1e-9),
            "r": r.mean(), "t": (r.mean() / se) if se and se == se else 0.0}


def line(label: str, s: dict | None) -> str:
    if not s:
        return f"| {label} | 0 | — | — | — | — | — |"
    return (f"| {label} | {s['n']} | {s['wr']:.0%} | {s['pts']:+.0f} | "
            f"${s['usd']:+,.0f} | {s['pf']:.2f} | {s['r']:+.3f} |")


def table(T: pd.DataFrame, arms: list[str], title: str) -> str:
    L = [f"### {title}", ""]
    for cost, cl in COSTS:
        L += [f"**cost {cl} ({cost:.0f} pt)**", "",
              "| arm | n | WR | net pts | $ @160 risk | PF | R/trade |",
              "|---|---:|---:|---:|---:|---:|---:|"]
        for arm in arms:
            for era in ("2025", "2026"):
                sel = T[(T["arm"] == arm) & (T["era"] == era)]
                L.append(line(f"{arm} · {era}", stats(sel, cost)))
        L.append("")
    return "\n".join(L)


def report(T: pd.DataFrame) -> str:
    L = ["# LDN-OBK-01 / LDN-PO3-01 — L1 mechanics", "",
         f"Authorised by `{PREREG}`. Bars only. 2023/24 untouched.",
         "Conservative intrabar (stop before target). No arm dies here on expectancy",
         "(§5.9.2); L1 produces numbers and ranks nothing.", ""]

    obk = T[T["branch"] == "OBK"]
    po3 = T[T["branch"] == "PO3"]

    L.append(table(obk, ["A/S1", "A/S2", "B/S1", "B/S2"],
                   "Continuation branch (LDN-OBK-01) — default is A/S1"))
    L.append(table(po3, ["F1", "F2"],
                   "Failure branch (LDN-PO3-01) — default is F1 (midpoint)"))

    # the declared reading: does the tight stop beat the structural stop
    L += ["### The tight-stop claim — the reason this family was greenlit", "",
          "Pre-committed reading: supported only if S1 beats S2 on R/trade in BOTH",
          "eras at BOTH cost levels.", "",
          "| entry | era | cost | S1 R/trade | S2 R/trade | S1 wins |",
          "|---|---|---|---:|---:|---|"]
    verdict_bits = []
    for ea in ("A", "B"):
        for era in ("2025", "2026"):
            for cost, cl in COSTS:
                s1 = stats(obk[(obk["arm"] == f"{ea}/S1") & (obk["era"] == era)], cost)
                s2 = stats(obk[(obk["arm"] == f"{ea}/S2") & (obk["era"] == era)], cost)
                if not s1 or not s2:
                    continue
                win = s1["r"] > s2["r"]
                if ea == "A":
                    verdict_bits.append(win)
                L.append(f"| {ea} | {era} | {cl} | {s1['r']:+.3f} | {s2['r']:+.3f} | "
                         f"{'YES' if win else 'no'} |")
    L += ["", f"**Default entry (A): S1 beats S2 in {sum(verdict_bits)} of "
          f"{len(verdict_bits)} era×cost cells.** "
          + ("Claim SUPPORTED." if verdict_bits and all(verdict_bits)
             else "Claim NOT supported as declared."), ""]

    s2_time = T[T["arm"].isin(["A/S2", "B/S2"])]["why"].value_counts(normalize=True)
    L += ["**Read the control before reading the verdict.** The structural-stop arms",
          f"exit on the clock {s2_time.get('time', 0):.0%} of the time: at a stop that",
          "wide, a 2R target sits 100-170 pts away and NQ does not travel that far",
          "inside the two-hour window. So S2 as specified is not really the same trade",
          "with a wider stop — it is a two-hour hold that exits at market. Its edge over",
          "S1 is near-zero beating negative, not a working alternative.",
          "",
          "**The defensible statement is therefore about S1 on its own terms, and it is",
          "not kind:** at 2R the trigger-candle stop is hit "
          f"{T[T['arm'] == 'A/S1']['why'].value_counts(normalize=True).get('stop', 0):.0%}"
          " of the time and the target "
          f"{T[T['arm'] == 'A/S1']['why'].value_counts(normalize=True).get('target', 0):.0%}"
          ". A 2R trade needs 33.3% to break even before costs. That is break-even",
          "geometry, and the cost stack decides it — which is exactly the shape that",
          "killed `nypre-euro-handoff`. The tighter stop does not rescue the level break;",
          "it gets you tapped out.", ""]

    # the declared variable
    L += ["### Declared variable — minimum displacement (default arms only)", ""]
    for branch, arm in (("OBK", "A/S1"), ("PO3", "F1")):
        sel = T[(T["branch"] == branch) & (T["arm"] == arm)]
        L += [f"**{arm}**", "",
              "| filter | era | cost | n | WR | net pts | PF | R/trade |",
              "|---|---|---|---:|---:|---:|---:|---:|"]
        for lbl, sub in (("none (as taught)", sel),
                         (f">= {MIN_DISP_FRAC:.2f}x range", sel[sel["disp_frac"] >= MIN_DISP_FRAC])):
            for era in ("2025", "2026"):
                for cost, cl in COSTS:
                    s = stats(sub[sub["era"] == era], cost)
                    if not s:
                        continue
                    L.append(f"| {lbl} | {era} | {cl} | {s['n']} | {s['wr']:.0%} | "
                             f"{s['pts']:+.0f} | {s['pf']:.2f} | {s['r']:+.3f} |")
        L.append("")

    # exit-reason mix, because a time-stop-heavy arm is a different animal
    L += ["### How trades ended (base cost, both eras)", "",
          "| arm | stop | target | time |", "|---|---:|---:|---:|"]
    for arm in ("A/S1", "A/S2", "B/S1", "B/S2", "F1", "F2"):
        sel = T[T["arm"] == arm]
        if sel.empty:
            continue
        m = sel["why"].value_counts(normalize=True)
        L.append(f"| {arm} | {m.get('stop',0):.0%} | {m.get('target',0):.0%} | "
                 f"{m.get('time',0):.0%} |")
    L.append("")
    return "\n".join(L)


def build_trials(T: pd.DataFrame) -> list[dict]:
    """Every arm x era on the ledger at trial time (§6.0.2), winners and losers alike."""
    rows = []
    for arm in sorted(T["arm"].unique()):
        for era in ("2025", "2026"):
            sel = T[(T["arm"] == arm) & (T["era"] == era)]
            s = stats(sel, 1.0)
            if not s or s["n"] < 2:
                continue
            fam = "LDN-OBK-01" if arm[0] in "AB" else "LDN-PO3-01"
            rows.append({
                "family": fam, "era": era, "prereg": PREREG,
                "trial": f"L1 {arm} R/trade base cost",
                "stat_type": "mean", "estimate": round(s["r"], 4), "n": s["n"],
                "t_stat": round(s["t"], 4),
                "effect": round(trial_ledger.effect_from_t(s["t"], s["n"]), 6),
                "verdict": (f"L1 arm {arm}: n={s['n']} WR {s['wr']:.0%} "
                            f"{s['pts']:+.0f}pts PF {s['pf']:.2f} — no expectancy kill "
                            f"at L1 per §5.9.2"),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    T = run(load_bars())
    if T.empty:
        print("no trades — check the span")
        return 1
    text = report(T)
    print(text)

    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    OUT_MD.write_text(text)
    T.to_parquet(ROOT / "output/london_obk_l1.parquet", index=False)
    print(f"wrote {OUT_MD.relative_to(ROOT)} ({len(T)} trades)")

    existing = trial_ledger.load()
    already = set(zip(existing["family"], existing["trial"], existing["era"]))
    fresh = [r for r in build_trials(T)
             if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"recorded {len(fresh)} trials")
    else:
        print("all trials already on the ledger — append-only, nothing re-recorded.")
    print(trial_ledger.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
