#!/usr/bin/env python3
"""NYA-LVL-01 — raw uncapped trigger set for the level-interaction family.

Authorised by docs/PREREG-level-interaction.md, committed before this file. Stage 1
only: build every touch of every level on the fit span and report it raw. NO filters,
NO cuts, NO optimisation, NO arm selection (§5.9.1 — no bin decisions off raw).

Six levels, lookahead-clean, computed on NQ:
  PM_HIGH / PM_LOW / PM_50   04:00-09:15 ET, fixed 09:15 same day
  PD_HIGH / PD_LOW / PD_50   04:00-20:00 ET prior day, fixed prior 20:00

Entry arms   A = break-then-retest (15m body close back at level); B = raw touch.
Stop arms    S_LEVEL = 15m close beyond the level; S_FAR = 15m close beyond the far
             extreme of the level's own range.
Exit arms    T_LADDER (next level), T_SCALP (16.0 pts), T_TIME (30 min).

§2.5 fill realism: a touch entry is a resting limit, so it fills ONLY if the bar
trades >= 1 tick beyond the level. Touch-and-reverse is recorded unfilled.

    python -m scripts.nya_lvl_census [--dry-run]
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
PREREG = "docs/PREREG-level-interaction.md"
OUT_PARQUET = ROOT / "output/nya_lvl_census.parquet"
OUT_MD = ROOT / "output/nya_lvl_census.md"

# --- frozen in the prereg ---------------------------------------------------------
FIT_START, FIT_END = "2025-06-02", "2026-07-15"
PM_WINDOW = (4 * 60, 9 * 60 + 15)          # 04:00 -> 09:15 ET
PD_WINDOW = (4 * 60, 20 * 60)              # 04:00 -> 20:00 ET, prior day
RTH = (9 * 60 + 30, 16 * 60)               # 09:30 -> 16:00 ET
TICK = 0.25
T_SCALP = 16.0                             # pts, derived in the prereg
T_TIME = 30                                # minutes
RETEST_ATR_FRAC = 0.25                     # Version A: body close within 0.25 x 15m ATR
COSTS = ((1.0, "base"), (2.0, "strict"))
DOLLAR_RISK = 160.0
LEVELS = ["PM_HIGH", "PM_50", "PM_LOW", "PD_HIGH", "PD_50", "PD_LOW"]


def load_bars() -> pd.DataFrame:
    frames = [pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
              for p in ("data/reference/nq_1m_master.parquet",
                        "data/reference/nq_1m_feb_jul2026.parquet")]
    b = (pd.concat(frames, ignore_index=True).drop_duplicates("ts_event")
         .sort_values("ts_event").reset_index(drop=True))
    b["ts_event"] = pd.to_datetime(b["ts_event"])
    b["day"] = b["ts_event"].dt.strftime("%Y-%m-%d")
    b["min"] = b["ts_event"].dt.hour * 60 + b["ts_event"].dt.minute
    return b


def m15(day_bars: pd.DataFrame) -> pd.DataFrame:
    """Right-closed, right-labelled 15m bars: a bar labelled T holds data before T."""
    g = day_bars.set_index("ts_event").resample("15min", closed="left", label="right")
    return g.agg(open=("open", "first"), high=("high", "max"),
                 low=("low", "min"), close=("close", "last")).dropna()


def sim(direction: int, entry: float, stop_ref: float, target: float | None,
        bars: np.ndarray, checks: list[tuple[int, float]],
        max_min: int | None) -> tuple[float, str, float, float]:
    """As taught: the stop is a 15-MINUTE CLOSE beyond `stop_ref`, not a hard stop.

    Targets and MFE/MAE are evaluated every minute; the stop is evaluated only at
    15-minute boundaries, using that bar's close. Conservative on ties: at a boundary
    the stop is checked before the target for that minute.
    """
    mfe = mae = 0.0
    chk = {i: c for i, c in checks}
    for i, (hi, lo, cl) in enumerate(bars):
        up = (hi - entry) if direction > 0 else (entry - lo)
        dn = (lo - entry) if direction > 0 else (entry - hi)
        mfe, mae = max(mfe, up), min(mae, dn)
        if i in chk:
            c15 = chk[i]
            beyond = (c15 < stop_ref) if direction > 0 else (c15 > stop_ref)
            if beyond:
                return ((c15 - entry) if direction > 0 else (entry - c15)), "stop", mfe, mae
        if target is not None:
            if (direction > 0 and hi >= target) or (direction < 0 and lo <= target):
                return abs(target - entry), "target", mfe, mae
        if max_min is not None and (i + 1) >= max_min:
            return ((cl - entry) if direction > 0 else (entry - cl)), "time", mfe, mae
    cl = bars[-1][2]
    return ((cl - entry) if direction > 0 else (entry - cl)), "eod", mfe, mae


def next_level_target(lv: str, levels: dict, direction: int, entry: float) -> float | None:
    """His stated ladder: from a 50 target that range's extreme; else the next level."""
    ladder = {"PM_50": ("PM_HIGH", "PM_LOW"), "PD_50": ("PD_HIGH", "PD_LOW")}
    if lv in ladder:
        return levels[ladder[lv][0] if direction > 0 else ladder[lv][1]]
    cands = [v for v in levels.values()
             if (v > entry + TICK if direction > 0 else v < entry - TICK)]
    if not cands:
        return None
    return min(cands) if direction > 0 else max(cands)


