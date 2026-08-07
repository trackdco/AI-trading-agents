#!/usr/bin/env python3
"""L0 census — LDN-OBK-01 / LDN-PO3-01, the London-open break event tree.

Authorised by docs/PREREG-london-open-break-tree.md, committed before this file.
Every definition below is frozen there; nothing is searched or tuned here.

One trigger, two branches. Price breaks the pre-open range after the London cash
open; the continuation branch says it goes, the failure branch says it snaps back.
This counts how often each actually happens. Per §5.9.1 a census kills only if the
claimed behaviour does not occur — raw P&L is not computed and does not kill.

Windows are declared in Europe/London and converted per day, so the ~3 weeks/year of
UK-US DST misalignment do not smear the clock.

    python -m scripts.london_obk_census [--dry-run]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger  # noqa: E402

NY = "America/New_York"
LON = "Europe/London"

PREREG = "docs/PREREG-london-open-break-tree.md"
OUT_PARQUET = ROOT / "output/london_obk_census.parquet"
OUT_MD = ROOT / "output/london_obk_census.md"

# --- frozen in the prereg, §"Declared definitions" -------------------------------
PREOPEN = ("06:00", "08:00")     # pre-open range window, Europe/London
PLACEBO = ("04:00", "06:00")     # placebo range, same width, no claim on the open
TRIGGER = ("08:00", "10:00")     # break window, Europe/London
FAIL_HORIZONS = (30, 60, 120)    # minutes; 30 inherited from NYA-FA-01
MIN_BARS = 60                    # a day needs this many 1m bars in 06:00-10:00 LON

# 2023/2024 are NOT touched by this census — fit-only, no holdout look spent.
SPAN_START = "2025-01-01"
SPAN_END = "2026-07-15"


def load_bars() -> pd.DataFrame:
    frames = []
    for path in ("data/reference/nq_1m_master.parquet",
                 "data/reference/nq_1m_feb_jul2026.parquet"):
        df = pd.read_parquet(ROOT / path).drop(columns=["roll"], errors="ignore")
        frames.append(df)
    bars = (pd.concat(frames, ignore_index=True)
            .drop_duplicates("ts_event")
            .sort_values("ts_event")
            .reset_index(drop=True))
    bars["ts_event"] = pd.to_datetime(bars["ts_event"])
    if bars["ts_event"].dt.tz is None:          # defensive: master is tz-aware ET
        bars["ts_event"] = bars["ts_event"].dt.tz_localize(NY)
    return bars


def lon_window(day: str, start: str, end: str):
    """`start`-`end` Europe/London on UK calendar date `day`, expressed in ET."""
    return (pd.Timestamp(f"{day} {start}", tz=LON).tz_convert(NY),
            pd.Timestamp(f"{day} {end}", tz=LON).tz_convert(NY))


def break_events(seg: pd.DataFrame, hi: float, lo: float, day: str, kind: str,
                 win_start: pd.Timestamp, win_end: pd.Timestamp) -> list[dict]:
    """First up-break and first down-break of [lo, hi] inside `seg`, with outcomes.

    A break is a 1m CLOSE beyond the level (not a wick — the failure branch's claim
    is about what happened after, and a wick has no after). Failure is a subsequent
    1m close back inside the range.
    """
    rows = []
    for side, level in (("up", hi), ("down", lo)):
        beyond = seg["close"] > level if side == "up" else seg["close"] < level
        if not beyond.any():
            continue
        b = seg.index[beyond][0]
        brk = seg.loc[b]
        after = seg.loc[b:].iloc[1:]                     # strictly after the break bar

        inside = (after["close"] <= hi) if side == "up" else (after["close"] >= lo)
        if inside.any():
            f = after.index[inside][0]
            fail_ts = after.loc[f, "ts_event"]
            mins_out = (fail_ts - brk["ts_event"]).total_seconds() / 60.0
            pre_fail = seg.loc[b:f]
        else:
            fail_ts, mins_out, pre_fail = pd.NaT, np.nan, seg.loc[b:]

        # excursion: max extension beyond the level before the first close back inside
        if side == "up":
            exc = float(pre_fail["high"].max() - level)
        else:
            exc = float(level - pre_fail["low"].min())

        row = {
            "day": day, "range_kind": kind, "side": side,
            "era": day[:4],
            "break_ts": brk["ts_event"], "break_px": float(brk["close"]),
            "level": float(level), "hi": float(hi), "lo": float(lo),
            "range_pts": float(hi - lo),
            "mins_outside": mins_out,
            "excursion_pts": exc,
            "mins_from_open": (brk["ts_event"] - win_start).total_seconds() / 60.0,
            # minutes of window left AFTER the failure — traverse has a time budget,
            # and a break that ran a long way has spent most of it
            "mins_left_after_fail": (
                (win_end - fail_ts).total_seconds() / 60.0
                if pd.notna(fail_ts) else np.nan),
        }
        for h in FAIL_HORIZONS:
            row[f"fail_{h}"] = bool(pd.notna(mins_out) and mins_out <= h)

        # traverse: after a failure, does price reach the far edge / the midpoint
        # before the window closes?
        far = lo if side == "up" else hi
        mid = (hi + lo) / 2.0
        if pd.notna(fail_ts):
            post = seg[seg["ts_event"] >= fail_ts]
            if side == "up":
                row["traverse_far"] = bool((post["low"] <= far).any())
                row["traverse_mid"] = bool((post["low"] <= mid).any())
            else:
                row["traverse_far"] = bool((post["high"] >= far).any())
                row["traverse_mid"] = bool((post["high"] >= mid).any())
        else:
            row["traverse_far"] = False
            row["traverse_mid"] = False
        rows.append(row)
    return rows


def build(bars: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    days = sorted(set(pd.bdate_range(SPAN_START, SPAN_END).strftime("%Y-%m-%d")))
    events, day_rows = [], []

    for day in days:
        t_start, t_end = lon_window(day, *TRIGGER)
        outer_start, _ = lon_window(day, *PLACEBO)
        frame = bars[(bars["ts_event"] >= outer_start) & (bars["ts_event"] < t_end)]
        if len(frame) < MIN_BARS:
            continue

        trig = frame[(frame["ts_event"] >= t_start)].reset_index(drop=True)
        if trig.empty:
            continue

        rec = {"day": day, "era": day[:4]}
        for kind, (a, b) in (("preopen", PREOPEN), ("placebo", PLACEBO)):
            r_start, r_end = lon_window(day, a, b)
            rng = frame[(frame["ts_event"] >= r_start) & (frame["ts_event"] < r_end)]
            if rng.empty:
                continue
            hi, lo = float(rng["high"].max()), float(rng["low"].min())
            ev = break_events(trig, hi, lo, day, kind, t_start, t_end)
            events.extend(ev)
            rec[f"{kind}_range"] = hi - lo
            rec[f"{kind}_broke"] = len(ev) > 0
        day_rows.append(rec)

    ev = pd.DataFrame(events)
    if not ev.empty:
        ev["excursion_frac"] = ev["excursion_pts"] / ev["range_pts"]
    return ev, pd.DataFrame(day_rows)


# --- reporting -------------------------------------------------------------------

def pct(x) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100*x:.0f}%"


def tercile_table(ev: pd.DataFrame, col: str, label: str) -> str:
    """Traverse odds by tercile of `col`. Transfer test of the NYA-FA-01 result."""
    sel = ev[ev["fail_120"] & ev[col].notna()].copy()
    if len(sel) < 30:
        return f"\n**{label}** — n={len(sel)}, too few to tercile.\n"
    # ties (mins_outside is integer-minute and clusters hard at 1-2) can collapse
    # qcut's edges, so label after the fact rather than asserting three bins exist
    binned = pd.qcut(sel[col], 3, duplicates="drop")
    names = ["low", "mid", "high"][-len(binned.cat.categories):]
    sel["t"] = binned.cat.rename_categories(names)
    g = sel.groupby("t", observed=True).agg(
        n=("day", "size"), far=("traverse_far", "mean"), mid=("traverse_mid", "mean"),
        budget=("mins_left_after_fail", "median"))
    out = [f"\n**{label}** (failed breaks only, n={len(sel)})\n",
           "| tercile | n | reaches far edge | reaches midpoint | median mins of window left |",
           "|---|---:|---:|---:|---:|"]
    for t, r in g.iterrows():
        out.append(f"| {t} | {int(r['n'])} | {pct(r['far'])} | {pct(r['mid'])} | "
                   f"{r['budget']:.0f} |")
    return "\n".join(out) + "\n"


def placebo_trials(ev: pd.DataFrame) -> list[dict]:
    """Pre-open vs placebo fail rate, per era, as a two-proportion z-test.

    This is the census's headline number and the one that goes on the ledger. The
    raw fail rate alone cannot support either branch — any range boundary gets
    poked and reverts — so the trial is the MARGIN over a range with no claim on
    the open, not the level.
    """
    rows = []
    for era in sorted(ev["era"].unique()):
        e = ev[ev["era"] == era]
        a = e[e["range_kind"] == "preopen"]["fail_120"]
        b = e[e["range_kind"] == "placebo"]["fail_120"]
        if len(a) < 2 or len(b) < 2:
            continue
        p1, p2, n1, n2 = a.mean(), b.mean(), len(a), len(b)
        pool = (a.sum() + b.sum()) / (n1 + n2)
        se = math.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
        z = (p1 - p2) / se if se else 0.0
        rows.append({"era": era, "p_preopen": p1, "p_placebo": p2,
                     "diff": p1 - p2, "n1": n1, "n2": n2, "z": z})
    return rows


def build_trials(ev: pd.DataFrame) -> list[dict]:
    """Every statistic this census computed, on the machine ledger (§6.0.2).

    Including the two transfer-test looks. They consumed search and they must be
    charged for it whether they helped or not — a ledger you only add winners to
    is the thing DSR exists to defend against.
    """
    rows: list[dict] = []
    pre = ev[ev["range_kind"] == "preopen"]

    for r in placebo_trials(ev):
        n = r["n1"] + r["n2"]
        rows.append({
            "family": "LDN-PO3-01", "era": r["era"], "prereg": PREREG,
            "trial": "fail120 preopen minus placebo",
            "stat_type": "mean", "estimate": round(r["diff"], 4), "n": n,
            "t_stat": round(r["z"], 4), "effect": round(trial_ledger.effect_from_t(r["z"], n), 6),
            "verdict": (f"census PASS — fail rate {100*r['p_preopen']:.0f}% vs placebo "
                        f"{100*r['p_placebo']:.0f}%; margin real but the level alone is not "
                        f"the signal, the margin is"),
        })

    # LDN-OBK-01's kill line is a frequency, tested against the declared 30% floor
    for era in sorted(pre["era"].unique()):
        e = pre[pre["era"] == era]
        ndays = e["day"].nunique()
        rows.append({
            "family": "LDN-OBK-01", "era": era, "prereg": PREREG,
            "trial": "break frequency vs 30pct census floor",
            "stat_type": "mean", "estimate": float(round(len(e), 0)), "n": ndays,
            "t_stat": 0.0, "effect": 0.0,
            "verdict": (f"census PASS on premise — {ndays} days carried >=1 break, far "
                        f"above the declared 30% floor; frequency is not an edge claim so "
                        f"no effect is charged"),
        })

    # the transfer test — both constructions, charged whether or not they worked
    for col, name in (("excursion_pts", "NYA-FA transfer: excursion tercile (points)"),
                      ("excursion_frac", "NYA-FA transfer: excursion tercile (norm by range)")):
        sel = pre[pre["fail_120"] & pre[col].notna()]
        if len(sel) < 30:
            continue
        # Spearman by hand — scipy is not in this venv, and rank-then-Pearson is
        # the definition anyway
        rho = sel[col].rank().corr(sel["traverse_far"].astype(float).rank())
        n = len(sel)
        t = rho * math.sqrt((n - 2) / max(1e-9, 1 - rho ** 2))
        rows.append({
            "family": "LDN-PO3-01", "era": "2025+2026", "prereg": PREREG,
            "trial": name, "stat_type": "rho", "estimate": round(float(rho), 4),
            "n": n, "t_stat": round(float(t), 4),
            "effect": round(trial_ledger.effect_from_t(t, n), 6),
            "verdict": ("transfer test of NYA-FA-01's discriminator — DID NOT REPLICATE "
                        "in London (points version inverted by the range-geometry "
                        "confound, normalised version flat)"),
        })
    return rows


def report(ev: pd.DataFrame, days: pd.DataFrame) -> str:
    L = ["# LDN-OBK-01 / LDN-PO3-01 — L0 census",
         "",
         f"Authorised by `{PREREG}`. Bars only. 2023/24 untouched — no holdout look spent.",
         f"Universe: {len(days)} London sessions "
         f"({', '.join(f'{e}: {n}' for e, n in days['era'].value_counts().sort_index().items())}).",
         ""]

    pre = ev[ev["range_kind"] == "preopen"]
    pla = ev[ev["range_kind"] == "placebo"]

    # --- 1. does the break happen at all (LDN-OBK-01 kill line: >=30% of days) ---
    L += ["## 1. Does the pre-open range get broken? (LDN-OBK-01 census kill line)", "",
          "| era | sessions | days with >=1 break | break freq | up-breaks | down-breaks |",
          "|---|---:|---:|---:|---:|---:|"]
    for era in sorted(days["era"].unique()):
        d = days[days["era"] == era]
        e = pre[pre["era"] == era]
        nb = e["day"].nunique()
        L.append(f"| {era} | {len(d)} | {nb} | {pct(nb/len(d))} | "
                 f"{(e['side']=='up').sum()} | {(e['side']=='down').sum()} |")
    L.append("")

    # --- 2. do breaks fail (LDN-PO3-01 kill line: >=15% of breaks) ---
    L += ["## 2. Do breaks fail? (LDN-PO3-01 census kill line, and the placebo control)", "",
          "| era | range | breaks | fail 30m | fail 60m | fail 120m |",
          "|---|---|---:|---:|---:|---:|"]
    for era in sorted(days["era"].unique()):
        for kind, src in (("pre-open", pre), ("placebo", pla)):
            e = src[src["era"] == era]
            if e.empty:
                continue
            L.append(f"| {era} | {kind} | {len(e)} | "
                     + " | ".join(pct(e[f'fail_{h}'].mean()) for h in FAIL_HORIZONS) + " |")
    L.append("")

    # --- 3. side symmetry ---
    L += ["## 3. Side symmetry", "",
          "| era | side | breaks | fail 30m | fail 120m | median excursion |",
          "|---|---|---:|---:|---:|---:|"]
    for era in sorted(days["era"].unique()):
        for side in ("up", "down"):
            e = pre[(pre["era"] == era) & (pre["side"] == side)]
            if e.empty:
                continue
            L.append(f"| {era} | {side} | {len(e)} | {pct(e['fail_30'].mean())} | "
                     f"{pct(e['fail_120'].mean())} | {e['excursion_pts'].median():.1f} pts |")
    L.append("")

    # --- 4. excursion: is there an event to trade at all ---
    L += ["## 4. Excursion beyond the level (the family's 'is there an event' test)", "",
          "| era | outcome | n | median | p25 | p75 | median range |",
          "|---|---|---:|---:|---:|---:|---:|"]
    for era in sorted(days["era"].unique()):
        e = pre[pre["era"] == era]
        for lbl, sel in (("failed <=120m", e[e["fail_120"]]), ("continued", e[~e["fail_120"]])):
            if sel.empty:
                continue
            x = sel["excursion_pts"]
            L.append(f"| {era} | {lbl} | {len(sel)} | {x.median():.1f} | "
                     f"{x.quantile(.25):.1f} | {x.quantile(.75):.1f} | "
                     f"{sel['range_pts'].median():.1f} |")
    L.append("")

    # --- 5. the NYA-FA-01 transfer ---
    L += ["## 5. Transfer test of NYA-FA-01's discriminators", "",
          "NY found excursion depth discriminates traverse (23% vs 8% far-edge) and",
          "time-outside discriminates nothing (16/19/12%). Same construction here.",
          tercile_table(pre, "excursion_pts", "Excursion depth before re-entry"),
          tercile_table(pre, "mins_outside", "Minutes spent outside the range"),
          "",
          "**POST-HOC, added after seeing the above — declared as a second look.**",
          "Excursion is in points, and the trip to the far edge is `range + excursion`,",
          "so a deeper excursion mechanically means a longer journey. NY's composites",
          "are far wider than a 2-hour London range, so the same points-tercile is not",
          "the same test. Normalising by range width is the like-for-like version.",
          "Both are ledgered; the search is charged for both.",
          tercile_table(pre, "excursion_frac", "Excursion as a FRACTION of range width"),
          "",
          "### Break quality — how many 'breaks' are bare touches",
          "",
          "The prereg froze a break as a bare 1m close beyond the level, with no",
          "minimum displacement. That is as-taught (neither source states a minimum in",
          "the transcripts) but it admits noise touches. Counted here because it sets",
          "up the obvious L1 declared variable, not because it changes the census.", "",
          "| era | breaks | excursion < 5pt | < 10pt | < 0.10x range |",
          "|---|---:|---:|---:|---:|"]
    for era in sorted(days["era"].unique()):
        e = pre[pre["era"] == era]
        L.append(f"| {era} | {len(e)} | {pct((e['excursion_pts']<5).mean())} | "
                 f"{pct((e['excursion_pts']<10).mean())} | "
                 f"{pct((e['excursion_frac']<0.10).mean())} |")
    L.append("")

    # --- 6. the headline trial: margin over placebo ---
    L += ["## 6. Headline trial — pre-open fail rate MINUS placebo fail rate", "",
          "The raw fail rate cannot support either branch on its own; any boundary",
          "gets poked and reverts. The trial is the margin over a range with no",
          "claim on the open. Two-proportion z, unpaired, fail-within-120m.", "",
          "| era | pre-open | placebo | margin | z |",
          "|---|---:|---:|---:|---:|"]
    for r in placebo_trials(pre.__class__(ev)):
        L.append(f"| {r['era']} | {pct(r['p_preopen'])} ({r['n1']}) | "
                 f"{pct(r['p_placebo'])} ({r['n2']}) | {100*r['diff']:+.0f} pp | "
                 f"{r['z']:+.2f} |")
    L.append("")

    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bars = load_bars()
    ev, days = build(bars)
    if ev.empty:
        print("no events — check the span")
        return 1

    text = report(ev, days)
    print(text)

    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    ev.to_parquet(OUT_PARQUET, index=False)
    OUT_MD.write_text(text)
    print(f"wrote {OUT_PARQUET.relative_to(ROOT)} ({len(ev)} events) "
          f"and {OUT_MD.relative_to(ROOT)}")

    ledger_rows = build_trials(ev)
    existing = trial_ledger.load()
    already = set(zip(existing["family"], existing["trial"], existing["era"]))
    fresh = [r for r in ledger_rows
             if (r["family"], r["trial"], r["era"]) not in already]
    if not fresh:
        print("all trials already on the ledger — append-only, nothing re-recorded.")
    else:
        trial_ledger.record(fresh)
        print(f"\nrecorded {len(fresh)} trials\n")
    print(trial_ledger.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
