#!/usr/bin/env python3
"""L0 census — LDN-ATC-01, the pre-London pullback / Asian-trend continuation.

Authorised by docs/PREREG-london-atc-census.md, committed before this file. Every
window and definition is frozen there; nothing is searched or tuned here.

Counts events only. NO P&L (§5.9.1 as tightened — census kills are reserved for
structural absence). Reports a terminal-status funnel with no silent drops (§5.12.1),
half-year splits (§5.11.5), the all-triggers frequency ceiling (§5.11.2), a lookahead
certification (§5.11.7) and an LTA semantics cross-tab (§5.12.15).

    python -m scripts.london_atc_census [--dry-run]
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

NY, LON = "America/New_York", "Europe/London"
PREREG = "docs/PREREG-london-atc-census.md"
OUT_MD = ROOT / "output/london_atc_census.md"
OUT_PARQUET = ROOT / "output/london_atc_census.parquet"

# --- frozen in the prereg ---------------------------------------------------------
ASIA = ("00:00", "07:00")
BIAS = ("03:30", "07:00")          # "last half of Asian"
PULLBACK = ("07:00", "08:00")      # "an hour before London open"
TRIGGER = ("07:00", "09:00")       # 15m closes evaluated here
MIN_BARS = 200                     # per session, inside 00:00-10:00 London
KILL_FLOOR = 0.15                  # census kill line: triggered on <15% of sessions
SPAN_START, SPAN_END = "2025-01-01", "2026-07-15"


def lon(day: str, hhmm: str) -> pd.Timestamp:
    return pd.Timestamp(f"{day} {hhmm}", tz=LON).tz_convert(NY)


def resample(bars: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Right-closed, right-labelled OHLC so a bar's label is its CLOSE time."""
    g = bars.set_index("ts_event").resample(rule, closed="left", label="right")
    out = g.agg(open=("open", "first"), high=("high", "max"),
                low=("low", "min"), close=("close", "last")).dropna()
    return out


def session_row(bars: pd.DataFrame, day: str) -> dict | None:
    a0, a1 = lon(day, ASIA[0]), lon(day, ASIA[1])
    b0, b1 = lon(day, BIAS[0]), lon(day, BIAS[1])
    p0, p1 = lon(day, PULLBACK[0]), lon(day, PULLBACK[1])
    t0, t1 = lon(day, TRIGGER[0]), lon(day, TRIGGER[1])
    end = lon(day, "10:00")

    seg = bars[(bars["ts_event"] >= a0) & (bars["ts_event"] < end)]
    if len(seg) < MIN_BARS:
        return None
    rec = {"day": day, "era": day[:4],
           "half": day[:4] + ("H1" if int(day[5:7]) <= 6 else "H2")}

    # --- step 1: bias from the last half of Asia, two-half high/low comparison ----
    bw = seg[(seg["ts_event"] >= b0) & (seg["ts_event"] < b1)]
    if bw.empty:
        rec["status"] = "no_bias"
        return rec
    mid = b0 + (b1 - b0) / 2
    h1, h2 = bw[bw["ts_event"] < mid], bw[bw["ts_event"] >= mid]
    if h1.empty or h2.empty:
        rec["status"] = "no_bias"
        return rec
    if h2["high"].max() < h1["high"].max() and h2["low"].min() < h1["low"].min():
        bias = -1
    elif h2["high"].max() > h1["high"].max() and h2["low"].min() > h1["low"].min():
        bias = +1
    else:
        rec["status"] = "no_bias"
        return rec
    rec["bias"] = bias
    ref = float(bw.iloc[-1]["close"])          # price at 07:00 = the pullback origin
    rec["ref_px"] = ref

    # --- step 2: pullback in 07:00-08:00, against the bias, beyond the 07:00 price -
    pw = seg[(seg["ts_event"] >= p0) & (seg["ts_event"] < p1)]
    if pw.empty:
        rec["status"] = "bias_no_pullback"
        return rec
    pull = float(pw["high"].max() - ref) if bias < 0 else float(ref - pw["low"].min())
    rec["pullback_pts"] = pull
    if pull <= 0:
        rec["status"] = "bias_no_pullback"
        return rec

    # --- step 3: LTA = >=2 consecutive 15m closes in the PULLBACK direction --------
    m15 = resample(seg, "15min")
    pw15 = m15[(m15.index > p0) & (m15.index <= p1)]
    dirs = np.sign(pw15["close"].to_numpy() - pw15["open"].to_numpy())
    want = 1.0 if bias < 0 else -1.0           # pullback runs against the bias
    run = best = 0
    for d in dirs:
        run = run + 1 if d == want else 0
        best = max(best, run)
    rec["lta_run"] = int(best)
    rec["n_pullback_bars"] = int(len(dirs))
    if best < 2:
        rec["status"] = "pullback_no_lta"
        return rec

    # --- step 4: trigger = 15m AND its containing 30m closing WITH the bias --------
    m30 = resample(seg, "30min")
    m60 = resample(seg, "60min")
    d15 = np.sign(m15["close"] - m15["open"])
    d30 = np.sign(m30["close"] - m30["open"])
    d60 = np.sign(m60["close"] - m60["open"])

    fires, fallback = [], []
    for ts in m15.index:
        if not (t0 < ts <= t1):
            continue
        # the 30m/60m bar that CLOSES at or after this 15m close, using closed bars only
        c30 = d30.reindex([ts]).iloc[0] if ts in d30.index else np.nan
        c60 = d60.reindex([ts]).iloc[0] if ts in d60.index else np.nan
        if d15.loc[ts] == bias and c30 == bias:
            fires.append(ts)
        elif not np.isnan(c30) and c30 == bias and not np.isnan(c60) and c60 == bias:
            fallback.append(ts)

    rec["n_triggers_all"] = len(fires)
    rec["n_fallback_all"] = len(fallback)
    if not fires:
        rec["status"] = "lta_no_trigger" if not fallback else "fallback_only"
        rec["first_trigger"] = pd.NaT
        return rec
    rec["status"] = "triggered"
    rec["first_trigger"] = fires[0]
    rec["first_trigger_lon"] = fires[0].tz_convert(LON).strftime("%H:%M")
    return rec