def build(bars: pd.DataFrame) -> pd.DataFrame:
    days = sorted(bars["day"].unique())
    days = [d for d in days if FIT_START <= d <= FIT_END]
    prior: dict | None = None
    rows = []

    for di, day in enumerate(days):
        db = bars[bars["day"] == day]
        pm = db[(db["min"] >= PM_WINDOW[0]) & (db["min"] < PM_WINDOW[1])]
        pd_ = db[(db["min"] >= PD_WINDOW[0]) & (db["min"] < PD_WINDOW[1])]
        rth = db[(db["min"] >= RTH[0]) & (db["min"] < RTH[1])]

        if len(pm) >= 60 and len(rth) >= 200 and prior is not None:
            lv = {"PM_HIGH": float(pm["high"].max()), "PM_LOW": float(pm["low"].min()),
                  "PD_HIGH": prior["hi"], "PD_LOW": prior["lo"]}
            lv["PM_50"] = (lv["PM_HIGH"] + lv["PM_LOW"]) / 2
            lv["PD_50"] = (lv["PD_HIGH"] + lv["PD_LOW"]) / 2
            rows += day_events(day, rth, lv, prior)

        if len(pd_) >= 100:
            prior = {"hi": float(pd_["high"].max()), "lo": float(pd_["low"].min()),
                     "close": float(pd_.iloc[-1]["close"]), "day": day}
    return pd.DataFrame(rows)


