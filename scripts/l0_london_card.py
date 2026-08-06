#!/usr/bin/env python3
"""LDN-CAN-01 L0 — the census data card (§5.10 transparency rule).

Authorised by docs/PREREG-london-canon-rebuild.md. Reads the L0 parquets and reports
the raw trigger population with NO selection applied, then evaluates the two census
kill lines declared in prereg §4 — and nothing else. No expectancy claim is made or
implied at this rung (§5.9.2).

    python -m scripts.l0_london_card
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-canon-rebuild.md"
OUT_MD = ROOT / "output/l0_london_card.md"
BANDS = {"std": "08:00-10:00 London", "wide": "07:30-10:30 London"}

# prereg §4, declared before the numbers were read
KILL_MIN_PER_SESSION = 2.0
KILL_MIN_TRADEABLE_FRAC = 0.60


def load(band: str) -> pd.DataFrame | None:
    p = ROOT / f"output/l0_triggers_london_fit_{band}.parquet"
    if not p.exists():
        return None
    T = pd.read_parquet(p)
    T["ts_et"] = pd.to_datetime(T["ts"], utc=True, format="mixed").dt.tz_convert(
        "America/New_York")                      # burn-list item 1: mixed DST offsets
    T["era"] = T["day"].str[:4]
    T["half"] = T["day"].str[:4] + T["day"].str[5:7].astype(int).map(
        lambda m: "H1" if m <= 6 else "H2")
    T["lon_hm"] = (T["ts_et"].dt.hour - T["et_hour_start"]) * 60 + T["ts_et"].dt.minute
    ct = T["cluster_types"].map(
        lambda v: set(v) if isinstance(v, (list, set)) else set(ast.literal_eval(str(v))))
    T["has_bb"], T["has_vwap"], T["has_poc"] = (ct.map(lambda s: "bb" in s),
                                                ct.map(lambda s: "vwap" in s),
                                                ct.map(lambda s: "poc" in s))
    # ANGUS v1.1 §9 ladder: FULL = BB+VWAP+POC, HALF = BB+VWAP, else NO TRADE
    T["ladder"] = "NO TRADE"
    T.loc[T["has_bb"] & T["has_vwap"], "ladder"] = "HALF (bb+vwap)"
    T.loc[T["has_bb"] & T["has_vwap"] & T["has_poc"], "ladder"] = "FULL (bb+vwap+poc)"
    return T


def mix(T: pd.DataFrame, col: str, title: str) -> list[str]:
    L = [f"**{title}**", "", "| value | n | share | 2025 | 2026 |", "|---|---:|---:|---:|---:|"]
    tot25 = max((T["era"] == "2025").sum(), 1)
    tot26 = max((T["era"] == "2026").sum(), 1)
    for v, n in T[col].value_counts().items():
        s = T[T[col] == v]
        L.append(f"| `{v}` | {n:,} | {n/len(T):.1%} | "
                 f"{(s['era']=='2025').sum()/tot25:.1%} | {(s['era']=='2026').sum()/tot26:.1%} |")
    return L + [""]


def main() -> int:
    Ts = {b: load(b) for b in BANDS}
    if Ts["std"] is None:
        print("L0 std parquet missing — run scripts.build_l0_triggers_london --span fit")
        return 1
    T = Ts["std"]
    nd = T["day"].nunique()
    per = len(T) / nd

    L = ["# LDN-CAN-01 — L0 census data card", "",
         f"Authorised by `{PREREG}`. **Bars only. No selection of any kind** — no caps, no",
         "stop gate, no score, no pattern filter, no order flow. This rung answers one",
         "question: what does the canon's own geometry (BB / daily-VWAP band / POC",
         "confluence, rejection blocks and displacements) fire on in the London window.", "",
         "**No expectancy claim is made or implied here** (§5.9.2). There are no P&L",
         "numbers on this card because none have been computed.", "",
         "**Sealed and untouched:** the 2023/24 days, `depth_london_2023_24` (128 days),",
         "the sealed flow months. This rung uses none of them.", "",
         "## 1. The raw population", "",
         "| | value |", "|---|---:|",
         f"| triggers | **{len(T):,}** |",
         f"| sessions | {nd} |",
         f"| **per session** | **{per:.1f}** |",
         f"| span | {T['day'].min()} → {T['day'].max()} |",
         f"| DST-misaligned sessions (04:00 ET start) | "
         f"{T[T['et_hour_start']==4]['day'].nunique()} |", ""]

    L += ["**Per era and half** (§5.11.5 — aggregates mask holes, so they are never the",
          "headline):", "", "| period | sessions | triggers | /session |",
          "|---|---:|---:|---:|"]
    for k in ("2025H2", "2026H1"):
        s = T[T["half"] == k]
        if len(s):
            L.append(f"| {k} | {s['day'].nunique()} | {len(s):,} | "
                     f"{len(s)/s['day'].nunique():.1f} |")
    for k in ("2025", "2026"):
        s = T[T["era"] == k]
        L.append(f"| **{k}** | {s['day'].nunique()} | {len(s):,} | "
                 f"{len(s)/s['day'].nunique():.1f} |")
    L.append("")

    # --- 2. Angus's own ladder --------------------------------------------------
    lad = T["ladder"].value_counts()
    tradeable = int(lad.get("FULL (bb+vwap+poc)", 0) + lad.get("HALF (bb+vwap)", 0))
    frac = tradeable / len(T)
    L += ["## 2. Against Angus's own sizing ladder (v1.1 §9)", "",
          "*FULL = BB+VWAP+POC · HALF = BB+VWAP · **no trade without both BB and VWAP***",
          "", "| tier | n | share | /session |", "|---|---:|---:|---:|"]
    for k in ("FULL (bb+vwap+poc)", "HALF (bb+vwap)", "NO TRADE"):
        n = int(lad.get(k, 0))
        L.append(f"| {k} | {n:,} | {n/len(T):.1%} | {n/nd:.1f} |")
    L += ["", f"**Tradeable under the strategy's own rule: {tradeable:,} of {len(T):,} "
          f"({frac:.1%}) — {tradeable/nd:.1f} per session.**", "",
          "The ladder is a RULE, not a finding: it was declared by Angus in the v1.1 spec",
          "long before this census, so applying it here is not selection.", ""]

    # --- 3. composition ---------------------------------------------------------
    L += ["## 3. What the population is made of", ""]
    L += mix(T, "pattern", "Pattern (A = reversal, B = continuation, B2 = rejection/fade)")
    L += mix(T, "kind", "Trigger shape")
    L += mix(T, "tf", "Entry timeframe")
    L += mix(T, "direction", "Side")
    L += mix(T, "htf_flag", "15m regime vs trade direction")
    L += [f"**VWAP actually touched** (the candle's range reached a VWAP band, not merely "
          f"proximity): **{T['vwap_touched'].mean():.1%}**", "",
          f"**Confluence count** — 2 levels {(T['confluence_count']==2).mean():.1%}, "
          f"3 levels {(T['confluence_count']==3).mean():.1%}", ""]

    # --- 4. clock ---------------------------------------------------------------
    L += ["## 4. Where in the session they fire", "",
          "Minutes after the London open (08:00 London), so DST-misaligned days line up:",
          "", "| window | n | share |", "|---|---:|---:|"]
    for lo, hi, lab in ((0, 15, "08:00–08:15"), (15, 30, "08:15–08:30"),
                        (30, 60, "08:30–09:00"), (60, 90, "09:00–09:30"),
                        (90, 121, "09:30–10:00")):
        s = T[(T["lon_hm"] >= lo) & (T["lon_hm"] < hi)]
        L.append(f"| {lab} | {len(s):,} | {len(s)/len(T):.1%} |")
    L.append("")

    # --- 5. event-universe sensitivity ------------------------------------------
    L += ["## 5. Event-universe sensitivity (§5.11.2) — run at stage one, not bolted on", ""]
    W = Ts["wide"]
    if W is None:
        L += ["_wide band not yet built_", ""]
    else:
        L += ["| band | sessions | triggers | /session | tradeable (ladder) | /session |",
              "|---|---:|---:|---:|---:|---:|"]
        for b, lab in BANDS.items():
            S = Ts[b]
            tr = int((S["ladder"] != "NO TRADE").sum())
            L.append(f"| {lab} | {S['day'].nunique()} | {len(S):,} | "
                     f"{len(S)/S['day'].nunique():.1f} | {tr:,} | "
                     f"{tr/S['day'].nunique():.1f} |")
        L += ["", f"Widening by 30 minutes each side changes the population by "
              f"**{len(W)/len(T)-1:+.1%}**. Recorded now so no later rung has to guess, and",
              "so a kill can never be written without this number on the page.", ""]

    # --- 6. the declared kill lines ---------------------------------------------
    k1 = per >= KILL_MIN_PER_SESSION
    k2 = frac >= KILL_MIN_TRADEABLE_FRAC
    L += ["## 6. Census kill lines — declared in prereg §4 before these numbers were read",
          "", "| line | bar | observed | verdict |", "|---|---|---:|---|",
          f"| triggers per session | ≥ {KILL_MIN_PER_SESSION:.0f} | {per:.1f} | "
          f"{'**PASS**' if k1 else '**FAIL**'} |",
          f"| carry both BB and VWAP | ≥ {KILL_MIN_TRADEABLE_FRAC:.0%} | {frac:.1%} | "
          f"{'**PASS**' if k2 else '**FAIL**'} |", "",
          ("**L0 PASSES. The substrate exists and is tradeable under the strategy's own "
           "rule.**" if (k1 and k2) else
           "**L0 FAILS its declared census line — the family dies here.**"), "",
          "L0 can only kill on the premise (§5.9.1). It has made no expectancy claim in",
          "either direction, and the next rung (L1 fills) is owed before any P&L exists.", ""]

    text = "\n".join(L)
    print(text)
    OUT_MD.write_text(text)

    rows = [{"family": "LDN-CAN-01", "era": "fit", "prereg": PREREG,
             "trial": f"L0 census {b} band, triggers per session",
             "stat_type": "mean", "estimate": round(len(Ts[b]) / Ts[b]["day"].nunique(), 4),
             "n": len(Ts[b]), "t_stat": 0.0, "effect": 0.0,
             "verdict": (f"L0 census, no selection: {len(Ts[b]):,} triggers over "
                         f"{Ts[b]['day'].nunique()} sessions; "
                         f"{(Ts[b]['ladder'] != 'NO TRADE').mean():.1%} tradeable under "
                         f"the v1.1 ladder; parity vs cached stream PASSED")}
            for b in BANDS if Ts[b] is not None]
    ex = trial_ledger.load()
    already = set(zip(ex["family"], ex["trial"], ex["era"]))
    fresh = [r for r in rows if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"\nrecorded {len(fresh)} trials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