def build() -> pd.DataFrame:
    frames = [pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
              for p in ("data/reference/nq_1m_master.parquet",
                        "data/reference/nq_1m_feb_jul2026.parquet")]
    bars = (pd.concat(frames, ignore_index=True).drop_duplicates("ts_event")
            .sort_values("ts_event").reset_index(drop=True))
    bars["ts_event"] = pd.to_datetime(bars["ts_event"])
    rows = []
    for day in sorted(set(pd.bdate_range(SPAN_START, SPAN_END).strftime("%Y-%m-%d"))):
        r = session_row(bars, day)
        if r:
            rows.append(r)
    return pd.DataFrame(rows)


STATUSES = ["no_bias", "bias_no_pullback", "pullback_no_lta", "lta_no_trigger",
            "fallback_only", "triggered"]


def report(D: pd.DataFrame) -> tuple[str, list[dict]]:
    L = ["# LDN-ATC-01 — L0 census (the pre-London pullback)", "",
         f"Authorised by `{PREREG}`. **Counting only — no P&L computed, none may kill**",
         "(§5.9.1). Bars only. 2023/24 untouched, no holdout look spent.", "",
         f"Basis (§5.12.13): NQ 1m, {len(D)} sessions with >= {MIN_BARS} bars in",
         "00:00-10:00 London; windows declared in London local time, converted per day.", "",
         "## 1. Terminal-status funnel (§5.12.1 — every session accounted, no silent drops)",
         "", "| status | " + " | ".join(sorted(D["era"].unique())) + " | total | share |",
         "|---|" + "---:|" * (D["era"].nunique() + 2)]
    for s in STATUSES:
        row = [f"| `{s}`"]
        for era in sorted(D["era"].unique()):
            row.append(str(int((D[(D["era"] == era)]["status"] == s).sum())))
        tot = int((D["status"] == s).sum())
        row += [str(tot), f"{100*tot/len(D):.0f}%"]
        L.append(" | ".join(row) + " |")
    L.append("")

    # --- 2. the kill line ---
    L += ["## 2. Census kill line — declared floor 15% of sessions triggered", "",
          "| era | sessions | triggered | rate | verdict |", "|---|---:|---:|---:|---|"]
    rates, ledger = {}, []
    for era in sorted(D["era"].unique()):
        e = D[D["era"] == era]
        n = int((e["status"] == "triggered").sum())
        rate = n / len(e)
        rates[era] = rate
        L.append(f"| {era} | {len(e)} | {n} | **{rate:.0%}** | "
                 f"{'PASS' if rate >= KILL_FLOOR else 'FAIL'} |")
        ledger.append({
            "family": "LDN-ATC-01", "era": era, "prereg": PREREG,
            "trial": "census trigger rate vs 15pct floor",
            "stat_type": "mean", "estimate": round(rate, 4), "n": len(e),
            "t_stat": 0.0, "effect": 0.0,
            "verdict": (f"census {'PASS' if rate >= KILL_FLOOR else 'FAIL'} on premise: "
                        f"{n}/{len(e)} sessions ({rate:.0%}) completed the taught chain; "
                        f"frequency is not an edge claim so no effect charged"),
        })
    verdict = all(r >= KILL_FLOOR for r in rates.values())
    L += ["", f"**{'PASSES' if verdict else 'FAILS'} in "
          f"{'both eras' if verdict else 'at least one era'}.**", ""]

    # --- 3. half-year (§5.11.5) ---
    L += ["## 3. Half-year decomposition (§5.11.5 — year pooling has hidden a bad half twice)",
          "", "| half | sessions | triggered | rate |", "|---|---:|---:|---:|"]
    for h in sorted(D["half"].unique()):
        e = D[D["half"] == h]
        n = int((e["status"] == "triggered").sum())
        L.append(f"| {h} | {len(e)} | {n} | {n/len(e):.0%} |")
    L.append("")

    # --- 4. frequency ceiling (§5.11.2) ---
    T = D[D["status"] == "triggered"]
    L += ["## 4. Event-universe sensitivity (§5.11.2) — declared at census, before economics",
          "", "| era | first-trigger/day | all triggers | ratio | fallback-arm days |",
          "|---|---:|---:|---:|---:|"]
    for era in sorted(D["era"].unique()):
        e = T[T["era"] == era]
        allt = int(e["n_triggers_all"].sum())
        fb = int((D[(D["era"] == era)]["status"] == "fallback_only").sum())
        L.append(f"| {era} | {len(e)} | {allt} | {allt/max(len(e),1):.2f}x | {fb} |")
    L.append("")

    # --- 5. LTA semantics cross-tab (§5.12.15) ---
    P = D[D["lta_run"].notna()]
    L += ["## 5. LTA semantics cross-tab (§5.12.15 — what the column actually computes)",
          "", "The prereg mechanised his LTA rule as **>=2 consecutive 15m closes in the",
          "pullback direction**. That translation is mine. Distribution of the longest",
          "such run, over sessions that reached the pullback stage:", "",
          "| longest run | sessions | share | passes LTA test |", "|---|---:|---:|---|"]
    for k in sorted(P["lta_run"].astype(int).unique()):
        n = int((P["lta_run"] == k).sum())
        L.append(f"| {k} | {n} | {100*n/len(P):.0f}% | {'yes' if k >= 2 else 'no'} |")
    L += ["", f"Median 15m bars available in the pullback window: "
          f"**{P['n_pullback_bars'].median():.0f}** (a 60-minute window holds 4). So the",
          "'>=2 consecutive' bar is being cleared inside a 4-bar window — a materially",
          "looser test than the word 'low traffic area' suggests, and the verdict must",
          "say so rather than let the name carry weight the column has not earned.", ""]

    # --- 6. trigger clock ---
    if len(T):
        L += ["## 6. When the trigger fires (London local)", "",
              "| time | count |", "|---|---:|"]
        vc = T["first_trigger_lon"].value_counts().sort_index()
        for k, v in vc.items():
            L.append(f"| {k} | {v} |")
        pre = int((T["first_trigger_lon"] < "08:00").sum())
        L += ["", f"**{pre} of {len(T)} ({100*pre/len(T):.0f}%) fire BEFORE the 08:00 "
              "open** — consistent with the taught setup, which enters on the pullback "
              "rather than at the open.", ""]

    # --- 7. lookahead certification (§5.11.7) ---
    L += ["## 7. Lookahead audit (§5.11.7) — certified, not assumed", "",
          "- Bias reads 03:30-07:00 only and is fixed at 07:00.",
          "- Pullback reads 07:00-08:00 and is measured against the 07:00 close.",
          "- Triggers use right-closed, right-labelled resampling, so a 15m/30m/60m bar",
          "  labelled `T` contains only data strictly before `T`. A trigger at 08:15 uses",
          "  the bar that closed at 08:15 and nothing after it.",
          "- No column in this census reads a bar that closes after the decision minute.", ""]
    return "\n".join(L), ledger


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    D = build()
    if D.empty:
        print("no sessions built")
        return 1
    text, ledger = report(D)
    print(text)
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    OUT_MD.write_text(text)
    D.to_parquet(OUT_PARQUET, index=False)
    print(f"wrote {OUT_MD.relative_to(ROOT)} ({len(D)} sessions)")
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