def day_events(day: str, rth: pd.DataFrame, lv: dict, prior: dict) -> list[dict]:
    b15 = m15(rth)
    if len(b15) < 4:
        return []
    atr15 = float((b15["high"] - b15["low"]).median())
    rth_open = float(rth.iloc[0]["open"])
    gap = rth_open - prior["close"]
    arr = rth[["ts_event", "high", "low", "close"]].to_numpy(object)
    minute_bars = rth[["high", "low", "close"]].to_numpy(float)
    ts_index = list(rth["ts_event"])

    taps15: dict[str, int] = {k: 0 for k in LEVELS}
    taps1: dict[str, int] = {k: 0 for k in LEVELS}
    broken: dict[str, bool] = {k: False for k in LEVELS}
    out = []

    for bi in range(len(b15)):
        bar = b15.iloc[bi]
        bar_ts = b15.index[bi]
        prev_close = float(b15.iloc[bi - 1]["close"]) if bi else rth_open
        for name in LEVELS:
            level = lv[name]
            # break tracking must run on EVERY bar. Previously it was skipped on bars
            # that touched the level — which is most breaks — so Version A never armed.
            crossed = ((bar["close"] > level and prev_close < level) or
                       (bar["close"] < level and prev_close > level))
            touched = bar["low"] <= level <= bar["high"]
            if not touched:
                if crossed:
                    broken[name] = True
                continue
            taps15[name] += 1

            direction = -1 if prev_close < level else 1   # fade the approach
            # §2.5: a resting limit fills only if price trades THROUGH the level
            filled = bool(bar["high"] >= level + TICK and bar["low"] <= level - TICK) or \
                bool(direction < 0 and bar["high"] >= level + TICK) or \
                bool(direction > 0 and bar["low"] <= level - TICK)

            # Version A: break-then-retest — level must have been broken earlier, and
            # the 15m BODY must close back at the level
            body_at = abs(float(bar["close"]) - level) <= RETEST_ATR_FRAC * atr15
            ver_a = bool(broken[name] and body_at)

            start = next((i for i, t in enumerate(ts_index) if t > bar_ts), None)
            if start is None or start >= len(minute_bars) - 1:
                continue
            fwd = minute_bars[start:]
            # indices within `fwd` at which a 15m bar closes, with that close price
            checks = [(int((t - ts_index[start]).total_seconds() // 60), float(c))
                      for t, c in zip(b15.index[bi + 1:], b15["close"].iloc[bi + 1:])
                      if t > bar_ts]
            checks = [(i, c) for i, c in checks if 0 <= i < len(fwd)]

            rec = {
                "day": day, "era": day[:4],
                "half": day[:4] + ("H1" if int(day[5:7]) <= 6 else "H2"),
                "level_type": name, "level_px": level, "side": direction,
                "clock": bar_ts.strftime("%H:%M"),
                "minute_of_rth": int((bar_ts.hour * 60 + bar_ts.minute) - RTH[0]),
                "tap_15m": taps15[name], "tap_1m": taps1[name],
                "filled": filled, "version_a": ver_a,
                "dist_from_open": float(level - rth_open),
                "level_age_min": (int((bar_ts.hour * 60 + bar_ts.minute) - PM_WINDOW[1])
                                  if name.startswith("PM") else None),
                "gap_context": float(gap),
                "atr15": atr15,
            }
            # S_FAR must be the range extreme on the LOSING side of THIS trade.
            # For a fade at an outer level that extreme IS the entry, so S_FAR is
            # undefined there — recorded as NaN, never silently coerced.
            rng = ("PM_HIGH", "PM_LOW") if name.startswith("PM") else ("PD_HIGH", "PD_LOW")
            far_ref = lv[rng[1]] if direction > 0 else lv[rng[0]]
            stops = {"S_LEVEL": level}
            if (direction > 0 and far_ref < level - TICK) or \
               (direction < 0 and far_ref > level + TICK):
                stops["S_FAR"] = far_ref
            rec["S_FAR_defined"] = "S_FAR" in stops

            for sname, stop_ref in stops.items():
                # close-based stop -> risk is not known at entry. Declared proxy:
                # S_LEVEL uses the 15m ATR, S_FAR uses the distance to the extreme.
                risk = atr15 if sname == "S_LEVEL" else abs(level - stop_ref)
                if risk < 1.0:
                    continue
                rec[f"{sname}_risk"] = risk
                tgt_ladder = next_level_target(name, lv, direction, level)
                for tname, tgt, cap in (
                        ("T_LADDER", tgt_ladder, None),
                        ("T_SCALP", level + direction * T_SCALP, None),
                        ("T_TIME", None, T_TIME)):
                    if tname == "T_LADDER" and tgt is None:
                        continue
                    pts, why, mfe, mae = sim(direction, level, stop_ref, tgt,
                                             fwd, checks, cap)
                    rec[f"{sname}_{tname}_pts"] = pts
                    rec[f"{sname}_{tname}_why"] = why
                    if sname == "S_LEVEL" and tname == "T_SCALP":
                        rec["mfe"], rec["mae"] = mfe, mae
                        rec["realised_stop_pts"] = abs(pts) if why == "stop" else np.nan
                        for cp in (5, 15, 30):
                            if len(fwd) > cp:
                                rec[f"t{cp}"] = float((fwd[cp][2] - level) * direction)
            out.append(rec)
            if crossed:
                broken[name] = True
    return out


# --- reporting -------------------------------------------------------------------

def stats(T: pd.DataFrame, col: str, risk_col: str, cost: float) -> dict | None:
    s = T[T[col].notna() & T[risk_col].notna()]
    if s.empty:
        return None
    net = s[col] - cost
    r = net / s[risk_col]
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    return {"n": len(net), "wr": (net > 0).mean(), "pts": net.sum(),
            "usd": DOLLAR_RISK * r.sum(), "pf": gw / max(gl, 1e-9), "r": r.mean()}


def report(D: pd.DataFrame) -> tuple[str, list[dict]]:
    F = D[D["filled"]]
    ndays = D["day"].nunique()
    L = ["# NYA-LVL-01 — RAW UNCAPPED TRIGGER SET (stage 1)", "",
         f"Authorised by `{PREREG}`. **Raw. No filters, no cuts, no optimisation, no arm",
         "selection.** §5.9.1: no bin decision is ever made off the raw trigger set, and",
         "ugly raw is the expected shape at this stage.", "",
         f"Fit span {FIT_START} -> {FIT_END}. **{ndays} sessions. "
         f"{len(D):,} touches, {len(F):,} filled** "
         f"({len(F)/ndays:.1f} filled/session). Sealed 2023/24 NOT touched.", "",
         "## 1. Does the trade exist? (the only kill legal at this stage)", "",
         "| era | sessions | touches | filled | filled/session | vs floor of 2 |",
         "|---|---:|---:|---:|---:|---|"]
    ledger = []
    for era in sorted(D["era"].unique()):
        d, f = D[D["era"] == era], F[F["era"] == era]
        nd = d["day"].nunique()
        rate = len(f) / nd
        L.append(f"| {era} | {nd} | {len(d):,} | {len(f):,} | **{rate:.1f}** | "
                 f"{'PASS' if rate >= 2 else 'FAIL'} |")
        ledger.append({
            "family": "NYA-LVL-01", "era": era, "prereg": PREREG,
            "trial": "census filled touches per session",
            "stat_type": "mean", "estimate": round(rate, 3), "n": nd,
            "t_stat": 0.0, "effect": 0.0,
            "verdict": (f"raw census: {len(f)} filled touches over {nd} sessions "
                        f"({rate:.1f}/session); frequency is not an edge claim"),
        })
    L.append("")

    L += ["## 2. Where the touches are (level type — expected first discriminator)", "",
          "| level | touches | filled | fill rate | share |", "|---|---:|---:|---:|---:|"]
    for lv in LEVELS:
        d, f = D[D["level_type"] == lv], F[F["level_type"] == lv]
        L.append(f"| `{lv}` | {len(d):,} | {len(f):,} | {len(f)/max(len(d),1):.0%} | "
                 f"{len(f)/max(len(F),1):.0%} |")
    L.append("")

    L += ["## 3. RAW P&L — every arm, side by side, nothing selected", "",
          "Version B (raw touch), all filled events. `S_LEVEL` = 15m-close stop at the",
          "level scale; `S_FAR` = the original far-extreme stop.", ""]
    for cost, cl in COSTS:
        L += [f"**cost {cl} ({cost:.0f} pt)**", "",
              "| stop | target | n | WR | net pts | $ @160 risk | PF | R/trade |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
        for sname in ("S_LEVEL", "S_FAR"):
            for tname in ("T_LADDER", "T_SCALP", "T_TIME"):
                s = stats(F, f"{sname}_{tname}_pts", f"{sname}_risk", cost)
                if not s:
                    continue
                L.append(f"| {sname} | {tname} | {s['n']:,} | {s['wr']:.0%} | "
                         f"{s['pts']:+,.0f} | ${s['usd']:+,.0f} | {s['pf']:.2f} | "
                         f"{s['r']:+.3f} |")
                if cl == "base":
                    ledger.append({
                        "family": "NYA-LVL-01", "era": "fit", "prereg": PREREG,
                        "trial": f"raw {sname}/{tname} R per trade",
                        "stat_type": "mean", "estimate": round(s["r"], 4), "n": s["n"],
                        "t_stat": 0.0, "effect": 0.0,
                        "verdict": (f"RAW uncapped, no filters: n={s['n']} WR "
                                    f"{s['wr']:.0%} PF {s['pf']:.2f} {s['pts']:+.0f}pts "
                                    f"— no bin decision legal off this (§5.9.1)"),
                    })
        L.append("")

    L += ["**Realised stop distance (Angus: oversized stops are disqualifying)**", "",
          "| stop arm | median pts | p90 pts |", "|---|---:|---:|"]
    for sname in ("S_LEVEL", "S_FAR"):
        c = F[f"{sname}_risk"].dropna()
        if len(c):
            L.append(f"| {sname} | {c.median():.1f} | {c.quantile(.9):.1f} |")
    L.append("")

    L += ["## 4. Year-halves (§5.11-5 — pooling has hidden a bad half twice)", "",
          "`S_LEVEL` + `T_SCALP`, base cost.", "",
          "| half | n | WR | net pts | PF |", "|---|---:|---:|---:|---:|"]
    for h in sorted(F["half"].unique()):
        s = stats(F[F["half"] == h], "S_LEVEL_T_SCALP_pts", "S_LEVEL_risk", 1.0)
        if s:
            L.append(f"| {h} | {s['n']:,} | {s['wr']:.0%} | {s['pts']:+,.0f} | "
                     f"{s['pf']:.2f} |")
    L.append("")

    L += ["## 5. Per level type (`S_LEVEL` + `T_SCALP`, base cost)", "",
          "| level | n | WR | net pts | PF | R/trade |", "|---|---:|---:|---:|---:|---:|"]
    for lv in LEVELS:
        s = stats(F[F["level_type"] == lv], "S_LEVEL_T_SCALP_pts", "S_LEVEL_risk", 1.0)
        if s:
            L.append(f"| `{lv}` | {s['n']:,} | {s['wr']:.0%} | {s['pts']:+,.0f} | "
                     f"{s['pf']:.2f} | {s['r']:+.3f} |")
    L += ["", "**Reported, not acted on.** Level type is recorded from birth because Angus",
          "expects it to be the first discriminator — but selecting on it here would be",
          "a bin decision off the raw set, which §5.9.1 forbids.", ""]

    L += ["## 6. Version A (break-then-retest) — the other taught machine", "",
          "| | n | WR | net pts | PF |", "|---|---:|---:|---:|---:|"]
    for lbl, sel in (("Version B (raw touch)", F),
                     ("Version A (retest close)", F[F["version_a"]])):
        s = stats(sel, "S_LEVEL_T_SCALP_pts", "S_LEVEL_risk", 1.0)
        if s:
            L.append(f"| {lbl} | {s['n']:,} | {s['wr']:.0%} | {s['pts']:+,.0f} | "
                     f"{s['pf']:.2f} |")
    L.append("")

    L += ["## 7. Recorded but NOT applied — the variables for later stages", "",
          "| variable | recorded | note |", "|---|---|---|",
          "| time of day | `clock`, `minute_of_rth` | his opening-candle and ~11:00 rules are later arms |",
          "| tap number | `tap_15m` | his three-tap rule is a later arm |",
          "| level age | `level_age_min` | PM levels only |",
          "| gap context | `gap_context` | RTH open vs prior close |",
          "| distance from open | `dist_from_open` | |",
          "| in-trade path | `mfe`, `mae`, `t5`, `t15`, `t30` | §5.12-5 schema, from birth |", ""]
    return "\n".join(L), ledger


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    D = build(load_bars())
    if D.empty:
        print("no events")
        return 1
    text, ledger = report(D)
    print(text)
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    OUT_MD.write_text(text)
    D.to_parquet(OUT_PARQUET, index=False)
    print(f"wrote {OUT_MD.relative_to(ROOT)} ({len(D):,} events)")
    existing = trial_ledger.load()
    already = set(zip(existing["family"], existing["trial"], existing["era"]))
    fresh = [r for r in ledger if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"recorded {len(fresh)} trials")
    print(trial_ledger.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
